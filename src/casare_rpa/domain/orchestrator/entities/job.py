"""Job domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


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
