"""
Rate Limiter Utility

Provides rate limiting functionality for controlling the frequency of operations
such as API calls, browser actions, or any resource-intensive tasks.
"""

import asyncio
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Dict, Optional, TypeVar, Union

from loguru import logger

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_second: float = 10.0
    """Maximum requests per second."""

    burst_size: int = 1
    """Maximum burst size (requests that can be made immediately)."""

    retry_after_limit: bool = True
    """Whether to retry after being rate limited (if False, raises exception)."""

    max_wait_time: float = 60.0
    """Maximum time to wait for rate limit to clear (seconds)."""

    @property
    def min_interval(self) -> float:
        """Minimum interval between requests in seconds."""
        return 1.0 / self.requests_per_second if self.requests_per_second > 0 else 0


@dataclass
class RateLimitStats:
    """Statistics for rate limiting."""

    total_requests: int = 0
    """Total number of requests made."""

    requests_delayed: int = 0
    """Number of requests that were delayed due to rate limiting."""

    total_delay_time: float = 0.0
    """Total time spent waiting due to rate limiting (seconds)."""

    requests_rejected: int = 0
    """Number of requests rejected due to rate limit exceeded."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "requests_delayed": self.requests_delayed,
            "total_delay_time": round(self.total_delay_time, 3),
            "requests_rejected": self.requests_rejected,
            "avg_delay": round(
                self.total_delay_time / self.requests_delayed if self.requests_delayed > 0 else 0,
                3,
            ),
        }


class RateLimiter:
    """
    Token bucket rate limiter for controlling request frequency.

    Uses the token bucket algorithm:
    - Tokens are added at a fixed rate (requests_per_second)
    - Each request consumes one token
    - If no tokens available, request waits or is rejected

    Example:
        limiter = RateLimiter(RateLimitConfig(requests_per_second=5))

        async def make_request():
            await limiter.acquire()
            # ... make the actual request
    """

    def __init__(self, config: RateLimitConfig | None = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if None)
        """
        self.config = config or RateLimitConfig()
        self._tokens = float(self.config.burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()
        self._stats = RateLimitStats()

        logger.debug(
            f"RateLimiter initialized: {self.config.requests_per_second} req/s, "
            f"burst={self.config.burst_size}"
        )

    @property
    def stats(self) -> RateLimitStats:
        """Get rate limiting statistics."""
        return self._stats

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # Add tokens based on time elapsed
        tokens_to_add = elapsed * self.config.requests_per_second
        self._tokens = min(self._tokens + tokens_to_add, float(self.config.burst_size))

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens for a request.

        This method will wait if necessary until tokens are available,
        or raise an exception if wait time exceeds max_wait_time.

        Args:
            tokens: Number of tokens to acquire (default 1)

        Returns:
            True if tokens were acquired

        Raises:
            RateLimitExceeded: If rate limit is exceeded and retry_after_limit is False
        """
        async with self._lock:
            self._stats.total_requests += 1
            self._refill_tokens()

            # Check if we have enough tokens
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            # Calculate wait time needed
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self.config.requests_per_second

            if wait_time > self.config.max_wait_time:
                self._stats.requests_rejected += 1
                if not self.config.retry_after_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded. Wait time ({wait_time:.2f}s) > "
                        f"max_wait_time ({self.config.max_wait_time:.2f}s)"
                    )
                wait_time = self.config.max_wait_time

            # Wait for tokens to become available
            logger.debug(f"Rate limited: waiting {wait_time:.3f}s for tokens")
            self._stats.requests_delayed += 1
            self._stats.total_delay_time += wait_time

        # Release lock while waiting
        await asyncio.sleep(wait_time)

        # Re-acquire and consume tokens
        async with self._lock:
            self._refill_tokens()
            self._tokens = max(0, self._tokens - tokens)

        return True

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False if rate limited
        """
        with self._sync_lock:
            self._refill_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                self._stats.total_requests += 1
                return True

            return False

    def reset(self) -> None:
        """Reset the rate limiter to initial state."""
        self._tokens = float(self.config.burst_size)
        self._last_update = time.monotonic()
        self._stats = RateLimitStats()


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded and retry is disabled."""

    pass


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for more precise rate limiting.

    Tracks actual request timestamps within a time window,
    providing more accurate rate limiting than token bucket.

    Example:
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1.0)

        async def make_request():
            await limiter.acquire()
            # ... make the actual request
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 1.0,
        max_wait_time: float = 60.0,
    ):
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Size of the sliding window in seconds
            max_wait_time: Maximum time to wait for rate limit to clear
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_wait_time = max_wait_time
        # Use maxlen to prevent unbounded growth under extreme load
        self._requests: deque = deque(maxlen=max_requests * 2)
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()
        self._stats = RateLimitStats()

        logger.debug(f"SlidingWindowRateLimiter initialized: {max_requests} req/{window_seconds}s")

    @property
    def stats(self) -> RateLimitStats:
        """Get rate limiting statistics."""
        return self._stats

    def _clean_old_requests(self) -> None:
        """Remove requests outside the current window."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

    async def acquire(self) -> bool:
        """
        Acquire permission to make a request.

        Returns:
            True if request is allowed

        Raises:
            RateLimitExceeded: If wait time exceeds max_wait_time
        """
        async with self._lock:
            self._stats.total_requests += 1
            self._clean_old_requests()

            if len(self._requests) < self.max_requests:
                self._requests.append(time.monotonic())
                return True

            # Calculate wait time until oldest request expires
            oldest = self._requests[0]
            wait_time = (oldest + self.window_seconds) - time.monotonic()

            if wait_time <= 0:
                self._clean_old_requests()
                self._requests.append(time.monotonic())
                return True

            if wait_time > self.max_wait_time:
                self._stats.requests_rejected += 1
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Wait time ({wait_time:.2f}s) > "
                    f"max_wait_time ({self.max_wait_time:.2f}s)"
                )

            self._stats.requests_delayed += 1
            self._stats.total_delay_time += wait_time

        # Release lock while waiting
        await asyncio.sleep(wait_time)

        async with self._lock:
            self._clean_old_requests()
            self._requests.append(time.monotonic())

        return True

    def try_acquire(self) -> bool:
        """
        Try to acquire without waiting.

        Returns:
            True if request is allowed, False if rate limited
        """
        with self._sync_lock:
            self._clean_old_requests()

            if len(self._requests) < self.max_requests:
                self._requests.append(time.monotonic())
                self._stats.total_requests += 1
                return True

            return False

    def reset(self) -> None:
        """Reset the rate limiter."""
        self._requests.clear()
        self._stats = RateLimitStats()


def rate_limited(requests_per_second: float = 10.0, burst_size: int = 1) -> Callable:
    """
    Decorator to rate limit a function.

    Args:
        requests_per_second: Maximum calls per second
        burst_size: Maximum burst size

    Returns:
        Decorated function

    Example:
        @rate_limited(requests_per_second=5)
        async def call_api():
            ...
    """
    config = RateLimitConfig(requests_per_second=requests_per_second, burst_size=burst_size)
    limiter = RateLimiter(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            await limiter.acquire()
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Global rate limiters for common use cases
# Use OrderedDict for LRU-like eviction when max size reached
from collections import OrderedDict

_global_limiters: OrderedDict[str, RateLimiter | SlidingWindowRateLimiter] = OrderedDict()
_MAX_GLOBAL_LIMITERS = 100  # Prevent unbounded growth


def get_rate_limiter(
    name: str, requests_per_second: float = 10.0, burst_size: int = 1
) -> RateLimiter:
    """
    Get or create a named global rate limiter.

    Args:
        name: Unique name for the rate limiter
        requests_per_second: Requests per second (only used on creation)
        burst_size: Burst size (only used on creation)

    Returns:
        RateLimiter instance
    """
    if name in _global_limiters:
        # Move to end (most recently used)
        _global_limiters.move_to_end(name)
        return _global_limiters[name]

    # Evict oldest if at capacity
    if len(_global_limiters) >= _MAX_GLOBAL_LIMITERS:
        _global_limiters.popitem(last=False)
        logger.debug(f"Evicted oldest rate limiter (max {_MAX_GLOBAL_LIMITERS} reached)")

    config = RateLimitConfig(requests_per_second=requests_per_second, burst_size=burst_size)
    _global_limiters[name] = RateLimiter(config)
    return _global_limiters[name]


def clear_rate_limiters() -> None:
    """Clear all global rate limiters."""
    _global_limiters.clear()


__all__ = [
    "RateLimitConfig",
    "RateLimitStats",
    "RateLimiter",
    "RateLimitExceeded",
    "SlidingWindowRateLimiter",
    "rate_limited",
    "get_rate_limiter",
    "clear_rate_limiters",
]
