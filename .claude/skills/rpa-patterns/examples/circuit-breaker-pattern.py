"""
Circuit Breaker Pattern for RPA Automation

Use Case: Prevent cascading failures, handle rate limits, avoid hammering failing services.

This pattern implements:
1. Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
2. Automatic reset after timeout
3. Failure counting and threshold
4. Metrics for monitoring
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable
from loguru import logger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation, requests pass through
    OPEN = "open"              # Failing, requests are rejected
    HALF_OPEN = "half_open"    # Testing if service has recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open and requests are rejected."""
    def __init__(self, message: str = "Circuit breaker is OPEN", retry_after_ms: int = 0):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes to close from HALF_OPEN
    timeout_ms: int = 60000             # Time before attempting reset (1 minute)
    half_open_max_calls: int = 1        # Max calls allowed in HALF_OPEN state
    track_success_rate: bool = True     # Track success rate for advanced opening


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: float = 0
    opened_count: int = 0
    closed_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    State transitions:
        CLOSED --(failures >= threshold)--> OPEN
        OPEN --(timeout elapsed)--> HALF_OPEN
        HALF_OPEN --(success)--> CLOSED
        HALF_OPEN --(failure)--> OPEN
    """

    def __init__(self, name: str = "circuit", config: CircuitBreakerConfig | None = None):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker
            config: Configuration (uses defaults if not provided)
        """
        self.name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._metrics = CircuitBreakerMetrics()
        self._half_open_calls = 0
        self._last_state_change = time.time()

    # ========================================================================
    # Public API
    # ========================================================================

    async def call(self, operation: Callable[[], Awaitable],
                   operation_name: str = "operation") -> any:
        """
        Execute operation with circuit breaker protection.

        Args:
            operation: Async callable to execute
            operation_name: Description for logging

        Returns:
            Result of the operation

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the operation itself
        """
        self._metrics.total_calls += 1

        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                self._metrics.rejected_calls += 1
                retry_after = max(0, self._config.timeout_ms -
                                  int((time.time() - self._last_state_change) * 1000))
                raise CircuitBreakerOpenError(
                    f"[{self.name}] Circuit is OPEN, rejecting {operation_name}",
                    retry_after_ms=retry_after
                )

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self._config.half_open_max_calls:
                self._metrics.rejected_calls += 1
                raise CircuitBreakerOpenError(
                    f"[{self.name}] Too many calls in HALF_OPEN state"
                )
            self._half_open_calls += 1

        try:
            result = await operation()
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    # ========================================================================
    # State Management
    # ========================================================================

    def _on_success(self) -> None:
        """Handle successful operation."""
        self._metrics.successful_calls += 1

        if self._state == CircuitState.HALF_OPEN:
            if self._metrics.successful_calls % self._config.success_threshold == 0:
                self._transition_to(CircuitState.CLOSED)
                self._half_open_calls = 0
                logger.info(f"[{self.name}] Circuit breaker CLOSED after successful recovery")

    def _on_failure(self) -> None:
        """Handle failed operation."""
        self._metrics.failed_calls += 1
        self._metrics.last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            self._half_open_calls = 0
            logger.warning(f"[{self.name}] Circuit breaker OPEN after failure in HALF_OPEN")
        elif self._state == CircuitState.CLOSED:
            consecutive_failures = self._metrics.failed_calls
            if consecutive_failures >= self._config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"[{self.name}] Circuit breaker OPEN after {consecutive_failures} failures"
                )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        elapsed = (time.time() - self._last_state_change) * 1000
        return elapsed >= self._config.timeout_ms

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state and record metrics."""
        if new_state == CircuitState.OPEN:
            self._metrics.opened_count += 1
        elif new_state == CircuitState.CLOSED:
            self._metrics.closed_count += 1

        self._state = new_state
        self._last_state_change = time.time()

    # ========================================================================
    # Query Methods
    # ========================================================================

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Current metrics."""
        return self._metrics

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN

    def get_state_dict(self) -> dict:
        """Get state as dict for monitoring."""
        return {
            "name": self.name,
            "state": self._state.value,
            "metrics": {
                "total_calls": self._metrics.total_calls,
                "successful_calls": self._metrics.successful_calls,
                "failed_calls": self._metrics.failed_calls,
                "rejected_calls": self._metrics.rejected_calls,
                "success_rate": self._metrics.success_rate,
                "opened_count": self._metrics.opened_count,
                "closed_count": self._metrics.closed_count,
            },
            "config": {
                "failure_threshold": self._config.failure_threshold,
                "timeout_ms": self._config.timeout_ms,
            }
        }

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self._transition_to(CircuitState.CLOSED)
        self._half_open_calls = 0
        logger.info(f"[{self.name}] Circuit breaker manually reset to CLOSED")


# ===========================================================================
# Global Circuit Breaker Registry
# ===========================================================================

_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """
    Get or create a named circuit breaker.

    Args:
        name: Unique identifier for the circuit
        config: Configuration (only used on first creation)

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers


def list_circuit_breakers() -> list[dict]:
    """Get state of all registered circuit breakers."""
    return [cb.get_state_dict() for cb in _circuit_breakers.values()]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers to CLOSED state."""
    for cb in _circuit_breakers.values():
        cb.reset()


# ===========================================================================
# Node Integration Example
# ===========================================================================

"""
Usage in an HTTP node:

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType

@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("circuit_name", PropertyType.STRING, default="api-circuit"),
)
@node(category="http")
class HttpWithCircuitNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")
        circuit_name = self.get_parameter("circuit_name", "api-circuit")

        # Get circuit breaker (creates with defaults if not exists)
        circuit = get_circuit_breaker(circuit_name)

        try:
            async def make_request():
                async with context.http_client.get(url) as response:
                    response.raise_for_status()
                    return await response.json()

            data = await circuit.call(make_request, operation_name=f"GET {url}")

            self.set_output_value("data", data)
            self.set_output_value("circuit_state", circuit.state.value)
            return {"success": True}

        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker open: {e}")
            self.set_output_value("circuit_state", "open")
            self.set_output_value("retry_after_ms", e.retry_after_ms)
            return {"success": False, "error": "Circuit breaker open", "retry_after_ms": e.retry_after_ms}

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"success": False, "error": str(e)}
"""
