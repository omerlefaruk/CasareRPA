"""
CasareRPA Infrastructure Layer - Supabase Realtime Client

Implements event-driven robot coordination using Supabase Realtime:
- Postgres Changes channel (CDC for instant job notifications)
- Broadcast channel (control commands: cancel_job, shutdown, pause)
- Presence channel (robot health tracking and load balancing)

Features:
- Hybrid poll+subscribe model for resilience
- Automatic reconnection with exponential backoff
- Channel subscription lifecycle management
- Type-safe payloads with Pydantic models
- Integration with DistributedRobotAgent

Architecture:
    +-----------------------+
    |   RealtimeClient      |
    |  (Connection Manager) |
    +-----------+-----------+
                |
    +-----------v-----------+
    | SubscriptionManager   |
    | (Channel Lifecycle)   |
    +-----------+-----------+
                |
    +-----------+-----------+-----------+
    |           |           |           |
    v           v           v           v
  Jobs      Control    Presence   Heartbeat
  Channel   Channel    Channel    Channel
  (CDC)     (Broadcast) (Track)   (Broadcast)

Database Schema (expected):
    -- Realtime requires replication enabled on tables
    ALTER TABLE job_queue REPLICA IDENTITY FULL;

    -- Enable Realtime for the table
    ALTER PUBLICATION supabase_realtime ADD TABLE job_queue;
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import (
    Any,
    TypeVar,
)

from loguru import logger

try:
    from realtime import AsyncRealtimeClient, RealtimeSubscribeStates
    from realtime.channel import AsyncRealtimeChannel

    HAS_REALTIME = True
except ImportError:
    HAS_REALTIME = False
    AsyncRealtimeClient = None
    RealtimeSubscribeStates = None
    AsyncRealtimeChannel = None


class RealtimeConnectionError(Exception):
    """Raised when connection to Supabase Realtime fails."""

    pass


class RealtimeSubscriptionError(Exception):
    """Raised when channel subscription fails."""

    pass


class RealtimeConnectionState(Enum):
    """Realtime client connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class ChannelType(Enum):
    """Supabase Realtime channel types."""

    POSTGRES_CHANGES = "postgres_changes"
    BROADCAST = "broadcast"
    PRESENCE = "presence"


class ChannelState(Enum):
    """Individual channel subscription state."""

    UNSUBSCRIBED = "unsubscribed"
    SUBSCRIBING = "subscribing"
    SUBSCRIBED = "subscribed"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class RealtimeConfig:
    """
    Configuration for Supabase Realtime client.

    Attributes:
        supabase_url: Supabase project URL (e.g., https://xxx.supabase.co)
        supabase_key: Supabase anon/service key
        robot_id: Unique identifier for this robot
        environment: Environment filter for job channel
        reconnect_max_attempts: Maximum reconnection attempts
        reconnect_base_delay_seconds: Base delay for exponential backoff
        reconnect_max_delay_seconds: Maximum delay between reconnects
        heartbeat_interval_seconds: Interval for heartbeat broadcasts
        presence_update_interval_seconds: Interval for presence updates
        subscribe_timeout_seconds: Timeout for channel subscription
    """

    supabase_url: str
    supabase_key: str
    robot_id: str
    environment: str = "default"
    reconnect_max_attempts: int = 10
    reconnect_base_delay_seconds: float = 1.0
    reconnect_max_delay_seconds: float = 60.0
    heartbeat_interval_seconds: float = 10.0
    presence_update_interval_seconds: float = 5.0
    subscribe_timeout_seconds: float = 10.0

    def get_realtime_url(self) -> str:
        """
        Convert Supabase URL to Realtime WebSocket URL.

        Returns:
            WebSocket URL for Realtime connection
        """
        base_url = self.supabase_url.rstrip("/")
        if base_url.startswith("https://"):
            ws_url = base_url.replace("https://", "wss://")
        elif base_url.startswith("http://"):
            ws_url = base_url.replace("http://", "ws://")
        else:
            ws_url = f"wss://{base_url}"

        return f"{ws_url}/realtime/v1/websocket"


@dataclass
class JobInsertedPayload:
    """
    Payload for job insert CDC event.

    Represents a new job inserted into the queue that robots should claim.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    priority: int
    environment: str
    created_at: datetime
    queue_name: str = "default"

    @classmethod
    def from_postgres_change(cls, payload: dict[str, Any]) -> JobInsertedPayload:
        """
        Parse from Postgres Changes payload.

        Args:
            payload: Raw CDC payload from Supabase

        Returns:
            Parsed JobInsertedPayload
        """
        record = payload.get("new", payload.get("record", {}))

        created_at_str = record.get("created_at", "")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now(UTC)
        else:
            created_at = datetime.now(UTC)

        return cls(
            job_id=str(record.get("id", "")),
            workflow_id=record.get("workflow_id", ""),
            workflow_name=record.get("workflow_name", ""),
            priority=record.get("priority", 1),
            environment=record.get("environment", "default"),
            created_at=created_at,
            queue_name=record.get("queue_name", "default"),
        )


@dataclass
class ControlCommandPayload:
    """
    Payload for control command broadcast.

    Control commands allow orchestrators to manage robots remotely.
    """

    command: str  # cancel_job, shutdown, pause, resume
    target_robot_id: str | None = None  # None = broadcast to all
    job_id: str | None = None  # For cancel_job command
    reason: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_broadcast(cls, payload: dict[str, Any]) -> ControlCommandPayload:
        """
        Parse from broadcast payload.

        Args:
            payload: Raw broadcast payload

        Returns:
            Parsed ControlCommandPayload
        """
        timestamp_str = payload.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(UTC)
        else:
            timestamp = datetime.now(UTC)

        return cls(
            command=payload.get("command", ""),
            target_robot_id=payload.get("target_robot_id"),
            job_id=payload.get("job_id"),
            reason=payload.get("reason"),
            timestamp=timestamp,
        )


@dataclass
class RobotPresenceInfo:
    """
    Robot presence information for health tracking.

    Published to presence channel for load balancing and monitoring.
    """

    robot_id: str
    status: str  # idle, busy, paused, shutting_down
    current_job_id: str | None = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    jobs_completed: int = 0
    jobs_failed: int = 0
    uptime_seconds: float = 0.0
    environment: str = "default"
    capabilities: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for presence tracking."""
        return {
            "robot_id": self.robot_id,
            "status": self.status,
            "current_job_id": self.current_job_id,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "uptime_seconds": self.uptime_seconds,
            "environment": self.environment,
            "capabilities": self.capabilities,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PresenceState:
    """
    Aggregated presence state from all robots.

    Used for load balancing and fleet monitoring.
    """

    robots: dict[str, RobotPresenceInfo] = field(default_factory=dict)
    last_sync: datetime = field(default_factory=lambda: datetime.now(UTC))

    def get_idle_robots(self) -> list[RobotPresenceInfo]:
        """Get all idle robots."""
        return [r for r in self.robots.values() if r.status == "idle"]

    def get_busy_robots(self) -> list[RobotPresenceInfo]:
        """Get all busy robots."""
        return [r for r in self.robots.values() if r.status == "busy"]

    def get_robot_by_id(self, robot_id: str) -> RobotPresenceInfo | None:
        """Get robot by ID."""
        return self.robots.get(robot_id)


# Type aliases for callbacks
JobInsertCallback = Callable[[JobInsertedPayload], Awaitable[None]]
ControlCommandCallback = Callable[[ControlCommandPayload], Awaitable[None]]
PresenceSyncCallback = Callable[[PresenceState], Awaitable[None]]
PresenceJoinCallback = Callable[[list[RobotPresenceInfo]], Awaitable[None]]
PresenceLeaveCallback = Callable[[list[str]], Awaitable[None]]
ConnectionStateCallback = Callable[[RealtimeConnectionState], None]

T = TypeVar("T")


class SubscriptionManager:
    """
    Manages channel subscriptions with lifecycle tracking.

    Handles subscription, unsubscription, and state transitions
    for all Realtime channels.
    """

    def __init__(self) -> None:
        """Initialize subscription manager."""
        self._channels: dict[str, Any] = {}  # channel_name -> channel object
        self._states: dict[str, ChannelState] = {}  # channel_name -> state
        self._callbacks: dict[str, list[Callable]] = {}  # channel_name -> callbacks
        self._lock = asyncio.Lock()

    def register_channel(
        self,
        name: str,
        channel: Any,
        callbacks: list[Callable] | None = None,
    ) -> None:
        """
        Register a channel for management.

        Args:
            name: Channel name
            channel: Channel object
            callbacks: Optional list of callbacks
        """
        self._channels[name] = channel
        self._states[name] = ChannelState.UNSUBSCRIBED
        self._callbacks[name] = callbacks or []

    async def subscribe_channel(self, name: str) -> bool:
        """
        Subscribe to a registered channel.

        Args:
            name: Channel name

        Returns:
            True if subscription succeeded
        """
        if name not in self._channels:
            logger.warning(f"Channel '{name}' not registered")
            return False

        channel = self._channels[name]
        self._states[name] = ChannelState.SUBSCRIBING

        try:
            subscribed = asyncio.Event()
            error_msg: str | None = None

            def on_subscribe(status: Any, err: Exception | None) -> None:
                nonlocal error_msg
                if HAS_REALTIME:
                    if status == RealtimeSubscribeStates.SUBSCRIBED:
                        self._states[name] = ChannelState.SUBSCRIBED
                        subscribed.set()
                    elif status == RealtimeSubscribeStates.CHANNEL_ERROR:
                        self._states[name] = ChannelState.ERROR
                        error_msg = str(err) if err else "Unknown error"
                        subscribed.set()
                    elif status == RealtimeSubscribeStates.TIMED_OUT:
                        self._states[name] = ChannelState.ERROR
                        error_msg = "Subscription timed out"
                        subscribed.set()
                    elif status == RealtimeSubscribeStates.CLOSED:
                        self._states[name] = ChannelState.CLOSED
                        subscribed.set()

            await channel.subscribe(on_subscribe)

            # Wait for subscription result with timeout
            try:
                await asyncio.wait_for(subscribed.wait(), timeout=10.0)
            except TimeoutError:
                self._states[name] = ChannelState.ERROR
                logger.error(f"Timeout waiting for channel '{name}' subscription")
                return False

            if self._states[name] == ChannelState.SUBSCRIBED:
                logger.info(f"Subscribed to channel '{name}'")
                return True
            else:
                logger.error(f"Failed to subscribe to channel '{name}': {error_msg}")
                return False

        except Exception as e:
            self._states[name] = ChannelState.ERROR
            logger.error(f"Exception subscribing to channel '{name}': {e}")
            return False

    async def unsubscribe_channel(self, name: str) -> bool:
        """
        Unsubscribe from a channel.

        Args:
            name: Channel name

        Returns:
            True if unsubscription succeeded
        """
        if name not in self._channels:
            return True

        channel = self._channels[name]
        try:
            await channel.unsubscribe()
            self._states[name] = ChannelState.UNSUBSCRIBED
            logger.info(f"Unsubscribed from channel '{name}'")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from channel '{name}': {e}")
            return False

    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all channels."""
        for name in list(self._channels.keys()):
            await self.unsubscribe_channel(name)

    def get_state(self, name: str) -> ChannelState:
        """Get channel state."""
        return self._states.get(name, ChannelState.UNSUBSCRIBED)

    def is_subscribed(self, name: str) -> bool:
        """Check if channel is subscribed."""
        return self._states.get(name) == ChannelState.SUBSCRIBED

    def get_all_states(self) -> dict[str, ChannelState]:
        """Get all channel states."""
        return dict(self._states)


class RealtimeClient:
    """
    Supabase Realtime client for event-driven robot coordination.

    Provides high-level interface for:
    - Job notification via Postgres Changes CDC
    - Control commands via Broadcast
    - Robot health tracking via Presence

    Implements hybrid poll+subscribe model for resilience.

    Usage:
        config = RealtimeConfig(
            supabase_url="https://xxx.supabase.co",
            supabase_key="your-key",
            robot_id="robot-001",
        )
        client = RealtimeClient(config)

        # Register callbacks
        client.on_job_inserted(handle_job)
        client.on_control_command(handle_command)
        client.on_presence_sync(handle_presence)

        # Connect and subscribe
        await client.connect()
        await client.subscribe_all()

        # ... robot runs ...

        # Cleanup
        await client.disconnect()
    """

    # Channel names
    CHANNEL_JOBS = "jobs"
    CHANNEL_CONTROL = "control"
    CHANNEL_PRESENCE = "robots"
    CHANNEL_HEARTBEAT = "heartbeats"

    def __init__(self, config: RealtimeConfig) -> None:
        """
        Initialize Realtime client.

        Args:
            config: Client configuration

        Raises:
            ImportError: If realtime package is not installed
        """
        if not HAS_REALTIME:
            raise ImportError(
                "realtime package is required for RealtimeClient. "
                "Install with: pip install realtime"
            )

        self._config = config
        self._state = RealtimeConnectionState.DISCONNECTED
        self._running = False
        self._reconnect_attempts = 0

        # Client and channels
        self._client: AsyncRealtimeClient | None = None
        self._subscription_manager = SubscriptionManager()

        # Presence state
        self._presence_state = PresenceState()
        self._robot_presence: RobotPresenceInfo | None = None

        # Notification event for hybrid model
        self._job_notification_event = asyncio.Event()

        # Callbacks
        self._on_job_inserted_callbacks: list[JobInsertCallback] = []
        self._on_control_command_callbacks: list[ControlCommandCallback] = []
        self._on_presence_sync_callbacks: list[PresenceSyncCallback] = []
        self._on_presence_join_callbacks: list[PresenceJoinCallback] = []
        self._on_presence_leave_callbacks: list[PresenceLeaveCallback] = []
        self._on_connection_state_callbacks: list[ConnectionStateCallback] = []

        # Background tasks
        self._reconnect_task: asyncio.Task | None = None
        self._presence_task: asyncio.Task | None = None

        logger.info(
            f"RealtimeClient initialized for robot '{config.robot_id}' at {config.supabase_url}"
        )

    @property
    def state(self) -> RealtimeConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._state == RealtimeConnectionState.CONNECTED

    @property
    def presence_state(self) -> PresenceState:
        """Get current presence state."""
        return self._presence_state

    @property
    def subscription_manager(self) -> SubscriptionManager:
        """Get subscription manager."""
        return self._subscription_manager

    def _set_state(self, new_state: RealtimeConnectionState) -> None:
        """Update state and notify callbacks."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.debug(f"Realtime state: {old_state.value} -> {new_state.value}")

            for callback in self._on_connection_state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.warning(f"Connection state callback error: {e}")

    def on_job_inserted(self, callback: JobInsertCallback) -> None:
        """
        Register callback for job insert events.

        Args:
            callback: Async function receiving JobInsertedPayload
        """
        self._on_job_inserted_callbacks.append(callback)

    def on_control_command(self, callback: ControlCommandCallback) -> None:
        """
        Register callback for control command events.

        Args:
            callback: Async function receiving ControlCommandPayload
        """
        self._on_control_command_callbacks.append(callback)

    def on_presence_sync(self, callback: PresenceSyncCallback) -> None:
        """
        Register callback for presence sync events.

        Args:
            callback: Async function receiving PresenceState
        """
        self._on_presence_sync_callbacks.append(callback)

    def on_presence_join(self, callback: PresenceJoinCallback) -> None:
        """
        Register callback for robot join events.

        Args:
            callback: Async function receiving list of RobotPresenceInfo
        """
        self._on_presence_join_callbacks.append(callback)

    def on_presence_leave(self, callback: PresenceLeaveCallback) -> None:
        """
        Register callback for robot leave events.

        Args:
            callback: Async function receiving list of robot IDs
        """
        self._on_presence_leave_callbacks.append(callback)

    def on_connection_state(self, callback: ConnectionStateCallback) -> None:
        """
        Register callback for connection state changes.

        Args:
            callback: Function receiving RealtimeConnectionState
        """
        self._on_connection_state_callbacks.append(callback)

    async def connect(self) -> bool:
        """
        Connect to Supabase Realtime.

        Returns:
            True if connection succeeded

        Raises:
            RealtimeConnectionError: If connection fails after retries
        """
        if self.is_connected:
            logger.warning("Already connected to Realtime")
            return True

        self._set_state(RealtimeConnectionState.CONNECTING)
        self._running = True

        try:
            realtime_url = self._config.get_realtime_url()
            logger.info(f"Connecting to Realtime: {realtime_url}")

            self._client = AsyncRealtimeClient(
                realtime_url,
                self._config.supabase_key,
            )

            await self._client.connect()

            self._set_state(RealtimeConnectionState.CONNECTED)
            self._reconnect_attempts = 0
            logger.info("Connected to Supabase Realtime")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Realtime: {e}")
            self._set_state(RealtimeConnectionState.FAILED)
            raise RealtimeConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """
        Disconnect from Supabase Realtime.

        Unsubscribes from all channels and closes the connection.
        """
        logger.info("Disconnecting from Realtime")
        self._running = False

        # Cancel background tasks
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self._presence_task and not self._presence_task.done():
            self._presence_task.cancel()
            try:
                await self._presence_task
            except asyncio.CancelledError:
                pass

        # Unsubscribe from channels
        await self._subscription_manager.unsubscribe_all()

        # Close client
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Realtime client: {e}")
            self._client = None

        self._set_state(RealtimeConnectionState.DISCONNECTED)
        logger.info("Disconnected from Realtime")

    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnection succeeded
        """
        if not self._running:
            return False

        self._set_state(RealtimeConnectionState.RECONNECTING)
        self._reconnect_attempts += 1

        if self._reconnect_attempts > self._config.reconnect_max_attempts:
            logger.error(f"Max reconnect attempts ({self._config.reconnect_max_attempts}) exceeded")
            self._set_state(RealtimeConnectionState.FAILED)
            return False

        # Calculate delay with exponential backoff and jitter
        delay = min(
            self._config.reconnect_base_delay_seconds * (2 ** (self._reconnect_attempts - 1)),
            self._config.reconnect_max_delay_seconds,
        )
        jitter = delay * random.uniform(0.1, 0.3)
        delay += jitter

        logger.info(
            f"Reconnect attempt {self._reconnect_attempts}/"
            f"{self._config.reconnect_max_attempts} in {delay:.1f}s"
        )
        await asyncio.sleep(delay)

        # Close existing client
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

        try:
            return await self.connect()
        except RealtimeConnectionError:
            return False

    async def _start_reconnect_monitor(self) -> None:
        """Background task to monitor connection and reconnect if needed."""
        while self._running:
            try:
                await asyncio.sleep(5)

                if not self._running:
                    break

                # Check if we need to reconnect
                if self._state in (
                    RealtimeConnectionState.FAILED,
                    RealtimeConnectionState.DISCONNECTED,
                ):
                    logger.info("Connection lost, attempting reconnect")
                    if await self._reconnect():
                        # Re-subscribe to channels
                        await self.subscribe_all()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reconnect monitor error: {e}")
                await asyncio.sleep(5)

    async def subscribe_all(self) -> bool:
        """
        Subscribe to all configured channels.

        Returns:
            True if all subscriptions succeeded
        """
        if not self.is_connected:
            logger.error("Cannot subscribe: not connected")
            return False

        success = True

        # Setup and subscribe to jobs channel (Postgres Changes)
        if not await self._setup_jobs_channel():
            success = False

        # Setup and subscribe to control channel (Broadcast)
        if not await self._setup_control_channel():
            success = False

        # Setup and subscribe to presence channel
        if not await self._setup_presence_channel():
            success = False

        # Start background tasks
        self._reconnect_task = asyncio.create_task(self._start_reconnect_monitor())

        return success

    async def _setup_jobs_channel(self) -> bool:
        """
        Setup Postgres Changes channel for job CDC.

        Returns:
            True if setup succeeded
        """
        if not self._client:
            return False

        channel = self._client.channel(self.CHANNEL_JOBS)

        # Configure Postgres Changes listener
        filter_str = f"environment=eq.{self._config.environment}"
        channel.on_postgres_changes(
            "INSERT",
            schema="public",
            table="job_queue",
            filter=filter_str,
            callback=self._handle_job_inserted,
        )

        self._subscription_manager.register_channel(self.CHANNEL_JOBS, channel)
        return await self._subscription_manager.subscribe_channel(self.CHANNEL_JOBS)

    async def _setup_control_channel(self) -> bool:
        """
        Setup Broadcast channel for control commands.

        Returns:
            True if setup succeeded
        """
        if not self._client:
            return False

        channel = self._client.channel(
            self.CHANNEL_CONTROL,
            {"config": {"broadcast": {"ack": True, "self": False}}},
        )

        # Listen for control commands
        channel.on_broadcast("cancel_job", self._handle_cancel_job_broadcast)
        channel.on_broadcast("shutdown", self._handle_shutdown_broadcast)
        channel.on_broadcast("pause", self._handle_pause_broadcast)
        channel.on_broadcast("resume", self._handle_resume_broadcast)

        self._subscription_manager.register_channel(self.CHANNEL_CONTROL, channel)
        return await self._subscription_manager.subscribe_channel(self.CHANNEL_CONTROL)

    async def _setup_presence_channel(self) -> bool:
        """
        Setup Presence channel for robot health tracking.

        Returns:
            True if setup succeeded
        """
        if not self._client:
            return False

        channel = self._client.channel(
            self.CHANNEL_PRESENCE,
            {"config": {"presence": {"key": self._config.robot_id}}},
        )

        # Setup presence callbacks
        channel.on_presence_sync(self._handle_presence_sync)
        channel.on_presence_join(self._handle_presence_join)
        channel.on_presence_leave(self._handle_presence_leave)

        self._subscription_manager.register_channel(self.CHANNEL_PRESENCE, channel)

        if not await self._subscription_manager.subscribe_channel(self.CHANNEL_PRESENCE):
            return False

        # Start presence update task
        self._presence_task = asyncio.create_task(self._presence_update_loop())
        return True

    def _handle_job_inserted(self, payload: dict[str, Any]) -> None:
        """
        Handle job insert CDC event.

        Args:
            payload: Raw CDC payload
        """
        try:
            job_payload = JobInsertedPayload.from_postgres_change(payload)
            logger.debug(f"Job inserted: {job_payload.job_id[:8]} - {job_payload.workflow_name}")

            # Signal hybrid model
            self._job_notification_event.set()

            # Invoke callbacks
            for callback in self._on_job_inserted_callbacks:
                asyncio.create_task(self._safe_callback(callback, job_payload))

        except Exception as e:
            logger.error(f"Error handling job insert: {e}")

    def _handle_cancel_job_broadcast(self, payload: dict[str, Any]) -> None:
        """Handle cancel_job control command."""
        self._handle_control_command("cancel_job", payload)

    def _handle_shutdown_broadcast(self, payload: dict[str, Any]) -> None:
        """Handle shutdown control command."""
        self._handle_control_command("shutdown", payload)

    def _handle_pause_broadcast(self, payload: dict[str, Any]) -> None:
        """Handle pause control command."""
        self._handle_control_command("pause", payload)

    def _handle_resume_broadcast(self, payload: dict[str, Any]) -> None:
        """Handle resume control command."""
        self._handle_control_command("resume", payload)

    def _handle_control_command(self, command: str, payload: dict[str, Any]) -> None:
        """
        Handle control command broadcast.

        Args:
            command: Command type
            payload: Raw broadcast payload
        """
        try:
            payload["command"] = command
            cmd_payload = ControlCommandPayload.from_broadcast(payload)

            # Check if command targets this robot
            if cmd_payload.target_robot_id and cmd_payload.target_robot_id != self._config.robot_id:
                logger.debug(f"Ignoring command for robot {cmd_payload.target_robot_id}")
                return

            logger.info(f"Control command received: {command}")

            # Invoke callbacks
            for callback in self._on_control_command_callbacks:
                asyncio.create_task(self._safe_callback(callback, cmd_payload))

        except Exception as e:
            logger.error(f"Error handling control command: {e}")

    def _handle_presence_sync(self) -> None:
        """Handle presence sync event."""
        try:
            # Get presence state from channel
            channel = self._subscription_manager._channels.get(self.CHANNEL_PRESENCE)
            if not channel:
                return

            raw_state = channel.presence_state()
            self._update_presence_state(raw_state)

            # Invoke callbacks
            for callback in self._on_presence_sync_callbacks:
                asyncio.create_task(self._safe_callback(callback, self._presence_state))

        except Exception as e:
            logger.error(f"Error handling presence sync: {e}")

    def _handle_presence_join(self, new_presences: dict[str, Any]) -> None:
        """Handle presence join event."""
        try:
            joined_robots = self._parse_presence_list(new_presences)
            if joined_robots:
                logger.info(f"Robots joined: {[r.robot_id for r in joined_robots]}")

                for callback in self._on_presence_join_callbacks:
                    asyncio.create_task(self._safe_callback(callback, joined_robots))

        except Exception as e:
            logger.error(f"Error handling presence join: {e}")

    def _handle_presence_leave(self, left_presences: dict[str, Any]) -> None:
        """Handle presence leave event."""
        try:
            left_ids = list(left_presences.keys()) if isinstance(left_presences, dict) else []
            if left_ids:
                logger.info(f"Robots left: {left_ids}")

                # Remove from presence state
                for robot_id in left_ids:
                    self._presence_state.robots.pop(robot_id, None)

                for callback in self._on_presence_leave_callbacks:
                    asyncio.create_task(self._safe_callback(callback, left_ids))

        except Exception as e:
            logger.error(f"Error handling presence leave: {e}")

    def _update_presence_state(self, raw_state: dict[str, Any]) -> None:
        """
        Update presence state from raw channel state.

        Args:
            raw_state: Raw presence state from channel
        """
        for key, presences in raw_state.items():
            if presences:
                # Take the most recent presence
                presence_data = presences[-1] if isinstance(presences, list) else presences
                if isinstance(presence_data, dict):
                    robot_id = presence_data.get("robot_id", key)
                    self._presence_state.robots[robot_id] = RobotPresenceInfo(
                        robot_id=robot_id,
                        status=presence_data.get("status", "unknown"),
                        current_job_id=presence_data.get("current_job_id"),
                        cpu_percent=presence_data.get("cpu_percent", 0.0),
                        memory_percent=presence_data.get("memory_percent", 0.0),
                        jobs_completed=presence_data.get("jobs_completed", 0),
                        jobs_failed=presence_data.get("jobs_failed", 0),
                        uptime_seconds=presence_data.get("uptime_seconds", 0.0),
                        environment=presence_data.get("environment", "default"),
                        capabilities=presence_data.get("capabilities", []),
                    )

        self._presence_state.last_sync = datetime.now(UTC)

    def _parse_presence_list(self, presences: dict[str, Any]) -> list[RobotPresenceInfo]:
        """Parse presence dictionary to list of RobotPresenceInfo."""
        result = []
        for key, presence_list in presences.items():
            if presence_list:
                presence_data = (
                    presence_list[-1] if isinstance(presence_list, list) else presence_list
                )
                if isinstance(presence_data, dict):
                    result.append(
                        RobotPresenceInfo(
                            robot_id=presence_data.get("robot_id", key),
                            status=presence_data.get("status", "unknown"),
                            current_job_id=presence_data.get("current_job_id"),
                            cpu_percent=presence_data.get("cpu_percent", 0.0),
                            memory_percent=presence_data.get("memory_percent", 0.0),
                            environment=presence_data.get("environment", "default"),
                        )
                    )
        return result

    async def _safe_callback(self, callback: Callable[[T], Awaitable[None]], payload: T) -> None:
        """
        Safely invoke async callback with error handling.

        Args:
            callback: Async callback function
            payload: Payload to pass to callback
        """
        try:
            await callback(payload)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    async def _presence_update_loop(self) -> None:
        """Background task to periodically update presence."""
        logger.debug("Presence update loop started")

        while self._running:
            try:
                await asyncio.sleep(self._config.presence_update_interval_seconds)

                if not self._running:
                    break

                if self._robot_presence:
                    await self.track_presence(self._robot_presence)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence update error: {e}")
                await asyncio.sleep(5)

        logger.debug("Presence update loop stopped")

    async def track_presence(self, info: RobotPresenceInfo) -> bool:
        """
        Update robot presence state.

        Args:
            info: Robot presence information

        Returns:
            True if tracking succeeded
        """
        channel = self._subscription_manager._channels.get(self.CHANNEL_PRESENCE)
        if not channel or not self._subscription_manager.is_subscribed(self.CHANNEL_PRESENCE):
            logger.warning("Presence channel not subscribed")
            return False

        try:
            self._robot_presence = info
            await channel.track(info.to_dict())
            return True
        except Exception as e:
            logger.error(f"Failed to track presence: {e}")
            return False

    async def send_broadcast(
        self,
        event: str,
        payload: dict[str, Any],
        channel_name: str = CHANNEL_CONTROL,
    ) -> bool:
        """
        Send a broadcast message to a channel.

        Args:
            event: Event name
            payload: Message payload
            channel_name: Target channel

        Returns:
            True if broadcast succeeded
        """
        channel = self._subscription_manager._channels.get(channel_name)
        if not channel:
            logger.warning(f"Channel '{channel_name}' not found")
            return False

        try:
            await channel.send_broadcast(event, payload)
            logger.debug(f"Broadcast sent: {event}")
            return True
        except Exception as e:
            logger.error(f"Failed to send broadcast: {e}")
            return False

    async def send_heartbeat(
        self,
        job_id: str,
        progress_percent: int = 0,
        current_node: str = "",
    ) -> bool:
        """
        Send heartbeat broadcast for current job.

        Args:
            job_id: Current job ID
            progress_percent: Job progress (0-100)
            current_node: Current executing node

        Returns:
            True if heartbeat succeeded
        """
        try:
            import psutil
        except ImportError:
            psutil = None

        payload = {
            "robot_id": self._config.robot_id,
            "job_id": job_id,
            "progress_percent": progress_percent,
            "current_node": current_node,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if psutil:
            try:
                payload["memory_mb"] = psutil.Process().memory_info().rss / (1024**2)
                payload["cpu_percent"] = psutil.Process().cpu_percent(interval=0.1)
            except Exception:
                pass

        return await self.send_broadcast("heartbeat", payload, self.CHANNEL_HEARTBEAT)

    async def wait_for_job_notification(self, timeout: float = 5.0) -> bool:
        """
        Wait for job notification with timeout (hybrid model).

        Used by robots to efficiently wait for new jobs:
        - Returns True if a job notification was received
        - Returns False on timeout (robot should poll)

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if notification received, False on timeout
        """
        self._job_notification_event.clear()
        try:
            await asyncio.wait_for(self._job_notification_event.wait(), timeout=timeout)
            return True
        except TimeoutError:
            return False

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive client status.

        Returns:
            Dict with client status information
        """
        return {
            "state": self._state.value,
            "is_connected": self.is_connected,
            "robot_id": self._config.robot_id,
            "environment": self._config.environment,
            "reconnect_attempts": self._reconnect_attempts,
            "channels": {
                name: state.value
                for name, state in self._subscription_manager.get_all_states().items()
            },
            "presence": {
                "total_robots": len(self._presence_state.robots),
                "idle_robots": len(self._presence_state.get_idle_robots()),
                "busy_robots": len(self._presence_state.get_busy_robots()),
                "last_sync": self._presence_state.last_sync.isoformat(),
            },
        }

    async def __aenter__(self) -> RealtimeClient:
        """Async context manager entry."""
        await self.connect()
        await self.subscribe_all()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> bool:
        """Async context manager exit."""
        await self.disconnect()
        return False
