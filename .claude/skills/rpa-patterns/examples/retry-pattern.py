"""
Retry Pattern with Exponential Backoff and Jitter

Use Case: Transient failures in network requests, API calls, or UI interactions.

This pattern implements:
1. Exponential backoff (1s, 2s, 4s, 8s...)
2. Random jitter to prevent thundering herd
3. Max delay cap to avoid excessive waits
4. Configurable retry count
"""

import asyncio
import random
from typing import Awaitable, Callable, TypeVar

from loguru import logger

T = TypeVar("T")


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    operation_name: str = "operation",
    max_attempts: int = 3,
    base_delay_ms: int = 1000,
    max_delay_ms: int = 10000,
    jitter_ms: int = 500,
) -> T:
    """
    Execute async operation with exponential backoff and jitter.

    Args:
        operation: Async callable to execute
        operation_name: Name for logging
        max_attempts: Total attempts (1 initial + retries)
        base_delay_ms: Starting delay in milliseconds
        max_delay_ms: Maximum delay cap
        jitter_ms: Random jitter to add (prevents synchronized retries)

    Returns:
        Result of successful operation

    Raises:
        Last exception if all attempts fail

    Example:
        result = await retry_with_backoff(
            lambda: page.click("#submit"),
            operation_name="click submit",
            max_attempts=5
        )
    """
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                logger.info(f"Retry attempt {attempt - 1}/{max_attempts - 1} for {operation_name}")

            result = await operation()
            if attempt > 1:
                logger.info(f"{operation_name} succeeded on attempt {attempt}")
            return result

        except Exception as e:
            last_error = e
            is_last = attempt == max_attempts

            if is_last:
                logger.error(f"{operation_name} failed after {max_attempts} attempts: {e}")
                raise

            # Calculate delay: exponential backoff + jitter
            exponential_delay = base_delay_ms * (2 ** (attempt - 1))
            capped_delay = min(exponential_delay, max_delay_ms)
            jitter = random.randint(0, jitter_ms)
            total_delay_ms = capped_delay + jitter

            logger.warning(
                f"{operation_name} failed (attempt {attempt}/{max_attempts}): {e}. "
                f"Retrying in {total_delay_ms}ms"
            )
            await asyncio.sleep(total_delay_ms / 1000)

    # Should never reach here, but type checker needs it
    if last_error:
        raise last_error
    raise RuntimeError(f"{operation_name} failed without exception")


# ===========================================================================
# RPA-Specific Retry Handlers
# ===========================================================================


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""

    pass


class TimeoutError(RetryableError):
    """Operation timed out."""

    pass


class NetworkError(RetryableError):
    """Network connectivity issue."""

    pass


def is_retryable(error: Exception) -> bool:
    """
    Determine if an error should trigger a retry.

    Retry these:
    - TimeoutError
    - NetworkError
    - Playwright TimeoutError
    - HTTP 5xx errors

    Don't retry:
    - ValueError, TypeError (code bugs)
    - HTTP 4xx (except 429)
    - Authentication errors
    """
    if isinstance(error, RetryableError):
        return True

    error_type = type(error).__name__
    error_msg = str(error).lower()

    # Playwright timeouts
    if "Timeout" in error_type:
        return True

    # HTTP 5xx
    if "500" in error_msg or "502" in error_msg or "503" in error_msg:
        return True

    # Rate limiting (429)
    if "429" in error_msg or "rate limit" in error_msg:
        return True

    return False


async def retry_if_retryable(
    operation: Callable[[], Awaitable[T]],
    operation_name: str = "operation",
    max_attempts: int = 3,
    base_delay_ms: int = 1000,
) -> T:
    """
    Retry only if the error is retryable (network, timeout, 5xx).

    Non-retryable errors (auth, 4xx client errors, code bugs) fail immediately.
    """
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()

        except Exception as e:
            last_error = e

            if not is_retryable(e):
                logger.error(f"{operation_name} failed with non-retryable error: {e}")
                raise

            if attempt < max_attempts:
                delay = base_delay_ms * (2 ** (attempt - 1))
                logger.warning(f"{operation_name} retryable error (attempt {attempt}): {e}")
                await asyncio.sleep(delay / 1000)

    raise last_error


# ===========================================================================
# Node Integration Example
# ===========================================================================

"""
Usage in a node:

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType

@properties(
    PropertyDef("max_retries", PropertyType.INTEGER, default=3),
    PropertyDef("base_delay", PropertyType.INTEGER, default=1000),
)
@node(category="http")
class RobustHttpNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")
        max_retries = self.get_parameter("max_retries", 3)
        base_delay = self.get_parameter("base_delay", 1000)

        async def fetch():
            async with context.http_client.get(url) as response:
                response.raise_for_status()
                return await response.json()

        try:
            data = await retry_with_backoff(
                fetch,
                operation_name=f"GET {url}",
                max_attempts=max_retries,
                base_delay_ms=base_delay,
            )
            self.set_output_value("data", data)
            return {"success": True}
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {"success": False, "error": str(e)}
"""
