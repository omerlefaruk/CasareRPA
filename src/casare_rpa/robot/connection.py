"""
Connection Manager for Robot Agent.

Provides resilient connection handling with:
- Exponential backoff for reconnection
- Circuit breaker pattern integration
- Connection state tracking
"""

import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Callable, Any
from loguru import logger
from supabase import create_client, Client

from casare_rpa.utils.retry import RetryConfig


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class ConnectionConfig:
    """Configuration for connection behavior."""

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,  # 5 minutes max
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        max_reconnect_attempts: int = 0,  # 0 = infinite
        connection_timeout: float = 30.0,
        heartbeat_interval: float = 5.0,
        heartbeat_timeout: float = 10.0,
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.max_reconnect_attempts = max_reconnect_attempts
        self.connection_timeout = connection_timeout
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        import random
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


class ConnectionManager:
    """
    Manages Supabase connection with resilience patterns.

    Features:
    - Exponential backoff on connection failures
    - Automatic reconnection
    - Connection state tracking
    - Health check support
    """

    def __init__(
        self,
        url: str,
        key: str,
        config: Optional[ConnectionConfig] = None,
        on_connected: Optional[Callable[[], Any]] = None,
        on_disconnected: Optional[Callable[[], Any]] = None,
        on_reconnecting: Optional[Callable[[int], Any]] = None,
    ):
        """
        Initialize connection manager.

        Args:
            url: Supabase URL
            key: Supabase API key
            config: Connection configuration
            on_connected: Callback when connection established
            on_disconnected: Callback when connection lost
            on_reconnecting: Callback when reconnecting (receives attempt number)
        """
        self.url = url
        self.key = key
        self.config = config or ConnectionConfig()

        # Callbacks
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_reconnecting = on_reconnecting

        # State
        self._client: Optional[Client] = None
        self._state = ConnectionState.DISCONNECTED
        self._reconnect_attempt = 0
        self._last_successful_operation: Optional[datetime] = None
        self._consecutive_failures = 0

        # Statistics
        self.stats = ConnectionStats()

    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client."""
        return self._client

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED

    def _set_state(self, new_state: ConnectionState):
        """Set connection state and trigger callbacks."""
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            logger.debug(f"Connection state: {old_state.value} -> {new_state.value}")

            if new_state == ConnectionState.CONNECTED and self._on_connected:
                try:
                    self._on_connected()
                except Exception as e:
                    logger.error(f"on_connected callback error: {e}")

            elif new_state == ConnectionState.DISCONNECTED and self._on_disconnected:
                try:
                    self._on_disconnected()
                except Exception as e:
                    logger.error(f"on_disconnected callback error: {e}")

    async def connect(self) -> bool:
        """
        Establish connection to Supabase.

        Returns:
            True if connected successfully, False otherwise
        """
        if not self.url or not self.key:
            logger.error("Supabase credentials not configured")
            self._set_state(ConnectionState.FAILED)
            return False

        self._set_state(ConnectionState.CONNECTING)
        self.stats.connection_attempts += 1

        try:
            logger.info("Connecting to Supabase...")

            # Create client with timeout
            self._client = await asyncio.wait_for(
                asyncio.to_thread(lambda: create_client(self.url, self.key)),
                timeout=self.config.connection_timeout
            )

            # Verify connection with a simple operation
            await asyncio.wait_for(
                asyncio.to_thread(lambda: self._client.table("robots").select("id").limit(1).execute()),
                timeout=self.config.connection_timeout
            )

            self._set_state(ConnectionState.CONNECTED)
            self._reconnect_attempt = 0
            self._consecutive_failures = 0
            self._last_successful_operation = datetime.now(timezone.utc)
            self.stats.successful_connections += 1

            logger.info("Connected to Supabase successfully")
            return True

        except asyncio.TimeoutError:
            logger.error(f"Connection timed out after {self.config.connection_timeout}s")
            self._set_state(ConnectionState.DISCONNECTED)
            self._consecutive_failures += 1
            self.stats.failed_connections += 1
            return False

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._set_state(ConnectionState.DISCONNECTED)
            self._consecutive_failures += 1
            self.stats.failed_connections += 1
            return False

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnected successfully, False otherwise
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        # Check max attempts
        if (self.config.max_reconnect_attempts > 0 and
            self._reconnect_attempt >= self.config.max_reconnect_attempts):
            logger.error(f"Max reconnection attempts ({self.config.max_reconnect_attempts}) reached")
            self._set_state(ConnectionState.FAILED)
            return False

        self._reconnect_attempt += 1
        self._set_state(ConnectionState.RECONNECTING)

        # Trigger callback
        if self._on_reconnecting:
            try:
                self._on_reconnecting(self._reconnect_attempt)
            except Exception as e:
                logger.error(f"on_reconnecting callback error: {e}")

        # Calculate delay
        delay = self.config.get_delay(self._reconnect_attempt)
        logger.info(f"Reconnection attempt {self._reconnect_attempt} in {delay:.1f}s...")

        await asyncio.sleep(delay)

        return await self.connect()

    async def disconnect(self):
        """Disconnect from Supabase."""
        self._client = None
        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("Disconnected from Supabase")

    async def execute(
        self,
        operation: Callable[[Client], Any],
        retry_on_failure: bool = True
    ) -> Any:
        """
        Execute an operation with automatic reconnection on failure.

        Args:
            operation: Function that takes Client and returns result
            retry_on_failure: Whether to retry on connection failure

        Returns:
            Operation result

        Raises:
            Exception: If operation fails and reconnection fails
        """
        if not self._client or not self.is_connected:
            if not await self.connect():
                raise ConnectionError("Not connected to Supabase")

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(lambda: operation(self._client)),
                timeout=self.config.heartbeat_timeout
            )

            self._last_successful_operation = datetime.now(timezone.utc)
            self._consecutive_failures = 0
            self.stats.successful_operations += 1
            return result

        except Exception as e:
            self._consecutive_failures += 1
            self.stats.failed_operations += 1

            if retry_on_failure:
                logger.warning(f"Operation failed: {e}. Attempting reconnection...")
                self._set_state(ConnectionState.DISCONNECTED)

                if await self.reconnect():
                    # Retry the operation once after reconnection
                    try:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(lambda: operation(self._client)),
                            timeout=self.config.heartbeat_timeout
                        )
                        self._last_successful_operation = datetime.now(timezone.utc)
                        self.stats.successful_operations += 1
                        return result
                    except Exception as retry_error:
                        self.stats.failed_operations += 1
                        raise retry_error

            raise

    async def health_check(self) -> bool:
        """
        Perform a health check on the connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._client or not self.is_connected:
            return False

        try:
            await asyncio.wait_for(
                asyncio.to_thread(lambda: self._client.table("robots").select("id").limit(1).execute()),
                timeout=self.config.heartbeat_timeout
            )
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def get_status(self) -> dict:
        """Get connection status information."""
        return {
            "state": self._state.value,
            "is_connected": self.is_connected,
            "reconnect_attempt": self._reconnect_attempt,
            "consecutive_failures": self._consecutive_failures,
            "last_successful_operation": self._last_successful_operation.isoformat() if self._last_successful_operation else None,
            "stats": self.stats.to_dict()
        }


class ConnectionStats:
    """Statistics for connection operations."""

    def __init__(self):
        self.connection_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_reconnects = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "connection_attempts": self.connection_attempts,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "total_reconnects": self.total_reconnects,
            "connection_success_rate": (
                (self.successful_connections / self.connection_attempts * 100)
                if self.connection_attempts > 0 else 0
            ),
            "operation_success_rate": (
                (self.successful_operations / (self.successful_operations + self.failed_operations) * 100)
                if (self.successful_operations + self.failed_operations) > 0 else 0
            ),
        }
