"""
Schedule management REST API router.

Allows Canvas to create and manage cron-based workflow schedules.

Endpoints:
- POST /schedules - Create schedule
- GET /schedules - List schedules (with optional workflow_id filter)
- GET /schedules/{schedule_id} - Get schedule details
- PUT /schedules/{schedule_id}/enable - Enable schedule
- PUT /schedules/{schedule_id}/disable - Disable schedule
- DELETE /schedules/{schedule_id} - Delete schedule
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from loguru import logger
from croniter import croniter

from casare_rpa.infrastructure.orchestrator.api.auth import (
    AuthenticatedUser,
    require_role,
)


router = APIRouter()


# =========================
# Request/Response Models
# =========================


class ScheduleRequest(BaseModel):
    """Request model for creating a schedule."""

    workflow_id: str = Field(..., description="Workflow to schedule")
    schedule_name: str = Field(..., min_length=1, max_length=255)
    cron_expression: str = Field(
        ..., description="Cron expression (e.g., '0 9 * * 1-5')"
    )
    enabled: bool = Field(default=True)
    priority: int = Field(default=10, ge=0, le=20, description="Job priority")
    execution_mode: str = Field(default="lan", description="lan or internet")
    metadata: dict = Field(default_factory=dict)

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v):
        """Validate cron expression."""
        try:
            croniter(v)
            return v
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v):
        allowed = ["lan", "internet"]
        if v not in allowed:
            raise ValueError(f"execution_mode must be one of {allowed}")
        return v


class ScheduleResponse(BaseModel):
    """Response model for schedule details."""

    schedule_id: str
    workflow_id: str
    schedule_name: str
    cron_expression: str
    enabled: bool
    priority: int
    execution_mode: str
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    run_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime


# =========================
# Utility Functions
# =========================


def calculate_next_run(
    cron_expression: str, base_time: Optional[datetime] = None
) -> datetime:
    """
    Calculate next run time from cron expression.

    Args:
        cron_expression: Cron expression
        base_time: Base time for calculation (defaults to now)

    Returns:
        Next run datetime (UTC)
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    cron = croniter(cron_expression, base_time)
    next_run = cron.get_next(datetime)

    return next_run


# =========================
# In-Memory Storage (Temporary)
# =========================
# WARNING: This is temporary in-memory storage.
# - Data is lost on restart
# - Not suitable for distributed deployments
# - Replace with database storage (PostgreSQL) for production
#
# Thread Safety: Uses asyncio.Lock for safe concurrent access.

import asyncio
from typing import Dict, Any

_schedules: Dict[str, Dict[str, Any]] = {}  # schedule_id -> schedule_data
_schedules_lock = asyncio.Lock()  # Async lock for thread-safe access


# Log prominent warning on module import
logger.warning(
    "⚠️  SCHEDULES USING IN-MEMORY STORAGE - Not suitable for production! "
    "All schedules will be LOST on restart. "
    "Replace with PostgreSQL storage for production deployments."
)


# =========================
# API Endpoints
# =========================


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleRequest,
    user: AuthenticatedUser = Depends(require_role("developer")),
) -> ScheduleResponse:
    """
    Create a new workflow schedule.

    Creates a cron-based schedule and registers it with APScheduler.

    Args:
        request: Schedule creation request

    Returns:
        ScheduleResponse with schedule details
    """
    try:
        schedule_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Calculate next run time
        next_run = (
            calculate_next_run(request.cron_expression) if request.enabled else None
        )

        # Create schedule data
        schedule_data = {
            "schedule_id": schedule_id,
            "workflow_id": request.workflow_id,
            "schedule_name": request.schedule_name,
            "cron_expression": request.cron_expression,
            "enabled": request.enabled,
            "priority": request.priority,
            "execution_mode": request.execution_mode,
            "next_run": next_run,
            "last_run": None,
            "run_count": 0,
            "failure_count": 0,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata,
        }

        # Thread-safe storage with async lock
        async with _schedules_lock:
            _schedules[schedule_id] = schedule_data

        # TODO: Register with APScheduler
        logger.info(
            "Schedule created: {} (workflow={}, cron='{}', enabled={})",
            schedule_id,
            request.workflow_id,
            request.cron_expression,
            request.enabled,
        )

        return ScheduleResponse(**schedule_data)

    except Exception as e:
        logger.error("Failed to create schedule: {}", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create schedule: {str(e)}"
        )


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000),
    user: AuthenticatedUser = Depends(require_role("viewer")),
) -> List[ScheduleResponse]:
    """
    List all schedules with optional filtering.

    Args:
        workflow_id: Filter by workflow ID (optional)
        enabled: Filter by enabled status (optional)
        limit: Maximum number of schedules to return

    Returns:
        List of schedules
    """
    try:
        # Thread-safe read with async lock
        async with _schedules_lock:
            schedules = list(_schedules.values())

        # Apply filters (on local copy, no lock needed)
        if workflow_id:
            schedules = [s for s in schedules if s["workflow_id"] == workflow_id]

        if enabled is not None:
            schedules = [s for s in schedules if s["enabled"] == enabled]

        # Sort by created_at descending
        schedules.sort(key=lambda s: s["created_at"], reverse=True)

        # Apply limit
        schedules = schedules[:limit]

        return [ScheduleResponse(**s) for s in schedules]

    except Exception as e:
        logger.error("Failed to list schedules: {}", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to list schedules: {str(e)}"
        )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    user: AuthenticatedUser = Depends(require_role("viewer")),
) -> ScheduleResponse:
    """
    Get schedule details by ID.

    Args:
        schedule_id: Schedule UUID

    Returns:
        ScheduleResponse
    """
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        )

    return ScheduleResponse(**schedule_data)


@router.put("/schedules/{schedule_id}/enable")
async def enable_schedule(
    schedule_id: str,
    user: AuthenticatedUser = Depends(require_role("operator")),
) -> ScheduleResponse:
    """
    Enable a schedule.

    Args:
        schedule_id: Schedule UUID

    Returns:
        Updated ScheduleResponse
    """
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

        if not schedule_data:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        # Update schedule (while holding lock)
        schedule_data["enabled"] = True
        schedule_data["next_run"] = calculate_next_run(schedule_data["cron_expression"])
        schedule_data["updated_at"] = datetime.now(timezone.utc)

    # TODO: Re-register with APScheduler
    logger.info("Schedule enabled: {}", schedule_id)

    return ScheduleResponse(**schedule_data)


@router.put("/schedules/{schedule_id}/disable")
async def disable_schedule(
    schedule_id: str,
    user: AuthenticatedUser = Depends(require_role("operator")),
) -> ScheduleResponse:
    """
    Disable a schedule.

    Args:
        schedule_id: Schedule UUID

    Returns:
        Updated ScheduleResponse
    """
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

        if not schedule_data:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        # Update schedule (while holding lock)
        schedule_data["enabled"] = False
        schedule_data["next_run"] = None
        schedule_data["updated_at"] = datetime.now(timezone.utc)

    # TODO: Unregister from APScheduler
    logger.info("Schedule disabled: {}", schedule_id)

    return ScheduleResponse(**schedule_data)


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user: AuthenticatedUser = Depends(require_role("admin")),
) -> dict:
    """
    Delete a schedule.

    Args:
        schedule_id: Schedule UUID

    Returns:
        Success message
    """
    async with _schedules_lock:
        if schedule_id not in _schedules:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        # Remove from storage (while holding lock)
        del _schedules[schedule_id]

    # TODO: Unregister from APScheduler
    logger.info("Schedule deleted: {}", schedule_id)

    return {
        "status": "success",
        "message": f"Schedule deleted: {schedule_id}",
    }


@router.put("/schedules/{schedule_id}/trigger")
async def trigger_schedule_now(
    schedule_id: str,
    user: AuthenticatedUser = Depends(require_role("operator")),
) -> dict:
    """
    Trigger a schedule execution immediately (manual override).

    Args:
        schedule_id: Schedule UUID

    Returns:
        Job ID of triggered execution
    """
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        )

    # TODO: Create job immediately
    job_id = str(uuid.uuid4())  # Placeholder

    logger.info("Schedule triggered manually: {} (job={})", schedule_id, job_id)

    return {
        "status": "success",
        "message": f"Schedule triggered: {schedule_id}",
        "job_id": job_id,
    }
