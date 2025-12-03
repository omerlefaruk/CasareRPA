"""
Tests for RobotAgent (distributed_agent.py).

Tests cover:
1. Agent initialization with various configurations
2. Agent lifecycle (start, stop, pause, resume)
3. Job claim and execution
4. Heartbeat mechanism for lease extension
5. Graceful shutdown with job completion waiting
6. Circuit breaker integration
7. Checkpoint save/restore for crash recovery

Mocking strategy:
- Mock PgQueuerConsumer, DBOSWorkflowExecutor, UnifiedResourceManager
- Mock MetricsCollector, AuditLogger
- Use AsyncMock for all async methods
"""

import asyncio
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock

import pytest
import orjson

from casare_rpa.robot.agent import (
    RobotAgent,
    RobotConfig,
    RobotCapabilities,
    AgentState,
    AgentCheckpoint,
    run_agent,
)
from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def temp_checkpoint_dir(tmp_path: Path) -> Path:
    """Create temporary checkpoint directory."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


@pytest.fixture
def robot_config(temp_log_dir: Path, temp_checkpoint_dir: Path) -> RobotConfig:
    """Create a test robot configuration."""
    return RobotConfig(
        robot_id="test-robot-001",
        robot_name="TestRobot",
        postgres_url="postgresql://test:test@localhost:5432/testdb",
        environment="test",
        tags=["test", "unit"],
        batch_size=1,
        max_concurrent_jobs=2,
        poll_interval_seconds=0.05,
        heartbeat_interval_seconds=0.1,
        presence_interval_seconds=0.1,
        visibility_timeout_seconds=30,
        graceful_shutdown_seconds=2,
        enable_checkpointing=True,
        enable_circuit_breaker=True,
        enable_audit_logging=False,
        log_dir=temp_log_dir,
        checkpoint_path=temp_checkpoint_dir,
    )


@pytest.fixture
def minimal_config(temp_log_dir: Path, temp_checkpoint_dir: Path) -> RobotConfig:
    """Create minimal config with fast polling for tests."""
    return RobotConfig(
        robot_id="test-robot-minimal",
        robot_name="MinimalRobot",
        postgres_url="",  # No database
        environment="test",
        poll_interval_seconds=0.01,
        heartbeat_interval_seconds=0.05,
        presence_interval_seconds=0.05,
        enable_checkpointing=False,
        enable_circuit_breaker=False,
        enable_audit_logging=False,
        enable_realtime=False,
        log_dir=temp_log_dir,
        checkpoint_path=temp_checkpoint_dir,
    )


@pytest.fixture
def mock_consumer():
    """Create mock PgQueuerConsumer."""
    consumer = AsyncMock()
    consumer.start = AsyncMock()
    consumer.stop = AsyncMock()
    consumer.claim_job = AsyncMock(return_value=None)
    consumer.complete_job = AsyncMock()
    consumer.fail_job = AsyncMock()
    consumer.release_job = AsyncMock()
    consumer.extend_lease = AsyncMock(return_value=True)
    consumer.update_progress = AsyncMock()
    consumer._pool = MagicMock()
    consumer._pool.acquire = MagicMock()
    return consumer


@pytest.fixture
def mock_executor():
    """Create mock DBOSWorkflowExecutor."""
    executor = AsyncMock()
    executor.start = AsyncMock()
    executor.stop = AsyncMock()

    # Create a result object with the expected attributes
    result = Mock()
    result.success = True
    result.executed_nodes = 5
    result.duration_ms = 1000
    result.recovered = False
    result.error = None

    executor.execute_workflow = AsyncMock(return_value=result)
    return executor


@pytest.fixture
def mock_resource_manager():
    """Create mock UnifiedResourceManager."""
    manager = AsyncMock()
    manager.start = AsyncMock()
    manager.stop = AsyncMock()
    manager.acquire_resources_for_job = AsyncMock(return_value={"browser": Mock()})
    manager.release_resources = AsyncMock()
    return manager


@pytest.fixture
def mock_metrics():
    """Create mock MetricsCollector."""
    metrics = Mock()
    metrics.start_resource_monitoring = AsyncMock()
    metrics.stop_resource_monitoring = AsyncMock()
    metrics.start_job = Mock()
    metrics.end_job = Mock()
    metrics.record_node = Mock()
    return metrics


@pytest.fixture
def sample_job():
    """Create a sample job object for testing."""
    job = Mock()
    job.job_id = f"job-{uuid.uuid4().hex[:8]}"
    job.workflow_name = "Test Workflow"
    job.workflow_json = '{"nodes": [], "connections": []}'
    job.variables = {"input_var": "test_value"}
    job.priority = 5
    job.retry_count = 0
    return job


# =============================================================================
# TEST SECTION 1: Agent Initialization
# =============================================================================


class TestAgentInitialization:
    """Tests for RobotAgent initialization."""

    def test_init_with_default_config(
        self, temp_log_dir: Path, temp_checkpoint_dir: Path
    ):
        """Agent initializes with default configuration."""
        config = RobotConfig(
            log_dir=temp_log_dir,
            checkpoint_path=temp_checkpoint_dir,
            enable_audit_logging=False,
        )
        agent = RobotAgent(config)

        assert agent.robot_id is not None
        assert agent.name is not None
        assert agent._state == AgentState.STOPPED
        assert not agent.is_running

    def test_init_with_custom_config(self, robot_config: RobotConfig):
        """Agent initializes with custom configuration."""
        agent = RobotAgent(robot_config)

        assert agent.robot_id == "test-robot-001"
        assert agent.name == "TestRobot"
        assert agent.config.environment == "test"
        assert agent.config.max_concurrent_jobs == 2

    def test_init_creates_log_directory(self, robot_config: RobotConfig):
        """Agent creates log directory on initialization."""
        agent = RobotAgent(robot_config)

        assert robot_config.log_dir.exists()

    def test_init_builds_capabilities(self, robot_config: RobotConfig):
        """Agent builds capabilities on initialization."""
        agent = RobotAgent(robot_config)

        assert agent._capabilities is not None
        assert isinstance(agent._capabilities, RobotCapabilities)
        assert (
            agent._capabilities.max_concurrent_jobs == robot_config.max_concurrent_jobs
        )

    def test_init_creates_circuit_breaker_when_enabled(self, robot_config: RobotConfig):
        """Agent creates circuit breaker when enabled."""
        agent = RobotAgent(robot_config)

        assert agent._circuit_breaker is not None
        assert isinstance(agent._circuit_breaker, CircuitBreaker)

    def test_init_no_circuit_breaker_when_disabled(self, minimal_config: RobotConfig):
        """Agent does not create circuit breaker when disabled."""
        agent = RobotAgent(minimal_config)

        assert agent._circuit_breaker is None

    def test_init_with_job_complete_callback(self, robot_config: RobotConfig):
        """Agent accepts job completion callback."""
        callback = Mock()
        agent = RobotAgent(robot_config, on_job_complete=callback)

        assert agent._on_job_complete == callback

    def test_config_from_env(
        self, monkeypatch, temp_log_dir: Path, temp_checkpoint_dir: Path
    ):
        """Config can be loaded from environment variables."""
        monkeypatch.setenv("CASARE_ROBOT_ID", "env-robot-001")
        monkeypatch.setenv("CASARE_ROBOT_NAME", "EnvRobot")
        monkeypatch.setenv("CASARE_ENVIRONMENT", "staging")
        monkeypatch.setenv("CASARE_ROBOT_TAGS", "web,desktop,test")
        monkeypatch.setenv("CASARE_MAX_CONCURRENT_JOBS", "4")

        config = RobotConfig.from_env()
        config.log_dir = temp_log_dir
        config.checkpoint_path = temp_checkpoint_dir

        assert config.robot_id == "env-robot-001"
        assert config.robot_name == "EnvRobot"
        assert config.environment == "staging"
        assert "web" in config.tags
        assert config.max_concurrent_jobs == 4


# =============================================================================
# TEST SECTION 2: Agent Lifecycle
# =============================================================================


class TestAgentLifecycle:
    """Tests for agent lifecycle (start, stop, pause, resume)."""

    @pytest.mark.asyncio
    async def test_start_sets_running_state(self, minimal_config: RobotConfig):
        """Starting agent sets running state."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    await agent.start()

        assert agent._state == AgentState.RUNNING
        assert agent.is_running
        assert agent._running

        await agent.stop()

    @pytest.mark.asyncio
    async def test_start_prevents_double_start(self, minimal_config: RobotConfig):
        """Starting already running agent logs warning."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    await agent.start()
                    # Second start should not raise, just warn
                    await agent.start()

        assert agent.is_running

        await agent.stop()

    @pytest.mark.asyncio
    async def test_stop_sets_stopped_state(self, minimal_config: RobotConfig):
        """Stopping agent sets stopped state."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    await agent.start()
                    await agent.stop()

        assert agent._state == AgentState.STOPPED
        assert not agent.is_running
        assert not agent._running

    @pytest.mark.asyncio
    async def test_stop_idempotent_when_not_running(self, minimal_config: RobotConfig):
        """Stopping non-running agent is safe."""
        agent = RobotAgent(minimal_config)

        # Should not raise
        await agent.stop()

        assert agent._state == AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_pause_sets_paused_state(self, minimal_config: RobotConfig):
        """Pausing agent sets paused state."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    with patch.object(
                        agent, "_update_registration_status", new_callable=AsyncMock
                    ):
                        await agent.start()
                        await agent.pause()

        assert agent._state == AgentState.PAUSED
        assert agent.is_paused

        await agent.stop()

    @pytest.mark.asyncio
    async def test_resume_from_paused_state(self, minimal_config: RobotConfig):
        """Resuming agent from paused state returns to running."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    with patch.object(
                        agent, "_update_registration_status", new_callable=AsyncMock
                    ):
                        await agent.start()
                        await agent.pause()
                        await agent.resume()

        assert agent._state == AgentState.RUNNING
        assert not agent.is_paused

        await agent.stop()

    @pytest.mark.asyncio
    async def test_pause_only_from_running_state(self, minimal_config: RobotConfig):
        """Pause only works from running state."""
        agent = RobotAgent(minimal_config)

        await agent.pause()  # Should log warning but not raise

        assert agent._state == AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_resume_only_from_paused_state(self, minimal_config: RobotConfig):
        """Resume only works from paused state."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    await agent.start()
                    await agent.resume()  # Should log warning but not raise

        assert agent._state == AgentState.RUNNING

        await agent.stop()


# =============================================================================
# TEST SECTION 3: Job Execution
# =============================================================================


class TestJobExecution:
    """Tests for job claim and execution."""

    @pytest.mark.asyncio
    async def test_execute_job_success(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Successfully executed job marks as completed."""
        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        await agent._execute_job(sample_job)

        mock_executor.execute_workflow.assert_awaited_once()
        mock_consumer.complete_job.assert_awaited_once()
        assert agent._stats["jobs_completed"] == 1
        assert agent._stats["jobs_failed"] == 0

    @pytest.mark.asyncio
    async def test_execute_job_failure(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Failed job execution marks as failed."""
        result = Mock()
        result.success = False
        result.error = "Workflow execution failed"
        result.duration_ms = 500
        mock_executor.execute_workflow.return_value = result

        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        await agent._execute_job(sample_job)

        mock_consumer.fail_job.assert_awaited_once()
        assert agent._stats["jobs_failed"] == 1
        assert agent._stats["jobs_completed"] == 0

    @pytest.mark.asyncio
    async def test_execute_job_exception(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Exception during execution marks job as failed."""
        mock_executor.execute_workflow.side_effect = RuntimeError("Execution crashed")

        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        await agent._execute_job(sample_job)

        mock_consumer.fail_job.assert_awaited_once()
        call_args = mock_consumer.fail_job.call_args
        assert "Execution crashed" in call_args[1]["error_message"]

    @pytest.mark.asyncio
    async def test_execute_job_calls_callback_on_success(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Job completion callback is called on success."""
        callback = Mock()

        agent = RobotAgent(minimal_config, on_job_complete=callback)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        await agent._execute_job(sample_job)

        callback.assert_called_once()
        call_args = callback.call_args[0]
        assert call_args[0] == sample_job.job_id
        assert call_args[1] is True  # success

    @pytest.mark.asyncio
    async def test_execute_job_calls_callback_on_failure(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Job completion callback is called on failure."""
        result = Mock()
        result.success = False
        result.error = "Test error"
        result.duration_ms = 100
        mock_executor.execute_workflow.return_value = result

        callback = Mock()

        agent = RobotAgent(minimal_config, on_job_complete=callback)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        await agent._execute_job(sample_job)

        callback.assert_called_once()
        call_args = callback.call_args[0]
        assert call_args[1] is False  # success
        assert call_args[2] == "Test error"  # error message

    @pytest.mark.asyncio
    async def test_execute_cancelled_job(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Cancelled job is handled properly."""
        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True
        agent._cancelled_jobs.add(sample_job.job_id)

        await agent._execute_job(sample_job)

        mock_consumer.fail_job.assert_awaited_once()
        mock_executor.execute_workflow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_job_tracking(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Job is tracked during execution."""
        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        # Make executor delay so we can check tracking
        async def delayed_execute(*args, **kwargs):
            await asyncio.sleep(0.1)
            result = Mock()
            result.success = True
            result.executed_nodes = 1
            result.duration_ms = 100
            result.recovered = False
            result.error = None
            return result

        mock_executor.execute_workflow.side_effect = delayed_execute

        task = asyncio.create_task(agent._execute_job(sample_job))

        await asyncio.sleep(0.05)
        assert sample_job.job_id in agent._current_jobs

        await task
        assert sample_job.job_id not in agent._current_jobs


# =============================================================================
# TEST SECTION 4: Heartbeat Mechanism
# =============================================================================


class TestHeartbeatMechanism:
    """Tests for heartbeat lease extension."""

    @pytest.mark.asyncio
    async def test_heartbeat_extends_lease(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        sample_job,
    ):
        """Heartbeat loop extends lease for active jobs."""
        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._running = True
        agent._current_jobs[sample_job.job_id] = sample_job

        # Run heartbeat loop briefly
        task = asyncio.create_task(agent._heartbeat_loop())

        await asyncio.sleep(0.15)  # Allow 2-3 heartbeats

        agent._running = False
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert mock_consumer.extend_lease.await_count >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_no_extension_without_jobs(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
    ):
        """Heartbeat does not extend lease when no jobs active."""
        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._running = True
        # No jobs in _current_jobs

        task = asyncio.create_task(agent._heartbeat_loop())

        await asyncio.sleep(0.15)

        agent._running = False
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        mock_consumer.extend_lease.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_heartbeat_handles_extension_failure(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        sample_job,
    ):
        """Heartbeat handles lease extension failure gracefully."""
        mock_consumer.extend_lease.return_value = False

        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._running = True
        agent._current_jobs[sample_job.job_id] = sample_job

        task = asyncio.create_task(agent._heartbeat_loop())

        await asyncio.sleep(0.15)

        agent._running = False
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should not crash, just log warning
        assert mock_consumer.extend_lease.await_count >= 1


# =============================================================================
# TEST SECTION 5: Graceful Shutdown
# =============================================================================


class TestGracefulShutdown:
    """Tests for graceful shutdown behavior."""

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_job_completion(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Shutdown waits for current job to complete."""
        minimal_config.graceful_shutdown_seconds = 5

        completion_event = asyncio.Event()

        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.2)
            completion_event.set()
            result = Mock()
            result.success = True
            result.executed_nodes = 1
            result.duration_ms = 200
            result.recovered = False
            result.error = None
            return result

        mock_executor.execute_workflow.side_effect = slow_execute

        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True

        # Start job execution
        exec_task = asyncio.create_task(agent._execute_job(sample_job))

        await asyncio.sleep(0.05)  # Let job start

        # Start shutdown while job is running
        stop_task = asyncio.create_task(agent.stop())

        await asyncio.wait([exec_task, stop_task], timeout=1.0)

        assert completion_event.is_set()

    @pytest.mark.asyncio
    async def test_shutdown_respects_timeout(
        self,
        minimal_config: RobotConfig,
        mock_consumer,
        mock_executor,
        sample_job,
    ):
        """Shutdown respects grace period timeout."""
        minimal_config.graceful_shutdown_seconds = 0.1

        async def very_slow_execute(*args, **kwargs):
            await asyncio.sleep(5)  # Would take too long
            result = Mock()
            result.success = True
            result.executed_nodes = 1
            result.duration_ms = 5000
            result.recovered = False
            result.error = None
            return result

        mock_executor.execute_workflow.side_effect = very_slow_execute

        agent = RobotAgent(minimal_config)
        agent._consumer = mock_consumer
        agent._executor = mock_executor
        agent._running = True
        agent._current_jobs[sample_job.job_id] = sample_job

        start_time = asyncio.get_event_loop().time()
        await agent.stop()
        elapsed = asyncio.get_event_loop().time() - start_time

        # Should timeout quickly, not wait for 5 second job
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_shutdown_cancels_background_tasks(self, minimal_config: RobotConfig):
        """Shutdown cancels all background tasks."""
        agent = RobotAgent(minimal_config)

        with patch.object(agent, "_init_components", new_callable=AsyncMock):
            with patch.object(agent, "_register", new_callable=AsyncMock):
                with patch.object(agent, "_setup_signal_handlers"):
                    await agent.start()

        # Tasks should be running
        assert agent._job_loop_task is not None
        assert agent._heartbeat_task is not None

        await agent.stop()

        # Tasks should be done (cancelled)
        assert agent._job_loop_task.done()
        assert agent._heartbeat_task.done()


# =============================================================================
# TEST SECTION 6: Circuit Breaker Integration
# =============================================================================


class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, robot_config: RobotConfig):
        """Circuit breaker opens after threshold failures."""
        robot_config.circuit_breaker.failure_threshold = 2

        agent = RobotAgent(robot_config)

        assert agent._circuit_breaker is not None
        assert agent._circuit_breaker.is_closed

        # Simulate failures
        async def failing_operation():
            raise RuntimeError("Test failure")

        for _ in range(3):
            try:
                await agent._circuit_breaker.call(failing_operation)
            except (RuntimeError, CircuitBreakerOpenError):
                pass

        assert agent._circuit_breaker.is_open

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_calls_when_open(
        self, robot_config: RobotConfig
    ):
        """Open circuit breaker blocks calls."""
        robot_config.circuit_breaker.failure_threshold = 1
        robot_config.circuit_breaker.timeout = 10  # Long timeout

        agent = RobotAgent(robot_config)

        # Force circuit open
        await agent._circuit_breaker.force_open()

        async def operation():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            await agent._circuit_breaker.call(operation)

    @pytest.mark.asyncio
    async def test_circuit_state_change_updates_stats(self, robot_config: RobotConfig):
        """Circuit state change updates agent stats."""
        robot_config.circuit_breaker.failure_threshold = 1

        agent = RobotAgent(robot_config)

        initial_opens = agent._stats["circuit_breaker_opens"]

        await agent._circuit_breaker.force_open()

        assert agent._stats["circuit_breaker_opens"] == initial_opens + 1


# =============================================================================
# TEST SECTION 7: Checkpoint Management
# =============================================================================


class TestCheckpointManagement:
    """Tests for checkpoint save/restore."""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, robot_config: RobotConfig):
        """Agent saves checkpoint with current state."""
        agent = RobotAgent(robot_config)
        agent._state = AgentState.RUNNING
        agent._stats["jobs_completed"] = 10
        agent._stats["jobs_failed"] = 2

        await agent._save_checkpoint()

        assert agent._checkpoint_file.exists()

        data = orjson.loads(agent._checkpoint_file.read_bytes())
        assert data["robot_id"] == robot_config.robot_id
        assert data["state"] == "running"
        assert data["stats"]["jobs_completed"] == 10

    @pytest.mark.asyncio
    async def test_restore_from_checkpoint(self, robot_config: RobotConfig):
        """Agent restores state from checkpoint."""
        # First, save a checkpoint
        agent = RobotAgent(robot_config)
        agent._state = AgentState.RUNNING
        agent._stats["jobs_completed"] = 15
        agent._stats["jobs_failed"] = 3

        await agent._save_checkpoint()

        # Create new agent and restore
        agent2 = RobotAgent(robot_config)
        await agent2._restore_from_checkpoint()

        assert agent2._stats["jobs_completed"] == 15
        assert agent2._stats["jobs_failed"] == 3
        assert agent2._stats["checkpoints_restored"] == 1

    @pytest.mark.asyncio
    async def test_restore_no_checkpoint(self, robot_config: RobotConfig):
        """Restore handles missing checkpoint gracefully."""
        # Delete any existing checkpoint
        agent = RobotAgent(robot_config)
        if agent._checkpoint_file.exists():
            agent._checkpoint_file.unlink()

        # Should not raise
        await agent._restore_from_checkpoint()

        assert agent._stats["checkpoints_restored"] == 0

    @pytest.mark.asyncio
    async def test_checkpoint_prunes_old_files(self, robot_config: RobotConfig):
        """Checkpoint management prunes old files."""
        robot_config.checkpoint_retention_count = 2

        agent = RobotAgent(robot_config)

        # Create multiple checkpoints
        for i in range(5):
            agent._stats["jobs_completed"] = i
            # Create checkpoint with unique name
            checkpoint_file = robot_config.checkpoint_path / f"agent_test_{i}.json"
            checkpoint_file.write_bytes(b'{"test": true}')

        await agent._prune_checkpoints()

        remaining = list(robot_config.checkpoint_path.glob("agent_*.json"))
        assert len(remaining) <= robot_config.checkpoint_retention_count + 1


# =============================================================================
# TEST SECTION 8: Status and Capabilities
# =============================================================================


class TestStatusAndCapabilities:
    """Tests for status reporting and capabilities."""

    def test_get_status(self, robot_config: RobotConfig):
        """Agent returns comprehensive status."""
        agent = RobotAgent(robot_config)
        agent._stats["jobs_completed"] = 5
        agent._stats["jobs_failed"] = 1

        status = agent.get_status()

        assert status["robot_id"] == robot_config.robot_id
        assert status["robot_name"] == robot_config.robot_name
        assert status["state"] == "stopped"
        assert status["stats"]["jobs_completed"] == 5

    def test_capabilities_include_system_info(self, robot_config: RobotConfig):
        """Capabilities include system information."""
        agent = RobotAgent(robot_config)

        caps = agent._capabilities.to_dict()

        assert "platform" in caps
        assert "cpu_cores" in caps
        assert "memory_gb" in caps
        assert caps["max_concurrent_jobs"] == robot_config.max_concurrent_jobs

    def test_cancel_job(self, robot_config: RobotConfig, sample_job):
        """Cancel job adds to cancelled set."""
        agent = RobotAgent(robot_config)
        agent._current_jobs[sample_job.job_id] = sample_job

        result = agent.cancel_job(sample_job.job_id)

        assert result is True
        assert sample_job.job_id in agent._cancelled_jobs

    def test_cancel_nonexistent_job(self, robot_config: RobotConfig):
        """Cancel nonexistent job returns False."""
        agent = RobotAgent(robot_config)

        result = agent.cancel_job("nonexistent-job-id")

        assert result is False


# =============================================================================
# TEST SECTION 9: Config Edge Cases
# =============================================================================


class TestConfigEdgeCases:
    """Tests for configuration edge cases."""

    def test_config_generates_robot_id_if_missing(
        self, temp_log_dir: Path, temp_checkpoint_dir: Path
    ):
        """Config generates robot ID if not provided."""
        config = RobotConfig(
            robot_id=None,
            log_dir=temp_log_dir,
            checkpoint_path=temp_checkpoint_dir,
        )

        assert config.robot_id is not None
        assert config.robot_id.startswith("robot-")

    def test_config_to_dict_masks_secrets(self, robot_config: RobotConfig):
        """Config to_dict masks sensitive fields."""
        config_dict = robot_config.to_dict()

        assert config_dict["postgres_url"] == "***"
        # supabase_key would be masked if set

    def test_config_from_dict(self, temp_log_dir: Path, temp_checkpoint_dir: Path):
        """Config can be created from dictionary."""
        data = {
            "robot_id": "dict-robot-001",
            "robot_name": "DictRobot",
            "environment": "production",
            "max_concurrent_jobs": 5,
        }

        config = RobotConfig.from_dict(data.copy())
        config.log_dir = temp_log_dir
        config.checkpoint_path = temp_checkpoint_dir

        assert config.robot_id == "dict-robot-001"
        assert config.max_concurrent_jobs == 5


# =============================================================================
# TEST SECTION 10: Agent Checkpoint Dataclass
# =============================================================================


class TestAgentCheckpoint:
    """Tests for AgentCheckpoint dataclass."""

    def test_checkpoint_to_dict(self):
        """Checkpoint converts to dictionary."""
        checkpoint = AgentCheckpoint(
            checkpoint_id="cp-001",
            robot_id="robot-001",
            state="running",
            current_jobs=["job-1", "job-2"],
            created_at="2024-01-01T00:00:00Z",
            last_heartbeat="2024-01-01T00:01:00Z",
            stats={"jobs_completed": 10},
        )

        data = checkpoint.to_dict()

        assert data["checkpoint_id"] == "cp-001"
        assert data["current_jobs"] == ["job-1", "job-2"]

    def test_checkpoint_from_dict(self):
        """Checkpoint can be created from dictionary."""
        data = {
            "checkpoint_id": "cp-002",
            "robot_id": "robot-002",
            "state": "paused",
            "current_jobs": [],
            "created_at": "2024-01-01T00:00:00Z",
            "last_heartbeat": "2024-01-01T00:00:00Z",
            "stats": {},
        }

        checkpoint = AgentCheckpoint.from_dict(data)

        assert checkpoint.checkpoint_id == "cp-002"
        assert checkpoint.state == "paused"


# =============================================================================
# TEST SECTION 11: Run Agent Helper
# =============================================================================


class TestRunAgentHelper:
    """Tests for run_agent convenience function."""

    @pytest.mark.asyncio
    async def test_run_agent_creates_agent(self, minimal_config: RobotConfig):
        """run_agent creates and starts agent."""
        with patch("casare_rpa.robot.agent.RobotAgent") as MockAgent:
            mock_instance = AsyncMock()
            mock_instance._shutdown_event = asyncio.Event()
            mock_instance.start = AsyncMock()
            mock_instance.stop = AsyncMock()
            MockAgent.return_value = mock_instance

            # Set shutdown event immediately so we don't hang
            async def set_shutdown():
                await asyncio.sleep(0.05)
                mock_instance._shutdown_event.set()

            asyncio.create_task(set_shutdown())

            await run_agent(minimal_config)

            mock_instance.start.assert_awaited_once()
            mock_instance.stop.assert_awaited_once()
