"""
Tests for PgQueuerConsumer.

These tests use mocking to avoid requiring a real PostgreSQL database.
For integration tests with a real database, see test_pgqueuer_consumer_integration.py.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from casare_rpa.infrastructure.queue import (
    PgQueuerConsumer,
    ClaimedJob,
    ConsumerConfig,
    ConnectionState,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def consumer_config() -> ConsumerConfig:
    """Create a test consumer configuration."""
    return ConsumerConfig(
        postgres_url="postgresql://test:test@localhost:5432/testdb",
        robot_id="test-robot-001",
        environment="test",
        batch_size=5,
        visibility_timeout_seconds=30,
        heartbeat_interval_seconds=10,
        max_reconnect_attempts=3,
        reconnect_base_delay_seconds=0.1,
        reconnect_max_delay_seconds=1.0,
        pool_min_size=1,
        pool_max_size=5,
    )


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg connection pool."""
    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def sample_job_row() -> Dict[str, Any]:
    """Create a sample job row as returned by the database."""
    return {
        "id": uuid.uuid4(),
        "workflow_id": "wf-123",
        "workflow_name": "Test Workflow",
        "workflow_json": '{"nodes": []}',
        "priority": 2,
        "environment": "test",
        "variables": {"key": "value"},
        "created_at": datetime.now(timezone.utc),
        "retry_count": 0,
        "max_retries": 3,
    }


# ==============================================================================
# Unit Tests - ClaimedJob
# ==============================================================================


class TestClaimedJob:
    """Tests for the ClaimedJob dataclass."""

    def test_to_dict_serializes_all_fields(self) -> None:
        """Test that to_dict includes all required fields."""
        now = datetime.now(timezone.utc)
        job = ClaimedJob(
            job_id="job-123",
            workflow_id="wf-456",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            priority=2,
            environment="production",
            variables={"input": "data"},
            created_at=now,
            claimed_at=now,
            retry_count=1,
            max_retries=3,
        )

        result = job.to_dict()

        assert result["job_id"] == "job-123"
        assert result["workflow_id"] == "wf-456"
        assert result["workflow_name"] == "Test Workflow"
        assert result["workflow_json"] == '{"nodes": []}'
        assert result["priority"] == 2
        assert result["environment"] == "production"
        assert result["variables"] == {"input": "data"}
        assert result["retry_count"] == 1
        assert result["max_retries"] == 3
        assert "created_at" in result
        assert "claimed_at" in result


# ==============================================================================
# Unit Tests - ConsumerConfig
# ==============================================================================


class TestConsumerConfig:
    """Tests for the ConsumerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = ConsumerConfig(
            postgres_url="postgresql://localhost/test",
            robot_id="robot-001",
        )

        assert config.environment == "default"
        assert config.batch_size == 1
        assert config.visibility_timeout_seconds == 30
        assert config.heartbeat_interval_seconds == 10
        assert config.max_reconnect_attempts == 10
        assert config.pool_min_size == 2
        assert config.pool_max_size == 10

    def test_custom_values(self, consumer_config: ConsumerConfig) -> None:
        """Test that custom values are preserved."""
        assert consumer_config.environment == "test"
        assert consumer_config.batch_size == 5
        assert consumer_config.visibility_timeout_seconds == 30


# ==============================================================================
# Unit Tests - PgQueuerConsumer Initialization
# ==============================================================================


class TestPgQueuerConsumerInit:
    """Tests for PgQueuerConsumer initialization."""

    def test_init_sets_correct_state(self, consumer_config: ConsumerConfig) -> None:
        """Test that initialization sets correct initial state."""
        consumer = PgQueuerConsumer(consumer_config)

        assert consumer.state == ConnectionState.DISCONNECTED
        assert consumer.robot_id == "test-robot-001"
        assert consumer.active_job_count == 0
        assert consumer.is_connected is False

    def test_init_without_asyncpg_raises_import_error(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that ImportError is raised when asyncpg is not available."""
        with patch(
            "casare_rpa.infrastructure.queue.pgqueuer_consumer.HAS_ASYNCPG", False
        ):
            # Need to reimport to trigger the check
            from importlib import reload
            import casare_rpa.infrastructure.queue.pgqueuer_consumer as module

            original_has_asyncpg = module.HAS_ASYNCPG
            try:
                module.HAS_ASYNCPG = False
                with pytest.raises(ImportError, match="asyncpg is required"):
                    PgQueuerConsumer(consumer_config)
            finally:
                module.HAS_ASYNCPG = original_has_asyncpg


# ==============================================================================
# Unit Tests - State Callbacks
# ==============================================================================


class TestStateCallbacks:
    """Tests for state change callbacks."""

    def test_add_state_callback(self, consumer_config: ConsumerConfig) -> None:
        """Test adding a state callback."""
        consumer = PgQueuerConsumer(consumer_config)
        callback = MagicMock()

        consumer.add_state_callback(callback)
        consumer._set_state(ConnectionState.CONNECTING)

        callback.assert_called_once_with(ConnectionState.CONNECTING)

    def test_remove_state_callback(self, consumer_config: ConsumerConfig) -> None:
        """Test removing a state callback."""
        consumer = PgQueuerConsumer(consumer_config)
        callback = MagicMock()

        consumer.add_state_callback(callback)
        consumer.remove_state_callback(callback)
        consumer._set_state(ConnectionState.CONNECTING)

        callback.assert_not_called()

    def test_state_callback_exception_does_not_propagate(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that exceptions in callbacks don't propagate."""
        consumer = PgQueuerConsumer(consumer_config)
        callback = MagicMock(side_effect=Exception("Callback error"))

        consumer.add_state_callback(callback)
        # Should not raise
        consumer._set_state(ConnectionState.CONNECTING)


# ==============================================================================
# Unit Tests - Connection Management
# ==============================================================================


class TestConnectionManagement:
    """Tests for connection management."""

    @pytest.mark.asyncio
    async def test_start_connects_to_database(
        self, consumer_config: ConsumerConfig, mock_pool: MagicMock
    ) -> None:
        """Test that start() establishes database connection."""
        consumer = PgQueuerConsumer(consumer_config)

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(
                return_value=mock_conn
            )
            mock_pool.acquire.return_value.__aexit__ = AsyncMock()
            mock_create_pool.return_value = mock_pool

            result = await consumer.start()

            assert result is True
            assert consumer.state == ConnectionState.CONNECTED
            mock_create_pool.assert_called_once()

        await consumer.stop()

    @pytest.mark.asyncio
    async def test_start_handles_connection_failure(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that start() handles connection failures."""
        consumer = PgQueuerConsumer(consumer_config)

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")

            result = await consumer.start()

            assert result is False
            assert consumer.state == ConnectionState.FAILED

    @pytest.mark.asyncio
    async def test_stop_releases_active_jobs(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that stop() releases active jobs back to queue."""
        consumer = PgQueuerConsumer(consumer_config)

        # Add a mock active job
        job = ClaimedJob(
            job_id="job-123",
            workflow_id="wf-456",
            workflow_name="Test",
            workflow_json="{}",
            priority=1,
            environment="test",
            variables={},
            created_at=datetime.now(timezone.utc),
            claimed_at=datetime.now(timezone.utc),
            retry_count=0,
            max_retries=3,
        )
        consumer._active_jobs["job-123"] = job
        consumer._running = True

        # Mock the release_job method
        consumer.release_job = AsyncMock(return_value=True)

        await consumer.stop()

        consumer.release_job.assert_called_once_with("job-123")
        assert consumer.state == ConnectionState.DISCONNECTED


# ==============================================================================
# Unit Tests - Job Claiming
# ==============================================================================


class TestJobClaiming:
    """Tests for job claiming functionality."""

    @pytest.mark.asyncio
    async def test_claim_job_returns_job_when_available(
        self,
        consumer_config: ConsumerConfig,
        sample_job_row: Dict[str, Any],
    ) -> None:
        """Test that claim_job returns a job when one is available."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        # Mock _execute_with_retry
        consumer._execute_with_retry = AsyncMock(return_value=[sample_job_row])

        job = await consumer.claim_job()

        assert job is not None
        assert job.workflow_id == "wf-123"
        assert job.workflow_name == "Test Workflow"
        assert job.priority == 2
        assert consumer.active_job_count == 1

    @pytest.mark.asyncio
    async def test_claim_job_returns_none_when_empty(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that claim_job returns None when queue is empty."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        consumer._execute_with_retry = AsyncMock(return_value=[])

        job = await consumer.claim_job()

        assert job is None
        assert consumer.active_job_count == 0

    @pytest.mark.asyncio
    async def test_claim_batch_respects_limit(
        self,
        consumer_config: ConsumerConfig,
        sample_job_row: Dict[str, Any],
    ) -> None:
        """Test that claim_batch respects the limit parameter."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        # Create multiple job rows
        rows = [
            {**sample_job_row, "id": uuid.uuid4()},
            {**sample_job_row, "id": uuid.uuid4()},
            {**sample_job_row, "id": uuid.uuid4()},
        ]
        consumer._execute_with_retry = AsyncMock(return_value=rows)

        jobs = await consumer.claim_batch(limit=3)

        assert len(jobs) == 3
        assert consumer.active_job_count == 3


# ==============================================================================
# Unit Tests - Job Completion/Failure
# ==============================================================================


class TestJobCompletion:
    """Tests for job completion and failure reporting."""

    @pytest.mark.asyncio
    async def test_complete_job_removes_from_active(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that complete_job removes job from active jobs."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        job_id = str(uuid.uuid4())
        consumer._active_jobs[job_id] = MagicMock()

        consumer._execute_with_retry = AsyncMock(
            return_value=[{"id": uuid.UUID(job_id)}]
        )

        result = await consumer.complete_job(job_id, {"output": "success"})

        assert result is True
        assert job_id not in consumer._active_jobs

    @pytest.mark.asyncio
    async def test_fail_job_returns_retry_status(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that fail_job indicates whether job will be retried."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        job_id = str(uuid.uuid4())
        consumer._active_jobs[job_id] = MagicMock()

        # Job will be retried
        consumer._execute_with_retry = AsyncMock(
            return_value=[
                {"id": uuid.UUID(job_id), "status": "pending", "retry_count": 1}
            ]
        )

        success, will_retry = await consumer.fail_job(job_id, "Test error")

        assert success is True
        assert will_retry is True

    @pytest.mark.asyncio
    async def test_fail_job_permanent_failure(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test fail_job when max retries exceeded."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        job_id = str(uuid.uuid4())
        consumer._active_jobs[job_id] = MagicMock()

        # Max retries exceeded
        consumer._execute_with_retry = AsyncMock(
            return_value=[
                {"id": uuid.UUID(job_id), "status": "failed", "retry_count": 3}
            ]
        )

        success, will_retry = await consumer.fail_job(job_id, "Final error")

        assert success is True
        assert will_retry is False


# ==============================================================================
# Unit Tests - Lease Extension
# ==============================================================================


class TestLeaseExtension:
    """Tests for lease extension (heartbeat) functionality."""

    @pytest.mark.asyncio
    async def test_extend_lease_success(self, consumer_config: ConsumerConfig) -> None:
        """Test successful lease extension."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        job_id = str(uuid.uuid4())

        consumer._execute_with_retry = AsyncMock(
            return_value=[{"id": uuid.UUID(job_id)}]
        )

        result = await consumer.extend_lease(job_id, extension_seconds=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_extend_lease_job_not_found(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test lease extension when job is not found."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._pool = MagicMock()

        job_id = str(uuid.uuid4())

        consumer._execute_with_retry = AsyncMock(return_value=[])

        result = await consumer.extend_lease(job_id)

        assert result is False


# ==============================================================================
# Unit Tests - Statistics
# ==============================================================================


class TestStatistics:
    """Tests for statistics and monitoring."""

    def test_get_stats_returns_correct_info(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that get_stats returns accurate information."""
        consumer = PgQueuerConsumer(consumer_config)
        consumer._state = ConnectionState.CONNECTED
        consumer._active_jobs["job-1"] = MagicMock()
        consumer._active_jobs["job-2"] = MagicMock()
        consumer._reconnect_attempts = 2

        stats = consumer.get_stats()

        assert stats["robot_id"] == "test-robot-001"
        assert stats["environment"] == "test"
        assert stats["state"] == "connected"
        assert stats["active_jobs"] == 2
        assert "job-1" in stats["active_job_ids"]
        assert "job-2" in stats["active_job_ids"]
        assert stats["reconnect_attempts"] == 2
        assert stats["config"]["batch_size"] == 5
        assert stats["config"]["visibility_timeout_seconds"] == 30


# ==============================================================================
# Unit Tests - Context Manager
# ==============================================================================


class TestContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops(
        self, consumer_config: ConsumerConfig
    ) -> None:
        """Test that context manager properly starts and stops consumer."""
        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_pool = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(
                return_value=mock_conn
            )
            mock_pool.acquire.return_value.__aexit__ = AsyncMock()
            mock_pool.close = AsyncMock()
            mock_create_pool.return_value = mock_pool

            async with PgQueuerConsumer(consumer_config) as consumer:
                assert consumer.state == ConnectionState.CONNECTED

            assert consumer.state == ConnectionState.DISCONNECTED
