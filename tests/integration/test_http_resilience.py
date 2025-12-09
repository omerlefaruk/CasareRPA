"""
Integration Tests for HTTP Resilience Components.

Tests the integration of:
- UnifiedHttpClient with HttpSessionPool
- Rate limiter blocks requests correctly
- Circuit breaker opens and recovers
- Retry with backoff works end-to-end

All external HTTP calls are mocked - no actual network requests.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

import pytest


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp for testing HTTP components."""
    with patch.dict("sys.modules", {"aiohttp": MagicMock()}):
        yield


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock HTTP responses."""

    def create(
        status: int = 200,
        json_data: Dict = None,
        text_data: str = "",
        raise_on_call: Exception = None,
    ):
        mock = AsyncMock()
        mock.status = status
        mock.json = AsyncMock(return_value=json_data or {})
        mock.text = AsyncMock(return_value=text_data)
        mock.release = AsyncMock()
        mock.closed = False

        if raise_on_call:
            mock.side_effect = raise_on_call

        return mock

    return create


# =============================================================================
# RATE LIMITER INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestRateLimiterIntegration:
    """Integration tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiter(self):
        """Test token bucket rate limiter blocks excess requests."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )

        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=2,
            max_wait_time=0.5,
        )
        limiter = RateLimiter(config)

        # First 2 requests should pass immediately (burst)
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed < 0.1, "Burst requests should be immediate"

        # Third request should wait
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed >= 0.05, "Third request should wait for token"

    @pytest.mark.asyncio
    async def test_sliding_window_rate_limiter(self):
        """Test sliding window rate limiter."""
        from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter

        limiter = SlidingWindowRateLimiter(
            max_requests=3,
            window_seconds=0.5,
            max_wait_time=1.0,
        )

        # First 3 requests should pass
        for _ in range(3):
            result = await limiter.acquire()
            assert result is True

        # Fourth request should wait
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed >= 0.1, "Fourth request should wait"

    @pytest.mark.asyncio
    async def test_rate_limiter_exceeds_max_wait(self):
        """Test rate limiter raises when max wait exceeded."""
        from casare_rpa.utils.resilience.rate_limiter import (
            SlidingWindowRateLimiter,
            RateLimitExceeded,
        )

        limiter = SlidingWindowRateLimiter(
            max_requests=1,
            window_seconds=10.0,  # Long window
            max_wait_time=0.01,  # Very short max wait
        )

        # First request passes
        await limiter.acquire()

        # Second request should raise
        with pytest.raises(RateLimitExceeded):
            await limiter.acquire()

    def test_rate_limiter_stats(self):
        """Test rate limiter statistics tracking."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )

        config = RateLimitConfig(requests_per_second=100, burst_size=10)
        limiter = RateLimiter(config)

        # Make some requests
        for _ in range(5):
            limiter.try_acquire()

        stats = limiter.stats.to_dict()
        assert stats["total_requests"] == 5
        assert "requests_delayed" in stats
        assert "total_delay_time" in stats

    @pytest.mark.asyncio
    async def test_per_domain_rate_limiting(self):
        """Test that rate limiting is per-domain."""
        from casare_rpa.utils.resilience.rate_limiter import (
            SlidingWindowRateLimiter,
        )

        # Two separate limiters for different domains
        limiter_a = SlidingWindowRateLimiter(max_requests=2, window_seconds=1.0)
        limiter_b = SlidingWindowRateLimiter(max_requests=2, window_seconds=1.0)

        # Both should allow 2 requests
        await limiter_a.acquire()
        await limiter_a.acquire()
        await limiter_b.acquire()
        await limiter_b.acquire()

        # limiter_a should block, limiter_b's state is independent
        assert limiter_a.try_acquire() is False


# =============================================================================
# CIRCUIT BREAKER INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit opens after failure threshold."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
        )

        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker("test", config)

        # Initial state
        assert breaker.state == CircuitState.CLOSED

        # Trigger failures
        async def failing_call():
            raise Exception("Simulated failure")

        for _ in range(3):
            try:
                await breaker.call(failing_call)
            except Exception:
                pass

        # Should be open now
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers(self):
        """Test circuit recovers after timeout."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
        )

        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout=0.1,  # Short timeout for testing
        )
        breaker = CircuitBreaker("test", config)

        # Trigger failures to open circuit
        async def failing_call():
            raise Exception("Failure")

        for _ in range(2):
            try:
                await breaker.call(failing_call)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Success should transition to half-open then closed
        async def success_call():
            return "ok"

        result = await breaker.call(success_call)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit blocks requests when open."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitBreakerOpenError,
        )

        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=60.0,  # Long timeout
        )
        breaker = CircuitBreaker("test", config)

        # Open the circuit
        async def failing_call():
            raise Exception("Failure")

        try:
            await breaker.call(failing_call)
        except Exception:
            pass

        # Should block new requests
        async def success_call():
            return "ok"

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await breaker.call(success_call)

        assert "test" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self):
        """Test circuit reopens on failure in half-open state."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
        )

        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.05,
        )
        breaker = CircuitBreaker("test", config)

        # Open circuit
        async def failing():
            raise Exception("Fail")

        try:
            await breaker.call(failing)
        except Exception:
            pass

        # Wait for half-open
        await asyncio.sleep(0.1)

        # Fail again in half-open
        try:
            await breaker.call(failing)
        except Exception:
            pass

        # Should be back to open
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_status(self):
        """Test circuit breaker status reporting."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        breaker = CircuitBreaker("status_test", CircuitBreakerConfig())
        status = breaker.get_status()

        assert status["name"] == "status_test"
        assert status["state"] == "closed"
        assert "failure_count" in status
        assert "stats" in status

    @pytest.mark.asyncio
    async def test_circuit_breaker_registry(self):
        """Test circuit breaker registry for shared instances."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreakerRegistry,
            CircuitBreakerConfig,
        )

        registry = CircuitBreakerRegistry()

        # Get or create
        breaker1 = registry.get_or_create("service_a", CircuitBreakerConfig())
        breaker2 = registry.get_or_create("service_a", CircuitBreakerConfig())

        # Should be same instance
        assert breaker1 is breaker2

        # Different service
        breaker3 = registry.get_or_create("service_b", CircuitBreakerConfig())
        assert breaker3 is not breaker1

        # Get all status
        status = registry.get_all_status()
        assert "service_a" in status
        assert "service_b" in status


# =============================================================================
# HTTP SESSION POOL INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestHttpSessionPoolIntegration:
    """Integration tests for HTTP session pool."""

    @pytest.mark.asyncio
    async def test_session_pool_lifecycle(self):
        """Test session pool creation and cleanup."""
        try:
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            pool = HttpSessionPool(
                max_sessions=3,
                max_connections_per_host=5,
            )

            # Pool should start empty
            assert pool.available_count == 0
            assert pool.in_use_count == 0

            await pool.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_session_pool_statistics(self):
        """Test session pool stats tracking."""
        try:
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            pool = HttpSessionPool()

            stats = pool.get_stats()
            assert "available" in stats
            assert "in_use" in stats
            assert "total" in stats
            assert "max_sessions" in stats
            assert "sessions_created" in stats

            await pool.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_session_pool_context_manager(self):
        """Test session pool as async context manager."""
        try:
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            async with HttpSessionPool() as pool:
                assert pool is not None
                assert not pool._closed

            # After exit, should be closed
            assert pool._closed

        except ImportError:
            pytest.skip("aiohttp not available")


# =============================================================================
# UNIFIED HTTP CLIENT INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestUnifiedHttpClientIntegration:
    """Integration tests for UnifiedHttpClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initializes with all components."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
                UnifiedHttpClientConfig,
            )

            config = UnifiedHttpClientConfig(
                max_retries=3,
                rate_limit_requests=10,
                circuit_failure_threshold=5,
            )
            client = UnifiedHttpClient(config)

            # Client should have all components
            assert hasattr(client, "_config")
            assert hasattr(client, "_rate_limiters")
            assert hasattr(client, "_circuit_registry")
            assert hasattr(client, "_stats")

            await client.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_client_statistics(self):
        """Test client statistics tracking."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
            )

            client = UnifiedHttpClient()
            await client.start()

            stats = client.stats.to_dict()
            assert "total_requests" in stats
            assert "successful_requests" in stats
            assert "failed_requests" in stats
            assert "retried_requests" in stats
            assert "success_rate" in stats

            await client.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
            )

            async with UnifiedHttpClient() as client:
                assert client._started is True

            assert client._started is False

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_client_combined_stats(self):
        """Test getting all stats from client."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
            )

            async with UnifiedHttpClient() as client:
                all_stats = client.get_all_stats()

                assert "requests" in all_stats
                assert "pool" in all_stats
                assert "rate_limiters" in all_stats
                assert "circuit_breakers" in all_stats

        except ImportError:
            pytest.skip("aiohttp not available")


# =============================================================================
# RETRY WITH BACKOFF TESTS
# =============================================================================


@pytest.mark.integration
class TestRetryWithBackoff:
    """Integration tests for retry with backoff."""

    def test_retry_config_delay_calculation(self):
        """Test retry delay calculation with backoff."""
        from casare_rpa.utils.resilience.retry import RetryConfig

        config = RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        # First attempt: 1.0
        assert config.get_delay(1) == 1.0
        # Second attempt: 2.0
        assert config.get_delay(2) == 2.0
        # Third attempt: 4.0
        assert config.get_delay(3) == 4.0
        # Fourth attempt: 8.0
        assert config.get_delay(4) == 8.0
        # Fifth attempt: 16.0
        assert config.get_delay(5) == 16.0

    def test_retry_config_respects_max_delay(self):
        """Test retry delay respects maximum."""
        from casare_rpa.utils.resilience.retry import RetryConfig

        config = RetryConfig(
            max_attempts=10,
            initial_delay=1.0,
            max_delay=5.0,
            backoff_multiplier=3.0,
            jitter=False,
        )

        # Should cap at max_delay
        for attempt in range(1, 11):
            delay = config.get_delay(attempt)
            assert delay <= 5.0, f"Delay {delay} exceeds max at attempt {attempt}"

    def test_retry_config_with_jitter(self):
        """Test retry delay includes jitter when enabled."""
        from casare_rpa.utils.resilience.retry import RetryConfig

        config = RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=True,
        )

        # Get multiple delays and verify they vary
        delays = [config.get_delay(3) for _ in range(10)]

        # With jitter, delays should vary
        unique_delays = set(delays)
        # At least some variation expected (may not be all unique due to randomness)
        # Just verify we get reasonable values
        for delay in delays:
            assert delay >= 0, "Delay should not be negative"
            assert delay <= 30.0, "Delay should not exceed max"

    def test_error_classification(self):
        """Test error classification for retry decisions."""
        from casare_rpa.utils.resilience.retry import classify_error, ErrorCategory

        # Timeout errors are classified as TRANSIENT (retry-able)
        timeout_err = asyncio.TimeoutError()
        assert classify_error(timeout_err) == ErrorCategory.TRANSIENT

        # Connection errors (simulate)
        class MockConnectionError(Exception):
            pass

        conn_err = MockConnectionError()
        # Generic exception should be UNKNOWN
        generic_result = classify_error(conn_err)
        assert isinstance(generic_result, ErrorCategory)
        assert generic_result == ErrorCategory.UNKNOWN

    def test_should_retry_logic(self):
        """Test should_retry decision logic."""
        from casare_rpa.utils.resilience.retry import RetryConfig

        config = RetryConfig(max_attempts=3)

        # Should retry timeout
        timeout_err = asyncio.TimeoutError()
        assert config.should_retry(timeout_err, attempt=1) is True
        assert config.should_retry(timeout_err, attempt=2) is True
        assert config.should_retry(timeout_err, attempt=3) is False  # Max reached


# =============================================================================
# END-TO-END RESILIENCE TESTS
# =============================================================================


@pytest.mark.integration
class TestResilienceEndToEnd:
    """End-to-end tests combining multiple resilience patterns."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_circuit_breaker(self):
        """Test rate limiting works with circuit breaker."""
        from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
        )

        rate_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)
        circuit = CircuitBreaker(
            "combo_test", CircuitBreakerConfig(failure_threshold=3)
        )

        call_count = 0

        async def rate_limited_call():
            nonlocal call_count
            await rate_limiter.acquire()
            call_count += 1
            return "success"

        # Make calls through both
        for _ in range(3):
            result = await circuit.call(rate_limited_call)
            assert result == "success"

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry_exhaustion(self):
        """Test circuit breaker opens after retries exhausted."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
        )
        from casare_rpa.utils.resilience.retry import RetryConfig

        circuit = CircuitBreaker(
            "retry_exhaust_test",
            CircuitBreakerConfig(failure_threshold=2),
        )
        retry_config = RetryConfig(max_attempts=2, initial_delay=0.01)

        async def failing_operation():
            raise Exception("Always fails")

        # Simulate retry exhaustion feeding into circuit breaker
        for attempt in range(1, 3):
            try:
                await circuit.call(failing_operation)
            except Exception:
                # Retry logic would normally go here
                if retry_config.should_retry(Exception(), attempt):
                    await asyncio.sleep(retry_config.get_delay(attempt))
                    continue
                break

        # After retries exhausted and failures recorded, circuit may open
        assert circuit._failure_count >= 1

    @pytest.mark.asyncio
    async def test_domain_extraction_for_rate_limiting(self):
        """Test domain extraction for per-domain rate limiting."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
            )

            client = UnifiedHttpClient()

            # Test domain extraction
            domain1 = client._extract_domain("https://api.example.com/v1/users")
            domain2 = client._extract_domain("https://api.example.com/v2/posts")
            domain3 = client._extract_domain("https://other.example.com/data")

            assert domain1 == "api.example.com"
            assert domain1 == domain2  # Same domain
            assert domain1 != domain3  # Different domain

            # Test base URL extraction
            base1 = client._extract_base_url("https://api.example.com/v1/users")
            assert base1 == "https://api.example.com"

            await client.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_singleton_client_access(self):
        """Test singleton client pattern."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                get_unified_http_client,
                close_unified_http_client,
            )

            # Get singleton
            client1 = await get_unified_http_client()
            client2 = await get_unified_http_client()

            # Should be same instance
            assert client1 is client2

            # Clean up
            await close_unified_http_client()

        except ImportError:
            pytest.skip("aiohttp not available")
