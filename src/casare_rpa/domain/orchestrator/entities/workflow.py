"""Workflow domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


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
