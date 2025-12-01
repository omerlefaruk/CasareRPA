"""Tests for retry module."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from casare_rpa.utils.resilience.retry import (
    ErrorCategory,
    classify_error,
    RetryConfig,
    retry_async,
    with_retry,
    with_timeout,
    retry_with_timeout,
    RetryStats,
    TRANSIENT_EXCEPTIONS,
)


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert ErrorCategory.TRANSIENT.value == "transient"
        assert ErrorCategory.PERMANENT.value == "permanent"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestClassifyError:
    """Tests for classify_error function."""

    def test_timeout_error_is_transient(self):
        """Test that TimeoutError is classified as transient."""
        assert classify_error(asyncio.TimeoutError()) == ErrorCategory.TRANSIENT
        assert classify_error(TimeoutError()) == ErrorCategory.TRANSIENT

    def test_connection_errors_are_transient(self):
        """Test that connection errors are transient."""
        assert classify_error(ConnectionError()) == ErrorCategory.TRANSIENT
        assert classify_error(ConnectionResetError()) == ErrorCategory.TRANSIENT
        assert classify_error(ConnectionRefusedError()) == ErrorCategory.TRANSIENT

    def test_os_error_is_transient(self):
        """Test that OSError is transient."""
        assert classify_error(OSError()) == ErrorCategory.TRANSIENT

    def test_pattern_based_classification(self):
        """Test classification based on error message patterns."""
        assert (
            classify_error(Exception("Connection timed out")) == ErrorCategory.TRANSIENT
        )
        assert (
            classify_error(Exception("Rate limit exceeded")) == ErrorCategory.TRANSIENT
        )
        assert (
            classify_error(Exception("Service temporarily unavailable"))
            == ErrorCategory.TRANSIENT
        )
        assert classify_error(Exception("Too many requests")) == ErrorCategory.TRANSIENT

    def test_unknown_error_classification(self):
        """Test that unknown errors are classified as unknown."""
        assert (
            classify_error(ValueError("Some validation error")) == ErrorCategory.UNKNOWN
        )
        assert classify_error(KeyError("missing_key")) == ErrorCategory.UNKNOWN


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
        assert config.retry_on is None
        assert config.retry_if is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=10.0,
            backoff_multiplier=1.5,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 10.0
        assert config.backoff_multiplier == 1.5
        assert config.jitter is False

    def test_should_retry_respects_max_attempts(self):
        """Test that should_retry respects max_attempts."""
        config = RetryConfig(max_attempts=3)
        error = ConnectionError()

        assert config.should_retry(error, 1) is True
        assert config.should_retry(error, 2) is True
        assert config.should_retry(error, 3) is False
        assert config.should_retry(error, 4) is False

    def test_should_retry_with_custom_retry_if(self):
        """Test should_retry with custom retry_if function."""
        config = RetryConfig(
            max_attempts=3, retry_if=lambda e: isinstance(e, ValueError)
        )

        assert config.should_retry(ValueError(), 1) is True
        assert config.should_retry(KeyError(), 1) is False

    def test_should_retry_with_retry_on_types(self):
        """Test should_retry with specific exception types."""
        config = RetryConfig(max_attempts=3, retry_on={ValueError, TypeError})

        assert config.should_retry(ValueError(), 1) is True
        assert config.should_retry(TypeError(), 1) is True
        assert config.should_retry(KeyError(), 1) is False

    def test_get_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=30.0,
            jitter=False,
        )

        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0
        assert config.get_delay(4) == 8.0

    def test_get_delay_capped_at_max(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=10.0,
            backoff_multiplier=2.0,
            max_delay=30.0,
            jitter=False,
        )

        assert config.get_delay(1) == 10.0
        assert config.get_delay(2) == 20.0
        assert config.get_delay(3) == 30.0  # Capped
        assert config.get_delay(4) == 30.0  # Capped

    def test_get_delay_with_jitter(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            jitter=True,
        )

        # With jitter, delays should vary
        delays = [config.get_delay(1) for _ in range(10)]
        # Not all should be exactly 1.0
        assert not all(d == 1.0 for d in delays)
        # But should be within ±25% of 1.0
        for d in delays:
            assert 0.75 <= d <= 1.25


class TestRetryAsync:
    """Tests for retry_async function."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_async(mock_func)

        assert result == "success"
        mock_func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test function succeeds after some retries."""
        mock_func = AsyncMock(
            side_effect=[ConnectionError(), ConnectionError(), "success"]
        )
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)

        result = await retry_async(mock_func, config=config)

        assert result == "success"
        assert mock_func.await_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        """Test that exception is raised after max attempts."""
        mock_func = AsyncMock(side_effect=ConnectionError("Failed"))
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)

        with pytest.raises(ConnectionError):
            await retry_async(mock_func, config=config)

        assert mock_func.await_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test that permanent errors are not retried."""
        mock_func = AsyncMock(side_effect=ValueError("Invalid"))
        config = RetryConfig(max_attempts=3, initial_delay=0.01)

        with pytest.raises(ValueError):
            await retry_async(mock_func, config=config)

        # Should only try once for non-transient error
        mock_func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        """Test that args and kwargs are passed to function."""
        mock_func = AsyncMock(return_value="result")

        await retry_async(mock_func, "arg1", "arg2", kwarg1="value1")

        mock_func.assert_awaited_once_with("arg1", "arg2", kwarg1="value1")


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorated function succeeds."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError()
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function metadata."""

        @with_retry()
        async def my_function():
            pass

        assert my_function.__name__ == "my_function"


class TestWithTimeout:
    """Tests for with_timeout function."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        """Test function that completes within timeout."""

        async def quick_func():
            return "done"

        result = await with_timeout(quick_func(), timeout=1.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """Test that TimeoutError is raised when function times out."""

        async def slow_func():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await with_timeout(slow_func(), timeout=0.01)

    @pytest.mark.asyncio
    async def test_cleanup_called_on_timeout(self):
        """Test that cleanup function is called on timeout."""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        async def slow_func():
            await asyncio.sleep(10)

        with pytest.raises(asyncio.TimeoutError):
            await with_timeout(slow_func(), timeout=0.01, cleanup=cleanup)

        assert cleanup_called is True

    @pytest.mark.asyncio
    async def test_async_cleanup_called_on_timeout(self):
        """Test that async cleanup function is called on timeout."""
        cleanup_called = False

        async def async_cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        async def slow_func():
            await asyncio.sleep(10)

        with pytest.raises(asyncio.TimeoutError):
            await with_timeout(slow_func(), timeout=0.01, cleanup=async_cleanup)

        assert cleanup_called is True


class TestRetryWithTimeout:
    """Tests for retry_with_timeout function."""

    @pytest.mark.asyncio
    async def test_success_within_timeout(self):
        """Test function succeeds within timeout."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_with_timeout(mock_func, timeout=1.0)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        """Test that timeouts trigger retries."""
        call_count = 0

        async def sometimes_slow():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                await asyncio.sleep(10)  # Will timeout
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        result = await retry_with_timeout(
            sometimes_slow,
            timeout=0.05,
            retry_config=config,
        )

        assert result == "success"
        assert call_count == 2


class TestRetryStats:
    """Tests for RetryStats class."""

    def test_initial_values(self):
        """Test initial stat values."""
        stats = RetryStats()
        assert stats.total_attempts == 0
        assert stats.successful_attempts == 0
        assert stats.failed_attempts == 0
        assert stats.retries_performed == 0
        assert stats.total_retry_delay == 0.0

    def test_record_successful_attempt(self):
        """Test recording successful attempt."""
        stats = RetryStats()
        stats.record_attempt(success=True)

        assert stats.total_attempts == 1
        assert stats.successful_attempts == 1
        assert stats.failed_attempts == 0

    def test_record_failed_attempt(self):
        """Test recording failed attempt."""
        stats = RetryStats()
        stats.record_attempt(success=False)

        assert stats.total_attempts == 1
        assert stats.successful_attempts == 0
        assert stats.failed_attempts == 1

    def test_record_retry_with_delay(self):
        """Test recording attempt with retry delay."""
        stats = RetryStats()
        stats.record_attempt(success=False, retry_delay=1.5)

        assert stats.retries_performed == 1
        assert stats.total_retry_delay == 1.5

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = RetryStats()
        stats.record_attempt(success=True)
        stats.record_attempt(success=True)
        stats.record_attempt(success=False)
        stats.record_attempt(success=True)

        assert stats.success_rate == 75.0

    def test_success_rate_zero_attempts(self):
        """Test success rate with zero attempts."""
        stats = RetryStats()
        assert stats.success_rate == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = RetryStats()
        stats.record_attempt(success=True)
        stats.record_attempt(success=False, retry_delay=1.0)

        result = stats.to_dict()

        assert result["total_attempts"] == 2
        assert result["successful_attempts"] == 1
        assert result["failed_attempts"] == 1
        assert result["retries_performed"] == 1
        assert result["total_retry_delay"] == 1.0
        assert result["success_rate"] == 50.0
