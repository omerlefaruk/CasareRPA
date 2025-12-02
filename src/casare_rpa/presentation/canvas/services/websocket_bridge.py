"""
WebSocket Bridge Service for Fleet Dashboard.

Bridges async WebSocket events from OrchestratorClient to Qt signals
for thread-safe UI updates. Implements exponential backoff reconnection.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.infrastructure.orchestrator.client import OrchestratorClient


@dataclass
class RobotStatusUpdate:
    """Real-time robot status update."""

    robot_id: str
    status: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    current_job: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class JobStatusUpdate:
    """Real-time job status update."""

    job_id: str
    status: str
    progress: int = 0
    current_node: str = ""
    error_message: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class QueueMetricsUpdate:
    """Real-time queue metrics update."""

    depth: int
    active_jobs: int = 0
    completed_today: int = 0
    failed_today: int = 0
    timestamp: Optional[datetime] = None


class WebSocketBridge(QObject):
    """
    Bridge between async WebSocket events and Qt signals.

    Features:
    - Converts OrchestratorClient callbacks to Qt signals
    - Thread-safe signal emission for UI updates
    - Exponential backoff reconnection (1s, 2s, 4s, 8s, max 60s)
    - Automatic reconnection on disconnect
    - Connection status tracking

    Usage:
        bridge = WebSocketBridge()
        bridge.robot_status_changed.connect(on_robot_update)
        await bridge.connect(orchestrator_client)
    """

    # Qt signals for UI updates
    robot_status_changed = Signal(object)  # RobotStatusUpdate
    job_status_changed = Signal(object)  # JobStatusUpdate
    queue_metrics_changed = Signal(object)  # QueueMetricsUpdate
    connection_status_changed = Signal(bool)  # connected: bool
    connection_error = Signal(str)  # error message

    # Batch signals for bulk updates
    robots_batch_updated = Signal(list)  # List[RobotStatusUpdate]
    jobs_batch_updated = Signal(list)  # List[JobStatusUpdate]

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize WebSocket bridge."""
        super().__init__(parent)

        self._client: Optional["OrchestratorClient"] = None
        self._connected = False
        self._reconnect_attempt = 0
        self._max_reconnect_delay = 60  # seconds
        self._base_reconnect_delay = 1  # seconds

        # Batch updates for efficiency
        self._robot_batch: List[RobotStatusUpdate] = []
        self._job_batch: List[JobStatusUpdate] = []

        # Batch flush timer (emit batched updates every 500ms)
        self._batch_timer = QTimer(self)
        self._batch_timer.setInterval(500)
        self._batch_timer.timeout.connect(self._flush_batches)

        # Reconnection timer
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)

        logger.debug("WebSocketBridge initialized")

    @property
    def is_connected(self) -> bool:
        """Check if bridge is connected to WebSocket."""
        return self._connected

    async def connect(self, client: "OrchestratorClient") -> bool:
        """
        Connect bridge to OrchestratorClient and start receiving events.

        Args:
            client: OrchestratorClient instance

        Returns:
            True if connected successfully
        """
        self._client = client

        # Register callbacks
        client.on("robot_status", self._on_robot_status)
        client.on("job_update", self._on_job_update)
        client.on("queue_metrics", self._on_queue_metrics)
        client.on("connected", self._on_connected)
        client.on("disconnected", self._on_disconnected)
        client.on("error", self._on_error)

        # Connect to orchestrator
        connected = await client.connect()

        if connected:
            self._connected = True
            self._reconnect_attempt = 0
            self.connection_status_changed.emit(True)
            self._batch_timer.start()

            # Start WebSocket subscriptions
            await client.subscribe_live_updates()

            logger.info("WebSocketBridge connected")
            return True
        else:
            self._connected = False
            self.connection_status_changed.emit(False)
            self._schedule_reconnect()
            return False

    async def disconnect(self) -> None:
        """Disconnect bridge from WebSocket."""
        self._batch_timer.stop()
        self._reconnect_timer.stop()

        if self._client:
            # Unregister callbacks
            self._client.off("robot_status", self._on_robot_status)
            self._client.off("job_update", self._on_job_update)
            self._client.off("queue_metrics", self._on_queue_metrics)
            self._client.off("connected", self._on_connected)
            self._client.off("disconnected", self._on_disconnected)
            self._client.off("error", self._on_error)

            await self._client.disconnect()
            self._client = None

        self._connected = False
        self.connection_status_changed.emit(False)
        logger.info("WebSocketBridge disconnected")

    def _on_robot_status(self, data: Dict[str, Any]) -> None:
        """Handle robot status update from WebSocket."""
        update = RobotStatusUpdate(
            robot_id=data.get("robot_id", ""),
            status=data.get("status", "offline"),
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_mb=data.get("memory_mb", 0.0),
            current_job=data.get("current_job"),
            timestamp=datetime.now(),
        )

        # Add to batch for efficient UI updates
        self._robot_batch.append(update)

        # Also emit individual signal for immediate handling
        self.robot_status_changed.emit(update)

    def _on_job_update(self, data: Dict[str, Any]) -> None:
        """Handle job status update from WebSocket."""
        update = JobStatusUpdate(
            job_id=data.get("job_id", ""),
            status=data.get("status", "pending"),
            progress=data.get("progress", 0),
            current_node=data.get("current_node", ""),
            error_message=data.get("error_message", ""),
            timestamp=datetime.now(),
        )

        # Add to batch
        self._job_batch.append(update)

        # Emit individual signal
        self.job_status_changed.emit(update)

    def _on_queue_metrics(self, data: Dict[str, Any]) -> None:
        """Handle queue metrics update from WebSocket."""
        update = QueueMetricsUpdate(
            depth=data.get("depth", 0),
            active_jobs=data.get("active_jobs", 0),
            completed_today=data.get("completed_today", 0),
            failed_today=data.get("failed_today", 0),
            timestamp=datetime.now(),
        )

        self.queue_metrics_changed.emit(update)

    def _on_connected(self, data: Dict[str, Any]) -> None:
        """Handle WebSocket connected event."""
        self._connected = True
        self._reconnect_attempt = 0
        self.connection_status_changed.emit(True)
        self._batch_timer.start()
        logger.info("WebSocket connected")

    def _on_disconnected(self, data: Dict[str, Any]) -> None:
        """Handle WebSocket disconnected event."""
        self._connected = False
        self.connection_status_changed.emit(False)
        self._batch_timer.stop()
        self._schedule_reconnect()
        logger.warning("WebSocket disconnected, scheduling reconnect")

    def _on_error(self, data: Dict[str, Any]) -> None:
        """Handle WebSocket error event."""
        error = data.get("error", "Unknown error")
        self.connection_error.emit(error)
        logger.error(f"WebSocket error: {error}")

    def _flush_batches(self) -> None:
        """Flush batched updates to UI."""
        if self._robot_batch:
            self.robots_batch_updated.emit(self._robot_batch.copy())
            self._robot_batch.clear()

        if self._job_batch:
            self.jobs_batch_updated.emit(self._job_batch.copy())
            self._job_batch.clear()

    def _schedule_reconnect(self) -> None:
        """Schedule reconnection with exponential backoff."""
        if self._reconnect_timer.isActive():
            return

        delay = min(
            self._base_reconnect_delay * (2**self._reconnect_attempt),
            self._max_reconnect_delay,
        )

        self._reconnect_attempt += 1
        self._reconnect_timer.start(int(delay * 1000))

        logger.info(
            f"Reconnection scheduled in {delay}s (attempt {self._reconnect_attempt})"
        )

    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to WebSocket."""
        if not self._client:
            return

        # Create async task for reconnection
        import qasync

        try:
            loop = qasync.QEventLoop.running_loop()
            if loop:
                asyncio.ensure_future(self._reconnect_async())
        except RuntimeError:
            logger.warning("No event loop available for reconnection")

    async def _reconnect_async(self) -> None:
        """Async reconnection handler."""
        if not self._client:
            return

        logger.info("Attempting WebSocket reconnection...")

        try:
            connected = await self._client.connect()

            if connected:
                self._connected = True
                self._reconnect_attempt = 0
                self.connection_status_changed.emit(True)
                self._batch_timer.start()

                await self._client.subscribe_live_updates()
                logger.info("Reconnected successfully")
            else:
                self._schedule_reconnect()

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self._schedule_reconnect()


# Singleton instance
_bridge: Optional[WebSocketBridge] = None


def get_websocket_bridge() -> WebSocketBridge:
    """Get or create singleton WebSocketBridge."""
    global _bridge
    if _bridge is None:
        _bridge = WebSocketBridge()
    return _bridge


__all__ = [
    "WebSocketBridge",
    "RobotStatusUpdate",
    "JobStatusUpdate",
    "QueueMetricsUpdate",
    "get_websocket_bridge",
]
