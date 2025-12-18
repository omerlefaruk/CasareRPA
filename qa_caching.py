import asyncio
import time
import os
import shutil
from typing import Dict, Any, Optional
from dataclasses import dataclass

from casare_rpa.infrastructure.cache.manager import TieredCacheManager, CacheConfig
from casare_rpa.infrastructure.cache.keys import CacheKeyGenerator
from casare_rpa.infrastructure.http.unified_http_client import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)
from casare_rpa.application.use_cases.node_executor import (
    NodeExecutor,
    NodeExecutionResult,
)
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.events import get_event_bus
from casare_rpa.domain.events.workflow_events import WorkflowStarted
from casare_rpa.application.services.cache_invalidator import CacheInvalidator


# Mock Context for NodeExecutor
class MockContext:
    def __init__(self):
        self.workflow_id = "test_wf_123"
        self.current_node = None

    def set_current_node(self, node_id):
        self.current_node = node_id


# Mock Node for testing
class MockCacheableNode(BaseNode):
    def _define_ports(self):
        self.add_input_port("input_val", "STRING")
        self.add_output_port("output_val", "STRING")

    async def execute(self, context) -> Dict[str, Any]:
        # Simulate heavy work
        await asyncio.sleep(0.5)
        val = self.get_input_value("input_val")
        return {"output_val": f"processed_{val}"}


async def run_qa_and_benchmarks():
    print("=== CasareRPA Caching QA & Benchmark ===")

    # 1. Test Key Generation
    print("\n[1] Testing Key Generation...")
    data = {"url": "https://api.example.com", "params": {"q": "test"}}
    key1 = CacheKeyGenerator.generate("api", data)
    key2 = CacheKeyGenerator.generate("api", data)
    key3 = CacheKeyGenerator.generate(
        "api", {"params": {"q": "test"}, "url": "https://api.example.com"}
    )

    assert key1 == key2 == key3
    print(f"✓ Deterministic keys generated: {key1}")

    # 2. Test Tiered Cache (L1/L2)
    print("\n[2] Testing Tiered Cache (L1/L2)...")
    cache_path = "./test_cache_dir"
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)

    config = CacheConfig(disk_path=cache_path, l1_ttl=2, l2_ttl=10)
    manager = TieredCacheManager(config)

    # Direct L2 test
    manager.l2.set("direct", "val")
    assert manager.l2.get("direct") == "val"
    print("✓ Direct L2 test passed")

    await manager.set("test_key", "test_value")

    # Hit L1
    start = time.perf_counter()
    val = await manager.get("test_key")
    l1_time = (time.perf_counter() - start) * 1000
    print(f"✓ L1 Hit: {val} in {l1_time:.4f}ms")

    # Clear L1, force L2
    await manager.l1.clear()
    start = time.perf_counter()
    val = await manager.get("test_key")
    l2_time = (time.perf_counter() - start) * 1000
    print(f"✓ L2 Hit (Promoted to L1): {val} in {l2_time:.4f}ms")
    assert val == "test_value"

    # 3. Test Node Execution Caching
    print("\n[3] Testing Node Execution Caching...")
    ctx = MockContext()
    executor = NodeExecutor(ctx, cache_manager=manager)

    node = MockCacheableNode("node_1")
    node.cacheable = True
    node.set_input_value("input_val", "hello")

    # First run (Cold)
    print("Running node (Cold)...")
    start = time.perf_counter()
    res1 = await executor.execute(node)
    cold_time = time.perf_counter() - start
    print(f"Cold execution: {cold_time:.4f}s")

    # Second run (Warm)
    print("Running node (Warm)...")
    start = time.perf_counter()
    res2 = await executor.execute(node)
    warm_time = time.perf_counter() - start
    print(f"Warm execution: {warm_time:.4f}s")

    improvement = (cold_time / warm_time) if warm_time > 0 else 0
    print(f"✓ Node Cache Benefit: {improvement:.1f}x faster")
    assert res1.result == res2.result
    assert warm_time < 0.05  # Should be near instant

    # 4. Test Event-Driven Invalidation
    print("\n[4] Testing Event-Driven Invalidation...")
    invalidator = CacheInvalidator(manager)
    invalidator.start()

    # Verify cache exists
    assert await manager.get(executor._get_node_cache_key(node)) is not None

    # Trigger WorkflowStarted event
    print("Publishing WorkflowStarted event...")
    get_event_bus().publish(WorkflowStarted(workflow_id=ctx.workflow_id))
    await asyncio.sleep(0.5)  # Wait for async handler

    # Verify cache is gone
    val = await manager.get(executor._get_node_cache_key(node))
    assert val is None
    print("✓ Cache successfully invalidated via EventBus")

    # 5. Test HTTP Caching
    print("\n[5] Testing HTTP Caching (Mocked)...")
    http_config = UnifiedHttpClientConfig(cache_enabled=True)
    async with UnifiedHttpClient(http_config, cache_manager=manager) as client:
        # Note: We can't easily test real HTTP without a server,
        # but we can verify the logic if we had a mock session.
        # For this QA, we'll just verify the config initialization.
        assert client._cache is not None
        print("✓ UnifiedHttpClient cache initialized")

    # Cleanup
    await manager.clear()
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    print("\n=== QA & Benchmarks Completed Successfully ===")


if __name__ == "__main__":
    # Add src to path
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent / "src"))

    asyncio.run(run_qa_and_benchmarks())
