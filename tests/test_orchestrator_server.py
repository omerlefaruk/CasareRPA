"""Tests for orchestrator WebSocket server."""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

# Check if websockets is available
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

from casare_rpa.orchestrator.protocol import Message, MessageType, MessageBuilder
from casare_rpa.orchestrator.models import Robot, RobotStatus, Job, JobStatus, JobPriority

# Skip all tests if websockets not installed
pytestmark = pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    ws.remote_address = ("127.0.0.1", 12345)
    return ws


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        id="job-001",
        workflow_id="wf-001",
        workflow_name="Test Workflow",
        workflow_json='{"nodes": []}',
        robot_id="r1",
        priority=JobPriority.NORMAL,
        status=JobStatus.PENDING,
    )


class TestRobotConnection:
    """Tests for RobotConnection class."""

    def test_robot_connection_creation(self, mock_websocket):
        """Test creating a robot connection."""
        from casare_rpa.orchestrator.server import RobotConnection

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="robot-001",
            robot_name="Test Robot",
            environment="production",
            max_concurrent_jobs=3,
            tags=["web", "desktop"]
        )

        assert conn.robot_id == "robot-001"
        assert conn.robot_name == "Test Robot"
        assert conn.environment == "production"
        assert conn.max_concurrent_jobs == 3
        assert conn.tags == ["web", "desktop"]
        assert conn.status == RobotStatus.ONLINE
        assert len(conn.current_jobs) == 0

    def test_robot_connection_is_available(self, mock_websocket):
        """Test availability check."""
        from casare_rpa.orchestrator.server import RobotConnection

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=2,
        )

        assert conn.is_available is True

        # Add a job
        conn.current_jobs.add("job-1")
        assert conn.is_available is True

        # Max out jobs
        conn.current_jobs.add("job-2")
        assert conn.is_available is False

        # Change status
        conn.current_jobs.clear()
        conn.status = RobotStatus.OFFLINE
        assert conn.is_available is False

    def test_robot_connection_to_robot(self, mock_websocket):
        """Test conversion to Robot model."""
        from casare_rpa.orchestrator.server import RobotConnection

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
            environment="dev",
            max_concurrent_jobs=2,
            tags=["tag1"],
        )
        conn.current_jobs.add("job-1")

        robot = conn.to_robot()

        assert isinstance(robot, Robot)
        assert robot.id == "r1"
        assert robot.name == "Robot 1"
        assert robot.environment == "dev"
        assert robot.current_jobs == 1
        assert robot.tags == ["tag1"]


class TestOrchestratorServer:
    """Tests for OrchestratorServer class."""

    def test_server_initialization(self):
        """Test server initialization."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer(
            host="127.0.0.1",
            port=9999,
            heartbeat_timeout=120,
            auth_token="secret-token"
        )

        assert server._host == "127.0.0.1"
        assert server._port == 9999
        assert server._heartbeat_timeout == 120
        assert server._auth_token == "secret-token"
        assert server._running is False
        assert len(server._connections) == 0

    def test_server_set_callbacks(self):
        """Test setting callbacks."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()

        on_connect = MagicMock()
        on_disconnect = MagicMock()
        on_progress = MagicMock()
        on_complete = MagicMock()
        on_failed = MagicMock()
        on_log = MagicMock()

        server.set_callbacks(
            on_robot_connect=on_connect,
            on_robot_disconnect=on_disconnect,
            on_job_progress=on_progress,
            on_job_complete=on_complete,
            on_job_failed=on_failed,
            on_log_entry=on_log,
        )

        assert server._on_robot_connect == on_connect
        assert server._on_robot_disconnect == on_disconnect
        assert server._on_job_progress == on_progress
        assert server._on_job_complete == on_complete
        assert server._on_job_failed == on_failed
        assert server._on_log_entry == on_log

    @pytest.mark.asyncio
    async def test_handle_register_success(self, mock_websocket):
        """Test handling successful registration."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()

        msg = MessageBuilder.register(
            robot_id="r1",
            robot_name="Robot 1",
            environment="dev",
            max_concurrent_jobs=2,
        )

        await server._handle_register(mock_websocket, msg)

        # Check registration
        assert "r1" in server._connections
        conn = server._connections["r1"]
        assert conn.robot_id == "r1"
        assert conn.robot_name == "Robot 1"

        # Check ACK sent
        mock_websocket.send.assert_called_once()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.type == MessageType.REGISTER_ACK
        assert sent_msg.payload["success"] is True

    @pytest.mark.asyncio
    async def test_handle_register_with_auth_failure(self, mock_websocket):
        """Test registration failure with wrong auth token."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer(auth_token="correct-token")

        msg = MessageBuilder.register(robot_id="r1", robot_name="Robot 1")
        msg.payload["auth_token"] = "wrong-token"

        await server._handle_register(mock_websocket, msg)

        # Check registration failed
        assert "r1" not in server._connections

        # Check failure ACK and close
        mock_websocket.send.assert_called_once()
        sent_json = mock_websocket.send.call_args[0][0]
        sent_msg = Message.from_json(sent_json)
        assert sent_msg.payload["success"] is False

        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_register_with_callback(self, mock_websocket):
        """Test registration triggers callback."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()
        on_connect = MagicMock()
        server.set_callbacks(on_robot_connect=on_connect)

        msg = MessageBuilder.register(robot_id="r1", robot_name="Robot 1")
        await server._handle_register(mock_websocket, msg)

        on_connect.assert_called_once()
        robot_arg = on_connect.call_args[0][0]
        assert isinstance(robot_arg, Robot)
        assert robot_arg.id == "r1"

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, mock_websocket):
        """Test handling heartbeat message."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        # Pre-register robot
        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
        )
        server._connections["r1"] = conn
        old_heartbeat = conn.last_heartbeat

        # Small delay to ensure time difference
        await asyncio.sleep(0.01)

        msg = MessageBuilder.heartbeat(
            robot_id="r1",
            status="busy",
            current_jobs=2,
            cpu_percent=75.5,
            memory_percent=60.0,
            disk_percent=50.0,
            active_job_ids=["j1", "j2"]
        )

        await server._handle_heartbeat(mock_websocket, msg)

        # Check connection updated
        assert conn.last_heartbeat > old_heartbeat
        assert conn.status == RobotStatus.BUSY
        assert conn.cpu_percent == 75.5
        assert conn.memory_percent == 60.0
        assert conn.current_jobs == {"j1", "j2"}

        # Check ACK sent
        mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_job_accept(self, mock_websocket):
        """Test handling job acceptance."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(websocket=mock_websocket, robot_id="r1", robot_name="Robot 1")
        server._connections["r1"] = conn

        # Create pending response
        future = asyncio.get_event_loop().create_future()
        server._pending_responses["corr-123"] = future

        msg = MessageBuilder.job_accept(job_id="j1", robot_id="r1", correlation_id="corr-123")
        await server._handle_job_accept(mock_websocket, msg)

        # Check job added to connection
        assert "j1" in conn.current_jobs

        # Check future resolved
        assert future.done()
        result = future.result()
        assert result["accepted"] is True

    @pytest.mark.asyncio
    async def test_handle_job_reject(self, mock_websocket):
        """Test handling job rejection."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(websocket=mock_websocket, robot_id="r1", robot_name="Robot 1")
        server._connections["r1"] = conn

        future = asyncio.get_event_loop().create_future()
        server._pending_responses["corr-456"] = future

        msg = MessageBuilder.job_reject(
            job_id="j1",
            robot_id="r1",
            reason="Robot is busy",
            correlation_id="corr-456"
        )
        await server._handle_job_reject(mock_websocket, msg)

        assert future.done()
        result = future.result()
        assert result["accepted"] is False
        assert result["reason"] == "Robot is busy"

    @pytest.mark.asyncio
    async def test_handle_job_progress(self, mock_websocket):
        """Test handling job progress update."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()
        on_progress = MagicMock()
        server.set_callbacks(on_job_progress=on_progress)

        msg = MessageBuilder.job_progress(
            job_id="j1",
            robot_id="r1",
            progress=50,
            current_node="node-3",
        )

        await server._handle_job_progress(mock_websocket, msg)

        on_progress.assert_called_once_with("j1", 50, "node-3")

    @pytest.mark.asyncio
    async def test_handle_job_complete(self, mock_websocket):
        """Test handling job completion."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()
        on_complete = MagicMock()
        server.set_callbacks(on_job_complete=on_complete)

        conn = RobotConnection(websocket=mock_websocket, robot_id="r1", robot_name="Robot 1")
        conn.current_jobs.add("j1")
        server._connections["r1"] = conn

        msg = MessageBuilder.job_complete(
            job_id="j1",
            robot_id="r1",
            result={"output": "data"},
            duration_ms=5000,
        )

        await server._handle_job_complete(mock_websocket, msg)

        # Job removed from connection
        assert "j1" not in conn.current_jobs

        # Callback invoked
        on_complete.assert_called_once_with("j1", {"output": "data"})

    @pytest.mark.asyncio
    async def test_handle_job_failed(self, mock_websocket):
        """Test handling job failure."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()
        on_failed = MagicMock()
        server.set_callbacks(on_job_failed=on_failed)

        conn = RobotConnection(websocket=mock_websocket, robot_id="r1", robot_name="Robot 1")
        conn.current_jobs.add("j1")
        server._connections["r1"] = conn

        msg = MessageBuilder.job_failed(
            job_id="j1",
            robot_id="r1",
            error_message="Timeout",
        )

        await server._handle_job_failed(mock_websocket, msg)

        assert "j1" not in conn.current_jobs
        on_failed.assert_called_once_with("j1", "Timeout")

    @pytest.mark.asyncio
    async def test_handle_log_entry(self, mock_websocket):
        """Test handling log entry."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()
        on_log = MagicMock()
        server.set_callbacks(on_log_entry=on_log)

        msg = MessageBuilder.log_entry(
            job_id="j1",
            robot_id="r1",
            level="INFO",
            message="Starting execution",
            node_id="node-1",
        )

        await server._handle_log_entry(mock_websocket, msg)

        on_log.assert_called_once_with("j1", "INFO", "Starting execution", "node-1")

    @pytest.mark.asyncio
    async def test_send_job_success(self, mock_websocket, sample_job):
        """Test sending job to robot successfully."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=2,
        )
        server._connections["r1"] = conn

        # Mock send to capture message and resolve response
        async def mock_send(msg):
            sent_msg = Message.from_json(msg)
            # Simulate robot accepting job
            for corr_id, future in list(server._pending_responses.items()):
                if not future.done():
                    future.set_result({"accepted": True, "job_id": sent_msg.payload["job_id"]})
                    break

        mock_websocket.send = mock_send

        result = await server.send_job("r1", sample_job, timeout=5.0)

        assert result["accepted"] is True

    @pytest.mark.asyncio
    async def test_send_job_robot_not_connected(self, sample_job):
        """Test sending job to disconnected robot."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer()

        result = await server.send_job("unknown-robot", sample_job)

        assert result["accepted"] is False
        assert "not connected" in result["reason"]

    @pytest.mark.asyncio
    async def test_send_job_robot_not_available(self, mock_websocket, sample_job):
        """Test sending job to unavailable robot."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=1,
        )
        conn.current_jobs.add("existing-job")
        server._connections["r1"] = conn

        result = await server.send_job("r1", sample_job)

        assert result["accepted"] is False
        assert "not available" in result["reason"]

    @pytest.mark.asyncio
    async def test_cancel_job(self, mock_websocket):
        """Test cancelling a job."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(websocket=mock_websocket, robot_id="r1", robot_name="Robot 1")
        conn.current_jobs.add("j1")
        server._connections["r1"] = conn

        # Mock to simulate robot responding
        async def mock_send(msg):
            sent_msg = Message.from_json(msg)
            for corr_id, future in list(server._pending_responses.items()):
                if not future.done():
                    future.set_result({"cancelled": True, "job_id": "j1"})
                    break

        mock_websocket.send = mock_send

        result = await server.cancel_job("r1", "j1", "Testing", timeout=5.0)

        assert result is True

    def test_get_connected_robots(self, mock_websocket):
        """Test getting list of connected robots."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        # Add some connections
        for i in range(3):
            conn = RobotConnection(
                websocket=mock_websocket,
                robot_id=f"r{i}",
                robot_name=f"Robot {i}",
            )
            server._connections[f"r{i}"] = conn

        robots = server.get_connected_robots()

        assert len(robots) == 3
        assert all(isinstance(r, Robot) for r in robots)

    def test_get_available_robots(self, mock_websocket):
        """Test getting list of available robots."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        # Add available robot
        conn1 = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
            max_concurrent_jobs=2,
        )
        server._connections["r1"] = conn1

        # Add busy robot
        conn2 = RobotConnection(
            websocket=mock_websocket,
            robot_id="r2",
            robot_name="Robot 2",
            max_concurrent_jobs=1,
        )
        conn2.current_jobs.add("j1")
        server._connections["r2"] = conn2

        # Add offline robot
        conn3 = RobotConnection(
            websocket=mock_websocket,
            robot_id="r3",
            robot_name="Robot 3",
        )
        conn3.status = RobotStatus.OFFLINE
        server._connections["r3"] = conn3

        available = server.get_available_robots()

        assert len(available) == 1
        assert available[0].id == "r1"

    def test_get_robot(self, mock_websocket):
        """Test getting specific robot."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
        )
        server._connections["r1"] = conn

        robot = server.get_robot("r1")
        assert robot is not None
        assert robot.id == "r1"

        none_robot = server.get_robot("unknown")
        assert none_robot is None

    def test_is_robot_connected(self, mock_websocket):
        """Test checking robot connection status."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
        )
        server._connections["r1"] = conn

        assert server.is_robot_connected("r1") is True
        assert server.is_robot_connected("r2") is False

    def test_connected_count(self, mock_websocket):
        """Test connected count property."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        assert server.connected_count == 0

        for i in range(5):
            server._connections[f"r{i}"] = RobotConnection(
                websocket=mock_websocket,
                robot_id=f"r{i}",
                robot_name=f"Robot {i}",
            )

        assert server.connected_count == 5

    def test_available_count(self, mock_websocket):
        """Test available count property."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        # 3 available
        for i in range(3):
            server._connections[f"r{i}"] = RobotConnection(
                websocket=mock_websocket,
                robot_id=f"r{i}",
                robot_name=f"Robot {i}",
                max_concurrent_jobs=2,
            )

        # 2 busy
        for i in range(3, 5):
            conn = RobotConnection(
                websocket=mock_websocket,
                robot_id=f"r{i}",
                robot_name=f"Robot {i}",
                max_concurrent_jobs=1,
            )
            conn.current_jobs.add("j1")
            server._connections[f"r{i}"] = conn

        assert server.connected_count == 5
        assert server.available_count == 3

    @pytest.mark.asyncio
    async def test_broadcast(self, mock_websocket):
        """Test broadcasting message to all robots."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        # Create multiple mock websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        server._connections["r1"] = RobotConnection(
            websocket=ws1,
            robot_id="r1",
            robot_name="Robot 1",
            environment="prod",
        )
        server._connections["r2"] = RobotConnection(
            websocket=ws2,
            robot_id="r2",
            robot_name="Robot 2",
            environment="prod",
        )
        server._connections["r3"] = RobotConnection(
            websocket=ws3,
            robot_id="r3",
            robot_name="Robot 3",
            environment="dev",
        )

        # Broadcast to all
        msg = MessageBuilder.pause(robot_id="all")
        await server.broadcast(msg)

        ws1.send.assert_called_once()
        ws2.send.assert_called_once()
        ws3.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_filtered_by_environment(self, mock_websocket):
        """Test broadcasting to specific environment."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer()

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        server._connections["r1"] = RobotConnection(
            websocket=ws1,
            robot_id="r1",
            robot_name="Robot 1",
            environment="prod",
        )
        server._connections["r2"] = RobotConnection(
            websocket=ws2,
            robot_id="r2",
            robot_name="Robot 2",
            environment="dev",
        )

        msg = MessageBuilder.pause(robot_id="all")
        await server.broadcast(msg, environment="prod")

        ws1.send.assert_called_once()
        ws2.send.assert_not_called()


class TestServerHealthCheck:
    """Tests for server health check functionality."""

    @pytest.mark.asyncio
    async def test_check_robot_health_marks_stale_offline(self, mock_websocket):
        """Test that stale robots are marked offline."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer(heartbeat_timeout=30)

        # Create connection with old heartbeat
        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
        )
        conn.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        server._connections["r1"] = conn

        await server._check_robot_health()

        # Robot should be removed
        assert "r1" not in server._connections

    @pytest.mark.asyncio
    async def test_check_robot_health_keeps_active(self, mock_websocket):
        """Test that active robots are kept."""
        from casare_rpa.orchestrator.server import OrchestratorServer, RobotConnection

        server = OrchestratorServer(heartbeat_timeout=60)

        conn = RobotConnection(
            websocket=mock_websocket,
            robot_id="r1",
            robot_name="Robot 1",
        )
        # Fresh heartbeat
        conn.last_heartbeat = datetime.utcnow()
        server._connections["r1"] = conn

        await server._check_robot_health()

        assert "r1" in server._connections
        assert conn.status == RobotStatus.ONLINE
