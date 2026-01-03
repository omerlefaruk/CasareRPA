"""Repository interfaces for orchestrator domain."""

from casare_rpa.domain.orchestrator.repositories.job_repository import JobRepository
from casare_rpa.domain.orchestrator.repositories.node_override_repository import (
    NodeOverrideRepository,
)
from casare_rpa.domain.orchestrator.repositories.robot_repository import RobotRepository
from casare_rpa.domain.orchestrator.repositories.schedule_repository import (
    ScheduleRepository,
)
from casare_rpa.domain.orchestrator.repositories.trigger_repository import (
    TriggerRepository,
)
from casare_rpa.domain.orchestrator.repositories.workflow_assignment_repository import (
    WorkflowAssignmentRepository,
)
from casare_rpa.domain.orchestrator.repositories.workflow_repository import (
    WorkflowRepository,
)

__all__ = [
    "RobotRepository",
    "JobRepository",
    "WorkflowRepository",
    "ScheduleRepository",
    "TriggerRepository",
    "WorkflowAssignmentRepository",
    "NodeOverrideRepository",
]
