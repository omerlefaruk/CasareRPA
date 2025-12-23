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

import threading
from collections import deque
from collections.abc import Callable
from typing import Any, Dict, Generic, List, Optional, TypeVar
from weakref import WeakValueDictionary

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
        reset_fn: Callable[[T], None] | None = None,
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

    def get_stats(self) -> dict[str, int]:
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

    def get(self, node_id: str) -> Any | None:
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

    def get_stats(self) -> dict[str, Any]:
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
def _create_result_dict() -> dict[str, Any]:
    return {"success": False, "data": None, "error": None}


def _reset_result_dict(d: dict[str, Any]) -> None:
    d.clear()
    d["success"] = False
    d["data"] = None
    d["error"] = None


_result_dict_pool = ObjectPool(
    factory=_create_result_dict,
    reset_fn=_reset_result_dict,
    max_size=200,
)


def get_result_dict() -> dict[str, Any]:
    """
    Get a pre-allocated result dictionary.

    PERFORMANCE: Avoids dict allocation on every node execution.

    Returns:
        Dictionary with success, data, error keys
    """
    return _result_dict_pool.acquire()


def return_result_dict(d: dict[str, Any]) -> None:
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


def _create_list() -> list[Any]:
    return []


def _reset_list(lst: list[Any]) -> None:
    lst.clear()


_list_pool = ObjectPool(
    factory=_create_list,
    reset_fn=_reset_list,
    max_size=100,
)


def get_list() -> list[Any]:
    """Get a pre-allocated list."""
    return _list_pool.acquire()


def return_list(lst: list[Any]) -> None:
    """Return a list to the pool."""
    _list_pool.release(lst)


# =============================================================================
# Node Instance Pool
# =============================================================================


class NodeInstancePool:
    """
    Pool node instances by type for reuse during workflow loading.

    PERFORMANCE: Reduces allocation overhead for repeated workflow loads.
    Nodes are reset before reuse to clear previous state.

    Usage:
        pool = get_node_instance_pool()
        node = pool.acquire("ClickElementNode", ClickElementNode, "node_123")
        # ... use node ...
        pool.release(node)  # Return to pool after workflow completes
    """

    def __init__(self, max_per_type: int = 20):
        """
        Initialize node instance pool.

        Args:
            max_per_type: Maximum instances to keep per node type
        """
        self._pools: dict[str, deque] = {}
        self._max_per_type = max_per_type
        self._lock = threading.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._returns = 0

    def acquire(
        self,
        node_type: str,
        node_class: type,
        node_id: str,
        config: dict | None = None,
    ) -> Any:
        """
        Get or create a node instance.

        Tries to reuse a pooled instance first, creating new if pool empty.

        Args:
            node_type: Node type name (e.g., "ClickElementNode")
            node_class: Node class to instantiate
            node_id: Unique node identifier
            config: Optional config dict

        Returns:
            Node instance (reused or newly created)
        """
        with self._lock:
            pool = self._pools.get(node_type)
            if pool and len(pool) > 0:
                self._hits += 1
                node = pool.pop()
                # Reset for reuse
                self._reset_node(node, node_id, config)
                return node

            self._misses += 1

        # Create new instance outside lock
        if config:
            return node_class(node_id, config=config)
        return node_class(node_id)

    def release(self, node: Any) -> None:
        """
        Return a node instance to the pool.

        Args:
            node: Node instance to pool
        """
        node_type = getattr(node, "node_type", None)
        if not node_type:
            return

        with self._lock:
            if node_type not in self._pools:
                self._pools[node_type] = deque()

            pool = self._pools[node_type]
            if len(pool) < self._max_per_type:
                self._returns += 1
                # Clear node state before pooling
                self._clear_node(node)
                pool.append(node)

    def release_all(self, nodes: dict[str, Any]) -> None:
        """
        Return multiple nodes to the pool.

        Args:
            nodes: Dict mapping node_id to node instance
        """
        for node in nodes.values():
            self.release(node)

    def _reset_node(self, node: Any, node_id: str, config: dict | None) -> None:
        """Reset node for reuse with new id and config."""
        node.node_id = node_id

        # Reset config
        if hasattr(node, "config"):
            node.config.clear()
            if config:
                node.config.update(config)

        # Reset ports data (keep port definitions)
        if hasattr(node, "_input_port_values"):
            node._input_port_values.clear()
        if hasattr(node, "_output_port_values"):
            node._output_port_values.clear()

    def _clear_node(self, node: Any) -> None:
        """Clear node state before pooling."""
        # Clear config values
        if hasattr(node, "config"):
            node.config.clear()

        # Clear port values
        if hasattr(node, "_input_port_values"):
            node._input_port_values.clear()
        if hasattr(node, "_output_port_values"):
            node._output_port_values.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            pool_sizes = {k: len(v) for k, v in self._pools.items()}
            total = self._hits + self._misses
            return {
                "total_pooled": sum(pool_sizes.values()),
                "pools": pool_sizes,
                "hits": self._hits,
                "misses": self._misses,
                "returns": self._returns,
                "hit_rate": self._hits / total if total > 0 else 0.0,
            }

    def clear(self) -> None:
        """Clear all pools."""
        with self._lock:
            self._pools.clear()


# Global node instance pool (thread-safe singleton)
_node_instance_pool: NodeInstancePool | None = None
_node_instance_pool_lock = threading.Lock()


def get_node_instance_pool() -> NodeInstancePool:
    """
    Get the global node instance pool.

    Thread-safe using double-checked locking pattern.
    """
    global _node_instance_pool
    if _node_instance_pool is None:
        with _node_instance_pool_lock:
            if _node_instance_pool is None:
                _node_instance_pool = NodeInstancePool()
    return _node_instance_pool
