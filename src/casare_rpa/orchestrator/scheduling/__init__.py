"""
Scheduling module for CasareRPA Orchestrator.

Provides:
- Intelligent job assignment with load balancing
- State affinity management for workflow sessions
- Business calendar with holidays and working hours
- Advanced scheduling with enterprise features
"""

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
]
