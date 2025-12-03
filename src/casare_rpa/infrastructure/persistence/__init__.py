"""
CasareRPA - Infrastructure Persistence

Persistence adapters for domain entities.
"""

from casare_rpa.infrastructure.persistence.file_system_project_repository import (
    FileSystemProjectRepository,
)
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage
from casare_rpa.infrastructure.persistence.repositories import (
    JobRepository,
    NodeOverrideRepository,
    RobotRepository,
    WorkflowAssignmentRepository,
)

__all__ = [
    "ProjectStorage",
    "FileSystemProjectRepository",
    # Robot orchestration repositories
    "JobRepository",
    "NodeOverrideRepository",
    "RobotRepository",
    "WorkflowAssignmentRepository",
]
