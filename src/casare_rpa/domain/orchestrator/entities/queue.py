"""
Queue domain entities for transaction queue management.

Provides UiPath-style transaction queue entities:
- Queue: Queue definition with schema and retry settings
- QueueItem: Individual transaction item in a queue
- QueueItemStatus: Status enum for queue items
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from casare_rpa.utils.datetime_helpers import parse_datetime


class QueueItemStatus(Enum):
    """Queue item status values."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    RETRY = "retry"
    DELETED = "deleted"


@dataclass
class Queue:
    """
    Queue definition domain entity.

    Represents a transaction queue with schema validation,
    retry settings, and configuration for dispatcher/performer pattern.
    """

    id: str
    name: str
    description: str = ""
    schema: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay_seconds: int = 60
    auto_retry: bool = True
    enforce_unique_reference: bool = False
    item_count: int = 0
    new_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    created_at: datetime | None = None
    created_by: str = ""

    def __post_init__(self):
        """Validate domain invariants."""
        if not self.id or not self.id.strip():
            raise ValueError("Queue ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Queue name cannot be empty")
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be >= 0, got {self.max_retries}")
        if self.retry_delay_seconds < 0:
            raise ValueError(f"Retry delay must be >= 0, got {self.retry_delay_seconds}")

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.completed_count + self.failed_count
        if total == 0:
            return 0.0
        return (self.completed_count / total) * 100

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Queue":
        """Create Queue from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            schema=data.get("schema", {}),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 60),
            auto_retry=data.get("auto_retry", True),
            enforce_unique_reference=data.get("enforce_unique_reference", False),
            item_count=data.get("item_count", 0),
            new_count=data.get("new_count", 0),
            in_progress_count=data.get("in_progress_count", 0),
            completed_count=data.get("completed_count", 0),
            failed_count=data.get("failed_count", 0),
            created_at=parse_datetime(data.get("created_at")),
            created_by=data.get("created_by", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Queue to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "auto_retry": self.auto_retry,
            "enforce_unique_reference": self.enforce_unique_reference,
            "item_count": self.item_count,
            "new_count": self.new_count,
            "in_progress_count": self.in_progress_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


@dataclass
class QueueItem:
    """
    Queue item (transaction) domain entity.

    Represents a single item in a transaction queue with
    status tracking, retry handling, and robot assignment.
    """

    id: str
    queue_id: str
    reference: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    status: QueueItemStatus = QueueItemStatus.NEW
    priority: int = 1
    retries: int = 0
    robot_id: str | None = None
    robot_name: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline: datetime | None = None
    postpone_until: datetime | None = None
    error_message: str = ""
    error_type: str = ""
    processing_exception_type: str = ""
    duration_ms: int = 0
    created_at: datetime | None = None

    def __post_init__(self):
        """Validate domain invariants."""
        if not self.id or not self.id.strip():
            raise ValueError("Queue item ID cannot be empty")
        if not self.queue_id or not self.queue_id.strip():
            raise ValueError("Queue ID cannot be empty")
        if self.priority < 0:
            raise ValueError(f"Priority must be >= 0, got {self.priority}")
        if self.retries < 0:
            raise ValueError(f"Retries must be >= 0, got {self.retries}")
        if self.duration_ms < 0:
            raise ValueError(f"Duration must be >= 0, got {self.duration_ms}")

    def is_terminal(self) -> bool:
        """Check if item is in a terminal state."""
        return self.status in (
            QueueItemStatus.COMPLETED,
            QueueItemStatus.FAILED,
            QueueItemStatus.ABANDONED,
            QueueItemStatus.DELETED,
        )

    def can_retry(self, max_retries: int) -> bool:
        """Check if item can be retried."""
        return self.status == QueueItemStatus.FAILED and self.retries < max_retries

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
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
    def from_dict(cls, data: dict[str, Any]) -> "QueueItem":
        """Create QueueItem from dictionary."""
        status = data.get("status")
        if isinstance(status, str):
            status = QueueItemStatus(status)
        elif isinstance(status, QueueItemStatus):
            pass
        else:
            status = QueueItemStatus.NEW

        return cls(
            id=data["id"],
            queue_id=data["queue_id"],
            reference=data.get("reference", ""),
            data=data.get("data", {}),
            output=data.get("output", {}),
            status=status,
            priority=data.get("priority", 1),
            retries=data.get("retries", 0),
            robot_id=data.get("robot_id"),
            robot_name=data.get("robot_name", ""),
            started_at=parse_datetime(data.get("started_at")),
            completed_at=parse_datetime(data.get("completed_at")),
            deadline=parse_datetime(data.get("deadline")),
            postpone_until=parse_datetime(data.get("postpone_until")),
            error_message=data.get("error_message", ""),
            error_type=data.get("error_type", ""),
            processing_exception_type=data.get("processing_exception_type", ""),
            duration_ms=data.get("duration_ms", 0),
            created_at=parse_datetime(data.get("created_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert QueueItem to dictionary."""
        return {
            "id": self.id,
            "queue_id": self.queue_id,
            "reference": self.reference,
            "data": self.data,
            "output": self.output,
            "status": self.status.value,
            "priority": self.priority,
            "retries": self.retries,
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "postpone_until": self.postpone_until.isoformat() if self.postpone_until else None,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "processing_exception_type": self.processing_exception_type,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
