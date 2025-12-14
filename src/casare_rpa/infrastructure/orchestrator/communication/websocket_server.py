"""
WebSocket Server for CasareRPA Orchestrator.
Handles robot connections and message routing.

DEPRECATED: This standalone websockets server is deprecated in favor of the
FastAPI WebSocket handlers in `websocket_handlers.py`. The FastAPI handlers
provide the same functionality on the main API server (port 8000) at:
- /ws/robot/{robot_id} - Robot registration, heartbeats, job updates
- /ws/admin - Admin dashboard updates
- /ws/logs/{robot_id} - Log streaming

Migration:
1. Update robot client to connect to ws://host:8000/ws/robot/{robot_id}
2. Remove OrchestratorEngine.start_server() calls
3. Use the FastAPI app with websocket_handlers router instead

This module will be removed in v3.0.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Set, Callable, Any, List
import json

from loguru import logger

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    from websockets.exceptions import ConnectionClosed

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("websockets not installed. Server features disabled.")

from casare_rpa.infrastructure.orchestrator.communication.models import (
    Job,
    Robot,
    RobotStatus,
)
from casare_rpa.infrastructure.orchestrator.communication.protocol import (
    Message,
    MessageBuilder,
    MessageType,
)


class RobotConnection:
    """Represents a connected robot."""

    def __init__(
        self,
        websocket: "WebSocketServerProtocol",
        robot_id: str,
        robot_name: str,
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        tags: Optional[List[str]] = None,
    ):
        self.websocket = websocket
        self.robot_id = robot_id
        self.robot_name = robot_name
        self.environment = environment
        self.max_concurrent_jobs = max_concurrent_jobs
        self.tags = tags or []
        self.connected_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.current_jobs: Set[str] = set()
        self.status = RobotStatus.ONLINE
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.disk_percent = 0.0

    @property
    def is_available(self) -> bool:
        """Check if robot can accept more jobs."""
        return (
            self.status == RobotStatus.ONLINE
            and len(self.current_jobs) < self.max_concurrent_jobs
        )

    def to_robot(self) -> Robot:
        """Convert to Robot model."""
        return Robot(
            id=self.robot_id,
            name=self.robot_name,
            status=self.status,
            environment=self.environment,
            max_concurrent_jobs=self.max_concurrent_jobs,
            current_jobs=len(self.current_jobs),
            last_seen=datetime.now(timezone.utc),
            last_heartbeat=self.last_heartbeat,
            tags=self.tags,
        )


class OrchestratorServer:
    """
    WebSocket server for robot communication.

    DEPRECATED: Use FastAPI WebSocket handlers instead.
    See module docstring for migration instructions.

    Handles:
    - Robot registration and authentication
    - Job distribution
    - Progress updates
    - Health monitoring
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        heartbeat_timeout: int = 60,
        auth_token: Optional[str] = None,
    ):
        """
        Initialize orchestrator server.

        DEPRECATED: This standalone server is deprecated. Use FastAPI WebSocket
        handlers at /ws/robot/{robot_id} instead. This class will be removed in v3.0.

        Args:
            host: Server bind address
            port: Server port
            heartbeat_timeout: Seconds before marking robot offline
            auth_token: Optional authentication token
        """
        import warnings

        warnings.warn(
            "OrchestratorServer is deprecated. Use FastAPI WebSocket handlers at "
            "/ws/robot/{robot_id} instead. This class will be removed in v3.0.",
            DeprecationWarning,
            stacklevel=2,
        )

        if not HAS_WEBSOCKETS:
            raise ImportError(
                "websockets package required. Install with: pip install websockets"
            )

        self._host = host
        self._port = port
        self._heartbeat_timeout = heartbeat_timeout
        self._auth_token = auth_token

        # Connected robots: robot_id -> RobotConnection
        self._connections: Dict[str, RobotConnection] = {}

        # Websocket -> robot_id mapping for quick lookup
        self._ws_to_robot: Dict[WebSocketServerProtocol, str] = {}

        # Pending responses: correlation_id -> Future
        self._pending_responses: Dict[str, asyncio.Future] = {}

        # Message handlers
        self._handlers: Dict[MessageType, Callable] = {}
        self._setup_handlers()

        # Event callbacks
        self._on_robot_connect: Optional[Callable[[Robot], Any]] = None
        self._on_robot_disconnect: Optional[Callable[[str], Any]] = None
        self._on_job_progress: Optional[Callable[[str, int, str], Any]] = None
        self._on_job_complete: Optional[Callable[[str, Dict], Any]] = None
        self._on_job_failed: Optional[Callable[[str, str], Any]] = None
        self._on_log_entry: Optional[Callable[[str, str, str, str], Any]] = None

        # Server state
        self._server = None
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info(f"OrchestratorServer initialized on {host}:{port}")

    def set_callbacks(
        self,
        on_robot_connect: Optional[Callable[[Robot], Any]] = None,
        on_robot_disconnect: Optional[Callable[[str], Any]] = None,
        on_job_progress: Optional[Callable[[str, int, str], Any]] = None,
        on_job_complete: Optional[Callable[[str, Dict], Any]] = None,
        on_job_failed: Optional[Callable[[str, str], Any]] = None,
        on_log_entry: Optional[Callable[[str, str, str, str], Any]] = None,
    ):
        """Set event callbacks."""
        self._on_robot_connect = on_robot_connect
        self._on_robot_disconnect = on_robot_disconnect
        self._on_job_progress = on_job_progress
        self._on_job_complete = on_job_complete
        self._on_job_failed = on_job_failed
        self._on_log_entry = on_log_entry

    def _setup_handlers(self):
        """Setup message handlers."""
        self._handlers = {
            MessageType.REGISTER: self._handle_register,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.DISCONNECT: self._handle_disconnect,
            MessageType.JOB_ACCEPT: self._handle_job_accept,
            MessageType.JOB_REJECT: self._handle_job_reject,
            MessageType.JOB_PROGRESS: self._handle_job_progress,
            MessageType.JOB_COMPLETE: self._handle_job_complete,
            MessageType.JOB_FAILED: self._handle_job_failed,
            MessageType.JOB_CANCELLED: self._handle_job_cancelled,
            MessageType.STATUS_RESPONSE: self._handle_status_response,
            MessageType.LOG_ENTRY: self._handle_log_entry,
            MessageType.LOG_BATCH: self._handle_log_batch,
        }

    async def start(self):
        """Start the WebSocket server."""
        if self._running:
            return

        self._server = await websockets.serve(
            self._handle_connection,
            self._host,
            self._port,
            ping_interval=30,
            ping_timeout=10,
        )

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(f"OrchestratorServer started on ws://{self._host}:{self._port}")

    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False

        # Cancel health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for conn in list(self._connections.values()):
            try:
                await conn.websocket.close(1001, "Server shutting down")
            except Exception:
                pass

        self._connections.clear()
        self._ws_to_robot.clear()

        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("OrchestratorServer stopped")

    async def _handle_connection(self, websocket: "WebSocketServerProtocol"):
        """Handle new WebSocket connection."""
        robot_id = None
        try:
            async for message in websocket:
                try:
                    msg = Message.from_json(message)
                    robot_id = self._ws_to_robot.get(websocket)

                    # Handle message
                    handler = self._handlers.get(msg.type)
                    if handler:
                        await handler(websocket, msg)
                    else:
                        logger.warning(f"Unknown message type: {msg.type}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
                    await self._send_error(websocket, "INVALID_JSON", str(e))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(websocket, "HANDLER_ERROR", str(e))

        except ConnectionClosed as e:
            logger.debug(f"Connection closed: {e}")
        finally:
            # Clean up connection
            if robot_id:
                await self._remove_connection(robot_id)

    async def _handle_register(self, websocket: WebSocketServerProtocol, msg: Message):
        """Handle robot registration."""
        payload = msg.payload
        robot_id = payload.get("robot_id")
        robot_name = payload.get("robot_name", robot_id)

        # Check authentication if required
        if self._auth_token:
            token = payload.get("auth_token")
            if token != self._auth_token:
                await self._send(
                    websocket,
                    MessageBuilder.register_ack(
                        robot_id=robot_id,
                        success=False,
                        message="Authentication failed",
                        correlation_id=msg.id,
                    ),
                )
                await websocket.close(4001, "Authentication failed")
                return

        # Create connection
        conn = RobotConnection(
            websocket=websocket,
            robot_id=robot_id,
            robot_name=robot_name,
            environment=payload.get("environment", "default"),
            max_concurrent_jobs=payload.get("max_concurrent_jobs", 1),
            tags=payload.get("tags", []),
        )

        # Register
        self._connections[robot_id] = conn
        self._ws_to_robot[websocket] = robot_id

        # Send acknowledgment
        await self._send(
            websocket,
            MessageBuilder.register_ack(
                robot_id=robot_id,
                success=True,
                message="Registration successful",
                config={
                    "heartbeat_interval": 30,
                    "log_batch_size": 100,
                },
                correlation_id=msg.id,
            ),
        )

        logger.info(f"Robot '{robot_name}' ({robot_id}) registered")

        # Notify callback
        if self._on_robot_connect:
            try:
                result = self._on_robot_connect(conn.to_robot())
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Robot connect callback error: {e}")

    async def _handle_heartbeat(self, websocket: WebSocketServerProtocol, msg: Message):
        """Handle heartbeat message."""
        robot_id = msg.payload.get("robot_id")
        conn = self._connections.get(robot_id)

        if conn:
            conn.last_heartbeat = datetime.now(timezone.utc)
            conn.status = RobotStatus(msg.payload.get("status", "online"))
            conn.cpu_percent = msg.payload.get("cpu_percent", 0.0)
            conn.memory_percent = msg.payload.get("memory_percent", 0.0)
            conn.disk_percent = msg.payload.get("disk_percent", 0.0)

            # Update active jobs
            active_jobs = msg.payload.get("active_job_ids", [])
            conn.current_jobs = set(active_jobs)

        await self._send(
            websocket,
            MessageBuilder.heartbeat_ack(
                robot_id=robot_id,
                correlation_id=msg.id,
            ),
        )

    async def _handle_disconnect(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle disconnect message."""
        robot_id = msg.payload.get("robot_id")
        reason = msg.payload.get("reason", "")
        logger.info(f"Robot {robot_id} disconnecting: {reason}")
        await websocket.close(1000, "Disconnect requested")

    async def _handle_job_accept(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job acceptance."""
        job_id = msg.payload.get("job_id")
        robot_id = msg.payload.get("robot_id")

        conn = self._connections.get(robot_id)
        if conn:
            conn.current_jobs.add(job_id)

        # Resolve pending response
        self._resolve_response(msg.correlation_id, {"accepted": True, "job_id": job_id})
        logger.debug(f"Job {job_id[:8]} accepted by robot {robot_id}")

    async def _handle_job_reject(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job rejection."""
        job_id = msg.payload.get("job_id")
        robot_id = msg.payload.get("robot_id")
        reason = msg.payload.get("reason")

        self._resolve_response(
            msg.correlation_id,
            {
                "accepted": False,
                "job_id": job_id,
                "reason": reason,
            },
        )
        logger.warning(f"Job {job_id[:8]} rejected by robot {robot_id}: {reason}")

    async def _handle_job_progress(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job progress update."""
        job_id = msg.payload.get("job_id")
        progress = msg.payload.get("progress", 0)
        current_node = msg.payload.get("current_node", "")

        if self._on_job_progress:
            try:
                result = self._on_job_progress(job_id, progress, current_node)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Job progress callback error: {e}")

    async def _handle_job_complete(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job completion."""
        job_id = msg.payload.get("job_id")
        robot_id = msg.payload.get("robot_id")
        result = msg.payload.get("result", {})

        # Remove from active jobs
        conn = self._connections.get(robot_id)
        if conn:
            conn.current_jobs.discard(job_id)

        if self._on_job_complete:
            try:
                callback_result = self._on_job_complete(job_id, result)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            except Exception as e:
                logger.error(f"Job complete callback error: {e}")

        logger.info(f"Job {job_id[:8]} completed by robot {robot_id}")

    async def _handle_job_failed(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job failure."""
        job_id = msg.payload.get("job_id")
        robot_id = msg.payload.get("robot_id")
        error_message = msg.payload.get("error_message", "Unknown error")

        # Remove from active jobs
        conn = self._connections.get(robot_id)
        if conn:
            conn.current_jobs.discard(job_id)

        if self._on_job_failed:
            try:
                result = self._on_job_failed(job_id, error_message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Job failed callback error: {e}")

        logger.error(f"Job {job_id[:8]} failed on robot {robot_id}: {error_message}")

    async def _handle_job_cancelled(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle job cancellation confirmation."""
        job_id = msg.payload.get("job_id")
        robot_id = msg.payload.get("robot_id")

        conn = self._connections.get(robot_id)
        if conn:
            conn.current_jobs.discard(job_id)

        self._resolve_response(
            msg.correlation_id, {"cancelled": True, "job_id": job_id}
        )
        logger.info(f"Job {job_id[:8]} cancelled on robot {robot_id}")

    async def _handle_status_response(
        self, websocket: WebSocketServerProtocol, msg: Message
    ):
        """Handle status response."""
        self._resolve_response(msg.correlation_id, msg.payload)

    async def _handle_log_entry(self, websocket: WebSocketServerProtocol, msg: Message):
        """Handle single log entry."""
        if self._on_log_entry:
            try:
                result = self._on_log_entry(
                    msg.payload.get("job_id"),
                    msg.payload.get("level"),
                    msg.payload.get("message"),
                    msg.payload.get("node_id", ""),
                )
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Log entry callback error: {e}")

    async def _handle_log_batch(self, websocket: WebSocketServerProtocol, msg: Message):
        """Handle batch log entries."""
        if self._on_log_entry:
            job_id = msg.payload.get("job_id")
            for entry in msg.payload.get("entries", []):
                try:
                    result = self._on_log_entry(
                        job_id,
                        entry.get("level"),
                        entry.get("message"),
                        entry.get("node_id", ""),
                    )
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Log batch callback error: {e}")

    async def _remove_connection(self, robot_id: str):
        """Remove a robot connection."""
        conn = self._connections.pop(robot_id, None)
        if conn:
            self._ws_to_robot.pop(conn.websocket, None)

            if self._on_robot_disconnect:
                try:
                    result = self._on_robot_disconnect(robot_id)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Robot disconnect callback error: {e}")

            logger.info(f"Robot '{conn.robot_name}' ({robot_id}) disconnected")

    async def _send(self, websocket: WebSocketServerProtocol, msg: Message):
        """Send message to a websocket."""
        try:
            await websocket.send(msg.to_json())
        except ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def _send_error(
        self,
        websocket: WebSocketServerProtocol,
        error_code: str,
        error_message: str,
        correlation_id: Optional[str] = None,
    ):
        """Send error message."""
        await self._send(
            websocket,
            MessageBuilder.error(
                error_code=error_code,
                error_message=error_message,
                correlation_id=correlation_id,
            ),
        )

    def _resolve_response(self, correlation_id: Optional[str], result: Any):
        """Resolve a pending response."""
        if correlation_id and correlation_id in self._pending_responses:
            future = self._pending_responses.pop(correlation_id)
            if not future.done():
                future.set_result(result)

    async def _health_check_loop(self):
        """Periodically check robot health."""
        while self._running:
            try:
                await asyncio.sleep(30)
                await self._check_robot_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _check_robot_health(self):
        """Check health of all connected robots."""
        now = datetime.now(timezone.utc)
        stale_robots = []

        for robot_id, conn in self._connections.items():
            elapsed = (now - conn.last_heartbeat).total_seconds()
            if elapsed > self._heartbeat_timeout:
                stale_robots.append(robot_id)
                conn.status = RobotStatus.OFFLINE
                logger.warning(
                    f"Robot '{conn.robot_name}' marked offline (no heartbeat)"
                )

        # Remove stale connections
        for robot_id in stale_robots:
            await self._remove_connection(robot_id)

    # ==================== PUBLIC API ====================

    async def send_job(
        self, robot_id: str, job: Job, timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Send a job to a robot.

        Args:
            robot_id: Target robot ID
            job: Job to send
            timeout: Response timeout in seconds

        Returns:
            Response dict with acceptance status
        """
        conn = self._connections.get(robot_id)
        if not conn:
            return {"accepted": False, "reason": "Robot not connected"}

        if not conn.is_available:
            return {"accepted": False, "reason": "Robot not available"}

        msg = MessageBuilder.job_assign(
            job_id=job.id,
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            workflow_json=job.workflow_json,
            priority=job.priority.value
            if hasattr(job.priority, "value")
            else job.priority,
        )

        # Create pending response
        future = asyncio.get_event_loop().create_future()
        self._pending_responses[msg.id] = future

        try:
            await self._send(conn.websocket, msg)

            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            self._pending_responses.pop(msg.id, None)
            return {"accepted": False, "reason": "Response timeout"}
        except Exception as e:
            self._pending_responses.pop(msg.id, None)
            return {"accepted": False, "reason": str(e)}

    async def cancel_job(
        self,
        robot_id: str,
        job_id: str,
        reason: str = "Cancelled by orchestrator",
        timeout: float = 10.0,
    ) -> bool:
        """
        Cancel a job on a robot.

        Args:
            robot_id: Robot running the job
            job_id: Job ID to cancel
            reason: Cancellation reason
            timeout: Response timeout

        Returns:
            True if cancelled successfully
        """
        conn = self._connections.get(robot_id)
        if not conn:
            return False

        msg = MessageBuilder.job_cancel(job_id=job_id, reason=reason)

        future = asyncio.get_event_loop().create_future()
        self._pending_responses[msg.id] = future

        try:
            await self._send(conn.websocket, msg)
            result = await asyncio.wait_for(future, timeout=timeout)
            return result.get("cancelled", False)
        except asyncio.TimeoutError:
            self._pending_responses.pop(msg.id, None)
            return False

    async def request_status(
        self, robot_id: str, timeout: float = 10.0
    ) -> Optional[Dict]:
        """Request status from a robot."""
        conn = self._connections.get(robot_id)
        if not conn:
            return None

        msg = MessageBuilder.status_request(robot_id=robot_id)

        future = asyncio.get_event_loop().create_future()
        self._pending_responses[msg.id] = future

        try:
            await self._send(conn.websocket, msg)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_responses.pop(msg.id, None)
            return None

    async def broadcast(self, msg: Message, environment: Optional[str] = None):
        """Broadcast message to all robots (optionally filtered by environment)."""
        for conn in self._connections.values():
            if environment and conn.environment != environment:
                continue
            await self._send(conn.websocket, msg)

    def get_connected_robots(self) -> List[Robot]:
        """Get list of connected robots."""
        return [conn.to_robot() for conn in self._connections.values()]

    def get_available_robots(self) -> List[Robot]:
        """Get list of available robots."""
        return [
            conn.to_robot() for conn in self._connections.values() if conn.is_available
        ]

    def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Get a specific robot."""
        conn = self._connections.get(robot_id)
        return conn.to_robot() if conn else None

    def is_robot_connected(self, robot_id: str) -> bool:
        """Check if a robot is connected."""
        return robot_id in self._connections

    @property
    def connected_count(self) -> int:
        """Get count of connected robots."""
        return len(self._connections)

    @property
    def available_count(self) -> int:
        """Get count of available robots."""
        return sum(1 for conn in self._connections.values() if conn.is_available)
