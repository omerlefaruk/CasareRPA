"""
Robot Log Handler - Loguru Handler for Streaming Logs to Orchestrator.

Provides a custom loguru handler that streams logs from robot workers
to the orchestrator via WebSocket. Includes offline buffering and
batch transmission for efficiency.
"""

import asyncio
import json
from collections import deque
from collections.abc import Callable
from typing import Any

from loguru import logger

from casare_rpa.domain.value_objects.log_entry import (
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
    LogLevel,
)


class RobotLogHandler:
    """
    Custom loguru sink for streaming logs to orchestrator.

    Features:
    - Batch transmission for efficiency
    - Offline buffering when disconnected
    - Level filtering
    - Source tagging
    - Async-safe operation

    Usage:
        handler = RobotLogHandler(
            robot_id="robot-123",
            send_callback=websocket.send,
        )

        # Add to loguru
        logger.add(handler.sink, format="{message}")

        # When connected
        handler.set_connected(True)
        await handler.start()

        # When disconnected
        handler.set_connected(False)
        await handler.flush()
    """

    def __init__(
        self,
        robot_id: str,
        send_callback: Callable[[str], Any] | None = None,
        min_level: LogLevel = LogLevel.DEBUG,
        batch_size: int = 50,
        flush_interval: float = 2.0,
        buffer_size: int = OFFLINE_BUFFER_SIZE,
    ) -> None:
        """
        Initialize robot log handler.

        Args:
            robot_id: ID of this robot.
            send_callback: Async callback to send messages (WebSocket).
            min_level: Minimum log level to stream.
            batch_size: Number of logs to batch before sending.
            flush_interval: Seconds between automatic flushes.
            buffer_size: Size of offline buffer.
        """
        self.robot_id = robot_id
        self._send_callback = send_callback
        self._min_level = min_level
        self._batch_size = min(batch_size, MAX_LOG_BATCH_SIZE)
        self._flush_interval = flush_interval
        self._buffer_size = buffer_size

        # Connection state
        self._connected = False

        # Log buffers
        self._send_queue: deque[dict[str, Any]] = deque(maxlen=self._buffer_size)
        self._offline_buffer: deque[dict[str, Any]] = deque(maxlen=self._buffer_size)

        # Sequence number for ordering
        self._sequence = 0

        # Background task
        self._running = False
        self._flush_task: asyncio.Task | None = None

        # Metrics
        self._logs_captured = 0
        self._logs_sent = 0
        self._logs_dropped = 0
        self._batches_sent = 0

        # Event for signaling new logs
        self._has_logs = asyncio.Event()

    def set_send_callback(self, callback: Callable[[str], Any]) -> None:
        """
        Set the send callback for transmitting logs.

        Args:
            callback: Async callable that accepts a JSON string.
        """
        self._send_callback = callback

    def set_connected(self, connected: bool) -> None:
        """
        Update connection state.

        Args:
            connected: Whether WebSocket is connected.
        """
        was_connected = self._connected
        self._connected = connected

        if connected and not was_connected:
            # Just reconnected - queue offline buffer for sending
            while self._offline_buffer:
                log_data = self._offline_buffer.popleft()
                self._send_queue.append(log_data)
            self._has_logs.set()
            logger.debug(
                f"Log handler reconnected, " f"{len(self._send_queue)} buffered logs queued"
            )

    @property
    def min_level(self) -> LogLevel:
        """Get minimum log level."""
        return self._min_level

    @min_level.setter
    def min_level(self, level: LogLevel) -> None:
        """Set minimum log level."""
        self._min_level = level

    def sink(self, message: Any) -> None:
        """
        Loguru sink function.

        Called by loguru for each log message. Extracts record data
        and queues for transmission.

        Args:
            message: Loguru message object with record attached.
        """
        record = message.record

        # Map loguru level to our LogLevel
        level_name = record["level"].name.upper()
        try:
            level = LogLevel.from_string(level_name)
        except (ValueError, KeyError):
            level = LogLevel.INFO

        # Filter by level
        if level < self._min_level:
            return

        self._logs_captured += 1

        # Build log entry data
        log_data = {
            "timestamp": record["time"].isoformat(),
            "level": level.value,
            "message": str(record["message"]),
            "source": record.get("name", ""),
        }

        # Include extra data if present
        if record["extra"]:
            # Filter out internal loguru keys
            extra = {k: v for k, v in record["extra"].items() if not k.startswith("_")}
            if extra:
                log_data["extra"] = extra

        # Add to appropriate buffer
        if self._connected:
            self._send_queue.append(log_data)
            self._has_logs.set()
        else:
            if len(self._offline_buffer) >= self._buffer_size:
                self._logs_dropped += 1
            self._offline_buffer.append(log_data)

    async def start(self) -> None:
        """Start the background flush task."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.debug(f"RobotLogHandler started for {self.robot_id}")

    async def stop(self) -> None:
        """Stop the handler and flush remaining logs."""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None

        # Final flush
        await self.flush()

        logger.debug(
            f"RobotLogHandler stopped. "
            f"Captured: {self._logs_captured}, "
            f"Sent: {self._logs_sent}, "
            f"Dropped: {self._logs_dropped}"
        )

    async def flush(self) -> int:
        """
        Flush pending logs immediately.

        Returns:
            Number of logs sent.
        """
        if not self._send_callback or not self._send_queue:
            return 0

        # Collect logs to send
        logs_to_send = []
        while self._send_queue and len(logs_to_send) < self._batch_size:
            logs_to_send.append(self._send_queue.popleft())

        if not logs_to_send:
            return 0

        # Build batch message
        self._sequence += 1
        batch = {
            "type": "log_batch",
            "robot_id": self.robot_id,
            "sequence": self._sequence,
            "logs": logs_to_send,
        }

        try:
            if asyncio.iscoroutinefunction(self._send_callback):
                await self._send_callback(json.dumps(batch))
            else:
                self._send_callback(json.dumps(batch))

            self._logs_sent += len(logs_to_send)
            self._batches_sent += 1
            return len(logs_to_send)

        except Exception as e:
            # Put logs back in buffer if send failed
            for log_data in reversed(logs_to_send):
                if len(self._offline_buffer) < self._buffer_size:
                    self._offline_buffer.appendleft(log_data)
                else:
                    self._logs_dropped += 1

            logger.warning(f"Failed to send log batch: {e}")
            return 0

    async def _flush_loop(self) -> None:
        """Background loop for periodic flushing."""
        while self._running:
            try:
                # Wait for logs or timeout
                try:
                    await asyncio.wait_for(
                        self._has_logs.wait(),
                        timeout=self._flush_interval,
                    )
                except TimeoutError:
                    pass

                self._has_logs.clear()

                # Flush if connected and have logs
                if self._connected and self._send_queue:
                    await self.flush()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flush loop error: {e}")
                await asyncio.sleep(1)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get handler metrics.

        Returns:
            Dictionary with metric values.
        """
        return {
            "robot_id": self.robot_id,
            "connected": self._connected,
            "min_level": self._min_level.value,
            "logs_captured": self._logs_captured,
            "logs_sent": self._logs_sent,
            "logs_dropped": self._logs_dropped,
            "batches_sent": self._batches_sent,
            "send_queue_size": len(self._send_queue),
            "offline_buffer_size": len(self._offline_buffer),
            "sequence": self._sequence,
        }


def create_robot_log_handler(
    robot_id: str,
    send_callback: Callable[[str], Any] | None = None,
    min_level: str = "DEBUG",
) -> tuple:
    """
    Create and configure a robot log handler.

    This is a convenience function that creates the handler and
    returns both the handler instance and the handler ID for removal.

    Args:
        robot_id: Robot identifier.
        send_callback: WebSocket send function.
        min_level: Minimum level string.

    Returns:
        Tuple of (RobotLogHandler, handler_id).

    Example:
        handler, handler_id = create_robot_log_handler(
            robot_id="robot-123",
            send_callback=websocket.send,
        )

        # Later, to remove:
        logger.remove(handler_id)
    """
    level = LogLevel.from_string(min_level)
    handler = RobotLogHandler(
        robot_id=robot_id,
        send_callback=send_callback,
        min_level=level,
    )

    # Add to loguru with custom format
    handler_id = logger.add(
        handler.sink,
        format="{message}",  # Minimal format, handler extracts what it needs
        level=min_level.upper(),
        filter=lambda record: not record["extra"].get("_skip_remote", False),
    )

    return handler, handler_id


__all__ = [
    "RobotLogHandler",
    "create_robot_log_handler",
]
