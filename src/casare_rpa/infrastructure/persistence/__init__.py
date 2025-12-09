"""
CasareRPA - Infrastructure Persistence

Persistence adapters for domain entities.

Result Pattern Support:
    Storage classes now provide *_safe() method variants that return
    Result[T, FileSystemError] instead of raising exceptions or returning None.

    Example:
        from casare_rpa.infrastructure.persistence import FolderStorage

        # Traditional (may fail silently):
        folders = FolderStorage.load_folders()

        # Result pattern (explicit error handling):
        result = FolderStorage.load_folders_safe()
        if result.is_ok():
            folders = result.unwrap()
        else:
            logger.error(f"Load failed: {result.error}")
"""

from casare_rpa.infrastructure.persistence.file_system_project_repository import (
    FileSystemProjectRepository,
)
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage
from casare_rpa.infrastructure.persistence.folder_storage import FolderStorage
from casare_rpa.infrastructure.persistence.template_storage import TemplateStorage
from casare_rpa.infrastructure.persistence.environment_storage import EnvironmentStorage
from casare_rpa.infrastructure.persistence.repositories import (
    JobRepository,
    NodeOverrideRepository,
    RobotRepository,
    WorkflowAssignmentRepository,
)

__all__ = [
    "ProjectStorage",
    "FileSystemProjectRepository",
    # Storage classes with Result pattern support
    "FolderStorage",
    "TemplateStorage",
    "EnvironmentStorage",
    # Robot orchestration repositories
    "JobRepository",
    "NodeOverrideRepository",
    "RobotRepository",
    "WorkflowAssignmentRepository",
]
