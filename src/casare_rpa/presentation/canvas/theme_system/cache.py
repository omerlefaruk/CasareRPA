"""
Stylesheet cache manager for UI tokens.

This module provides a simple caching mechanism for generated stylesheets
to avoid rebuilding them repeatedly.

Usage:
    from casare_rpa.presentation.canvas.theme_system.cache import (
        get_cached,
        clear_cache,
    )

    # Get or build stylesheet
    stylesheet = get_cached("button_primary", lambda: build_button_style())

    # Clear cache (e.g., after theme change)
    clear_cache()
"""

from __future__ import annotations

from typing import Callable, TypeVar

# Module-level cache dictionary
_cache: dict[str, str] = {}

T = TypeVar("T")


def get_cached(key: str, generator_fn: Callable[[], T]) -> T:
    """
    Get a value from cache, or generate and store it.

    Thread-safe for read operations. For write operations, assumes
    single-threaded initialization (typical for Qt startup).

    Args:
        key: Cache key to lookup.
        generator_fn: Function that generates the value if not cached.

    Returns:
        The cached or generated value.

    Example:
        stylesheet = get_cached("button_style", lambda: build_button_style())
    """
    if key not in _cache:
        _cache[key] = generator_fn()  # type: ignore[assignment]
    return _cache[key]  # type: ignore[return-value]


def clear_cache() -> None:
    """
    Clear all cached stylesheets.

    Call this after theme changes to force regeneration of all stylesheets.
    """
    _cache.clear()


def get_cache_size() -> int:
    """
    Get the number of items currently in the cache.

    Returns:
        Number of cached items.
    """
    return len(_cache)


def has_cached(key: str) -> bool:
    """
    Check if a key exists in the cache.

    Args:
        key: Cache key to check.

    Returns:
        True if the key exists in cache, False otherwise.
    """
    return key in _cache


__all__ = [
    "get_cached",
    "clear_cache",
    "get_cache_size",
    "has_cached",
]
