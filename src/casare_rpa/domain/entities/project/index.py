"""
CasareRPA - Project Index

Project index classes for project registry management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from casare_rpa.domain.entities.project.base import PROJECT_SCHEMA_VERSION
from casare_rpa.domain.entities.project.project import Project


@dataclass
class ProjectIndexEntry:
    """
    Entry in the projects index for quick project lookup.

    Domain value object for project registry tracking.
    """

    id: str
    name: str
    path: str
    last_opened: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "last_opened": self.last_opened.isoformat() if self.last_opened else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectIndexEntry":
        """Create from dictionary."""
        last_opened = None
        if data.get("last_opened"):
            last_opened = datetime.fromisoformat(data["last_opened"])

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            path=data.get("path", ""),
            last_opened=last_opened,
        )


@dataclass
class ProjectsIndex:
    """
    Index of all known projects for the application.

    Domain entity managing the project registry.
    Stored in CONFIG_DIR/projects_index.json
    """

    projects: List[ProjectIndexEntry] = field(default_factory=list)
    recent_limit: int = 10
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "projects": [p.to_dict() for p in self.projects],
            "recent_limit": self.recent_limit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectsIndex":
        """Create from dictionary."""
        projects = [ProjectIndexEntry.from_dict(p) for p in data.get("projects", [])]
        return cls(
            projects=projects,
            recent_limit=data.get("recent_limit", 10),
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def add_project(self, project: Project) -> None:
        """
        Add or update a project in the index.

        Args:
            project: Project to add
        """
        # Remove existing entry if present
        self.projects = [p for p in self.projects if p.id != project.id]

        # Add new entry at the beginning
        entry = ProjectIndexEntry(
            id=project.id,
            name=project.name,
            path=str(project.path) if project.path else "",
            last_opened=datetime.now(),
        )
        self.projects.insert(0, entry)

        # Trim to recent_limit
        self.projects = self.projects[: self.recent_limit]

    def remove_project(self, project_id: str) -> bool:
        """
        Remove a project from the index.

        Args:
            project_id: ID of project to remove

        Returns:
            True if project was removed
        """
        original_len = len(self.projects)
        self.projects = [p for p in self.projects if p.id != project_id]
        return len(self.projects) < original_len

    def get_project(self, project_id: str) -> Optional[ProjectIndexEntry]:
        """
        Get a project entry by ID.

        Args:
            project_id: Project ID to find

        Returns:
            ProjectIndexEntry if found, None otherwise
        """
        for p in self.projects:
            if p.id == project_id:
                return p
        return None

    def get_recent_projects(self, limit: Optional[int] = None) -> List[ProjectIndexEntry]:
        """
        Get recently opened projects.

        Args:
            limit: Max number of projects to return

        Returns:
            List of recent project entries
        """
        limit = limit or self.recent_limit
        return self.projects[:limit]

    def update_last_opened(self, project_id: str) -> None:
        """
        Update the last_opened timestamp for a project.

        Args:
            project_id: ID of project to update
        """
        for p in self.projects:
            if p.id == project_id:
                p.last_opened = datetime.now()
                # Move to front of list
                self.projects.remove(p)
                self.projects.insert(0, p)
                break
