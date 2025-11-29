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
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Tuple, Union
from zoneinfo import ZoneInfo
from collections import defaultdict
import asyncio
import threading
import uuid
import re

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
    logger.warning("APScheduler not installed. Advanced scheduling features disabled.")

from .calendar import BusinessCalendar, CalendarConfig


class ScheduleType(Enum):
    """Types of schedules."""

    INTERVAL = "interval"
    CRON = "cron"
    EVENT = "event"
    DEPENDENCY = "dependency"
    ONE_TIME = "one_time"


class ScheduleStatus(Enum):
    """Status of a schedule."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    COMPLETED = "completed"
    ERROR = "error"


class SLAStatus(Enum):
    """SLA compliance status."""

    OK = "ok"
    WARNING = "warning"
    BREACHED = "breached"
    UNKNOWN = "unknown"


class EventType(Enum):
    """Types of events for event-driven scheduling."""

    FILE_ARRIVAL = "file_arrival"
    WEBHOOK = "webhook"
    DATABASE_CHANGE = "database_change"
    QUEUE_MESSAGE = "queue_message"
    WORKFLOW_COMPLETED = "workflow_completed"
    CUSTOM = "custom"


CRON_ALIASES: Dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
    "@every_minute": "* * * * *",
    "@every_5_minutes": "*/5 * * * *",
    "@every_10_minutes": "*/10 * * * *",
    "@every_15_minutes": "*/15 * * * *",
    "@every_30_minutes": "*/30 * * * *",
    "@business_hours": "0 9-17 * * 1-5",
    "@weekdays": "0 9 * * 1-5",
    "@weekends": "0 9 * * 0,6",
    "@end_of_month": "0 0 L * *",
    "@first_monday": "0 0 * * 1#1",
    "@last_friday": "0 17 * * 5L",
}


@dataclass
class SLAConfig:
    """
    SLA configuration for a schedule.

    Attributes:
        max_duration_seconds: Maximum allowed execution duration
        max_start_delay_seconds: Maximum delay from scheduled time to start
        success_rate_threshold: Minimum success rate percentage (0-100)
        consecutive_failure_limit: Max consecutive failures before alerting
        on_breach: Callback function when SLA is breached
    """

    max_duration_seconds: Optional[int] = None
    max_start_delay_seconds: Optional[int] = 300
    success_rate_threshold: float = 95.0
    consecutive_failure_limit: int = 3
    on_breach: Optional[Callable[[str, str, Any], None]] = None


@dataclass
class RateLimitConfig:
    """
    Rate limiting configuration (sliding window).

    Attributes:
        max_executions: Maximum executions in time window
        window_seconds: Time window in seconds
        queue_overflow: Whether to queue excess requests or reject
    """

    max_executions: int = 10
    window_seconds: int = 3600
    queue_overflow: bool = True


@dataclass
class DependencyConfig:
    """
    Dependency configuration for DAG-based scheduling.

    Attributes:
        depends_on: List of schedule IDs this schedule depends on
        wait_for_all: Whether to wait for all dependencies or just one
        timeout_seconds: Timeout waiting for dependencies
        trigger_on_success_only: Only trigger if dependencies succeeded
    """

    depends_on: List[str] = field(default_factory=list)
    wait_for_all: bool = True
    timeout_seconds: int = 3600
    trigger_on_success_only: bool = True


@dataclass
class ConditionalConfig:
    """
    Conditional execution configuration.

    Attributes:
        condition_fn: Function that returns True if execution should proceed
        condition_expression: String expression to evaluate
        retry_on_condition_fail: Whether to retry if condition fails
        retry_interval_seconds: Interval between condition checks
        max_condition_retries: Maximum condition check retries
    """

    condition_fn: Optional[Callable[[], bool]] = None
    condition_expression: Optional[str] = None
    retry_on_condition_fail: bool = False
    retry_interval_seconds: int = 60
    max_condition_retries: int = 5


@dataclass
class CatchUpConfig:
    """
    Catch-up configuration for missed runs.

    Attributes:
        enabled: Whether catch-up is enabled
        max_catch_up_runs: Maximum missed runs to catch up
        catch_up_window_hours: How far back to look for missed runs
        run_sequentially: Run catch-up executions one at a time
    """

    enabled: bool = True
    max_catch_up_runs: int = 5
    catch_up_window_hours: int = 24
    run_sequentially: bool = True


@dataclass
class EventTriggerConfig:
    """
    Event-driven trigger configuration.

    Attributes:
        event_type: Type of event to trigger on
        event_source: Source identifier (file path, webhook ID, etc.)
        event_filter: Optional filter for event data
        debounce_seconds: Minimum time between triggers
        batch_events: Whether to batch multiple events
        batch_window_seconds: Time window for batching
    """

    event_type: EventType
    event_source: str
    event_filter: Optional[Dict[str, Any]] = None
    debounce_seconds: int = 0
    batch_events: bool = False
    batch_window_seconds: int = 60


@dataclass
class AdvancedSchedule:
    """
    Advanced schedule definition with enterprise features.

    Attributes:
        id: Unique schedule identifier
        name: Human-readable schedule name
        workflow_id: ID of workflow to execute
        workflow_name: Human-readable workflow name
        schedule_type: Type of schedule
        enabled: Whether schedule is active
        timezone: Timezone for schedule calculations

        cron_expression: Cron expression (for CRON type)
        interval_seconds: Interval in seconds (for INTERVAL type)
        run_at: Specific datetime (for ONE_TIME type)

        calendar_id: Business calendar ID for working hours/holidays
        respect_business_hours: Whether to only run during business hours
        sla: SLA configuration
        rate_limit: Rate limiting configuration
        dependency: Dependency configuration for DAG execution
        conditional: Conditional execution configuration
        catch_up: Catch-up configuration for missed runs
        event_trigger: Event-driven trigger configuration

        priority: Execution priority (0-3)
        robot_id: Specific robot to execute on (None = any)
        variables: Variables to pass to workflow
        tags: Tags for categorization
        metadata: Additional metadata

        last_run: Timestamp of last execution
        next_run: Calculated next run time
        run_count: Total number of executions
        success_count: Number of successful executions
        failure_count: Number of failed executions
        consecutive_failures: Current consecutive failure count

        created_at: Creation timestamp
        created_by: User who created the schedule
        updated_at: Last update timestamp
    """

    id: str
    name: str
    workflow_id: str
    workflow_name: str = ""
    schedule_type: ScheduleType = ScheduleType.CRON
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    enabled: bool = True
    timezone: str = "UTC"

    cron_expression: str = ""
    interval_seconds: int = 0
    run_at: Optional[datetime] = None

    calendar_id: Optional[str] = None
    respect_business_hours: bool = False
    sla: Optional[SLAConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    dependency: Optional[DependencyConfig] = None
    conditional: Optional[ConditionalConfig] = None
    catch_up: Optional[CatchUpConfig] = None
    event_trigger: Optional[EventTriggerConfig] = None

    priority: int = 1
    robot_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0

    created_at: Optional[datetime] = None
    created_by: str = ""
    updated_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.run_count == 0:
            return 100.0
        return (self.success_count / self.run_count) * 100

    @property
    def sla_status(self) -> SLAStatus:
        """Get current SLA status."""
        if not self.sla:
            return SLAStatus.UNKNOWN

        if self.consecutive_failures >= self.sla.consecutive_failure_limit:
            return SLAStatus.BREACHED

        if self.success_rate < self.sla.success_rate_threshold:
            if self.success_rate < self.sla.success_rate_threshold - 5:
                return SLAStatus.BREACHED
            return SLAStatus.WARNING

        return SLAStatus.OK


class CronExpressionParser:
    """
    Parser for cron expressions with human-readable aliases.

    Supports:
    - Standard 5-field cron: minute hour day month weekday
    - Extended 6-field cron: second minute hour day month weekday
    - Human-readable aliases (@daily, @hourly, etc.)
    - Special syntax (L for last, # for nth weekday)
    """

    FIELD_NAMES = ["minute", "hour", "day", "month", "day_of_week"]
    FIELD_NAMES_6 = ["second", "minute", "hour", "day", "month", "day_of_week"]

    @classmethod
    def parse(cls, expression: str) -> Dict[str, str]:
        """
        Parse cron expression into APScheduler trigger kwargs.

        Args:
            expression: Cron expression or alias

        Returns:
            Dict with cron trigger parameters

        Raises:
            ValueError: If expression is invalid
        """
        expression = expression.strip()

        if expression.startswith("@"):
            alias_lower = expression.lower()
            if alias_lower in CRON_ALIASES:
                expression = CRON_ALIASES[alias_lower]
            else:
                raise ValueError(f"Unknown cron alias: {expression}")

        parts = expression.split()

        if len(parts) == 5:
            return dict(zip(cls.FIELD_NAMES, parts))
        elif len(parts) == 6:
            return dict(zip(cls.FIELD_NAMES_6, parts))
        else:
            raise ValueError(
                f"Invalid cron expression: {expression}. "
                f"Expected 5 or 6 fields, got {len(parts)}"
            )

    @classmethod
    def validate(cls, expression: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a cron expression.

        Args:
            expression: Cron expression to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.parse(expression)
            return True, None
        except ValueError as e:
            return False, str(e)

    @classmethod
    def to_human_readable(cls, expression: str) -> str:
        """
        Convert cron expression to human-readable description.

        Args:
            expression: Cron expression

        Returns:
            Human-readable description
        """
        expression = expression.strip()

        for alias, cron in CRON_ALIASES.items():
            if expression.lower() == alias or expression == cron:
                return cls._alias_to_description(alias)

        try:
            parts = cls.parse(expression)
        except ValueError:
            return f"Invalid expression: {expression}"

        return cls._build_description(parts)

    @classmethod
    def _alias_to_description(cls, alias: str) -> str:
        """Get description for cron alias."""
        descriptions = {
            "@yearly": "Once a year at midnight on January 1st",
            "@annually": "Once a year at midnight on January 1st",
            "@monthly": "Once a month at midnight on the 1st",
            "@weekly": "Once a week at midnight on Sunday",
            "@daily": "Once a day at midnight",
            "@midnight": "Once a day at midnight",
            "@hourly": "Once every hour",
            "@every_minute": "Every minute",
            "@every_5_minutes": "Every 5 minutes",
            "@every_10_minutes": "Every 10 minutes",
            "@every_15_minutes": "Every 15 minutes",
            "@every_30_minutes": "Every 30 minutes",
            "@business_hours": "Every hour during business hours (9-17) on weekdays",
            "@weekdays": "At 9 AM on weekdays",
            "@weekends": "At 9 AM on weekends",
            "@end_of_month": "At midnight on the last day of the month",
            "@first_monday": "At midnight on the first Monday of the month",
            "@last_friday": "At 5 PM on the last Friday of the month",
        }
        return descriptions.get(alias.lower(), f"Custom schedule: {alias}")

    @classmethod
    def _build_description(cls, parts: Dict[str, str]) -> str:
        """Build description from parsed cron parts."""
        descriptions = []

        minute = parts.get("minute", "*")
        hour = parts.get("hour", "*")
        day = parts.get("day", "*")
        month = parts.get("month", "*")
        dow = parts.get("day_of_week", "*")

        if minute == "*" and hour == "*":
            descriptions.append("Every minute")
        elif minute.startswith("*/"):
            interval = minute[2:]
            descriptions.append(f"Every {interval} minutes")
        elif hour == "*":
            descriptions.append(f"At minute {minute} every hour")
        else:
            if hour.startswith("*/"):
                interval = hour[2:]
                descriptions.append(f"Every {interval} hours at minute {minute}")
            else:
                descriptions.append(f"At {hour}:{minute.zfill(2)}")

        if day != "*":
            if day == "L":
                descriptions.append("on the last day of the month")
            elif "#" in day:
                descriptions.append(f"on day pattern {day}")
            else:
                descriptions.append(f"on day {day}")

        if month != "*":
            month_names = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            try:
                month_idx = int(month) - 1
                if 0 <= month_idx < 12:
                    descriptions.append(f"in {month_names[month_idx]}")
                else:
                    descriptions.append(f"in month {month}")
            except ValueError:
                descriptions.append(f"in month {month}")

        if dow != "*":
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            if dow == "1-5":
                descriptions.append("on weekdays")
            elif dow == "0,6":
                descriptions.append("on weekends")
            elif "L" in dow:
                descriptions.append(f"on last {dow.replace('L', '')} of month")
            elif "#" in dow:
                parts_dow = dow.split("#")
                if len(parts_dow) == 2:
                    try:
                        day_idx = int(parts_dow[0])
                        occurrence = parts_dow[1]
                        if 0 <= day_idx <= 6:
                            descriptions.append(
                                f"on {occurrence}{'st' if occurrence == '1' else 'nd' if occurrence == '2' else 'rd' if occurrence == '3' else 'th'} "
                                f"{day_names[day_idx]} of month"
                            )
                    except ValueError:
                        descriptions.append(f"on {dow}")
            else:
                try:
                    day_idx = int(dow)
                    if 0 <= day_idx <= 6:
                        descriptions.append(f"on {day_names[day_idx]}")
                    else:
                        descriptions.append(f"on day {dow}")
                except ValueError:
                    descriptions.append(f"on {dow}")

        return " ".join(descriptions)

    @classmethod
    def get_available_aliases(cls) -> Dict[str, str]:
        """Get all available cron aliases with descriptions."""
        result = {}
        for alias in CRON_ALIASES:
            result[alias] = cls._alias_to_description(alias)
        return result


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for schedule executions.

    Tracks executions within a time window and enforces limits.
    """

    def __init__(self, max_executions: int, window_seconds: int):
        """
        Initialize rate limiter.

        Args:
            max_executions: Maximum executions allowed in window
            window_seconds: Window duration in seconds
        """
        self._max_executions = max_executions
        self._window = timedelta(seconds=window_seconds)
        self._executions: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def can_execute(self, schedule_id: str) -> bool:
        """
        Check if execution is allowed for schedule.

        Args:
            schedule_id: Schedule ID to check

        Returns:
            True if execution is allowed
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            return len(self._executions[schedule_id]) < self._max_executions

    def record_execution(self, schedule_id: str) -> None:
        """
        Record an execution for rate limiting.

        Args:
            schedule_id: Schedule ID
        """
        with self._lock:
            self._executions[schedule_id].append(datetime.utcnow())

    def get_wait_time(self, schedule_id: str) -> int:
        """
        Get seconds to wait before next execution allowed.

        Args:
            schedule_id: Schedule ID

        Returns:
            Seconds to wait (0 if can execute now)
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            executions = self._executions[schedule_id]

            if len(executions) < self._max_executions:
                return 0

            oldest = min(executions)
            wait_until = oldest + self._window
            wait_seconds = (wait_until - datetime.utcnow()).total_seconds()
            return max(0, int(wait_seconds))

    def get_remaining_capacity(self, schedule_id: str) -> int:
        """
        Get remaining executions allowed in current window.

        Args:
            schedule_id: Schedule ID

        Returns:
            Number of executions remaining
        """
        with self._lock:
            self._cleanup_old_entries(schedule_id)
            return max(0, self._max_executions - len(self._executions[schedule_id]))

    def _cleanup_old_entries(self, schedule_id: str) -> None:
        """Remove expired entries from tracking."""
        cutoff = datetime.utcnow() - self._window
        self._executions[schedule_id] = [
            ts for ts in self._executions[schedule_id] if ts > cutoff
        ]


class DependencyTracker:
    """
    Tracks workflow dependencies for DAG-based scheduling.

    Manages dependency completion status and triggers dependent schedules.
    """

    @dataclass
    class CompletionRecord:
        """Record of a schedule completion."""

        schedule_id: str
        completed_at: datetime
        success: bool
        result: Any = None

    def __init__(self, ttl_seconds: int = 86400):
        """
        Initialize dependency tracker.

        Args:
            ttl_seconds: Time to keep completion records
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._completions: Dict[str, List["DependencyTracker.CompletionRecord"]] = (
            defaultdict(list)
        )
        self._waiters: Dict[str, List[asyncio.Event]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_completion(
        self,
        schedule_id: str,
        success: bool,
        result: Any = None,
    ) -> None:
        """
        Record schedule completion for dependency tracking.

        Args:
            schedule_id: Completed schedule ID
            success: Whether execution succeeded
            result: Optional execution result
        """
        record = self.CompletionRecord(
            schedule_id=schedule_id,
            completed_at=datetime.utcnow(),
            success=success,
            result=result,
        )

        with self._lock:
            self._completions[schedule_id].append(record)
            self._cleanup_old(schedule_id)

            waiters = self._waiters.pop(schedule_id, [])
            for event in waiters:
                event.set()

        logger.debug(
            f"Recorded completion for schedule {schedule_id}: success={success}"
        )

    def is_dependency_satisfied(
        self,
        dependency_id: str,
        since: Optional[datetime] = None,
        require_success: bool = True,
    ) -> bool:
        """
        Check if a dependency has been satisfied.

        Args:
            dependency_id: Schedule ID of dependency
            since: Only check completions since this time
            require_success: Whether to require successful completion

        Returns:
            True if dependency is satisfied
        """
        with self._lock:
            self._cleanup_old(dependency_id)
            completions = self._completions.get(dependency_id, [])

            for record in reversed(completions):
                if since and record.completed_at < since:
                    continue
                if require_success and not record.success:
                    continue
                return True

            return False

    def are_dependencies_satisfied(
        self,
        dependency_ids: List[str],
        wait_for_all: bool = True,
        since: Optional[datetime] = None,
        require_success: bool = True,
    ) -> Tuple[bool, List[str]]:
        """
        Check if multiple dependencies are satisfied.

        Args:
            dependency_ids: List of dependency schedule IDs
            wait_for_all: Whether all must be satisfied or just one
            since: Only check completions since this time
            require_success: Whether to require successful completion

        Returns:
            Tuple of (all_satisfied, list_of_unsatisfied)
        """
        unsatisfied = []
        satisfied_count = 0

        for dep_id in dependency_ids:
            if self.is_dependency_satisfied(dep_id, since, require_success):
                satisfied_count += 1
            else:
                unsatisfied.append(dep_id)

        if wait_for_all:
            return len(unsatisfied) == 0, unsatisfied
        else:
            return satisfied_count > 0, unsatisfied

    async def wait_for_dependency(
        self,
        dependency_id: str,
        timeout_seconds: int = 3600,
    ) -> bool:
        """
        Wait for a dependency to complete.

        Args:
            dependency_id: Schedule ID to wait for
            timeout_seconds: Maximum wait time

        Returns:
            True if dependency completed, False if timeout
        """
        if self.is_dependency_satisfied(dependency_id):
            return True

        event = asyncio.Event()
        with self._lock:
            self._waiters[dependency_id].append(event)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            return True
        except asyncio.TimeoutError:
            with self._lock:
                waiters = self._waiters.get(dependency_id, [])
                if event in waiters:
                    waiters.remove(event)
            return False

    def get_latest_completion(
        self, schedule_id: str
    ) -> Optional["DependencyTracker.CompletionRecord"]:
        """Get most recent completion record for a schedule."""
        with self._lock:
            completions = self._completions.get(schedule_id, [])
            return completions[-1] if completions else None

    def _cleanup_old(self, schedule_id: str) -> None:
        """Remove old completion records."""
        cutoff = datetime.utcnow() - self._ttl
        self._completions[schedule_id] = [
            r for r in self._completions[schedule_id] if r.completed_at > cutoff
        ]


class SLAMonitor:
    """
    Monitors SLA compliance for schedules.

    Tracks execution times, success rates, and triggers alerts on breaches.
    """

    @dataclass
    class ExecutionMetrics:
        """Metrics for a single execution."""

        schedule_id: str
        started_at: datetime
        completed_at: Optional[datetime] = None
        scheduled_time: Optional[datetime] = None
        success: bool = False
        duration_ms: int = 0
        start_delay_ms: int = 0

    def __init__(self):
        """Initialize SLA monitor."""
        self._metrics: Dict[str, List["SLAMonitor.ExecutionMetrics"]] = defaultdict(
            list
        )
        self._active_executions: Dict[str, "SLAMonitor.ExecutionMetrics"] = {}
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable[[str, SLAStatus, str], None]] = []

    def add_alert_callback(
        self, callback: Callable[[str, SLAStatus, str], None]
    ) -> None:
        """
        Add callback for SLA alerts.

        Args:
            callback: Function called with (schedule_id, status, message)
        """
        self._alert_callbacks.append(callback)

    def record_start(
        self,
        schedule_id: str,
        scheduled_time: Optional[datetime] = None,
    ) -> str:
        """
        Record execution start.

        Args:
            schedule_id: Schedule ID
            scheduled_time: When execution was scheduled for

        Returns:
            Execution tracking ID
        """
        execution_id = str(uuid.uuid4())
        now = datetime.utcnow()

        start_delay_ms = 0
        if scheduled_time:
            delay = (now - scheduled_time).total_seconds() * 1000
            start_delay_ms = int(max(0, delay))

        metrics = self.ExecutionMetrics(
            schedule_id=schedule_id,
            started_at=now,
            scheduled_time=scheduled_time,
            start_delay_ms=start_delay_ms,
        )

        with self._lock:
            self._active_executions[execution_id] = metrics

        return execution_id

    def record_completion(
        self,
        execution_id: str,
        success: bool,
        sla_config: Optional[SLAConfig] = None,
    ) -> Optional["SLAMonitor.ExecutionMetrics"]:
        """
        Record execution completion and check SLA.

        Args:
            execution_id: Execution tracking ID from record_start
            success: Whether execution succeeded
            sla_config: SLA configuration for checking

        Returns:
            Execution metrics or None if not found
        """
        with self._lock:
            metrics = self._active_executions.pop(execution_id, None)
            if not metrics:
                return None

            metrics.completed_at = datetime.utcnow()
            metrics.success = success
            metrics.duration_ms = int(
                (metrics.completed_at - metrics.started_at).total_seconds() * 1000
            )

            self._metrics[metrics.schedule_id].append(metrics)

            if len(self._metrics[metrics.schedule_id]) > 1000:
                self._metrics[metrics.schedule_id] = self._metrics[metrics.schedule_id][
                    -500:
                ]

        if sla_config:
            self._check_sla(metrics, sla_config)

        return metrics

    def _check_sla(
        self, metrics: "SLAMonitor.ExecutionMetrics", sla: SLAConfig
    ) -> None:
        """Check SLA compliance and trigger alerts if needed."""
        breaches = []

        if sla.max_duration_seconds:
            max_duration_ms = sla.max_duration_seconds * 1000
            if metrics.duration_ms > max_duration_ms:
                breaches.append(
                    f"Duration {metrics.duration_ms}ms exceeded limit {max_duration_ms}ms"
                )

        if sla.max_start_delay_seconds:
            max_delay_ms = sla.max_start_delay_seconds * 1000
            if metrics.start_delay_ms > max_delay_ms:
                breaches.append(
                    f"Start delay {metrics.start_delay_ms}ms exceeded limit {max_delay_ms}ms"
                )

        if breaches:
            message = "; ".join(breaches)
            logger.warning(f"SLA breach for {metrics.schedule_id}: {message}")

            for callback in self._alert_callbacks:
                try:
                    callback(metrics.schedule_id, SLAStatus.BREACHED, message)
                except Exception as e:
                    logger.error(f"SLA alert callback failed: {e}")

            if sla.on_breach:
                try:
                    sla.on_breach(metrics.schedule_id, message, metrics)
                except Exception as e:
                    logger.error(f"SLA breach handler failed: {e}")

    def get_metrics(
        self,
        schedule_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List["SLAMonitor.ExecutionMetrics"]:
        """
        Get execution metrics for a schedule.

        Args:
            schedule_id: Schedule ID
            since: Only get metrics since this time
            limit: Maximum number of records

        Returns:
            List of execution metrics
        """
        with self._lock:
            metrics = self._metrics.get(schedule_id, [])
            if since:
                metrics = [m for m in metrics if m.started_at >= since]
            return list(reversed(metrics[-limit:]))

    def get_success_rate(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> float:
        """
        Calculate success rate for a schedule.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to calculate over

        Returns:
            Success rate percentage (0-100)
        """
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)

        if not metrics:
            return 100.0

        success_count = sum(1 for m in metrics if m.success)
        return (success_count / len(metrics)) * 100

    def get_average_duration(
        self,
        schedule_id: str,
        window_hours: int = 24,
    ) -> int:
        """
        Calculate average execution duration.

        Args:
            schedule_id: Schedule ID
            window_hours: Time window to calculate over

        Returns:
            Average duration in milliseconds
        """
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        metrics = self.get_metrics(schedule_id, since=cutoff)

        if not metrics:
            return 0

        total_duration = sum(m.duration_ms for m in metrics)
        return total_duration // len(metrics)


class AdvancedScheduler:
    """
    Enterprise-grade scheduler with advanced features.

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

        self._rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._dependency_tracker = DependencyTracker()
        self._sla_monitor = SLAMonitor()

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
        schedule.updated_at = datetime.utcnow()
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
        now = datetime.utcnow()

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

        if schedule.conditional:
            condition_met = await self._check_condition(schedule)
            if not condition_met:
                if schedule.conditional.retry_on_condition_fail:
                    logger.info(f"Schedule {schedule_id} condition not met, will retry")
                else:
                    logger.info(f"Schedule {schedule_id} condition not met, skipping")
                return

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

        if rate_limiter:
            rate_limiter.record_execution(schedule_id)

        execution_id = self._sla_monitor.record_start(schedule_id, schedule.next_run)

        logger.info(
            f"Executing schedule '{schedule.name}' "
            f"(catch_up={catch_up}, type={schedule.schedule_type.value})"
        )

        schedule.last_run = datetime.utcnow()
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

        self._sla_monitor.record_completion(execution_id, success, schedule.sla)

        self.notify_completion(schedule_id, success)

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
                    result = eval(
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
            "generated_at": datetime.utcnow().isoformat(),
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
        graph = {}
        for schedule in self._schedules.values():
            if schedule.dependency:
                graph[schedule.id] = schedule.dependency.depends_on
            else:
                graph[schedule.id] = []

        visited = set()
        rec_stack = set()
        cycle_path: List[str] = []

        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_path.extend(path[path.index(neighbor) :])
                    cycle_path.append(neighbor)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node, []):
                    return False, cycle_path

        return True, []
