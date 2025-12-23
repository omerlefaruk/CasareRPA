"""
CasareRPA - Project Folder Entity

Folder/category organization for projects.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FolderColor(Enum):
    """Predefined folder colors."""

    BLUE = "#2196F3"
    GREEN = "#4CAF50"
    ORANGE = "#FF9800"
    RED = "#F44336"
    PURPLE = "#9C27B0"
    TEAL = "#009688"
    PINK = "#E91E63"
    GRAY = "#607D8B"


def generate_folder_id() -> str:
    """Generate unique folder ID."""
    return f"fold_{uuid.uuid4().hex[:8]}"


@dataclass
class ProjectFolder:
    """
    Domain entity representing a folder for organizing projects.

    Supports nested hierarchy with parent-child relationships.

    Attributes:
        id: Unique folder identifier (fold_uuid8)
        name: Folder display name
        parent_id: Parent folder ID (None for root-level folders)
        description: Folder description
        color: Hex color for UI display
        icon: Icon name for UI
        project_ids: List of project IDs in this folder
        is_expanded: UI state - whether folder is expanded in tree
        is_archived: Whether folder is archived/hidden
        sort_order: Order position among siblings
        created_at: Creation timestamp
        modified_at: Last modification timestamp
    """

    id: str
    name: str
    parent_id: str | None = None
    description: str = ""
    color: str = FolderColor.BLUE.value
    icon: str = "folder"
    project_ids: list[str] = field(default_factory=list)
    is_expanded: bool = True
    is_archived: bool = False
    sort_order: int = 0
    created_at: datetime | None = None
    modified_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    @property
    def is_root(self) -> bool:
        """Check if this is a root-level folder."""
        return self.parent_id is None

    @property
    def project_count(self) -> int:
        """Get number of projects in this folder."""
        return len(self.project_ids)

    def add_project(self, project_id: str) -> bool:
        """
        Add a project to this folder.

        Args:
            project_id: Project ID to add

        Returns:
            True if added, False if already exists
        """
        if project_id not in self.project_ids:
            self.project_ids.append(project_id)
            self.touch_modified()
            return True
        return False

    def remove_project(self, project_id: str) -> bool:
        """
        Remove a project from this folder.

        Args:
            project_id: Project ID to remove

        Returns:
            True if removed, False if not found
        """
        if project_id in self.project_ids:
            self.project_ids.remove(project_id)
            self.touch_modified()
            return True
        return False

    def has_project(self, project_id: str) -> bool:
        """Check if project is in this folder."""
        return project_id in self.project_ids

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "project_ids": self.project_ids,
            "is_expanded": self.is_expanded,
            "is_archived": self.is_archived,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectFolder":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        return cls(
            id=data.get("id", generate_folder_id()),
            name=data.get("name", "Unnamed Folder"),
            parent_id=data.get("parent_id"),
            description=data.get("description", ""),
            color=data.get("color", FolderColor.BLUE.value),
            icon=data.get("icon", "folder"),
            project_ids=data.get("project_ids", []),
            is_expanded=data.get("is_expanded", True),
            is_archived=data.get("is_archived", False),
            sort_order=data.get("sort_order", 0),
            created_at=created_at,
            modified_at=modified_at,
        )

    @classmethod
    def create_new(cls, name: str, **kwargs: Any) -> "ProjectFolder":
        """
        Factory method to create a new folder.

        Args:
            name: Folder name
            **kwargs: Additional folder attributes

        Returns:
            New ProjectFolder instance with generated ID
        """
        return cls(id=generate_folder_id(), name=name, **kwargs)

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        parent_info = f", parent='{self.parent_id}'" if self.parent_id else ""
        return f"ProjectFolder(id='{self.id}', name='{self.name}'{parent_info})"


@dataclass
class FoldersFile:
    """
    Container for folder hierarchy stored in folders.json.

    Stores global folder structure for all projects.
    """

    folders: dict[str, ProjectFolder] = field(default_factory=dict)
    schema_version: str = "2.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "folders": {folder_id: folder.to_dict() for folder_id, folder in self.folders.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FoldersFile":
        """Create from dictionary."""
        folders_data = data.get("folders", {})

        folders = {
            folder_id: ProjectFolder.from_dict(folder_data)
            for folder_id, folder_data in folders_data.items()
        }

        return cls(
            folders=folders,
            schema_version=data.get("$schema_version", "2.0.0"),
        )

    def get_folder(self, folder_id: str) -> ProjectFolder | None:
        """Get folder by ID."""
        return self.folders.get(folder_id)

    def add_folder(self, folder: ProjectFolder) -> None:
        """Add or update a folder."""
        self.folders[folder.id] = folder

    def remove_folder(self, folder_id: str) -> bool:
        """Remove a folder. Returns True if removed."""
        if folder_id in self.folders:
            del self.folders[folder_id]
            return True
        return False

    def get_root_folders(self) -> list[ProjectFolder]:
        """Get all root-level folders (no parent)."""
        return [f for f in self.folders.values() if f.is_root and not f.is_archived]

    def get_children(self, parent_id: str) -> list[ProjectFolder]:
        """Get child folders of a parent."""
        return [f for f in self.folders.values() if f.parent_id == parent_id and not f.is_archived]

    def get_folder_path(self, folder_id: str) -> list[str]:
        """
        Get full path from root to folder as list of folder IDs.

        Returns:
            List of folder IDs from root to target folder
        """
        path = []
        current_id = folder_id

        while current_id:
            folder = self.folders.get(current_id)
            if not folder:
                break
            path.insert(0, current_id)
            current_id = folder.parent_id

        return path

    def move_project(
        self,
        project_id: str,
        from_folder_id: str | None,
        to_folder_id: str | None,
    ) -> bool:
        """
        Move a project between folders.

        Args:
            project_id: Project to move
            from_folder_id: Source folder (None if not in any folder)
            to_folder_id: Destination folder (None to remove from folders)

        Returns:
            True if moved successfully
        """
        # Remove from source folder
        if from_folder_id:
            from_folder = self.folders.get(from_folder_id)
            if from_folder:
                from_folder.remove_project(project_id)

        # Add to destination folder
        if to_folder_id:
            to_folder = self.folders.get(to_folder_id)
            if to_folder:
                to_folder.add_project(project_id)
                return True
            return False

        return True
