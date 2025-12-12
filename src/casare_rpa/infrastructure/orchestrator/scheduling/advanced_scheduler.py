"""
Advanced Scheduler for CasareRPA Orchestrator.

Enterprise scheduling features including:
- Cron expressions with human-readable aliases
- Dependency-based scheduling (DAG execution)
- Sliding window rate limiting
- Conditional scheduling
- SLA monitoring and alerting
- Catch-up execution for missed runs
- Timezone-aware scheduling

This module orchestrates the scheduling components:
- scheduling_strategies: Cron parsing and scheduling strategies
- schedule_optimizer: Rate limiting and execution optimization
- schedule_conflict_resolver: Dependency tracking and conflict resolution
- sla_monitor: SLA monitoring and alerting
- schedule_models: Data classes and enums for schedules
"""

import asyncio
import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from loguru import logger

# Import extracted modules
from casare_rpa.infrastructure.orchestrator.scheduling.scheduling_strategies import (
    CRON_ALIASES,
    CronExpressionParser,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_optimizer import (
    RateLimitConfig,
    SlidingWindowRateLimiter,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_conflict_resolver import (
    DependencyConfig,
    DependencyTracker,
    DependencyGraphValidator,
)
from casare_rpa.infrastructure.orchestrator.scheduling.sla_monitor import (
    SLAConfig,
    SLAMonitor,
    SLAStatus,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_models import (
    AdvancedSchedule,
    CatchUpConfig,
    ConditionalConfig,
    EventTriggerConfig,
    EventType,
    ScheduleStatus,
    ScheduleType,
)

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
    logger.warning("APScheduler not installed. Advanced scheduling features disabled.")

from casare_rpa.infrastructure.orchestrator.scheduling.calendar import BusinessCalendar


# Re-export commonly used classes from extracted modules
__all__ = [
    # Enums (from schedule_models)
    "ScheduleType",
    "ScheduleStatus",
    "EventType",
    # Configs (re-exported)
    "SLAConfig",
    "RateLimitConfig",
    "DependencyConfig",
    "ConditionalConfig",
    "CatchUpConfig",
    "EventTriggerConfig",
    # Data classes (from schedule_models)
    "AdvancedSchedule",
    # Components (re-exported)
    "CronExpressionParser",
    "SlidingWindowRateLimiter",
    "DependencyTracker",
    "SLAMonitor",
    "SLAStatus",
    # Main scheduler
    "AdvancedScheduler",
    # Constants
    "CRON_ALIASES",
]


class AdvancedScheduler:
    """
    Enterprise-grade scheduler with advanced features.

    Orchestrates scheduling components:
    - CronExpressionParser for cron handling
    - SlidingWindowRateLimiter for rate limiting
    - DependencyTracker for DAG scheduling
    - SLAMonitor for SLA compliance

    Features:
    - Multiple schedule types (cron, interval, event, dependency, one-time)
    - Business calendar integration
    - SLA monitoring and alerting
    - Rate limiting (sliding window)
    - Dependency-based scheduling (DAG)
    - Conditional execution
    - Catch-up for missed runs
    - Timezone-aware scheduling
    """

    def __init__(
        self,
        on_schedule_trigger: Optional[Callable[[AdvancedSchedule], Any]] = None,
        default_timezone: str = "UTC",
    ):
        """
        Initialize advanced scheduler.

        Args:
            on_schedule_trigger: Callback when schedule triggers
            default_timezone: Default timezone for schedules
        """
        if not HAS_APSCHEDULER:
            raise ImportError(
                "APScheduler is required for advanced scheduling. "
                "Install with: pip install apscheduler"
            )

        self._on_trigger = on_schedule_trigger
        self._default_tz = default_timezone
        self._schedules: Dict[str, AdvancedSchedule] = {}
        self._calendars: Dict[str, BusinessCalendar] = {}
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

        # Use extracted components
        self._rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._dependency_tracker = DependencyTracker()
        self._sla_monitor = SLAMonitor()
        self._graph_validator = DependencyGraphValidator()

        self._lock = threading.Lock()

        logger.info("AdvancedScheduler initialized")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    @property
    def sla_monitor(self) -> SLAMonitor:
        """Get SLA monitor instance."""
        return self._sla_monitor

    @property
    def dependency_tracker(self) -> DependencyTracker:
        """Get dependency tracker instance."""
        return self._dependency_tracker

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": False,
            "max_instances": 3,
            "misfire_grace_time": 300,
        }

        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self._default_tz,
        )

        self._scheduler.start()
        self._running = True

        logger.info("AdvancedScheduler started")

    async def stop(self, wait: bool = True) -> None:
        """
        Stop the scheduler.

        Args:
            wait: Whether to wait for running jobs to complete
        """
        if not self._running:
            return

        if self._scheduler:
            self._scheduler.shutdown(wait=wait)
            self._scheduler = None

        self._running = False
        logger.info("AdvancedScheduler stopped")

    def register_calendar(self, calendar_id: str, calendar: BusinessCalendar) -> None:
        """
        Register a business calendar.

        Args:
            calendar_id: Unique identifier for calendar
            calendar: BusinessCalendar instance
        """
        self._calendars[calendar_id] = calendar
        logger.debug(f"Registered calendar: {calendar_id}")

    def get_calendar(self, calendar_id: str) -> Optional[BusinessCalendar]:
        """Get a registered calendar."""
        return self._calendars.get(calendar_id)

    def add_schedule(self, schedule: AdvancedSchedule) -> bool:
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
            logger.debug(f"Schedule {schedule.id} is disabled, storing only")
            self._schedules[schedule.id] = schedule
            return True

        try:
            trigger = self._create_trigger(schedule)
            if trigger is None and schedule.schedule_type not in (
                ScheduleType.EVENT,
                ScheduleType.DEPENDENCY,
            ):
                logger.error(f"Failed to create trigger for schedule {schedule.id}")
                return False

            # Setup rate limiter if configured
            if schedule.rate_limit:
                self._rate_limiters[schedule.id] = SlidingWindowRateLimiter(
                    max_executions=schedule.rate_limit.max_executions,
                    window_seconds=schedule.rate_limit.window_seconds,
                )

            if trigger:
                self._scheduler.add_job(
                    func=self._execute_schedule,
                    trigger=trigger,
                    id=schedule.id,
                    args=[schedule.id],
                    name=schedule.name,
                    replace_existing=True,
                )

                job = self._scheduler.get_job(schedule.id)
                if job and job.next_run_time:
                    schedule.next_run = job.next_run_time

            self._schedules[schedule.id] = schedule

            logger.info(
                f"Schedule '{schedule.name}' added (type={schedule.schedule_type.value}), "
                f"next_run={schedule.next_run}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule.id}: {e}")
            return False

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a schedule.

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            True if removed successfully
        """
        try:
            if self._scheduler:
                try:
                    self._scheduler.remove_job(schedule_id)
                except Exception:
                    pass

            self._schedules.pop(schedule_id, None)
            self._rate_limiters.pop(schedule_id, None)

            logger.info(f"Schedule {schedule_id} removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove schedule {schedule_id}: {e}")
            return False

    def update_schedule(self, schedule: AdvancedSchedule) -> bool:
        """
        Update an existing schedule.

        Args:
            schedule: Updated schedule

        Returns:
            True if updated successfully
        """
        schedule.updated_at = datetime.now(timezone.utc)
        self.remove_schedule(schedule.id)
        return self.add_schedule(schedule)

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.status = ScheduleStatus.PAUSED
        if self._scheduler:
            try:
                self._scheduler.pause_job(schedule_id)
            except Exception:
                pass
        logger.info(f"Schedule {schedule_id} paused")
        return True

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.status = ScheduleStatus.ACTIVE
        if self._scheduler:
            try:
                self._scheduler.resume_job(schedule_id)
            except Exception:
                pass
        logger.info(f"Schedule {schedule_id} resumed")
        return True

    def get_schedule(self, schedule_id: str) -> Optional[AdvancedSchedule]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def get_all_schedules(self) -> List[AdvancedSchedule]:
        """Get all schedules."""
        return list(self._schedules.values())

    def get_schedules_by_status(self, status: ScheduleStatus) -> List[AdvancedSchedule]:
        """Get schedules with a specific status."""
        return [s for s in self._schedules.values() if s.status == status]

    def trigger_event(
        self,
        event_type: EventType,
        event_source: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Trigger event-driven schedules.

        Args:
            event_type: Type of event
            event_source: Source identifier
            event_data: Optional event payload

        Returns:
            List of triggered schedule IDs
        """
        triggered = []

        for schedule in self._schedules.values():
            if schedule.schedule_type != ScheduleType.EVENT:
                continue
            if not schedule.event_trigger:
                continue
            if schedule.event_trigger.event_type != event_type:
                continue
            if schedule.event_trigger.event_source != event_source:
                continue

            if schedule.event_trigger.event_filter and event_data:
                if not self._matches_filter(
                    event_data, schedule.event_trigger.event_filter
                ):
                    continue

            asyncio.create_task(self._execute_schedule(schedule.id, event_data))
            triggered.append(schedule.id)

        return triggered

    def notify_completion(
        self,
        schedule_id: str,
        success: bool,
        result: Any = None,
    ) -> None:
        """
        Notify completion of a schedule execution.

        Used for dependency tracking and triggering dependent schedules.

        Args:
            schedule_id: Completed schedule ID
            success: Whether execution succeeded
            result: Optional execution result
        """
        self._dependency_tracker.record_completion(schedule_id, success, result)

        # Check for dependent schedules to trigger
        for schedule in self._schedules.values():
            if schedule.schedule_type != ScheduleType.DEPENDENCY:
                continue
            if not schedule.dependency:
                continue
            if schedule_id not in schedule.dependency.depends_on:
                continue

            satisfied, _ = self._dependency_tracker.are_dependencies_satisfied(
                schedule.dependency.depends_on,
                schedule.dependency.wait_for_all,
                require_success=schedule.dependency.trigger_on_success_only,
            )

            if satisfied:
                asyncio.create_task(self._execute_schedule(schedule.id))

    def get_upcoming_runs(
        self,
        limit: int = 20,
        workflow_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming scheduled runs.

        Args:
            limit: Maximum runs to return
            workflow_id: Optional filter by workflow

        Returns:
            List of upcoming run info
        """
        if not self._scheduler:
            return []

        jobs = self._scheduler.get_jobs()
        upcoming = []

        for job in jobs:
            if not job.next_run_time:
                continue

            schedule = self._schedules.get(job.id)
            if not schedule:
                continue

            if workflow_id and schedule.workflow_id != workflow_id:
                continue

            upcoming.append(
                {
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "workflow_id": schedule.workflow_id,
                    "workflow_name": schedule.workflow_name,
                    "next_run": job.next_run_time,
                    "type": schedule.schedule_type.value,
                    "status": schedule.status.value,
                }
            )

        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming[:limit]

    def check_missed_runs(self) -> List[AdvancedSchedule]:
        """
        Check for schedules with missed runs that need catch-up.

        Returns:
            List of schedules needing catch-up
        """
        needs_catchup = []
        now = datetime.now(timezone.utc)

        for schedule in self._schedules.values():
            if not schedule.catch_up or not schedule.catch_up.enabled:
                continue
            if schedule.status != ScheduleStatus.ACTIVE:
                continue
            if not schedule.last_run:
                continue

            window_start = now - timedelta(
                hours=schedule.catch_up.catch_up_window_hours
            )
            if schedule.last_run < window_start:
                needs_catchup.append(schedule)

        return needs_catchup

    async def execute_catch_up(self, schedule_id: str) -> int:
        """
        Execute catch-up runs for a schedule.

        Args:
            schedule_id: Schedule ID to catch up

        Returns:
            Number of catch-up executions performed
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return 0
        if not schedule.catch_up or not schedule.catch_up.enabled:
            return 0

        max_runs = schedule.catch_up.max_catch_up_runs
        executed = 0

        for _ in range(max_runs):
            try:
                await self._execute_schedule(schedule_id, catch_up=True)
                executed += 1

                if schedule.catch_up.run_sequentially:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Catch-up execution failed for {schedule_id}: {e}")
                break

        logger.info(f"Executed {executed} catch-up runs for schedule {schedule_id}")
        return executed

    def _create_trigger(self, schedule: AdvancedSchedule):
        """Create APScheduler trigger from schedule configuration."""
        tz = ZoneInfo(schedule.timezone) if schedule.timezone else None

        if schedule.schedule_type == ScheduleType.ONE_TIME:
            if not schedule.run_at:
                return None
            run_time = schedule.run_at
            if isinstance(run_time, str):
                run_time = datetime.fromisoformat(run_time.replace("Z", "+00:00"))

            if schedule.respect_business_hours and schedule.calendar_id:
                calendar = self._calendars.get(schedule.calendar_id)
                if calendar:
                    run_time = calendar.adjust_to_working_time(
                        run_time, schedule.workflow_id
                    )

            return DateTrigger(run_date=run_time, timezone=tz)

        elif schedule.schedule_type == ScheduleType.CRON:
            if not schedule.cron_expression:
                return None
            try:
                cron_kwargs = CronExpressionParser.parse(schedule.cron_expression)
                return CronTrigger(**cron_kwargs, timezone=tz)
            except ValueError as e:
                logger.error(f"Invalid cron expression: {e}")
                return None

        elif schedule.schedule_type == ScheduleType.INTERVAL:
            if schedule.interval_seconds <= 0:
                return None
            return IntervalTrigger(seconds=schedule.interval_seconds, timezone=tz)

        elif schedule.schedule_type == ScheduleType.EVENT:
            return None

        elif schedule.schedule_type == ScheduleType.DEPENDENCY:
            return None

        return None

    async def _execute_schedule(
        self,
        schedule_id: str,
        event_data: Optional[Dict[str, Any]] = None,
        catch_up: bool = False,
    ) -> None:
        """
        Execute a scheduled job.

        Handles rate limiting, business hours, conditions, and SLA tracking.

        Args:
            schedule_id: Schedule ID to execute
            event_data: Optional event data for event-driven schedules
            catch_up: Whether this is a catch-up execution
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return

        if schedule.status != ScheduleStatus.ACTIVE:
            logger.debug(f"Schedule {schedule_id} not active, skipping")
            return

        # Check rate limiting
        rate_limiter = self._rate_limiters.get(schedule_id)
        if rate_limiter and not rate_limiter.can_execute(schedule_id):
            if schedule.rate_limit and schedule.rate_limit.queue_overflow:
                wait_time = rate_limiter.get_wait_time(schedule_id)
                logger.info(
                    f"Schedule {schedule_id} rate limited, queueing for {wait_time}s"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.warning(f"Schedule {schedule_id} rate limited, skipping")
                return

        # Check business hours
        if schedule.respect_business_hours and schedule.calendar_id:
            calendar = self._calendars.get(schedule.calendar_id)
            if calendar:
                now = datetime.now(ZoneInfo(schedule.timezone))
                can_exec, reason = calendar.can_execute(now, schedule.workflow_id)
                if not can_exec:
                    next_time = calendar.get_next_working_time(
                        now, schedule.workflow_id
                    )
                    logger.info(
                        f"Schedule {schedule_id} blocked: {reason}. "
                        f"Next working time: {next_time}"
                    )
                    return

        # Check conditional execution
        if schedule.conditional:
            condition_met = await self._check_condition(schedule)
            if not condition_met:
                if schedule.conditional.retry_on_condition_fail:
                    logger.info(f"Schedule {schedule_id} condition not met, will retry")
                else:
                    logger.info(f"Schedule {schedule_id} condition not met, skipping")
                return

        # Check dependencies
        if schedule.dependency and schedule.schedule_type != ScheduleType.DEPENDENCY:
            satisfied, unsatisfied = (
                self._dependency_tracker.are_dependencies_satisfied(
                    schedule.dependency.depends_on,
                    schedule.dependency.wait_for_all,
                    require_success=schedule.dependency.trigger_on_success_only,
                )
            )
            if not satisfied:
                logger.info(
                    f"Schedule {schedule_id} waiting for dependencies: {unsatisfied}"
                )
                return

        # Record execution for rate limiting
        if rate_limiter:
            rate_limiter.record_execution(schedule_id)

        # Start SLA tracking
        execution_id = self._sla_monitor.record_start(schedule_id, schedule.next_run)

        logger.info(
            f"Executing schedule '{schedule.name}' "
            f"(catch_up={catch_up}, type={schedule.schedule_type.value})"
        )

        schedule.last_run = datetime.now(timezone.utc)
        schedule.run_count += 1

        success = False
        try:
            if self._on_trigger:
                if event_data:
                    schedule.variables["_event_data"] = event_data
                result = self._on_trigger(schedule)
                if asyncio.iscoroutine(result):
                    await result
                success = True
                schedule.success_count += 1
                schedule.consecutive_failures = 0
        except Exception as e:
            logger.error(f"Schedule {schedule.name} execution failed: {e}")
            schedule.failure_count += 1
            schedule.consecutive_failures += 1

            if (
                schedule.sla
                and schedule.consecutive_failures
                >= schedule.sla.consecutive_failure_limit
            ):
                schedule.status = ScheduleStatus.ERROR
                logger.error(
                    f"Schedule {schedule_id} disabled due to {schedule.consecutive_failures} "
                    f"consecutive failures"
                )

        # Record SLA completion
        self._sla_monitor.record_completion(execution_id, success, schedule.sla)

        # Notify completion for dependency tracking
        self.notify_completion(schedule_id, success)

        # Update next run time
        if self._scheduler:
            job = self._scheduler.get_job(schedule_id)
            if job and job.next_run_time:
                schedule.next_run = job.next_run_time

    async def _check_condition(self, schedule: AdvancedSchedule) -> bool:
        """Check conditional execution criteria."""
        if not schedule.conditional:
            return True

        max_retries = schedule.conditional.max_condition_retries
        retry_interval = schedule.conditional.retry_interval_seconds

        for attempt in range(max_retries + 1):
            if schedule.conditional.condition_fn:
                try:
                    result = schedule.conditional.condition_fn()
                    if asyncio.iscoroutine(result):
                        result = await result
                    if result:
                        return True
                except Exception as e:
                    logger.warning(f"Condition check failed: {e}")

            if schedule.conditional.condition_expression:
                try:
                    # Use safe_eval instead of dangerous eval() to prevent RCE
                    from casare_rpa.utils.security.safe_eval import safe_eval

                    result = safe_eval(
                        schedule.conditional.condition_expression,
                        {"schedule": schedule},
                    )
                    if result:
                        return True
                except Exception as e:
                    logger.warning(f"Condition expression failed: {e}")

            if not schedule.conditional.retry_on_condition_fail:
                break

            if attempt < max_retries:
                await asyncio.sleep(retry_interval)

        return False

    def _matches_filter(
        self, event_data: Dict[str, Any], filter_spec: Dict[str, Any]
    ) -> bool:
        """Check if event data matches filter specification."""
        for key, expected in filter_spec.items():
            if key not in event_data:
                return False
            actual = event_data[key]

            if isinstance(expected, dict):
                if "$eq" in expected and actual != expected["$eq"]:
                    return False
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                if "$gt" in expected and not (actual > expected["$gt"]):
                    return False
                if "$lt" in expected and not (actual < expected["$lt"]):
                    return False
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$regex" in expected:
                    if not re.match(expected["$regex"], str(actual)):
                        return False
            elif actual != expected:
                return False

        return True

    def get_sla_report(
        self,
        schedule_id: Optional[str] = None,
        window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Generate SLA compliance report.

        Args:
            schedule_id: Optional specific schedule (None for all)
            window_hours: Time window for metrics

        Returns:
            SLA report dictionary
        """
        schedules = (
            [self._schedules[schedule_id]]
            if schedule_id and schedule_id in self._schedules
            else list(self._schedules.values())
        )

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_hours": window_hours,
            "schedules": [],
        }

        for schedule in schedules:
            if not schedule.sla:
                continue

            success_rate = self._sla_monitor.get_success_rate(schedule.id, window_hours)
            avg_duration = self._sla_monitor.get_average_duration(
                schedule.id, window_hours
            )

            schedule_report = {
                "schedule_id": schedule.id,
                "schedule_name": schedule.name,
                "status": schedule.sla_status.value,
                "success_rate": round(success_rate, 2),
                "success_rate_threshold": schedule.sla.success_rate_threshold,
                "average_duration_ms": avg_duration,
                "max_duration_ms": (
                    schedule.sla.max_duration_seconds * 1000
                    if schedule.sla.max_duration_seconds
                    else None
                ),
                "consecutive_failures": schedule.consecutive_failures,
                "consecutive_failure_limit": schedule.sla.consecutive_failure_limit,
                "run_count": schedule.run_count,
            }

            report["schedules"].append(schedule_report)

        return report

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get dependency graph of all schedules.

        Returns:
            Dictionary mapping schedule ID to list of dependent schedule IDs
        """
        graph: Dict[str, List[str]] = {}

        for schedule in self._schedules.values():
            if schedule.dependency and schedule.dependency.depends_on:
                for dep_id in schedule.dependency.depends_on:
                    if dep_id not in graph:
                        graph[dep_id] = []
                    graph[dep_id].append(schedule.id)

        return graph

    def validate_dependency_graph(self) -> Tuple[bool, List[str]]:
        """
        Validate dependency graph for cycles.

        Returns:
            Tuple of (is_valid, cycle_path)
        """
        # Build graph from current schedules
        graph = {}
        for schedule in self._schedules.values():
            if schedule.dependency:
                graph[schedule.id] = schedule.dependency.depends_on
            else:
                graph[schedule.id] = []

        self._graph_validator.set_graph(graph)
        return self._graph_validator.validate()
