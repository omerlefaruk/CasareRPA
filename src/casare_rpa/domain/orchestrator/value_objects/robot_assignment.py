"""RobotAssignment value object for workflow-level robot assignments."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from casare_rpa.utils.datetime_helpers import parse_datetime


@dataclass(frozen=True)
class RobotAssignment:
    """Value object representing a workflow-to-robot assignment.

    RobotAssignment is immutable (frozen=True) and identifies the default robot
    for executing a workflow. When a workflow is triggered, the orchestrator
    first checks for a RobotAssignment to determine which robot should run it.

    Attributes:
        workflow_id: ID of the workflow being assigned.
        robot_id: ID of the robot assigned to run this workflow.
        is_default: Whether this is the default assignment for the workflow.
        priority: Assignment priority (higher = preferred when multiple exist).
        created_at: When this assignment was created.
        created_by: User/system that created this assignment.
        notes: Optional notes about why this assignment was made.
    """

    workflow_id: str
    robot_id: str
    is_default: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    notes: str | None = None

    def __post_init__(self):
        """Validate assignment invariants."""
        if not self.workflow_id or not self.workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")
        if not self.robot_id or not self.robot_id.strip():
            raise ValueError("robot_id cannot be empty")
        if self.priority < 0:
            raise ValueError(f"priority must be >= 0, got {self.priority}")

    def to_dict(self) -> dict:
        """Serialize assignment to dictionary.

        Returns:
            Dictionary representation of the assignment.
        """
        return {
            "workflow_id": self.workflow_id,
            "robot_id": self.robot_id,
            "is_default": self.is_default,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RobotAssignment":
        """Create RobotAssignment from dictionary.

        Args:
            data: Dictionary with assignment data.

        Returns:
            RobotAssignment instance.
        """
        created_at = parse_datetime(data.get("created_at"))
        if created_at is None:
            created_at = datetime.utcnow()

        return cls(
            workflow_id=data["workflow_id"],
            robot_id=data["robot_id"],
            is_default=data.get("is_default", True),
            priority=data.get("priority", 0),
            created_at=created_at,
            created_by=data.get("created_by", ""),
            notes=data.get("notes"),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RobotAssignment(workflow_id={self.workflow_id!r}, "
            f"robot_id={self.robot_id!r}, is_default={self.is_default})"
        )
