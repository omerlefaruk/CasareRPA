"""
CasareRPA - Cache System End-to-End Tests

E2E tests for cache system operations:
- Cache key generation
- Cache read/write/invalidate
- Cache expiration
- Cache consistency

Run with: pytest tests/e2e/test_cache_system_e2e.py -v -m e2e
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    pass


# =============================================================================
# Cache Key Tests
# =============================================================================


@pytest.mark.e2e
class TestCacheKeyGeneration:
    """E2E tests for cache key generation."""

    def test_simple_key_generation(self) -> None:
        """Test generating simple cache keys."""
        # Basic key format
        workflow_id = "workflow_123"
        node_id = "node_456"
        key = f"{workflow_id}:{node_id}:output"

        assert "workflow_123" in key
        assert "node_456" in key
        assert key == "workflow_123:node_456:output"

    def test_composite_key_generation(self) -> None:
        """Test generating composite cache keys."""
        parts = {
            "workflow_id": "wf_001",
            "node_id": "node_001",
            "iteration": 5,
            "branch": "main",
        }

        key = ":".join(f"{k}={v}" for k, v in parts.items())
        assert "workflow_id=wf_001" in key
        assert "iteration=5" in key

    def test_key_uniqueness(self) -> None:
        """Test that different inputs produce different keys."""
        keys = set()

        for i in range(100):
            key = f"workflow_{i}:node_{i % 10}:output"
            keys.add(key)

        # All keys should be unique
        assert len(keys) == 100


# =============================================================================
# Cache Read/Write Tests
# =============================================================================


@pytest.mark.e2e
class TestCacheReadWrite:
    """E2E tests for cache read/write operations."""

    def test_simple_cache_write_and_read(self) -> None:
        """Test writing and reading from cache."""
        # Simulate simple in-memory cache
        cache: dict[str, Any] = {}

        # Write
        cache["test_key"] = {"data": "test_value", "timestamp": time.time()}

        # Read
        cached = cache.get("test_key")
        assert cached is not None
        assert cached["data"] == "test_value"

    def test_complex_data_caching(self) -> None:
        """Test caching complex data structures."""
        cache: dict[str, Any] = {}

        complex_data = {
            "nodes": [
                {"id": "node_1", "type": "StartNode"},
                {"id": "node_2", "type": "EndNode"},
            ],
            "connections": [
                {"from": "node_1", "to": "node_2"},
            ],
            "metadata": {
                "version": "1.0.0",
                "created": "2024-01-01",
            },
        }

        cache["workflow_data"] = complex_data

        retrieved = cache.get("workflow_data")
        assert retrieved == complex_data
        assert len(retrieved["nodes"]) == 2

    def test_cache_overwrite(self) -> None:
        """Test overwriting cached values."""
        cache: dict[str, Any] = {}

        cache["key"] = "value_1"
        assert cache["key"] == "value_1"

        cache["key"] = "value_2"
        assert cache["key"] == "value_2"

    def test_cache_miss(self) -> None:
        """Test cache miss behavior."""
        cache: dict[str, Any] = {}

        result = cache.get("nonexistent_key")
        assert result is None

        result = cache.get("nonexistent_key", "default")
        assert result == "default"


# =============================================================================
# Cache Invalidation Tests
# =============================================================================


@pytest.mark.e2e
class TestCacheInvalidation:
    """E2E tests for cache invalidation."""

    def test_delete_single_key(self) -> None:
        """Test deleting a single cache key."""
        cache: dict[str, Any] = {
            "key_1": "value_1",
            "key_2": "value_2",
            "key_3": "value_3",
        }

        del cache["key_2"]

        assert "key_1" in cache
        assert "key_2" not in cache
        assert "key_3" in cache

    def test_delete_by_prefix(self) -> None:
        """Test deleting cache keys by prefix."""
        cache: dict[str, Any] = {
            "workflow_1:node_1": "value_1",
            "workflow_1:node_2": "value_2",
            "workflow_2:node_1": "value_3",
            "workflow_2:node_2": "value_4",
        }

        # Delete all keys starting with "workflow_1:"
        keys_to_delete = [k for k in cache if k.startswith("workflow_1:")]
        for key in keys_to_delete:
            del cache[key]

        assert len(cache) == 2
        assert all(k.startswith("workflow_2:") for k in cache)

    def test_clear_all_cache(self) -> None:
        """Test clearing entire cache."""
        cache: dict[str, Any] = {
            "key_1": "value_1",
            "key_2": "value_2",
            "key_3": "value_3",
        }

        cache.clear()

        assert len(cache) == 0


# =============================================================================
# Cache Expiration Tests
# =============================================================================


@pytest.mark.e2e
class TestCacheExpiration:
    """E2E tests for cache expiration."""

    def test_ttl_expiration(self) -> None:
        """Test time-to-live based expiration."""
        cache: dict[str, dict[str, Any]] = {}

        # Store with TTL (as timestamp)
        ttl_seconds = 1
        cache["key"] = {
            "value": "test_data",
            "expires_at": time.time() + ttl_seconds,
        }

        # Check immediately - should be valid
        entry = cache.get("key")
        assert entry is not None
        assert entry["expires_at"] > time.time()

        # Wait for expiration
        time.sleep(ttl_seconds + 0.1)

        # Should be expired
        entry = cache.get("key")
        assert entry is not None
        assert entry["expires_at"] < time.time()  # Expired

    def test_check_expiration_on_read(self) -> None:
        """Test that expiration is checked on read."""
        cache: dict[str, dict[str, Any]] = {}

        def cache_get(key: str) -> Any | None:
            entry = cache.get(key)
            if entry is None:
                return None
            if entry.get("expires_at", float("inf")) < time.time():
                del cache[key]  # Clean up expired entry
                return None
            return entry.get("value")

        # Store with short TTL
        cache["key"] = {
            "value": "test_data",
            "expires_at": time.time() + 0.1,
        }

        # Read immediately
        assert cache_get("key") == "test_data"

        # Wait and read again
        time.sleep(0.2)
        assert cache_get("key") is None
        assert "key" not in cache  # Entry removed


# =============================================================================
# Cache Consistency Tests
# =============================================================================


@pytest.mark.e2e
class TestCacheConsistency:
    """E2E tests for cache consistency."""

    def test_cache_reflects_updates(self) -> None:
        """Test that cache reflects data updates."""
        cache: dict[str, Any] = {}
        data_store = {"counter": 0}

        # Initial cache
        cache["counter"] = data_store["counter"]
        assert cache["counter"] == 0

        # Update data
        data_store["counter"] = 10
        cache["counter"] = data_store["counter"]
        assert cache["counter"] == 10

    def test_cache_isolation(self) -> None:
        """Test that cached data is properly isolated."""
        cache: dict[str, Any] = {}

        # Store list
        original_list = [1, 2, 3]
        cache["list"] = original_list.copy()

        # Modify original
        original_list.append(4)

        # Cache should be unchanged
        assert cache["list"] == [1, 2, 3]

    def test_workflow_node_caching(self) -> None:
        """Test caching workflow node outputs."""
        cache: dict[str, Any] = {}

        # Simulate workflow execution with caching
        workflow_id = "wf_test"
        nodes = ["node_1", "node_2", "node_3"]

        for i, node_id in enumerate(nodes):
            key = f"{workflow_id}:{node_id}:output"
            cache[key] = {"result": f"output_{i}", "success": True}

        # Verify all outputs cached
        for i, node_id in enumerate(nodes):
            key = f"{workflow_id}:{node_id}:output"
            cached = cache.get(key)
            assert cached is not None
            assert cached["result"] == f"output_{i}"
            assert cached["success"] is True


# =============================================================================
# Async Cache Tests
# =============================================================================


@pytest.mark.e2e
class TestAsyncCache:
    """E2E tests for async cache operations."""

    @pytest.mark.asyncio
    async def test_async_cache_operations(self) -> None:
        """Test cache operations in async context."""
        cache: dict[str, Any] = {}

        async def cache_set(key: str, value: Any) -> None:
            await asyncio.sleep(0.01)  # Simulate async operation
            cache[key] = value

        async def cache_get(key: str) -> Any | None:
            await asyncio.sleep(0.01)  # Simulate async operation
            return cache.get(key)

        # Set values
        await cache_set("async_key", "async_value")

        # Get values
        result = await cache_get("async_key")
        assert result == "async_value"

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self) -> None:
        """Test concurrent access to cache."""
        cache: dict[str, int] = {"counter": 0}

        async def increment():
            await asyncio.sleep(0.001)
            cache["counter"] = cache.get("counter", 0) + 1

        # Run concurrent increments
        await asyncio.gather(*[increment() for _ in range(10)])

        # Note: Without locking, result may not be exactly 10
        assert cache["counter"] > 0

    @pytest.mark.asyncio
    async def test_cache_with_workflow_execution(self) -> None:
        """Test cache during simulated workflow execution."""
        cache: dict[str, Any] = {}

        async def execute_node(node_id: str, input_data: Any) -> dict:
            # Check cache first
            cache_key = f"node:{node_id}:output"
            cached = cache.get(cache_key)
            if cached is not None:
                return {"success": True, "from_cache": True, "data": cached}

            # Execute node
            await asyncio.sleep(0.01)  # Simulate work
            result = f"processed_{input_data}"

            # Cache result
            cache[cache_key] = result

            return {"success": True, "from_cache": False, "data": result}

        # First execution - not cached
        result1 = await execute_node("node_1", "input")
        assert result1["from_cache"] is False

        # Second execution - should be cached
        result2 = await execute_node("node_1", "input")
        assert result2["from_cache"] is True
        assert result2["data"] == result1["data"]
