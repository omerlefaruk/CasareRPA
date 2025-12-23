"""
Workflow Cache for CasareRPA.

Caches parsed workflow schemas to avoid redundant parsing.
Uses content fingerprinting for cache invalidation.
"""

import hashlib
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional

import orjson
from loguru import logger


class WorkflowCache:
    """
    LRU cache for parsed workflow schemas.

    Cache key: SHA-256 hash of workflow JSON content (first 16 chars)
    Cache value: Parsed WorkflowSchema

    Thread-safe with configurable max size.
    """

    def __init__(self, max_size: int = 20) -> None:
        """
        Initialize workflow cache.

        Args:
            max_size: Maximum number of workflows to cache (default 20)
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    # Internal keys to exclude from fingerprint (added by loader)
    _INTERNAL_KEYS = {"__validated__"}

    @staticmethod
    def compute_fingerprint(workflow_data: dict[str, Any]) -> str:
        """
        Compute content hash for workflow data.

        Excludes internal marker keys (like __validated__) that are
        added during loading and would change the fingerprint.

        Args:
            workflow_data: Workflow dictionary to fingerprint

        Returns:
            16-character hex fingerprint
        """
        # Filter out internal keys that would change fingerprint
        clean_data = {
            k: v for k, v in workflow_data.items() if k not in WorkflowCache._INTERNAL_KEYS
        }
        content = orjson.dumps(clean_data, option=orjson.OPT_SORT_KEYS)
        return hashlib.sha256(content).hexdigest()[:16]

    def get(self, fingerprint: str) -> Any | None:
        """
        Get cached workflow by fingerprint.

        Args:
            fingerprint: Content fingerprint from compute_fingerprint()

        Returns:
            Cached workflow schema or None if not found
        """
        with self._lock:
            if fingerprint in self._cache:
                self._hits += 1
                self._cache.move_to_end(fingerprint)
                logger.debug(f"Workflow cache hit: {fingerprint}")
                return self._cache[fingerprint]
            self._misses += 1
            return None

    def put(self, fingerprint: str, workflow: Any) -> None:
        """
        Cache a parsed workflow.

        Args:
            fingerprint: Content fingerprint from compute_fingerprint()
            workflow: Parsed workflow schema to cache
        """
        with self._lock:
            if len(self._cache) >= self._max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Workflow cache evicted: {evicted_key}")
            self._cache[fingerprint] = workflow
            logger.debug(f"Workflow cached: {fingerprint}")

    def invalidate(self, fingerprint: str) -> None:
        """
        Invalidate a specific cache entry.

        Args:
            fingerprint: Content fingerprint to invalidate
        """
        with self._lock:
            if fingerprint in self._cache:
                del self._cache[fingerprint]
                logger.debug(f"Workflow cache invalidated: {fingerprint}")

    def clear(self) -> None:
        """Clear all cached workflows and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.debug("Workflow cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with size, max_size, hits, misses, hit_rate
        """
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
            }


# Global instance (thread-safe singleton)
_workflow_cache: WorkflowCache | None = None
_workflow_cache_lock = threading.Lock()


def get_workflow_cache() -> WorkflowCache:
    """
    Get global workflow cache singleton.

    Returns:
        WorkflowCache singleton instance
    """
    global _workflow_cache
    if _workflow_cache is None:
        with _workflow_cache_lock:
            if _workflow_cache is None:
                _workflow_cache = WorkflowCache()
                logger.debug("Workflow cache singleton initialized")
    return _workflow_cache
