"""
CasareRPA - Infrastructure: Async Utilities

Utilities for handling async operations, specifically wrapping blocking calls
to prevent blocking the event loop.
"""

import asyncio
import functools
from typing import Any, Callable, TypeVar


T = TypeVar("T")


async def run_in_executor(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a blocking function in the default loop executor.

    Args:
        func: The blocking function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function (wrapped via functools.partial)

    Returns:
        The result of the function call
    """
    loop = asyncio.get_running_loop()

    if kwargs:
        # run_in_executor doesn't support kwargs directly
        func_with_kwargs = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_with_kwargs)

    return await loop.run_in_executor(None, func, *args)


def async_wrap(func: Callable[..., T]) -> Callable[..., Any]:
    """
    Decorator to wrap a blocking function into an async one using run_in_executor.

    Example:
        @async_wrap
        def blocking_io():
            time.sleep(1)
            return "done"

        # Usage:
        result = await blocking_io()
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await run_in_executor(func, *args, **kwargs)

    return wrapper
