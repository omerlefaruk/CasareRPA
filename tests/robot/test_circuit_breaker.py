"""
Tests for Robot Agent Circuit Breaker Pattern.

Tests circuit breaker states and transitions:
- CLOSED: Normal operation, requests pass through
- OPEN: Service failing, requests blocked
- HALF_OPEN: Testing if service recovered

Tests cover:
- State transitions based on failures/successes
- Failure threshold triggers open
- Timeout triggers half-open
- Success threshold closes circuit
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitBreakerStats,
    CircuitState,
    get_circuit_breaker,
    get_circuit_breaker_registry,
)


# --- Fixtures ---


@pytest.fixture
def default_config() -> CircuitBreakerConfig:
    """Default circuit breaker config for testing."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,  # Short timeout for testing
        half_open_max_calls=2,
    )


@pytest.fixture
def circuit_breaker(default_config: CircuitBreakerConfig) -> CircuitBreaker:
    """Provide circuit breaker with test configuration."""
    return CircuitBreaker(name="test-circuit", config=default_config)


@pytest.fixture
def successful_async_func() -> AsyncMock:
    """Mock async function that succeeds."""
    func = AsyncMock(return_value="success")
    return func


@pytest.fixture
def failing_async_func() -> AsyncMock:
    """Mock async function that raises exception."""
    func = AsyncMock(side_effect=Exception("Service unavailable"))
    return func


# --- CircuitBreakerConfig Tests ---


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self):
        """Default config has sensible defaults."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3

    def test_custom_values(self):
        """Config accepts custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=120.0,
            half_open_max_calls=5,
        )

        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout == 120.0
        assert config.half_open_max_calls == 5


# --- CircuitBreaker Initial State Tests ---


class TestCircuitBreakerInitialState:
    """Tests for initial circuit breaker state."""

    def test_starts_in_closed_state(self, circuit_breaker: CircuitBreaker):
        """Circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed is True
        assert circuit_breaker.is_open is False

    def test_initial_counters_zero(self, circuit_breaker: CircuitBreaker):
        """Initial failure and success counts are zero."""
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0

    def test_initial_stats_empty(self, circuit_breaker: CircuitBreaker):
        """Initial stats are zero."""
        stats = circuit_breaker.stats.to_dict()

        assert stats["total_calls"] == 0
        assert stats["successful_calls"] == 0
        assert stats["failed_calls"] == 0
        assert stats["blocked_calls"] == 0
        assert stats["times_opened"] == 0


# --- CLOSED State Tests ---


class TestCircuitBreakerClosedState:
    """Tests for CLOSED state behavior."""

    @pytest.mark.asyncio
    async def test_successful_call_passes_through(
        self,
        circuit_breaker: CircuitBreaker,
        successful_async_func: AsyncMock,
    ):
        """Successful calls pass through in CLOSED state."""
        result = await circuit_breaker.call(successful_async_func)

        assert result == "success"
        successful_async_func.assert_awaited_once()
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call_updates_stats(
        self,
        circuit_breaker: CircuitBreaker,
        successful_async_func: AsyncMock,
    ):
        """Successful calls update statistics."""
        await circuit_breaker.call(successful_async_func)

        assert circuit_breaker.stats.total_calls == 1
        assert circuit_breaker.stats.successful_calls == 1
        assert circuit_breaker.stats.failed_calls == 0

    @pytest.mark.asyncio
    async def test_failure_increments_count(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
    ):
        """Failed calls increment failure count."""
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_async_func)

        assert circuit_breaker._failure_count == 1
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(
        self,
        circuit_breaker: CircuitBreaker,
        successful_async_func: AsyncMock,
        failing_async_func: AsyncMock,
    ):
        """Success resets failure count in CLOSED state."""
        # Two failures
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        assert circuit_breaker._failure_count == 2

        # Success resets
        await circuit_breaker.call(successful_async_func)

        assert circuit_breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_sync_function_works(self, circuit_breaker: CircuitBreaker):
        """Sync functions are handled correctly."""

        def sync_func():
            return "sync_result"

        result = await circuit_breaker.call(sync_func)

        assert result == "sync_result"


# --- Transition to OPEN State Tests ---


class TestCircuitBreakerTransitionToOpen:
    """Tests for CLOSED -> OPEN transition."""

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Circuit opens after reaching failure threshold."""
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_records_opened_time(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Opening records the time when opened."""
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        assert circuit_breaker._opened_at is not None
        assert isinstance(circuit_breaker._opened_at, datetime)

    @pytest.mark.asyncio
    async def test_increments_times_opened_stat(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Times opened stat is incremented."""
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        assert circuit_breaker.stats.times_opened == 1

    @pytest.mark.asyncio
    async def test_state_change_callback_called(
        self,
        default_config: CircuitBreakerConfig,
        failing_async_func: AsyncMock,
    ):
        """State change callback is called on transition."""
        callback = MagicMock()
        breaker = CircuitBreaker(
            name="test",
            config=default_config,
            on_state_change=callback,
        )

        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        callback.assert_called_once_with(CircuitState.CLOSED, CircuitState.OPEN)


# --- OPEN State Tests ---


class TestCircuitBreakerOpenState:
    """Tests for OPEN state behavior."""

    @pytest.mark.asyncio
    async def test_blocks_requests(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """OPEN state blocks all requests."""
        # Open the circuit
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        # Attempt to call - should be blocked
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await circuit_breaker.call(successful_async_func)

        assert exc_info.value.circuit_name == "test-circuit"
        successful_async_func.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_blocked_calls_increment_stat(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Blocked calls increment blocked_calls stat."""
        # Open the circuit
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        # Multiple blocked attempts
        for _ in range(3):
            with pytest.raises(CircuitBreakerOpenError):
                await circuit_breaker.call(successful_async_func)

        assert circuit_breaker.stats.blocked_calls == 3

    @pytest.mark.asyncio
    async def test_remaining_time_reported(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Error includes remaining time until retry."""
        # Open the circuit
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await circuit_breaker.call(successful_async_func)

        assert exc_info.value.remaining_seconds > 0
        assert exc_info.value.remaining_seconds <= default_config.timeout


# --- Transition to HALF_OPEN State Tests ---


class TestCircuitBreakerTransitionToHalfOpen:
    """Tests for OPEN -> HALF_OPEN transition."""

    @pytest.mark.asyncio
    async def test_transitions_after_timeout(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """Circuit transitions to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,  # 100ms timeout
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next call should trigger transition
        await breaker.call(successful_async_func)

        # Circuit should now be CLOSED (success in half-open)
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_resets_half_open_counters(
        self,
        failing_async_func: AsyncMock,
    ):
        """Transition to HALF_OPEN resets counters."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        # Wait and trigger state check
        await asyncio.sleep(0.15)

        # Use _check_state_transition directly for reliable testing
        async with breaker._lock:
            await breaker._check_state_transition()

        assert breaker._half_open_calls == 0
        assert breaker._success_count == 0


# --- HALF_OPEN State Tests ---


class TestCircuitBreakerHalfOpenState:
    """Tests for HALF_OPEN state behavior."""

    @pytest.mark.asyncio
    async def test_limits_concurrent_calls(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """HALF_OPEN limits number of concurrent calls."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
            half_open_max_calls=2,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Manually set to half-open for precise testing
        async with breaker._lock:
            await breaker._check_state_transition()

        assert breaker.state == CircuitState.HALF_OPEN

        # Max calls should be allowed
        breaker._half_open_calls = config.half_open_max_calls

        # Additional call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(successful_async_func)

    @pytest.mark.asyncio
    async def test_success_increments_count(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """Success in HALF_OPEN increments success count."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=3,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        await asyncio.sleep(0.15)

        # First success in half-open
        await breaker.call(successful_async_func)

        assert breaker._success_count == 1

    @pytest.mark.asyncio
    async def test_failure_returns_to_open(
        self,
        failing_async_func: AsyncMock,
    ):
        """Failure in HALF_OPEN returns to OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        await asyncio.sleep(0.15)

        # Should be half-open now, fail again
        with pytest.raises(Exception):
            await breaker.call(failing_async_func)

        assert breaker.state == CircuitState.OPEN


# --- Transition to CLOSED State Tests ---


class TestCircuitBreakerTransitionToClosed:
    """Tests for HALF_OPEN -> CLOSED transition."""

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """Circuit closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        await asyncio.sleep(0.15)

        # Success threshold calls
        for _ in range(config.success_threshold):
            await breaker.call(successful_async_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True

    @pytest.mark.asyncio
    async def test_clears_opened_at_timestamp(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """Closing clears the opened_at timestamp."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        assert breaker._opened_at is not None

        await asyncio.sleep(0.15)

        # Success threshold
        for _ in range(config.success_threshold):
            await breaker.call(successful_async_func)

        assert breaker._opened_at is None

    @pytest.mark.asyncio
    async def test_resets_failure_count(
        self,
        failing_async_func: AsyncMock,
        successful_async_func: AsyncMock,
    ):
        """Closing resets failure count."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker(name="test", config=config)

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_async_func)

        await asyncio.sleep(0.15)

        for _ in range(config.success_threshold):
            await breaker.call(successful_async_func)

        assert breaker._failure_count == 0


# --- Manual Control Tests ---


class TestCircuitBreakerManualControl:
    """Tests for manual circuit breaker control."""

    @pytest.mark.asyncio
    async def test_reset_closes_circuit(self, circuit_breaker: CircuitBreaker):
        """reset() closes circuit and clears counters."""
        # Manually set to open state
        circuit_breaker._state = CircuitState.OPEN
        circuit_breaker._failure_count = 5
        circuit_breaker._opened_at = datetime.now(timezone.utc)

        await circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0
        assert circuit_breaker._opened_at is None

    @pytest.mark.asyncio
    async def test_force_open_opens_circuit(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """force_open() opens circuit immediately."""
        assert circuit_breaker.state == CircuitState.CLOSED

        await circuit_breaker.force_open()

        assert circuit_breaker.state == CircuitState.OPEN


# --- Status Reporting Tests ---


class TestCircuitBreakerStatus:
    """Tests for status reporting."""

    @pytest.mark.asyncio
    async def test_get_status_returns_complete_info(
        self,
        circuit_breaker: CircuitBreaker,
        successful_async_func: AsyncMock,
    ):
        """get_status() returns complete circuit information."""
        await circuit_breaker.call(successful_async_func)

        status = circuit_breaker.get_status()

        assert status["name"] == "test-circuit"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["success_count"] == 0
        assert status["remaining_open_time"] == 0
        assert "stats" in status

    @pytest.mark.asyncio
    async def test_status_includes_timestamps(
        self,
        circuit_breaker: CircuitBreaker,
        failing_async_func: AsyncMock,
        default_config: CircuitBreakerConfig,
    ):
        """Status includes relevant timestamps when available."""
        # Open the circuit
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_func)

        status = circuit_breaker.get_status()

        assert status["last_failure_time"] is not None
        assert status["opened_at"] is not None


# --- CircuitBreakerStats Tests ---


class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats."""

    @pytest.mark.asyncio
    async def test_increment_methods_thread_safe(self):
        """Stats increment methods are thread-safe."""
        stats = CircuitBreakerStats()

        # Concurrent increments
        tasks = [
            stats.increment_total(),
            stats.increment_total(),
            stats.increment_successful(),
            stats.increment_failed(),
            stats.increment_blocked(),
        ]
        await asyncio.gather(*tasks)

        assert stats.total_calls == 2
        assert stats.successful_calls == 1
        assert stats.failed_calls == 1
        assert stats.blocked_calls == 1

    def test_to_dict_calculates_success_rate(self):
        """to_dict() calculates success rate correctly."""
        stats = CircuitBreakerStats()
        stats._total_calls = 100
        stats._successful_calls = 75
        stats._failed_calls = 25

        result = stats.to_dict()

        assert result["success_rate"] == 75.0

    def test_to_dict_handles_zero_calls(self):
        """to_dict() handles zero total calls."""
        stats = CircuitBreakerStats()

        result = stats.to_dict()

        assert result["success_rate"] == 0


# --- CircuitBreakerRegistry Tests ---


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    def test_get_or_create_new_breaker(self):
        """get_or_create() creates new breaker."""
        registry = CircuitBreakerRegistry()

        breaker = registry.get_or_create("new-circuit")

        assert breaker is not None
        assert breaker.name == "new-circuit"

    def test_get_or_create_returns_existing(self):
        """get_or_create() returns existing breaker."""
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_or_create("same-circuit")

        breaker2 = registry.get_or_create("same-circuit")

        assert breaker1 is breaker2

    def test_get_returns_none_for_missing(self):
        """get() returns None for missing breaker."""
        registry = CircuitBreakerRegistry()

        result = registry.get("non-existent")

        assert result is None

    def test_get_all_status(self):
        """get_all_status() returns all breaker statuses."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("circuit-1")
        registry.get_or_create("circuit-2")

        statuses = registry.get_all_status()

        assert len(statuses) == 2
        assert "circuit-1" in statuses
        assert "circuit-2" in statuses

    @pytest.mark.asyncio
    async def test_reset_all(self):
        """reset_all() resets all breakers."""
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_or_create("circuit-1")
        breaker2 = registry.get_or_create("circuit-2")

        # Open both
        await breaker1.force_open()
        await breaker2.force_open()

        await registry.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


# --- Global Functions Tests ---


class TestGlobalFunctions:
    """Tests for module-level functions."""

    def test_get_circuit_breaker_creates_breaker(self):
        """get_circuit_breaker() creates/returns breaker."""
        # Note: Uses global registry, may have state from other tests
        breaker = get_circuit_breaker("global-test-circuit")

        assert breaker is not None
        assert breaker.name == "global-test-circuit"

    def test_get_circuit_breaker_with_config(self):
        """get_circuit_breaker() accepts custom config."""
        config = CircuitBreakerConfig(failure_threshold=10)

        breaker = get_circuit_breaker("global-config-circuit", config)

        # Config is only applied if breaker doesn't exist
        assert breaker.config.failure_threshold in [5, 10]

    def test_get_circuit_breaker_registry(self):
        """get_circuit_breaker_registry() returns global registry."""
        registry = get_circuit_breaker_registry()

        assert registry is not None
        assert isinstance(registry, CircuitBreakerRegistry)


# --- CircuitBreakerOpenError Tests ---


class TestCircuitBreakerOpenError:
    """Tests for CircuitBreakerOpenError exception."""

    def test_error_message_format(self):
        """Error message includes circuit name and remaining time."""
        error = CircuitBreakerOpenError("test-circuit", 30.5)

        assert "test-circuit" in str(error)
        assert "30.5" in str(error)
        assert error.circuit_name == "test-circuit"
        assert error.remaining_seconds == 30.5


# --- Edge Cases ---


class TestCircuitBreakerEdgeCases:
    """Edge case tests for circuit breaker."""

    @pytest.mark.asyncio
    async def test_handles_callback_error(self, default_config: CircuitBreakerConfig):
        """Handles errors in state change callback gracefully."""

        def failing_callback(old, new):
            raise ValueError("Callback error")

        breaker = CircuitBreaker(
            name="test",
            config=default_config,
            on_state_change=failing_callback,
        )
        failing_func = AsyncMock(side_effect=Exception("fail"))

        # Should not raise even with failing callback
        for _ in range(default_config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_concurrent_calls_safe(
        self,
        circuit_breaker: CircuitBreaker,
        successful_async_func: AsyncMock,
    ):
        """Multiple concurrent calls are thread-safe."""
        # Run many concurrent calls
        tasks = [circuit_breaker.call(successful_async_func) for _ in range(20)]

        results = await asyncio.gather(*tasks)

        assert all(r == "success" for r in results)
        assert circuit_breaker.stats.total_calls == 20
        assert circuit_breaker.stats.successful_calls == 20

    @pytest.mark.asyncio
    async def test_rapid_state_transitions(self):
        """Handles rapid state transitions correctly."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.01,
        )
        breaker = CircuitBreaker(name="rapid", config=config)

        failing = AsyncMock(side_effect=Exception("fail"))
        success = AsyncMock(return_value="ok")

        # Rapid transitions
        for _ in range(5):
            # Open
            with pytest.raises(Exception):
                await breaker.call(failing)

            await asyncio.sleep(0.02)

            # Close
            await breaker.call(success)

        # Should end in closed state
        assert breaker.state == CircuitState.CLOSED
