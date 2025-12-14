"""
REST API Endpoints for Cloud Orchestrator.

Provides REST endpoints for robot management, job submission, and log queries.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from casare_rpa.domain.value_objects.log_entry import LogLevel, LogQuery
from casare_rpa.infrastructure.orchestrator.server_auth import verify_admin_api_key
from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    get_job_producer,
    get_log_cleanup_job,
    get_log_repository,
    get_log_streaming_service,
    get_robot_manager,
)
from loguru import logger


# =============================================================================
# MODELS
# =============================================================================


class RobotRegistration(BaseModel):
    """Robot registration message from WebSocket."""

    robot_id: str
    robot_name: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    environment: str = "production"
    api_key_hash: Optional[str] = None
    tenant_id: Optional[str] = None


class JobSubmission(BaseModel):
    """Job submission request."""

    workflow_id: str
    workflow_data: Dict[str, Any]
    variables: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    target_robot_id: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    timeout: Optional[int] = None
    tenant_id: Optional[str] = None


class JobResponse(BaseModel):
    """Job response after submission."""

    job_id: str
    status: str
    workflow_id: str
    robot_id: Optional[str] = None
    created_at: datetime


class RobotInfo(BaseModel):
    """Robot information for API response."""

    robot_id: str
    robot_name: str
    status: str
    capabilities: List[str] = Field(default_factory=list)
    current_jobs: int = 0
    max_concurrent_jobs: int = 1
    last_heartbeat: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    tenant_id: Optional[str] = None


class LogQueryRequest(BaseModel):
    """Log query parameters."""

    robot_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_level: str = "DEBUG"
    source: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class LogEntryResponse(BaseModel):
    """Log entry response."""

    id: str
    robot_id: str
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class LogStatsResponse(BaseModel):
    """Log statistics response."""

    total_count: int
    by_level: Dict[str, int]
    oldest_log: Optional[datetime] = None
    newest_log: Optional[datetime] = None
    storage_bytes: int


# =============================================================================
# ROUTER
# =============================================================================


router = APIRouter()


# Robot management endpoints (require admin authentication)
@router.get("/robots", response_model=List[RobotInfo])
async def list_robots(
    _: str = Depends(verify_admin_api_key),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
):
    """List all connected robots, optionally filtered by tenant. Requires admin API key."""
    manager = get_robot_manager()
    robots = manager.get_all_robots(tenant_id=tenant_id)
    return [
        RobotInfo(
            robot_id=r.robot_id,
            robot_name=r.robot_name,
            status=r.status,
            capabilities=r.capabilities,
            current_jobs=len(r.current_job_ids),
            max_concurrent_jobs=r.max_concurrent_jobs,
            last_heartbeat=r.last_heartbeat,
            connected_at=r.connected_at,
            tenant_id=r.tenant_id,
        )
        for r in robots
    ]


@router.get("/robots/{robot_id}", response_model=RobotInfo)
async def get_robot(robot_id: str, _: str = Depends(verify_admin_api_key)):
    """Get a specific robot by ID. Requires admin API key."""
    manager = get_robot_manager()
    robot = manager.get_robot(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return RobotInfo(
        robot_id=robot.robot_id,
        robot_name=robot.robot_name,
        status=robot.status,
        capabilities=robot.capabilities,
        current_jobs=len(robot.current_job_ids),
        max_concurrent_jobs=robot.max_concurrent_jobs,
        last_heartbeat=robot.last_heartbeat,
        connected_at=robot.connected_at,
        tenant_id=robot.tenant_id,
    )


# Job endpoints (require admin authentication)
@router.post("/jobs", response_model=JobResponse)
async def submit_job(
    submission: JobSubmission,
    _: str = Depends(verify_admin_api_key),
):
    """Submit a job for execution. Requires admin API key.

    Uses durable PostgreSQL queue when available, falls back to in-memory
    job assignment for backward compatibility.
    """
    import orjson

    producer = get_job_producer()

    if producer is not None and producer.is_connected:
        # Use durable PostgreSQL queue (DDD 2025 - recommended path)
        try:
            workflow_json = orjson.dumps(submission.workflow_data).decode("utf-8")
            workflow_name = submission.workflow_data.get("name", submission.workflow_id)

            enqueued_job = await producer.enqueue_job(
                workflow_id=submission.workflow_id,
                workflow_name=workflow_name,
                workflow_json=workflow_json,
                priority=submission.priority,
                variables=submission.variables,
            )

            logger.info(f"Job {enqueued_job.job_id} enqueued to durable queue")

            return JobResponse(
                job_id=enqueued_job.job_id,
                status="pending",  # Job is queued, not yet assigned
                workflow_id=enqueued_job.workflow_id,
                robot_id=None,  # Robot will claim via SKIP LOCKED
                created_at=enqueued_job.created_at,
            )
        except Exception as e:
            logger.warning(f"Durable queue submission failed, falling back: {e}")
            # Fall through to in-memory fallback

    # Fallback: Use in-memory RobotManager (legacy path)
    manager = get_robot_manager()
    job = await manager.submit_job(
        workflow_id=submission.workflow_id,
        workflow_data=submission.workflow_data,
        variables=submission.variables,
        priority=submission.priority,
        target_robot_id=submission.target_robot_id,
        required_capabilities=submission.required_capabilities,
        timeout=submission.timeout,
        tenant_id=submission.tenant_id,
    )
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        workflow_id=job.workflow_id,
        robot_id=job.assigned_robot_id,
        created_at=job.created_at,
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, _: str = Depends(verify_admin_api_key)):
    """Get job status by ID. Requires admin API key."""
    manager = get_robot_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "workflow_id": job.workflow_id,
        "status": job.status,
        "priority": job.priority,
        "assigned_robot_id": job.assigned_robot_id,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/jobs")
async def list_jobs(
    _: str = Depends(verify_admin_api_key),
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(100, ge=1, le=1000),
):
    """List jobs with optional status and tenant filter. Requires admin API key."""
    manager = get_robot_manager()
    jobs = list(manager.get_all_jobs().values())

    if status:
        jobs = [j for j in jobs if j.status == status]

    if tenant_id:
        jobs = [j for j in jobs if j.tenant_id == tenant_id]

    # Sort by priority (higher first) then created_at (older first)
    jobs.sort(key=lambda j: (-j.priority, j.created_at))

    return [
        {
            "job_id": j.job_id,
            "workflow_id": j.workflow_id,
            "status": j.status,
            "priority": j.priority,
            "assigned_robot_id": j.assigned_robot_id,
            "tenant_id": j.tenant_id,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs[:limit]
    ]


# =============================================================================
# LOG ENDPOINTS
# =============================================================================


@router.get("/logs", response_model=List[LogEntryResponse])
async def query_logs(
    _: str = Depends(verify_admin_api_key),
    tenant_id: str = Query(..., description="Tenant ID (required)"),
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range"),
    min_level: str = Query("DEBUG", description="Minimum log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search_text: Optional[str] = Query(None, description="Search in message"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """Query historical logs with filtering. Requires admin API key."""
    log_repository = get_log_repository()
    if log_repository is None:
        raise HTTPException(
            status_code=503,
            detail="Log service not available",
        )

    try:
        query = LogQuery(
            tenant_id=tenant_id,
            robot_id=robot_id,
            start_time=start_time,
            end_time=end_time,
            min_level=LogLevel.from_string(min_level),
            source=source,
            search_text=search_text,
            limit=limit,
            offset=offset,
        )
        entries = await log_repository.query(query)
        return [
            LogEntryResponse(
                id=e.id,
                robot_id=e.robot_id,
                timestamp=e.timestamp,
                level=e.level.value,
                message=e.message,
                source=e.source,
                extra=e.extra,
            )
            for e in entries
        ]
    except Exception as e:
        logger.error(f"Log query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stats", response_model=LogStatsResponse)
async def get_log_stats(
    _: str = Depends(verify_admin_api_key),
    tenant_id: str = Query(..., description="Tenant ID (required)"),
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
):
    """Get log statistics. Requires admin API key."""
    log_repository = get_log_repository()
    if log_repository is None:
        raise HTTPException(
            status_code=503,
            detail="Log service not available",
        )

    try:
        stats = await log_repository.get_stats(tenant_id, robot_id)
        return LogStatsResponse(
            total_count=stats.total_count,
            by_level=stats.by_level,
            oldest_log=stats.oldest_log,
            newest_log=stats.newest_log,
            storage_bytes=stats.storage_bytes,
        )
    except Exception as e:
        logger.error(f"Log stats query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/streaming/metrics")
async def get_log_streaming_metrics(_: str = Depends(verify_admin_api_key)):
    """Get log streaming service metrics. Requires admin API key."""
    log_streaming_service = get_log_streaming_service()
    if log_streaming_service is None:
        raise HTTPException(
            status_code=503,
            detail="Log streaming service not available",
        )

    return log_streaming_service.get_metrics()


@router.get("/logs/cleanup/status")
async def get_log_cleanup_status(_: str = Depends(verify_admin_api_key)):
    """Get log cleanup job status. Requires admin API key."""
    log_cleanup_job = get_log_cleanup_job()
    if log_cleanup_job is None:
        raise HTTPException(
            status_code=503,
            detail="Log cleanup job not available",
        )

    return log_cleanup_job.get_status()


@router.post("/logs/cleanup/run")
async def trigger_log_cleanup(_: str = Depends(verify_admin_api_key)):
    """Manually trigger log cleanup. Requires admin API key."""
    log_cleanup_job = get_log_cleanup_job()
    if log_cleanup_job is None:
        raise HTTPException(
            status_code=503,
            detail="Log cleanup job not available",
        )

    result = await log_cleanup_job.run_cleanup()
    return result
