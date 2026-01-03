"""
Job Scheduler for CasareRPA Orchestrator.
Implements cron-based scheduling using APScheduler.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from loguru import logger

try:
    from apscheduler.executors.asyncio import AsyncIOExecutor
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed. Scheduling features disabled.")

from casare_rpa.domain.orchestrator.entities import Schedule, ScheduleFrequency


class ScheduleExecutionError(Exception):
    """Raised when a scheduled job fails to execute."""

    pass


def parse_cron_expression(cron_expr: str) -> dict[str, str]:
    """
    Parse cron expression into APScheduler trigger kwargs.

    Supports standard 5-field cron: minute hour day month weekday
    Also supports 6-field with seconds: second minute hour day month weekday

    Args:
        cron_expr: Cron expression string

    Returns:
        Dict with cron trigger parameters
    """
    parts = cron_expr.strip().split()

    if len(parts) == 5:
        # Standard 5-field: minute hour day month weekday
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }
    elif len(parts) == 6:
        # Extended 6-field: second minute hour day month weekday
        return {
            "second": parts[0],
            "minute": parts[1],
            "hour": parts[2],
            "day": parts[3],
            "month": parts[4],
            "day_of_week": parts[5],
        }
    else:
        raise ValueError(f"Invalid cron expression: {cron_expr}")


def frequency_to_interval(frequency: ScheduleFrequency) -> timedelta | None:
    """Convert schedule frequency to timedelta."""
    intervals = {
        ScheduleFrequency.HOURLY: timedelta(hours=1),
        ScheduleFrequency.DAILY: timedelta(days=1),
        ScheduleFrequency.WEEKLY: timedelta(weeks=1),
        ScheduleFrequency.MONTHLY: timedelta(days=30),  # Approximate
    }
    return intervals.get(frequency)


class JobScheduler:
    """
    Scheduler for automated job execution.

    Features:
    - Cron-based scheduling
    - Simple frequency scheduling (hourly, daily, weekly, monthly)
    - One-time scheduled jobs
    - Timezone support
    - Schedule enable/disable
    - Next run calculation
    """

    def __init__(
        self,
        on_schedule_trigger: Callable[[Schedule], Any] | None = None,
        tz_name: str = "UTC",
    ):
        """
        Initialize scheduler.

        Args:
            on_schedule_trigger: Callback when schedule triggers (async or sync)
            tz_name: Default timezone for schedules
        """
        if not HAS_APSCHEDULER:
            raise ImportError(
                "APScheduler is required for scheduling. Install with: pip install apscheduler"
            )

        self._default_timezone = tz_name
        self._on_schedule_trigger = on_schedule_trigger
        self._schedules: dict[str, Schedule] = {}
        self._scheduler: AsyncIOScheduler | None = None
        self._running = False

        logger.info("JobScheduler initialized")

    async def start(self):
        """Start the scheduler."""
        if self._running:
            return

        # Configure scheduler
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": True,  # Combine missed runs
            "max_instances": 1,  # Only one instance per schedule
            "misfire_grace_time": 60,  # Allow 1 minute late
        }

        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self._default_timezone,
        )

        self._scheduler.start()
        self._running = True
        logger.info("JobScheduler started")

    async def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

        self._running = False
        logger.info("JobScheduler stopped")

    def add_schedule(self, schedule: Schedule) -> bool:
        """
        Add a schedule to the scheduler.

        Args:
            schedule: Schedule to add

        Returns:
            True if added successfully
        """
        if not self._scheduler:
            logger.error("Scheduler not running")
            return False

        if not schedule.enabled:
            logger.debug(f"Schedule {schedule.id} is disabled, not adding")
            return True

        try:
            # Create trigger based on frequency
            trigger = self._create_trigger(schedule)
            if not trigger:
                return False

            # Add job to scheduler
            self._scheduler.add_job(
                func=self._execute_schedule,
                trigger=trigger,
                id=schedule.id,
                args=[schedule.id],
                name=schedule.name,
                replace_existing=True,
            )

            self._schedules[schedule.id] = schedule

            # Calculate next run
            next_run = self._scheduler.get_job(schedule.id)
            if next_run and next_run.next_run_time:
                schedule.next_run = next_run.next_run_time

            logger.info(f"Schedule '{schedule.name}' added, next run: {schedule.next_run}")
            return True

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule.id}: {e}")
            return False

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a schedule from the scheduler.

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            True if removed successfully
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.remove_job(schedule_id)
            self._schedules.pop(schedule_id, None)
            logger.info(f"Schedule {schedule_id} removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove schedule {schedule_id}: {e}")
            return False

    def update_schedule(self, schedule: Schedule) -> bool:
        """
        Update an existing schedule.

        Args:
            schedule: Updated schedule

        Returns:
            True if updated successfully
        """
        # Remove old and add new
        self.remove_schedule(schedule.id)
        return self.add_schedule(schedule)

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.enabled = True
        return self.add_schedule(schedule)

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.enabled = False
        return self.remove_schedule(schedule_id)

    def pause_all(self):
        """Pause all schedules."""
        if self._scheduler:
            self._scheduler.pause()
            logger.info("All schedules paused")

    def resume_all(self):
        """Resume all schedules."""
        if self._scheduler:
            self._scheduler.resume()
            logger.info("All schedules resumed")

    def get_next_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get upcoming scheduled runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of upcoming run info
        """
        if not self._scheduler:
            return []

        jobs = self._scheduler.get_jobs()
        upcoming = []

        for job in jobs:
            if job.next_run_time and len(upcoming) < limit:
                schedule = self._schedules.get(job.id)
                upcoming.append(
                    {
                        "schedule_id": job.id,
                        "schedule_name": schedule.name if schedule else job.name,
                        "workflow_name": schedule.workflow_name if schedule else "",
                        "next_run": job.next_run_time,
                    }
                )

        # Sort by next_run
        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming[:limit]

    def get_schedule_info(self, schedule_id: str) -> dict[str, Any] | None:
        """Get info about a specific schedule."""
        if not self._scheduler:
            return None

        job = self._scheduler.get_job(schedule_id)
        schedule = self._schedules.get(schedule_id)

        if not job or not schedule:
            return None

        return {
            "id": schedule.id,
            "name": schedule.name,
            "workflow_id": schedule.workflow_id,
            "workflow_name": schedule.workflow_name,
            "frequency": schedule.frequency.value,
            "cron_expression": schedule.cron_expression,
            "enabled": schedule.enabled,
            "next_run": job.next_run_time,
            "last_run": schedule.last_run,
            "run_count": schedule.run_count,
            "success_count": schedule.success_count,
        }

    def _create_trigger(self, schedule: Schedule):
        """Create APScheduler trigger from schedule."""
        tz = ZoneInfo(schedule.timezone) if schedule.timezone else None

        if schedule.frequency == ScheduleFrequency.ONCE:
            # One-time execution
            if not schedule.next_run:
                logger.error(f"ONCE schedule {schedule.id} has no next_run time")
                return None
            run_time = schedule.next_run
            if isinstance(run_time, str):
                run_time = datetime.fromisoformat(run_time.replace("Z", ""))
            return DateTrigger(run_date=run_time, timezone=tz)

        elif schedule.frequency == ScheduleFrequency.CRON:
            # Cron expression
            if not schedule.cron_expression:
                logger.error(f"CRON schedule {schedule.id} has no cron expression")
                return None
            try:
                cron_kwargs = parse_cron_expression(schedule.cron_expression)
                return CronTrigger(**cron_kwargs, timezone=tz)
            except ValueError as e:
                logger.error(f"Invalid cron expression for schedule {schedule.id}: {e}")
                return None

        else:
            # Interval-based (hourly, daily, weekly, monthly)
            interval = frequency_to_interval(schedule.frequency)
            if not interval:
                logger.error(f"Unknown frequency for schedule {schedule.id}")
                return None
            return IntervalTrigger(seconds=int(interval.total_seconds()), timezone=tz)

    async def _execute_schedule(self, schedule_id: str):
        """
        Execute a scheduled job.

        This is called by APScheduler when a schedule triggers.
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found during execution")
            return

        logger.info(f"Schedule '{schedule.name}' triggered")

        # Update last run
        schedule.last_run = datetime.now(UTC)
        schedule.run_count += 1

        # Call the trigger callback
        if self._on_schedule_trigger:
            try:
                result = self._on_schedule_trigger(schedule)
                if asyncio.iscoroutine(result):
                    await result
                schedule.success_count += 1
            except Exception as e:
                logger.error(f"Schedule {schedule.name} execution failed: {e}")

        # Update next run
        job = self._scheduler.get_job(schedule_id)
        if job and job.next_run_time:
            schedule.next_run = job.next_run_time


class ScheduleManager:
    """
    High-level schedule management.

    Combines scheduler with persistence and job creation.
    """

    def __init__(self, job_creator: Callable[[Schedule], Any], tz_name: str = "UTC"):
        """
        Initialize schedule manager.

        Args:
            job_creator: Function to create jobs from schedules
            tz_name: Default timezone
        """
        self._job_creator = job_creator
        self._scheduler = JobScheduler(on_schedule_trigger=self._on_trigger, tz_name=tz_name)
        self._schedules: dict[str, Schedule] = {}

    async def start(self):
        """Start the schedule manager."""
        await self._scheduler.start()

    async def stop(self):
        """Stop the schedule manager."""
        await self._scheduler.stop()

    def add_schedule(self, schedule: Schedule) -> bool:
        """Add a schedule."""
        self._schedules[schedule.id] = schedule
        return self._scheduler.add_schedule(schedule)

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule."""
        self._schedules.pop(schedule_id, None)
        return self._scheduler.remove_schedule(schedule_id)

    def update_schedule(self, schedule: Schedule) -> bool:
        """Update a schedule."""
        self._schedules[schedule.id] = schedule
        return self._scheduler.update_schedule(schedule)

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = True
        return self._scheduler.enable_schedule(schedule_id)

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = False
        return self._scheduler.disable_schedule(schedule_id)

    def get_schedule(self, schedule_id: str) -> Schedule | None:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def get_all_schedules(self) -> list[Schedule]:
        """Get all schedules."""
        return list(self._schedules.values())

    def get_upcoming_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get upcoming scheduled runs."""
        return self._scheduler.get_next_runs(limit)

    async def _on_trigger(self, schedule: Schedule):
        """Handle schedule trigger."""
        logger.info(f"Creating job for schedule '{schedule.name}'")
        try:
            result = self._job_creator(schedule)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Failed to create job for schedule {schedule.name}: {e}")
            raise


def get_next_run_time(
    frequency: ScheduleFrequency,
    cron_expression: str = "",
    tz_name: str = "UTC",
    from_time: datetime | None = None,
) -> datetime | None:
    """
    Calculate next run time for a schedule.

    Args:
        frequency: Schedule frequency
        cron_expression: Cron expression
        tz_name: Timezone name
        from_time: Base time (defaults to now)

    Returns:
        Next execution time or None
    """
    if from_time is None:
        from_time = datetime.now(UTC)

    # Ensure from_time has timezone
    if from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=UTC)

    if frequency == ScheduleFrequency.ONCE:
        return None

    try:
        ZoneInfo(tz_name)
    except Exception:
        pass
