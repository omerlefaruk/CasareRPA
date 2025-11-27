"""
Selector validation cache for CasareRPA.

Provides LRU caching for selector validation results to avoid
repeated DOM queries for the same selectors.
"""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from loguru import logger


@dataclass
class CachedSelectorResult:
    """Cached result of a selector validation."""

    selector_value: str
    selector_type: str
    page_url: str
    count: int
    is_unique: bool
    execution_time_ms: float
    cached_at: float = field(default_factory=time.time)
    hit_count: int = 0

    def is_expired(self, ttl_seconds: float = 60.0) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.cached_at) > ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "is_unique": self.is_unique,
            "time": self.execution_time_ms,
            "success": True,
            "cached": True,
        }


class SelectorCache:
    """
    LRU cache for selector validation results.

    Features:
    - Configurable max size with LRU eviction
    - TTL-based expiration
    - URL-aware caching (different pages have different DOMs)
    - Hit/miss statistics tracking
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: float = 60.0,
        enabled: bool = True,
    ):
        """
        Initialize the selector cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
            enabled: Whether caching is enabled
        """
        self._cache: OrderedDict[str, CachedSelectorResult] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._enabled = enabled

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _make_key(self, selector_value: str, selector_type: str, page_url: str) -> str:
        """
        Create a cache key from selector parameters.

        Args:
            selector_value: The selector string
            selector_type: Type of selector (xpath, css, etc.)
            page_url: URL of the page (for URL-aware caching)

        Returns:
            Hash-based cache key
        """
        # Use hash of URL to keep keys reasonable length
        url_hash = hashlib.md5(page_url.encode()).hexdigest()[:8]
        key_str = f"{selector_type}:{selector_value}:{url_hash}"
        return key_str

    def get(
        self, selector_value: str, selector_type: str, page_url: str
    ) -> Optional[CachedSelectorResult]:
        """
        Get a cached selector validation result.

        Args:
            selector_value: The selector string
            selector_type: Type of selector
            page_url: URL of the page

        Returns:
            Cached result if found and valid, None otherwise
        """
        if not self._enabled:
            return None

        key = self._make_key(selector_value, selector_type, page_url)

        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check TTL
        if entry.is_expired(self._ttl_seconds):
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self._hits += 1

        logger.debug(
            f"Cache hit for selector: {selector_type}:{selector_value[:30]}..."
        )
        return entry

    def put(
        self,
        selector_value: str,
        selector_type: str,
        page_url: str,
        count: int,
        execution_time_ms: float,
    ) -> None:
        """
        Store a selector validation result in cache.

        Args:
            selector_value: The selector string
            selector_type: Type of selector
            page_url: URL of the page
            count: Number of elements matched
            execution_time_ms: Time taken to validate
        """
        if not self._enabled:
            return

        key = self._make_key(selector_value, selector_type, page_url)

        # Evict if at capacity
        while len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1

        self._cache[key] = CachedSelectorResult(
            selector_value=selector_value,
            selector_type=selector_type,
            page_url=page_url,
            count=count,
            is_unique=(count == 1),
            execution_time_ms=execution_time_ms,
        )

        logger.debug(f"Cached selector: {selector_type}:{selector_value[:30]}...")

    def invalidate(self, page_url: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            page_url: If provided, only invalidate entries for this URL.
                     If None, invalidate all entries.

        Returns:
            Number of entries invalidated
        """
        if page_url is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Invalidated all {count} cache entries")
            return count

        # Invalidate entries for specific URL
        url_hash = hashlib.md5(page_url.encode()).hexdigest()[:8]
        keys_to_remove = [k for k in self._cache.keys() if k.endswith(f":{url_hash}")]

        for key in keys_to_remove:
            del self._cache[key]

        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for URL")
        return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        keys_to_remove = [
            k for k, v in self._cache.items() if v.is_expired(self._ttl_seconds)
        ]

        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")

        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "enabled": self._enabled,
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl_seconds,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate_percent": round(hit_rate, 2),
        }

    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True
        logger.info("Selector cache enabled")

    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False
        logger.info("Selector cache disabled")

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)


# Global cache instance
_global_cache: Optional[SelectorCache] = None


def get_selector_cache() -> SelectorCache:
    """Get the global selector cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SelectorCache()
    return _global_cache


def reset_selector_cache() -> None:
    """Reset the global selector cache (useful for testing)."""
    global _global_cache
    _global_cache = None
