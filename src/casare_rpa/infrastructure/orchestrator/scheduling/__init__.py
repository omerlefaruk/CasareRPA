"""
Scheduling module for CasareRPA Orchestrator.

Provides:
- Intelligent job assignment with load balancing
- State affinity management for workflow sessions
- Business calendar with holidays and working hours
- Advanced scheduling with enterprise features
- Global scheduler singleton for API integration
"""

from typing import Optional

from loguru import logger

from .job_assignment import (
    JobAssignmentEngine,
    ScoringWeights,
    RobotCapability,
    CapabilityType,
    JobRequirements,
    RobotInfo,
    AssignmentResult,
    StateAffinityTracker,
    NoCapableRobotError,
    assign_job_to_robot,
)

from .state_affinity import (
    StateAffinityLevel,
    RobotState,
    WorkflowSession,
    StateAffinityManager,
    SessionAffinityError,
    StateAffinityDecision,
)

from .calendar import (
    DayOfWeek,
    HolidayType,
    Holiday,
    WorkingHours,
    BlackoutPeriod,
    CalendarConfig,
    BusinessCalendar,
)

from .advanced_scheduler import (
    ScheduleType,
    ScheduleStatus,
    SLAStatus,
    EventType,
    CRON_ALIASES,
    SLAConfig,
    RateLimitConfig,
    DependencyConfig,
    ConditionalConfig,
    CatchUpConfig,
    EventTriggerConfig,
    AdvancedSchedule,
    CronExpressionParser,
    SlidingWindowRateLimiter,
    DependencyTracker,
    SLAMonitor,
    AdvancedScheduler,
)


# =========================
# Global Scheduler Singleton
# =========================

_global_scheduler: Optional[AdvancedScheduler] = None
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
    global _global_scheduler, _scheduler_initialized

    if _scheduler_initialized and _global_scheduler is not None:
        logger.warning(
            "Global scheduler already initialized, returning existing instance"
        )
        return _global_scheduler

    try:
        _global_scheduler = AdvancedScheduler(
            on_schedule_trigger=on_schedule_trigger,
            default_timezone=default_timezone,
        )
        await _global_scheduler.start()
        _scheduler_initialized = True
        logger.info("Global scheduler initialized and started")
        return _global_scheduler
    except ImportError as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        raise


async def shutdown_global_scheduler() -> None:
    """
    Shutdown the global scheduler.

    Should be called during application shutdown (lifespan context).
    """
    global _global_scheduler, _scheduler_initialized

    if _global_scheduler is not None:
        await _global_scheduler.stop(wait=True)
        logger.info("Global scheduler stopped")

    _global_scheduler = None
    _scheduler_initialized = False


def get_global_scheduler() -> Optional[AdvancedScheduler]:
    """
    Get the global scheduler instance.

    Returns:
        The AdvancedScheduler instance, or None if not initialized.
    """
    return _global_scheduler


def is_scheduler_initialized() -> bool:
    """
    Check if the global scheduler is initialized and running.

    Returns:
        True if scheduler is initialized and running.
    """
    return _scheduler_initialized and _global_scheduler is not None


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
    # Advanced Scheduler
    "ScheduleType",
    "ScheduleStatus",
    "SLAStatus",
    "EventType",
    "CRON_ALIASES",
    "SLAConfig",
    "RateLimitConfig",
    "DependencyConfig",
    "ConditionalConfig",
    "CatchUpConfig",
    "EventTriggerConfig",
    "AdvancedSchedule",
    "CronExpressionParser",
    "SlidingWindowRateLimiter",
    "DependencyTracker",
    "SLAMonitor",
    "AdvancedScheduler",
    # Global Scheduler Functions
    "init_global_scheduler",
    "shutdown_global_scheduler",
    "get_global_scheduler",
    "is_scheduler_initialized",
]
