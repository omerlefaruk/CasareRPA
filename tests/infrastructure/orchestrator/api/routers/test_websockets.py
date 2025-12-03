"""
Tests for WebSocket endpoints for real-time monitoring.

Tests cover:
- WebSocket connection lifecycle (connect, disconnect)
- Authentication verification (JWT, robot token, dev mode)
- Live jobs endpoint (connection, ping/pong, broadcast)
- Robot status endpoint (connection, updates)
- Queue metrics endpoint (connection, initial metrics)
- Connection manager (broadcast, disconnect handling, timeout)
- Event handlers (job status, robot heartbeat, queue depth)
- Error handling scenarios
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
    ConnectionManager,
    verify_websocket_token,
    websocket_live_jobs,
    websocket_robot_status,
    websocket_queue_metrics,
    broadcast_job_update,
    broadcast_robot_status,
    broadcast_queue_metrics,
    on_job_status_changed,
    on_robot_heartbeat,
    on_queue_depth_changed,
    live_jobs_manager,
    robot_status_manager,
    queue_metrics_manager,
    router,
    WS_SEND_TIMEOUT,
)
from casare_rpa.infrastructure.events import MonitoringEvent


# ============================================================================
# Test Data
# ============================================================================

TEST_JOB_ID = "job-test-001"
TEST_ROBOT_ID = "robot-test-001"
TEST_USER_ID = "user-test-001"


# ============================================================================
# Mock WebSocket
# ============================================================================


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code: Optional[int] = None
        self.close_reason: Optional[str] = None
        self.sent_messages: List[str] = []
        self.received_messages: List[str] = []
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._disconnect_on_receive = False

    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True

    async def close(self, code: int = 1000, reason: str = ""):
        """Close the WebSocket connection."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def send_text(self, data: str):
        """Send text message."""
        self.sent_messages.append(data)

    async def receive_text(self) -> str:
        """Receive text message from queue."""
        if self._disconnect_on_receive:
            raise WebSocketDisconnect(code=1000)
        return await self._receive_queue.get()

    def queue_message(self, message: str):
        """Queue a message to be received."""
        self._receive_queue.put_nowait(message)

    def set_disconnect_on_receive(self):
        """Configure to raise WebSocketDisconnect on next receive."""
        self._disconnect_on_receive = True

    def get_sent_json(self) -> List[Dict[str, Any]]:
        """Parse all sent messages as JSON."""
        import orjson

        return [orjson.loads(msg) for msg in self.sent_messages]


class SlowMockWebSocket(MockWebSocket):
    """Mock WebSocket that takes time to send (for timeout testing)."""

    def __init__(self, send_delay: float = 2.0):
        super().__init__()
        self._send_delay = send_delay

    async def send_text(self, data: str):
        """Slow send that may timeout."""
        await asyncio.sleep(self._send_delay)
        self.sent_messages.append(data)


class FailingMockWebSocket(MockWebSocket):
    """Mock WebSocket that fails on send."""

    async def send_text(self, data: str):
        """Raise exception on send."""
        raise Exception("WebSocket send failed")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    return MockWebSocket()


@pytest.fixture
def slow_websocket():
    """Create slow mock WebSocket for timeout tests."""
    return SlowMockWebSocket(send_delay=WS_SEND_TIMEOUT + 0.5)


@pytest.fixture
def failing_websocket():
    """Create failing mock WebSocket."""
    return FailingMockWebSocket()


@pytest.fixture
def connection_manager():
    """Create fresh ConnectionManager for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_metrics_collector():
    """Create mock metrics collector."""
    collector = MagicMock()
    collector.get_queue_depth.return_value = 42
    return collector


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client with WebSocket support."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ============================================================================
# ConnectionManager Tests
# ============================================================================


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(
        self, connection_manager: ConnectionManager, mock_websocket: MockWebSocket
    ) -> None:
        """Test connect accepts and tracks WebSocket."""
        await connection_manager.connect(mock_websocket)

        assert mock_websocket.accepted
        assert mock_websocket in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_connect_tracks_multiple_connections(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test manager tracks multiple connections."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)
        await connection_manager.connect(ws3)

        assert len(connection_manager.active_connections) == 3

    def test_disconnect_removes_websocket(
        self, connection_manager: ConnectionManager, mock_websocket: MockWebSocket
    ) -> None:
        """Test disconnect removes WebSocket from tracking."""
        connection_manager.active_connections.add(mock_websocket)

        connection_manager.disconnect(mock_websocket)

        assert mock_websocket not in connection_manager.active_connections

    def test_disconnect_handles_nonexistent_websocket(
        self, connection_manager: ConnectionManager, mock_websocket: MockWebSocket
    ) -> None:
        """Test disconnect gracefully handles non-tracked WebSocket."""
        # Should not raise
        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcast sends to all connected clients."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_handles_timeout(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcast handles slow clients with timeout."""
        normal_ws = MockWebSocket()
        slow_ws = SlowMockWebSocket(send_delay=WS_SEND_TIMEOUT + 1.0)

        await connection_manager.connect(normal_ws)
        await connection_manager.connect(slow_ws)

        message = {"type": "test"}

        # Set a shorter timeout for test speed
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.WS_SEND_TIMEOUT",
            0.1,
        ):
            await connection_manager.broadcast(message)

        # Normal ws should receive
        assert len(normal_ws.sent_messages) == 1
        # Slow ws should be disconnected
        assert slow_ws not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failure(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcast handles send failures gracefully."""
        normal_ws = MockWebSocket()
        failing_ws = FailingMockWebSocket()

        await connection_manager.connect(normal_ws)
        await connection_manager.connect(failing_ws)

        message = {"type": "test"}
        await connection_manager.broadcast(message)

        # Normal ws should receive
        assert len(normal_ws.sent_messages) == 1
        # Failing ws should be disconnected
        assert failing_ws not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcast with no connections does nothing."""
        message = {"type": "test"}
        # Should not raise
        await connection_manager.broadcast(message)


# ============================================================================
# verify_websocket_token Tests
# ============================================================================


class TestVerifyWebsocketToken:
    """Tests for verify_websocket_token function."""

    @pytest.mark.asyncio
    async def test_dev_mode_allows_no_token(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test dev mode allows unauthenticated connections."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            True,
        ):
            result = await verify_websocket_token(mock_websocket, token=None)

        assert result == "dev_user"
        assert not mock_websocket.closed

    @pytest.mark.asyncio
    async def test_no_token_rejects_in_production(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test missing token rejects connection in production."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            False,
        ):
            result = await verify_websocket_token(mock_websocket, token=None)

        assert result is None
        assert mock_websocket.closed
        assert mock_websocket.close_code == 4001

    @pytest.mark.asyncio
    async def test_valid_jwt_token(self, mock_websocket: MockWebSocket) -> None:
        """Test valid JWT token authenticates user."""
        mock_payload = MagicMock()
        mock_payload.type = "access"
        mock_payload.sub = TEST_USER_ID

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.decode_token",
            return_value=mock_payload,
        ):
            result = await verify_websocket_token(
                mock_websocket, token="valid.jwt.token"
            )

        assert result == TEST_USER_ID
        assert not mock_websocket.closed

    @pytest.mark.asyncio
    async def test_invalid_jwt_falls_back_to_robot_token(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test invalid JWT falls back to robot token validation."""
        mock_authenticator = MagicMock()
        mock_authenticator.is_enabled = True
        mock_authenticator.verify_token_async = AsyncMock(return_value=TEST_ROBOT_ID)

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.decode_token",
            side_effect=Exception("Invalid JWT"),
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.websockets.get_robot_authenticator",
                return_value=mock_authenticator,
            ):
                result = await verify_websocket_token(
                    mock_websocket, token="robot_api_key"
                )

        assert result == TEST_ROBOT_ID
        assert not mock_websocket.closed

    @pytest.mark.asyncio
    async def test_invalid_both_tokens_rejects(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test invalid JWT and robot token rejects connection."""
        mock_authenticator = MagicMock()
        mock_authenticator.is_enabled = True
        mock_authenticator.verify_token_async = AsyncMock(return_value=None)

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            False,
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.websockets.decode_token",
                side_effect=Exception("Invalid JWT"),
            ):
                with patch(
                    "casare_rpa.infrastructure.orchestrator.api.routers.websockets.get_robot_authenticator",
                    return_value=mock_authenticator,
                ):
                    result = await verify_websocket_token(
                        mock_websocket, token="invalid_token"
                    )

        assert result is None
        assert mock_websocket.closed
        assert mock_websocket.close_code == 4001


# ============================================================================
# Live Jobs WebSocket Endpoint Tests
# ============================================================================


class TestWebsocketLiveJobs:
    """Tests for /live-jobs WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_connection_rejected_without_auth(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test connection rejected without authentication."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await websocket_live_jobs(mock_websocket, token=None)

        # Should not be added to manager
        assert mock_websocket not in live_jobs_manager.active_connections

    @pytest.mark.asyncio
    async def test_ping_pong_handling(self, mock_websocket: MockWebSocket) -> None:
        """Test ping/pong keep-alive mechanism."""
        mock_websocket.queue_message("ping")
        mock_websocket.set_disconnect_on_receive()  # Disconnect after first message

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=TEST_USER_ID,
        ):
            await websocket_live_jobs(mock_websocket, token="valid_token")

        # Check pong was sent
        assert "pong" in mock_websocket.sent_messages

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_manager(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test WebSocketDisconnect removes client from manager."""
        mock_websocket.set_disconnect_on_receive()

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=TEST_USER_ID,
        ):
            # Ensure clean state
            live_jobs_manager.active_connections.discard(mock_websocket)

            await websocket_live_jobs(mock_websocket, token="valid_token")

        # Should be removed after disconnect
        assert mock_websocket not in live_jobs_manager.active_connections


# ============================================================================
# Robot Status WebSocket Endpoint Tests
# ============================================================================


class TestWebsocketRobotStatus:
    """Tests for /robot-status WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_connection_rejected_without_auth(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test connection rejected without authentication."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await websocket_robot_status(mock_websocket, token=None)

        assert mock_websocket not in robot_status_manager.active_connections

    @pytest.mark.asyncio
    async def test_ping_pong_handling(self, mock_websocket: MockWebSocket) -> None:
        """Test ping/pong keep-alive mechanism."""
        mock_websocket.queue_message("ping")
        mock_websocket.set_disconnect_on_receive()

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=TEST_USER_ID,
        ):
            await websocket_robot_status(mock_websocket, token="valid_token")

        assert "pong" in mock_websocket.sent_messages


# ============================================================================
# Queue Metrics WebSocket Endpoint Tests
# ============================================================================


class TestWebsocketQueueMetrics:
    """Tests for /queue-metrics WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_connection_rejected_without_auth(
        self, mock_websocket: MockWebSocket
    ) -> None:
        """Test connection rejected without authentication."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await websocket_queue_metrics(mock_websocket, token=None)

        assert mock_websocket not in queue_metrics_manager.active_connections

    @pytest.mark.asyncio
    async def test_sends_initial_queue_depth(
        self, mock_websocket: MockWebSocket, mock_metrics_collector
    ) -> None:
        """Test initial queue depth is sent on connection."""
        mock_websocket.set_disconnect_on_receive()

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=TEST_USER_ID,
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.websockets.get_metrics_collector",
                return_value=mock_metrics_collector,
            ):
                await websocket_queue_metrics(mock_websocket, token="valid_token")

        # Check initial message was sent
        assert len(mock_websocket.sent_messages) >= 1
        sent_json = mock_websocket.get_sent_json()
        assert sent_json[0]["depth"] == 42

    @pytest.mark.asyncio
    async def test_ping_pong_handling(
        self, mock_websocket: MockWebSocket, mock_metrics_collector
    ) -> None:
        """Test ping/pong keep-alive mechanism."""
        # Queue ping, then disconnect
        mock_websocket.queue_message("ping")
        mock_websocket.set_disconnect_on_receive()

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.verify_websocket_token",
            new_callable=AsyncMock,
            return_value=TEST_USER_ID,
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.websockets.get_metrics_collector",
                return_value=mock_metrics_collector,
            ):
                await websocket_queue_metrics(mock_websocket, token="valid_token")

        # After initial message, pong should be in response
        assert "pong" in mock_websocket.sent_messages


# ============================================================================
# Broadcast Helper Function Tests
# ============================================================================


class TestBroadcastJobUpdate:
    """Tests for broadcast_job_update function."""

    @pytest.mark.asyncio
    async def test_broadcasts_job_update(self) -> None:
        """Test job update is broadcast to all connected clients."""
        mock_ws = MockWebSocket()
        await live_jobs_manager.connect(mock_ws)

        try:
            await broadcast_job_update(TEST_JOB_ID, "completed")

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["job_id"] == TEST_JOB_ID
            assert sent_json[0]["status"] == "completed"
            assert "timestamp" in sent_json[0]
        finally:
            live_jobs_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_handles_no_connections(self) -> None:
        """Test broadcast with no connections does not raise."""
        # Ensure no connections
        live_jobs_manager.active_connections.clear()

        # Should not raise
        await broadcast_job_update(TEST_JOB_ID, "completed")


class TestBroadcastRobotStatus:
    """Tests for broadcast_robot_status function."""

    @pytest.mark.asyncio
    async def test_broadcasts_robot_status(self) -> None:
        """Test robot status is broadcast to all connected clients."""
        mock_ws = MockWebSocket()
        await robot_status_manager.connect(mock_ws)

        try:
            await broadcast_robot_status(
                robot_id=TEST_ROBOT_ID,
                status="busy",
                cpu_percent=45.5,
                memory_mb=2048.0,
            )

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["robot_id"] == TEST_ROBOT_ID
            assert sent_json[0]["status"] == "busy"
            assert sent_json[0]["cpu_percent"] == 45.5
            assert sent_json[0]["memory_mb"] == 2048.0
        finally:
            robot_status_manager.disconnect(mock_ws)


class TestBroadcastQueueMetrics:
    """Tests for broadcast_queue_metrics function."""

    @pytest.mark.asyncio
    async def test_broadcasts_queue_metrics(self) -> None:
        """Test queue metrics are broadcast to all connected clients."""
        mock_ws = MockWebSocket()
        await queue_metrics_manager.connect(mock_ws)

        try:
            await broadcast_queue_metrics(depth=100)

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["depth"] == 100
            assert "timestamp" in sent_json[0]
        finally:
            queue_metrics_manager.disconnect(mock_ws)


# ============================================================================
# Event Handler Tests
# ============================================================================


class TestOnJobStatusChanged:
    """Tests for on_job_status_changed event handler."""

    @pytest.mark.asyncio
    async def test_handles_job_status_event(self) -> None:
        """Test handler broadcasts job status change."""
        mock_ws = MockWebSocket()
        await live_jobs_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="JOB_STATUS_CHANGED",
                payload={"job_id": TEST_JOB_ID, "status": "completed"},
            )

            await on_job_status_changed(event)

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["job_id"] == TEST_JOB_ID
            assert sent_json[0]["status"] == "completed"
        finally:
            live_jobs_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_ignores_incomplete_payload(self) -> None:
        """Test handler ignores events without job_id or status."""
        mock_ws = MockWebSocket()
        await live_jobs_manager.connect(mock_ws)

        try:
            # Missing job_id
            event1 = MonitoringEvent(
                event_type="JOB_STATUS_CHANGED",
                payload={"status": "completed"},
            )
            await on_job_status_changed(event1)

            # Missing status
            event2 = MonitoringEvent(
                event_type="JOB_STATUS_CHANGED",
                payload={"job_id": TEST_JOB_ID},
            )
            await on_job_status_changed(event2)

            # Neither should broadcast
            assert len(mock_ws.sent_messages) == 0
        finally:
            live_jobs_manager.disconnect(mock_ws)


class TestOnRobotHeartbeat:
    """Tests for on_robot_heartbeat event handler."""

    @pytest.mark.asyncio
    async def test_handles_robot_heartbeat_event(self) -> None:
        """Test handler broadcasts robot heartbeat."""
        mock_ws = MockWebSocket()
        await robot_status_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="ROBOT_HEARTBEAT",
                payload={
                    "robot_id": TEST_ROBOT_ID,
                    "status": "busy",
                    "cpu_percent": 55.0,
                    "memory_mb": 1024.0,
                },
            )

            await on_robot_heartbeat(event)

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["robot_id"] == TEST_ROBOT_ID
            assert sent_json[0]["status"] == "busy"
        finally:
            robot_status_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_uses_defaults_for_missing_fields(self) -> None:
        """Test handler uses defaults for missing metrics."""
        mock_ws = MockWebSocket()
        await robot_status_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="ROBOT_HEARTBEAT",
                payload={"robot_id": TEST_ROBOT_ID},  # Minimal payload
            )

            await on_robot_heartbeat(event)

            sent_json = mock_ws.get_sent_json()
            assert sent_json[0]["status"] == "idle"  # Default
            assert sent_json[0]["cpu_percent"] == 0.0  # Default
            assert sent_json[0]["memory_mb"] == 0.0  # Default
        finally:
            robot_status_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_ignores_event_without_robot_id(self) -> None:
        """Test handler ignores events without robot_id."""
        mock_ws = MockWebSocket()
        await robot_status_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="ROBOT_HEARTBEAT",
                payload={"status": "busy"},  # No robot_id
            )

            await on_robot_heartbeat(event)

            assert len(mock_ws.sent_messages) == 0
        finally:
            robot_status_manager.disconnect(mock_ws)


class TestOnQueueDepthChanged:
    """Tests for on_queue_depth_changed event handler."""

    @pytest.mark.asyncio
    async def test_handles_queue_depth_event(self) -> None:
        """Test handler broadcasts queue depth change."""
        mock_ws = MockWebSocket()
        await queue_metrics_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="QUEUE_DEPTH_CHANGED",
                payload={"queue_depth": 50},
            )

            await on_queue_depth_changed(event)

            sent_json = mock_ws.get_sent_json()
            assert len(sent_json) == 1
            assert sent_json[0]["depth"] == 50
        finally:
            queue_metrics_manager.disconnect(mock_ws)

    @pytest.mark.asyncio
    async def test_uses_default_for_missing_depth(self) -> None:
        """Test handler uses 0 as default queue depth."""
        mock_ws = MockWebSocket()
        await queue_metrics_manager.connect(mock_ws)

        try:
            event = MonitoringEvent(
                event_type="QUEUE_DEPTH_CHANGED",
                payload={},  # No queue_depth
            )

            await on_queue_depth_changed(event)

            sent_json = mock_ws.get_sent_json()
            assert sent_json[0]["depth"] == 0  # Default
        finally:
            queue_metrics_manager.disconnect(mock_ws)


# ============================================================================
# Integration Tests via TestClient
# ============================================================================


class TestWebSocketIntegration:
    """Integration tests using FastAPI TestClient."""

    def test_live_jobs_websocket_connects_in_dev_mode(self, client: TestClient) -> None:
        """Test live-jobs WebSocket connects in dev mode."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            True,
        ):
            with client.websocket_connect("/live-jobs") as websocket:
                websocket.send_text("ping")
                response = websocket.receive_text()
                assert response == "pong"

    def test_robot_status_websocket_connects_in_dev_mode(
        self, client: TestClient
    ) -> None:
        """Test robot-status WebSocket connects in dev mode."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            True,
        ):
            with client.websocket_connect("/robot-status") as websocket:
                websocket.send_text("ping")
                response = websocket.receive_text()
                assert response == "pong"

    def test_queue_metrics_websocket_sends_initial_depth(
        self, client: TestClient, mock_metrics_collector
    ) -> None:
        """Test queue-metrics WebSocket sends initial queue depth."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.JWT_DEV_MODE",
            True,
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.websockets.get_metrics_collector",
                return_value=mock_metrics_collector,
            ):
                with client.websocket_connect("/queue-metrics") as websocket:
                    import orjson

                    # First message should be initial queue depth
                    response = websocket.receive_text()
                    data = orjson.loads(response)
                    assert data["depth"] == 42

    def test_websocket_with_token_parameter(self, client: TestClient) -> None:
        """Test WebSocket accepts token via query parameter."""
        mock_payload = MagicMock()
        mock_payload.type = "access"
        mock_payload.sub = TEST_USER_ID

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.websockets.decode_token",
            return_value=mock_payload,
        ):
            with client.websocket_connect(
                "/live-jobs?token=valid.jwt.token"
            ) as websocket:
                websocket.send_text("ping")
                response = websocket.receive_text()
                assert response == "pong"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_broadcast_to_many_connections(self) -> None:
        """Test broadcast handles many connections efficiently."""
        manager = ConnectionManager()
        websockets = [MockWebSocket() for _ in range(100)]

        for ws in websockets:
            await manager.connect(ws)

        message = {"type": "test", "data": "broadcast"}
        await manager.broadcast(message)

        for ws in websockets:
            assert len(ws.sent_messages) == 1

        # Cleanup
        for ws in websockets:
            manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(self) -> None:
        """Test concurrent broadcasts don't interfere."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(ws)

        try:
            # Run multiple broadcasts concurrently
            tasks = [manager.broadcast({"id": i}) for i in range(10)]
            await asyncio.gather(*tasks)

            # All messages should be received
            assert len(ws.sent_messages) == 10
        finally:
            manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_disconnect_during_broadcast(self) -> None:
        """Test client disconnecting during broadcast is handled."""
        manager = ConnectionManager()
        normal_ws = MockWebSocket()
        failing_ws = FailingMockWebSocket()

        await manager.connect(normal_ws)
        await manager.connect(failing_ws)

        # Should not raise, failing connection removed
        await manager.broadcast({"test": True})

        assert normal_ws in manager.active_connections
        assert failing_ws not in manager.active_connections

    @pytest.mark.asyncio
    async def test_empty_message_broadcast(self) -> None:
        """Test broadcasting empty dict."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(ws)

        try:
            await manager.broadcast({})
            assert len(ws.sent_messages) == 1
        finally:
            manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_large_message_broadcast(self) -> None:
        """Test broadcasting large message."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        await manager.connect(ws)

        try:
            large_data = {"data": "x" * 100000}  # 100KB payload
            await manager.broadcast(large_data)
            assert len(ws.sent_messages) == 1
        finally:
            manager.disconnect(ws)
