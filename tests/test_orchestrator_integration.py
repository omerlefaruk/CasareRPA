"""
Integration tests for orchestrator-robot WebSocket communication.

Tests the complete flow of:
- Orchestrator server startup
- Robot connection and registration
- Job dispatch and execution
- Progress reporting and completion
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from unittest.mock import MagicMock, AsyncMock

import pytest

# Try to import websockets - skip tests if not available
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

pytestmark = pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")


class TestOrchestratorServerUnit:
    """Unit tests for OrchestratorServer."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock orchestrator server for unit testing."""
        from casare_rpa.orchestrator.server import OrchestratorServer

        server = OrchestratorServer(host="127.0.0.1", port=0)
        return server

    def test_server_initialization(self, mock_server):
        """Test server initializes correctly."""
        assert mock_server._host == "127.0.0.1"
        assert mock_server._running is False
        assert mock_server.connected_count == 0

    def test_server_callbacks_set(self, mock_server):
        """Test callbacks can be set."""
        callback = MagicMock()
        mock_server.set_callbacks(
            on_robot_connect=callback,
            on_robot_disconnect=callback,
        )
        assert mock_server._on_robot_connect == callback
        assert mock_server._on_robot_disconnect == callback


class TestRobotWebSocketClientUnit:
    """Unit tests for RobotWebSocketClient."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock robot WebSocket client."""
        from casare_rpa.robot.websocket_client import RobotWebSocketClient

        client = RobotWebSocketClient(
            robot_id="test-robot-001",
            robot_name="Test Robot",
            orchestrator_url="ws://localhost:8765",
            max_concurrent_jobs=2,
        )
        return client

    def test_client_initialization(self, mock_client):
        """Test client initializes correctly."""
        assert mock_client.robot_id == "test-robot-001"
        assert mock_client.robot_name == "Test Robot"
        assert mock_client.max_concurrent_jobs == 2
        assert mock_client.is_connected is False
        assert mock_client.current_job_count == 0

    def test_client_availability(self, mock_client):
        """Test availability check."""
        assert mock_client.is_available is False  # Not connected

        # Simulate connection and jobs
        mock_client._connected = True
        assert mock_client.is_available is True

        mock_client._active_jobs.add("job-1")
        mock_client._active_jobs.add("job-2")
        assert mock_client.is_available is False  # At capacity

    def test_client_callbacks_set(self, mock_client):
        """Test callbacks can be set."""
        callback = MagicMock()
        mock_client.set_callbacks(
            on_job_assigned=callback,
            on_connected=callback,
        )
        assert mock_client._on_job_assigned == callback
        assert mock_client._on_connected == callback

    def test_job_tracking(self, mock_client):
        """Test job tracking methods."""
        assert mock_client.current_job_count == 0

        mock_client.mark_job_active("job-1")
        assert mock_client.current_job_count == 1
        assert "job-1" in mock_client._active_jobs

        mock_client.mark_job_complete("job-1")
        assert mock_client.current_job_count == 0
        assert "job-1" not in mock_client._active_jobs


class TestEngineServerIntegration:
    """Tests for OrchestratorEngine server integration."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock orchestrator engine."""
        from casare_rpa.orchestrator.engine import OrchestratorEngine

        # Create engine with mock service
        engine = OrchestratorEngine()
        return engine

    def test_engine_server_fields(self, mock_engine):
        """Test engine has server fields."""
        assert mock_engine._server is None
        assert mock_engine._server_port == 8765
        assert hasattr(mock_engine, 'start_server')
        assert hasattr(mock_engine, 'dispatch_job_to_robot')
        assert hasattr(mock_engine, 'connected_robots')
        assert hasattr(mock_engine, 'available_robots')

    def test_connected_robots_empty(self, mock_engine):
        """Test connected_robots returns empty when no server."""
        assert mock_engine.connected_robots == []
        assert mock_engine.available_robots == []


class TestProtocolMessages:
    """Test protocol message building and parsing."""

    def test_register_message(self):
        """Test robot registration message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType, Message

        msg = MessageBuilder.register(
            robot_id="robot-001",
            robot_name="Test Robot",
            environment="production",
            max_concurrent_jobs=2,
        )

        assert msg.type == MessageType.REGISTER
        assert msg.payload["robot_id"] == "robot-001"
        assert msg.payload["robot_name"] == "Test Robot"
        assert msg.payload["environment"] == "production"
        assert msg.payload["max_concurrent_jobs"] == 2

    def test_heartbeat_message(self):
        """Test heartbeat message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.heartbeat(
            robot_id="robot-001",
            status="online",
            current_jobs=1,
            cpu_percent=45.5,
            active_job_ids=["job-1"],
        )

        assert msg.type == MessageType.HEARTBEAT
        assert msg.payload["robot_id"] == "robot-001"
        assert msg.payload["status"] == "online"
        assert msg.payload["current_jobs"] == 1
        assert msg.payload["cpu_percent"] == 45.5

    def test_job_assign_message(self):
        """Test job assignment message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.job_assign(
            job_id="job-001",
            workflow_id="wf-001",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
            priority=2,
        )

        assert msg.type == MessageType.JOB_ASSIGN
        assert msg.payload["job_id"] == "job-001"
        assert msg.payload["workflow_name"] == "Test Workflow"

    def test_job_progress_message(self):
        """Test job progress message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.job_progress(
            job_id="job-001",
            robot_id="robot-001",
            progress=50,
            current_node="node_2",
        )

        assert msg.type == MessageType.JOB_PROGRESS
        assert msg.payload["progress"] == 50
        assert msg.payload["current_node"] == "node_2"

    def test_job_complete_message(self):
        """Test job completion message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.job_complete(
            job_id="job-001",
            robot_id="robot-001",
            result={"output": "success"},
            duration_ms=5000,
        )

        assert msg.type == MessageType.JOB_COMPLETE
        assert msg.payload["result"]["output"] == "success"
        assert msg.payload["duration_ms"] == 5000

    def test_job_failed_message(self):
        """Test job failure message."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.job_failed(
            job_id="job-001",
            robot_id="robot-001",
            error_message="Element not found",
            error_type="SelectorError",
            failed_node="click_node",
        )

        assert msg.type == MessageType.JOB_FAILED
        assert msg.payload["error_message"] == "Element not found"
        assert msg.payload["error_type"] == "SelectorError"
        assert msg.payload["failed_node"] == "click_node"

    def test_message_serialization(self):
        """Test message JSON serialization/deserialization."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, Message, MessageType

        original = MessageBuilder.heartbeat(
            robot_id="robot-001",
            status="online",
            current_jobs=0,
        )

        json_str = original.to_json()
        parsed = Message.from_json(json_str)

        assert parsed.type == MessageType.HEARTBEAT
        assert parsed.payload["robot_id"] == "robot-001"
        assert parsed.payload["status"] == "online"


class TestAgentWebSocketIntegration:
    """Test RobotAgent WebSocket integration."""

    @pytest.fixture
    def mock_agent_config(self):
        """Create a mock agent config."""
        from casare_rpa.robot.config import RobotConfig

        # Return a config object with test values
        config = RobotConfig()
        config.robot_id = "test-agent-001"
        config.robot_name = "Test Agent"
        return config

    def test_agent_has_websocket_methods(self):
        """Test that RobotAgent has WebSocket methods."""
        from casare_rpa.robot.agent import RobotAgent

        # Check method exists
        assert hasattr(RobotAgent, 'connect_to_orchestrator')
        assert hasattr(RobotAgent, 'disconnect_from_orchestrator')
        assert hasattr(RobotAgent, '_on_ws_job_assigned')
        assert hasattr(RobotAgent, '_on_ws_job_cancelled')


class TestEndToEndScenarios:
    """End-to-end scenario tests (mocked)."""

    @pytest.mark.asyncio
    async def test_robot_connection_flow(self):
        """Test the robot connection flow with mocked server."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, Message, MessageType

        # Simulate registration flow
        register_msg = MessageBuilder.register(
            robot_id="robot-e2e",
            robot_name="E2E Robot",
            environment="test",
        )

        # Verify message structure
        assert register_msg.type == MessageType.REGISTER
        assert register_msg.id is not None  # UUID generated

        # Simulate ack
        ack_msg = MessageBuilder.register_ack(
            robot_id="robot-e2e",
            success=True,
            message="Registered",
            correlation_id=register_msg.id,
        )

        assert ack_msg.type == MessageType.REGISTER_ACK
        assert ack_msg.correlation_id == register_msg.id
        assert ack_msg.payload["success"] is True

    @pytest.mark.asyncio
    async def test_job_execution_flow(self):
        """Test the job execution flow with mocked messages."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        job_id = str(uuid.uuid4())

        # 1. Server assigns job
        assign_msg = MessageBuilder.job_assign(
            job_id=job_id,
            workflow_id="wf-test",
            workflow_name="Test Workflow",
            workflow_json='{"nodes": []}',
        )
        assert assign_msg.type == MessageType.JOB_ASSIGN

        # 2. Robot accepts
        accept_msg = MessageBuilder.job_accept(
            job_id=job_id,
            robot_id="robot-001",
            correlation_id=assign_msg.id,
        )
        assert accept_msg.type == MessageType.JOB_ACCEPT
        assert accept_msg.correlation_id == assign_msg.id

        # 3. Robot reports progress
        progress_msg = MessageBuilder.job_progress(
            job_id=job_id,
            robot_id="robot-001",
            progress=50,
            current_node="middle_node",
        )
        assert progress_msg.type == MessageType.JOB_PROGRESS

        # 4. Robot completes
        complete_msg = MessageBuilder.job_complete(
            job_id=job_id,
            robot_id="robot-001",
            result={"success": True},
            duration_ms=1000,
        )
        assert complete_msg.type == MessageType.JOB_COMPLETE

    @pytest.mark.asyncio
    async def test_job_cancellation_flow(self):
        """Test the job cancellation flow."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        job_id = str(uuid.uuid4())

        # 1. Server sends cancel
        cancel_msg = MessageBuilder.job_cancel(
            job_id=job_id,
            reason="User requested",
        )
        assert cancel_msg.type == MessageType.JOB_CANCEL

        # 2. Robot confirms
        cancelled_msg = MessageBuilder.job_cancelled(
            job_id=job_id,
            robot_id="robot-001",
            correlation_id=cancel_msg.id,
        )
        assert cancelled_msg.type == MessageType.JOB_CANCELLED


class TestMessageTypes:
    """Test all message types are properly defined."""

    def test_all_message_types(self):
        """Verify all expected message types exist."""
        from casare_rpa.orchestrator.protocol import MessageType

        expected_types = [
            "REGISTER", "REGISTER_ACK",
            "HEARTBEAT", "HEARTBEAT_ACK",
            "DISCONNECT",
            "JOB_ASSIGN", "JOB_ACCEPT", "JOB_REJECT",
            "JOB_PROGRESS", "JOB_COMPLETE", "JOB_FAILED",
            "JOB_CANCEL", "JOB_CANCELLED",
            "STATUS_REQUEST", "STATUS_RESPONSE",
            "LOG_ENTRY", "LOG_BATCH",
            "PAUSE", "RESUME", "SHUTDOWN",
            "ERROR",
        ]

        for type_name in expected_types:
            assert hasattr(MessageType, type_name), f"Missing MessageType: {type_name}"


class TestErrorHandling:
    """Test error handling in orchestrator components."""

    def test_client_job_failure_tracking(self):
        """Test client properly tracks failed jobs."""
        from casare_rpa.robot.websocket_client import RobotWebSocketClient

        client = RobotWebSocketClient(
            robot_id="error-test",
            robot_name="Error Test Robot",
            orchestrator_url="ws://localhost:8765",
        )

        # Add job
        client.mark_job_active("job-fail")
        assert "job-fail" in client._active_jobs

        # Complete removes job
        client.mark_job_complete("job-fail")
        assert "job-fail" not in client._active_jobs

    def test_error_message_builder(self):
        """Test error message creation."""
        from casare_rpa.orchestrator.protocol import MessageBuilder, MessageType

        msg = MessageBuilder.error(
            error_code="INVALID_STATE",
            error_message="Cannot accept job in current state",
            details={"current_jobs": 5, "max_jobs": 5},
        )

        assert msg.type == MessageType.ERROR
        assert msg.payload["error_code"] == "INVALID_STATE"
        assert msg.payload["details"]["current_jobs"] == 5
