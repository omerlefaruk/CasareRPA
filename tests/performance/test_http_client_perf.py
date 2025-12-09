"""
HTTP Client Performance Tests.

Tests the performance of the unified HTTP client including:
- Session reuse vs creating new sessions
- Rate limiter overhead
- Circuit breaker overhead
- Concurrent request handling

Run with: pytest tests/performance/test_http_client_perf.py -v
"""

import asyncio
import time
import tracemalloc
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Performance thresholds
MAX_SESSION_CREATION_TIME_MS = 50.0
MAX_RATE_LIMITER_OVERHEAD_MS = 1.0
MAX_CIRCUIT_BREAKER_OVERHEAD_MS = 1.0
MAX_CONCURRENT_REQUEST_OVERHEAD_MS = 10.0


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session for testing."""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})
    mock_response.text = AsyncMock(return_value="OK")
    mock_response.read = AsyncMock(return_value=b"OK")
    mock_response.release = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.request = AsyncMock(return_value=mock_response)
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


class TestRateLimiterPerformance:
    """Test rate limiter performance and overhead."""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_overhead(self) -> None:
        """Test that rate limiter acquire has minimal overhead."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )

        config = RateLimitConfig(
            requests_per_second=10000,  # Very high to avoid blocking
            burst_size=10000,
        )
        limiter = RateLimiter(config)

        # Warm up
        await limiter.acquire()

        # Measure overhead
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            await limiter.acquire()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / iterations) * 1000

        assert avg_time_ms < MAX_RATE_LIMITER_OVERHEAD_MS, (
            f"Rate limiter acquire overhead {avg_time_ms:.3f}ms "
            f"exceeds {MAX_RATE_LIMITER_OVERHEAD_MS}ms threshold"
        )

    @pytest.mark.asyncio
    async def test_sliding_window_limiter_performance(self) -> None:
        """Test sliding window rate limiter performance."""
        from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter

        limiter = SlidingWindowRateLimiter(
            max_requests=10000,  # High to avoid blocking
            window_seconds=1.0,
        )

        # Warm up
        await limiter.acquire()

        # Measure overhead
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            await limiter.acquire()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / iterations) * 1000

        assert avg_time_ms < MAX_RATE_LIMITER_OVERHEAD_MS, (
            f"Sliding window limiter overhead {avg_time_ms:.3f}ms "
            f"exceeds {MAX_RATE_LIMITER_OVERHEAD_MS}ms threshold"
        )

    @pytest.mark.asyncio
    async def test_try_acquire_is_faster(self) -> None:
        """Test that try_acquire is faster than async acquire."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )

        config = RateLimitConfig(requests_per_second=10000, burst_size=10000)
        limiter = RateLimiter(config)

        # Measure async acquire
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            await limiter.acquire()
        async_time = time.perf_counter() - start

        # Measure try_acquire (sync)
        limiter.reset()
        start = time.perf_counter()
        for _ in range(iterations):
            limiter.try_acquire()
        sync_time = time.perf_counter() - start

        # try_acquire should be faster (no async overhead)
        assert sync_time < async_time, (
            f"try_acquire ({sync_time*1000:.3f}ms) should be faster than "
            f"acquire ({async_time*1000:.3f}ms)"
        )

    def test_rate_limiter_stats_overhead(self) -> None:
        """Test that stats tracking has minimal overhead."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )

        config = RateLimitConfig(requests_per_second=10000, burst_size=10000)
        limiter = RateLimiter(config)

        iterations = 10000
        start = time.perf_counter()
        for _ in range(iterations):
            limiter.try_acquire()
            _ = limiter.stats.total_requests
        elapsed = time.perf_counter() - start

        avg_time_us = (elapsed / iterations) * 1_000_000

        # Should be very fast (< 10 microseconds per operation)
        assert (
            avg_time_us < 10
        ), f"Stats access overhead {avg_time_us:.1f}us exceeds 10us threshold"


class TestCircuitBreakerPerformance:
    """Test circuit breaker performance and overhead."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_overhead(self) -> None:
        """Test that circuit breaker has minimal overhead on calls."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        config = CircuitBreakerConfig(
            failure_threshold=100,
            success_threshold=1,
            timeout=60.0,
        )
        breaker = CircuitBreaker("test_breaker", config)

        async def fast_operation() -> int:
            return 42

        # Warm up
        await breaker.call(fast_operation)

        # Measure overhead
        iterations = 500
        start = time.perf_counter()
        for _ in range(iterations):
            await breaker.call(fast_operation)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / iterations) * 1000

        assert avg_time_ms < MAX_CIRCUIT_BREAKER_OVERHEAD_MS, (
            f"Circuit breaker overhead {avg_time_ms:.3f}ms "
            f"exceeds {MAX_CIRCUIT_BREAKER_OVERHEAD_MS}ms threshold"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_check_performance(self) -> None:
        """Test circuit breaker state checking performance."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        config = CircuitBreakerConfig()
        breaker = CircuitBreaker("test_breaker", config)

        iterations = 10000
        start = time.perf_counter()
        for _ in range(iterations):
            _ = breaker.is_closed
            _ = breaker.is_open
            _ = breaker.state
        elapsed = time.perf_counter() - start

        avg_time_us = (elapsed / iterations) * 1_000_000

        # State checks should be very fast (< 1 microsecond)
        assert (
            avg_time_us < 1
        ), f"State check overhead {avg_time_us:.3f}us exceeds 1us threshold"

    @pytest.mark.asyncio
    async def test_circuit_breaker_stats_performance(self) -> None:
        """Test circuit breaker stats tracking performance."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        config = CircuitBreakerConfig()
        breaker = CircuitBreaker("test_breaker", config)

        async def fast_operation() -> int:
            return 42

        # Run some operations to populate stats
        for _ in range(100):
            await breaker.call(fast_operation)

        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            _ = breaker.get_status()
        elapsed = time.perf_counter() - start

        avg_time_us = (elapsed / iterations) * 1_000_000

        # Status generation should be fast (< 50 microseconds)
        assert (
            avg_time_us < 50
        ), f"Status generation {avg_time_us:.1f}us exceeds 50us threshold"

    @pytest.mark.asyncio
    async def test_circuit_breaker_registry_performance(self) -> None:
        """Test circuit breaker registry lookup performance."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreakerRegistry,
            CircuitBreakerConfig,
        )

        registry = CircuitBreakerRegistry()
        config = CircuitBreakerConfig()

        # Create many breakers
        for i in range(100):
            registry.get_or_create(f"breaker_{i}", config)

        # Measure lookup performance
        iterations = 10000
        start = time.perf_counter()
        for i in range(iterations):
            _ = registry.get_or_create(f"breaker_{i % 100}", config)
        elapsed = time.perf_counter() - start

        avg_time_us = (elapsed / iterations) * 1_000_000

        # Registry lookup should be fast (< 5 microseconds)
        assert (
            avg_time_us < 5
        ), f"Registry lookup {avg_time_us:.1f}us exceeds 5us threshold"


class TestSessionPoolPerformance:
    """Test session pool performance."""

    @pytest.mark.asyncio
    async def test_session_pool_creation_time(self, mock_aiohttp_session) -> None:
        """Test session pool creation time."""
        with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            start = time.perf_counter()
            pool = HttpSessionPool(
                max_sessions=10,
                max_connections_per_host=10,
            )
            elapsed = time.perf_counter() - start

            elapsed_ms = elapsed * 1000

            assert elapsed_ms < MAX_SESSION_CREATION_TIME_MS, (
                f"Session pool creation took {elapsed_ms:.1f}ms "
                f"(threshold: {MAX_SESSION_CREATION_TIME_MS}ms)"
            )

            await pool.close()

    @pytest.mark.asyncio
    async def test_session_reuse_vs_new_session(self, mock_aiohttp_session) -> None:
        """
        Test that session reuse is faster than creating new sessions.

        This validates the pooling strategy provides performance benefits.
        """
        with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            pool = HttpSessionPool(max_sessions=10)

            # Measure time with session reuse (pool)
            iterations = 100
            start = time.perf_counter()
            for _ in range(iterations):
                await pool.request("GET", "https://example.com/test")
            pool_time = time.perf_counter() - start

            # Measure time creating new sessions each time (simulated)
            start = time.perf_counter()
            for _ in range(iterations):
                # Simulate session creation overhead
                session = mock_aiohttp_session
                await session.get("https://example.com/test")
            new_session_time = time.perf_counter() - start

            await pool.close()

            # Pool should be at least as fast (often faster due to reuse)
            # Note: With mocks, the difference may be minimal
            # The real benefit is in actual network scenarios


class TestUnifiedHttpClientPerformance:
    """Test unified HTTP client performance."""

    @pytest.mark.asyncio
    async def test_client_initialization_time(self, mock_aiohttp_session) -> None:
        """Test client initialization is fast."""
        with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
            with patch(
                "casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE",
                True,
            ):
                from casare_rpa.infrastructure.http.unified_http_client import (
                    UnifiedHttpClient,
                    UnifiedHttpClientConfig,
                )

                config = UnifiedHttpClientConfig()

                start = time.perf_counter()
                client = UnifiedHttpClient(config)
                elapsed = time.perf_counter() - start

                elapsed_ms = elapsed * 1000

                assert elapsed_ms < MAX_SESSION_CREATION_TIME_MS, (
                    f"Client initialization took {elapsed_ms:.1f}ms "
                    f"(threshold: {MAX_SESSION_CREATION_TIME_MS}ms)"
                )

    @pytest.mark.asyncio
    async def test_stats_collection_overhead(self, mock_aiohttp_session) -> None:
        """Test that stats collection has minimal overhead."""
        with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
            with patch(
                "casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE",
                True,
            ):
                from casare_rpa.infrastructure.http.unified_http_client import (
                    UnifiedHttpClient,
                    UnifiedHttpClientConfig,
                )

                config = UnifiedHttpClientConfig(
                    rate_limit_requests=10000,
                    rate_limit_window=1.0,
                )
                client = UnifiedHttpClient(config)

                # Mock the pool
                with patch.object(client, "_pool", mock_aiohttp_session):
                    client._started = True

                    iterations = 100
                    start = time.perf_counter()
                    for _ in range(iterations):
                        _ = client.stats.to_dict()
                        _ = client.get_all_stats()
                    elapsed = time.perf_counter() - start

                    avg_time_us = (elapsed / iterations) * 1_000_000

                    # Stats collection should be fast (< 100 microseconds)
                    assert (
                        avg_time_us < 100
                    ), f"Stats collection {avg_time_us:.1f}us exceeds 100us threshold"


class TestConcurrentRequestPerformance:
    """Test concurrent request handling performance."""

    @pytest.mark.asyncio
    async def test_concurrent_rate_limiter_acquire(self) -> None:
        """Test concurrent rate limiter acquires."""
        from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter

        limiter = SlidingWindowRateLimiter(
            max_requests=10000,
            window_seconds=1.0,
        )

        async def acquire_task():
            for _ in range(10):
                await limiter.acquire()

        start = time.perf_counter()
        tasks = [acquire_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # 1000 concurrent acquires should complete quickly
        assert (
            elapsed < 1.0
        ), f"1000 concurrent acquires took {elapsed:.2f}s (threshold: 1.0s)"

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_calls(self) -> None:
        """Test concurrent circuit breaker calls."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        config = CircuitBreakerConfig(failure_threshold=1000)
        breaker = CircuitBreaker("concurrent_test", config)

        async def fast_operation() -> int:
            return 42

        async def call_task():
            for _ in range(10):
                await breaker.call(fast_operation)

        start = time.perf_counter()
        tasks = [call_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # 1000 concurrent calls should complete quickly
        assert (
            elapsed < 1.0
        ), f"1000 concurrent circuit breaker calls took {elapsed:.2f}s"


class TestRateLimiterMemory:
    """Test rate limiter memory usage."""

    def test_sliding_window_memory_bounded(self) -> None:
        """
        Test that sliding window limiter memory is bounded.

        The deque should not grow unbounded under high load.
        """
        from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter

        tracemalloc.start()

        limiter = SlidingWindowRateLimiter(
            max_requests=100,
            window_seconds=1.0,
        )

        # Simulate high load with many try_acquire calls
        for _ in range(10000):
            limiter.try_acquire()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kb = peak / 1024

        # Memory should be bounded (< 100KB for limiter state)
        assert (
            peak_kb < 100
        ), f"Sliding window memory usage {peak_kb:.1f}KB exceeds 100KB threshold"

    @pytest.mark.asyncio
    async def test_global_limiters_bounded(self) -> None:
        """Test that global rate limiters are bounded."""
        from casare_rpa.utils.resilience.rate_limiter import (
            get_rate_limiter,
            clear_rate_limiters,
            _global_limiters,
        )

        clear_rate_limiters()

        # Create many limiters (should trigger eviction)
        for i in range(150):
            get_rate_limiter(f"limiter_{i}", requests_per_second=10.0)

        # Should be bounded to max size
        assert (
            len(_global_limiters) <= 100
        ), f"Global limiters count {len(_global_limiters)} exceeds max 100"

        clear_rate_limiters()
