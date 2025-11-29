"""
Tests for DLQManager (Dead Letter Queue with exponential backoff retry).

These tests use mocking to avoid requiring a real PostgreSQL database.
For integration tests with a real database, see test_dlq_manager_integration.py.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.infrastructure.queue import (
    DLQManager,
    DLQManagerConfig,
    DLQEntry,
    FailedJob,
    RetryAction,
    RetryResult,
    RETRY_SCHEDULE,
    JITTER_FACTOR,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def dlq_config() -> DLQManagerConfig:
    """Create a test DLQ manager configuration."""
    return DLQManagerConfig(
        postgres_url="postgresql://test:test@localhost:5432/testdb",
        job_queue_table="job_queue",
        dlq_table="job_queue_dlq",
        retry_schedule=[10, 60, 300, 900, 3600],
        jitter_factor=0.2,
        pool_min_size=1,
        pool_max_size=3,
    )


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg connection pool."""
    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def sample_failed_job() -> FailedJob:
    """Create a sample failed job."""
    return FailedJob(
        job_id=str(uuid.uuid4()),
        workflow_id="wf-test-123",
        workflow_name="Test Workflow",
        workflow_json='{"nodes": [], "connections": []}',
        variables={"input": "test_value"},
        retry_count=0,
        error_message="Element not found: #submit-button",
        error_details={
            "error_type": "ElementNotFoundError",
            "selector": "#submit-button",
            "page_url": "https://example.com/form",
        },
    )


@pytest.fixture
def sample_dlq_row() -> Dict[str, Any]:
    """Create a sample DLQ database row."""
    now = datetime.now(timezone.utc)
    return {
        "id": uuid.uuid4(),
        "original_job_id": uuid.uuid4(),
        "workflow_id": "wf-test-123",
        "workflow_name": "Test Workflow",
        "workflow_json": '{"nodes": []}',
        "variables": {"key": "value"},
        "error_message": "Test error",
        "error_details": {"type": "TestError"},
        "retry_count": 5,
        "first_failed_at": now,
        "last_failed_at": now,
        "created_at": now,
        "reprocessed_at": None,
        "reprocessed_by": None,
    }


# ==============================================================================
# Unit Tests - Constants
# ==============================================================================


class TestRetryScheduleConstants:
    """Tests for retry schedule constants."""

    def test_retry_schedule_has_correct_values(self) -> None:
        """Test that RETRY_SCHEDULE matches documented values."""
        assert RETRY_SCHEDULE == [10, 60, 300, 900, 3600]

    def test_retry_schedule_is_increasing(self) -> None:
        """Test that retry delays increase exponentially."""
        for i in range(len(RETRY_SCHEDULE) - 1):
            assert RETRY_SCHEDULE[i] < RETRY_SCHEDULE[i + 1]

    def test_jitter_factor_is_twenty_percent(self) -> None:
        """Test that JITTER_FACTOR is 0.2 (20%)."""
        assert JITTER_FACTOR == 0.2


# ==============================================================================
# Unit Tests - FailedJob
# ==============================================================================


class TestFailedJob:
    """Tests for the FailedJob dataclass."""

    def test_to_dict_serializes_all_fields(self, sample_failed_job: FailedJob) -> None:
        """Test that to_dict includes all required fields."""
        result = sample_failed_job.to_dict()

        assert result["job_id"] == sample_failed_job.job_id
        assert result["workflow_id"] == "wf-test-123"
        assert result["workflow_name"] == "Test Workflow"
        assert result["retry_count"] == 0
        assert result["error_message"] == "Element not found: #submit-button"
        assert result["error_details"]["error_type"] == "ElementNotFoundError"
        assert result["variables"]["input"] == "test_value"

    def test_to_dict_handles_none_timestamps(self) -> None:
        """Test that to_dict handles None timestamps."""
        job = FailedJob(
            job_id="test-id",
            workflow_id="wf-1",
            workflow_name="Test",
            workflow_json="{}",
            variables={},
            retry_count=0,
            error_message="Error",
        )

        result = job.to_dict()

        assert result["first_failed_at"] is None
        assert result["last_failed_at"] is None


# ==============================================================================
# Unit Tests - DLQEntry
# ==============================================================================


class TestDLQEntry:
    """Tests for the DLQEntry dataclass."""

    def test_to_dict_serializes_all_fields(
        self, sample_dlq_row: Dict[str, Any]
    ) -> None:
        """Test that to_dict includes all required fields."""
        now = datetime.now(timezone.utc)
        entry = DLQEntry(
            id=str(sample_dlq_row["id"]),
            original_job_id=str(sample_dlq_row["original_job_id"]),
            workflow_id="wf-test-123",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            variables={"key": "value"},
            error_message="Test error",
            error_details={"type": "TestError"},
            retry_count=5,
            first_failed_at=now,
            last_failed_at=now,
            created_at=now,
        )

        result = entry.to_dict()

        assert "id" in result
        assert "original_job_id" in result
        assert result["workflow_id"] == "wf-test-123"
        assert result["retry_count"] == 5
        assert result["reprocessed_at"] is None
        assert result["reprocessed_by"] is None

    def test_to_dict_with_reprocessed_fields(self) -> None:
        """Test that to_dict includes reprocessed fields when set."""
        now = datetime.now(timezone.utc)
        entry = DLQEntry(
            id="entry-1",
            original_job_id="job-1",
            workflow_id="wf-1",
            workflow_name="Test",
            workflow_json="{}",
            variables={},
            error_message="Error",
            error_details=None,
            retry_count=5,
            first_failed_at=now,
            last_failed_at=now,
            created_at=now,
            reprocessed_at=now,
            reprocessed_by="admin",
        )

        result = entry.to_dict()

        assert result["reprocessed_at"] is not None
        assert result["reprocessed_by"] == "admin"


# ==============================================================================
# Unit Tests - DLQManagerConfig
# ==============================================================================


class TestDLQManagerConfig:
    """Tests for the DLQManagerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = DLQManagerConfig(postgres_url="postgresql://localhost/test")

        assert config.job_queue_table == "job_queue"
        assert config.dlq_table == "job_queue_dlq"
        assert config.retry_schedule == [10, 60, 300, 900, 3600]
        assert config.jitter_factor == 0.2
        assert config.pool_min_size == 1
        assert config.pool_max_size == 5

    def test_custom_values(self, dlq_config: DLQManagerConfig) -> None:
        """Test that custom values are preserved."""
        assert dlq_config.job_queue_table == "job_queue"
        assert dlq_config.dlq_table == "job_queue_dlq"
        assert dlq_config.pool_max_size == 3


# ==============================================================================
# Unit Tests - DLQManager Initialization
# ==============================================================================


class TestDLQManagerInit:
    """Tests for DLQManager initialization."""

    def test_init_sets_correct_properties(self, dlq_config: DLQManagerConfig) -> None:
        """Test that initialization sets correct properties."""
        manager = DLQManager(dlq_config)

        assert manager.max_retries == 5
        assert manager.is_running is False

    def test_init_without_asyncpg_raises_import_error(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test that ImportError is raised when asyncpg is not available."""
        import casare_rpa.infrastructure.queue.dlq_manager as module

        original_has_asyncpg = module.HAS_ASYNCPG
        try:
            module.HAS_ASYNCPG = False
            with pytest.raises(ImportError, match="asyncpg is required"):
                DLQManager(dlq_config)
        finally:
            module.HAS_ASYNCPG = original_has_asyncpg


# ==============================================================================
# Unit Tests - Backoff Calculation
# ==============================================================================


class TestBackoffCalculation:
    """Tests for exponential backoff with jitter."""

    def test_calculate_backoff_delay_first_retry(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test backoff delay for first retry (10s base)."""
        manager = DLQManager(dlq_config)

        base_delay, delay_with_jitter = manager.calculate_backoff_delay(0)

        assert base_delay == 10
        # With ±20% jitter, delay should be between 8 and 12
        assert 8 <= delay_with_jitter <= 12

    def test_calculate_backoff_delay_second_retry(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test backoff delay for second retry (60s base)."""
        manager = DLQManager(dlq_config)

        base_delay, delay_with_jitter = manager.calculate_backoff_delay(1)

        assert base_delay == 60
        # With ±20% jitter, delay should be between 48 and 72
        assert 48 <= delay_with_jitter <= 72

    def test_calculate_backoff_delay_all_retries(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test backoff delay for all retry levels."""
        manager = DLQManager(dlq_config)
        expected_base_delays = [10, 60, 300, 900, 3600]

        for retry_count, expected_base in enumerate(expected_base_delays):
            base_delay, delay_with_jitter = manager.calculate_backoff_delay(retry_count)
            assert base_delay == expected_base

            # Check jitter bounds (±20%)
            min_jitter = int(expected_base * 0.8)
            max_jitter = int(expected_base * 1.2)
            assert min_jitter <= delay_with_jitter <= max_jitter

    def test_calculate_backoff_delay_beyond_max_retries(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test that delay is 0 when retry count exceeds schedule."""
        manager = DLQManager(dlq_config)

        base_delay, delay_with_jitter = manager.calculate_backoff_delay(5)

        assert base_delay == 0
        assert delay_with_jitter == 0

    def test_jitter_provides_variance(self, dlq_config: DLQManagerConfig) -> None:
        """Test that jitter provides variance across multiple calls."""
        manager = DLQManager(dlq_config)
        delays = set()

        # Calculate delay multiple times; with jitter, values should vary
        for _ in range(20):
            _, delay = manager.calculate_backoff_delay(2)  # 300s base
            delays.add(delay)

        # Should have multiple different values due to jitter
        assert len(delays) > 1


# ==============================================================================
# Unit Tests - Connection Management
# ==============================================================================


class TestConnectionManagement:
    """Tests for connection management."""

    @pytest.mark.asyncio
    async def test_start_connects_to_database(
        self, dlq_config: DLQManagerConfig, mock_pool: MagicMock
    ) -> None:
        """Test that start() establishes database connection."""
        manager = DLQManager(dlq_config)

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(
                return_value=mock_conn
            )
            mock_pool.acquire.return_value.__aexit__ = AsyncMock()
            mock_create_pool.return_value = mock_pool

            await manager.start()

            assert manager.is_running is True
            mock_create_pool.assert_called_once()

        await manager.stop()

    @pytest.mark.asyncio
    async def test_start_handles_connection_failure(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test that start() raises on connection failure."""
        manager = DLQManager(dlq_config)

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await manager.start()

            assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_stop_closes_pool(
        self, dlq_config: DLQManagerConfig, mock_pool: MagicMock
    ) -> None:
        """Test that stop() closes the connection pool."""
        manager = DLQManager(dlq_config)
        manager._pool = mock_pool
        manager._running = True

        await manager.stop()

        mock_pool.close.assert_called_once()
        assert manager.is_running is False


# ==============================================================================
# Unit Tests - Handle Job Failure
# ==============================================================================


class TestHandleJobFailure:
    """Tests for handle_job_failure method."""

    @pytest.mark.asyncio
    async def test_handle_failure_schedules_retry_on_first_failure(
        self,
        dlq_config: DLQManagerConfig,
        sample_failed_job: FailedJob,
    ) -> None:
        """Test that first failure schedules a retry."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        # Mock the database call
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(
            return_value={"id": uuid.UUID(sample_failed_job.job_id)}
        )
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        result = await manager.handle_job_failure(sample_failed_job)

        assert result.action == RetryAction.RETRY
        assert result.retry_count == 1
        assert result.delay_seconds is not None
        assert 8 <= result.delay_seconds <= 12  # 10s ± 20%
        assert result.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_handle_failure_moves_to_dlq_after_max_retries(
        self,
        dlq_config: DLQManagerConfig,
        sample_failed_job: FailedJob,
    ) -> None:
        """Test that job is moved to DLQ after exhausting retries."""
        sample_failed_job.retry_count = 5  # Max retries

        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        dlq_entry_id = uuid.uuid4()

        # Mock the database calls
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": dlq_entry_id})
        mock_conn.execute = AsyncMock()
        mock_conn.transaction = MagicMock()
        mock_conn.transaction.return_value.__aenter__ = AsyncMock()
        mock_conn.transaction.return_value.__aexit__ = AsyncMock()
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        result = await manager.handle_job_failure(sample_failed_job)

        assert result.action == RetryAction.MOVE_TO_DLQ
        assert result.retry_count == 5
        assert result.dlq_entry_id == str(dlq_entry_id)
        assert result.delay_seconds is None

    @pytest.mark.asyncio
    async def test_handle_failure_raises_when_not_connected(
        self,
        dlq_config: DLQManagerConfig,
        sample_failed_job: FailedJob,
    ) -> None:
        """Test that handle_job_failure raises when not connected."""
        manager = DLQManager(dlq_config)
        # Not calling start(), so _pool is None

        with pytest.raises(ConnectionError, match="not connected"):
            await manager.handle_job_failure(sample_failed_job)


# ==============================================================================
# Unit Tests - DLQ Operations
# ==============================================================================


class TestDLQOperations:
    """Tests for DLQ inspection and retry operations."""

    @pytest.mark.asyncio
    async def test_list_dlq_entries(
        self,
        dlq_config: DLQManagerConfig,
        sample_dlq_row: Dict[str, Any],
    ) -> None:
        """Test listing DLQ entries."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[sample_dlq_row])
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        entries = await manager.list_dlq_entries()

        assert len(entries) == 1
        assert entries[0].workflow_id == "wf-test-123"
        assert entries[0].retry_count == 5

    @pytest.mark.asyncio
    async def test_get_dlq_entry(
        self,
        dlq_config: DLQManagerConfig,
        sample_dlq_row: Dict[str, Any],
    ) -> None:
        """Test getting a specific DLQ entry."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=sample_dlq_row)
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        entry = await manager.get_dlq_entry(str(sample_dlq_row["id"]))

        assert entry is not None
        assert entry.workflow_id == "wf-test-123"

    @pytest.mark.asyncio
    async def test_get_dlq_entry_not_found(self, dlq_config: DLQManagerConfig) -> None:
        """Test getting a DLQ entry that doesn't exist."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        entry = await manager.get_dlq_entry(str(uuid.uuid4()))

        assert entry is None

    @pytest.mark.asyncio
    async def test_retry_from_dlq(self, dlq_config: DLQManagerConfig) -> None:
        """Test manual retry from DLQ."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        new_job_id = uuid.uuid4()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"id": new_job_id})
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        entry_id = str(uuid.uuid4())
        result = await manager.retry_from_dlq(entry_id, reprocessed_by="admin")

        assert result == str(new_job_id)

    @pytest.mark.asyncio
    async def test_retry_from_dlq_already_reprocessed(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test retry from DLQ when entry is already reprocessed."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(
            return_value=None
        )  # No result = already reprocessed
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        entry_id = str(uuid.uuid4())
        result = await manager.retry_from_dlq(entry_id)

        assert result is None


# ==============================================================================
# Unit Tests - Statistics
# ==============================================================================


class TestStatistics:
    """Tests for DLQ statistics."""

    @pytest.mark.asyncio
    async def test_get_dlq_stats(self, dlq_config: DLQManagerConfig) -> None:
        """Test getting DLQ statistics."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"total": 10, "pending": 7})
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        stats = await manager.get_dlq_stats()

        assert stats["total"] == 10
        assert stats["pending"] == 7

    @pytest.mark.asyncio
    async def test_get_dlq_stats_with_filter(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test getting DLQ statistics with workflow filter."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"total": 3, "pending": 2})
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        stats = await manager.get_dlq_stats(workflow_id="wf-specific")

        assert stats["total"] == 3


# ==============================================================================
# Unit Tests - Purge
# ==============================================================================


class TestPurge:
    """Tests for DLQ purge operations."""

    @pytest.mark.asyncio
    async def test_purge_reprocessed(self, dlq_config: DLQManagerConfig) -> None:
        """Test purging reprocessed DLQ entries."""
        manager = DLQManager(dlq_config)
        manager._running = True
        manager._pool = MagicMock()

        purged_ids = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=purged_ids)
        manager._pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_conn
        )
        manager._pool.acquire.return_value.__aexit__ = AsyncMock()

        count = await manager.purge_reprocessed(older_than_days=30)

        assert count == 2


# ==============================================================================
# Unit Tests - Context Manager
# ==============================================================================


class TestContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops(
        self, dlq_config: DLQManagerConfig
    ) -> None:
        """Test that context manager properly starts and stops manager."""
        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_pool = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(
                return_value=mock_conn
            )
            mock_pool.acquire.return_value.__aexit__ = AsyncMock()
            mock_pool.close = AsyncMock()
            mock_create_pool.return_value = mock_pool

            async with DLQManager(dlq_config) as manager:
                assert manager.is_running is True

            assert manager.is_running is False


# ==============================================================================
# Unit Tests - RetryResult
# ==============================================================================


class TestRetryResult:
    """Tests for RetryResult dataclass."""

    def test_retry_result_for_retry_action(self) -> None:
        """Test RetryResult for retry action."""
        now = datetime.now(timezone.utc)
        result = RetryResult(
            action=RetryAction.RETRY,
            job_id="job-123",
            retry_count=2,
            next_retry_at=now,
            delay_seconds=60,
        )

        assert result.action == RetryAction.RETRY
        assert result.job_id == "job-123"
        assert result.retry_count == 2
        assert result.delay_seconds == 60
        assert result.dlq_entry_id is None

    def test_retry_result_for_dlq_action(self) -> None:
        """Test RetryResult for DLQ action."""
        result = RetryResult(
            action=RetryAction.MOVE_TO_DLQ,
            job_id="job-456",
            retry_count=5,
            dlq_entry_id="dlq-entry-789",
        )

        assert result.action == RetryAction.MOVE_TO_DLQ
        assert result.dlq_entry_id == "dlq-entry-789"
        assert result.next_retry_at is None
        assert result.delay_seconds is None
