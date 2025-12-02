"""
Tests for LogRepository.

Mock ALL external APIs (asyncpg, database connections).
Test CRUD operations, batch saves, cleanup, and partition management.
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.domain.value_objects.log_entry import (
    LogEntry,
    LogLevel,
    LogQuery,
    LogStats,
    DEFAULT_LOG_RETENTION_DAYS,
)
from casare_rpa.infrastructure.persistence.repositories.log_repository import (
    LogRepository,
)


@pytest.fixture
def mock_pool_manager() -> AsyncMock:
    """Create mock database pool manager."""
    manager = AsyncMock()
    pool = AsyncMock()
    conn = AsyncMock()

    manager.get_pool.return_value = pool
    pool.acquire.return_value = conn
    pool.release = AsyncMock()

    return manager


@pytest.fixture
def mock_connection(mock_pool_manager: AsyncMock) -> AsyncMock:
    """Get mock database connection from pool manager."""
    return mock_pool_manager.get_pool.return_value.acquire.return_value


@pytest.fixture
def log_repository(mock_pool_manager: AsyncMock) -> LogRepository:
    """Create LogRepository with mock pool manager."""
    return LogRepository(pool_manager=mock_pool_manager)


@pytest.fixture
def sample_log_entry() -> LogEntry:
    """Create sample log entry for testing."""
    return LogEntry(
        id="entry-123",
        robot_id="robot-456",
        tenant_id="tenant-789",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        level=LogLevel.INFO,
        message="Test log message",
        source="test_module",
        extra={"key": "value"},
    )


# ============================================================================
# Save Single Entry Tests
# ============================================================================


class TestLogRepositorySave:
    """Tests for LogRepository.save method."""

    @pytest.mark.asyncio
    async def test_save_entry_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Save single entry executes correct SQL."""
        mock_connection.execute.return_value = None

        result = await log_repository.save(sample_log_entry)

        assert result == sample_log_entry
        mock_connection.execute.assert_awaited_once()

        # Verify SQL contains correct table
        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO robot_logs" in sql
        assert "id, robot_id, tenant_id, timestamp, level" in sql

    @pytest.mark.asyncio
    async def test_save_entry_parameters(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Save passes correct parameters."""
        mock_connection.execute.return_value = None

        await log_repository.save(sample_log_entry)

        call_args = mock_connection.execute.call_args
        params = call_args[0][1:]

        assert params[0] == "entry-123"  # id
        assert params[1] == "robot-456"  # robot_id
        assert params[2] == "tenant-789"  # tenant_id
        assert params[4] == "INFO"  # level value

    @pytest.mark.asyncio
    async def test_save_entry_error_propagates(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Database errors are propagated."""
        mock_connection.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await log_repository.save(sample_log_entry)

    @pytest.mark.asyncio
    async def test_save_releases_connection(
        self,
        log_repository: LogRepository,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Connection is released after save."""
        mock_connection.execute.return_value = None

        await log_repository.save(sample_log_entry)

        pool = await mock_pool_manager.get_pool()
        pool.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Save Batch Tests
# ============================================================================


class TestLogRepositorySaveBatch:
    """Tests for LogRepository.save_batch method."""

    @pytest.mark.asyncio
    async def test_save_batch_empty_returns_zero(
        self,
        log_repository: LogRepository,
    ) -> None:
        """Empty batch returns 0 without database call."""
        result = await log_repository.save_batch([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_save_batch_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Save batch inserts all entries."""
        entries = [
            LogEntry(
                id=f"entry-{i}",
                robot_id="robot-123",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message=f"Message {i}",
            )
            for i in range(3)
        ]
        mock_connection.executemany.return_value = None

        result = await log_repository.save_batch(entries)

        assert result == 3
        mock_connection.executemany.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_batch_uses_conflict_handling(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Batch insert uses ON CONFLICT DO NOTHING."""
        mock_connection.executemany.return_value = None

        await log_repository.save_batch([sample_log_entry])

        call_args = mock_connection.executemany.call_args
        sql = call_args[0][0]
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql

    @pytest.mark.asyncio
    async def test_save_batch_error_propagates(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
        sample_log_entry: LogEntry,
    ) -> None:
        """Batch database errors are propagated."""
        mock_connection.executemany.side_effect = Exception("Batch error")

        with pytest.raises(Exception, match="Batch error"):
            await log_repository.save_batch([sample_log_entry])


# ============================================================================
# Query Tests
# ============================================================================


class TestLogRepositoryQuery:
    """Tests for LogRepository.query method."""

    @pytest.mark.asyncio
    async def test_query_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Query returns parsed log entries."""
        mock_rows = [
            {
                "id": "entry-1",
                "robot_id": "robot-123",
                "tenant_id": "tenant-456",
                "timestamp": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                "level": "INFO",
                "message": "Test message",
                "source": "test",
                "extra": {},
            }
        ]
        mock_connection.fetch.return_value = mock_rows

        query = LogQuery(tenant_id="tenant-456")
        results = await log_repository.query(query)

        assert len(results) == 1
        assert results[0].id == "entry-1"
        assert results[0].level == LogLevel.INFO

    @pytest.mark.asyncio
    async def test_query_passes_all_parameters(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Query passes all filter parameters."""
        mock_connection.fetch.return_value = []

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
        await log_repository.query(query)

        call_args = mock_connection.fetch.call_args
        params = call_args[0][1:]

        assert params[0] == "tenant-123"  # tenant_id
        assert params[1] == "robot-456"  # robot_id
        assert params[2] == start  # start_time
        assert params[3] == end  # end_time
        assert params[4] == "WARNING"  # min_level
        assert params[5] == "test_source"  # source
        assert params[6] == "error"  # search_text
        assert params[7] == 50  # limit
        assert params[8] == 10  # offset

    @pytest.mark.asyncio
    async def test_query_empty_result(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Empty query result returns empty list."""
        mock_connection.fetch.return_value = []

        query = LogQuery(tenant_id="tenant-123")
        results = await log_repository.query(query)

        assert results == []


# ============================================================================
# Get By Robot Tests
# ============================================================================


class TestLogRepositoryGetByRobot:
    """Tests for LogRepository.get_by_robot method."""

    @pytest.mark.asyncio
    async def test_get_by_robot_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Get logs for specific robot."""
        mock_rows = [
            {
                "id": "entry-1",
                "robot_id": "robot-123",
                "tenant_id": "tenant-456",
                "timestamp": datetime.now(timezone.utc),
                "level": "ERROR",
                "message": "Error message",
                "source": None,
                "extra": None,
            }
        ]
        mock_connection.fetch.return_value = mock_rows

        results = await log_repository.get_by_robot(
            robot_id="robot-123",
            tenant_id="tenant-456",
            limit=50,
            min_level=LogLevel.ERROR,
        )

        assert len(results) == 1
        assert results[0].robot_id == "robot-123"


# ============================================================================
# Get Stats Tests
# ============================================================================


class TestLogRepositoryGetStats:
    """Tests for LogRepository.get_stats method."""

    @pytest.mark.asyncio
    async def test_get_stats_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Get log statistics."""
        oldest = datetime(2024, 1, 1, tzinfo=timezone.utc)
        newest = datetime(2024, 1, 31, tzinfo=timezone.utc)

        mock_connection.fetchrow.return_value = {
            "total_count": 1000,
            "trace_count": 100,
            "debug_count": 200,
            "info_count": 400,
            "warning_count": 200,
            "error_count": 80,
            "critical_count": 20,
            "oldest_log": oldest,
            "newest_log": newest,
            "storage_bytes": 512000,
        }

        stats = await log_repository.get_stats(
            tenant_id="tenant-123",
            robot_id="robot-456",
        )

        assert stats.tenant_id == "tenant-123"
        assert stats.robot_id == "robot-456"
        assert stats.total_count == 1000
        assert stats.by_level["INFO"] == 400
        assert stats.by_level["ERROR"] == 80
        assert stats.oldest_log == oldest
        assert stats.newest_log == newest
        assert stats.storage_bytes == 512000

    @pytest.mark.asyncio
    async def test_get_stats_empty(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Get stats when no logs exist."""
        mock_connection.fetchrow.return_value = None

        stats = await log_repository.get_stats(tenant_id="tenant-123")

        assert stats.total_count == 0
        assert stats.by_level == {}
        assert stats.oldest_log is None
        assert stats.newest_log is None
        assert stats.storage_bytes == 0


# ============================================================================
# Cleanup Old Logs Tests
# ============================================================================


class TestLogRepositoryCleanup:
    """Tests for LogRepository.cleanup_old_logs method."""

    @pytest.mark.asyncio
    async def test_cleanup_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Cleanup drops old partitions."""
        mock_connection.fetch.return_value = [
            {"partition_name": "robot_logs_2023_11"},
            {"partition_name": "robot_logs_2023_12"},
        ]
        mock_connection.execute.return_value = None

        result = await log_repository.cleanup_old_logs(retention_days=30)

        assert result["status"] == "completed"
        assert len(result["partitions_dropped"]) == 2
        assert "robot_logs_2023_11" in result["partitions_dropped"]
        assert result["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_cleanup_no_partitions_to_drop(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Cleanup with no old partitions."""
        mock_connection.fetch.return_value = []
        mock_connection.execute.return_value = None

        result = await log_repository.cleanup_old_logs(retention_days=30)

        assert result["status"] == "completed"
        assert result["partitions_dropped"] == []

    @pytest.mark.asyncio
    async def test_cleanup_uses_default_retention(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Cleanup uses default retention period."""
        mock_connection.fetch.return_value = []
        mock_connection.execute.return_value = None

        result = await log_repository.cleanup_old_logs()

        assert result["retention_days"] == DEFAULT_LOG_RETENTION_DAYS

    @pytest.mark.asyncio
    async def test_cleanup_error_records_failure(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Cleanup failure is recorded."""
        mock_connection.fetch.side_effect = Exception("Partition drop failed")
        # Second execute call for error logging should succeed
        mock_connection.execute.return_value = None

        with pytest.raises(Exception, match="Partition drop failed"):
            await log_repository.cleanup_old_logs()

    @pytest.mark.asyncio
    async def test_cleanup_records_history(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Cleanup records history in database."""
        mock_connection.fetch.return_value = []
        mock_connection.execute.return_value = None

        await log_repository.cleanup_old_logs()

        # Should have called execute for history insert
        execute_calls = mock_connection.execute.call_args_list
        history_call = execute_calls[-1]
        sql = history_call[0][0]
        assert "robot_logs_cleanup_history" in sql


# ============================================================================
# Ensure Partitions Tests
# ============================================================================


class TestLogRepositoryEnsurePartitions:
    """Tests for LogRepository.ensure_partitions method."""

    @pytest.mark.asyncio
    async def test_ensure_partitions_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Ensure partitions returns status."""
        mock_connection.fetch.return_value = [
            {"partition_name": "robot_logs_2024_02", "status": "created"},
            {"partition_name": "robot_logs_2024_03", "status": "exists"},
        ]

        results = await log_repository.ensure_partitions(months_ahead=2)

        assert len(results) == 2
        assert results[0]["partition"] == "robot_logs_2024_02"
        assert results[0]["status"] == "created"

    @pytest.mark.asyncio
    async def test_ensure_partitions_default_months(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Ensure partitions uses default months ahead."""
        mock_connection.fetch.return_value = []

        await log_repository.ensure_partitions()

        call_args = mock_connection.fetch.call_args
        assert call_args[0][1] == 2  # Default months_ahead


# ============================================================================
# Get Cleanup History Tests
# ============================================================================


class TestLogRepositoryGetCleanupHistory:
    """Tests for LogRepository.get_cleanup_history method."""

    @pytest.mark.asyncio
    async def test_get_cleanup_history_success(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Get cleanup history returns records."""
        cleanup_time = datetime(2024, 1, 15, 2, 0, 0, tzinfo=timezone.utc)
        mock_connection.fetch.return_value = [
            {
                "id": "cleanup-1",
                "cleanup_time": cleanup_time,
                "partitions_dropped": ["robot_logs_2023_11"],
                "rows_deleted": 10000,
                "retention_days": 30,
                "duration_ms": 1500,
                "status": "completed",
                "error_message": None,
            }
        ]

        history = await log_repository.get_cleanup_history(limit=10)

        assert len(history) == 1
        assert history[0]["status"] == "completed"
        assert history[0]["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_get_cleanup_history_empty(
        self,
        log_repository: LogRepository,
        mock_connection: AsyncMock,
    ) -> None:
        """Get cleanup history when empty."""
        mock_connection.fetch.return_value = []

        history = await log_repository.get_cleanup_history()

        assert history == []


# ============================================================================
# Row to Entry Conversion Tests
# ============================================================================


class TestLogRepositoryRowConversion:
    """Tests for LogRepository._row_to_entry method."""

    def test_row_to_entry_full(
        self,
        log_repository: LogRepository,
    ) -> None:
        """Convert full database row to LogEntry."""
        row = {
            "id": "entry-123",
            "robot_id": "robot-456",
            "tenant_id": "tenant-789",
            "timestamp": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "level": "WARNING",
            "message": "Warning message",
            "source": "test_source",
            "extra": {"key": "value"},
        }

        entry = log_repository._row_to_entry(row)

        assert entry.id == "entry-123"
        assert entry.level == LogLevel.WARNING
        assert entry.extra == {"key": "value"}

    def test_row_to_entry_with_string_extra(
        self,
        log_repository: LogRepository,
    ) -> None:
        """Convert row with JSON string extra."""
        row = {
            "id": "entry-123",
            "robot_id": "robot-456",
            "tenant_id": "tenant-789",
            "timestamp": datetime.now(timezone.utc),
            "level": "INFO",
            "message": "Test",
            "source": None,
            "extra": '{"key": "value"}',
        }

        entry = log_repository._row_to_entry(row)

        assert entry.extra == {"key": "value"}

    def test_row_to_entry_with_empty_extra(
        self,
        log_repository: LogRepository,
    ) -> None:
        """Convert row with empty extra."""
        row = {
            "id": "entry-123",
            "robot_id": "robot-456",
            "tenant_id": "tenant-789",
            "timestamp": datetime.now(timezone.utc),
            "level": "INFO",
            "message": "Test",
            "source": None,
            "extra": "",
        }

        entry = log_repository._row_to_entry(row)

        assert entry.extra == {}
