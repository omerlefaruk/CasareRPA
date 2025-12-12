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
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from loguru import logger
import orjson

from casare_rpa.infrastructure.orchestrator.api.auth import (
    get_current_user,
    AuthenticatedUser,
)

from casare_rpa.infrastructure.queue import (
    get_memory_queue,
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

# UUID validation pattern (prevents path traversal and injection)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_uuid_format(value: str, field_name: str = "ID") -> str:
    """
    Validate that a string is a valid UUID format.

    Prevents path traversal attacks by ensuring the ID contains only
    valid UUID characters (hex digits and hyphens).

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Returns:
        The validated UUID string

    Raises:
        HTTPException: 400 if format is invalid
    """
    if not UUID_PATTERN.match(value):
        logger.warning(
            "Invalid {} format rejected: {}",
            field_name,
            value[:50] if len(value) > 50 else value,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format. Expected UUID.",
        )
    return value


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

        # Accept both dict (Canvas format) and list format for nodes
        nodes = v["nodes"]
        if isinstance(nodes, dict):
            node_count = len(nodes)
        elif isinstance(nodes, list):
            node_count = len(nodes)
        else:
            raise ValueError("workflow_json.nodes must be a dict or list")

        # Security: Limit node count to prevent resource exhaustion
        if node_count > MAX_NODES_COUNT:
            raise ValueError(
                f"Workflow exceeds maximum node count ({node_count} > {MAX_NODES_COUNT})"
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
# Trigger Manager Singleton
# =========================

_trigger_manager: Optional["TriggerManager"] = None  # type: ignore


def set_trigger_manager(manager: "TriggerManager") -> None:  # type: ignore
    """Set the global trigger manager for webhook registration."""
    global _trigger_manager
    _trigger_manager = manager
    logger.info("Workflows router: TriggerManager set")


def _get_trigger_manager() -> Optional["TriggerManager"]:  # type: ignore
    """Get the global trigger manager."""
    return _trigger_manager


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

    # Use PostgreSQL job_queue table (read by Robot's PgQueuerConsumer)
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

        # Get workflow name from metadata or workflow_json
        workflow_name = (
            metadata.get("workflow_name")
            or workflow_json.get("metadata", {}).get("name")
            or "Untitled Workflow"
        )

        async with pool.acquire() as conn:
            # Insert into job_queue table (used by Robot's PgQueuerConsumer)
            await conn.execute(
                """
                INSERT INTO job_queue (
                    id, workflow_id, workflow_name, workflow_json,
                    priority, status, environment, visible_after,
                    created_at, retry_count, max_retries, metadata
                ) VALUES ($1, $2, $3, $4, $5, 'pending', $6, NOW(), NOW(), 0, 3, $7)
                """,
                uuid.UUID(job_id),
                workflow_id,
                workflow_name,
                orjson.dumps(workflow_json).decode(),  # Store as JSON text
                priority,
                execution_mode,  # Use execution_mode as environment
                orjson.dumps(metadata).decode(),
            )

        logger.info(
            "Job enqueued to job_queue: {} (workflow={}, name={}, mode={})",
            job_id,
            workflow_id,
            workflow_name,
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
    current_user: AuthenticatedUser = Depends(get_current_user),
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
            # Create schedule via the schedules router
            if not request.schedule_cron:
                raise HTTPException(
                    status_code=400,
                    detail="schedule_cron is required when trigger_type=scheduled",
                )

            try:
                from casare_rpa.infrastructure.orchestrator.scheduling import (
                    get_global_scheduler,
                    is_scheduler_initialized,
                    AdvancedSchedule,
                    ScheduleType,
                    ScheduleStatus,
                )
                from croniter import croniter

                schedule_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)

                # Validate cron expression
                try:
                    cron = croniter(request.schedule_cron, now)
                    next_run = cron.get_next(datetime)
                except (ValueError, KeyError) as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid cron expression: {str(e)}",
                    )

                # Create AdvancedSchedule for APScheduler
                advanced_schedule = AdvancedSchedule(
                    id=schedule_id,
                    name=f"Schedule for {request.workflow_name}",
                    workflow_id=workflow_id,
                    workflow_name=request.workflow_name,
                    schedule_type=ScheduleType.CRON,
                    status=ScheduleStatus.ACTIVE,
                    enabled=True,
                    cron_expression=request.schedule_cron,
                    priority=request.priority,
                    metadata={
                        "execution_mode": request.execution_mode,
                        **request.metadata,
                    },
                    next_run=next_run,
                    created_at=now,
                    updated_at=now,
                )

                # Register with APScheduler if available
                scheduler = get_global_scheduler()
                if scheduler is not None and is_scheduler_initialized():
                    success = scheduler.add_schedule(advanced_schedule)
                    if success:
                        logger.info(
                            "Schedule registered with APScheduler: {} (workflow={}, cron='{}')",
                            schedule_id,
                            workflow_id,
                            request.schedule_cron,
                        )
                    else:
                        logger.warning(
                            "Failed to register schedule with APScheduler: {}",
                            schedule_id,
                        )
                else:
                    logger.warning(
                        "APScheduler not initialized, schedule stored but won't auto-execute: {}",
                        schedule_id,
                    )

                # Store schedule in database if pool available
                pool = get_db_pool()
                if pool:
                    try:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO schedules (
                                    id, workflow_id, schedule_name, cron_expression,
                                    enabled, priority, execution_mode, next_run,
                                    created_at, updated_at, metadata
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9, $10)
                                ON CONFLICT (id) DO UPDATE SET
                                    cron_expression = EXCLUDED.cron_expression,
                                    enabled = EXCLUDED.enabled,
                                    updated_at = NOW()
                                """,
                                uuid.UUID(schedule_id),
                                uuid.UUID(workflow_id),
                                f"Schedule for {request.workflow_name}",
                                request.schedule_cron,
                                True,
                                request.priority,
                                request.execution_mode,
                                next_run,
                                now,
                                orjson.dumps(request.metadata).decode(),
                            )
                        logger.info("Schedule stored in database: {}", schedule_id)
                    except Exception as e:
                        logger.error("Failed to store schedule in database: {}", e)

                status_message = f"Workflow submitted and scheduled (cron: {request.schedule_cron}, next_run: {next_run.isoformat()})"

            except HTTPException:
                raise
            except Exception as e:
                logger.error("Failed to create schedule: {}", e)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create schedule: {str(e)}",
                )

        elif request.trigger_type == "webhook":
            # Register webhook trigger via TriggerManager
            try:
                from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
                from casare_rpa.triggers.manager import TriggerManager

                trigger_id = str(uuid.uuid4())

                # Build webhook config from metadata
                webhook_config = request.metadata.get("webhook_config", {})
                endpoint = webhook_config.get("endpoint", f"/hooks/{trigger_id}")
                auth_type = webhook_config.get("auth_type", "none")
                secret = webhook_config.get("secret", "")

                # Create trigger configuration
                trigger_config = BaseTriggerConfig(
                    id=trigger_id,
                    name=f"Webhook for {request.workflow_name}",
                    trigger_type=TriggerType.WEBHOOK,
                    scenario_id=request.metadata.get("scenario_id", "default"),
                    workflow_id=workflow_id,
                    enabled=True,
                    priority=request.priority,
                    description=f"Webhook trigger for workflow: {request.workflow_name}",
                    config={
                        "endpoint": endpoint,
                        "auth_type": auth_type,
                        "secret": secret,
                        "methods": webhook_config.get("methods", ["POST"]),
                        "execution_mode": request.execution_mode,
                    },
                )

                # Get or create trigger manager instance
                # Note: In production, this should be accessed via dependency injection
                # For now, we create a singleton-like reference
                trigger_manager = _get_trigger_manager()
                if trigger_manager:
                    registered_trigger = await trigger_manager.register_trigger(
                        trigger_config
                    )
                    if registered_trigger:
                        webhook_url = trigger_manager.get_webhook_url(trigger_id)
                        logger.info(
                            "Webhook trigger registered: {} (workflow={}, endpoint='{}')",
                            trigger_id,
                            workflow_id,
                            endpoint,
                        )
                        status_message = f"Workflow submitted with webhook trigger (URL: {webhook_url})"
                    else:
                        logger.warning(
                            "Failed to register webhook trigger: {}", trigger_id
                        )
                        status_message = (
                            "Workflow submitted but webhook registration failed"
                        )
                else:
                    logger.warning(
                        "TriggerManager not available, webhook registered in config only"
                    )
                    status_message = (
                        f"Workflow submitted for webhook trigger (endpoint: {endpoint})"
                    )

                # Store webhook config in database
                pool = get_db_pool()
                if pool:
                    try:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO webhook_triggers (
                                    id, workflow_id, endpoint, auth_type,
                                    enabled, created_at, metadata
                                ) VALUES ($1, $2, $3, $4, $5, NOW(), $6)
                                ON CONFLICT (id) DO UPDATE SET
                                    endpoint = EXCLUDED.endpoint,
                                    auth_type = EXCLUDED.auth_type
                                """,
                                uuid.UUID(trigger_id),
                                uuid.UUID(workflow_id),
                                endpoint,
                                auth_type,
                                True,
                                orjson.dumps(trigger_config.to_dict()).decode(),
                            )
                        logger.info(
                            "Webhook trigger stored in database: {}", trigger_id
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to store webhook in database (table may not exist): {}",
                            e,
                        )

            except ImportError as e:
                logger.warning("Trigger system not available: {}", e)
                status_message = (
                    "Workflow submitted (webhook trigger requires trigger system)"
                )
            except Exception as e:
                logger.error("Failed to register webhook trigger: {}", e)
                status_message = (
                    f"Workflow submitted but webhook setup failed: {str(e)}"
                )

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
    current_user: AuthenticatedUser = Depends(get_current_user),
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
async def get_workflow(
    workflow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkflowDetailsResponse:
    """
    Get workflow details by ID.

    Tries database first, falls back to filesystem.

    Args:
        workflow_id: Workflow UUID
        current_user: Authenticated user from JWT

    Returns:
        WorkflowDetailsResponse
    """
    # Security: Validate UUID format to prevent path traversal
    validate_uuid_format(workflow_id, "workflow_id")

    try:
        # Try database first
        pool = get_db_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        SELECT workflow_id, workflow_name, workflow_json,
                               version, description, created_at, updated_at
                        FROM workflows
                        WHERE workflow_id = $1
                        """,
                        uuid.UUID(workflow_id),
                    )

                    if row:
                        # Parse workflow_json from JSONB
                        workflow_json = row["workflow_json"]
                        if isinstance(workflow_json, str):
                            workflow_json = orjson.loads(workflow_json)

                        logger.debug(
                            "Workflow retrieved from database: {}", workflow_id
                        )
                        return WorkflowDetailsResponse(
                            workflow_id=str(row["workflow_id"]),
                            workflow_name=row["workflow_name"],
                            workflow_json=workflow_json,
                            version=row["version"] or 1,
                            description=row["description"],
                            created_at=row["created_at"] or datetime.now(timezone.utc),
                            updated_at=row["updated_at"] or datetime.now(timezone.utc),
                        )
            except Exception as e:
                logger.warning(
                    "Database lookup failed for workflow {}, trying filesystem: {}",
                    workflow_id,
                    e,
                )

        # Fallback to filesystem
        workflows_dir = get_workflows_dir()
        file_path = workflows_dir / f"{workflow_id}.json"

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_id}"
            )

        # Load workflow data
        workflow_data = orjson.loads(file_path.read_bytes())

        logger.debug("Workflow retrieved from filesystem: {}", workflow_id)
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

    except HTTPException:
        raise

    except orjson.JSONDecodeError:
        logger.error("Corrupted workflow file: {}", workflow_id)
        raise HTTPException(status_code=500, detail="Corrupted workflow file")

    except Exception as e:
        logger.error("Failed to retrieve workflow {}: {}", workflow_id, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Delete workflow.

    Deletes from both database and filesystem.

    Args:
        workflow_id: Workflow UUID
        current_user: Authenticated user from JWT

    Returns:
        Success message
    """
    # Security: Validate UUID format to prevent path traversal
    validate_uuid_format(workflow_id, "workflow_id")

    try:
        db_deleted = False
        fs_deleted = False

        # Delete from database first
        pool = get_db_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    # Delete workflow from main table
                    result = await conn.execute(
                        "DELETE FROM workflows WHERE workflow_id = $1",
                        uuid.UUID(workflow_id),
                    )
                    if result and "DELETE" in result:
                        db_deleted = True
                        logger.info("Workflow deleted from database: {}", workflow_id)

                    # Also delete any associated schedules
                    await conn.execute(
                        "DELETE FROM schedules WHERE workflow_id = $1",
                        uuid.UUID(workflow_id),
                    )

                    # And webhook triggers if table exists
                    try:
                        await conn.execute(
                            "DELETE FROM webhook_triggers WHERE workflow_id = $1",
                            uuid.UUID(workflow_id),
                        )
                    except Exception:
                        pass  # Table may not exist

            except Exception as e:
                logger.warning(
                    "Failed to delete workflow from database: {} - {}",
                    workflow_id,
                    e,
                )

        # Delete from filesystem
        workflows_dir = get_workflows_dir()
        file_path = workflows_dir / f"{workflow_id}.json"

        if file_path.exists():
            file_path.unlink()
            fs_deleted = True
            logger.info("Workflow deleted from filesystem: {}", workflow_id)

        # Unregister any associated webhook triggers
        trigger_manager = _get_trigger_manager()
        if trigger_manager:
            try:
                # Find and unregister triggers for this workflow
                for trigger in trigger_manager.get_all_triggers():
                    if trigger.config.workflow_id == workflow_id:
                        await trigger_manager.unregister_trigger(trigger.config.id)
                        logger.info(
                            "Unregistered trigger {} for workflow {}",
                            trigger.config.id,
                            workflow_id,
                        )
            except Exception as e:
                logger.warning("Failed to unregister triggers for workflow: {}", e)

        if not db_deleted and not fs_deleted:
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_id}"
            )

        return {
            "status": "success",
            "message": f"Workflow deleted: {workflow_id}",
            "deleted_from": {
                "database": db_deleted,
                "filesystem": fs_deleted,
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Failed to delete workflow {}: {}", workflow_id, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete workflow: {str(e)}"
        )
