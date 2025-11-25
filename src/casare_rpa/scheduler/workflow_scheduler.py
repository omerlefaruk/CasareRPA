"""
Workflow Scheduler Service for CasareRPA.
Executes workflows at scheduled times.
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from loguru import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed. Install with: pip install apscheduler")


class ScheduleStatus(Enum):
    """Status of a scheduled execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScheduleExecutionResult:
    """Result of a scheduled workflow execution."""
    schedule_id: str
    schedule_name: str
    workflow_path: str
    workflow_name: str
    status: ScheduleStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    success: bool = False
    error_message: str = ""
    output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "schedule_name": self.schedule_name,
            "workflow_path": self.workflow_path,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "output": self.output
        }


@dataclass
class SchedulerConfig:
    """Configuration for the workflow scheduler."""
    check_interval_seconds: int = 60
    max_concurrent_executions: int = 3
    execution_timeout_seconds: int = 3600  # 1 hour
    retry_failed: bool = False
    retry_delay_seconds: int = 300  # 5 minutes
    max_retries: int = 3
    log_executions: bool = True


class WorkflowSchedulerService:
    """
    Service for scheduling and executing workflows.

    Features:
    - Cron-based scheduling
    - Interval-based scheduling (hourly, daily, weekly, monthly)
    - One-time scheduled executions
    - Concurrent execution management
    - Execution history tracking
    - Retry logic for failed executions
    """

    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        on_execution_start: Optional[Callable] = None,
        on_execution_complete: Optional[Callable] = None,
        on_execution_error: Optional[Callable] = None
    ):
        """
        Initialize the scheduler service.

        Args:
            config: Scheduler configuration
            on_execution_start: Callback when execution starts
            on_execution_complete: Callback when execution completes
            on_execution_error: Callback when execution fails
        """
        self._config = config or SchedulerConfig()
        self._on_execution_start = on_execution_start
        self._on_execution_complete = on_execution_complete
        self._on_execution_error = on_execution_error

        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_semaphore = asyncio.Semaphore(
            self._config.max_concurrent_executions
        )

        # Schedule storage reference
        self._schedule_storage = None

    async def start(self) -> bool:
        """
        Start the scheduler service.

        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return True

        if not HAS_APSCHEDULER:
            logger.error("APScheduler is required for scheduling")
            return False

        try:
            # Initialize APScheduler
            jobstores = {"default": MemoryJobStore()}
            executors = {"default": AsyncIOExecutor()}
            job_defaults = {
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutes grace period
            }

            self._scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults
            )

            # Start scheduler
            self._scheduler.start()
            self._running = True

            # Load and register all schedules
            await self._load_schedules()

            # Start the schedule check loop
            asyncio.create_task(self._check_schedules_loop())

            logger.info("Workflow scheduler service started")
            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False

    async def stop(self) -> None:
        """Stop the scheduler service."""
        if not self._running:
            return

        self._running = False

        # Cancel active executions
        for schedule_id, task in self._active_executions.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled execution for schedule {schedule_id}")

        # Shutdown APScheduler
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

        logger.info("Workflow scheduler service stopped")

    async def _load_schedules(self) -> None:
        """Load schedules from storage and register them."""
        try:
            from ..canvas.schedule_storage import get_schedule_storage

            self._schedule_storage = get_schedule_storage()
            schedules = self._schedule_storage.get_enabled_schedules()

            for schedule in schedules:
                self._register_schedule(schedule)

            logger.info(f"Loaded {len(schedules)} enabled schedules")

        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")

    def _register_schedule(self, schedule) -> bool:
        """
        Register a schedule with APScheduler.

        Args:
            schedule: WorkflowSchedule object

        Returns:
            True if registered successfully
        """
        if not self._scheduler or not schedule.enabled:
            return False

        try:
            # Remove existing job if any
            try:
                self._scheduler.remove_job(schedule.id)
            except Exception:
                pass

            # Create appropriate trigger
            trigger = self._create_trigger(schedule)
            if not trigger:
                logger.warning(f"Could not create trigger for schedule {schedule.id}")
                return False

            # Add job
            self._scheduler.add_job(
                func=self._execute_schedule,
                trigger=trigger,
                id=schedule.id,
                args=[schedule.id],
                name=schedule.name,
                replace_existing=True
            )

            logger.debug(f"Registered schedule: {schedule.name} ({schedule.frequency})")
            return True

        except Exception as e:
            logger.error(f"Failed to register schedule {schedule.id}: {e}")
            return False

    def _create_trigger(self, schedule):
        """Create APScheduler trigger from schedule."""
        from ..canvas.schedule_dialog import ScheduleFrequency

        if schedule.frequency == ScheduleFrequency.ONCE:
            if not schedule.next_run:
                return None
            return DateTrigger(run_date=schedule.next_run)

        elif schedule.frequency == ScheduleFrequency.HOURLY:
            return IntervalTrigger(hours=1)

        elif schedule.frequency == ScheduleFrequency.DAILY:
            return CronTrigger(
                hour=schedule.time_hour,
                minute=schedule.time_minute
            )

        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            # day_of_week: 0=Monday, 6=Sunday
            day_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            return CronTrigger(
                day_of_week=day_map[schedule.day_of_week],
                hour=schedule.time_hour,
                minute=schedule.time_minute
            )

        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            return CronTrigger(
                day=schedule.day_of_month,
                hour=schedule.time_hour,
                minute=schedule.time_minute
            )

        elif schedule.frequency == ScheduleFrequency.CRON:
            if not schedule.cron_expression:
                return None
            parts = schedule.cron_expression.split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            elif len(parts) == 6:
                return CronTrigger(
                    second=parts[0],
                    minute=parts[1],
                    hour=parts[2],
                    day=parts[3],
                    month=parts[4],
                    day_of_week=parts[5]
                )

        return None

    async def _check_schedules_loop(self) -> None:
        """Periodically check for due schedules."""
        while self._running:
            try:
                await self._check_due_schedules()
            except Exception as e:
                logger.error(f"Error checking schedules: {e}")

            await asyncio.sleep(self._config.check_interval_seconds)

    async def _check_due_schedules(self) -> None:
        """Check for and execute due schedules."""
        if not self._schedule_storage:
            return

        due_schedules = self._schedule_storage.get_due_schedules()

        for schedule in due_schedules:
            if schedule.id not in self._active_executions:
                # Start execution
                task = asyncio.create_task(
                    self._execute_schedule(schedule.id)
                )
                self._active_executions[schedule.id] = task

    async def _execute_schedule(self, schedule_id: str) -> None:
        """
        Execute a scheduled workflow.

        Args:
            schedule_id: ID of the schedule to execute
        """
        schedule = None
        result = None

        try:
            # Get schedule
            if not self._schedule_storage:
                from ..canvas.schedule_storage import get_schedule_storage
                self._schedule_storage = get_schedule_storage()

            schedule = self._schedule_storage.get_schedule(schedule_id)
            if not schedule:
                logger.error(f"Schedule not found: {schedule_id}")
                return

            # Acquire semaphore for concurrent execution limit
            async with self._execution_semaphore:
                logger.info(f"Executing schedule: {schedule.name}")

                started_at = datetime.now()
                result = ScheduleExecutionResult(
                    schedule_id=schedule_id,
                    schedule_name=schedule.name,
                    workflow_path=schedule.workflow_path,
                    workflow_name=schedule.workflow_name,
                    status=ScheduleStatus.RUNNING,
                    started_at=started_at
                )

                # Notify start
                if self._on_execution_start:
                    try:
                        self._on_execution_start(result)
                    except Exception:
                        pass

                # Check workflow exists
                workflow_path = Path(schedule.workflow_path)
                if not workflow_path.exists():
                    raise FileNotFoundError(
                        f"Workflow file not found: {workflow_path}"
                    )

                # Load and execute workflow
                success, error = await self._run_workflow(workflow_path)

                # Calculate duration
                completed_at = datetime.now()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                # Update result
                result.status = ScheduleStatus.COMPLETED if success else ScheduleStatus.FAILED
                result.completed_at = completed_at
                result.duration_ms = duration_ms
                result.success = success
                result.error_message = error or ""

                # Update schedule stats
                self._schedule_storage.mark_schedule_run(
                    schedule_id,
                    success=success,
                    error_message=error or ""
                )

                # Notify completion
                if success:
                    logger.info(
                        f"Schedule completed: {schedule.name} "
                        f"(duration: {duration_ms}ms)"
                    )
                    if self._on_execution_complete:
                        try:
                            self._on_execution_complete(result)
                        except Exception:
                            pass
                else:
                    logger.error(
                        f"Schedule failed: {schedule.name} - {error}"
                    )
                    if self._on_execution_error:
                        try:
                            self._on_execution_error(result)
                        except Exception:
                            pass

                # Log to history
                if self._config.log_executions:
                    await self._log_execution(result)

        except asyncio.CancelledError:
            logger.info(f"Schedule execution cancelled: {schedule_id}")
            if result:
                result.status = ScheduleStatus.SKIPPED
                result.error_message = "Execution cancelled"

        except Exception as e:
            logger.error(f"Schedule execution error: {e}")
            if result:
                result.status = ScheduleStatus.FAILED
                result.completed_at = datetime.now()
                result.error_message = str(e)

                if self._on_execution_error:
                    try:
                        self._on_execution_error(result)
                    except Exception:
                        pass

                if self._config.log_executions:
                    await self._log_execution(result)

        finally:
            # Remove from active executions
            self._active_executions.pop(schedule_id, None)

    async def _run_workflow(self, workflow_path: Path) -> tuple:
        """
        Run a workflow file.

        Args:
            workflow_path: Path to workflow JSON file

        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        try:
            # Import runner
            from ..runner.workflow_runner import WorkflowRunner
            from ..utils.workflow_loader import load_workflow_from_file
            from ..core.events import EventBus

            # Load workflow
            workflow = load_workflow_from_file(workflow_path)
            if not workflow:
                return False, f"Failed to load workflow: {workflow_path}"

            # Create runner
            event_bus = EventBus()
            runner = WorkflowRunner(workflow, event_bus)

            # Execute with timeout
            try:
                success = await asyncio.wait_for(
                    runner.run(),
                    timeout=self._config.execution_timeout_seconds
                )
                return success, None if success else "Workflow execution failed"

            except asyncio.TimeoutError:
                runner.stop()
                return False, "Workflow execution timed out"

        except Exception as e:
            return False, str(e)

    async def _log_execution(self, result: ScheduleExecutionResult) -> None:
        """Log execution to history."""
        try:
            from .execution_history import get_execution_history
            history = get_execution_history()
            history.add_entry(result)
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    def add_schedule(self, schedule) -> bool:
        """
        Add a new schedule dynamically.

        Args:
            schedule: WorkflowSchedule object

        Returns:
            True if added successfully
        """
        if self._schedule_storage:
            self._schedule_storage.save_schedule(schedule)
        return self._register_schedule(schedule)

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a schedule.

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            True if removed successfully
        """
        if self._scheduler:
            try:
                self._scheduler.remove_job(schedule_id)
            except Exception:
                pass

        if self._schedule_storage:
            return self._schedule_storage.delete_schedule(schedule_id)

        return True

    def update_schedule(self, schedule) -> bool:
        """
        Update an existing schedule.

        Args:
            schedule: Updated WorkflowSchedule object

        Returns:
            True if updated successfully
        """
        if self._schedule_storage:
            self._schedule_storage.save_schedule(schedule)
        return self._register_schedule(schedule)

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        if self._scheduler:
            try:
                self._scheduler.pause_job(schedule_id)
                return True
            except Exception as e:
                logger.error(f"Failed to pause schedule {schedule_id}: {e}")
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule."""
        if self._scheduler:
            try:
                self._scheduler.resume_job(schedule_id)
                return True
            except Exception as e:
                logger.error(f"Failed to resume schedule {schedule_id}: {e}")
        return False

    def get_next_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get upcoming scheduled runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of upcoming run info
        """
        if not self._scheduler:
            return []

        upcoming = []
        jobs = self._scheduler.get_jobs()

        for job in jobs:
            if job.next_run_time and len(upcoming) < limit:
                upcoming.append({
                    "schedule_id": job.id,
                    "schedule_name": job.name,
                    "next_run": job.next_run_time.isoformat()
                })

        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming[:limit]

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    @property
    def active_execution_count(self) -> int:
        """Get number of currently running executions."""
        return len(self._active_executions)


# Singleton instance
_scheduler_instance: Optional[WorkflowSchedulerService] = None


def get_scheduler_service() -> WorkflowSchedulerService:
    """Get the global scheduler service instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkflowSchedulerService()
    return _scheduler_instance


async def start_scheduler_service(config: Optional[SchedulerConfig] = None) -> bool:
    """
    Start the global scheduler service.

    Args:
        config: Optional scheduler configuration

    Returns:
        True if started successfully
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkflowSchedulerService(config=config)
    return await _scheduler_instance.start()


async def stop_scheduler_service() -> None:
    """Stop the global scheduler service."""
    global _scheduler_instance
    if _scheduler_instance:
        await _scheduler_instance.stop()
