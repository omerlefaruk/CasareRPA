"""
Tests for LogEntry domain value objects.

Tests LogLevel enum, LogEntry, LogBatch, LogQuery, and LogStats dataclasses.
Following domain test rules: NO mocks, test pure logic with real domain objects.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from casare_rpa.domain.value_objects.log_entry import (
    LogLevel,
    LogEntry,
    LogBatch,
    LogQuery,
    LogStats,
    DEFAULT_LOG_RETENTION_DAYS,
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
)


# ============================================================================
# LogLevel Enum Tests
# ============================================================================


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_all_levels_exist(self) -> None:
        """All expected log levels are defined."""
        assert LogLevel.TRACE is not None
        assert LogLevel.DEBUG is not None
        assert LogLevel.INFO is not None
        assert LogLevel.WARNING is not None
        assert LogLevel.ERROR is not None
        assert LogLevel.CRITICAL is not None

    def test_level_values(self) -> None:
        """Level values are as expected."""
        assert LogLevel.TRACE.value == "TRACE"
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"


class TestLogLevelFromString:
    """Tests for LogLevel.from_string method."""

    def test_from_string_exact_match(self) -> None:
        """Exact string match returns correct level."""
        assert LogLevel.from_string("TRACE") == LogLevel.TRACE
        assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("WARNING") == LogLevel.WARNING
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("CRITICAL") == LogLevel.CRITICAL

    def test_from_string_case_insensitive(self) -> None:
        """String matching is case-insensitive."""
        assert LogLevel.from_string("trace") == LogLevel.TRACE
        assert LogLevel.from_string("Debug") == LogLevel.DEBUG
        assert LogLevel.from_string("InFo") == LogLevel.INFO

    def test_from_string_with_whitespace(self) -> None:
        """Leading/trailing whitespace is handled."""
        assert LogLevel.from_string("  INFO  ") == LogLevel.INFO
        assert LogLevel.from_string("\tDEBUG\n") == LogLevel.DEBUG

    def test_from_string_aliases(self) -> None:
        """Common aliases map to correct levels."""
        assert LogLevel.from_string("WARN") == LogLevel.WARNING
        assert LogLevel.from_string("ERR") == LogLevel.ERROR
        assert LogLevel.from_string("FATAL") == LogLevel.CRITICAL
        assert LogLevel.from_string("VERBOSE") == LogLevel.TRACE

    def test_from_string_unknown_defaults_to_info(self) -> None:
        """Unknown strings default to INFO."""
        assert LogLevel.from_string("UNKNOWN") == LogLevel.INFO
        assert LogLevel.from_string("CUSTOM") == LogLevel.INFO
        assert LogLevel.from_string("") == LogLevel.INFO


class TestLogLevelSeverity:
    """Tests for LogLevel.severity property."""

    def test_severity_ordering(self) -> None:
        """Severity values are ordered correctly."""
        assert LogLevel.TRACE.severity < LogLevel.DEBUG.severity
        assert LogLevel.DEBUG.severity < LogLevel.INFO.severity
        assert LogLevel.INFO.severity < LogLevel.WARNING.severity
        assert LogLevel.WARNING.severity < LogLevel.ERROR.severity
        assert LogLevel.ERROR.severity < LogLevel.CRITICAL.severity

    def test_severity_values(self) -> None:
        """Severity values are as expected."""
        assert LogLevel.TRACE.severity == 0
        assert LogLevel.DEBUG.severity == 10
        assert LogLevel.INFO.severity == 20
        assert LogLevel.WARNING.severity == 30
        assert LogLevel.ERROR.severity == 40
        assert LogLevel.CRITICAL.severity == 50


class TestLogLevelComparison:
    """Tests for LogLevel comparison operators."""

    def test_greater_than(self) -> None:
        """Greater than comparison works correctly."""
        assert LogLevel.ERROR > LogLevel.WARNING
        assert LogLevel.CRITICAL > LogLevel.DEBUG
        assert not LogLevel.DEBUG > LogLevel.INFO

    def test_greater_than_or_equal(self) -> None:
        """Greater than or equal comparison works correctly."""
        assert LogLevel.ERROR >= LogLevel.ERROR
        assert LogLevel.ERROR >= LogLevel.WARNING
        assert not LogLevel.DEBUG >= LogLevel.INFO

    def test_less_than(self) -> None:
        """Less than comparison works correctly."""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.TRACE < LogLevel.CRITICAL
        assert not LogLevel.ERROR < LogLevel.WARNING

    def test_less_than_or_equal(self) -> None:
        """Less than or equal comparison works correctly."""
        assert LogLevel.DEBUG <= LogLevel.DEBUG
        assert LogLevel.DEBUG <= LogLevel.INFO
        assert not LogLevel.ERROR <= LogLevel.WARNING


# ============================================================================
# LogEntry Tests
# ============================================================================


class TestLogEntryCreation:
    """Tests for LogEntry initialization."""

    def test_create_minimal_entry(self) -> None:
        """Create log entry with required fields only."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test message",
        )
        assert entry.robot_id == "robot-123"
        assert entry.tenant_id == "tenant-456"
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.id is not None  # Auto-generated
        assert entry.source is None
        assert entry.extra is None

    def test_create_full_entry(self) -> None:
        """Create log entry with all fields."""
        timestamp = datetime.now(timezone.utc)
        entry = LogEntry(
            id="entry-789",
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=timestamp,
            level=LogLevel.ERROR,
            message="Error occurred",
            source="test_module",
            extra={"key": "value"},
        )
        assert entry.id == "entry-789"
        assert entry.robot_id == "robot-123"
        assert entry.tenant_id == "tenant-456"
        assert entry.timestamp == timestamp
        assert entry.level == LogLevel.ERROR
        assert entry.message == "Error occurred"
        assert entry.source == "test_module"
        assert entry.extra == {"key": "value"}

    def test_auto_generated_id_is_uuid(self) -> None:
        """Auto-generated ID is a valid UUID string."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test",
        )
        # UUID format: 8-4-4-4-12 = 36 chars
        assert len(entry.id) == 36
        assert entry.id.count("-") == 4


class TestLogEntryValidation:
    """Tests for LogEntry validation."""

    def test_empty_robot_id_raises_error(self) -> None:
        """Empty robot_id raises ValueError."""
        with pytest.raises(ValueError, match="robot_id is required"):
            LogEntry(
                robot_id="",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message="Test",
            )

    def test_empty_tenant_id_raises_error(self) -> None:
        """Empty tenant_id raises ValueError."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            LogEntry(
                robot_id="robot-123",
                tenant_id="",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message="Test",
            )

    def test_empty_message_raises_error(self) -> None:
        """Empty message raises ValueError."""
        with pytest.raises(ValueError, match="message is required"):
            LogEntry(
                robot_id="robot-123",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message="",
            )


class TestLogEntryImmutability:
    """Tests for LogEntry immutability (frozen dataclass)."""

    def test_frozen_dataclass(self) -> None:
        """LogEntry is immutable (frozen)."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test",
        )
        with pytest.raises(AttributeError):
            entry.message = "Modified"


class TestLogEntrySerializationToDict:
    """Tests for LogEntry.to_dict method."""

    def test_to_dict_all_fields(self) -> None:
        """Serialize entry with all fields."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        entry = LogEntry(
            id="entry-123",
            robot_id="robot-456",
            tenant_id="tenant-789",
            timestamp=timestamp,
            level=LogLevel.WARNING,
            message="Warning message",
            source="test_source",
            extra={"key": "value"},
        )
        data = entry.to_dict()

        assert data["id"] == "entry-123"
        assert data["robot_id"] == "robot-456"
        assert data["tenant_id"] == "tenant-789"
        assert data["timestamp"] == "2024-01-15T10:30:00+00:00"
        assert data["level"] == "WARNING"
        assert data["message"] == "Warning message"
        assert data["source"] == "test_source"
        assert data["extra"] == {"key": "value"}

    def test_to_dict_minimal_fields(self) -> None:
        """Serialize entry with minimal fields."""
        timestamp = datetime.now(timezone.utc)
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=timestamp,
            level=LogLevel.INFO,
            message="Test",
        )
        data = entry.to_dict()

        assert data["source"] is None
        assert data["extra"] is None


class TestLogEntrySerializationFromDict:
    """Tests for LogEntry.from_dict method."""

    def test_from_dict_all_fields(self) -> None:
        """Deserialize entry with all fields."""
        data = {
            "id": "entry-123",
            "robot_id": "robot-456",
            "tenant_id": "tenant-789",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": "ERROR",
            "message": "Error message",
            "source": "test_source",
            "extra": {"key": "value"},
        }
        entry = LogEntry.from_dict(data)

        assert entry.id == "entry-123"
        assert entry.robot_id == "robot-456"
        assert entry.tenant_id == "tenant-789"
        assert entry.level == LogLevel.ERROR
        assert entry.message == "Error message"
        assert entry.source == "test_source"
        assert entry.extra == {"key": "value"}

    def test_from_dict_with_z_suffix_timestamp(self) -> None:
        """Handle Z suffix in timestamp."""
        data = {
            "robot_id": "robot-123",
            "tenant_id": "tenant-456",
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "message": "Test",
        }
        entry = LogEntry.from_dict(data)
        assert entry.timestamp.tzinfo is not None

    def test_from_dict_without_timestamp(self) -> None:
        """Handle missing timestamp (uses current time)."""
        data = {
            "robot_id": "robot-123",
            "tenant_id": "tenant-456",
            "level": "INFO",
            "message": "Test",
        }
        before = datetime.now(timezone.utc)
        entry = LogEntry.from_dict(data)
        after = datetime.now(timezone.utc)

        assert before <= entry.timestamp <= after

    def test_from_dict_level_string(self) -> None:
        """Handle level as string."""
        data = {
            "robot_id": "robot-123",
            "tenant_id": "tenant-456",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": "WARNING",
            "message": "Test",
        }
        entry = LogEntry.from_dict(data)
        assert entry.level == LogLevel.WARNING

    def test_from_dict_level_enum(self) -> None:
        """Handle level as LogLevel enum."""
        data = {
            "robot_id": "robot-123",
            "tenant_id": "tenant-456",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": LogLevel.ERROR,
            "message": "Test",
        }
        entry = LogEntry.from_dict(data)
        assert entry.level == LogLevel.ERROR

    def test_from_dict_auto_generates_id(self) -> None:
        """Auto-generate ID if not provided."""
        data = {
            "robot_id": "robot-123",
            "tenant_id": "tenant-456",
            "message": "Test",
        }
        entry = LogEntry.from_dict(data)
        assert entry.id is not None
        assert len(entry.id) == 36  # UUID format

    def test_roundtrip_serialization(self) -> None:
        """Serialize then deserialize preserves data."""
        original = LogEntry(
            id="entry-123",
            robot_id="robot-456",
            tenant_id="tenant-789",
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            level=LogLevel.ERROR,
            message="Test message",
            source="test_source",
            extra={"key": "value"},
        )
        data = original.to_dict()
        restored = LogEntry.from_dict(data)

        assert restored.id == original.id
        assert restored.robot_id == original.robot_id
        assert restored.tenant_id == original.tenant_id
        assert restored.level == original.level
        assert restored.message == original.message
        assert restored.source == original.source
        assert restored.extra == original.extra


# ============================================================================
# LogBatch Tests
# ============================================================================


class TestLogBatchCreation:
    """Tests for LogBatch initialization."""

    def test_create_batch(self) -> None:
        """Create log batch with entries."""
        entry1 = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Message 1",
        )
        entry2 = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.DEBUG,
            message="Message 2",
        )

        batch = LogBatch(
            robot_id="robot-123",
            entries=(entry1, entry2),
            sequence=42,
        )

        assert batch.robot_id == "robot-123"
        assert len(batch.entries) == 2
        assert batch.sequence == 42

    def test_create_empty_batch(self) -> None:
        """Create batch with no entries."""
        batch = LogBatch(
            robot_id="robot-123",
            entries=(),
        )
        assert len(batch.entries) == 0
        assert batch.sequence == 0


class TestLogBatchSerialization:
    """Tests for LogBatch serialization."""

    def test_to_dict(self) -> None:
        """Serialize batch to dictionary."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            level=LogLevel.INFO,
            message="Test message",
            source="test_source",
            extra={"key": "value"},
        )
        batch = LogBatch(
            robot_id="robot-123",
            entries=(entry,),
            sequence=1,
        )

        data = batch.to_dict()

        assert data["type"] == "log_batch"
        assert data["robot_id"] == "robot-123"
        assert data["sequence"] == 1
        assert len(data["logs"]) == 1
        assert data["logs"][0]["level"] == "INFO"
        assert data["logs"][0]["message"] == "Test message"

    def test_from_dict(self) -> None:
        """Deserialize batch from dictionary."""
        data = {
            "robot_id": "robot-123",
            "sequence": 5,
            "logs": [
                {
                    "timestamp": "2024-01-15T10:30:00+00:00",
                    "level": "ERROR",
                    "message": "Error 1",
                    "source": "test",
                },
                {
                    "timestamp": "2024-01-15T10:30:01+00:00",
                    "level": "WARNING",
                    "message": "Warning 1",
                },
            ],
        }

        batch = LogBatch.from_dict(data, tenant_id="tenant-456")

        assert batch.robot_id == "robot-123"
        assert batch.sequence == 5
        assert len(batch.entries) == 2
        assert batch.entries[0].level == LogLevel.ERROR
        assert batch.entries[0].tenant_id == "tenant-456"
        assert batch.entries[1].level == LogLevel.WARNING

    def test_from_dict_empty_logs(self) -> None:
        """Handle batch with no logs."""
        data = {
            "robot_id": "robot-123",
            "logs": [],
        }
        batch = LogBatch.from_dict(data, tenant_id="tenant-456")
        assert len(batch.entries) == 0


# ============================================================================
# LogQuery Tests
# ============================================================================


class TestLogQueryCreation:
    """Tests for LogQuery initialization."""

    def test_create_minimal_query(self) -> None:
        """Create query with required fields only."""
        query = LogQuery(tenant_id="tenant-123")

        assert query.tenant_id == "tenant-123"
        assert query.robot_id is None
        assert query.start_time is None
        assert query.end_time is None
        assert query.min_level == LogLevel.DEBUG
        assert query.source is None
        assert query.search_text is None
        assert query.limit == 100
        assert query.offset == 0

    def test_create_full_query(self) -> None:
        """Create query with all fields."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        query = LogQuery(
            tenant_id="tenant-123",
            robot_id="robot-456",
            start_time=start,
            end_time=end,
            min_level=LogLevel.WARNING,
            source="test_source",
            search_text="error",
            limit=50,
            offset=10,
        )

        assert query.tenant_id == "tenant-123"
        assert query.robot_id == "robot-456"
        assert query.start_time == start
        assert query.end_time == end
        assert query.min_level == LogLevel.WARNING
        assert query.source == "test_source"
        assert query.search_text == "error"
        assert query.limit == 50
        assert query.offset == 10


class TestLogQueryValidation:
    """Tests for LogQuery validation."""

    def test_empty_tenant_id_raises_error(self) -> None:
        """Empty tenant_id raises ValueError."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            LogQuery(tenant_id="")

    def test_limit_too_small_raises_error(self) -> None:
        """Limit less than 1 raises ValueError."""
        with pytest.raises(ValueError, match="limit must be between 1 and 10000"):
            LogQuery(tenant_id="tenant-123", limit=0)

    def test_limit_too_large_raises_error(self) -> None:
        """Limit greater than 10000 raises ValueError."""
        with pytest.raises(ValueError, match="limit must be between 1 and 10000"):
            LogQuery(tenant_id="tenant-123", limit=10001)

    def test_negative_offset_raises_error(self) -> None:
        """Negative offset raises ValueError."""
        with pytest.raises(ValueError, match="offset cannot be negative"):
            LogQuery(tenant_id="tenant-123", offset=-1)


class TestLogQuerySerialization:
    """Tests for LogQuery serialization."""

    def test_to_dict(self) -> None:
        """Serialize query to dictionary."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        query = LogQuery(
            tenant_id="tenant-123",
            robot_id="robot-456",
            start_time=start,
            end_time=end,
            min_level=LogLevel.ERROR,
            source="test",
            search_text="error",
            limit=25,
            offset=5,
        )

        data = query.to_dict()

        assert data["tenant_id"] == "tenant-123"
        assert data["robot_id"] == "robot-456"
        assert data["start_time"] == "2024-01-01T00:00:00+00:00"
        assert data["end_time"] == "2024-01-31T00:00:00+00:00"
        assert data["min_level"] == "ERROR"
        assert data["source"] == "test"
        assert data["search_text"] == "error"
        assert data["limit"] == 25
        assert data["offset"] == 5

    def test_to_dict_optional_fields_none(self) -> None:
        """Serialize query with optional fields as None."""
        query = LogQuery(tenant_id="tenant-123")
        data = query.to_dict()

        assert data["robot_id"] is None
        assert data["start_time"] is None
        assert data["end_time"] is None


# ============================================================================
# LogStats Tests
# ============================================================================


class TestLogStatsCreation:
    """Tests for LogStats initialization."""

    def test_create_stats(self) -> None:
        """Create stats with all fields."""
        oldest = datetime(2024, 1, 1, tzinfo=timezone.utc)
        newest = datetime(2024, 1, 31, tzinfo=timezone.utc)

        stats = LogStats(
            tenant_id="tenant-123",
            robot_id="robot-456",
            total_count=1000,
            by_level={
                "TRACE": 100,
                "DEBUG": 200,
                "INFO": 400,
                "WARNING": 200,
                "ERROR": 80,
                "CRITICAL": 20,
            },
            oldest_log=oldest,
            newest_log=newest,
            storage_bytes=512000,
        )

        assert stats.tenant_id == "tenant-123"
        assert stats.robot_id == "robot-456"
        assert stats.total_count == 1000
        assert stats.by_level["INFO"] == 400
        assert stats.oldest_log == oldest
        assert stats.newest_log == newest
        assert stats.storage_bytes == 512000

    def test_create_empty_stats(self) -> None:
        """Create stats for empty log set."""
        stats = LogStats(
            tenant_id="tenant-123",
            total_count=0,
            by_level={},
            oldest_log=None,
            newest_log=None,
            storage_bytes=0,
        )

        assert stats.total_count == 0
        assert stats.oldest_log is None
        assert stats.newest_log is None


class TestLogStatsSerialization:
    """Tests for LogStats serialization."""

    def test_to_dict(self) -> None:
        """Serialize stats to dictionary."""
        oldest = datetime(2024, 1, 1, tzinfo=timezone.utc)
        newest = datetime(2024, 1, 31, tzinfo=timezone.utc)

        stats = LogStats(
            tenant_id="tenant-123",
            robot_id="robot-456",
            total_count=500,
            by_level={"INFO": 300, "ERROR": 200},
            oldest_log=oldest,
            newest_log=newest,
            storage_bytes=256000,
        )

        data = stats.to_dict()

        assert data["tenant_id"] == "tenant-123"
        assert data["robot_id"] == "robot-456"
        assert data["total_count"] == 500
        assert data["by_level"] == {"INFO": 300, "ERROR": 200}
        assert data["oldest_log"] == "2024-01-01T00:00:00+00:00"
        assert data["newest_log"] == "2024-01-31T00:00:00+00:00"
        assert data["storage_bytes"] == 256000

    def test_to_dict_with_none_dates(self) -> None:
        """Serialize stats with None dates."""
        stats = LogStats(
            tenant_id="tenant-123",
            total_count=0,
            by_level={},
            oldest_log=None,
            newest_log=None,
            storage_bytes=0,
        )
        data = stats.to_dict()

        assert data["oldest_log"] is None
        assert data["newest_log"] is None


# ============================================================================
# Module Constants Tests
# ============================================================================


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_default_retention_days(self) -> None:
        """Default retention is 30 days."""
        assert DEFAULT_LOG_RETENTION_DAYS == 30

    def test_max_batch_size(self) -> None:
        """Max batch size is 100."""
        assert MAX_LOG_BATCH_SIZE == 100

    def test_offline_buffer_size(self) -> None:
        """Offline buffer size is 1000."""
        assert OFFLINE_BUFFER_SIZE == 1000
