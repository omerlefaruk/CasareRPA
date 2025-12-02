"""
CasareRPA - Infrastructure Persistence

Persistence adapters for domain entities.
"""

from .project_storage import ProjectStorage
from .file_system_project_repository import FileSystemProjectRepository
from .repositories import (
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
