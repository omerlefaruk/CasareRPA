"""
Unified HTTP Client for CasareRPA.

Composes all resilience patterns into a single facade:
- HttpSessionPool for connection reuse
- RetryConfig with exponential backoff
- SlidingWindowRateLimiter for per-domain rate limiting
- CircuitBreaker for failure isolation
"""

import asyncio
import ipaddress
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from loguru import logger

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool
from casare_rpa.utils.resilience.retry import (
    RetryConfig,
    classify_error,
)
from casare_rpa.utils.resilience.rate_limiter import (
    SlidingWindowRateLimiter,
    RateLimitExceeded,
)
from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
)
from casare_rpa.infrastructure.cache.manager import TieredCacheManager, CacheConfig
from casare_rpa.infrastructure.cache.keys import CacheKeyGenerator


# HTTP status codes that trigger retry
RETRY_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}

# SSRF Protection Configuration
ALLOWED_URL_SCHEMES: Set[str] = {"http", "https"}
BLOCKED_HOSTS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
    "::1",
}
BLOCKED_IP_RANGES: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),  # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


@dataclass
class UnifiedHttpClientConfig:
    """Configuration for UnifiedHttpClient."""

    # Session pool settings
    max_sessions: int = 10
    max_connections_per_host: int = 10
    session_max_age: float = 300.0
    session_idle_timeout: float = 60.0

    # Request defaults
    default_timeout: float = 30.0
    connect_timeout: float = 10.0

    # Retry settings
    max_retries: int = 3
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_backoff_multiplier: float = 2.0
    retry_jitter: bool = True

    # Rate limiting settings (per domain)
    rate_limit_requests: int = 10
    rate_limit_window: float = 1.0
    rate_limit_max_wait: float = 60.0

    # Circuit breaker settings (per base URL)
    circuit_failure_threshold: int = 5
    circuit_success_threshold: int = 2
    circuit_timeout: float = 60.0

    # Headers
    user_agent: str = "CasareRPA/1.0"
    default_headers: Dict[str, str] = field(default_factory=dict)

    # SSRF Protection
    enable_ssrf_protection: bool = True
    allow_private_ips: bool = False  # Set True to allow internal network requests
    additional_blocked_hosts: Optional[List[str]] = None

    # Caching settings
    cache_enabled: bool = False
    cache_ttl: int = 300  # 5 minutes
    cache_methods: Set[str] = field(default_factory=lambda: {"GET"})


@dataclass
class RequestStats:
    """Statistics for HTTP requests through UnifiedHttpClient."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0
    rate_limited_requests: int = 0
    circuit_broken_requests: int = 0
    total_retry_delay_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "retried_requests": self.retried_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "circuit_broken_requests": self.circuit_broken_requests,
            "total_retry_delay_ms": round(self.total_retry_delay_ms, 2),
            "success_rate": round(self.success_rate, 2),
        }


class CachingResponseWrapper:
    """Wraps aiohttp.ClientResponse to cache the body once read."""

    def __init__(
        self,
        response: "aiohttp.ClientResponse",
        cache: TieredCacheManager,
        key: str,
        ttl: int,
    ):
        self._response = response
        self._cache = cache
        self._key = key
        self._ttl = ttl
        self._body: Optional[bytes] = None

    @property
    def status(self):
        return self._response.status

    @property
    def headers(self):
        return self._response.headers

    async def read(self) -> bytes:
        if self._body is None:
            self._body = await self._response.read()
            if self.status < 400:  # Only cache successful responses
                await self._cache.set(
                    self._key,
                    {
                        "status": self.status,
                        "body": self._body,
                        "headers": dict(self.headers),
                    },
                    ttl=self._ttl,
                )
        return self._body

    async def json(self, **kwargs) -> Any:
        data = await self.read()
        import orjson

        return orjson.loads(data)

    async def text(self, encoding: Optional[str] = None) -> str:
        data = await self.read()
        return data.decode(encoding or "utf-8")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._response.__aexit__(exc_type, exc_val, exc_tb)

    def release(self):
        self._response.release()


class CachedResponse:
    """A mock response object that mimics aiohttp.ClientResponse for cached data."""

    def __init__(self, status: int, body: bytes, headers: Dict[str, str]):
        self.status = status
        self._body = body
        self.headers = headers

    async def json(self, **kwargs) -> Any:
        import orjson

        return orjson.loads(self._body)

    async def text(self, encoding: Optional[str] = None) -> str:
        return self._body.decode(encoding or "utf-8")

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def release(self):
        pass


class UnifiedHttpClient:
    """
    Unified HTTP client with resilience patterns.

    Composes:
    - Connection pooling (HttpSessionPool)
    - Exponential backoff retry (RetryConfig)
    - Per-domain rate limiting (SlidingWindowRateLimiter)
    - Per-base-URL circuit breaker (CircuitBreaker)

    Example:
        async with UnifiedHttpClient() as client:
            response = await client.get("https://api.example.com/data")
            data = await response.json()

        # Or with custom config:
        config = UnifiedHttpClientConfig(max_retries=5)
        client = UnifiedHttpClient(config)
        await client.start()
        try:
            response = await client.post("https://api.example.com", json={"key": "value"})
        finally:
            await client.close()
    """

    def __init__(
        self,
        config: Optional[UnifiedHttpClientConfig] = None,
        cache_manager: Optional[TieredCacheManager] = None,
    ) -> None:
        """
        Initialize UnifiedHttpClient.

        Args:
            config: Client configuration. Uses defaults if None.
            cache_manager: Optional cache manager. If None and config.cache_enabled,
                          a new one will be created.
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for UnifiedHttpClient. " "Install with: pip install aiohttp"
            )

        self._config = config or UnifiedHttpClientConfig()
        self._pool: Optional[HttpSessionPool] = None
        self._rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self._circuit_registry = CircuitBreakerRegistry()
        self._stats = RequestStats()
        self._started = False
        self._lock = asyncio.Lock()

        # Initialize cache manager
        self._cache = cache_manager
        if self._cache is None and self._config.cache_enabled:
            self._cache = TieredCacheManager(CacheConfig(enabled=True))

        logger.debug(
            f"UnifiedHttpClient initialized with config: "
            f"max_retries={self._config.max_retries}, "
            f"rate_limit={self._config.rate_limit_requests}/{self._config.rate_limit_window}s"
        )

    @property
    def stats(self) -> RequestStats:
        """Get request statistics."""
        return self._stats

    async def start(self) -> None:
        """Start the client and initialize the session pool."""
        if self._started:
            return

        async with self._lock:
            if self._started:
                return

            self._pool = HttpSessionPool(
                max_sessions=self._config.max_sessions,
                max_connections_per_host=self._config.max_connections_per_host,
                max_session_age=self._config.session_max_age,
                idle_timeout=self._config.session_idle_timeout,
                request_timeout=self._config.default_timeout,
                connect_timeout=self._config.connect_timeout,
                user_agent=self._config.user_agent,
                default_headers=self._config.default_headers,
            )
            self._started = True
            logger.debug("UnifiedHttpClient started")

    async def close(self) -> None:
        """Close the client and release all resources."""
        if not self._started:
            return

        async with self._lock:
            if not self._started:
                return

            if self._pool:
                await self._pool.close()
                self._pool = None

            self._rate_limiters.clear()
            self._started = False
            logger.debug("UnifiedHttpClient closed")

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting."""
        parsed = urlparse(url)
        return parsed.netloc

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL for circuit breaker."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _get_rate_limiter(self, domain: str) -> SlidingWindowRateLimiter:
        """Get or create rate limiter for domain."""
        if domain not in self._rate_limiters:
            self._rate_limiters[domain] = SlidingWindowRateLimiter(
                max_requests=self._config.rate_limit_requests,
                window_seconds=self._config.rate_limit_window,
                max_wait_time=self._config.rate_limit_max_wait,
            )
        return self._rate_limiters[domain]

    def _get_circuit_breaker(self, base_url: str) -> CircuitBreaker:
        """Get or create circuit breaker for base URL."""
        config = CircuitBreakerConfig(
            failure_threshold=self._config.circuit_failure_threshold,
            success_threshold=self._config.circuit_success_threshold,
            timeout=self._config.circuit_timeout,
        )
        return self._circuit_registry.get_or_create(base_url, config)

    def _should_retry_status(self, status_code: int) -> bool:
        """Check if HTTP status code should trigger retry."""
        return status_code in RETRY_STATUS_CODES

    def _validate_url_for_ssrf(self, url: str) -> None:
        """
        Validate URL for SSRF protection.

        Raises:
            ValueError: If URL is blocked by SSRF protection.
        """
        if not self._config.enable_ssrf_protection:
            return

        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            raise ValueError(
                f"SSRF Protection: Invalid URL scheme '{parsed.scheme}'. "
                f"Allowed: {ALLOWED_URL_SCHEMES}"
            )

        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("SSRF Protection: URL must have a hostname")

        hostname_lower = hostname.lower()

        # Check blocked hosts
        all_blocked = BLOCKED_HOSTS.copy()
        if self._config.additional_blocked_hosts:
            all_blocked.update(self._config.additional_blocked_hosts)

        if hostname_lower in all_blocked:
            raise ValueError(f"SSRF Protection: Blocked host '{hostname}'")

        # Check if hostname is an IP address in blocked ranges
        if not self._config.allow_private_ips:
            try:
                ip = ipaddress.ip_address(hostname)
                for blocked_range in BLOCKED_IP_RANGES:
                    if ip in blocked_range:
                        raise ValueError(f"SSRF Protection: Blocked IP range for '{hostname}'")
            except ValueError as e:
                # Re-raise if it's our SSRF protection error
                if "SSRF Protection" in str(e):
                    raise
                # Not an IP address, hostname is fine - continue

    def _sanitize_url_for_logging(self, url: str) -> str:
        """Remove query parameters from URL for safe logging."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def _build_retry_config(self, retry_count: int) -> RetryConfig:
        """Build retry configuration."""
        return RetryConfig(
            max_attempts=retry_count,
            initial_delay=self._config.retry_initial_delay,
            max_delay=self._config.retry_max_delay,
            backoff_multiplier=self._config.retry_backoff_multiplier,
            jitter=self._config.retry_jitter,
        )

    def _get_cache_key(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        json: Any,
        data: Any,
    ) -> str:
        """Generate a cache key for the request."""
        # Filter headers to only include those that affect the response (e.g., Accept)
        # For now, we'll just use the URL and method for simplicity,
        # but in production we might want to include some headers.
        cache_data = {"method": method, "url": url, "json": json, "data": data}
        return CacheKeyGenerator.generate("api", cache_data)

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        data: Any = None,
        timeout: Optional[float] = None,
        retry_count: int = 3,
        rate_limit_key: Optional[str] = None,
        skip_rate_limit: bool = False,
        skip_circuit_breaker: bool = False,
    ) -> "aiohttp.ClientResponse":
        """
        Make an HTTP request with all resilience patterns.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            headers: Additional headers
            json: JSON body (mutually exclusive with data)
            data: Form data or raw body
            timeout: Request timeout in seconds (overrides default)
            retry_count: Number of retry attempts (default 3)
            rate_limit_key: Custom key for rate limiting (defaults to domain)
            skip_rate_limit: Skip rate limiting for this request
            skip_circuit_breaker: Skip circuit breaker for this request

        Returns:
            aiohttp.ClientResponse

        Raises:
            ValueError: If URL is blocked by SSRF protection
            RateLimitExceeded: If rate limit wait exceeds max_wait_time
            CircuitBreakerOpenError: If circuit breaker is open
            aiohttp.ClientError: On request failure after all retries
        """
        # Check cache first
        cache_key = None
        if self._cache and method.upper() in self._config.cache_methods:
            cache_key = self._get_cache_key(method, url, headers, json, data)
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {method} {url}")
                return CachedResponse(cached["status"], cached["body"], cached["headers"])

        # SSRF Protection - validate URL before any processing
        self._validate_url_for_ssrf(url)

        if not self._started:
            await self.start()

        self._stats.total_requests += 1

        # Extract URL components
        domain = rate_limit_key or self._extract_domain(url)
        base_url = self._extract_base_url(url)

        # Apply rate limiting
        if not skip_rate_limit:
            rate_limiter = self._get_rate_limiter(domain)
            try:
                await rate_limiter.acquire()
            except RateLimitExceeded:
                self._stats.rate_limited_requests += 1
                raise

        # Get circuit breaker
        circuit = self._get_circuit_breaker(base_url) if not skip_circuit_breaker else None

        # Build request kwargs
        request_kwargs: Dict[str, Any] = {}
        if headers:
            request_kwargs["headers"] = headers
        if json is not None:
            request_kwargs["json"] = json
        if data is not None:
            request_kwargs["data"] = data
        if timeout is not None:
            request_kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)

        # Retry configuration
        retry_config = self._build_retry_config(retry_count)
        last_exception: Optional[Exception] = None

        for attempt in range(1, retry_count + 1):
            try:
                # Execute through circuit breaker if enabled
                if circuit:
                    try:
                        response = await circuit.call(
                            self._do_request, method, url, **request_kwargs
                        )
                    except CircuitBreakerOpenError:
                        self._stats.circuit_broken_requests += 1
                        raise
                else:
                    response = await self._do_request(method, url, **request_kwargs)

                # Check for retryable status codes
                if self._should_retry_status(response.status):
                    if attempt < retry_count:
                        delay = retry_config.get_delay(attempt)
                        logger.warning(
                            f"HTTP {response.status} for {method} "
                            f"{self._sanitize_url_for_logging(url)}, "
                            f"attempt {attempt}/{retry_count}. Retrying in {delay:.2f}s"
                        )
                        self._stats.retried_requests += 1
                        self._stats.total_retry_delay_ms += delay * 1000
                        await response.release()
                        await asyncio.sleep(delay)
                        continue

                self._stats.successful_requests += 1

                if cache_key:
                    return CachingResponseWrapper(
                        response, self._cache, cache_key, self._config.cache_ttl
                    )

                return response

            except CircuitBreakerOpenError:
                raise

            except Exception as e:
                last_exception = e
                category = classify_error(e)

                if retry_config.should_retry(e, attempt) and attempt < retry_count:
                    delay = retry_config.get_delay(attempt)
                    logger.warning(
                        f"{method} {self._sanitize_url_for_logging(url)} "
                        f"failed ({category.value}): {e}. "
                        f"Attempt {attempt}/{retry_count}. Retrying in {delay:.2f}s"
                    )
                    self._stats.retried_requests += 1
                    self._stats.total_retry_delay_ms += delay * 1000
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{method} {self._sanitize_url_for_logging(url)} "
                        f"failed ({category.value}): {e}. "
                        f"Attempt {attempt}/{retry_count}. Not retrying."
                    )
                    self._stats.failed_requests += 1
                    raise

        # Should not reach here, but safety net
        self._stats.failed_requests += 1
        if last_exception:
            raise last_exception
        raise RuntimeError("Request failed with no exception recorded")

    async def _do_request(self, method: str, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Execute the actual HTTP request using the session pool."""
        return await self._pool.request(method, url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a PATCH request."""
        return await self.request("PATCH", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make a HEAD request."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> "aiohttp.ClientResponse":
        """Make an OPTIONS request."""
        return await self.request("OPTIONS", url, **kwargs)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get session pool statistics."""
        if self._pool:
            return self._pool.get_stats()
        return {}

    def get_rate_limiter_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limiter statistics for all domains."""
        return {domain: limiter.stats.to_dict() for domain, limiter in self._rate_limiters.items()}

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker status for all base URLs."""
        return self._circuit_registry.get_all_status()

    def get_all_stats(self) -> Dict[str, Any]:
        """Get all statistics combined."""
        return {
            "requests": self._stats.to_dict(),
            "pool": self.get_pool_stats(),
            "rate_limiters": self.get_rate_limiter_stats(),
            "circuit_breakers": self.get_circuit_breaker_status(),
        }

    async def __aenter__(self) -> "UnifiedHttpClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


# Singleton instance for shared usage
_default_client: Optional[UnifiedHttpClient] = None
_default_client_lock = asyncio.Lock()


async def get_unified_http_client(
    config: Optional[UnifiedHttpClientConfig] = None,
) -> UnifiedHttpClient:
    """
    Get the default shared UnifiedHttpClient instance.

    Args:
        config: Configuration for the client (only used on first call)

    Returns:
        UnifiedHttpClient singleton instance
    """
    global _default_client

    if _default_client is None:
        async with _default_client_lock:
            if _default_client is None:
                _default_client = UnifiedHttpClient(config)
                await _default_client.start()

    return _default_client


async def close_unified_http_client() -> None:
    """Close the default shared UnifiedHttpClient instance."""
    global _default_client

    if _default_client is not None:
        async with _default_client_lock:
            if _default_client is not None:
                await _default_client.close()
                _default_client = None


__all__ = [
    "UnifiedHttpClient",
    "UnifiedHttpClientConfig",
    "RequestStats",
    "RETRY_STATUS_CODES",
    "ALLOWED_URL_SCHEMES",
    "BLOCKED_HOSTS",
    "BLOCKED_IP_RANGES",
    "get_unified_http_client",
    "close_unified_http_client",
]
