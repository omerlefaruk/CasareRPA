"""Job domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from casare_rpa.utils.datetime_helpers import parse_datetime


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(Enum):
    """Job priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Job:
    """Job execution domain entity with state machine behavior."""

    id: str
    workflow_id: str
    workflow_name: str
    robot_id: str
    robot_name: str = ""
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    environment: str = "default"
    workflow_json: str = "{}"
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    progress: int = 0  # 0-100 percentage
    current_node: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    logs: str = ""
    error_message: str = ""
    created_at: Optional[datetime] = None
    created_by: str = ""

    # State machine transitions
    VALID_TRANSITIONS = {
        JobStatus.PENDING: [JobStatus.QUEUED, JobStatus.CANCELLED],
        JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELLED],
        JobStatus.RUNNING: [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        ],
        # Terminal states cannot transition
        JobStatus.COMPLETED: [],
        JobStatus.FAILED: [],
        JobStatus.CANCELLED: [],
        JobStatus.TIMEOUT: [],
    }

    def __post_init__(self):
        """Validate domain invariants after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Job ID cannot be empty")
        if not self.workflow_id or not self.workflow_id.strip():
            raise ValueError("Workflow ID cannot be empty")
        if not self.workflow_name or not self.workflow_name.strip():
            raise ValueError("Workflow name cannot be empty")
        if not self.robot_id or not self.robot_id.strip():
            raise ValueError("Robot ID cannot be empty")
        if self.progress < 0 or self.progress > 100:
            raise ValueError(f"Progress must be 0-100, got {self.progress}")
        if self.duration_ms < 0:
            raise ValueError(f"Duration must be >= 0, got {self.duration_ms}")

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state.

        Returns:
            True if job status is terminal (cannot transition further).
        """
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        )

    def can_transition_to(self, new_status: JobStatus) -> bool:
        """Check if job can transition to a new status.

        Args:
            new_status: Target status to transition to.

        Returns:
            True if transition is valid.
        """
        valid_targets = self.VALID_TRANSITIONS.get(self.status, [])
        return new_status in valid_targets

    def transition_to(self, new_status: JobStatus) -> None:
        """Transition job to a new status.

        Args:
            new_status: Target status to transition to.

        Raises:
            JobTransitionError: If transition is invalid.
        """
        from casare_rpa.domain.orchestrator.errors import JobTransitionError

        if not self.can_transition_to(new_status):
            raise JobTransitionError(
                f"Invalid transition from {self.status.value} to {new_status.value}"
            )

        self.status = new_status

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string.

        Returns:
            Human-readable duration (e.g., "1.5s", "2.3m", "1.2h").
        """
        if self.duration_ms == 0:
            return "-"
        seconds = self.duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        hours = minutes / 60
        return f"{hours:.1f}h"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create Job from dictionary.

        Args:
            data: Dictionary with job data.

        Returns:
            Job instance.
        """
        # Convert string enums back to enum instances
        status = data.get("status")
        if isinstance(status, str):
            status = JobStatus(status)
        elif isinstance(status, JobStatus):
            pass
        else:
            status = JobStatus.PENDING

        priority = data.get("priority")
        if isinstance(priority, str):
            priority = JobPriority[priority.upper()]
        elif isinstance(priority, int):
            priority = JobPriority(priority)
        elif isinstance(priority, JobPriority):
            pass
        else:
            priority = JobPriority.NORMAL

        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            workflow_name=data["workflow_name"],
            robot_id=data["robot_id"],
            robot_name=data.get("robot_name", ""),
            status=status,
            priority=priority,
            environment=data.get("environment", "default"),
            workflow_json=data.get("workflow", data.get("workflow_json", "{}")),
            scheduled_time=parse_datetime(data.get("scheduled_time")),
            started_at=parse_datetime(data.get("started_at")),
            completed_at=parse_datetime(data.get("completed_at")),
            duration_ms=data.get("duration_ms", 0),
            progress=data.get("progress", 0),
            current_node=data.get("current_node", ""),
            result=data.get("result", {}),
            logs=data.get("logs", ""),
            error_message=data.get("error_message", ""),
            created_at=parse_datetime(data.get("created_at")),
            created_by=data.get("created_by", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Job to dictionary.

        Returns:
            Dictionary representation of job.
        """
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "status": self.status.value,
            "priority": self.priority.value,
            "environment": self.environment,
            "workflow": self.workflow_json,
            "workflow_json": self.workflow_json,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "progress": self.progress,
            "current_node": self.current_node,
            "result": self.result,
            "logs": self.logs,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }
