"""
Tests for WebSocket connection management and broadcasting.

Tests the ConnectionManager class and WebSocket endpoints.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from fastapi import WebSocket

from casare_rpa.orchestrator.api.routers.websockets import (
    ConnectionManager,
    broadcast_job_update,
    broadcast_robot_status,
    broadcast_queue_metrics,
)


@pytest.fixture
def connection_manager():
    """Create fresh ConnectionManager instance."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket connection."""
    ws = Mock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    return ws


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connect_adds_websocket(self, connection_manager, mock_websocket):
        """Test that connect adds WebSocket to active connections."""
        await connection_manager.connect(mock_websocket)

        assert mock_websocket in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, connection_manager):
        """Test connecting multiple clients."""
        ws1 = Mock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = Mock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        assert len(connection_manager.active_connections) == 2
        assert ws1 in connection_manager.active_connections
        assert ws2 in connection_manager.active_connections

    def test_disconnect_removes_websocket(self, connection_manager, mock_websocket):
        """Test that disconnect removes WebSocket."""
        connection_manager.active_connections.add(mock_websocket)

        connection_manager.disconnect(mock_websocket)

        assert mock_websocket not in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 0

    def test_disconnect_nonexistent_websocket(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket that's not connected."""
        # Should not raise error (using discard instead of remove)
        connection_manager.disconnect(mock_websocket)

        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_success(self, connection_manager, mock_websocket):
        """Test successful broadcast to single client."""
        await connection_manager.connect(mock_websocket)

        message = {"type": "test", "data": "hello"}
        await connection_manager.broadcast(message)

        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "test" in sent_data
        assert "hello" in sent_data

    @pytest.mark.asyncio
    async def test_broadcast_multiple_clients(self, connection_manager):
        """Test broadcasting to multiple clients."""
        ws1 = Mock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()

        ws2 = Mock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        message = {"type": "broadcast_test"}
        await connection_manager.broadcast(message)

        # Both clients should receive the message
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_timeout_disconnects_client(self, connection_manager):
        """Test that slow clients are disconnected on timeout."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        # Simulate timeout by making send_text hang
        mock_websocket.send_text = AsyncMock(side_effect=asyncio.TimeoutError())

        await connection_manager.connect(mock_websocket)
        assert len(connection_manager.active_connections) == 1

        # Broadcast should timeout and disconnect client
        message = {"type": "test"}
        await connection_manager.broadcast(message)

        # Client should be disconnected after timeout
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_error(self, connection_manager):
        """Test that clients with send errors are disconnected."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection lost"))

        await connection_manager.connect(mock_websocket)
        assert len(connection_manager.active_connections) == 1

        # Broadcast should handle error and disconnect client
        message = {"type": "test"}
        await connection_manager.broadcast(message)

        # Client should be disconnected after error
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure(self, connection_manager):
        """Test that healthy clients receive broadcast even if some fail."""
        # Create two clients: one healthy, one failing
        healthy_ws = Mock(spec=WebSocket)
        healthy_ws.accept = AsyncMock()
        healthy_ws.send_text = AsyncMock()

        failing_ws = Mock(spec=WebSocket)
        failing_ws.accept = AsyncMock()
        failing_ws.send_text = AsyncMock(side_effect=Exception("Error"))

        await connection_manager.connect(healthy_ws)
        await connection_manager.connect(failing_ws)

        message = {"type": "test"}
        await connection_manager.broadcast(message)

        # Healthy client should receive message
        healthy_ws.send_text.assert_called_once()

        # Failing client should be disconnected
        assert healthy_ws in connection_manager.active_connections
        assert failing_ws not in connection_manager.active_connections


class TestBroadcastHelpers:
    """Tests for broadcast helper functions."""

    @pytest.mark.asyncio
    async def test_broadcast_job_update(self):
        """Test job update broadcast helper."""
        with patch(
            "casare_rpa.orchestrator.api.routers.websockets.live_jobs_manager"
        ) as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await broadcast_job_update("job-123", "completed")

            # Verify broadcast was called with correct message structure
            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args[0][0]
            assert call_args["job_id"] == "job-123"
            assert call_args["status"] == "completed"
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_robot_status(self):
        """Test robot status broadcast helper."""
        with patch(
            "casare_rpa.orchestrator.api.routers.websockets.robot_status_manager"
        ) as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await broadcast_robot_status("robot-001", "busy", 45.2, 1024.5)

            # Verify broadcast was called with correct message structure
            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args[0][0]
            assert call_args["robot_id"] == "robot-001"
            assert call_args["status"] == "busy"
            assert call_args["cpu_percent"] == 45.2
            assert call_args["memory_mb"] == 1024.5
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_queue_metrics(self):
        """Test queue metrics broadcast helper."""
        with patch(
            "casare_rpa.orchestrator.api.routers.websockets.queue_metrics_manager"
        ) as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await broadcast_queue_metrics(42)

            # Verify broadcast was called with correct message structure
            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args[0][0]
            assert call_args["depth"] == 42
            assert "timestamp" in call_args


class TestWebSocketEndpoints:
    """Integration tests for WebSocket endpoints."""

    # Note: Full integration tests would require TestClient with WebSocket support
    # These are structural tests verifying the endpoint behavior

    @pytest.mark.asyncio
    async def test_connection_manager_lifecycle(self):
        """Test full lifecycle: connect, broadcast, disconnect."""
        manager = ConnectionManager()

        # Create mock WebSocket
        ws = Mock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()

        # Connect
        await manager.connect(ws)
        assert len(manager.active_connections) == 1

        # Broadcast
        await manager.broadcast({"type": "test"})
        ws.send_text.assert_called()

        # Disconnect
        manager.disconnect(ws)
        assert len(manager.active_connections) == 0
