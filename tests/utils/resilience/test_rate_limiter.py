"""Tests for rate_limiter module."""

import asyncio
import time
import pytest

from casare_rpa.utils.resilience.rate_limiter import (
    RateLimitConfig,
    RateLimitStats,
    RateLimiter,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    rate_limited,
    get_rate_limiter,
    clear_rate_limiters,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_second == 10.0
        assert config.burst_size == 1
        assert config.retry_after_limit is True
        assert config.max_wait_time == 60.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_second=5.0,
            burst_size=10,
            retry_after_limit=False,
            max_wait_time=30.0,
        )
        assert config.requests_per_second == 5.0
        assert config.burst_size == 10
        assert config.retry_after_limit is False
        assert config.max_wait_time == 30.0

    def test_min_interval_property(self):
        """Test min_interval calculation."""
        config = RateLimitConfig(requests_per_second=10.0)
        assert config.min_interval == 0.1

        config = RateLimitConfig(requests_per_second=5.0)
        assert config.min_interval == 0.2

    def test_min_interval_zero_rps(self):
        """Test min_interval with zero requests per second."""
        config = RateLimitConfig(requests_per_second=0.0)
        assert config.min_interval == 0


class TestRateLimitStats:
    """Tests for RateLimitStats class."""

    def test_default_values(self):
        """Test default stat values."""
        stats = RateLimitStats()
        assert stats.total_requests == 0
        assert stats.requests_delayed == 0
        assert stats.total_delay_time == 0.0
        assert stats.requests_rejected == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = RateLimitStats(
            total_requests=100,
            requests_delayed=10,
            total_delay_time=5.5,
            requests_rejected=2,
        )

        result = stats.to_dict()

        assert result["total_requests"] == 100
        assert result["requests_delayed"] == 10
        assert result["total_delay_time"] == 5.5
        assert result["requests_rejected"] == 2
        assert result["avg_delay"] == 0.55

    def test_avg_delay_zero_delayed(self):
        """Test avg_delay calculation with zero delayed requests."""
        stats = RateLimitStats(
            total_requests=100,
            requests_delayed=0,
            total_delay_time=0.0,
        )

        result = stats.to_dict()
        assert result["avg_delay"] == 0


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        config = RateLimitConfig(requests_per_second=5.0, burst_size=3)
        limiter = RateLimiter(config)

        assert limiter.config == config
        assert limiter._tokens == 3.0

    def test_default_config(self):
        """Test rate limiter with default config."""
        limiter = RateLimiter()
        assert limiter.config.requests_per_second == 10.0

    @pytest.mark.asyncio
    async def test_acquire_immediate_success(self):
        """Test immediate acquisition when tokens available."""
        config = RateLimitConfig(requests_per_second=100.0, burst_size=10)
        limiter = RateLimiter(config)

        result = await limiter.acquire()

        assert result is True
        assert limiter._tokens < 10.0

    @pytest.mark.asyncio
    async def test_acquire_multiple(self):
        """Test acquiring multiple requests."""
        config = RateLimitConfig(requests_per_second=1000.0, burst_size=5)
        limiter = RateLimiter(config)

        for _ in range(5):
            result = await limiter.acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_waits_when_exhausted(self):
        """Test that acquire waits when tokens exhausted."""
        config = RateLimitConfig(
            requests_per_second=100.0,
            burst_size=1,
            max_wait_time=5.0,
        )
        limiter = RateLimiter(config)

        # Exhaust tokens
        await limiter.acquire()

        # Next acquire should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should have waited some time (at least a few ms)
        assert elapsed >= 0.005

    @pytest.mark.asyncio
    async def test_acquire_raises_when_wait_too_long(self):
        """Test that acquire raises when wait exceeds max_wait_time."""
        config = RateLimitConfig(
            requests_per_second=0.1,  # Very slow
            burst_size=1,
            max_wait_time=0.01,  # Very short
            retry_after_limit=False,
        )
        limiter = RateLimiter(config)

        # Exhaust tokens
        await limiter.acquire()

        # Next acquire should raise
        with pytest.raises(RateLimitExceeded):
            await limiter.acquire()

    def test_try_acquire_success(self):
        """Test non-blocking acquire succeeds."""
        config = RateLimitConfig(requests_per_second=100.0, burst_size=5)
        limiter = RateLimiter(config)

        result = limiter.try_acquire()

        assert result is True

    def test_try_acquire_fails_when_exhausted(self):
        """Test non-blocking acquire fails when tokens exhausted."""
        config = RateLimitConfig(requests_per_second=1.0, burst_size=1)
        limiter = RateLimiter(config)

        # First should succeed
        assert limiter.try_acquire() is True

        # Second should fail (no waiting)
        assert limiter.try_acquire() is False

    def test_reset(self):
        """Test resetting the rate limiter."""
        config = RateLimitConfig(requests_per_second=1.0, burst_size=5)
        limiter = RateLimiter(config)

        # Exhaust some tokens
        limiter.try_acquire()
        limiter.try_acquire()
        limiter.try_acquire()

        # Reset
        limiter.reset()

        # Should be back to full tokens
        assert limiter._tokens == 5.0

    def test_stats_tracking(self):
        """Test that stats are tracked correctly."""
        config = RateLimitConfig(requests_per_second=100.0, burst_size=5)
        limiter = RateLimiter(config)

        limiter.try_acquire()
        limiter.try_acquire()

        assert limiter.stats.total_requests == 2


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter class."""

    def test_initialization(self):
        """Test sliding window rate limiter initialization."""
        limiter = SlidingWindowRateLimiter(
            max_requests=10,
            window_seconds=1.0,
            max_wait_time=30.0,
        )

        assert limiter.max_requests == 10
        assert limiter.window_seconds == 1.0
        assert limiter.max_wait_time == 30.0

    def test_default_values(self):
        """Test default initialization values."""
        limiter = SlidingWindowRateLimiter()
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 1.0
        assert limiter.max_wait_time == 60.0

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquire within rate limit."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)

        for _ in range(5):
            result = await limiter.acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_waits_when_exceeded(self):
        """Test that acquire waits when limit exceeded."""
        limiter = SlidingWindowRateLimiter(
            max_requests=2,
            window_seconds=0.1,
            max_wait_time=1.0,
        )

        # Make requests up to limit
        await limiter.acquire()
        await limiter.acquire()

        # Next should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should have waited for the window to slide
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_acquire_raises_when_wait_too_long(self):
        """Test that acquire raises when wait exceeds max_wait_time."""
        limiter = SlidingWindowRateLimiter(
            max_requests=1,
            window_seconds=10.0,  # Long window
            max_wait_time=0.01,  # Short wait
        )

        # Use up the limit
        await limiter.acquire()

        # Next should raise
        with pytest.raises(RateLimitExceeded):
            await limiter.acquire()

    def test_try_acquire_success(self):
        """Test non-blocking acquire succeeds."""
        limiter = SlidingWindowRateLimiter(max_requests=5)

        result = limiter.try_acquire()

        assert result is True

    def test_try_acquire_fails_when_exceeded(self):
        """Test non-blocking acquire fails when limit exceeded."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10.0)

        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False

    def test_reset(self):
        """Test resetting the sliding window limiter."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10.0)

        limiter.try_acquire()
        limiter.try_acquire()
        assert limiter.try_acquire() is False

        limiter.reset()

        # After reset, should be able to acquire again
        assert limiter.try_acquire() is True

    def test_stats_tracking(self):
        """Test that stats are tracked correctly."""
        limiter = SlidingWindowRateLimiter(max_requests=5)

        limiter.try_acquire()
        limiter.try_acquire()

        assert limiter.stats.total_requests == 2


class TestRateLimitedDecorator:
    """Tests for rate_limited decorator."""

    @pytest.mark.asyncio
    async def test_decorator_applies_rate_limit(self):
        """Test that decorator applies rate limiting."""
        call_count = 0

        @rate_limited(requests_per_second=100.0, burst_size=2)
        async def limited_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # First two should be immediate (within burst)
        result1 = await limited_func()
        result2 = await limited_func()

        assert result1 == 1
        assert result2 == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_return_value(self):
        """Test that decorator preserves function return value."""

        @rate_limited(requests_per_second=100.0)
        async def func_with_return():
            return "expected_value"

        result = await func_with_return()
        assert result == "expected_value"


class TestGlobalRateLimiters:
    """Tests for global rate limiter functions."""

    def test_get_rate_limiter_creates_new(self):
        """Test that get_rate_limiter creates new limiter."""
        clear_rate_limiters()

        limiter = get_rate_limiter("test_limiter", requests_per_second=5.0)

        assert limiter is not None
        assert limiter.config.requests_per_second == 5.0

    def test_get_rate_limiter_returns_same(self):
        """Test that get_rate_limiter returns same instance."""
        clear_rate_limiters()

        limiter1 = get_rate_limiter("same_name")
        limiter2 = get_rate_limiter("same_name")

        assert limiter1 is limiter2

    def test_get_rate_limiter_different_names(self):
        """Test that different names get different limiters."""
        clear_rate_limiters()

        limiter1 = get_rate_limiter("name1")
        limiter2 = get_rate_limiter("name2")

        assert limiter1 is not limiter2

    def test_clear_rate_limiters(self):
        """Test clearing all global rate limiters."""
        get_rate_limiter("test1")
        get_rate_limiter("test2")

        clear_rate_limiters()

        # After clear, new limiter should be created
        limiter = get_rate_limiter("test1")
        assert limiter is not None
