"""
REST API endpoints for job management.

Provides operations for job control: cancel, retry, status updates.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Request
from loguru import logger
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address


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


# ==================== ENDPOINTS ====================


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
