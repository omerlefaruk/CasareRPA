"""
Secure Agent Tunnel for On-Premises Robots.

Establishes outbound-only secure WebSocket connection from on-prem
robots to cloud control plane with mTLS authentication.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import websockets
from websockets.client import WebSocketClientProtocol
from loguru import logger

from casare_rpa.infrastructure.tunnel.mtls import MTLSConfig


class TunnelState(Enum):
    """Tunnel connection states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    REGISTERED = "registered"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class MessageType(Enum):
    """Types of tunnel messages."""

    # Control messages
    REGISTER = "register"
    REGISTER_ACK = "register_ack"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    ERROR = "error"

    # Job messages
    JOB_ASSIGN = "job_assign"
    JOB_ACCEPT = "job_accept"
    JOB_REJECT = "job_reject"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETE = "job_complete"
    JOB_FAILED = "job_failed"

    # Status messages
    STATUS_UPDATE = "status_update"
    CAPABILITY_UPDATE = "capability_update"


@dataclass
class RobotCapabilities:
    """Robot capabilities advertised to control plane."""

    robot_type: str = "desktop"  # browser, desktop, hybrid
    browser_types: List[str] = field(default_factory=lambda: ["chromium"])
    desktop_supported: bool = True
    max_concurrent_jobs: int = 1
    tags: List[str] = field(default_factory=list)
    os_info: str = ""
    memory_mb: int = 0
    cpu_cores: int = 0


@dataclass
class TunnelConfig:
    """
    Configuration for agent tunnel.

    Attributes:
        control_plane_url: WebSocket URL of control plane
        mtls_config: mTLS configuration for authentication
        robot_name: Human-readable robot name
        robot_id: Unique robot identifier (auto-generated if not provided)
        capabilities: Robot capabilities
        heartbeat_interval: Seconds between heartbeats
        reconnect_delay: Initial reconnect delay in seconds
        max_reconnect_delay: Maximum reconnect delay in seconds
        reconnect_multiplier: Delay multiplier for exponential backoff
    """

    control_plane_url: str
    mtls_config: MTLSConfig
    robot_name: str = "On-Prem Robot"
    robot_id: Optional[str] = None
    capabilities: RobotCapabilities = field(default_factory=RobotCapabilities)
    heartbeat_interval: int = 30
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    reconnect_multiplier: float = 2.0

    def __post_init__(self):
        if not self.robot_id:
            self.robot_id = f"robot-{uuid.uuid4().hex[:12]}"


class AgentTunnel:
    """
    Secure tunnel for on-premises robot to cloud control plane.

    Features:
    - mTLS authentication (outbound connection only)
    - Automatic reconnection with exponential backoff
    - Heartbeat monitoring
    - Job assignment and status reporting
    - Capability advertisement

    Usage:
        config = TunnelConfig(
            control_plane_url="wss://api.casarerpa.com/ws/robot",
            mtls_config=MTLSConfig(
                ca_cert_path=Path("certs/ca.crt"),
                client_cert_path=Path("certs/robot.crt"),
                client_key_path=Path("certs/robot.key"),
            ),
            robot_name="Desktop Robot 1",
        )

        tunnel = AgentTunnel(config)
        tunnel.on_job_received = handle_job
        await tunnel.connect()
    """

    def __init__(self, config: TunnelConfig):
        """
        Initialize agent tunnel.

        Args:
            config: Tunnel configuration
        """
        self.config = config
        self._state = TunnelState.DISCONNECTED
        self._ws: Optional[WebSocketClientProtocol] = None
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_delay = config.reconnect_delay

        # Callbacks
        self.on_job_received: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_state_changed: Optional[Callable[[TunnelState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Metrics
        self._connected_at: Optional[datetime] = None
        self._last_heartbeat: Optional[datetime] = None
        self._jobs_received: int = 0
        self._reconnect_count: int = 0

    @property
    def state(self) -> TunnelState:
        """Get current tunnel state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if tunnel is connected and registered."""
        return self._state == TunnelState.REGISTERED

    def _set_state(self, new_state: TunnelState) -> None:
        """Update state and notify callback."""
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            logger.info(f"Tunnel state: {old_state.value} -> {new_state.value}")
            if self.on_state_changed:
                try:
                    self.on_state_changed(new_state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")

    async def connect(self) -> bool:
        """
        Connect to control plane.

        Returns:
            True if connection successful
        """
        if self._running:
            logger.warning("Tunnel already running")
            return False

        self._running = True
        self._set_state(TunnelState.CONNECTING)

        try:
            # Create SSL context with mTLS
            ssl_context = self.config.mtls_config.create_ssl_context()

            # Connect with mTLS
            self._ws = await websockets.connect(
                self.config.control_plane_url,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            )

            self._set_state(TunnelState.CONNECTED)
            self._connected_at = datetime.now(timezone.utc)
            self._reconnect_delay = self.config.reconnect_delay  # Reset backoff

            # Register with control plane
            await self._register()

            # Start background tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Tunnel connected: {self.config.robot_name} ({self.config.robot_id})")
            return True

        except Exception as e:
            self._set_state(TunnelState.ERROR)
            logger.error(f"Tunnel connection failed: {e}")
            if self.on_error:
                self.on_error(str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from control plane."""
        self._running = False

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        # Close WebSocket
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self._ws = None

        self._set_state(TunnelState.DISCONNECTED)
        logger.info("Tunnel disconnected")

    async def run_forever(self) -> None:
        """
        Run tunnel with automatic reconnection.

        This method runs indefinitely, reconnecting on disconnection.
        """
        while self._running:
            if self._state in (TunnelState.DISCONNECTED, TunnelState.ERROR):
                success = await self.connect()
                if not success:
                    # Exponential backoff
                    logger.info(f"Reconnecting in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(
                        self._reconnect_delay * self.config.reconnect_multiplier,
                        self.config.max_reconnect_delay,
                    )
                    self._reconnect_count += 1
                    self._set_state(TunnelState.RECONNECTING)
            else:
                await asyncio.sleep(1)

    async def _register(self) -> None:
        """Register robot with control plane."""
        self._set_state(TunnelState.AUTHENTICATING)

        message = {
            "type": MessageType.REGISTER.value,
            "robot_id": self.config.robot_id,
            "robot_name": self.config.robot_name,
            "capabilities": {
                "robot_type": self.config.capabilities.robot_type,
                "browser_types": self.config.capabilities.browser_types,
                "desktop_supported": self.config.capabilities.desktop_supported,
                "max_concurrent_jobs": self.config.capabilities.max_concurrent_jobs,
                "tags": self.config.capabilities.tags,
                "os_info": self.config.capabilities.os_info,
                "memory_mb": self.config.capabilities.memory_mb,
                "cpu_cores": self.config.capabilities.cpu_cores,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> None:
        """Send message to control plane."""
        if not self._ws:
            raise RuntimeError("Not connected")

        await self._ws.send(json.dumps(message))
        logger.debug(f"Sent: {message.get('type', 'unknown')}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running and self._ws:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                if self._state == TunnelState.REGISTERED:
                    message = {
                        "type": MessageType.HEARTBEAT.value,
                        "robot_id": self.config.robot_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await self._send(message)
                    self._last_heartbeat = datetime.now(timezone.utc)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self._set_state(TunnelState.ERROR)
                break

    async def _receive_loop(self) -> None:
        """Receive and process messages from control plane."""
        while self._running and self._ws:
            try:
                raw_message = await self._ws.recv()
                message = json.loads(raw_message)
                await self._handle_message(message)

            except websockets.ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                self._set_state(TunnelState.DISCONNECTED)
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle received message."""
        msg_type = message.get("type", "")
        logger.debug(f"Received: {msg_type}")

        if msg_type == MessageType.REGISTER_ACK.value:
            self._set_state(TunnelState.REGISTERED)
            logger.info("Robot registered with control plane")

        elif msg_type == MessageType.HEARTBEAT_ACK.value:
            pass  # Heartbeat acknowledged

        elif msg_type == MessageType.JOB_ASSIGN.value:
            self._jobs_received += 1
            await self._handle_job_assignment(message)

        elif msg_type == MessageType.ERROR.value:
            error_msg = message.get("message", "Unknown error")
            logger.error(f"Control plane error: {error_msg}")
            if self.on_error:
                self.on_error(error_msg)

    async def _handle_job_assignment(self, message: Dict[str, Any]) -> None:
        """Handle job assignment from control plane."""
        job_id = message.get("job_id")
        message.get("workflow_json")

        logger.info(f"Job assigned: {job_id}")

        if self.on_job_received:
            try:
                # Notify callback
                self.on_job_received(message)

                # Accept job
                await self._send(
                    {
                        "type": MessageType.JOB_ACCEPT.value,
                        "job_id": job_id,
                        "robot_id": self.config.robot_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Job callback error: {e}")
                await self._send(
                    {
                        "type": MessageType.JOB_REJECT.value,
                        "job_id": job_id,
                        "robot_id": self.config.robot_id,
                        "reason": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
        else:
            # No callback - reject job
            await self._send(
                {
                    "type": MessageType.JOB_REJECT.value,
                    "job_id": job_id,
                    "robot_id": self.config.robot_id,
                    "reason": "No job handler configured",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    async def report_job_progress(
        self,
        job_id: str,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """
        Report job progress to control plane.

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        await self._send(
            {
                "type": MessageType.JOB_PROGRESS.value,
                "job_id": job_id,
                "robot_id": self.config.robot_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def report_job_complete(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Report job completion to control plane.

        Args:
            job_id: Job identifier
            result: Optional result data
        """
        await self._send(
            {
                "type": MessageType.JOB_COMPLETE.value,
                "job_id": job_id,
                "robot_id": self.config.robot_id,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def report_job_failed(
        self,
        job_id: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Report job failure to control plane.

        Args:
            job_id: Job identifier
            error: Error message
            details: Optional error details
        """
        await self._send(
            {
                "type": MessageType.JOB_FAILED.value,
                "job_id": job_id,
                "robot_id": self.config.robot_id,
                "error": error,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def update_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update robot status on control plane.

        Args:
            status: Status string (idle, busy, error)
            metadata: Optional metadata
        """
        await self._send(
            {
                "type": MessageType.STATUS_UPDATE.value,
                "robot_id": self.config.robot_id,
                "status": status,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get tunnel metrics."""
        return {
            "state": self._state.value,
            "robot_id": self.config.robot_id,
            "connected_at": self._connected_at.isoformat() if self._connected_at else None,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            "jobs_received": self._jobs_received,
            "reconnect_count": self._reconnect_count,
        }
