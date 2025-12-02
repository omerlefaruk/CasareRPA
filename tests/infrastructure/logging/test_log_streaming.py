"""
Tests for LogStreamingService.

Mock ALL external APIs (WebSocket connections, database).
Test subscriber management, broadcasting, filtering, and persistence.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.domain.value_objects.log_entry import (
    LogEntry,
    LogBatch,
    LogLevel,
)
from casare_rpa.infrastructure.logging.log_streaming_service import (
    LogStreamingService,
)


@pytest.fixture
def mock_log_repository() -> AsyncMock:
    """Create mock log repository."""
    repo = AsyncMock()
    repo.save_batch.return_value = 0
    return repo


@pytest.fixture
def log_streaming_service(mock_log_repository: AsyncMock) -> LogStreamingService:
    """Create LogStreamingService with mock repository."""
    return LogStreamingService(
        log_repository=mock_log_repository,
        persist_logs=True,
        buffer_size=100,
    )


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    return ws


@pytest.fixture
def sample_batch_data() -> Dict[str, Any]:
    """Create sample log batch data."""
    return {
        "robot_id": "robot-123",
        "sequence": 1,
        "logs": [
            {
                "timestamp": "2024-01-15T10:30:00+00:00",
                "level": "INFO",
                "message": "Test message 1",
                "source": "test_source",
            },
            {
                "timestamp": "2024-01-15T10:30:01+00:00",
                "level": "ERROR",
                "message": "Test error",
                "source": "test_source",
            },
        ],
    }


# ============================================================================
# Service Lifecycle Tests
# ============================================================================


class TestLogStreamingServiceLifecycle:
    """Tests for service start/stop."""

    @pytest.mark.asyncio
    async def test_start_service(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Start service sets running flag."""
        await log_streaming_service.start()

        assert log_streaming_service._running is True
        assert log_streaming_service._persist_task is not None

        await log_streaming_service.stop()

    @pytest.mark.asyncio
    async def test_start_twice_logs_warning(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Starting twice logs warning."""
        await log_streaming_service.start()
        await log_streaming_service.start()  # Should warn

        assert log_streaming_service._running is True

        await log_streaming_service.stop()

    @pytest.mark.asyncio
    async def test_stop_service(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Stop service clears running flag."""
        await log_streaming_service.start()
        await log_streaming_service.stop()

        assert log_streaming_service._running is False
        assert log_streaming_service._persist_task is None

    @pytest.mark.asyncio
    async def test_stop_without_start(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Stop without start is safe."""
        await log_streaming_service.stop()
        assert log_streaming_service._running is False


# ============================================================================
# Subscriber Management Tests
# ============================================================================


class TestLogStreamingServiceSubscription:
    """Tests for subscribe/unsubscribe methods."""

    @pytest.mark.asyncio
    async def test_subscribe_to_specific_robots(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Subscribe to specific robot IDs."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=["robot-1", "robot-2"],
            tenant_id="tenant-123",
            min_level=LogLevel.INFO,
        )

        assert mock_websocket in log_streaming_service._subscribers
        assert mock_websocket in log_streaming_service._robot_subscribers["robot-1"]
        assert mock_websocket in log_streaming_service._robot_subscribers["robot-2"]

    @pytest.mark.asyncio
    async def test_subscribe_to_all_robots(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Subscribe to all robots (global subscriber)."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=None,
            tenant_id="tenant-123",
        )

        assert mock_websocket in log_streaming_service._global_subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_from_all_sets(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Unsubscribe removes from all subscriber sets."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=["robot-1"],
        )
        await log_streaming_service.unsubscribe(mock_websocket)

        assert mock_websocket not in log_streaming_service._subscribers
        assert mock_websocket not in log_streaming_service._robot_subscribers.get(
            "robot-1", set()
        )

    @pytest.mark.asyncio
    async def test_unsubscribe_global_subscriber(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Unsubscribe global subscriber."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=None,
        )
        await log_streaming_service.unsubscribe(mock_websocket)

        assert mock_websocket not in log_streaming_service._global_subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_is_safe(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Unsubscribing non-existent websocket is safe."""
        await log_streaming_service.unsubscribe(mock_websocket)
        # No error raised

    @pytest.mark.asyncio
    async def test_get_subscriber_count(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Get subscriber count."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await log_streaming_service.subscribe(ws1, robot_ids=["robot-1"])
        await log_streaming_service.subscribe(ws2, robot_ids=None)

        assert log_streaming_service.get_subscriber_count() == 2


# ============================================================================
# Receive Log Batch Tests
# ============================================================================


class TestLogStreamingServiceReceiveBatch:
    """Tests for receive_log_batch method."""

    @pytest.mark.asyncio
    async def test_receive_batch_success(
        self,
        log_streaming_service: LogStreamingService,
        sample_batch_data: Dict[str, Any],
    ) -> None:
        """Receive batch returns log count."""
        count = await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=sample_batch_data,
            tenant_id="tenant-456",
        )

        assert count == 2
        assert log_streaming_service._logs_received == 2

    @pytest.mark.asyncio
    async def test_receive_batch_queues_for_persistence(
        self,
        log_streaming_service: LogStreamingService,
        sample_batch_data: Dict[str, Any],
    ) -> None:
        """Received logs are queued for persistence."""
        await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=sample_batch_data,
            tenant_id="tenant-456",
        )

        assert log_streaming_service._persist_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_receive_batch_invalid_data(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Invalid batch data returns 0."""
        invalid_data = {"invalid": "data"}

        count = await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=invalid_data,
            tenant_id="tenant-456",
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_receive_batch_broadcasts_to_subscribers(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
        sample_batch_data: Dict[str, Any],
    ) -> None:
        """Received logs are broadcast to subscribers."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=["robot-123"],
            min_level=LogLevel.DEBUG,
        )

        await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=sample_batch_data,
            tenant_id="tenant-456",
        )

        assert mock_websocket.send.await_count == 2  # 2 logs

    @pytest.mark.asyncio
    async def test_receive_batch_filters_by_level(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
        sample_batch_data: Dict[str, Any],
    ) -> None:
        """Broadcasts filter by subscriber min_level."""
        await log_streaming_service.subscribe(
            websocket=mock_websocket,
            robot_ids=["robot-123"],
            min_level=LogLevel.ERROR,  # Only ERROR and above
        )

        await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=sample_batch_data,
            tenant_id="tenant-456",
        )

        # Only 1 ERROR log should be sent
        assert mock_websocket.send.await_count == 1


# ============================================================================
# Receive Single Log Tests
# ============================================================================


class TestLogStreamingServiceReceiveSingle:
    """Tests for receive_single_log method."""

    @pytest.mark.asyncio
    async def test_receive_single_log(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Receive single log entry."""
        await log_streaming_service.receive_single_log(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            message="Single log message",
            source="test",
        )

        assert log_streaming_service._logs_received == 1

    @pytest.mark.asyncio
    async def test_receive_single_log_queues_persistence(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Single log is queued for persistence."""
        await log_streaming_service.receive_single_log(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level="ERROR",
            message="Error message",
        )

        assert log_streaming_service._persist_queue.qsize() == 1


# ============================================================================
# Broadcasting Tests
# ============================================================================


class TestLogStreamingServiceBroadcast:
    """Tests for log broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcast_to_robot_subscribers(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Broadcast to robot-specific subscribers."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await log_streaming_service.subscribe(ws1, robot_ids=["robot-1"])
        await log_streaming_service.subscribe(ws2, robot_ids=["robot-2"])

        entry = LogEntry(
            robot_id="robot-1",
            tenant_id="tenant-123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test",
        )

        await log_streaming_service._broadcast_logs(
            robot_id="robot-1",
            tenant_id="tenant-123",
            entries=[entry],
        )

        ws1.send.assert_awaited_once()
        ws2.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_to_global_subscribers(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Broadcast to global subscribers matching tenant."""
        ws_global = AsyncMock()

        await log_streaming_service.subscribe(
            ws_global,
            robot_ids=None,
            tenant_id="tenant-123",
        )

        entry = LogEntry(
            robot_id="robot-1",
            tenant_id="tenant-123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test",
        )

        await log_streaming_service._broadcast_logs(
            robot_id="robot-1",
            tenant_id="tenant-123",
            entries=[entry],
        )

        ws_global.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_filters_by_source(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Broadcast filters by source when specified."""
        await log_streaming_service.subscribe(
            mock_websocket,
            robot_ids=["robot-1"],
            sources=["allowed_source"],
        )

        entry1 = LogEntry(
            robot_id="robot-1",
            tenant_id="tenant-123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Allowed",
            source="allowed_source",
        )
        entry2 = LogEntry(
            robot_id="robot-1",
            tenant_id="tenant-123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Blocked",
            source="other_source",
        )

        await log_streaming_service._broadcast_logs(
            robot_id="robot-1",
            tenant_id="tenant-123",
            entries=[entry1, entry2],
        )

        # Only entry1 should be sent
        assert mock_websocket.send.await_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Failed websocket connections are removed."""
        ws_failing = AsyncMock()
        ws_failing.send.side_effect = Exception("Connection closed")

        await log_streaming_service.subscribe(
            ws_failing,
            robot_ids=["robot-1"],
        )

        entry = LogEntry(
            robot_id="robot-1",
            tenant_id="tenant-123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Test",
        )

        await log_streaming_service._broadcast_logs(
            robot_id="robot-1",
            tenant_id="tenant-123",
            entries=[entry],
        )

        # Failed connection should be removed
        assert ws_failing not in log_streaming_service._subscribers


# ============================================================================
# Offline Buffer Tests
# ============================================================================


class TestLogStreamingServiceBuffer:
    """Tests for offline buffering."""

    def test_buffer_log(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Buffer log entry for offline robot."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Buffered log",
        )

        log_streaming_service.buffer_log("robot-123", entry)

        buffer = log_streaming_service._offline_buffers["robot-123"]
        assert len(buffer) == 1
        assert buffer[0] == entry

    def test_buffer_drops_oldest_when_full(
        self,
    ) -> None:
        """Buffer drops oldest entry when full."""
        service = LogStreamingService(buffer_size=2)

        for i in range(3):
            entry = LogEntry(
                robot_id="robot-123",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message=f"Message {i}",
            )
            service.buffer_log("robot-123", entry)

        buffer = service._offline_buffers["robot-123"]
        assert len(buffer) == 2
        assert buffer[0].message == "Message 1"  # First dropped
        assert service._logs_dropped == 1

    def test_get_buffered_logs_clears_buffer(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Get buffered logs returns and clears buffer."""
        entry = LogEntry(
            robot_id="robot-123",
            tenant_id="tenant-456",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            message="Buffered",
        )
        log_streaming_service.buffer_log("robot-123", entry)

        logs = log_streaming_service.get_buffered_logs("robot-123")

        assert len(logs) == 1
        assert "robot-123" not in log_streaming_service._offline_buffers

    def test_get_buffered_logs_empty(
        self,
        log_streaming_service: LogStreamingService,
    ) -> None:
        """Get buffered logs for unknown robot returns empty list."""
        logs = log_streaming_service.get_buffered_logs("unknown-robot")
        assert logs == []


# ============================================================================
# Metrics Tests
# ============================================================================


class TestLogStreamingServiceMetrics:
    """Tests for service metrics."""

    @pytest.mark.asyncio
    async def test_get_metrics(
        self,
        log_streaming_service: LogStreamingService,
        mock_websocket: AsyncMock,
    ) -> None:
        """Get service metrics."""
        await log_streaming_service.subscribe(
            mock_websocket,
            robot_ids=["robot-1"],
        )

        metrics = log_streaming_service.get_metrics()

        assert "running" in metrics
        assert "subscribers" in metrics
        assert metrics["subscribers"] == 1
        assert "logs_received" in metrics
        assert "logs_broadcast" in metrics
        assert "logs_persisted" in metrics
        assert "logs_dropped" in metrics

    @pytest.mark.asyncio
    async def test_metrics_track_received(
        self,
        log_streaming_service: LogStreamingService,
        sample_batch_data: Dict[str, Any],
    ) -> None:
        """Metrics track received log count."""
        await log_streaming_service.receive_log_batch(
            robot_id="robot-123",
            batch_data=sample_batch_data,
            tenant_id="tenant-456",
        )

        metrics = log_streaming_service.get_metrics()
        assert metrics["logs_received"] == 2


# ============================================================================
# Persistence Worker Tests
# ============================================================================


class TestLogStreamingServicePersistence:
    """Tests for persistence worker."""

    @pytest.mark.asyncio
    async def test_persist_batch_success(
        self,
        log_streaming_service: LogStreamingService,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Persist batch saves to repository."""
        mock_log_repository.save_batch.return_value = 5

        entries = [
            LogEntry(
                robot_id="robot-123",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message=f"Message {i}",
            )
            for i in range(5)
        ]

        await log_streaming_service._persist_batch(entries)

        mock_log_repository.save_batch.assert_awaited_once_with(entries)
        assert log_streaming_service._logs_persisted == 5

    @pytest.mark.asyncio
    async def test_persist_batch_error_tracks_dropped(
        self,
        log_streaming_service: LogStreamingService,
        mock_log_repository: AsyncMock,
    ) -> None:
        """Persistence error tracks dropped logs."""
        mock_log_repository.save_batch.side_effect = Exception("DB error")

        entries = [
            LogEntry(
                robot_id="robot-123",
                tenant_id="tenant-456",
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                message="Test",
            )
        ]

        await log_streaming_service._persist_batch(entries)

        assert log_streaming_service._logs_dropped == 1

    @pytest.mark.asyncio
    async def test_persist_no_repository(
        self,
    ) -> None:
        """Persist with no repository is no-op."""
        service = LogStreamingService(log_repository=None)
        await service._persist_batch([])  # Should not error
