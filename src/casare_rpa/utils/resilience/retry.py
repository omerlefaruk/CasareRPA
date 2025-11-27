"""
Retry and timeout utilities for CasareRPA.

This module provides decorators and utilities for automatic retry logic,
timeout handling, and error classification for robust node execution.
"""

import asyncio
import functools
import random
from enum import Enum
from typing import Any, Callable, Optional, Set, Type, TypeVar
from loguru import logger


class ErrorCategory(Enum):
    """Classification of errors for retry decisions."""

    TRANSIENT = "transient"  # Retry-able errors (network, timeout, etc.)
    PERMANENT = "permanent"  # Fatal errors (validation, config, etc.)
    UNKNOWN = "unknown"  # Unclassified errors


# Common transient exceptions that should be retried
TRANSIENT_EXCEPTIONS: Set[Type[Exception]] = {
    asyncio.TimeoutError,
    ConnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
    TimeoutError,
    OSError,  # Network-related OS errors
}

# Common transient error message patterns
TRANSIENT_PATTERNS = [
    "timeout",
    "timed out",
    "connection reset",
    "connection refused",
    "temporarily unavailable",
    "try again",
    "rate limit",
    "too many requests",
    "service unavailable",
    "network",
    "socket",
]


def classify_error(exception: Exception) -> ErrorCategory:
    """
    Classify an exception as transient or permanent.

    Args:
        exception: The exception to classify

    Returns:
        ErrorCategory indicating if the error is retry-able
    """
    # Check exception type
    for transient_type in TRANSIENT_EXCEPTIONS:
        if isinstance(exception, transient_type):
            return ErrorCategory.TRANSIENT

    # Check error message patterns
    error_msg = str(exception).lower()
    for pattern in TRANSIENT_PATTERNS:
        if pattern in error_msg:
            return ErrorCategory.TRANSIENT

    # Playwright-specific transient errors
    if "playwright" in type(exception).__module__.lower():
        playwright_transient = [
            "target closed",
            "browser has been closed",
            "page has been closed",
            "navigation failed",
            "net::err",
        ]
        for pattern in playwright_transient:
            if pattern in error_msg:
                return ErrorCategory.TRANSIENT

    return ErrorCategory.UNKNOWN


T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[Set[Type[Exception]]] = None,
        retry_if: Optional[Callable[[Exception], bool]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts (including initial)
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            retry_on: Set of exception types to retry on
            retry_if: Callable that returns True if exception should be retried
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.retry_on = retry_on
        self.retry_if = retry_if

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (1-based)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False

        # Check custom retry condition first
        if self.retry_if is not None:
            return self.retry_if(exception)

        # Check specific exception types
        if self.retry_on is not None:
            return any(isinstance(exception, exc_type) for exc_type in self.retry_on)

        # Default: retry on transient errors
        category = classify_error(exception)
        return category == ErrorCategory.TRANSIENT

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter (±25%)
        if self.jitter:
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    backoff_multiplier=2.0,
    jitter=True,
)


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with retry logic.

    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        config: Retry configuration (uses default if None)
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Result of the function

    Raises:
        The last exception if all retries fail
    """
    config = config or DEFAULT_RETRY_CONFIG
    last_exception: Optional[Exception] = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            category = classify_error(e)

            if config.should_retry(e, attempt):
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt}/{config.max_attempts} failed "
                    f"({category.value}): {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Attempt {attempt}/{config.max_attempts} failed "
                    f"({category.value}): {e}. Not retrying."
                )
                raise

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic error: no result or exception")


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to an async function.

    Args:
        config: Retry configuration (uses default if None)

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_async(func, *args, config=config, **kwargs)

        return wrapper

    return decorator


async def with_timeout(
    coro: Any,
    timeout: float,
    cleanup: Optional[Callable[[], Any]] = None,
) -> Any:
    """
    Execute a coroutine with timeout protection.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        cleanup: Optional cleanup function to call on timeout

    Returns:
        Result of the coroutine

    Raises:
        asyncio.TimeoutError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        if cleanup:
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
            except Exception as cleanup_error:
                logger.error(f"Cleanup after timeout failed: {cleanup_error}")
        raise


async def retry_with_timeout(
    func: Callable[..., Any],
    *args: Any,
    timeout: float = 30.0,
    retry_config: Optional[RetryConfig] = None,
    cleanup: Optional[Callable[[], Any]] = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with both retry and timeout protection.

    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        timeout: Timeout per attempt in seconds
        retry_config: Retry configuration
        cleanup: Optional cleanup function on timeout
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Result of the function

    Raises:
        The last exception if all retries fail
    """
    retry_config = retry_config or DEFAULT_RETRY_CONFIG
    last_exception: Optional[Exception] = None

    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            return await with_timeout(
                func(*args, **kwargs),
                timeout=timeout,
                cleanup=cleanup,
            )
        except Exception as e:
            last_exception = e
            category = classify_error(e)

            if retry_config.should_retry(e, attempt):
                delay = retry_config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt}/{retry_config.max_attempts} failed "
                    f"({category.value}): {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Attempt {attempt}/{retry_config.max_attempts} failed "
                    f"({category.value}): {e}. Not retrying."
                )
                raise

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic error: no result or exception")


class RetryStats:
    """Statistics tracking for retry operations."""

    def __init__(self):
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retries_performed = 0
        self.total_retry_delay = 0.0

    def record_attempt(self, success: bool, retry_delay: float = 0.0):
        """Record an attempt."""
        self.total_attempts += 1
        if success:
            self.successful_attempts += 1
        else:
            self.failed_attempts += 1
        if retry_delay > 0:
            self.retries_performed += 1
            self.total_retry_delay += retry_delay

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "failed_attempts": self.failed_attempts,
            "retries_performed": self.retries_performed,
            "total_retry_delay": self.total_retry_delay,
            "success_rate": self.success_rate,
        }
