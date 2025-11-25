"""
CasareRPA Scheduler Module.
Provides scheduling capabilities for automated workflow execution.
"""
from .workflow_scheduler import (
    WorkflowSchedulerService,
    SchedulerConfig,
    ScheduleExecutionResult,
    get_scheduler_service,
    start_scheduler_service,
    stop_scheduler_service,
)
from .execution_history import (
    ExecutionHistoryEntry,
    ExecutionHistory,
    get_execution_history,
)

__all__ = [
    # Scheduler
    "WorkflowSchedulerService",
    "SchedulerConfig",
    "ScheduleExecutionResult",
    "get_scheduler_service",
    "start_scheduler_service",
    "stop_scheduler_service",
    # History
    "ExecutionHistoryEntry",
    "ExecutionHistory",
    "get_execution_history",
]
