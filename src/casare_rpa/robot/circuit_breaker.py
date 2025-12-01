"""
Circuit Breaker Pattern for Robot Agent.

Prevents cascading failures by stopping requests when a service is unhealthy.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked
- HALF_OPEN: Testing if service has recovered
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable, Any, TypeVar
from loguru import logger


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


T = TypeVar("T")


class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker configuration.

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in half-open before closing
            timeout: Seconds to wait in open state before trying half-open
            half_open_max_calls: Max concurrent calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and blocking requests."""

    def __init__(self, circuit_name: str, remaining_seconds: float):
        self.circuit_name = circuit_name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit breaker '{circuit_name}' is open. "
            f"Retry in {remaining_seconds:.1f}s"
        )


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Monitors failures and opens the circuit when threshold is reached,
    blocking further requests until service recovers.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name for this circuit (for logging)
            config: Circuit breaker configuration
            on_state_change: Callback when state changes (old_state, new_state)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._on_state_change = on_state_change

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._half_open_calls = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Statistics
        self.stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    def _set_state(self, new_state: CircuitState):
        """Set circuit state and trigger callback."""
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            logger.info(
                f"Circuit breaker '{self.name}': "
                f"{old_state.value} -> {new_state.value}"
            )

            if new_state == CircuitState.OPEN:
                self._opened_at = datetime.now(timezone.utc)
                self.stats.increment_times_opened_sync()  # Safe: called from within lock

            elif new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._success_count = 0

            elif new_state == CircuitState.CLOSED:
                self._failure_count = 0
                self._opened_at = None

            if self._on_state_change:
                try:
                    self._on_state_change(old_state, new_state)
                except Exception as e:
                    logger.error(f"Circuit breaker state change callback error: {e}")

    async def _check_state_transition(self):
        """Check if state should transition based on timeout."""
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = (datetime.now(timezone.utc) - self._opened_at).total_seconds()
            if elapsed >= self.config.timeout:
                self._set_state(CircuitState.HALF_OPEN)

    def _get_remaining_open_time(self) -> float:
        """Get remaining time until circuit tries half-open."""
        if self._state != CircuitState.OPEN or not self._opened_at:
            return 0

        elapsed = (datetime.now(timezone.utc) - self._opened_at).total_seconds()
        remaining = self.config.timeout - elapsed
        return max(0, remaining)

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async or sync function to call
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function raises an exception
        """
        async with self._lock:
            await self._check_state_transition()

            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                remaining = self._get_remaining_open_time()
                await self.stats.increment_blocked()
                raise CircuitBreakerOpenError(self.name, remaining)

            # Check half-open call limit
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    await self.stats.increment_blocked()
                    raise CircuitBreakerOpenError(self.name, 0)
                self._half_open_calls += 1

        # Execute the function (stats incremented thread-safely)
        await self.stats.increment_total()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self):
        """Handle successful call."""
        await self.stats.increment_successful()
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' half-open success: "
                    f"{self._success_count}/{self.config.success_threshold}"
                )

                if self._success_count >= self.config.success_threshold:
                    self._set_state(CircuitState.CLOSED)

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def _on_failure(self, exception: Exception):
        """Handle failed call."""
        await self.stats.increment_failed()
        async with self._lock:
            self._last_failure_time = datetime.now(timezone.utc)

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open state -> back to open
                logger.warning(
                    f"Circuit breaker '{self.name}' half-open failure: {exception}"
                )
                self._set_state(CircuitState.OPEN)

            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' failure count: "
                    f"{self._failure_count}/{self.config.failure_threshold}"
                )

                if self._failure_count >= self.config.failure_threshold:
                    self._set_state(CircuitState.OPEN)

    async def reset(self):
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._opened_at = None
            self._set_state(CircuitState.CLOSED)
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    async def force_open(self):
        """Manually open circuit breaker."""
        async with self._lock:
            self._set_state(CircuitState.OPEN)
            logger.info(f"Circuit breaker '{self.name}' manually opened")

    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
            "opened_at": (self._opened_at.isoformat() if self._opened_at else None),
            "remaining_open_time": self._get_remaining_open_time(),
            "stats": self.stats.to_dict(),
        }


class CircuitBreakerStats:
    """Statistics for circuit breaker (thread-safe with atomic counters)."""

    def __init__(self):
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._blocked_calls = 0
        self._times_opened = 0
        self._lock = asyncio.Lock()

    @property
    def total_calls(self) -> int:
        return self._total_calls

    @property
    def successful_calls(self) -> int:
        return self._successful_calls

    @property
    def failed_calls(self) -> int:
        return self._failed_calls

    @property
    def blocked_calls(self) -> int:
        return self._blocked_calls

    @property
    def times_opened(self) -> int:
        return self._times_opened

    async def increment_total(self):
        """Thread-safe increment of total calls."""
        async with self._lock:
            self._total_calls += 1

    async def increment_successful(self):
        """Thread-safe increment of successful calls."""
        async with self._lock:
            self._successful_calls += 1

    async def increment_failed(self):
        """Thread-safe increment of failed calls."""
        async with self._lock:
            self._failed_calls += 1

    async def increment_blocked(self):
        """Thread-safe increment of blocked calls."""
        async with self._lock:
            self._blocked_calls += 1

    async def increment_times_opened(self):
        """Thread-safe increment of times opened."""
        async with self._lock:
            self._times_opened += 1

    def increment_times_opened_sync(self):
        """Sync increment - only call from within an existing lock context."""
        self._times_opened += 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        total = self._total_calls
        successful = self._successful_calls
        return {
            "total_calls": total,
            "successful_calls": successful,
            "failed_calls": self._failed_calls,
            "blocked_calls": self._blocked_calls,
            "times_opened": self._times_opened,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_status(self) -> dict[str, dict]:
        """Get status of all circuit breakers."""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    async def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()


# Global registry instance
_circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker from global registry."""
    return _circuit_breaker_registry.get_or_create(name, config)


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return _circuit_breaker_registry
