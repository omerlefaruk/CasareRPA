"""Circuit breaker (domain service).

Used by application orchestration code to prevent cascading failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    success_threshold: int = 2


@dataclass
class _CircuitBreakerState:
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=datetime.now)


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = _CircuitBreakerState()

    @property
    def is_open(self) -> bool:
        if self._state.state == CircuitState.OPEN:
            if self._state.last_failure_time is None:
                return True

            elapsed = (datetime.now() - self._state.last_failure_time).total_seconds()
            if elapsed >= self.config.recovery_timeout_seconds:
                self._state.state = CircuitState.HALF_OPEN
                self._state.last_state_change = datetime.now()
                return False

            return True

        return False

    def record_failure(self, _error_type: str | None = None) -> None:
        self._state.failure_count += 1
        self._state.last_failure_time = datetime.now()
        self._state.last_state_change = datetime.now()

        if self._state.state == CircuitState.HALF_OPEN:
            self._state.state = CircuitState.OPEN
            self._state.success_count = 0
            return

        if self._state.failure_count >= self.config.failure_threshold:
            self._state.state = CircuitState.OPEN
            self._state.success_count = 0

    def record_success(self) -> None:
        if self._state.state == CircuitState.HALF_OPEN:
            self._state.success_count += 1
            if self._state.success_count >= self.config.success_threshold:
                self._state.state = CircuitState.CLOSED
                self._state.failure_count = 0
                self._state.success_count = 0
                self._state.last_failure_time = None
                self._state.last_state_change = datetime.now()
            return

        if self._state.state == CircuitState.CLOSED:
            self._state.failure_count = 0
            self._state.success_count = 0
            self._state.last_failure_time = None

    def reset(self) -> None:
        """Reset breaker to the initial CLOSED state."""
        self._state.state = CircuitState.CLOSED
        self._state.failure_count = 0
        self._state.success_count = 0
        self._state.last_failure_time = None
        self._state.last_state_change = datetime.now()
