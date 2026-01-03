"""
LogStreamingService - Real-time Log Streaming for Robot Orchestration.

Collects logs from robots via WebSocket and broadcasts to subscribed admin clients.
Provides buffering for temporary disconnections and efficient batch processing.
"""

import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from casare_rpa.domain.value_objects.log_entry import (
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
    LogBatch,
    LogEntry,
    LogLevel,
)
from casare_rpa.infrastructure.persistence.repositories.log_repository import (
    LogRepository,
)


class LogStreamingService:
    """
    Real-time log streaming service for robot orchestration.

    Features:
    - Collect logs from robots via WebSocket
    - Broadcast to subscribed admin clients
    - Buffer logs for temporary disconnections
    - Batch processing for efficiency
    - Level filtering per subscriber

    Usage:
        service = LogStreamingService(log_repository)
        await service.start()

        # Robot sends logs
        await service.receive_log_batch(robot_id, log_batch, tenant_id)

        # Admin subscribes to logs
        await service.subscribe(websocket, robot_ids=['robot-1'], min_level='INFO')

        # Admin receives log stream via their WebSocket
    """

    def __init__(
        self,
        log_repository: LogRepository | None = None,
        persist_logs: bool = True,
        buffer_size: int = OFFLINE_BUFFER_SIZE,
    ) -> None:
        """
        Initialize log streaming service.

        Args:
            log_repository: Repository for persisting logs.
            persist_logs: Whether to persist logs to database.
            buffer_size: Size of offline buffer per robot.
        """
        self._repository = log_repository
        self._persist_logs = persist_logs
        self._buffer_size = buffer_size
        self._running = False

        # Subscribers: websocket -> subscription config
        self._subscribers: dict[Any, dict[str, Any]] = {}

        # Subscriber sets by robot (for efficient broadcast)
        # robot_id -> set of websockets
        self._robot_subscribers: dict[str, set[Any]] = defaultdict(set)

        # All-robots subscribers (admins watching all logs)
        self._global_subscribers: set[Any] = set()

        # Offline buffers: robot_id -> list of LogEntry
        self._offline_buffers: dict[str, list[LogEntry]] = defaultdict(list)

        # Batch queue for persistence
        self._persist_queue: asyncio.Queue = asyncio.Queue()
        self._persist_task: asyncio.Task | None = None

        # Metrics
        self._logs_received = 0
        self._logs_broadcast = 0
        self._logs_persisted = 0
        self._logs_dropped = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the log streaming service."""
        if self._running:
            logger.warning("LogStreamingService already running")
            return

        self._running = True

        # Start persistence worker if enabled
        if self._persist_logs and self._repository:
            self._persist_task = asyncio.create_task(self._persist_worker())
            logger.debug("Started log persistence worker")

        logger.info("LogStreamingService started")

    async def stop(self) -> None:
        """Stop the log streaming service gracefully."""
        self._running = False

        # Stop persistence worker
        if self._persist_task:
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelledError:
                pass
            self._persist_task = None

        # Flush any remaining logs
        await self._flush_persist_queue()

        logger.info(
            f"LogStreamingService stopped. "
            f"Received: {self._logs_received}, "
            f"Broadcast: {self._logs_broadcast}, "
            f"Persisted: {self._logs_persisted}, "
            f"Dropped: {self._logs_dropped}"
        )

    async def subscribe(
        self,
        websocket: Any,
        robot_ids: list[str] | None = None,
        tenant_id: str | None = None,
        min_level: LogLevel = LogLevel.DEBUG,
        sources: list[str] | None = None,
    ) -> None:
        """
        Subscribe to log streams.

        Args:
            websocket: WebSocket connection to send logs to.
            robot_ids: List of robot IDs to subscribe to (None = all robots).
            tenant_id: Tenant ID for filtering (required for all-robots).
            min_level: Minimum log level to receive.
            sources: Optional list of sources to filter.
        """
        async with self._lock:
            config = {
                "robot_ids": robot_ids,
                "tenant_id": tenant_id,
                "min_level": min_level,
                "sources": sources,
                "subscribed_at": datetime.now(UTC),
            }
            self._subscribers[websocket] = config

            if robot_ids:
                for robot_id in robot_ids:
                    self._robot_subscribers[robot_id].add(websocket)
            else:
                self._global_subscribers.add(websocket)

            logger.debug(
                f"New log subscriber: robots={robot_ids or 'all'}, level={min_level.value}"
            )

    async def unsubscribe(self, websocket: Any) -> None:
        """
        Unsubscribe from log streams.

        Args:
            websocket: WebSocket to unsubscribe.
        """
        async with self._lock:
            config = self._subscribers.pop(websocket, None)
            if config:
                robot_ids = config.get("robot_ids")
                if robot_ids:
                    for robot_id in robot_ids:
                        self._robot_subscribers[robot_id].discard(websocket)
                else:
                    self._global_subscribers.discard(websocket)

                logger.debug("Log subscriber removed")

    async def receive_log_batch(
        self,
        robot_id: str,
        batch_data: dict[str, Any],
        tenant_id: str,
    ) -> int:
        """
        Receive a batch of logs from a robot.

        Args:
            robot_id: ID of the robot sending logs.
            batch_data: Dictionary with log batch data.
            tenant_id: Tenant ID for the robot.

        Returns:
            Number of logs processed.
        """
        try:
            batch = LogBatch.from_dict(batch_data, tenant_id)
        except Exception as e:
            logger.error(f"Failed to parse log batch from {robot_id}: {e}")
            return 0

        self._logs_received += len(batch.entries)

        # Persist logs
        if self._persist_logs and batch.entries:
            await self._persist_queue.put(batch.entries)

        # Broadcast to subscribers
        await self._broadcast_logs(robot_id, tenant_id, list(batch.entries))

        return len(batch.entries)

    async def receive_single_log(
        self,
        robot_id: str,
        tenant_id: str,
        timestamp: datetime,
        level: str,
        message: str,
        source: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """
        Receive a single log entry from a robot.

        Args:
            robot_id: ID of the robot.
            tenant_id: Tenant ID.
            timestamp: Log timestamp.
            level: Log level string.
            message: Log message.
            source: Optional source identifier.
            extra: Optional extra data.
        """
        entry = LogEntry(
            robot_id=robot_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            level=LogLevel.from_string(level),
            message=message,
            source=source,
            extra=extra,
        )

        self._logs_received += 1

        # Persist
        if self._persist_logs:
            await self._persist_queue.put([entry])

        # Broadcast
        await self._broadcast_logs(robot_id, tenant_id, [entry])

    async def _broadcast_logs(
        self,
        robot_id: str,
        tenant_id: str,
        entries: list[LogEntry],
    ) -> None:
        """
        Broadcast logs to relevant subscribers.

        Args:
            robot_id: Robot ID.
            tenant_id: Tenant ID.
            entries: Log entries to broadcast.
        """
        if not entries:
            return

        # Find relevant subscribers
        async with self._lock:
            subscribers = set()

            # Robot-specific subscribers
            subscribers.update(self._robot_subscribers.get(robot_id, set()))

            # Global subscribers for this tenant
            for ws in self._global_subscribers:
                config = self._subscribers.get(ws, {})
                if config.get("tenant_id") == tenant_id or config.get("tenant_id") is None:
                    subscribers.add(ws)

        # Broadcast to each subscriber
        failed_sockets = []
        for ws in subscribers:
            config = self._subscribers.get(ws, {})
            min_level = config.get("min_level", LogLevel.DEBUG)
            sources = config.get("sources")

            # Filter entries for this subscriber
            filtered = [
                e
                for e in entries
                if e.level >= min_level and (sources is None or e.source in sources)
            ]

            if not filtered:
                continue

            try:
                await self._send_to_subscriber(ws, robot_id, filtered)
                self._logs_broadcast += len(filtered)
            except Exception as e:
                logger.warning(f"Failed to send logs to subscriber: {e}")
                failed_sockets.append(ws)

        # Clean up failed connections
        for ws in failed_sockets:
            await self.unsubscribe(ws)

    async def _send_to_subscriber(
        self,
        websocket: Any,
        robot_id: str,
        entries: list[LogEntry],
    ) -> None:
        """
        Send log entries to a subscriber.

        Args:
            websocket: Subscriber's WebSocket.
            robot_id: Robot ID.
            entries: Filtered log entries.
        """
        import json

        for entry in entries:
            message = {
                "type": "log_entry",
                "robot_id": robot_id,
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level.value,
                "message": entry.message,
                "source": entry.source,
            }
            await websocket.send(json.dumps(message))

    async def _persist_worker(self) -> None:
        """Background worker for persisting logs."""
        batch: list[LogEntry] = []
        last_persist = datetime.now(UTC)

        while self._running:
            try:
                # Get entries with timeout for periodic flushes
                try:
                    entries = await asyncio.wait_for(
                        self._persist_queue.get(),
                        timeout=1.0,
                    )
                    batch.extend(entries)
                except TimeoutError:
                    pass

                # Persist when batch is large enough or after timeout
                now = datetime.now(UTC)
                should_persist = len(batch) >= MAX_LOG_BATCH_SIZE or (
                    batch and (now - last_persist).total_seconds() > 5.0
                )

                if should_persist and batch:
                    await self._persist_batch(batch)
                    batch = []
                    last_persist = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Persist worker error: {e}")
                await asyncio.sleep(1)

        # Final flush
        if batch:
            await self._persist_batch(batch)

    async def _persist_batch(self, entries: list[LogEntry]) -> None:
        """
        Persist a batch of log entries.

        Args:
            entries: Entries to persist.
        """
        if not self._repository:
            return

        try:
            count = await self._repository.save_batch(entries)
            self._logs_persisted += count
        except Exception as e:
            logger.error(f"Failed to persist log batch: {e}")
            self._logs_dropped += len(entries)

    async def _flush_persist_queue(self) -> None:
        """Flush remaining entries in persist queue."""
        if not self._repository:
            return

        batch = []
        while not self._persist_queue.empty():
            try:
                entries = self._persist_queue.get_nowait()
                batch.extend(entries)
            except asyncio.QueueEmpty:
                break

        if batch:
            await self._persist_batch(batch)

    def buffer_log(self, robot_id: str, entry: LogEntry) -> None:
        """
        Buffer a log entry for offline robot.

        Used when a robot reconnects and has buffered logs.

        Args:
            robot_id: Robot ID.
            entry: Log entry to buffer.
        """
        buffer = self._offline_buffers[robot_id]
        if len(buffer) >= self._buffer_size:
            # Drop oldest entry
            buffer.pop(0)
            self._logs_dropped += 1

        buffer.append(entry)

    def get_buffered_logs(self, robot_id: str) -> list[LogEntry]:
        """
        Get and clear buffered logs for a robot.

        Args:
            robot_id: Robot ID.

        Returns:
            List of buffered log entries.
        """
        return self._offline_buffers.pop(robot_id, [])

    def get_subscriber_count(self) -> int:
        """Get total subscriber count."""
        return len(self._subscribers)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Dictionary with metrics.
        """
        return {
            "running": self._running,
            "subscribers": len(self._subscribers),
            "global_subscribers": len(self._global_subscribers),
            "robot_subscriptions": {
                robot_id: len(subs) for robot_id, subs in self._robot_subscribers.items() if subs
            },
            "logs_received": self._logs_received,
            "logs_broadcast": self._logs_broadcast,
            "logs_persisted": self._logs_persisted,
            "logs_dropped": self._logs_dropped,
            "persist_queue_size": self._persist_queue.qsize(),
            "offline_buffers": {
                robot_id: len(buffer) for robot_id, buffer in self._offline_buffers.items()
            },
        }


# Thread-safe singleton using LazySingleton for deferred initialization
import threading

_log_streaming_lock = threading.Lock()
_log_streaming_instance: LogStreamingService | None = None


def _create_log_streaming_service() -> LogStreamingService:
    """Factory function for creating LogStreamingService."""
    from casare_rpa.infrastructure.persistence.repositories.log_repository import (
        LogRepository,
    )

    return LogStreamingService(LogRepository())


def get_log_streaming_service() -> LogStreamingService:
    """
    Get or create the singleton LogStreamingService.

    Returns:
        LogStreamingService instance.
    """
    # Double-checked locking pattern
    instance = _log_streaming_instance
    if instance is not None:
        return instance

    with _log_streaming_lock:
        # Check again within the lock
        import casare_rpa.infrastructure.logging.log_streaming_service as mod

        if mod._log_streaming_instance is None:
            mod._log_streaming_instance = _create_log_streaming_service()
        return mod._log_streaming_instance


async def init_log_streaming_service(
    log_repository: LogRepository | None = None,
) -> LogStreamingService:
    """
    Initialize and start the log streaming service.

    Args:
        log_repository: Optional repository instance.

    Returns:
        Started LogStreamingService.
    """
    with _log_streaming_lock:
        import casare_rpa.infrastructure.logging.log_streaming_service as mod

        if mod._log_streaming_instance is None:
            mod._log_streaming_instance = LogStreamingService(log_repository)
        service = mod._log_streaming_instance

    await service.start()
    return service


def reset_log_streaming_service() -> None:
    """Reset the log streaming service instance (for testing)."""
    with _log_streaming_lock:
        import casare_rpa.infrastructure.logging.log_streaming_service as mod

        mod._log_streaming_instance = None
    logger.debug("Log streaming service reset")


__all__ = [
    "LogStreamingService",
    "get_log_streaming_service",
    "init_log_streaming_service",
    "reset_log_streaming_service",
]
