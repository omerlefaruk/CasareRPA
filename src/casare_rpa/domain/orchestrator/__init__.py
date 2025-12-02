"""Orchestrator domain layer.

Contains entities, value objects, services, and errors for the orchestrator domain.
"""

from .entities import (
    Robot,
    RobotStatus,
    RobotCapability,
    Job,
    JobStatus,
    JobPriority,
    Workflow,
    WorkflowStatus,
    Schedule,
    ScheduleFrequency,
    DashboardMetrics,
    JobHistoryEntry,
)
from .value_objects import (
    RobotAssignment,
    NodeRobotOverride,
)
from .services import (
    RobotSelectionService,
)
from .errors import (
    OrchestratorDomainError,
    RobotAtCapacityError,
    RobotUnavailableError,
    RobotNotFoundError,
    NoAvailableRobotError,
    InvalidRobotStateError,
    DuplicateJobAssignmentError,
    InvalidJobStateError,
    JobTransitionError,
    JobNotFoundError,
    InvalidAssignmentError,
    DuplicateAssignmentError,
)

__all__ = [
    # Entities
    "Robot",
    "RobotStatus",
    "RobotCapability",
    "Job",
    "JobStatus",
    "JobPriority",
    "Workflow",
    "WorkflowStatus",
    "Schedule",
    "ScheduleFrequency",
    "DashboardMetrics",
    "JobHistoryEntry",
    # Value Objects
    "RobotAssignment",
    "NodeRobotOverride",
    # Services
    "RobotSelectionService",
    # Errors
    "OrchestratorDomainError",
    "RobotAtCapacityError",
    "RobotUnavailableError",
    "RobotNotFoundError",
    "NoAvailableRobotError",
    "InvalidRobotStateError",
    "DuplicateJobAssignmentError",
    "InvalidJobStateError",
    "JobTransitionError",
    "JobNotFoundError",
    "InvalidAssignmentError",
    "DuplicateAssignmentError",
]
