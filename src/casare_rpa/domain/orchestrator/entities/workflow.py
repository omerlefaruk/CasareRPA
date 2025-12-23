"""Workflow domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from casare_rpa.utils.datetime_helpers import parse_datetime


class WorkflowStatus(Enum):
    """Workflow lifecycle status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Workflow:
    """Workflow definition domain entity."""

    id: str
    name: str
    description: str = ""
    json_definition: str = "{}"
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    execution_count: int = 0
    success_count: int = 0
    avg_duration_ms: int = 0

    def __post_init__(self):
        """Validate domain invariants after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Workflow ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Workflow name cannot be empty")
        if self.version < 1:
            raise ValueError(f"Version must be >= 1, got {self.version}")
        if self.execution_count < 0:
            raise ValueError(f"Execution count must be >= 0, got {self.execution_count}")
        if self.success_count < 0:
            raise ValueError(f"Success count must be >= 0, got {self.success_count}")
        if self.success_count > self.execution_count:
            raise ValueError(
                f"Success count ({self.success_count}) cannot exceed "
                f"execution count ({self.execution_count})"
            )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage.

        Returns:
            Success rate as percentage (0-100).
        """
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        """Create Workflow from dictionary.

        Args:
            data: Dictionary with workflow data.

        Returns:
            Workflow instance.
        """
        # Convert string status to enum
        status = data.get("status")
        if isinstance(status, str):
            status = WorkflowStatus(status)
        elif isinstance(status, WorkflowStatus):
            pass
        else:
            status = WorkflowStatus.DRAFT

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            json_definition=data.get("json_definition", "{}"),
            version=data.get("version", 1),
            status=status,
            created_by=data.get("created_by", ""),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
            tags=data.get("tags", []),
            execution_count=data.get("execution_count", 0),
            success_count=data.get("success_count", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Workflow to dictionary.

        Returns:
            Dictionary representation of workflow.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "json_definition": self.json_definition,
            "version": self.version,
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "avg_duration_ms": self.avg_duration_ms,
        }
