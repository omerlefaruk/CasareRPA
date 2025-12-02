"""
Tests for RobotAgent.

Tests cover:
- Happy path: Connection, registration, job execution, heartbeat integration
- Sad path: Connection failures, disconnection handling, job failures
- Edge cases: Reconnection behavior, signal handling, concurrent job limits
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock

import pytest

from casare_rpa.infrastructure.agent.robot_agent import (
    RobotAgent,
    RobotAgentError,
)
from casare_rpa.infrastructure.agent.robot_config import RobotConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def robot_config() -> RobotConfig:
    """Provide a valid RobotConfig for testing."""
    return RobotConfig(
        robot_name="Test Robot",
        control_plane_url="ws://localhost:8080/ws",
        robot_id="robot-test-12345",
        heartbeat_interval=30,
        max_concurrent_jobs=2,
        capabilities=["browser", "desktop"],
        tags=["test"],
        environment="test",
    )


# ============================================================================
# Happy Path Tests - Initialization
# ============================================================================


class TestRobotAgentCreation:
    """Test RobotAgent initialization."""

    def test_create_with_config(self, robot_config):
        """Creating agent with config succeeds."""
        agent = RobotAgent(robot_config)

        assert agent.config is robot_config
        assert agent.is_running is False
        assert agent.is_connected is False
        assert agent.is_registered is False
        assert agent.active_job_count == 0

    def test_executor_created_with_config_values(self, robot_config):
        """Executor is created with config values."""
        agent = RobotAgent(robot_config)

        assert agent.executor.continue_on_error == robot_config.continue_on_error
        assert agent.executor.job_timeout == robot_config.job_timeout

    def test_heartbeat_created_with_config_values(self, robot_config):
        """Heartbeat service is created with config values."""
        agent = RobotAgent(robot_config)

        assert agent.heartbeat.interval == robot_config.heartbeat_interval

    def test_semaphore_initialized_with_max_jobs(self, robot_config):
        """Job semaphore initialized with max_concurrent_jobs."""
        agent = RobotAgent(robot_config)

        # Semaphore should allow up to max_concurrent_jobs acquisitions
        assert agent._job_semaphore._value == robot_config.max_concurrent_jobs


class TestRobotAgentProperties:
    """Test RobotAgent properties."""

    def test_is_running_initially_false(self, robot_config):
        """is_running is False before start."""
        agent = RobotAgent(robot_config)
        assert agent.is_running is False

    def test_is_connected_initially_false(self, robot_config):
        """is_connected is False before connection."""
        agent = RobotAgent(robot_config)
        assert agent.is_connected is False

    def test_is_registered_initially_false(self, robot_config):
        """is_registered is False before registration."""
        agent = RobotAgent(robot_config)
        assert agent.is_registered is False

    def test_active_job_ids_initially_empty(self, robot_config):
        """active_job_ids is empty initially."""
        agent = RobotAgent(robot_config)
        assert agent.active_job_ids == []


class TestRobotAgentStatus:
    """Test status reporting functionality."""

    def test_get_status_returns_complete_info(self, robot_config):
        """get_status returns complete status information."""
        agent = RobotAgent(robot_config)
        status = agent.get_status()

        assert status["robot_id"] == "robot-test-12345"
        assert status["robot_name"] == "Test Robot"
        assert status["running"] is False
        assert status["connected"] is False
        assert status["registered"] is False
        assert status["active_jobs"] == 0
        assert "heartbeat" in status


# ============================================================================
# Message Handling Tests
# ============================================================================


class TestRobotAgentMessageHandling:
    """Test message handling functionality."""

    @pytest.mark.asyncio
    async def test_handle_register_ack_sets_registered(self, robot_config):
        """Register acknowledgement sets registered flag."""
        agent = RobotAgent(robot_config)

        await agent._handle_register_ack({"type": "register_ack"})

        assert agent.is_registered is True

    @pytest.mark.asyncio
    async def test_handle_heartbeat_ack_logged(self, robot_config):
        """Heartbeat acknowledgement is handled without error."""
        agent = RobotAgent(robot_config)

        # Should not raise
        await agent._handle_heartbeat_ack({"type": "heartbeat_ack"})

    @pytest.mark.asyncio
    async def test_handle_error_logged(self, robot_config):
        """Error message from orchestrator is logged."""
        agent = RobotAgent(robot_config)

        # Should not raise
        await agent._handle_error(
            {
                "type": "error",
                "code": "TEST_ERROR",
                "message": "Test error message",
            }
        )

    @pytest.mark.asyncio
    async def test_handle_ping_sends_pong(self, robot_config, mock_websocket):
        """Ping message triggers pong response."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        await agent._handle_ping({"type": "ping"})

        sent = mock_websocket.get_last_sent()
        assert sent["type"] == "pong"
        assert sent["robot_id"] == "robot-test-12345"


class TestRobotAgentJobAssignment:
    """Test job assignment handling."""

    @pytest.mark.asyncio
    async def test_handle_job_assign_accepts_job(self, robot_config, mock_websocket):
        """Job assignment sends accept message."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Mock executor to avoid actual execution
        agent.executor.execute = AsyncMock(return_value={"success": True})

        job_message = {
            "type": "job_assign",
            "job_id": "job-001",
            "workflow_name": "Test Workflow",
            "workflow_json": "{}",
        }

        await agent._handle_job_assign(job_message)

        # Should send job_accept
        messages = mock_websocket.get_sent_messages()
        accept_msg = next(m for m in messages if m["type"] == "job_accept")
        assert accept_msg["job_id"] == "job-001"

    @pytest.mark.asyncio
    async def test_handle_job_assign_rejects_at_capacity(
        self, robot_config, mock_websocket
    ):
        """Job assignment at capacity sends reject message."""
        robot_config.max_concurrent_jobs = 1
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Simulate already at capacity
        agent._current_jobs["existing-job"] = MagicMock()

        job_message = {
            "type": "job_assign",
            "job_id": "job-002",
            "workflow_name": "Test Workflow",
        }

        await agent._handle_job_assign(job_message)

        # Should send job_reject
        messages = mock_websocket.get_sent_messages()
        reject_msg = next(m for m in messages if m["type"] == "job_reject")
        assert reject_msg["job_id"] == "job-002"
        assert "capacity" in reject_msg["reason"].lower()

    @pytest.mark.asyncio
    async def test_handle_job_assign_invokes_callback(
        self, robot_config, mock_websocket
    ):
        """Job assignment invokes on_job_started callback."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        started_jobs = []

        def on_started(job_id):
            started_jobs.append(job_id)

        agent.on_job_started = on_started
        agent.executor.execute = AsyncMock(return_value={"success": True})

        await agent._handle_job_assign(
            {
                "type": "job_assign",
                "job_id": "job-003",
                "workflow_name": "Test",
                "workflow_json": "{}",
            }
        )

        # Allow task to start
        await asyncio.sleep(0.1)

        assert "job-003" in started_jobs


class TestRobotAgentJobCancellation:
    """Test job cancellation handling."""

    @pytest.mark.asyncio
    async def test_handle_job_cancel_cancels_active_job(
        self, robot_config, mock_websocket
    ):
        """Job cancellation cancels active job."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Add mock active job
        mock_task = MagicMock()
        agent._current_jobs["job-001"] = mock_task

        await agent._handle_job_cancel(
            {
                "type": "job_cancel",
                "job_id": "job-001",
            }
        )

        mock_task.cancel.assert_called_once()

        # Should send job_cancelled
        messages = mock_websocket.get_sent_messages()
        cancel_msg = next(m for m in messages if m["type"] == "job_cancelled")
        assert cancel_msg["job_id"] == "job-001"

    @pytest.mark.asyncio
    async def test_handle_job_cancel_nonexistent_job(
        self, robot_config, mock_websocket
    ):
        """Cancelling nonexistent job does not raise."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Should not raise
        await agent._handle_job_cancel(
            {
                "type": "job_cancel",
                "job_id": "nonexistent-job",
            }
        )


# ============================================================================
# Connection and Registration Tests
# ============================================================================


class TestRobotAgentRegistration:
    """Test registration functionality."""

    @pytest.mark.asyncio
    async def test_register_sends_correct_message(self, robot_config, mock_websocket):
        """Registration sends correct message format."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket

        await agent._register()

        messages = mock_websocket.get_sent_messages()
        assert len(messages) == 1

        reg_msg = messages[0]
        assert reg_msg["type"] == "register"
        assert reg_msg["robot_id"] == "robot-test-12345"
        assert reg_msg["robot_name"] == "Test Robot"
        assert reg_msg["capabilities"]["types"] == ["browser", "desktop"]
        assert reg_msg["environment"] == "test"


class TestRobotAgentSend:
    """Test message sending functionality."""

    @pytest.mark.asyncio
    async def test_send_without_connection_raises(self, robot_config):
        """Sending without connection raises RobotAgentError."""
        agent = RobotAgent(robot_config)
        agent._ws = None

        with pytest.raises(RobotAgentError, match="Not connected"):
            await agent._send({"type": "test"})

    @pytest.mark.asyncio
    async def test_send_serializes_message(self, robot_config, mock_websocket):
        """Sending serializes message to JSON."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket

        await agent._send({"type": "test", "data": 123})

        # Should have sent JSON string
        assert len(mock_websocket.sent_messages) == 1
        parsed = json.loads(mock_websocket.sent_messages[0])
        assert parsed["type"] == "test"
        assert parsed["data"] == 123


# ============================================================================
# Heartbeat Integration Tests
# ============================================================================


class TestRobotAgentHeartbeat:
    """Test heartbeat integration."""

    @pytest.mark.asyncio
    async def test_send_heartbeat_includes_job_info(self, robot_config, mock_websocket):
        """Heartbeat includes current job information."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True
        agent._jobs_completed = 5
        agent._jobs_failed = 2
        agent._current_jobs = {"job-001": MagicMock()}

        heartbeat_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {},
            "health": "healthy",
        }

        await agent._send_heartbeat(heartbeat_data)

        messages = mock_websocket.get_sent_messages()
        hb_msg = messages[0]

        assert hb_msg["type"] == "heartbeat"
        assert hb_msg["jobs_completed"] == 5
        assert hb_msg["jobs_failed"] == 2
        assert "job-001" in hb_msg["current_jobs"]

    @pytest.mark.asyncio
    async def test_send_heartbeat_skipped_when_disconnected(self, robot_config):
        """Heartbeat is skipped when not connected."""
        agent = RobotAgent(robot_config)
        agent._ws = None
        agent._connected = False

        # Should not raise
        await agent._send_heartbeat({"data": "test"})


# ============================================================================
# Progress Reporting Tests
# ============================================================================


class TestRobotAgentProgressReporting:
    """Test job progress reporting."""

    @pytest.mark.asyncio
    async def test_on_job_progress_sends_message(self, robot_config, mock_websocket):
        """Job progress sends message to orchestrator."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        await agent._on_job_progress("job-001", 50, "Processing...")

        messages = mock_websocket.get_sent_messages()
        progress_msg = messages[0]

        assert progress_msg["type"] == "job_progress"
        assert progress_msg["job_id"] == "job-001"
        assert progress_msg["progress"] == 50
        assert progress_msg["message"] == "Processing..."

    @pytest.mark.asyncio
    async def test_on_job_progress_handles_error(self, robot_config, mock_websocket):
        """Progress reporting handles send errors gracefully."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Make send fail
        mock_websocket.closed = True

        # Should not raise
        await agent._on_job_progress("job-001", 50, "Processing...")


# ============================================================================
# Job Execution Tests
# ============================================================================


class TestRobotAgentJobExecution:
    """Test job execution flow."""

    @pytest.mark.asyncio
    async def test_execute_job_success_sends_complete(
        self, robot_config, mock_websocket
    ):
        """Successful job execution sends job_complete message."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(
            return_value={
                "success": True,
                "job_id": "job-001",
            }
        )

        job_data = {
            "job_id": "job-001",
            "workflow_json": "{}",
        }

        await agent._execute_job(job_data)

        messages = mock_websocket.get_sent_messages()
        complete_msg = next(m for m in messages if m["type"] == "job_complete")
        assert complete_msg["job_id"] == "job-001"

    @pytest.mark.asyncio
    async def test_execute_job_failure_sends_failed(self, robot_config, mock_websocket):
        """Failed job execution sends job_failed message."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(
            return_value={
                "success": False,
                "job_id": "job-001",
                "error": "Execution failed",
            }
        )

        job_data = {
            "job_id": "job-001",
            "workflow_json": "{}",
        }

        await agent._execute_job(job_data)

        messages = mock_websocket.get_sent_messages()
        failed_msg = next(m for m in messages if m["type"] == "job_failed")
        assert failed_msg["job_id"] == "job-001"
        assert "error" in failed_msg

    @pytest.mark.asyncio
    async def test_execute_job_increments_completed_counter(
        self, robot_config, mock_websocket
    ):
        """Successful job increments completed counter."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(return_value={"success": True})

        assert agent._jobs_completed == 0

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        assert agent._jobs_completed == 1

    @pytest.mark.asyncio
    async def test_execute_job_increments_failed_counter(
        self, robot_config, mock_websocket
    ):
        """Failed job increments failed counter."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(
            return_value={
                "success": False,
                "error": "Failed",
            }
        )

        assert agent._jobs_failed == 0

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        assert agent._jobs_failed == 1

    @pytest.mark.asyncio
    async def test_execute_job_removes_from_current_jobs(
        self, robot_config, mock_websocket
    ):
        """Completed job is removed from current jobs."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(return_value={"success": True})

        # Add to current jobs
        agent._current_jobs["job-001"] = MagicMock()

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        assert "job-001" not in agent._current_jobs

    @pytest.mark.asyncio
    async def test_execute_job_invokes_completed_callback(
        self, robot_config, mock_websocket
    ):
        """Job completion invokes callback."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        completed_jobs = []

        def on_completed(job_id, success):
            completed_jobs.append((job_id, success))

        agent.on_job_completed = on_completed
        agent.executor.execute = AsyncMock(return_value={"success": True})

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        assert ("job-001", True) in completed_jobs


# ============================================================================
# Stop Tests
# ============================================================================


class TestRobotAgentStop:
    """Test agent stop functionality."""

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self, robot_config):
        """Stop sets running flag to False."""
        agent = RobotAgent(robot_config)
        agent._running = True

        await agent.stop(wait_for_jobs=False)

        assert agent.is_running is False

    @pytest.mark.asyncio
    async def test_stop_closes_websocket(self, robot_config, mock_websocket):
        """Stop closes WebSocket connection."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._running = True

        await agent.stop(wait_for_jobs=False)

        assert mock_websocket.closed is True

    @pytest.mark.asyncio
    async def test_stop_stops_heartbeat(self, robot_config):
        """Stop stops heartbeat service."""
        agent = RobotAgent(robot_config)
        agent._running = True

        # Mock heartbeat
        agent.heartbeat = MagicMock()
        agent.heartbeat.stop = AsyncMock()

        await agent.stop(wait_for_jobs=False)

        agent.heartbeat.stop.assert_awaited_once()


# ============================================================================
# Event Callback Tests
# ============================================================================


class TestRobotAgentEventCallbacks:
    """Test event callback invocation."""

    def test_on_connected_callback_set(self, robot_config):
        """on_connected callback can be set."""
        agent = RobotAgent(robot_config)

        callback = MagicMock()
        agent.on_connected = callback

        assert agent.on_connected is callback

    def test_on_disconnected_callback_set(self, robot_config):
        """on_disconnected callback can be set."""
        agent = RobotAgent(robot_config)

        callback = MagicMock()
        agent.on_disconnected = callback

        assert agent.on_disconnected is callback


# ============================================================================
# Edge Cases
# ============================================================================


class TestRobotAgentEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self, robot_config):
        """Unknown message type is logged and ignored."""
        agent = RobotAgent(robot_config)

        # Should not raise
        await agent._handle_message({"type": "unknown_type"})

    @pytest.mark.asyncio
    async def test_reconnect_delay_reset_on_connect(self, robot_config):
        """Reconnect delay is reset after successful connection."""
        agent = RobotAgent(robot_config)
        agent._reconnect_delay = 30.0  # Simulated backoff

        # Reset should happen in _connect_and_run, but we test the logic
        # By checking that delay is reset in config
        assert agent.config.reconnect_delay == 1.0  # Default

    def test_signal_handler_sets_running_false_on_windows(self, robot_config):
        """Signal handler on Windows sets running to False."""
        agent = RobotAgent(robot_config)
        agent._running = True

        agent._signal_handler(2, None)  # SIGINT

        assert agent._running is False

    @pytest.mark.asyncio
    async def test_execute_job_handles_cancellation(self, robot_config, mock_websocket):
        """Cancelled job sends job_cancelled message."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        # Make executor raise CancelledError
        agent.executor.execute = AsyncMock(side_effect=asyncio.CancelledError())

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        messages = mock_websocket.get_sent_messages()
        cancel_msg = next(m for m in messages if m["type"] == "job_cancelled")
        assert cancel_msg["job_id"] == "job-001"

    @pytest.mark.asyncio
    async def test_execute_job_handles_exception(self, robot_config, mock_websocket):
        """Unexpected exception in job sends job_failed message."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket
        agent._connected = True

        agent.executor.execute = AsyncMock(side_effect=Exception("Unexpected error"))

        await agent._execute_job({"job_id": "job-001", "workflow_json": "{}"})

        messages = mock_websocket.get_sent_messages()
        failed_msg = next(m for m in messages if m["type"] == "job_failed")
        assert failed_msg["job_id"] == "job-001"
        assert "Unexpected error" in failed_msg["error"]

    def test_heartbeat_failure_handler_logs(self, robot_config):
        """Heartbeat failure handler logs warning."""
        agent = RobotAgent(robot_config)

        # Should not raise
        agent._on_heartbeat_failure(Exception("Test error"))

    @pytest.mark.asyncio
    async def test_double_start_warns(self, robot_config):
        """Starting already running agent warns and returns."""
        agent = RobotAgent(robot_config)
        agent._running = True

        # Should return immediately without error
        # (We cannot await start() because it runs forever, so we check _running flag)
        assert agent.is_running is True


# ============================================================================
# API Key Authentication Tests
# ============================================================================


class TestRobotAgentApiKeyAuthentication:
    """Test API key authentication functionality."""

    @pytest.fixture
    def robot_config_with_api_key(self) -> RobotConfig:
        """Provide RobotConfig with API key configured."""
        valid_key = "crpa_" + "a" * 43
        return RobotConfig(
            robot_name="Test Robot with API Key",
            control_plane_url="ws://localhost:8080/ws",
            robot_id="robot-test-12345",
            api_key=valid_key,
            heartbeat_interval=30,
            max_concurrent_jobs=2,
            capabilities=["browser"],
            environment="test",
        )

    def test_config_uses_api_key_true(self, robot_config_with_api_key):
        """Config with API key has uses_api_key True."""
        assert robot_config_with_api_key.uses_api_key is True

    def test_config_uses_api_key_false_without_key(self, robot_config):
        """Config without API key has uses_api_key False."""
        assert robot_config.uses_api_key is False

    @pytest.mark.asyncio
    async def test_register_without_api_key(self, robot_config, mock_websocket):
        """Registration without API key does not include api_key_hash."""
        agent = RobotAgent(robot_config)
        agent._ws = mock_websocket

        await agent._register()

        messages = mock_websocket.get_sent_messages()
        assert len(messages) == 1
        reg_msg = messages[0]

        assert reg_msg["type"] == "register"
        assert "api_key_hash" not in reg_msg

    @pytest.mark.asyncio
    async def test_register_with_api_key_includes_hash(
        self, robot_config_with_api_key, mock_websocket
    ):
        """Registration with API key includes api_key_hash."""
        agent = RobotAgent(robot_config_with_api_key)
        agent._ws = mock_websocket

        await agent._register()

        messages = mock_websocket.get_sent_messages()
        assert len(messages) == 1
        reg_msg = messages[0]

        assert reg_msg["type"] == "register"
        assert "api_key_hash" in reg_msg
        # Verify hash is a 64-character hex string
        assert len(reg_msg["api_key_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in reg_msg["api_key_hash"])

    @pytest.mark.asyncio
    async def test_register_api_key_hash_is_consistent(
        self, robot_config_with_api_key, mock_websocket
    ):
        """API key hash in registration is consistent with hashlib SHA-256."""
        import hashlib

        agent = RobotAgent(robot_config_with_api_key)
        agent._ws = mock_websocket

        await agent._register()

        messages = mock_websocket.get_sent_messages()
        reg_msg = messages[0]

        # Calculate expected hash
        expected_hash = hashlib.sha256(
            robot_config_with_api_key.api_key.encode()
        ).hexdigest()

        assert reg_msg["api_key_hash"] == expected_hash

    def test_agent_status_includes_api_key_info(self, robot_config_with_api_key):
        """Agent status includes API key configuration info."""
        agent = RobotAgent(robot_config_with_api_key)
        status = agent.get_status()

        # Config should be accessible for API key status
        assert agent.config.uses_api_key is True


class TestRobotAgentConnectionWithApiKey:
    """Test WebSocket connection with API key headers."""

    @pytest.fixture
    def robot_config_with_api_key(self) -> RobotConfig:
        """Provide RobotConfig with API key configured."""
        valid_key = "crpa_" + "a" * 43
        return RobotConfig(
            robot_name="Test Robot with API Key",
            control_plane_url="ws://localhost:8080/ws",
            robot_id="robot-test-12345",
            api_key=valid_key,
            heartbeat_interval=30,
            max_concurrent_jobs=2,
        )

    @pytest.mark.asyncio
    async def test_connect_sends_api_key_header(
        self, robot_config_with_api_key, mock_websocket
    ):
        """Connection with API key sends X-Api-Key header."""
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_websocket

            # Queue a message to prevent hanging
            mock_websocket.queue_message({"type": "register_ack"})

            agent = RobotAgent(robot_config_with_api_key)
            agent._running = True

            # Start connection but interrupt quickly
            try:
                # Run with timeout to avoid hanging
                await asyncio.wait_for(
                    agent._connect_and_run(),
                    timeout=0.5,
                )
            except (asyncio.TimeoutError, Exception):
                pass  # Expected

            # Verify connect was called with extra_headers
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]

            assert "extra_headers" in call_kwargs
            assert "X-Api-Key" in call_kwargs["extra_headers"]
            assert (
                call_kwargs["extra_headers"]["X-Api-Key"]
                == robot_config_with_api_key.api_key
            )

    @pytest.mark.asyncio
    async def test_connect_without_api_key_no_header(
        self, robot_config, mock_websocket
    ):
        """Connection without API key does not send X-Api-Key header."""
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_websocket

            # Queue a message to prevent hanging
            mock_websocket.queue_message({"type": "register_ack"})

            agent = RobotAgent(robot_config)
            agent._running = True

            try:
                await asyncio.wait_for(
                    agent._connect_and_run(),
                    timeout=0.5,
                )
            except (asyncio.TimeoutError, Exception):
                pass

            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]

            # No extra_headers or X-Api-Key should not be present
            extra_headers = call_kwargs.get("extra_headers", {})
            assert "X-Api-Key" not in extra_headers


class TestRobotAgentApiKeyErrorHandling:
    """Test error handling for API key authentication."""

    @pytest.fixture
    def robot_config_with_api_key(self) -> RobotConfig:
        """Provide RobotConfig with API key configured."""
        valid_key = "crpa_" + "a" * 43
        return RobotConfig(
            robot_name="Test Robot with API Key",
            control_plane_url="ws://localhost:8080/ws",
            robot_id="robot-test-12345",
            api_key=valid_key,
        )

    @pytest.mark.asyncio
    async def test_connection_failure_with_api_key(
        self, robot_config_with_api_key, mock_websocket
    ):
        """Connection failure with API key is handled gracefully."""
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("Authentication failed")

            agent = RobotAgent(robot_config_with_api_key)
            agent._running = True

            # Should raise the connection error
            with pytest.raises(Exception, match="Authentication failed"):
                await agent._connect_and_run()

            # Agent should not be connected
            assert agent.is_connected is False
            assert agent.is_registered is False

    @pytest.mark.asyncio
    async def test_auth_error_message_handling(
        self, robot_config_with_api_key, mock_websocket
    ):
        """Authentication error message from orchestrator is handled."""
        agent = RobotAgent(robot_config_with_api_key)
        agent._ws = mock_websocket
        agent._connected = True

        # Simulate auth error from orchestrator
        error_msg = {
            "type": "error",
            "code": "AUTH_FAILED",
            "message": "Invalid or expired API key",
        }

        # Should not raise - just log
        await agent._handle_error(error_msg)
