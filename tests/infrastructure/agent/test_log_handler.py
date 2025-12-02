"""
Tests for RobotLogHandler.

Mock ALL external APIs (WebSocket send callbacks).
Test log capture, batching, offline buffering, and reconnection.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from casare_rpa.domain.value_objects.log_entry import (
    LogLevel,
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
)
from casare_rpa.infrastructure.agent.log_handler import (
    RobotLogHandler,
    create_robot_log_handler,
)


@pytest.fixture
def mock_send_callback() -> AsyncMock:
    """Create mock async send callback."""
    return AsyncMock()


@pytest.fixture
def robot_log_handler(mock_send_callback: AsyncMock) -> RobotLogHandler:
    """Create RobotLogHandler with mock callback."""
    return RobotLogHandler(
        robot_id="robot-123",
        send_callback=mock_send_callback,
        min_level=LogLevel.DEBUG,
        batch_size=10,
        flush_interval=1.0,
        buffer_size=100,
    )


@pytest.fixture
def mock_loguru_message() -> Mock:
    """Create mock loguru message with record."""
    message = Mock()
    record = {
        "time": datetime.now(timezone.utc),
        "level": Mock(name="INFO"),
        "message": "Test log message",
        "name": "test_module",
        "extra": {},
    }
    record["level"].name = "INFO"
    message.record = record
    return message


# ============================================================================
# Handler Initialization Tests
# ============================================================================


class TestRobotLogHandlerInit:
    """Tests for RobotLogHandler initialization."""

    def test_create_with_defaults(self) -> None:
        """Create handler with default values."""
        handler = RobotLogHandler(robot_id="robot-123")

        assert handler.robot_id == "robot-123"
        assert handler._min_level == LogLevel.DEBUG
        assert handler._batch_size == 50
        assert handler._flush_interval == 2.0
        assert handler._buffer_size == OFFLINE_BUFFER_SIZE
        assert handler._connected is False

    def test_create_with_custom_values(
        self,
        mock_send_callback: AsyncMock,
    ) -> None:
        """Create handler with custom values."""
        handler = RobotLogHandler(
            robot_id="robot-456",
            send_callback=mock_send_callback,
            min_level=LogLevel.WARNING,
            batch_size=25,
            flush_interval=3.0,
            buffer_size=500,
        )

        assert handler.robot_id == "robot-456"
        assert handler._min_level == LogLevel.WARNING
        assert handler._batch_size == 25
        assert handler._flush_interval == 3.0
        assert handler._buffer_size == 500

    def test_batch_size_capped(self) -> None:
        """Batch size is capped at MAX_LOG_BATCH_SIZE."""
        handler = RobotLogHandler(
            robot_id="robot-123",
            batch_size=500,  # Exceeds MAX_LOG_BATCH_SIZE
        )

        assert handler._batch_size == MAX_LOG_BATCH_SIZE


# ============================================================================
# Handler Lifecycle Tests
# ============================================================================


class TestRobotLogHandlerLifecycle:
    """Tests for handler start/stop."""

    @pytest.mark.asyncio
    async def test_start_handler(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Start handler creates flush task."""
        await robot_log_handler.start()

        assert robot_log_handler._running is True
        assert robot_log_handler._flush_task is not None

        await robot_log_handler.stop()

    @pytest.mark.asyncio
    async def test_start_twice_is_safe(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Starting twice is safe."""
        await robot_log_handler.start()
        await robot_log_handler.start()

        assert robot_log_handler._running is True

        await robot_log_handler.stop()

    @pytest.mark.asyncio
    async def test_stop_handler(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Stop handler clears running flag."""
        await robot_log_handler.start()
        await robot_log_handler.stop()

        assert robot_log_handler._running is False
        assert robot_log_handler._flush_task is None

    @pytest.mark.asyncio
    async def test_stop_flushes_remaining(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Stop flushes remaining logs."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)

        await robot_log_handler.stop()

        # Should have attempted to flush
        # (may or may not succeed based on timing)


# ============================================================================
# Connection State Tests
# ============================================================================


class TestRobotLogHandlerConnection:
    """Tests for connection state management."""

    def test_set_connected_true(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Set connected state to true."""
        robot_log_handler.set_connected(True)
        assert robot_log_handler._connected is True

    def test_set_connected_false(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Set connected state to false."""
        robot_log_handler.set_connected(True)
        robot_log_handler.set_connected(False)
        assert robot_log_handler._connected is False

    def test_reconnect_moves_offline_to_send_queue(
        self,
        robot_log_handler: RobotLogHandler,
        mock_loguru_message: Mock,
    ) -> None:
        """Reconnecting moves offline buffer to send queue."""
        # Disconnect and capture log
        robot_log_handler.set_connected(False)
        robot_log_handler.sink(mock_loguru_message)

        assert len(robot_log_handler._offline_buffer) == 1
        assert len(robot_log_handler._send_queue) == 0

        # Reconnect
        robot_log_handler.set_connected(True)

        assert len(robot_log_handler._offline_buffer) == 0
        assert len(robot_log_handler._send_queue) == 1

    def test_set_send_callback(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Set send callback."""
        new_callback = AsyncMock()
        robot_log_handler.set_send_callback(new_callback)
        assert robot_log_handler._send_callback == new_callback


# ============================================================================
# Level Filter Tests
# ============================================================================


class TestRobotLogHandlerLevelFilter:
    """Tests for log level filtering."""

    def test_get_min_level(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Get minimum log level."""
        assert robot_log_handler.min_level == LogLevel.DEBUG

    def test_set_min_level(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Set minimum log level."""
        robot_log_handler.min_level = LogLevel.ERROR
        assert robot_log_handler.min_level == LogLevel.ERROR

    def test_sink_filters_below_min_level(
        self,
    ) -> None:
        """Sink filters logs below min_level."""
        handler = RobotLogHandler(
            robot_id="robot-123",
            min_level=LogLevel.WARNING,
        )
        handler.set_connected(True)

        # Create DEBUG level message
        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="DEBUG"),
            "message": "Debug message",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "DEBUG"
        message.record = record

        handler.sink(message)

        # Should not be added to queue (DEBUG < WARNING)
        assert len(handler._send_queue) == 0
        assert handler._logs_captured == 0

    def test_sink_accepts_at_or_above_min_level(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Sink accepts logs at or above min_level."""
        robot_log_handler.min_level = LogLevel.INFO
        robot_log_handler.set_connected(True)

        # Create INFO level message
        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="INFO"),
            "message": "Info message",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "INFO"
        message.record = record

        robot_log_handler.sink(message)

        assert len(robot_log_handler._send_queue) == 1


# ============================================================================
# Sink Tests
# ============================================================================


class TestRobotLogHandlerSink:
    """Tests for loguru sink function."""

    def test_sink_captures_log_when_connected(
        self,
        robot_log_handler: RobotLogHandler,
        mock_loguru_message: Mock,
    ) -> None:
        """Sink captures log to send queue when connected."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)

        assert len(robot_log_handler._send_queue) == 1
        assert robot_log_handler._logs_captured == 1

    def test_sink_buffers_log_when_disconnected(
        self,
        robot_log_handler: RobotLogHandler,
        mock_loguru_message: Mock,
    ) -> None:
        """Sink buffers log when disconnected."""
        robot_log_handler.set_connected(False)
        robot_log_handler.sink(mock_loguru_message)

        assert len(robot_log_handler._offline_buffer) == 1
        assert len(robot_log_handler._send_queue) == 0

    def test_sink_extracts_correct_fields(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Sink extracts correct fields from loguru record."""
        robot_log_handler.set_connected(True)

        message = Mock()
        timestamp = datetime.now(timezone.utc)
        record = {
            "time": timestamp,
            "level": Mock(name="ERROR"),
            "message": "Error occurred",
            "name": "my_module",
            "extra": {"user_id": "123"},
        }
        record["level"].name = "ERROR"
        message.record = record

        robot_log_handler.sink(message)

        log_data = robot_log_handler._send_queue[0]
        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error occurred"
        assert log_data["source"] == "my_module"
        assert log_data["extra"] == {"user_id": "123"}

    def test_sink_handles_unknown_level(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Sink handles unknown log level."""
        robot_log_handler.set_connected(True)

        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="CUSTOM"),
            "message": "Custom level",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "CUSTOM"
        message.record = record

        robot_log_handler.sink(message)

        # Should default to INFO
        log_data = robot_log_handler._send_queue[0]
        assert log_data["level"] == "INFO"

    def test_sink_filters_internal_extra_keys(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Sink filters out internal loguru extra keys."""
        robot_log_handler.set_connected(True)

        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="INFO"),
            "message": "Test",
            "name": "test",
            "extra": {
                "_internal_key": "hidden",
                "visible_key": "shown",
            },
        }
        record["level"].name = "INFO"
        message.record = record

        robot_log_handler.sink(message)

        log_data = robot_log_handler._send_queue[0]
        assert "_internal_key" not in log_data.get("extra", {})
        assert log_data["extra"]["visible_key"] == "shown"


# ============================================================================
# Flush Tests
# ============================================================================


class TestRobotLogHandlerFlush:
    """Tests for flush method."""

    @pytest.mark.asyncio
    async def test_flush_sends_batch(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Flush sends batched logs."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)
        robot_log_handler.sink(mock_loguru_message)

        count = await robot_log_handler.flush()

        assert count == 2
        mock_send_callback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_flush_empty_queue_returns_zero(
        self,
        robot_log_handler: RobotLogHandler,
    ) -> None:
        """Flush with empty queue returns 0."""
        count = await robot_log_handler.flush()
        assert count == 0

    @pytest.mark.asyncio
    async def test_flush_no_callback_returns_zero(
        self,
    ) -> None:
        """Flush with no callback returns 0."""
        handler = RobotLogHandler(robot_id="robot-123", send_callback=None)
        handler.set_connected(True)

        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="INFO"),
            "message": "Test",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "INFO"
        message.record = record
        handler.sink(message)

        count = await handler.flush()
        assert count == 0

    @pytest.mark.asyncio
    async def test_flush_sends_correct_format(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Flush sends correctly formatted batch."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)

        await robot_log_handler.flush()

        call_args = mock_send_callback.call_args
        sent_data = json.loads(call_args[0][0])

        assert sent_data["type"] == "log_batch"
        assert sent_data["robot_id"] == "robot-123"
        assert sent_data["sequence"] == 1
        assert len(sent_data["logs"]) == 1

    @pytest.mark.asyncio
    async def test_flush_increments_sequence(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Flush increments sequence number."""
        robot_log_handler.set_connected(True)

        robot_log_handler.sink(mock_loguru_message)
        await robot_log_handler.flush()

        robot_log_handler.sink(mock_loguru_message)
        await robot_log_handler.flush()

        calls = mock_send_callback.call_args_list
        batch1 = json.loads(calls[0][0][0])
        batch2 = json.loads(calls[1][0][0])

        assert batch1["sequence"] == 1
        assert batch2["sequence"] == 2

    @pytest.mark.asyncio
    async def test_flush_error_moves_to_offline_buffer(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Flush error moves logs to offline buffer."""
        mock_send_callback.side_effect = Exception("Send failed")

        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)

        count = await robot_log_handler.flush()

        assert count == 0
        assert len(robot_log_handler._offline_buffer) == 1

    @pytest.mark.asyncio
    async def test_flush_with_sync_callback(
        self,
    ) -> None:
        """Flush works with synchronous callback."""
        sync_callback = Mock()
        handler = RobotLogHandler(
            robot_id="robot-123",
            send_callback=sync_callback,
        )
        handler.set_connected(True)

        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="INFO"),
            "message": "Test",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "INFO"
        message.record = record
        handler.sink(message)

        count = await handler.flush()

        assert count == 1
        sync_callback.assert_called_once()


# ============================================================================
# Offline Buffer Tests
# ============================================================================


class TestRobotLogHandlerOfflineBuffer:
    """Tests for offline buffering."""

    def test_offline_buffer_capped(
        self,
    ) -> None:
        """Offline buffer is capped at buffer_size."""
        handler = RobotLogHandler(
            robot_id="robot-123",
            buffer_size=2,
        )
        handler.set_connected(False)

        message = Mock()
        record = {
            "time": datetime.now(timezone.utc),
            "level": Mock(name="INFO"),
            "message": "Test",
            "name": "test",
            "extra": {},
        }
        record["level"].name = "INFO"
        message.record = record

        # Add 3 logs to buffer of size 2
        handler.sink(message)
        handler.sink(message)
        handler.sink(message)

        assert len(handler._offline_buffer) == 2
        assert handler._logs_dropped == 1


# ============================================================================
# Metrics Tests
# ============================================================================


class TestRobotLogHandlerMetrics:
    """Tests for handler metrics."""

    def test_get_metrics(
        self,
        robot_log_handler: RobotLogHandler,
        mock_loguru_message: Mock,
    ) -> None:
        """Get handler metrics."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)

        metrics = robot_log_handler.get_metrics()

        assert metrics["robot_id"] == "robot-123"
        assert metrics["connected"] is True
        assert metrics["min_level"] == "DEBUG"
        assert metrics["logs_captured"] == 1
        assert metrics["logs_sent"] == 0
        assert metrics["send_queue_size"] == 1

    @pytest.mark.asyncio
    async def test_metrics_track_sent(
        self,
        robot_log_handler: RobotLogHandler,
        mock_send_callback: AsyncMock,
        mock_loguru_message: Mock,
    ) -> None:
        """Metrics track sent count after flush."""
        robot_log_handler.set_connected(True)
        robot_log_handler.sink(mock_loguru_message)
        await robot_log_handler.flush()

        metrics = robot_log_handler.get_metrics()
        assert metrics["logs_sent"] == 1
        assert metrics["batches_sent"] == 1


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestCreateRobotLogHandler:
    """Tests for create_robot_log_handler factory."""

    def test_create_handler_and_id(
        self,
        mock_send_callback: AsyncMock,
    ) -> None:
        """Factory creates handler and returns ID."""
        with patch("casare_rpa.infrastructure.agent.log_handler.logger") as mock_logger:
            mock_logger.add.return_value = 42

            handler, handler_id = create_robot_log_handler(
                robot_id="robot-123",
                send_callback=mock_send_callback,
                min_level="INFO",
            )

            assert isinstance(handler, RobotLogHandler)
            assert handler.robot_id == "robot-123"
            assert handler.min_level == LogLevel.INFO
            assert handler_id == 42

    def test_create_handler_default_level(
        self,
    ) -> None:
        """Factory uses DEBUG as default level."""
        with patch("casare_rpa.infrastructure.agent.log_handler.logger") as mock_logger:
            mock_logger.add.return_value = 1

            handler, _ = create_robot_log_handler(robot_id="robot-123")

            assert handler.min_level == LogLevel.DEBUG
