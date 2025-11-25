"""
Tests for Phase 8B: Robot Hardening

Comprehensive tests for:
- Connection manager with exponential backoff
- Circuit breaker pattern
- Offline job queue
- Checkpoint manager
- Metrics collector
- Audit logging
- Job executor
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import robot modules
from casare_rpa.robot.connection import (
    ConnectionManager,
    ConnectionConfig,
    ConnectionState,
    ConnectionStats,
)
from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)
from casare_rpa.robot.offline_queue import (
    OfflineQueue,
    CachedJobStatus,
)
from casare_rpa.robot.checkpoint import (
    CheckpointManager,
    CheckpointState,
    create_checkpoint_state,
)
from casare_rpa.robot.metrics import (
    MetricsCollector,
    JobMetrics,
    NodeMetrics,
)
from casare_rpa.robot.audit import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditSeverity,
)
from casare_rpa.robot.job_executor import (
    JobExecutor,
    JobExecutorConfig,
    JobStatus,
)
from casare_rpa.robot.config import (
    RobotConfig,
    ConnectionConfig as RobotConnectionConfig,
    validate_credentials,
)


# ============================================================================
# CONNECTION MANAGER TESTS
# ============================================================================

class TestConnectionConfig:
    """Tests for ConnectionConfig."""

    def test_default_values(self):
        config = ConnectionConfig()
        assert config.initial_delay == 1.0
        assert config.max_delay == 300.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True

    def test_get_delay_exponential(self):
        config = ConnectionConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=100.0,
            jitter=False,
        )
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0
        assert config.get_delay(4) == 8.0

    def test_get_delay_capped(self):
        config = ConnectionConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=5.0,
            jitter=False,
        )
        assert config.get_delay(10) == 5.0  # Capped at max_delay

    def test_get_delay_with_jitter(self):
        config = ConnectionConfig(
            initial_delay=10.0,
            jitter=True,
        )
        delays = [config.get_delay(1) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_initialization(self):
        manager = ConnectionManager(
            url="https://test.supabase.co",
            key="test-key",
        )
        assert manager.url == "https://test.supabase.co"
        assert manager.key == "test-key"
        assert manager.state == ConnectionState.DISCONNECTED
        assert manager.is_connected is False

    def test_state_transitions(self):
        manager = ConnectionManager(url="", key="")
        assert manager._state == ConnectionState.DISCONNECTED

        manager._set_state(ConnectionState.CONNECTING)
        assert manager.state == ConnectionState.CONNECTING

        manager._set_state(ConnectionState.CONNECTED)
        assert manager.is_connected is True

    def test_callbacks_triggered(self):
        connected_called = []
        disconnected_called = []

        manager = ConnectionManager(
            url="",
            key="",
            on_connected=lambda: connected_called.append(True),
            on_disconnected=lambda: disconnected_called.append(True),
        )

        manager._set_state(ConnectionState.CONNECTED)
        assert len(connected_called) == 1

        manager._set_state(ConnectionState.DISCONNECTED)
        assert len(disconnected_called) == 1

    def test_get_status(self):
        manager = ConnectionManager(url="test", key="test")
        status = manager.get_status()

        assert "state" in status
        assert "is_connected" in status
        assert "reconnect_attempt" in status
        assert "stats" in status


class TestConnectionStats:
    """Tests for ConnectionStats."""

    def test_initialization(self):
        stats = ConnectionStats()
        assert stats.connection_attempts == 0
        assert stats.successful_connections == 0
        assert stats.failed_connections == 0

    def test_to_dict(self):
        stats = ConnectionStats()
        stats.connection_attempts = 10
        stats.successful_connections = 8
        stats.failed_connections = 2

        d = stats.to_dict()
        assert d["connection_attempts"] == 10
        assert d["connection_success_rate"] == 80.0


# ============================================================================
# CIRCUIT BREAKER TESTS
# ============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self):
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initialization(self):
        cb = CircuitBreaker("test")
        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True
        assert cb.is_open is False

    @pytest.mark.asyncio
    async def test_successful_call(self):
        cb = CircuitBreaker("test")

        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_opens_after_failures(self):
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config=config)

        async def fail_func():
            raise Exception("failure")

        # Should open after 3 failures
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_blocks_when_open(self):
        config = CircuitBreakerConfig(failure_threshold=1, timeout=60.0)
        cb = CircuitBreaker("test", config=config)

        async def fail_func():
            raise Exception("failure")

        # Trigger open state
        with pytest.raises(Exception):
            await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN

        # Should block subsequent calls
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await cb.call(fail_func)

        assert exc_info.value.circuit_name == "test"

    @pytest.mark.asyncio
    async def test_half_open_transition(self):
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        cb = CircuitBreaker("test", config=config)

        async def fail_func():
            raise Exception("failure")

        # Trigger open state
        with pytest.raises(Exception):
            await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Next call should transition to half-open
        await cb._check_state_transition()
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self):
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.1,
        )
        cb = CircuitBreaker("test", config=config)

        call_count = [0]

        async def sometimes_fail():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("first call fails")
            return "success"

        # First call fails, opens circuit
        with pytest.raises(Exception):
            await cb.call(sometimes_fail)

        await asyncio.sleep(0.2)

        # Successes in half-open should close circuit
        await cb.call(sometimes_fail)
        await cb.call(sometimes_fail)

        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config=config)

        async def fail_func():
            raise Exception("failure")

        with pytest.raises(Exception):
            await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN

        await cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_get_status(self):
        cb = CircuitBreaker("test")
        status = cb.get_status()

        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert "stats" in status


# ============================================================================
# OFFLINE QUEUE TESTS
# ============================================================================

class TestOfflineQueue:
    """Tests for OfflineQueue."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database for testing."""
        return tmp_path / "test_queue.db"

    @pytest.fixture
    def queue(self, temp_db):
        """Create queue instance."""
        return OfflineQueue(db_path=temp_db, robot_id="test-robot")

    @pytest.mark.asyncio
    async def test_cache_job(self, queue):
        result = await queue.cache_job(
            job_id="job-1",
            workflow_json='{"nodes": []}',
            original_status="pending",
        )
        assert result is True

        # Verify job is cached
        cached = await queue.get_cached_jobs()
        assert len(cached) == 1
        assert cached[0]["id"] == "job-1"

    @pytest.mark.asyncio
    async def test_mark_in_progress(self, queue):
        await queue.cache_job("job-1", '{}')
        result = await queue.mark_in_progress("job-1")
        assert result is True

        in_progress = await queue.get_in_progress_jobs()
        assert len(in_progress) == 1

    @pytest.mark.asyncio
    async def test_mark_completed(self, queue):
        await queue.cache_job("job-1", '{}')
        await queue.mark_in_progress("job-1")
        result = await queue.mark_completed(
            "job-1",
            success=True,
            result={"message": "done"},
        )
        assert result is True

        to_sync = await queue.get_jobs_to_sync()
        assert len(to_sync) == 1
        assert to_sync[0]["cached_status"] == "completed"

    @pytest.mark.asyncio
    async def test_mark_synced(self, queue):
        await queue.cache_job("job-1", '{}')
        await queue.mark_completed("job-1", success=True)
        await queue.mark_synced("job-1")

        to_sync = await queue.get_jobs_to_sync()
        assert len(to_sync) == 0

    @pytest.mark.asyncio
    async def test_checkpoint_save_and_restore(self, queue):
        await queue.save_checkpoint(
            job_id="job-1",
            checkpoint_id="cp-1",
            node_id="node-1",
            state={"variables": {"x": 1}},
        )

        checkpoint = await queue.get_latest_checkpoint("job-1")
        assert checkpoint is not None
        assert checkpoint["node_id"] == "node-1"
        assert checkpoint["state"]["variables"]["x"] == 1

    @pytest.mark.asyncio
    async def test_clear_checkpoints(self, queue):
        await queue.save_checkpoint("job-1", "cp-1", "node-1", {})
        await queue.save_checkpoint("job-1", "cp-2", "node-2", {})

        await queue.clear_checkpoints("job-1")

        checkpoint = await queue.get_latest_checkpoint("job-1")
        assert checkpoint is None

    @pytest.mark.asyncio
    async def test_log_event(self, queue):
        await queue.log_event(
            job_id="job-1",
            event_type="started",
            event_data={"timestamp": "2024-01-01"},
        )

        history = await queue.get_job_history("job-1")
        assert len(history) == 1
        assert history[0]["event_type"] == "started"

    @pytest.mark.asyncio
    async def test_queue_stats(self, queue):
        await queue.cache_job("job-1", '{}')
        await queue.cache_job("job-2", '{}')
        await queue.mark_in_progress("job-1")

        stats = await queue.get_queue_stats()
        assert stats.get("cached", 0) == 1
        assert stats.get("in_progress", 0) == 1


# ============================================================================
# CHECKPOINT MANAGER TESTS
# ============================================================================

class TestCheckpointState:
    """Tests for CheckpointState."""

    def test_creation(self):
        state = CheckpointState(
            checkpoint_id="cp-1",
            job_id="job-1",
            workflow_name="test",
            created_at="2024-01-01T00:00:00",
            current_node_id="node-1",
            executed_nodes=["node-0"],
            execution_path=["node-0"],
            variables={"x": 1},
            errors=[],
        )
        assert state.checkpoint_id == "cp-1"
        assert state.current_node_id == "node-1"

    def test_to_dict(self):
        state = CheckpointState(
            checkpoint_id="cp-1",
            job_id="job-1",
            workflow_name="test",
            created_at="2024-01-01T00:00:00",
            current_node_id="node-1",
            executed_nodes=[],
            execution_path=[],
            variables={},
            errors=[],
        )
        d = state.to_dict()
        assert d["checkpoint_id"] == "cp-1"

    def test_from_dict(self):
        data = {
            "checkpoint_id": "cp-1",
            "job_id": "job-1",
            "workflow_name": "test",
            "created_at": "2024-01-01T00:00:00",
            "current_node_id": "node-1",
            "executed_nodes": [],
            "execution_path": [],
            "variables": {},
            "errors": [],
        }
        state = CheckpointState.from_dict(data)
        assert state.checkpoint_id == "cp-1"


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def temp_queue(self, tmp_path):
        return OfflineQueue(db_path=tmp_path / "test.db", robot_id="test")

    @pytest.fixture
    def manager(self, temp_queue):
        return CheckpointManager(temp_queue)

    def test_start_job(self, manager):
        manager.start_job("job-1", "test-workflow")
        assert manager._current_job_id == "job-1"
        assert manager._current_workflow_name == "test-workflow"

    def test_end_job(self, manager):
        manager.start_job("job-1", "test")
        manager.end_job()
        assert manager._current_job_id is None

    def test_is_node_executed(self, manager):
        manager.start_job("job-1", "test")
        manager._executed_nodes.add("node-1")

        assert manager.is_node_executed("node-1") is True
        assert manager.is_node_executed("node-2") is False

    def test_record_error(self, manager):
        manager.start_job("job-1", "test")
        manager.record_error("node-1", "Test error")

        assert len(manager._errors) == 1
        assert manager._errors[0]["node_id"] == "node-1"


class TestCreateCheckpointState:
    """Tests for create_checkpoint_state factory."""

    def test_creates_valid_state(self):
        state = create_checkpoint_state(
            job_id="job-1",
            workflow_name="test",
            node_id="node-1",
            executed_nodes=["node-0"],
            variables={"x": 1},
        )

        assert state.job_id == "job-1"
        assert state.current_node_id == "node-1"
        assert len(state.checkpoint_id) == 8


# ============================================================================
# METRICS COLLECTOR TESTS
# ============================================================================

class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_start_job(self, collector):
        metrics = collector.start_job("job-1", "test-workflow", total_nodes=5)
        assert metrics.job_id == "job-1"
        assert metrics.total_nodes == 5

    def test_end_job(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.end_job(success=True)

        assert collector._total_jobs == 1
        assert collector._successful_jobs == 1

    def test_record_node(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.record_node(
            node_id="node-1",
            node_type="ClickNode",
            duration_ms=100.0,
            success=True,
        )

        assert collector._current_job.completed_nodes == 1
        assert "ClickNode" in collector._node_stats

    def test_record_node_failure(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.record_node(
            node_id="node-1",
            node_type="ClickNode",
            duration_ms=100.0,
            success=False,
            error_type="ElementNotFound",
        )

        assert collector._current_job.failed_nodes == 1

    def test_get_summary(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.end_job(success=True)

        summary = collector.get_summary()
        assert summary["total_jobs"] == 1
        assert summary["success_rate_percent"] == 100.0

    def test_get_node_stats(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.record_node("n1", "ClickNode", 100.0, True)
        collector.record_node("n2", "ClickNode", 200.0, True)
        collector.record_node("n3", "TypeNode", 50.0, True)
        collector.end_job(success=True)

        stats = collector.get_node_stats()
        assert stats["ClickNode"]["total_executions"] == 2
        assert stats["TypeNode"]["total_executions"] == 1

    def test_get_error_summary(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.record_node("n1", "Click", 100.0, False, "Timeout")
        collector.record_node("n2", "Click", 100.0, False, "Timeout")
        collector.record_node("n3", "Click", 100.0, False, "NotFound")
        collector.end_job(success=False, error_message="Failed")

        errors = collector.get_error_summary()
        assert len(errors) > 0

    def test_get_recent_jobs(self, collector):
        collector.start_job("job-1", "test1", 5)
        collector.end_job(success=True)
        collector.start_job("job-2", "test2", 3)
        collector.end_job(success=False)

        recent = collector.get_recent_jobs(limit=10)
        assert len(recent) == 2

    def test_reset(self, collector):
        collector.start_job("job-1", "test", 5)
        collector.end_job(success=True)
        collector.reset()

        assert collector._total_jobs == 0
        assert len(collector._job_metrics) == 0


# ============================================================================
# AUDIT LOGGER TESTS
# ============================================================================

class TestAuditEntry:
    """Tests for AuditEntry."""

    def test_creation(self):
        entry = AuditEntry(
            event_type=AuditEventType.JOB_STARTED,
            severity=AuditSeverity.INFO,
            message="Job started",
            job_id="job-1",
        )
        assert entry.event_type == AuditEventType.JOB_STARTED
        assert entry.job_id == "job-1"

    def test_to_dict(self):
        entry = AuditEntry(
            event_type=AuditEventType.JOB_STARTED,
            severity=AuditSeverity.INFO,
            message="Test",
        )
        d = entry.to_dict()
        assert "timestamp" in d
        assert d["event_type"] == "job.started"

    def test_to_json(self):
        entry = AuditEntry(
            event_type=AuditEventType.JOB_STARTED,
            severity=AuditSeverity.INFO,
            message="Test",
        )
        json_str = entry.to_json()
        assert "job.started" in json_str


class TestAuditLogger:
    """Tests for AuditLogger."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path / "audit"

    @pytest.fixture
    def logger(self, temp_dir):
        return AuditLogger("test-robot", log_dir=temp_dir)

    def test_initialization(self, logger):
        assert logger.robot_id == "test-robot"
        assert logger._current_file is not None

    def test_log_event(self, logger):
        logger.log(
            AuditEventType.JOB_STARTED,
            "Job started",
            job_id="job-1",
        )

        # Check buffer
        assert len(logger._buffer) == 1
        assert logger._buffer[0].job_id == "job-1"

    def test_job_context(self, logger):
        with logger.job_context("job-1"):
            logger.log(AuditEventType.NODE_STARTED, "Node started")

        assert logger._buffer[-1].job_id == "job-1"

    def test_convenience_methods(self, logger):
        logger.robot_started()
        logger.connection_established()
        logger.job_received("job-1", "test-workflow")
        logger.job_started("job-1", 5)
        logger.job_completed("job-1", 1000.0)

        assert len(logger._buffer) == 5

    def test_get_recent(self, logger):
        for i in range(5):
            logger.log(AuditEventType.JOB_STARTED, f"Job {i}")

        recent = logger.get_recent(limit=3)
        assert len(recent) == 3

    def test_query_by_event_type(self, logger):
        logger.job_started("job-1", 5)
        logger.job_completed("job-1", 1000.0)
        logger.job_started("job-2", 3)

        results = logger.query(
            event_types=[AuditEventType.JOB_STARTED],
            limit=10,
        )
        assert len(results) == 2


# ============================================================================
# JOB EXECUTOR TESTS
# ============================================================================

class TestJobExecutorConfig:
    """Tests for JobExecutorConfig."""

    def test_default_values(self):
        config = JobExecutorConfig()
        assert config.max_concurrent_jobs == 3
        assert config.checkpoint_enabled is True

    def test_from_dict(self):
        config = JobExecutorConfig.from_dict({
            "max_concurrent_jobs": 5,
            "checkpoint_enabled": False,
        })
        assert config.max_concurrent_jobs == 5
        assert config.checkpoint_enabled is False


class TestJobExecutor:
    """Tests for JobExecutor."""

    @pytest.fixture
    def executor(self):
        return JobExecutor(max_concurrent_jobs=2)

    def test_initialization(self, executor):
        assert executor.max_concurrent_jobs == 2
        assert executor.running_count == 0
        assert executor.is_at_capacity is False

    @pytest.mark.asyncio
    async def test_start_stop(self, executor):
        await executor.start()
        assert executor._running is True

        await executor.stop()
        assert executor._running is False

    def test_get_status(self, executor):
        status = executor.get_status()
        assert status["max_concurrent_jobs"] == 2
        assert status["running_count"] == 0
        assert status["is_at_capacity"] is False

    def test_set_max_concurrent(self, executor):
        executor.set_max_concurrent(5)
        assert executor.max_concurrent_jobs == 5

    def test_set_max_concurrent_invalid(self, executor):
        with pytest.raises(ValueError):
            executor.set_max_concurrent(0)


# ============================================================================
# ROBOT CONFIG TESTS
# ============================================================================

class TestRobotConfig:
    """Tests for RobotConfig."""

    def test_default_initialization(self):
        config = RobotConfig()
        assert config.robot_id is not None
        assert config.robot_name is not None

    def test_to_dict(self):
        config = RobotConfig()
        d = config.to_dict()

        assert "robot_id" in d
        assert "connection" in d
        assert "job_execution" in d
        assert "observability" in d

    def test_from_dict(self):
        data = {
            "robot_id": "test-id",
            "robot_name": "Test Robot",
            "connection": {"url": "https://test.com"},
            "job_execution": {"max_concurrent_jobs": 5},
        }
        config = RobotConfig.from_dict(data)
        assert config.robot_id == "test-id"
        assert config.job_execution.max_concurrent_jobs == 5


class TestValidateCredentials:
    """Tests for credential validation."""

    def test_missing_url(self):
        valid, error = validate_credentials("", "key")
        assert valid is False
        assert "URL" in error

    def test_missing_key(self):
        valid, error = validate_credentials("https://test.supabase.co", "")
        assert valid is False
        assert "key" in error

    def test_http_url(self):
        valid, error = validate_credentials("http://test.com", "key123456789012345678")
        assert valid is False
        assert "HTTPS" in error

    def test_short_key(self):
        valid, error = validate_credentials("https://test.supabase.co", "short")
        assert valid is False
        assert "invalid" in error.lower()

    def test_valid_credentials(self):
        valid, error = validate_credentials(
            "https://test.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        )
        assert valid is True
        assert error is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRobotHardeningIntegration:
    """Integration tests for robot hardening components."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_connection(self):
        """Test circuit breaker protecting connection operations."""
        cb = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(failure_threshold=2, timeout=0.1),
        )

        fail_count = [0]

        async def flaky_operation():
            fail_count[0] += 1
            if fail_count[0] <= 2:
                raise ConnectionError("Connection failed")
            return "success"

        # First two calls fail
        with pytest.raises(ConnectionError):
            await cb.call(flaky_operation)
        with pytest.raises(ConnectionError):
            await cb.call(flaky_operation)

        # Circuit should be open
        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Should succeed now (half-open -> closed)
        result = await cb.call(flaky_operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_metrics_with_checkpoint(self, tmp_path):
        """Test metrics collection with checkpointing."""
        queue = OfflineQueue(db_path=tmp_path / "test.db", robot_id="test")
        checkpoint_mgr = CheckpointManager(queue)
        metrics = MetricsCollector()

        # Start job
        checkpoint_mgr.start_job("job-1", "test-workflow")
        metrics.start_job("job-1", "test-workflow", 3)

        # Simulate node execution
        for i in range(3):
            node_id = f"node-{i}"
            metrics.record_node(node_id, "TestNode", 100.0, True)
            checkpoint_mgr._executed_nodes.add(node_id)

            # Save checkpoint
            await queue.save_checkpoint(
                "job-1",
                f"cp-{i}",
                node_id,
                {"executed": list(checkpoint_mgr._executed_nodes)},
            )

        # End job
        metrics.end_job(success=True)
        checkpoint_mgr.end_job()

        # Verify
        assert metrics._total_jobs == 1
        assert metrics._successful_jobs == 1

        checkpoint = await queue.get_latest_checkpoint("job-1")
        assert checkpoint is not None
        assert len(checkpoint["state"]["executed"]) == 3

    @pytest.mark.asyncio
    async def test_offline_queue_workflow(self, tmp_path):
        """Test complete offline queue workflow."""
        queue = OfflineQueue(db_path=tmp_path / "test.db", robot_id="test")

        # Cache job
        await queue.cache_job("job-1", '{"nodes": []}')

        # Mark in progress
        await queue.mark_in_progress("job-1")

        # Log events
        await queue.log_event("job-1", "started")
        await queue.log_event("job-1", "node_completed", {"node": "node-1"})

        # Complete job
        await queue.mark_completed("job-1", success=True, result={"status": "done"})

        # Check sync queue
        to_sync = await queue.get_jobs_to_sync()
        assert len(to_sync) == 1

        # Sync
        await queue.mark_synced("job-1")

        # Verify synced
        to_sync = await queue.get_jobs_to_sync()
        assert len(to_sync) == 0

        # Check history
        history = await queue.get_job_history("job-1")
        assert len(history) == 2
