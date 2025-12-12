"""
Object Pooling Utilities for CasareRPA.

PERFORMANCE: Object pooling reduces garbage collection pressure and
allocation overhead for frequently created/destroyed objects.

Features:
- Generic object pool with configurable size
- WeakRef cache for node lookups
- Specialized pools for common objects (ExecutionResult dicts)

Usage:
    from casare_rpa.utils.performance.object_pool import (
        get_result_dict,
        return_result_dict,
        get_node_cache,
    )

    # Get a pre-allocated result dict
    result = get_result_dict()
    result["success"] = True
    result["data"] = {"value": 42}

    # Return to pool when done
    return_result_dict(result)
"""

from typing import Any, Callable, Dict, Generic, Optional, TypeVar, List
from weakref import WeakValueDictionary
from collections import deque
import threading


T = TypeVar("T")


class ObjectPool(Generic[T]):
    """
    Generic object pool for reducing allocation overhead.

    PERFORMANCE: Reuses objects instead of allocating/deallocating.
    Useful for hot paths where same object types are repeatedly created.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        reset_fn: Optional[Callable[[T], None]] = None,
        max_size: int = 100,
    ):
        """
        Initialize object pool.

        Args:
            factory: Function to create new objects
            reset_fn: Optional function to reset object state before reuse
            max_size: Maximum pool size (excess objects are discarded)
        """
        self._factory = factory
        self._reset_fn = reset_fn
        self._max_size = max_size
        self._pool: deque[T] = deque()
        self._lock = threading.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._returns = 0

    def acquire(self) -> T:
        """
        Get an object from the pool (or create new one).

        Returns:
            Object from pool or newly created
        """
        with self._lock:
            if self._pool:
                self._hits += 1
                obj = self._pool.pop()
                if self._reset_fn:
                    self._reset_fn(obj)
                return obj

            self._misses += 1
            return self._factory()

    def release(self, obj: T) -> None:
        """
        Return an object to the pool.

        Args:
            obj: Object to return
        """
        with self._lock:
            if len(self._pool) < self._max_size:
                self._returns += 1
                self._pool.append(obj)
            # Else: discard (let GC handle it)

    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "returns": self._returns,
                "hit_rate": self._hits / max(1, self._hits + self._misses),
            }

    def clear(self) -> None:
        """Clear the pool."""
        with self._lock:
            self._pool.clear()


# =============================================================================
# WeakRef Node Cache
# =============================================================================


class WeakNodeCache:
    """
    WeakRef cache for node lookups.

    PERFORMANCE: Caches node references without preventing garbage collection.
    Useful for looking up nodes by ID without maintaining strong references.
    """

    def __init__(self):
        """Initialize weak node cache."""
        self._cache: WeakValueDictionary = WeakValueDictionary()
        self._hits = 0
        self._misses = 0

    def get(self, node_id: str) -> Optional[Any]:
        """
        Get node from cache.

        Args:
            node_id: Node identifier

        Returns:
            Node object if in cache, else None
        """
        node = self._cache.get(node_id)
        if node is not None:
            self._hits += 1
        else:
            self._misses += 1
        return node

    def set(self, node_id: str, node: Any) -> None:
        """
        Add node to cache.

        Args:
            node_id: Node identifier
            node: Node object
        """
        self._cache[node_id] = node

    def remove(self, node_id: str) -> None:
        """Remove node from cache."""
        self._cache.pop(node_id, None)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(1, self._hits + self._misses),
        }


# =============================================================================
# Specialized Pools
# =============================================================================


# Result dict pool - frequently created for node execution results
def _create_result_dict() -> Dict[str, Any]:
    return {"success": False, "data": None, "error": None}


def _reset_result_dict(d: Dict[str, Any]) -> None:
    d.clear()
    d["success"] = False
    d["data"] = None
    d["error"] = None


_result_dict_pool = ObjectPool(
    factory=_create_result_dict,
    reset_fn=_reset_result_dict,
    max_size=200,
)


def get_result_dict() -> Dict[str, Any]:
    """
    Get a pre-allocated result dictionary.

    PERFORMANCE: Avoids dict allocation on every node execution.

    Returns:
        Dictionary with success, data, error keys
    """
    return _result_dict_pool.acquire()


def return_result_dict(d: Dict[str, Any]) -> None:
    """
    Return a result dictionary to the pool.

    Args:
        d: Dictionary to return
    """
    _result_dict_pool.release(d)


# Global node cache
_node_cache = WeakNodeCache()


def get_node_cache() -> WeakNodeCache:
    """Get the global node cache."""
    return _node_cache


# =============================================================================
# List Pool for temporary lists
# =============================================================================


def _create_list() -> List[Any]:
    return []


def _reset_list(lst: List[Any]) -> None:
    lst.clear()


_list_pool = ObjectPool(
    factory=_create_list,
    reset_fn=_reset_list,
    max_size=100,
)


def get_list() -> List[Any]:
    """Get a pre-allocated list."""
    return _list_pool.acquire()


def return_list(lst: List[Any]) -> None:
    """Return a list to the pool."""
    _list_pool.release(lst)
