import pytest
import asyncio
import os
import shutil
from casare_rpa.infrastructure.cache.manager import TieredCacheManager, CacheConfig
from casare_rpa.application.services.cache_invalidator import CacheInvalidator
from casare_rpa.domain.events import get_event_bus, WorkflowStarted


@pytest.fixture
async def cache_manager(tmp_path):
    test_dir = tmp_path / "cache_test"
    config = CacheConfig(enabled=True, disk_path=str(test_dir), l1_ttl=60, l2_ttl=3600)
    manager = TieredCacheManager(config)
    yield manager
    # Cleanup
    if manager.l2:
        manager.l2.close()

    # Give Windows a moment to release file locks
    await asyncio.sleep(0.2)

    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass  # Best effort cleanup on Windows


@pytest.mark.asyncio
async def test_l1_l2_promotion(cache_manager):
    """Test that getting from L2 promotes the value to L1."""
    key = "promo_test"
    value = {"data": "important"}

    # 1. Set in both
    await cache_manager.set(key, value)

    # 2. Delete from L1 only
    await cache_manager.l1.delete(key)

    # Verify L1 is empty
    assert await cache_manager.l1.get(key) is None

    # 3. Get via manager (should trigger promotion from L2)
    retrieved = await cache_manager.get(key)
    assert retrieved == value

    # 4. Verify it's now in L1
    l1_val = await cache_manager.l1.get(key)
    assert l1_val == value


@pytest.mark.asyncio
async def test_event_bus_invalidation(cache_manager):
    """Test that WorkflowStarted event clears the cache."""
    invalidator = CacheInvalidator(cache_manager)
    invalidator.start()

    key = "node:test_wf:123"
    await cache_manager.set(key, "some result")

    # Verify it exists
    assert await cache_manager.get(key) == "some result"

    # Publish event
    bus = get_event_bus()
    bus.publish(WorkflowStarted(workflow_id="test_wf", workflow_name="Test"))

    # Give a tiny bit of time for the async task to run
    await asyncio.sleep(0.1)

    # Verify it's gone
    assert await cache_manager.get(key) is None


@pytest.mark.asyncio
async def test_compression_logic(cache_manager):
    """Test that large objects are compressed/decompressed correctly."""
    import pickle

    # Create a large string (> 1KB threshold)
    large_data = "x" * 2000
    key = "large_key"

    await cache_manager.set(key, large_data)

    # Verify raw L2 data is bytes (compressed)
    raw_l2 = cache_manager.l2.get(key)
    assert raw_l2 is not None
    assert isinstance(raw_l2, bytes)

    # Compressed size should be smaller than original pickled size
    original_pickled_size = len(pickle.dumps(large_data))
    assert len(raw_l2) < original_pickled_size

    # Verify retrieval works
    retrieved = await cache_manager.get(key)
    assert retrieved == large_data
