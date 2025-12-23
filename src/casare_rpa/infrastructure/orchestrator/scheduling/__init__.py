"""
Scheduling module for CasareRPA Orchestrator.

Provides:
- Intelligent job assignment with load balancing
- State affinity management for workflow sessions
- Business calendar with holidays and working hours
- Advanced scheduling with enterprise features
- Global scheduler singleton for API integration

Module structure (after refactoring):
- scheduling_strategies.py: Cron parsing and scheduling strategies
- schedule_optimizer.py: Rate limiting and execution optimization
- schedule_conflict_resolver.py: Dependency tracking and conflict resolution
- sla_monitor.py: SLA monitoring and alerting
- advanced_scheduler.py: Main scheduler orchestrator
"""

# =========================
# Global Scheduler Singleton
# =========================
import threading
from typing import Optional

from loguru import logger

# Import from main scheduler (orchestrator)
from casare_rpa.infrastructure.orchestrator.scheduling.advanced_scheduler import (
    AdvancedScheduler,
)
from casare_rpa.infrastructure.orchestrator.scheduling.calendar import (
    BlackoutPeriod,
    BusinessCalendar,
    CalendarConfig,
    DayOfWeek,
    Holiday,
    HolidayType,
    WorkingHours,
)
from casare_rpa.infrastructure.orchestrator.scheduling.job_assignment import (
    AssignmentResult,
    CapabilityType,
    JobAssignmentEngine,
    JobRequirements,
    NoCapableRobotError,
    RobotCapability,
    RobotInfo,
    ScoringWeights,
    StateAffinityTracker,
    assign_job_to_robot,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_conflict_resolver import (
    CompletionRecord,
    ConflictResolver,
    DependencyConfig,
    DependencyGraphValidator,
    DependencyTracker,
)

# Import from schedule models
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_models import (
    AdvancedSchedule,
    CatchUpConfig,
    ConditionalConfig,
    EventTriggerConfig,
    EventType,
    ScheduleStatus,
    ScheduleType,
)
from casare_rpa.infrastructure.orchestrator.scheduling.schedule_optimizer import (
    ExecutionOptimizer,
    PriorityQueue,
    RateLimitConfig,
    SlidingWindowRateLimiter,
)

# Import from extracted modules for direct access
from casare_rpa.infrastructure.orchestrator.scheduling.scheduling_strategies import (
    CRON_ALIASES,
    CronExpressionParser,
    CronSchedulingStrategy,
    DependencySchedulingStrategy,
    EventDrivenStrategy,
    IntervalSchedulingStrategy,
    OneTimeSchedulingStrategy,
    SchedulingStrategy,
)
from casare_rpa.infrastructure.orchestrator.scheduling.sla_monitor import (
    ExecutionMetrics,
    SLAAggregator,
    SLAConfig,
    SLAMonitor,
    SLAReport,
    SLAStatus,
)
from casare_rpa.infrastructure.orchestrator.scheduling.state_affinity import (
    RobotState,
    SessionAffinityError,
    StateAffinityDecision,
    StateAffinityLevel,
    StateAffinityManager,
    WorkflowSession,
)

# Thread-safe state holder for scheduler
_scheduler_lock = threading.Lock()
_scheduler_instance: AdvancedScheduler | None = None
_scheduler_initialized: bool = False


async def init_global_scheduler(
    on_schedule_trigger=None,
    default_timezone: str = "UTC",
) -> AdvancedScheduler:
    """
    Initialize the global scheduler singleton.

    Should be called during application startup (lifespan context).

    Args:
        on_schedule_trigger: Callback function when a schedule triggers.
                            Receives AdvancedSchedule as argument.
        default_timezone: Default timezone for schedules.

    Returns:
        The initialized AdvancedScheduler instance.

    Raises:
        RuntimeError: If scheduler is already initialized.
    """
    # Use module-level variables with lock for thread safety
    _set_scheduler_state = _get_scheduler_state_setter()

    with _scheduler_lock:
        if _scheduler_initialized and _scheduler_instance is not None:
            logger.warning("Global scheduler already initialized, returning existing instance")
            return _scheduler_instance

    try:
        scheduler = AdvancedScheduler(
            on_schedule_trigger=on_schedule_trigger,
            default_timezone=default_timezone,
        )
        await scheduler.start()

        with _scheduler_lock:
            _set_scheduler_state(scheduler, True)

        logger.info("Global scheduler initialized and started")
        return scheduler
    except ImportError as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        raise


async def shutdown_global_scheduler() -> None:
    """
    Shutdown the global scheduler.

    Should be called during application shutdown (lifespan context).
    """
    _set_scheduler_state = _get_scheduler_state_setter()

    with _scheduler_lock:
        scheduler = _scheduler_instance
        if scheduler is not None:
            _set_scheduler_state(None, False)

    if scheduler is not None:
        await scheduler.stop(wait=True)
        logger.info("Global scheduler stopped")


def get_global_scheduler() -> AdvancedScheduler | None:
    """
    Get the global scheduler instance.

    Returns:
        The AdvancedScheduler instance, or None if not initialized.
    """
    with _scheduler_lock:
        return _scheduler_instance


def is_scheduler_initialized() -> bool:
    """
    Check if the global scheduler is initialized and running.

    Returns:
        True if scheduler is initialized and running.
    """
    with _scheduler_lock:
        return _scheduler_initialized and _scheduler_instance is not None


def reset_scheduler_state() -> None:
    """Reset scheduler state for testing."""
    _set_scheduler_state = _get_scheduler_state_setter()
    with _scheduler_lock:
        _set_scheduler_state(None, False)
    logger.debug("Scheduler state reset")


def _get_scheduler_state_setter():
    """Get setter function for scheduler state (avoids global keyword)."""

    def set_state(instance: AdvancedScheduler | None, initialized: bool) -> None:
        # Rebind module-level variables
        import casare_rpa.infrastructure.orchestrator.scheduling as mod

        mod._scheduler_instance = instance
        mod._scheduler_initialized = initialized

    return set_state


__all__ = [
    # Job Assignment
    "JobAssignmentEngine",
    "ScoringWeights",
    "RobotCapability",
    "CapabilityType",
    "JobRequirements",
    "RobotInfo",
    "AssignmentResult",
    "StateAffinityTracker",
    "NoCapableRobotError",
    "assign_job_to_robot",
    # State Affinity
    "StateAffinityLevel",
    "RobotState",
    "WorkflowSession",
    "StateAffinityManager",
    "SessionAffinityError",
    "StateAffinityDecision",
    # Business Calendar
    "DayOfWeek",
    "HolidayType",
    "Holiday",
    "WorkingHours",
    "BlackoutPeriod",
    "CalendarConfig",
    "BusinessCalendar",
    # Scheduling Strategies (extracted)
    "CRON_ALIASES",
    "CronExpressionParser",
    "SchedulingStrategy",
    "CronSchedulingStrategy",
    "IntervalSchedulingStrategy",
    "OneTimeSchedulingStrategy",
    "EventDrivenStrategy",
    "DependencySchedulingStrategy",
    # Schedule Optimizer (extracted)
    "RateLimitConfig",
    "SlidingWindowRateLimiter",
    "ExecutionOptimizer",
    "PriorityQueue",
    # Conflict Resolver (extracted)
    "DependencyConfig",
    "DependencyTracker",
    "CompletionRecord",
    "ConflictResolver",
    "DependencyGraphValidator",
    # SLA Monitor (extracted)
    "SLAConfig",
    "SLAStatus",
    "SLAMonitor",
    "SLAAggregator",
    "ExecutionMetrics",
    "SLAReport",
    # Advanced Scheduler (orchestrator)
    "ScheduleType",
    "ScheduleStatus",
    "EventType",
    "ConditionalConfig",
    "CatchUpConfig",
    "EventTriggerConfig",
    "AdvancedSchedule",
    "AdvancedScheduler",
    # Global Scheduler Functions
    "init_global_scheduler",
    "shutdown_global_scheduler",
    "get_global_scheduler",
    "is_scheduler_initialized",
    "reset_scheduler_state",
]
