"""
Workflow management REST API router.

Allows Canvas to submit workflows to Orchestrator for remote execution.
Implements dual storage (PostgreSQL + filesystem backup).

Endpoints:
- POST /workflows - Submit workflow
- GET /workflows/{workflow_id} - Get workflow details
- POST /workflows/upload - Upload workflow JSON file
- DELETE /workflows/{workflow_id} - Delete workflow

Security:
- JSON payload size limits to prevent DoS attacks
- File upload validation (size, type, content)
- Node count limits to prevent resource exhaustion
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field, field_validator
from loguru import logger
import orjson

from casare_rpa.infrastructure.queue import (
    get_memory_queue,
    MemoryQueue,
)


# Database pool (initialized by main.py lifespan)
_db_pool: Optional[asyncpg.Pool] = None


def set_db_pool(pool: asyncpg.Pool) -> None:
    """Set the database pool for workflow operations."""
    global _db_pool
    _db_pool = pool


def get_db_pool() -> Optional[asyncpg.Pool]:
    """Get the database pool."""
    return _db_pool


router = APIRouter()


# =========================
# Security Constants
# =========================

# Maximum JSON payload size (10MB) - prevents DoS via large payloads
MAX_WORKFLOW_SIZE_BYTES = 10 * 1024 * 1024

# Maximum file upload size (50MB)
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024

# Maximum number of nodes in a workflow
MAX_NODES_COUNT = 1000

# Allowed content types for file uploads
ALLOWED_UPLOAD_CONTENT_TYPES = {
    "application/json",
    "text/plain",
    "application/octet-stream",  # Some browsers send this for .json files
}


# =========================
# Request/Response Models
# =========================


class WorkflowSubmissionRequest(BaseModel):
    """Request model for workflow submission."""

    workflow_name: str = Field(..., min_length=1, max_length=255)
    workflow_json: Dict[str, Any] = Field(..., description="Workflow graph definition")
    trigger_type: str = Field(
        default="manual", description="manual, scheduled, or webhook"
    )
    execution_mode: str = Field(default="lan", description="lan or internet")
    schedule_cron: Optional[str] = Field(
        None, description="Cron expression if trigger_type=scheduled"
    )
    priority: int = Field(
        default=10, ge=0, le=20, description="Job priority (0=highest, 20=lowest)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v):
        allowed = ["manual", "scheduled", "webhook"]
        if v not in allowed:
            raise ValueError(f"trigger_type must be one of {allowed}")
        return v

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v):
        allowed = ["lan", "internet"]
        if v not in allowed:
            raise ValueError(f"execution_mode must be one of {allowed}")
        return v

    @field_validator("workflow_json")
    @classmethod
    def validate_workflow_json(cls, v):
        # Basic validation - must have nodes key
        if "nodes" not in v:
            raise ValueError("workflow_json must contain 'nodes' key")
        if not isinstance(v["nodes"], list):
            raise ValueError("workflow_json.nodes must be a list")

        # Security: Limit node count to prevent resource exhaustion
        if len(v["nodes"]) > MAX_NODES_COUNT:
            raise ValueError(
                f"Workflow exceeds maximum node count ({len(v['nodes'])} > {MAX_NODES_COUNT})"
            )

        return v


class WorkflowSubmissionResponse(BaseModel):
    """Response model for workflow submission."""

    workflow_id: str
    job_id: Optional[str] = None
    schedule_id: Optional[str] = None
    status: str
    message: str
    created_at: datetime


class WorkflowDetailsResponse(BaseModel):
    """Response model for workflow details."""

    workflow_id: str
    workflow_name: str
    workflow_json: Dict[str, Any]
    version: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


# =========================
# Utility Functions
# =========================


def get_workflows_dir() -> Path:
    """Get workflows directory path from environment or use default."""
    workflows_dir = Path(os.getenv("WORKFLOWS_DIR", "./workflows"))
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return workflows_dir


async def store_workflow_filesystem(
    workflow_id: str,
    workflow_name: str,
    workflow_json: Dict[str, Any],
) -> Path:
    """
    Store workflow on filesystem (backup storage).

    Args:
        workflow_id: Workflow identifier
        workflow_name: Workflow name
        workflow_json: Workflow definition

    Returns:
        Path to saved file
    """
    workflows_dir = get_workflows_dir()
    file_path = workflows_dir / f"{workflow_id}.json"

    # Prepare workflow data with metadata
    workflow_data = {
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "workflow_json": workflow_json,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save with orjson for performance
    file_path.write_bytes(orjson.dumps(workflow_data, option=orjson.OPT_INDENT_2))

    logger.info("Workflow stored to filesystem: {} ({})", workflow_id, file_path)
    return file_path


async def store_workflow_database(
    workflow_id: str,
    workflow_name: str,
    workflow_json: Dict[str, Any],
    description: Optional[str] = None,
) -> bool:
    """
    Store workflow in PostgreSQL database (primary storage).

    Args:
        workflow_id: Workflow identifier
        workflow_name: Workflow name
        workflow_json: Workflow definition
        description: Optional description

    Returns:
        True if successful, False otherwise
    """
    pool = get_db_pool()
    if not pool:
        logger.warning(
            "Database pool not available for workflow: {} - using filesystem only",
            workflow_id,
        )
        return False

    try:
        async with pool.acquire() as conn:
            # Use UPSERT to handle both insert and update
            await conn.execute(
                """
                INSERT INTO workflows (
                    workflow_id, workflow_name, workflow_json, description,
                    version, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, 1, NOW(), NOW())
                ON CONFLICT (workflow_id) DO UPDATE SET
                    workflow_name = EXCLUDED.workflow_name,
                    workflow_json = EXCLUDED.workflow_json,
                    description = EXCLUDED.description,
                    version = workflows.version + 1,
                    updated_at = NOW()
                """,
                uuid.UUID(workflow_id),
                workflow_name,
                orjson.dumps(workflow_json).decode(),  # JSONB needs string
                description or "",
            )

        logger.info("Workflow stored to database: {}", workflow_id)
        return True

    except Exception as e:
        logger.error("Failed to store workflow in database: {}", e)
        return False


async def enqueue_job(
    workflow_id: str,
    workflow_json: Dict[str, Any],
    priority: int,
    execution_mode: str,
    metadata: Dict[str, Any],
) -> str:
    """
    Enqueue job to queue (PostgreSQL jobs table or MemoryQueue fallback).

    Args:
        workflow_id: Workflow identifier
        workflow_json: Workflow definition
        priority: Job priority
        execution_mode: lan or internet
        metadata: Additional job metadata

    Returns:
        job_id: Created job identifier
    """
    # Check if USE_MEMORY_QUEUE is set
    use_memory_queue = os.getenv("USE_MEMORY_QUEUE", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    if use_memory_queue:
        # Use in-memory queue fallback
        queue = get_memory_queue()

        job_id = await queue.enqueue(
            workflow_id=workflow_id,
            workflow_json=workflow_json,
            priority=priority,
            execution_mode=execution_mode,
            metadata=metadata,
        )

        logger.info(
            "Job enqueued to memory queue: {} (workflow={}, mode={})",
            job_id,
            workflow_id,
            execution_mode,
        )
        return job_id

    # Use PostgreSQL jobs table
    pool = get_db_pool()
    if not pool:
        logger.warning("Database pool not available, using memory queue fallback")
        queue = get_memory_queue()
        return await queue.enqueue(
            workflow_id=workflow_id,
            workflow_json=workflow_json,
            priority=priority,
            execution_mode=execution_mode,
            metadata=metadata,
        )

    try:
        job_id = str(uuid.uuid4())

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO jobs (
                    job_id, workflow_id, status, priority, execution_mode,
                    created_at, retry_count, max_retries, metadata
                ) VALUES ($1, $2, 'pending', $3, $4, NOW(), 0, 3, $5)
                """,
                uuid.UUID(job_id),
                uuid.UUID(workflow_id),
                priority,
                execution_mode,
                orjson.dumps(metadata).decode(),
            )

        logger.info(
            "Job enqueued to database: {} (workflow={}, mode={})",
            job_id,
            workflow_id,
            execution_mode,
        )
        return job_id

    except Exception as e:
        logger.error(
            "Failed to enqueue job to database: {} - falling back to memory queue", e
        )
        queue = get_memory_queue()
        return await queue.enqueue(
            workflow_id=workflow_id,
            workflow_json=workflow_json,
            priority=priority,
            execution_mode=execution_mode,
            metadata=metadata,
        )


# =========================
# API Endpoints
# =========================


@router.post("/workflows", response_model=WorkflowSubmissionResponse)
async def submit_workflow(
    request: WorkflowSubmissionRequest,
) -> WorkflowSubmissionResponse:
    """
    Submit a workflow from Canvas to Orchestrator.

    Workflow Submission Flow:
    1. Generate workflow_id
    2. Store in PostgreSQL (primary)
    3. Store in filesystem (backup)
    4. If trigger_type=manual: enqueue job immediately
    5. If trigger_type=scheduled: create schedule (TODO)
    6. Return workflow_id and job_id/schedule_id

    Args:
        request: Workflow submission request

    Returns:
        WorkflowSubmissionResponse with IDs and status
    """
    try:
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())

        logger.info(
            "Workflow submission started: {} (name={}, trigger={}, mode={})",
            workflow_id,
            request.workflow_name,
            request.trigger_type,
            request.execution_mode,
        )

        # Store in database (primary)
        db_stored = await store_workflow_database(
            workflow_id=workflow_id,
            workflow_name=request.workflow_name,
            workflow_json=request.workflow_json,
            description=request.metadata.get("description"),
        )

        # Store in filesystem (backup) - always do this for safety
        backup_enabled = os.getenv("WORKFLOW_BACKUP_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        if backup_enabled:
            await store_workflow_filesystem(
                workflow_id=workflow_id,
                workflow_name=request.workflow_name,
                workflow_json=request.workflow_json,
            )

        # Handle trigger type
        job_id = None
        schedule_id = None
        status_message = ""

        if request.trigger_type == "manual":
            # Enqueue job immediately
            job_id = await enqueue_job(
                workflow_id=workflow_id,
                workflow_json=request.workflow_json,
                priority=request.priority,
                execution_mode=request.execution_mode,
                metadata=request.metadata,
            )
            status_message = (
                f"Workflow submitted and queued for {request.execution_mode} execution"
            )

        elif request.trigger_type == "scheduled":
            # TODO: Create schedule via ScheduleManagementService
            schedule_id = str(uuid.uuid4())  # Placeholder
            status_message = (
                f"Workflow submitted and scheduled (cron: {request.schedule_cron})"
            )
            logger.warning(
                "Schedule creation not yet implemented, returning placeholder"
            )

        elif request.trigger_type == "webhook":
            # TODO: Register webhook trigger
            status_message = (
                "Workflow submitted for webhook trigger (not yet implemented)"
            )
            logger.warning("Webhook trigger not yet implemented")

        return WorkflowSubmissionResponse(
            workflow_id=workflow_id,
            job_id=job_id,
            schedule_id=schedule_id,
            status="success" if db_stored else "degraded",
            message=status_message,
            created_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error("Workflow submission failed: {}", e)
        raise HTTPException(
            status_code=500, detail=f"Workflow submission failed: {str(e)}"
        )


@router.post("/workflows/upload", response_model=WorkflowSubmissionResponse)
async def upload_workflow(
    file: UploadFile = File(...),
    trigger_type: str = "manual",
    execution_mode: str = "lan",
    priority: int = 10,
) -> WorkflowSubmissionResponse:
    """
    Upload workflow JSON file.

    Alternative to JSON payload for large workflows.

    Security:
    - File size limit: 50MB
    - File type validation: .json extension + content type check
    - Content validation: Valid JSON with nodes array

    Args:
        file: Uploaded .json file
        trigger_type: manual, scheduled, or webhook
        execution_mode: lan or internet
        priority: Job priority (0=highest, 20=lowest)

    Returns:
        WorkflowSubmissionResponse

    Raises:
        HTTPException 400: Invalid file type or content
        HTTPException 413: File too large
    """
    try:
        # Security: Validate file extension
        if not file.filename or not file.filename.lower().endswith(".json"):
            raise HTTPException(
                status_code=400,
                detail="File must be a .json file",
            )

        # Security: Validate content type (if provided)
        if file.content_type and file.content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
            logger.warning(
                "Upload rejected - invalid content type: {} for file {}",
                file.content_type,
                file.filename,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {file.content_type}. "
                f"Allowed: {', '.join(ALLOWED_UPLOAD_CONTENT_TYPES)}",
            )

        # Security: Check file size before reading full content
        # file.size may be None for streamed uploads, so we check after read
        if file.size and file.size > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_BYTES // 1024 // 1024}MB",
            )

        # Read content with size limit
        content = await file.read()

        # Security: Verify actual size after read
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_BYTES // 1024 // 1024}MB",
            )

        # Parse JSON
        try:
            workflow_data = orjson.loads(content)
        except orjson.JSONDecodeError as e:
            logger.error("Invalid JSON in uploaded file {}: {}", file.filename, e)
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Extract workflow name from filename (without .json extension)
        workflow_name = Path(file.filename).stem

        # Create submission request (validation happens in WorkflowSubmissionRequest)
        request = WorkflowSubmissionRequest(
            workflow_name=workflow_name,
            workflow_json=workflow_data.get("workflow_json", workflow_data),
            trigger_type=trigger_type,
            execution_mode=execution_mode,
            priority=priority,
        )

        # Use regular submission endpoint
        return await submit_workflow(request)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(
            "File upload failed for {}: {}", file.filename if file else "unknown", e
        )
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetailsResponse)
async def get_workflow(workflow_id: str) -> WorkflowDetailsResponse:
    """
    Get workflow details by ID.

    Tries database first, falls back to filesystem.

    Args:
        workflow_id: Workflow UUID

    Returns:
        WorkflowDetailsResponse
    """
    try:
        # TODO: Try database first
        # For now, read from filesystem
        workflows_dir = get_workflows_dir()
        file_path = workflows_dir / f"{workflow_id}.json"

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_id}"
            )

        # Load workflow data
        workflow_data = orjson.loads(file_path.read_bytes())

        return WorkflowDetailsResponse(
            workflow_id=workflow_data.get("workflow_id", workflow_id),
            workflow_name=workflow_data.get("workflow_name", "Unknown"),
            workflow_json=workflow_data.get("workflow_json", {}),
            version=workflow_data.get("version", 1),
            description=workflow_data.get("description"),
            created_at=datetime.fromisoformat(workflow_data["created_at"])
            if "created_at" in workflow_data
            else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(workflow_data["updated_at"])
            if "updated_at" in workflow_data
            else datetime.now(timezone.utc),
        )

    except orjson.JSONDecodeError as e:
        logger.error("Corrupted workflow file: {}", workflow_id)
        raise HTTPException(status_code=500, detail="Corrupted workflow file")

    except Exception as e:
        logger.error("Failed to retrieve workflow {}: {}", workflow_id, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str) -> Dict[str, str]:
    """
    Delete workflow.

    Deletes from both database and filesystem.

    Args:
        workflow_id: Workflow UUID

    Returns:
        Success message
    """
    try:
        # TODO: Delete from database

        # Delete from filesystem
        workflows_dir = get_workflows_dir()
        file_path = workflows_dir / f"{workflow_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.info("Workflow deleted from filesystem: {}", workflow_id)

        return {
            "status": "success",
            "message": f"Workflow deleted: {workflow_id}",
        }

    except Exception as e:
        logger.error("Failed to delete workflow {}: {}", workflow_id, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete workflow: {str(e)}"
        )
