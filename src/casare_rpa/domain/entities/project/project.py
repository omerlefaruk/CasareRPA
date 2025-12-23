"""
CasareRPA - Project Entity

Main Project domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from casare_rpa.domain.entities.project.base import (
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
)
from casare_rpa.domain.entities.project.settings import ProjectSettings


@dataclass
class Project:
    """
    Domain entity representing a CasareRPA project.

    A project is a folder containing workflows, scenarios, variables,
    and credential bindings organized for a specific automation goal.

    Attributes:
        id: Unique project identifier (proj_uuid8)
        name: Human-readable project name
        description: Project description
        author: Project creator
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        tags: List of tags for categorization
        settings: Project-level execution settings

        folder_id: ID of folder containing this project (v2.0.0)
        template_id: ID of template this project was created from (v2.0.0)
        environment_ids: List of environment IDs in this project (v2.0.0)
        active_environment_id: Currently active environment (v2.0.0)
    """

    id: str
    name: str
    description: str = ""
    author: str = ""
    created_at: datetime | None = None
    modified_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    schema_version: str = PROJECT_SCHEMA_VERSION

    # v2.0.0 fields
    folder_id: str | None = None
    template_id: str | None = None
    environment_ids: list[str] = field(default_factory=list)
    active_environment_id: str | None = None

    # Runtime properties (not serialized)
    _path: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    @property
    def path(self) -> Path | None:
        """Get project folder path."""
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        """Set project folder path."""
        self._path = value

    @property
    def scenarios_dir(self) -> Path | None:
        """Get scenarios directory path."""
        if self._path:
            return self._path / "scenarios"
        return None

    @property
    def project_file(self) -> Path | None:
        """Get project.json file path."""
        if self._path:
            return self._path / "project.json"
        return None

    @property
    def variables_file(self) -> Path | None:
        """Get variables.json file path."""
        if self._path:
            return self._path / "variables.json"
        return None

    @property
    def credentials_file(self) -> Path | None:
        """Get credentials.json file path."""
        if self._path:
            return self._path / "credentials.json"
        return None

    @property
    def environments_dir(self) -> Path | None:
        """Get environments directory path (v2.0.0)."""
        if self._path:
            return self._path / "environments"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for project.json."""
        return {
            "$schema_version": self.schema_version,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "tags": self.tags,
            "settings": self.settings.to_dict(),
            # v2.0.0 fields
            "folder_id": self.folder_id,
            "template_id": self.template_id,
            "environment_ids": self.environment_ids,
            "active_environment_id": self.active_environment_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        return cls(
            id=data.get("id", generate_project_id()),
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            created_at=created_at,
            modified_at=modified_at,
            tags=data.get("tags", []),
            settings=ProjectSettings.from_dict(data.get("settings", {})),
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
            # v2.0.0 fields (with defaults for v1.0.0 migration)
            folder_id=data.get("folder_id"),
            template_id=data.get("template_id"),
            environment_ids=data.get("environment_ids", []),
            active_environment_id=data.get("active_environment_id"),
        )

    @classmethod
    def create_new(cls, name: str, path: Path, **kwargs: Any) -> "Project":
        """
        Factory method to create a new project.

        Args:
            name: Project name
            path: Path where project will be stored
            **kwargs: Additional project attributes

        Returns:
            New Project instance with generated ID
        """
        project = cls(id=generate_project_id(), name=name, **kwargs)
        project._path = path
        return project

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        return f"Project(id='{self.id}', name='{self.name}')"
