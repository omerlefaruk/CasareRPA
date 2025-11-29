"""Workflow domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    execution_count: int = 0
    success_count: int = 0
    avg_duration_ms: int = 0

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
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
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

        # Parse datetime strings
        def parse_datetime(value):
            if value is None or value == "":
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return None
            return None

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

    def to_dict(self) -> Dict[str, Any]:
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
