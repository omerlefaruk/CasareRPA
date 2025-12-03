"""Orchestrator domain layer.

Contains entities, value objects, services, and errors for the orchestrator domain.
"""

from casare_rpa.domain.orchestrator.entities import (
    DashboardMetrics,
    Job,
    JobHistoryEntry,
    JobPriority,
    JobStatus,
    Robot,
    RobotCapability,
    RobotStatus,
    Schedule,
    ScheduleFrequency,
    Workflow,
    WorkflowStatus,
)
from casare_rpa.domain.orchestrator.errors import (
    DuplicateAssignmentError,
    DuplicateJobAssignmentError,
    InvalidAssignmentError,
    InvalidJobStateError,
    InvalidRobotStateError,
    JobNotFoundError,
    JobTransitionError,
    NoAvailableRobotError,
    OrchestratorDomainError,
    RobotAtCapacityError,
    RobotNotFoundError,
    RobotUnavailableError,
)
from casare_rpa.domain.orchestrator.services import (
    RobotSelectionService,
)
from casare_rpa.domain.orchestrator.value_objects import (
    NodeRobotOverride,
    RobotAssignment,
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
