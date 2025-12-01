"""
CasareRPA - Infrastructure Persistence

Persistence adapters for domain entities.
"""

from .project_storage import ProjectStorage
from .file_system_project_repository import FileSystemProjectRepository

__all__ = [
    "ProjectStorage",
    "FileSystemProjectRepository",
]
