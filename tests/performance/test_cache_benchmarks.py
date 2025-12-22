import pytest
import time
import asyncio
from casare_rpa.infrastructure.cache.manager import TieredCacheManager, CacheConfig


@pytest.mark.asyncio
async def test_cache_performance_benchmarks(tmp_path):
    """Benchmark L1 vs L2 vs Cold retrieval."""
    test_dir = tmp_path / "perf_cache"
    config = CacheConfig(enabled=True, disk_path=str(test_dir))
    manager = TieredCacheManager(config)

    key = "perf_test"
    value = {"data": "x" * 1000}  # 1KB data

    # 1. Cold Set
    start = time.perf_counter()
    await manager.set(key, value)
    set_time = (time.perf_counter() - start) * 1000

    # 2. L1 Hit (Immediate)
    start = time.perf_counter()
    await manager.get(key)
    l1_time = (time.perf_counter() - start) * 1000

    # 3. L2 Hit (Clear L1 first)
    await manager.l1.clear()
    start = time.perf_counter()
    await manager.get(key)
    l2_time = (time.perf_counter() - start) * 1000

    print("\nCache Performance Results:")
    print(f"Set Time: {set_time:.4f}ms")
    print(f"L1 Hit Time: {l1_time:.4f}ms")
    print(f"L2 Hit Time: {l2_time:.4f}ms")

    # Assertions for sanity
    assert l1_time < 1.0, "L1 should be sub-millisecond"
    assert l2_time < 10.0, "L2 should be very fast (<10ms)"
    assert l1_time < l2_time, "L1 must be faster than L2"

    if manager.l2:
        manager.l2.close()
