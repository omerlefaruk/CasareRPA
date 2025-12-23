"""
Schedule management REST API router.

Allows Canvas to create and manage cron-based workflow schedules.
Integrates with APScheduler via the AdvancedScheduler for actual job scheduling.

Endpoints:
- POST /schedules - Create schedule
- GET /schedules - List schedules (with optional workflow_id filter)
- GET /schedules/{schedule_id} - Get schedule details
- PUT /schedules/{schedule_id}/enable - Enable schedule
- PUT /schedules/{schedule_id}/disable - Disable schedule
- DELETE /schedules/{schedule_id} - Delete schedule
- PUT /schedules/{schedule_id}/trigger - Trigger schedule immediately
"""

import asyncio
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from casare_rpa.infrastructure.orchestrator.api.auth import (
    AuthenticatedUser,
    get_current_user,
)
from casare_rpa.infrastructure.orchestrator.scheduling import (
    AdvancedSchedule,
    ScheduleStatus,
    ScheduleType,
    get_global_scheduler,
    is_scheduler_initialized,
)

try:
    import asyncpg
except ImportError:
    asyncpg = None

router = APIRouter()

# UUID validation pattern (prevents path traversal and injection)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_uuid_format(value: str, field_name: str = "ID") -> str:
    """
    Validate that a string is a valid UUID format.

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
# Database Pool Management
# =========================

_db_pool = None


def set_db_pool(pool) -> None:
    """Set the database pool for schedule operations."""
    global _db_pool
    _db_pool = pool
    if pool:
        logger.info("Schedules router: Database pool set (PostgreSQL storage ready)")


def get_db_pool():
    """Get the database pool."""
    return _db_pool


# =========================
# Request/Response Models
# =========================


class ScheduleRequest(BaseModel):
    """Request model for creating a schedule."""

    workflow_id: str = Field(..., description="Workflow to schedule")
    schedule_name: str = Field(..., min_length=1, max_length=255)
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 9 * * 1-5')")
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
    next_run: datetime | None
    last_run: datetime | None
    run_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime


# =========================
# Utility Functions
# =========================


def calculate_next_run(cron_expression: str, base_time: datetime | None = None) -> datetime:
    """
    Calculate next run time from cron expression.

    Args:
        cron_expression: Cron expression
        base_time: Base time for calculation (defaults to now)

    Returns:
        Next run datetime (UTC)
    """
    if base_time is None:
        base_time = datetime.now(UTC)

    cron = croniter(cron_expression, base_time)
    next_run = cron.get_next(datetime)

    return next_run


async def _execute_scheduled_workflow(schedule: AdvancedSchedule) -> None:
    """
    Callback function that executes when a schedule triggers.

    This is called by the AdvancedScheduler when a job fires.
    Submits a job to the orchestrator for execution on a robot.

    Args:
        schedule: The schedule that triggered
    """
    logger.info(
        "Scheduled workflow execution triggered: workflow_id={}, schedule_name={}",
        schedule.workflow_id,
        schedule.name,
    )

    job_id = f"scheduled_{schedule.id}_{uuid.uuid4().hex[:8]}"

    try:
        # Import dependencies for job submission
        from casare_rpa.application.orchestrator.services.dispatcher_service import (
            JobDispatcher,
        )
        from casare_rpa.application.orchestrator.use_cases import SubmitJobUseCase
        from casare_rpa.domain.orchestrator.entities.job import JobPriority
        from casare_rpa.domain.orchestrator.services.robot_selection_service import (
            RobotSelectionService,
        )
        from casare_rpa.infrastructure.persistence.repositories import (
            JobRepository,
            NodeOverrideRepository,
            RobotRepository,
            WorkflowAssignmentRepository,
        )

        # Get workflow data from schedule metadata or storage
        workflow_data = await _get_workflow_data(schedule)
        if not workflow_data:
            logger.error(
                "Cannot execute scheduled workflow: workflow data not found for {}",
                schedule.workflow_id,
            )
            return

        # Initialize repositories
        job_repo = JobRepository()
        robot_repo = RobotRepository()
        assignment_repo = WorkflowAssignmentRepository()
        override_repo = NodeOverrideRepository()
        robot_selection = RobotSelectionService()
        dispatcher = JobDispatcher()

        # Create and execute the SubmitJobUseCase
        submit_use_case = SubmitJobUseCase(
            job_repository=job_repo,
            robot_repository=robot_repo,
            assignment_repository=assignment_repo,
            override_repository=override_repo,
            robot_selection_service=robot_selection,
            dispatcher=dispatcher,
        )

        # Map schedule priority (0-20) to JobPriority enum
        priority = JobPriority.NORMAL
        if schedule.priority >= 15:
            priority = JobPriority.CRITICAL
        elif schedule.priority >= 10:
            priority = JobPriority.HIGH
        elif schedule.priority <= 5:
            priority = JobPriority.LOW

        # Submit the job
        job = await submit_use_case.execute(
            workflow_id=schedule.workflow_id,
            workflow_data=workflow_data,
            robot_id=schedule.robot_id,
            priority=priority,
            variables=schedule.variables or {},
            workflow_name=schedule.workflow_name or schedule.name,
            created_by=f"scheduler:{schedule.id}",
        )

        logger.info(
            "Scheduled job submitted successfully: job_id={}, workflow_id={}, robot_id={}",
            job.id,
            schedule.workflow_id,
            job.robot_id,
        )

        # Publish event for monitoring
        try:
            from casare_rpa.infrastructure.events import (
                MonitoringEventType,
                get_monitoring_event_bus,
            )

            event_bus = get_monitoring_event_bus()
            await event_bus.publish(
                MonitoringEventType.JOB_STATUS_CHANGED,
                {
                    "job_id": job.id,
                    "workflow_id": schedule.workflow_id,
                    "status": job.status.value,
                    "source": "scheduler",
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "triggered_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as event_error:
            logger.warning("Failed to publish job event: {}", event_error)

    except ImportError as import_error:
        # Dependencies not available - log and publish fallback event
        logger.warning(
            "Job submission dependencies not available ({}), publishing event only",
            import_error,
        )
        await _publish_fallback_job_event(job_id, schedule)

    except Exception as e:
        logger.error(
            "Failed to submit scheduled job for workflow {}: {}",
            schedule.workflow_id,
            e,
        )
        # Publish failure event
        try:
            from casare_rpa.infrastructure.events import (
                MonitoringEventType,
                get_monitoring_event_bus,
            )

            event_bus = get_monitoring_event_bus()
            await event_bus.publish(
                MonitoringEventType.JOB_STATUS_CHANGED,
                {
                    "job_id": job_id,
                    "workflow_id": schedule.workflow_id,
                    "status": "failed",
                    "source": "scheduler",
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "error": str(e),
                    "triggered_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as event_error:
            logger.warning("Failed to publish failure event: {}", event_error)


async def _get_workflow_data(schedule: AdvancedSchedule) -> dict[str, Any] | None:
    """
    Retrieve workflow data for scheduled execution.

    Tries to get workflow data from:
    1. Schedule metadata (workflow_json field)
    2. Database workflow storage
    3. File-based project storage

    Args:
        schedule: The schedule containing workflow reference

    Returns:
        Workflow data dictionary or None if not found
    """
    # Check if workflow data is embedded in schedule metadata
    if schedule.metadata:
        workflow_json = schedule.metadata.get("workflow_json")
        if workflow_json:
            if isinstance(workflow_json, str):
                import orjson

                try:
                    return orjson.loads(workflow_json)
                except Exception:
                    pass
            elif isinstance(workflow_json, dict):
                return workflow_json

        # Check for workflow_data key
        workflow_data = schedule.metadata.get("workflow_data")
        if isinstance(workflow_data, dict):
            return workflow_data

    # Try to load from database if pool is available
    if _db_pool is not None:
        try:
            async with _db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT workflow_json, metadata FROM workflows
                    WHERE workflow_id = $1
                    """,
                    schedule.workflow_id,
                )
                if row:
                    import orjson

                    workflow_json = row.get("workflow_json")
                    if workflow_json:
                        if isinstance(workflow_json, str):
                            return orjson.loads(workflow_json)
                        return workflow_json
        except Exception as db_error:
            logger.debug("Could not load workflow from database: {}", db_error)

    # Fallback: Create minimal workflow data structure
    # This allows the job to be created even if full workflow data is unavailable
    # The robot will need to fetch the full workflow when executing
    return {
        "workflow_id": schedule.workflow_id,
        "name": schedule.workflow_name or schedule.name,
        "nodes": {},
        "connections": [],
        "variables": schedule.variables or {},
        "metadata": {
            "scheduled": True,
            "schedule_id": schedule.id,
            "schedule_name": schedule.name,
        },
    }


async def _publish_fallback_job_event(job_id: str, schedule: AdvancedSchedule) -> None:
    """
    Publish a fallback job event when full job submission is not available.

    This ensures monitoring systems are notified even if the orchestrator
    components are not fully initialized.

    Args:
        job_id: Generated job ID
        schedule: The schedule that triggered
    """
    try:
        from casare_rpa.infrastructure.events import (
            MonitoringEventType,
            get_monitoring_event_bus,
        )

        event_bus = get_monitoring_event_bus()
        await event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {
                "job_id": job_id,
                "workflow_id": schedule.workflow_id,
                "status": "pending",
                "source": "scheduler",
                "schedule_id": schedule.id,
                "schedule_name": schedule.name,
                "triggered_at": datetime.now(UTC).isoformat(),
                "fallback": True,
            },
        )
        logger.info(
            "Published fallback scheduled job event for workflow_id={}",
            schedule.workflow_id,
        )
    except Exception as e:
        logger.error("Failed to publish fallback job event: {}", e)


def _convert_to_advanced_schedule(
    schedule_id: str,
    request: ScheduleRequest,
    now: datetime,
    next_run: datetime | None,
) -> AdvancedSchedule:
    """
    Convert API request to AdvancedSchedule for APScheduler.

    Args:
        schedule_id: Unique schedule identifier
        request: Schedule creation request
        now: Current timestamp
        next_run: Calculated next run time

    Returns:
        AdvancedSchedule instance
    """
    return AdvancedSchedule(
        id=schedule_id,
        name=request.schedule_name,
        workflow_id=request.workflow_id,
        workflow_name=request.metadata.get("workflow_name", ""),
        schedule_type=ScheduleType.CRON,
        status=ScheduleStatus.ACTIVE if request.enabled else ScheduleStatus.PAUSED,
        enabled=request.enabled,
        cron_expression=request.cron_expression,
        priority=request.priority,
        metadata={
            "execution_mode": request.execution_mode,
            **request.metadata,
        },
        next_run=next_run,
        created_at=now,
        updated_at=now,
    )


def _schedule_to_response(schedule: AdvancedSchedule) -> dict[str, Any]:
    """
    Convert AdvancedSchedule to API response format.

    Args:
        schedule: AdvancedSchedule instance

    Returns:
        Dictionary matching ScheduleResponse schema
    """
    return {
        "schedule_id": schedule.id,
        "workflow_id": schedule.workflow_id,
        "schedule_name": schedule.name,
        "cron_expression": schedule.cron_expression,
        "enabled": schedule.enabled,
        "priority": schedule.priority,
        "execution_mode": schedule.metadata.get("execution_mode", "lan"),
        "next_run": schedule.next_run,
        "last_run": schedule.last_run,
        "run_count": schedule.run_count,
        "failure_count": schedule.failure_count,
        "created_at": schedule.created_at or datetime.now(UTC),
        "updated_at": schedule.updated_at or datetime.now(UTC),
    }


# =========================
# In-Memory Storage (Fallback)
# =========================
# Used when scheduler is not initialized or as backup storage.
# Thread-safe with asyncio.Lock.

_schedules: dict[str, dict[str, Any]] = {}
_schedules_lock = asyncio.Lock()


# =========================
# API Endpoints
# =========================


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ScheduleResponse:
    """
    Create a new workflow schedule.

    Creates a cron-based schedule and registers it with APScheduler.

    Args:
        request: Schedule creation request
        current_user: Authenticated user from JWT

    Returns:
        ScheduleResponse with schedule details
    """
    # Security: Validate workflow_id format
    validate_uuid_format(request.workflow_id, "workflow_id")
    try:
        schedule_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Calculate next run time
        next_run = calculate_next_run(request.cron_expression) if request.enabled else None

        # Try to register with APScheduler if available
        scheduler = get_global_scheduler()
        if scheduler is not None and is_scheduler_initialized():
            advanced_schedule = _convert_to_advanced_schedule(schedule_id, request, now, next_run)
            success = scheduler.add_schedule(advanced_schedule)
            if not success:
                logger.warning("Failed to add schedule to APScheduler, using in-memory only")

            # Get updated next_run from scheduler (may differ from calculated)
            registered_schedule = scheduler.get_schedule(schedule_id)
            if registered_schedule and registered_schedule.next_run:
                next_run = registered_schedule.next_run

            logger.info(
                "Schedule registered with APScheduler: {} (workflow={}, cron='{}', enabled={})",
                schedule_id,
                request.workflow_id,
                request.cron_expression,
                request.enabled,
            )
        else:
            logger.warning(
                "APScheduler not initialized, schedule stored in-memory only: {}",
                schedule_id,
            )

        # Create schedule data for storage/response
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

        # Thread-safe storage with async lock (backup)
        async with _schedules_lock:
            _schedules[schedule_id] = schedule_data

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
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    workflow_id: str | None = Query(None, description="Filter by workflow ID"),
    enabled: bool | None = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ScheduleResponse]:
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
        schedules: list[dict[str, Any]] = []

        # Get from APScheduler if available
        scheduler = get_global_scheduler()
        if scheduler is not None and is_scheduler_initialized():
            for schedule in scheduler.get_all_schedules():
                schedule_dict = _schedule_to_response(schedule)
                schedules.append(schedule_dict)
        else:
            # Fallback to in-memory storage
            async with _schedules_lock:
                schedules = list(_schedules.values())

        # Apply filters
        if workflow_id:
            schedules = [s for s in schedules if s["workflow_id"] == workflow_id]

        if enabled is not None:
            schedules = [s for s in schedules if s["enabled"] == enabled]

        # Sort by created_at descending
        schedules.sort(
            key=lambda s: s.get("created_at") or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

        # Apply limit
        schedules = schedules[:limit]

        return [ScheduleResponse(**s) for s in schedules]

    except Exception as e:
        logger.error("Failed to list schedules: {}", e)
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ScheduleResponse:
    """
    Get schedule details by ID.

    Args:
        schedule_id: Schedule UUID
        current_user: Authenticated user from JWT

    Returns:
        ScheduleResponse
    """
    # Security: Validate UUID format
    validate_uuid_format(schedule_id, "schedule_id")

    # Try APScheduler first
    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        schedule = scheduler.get_schedule(schedule_id)
        if schedule:
            return ScheduleResponse(**_schedule_to_response(schedule))

    # Fallback to in-memory
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    return ScheduleResponse(**schedule_data)


@router.put("/schedules/{schedule_id}/enable")
async def enable_schedule(
    schedule_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ScheduleResponse:
    """
    Enable a schedule.

    Resumes the job in APScheduler and updates the schedule status.

    Args:
        schedule_id: Schedule UUID
        current_user: Authenticated user from JWT

    Returns:
        Updated ScheduleResponse
    """
    # Security: Validate UUID format
    validate_uuid_format(schedule_id, "schedule_id")

    # Get schedule from in-memory storage first
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    # Resume in APScheduler if available
    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        success = scheduler.resume_schedule(schedule_id)
        if success:
            logger.info("Schedule resumed in APScheduler: {}", schedule_id)

            # Get updated schedule from scheduler
            advanced_schedule = scheduler.get_schedule(schedule_id)
            if advanced_schedule:
                schedule_data = _schedule_to_response(advanced_schedule)
                # Update in-memory storage
                async with _schedules_lock:
                    _schedules[schedule_id] = schedule_data
                return ScheduleResponse(**schedule_data)
        else:
            logger.warning(
                "Failed to resume schedule in APScheduler, updating in-memory only: {}",
                schedule_id,
            )

    # Update in-memory storage
    async with _schedules_lock:
        schedule_data["enabled"] = True
        schedule_data["next_run"] = calculate_next_run(schedule_data["cron_expression"])
        schedule_data["updated_at"] = datetime.now(UTC)

    logger.info("Schedule enabled: {}", schedule_id)
    return ScheduleResponse(**schedule_data)


@router.put("/schedules/{schedule_id}/disable")
async def disable_schedule(
    schedule_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ScheduleResponse:
    """
    Disable a schedule.

    Pauses the job in APScheduler and updates the schedule status.

    Args:
        schedule_id: Schedule UUID
        current_user: Authenticated user from JWT

    Returns:
        Updated ScheduleResponse
    """
    # Security: Validate UUID format
    validate_uuid_format(schedule_id, "schedule_id")

    # Get schedule from in-memory storage first
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    # Pause in APScheduler if available
    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        success = scheduler.pause_schedule(schedule_id)
        if success:
            logger.info("Schedule paused in APScheduler: {}", schedule_id)

            # Get updated schedule from scheduler
            advanced_schedule = scheduler.get_schedule(schedule_id)
            if advanced_schedule:
                schedule_data = _schedule_to_response(advanced_schedule)
                schedule_data["enabled"] = False
                schedule_data["next_run"] = None
                # Update in-memory storage
                async with _schedules_lock:
                    _schedules[schedule_id] = schedule_data
                return ScheduleResponse(**schedule_data)
        else:
            logger.warning(
                "Failed to pause schedule in APScheduler, updating in-memory only: {}",
                schedule_id,
            )

    # Update in-memory storage
    async with _schedules_lock:
        schedule_data["enabled"] = False
        schedule_data["next_run"] = None
        schedule_data["updated_at"] = datetime.now(UTC)

    logger.info("Schedule disabled: {}", schedule_id)
    return ScheduleResponse(**schedule_data)


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Delete a schedule.

    Removes the job from APScheduler and deletes from storage.

    Args:
        schedule_id: Schedule UUID
        current_user: Authenticated user from JWT

    Returns:
        Success message
    """
    # Security: Validate UUID format
    validate_uuid_format(schedule_id, "schedule_id")

    # Check if schedule exists
    async with _schedules_lock:
        if schedule_id not in _schedules:
            # Also check APScheduler
            scheduler = get_global_scheduler()
            if scheduler is None or not scheduler.get_schedule(schedule_id):
                raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    # Remove from APScheduler if available
    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        success = scheduler.remove_schedule(schedule_id)
        if success:
            logger.info("Schedule removed from APScheduler: {}", schedule_id)
        else:
            logger.warning("Failed to remove schedule from APScheduler: {}", schedule_id)

    # Remove from in-memory storage
    async with _schedules_lock:
        _schedules.pop(schedule_id, None)

    logger.info("Schedule deleted: {}", schedule_id)

    return {
        "status": "success",
        "message": f"Schedule deleted: {schedule_id}",
    }


@router.put("/schedules/{schedule_id}/trigger")
async def trigger_schedule_now(
    schedule_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Trigger a schedule execution immediately (manual override).

    Modifies the job's next_run_time to now for immediate execution.

    Args:
        schedule_id: Schedule UUID
        current_user: Authenticated user from JWT

    Returns:
        Job ID of triggered execution
    """
    # Security: Validate UUID format
    validate_uuid_format(schedule_id, "schedule_id")

    # Check if schedule exists
    async with _schedules_lock:
        schedule_data = _schedules.get(schedule_id)

    if not schedule_data:
        # Check APScheduler
        scheduler = get_global_scheduler()
        if scheduler is not None:
            advanced_schedule = scheduler.get_schedule(schedule_id)
            if advanced_schedule:
                schedule_data = _schedule_to_response(advanced_schedule)

    if not schedule_data:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    job_id = f"manual_{schedule_id}_{uuid.uuid4().hex[:8]}"

    # Try to trigger via APScheduler
    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        # Get the underlying APScheduler instance and modify job
        if scheduler._scheduler is not None:
            try:
                job = scheduler._scheduler.get_job(schedule_id)
                if job:
                    # Modify next run time to now for immediate execution
                    job.modify(next_run_time=datetime.now(UTC))
                    logger.info(
                        "Schedule triggered immediately via APScheduler: {} (job={})",
                        schedule_id,
                        job_id,
                    )
                    return {
                        "status": "success",
                        "message": f"Schedule triggered: {schedule_id}",
                        "job_id": job_id,
                        "triggered_via": "apscheduler",
                    }
            except Exception as e:
                logger.warning(
                    "Failed to trigger via APScheduler, using manual execution: {}",
                    e,
                )

        # Fallback: Create and execute an AdvancedSchedule directly
        advanced_schedule = scheduler.get_schedule(schedule_id)
        if advanced_schedule:
            # Execute the schedule callback directly
            asyncio.create_task(_execute_scheduled_workflow(advanced_schedule))
            logger.info(
                "Schedule triggered manually: {} (job={})",
                schedule_id,
                job_id,
            )
            return {
                "status": "success",
                "message": f"Schedule triggered: {schedule_id}",
                "job_id": job_id,
                "triggered_via": "direct",
            }

    # No scheduler available - create manual job event
    try:
        from casare_rpa.infrastructure.events import (
            MonitoringEventType,
            get_monitoring_event_bus,
        )

        event_bus = get_monitoring_event_bus()
        await event_bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {
                "job_id": job_id,
                "workflow_id": schedule_data["workflow_id"],
                "status": "pending",
                "source": "manual_trigger",
                "schedule_id": schedule_id,
                "schedule_name": schedule_data["schedule_name"],
                "triggered_at": datetime.now(UTC).isoformat(),
            },
        )
        logger.info("Schedule triggered manually: {} (job={})", schedule_id, job_id)
    except Exception as e:
        logger.error("Failed to publish manual trigger event: {}", e)

    return {
        "status": "success",
        "message": f"Schedule triggered: {schedule_id}",
        "job_id": job_id,
        "triggered_via": "event",
    }


@router.get("/schedules/upcoming", response_model=list[dict])
async def get_upcoming_schedules(
    limit: int = Query(20, ge=1, le=100),
    workflow_id: str | None = Query(None, description="Filter by workflow ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict]:
    """
    Get upcoming scheduled runs.

    Uses APScheduler to get actual next run times.

    Args:
        limit: Maximum number of runs to return
        workflow_id: Filter by workflow ID (optional)
        current_user: Authenticated user from JWT

    Returns:
        List of upcoming run info
    """
    # Security: Validate workflow_id format if provided
    if workflow_id:
        validate_uuid_format(workflow_id, "workflow_id")

    scheduler = get_global_scheduler()
    if scheduler is not None and is_scheduler_initialized():
        upcoming = scheduler.get_upcoming_runs(limit=limit, workflow_id=workflow_id)
        return upcoming

    # Fallback to in-memory calculation
    async with _schedules_lock:
        schedules = [s for s in _schedules.values() if s["enabled"]]

    if workflow_id:
        schedules = [s for s in schedules if s["workflow_id"] == workflow_id]

    upcoming = []
    for schedule in schedules:
        if schedule.get("next_run"):
            upcoming.append(
                {
                    "schedule_id": schedule["schedule_id"],
                    "schedule_name": schedule["schedule_name"],
                    "workflow_id": schedule["workflow_id"],
                    "workflow_name": schedule.get("metadata", {}).get("workflow_name", ""),
                    "next_run": schedule["next_run"],
                    "type": "cron",
                    "status": "active" if schedule["enabled"] else "paused",
                }
            )

    upcoming.sort(key=lambda x: x["next_run"])
    return upcoming[:limit]
