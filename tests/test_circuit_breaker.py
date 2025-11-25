"""
Tests for Circuit Breaker pattern implementation.

Tests state machine transitions, failure thresholds, recovery behavior,
and statistics tracking.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

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


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_config():
    """Create default circuit breaker config."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=5.0,
        half_open_max_calls=2,
    )


@pytest.fixture
def circuit_breaker(default_config):
    """Create a circuit breaker for testing."""
    return CircuitBreaker("test_circuit", default_config)


@pytest.fixture
async def async_success_func():
    """Create an async function that succeeds."""
    async def func():
        return "success"
    return func


@pytest.fixture
async def async_failure_func():
    """Create an async function that fails."""
    async def func():
        raise ValueError("Test failure")
    return func


# ============================================================================
# Configuration Tests
# ============================================================================

class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=30.0,
            half_open_max_calls=1,
        )

        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout == 30.0
        assert config.half_open_max_calls == 1


# ============================================================================
# State Machine Tests
# ============================================================================

class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state machine transitions."""

    def test_initial_state_is_closed(self, circuit_breaker):
        """Test that initial state is CLOSED."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed is True
        assert circuit_breaker.is_open is False

    @pytest.mark.asyncio
    async def test_closed_to_open_on_failures(self, circuit_breaker):
        """Test transition from CLOSED to OPEN after failure threshold."""
        async def failing_func():
            raise ValueError("failure")

        # Cause failures up to threshold
        for i in range(3):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        # Should now be OPEN
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self, default_config):
        """Test transition from OPEN to HALF_OPEN after timeout."""
        # Create config with very short timeout
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.1,  # 100ms
            half_open_max_calls=1,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        # Trigger OPEN state
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Next call should trigger state check -> HALF_OPEN
        async def success_func():
            return "ok"

        result = await cb.call(success_func)
        # State should have transitioned through HALF_OPEN
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self, default_config):
        """Test transition from HALF_OPEN to CLOSED after success threshold."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.1,
            half_open_max_calls=5,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        async def success_func():
            return "ok"

        # Trigger OPEN
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        await asyncio.sleep(0.2)  # Wait for timeout

        # Call successes to close circuit
        await cb.call(success_func)
        await cb.call(success_func)

        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self, default_config):
        """Test transition from HALF_OPEN back to OPEN on failure."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.1,
            half_open_max_calls=5,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        # Trigger OPEN
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        await asyncio.sleep(0.2)  # Wait for timeout

        # Next call in HALF_OPEN fails -> back to OPEN
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN


# ============================================================================
# Blocking Tests
# ============================================================================

class TestCircuitBreakerBlocking:
    """Test circuit breaker blocking behavior."""

    @pytest.mark.asyncio
    async def test_open_circuit_blocks_calls(self, circuit_breaker):
        """Test that OPEN circuit blocks calls."""
        async def failing_func():
            raise ValueError("failure")

        async def success_func():
            return "ok"

        # Trigger OPEN
        for i in range(3):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        # Now calls should be blocked
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await circuit_breaker.call(success_func)

        assert exc_info.value.circuit_name == "test_circuit"
        assert exc_info.value.remaining_seconds >= 0

    @pytest.mark.asyncio
    async def test_half_open_limits_concurrent_calls(self):
        """Test that HALF_OPEN limits concurrent calls."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.1,
            half_open_max_calls=1,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        async def slow_success_func():
            await asyncio.sleep(0.5)
            return "ok"

        # Trigger OPEN
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        await asyncio.sleep(0.2)  # Wait for timeout

        # First call goes through (starts slow)
        task1 = asyncio.create_task(cb.call(slow_success_func))

        await asyncio.sleep(0.05)  # Let first call start

        # Second call should be blocked (half_open_max_calls=1)
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(slow_success_func)

        await task1


# ============================================================================
# Success/Failure Counting Tests
# ============================================================================

class TestCircuitBreakerCounting:
    """Test success/failure counting."""

    @pytest.mark.asyncio
    async def test_failure_count_increments(self, circuit_breaker):
        """Test that failure count increments correctly."""
        async def failing_func():
            raise ValueError("failure")

        for i in range(2):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        status = circuit_breaker.get_status()
        assert status["failure_count"] == 2

    @pytest.mark.asyncio
    async def test_failure_count_resets_on_success(self, circuit_breaker):
        """Test that failure count resets after success in CLOSED state."""
        async def failing_func():
            raise ValueError("failure")

        async def success_func():
            return "ok"

        # Accumulate some failures (but not enough to open)
        for i in range(2):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        # Success should reset count
        await circuit_breaker.call(success_func)

        status = circuit_breaker.get_status()
        assert status["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_success_count_in_half_open(self):
        """Test success counting in HALF_OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=3,
            timeout=0.1,
            half_open_max_calls=5,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        async def success_func():
            return "ok"

        # Trigger OPEN
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        await asyncio.sleep(0.2)

        # Count successes in HALF_OPEN
        await cb.call(success_func)

        status = cb.get_status()
        assert status["success_count"] == 1


# ============================================================================
# Statistics Tests
# ============================================================================

class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""

    def test_stats_initialization(self):
        """Test initial stats values."""
        stats = CircuitBreakerStats()

        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.blocked_calls == 0
        assert stats.times_opened == 0

    def test_stats_to_dict(self):
        """Test stats conversion to dictionary."""
        stats = CircuitBreakerStats()
        stats.total_calls = 100
        stats.successful_calls = 80
        stats.failed_calls = 20
        stats.blocked_calls = 5
        stats.times_opened = 2

        data = stats.to_dict()

        assert data["total_calls"] == 100
        assert data["successful_calls"] == 80
        assert data["failed_calls"] == 20
        assert data["blocked_calls"] == 5
        assert data["times_opened"] == 2
        assert data["success_rate"] == 80.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = CircuitBreakerStats()

        # Zero calls -> 0% rate
        assert stats.to_dict()["success_rate"] == 0

        stats.total_calls = 10
        stats.successful_calls = 7

        assert stats.to_dict()["success_rate"] == 70.0

    @pytest.mark.asyncio
    async def test_stats_tracked_during_operation(self, circuit_breaker):
        """Test that stats are tracked during operations."""
        async def success_func():
            return "ok"

        async def failing_func():
            raise ValueError("failure")

        # Call successes
        await circuit_breaker.call(success_func)
        await circuit_breaker.call(success_func)

        # Call failures
        for i in range(3):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        stats = circuit_breaker.stats.to_dict()

        assert stats["total_calls"] == 5
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 3
        assert stats["times_opened"] == 1

    @pytest.mark.asyncio
    async def test_blocked_calls_tracked(self, circuit_breaker):
        """Test that blocked calls are tracked."""
        async def failing_func():
            raise ValueError("failure")

        async def success_func():
            return "ok"

        # Trigger OPEN
        for i in range(3):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        # Try to call (should be blocked)
        for i in range(2):
            try:
                await circuit_breaker.call(success_func)
            except CircuitBreakerOpenError:
                pass

        assert circuit_breaker.stats.blocked_calls == 2


# ============================================================================
# Manual Control Tests
# ============================================================================

class TestCircuitBreakerManualControl:
    """Test manual circuit breaker control."""

    @pytest.mark.asyncio
    async def test_manual_reset(self, circuit_breaker):
        """Test manual reset to CLOSED state."""
        async def failing_func():
            raise ValueError("failure")

        # Trigger OPEN
        for i in range(3):
            try:
                await circuit_breaker.call(failing_func)
            except ValueError:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Manual reset
        await circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.get_status()["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_force_open(self, circuit_breaker):
        """Test force open functionality."""
        assert circuit_breaker.state == CircuitState.CLOSED

        await circuit_breaker.force_open()

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_open is True


# ============================================================================
# State Change Callback Tests
# ============================================================================

class TestCircuitBreakerCallbacks:
    """Test state change callbacks."""

    @pytest.mark.asyncio
    async def test_state_change_callback_called(self):
        """Test that state change callback is invoked."""
        callback_calls = []

        def on_state_change(old_state, new_state):
            callback_calls.append((old_state, new_state))

        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config, on_state_change)

        async def failing_func():
            raise ValueError("failure")

        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        # Should have recorded state change
        assert len(callback_calls) == 1
        assert callback_calls[0] == (CircuitState.CLOSED, CircuitState.OPEN)

    @pytest.mark.asyncio
    async def test_callback_exception_handled(self):
        """Test that callback exceptions are handled."""
        def bad_callback(old_state, new_state):
            raise RuntimeError("Callback error")

        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config, bad_callback)

        async def failing_func():
            raise ValueError("failure")

        # Should not raise despite callback error
        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        # Circuit should still transition
        assert cb.state == CircuitState.OPEN


# ============================================================================
# Registry Tests
# ============================================================================

class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def test_get_or_create_new(self):
        """Test creating new circuit breaker via registry."""
        registry = CircuitBreakerRegistry()

        cb = registry.get_or_create("new_circuit")

        assert cb is not None
        assert cb.name == "new_circuit"

    def test_get_or_create_existing(self):
        """Test getting existing circuit breaker."""
        registry = CircuitBreakerRegistry()

        cb1 = registry.get_or_create("circuit")
        cb2 = registry.get_or_create("circuit")

        assert cb1 is cb2

    def test_get_existing(self):
        """Test getting existing circuit breaker."""
        registry = CircuitBreakerRegistry()

        registry.get_or_create("circuit")
        cb = registry.get("circuit")

        assert cb is not None
        assert cb.name == "circuit"

    def test_get_nonexistent(self):
        """Test getting non-existent circuit breaker."""
        registry = CircuitBreakerRegistry()

        cb = registry.get("nonexistent")

        assert cb is None

    def test_get_all_status(self):
        """Test getting status of all circuit breakers."""
        registry = CircuitBreakerRegistry()

        registry.get_or_create("circuit1")
        registry.get_or_create("circuit2")

        all_status = registry.get_all_status()

        assert "circuit1" in all_status
        assert "circuit2" in all_status
        assert all_status["circuit1"]["name"] == "circuit1"

    @pytest.mark.asyncio
    async def test_reset_all(self):
        """Test resetting all circuit breakers."""
        registry = CircuitBreakerRegistry()

        cb1 = registry.get_or_create("circuit1")
        cb2 = registry.get_or_create("circuit2")

        await cb1.force_open()
        await cb2.force_open()

        await registry.reset_all()

        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED


# ============================================================================
# Global Function Tests
# ============================================================================

class TestGlobalFunctions:
    """Test global helper functions."""

    def test_get_circuit_breaker(self):
        """Test global get_circuit_breaker function."""
        cb = get_circuit_breaker("global_test")

        assert cb is not None
        assert cb.name == "global_test"

    def test_get_circuit_breaker_registry(self):
        """Test global get_circuit_breaker_registry function."""
        registry = get_circuit_breaker_registry()

        assert registry is not None
        assert isinstance(registry, CircuitBreakerRegistry)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_sync_function_support(self, circuit_breaker):
        """Test that sync functions are supported."""
        def sync_func():
            return "sync_result"

        result = await circuit_breaker.call(sync_func)

        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_function_with_args(self, circuit_breaker):
        """Test function with arguments."""
        async def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await circuit_breaker.call(func_with_args, "x", "y", c="z")

        assert result == "x-y-z"

    @pytest.mark.asyncio
    async def test_get_status(self, circuit_breaker):
        """Test get_status returns all expected fields."""
        status = circuit_breaker.get_status()

        assert "name" in status
        assert "state" in status
        assert "failure_count" in status
        assert "success_count" in status
        assert "last_failure_time" in status
        assert "opened_at" in status
        assert "remaining_open_time" in status
        assert "stats" in status

    @pytest.mark.asyncio
    async def test_remaining_open_time_decreases(self):
        """Test that remaining open time decreases."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=1.0,
        )
        cb = CircuitBreaker("test", config)

        async def failing_func():
            raise ValueError("failure")

        try:
            await cb.call(failing_func)
        except ValueError:
            pass

        time1 = cb.get_status()["remaining_open_time"]
        await asyncio.sleep(0.2)
        time2 = cb.get_status()["remaining_open_time"]

        assert time2 < time1
