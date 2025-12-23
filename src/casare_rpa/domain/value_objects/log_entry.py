"""
LogEntry Value Object for Robot Log Streaming.

Defines immutable log entry value objects for streaming robot logs
to the orchestrator with 30-day retention policy.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Union

# Type alias for JSON-serializable log extra data
JsonValue = Union[str, int, float, bool, None, list, dict]
LogExtraData = dict[str, JsonValue]


class LogLevel(Enum):
    """Log severity level."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """
        Convert string to LogLevel.

        Args:
            level: Level string (case-insensitive).

        Returns:
            LogLevel enum value.
        """
        normalized = level.upper().strip()
        try:
            return cls(normalized)
        except ValueError:
            # Map common aliases
            aliases = {
                "WARN": cls.WARNING,
                "ERR": cls.ERROR,
                "FATAL": cls.CRITICAL,
                "VERBOSE": cls.TRACE,
            }
            return aliases.get(normalized, cls.INFO)

    @property
    def severity(self) -> int:
        """Get numeric severity (higher = more severe)."""
        severity_map = {
            LogLevel.TRACE: 0,
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50,
        }
        return severity_map.get(self, 20)

    def __ge__(self, other: "LogLevel") -> bool:
        """Compare severity levels."""
        return self.severity >= other.severity

    def __gt__(self, other: "LogLevel") -> bool:
        """Compare severity levels."""
        return self.severity > other.severity

    def __le__(self, other: "LogLevel") -> bool:
        """Compare severity levels."""
        return self.severity <= other.severity

    def __lt__(self, other: "LogLevel") -> bool:
        """Compare severity levels."""
        return self.severity < other.severity


@dataclass(frozen=True)
class LogEntry:
    """
    Immutable log entry value object.

    Represents a single log message from a robot, including
    metadata for routing and retention.

    Attributes:
        id: Unique identifier for the log entry.
        robot_id: ID of the robot that generated this log.
        tenant_id: Tenant ID for multi-tenancy isolation.
        timestamp: When the log was generated.
        level: Log severity level.
        message: The log message content.
        source: Optional source identifier (module, node type, etc.).
        extra: Optional additional structured data.
    """

    robot_id: str
    tenant_id: str
    timestamp: datetime
    level: LogLevel
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str | None = None
    extra: LogExtraData | None = None

    def __post_init__(self) -> None:
        """Validate log entry data."""
        if not self.robot_id:
            raise ValueError("robot_id is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.message:
            raise ValueError("message is required")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "id": self.id,
            "robot_id": self.robot_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with log entry fields.

        Returns:
            LogEntry instance.
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            # Parse ISO format timestamp
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(UTC)

        level = data.get("level", "INFO")
        if isinstance(level, str):
            level = LogLevel.from_string(level)
        elif not isinstance(level, LogLevel):
            level = LogLevel.INFO

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            robot_id=data["robot_id"],
            tenant_id=data["tenant_id"],
            timestamp=timestamp,
            level=level,
            message=data["message"],
            source=data.get("source"),
            extra=data.get("extra"),
        )


@dataclass(frozen=True)
class LogBatch:
    """
    Batch of log entries for efficient transmission.

    Attributes:
        robot_id: ID of the robot sending the batch.
        entries: List of log entries.
        sequence: Sequence number for ordering/deduplication.
    """

    robot_id: str
    entries: tuple  # Tuple of LogEntry for immutability
    sequence: int = 0

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary for WebSocket transmission.

        Returns:
            Dictionary representation.
        """
        return {
            "type": "log_batch",
            "robot_id": self.robot_id,
            "sequence": self.sequence,
            "logs": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "level": e.level.value,
                    "message": e.message,
                    "source": e.source,
                    "extra": e.extra,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], tenant_id: str) -> "LogBatch":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with batch data.
            tenant_id: Tenant ID to assign to entries.

        Returns:
            LogBatch instance.
        """
        robot_id = data["robot_id"]
        entries = []

        for log_data in data.get("logs", []):
            entry_data = {
                "robot_id": robot_id,
                "tenant_id": tenant_id,
                **log_data,
            }
            entries.append(LogEntry.from_dict(entry_data))

        return cls(
            robot_id=robot_id,
            entries=tuple(entries),
            sequence=data.get("sequence", 0),
        )


@dataclass(frozen=True)
class LogQuery:
    """
    Query parameters for searching logs.

    Attributes:
        robot_id: Filter by robot ID (optional).
        tenant_id: Filter by tenant ID (required for multi-tenancy).
        start_time: Start of time range.
        end_time: End of time range.
        min_level: Minimum log level to include.
        source: Filter by source.
        search_text: Full-text search in message.
        limit: Maximum number of results.
        offset: Pagination offset.
    """

    tenant_id: str
    robot_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    min_level: LogLevel = LogLevel.DEBUG
    source: str | None = None
    search_text: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate query parameters."""
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if self.limit < 1 or self.limit > 10000:
            raise ValueError("limit must be between 1 and 10000")
        if self.offset < 0:
            raise ValueError("offset cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "tenant_id": self.tenant_id,
            "robot_id": self.robot_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "min_level": self.min_level.value,
            "source": self.source,
            "search_text": self.search_text,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass(frozen=True)
class LogStats:
    """
    Log statistics summary.

    Attributes:
        tenant_id: Tenant ID.
        robot_id: Robot ID (optional, if robot-specific).
        total_count: Total log entries.
        by_level: Count by log level.
        oldest_log: Timestamp of oldest log.
        newest_log: Timestamp of newest log.
        storage_bytes: Estimated storage usage.
    """

    tenant_id: str
    total_count: int
    by_level: dict[str, int]
    oldest_log: datetime | None
    newest_log: datetime | None
    storage_bytes: int
    robot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "tenant_id": self.tenant_id,
            "robot_id": self.robot_id,
            "total_count": self.total_count,
            "by_level": self.by_level,
            "oldest_log": self.oldest_log.isoformat() if self.oldest_log else None,
            "newest_log": self.newest_log.isoformat() if self.newest_log else None,
            "storage_bytes": self.storage_bytes,
        }


# Default retention period in days
DEFAULT_LOG_RETENTION_DAYS: int = 30

# Maximum batch size for log transmission
MAX_LOG_BATCH_SIZE: int = 100

# Buffer size for offline log storage
OFFLINE_BUFFER_SIZE: int = 1000


__all__ = [
    "LogLevel",
    "LogEntry",
    "LogBatch",
    "LogQuery",
    "LogStats",
    "DEFAULT_LOG_RETENTION_DAYS",
    "MAX_LOG_BATCH_SIZE",
    "OFFLINE_BUFFER_SIZE",
]
