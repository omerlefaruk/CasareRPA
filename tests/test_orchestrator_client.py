"""Tests for orchestrator robot client."""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Check if websockets is available
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

from casare_rpa.orchestrator.protocol import Message, MessageType, MessageBuilder

# Skip all tests if websockets not installed
pytestmark = pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestRobotClientInitialization:
    """Tests for RobotClient initialization."""

    def test_client_initialization(self):
        """Test basic client initialization."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="robot-001",
            robot_name="Test Robot",
            orchestrator_url="ws://localhost:8765",
            environment="production",
            max_concurrent_jobs=3,
            tags=["web", "desktop"],
            auth_token="secret",
            heartbeat_interval=60,
            reconnect_interval=10,
            max_reconnect_attempts=5,
        )

        assert client.robot_id == "robot-001"
        assert client.robot_name == "Test Robot"
        assert client.orchestrator_url == "ws://localhost:8765"
        assert client.environment == "production"
        assert client.max_concurrent_jobs == 3
        assert client.tags == ["web", "desktop"]
        assert client.auth_token == "secret"
        assert client.heartbeat_interval == 60
        assert client.reconnect_interval == 10
        assert client.max_reconnect_attempts == 5

    def test_client_defaults(self):
        """Test client with default values."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
        )

        assert client.orchestrator_url == "ws://localhost:8765"
        assert client.environment == "default"
        assert client.max_concurrent_jobs == 1
        assert client.tags == []
        assert client.auth_token is None
        assert client.heartbeat_interval == 30
        assert client.reconnect_interval == 5
        assert client.max_reconnect_attempts == 0

    def test_client_set_callbacks(self):
        """Test setting callbacks."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        on_job = MagicMock()
        on_cancel = MagicMock()
        on_connected = MagicMock()
        on_disconnected = MagicMock()

        client.set_callbacks(
            on_job_received=on_job,
            on_job_cancel=on_cancel,
            on_connected=on_connected,
            on_disconnected=on_disconnected,
        )

        assert client._on_job_received == on_job
        assert client._on_job_cancel == on_cancel
        assert client._on_connected == on_connected
        assert client._on_disconnected == on_disconnected


class TestRobotClientProperties:
    """Tests for RobotClient properties."""

    def test_is_connected(self):
        """Test is_connected property."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        assert client.is_connected is False

        client._connected = True
        assert client.is_connected is True

    def test_is_paused(self):
        """Test is_paused property."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        assert client.is_paused is False

        client._paused = True
        assert client.is_paused is True

    def test_active_job_count(self):
        """Test active_job_count property."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        assert client.active_job_count == 0

        client._active_jobs["j1"] = {"job_id": "j1"}
        assert client.active_job_count == 1

        client._active_jobs["j2"] = {"job_id": "j2"}
        assert client.active_job_count == 2

    def test_is_available(self):
        """Test is_available property."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=2,
        )

        # Not connected
        assert client.is_available is False

        # Connected but not paused
        client._connected = True
        assert client.is_available is True

        # Paused
        client._paused = True
        assert client.is_available is False

        # Not paused but max jobs
        client._paused = False
        client._active_jobs["j1"] = {}
        client._active_jobs["j2"] = {}
        assert client.is_available is False

    def test_get_active_jobs(self):
        """Test get_active_jobs method."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        assert client.get_active_jobs() == []

        client._active_jobs["j1"] = {}
        client._active_jobs["j2"] = {}

        jobs = client.get_active_jobs()
        assert "j1" in jobs
        assert "j2" in jobs


class TestRobotClientCapabilities:
    """Tests for RobotClient capabilities."""

    def test_get_capabilities(self):
        """Test getting robot capabilities."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        caps = client._get_capabilities()

        assert "platform" in caps
        assert "python_version" in caps


class TestRobotClientMessageHandlers:
    """Tests for RobotClient message handlers."""

    @pytest.mark.asyncio
    async def test_handle_register_ack_success(self):
        """Test handling successful registration ack."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        msg = MessageBuilder.register_ack(
            robot_id="r1",
            success=True,
            message="OK",
            config={"heartbeat_interval": 45},
        )

        await client._handle_register_ack(msg)

        assert client.heartbeat_interval == 45

    @pytest.mark.asyncio
    async def test_handle_register_ack_failure(self, mock_websocket):
        """Test handling failed registration ack."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._running = True

        msg = MessageBuilder.register_ack(
            robot_id="r1",
            success=False,
            message="Authentication failed",
        )

        await client._handle_register_ack(msg)

        # Should trigger disconnect
        mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_handle_heartbeat_ack(self):
        """Test handling heartbeat ack."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        msg = MessageBuilder.heartbeat_ack(robot_id="r1")

        # Should not raise
        await client._handle_heartbeat_ack(msg)

    @pytest.mark.asyncio
    async def test_handle_job_assign_accept(self, mock_websocket):
        """Test handling job assignment - accept."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=2,
        )
        client._websocket = mock_websocket
        client._connected = True

        on_job = MagicMock()
        client.set_callbacks(on_job_received=on_job)

        msg = MessageBuilder.job_assign(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Workflow 1",
            workflow_json='{"nodes": []}',
            parameters={"input": "value"},
        )

        await client._handle_job_assign(msg)

        # Job should be added
        assert "j1" in client._active_jobs
        job_info = client._active_jobs["j1"]
        assert job_info["workflow_id"] == "wf1"
        assert job_info["parameters"] == {"input": "value"}

        # Accept message sent
        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_ACCEPT

        # Callback invoked
        on_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_job_assign_reject_paused(self, mock_websocket):
        """Test handling job assignment - reject when paused."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._paused = True

        msg = MessageBuilder.job_assign(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Workflow 1",
            workflow_json="{}",
        )

        await client._handle_job_assign(msg)

        # Job not added
        assert "j1" not in client._active_jobs

        # Reject message sent
        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_REJECT
        assert "paused" in sent_msg.payload["reason"]

    @pytest.mark.asyncio
    async def test_handle_job_assign_reject_max_jobs(self, mock_websocket):
        """Test handling job assignment - reject when at max jobs."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=1,
        )
        client._websocket = mock_websocket
        client._active_jobs["existing"] = {}

        msg = MessageBuilder.job_assign(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Workflow 1",
            workflow_json="{}",
        )

        await client._handle_job_assign(msg)

        # Job not added
        assert "j1" not in client._active_jobs

        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_REJECT

    @pytest.mark.asyncio
    async def test_handle_job_cancel(self, mock_websocket):
        """Test handling job cancellation."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._active_jobs["j1"] = {"job_id": "j1"}

        on_cancel = MagicMock()
        client.set_callbacks(on_job_cancel=on_cancel)

        msg = MessageBuilder.job_cancel(job_id="j1", reason="User cancelled")

        await client._handle_job_cancel(msg)

        # Job removed
        assert "j1" not in client._active_jobs

        # Callback invoked
        on_cancel.assert_called_once_with("j1")

        # Cancelled confirmation sent
        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_CANCELLED

    @pytest.mark.asyncio
    async def test_handle_status_request(self, mock_websocket):
        """Test handling status request."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._active_jobs["j1"] = {}
        client._active_jobs["j2"] = {}

        msg = MessageBuilder.status_request(robot_id="r1")

        await client._handle_status_request(msg)

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.STATUS_RESPONSE
        assert sent_msg.payload["current_jobs"] == 2
        assert "j1" in sent_msg.payload["active_job_ids"]
        assert "j2" in sent_msg.payload["active_job_ids"]

    @pytest.mark.asyncio
    async def test_handle_pause(self):
        """Test handling pause command."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        msg = MessageBuilder.pause(robot_id="r1")

        await client._handle_pause(msg)

        assert client._paused is True

    @pytest.mark.asyncio
    async def test_handle_resume(self):
        """Test handling resume command."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._paused = True

        msg = MessageBuilder.resume(robot_id="r1")

        await client._handle_resume(msg)

        assert client._paused is False

    @pytest.mark.asyncio
    async def test_handle_shutdown_graceful(self):
        """Test handling graceful shutdown command."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        msg = MessageBuilder.shutdown(robot_id="r1", graceful=True)

        await client._handle_shutdown(msg)

        assert client._paused is True

    @pytest.mark.asyncio
    async def test_handle_shutdown_immediate(self, mock_websocket):
        """Test handling immediate shutdown command."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._running = True

        msg = MessageBuilder.shutdown(robot_id="r1", graceful=False)

        await client._handle_shutdown(msg)

        # Should trigger disconnect
        mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_handle_error(self):
        """Test handling error message."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")

        msg = MessageBuilder.error(
            error_code="TEST_ERROR",
            error_message="Test error message",
        )

        # Should not raise
        await client._handle_error(msg)


class TestRobotClientReporting:
    """Tests for RobotClient job reporting."""

    @pytest.mark.asyncio
    async def test_report_progress(self, mock_websocket):
        """Test reporting job progress."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket

        await client.report_progress(
            job_id="j1",
            progress=50,
            current_node="node-3",
            message="Processing",
        )

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_PROGRESS
        assert sent_msg.payload["progress"] == 50
        assert sent_msg.payload["current_node"] == "node-3"
        assert sent_msg.payload["message"] == "Processing"

    @pytest.mark.asyncio
    async def test_report_job_complete(self, mock_websocket):
        """Test reporting job completion."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._active_jobs["j1"] = {
            "job_id": "j1",
            "started_at": datetime.utcnow() - timedelta(seconds=10),
        }

        await client.report_job_complete(
            job_id="j1",
            result={"output": "success"},
        )

        # Job removed
        assert "j1" not in client._active_jobs

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_COMPLETE
        assert sent_msg.payload["result"] == {"output": "success"}
        assert sent_msg.payload["duration_ms"] >= 10000

    @pytest.mark.asyncio
    async def test_report_job_failed(self, mock_websocket):
        """Test reporting job failure."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._active_jobs["j1"] = {}

        await client.report_job_failed(
            job_id="j1",
            error_message="Connection timeout",
            error_type="NetworkError",
            stack_trace="Traceback...",
            failed_node="node-5",
        )

        # Job removed
        assert "j1" not in client._active_jobs

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.JOB_FAILED
        assert sent_msg.payload["error_message"] == "Connection timeout"
        assert sent_msg.payload["error_type"] == "NetworkError"

    @pytest.mark.asyncio
    async def test_send_log(self, mock_websocket):
        """Test sending log entry."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket

        await client.send_log(
            job_id="j1",
            level="INFO",
            message="Starting execution",
            node_id="node-1",
            extra={"step": 1},
        )

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.LOG_ENTRY
        assert sent_msg.payload["level"] == "INFO"
        assert sent_msg.payload["message"] == "Starting execution"

    @pytest.mark.asyncio
    async def test_send_log_batch(self, mock_websocket):
        """Test sending batch logs."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket

        entries = [
            {"level": "INFO", "message": "Step 1"},
            {"level": "DEBUG", "message": "Step 2"},
        ]

        await client.send_log_batch(job_id="j1", entries=entries)

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.LOG_BATCH
        assert sent_msg.payload["entries"] == entries


class TestRobotClientHeartbeat:
    """Tests for RobotClient heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_send_heartbeat_online(self, mock_websocket):
        """Test sending heartbeat when online."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket

        await client._send_heartbeat()

        mock_websocket.send.assert_called()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.HEARTBEAT
        assert sent_msg.payload["status"] == "online"

    @pytest.mark.asyncio
    async def test_send_heartbeat_paused(self, mock_websocket):
        """Test sending heartbeat when paused."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._paused = True

        await client._send_heartbeat()

        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.payload["status"] == "paused"

    @pytest.mark.asyncio
    async def test_send_heartbeat_busy(self, mock_websocket):
        """Test sending heartbeat when busy."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=1,
        )
        client._websocket = mock_websocket
        client._active_jobs["j1"] = {}

        await client._send_heartbeat()

        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.payload["status"] == "busy"


class TestRobotClientConnection:
    """Tests for RobotClient connection handling."""

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_websocket):
        """Test disconnecting from server."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(robot_id="r1", robot_name="Robot 1")
        client._websocket = mock_websocket
        client._connected = True
        client._running = True

        on_disconnected = MagicMock()
        client.set_callbacks(on_disconnected=on_disconnected)

        await client.disconnect("Test disconnect")

        assert client._running is False
        assert client._connected is False
        assert client._websocket is None
        mock_websocket.send.assert_called()  # Disconnect message
        mock_websocket.close.assert_called()
        on_disconnected.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_max_attempts(self):
        """Test connection with max retry attempts."""
        from casare_rpa.orchestrator.client import RobotClient

        client = RobotClient(
            robot_id="r1",
            robot_name="Robot 1",
            max_reconnect_attempts=2,
            reconnect_interval=0.01,  # Fast for testing
        )

        with patch('websockets.connect', side_effect=ConnectionRefusedError):
            result = await client.connect()

        assert result is False
        assert client._reconnect_count >= 2
