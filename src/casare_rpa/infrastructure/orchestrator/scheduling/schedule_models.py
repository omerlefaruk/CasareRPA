"""
Schedule models for CasareRPA Orchestrator.

Contains data classes and enums for schedule definitions.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from casare_rpa.infrastructure.orchestrator.scheduling.schedule_conflict_resolver import (
    DependencyConfig,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_optimizer import (
    RateLimitConfig,
)
from casare_rpa.infrastructure.orchestrator.scheduling.sla_monitor import (
    SLAConfig,
    SLAStatus,
)


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


class EventType(Enum):
    """Types of events for event-driven scheduling."""

    FILE_ARRIVAL = "file_arrival"
    WEBHOOK = "webhook"
    DATABASE_CHANGE = "database_change"
    QUEUE_MESSAGE = "queue_message"
    WORKFLOW_COMPLETED = "workflow_completed"
    CUSTOM = "custom"


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

    condition_fn: Callable[[], bool] | None = None
    condition_expression: str | None = None
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
    event_filter: dict[str, Any] | None = None
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
    run_at: datetime | None = None

    calendar_id: str | None = None
    respect_business_hours: bool = False
    sla: SLAConfig | None = None
    rate_limit: RateLimitConfig | None = None
    dependency: DependencyConfig | None = None
    conditional: ConditionalConfig | None = None
    catch_up: CatchUpConfig | None = None
    event_trigger: EventTriggerConfig | None = None

    priority: int = 1
    robot_id: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0

    created_at: datetime | None = None
    created_by: str = ""
    updated_at: datetime | None = None

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
