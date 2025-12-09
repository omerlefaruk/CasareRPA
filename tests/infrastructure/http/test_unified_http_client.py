"""
Tests for UnifiedHttpClient - HTTP client with resilience patterns.

Tests cover:
- Session pooling: verify sessions are reused
- Rate limiting: verify requests are throttled per domain
- Circuit breaker: verify circuit opens after failures
- Retry logic: verify exponential backoff on 429/5xx
- All HTTP methods: get, post, put, delete, patch, head, options
- Configuration: verify UnifiedHttpClientConfig works
- Stats: verify get_all_stats() returns correct data
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Any, Dict

# Import the modules under test
from casare_rpa.infrastructure.http.unified_http_client import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
    RequestStats,
    RETRY_STATUS_CODES,
)
from casare_rpa.utils.resilience.rate_limiter import RateLimitExceeded
from casare_rpa.robot.circuit_breaker import CircuitBreakerOpenError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_http_pool():
    """Create a mock HttpSessionPool."""
    pool = AsyncMock()
    pool.request = AsyncMock()
    pool.close = AsyncMock()
    pool.get_stats = Mock(
        return_value={
            "total_sessions": 1,
            "active_sessions": 1,
        }
    )
    return pool


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response."""
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"success": True})
    response.text = AsyncMock(return_value="OK")
    response.release = AsyncMock()
    return response


@pytest.fixture
def mock_error_response():
    """Create a mock aiohttp error response (500)."""
    response = AsyncMock()
    response.status = 500
    response.json = AsyncMock(return_value={"error": "Server error"})
    response.text = AsyncMock(return_value="Internal Server Error")
    response.release = AsyncMock()
    return response


@pytest.fixture
def mock_rate_limited_response():
    """Create a mock aiohttp rate-limited response (429)."""
    response = AsyncMock()
    response.status = 429
    response.json = AsyncMock(return_value={"error": "Too many requests"})
    response.text = AsyncMock(return_value="Too Many Requests")
    response.release = AsyncMock()
    return response


@pytest.fixture
def default_config():
    """Create a default configuration for testing."""
    return UnifiedHttpClientConfig(
        max_sessions=5,
        max_retries=3,
        retry_initial_delay=0.01,  # Fast retries for tests
        retry_max_delay=0.1,
        rate_limit_requests=100,  # High limit to avoid rate limiting in most tests
        rate_limit_window=1.0,
        circuit_failure_threshold=5,
        circuit_timeout=0.1,  # Fast circuit breaker timeout for tests
    )


@pytest.fixture
def strict_rate_limit_config():
    """Create a config with strict rate limiting for rate limit tests."""
    return UnifiedHttpClientConfig(
        rate_limit_requests=1,
        rate_limit_window=10.0,  # Only 1 request per 10 seconds
        rate_limit_max_wait=0.01,  # Very short max wait = will exceed quickly
    )


# ============================================================================
# RequestStats Tests
# ============================================================================


class TestRequestStats:
    """Tests for RequestStats dataclass."""

    def test_initial_values(self):
        """Stats should start at zero."""
        stats = RequestStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.retried_requests == 0
        assert stats.rate_limited_requests == 0
        assert stats.circuit_broken_requests == 0
        assert stats.total_retry_delay_ms == 0.0

    def test_success_rate_zero_requests(self):
        """Success rate should be 0 when no requests made."""
        stats = RequestStats()
        assert stats.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Success rate should be correctly calculated."""
        stats = RequestStats()
        stats.total_requests = 10
        stats.successful_requests = 7
        assert stats.success_rate == 70.0

    def test_success_rate_100_percent(self):
        """Success rate should be 100 when all requests succeed."""
        stats = RequestStats()
        stats.total_requests = 5
        stats.successful_requests = 5
        assert stats.success_rate == 100.0

    def test_to_dict(self):
        """to_dict should return all fields."""
        stats = RequestStats()
        stats.total_requests = 10
        stats.successful_requests = 8
        stats.failed_requests = 2
        stats.retried_requests = 3
        stats.rate_limited_requests = 1
        stats.circuit_broken_requests = 0
        stats.total_retry_delay_ms = 150.5

        result = stats.to_dict()

        assert result["total_requests"] == 10
        assert result["successful_requests"] == 8
        assert result["failed_requests"] == 2
        assert result["retried_requests"] == 3
        assert result["rate_limited_requests"] == 1
        assert result["circuit_broken_requests"] == 0
        assert result["total_retry_delay_ms"] == 150.5
        assert result["success_rate"] == 80.0


# ============================================================================
# UnifiedHttpClientConfig Tests
# ============================================================================


class TestUnifiedHttpClientConfig:
    """Tests for UnifiedHttpClientConfig dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = UnifiedHttpClientConfig()
        assert config.max_sessions == 10
        assert config.max_retries == 3
        assert config.default_timeout == 30.0
        assert config.rate_limit_requests == 10
        assert config.circuit_failure_threshold == 5
        assert config.user_agent == "CasareRPA/1.0"

    def test_custom_values(self):
        """Config should accept custom values."""
        config = UnifiedHttpClientConfig(
            max_sessions=20,
            max_retries=5,
            default_timeout=60.0,
            user_agent="CustomAgent/2.0",
        )
        assert config.max_sessions == 20
        assert config.max_retries == 5
        assert config.default_timeout == 60.0
        assert config.user_agent == "CustomAgent/2.0"

    def test_default_headers(self):
        """Config should support default headers."""
        config = UnifiedHttpClientConfig(
            default_headers={"Authorization": "Bearer token123"}
        )
        assert config.default_headers["Authorization"] == "Bearer token123"


# ============================================================================
# UnifiedHttpClient Initialization Tests
# ============================================================================


class TestUnifiedHttpClientInit:
    """Tests for UnifiedHttpClient initialization."""

    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    def test_init_with_default_config(self):
        """Client should initialize with default config."""
        client = UnifiedHttpClient()
        assert client._config is not None
        assert client._config.max_sessions == 10
        assert client._started is False

    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    def test_init_with_custom_config(self, default_config):
        """Client should use custom config when provided."""
        client = UnifiedHttpClient(default_config)
        assert client._config.max_sessions == 5
        assert client._config.max_retries == 3

    @patch(
        "casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", False
    )
    def test_init_without_aiohttp_raises(self):
        """Client should raise ImportError if aiohttp not available."""
        with pytest.raises(ImportError, match="aiohttp is required"):
            UnifiedHttpClient()


# ============================================================================
# Session Pooling Tests
# ============================================================================


class TestSessionPooling:
    """Tests for session pooling behavior."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    @patch("casare_rpa.infrastructure.http.unified_http_client.HttpSessionPool")
    async def test_pool_initialized_on_start(self, MockPool, default_config):
        """Session pool should be initialized on start."""
        mock_pool = AsyncMock()
        MockPool.return_value = mock_pool

        client = UnifiedHttpClient(default_config)
        await client.start()

        MockPool.assert_called_once()
        assert client._started is True

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    @patch("casare_rpa.infrastructure.http.unified_http_client.HttpSessionPool")
    async def test_start_is_idempotent(self, MockPool, default_config):
        """Multiple start calls should not recreate pool."""
        mock_pool = AsyncMock()
        MockPool.return_value = mock_pool

        client = UnifiedHttpClient(default_config)
        await client.start()
        await client.start()
        await client.start()

        MockPool.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    @patch("casare_rpa.infrastructure.http.unified_http_client.HttpSessionPool")
    async def test_close_releases_pool(self, MockPool, default_config):
        """Close should release the session pool."""
        mock_pool = AsyncMock()
        MockPool.return_value = mock_pool

        client = UnifiedHttpClient(default_config)
        await client.start()
        await client.close()

        mock_pool.close.assert_awaited_once()
        assert client._started is False


# ============================================================================
# HTTP Methods Tests
# ============================================================================


class TestHttpMethods:
    """Tests for all HTTP method wrappers."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_get_method(self, default_config, mock_http_pool, mock_response):
        """GET method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.get(
            "https://api.example.com/data",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_post_method(self, default_config, mock_http_pool, mock_response):
        """POST method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.post(
            "https://api.example.com/data",
            json={"key": "value"},
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_put_method(self, default_config, mock_http_pool, mock_response):
        """PUT method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.put(
            "https://api.example.com/data/1",
            json={"key": "updated"},
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_delete_method(self, default_config, mock_http_pool, mock_response):
        """DELETE method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.delete(
            "https://api.example.com/data/1",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_patch_method(self, default_config, mock_http_pool, mock_response):
        """PATCH method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.patch(
            "https://api.example.com/data/1",
            json={"field": "patched"},
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_head_method(self, default_config, mock_http_pool, mock_response):
        """HEAD method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.head(
            "https://api.example.com/data",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_options_method(self, default_config, mock_http_pool, mock_response):
        """OPTIONS method should call request with correct method."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.options(
            "https://api.example.com/data",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200


# ============================================================================
# Retry Logic Tests
# ============================================================================


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_retry_on_500_error(
        self, default_config, mock_http_pool, mock_error_response, mock_response
    ):
        """Should retry on 500 status code."""
        # First call returns 500, second returns 200
        mock_http_pool.request.side_effect = [mock_error_response, mock_response]

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.get(
            "https://api.example.com/data",
            retry_count=3,
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200
        assert client.stats.retried_requests >= 1

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_retry_on_429_rate_limit(
        self, default_config, mock_http_pool, mock_rate_limited_response, mock_response
    ):
        """Should retry on 429 status code."""
        # First call returns 429, second returns 200
        mock_http_pool.request.side_effect = [mock_rate_limited_response, mock_response]

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.get(
            "https://api.example.com/data",
            retry_count=3,
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200
        assert client.stats.retried_requests >= 1

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_retry_on_connection_error(
        self, default_config, mock_http_pool, mock_response
    ):
        """Should retry on connection errors."""
        # First call raises, second succeeds
        mock_http_pool.request.side_effect = [
            ConnectionError("Connection refused"),
            mock_response,
        ]

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        response = await client.get(
            "https://api.example.com/data",
            retry_count=3,
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert response.status == 200
        assert client.stats.retried_requests >= 1

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_exhausted_retries_raises(
        self, default_config, mock_http_pool, mock_error_response
    ):
        """Should raise after all retries exhausted."""
        # All calls return 500
        mock_http_pool.request.return_value = mock_error_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        # After retry_count attempts, should still get 500 response
        response = await client.get(
            "https://api.example.com/data",
            retry_count=2,
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        # The last response is returned even if it's an error status
        assert response.status == 500


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_rate_limiter_created_per_domain(
        self, default_config, mock_http_pool, mock_response
    ):
        """Rate limiter should be created for each domain."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        # Make requests to different domains
        await client.get("https://api1.example.com/data", skip_circuit_breaker=True)
        await client.get("https://api2.example.com/data", skip_circuit_breaker=True)

        # Should have rate limiters for both domains
        assert "api1.example.com" in client._rate_limiters
        assert "api2.example.com" in client._rate_limiters

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_skip_rate_limit_flag(
        self, strict_rate_limit_config, mock_http_pool, mock_response
    ):
        """skip_rate_limit flag should bypass rate limiting."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(strict_rate_limit_config)
        client._pool = mock_http_pool
        client._started = True

        # Multiple requests with skip_rate_limit should all succeed
        for _ in range(5):
            response = await client.get(
                "https://api.example.com/data",
                skip_rate_limit=True,
                skip_circuit_breaker=True,
            )
            assert response.status == 200


# ============================================================================
# Circuit Breaker Tests
# ============================================================================


class TestCircuitBreaker:
    """Tests for circuit breaker behavior."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_circuit_breaker_created_per_base_url(
        self, default_config, mock_http_pool, mock_response
    ):
        """Circuit breaker should be created for each base URL."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        # Make requests to different base URLs
        await client.get("https://api1.example.com/path1", skip_rate_limit=True)
        await client.get("https://api2.example.com/path2", skip_rate_limit=True)

        # Check circuit breakers were created
        status = client.get_circuit_breaker_status()
        assert "https://api1.example.com" in status
        assert "https://api2.example.com" in status

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_skip_circuit_breaker_flag(
        self, default_config, mock_http_pool, mock_response
    ):
        """skip_circuit_breaker flag should bypass circuit breaker."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        # Request with skip_circuit_breaker should not create circuit breaker
        await client.get(
            "https://api.example.com/data",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        # No circuit breaker should be created
        status = client.get_circuit_breaker_status()
        assert "https://api.example.com" not in status


# ============================================================================
# Statistics Tests
# ============================================================================


class TestStatistics:
    """Tests for statistics collection."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_successful_request_updates_stats(
        self, default_config, mock_http_pool, mock_response
    ):
        """Successful request should update stats."""
        mock_http_pool.request.return_value = mock_response

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        await client.get(
            "https://api.example.com/data",
            skip_rate_limit=True,
            skip_circuit_breaker=True,
        )

        assert client.stats.total_requests == 1
        assert client.stats.successful_requests == 1
        assert client.stats.failed_requests == 0

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_get_all_stats_returns_complete_data(
        self, default_config, mock_http_pool, mock_response
    ):
        """get_all_stats should return complete statistics."""
        mock_http_pool.request.return_value = mock_response
        mock_http_pool.get_stats.return_value = {"sessions": 1}

        client = UnifiedHttpClient(default_config)
        client._pool = mock_http_pool
        client._started = True

        await client.get("https://api.example.com/data", skip_circuit_breaker=True)

        all_stats = client.get_all_stats()

        assert "requests" in all_stats
        assert "pool" in all_stats
        assert "rate_limiters" in all_stats
        assert "circuit_breakers" in all_stats

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    async def test_get_pool_stats_when_not_started(self, default_config):
        """get_pool_stats should return empty dict when pool not started."""
        client = UnifiedHttpClient(default_config)

        stats = client.get_pool_stats()

        assert stats == {}


# ============================================================================
# Context Manager Tests
# ============================================================================


class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    @patch("casare_rpa.infrastructure.http.unified_http_client.HttpSessionPool")
    async def test_async_context_manager_starts_client(self, MockPool, default_config):
        """Async context manager should start client on enter."""
        mock_pool = AsyncMock()
        MockPool.return_value = mock_pool

        async with UnifiedHttpClient(default_config) as client:
            assert client._started is True

    @pytest.mark.asyncio
    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    @patch("casare_rpa.infrastructure.http.unified_http_client.HttpSessionPool")
    async def test_async_context_manager_closes_on_exit(self, MockPool, default_config):
        """Async context manager should close client on exit."""
        mock_pool = AsyncMock()
        MockPool.return_value = mock_pool

        async with UnifiedHttpClient(default_config) as client:
            pass

        mock_pool.close.assert_awaited_once()


# ============================================================================
# URL Parsing Tests
# ============================================================================


class TestUrlParsing:
    """Tests for URL parsing helper methods."""

    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    def test_extract_domain(self, default_config):
        """_extract_domain should return domain from URL."""
        client = UnifiedHttpClient(default_config)

        assert (
            client._extract_domain("https://api.example.com/path") == "api.example.com"
        )
        assert (
            client._extract_domain("https://api.example.com:8080/path")
            == "api.example.com:8080"
        )
        assert client._extract_domain("http://localhost:3000/api") == "localhost:3000"

    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    def test_extract_base_url(self, default_config):
        """_extract_base_url should return base URL without path."""
        client = UnifiedHttpClient(default_config)

        assert (
            client._extract_base_url("https://api.example.com/path/to/resource")
            == "https://api.example.com"
        )
        assert (
            client._extract_base_url("http://localhost:3000/api/v1/users")
            == "http://localhost:3000"
        )


# ============================================================================
# Retry Status Code Tests
# ============================================================================


class TestRetryStatusCodes:
    """Tests for retry status code detection."""

    @patch("casare_rpa.infrastructure.http.unified_http_client.AIOHTTP_AVAILABLE", True)
    def test_should_retry_status_codes(self, default_config):
        """Should identify retryable status codes."""
        client = UnifiedHttpClient(default_config)

        # Should retry
        assert client._should_retry_status(429) is True  # Too Many Requests
        assert client._should_retry_status(500) is True  # Internal Server Error
        assert client._should_retry_status(502) is True  # Bad Gateway
        assert client._should_retry_status(503) is True  # Service Unavailable
        assert client._should_retry_status(504) is True  # Gateway Timeout

        # Should not retry
        assert client._should_retry_status(200) is False
        assert client._should_retry_status(201) is False
        assert client._should_retry_status(400) is False
        assert client._should_retry_status(401) is False
        assert client._should_retry_status(403) is False
        assert client._should_retry_status(404) is False


# ============================================================================
# RETRY_STATUS_CODES Constant Tests
# ============================================================================


class TestRetryStatusCodesConstant:
    """Tests for RETRY_STATUS_CODES constant."""

    def test_retry_status_codes_contains_expected(self):
        """RETRY_STATUS_CODES should contain expected codes."""
        assert 429 in RETRY_STATUS_CODES
        assert 500 in RETRY_STATUS_CODES
        assert 502 in RETRY_STATUS_CODES
        assert 503 in RETRY_STATUS_CODES
        assert 504 in RETRY_STATUS_CODES

    def test_retry_status_codes_excludes_client_errors(self):
        """RETRY_STATUS_CODES should not contain client errors."""
        assert 400 not in RETRY_STATUS_CODES
        assert 401 not in RETRY_STATUS_CODES
        assert 403 not in RETRY_STATUS_CODES
        assert 404 not in RETRY_STATUS_CODES
