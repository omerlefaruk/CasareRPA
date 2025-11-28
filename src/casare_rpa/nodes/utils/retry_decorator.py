"""Retry decorator and utilities for node operations."""

import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Callable, TypeVar, Any, Generic, Optional

from loguru import logger

T = TypeVar("T")


@dataclass
class RetryResult(Generic[T]):
    """Result of a retry operation with metadata."""

    success: bool
    value: Optional[T]
    attempts: int
    last_error: Optional[Exception] = None

    @property
    def failed(self) -> bool:
        return not self.success


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator to retry async operations.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            # Should not reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry exhausted without exception")

        return wrapper

    return decorator


async def retry_operation(
    operation: Callable[[], T],
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff: float = 1.0,
    operation_name: str = "operation",
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> RetryResult[T]:
    """Execute an async operation with retry logic.

    This is the recommended approach for node operations as it:
    - Returns attempt count for logging/output
    - Provides hooks for custom retry handling
    - Does not raise on failure (returns RetryResult)

    Args:
        operation: Async callable to execute (no args, use closure)
        max_attempts: Maximum number of attempts (1 = no retry)
        delay_seconds: Delay between retries in seconds
        backoff: Multiplier for delay on each retry (1.0 = constant)
        operation_name: Name for logging purposes
        on_retry: Optional callback(attempt, exception) called before retry

    Returns:
        RetryResult with success status, value, attempts, and last error

    Example:
        async def do_click():
            await page.click(selector)
            return True

        result = await retry_operation(
            do_click,
            max_attempts=3,
            delay_seconds=1.0,
            operation_name="click element"
        )
        if result.success:
            return {"success": True, "attempts": result.attempts}
        else:
            raise result.last_error
    """
    current_delay = delay_seconds
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            value = await operation()
            return RetryResult(success=True, value=value, attempts=attempt)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    f"{operation_name} failed (attempt {attempt}/{max_attempts}): {e}"
                )
                if on_retry:
                    on_retry(attempt, e)
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    return RetryResult(
        success=False, value=None, attempts=max_attempts, last_error=last_exception
    )


async def retry_async(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Retry an async function call.

    Functional alternative to decorator for one-off retries.

    Args:
        func: Async function to call
        *args: Positional arguments for func
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exception types to catch and retry
        **kwargs: Keyword arguments for func

    Returns:
        Result of successful function call

    Raises:
        Last exception if all retries fail
    """
    current_delay = delay
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry exhausted without exception")
