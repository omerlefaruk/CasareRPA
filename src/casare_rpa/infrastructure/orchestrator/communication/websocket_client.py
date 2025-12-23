"""
WebSocket Client for CasareRPA Robot.
Connects to orchestrator and handles job execution.

The client connects to the FastAPI WebSocket endpoint at:
- ws://host:8000/ws/robot/{robot_id}?api_key={api_key}

For backward compatibility, the legacy standalone server at port 8765
is also supported but deprecated.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Callable, Any, List
import json
import platform

from loguru import logger

try:
    import websockets
    from websockets.asyncio.client import ClientConnection
    from websockets.exceptions import ConnectionClosed

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("websockets not installed. Client features disabled.")

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from casare_rpa.infrastructure.orchestrator.communication.protocol import (
    Message,
    MessageBuilder,
    MessageType,
)


class RobotClient:
    """
    WebSocket client for robot-orchestrator communication.

    Handles:
    - Connection management with auto-reconnect
    - Heartbeat sending
    - Job reception and status reporting
    - Log forwarding
    """

    def __init__(
        self,
        robot_id: str,
        robot_name: str,
        orchestrator_url: str = "wss://api.casare.net/ws/robot",
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        tags: Optional[List[str]] = None,
        auth_token: Optional[str] = None,
        heartbeat_interval: int = 30,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 0,  # 0 = infinite
    ):
        """
        Initialize robot client.

        Args:
            robot_id: Unique robot identifier
            robot_name: Human-readable robot name
            orchestrator_url: WebSocket base URL of orchestrator.
                Default: wss://api.casare.net/ws/robot (production Cloudflare Tunnel).
                The robot_id will be appended to this URL.
                Alternative: ws://localhost:8000/ws/robot (local development)
                Legacy: ws://localhost:8765 (deprecated standalone server)
            environment: Robot environment/pool
            max_concurrent_jobs: Maximum concurrent jobs
            tags: Robot capability tags
            auth_token: Authentication token (passed as api_key query param)
            heartbeat_interval: Seconds between heartbeats
            reconnect_interval: Seconds between reconnection attempts
            max_reconnect_attempts: Max reconnection attempts (0 = infinite)
        """
        if not HAS_WEBSOCKETS:
            raise ImportError("websockets package required. Install with: pip install websockets")

        self.robot_id = robot_id
        self.robot_name = robot_name
        self.orchestrator_url = orchestrator_url
        self.environment = environment
        self.max_concurrent_jobs = max_concurrent_jobs
        self.tags = tags or []
        self.auth_token = auth_token
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts

        # Exponential backoff settings for connection resilience
        self._initial_backoff = 1  # Start with 1 second
        self._max_backoff = 60  # Cap at 60 seconds
        self._backoff_multiplier = 2  # Double each time
        self._current_backoff = self._initial_backoff

        # Connection state
        self._websocket: Optional[ClientConnection] = None
        self._connected = False
        self._running = False
        self._reconnect_count = 0
        self._start_time = datetime.now(timezone.utc)

        # Active jobs
        self._active_jobs: Dict[str, Dict[str, Any]] = {}
        self._paused = False

        # Message handlers
        self._handlers: Dict[MessageType, Callable] = {}
        self._setup_handlers()

        # Event callbacks
        self._on_job_received: Optional[Callable[[Dict], Any]] = None
        self._on_job_cancel: Optional[Callable[[str], Any]] = None
        self._on_connected: Optional[Callable[[], Any]] = None
        self._on_disconnected: Optional[Callable[[], Any]] = None

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

        # Pending responses
        self._pending_responses: Dict[str, asyncio.Future] = {}

        logger.info(f"RobotClient '{robot_name}' ({robot_id}) initialized")

    def set_callbacks(
        self,
        on_job_received: Optional[Callable[[Dict], Any]] = None,
        on_job_cancel: Optional[Callable[[str], Any]] = None,
        on_connected: Optional[Callable[[], Any]] = None,
        on_disconnected: Optional[Callable[[], Any]] = None,
    ):
        """Set event callbacks."""
        self._on_job_received = on_job_received
        self._on_job_cancel = on_job_cancel
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

    def _setup_handlers(self):
        """Setup message handlers."""
        self._handlers = {
            MessageType.REGISTER_ACK: self._handle_register_ack,
            MessageType.HEARTBEAT_ACK: self._handle_heartbeat_ack,
            MessageType.JOB_ASSIGN: self._handle_job_assign,
            MessageType.JOB_CANCEL: self._handle_job_cancel,
            MessageType.STATUS_REQUEST: self._handle_status_request,
            MessageType.PAUSE: self._handle_pause,
            MessageType.RESUME: self._handle_resume,
            MessageType.SHUTDOWN: self._handle_shutdown,
            MessageType.ERROR: self._handle_error,
        }

    async def connect(self) -> bool:
        """
        Connect to orchestrator.

        Returns:
            True if connected successfully
        """
        if self._connected:
            return True

        self._running = True

        # Build connection URL
        # FastAPI endpoint format: ws://host:port/ws/robot/{robot_id}?api_key={token}
        # Legacy format: ws://host:port (robot_id in registration message)
        if "/ws/robot" in self.orchestrator_url:
            # FastAPI endpoint - append robot_id and api_key
            url = f"{self.orchestrator_url}/{self.robot_id}"
            if self.auth_token:
                url = f"{url}?api_key={self.auth_token}"
        else:
            # Legacy standalone server
            url = self.orchestrator_url

        while self._running:
            try:
                logger.info(f"Connecting to orchestrator at {url}")
                self._websocket = await websockets.connect(
                    url,
                    ping_interval=30,
                    ping_timeout=10,
                )

                # Send registration
                await self._register()

                self._connected = True
                self._reconnect_count = 0
<<<<<<< HEAD
                self._current_backoff = (
                    self._initial_backoff
                )  # Reset backoff on success
=======
                self._current_backoff = self._initial_backoff  # Reset backoff on success
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

                # Start background tasks
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                self._receive_task = asyncio.create_task(self._receive_loop())

                logger.info("Connected to orchestrator")

                # Notify callback
                if self._on_connected:
                    try:
                        result = self._on_connected()
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Connected callback error: {e}")

                return True

            except (ConnectionRefusedError, OSError) as e:
                self._reconnect_count += 1
                logger.warning(
                    f"Connection failed (attempt {self._reconnect_count}): {e}. "
                    f"Retrying in {self._current_backoff}s..."
                )

                if (
                    self.max_reconnect_attempts > 0
                    and self._reconnect_count >= self.max_reconnect_attempts
                ):
                    logger.error("Max reconnection attempts reached")
                    self._running = False
                    return False

                # Use exponential backoff
                await asyncio.sleep(self._current_backoff)
                # Increase backoff for next attempt (exponential with cap)
                self._current_backoff = min(
                    self._current_backoff * self._backoff_multiplier, self._max_backoff
                )

            except Exception as e:
                logger.error(f"Connection error: {e}")
                self._running = False
                return False

        return False

    async def disconnect(self, reason: str = "Client disconnecting"):
        """Disconnect from orchestrator."""
        self._running = False
        self._connected = False

        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Send disconnect message
        if self._websocket:
            try:
                await self._send(
                    MessageBuilder.disconnect(
                        robot_id=self.robot_id,
                        reason=reason,
                    )
                )
                await self._websocket.close(1000, reason)
            except Exception:
                pass
            self._websocket = None

        logger.info("Disconnected from orchestrator")

        if self._on_disconnected:
            try:
                result = self._on_disconnected()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Disconnected callback error: {e}")

    async def _register(self):
        """Send registration message."""
        msg = MessageBuilder.register(
            robot_id=self.robot_id,
            robot_name=self.robot_name,
            environment=self.environment,
            max_concurrent_jobs=self.max_concurrent_jobs,
            tags=self.tags,
            capabilities=self._get_capabilities(),
        )

        if self.auth_token:
            msg.payload["auth_token"] = self.auth_token

        await self._send(msg)

    def _get_capabilities(self) -> Dict[str, Any]:
        """Get robot capabilities."""
        caps = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }

        if HAS_PSUTIL:
            caps.update(
                {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                }
            )

        return caps

    async def _send(self, msg: Message):
        """Send message to orchestrator."""
        if not self._websocket:
            return

        try:
            await self._websocket.send(msg.to_json())
        except ConnectionClosed:
            self._connected = False
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def _receive_loop(self):
        """Receive and process messages."""
        try:
            while self._running and self._websocket:
                try:
                    message = await self._websocket.recv()
                    msg = Message.from_json(message)

                    handler = self._handlers.get(msg.type)
                    if handler:
                        await handler(msg)
                    else:
                        logger.warning(f"Unknown message type: {msg.type}")

                except ConnectionClosed:
                    logger.warning("Connection lost")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        finally:
            self._connected = False
            if self._running:
                # Attempt reconnection
                asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        """Attempt to reconnect with exponential backoff."""
        if self._on_disconnected:
            try:
                result = self._on_disconnected()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass

        # Use exponential backoff for reconnection
        logger.info(f"Reconnecting in {self._current_backoff}s...")
        await asyncio.sleep(self._current_backoff)

        # Increase backoff for next attempt
        self._current_backoff = min(
            self._current_backoff * self._backoff_multiplier, self._max_backoff
        )

        if self._running:
            await self.connect()

    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._running and self._connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_heartbeat(self):
        """Send heartbeat message."""
        status = "paused" if self._paused else "online"
        if len(self._active_jobs) >= self.max_concurrent_jobs:
            status = "busy"

        cpu_percent = 0.0
        memory_percent = 0.0
        disk_percent = 0.0

        if HAS_PSUTIL:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

        await self._send(
            MessageBuilder.heartbeat(
                robot_id=self.robot_id,
                status=status,
                current_jobs=len(self._active_jobs),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                active_job_ids=list(self._active_jobs.keys()),
            )
        )

    # ==================== MESSAGE HANDLERS ====================

    async def _handle_register_ack(self, msg: Message):
        """Handle registration acknowledgment."""
        payload = msg.payload
        if payload.get("success"):
            logger.info("Registration acknowledged by orchestrator")
            # Apply any config from orchestrator
            config = payload.get("config", {})
            if "heartbeat_interval" in config:
                self.heartbeat_interval = config["heartbeat_interval"]
        else:
            logger.error(f"Registration failed: {payload.get('message')}")
            await self.disconnect("Registration failed")

    async def _handle_heartbeat_ack(self, msg: Message):
        """Handle heartbeat acknowledgment."""
        pass  # Just confirms heartbeat received

    async def _handle_job_assign(self, msg: Message):
        """Handle job assignment."""
        payload = msg.payload
        job_id = payload.get("job_id")

        logger.info(f"Job assignment received: {job_id[:8]}")

        # Check if we can accept
        if self._paused:
            await self._send(
                MessageBuilder.job_reject(
                    job_id=job_id,
                    robot_id=self.robot_id,
                    reason="Robot is paused",
                    correlation_id=msg.id,
                )
            )
            return

        if len(self._active_jobs) >= self.max_concurrent_jobs:
            await self._send(
                MessageBuilder.job_reject(
                    job_id=job_id,
                    robot_id=self.robot_id,
                    reason="Maximum concurrent jobs reached",
                    correlation_id=msg.id,
                )
            )
            return

        # Accept the job
        self._active_jobs[job_id] = {
            "job_id": job_id,
            "workflow_id": payload.get("workflow_id"),
            "workflow_name": payload.get("workflow_name"),
            "workflow_json": payload.get("workflow_json"),
            "priority": payload.get("priority"),
            "timeout_seconds": payload.get("timeout_seconds"),
            "parameters": payload.get("parameters", {}),
            "started_at": datetime.now(timezone.utc),
        }

        await self._send(
            MessageBuilder.job_accept(
                job_id=job_id,
                robot_id=self.robot_id,
                correlation_id=msg.id,
            )
        )

        # Notify callback
        if self._on_job_received:
            try:
                result = self._on_job_received(self._active_jobs[job_id])
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Job received callback error: {e}")
                # Report failure
                await self.report_job_failed(job_id, str(e))

    async def _handle_job_cancel(self, msg: Message):
        """Handle job cancellation request."""
        job_id = msg.payload.get("job_id")
        reason = msg.payload.get("reason", "Cancelled by orchestrator")

        logger.info(f"Job cancellation requested: {job_id[:8]} - {reason}")

        if job_id in self._active_jobs:
            # Notify callback
            if self._on_job_cancel:
                try:
                    result = self._on_job_cancel(job_id)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Job cancel callback error: {e}")

            # Remove from active jobs
            self._active_jobs.pop(job_id, None)

        await self._send(
            MessageBuilder.job_cancelled(
                job_id=job_id,
                robot_id=self.robot_id,
                correlation_id=msg.id,
            )
        )

    async def _handle_status_request(self, msg: Message):
        """Handle status request."""
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        system_info = {}
        if HAS_PSUTIL:
            system_info = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }

        await self._send(
            MessageBuilder.status_response(
                robot_id=self.robot_id,
                status="paused" if self._paused else "online",
                current_jobs=len(self._active_jobs),
                active_job_ids=list(self._active_jobs.keys()),
                uptime_seconds=int(uptime),
                system_info=system_info,
                correlation_id=msg.id,
            )
        )

    async def _handle_pause(self, msg: Message):
        """Handle pause command."""
        logger.info("Received pause command")
        self._paused = True

    async def _handle_resume(self, msg: Message):
        """Handle resume command."""
        logger.info("Received resume command")
        self._paused = False

    async def _handle_shutdown(self, msg: Message):
        """Handle shutdown command."""
        graceful = msg.payload.get("graceful", True)
        logger.info(f"Received shutdown command (graceful={graceful})")

        if graceful:
            # Wait for active jobs to complete
            self._paused = True
            # Let caller handle actual shutdown
        else:
            await self.disconnect("Shutdown requested")

    async def _handle_error(self, msg: Message):
        """Handle error message."""
        error_code = msg.payload.get("error_code")
        error_message = msg.payload.get("error_message")
        logger.error(f"Received error from orchestrator: [{error_code}] {error_message}")

    # ==================== PUBLIC API ====================

    async def report_progress(
        self, job_id: str, progress: int, current_node: str = "", message: str = ""
    ):
        """
        Report job progress to orchestrator.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_node: Current node being executed
            message: Optional status message
        """
        await self._send(
            MessageBuilder.job_progress(
                job_id=job_id,
                robot_id=self.robot_id,
                progress=progress,
                current_node=current_node,
                message=message,
            )
        )

    async def report_job_complete(self, job_id: str, result: Optional[Dict[str, Any]] = None):
        """
        Report job completion to orchestrator.

        Args:
            job_id: Job ID
            result: Job result data
        """
        job_info = self._active_jobs.pop(job_id, None)
        duration_ms = 0
        if job_info:
            duration_ms = int(
                (datetime.now(timezone.utc) - job_info["started_at"]).total_seconds() * 1000
            )

        await self._send(
            MessageBuilder.job_complete(
                job_id=job_id,
                robot_id=self.robot_id,
                result=result or {},
                duration_ms=duration_ms,
            )
        )

        logger.info(f"Job {job_id[:8]} completed")

    async def report_job_failed(
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
            error_type: Error type/category
            stack_trace: Stack trace if available
            failed_node: Node that failed
        """
        self._active_jobs.pop(job_id, None)

        await self._send(
            MessageBuilder.job_failed(
                job_id=job_id,
                robot_id=self.robot_id,
                error_message=error_message,
                error_type=error_type,
                stack_trace=stack_trace,
                failed_node=failed_node,
            )
        )

        logger.error(f"Job {job_id[:8]} failed: {error_message}")

    async def send_log(
        self,
        job_id: str,
        level: str,
        message: str,
        node_id: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Send log entry to orchestrator.

        Args:
            job_id: Job ID
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            node_id: Associated node ID
            extra: Additional data
        """
        await self._send(
            MessageBuilder.log_entry(
                job_id=job_id,
                robot_id=self.robot_id,
                level=level,
                message=message,
                node_id=node_id,
                extra=extra,
            )
        )

    async def send_log_batch(self, job_id: str, entries: List[Dict[str, Any]]):
        """
        Send batch of log entries.

        Args:
            job_id: Job ID
            entries: List of log entries
        """
        await self._send(
            MessageBuilder.log_batch(
                job_id=job_id,
                robot_id=self.robot_id,
                entries=entries,
            )
        )

    @property
    def is_connected(self) -> bool:
        """Check if connected to orchestrator."""
        return self._connected

    @property
    def is_paused(self) -> bool:
        """Check if robot is paused."""
        return self._paused

    @property
    def active_job_count(self) -> int:
        """Get count of active jobs."""
        return len(self._active_jobs)

    @property
    def is_available(self) -> bool:
        """Check if robot can accept more jobs."""
        return (
            self._connected
            and not self._paused
            and len(self._active_jobs) < self.max_concurrent_jobs
        )

    def get_active_jobs(self) -> List[str]:
        """Get list of active job IDs."""
        return list(self._active_jobs.keys())
