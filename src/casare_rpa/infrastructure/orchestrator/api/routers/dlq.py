"""
REST API endpoints for Dead Letter Queue management.

Provides operations for DLQ inspection, retry, and cleanup.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query, Request
from loguru import logger
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from casare_rpa.infrastructure.orchestrator.server_lifecycle import get_dlq_manager


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ==================== PYDANTIC MODELS ====================


class DLQEntryResponse(BaseModel):
    """Response model for a DLQ entry."""

    id: str
    original_job_id: str
    workflow_id: str
    workflow_name: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int
    first_failed_at: datetime
    last_failed_at: datetime
    created_at: datetime
    reprocessed_at: Optional[datetime] = None
    reprocessed_by: Optional[str] = None


class DLQListResponse(BaseModel):
    """Response model for listing DLQ entries."""

    entries: List[DLQEntryResponse]
    total: int
    pending: int
    limit: int
    offset: int


class DLQRetryResponse(BaseModel):
    """Response model for DLQ retry."""

    dlq_entry_id: str
    new_job_id: str
    message: str


class DLQDeleteResponse(BaseModel):
    """Response model for DLQ deletion."""

    dlq_entry_id: str
    deleted: bool
    message: str


class DLQStatsResponse(BaseModel):
    """Response model for DLQ statistics."""

    total: int
    pending: int
    reprocessed: int
    workflow_id: Optional[str] = None


class DLQPurgeResponse(BaseModel):
    """Response model for DLQ purge operation."""

    purged_count: int
    older_than_days: int
    message: str


# ==================== ENDPOINTS ====================


@router.get("/dlq", response_model=DLQListResponse)
@limiter.limit("60/minute")
async def list_dlq_entries(
    request: Request,
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    pending_only: bool = Query(
        True, description="Only show entries not yet reprocessed"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List entries in the Dead Letter Queue.

    Returns failed jobs that have exceeded their retry limits.

    Rate Limit: 60 requests/minute per IP
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        entries = await dlq_manager.list_dlq_entries(
            workflow_id=workflow_id,
            pending_only=pending_only,
            limit=limit,
            offset=offset,
        )
        stats = await dlq_manager.get_dlq_stats(workflow_id=workflow_id)

        return DLQListResponse(
            entries=[
                DLQEntryResponse(
                    id=e.id,
                    original_job_id=e.original_job_id,
                    workflow_id=e.workflow_id,
                    workflow_name=e.workflow_name,
                    error_message=e.error_message,
                    error_details=e.error_details,
                    retry_count=e.retry_count,
                    first_failed_at=e.first_failed_at,
                    last_failed_at=e.last_failed_at,
                    created_at=e.created_at,
                    reprocessed_at=e.reprocessed_at,
                    reprocessed_by=e.reprocessed_by,
                )
                for e in entries
            ],
            total=stats["total"],
            pending=stats["pending"],
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list DLQ entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list DLQ entries: {e}")


@router.get("/dlq/stats", response_model=DLQStatsResponse)
@limiter.limit("120/minute")
async def get_dlq_stats(
    request: Request,
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
):
    """
    Get Dead Letter Queue statistics.

    Rate Limit: 120 requests/minute per IP
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        stats = await dlq_manager.get_dlq_stats(workflow_id=workflow_id)

        return DLQStatsResponse(
            total=stats["total"],
            pending=stats["pending"],
            reprocessed=stats["total"] - stats["pending"],
            workflow_id=workflow_id,
        )

    except Exception as e:
        logger.error(f"Failed to get DLQ stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get DLQ stats: {e}")


@router.get("/dlq/{entry_id}", response_model=DLQEntryResponse)
@limiter.limit("120/minute")
async def get_dlq_entry(
    request: Request,
    entry_id: str = Path(
        ..., min_length=1, max_length=64, description="DLQ entry UUID"
    ),
):
    """
    Get a specific DLQ entry by ID.

    Rate Limit: 120 requests/minute per IP
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        entry = await dlq_manager.get_dlq_entry(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail=f"DLQ entry {entry_id} not found",
            )

        return DLQEntryResponse(
            id=entry.id,
            original_job_id=entry.original_job_id,
            workflow_id=entry.workflow_id,
            workflow_name=entry.workflow_name,
            error_message=entry.error_message,
            error_details=entry.error_details,
            retry_count=entry.retry_count,
            first_failed_at=entry.first_failed_at,
            last_failed_at=entry.last_failed_at,
            created_at=entry.created_at,
            reprocessed_at=entry.reprocessed_at,
            reprocessed_by=entry.reprocessed_by,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get DLQ entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get DLQ entry: {e}")


@router.post("/dlq/{entry_id}/retry", response_model=DLQRetryResponse)
@limiter.limit("30/minute")
async def retry_dlq_entry(
    request: Request,
    entry_id: str = Path(
        ..., min_length=1, max_length=64, description="DLQ entry UUID"
    ),
    reprocessed_by: str = Query(
        "api", description="Identifier of who initiated the retry"
    ),
):
    """
    Retry a job from the Dead Letter Queue.

    Creates a new job in the main queue with reset retry count.
    Marks the DLQ entry as reprocessed.

    Rate Limit: 30 requests/minute per IP
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        new_job_id = await dlq_manager.retry_from_dlq(
            entry_id=entry_id,
            reprocessed_by=reprocessed_by,
        )

        if new_job_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"DLQ entry {entry_id} not found or already reprocessed",
            )

        logger.info(
            f"DLQ entry {entry_id} retried as job {new_job_id} by {reprocessed_by}"
        )

        return DLQRetryResponse(
            dlq_entry_id=entry_id,
            new_job_id=new_job_id,
            message="Job queued for retry from DLQ",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry DLQ entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry from DLQ: {e}")


@router.delete("/dlq/{entry_id}", response_model=DLQDeleteResponse)
@limiter.limit("30/minute")
async def delete_dlq_entry(
    request: Request,
    entry_id: str = Path(
        ..., min_length=1, max_length=64, description="DLQ entry UUID"
    ),
):
    """
    Delete a DLQ entry permanently.

    This action cannot be undone. The failed job data will be lost.

    Rate Limit: 30 requests/minute per IP
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        deleted = await dlq_manager.delete_dlq_entry(entry_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"DLQ entry {entry_id} not found",
            )

        logger.info(f"DLQ entry {entry_id} deleted via API")

        return DLQDeleteResponse(
            dlq_entry_id=entry_id,
            deleted=True,
            message="DLQ entry deleted",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete DLQ entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete DLQ entry: {e}")


@router.post("/dlq/purge", response_model=DLQPurgeResponse)
@limiter.limit("5/minute")
async def purge_dlq(
    request: Request,
    older_than_days: int = Query(
        30, ge=1, le=365, description="Purge entries older than this many days"
    ),
):
    """
    Purge old reprocessed DLQ entries.

    Only deletes entries that have been reprocessed (retried).
    Pending entries are not affected.

    Rate Limit: 5 requests/minute per IP (destructive operation)
    """
    dlq_manager = get_dlq_manager()
    if dlq_manager is None:
        raise HTTPException(
            status_code=503,
            detail="DLQ service not available. Database may not be configured.",
        )

    try:
        purged_count = await dlq_manager.purge_reprocessed(
            older_than_days=older_than_days
        )

        logger.info(
            f"Purged {purged_count} DLQ entries older than {older_than_days} days"
        )

        return DLQPurgeResponse(
            purged_count=purged_count,
            older_than_days=older_than_days,
            message=f"Purged {purged_count} reprocessed entries older than {older_than_days} days",
        )

    except Exception as e:
        logger.error(f"Failed to purge DLQ entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to purge DLQ: {e}")
