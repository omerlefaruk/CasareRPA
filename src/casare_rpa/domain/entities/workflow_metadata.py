"""
CasareRPA - Domain Entity: Workflow Metadata
Represents workflow identity and versioning information.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..value_objects.types import SCHEMA_VERSION


class WorkflowMetadata:
    """
    Workflow metadata entity - represents workflow identity and versioning.

    This entity contains descriptive information about a workflow including
    its name, author, version, and timestamps. It is part of the WorkflowSchema
    aggregate root.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize workflow metadata.

        Args:
            name: Workflow name (required, non-empty)
            description: Workflow description
            author: Workflow creator
            version: Workflow version
            tags: List of tags for categorization

        Raises:
            ValueError: If name is empty or whitespace-only
        """
        self._validate_name(name)
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.schema_version = SCHEMA_VERSION

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate workflow name."""
        if not name or not name.strip():
            raise ValueError("Workflow name cannot be empty or whitespace-only")
        if len(name) > 255:
            raise ValueError(f"Workflow name too long: {len(name)} chars (max 255)")

    def update_modified_timestamp(self) -> None:
        """Update the modified timestamp to current time."""
        self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize metadata to dictionary.

        Returns:
            Dictionary representation of metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowMetadata":
        """
        Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            WorkflowMetadata instance
        """
        metadata = cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
        )
        metadata.created_at = data.get("created_at", metadata.created_at)
        metadata.modified_at = data.get("modified_at", metadata.modified_at)
        metadata.schema_version = data.get("schema_version", SCHEMA_VERSION)
        return metadata

    def __repr__(self) -> str:
        """String representation."""
        return f"WorkflowMetadata(name='{self.name}', version='{self.version}')"
