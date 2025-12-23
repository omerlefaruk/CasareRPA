"""REST API endpoints for job management.

Provides:
- Admin/user operations: cancel, retry
- Robot operations (internet-safe): claim, complete, fail, release
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from loguru import logger
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from casare_rpa.infrastructure.orchestrator.api.auth import verify_robot_token


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Module-level database pool reference
_db_pool = None


def set_db_pool(pool) -> None:
    """Set database pool for this router."""
    global _db_pool
    _db_pool = pool
    logger.debug("Database pool set for jobs router")


def get_db_pool():
    """Get database pool."""
    return _db_pool


# ==================== PYDANTIC MODELS ====================


class JobCancelResponse(BaseModel):
    """Response for job cancellation."""

    job_id: str
    cancelled: bool
    previous_status: str
    message: str


class JobRetryResponse(BaseModel):
    """Response for job retry."""

    original_job_id: str
    new_job_id: str
    message: str


class JobProgressUpdate(BaseModel):
    """Request model for progress update."""

    progress: int = Field(..., ge=0, le=100)
    current_node: Optional[str] = None
    message: Optional[str] = None


class JobClaimRequest(BaseModel):
    """Request for robots to claim a job."""

    environment: str = Field(default="default", max_length=64)
    limit: int = Field(default=1, ge=1, le=10)
    visibility_timeout_seconds: int = Field(default=30, ge=5, le=3600)


class JobClaimResponse(BaseModel):
    """Response payload for claimed job."""

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: Dict[str, Any]
    created_at: datetime
    claimed_at: datetime
    retry_count: int
    max_retries: int


class JobCompleteRequest(BaseModel):
    """Request body for completing a job."""

    result: Dict[str, Any] = Field(default_factory=dict)


class JobFailRequest(BaseModel):
    """Request body for failing a job."""

    error_message: str = Field(..., min_length=1, max_length=5000)


class JobExtendLeaseRequest(BaseModel):
    """Request body for extending job visibility lease."""

    extension_seconds: int = Field(default=30, ge=5, le=3600)


# ==================== ENDPOINTS ====================


@router.post(
    "/jobs/claim",
    response_model=Optional[JobClaimResponse],
    dependencies=[Depends(verify_robot_token)],
)
@limiter.limit("120/minute")
async def claim_job(
    request: Request,
    payload: JobClaimRequest,
    robot_id: str = Depends(verify_robot_token),
):
    """Claim the next available job for an authenticated robot.

    This endpoint allows robots to run without direct database access.
    It uses SKIP LOCKED semantics in a single UPDATE statement.
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE job_queue
                SET status = 'running',
                    robot_id = $3,
                    started_at = NOW(),
                    visible_after = NOW() + INTERVAL '1 second' * $4
                WHERE id IN (
                    SELECT id
                    FROM job_queue
                    WHERE status = 'pending'
                      AND visible_after <= NOW()
                      AND (environment = $1 OR environment = 'default' OR $1 = 'default')
                    ORDER BY priority DESC, created_at ASC
                    LIMIT $2
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id,
                          workflow_id,
                          workflow_name,
                          workflow_json,
                          priority,
                          environment,
                          variables,
                          created_at,
                          retry_count,
                          max_retries,
                          started_at;
                """,
                payload.environment,
                payload.limit,
                robot_id,
                payload.visibility_timeout_seconds,
            )

            if row is None:
                return None

            return JobClaimResponse(
                job_id=str(row["id"]),
                workflow_id=str(row.get("workflow_id") or ""),
                workflow_name=str(row.get("workflow_name") or ""),
                workflow_json=str(row.get("workflow_json") or ""),
                priority=int(row.get("priority") or 0),
                environment=str(row.get("environment") or "default"),
                variables=row.get("variables") or {},
                created_at=row.get("created_at") or datetime.utcnow(),
                claimed_at=row.get("started_at") or datetime.utcnow(),
                retry_count=int(row.get("retry_count") or 0),
                max_retries=int(row.get("max_retries") or 0),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to claim job for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to claim job: {e}")


@router.post(
    "/jobs/{job_id}/complete",
    dependencies=[Depends(verify_robot_token)],
)
@limiter.limit("120/minute")
async def complete_job(
    request: Request,
    payload: JobCompleteRequest,
    job_id: str = Path(..., min_length=1, max_length=64),
    robot_id: str = Depends(verify_robot_token),
):
    """Mark a running job as completed (robot-authenticated)."""
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        import orjson

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE job_queue
                SET status = 'completed',
                    completed_at = NOW(),
                    result = $2::jsonb
                WHERE id = $1::uuid
                  AND status = 'running'
                  AND robot_id = $3
                RETURNING id;
                """,
                job_id,
                orjson.dumps(payload.result).decode(),
                robot_id,
            )

            if row is None:
                raise HTTPException(
                    status_code=409,
                    detail="Job not running for this robot (already finished or claimed elsewhere)",
                )

            return {"job_id": job_id, "completed": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete job {job_id} for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete job: {e}")


@router.post(
    "/jobs/{job_id}/fail",
    dependencies=[Depends(verify_robot_token)],
)
@limiter.limit("120/minute")
async def fail_job(
    request: Request,
    payload: JobFailRequest,
    job_id: str = Path(..., min_length=1, max_length=64),
    robot_id: str = Depends(verify_robot_token),
):
    """Mark a running job as failed (robot-authenticated).

    If retry_count < max_retries, the job is returned to pending.
    Otherwise, it becomes failed.
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE job_queue
                SET status = CASE
                        WHEN retry_count < max_retries THEN 'pending'
                        ELSE 'failed'
                    END,
                    error_message = $2,
                    retry_count = retry_count + 1,
                    robot_id = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE robot_id
                    END,
                    visible_after = CASE
                        WHEN retry_count < max_retries THEN NOW() + INTERVAL '5 seconds'
                        ELSE visible_after
                    END
                WHERE id = $1::uuid
                  AND status = 'running'
                  AND robot_id = $3
                RETURNING id, status;
                """,
                job_id,
                payload.error_message,
                robot_id,
            )

            if row is None:
                raise HTTPException(
                    status_code=409,
                    detail="Job not running for this robot (already finished or claimed elsewhere)",
                )

            return {"job_id": job_id, "status": row["status"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fail job {job_id} for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fail job: {e}")


@router.post(
    "/jobs/{job_id}/release",
    dependencies=[Depends(verify_robot_token)],
)
@limiter.limit("120/minute")
async def release_job(
    request: Request,
    job_id: str = Path(..., min_length=1, max_length=64),
    robot_id: str = Depends(verify_robot_token),
):
    """Release a running job back to pending (robot-authenticated)."""
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE job_queue
                SET status = 'pending',
                    robot_id = NULL,
                    started_at = NULL,
                    visible_after = NOW()
                WHERE id = $1::uuid
                  AND status = 'running'
                  AND robot_id = $2
                RETURNING id;
                """,
                job_id,
                robot_id,
            )

            if row is None:
<<<<<<< HEAD
                raise HTTPException(
                    status_code=409, detail="Job not running for this robot"
                )
=======
                raise HTTPException(status_code=409, detail="Job not running for this robot")
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

            return {"job_id": job_id, "released": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to release job {job_id} for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to release job: {e}")


@router.post(
    "/jobs/{job_id}/extend-lease",
    dependencies=[Depends(verify_robot_token)],
)
@limiter.limit("240/minute")
async def extend_job_lease(
    request: Request,
    payload: JobExtendLeaseRequest,
    job_id: str = Path(..., min_length=1, max_length=64),
    robot_id: str = Depends(verify_robot_token),
):
    """Extend the visibility lease for a running job (robot-authenticated)."""
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE job_queue
                SET visible_after = NOW() + INTERVAL '1 second' * $2
                WHERE id = $1::uuid
                  AND status = 'running'
                  AND robot_id = $3
                RETURNING id;
                """,
                job_id,
                payload.extension_seconds,
                robot_id,
            )

            if row is None:
                raise HTTPException(
                    status_code=409,
                    detail="Job not running for this robot (already finished or claimed elsewhere)",
                )

            return {"job_id": job_id, "extended": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend lease for job {job_id} (robot {robot_id}): {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extend lease: {e}")


@router.post("/jobs/{job_id}/cancel", response_model=JobCancelResponse)
@limiter.limit("60/minute")
async def cancel_job(
    request: Request,
    job_id: str = Path(..., min_length=1, max_length=64),
):
    """
    Cancel a pending or running job.

    Jobs that are already completed, failed, or cancelled cannot be cancelled.

    Rate Limit: 60 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Get current job status
            row = await conn.fetchrow(
                "SELECT job_id, status FROM jobs WHERE job_id = $1",
                job_id,
            )

            if row is None:
                # Also check job_queue table
                row = await conn.fetchrow(
                    "SELECT id as job_id, status FROM job_queue WHERE id = $1",
                    job_id,
                )

            if row is None:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

            previous_status = row["status"]

            # Check if job can be cancelled
            if previous_status in ("completed", "failed", "cancelled"):
                return JobCancelResponse(
                    job_id=job_id,
                    cancelled=False,
                    previous_status=previous_status,
                    message=f"Job already {previous_status}, cannot cancel",
                )

            # Update job status to cancelled
            now = datetime.utcnow()

            # Try jobs table first
            result = await conn.execute(
                """
                UPDATE jobs
                SET status = 'cancelled',
                    completed_at = $2,
                    error_message = 'Cancelled by user',
                    updated_at = NOW()
                WHERE job_id = $1
                AND status NOT IN ('completed', 'failed', 'cancelled')
                """,
                job_id,
                now,
            )

            if result == "UPDATE 0":
                # Try job_queue table
                await conn.execute(
                    """
                    UPDATE job_queue
                    SET status = 'cancelled'
                    WHERE id = $1
                    AND status NOT IN ('completed', 'failed', 'cancelled')
                    """,
                    job_id,
                )

            logger.info(f"Cancelled job: {job_id} (was {previous_status})")

            return JobCancelResponse(
                job_id=job_id,
                cancelled=True,
                previous_status=previous_status,
                message="Job cancelled successfully",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {e}")


@router.post("/jobs/{job_id}/retry", response_model=JobRetryResponse)
@limiter.limit("30/minute")
async def retry_job(
    request: Request,
    job_id: str = Path(..., min_length=1, max_length=64),
):
    """
    Retry a failed or cancelled job.

    Creates a new job with the same workflow and parameters.
    Only failed, cancelled, or timeout jobs can be retried.

    Rate Limit: 30 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Get original job
            row = await conn.fetchrow(
                """
                SELECT job_id, workflow_id, workflow_name, payload, environment,
                       priority, robot_uuid, status
                FROM jobs WHERE job_id = $1
                """,
                job_id,
            )

            if row is None:
                # Try job_queue table
                row = await conn.fetchrow(
                    """
                    SELECT id as job_id, workflow_id, workflow_json as payload,
                           environment, priority, status
                    FROM job_queue WHERE id = $1
                    """,
                    job_id,
                )

            if row is None:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

            status = row["status"]

            # Check if job can be retried
            if status not in ("failed", "cancelled", "timeout"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot retry job with status '{status}'. Only failed, cancelled, or timeout jobs can be retried.",
                )

            # Create new job
            new_job_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Insert into jobs table
            await conn.execute(
                """
                INSERT INTO jobs (
                    job_id, workflow_id, workflow_name, payload, environment,
                    priority, robot_uuid, status, created_at, progress
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, 'pending', $8, 0
                )
                """,
                new_job_id,
                row.get("workflow_id"),
                row.get("workflow_name", ""),
                row.get("payload"),
                row.get("environment", "default"),
                row.get("priority", 1),
                row.get("robot_uuid"),
                now,
            )

            # Also enqueue to job_queue if using PgQueuer
            try:
                await conn.execute(
                    """
                    INSERT INTO job_queue (
                        id, workflow_id, workflow_json, environment, priority, status
                    ) VALUES (
                        $1, $2, $3, $4, $5, 'pending'
                    )
                    """,
                    new_job_id,
                    row.get("workflow_id"),
                    row.get("payload"),
                    row.get("environment", "default"),
                    row.get("priority", 1),
                )
            except Exception:
                # job_queue table might not exist or have different schema
                pass

            logger.info(f"Retried job {job_id} as new job {new_job_id}")

            return JobRetryResponse(
                original_job_id=job_id,
                new_job_id=new_job_id,
                message="Job queued for retry",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry job: {e}")


@router.put("/jobs/{job_id}/progress")
@limiter.limit("600/minute")
async def update_job_progress(
    request: Request,
    job_id: str = Path(..., min_length=1, max_length=64),
    update: JobProgressUpdate = ...,
):
    """
    Update job execution progress.

    Used by robot agents to report progress during execution.

    Rate Limit: 600 requests/minute per IP (very high for progress updates)
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE jobs
                SET progress = $2,
                    current_node = COALESCE($3, current_node),
                    updated_at = NOW()
                WHERE job_id = $1
                AND status = 'running'
                """,
                job_id,
                update.progress,
                update.current_node,
            )

            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=404,
                    detail=f"Job {job_id} not found or not running",
                )

            return {
                "job_id": job_id,
                "progress": update.progress,
                "current_node": update.current_node,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update progress for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {e}")
