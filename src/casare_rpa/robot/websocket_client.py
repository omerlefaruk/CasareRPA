"""
WebSocket client for Robot to connect to CasareRPA Orchestrator.

Provides resilient connection with auto-reconnect and message handling.
"""

import asyncio
from typing import Optional, Callable, Any, Set
import platform
import psutil

from loguru import logger

try:
    import websockets
    from websockets.asyncio.client import ClientConnection
    from websockets.exceptions import ConnectionClosed

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("websockets not installed. WebSocket client disabled.")

from casare_rpa.orchestrator.protocol import (
    Message,
    MessageType,
    MessageBuilder,
)


class RobotWebSocketClient:
    """
    WebSocket client for robot-orchestrator communication.

    Features:
    - Auto-reconnect with exponential backoff
    - Heartbeat management
    - Job acceptance/rejection
    - Progress reporting
    - Graceful shutdown
    """

    def __init__(
        self,
        robot_id: str,
        robot_name: str,
        orchestrator_url: str = "ws://localhost:8765",
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        reconnect_delay: float = 5.0,
        max_reconnect_delay: float = 60.0,
        heartbeat_interval: float = 30.0,
    ):
        """
        Initialize WebSocket client.

        Args:
            robot_id: Unique robot identifier
            robot_name: Human-readable robot name
            orchestrator_url: WebSocket URL of orchestrator
            environment: Robot environment/pool
            max_concurrent_jobs: Maximum concurrent jobs
            reconnect_delay: Initial reconnect delay in seconds
            max_reconnect_delay: Maximum reconnect delay
            heartbeat_interval: Seconds between heartbeats
        """
        if not HAS_WEBSOCKETS:
            raise ImportError(
                "websockets package required. Install with: pip install websockets"
            )

        self.robot_id = robot_id
        self.robot_name = robot_name
        self.orchestrator_url = orchestrator_url
        self.environment = environment
        self.max_concurrent_jobs = max_concurrent_jobs

        # Connection settings
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._heartbeat_interval = heartbeat_interval

        # State
        self._ws: Optional[ClientConnection] = None
        self._connected = False
        self._running = False
        self._active_jobs: Set[str] = set()

        # Callbacks
        self._on_job_assigned: Optional[Callable[[dict], Any]] = None
        self._on_job_cancelled: Optional[Callable[[str, str], Any]] = None
        self._on_connected: Optional[Callable[[], Any]] = None
        self._on_disconnected: Optional[Callable[[], Any]] = None

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._listen_task: Optional[asyncio.Task] = None

        # Server config (received on registration)
        self._server_config: dict = {}

        logger.info(f"RobotWebSocketClient initialized for {robot_name} ({robot_id})")

    def set_callbacks(
        self,
        on_job_assigned: Optional[Callable[[dict], Any]] = None,
        on_job_cancelled: Optional[Callable[[str, str], Any]] = None,
        on_connected: Optional[Callable[[], Any]] = None,
        on_disconnected: Optional[Callable[[], Any]] = None,
    ):
        """Set event callbacks."""
        self._on_job_assigned = on_job_assigned
        self._on_job_cancelled = on_job_cancelled
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

    @property
    def is_connected(self) -> bool:
        """Check if connected to orchestrator."""
        return self._connected and self._ws is not None

    @property
    def current_job_count(self) -> int:
        """Get number of active jobs."""
        return len(self._active_jobs)

    @property
    def is_available(self) -> bool:
        """Check if robot can accept more jobs."""
        return self._connected and len(self._active_jobs) < self.max_concurrent_jobs

    async def connect(self):
        """
        Connect to orchestrator with auto-reconnect.

        This method blocks while connected and automatically
        reconnects if the connection drops.
        """
        self._running = True
        delay = self._reconnect_delay

        while self._running:
            try:
                logger.info(f"Connecting to orchestrator at {self.orchestrator_url}")

                self._ws = await websockets.connect(
                    self.orchestrator_url,
                    ping_interval=30,
                    ping_timeout=10,
                )

                # Register with orchestrator
                if await self._register():
                    self._connected = True
                    delay = self._reconnect_delay  # Reset delay on success

                    # Notify callback
                    if self._on_connected:
                        try:
                            result = self._on_connected()
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"on_connected callback error: {e}")

                    # Start background tasks
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                    # Listen for messages (blocking)
                    await self._listen()
                else:
                    logger.error("Registration failed")
                    await self._ws.close()

            except ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            finally:
                await self._cleanup_connection()

            if not self._running:
                break

            # Wait before reconnecting
            logger.info(f"Reconnecting in {delay:.1f}s...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, self._max_reconnect_delay)

    async def _register(self) -> bool:
        """Register with orchestrator."""
        msg = MessageBuilder.register(
            robot_id=self.robot_id,
            robot_name=self.robot_name,
            environment=self.environment,
            max_concurrent_jobs=self.max_concurrent_jobs,
            tags=[],
            capabilities={
                "browser": True,
                "desktop": platform.system() == "Windows",
                "python_version": platform.python_version(),
            },
        )

        await self._send(msg)

        # Wait for acknowledgment
        try:
            response = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
            ack = Message.from_json(response)

            if ack.type == MessageType.REGISTER_ACK:
                if ack.payload.get("success"):
                    self._server_config = ack.payload.get("config", {})
                    logger.info(
                        f"Registered with orchestrator: {ack.payload.get('message')}"
                    )
                    return True
                else:
                    logger.error(f"Registration rejected: {ack.payload.get('message')}")
                    return False
        except asyncio.TimeoutError:
            logger.error("Registration timeout")
            return False

        return False

    async def _listen(self):
        """Listen for messages from orchestrator."""
        async for message in self._ws:
            try:
                msg = Message.from_json(message)
                await self._handle_message(msg)
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def _handle_message(self, msg: Message):
        """Handle incoming message from orchestrator."""
        if msg.type == MessageType.JOB_ASSIGN:
            await self._handle_job_assign(msg)
        elif msg.type == MessageType.JOB_CANCEL:
            await self._handle_job_cancel(msg)
        elif msg.type == MessageType.HEARTBEAT_ACK:
            pass  # Acknowledgment received
        elif msg.type == MessageType.STATUS_REQUEST:
            await self._handle_status_request(msg)
        elif msg.type == MessageType.PAUSE:
            logger.info("Received pause command")
        elif msg.type == MessageType.RESUME:
            logger.info("Received resume command")
        elif msg.type == MessageType.SHUTDOWN:
            logger.info("Received shutdown command")
            graceful = msg.payload.get("graceful", True)
            if graceful:
                await self.disconnect("Shutdown requested by orchestrator")
            else:
                self._running = False
        elif msg.type == MessageType.ERROR:
            logger.error(f"Error from orchestrator: {msg.payload.get('error_message')}")
        else:
            logger.debug(f"Unhandled message type: {msg.type}")

    async def _handle_job_assign(self, msg: Message):
        """Handle job assignment from orchestrator."""
        payload = msg.payload
        job_id = payload.get("job_id")

        # Check if we can accept
        if not self.is_available:
            # Reject job
            reject_msg = MessageBuilder.job_reject(
                job_id=job_id,
                robot_id=self.robot_id,
                reason="Robot at capacity",
                correlation_id=msg.id,
            )
            await self._send(reject_msg)
            logger.warning(f"Rejected job {job_id[:8]}: at capacity")
            return

        # Accept job
        self._active_jobs.add(job_id)

        accept_msg = MessageBuilder.job_accept(
            job_id=job_id,
            robot_id=self.robot_id,
            correlation_id=msg.id,
        )
        await self._send(accept_msg)
        logger.info(f"Accepted job {job_id[:8]}")

        # Notify callback
        if self._on_job_assigned:
            try:
                result = self._on_job_assigned(payload)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Job assigned callback error: {e}")
                # Report failure
                await self.send_job_failed(job_id, str(e))

    async def _handle_job_cancel(self, msg: Message):
        """Handle job cancellation request."""
        job_id = msg.payload.get("job_id")
        reason = msg.payload.get("reason", "")

        if job_id in self._active_jobs:
            # Notify callback
            if self._on_job_cancelled:
                try:
                    result = self._on_job_cancelled(job_id, reason)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Job cancelled callback error: {e}")

            self._active_jobs.discard(job_id)

            # Confirm cancellation
            cancel_msg = MessageBuilder.job_cancelled(
                job_id=job_id,
                robot_id=self.robot_id,
                correlation_id=msg.id,
            )
            await self._send(cancel_msg)
            logger.info(f"Cancelled job {job_id[:8]}: {reason}")

    async def _handle_status_request(self, msg: Message):
        """Handle status request from orchestrator."""
        response = MessageBuilder.status_response(
            robot_id=self.robot_id,
            status="online" if self._connected else "offline",
            current_jobs=len(self._active_jobs),
            active_job_ids=list(self._active_jobs),
            uptime_seconds=0,  # Could track actual uptime
            system_info=self._get_system_info(),
            correlation_id=msg.id,
        )
        await self._send(response)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._running and self._connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self._connected:
                    await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_heartbeat(self):
        """Send heartbeat to orchestrator."""
        info = self._get_system_info()

        msg = MessageBuilder.heartbeat(
            robot_id=self.robot_id,
            status="online",
            current_jobs=len(self._active_jobs),
            cpu_percent=info.get("cpu_percent", 0),
            memory_percent=info.get("memory_percent", 0),
            disk_percent=info.get("disk_percent", 0),
            active_job_ids=list(self._active_jobs),
        )
        await self._send(msg)

    def _get_system_info(self) -> dict:
        """Get system resource information."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent
                if platform.system() != "Windows"
                else psutil.disk_usage("C:\\").percent,
                "platform": platform.system(),
                "python_version": platform.python_version(),
            }
        except Exception:
            return {}

    async def _cleanup_connection(self):
        """Clean up after connection loss."""
        self._connected = False

        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Notify callback
        if self._on_disconnected:
            try:
                result = self._on_disconnected()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"on_disconnected callback error: {e}")

    async def _send(self, msg: Message):
        """Send message to orchestrator."""
        if self._ws:
            try:
                await self._ws.send(msg.to_json())
            except Exception as e:
                logger.error(f"Send error: {e}")
                raise

    # ==================== PUBLIC API ====================

    async def send_job_progress(
        self, job_id: str, progress: int, current_node: str = "", message: str = ""
    ):
        """
        Report job progress to orchestrator.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_node: Current node being executed
            message: Progress message
        """
        if not self._connected:
            return

        msg = MessageBuilder.job_progress(
            job_id=job_id,
            robot_id=self.robot_id,
            progress=progress,
            current_node=current_node,
            message=message,
        )
        await self._send(msg)

    async def send_job_complete(
        self, job_id: str, result: Optional[dict] = None, duration_ms: int = 0
    ):
        """
        Report job completion to orchestrator.

        Args:
            job_id: Job ID
            result: Job result data
            duration_ms: Job duration in milliseconds
        """
        self._active_jobs.discard(job_id)

        if not self._connected:
            logger.warning(f"Cannot report completion for {job_id}: not connected")
            return

        msg = MessageBuilder.job_complete(
            job_id=job_id,
            robot_id=self.robot_id,
            result=result or {},
            duration_ms=duration_ms,
        )
        await self._send(msg)
        logger.info(f"Reported job {job_id[:8]} complete")

    async def send_job_failed(
        self,
        job_id: str,
        error_message: str,
        error_type: str = "ExecutionError",
        stack_trace: str = "",
        failed_node: str = "",
    ):
        """
        Report job failure to orchestrator.

        Args:
            job_id: Job ID
            error_message: Error description
            error_type: Error type/class
            stack_trace: Stack trace if available
            failed_node: Node that failed
        """
        self._active_jobs.discard(job_id)

        if not self._connected:
            logger.warning(f"Cannot report failure for {job_id}: not connected")
            return

        msg = MessageBuilder.job_failed(
            job_id=job_id,
            robot_id=self.robot_id,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            failed_node=failed_node,
        )
        await self._send(msg)
        logger.error(f"Reported job {job_id[:8]} failed: {error_message}")

    async def send_log_entry(
        self, job_id: str, level: str, message: str, node_id: str = ""
    ):
        """Send log entry to orchestrator."""
        if not self._connected:
            return

        msg = MessageBuilder.log_entry(
            job_id=job_id,
            robot_id=self.robot_id,
            level=level,
            message=message,
            node_id=node_id,
        )
        await self._send(msg)

    async def disconnect(self, reason: str = ""):
        """
        Gracefully disconnect from orchestrator.

        Args:
            reason: Disconnect reason
        """
        self._running = False

        if self._ws and self._connected:
            # Send disconnect message
            msg = MessageBuilder.disconnect(
                robot_id=self.robot_id,
                reason=reason,
            )
            try:
                await self._send(msg)
                await self._ws.close(1000, reason or "Client disconnecting")
            except Exception:
                pass

        await self._cleanup_connection()
        logger.info(f"Disconnected from orchestrator: {reason}")

    def mark_job_active(self, job_id: str):
        """Mark a job as active (for tracking)."""
        self._active_jobs.add(job_id)

    def mark_job_complete(self, job_id: str):
        """Mark a job as complete (for tracking)."""
        self._active_jobs.discard(job_id)
