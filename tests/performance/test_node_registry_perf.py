"""
Node Registry Performance Tests.

Tests the lazy loading effectiveness and lookup performance of the node registry.
Measures:
- Time to import all nodes
- Lazy loading effectiveness (first import vs subsequent)
- get_node_class() lookup time
- Memory footprint with all nodes loaded

Run with: pytest tests/performance/test_node_registry_perf.py -v
"""

import gc
import importlib
import sys
import time
import tracemalloc
from typing import Dict, List, Type

import pytest


# Performance thresholds
MAX_FIRST_IMPORT_TIME_S = 5.0  # Cold import of all nodes
MAX_SUBSEQUENT_IMPORT_TIME_S = 0.1  # Cached import
MAX_SINGLE_LOOKUP_TIME_MS = 10.0  # Single node lookup
MAX_MEMORY_MB = 100  # Memory footprint with all nodes loaded
MAX_REGISTRY_SIZE = 500  # Expected node count (sanity check)


class TestNodeRegistryImportPerformance:
    """Test import performance of the node registry."""

    def test_initial_import_time(self) -> None:
        """
        Test that importing the nodes package is fast.

        The package uses lazy loading, so initial import should only
        load the registry dict, not all node classes.
        """
        # Clear from cache to simulate cold import
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        start = time.perf_counter()
        import casare_rpa.nodes as nodes_module

        elapsed = time.perf_counter() - start

        # Initial import should be very fast (just loading registry)
        assert elapsed < 1.0, (
            f"Initial nodes package import took {elapsed:.2f}s (threshold: 1.0s). "
            "Lazy loading may not be working."
        )

        # Verify registry is available
        assert hasattr(nodes_module, "_NODE_REGISTRY")
        assert len(nodes_module._NODE_REGISTRY) > 100, "Registry seems too small"

    def test_lazy_loading_effectiveness(self) -> None:
        """
        Test that nodes are not loaded until accessed.

        After importing the package, _loaded_classes should be empty
        until we explicitly access a node class.
        """
        # Reimport to get fresh state
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        import casare_rpa.nodes as nodes

        # Check that no classes are loaded yet
        assert (
            len(nodes._loaded_classes) == 0
        ), f"Expected 0 loaded classes after import, found {len(nodes._loaded_classes)}"

        # Access a few nodes
        _ = nodes.StartNode
        _ = nodes.EndNode
        _ = nodes.SetVariableNode

        # Now we should have exactly 3 classes loaded
        assert (
            len(nodes._loaded_classes) == 3
        ), f"Expected 3 loaded classes, found {len(nodes._loaded_classes)}"

    def test_first_import_vs_subsequent(self) -> None:
        """
        Test that subsequent lookups are faster than first lookup.

        First lookup triggers module import, subsequent lookups hit cache.
        """
        # Clear cache
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        import casare_rpa.nodes as nodes

        # First lookup (triggers import)
        start = time.perf_counter()
        _ = nodes.ClickElementNode
        first_time = time.perf_counter() - start

        # Subsequent lookup (from cache)
        start = time.perf_counter()
        _ = nodes.ClickElementNode
        second_time = time.perf_counter() - start

        # Subsequent should be much faster
        assert second_time < first_time, (
            f"Subsequent lookup ({second_time*1000:.3f}ms) not faster than "
            f"first ({first_time*1000:.3f}ms)"
        )

        # Subsequent should be very fast (< 0.1ms typically)
        assert (
            second_time < 0.001
        ), f"Cached lookup took {second_time*1000:.3f}ms (threshold: 1.0ms)"


class TestNodeLookupPerformance:
    """Test node lookup performance."""

    def test_single_lookup_time(self) -> None:
        """Test that single node lookup is fast."""
        from casare_rpa.nodes import _lazy_import

        # Warm up cache
        _ = _lazy_import("StartNode")

        # Time cached lookup
        start = time.perf_counter()
        for _ in range(100):
            _ = _lazy_import("StartNode")
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / 100) * 1000

        assert avg_time_ms < MAX_SINGLE_LOOKUP_TIME_MS, (
            f"Average lookup time {avg_time_ms:.3f}ms exceeds "
            f"threshold {MAX_SINGLE_LOOKUP_TIME_MS}ms"
        )

    def test_multiple_node_lookup_performance(self) -> None:
        """Test looking up multiple different nodes."""
        from casare_rpa.nodes import _lazy_import, _NODE_REGISTRY

        # Get a sample of node names
        sample_nodes = list(_NODE_REGISTRY.keys())[:50]

        # First pass: warm cache
        for name in sample_nodes:
            _ = _lazy_import(name)

        # Second pass: measure cached lookups
        start = time.perf_counter()
        for _ in range(10):
            for name in sample_nodes:
                _ = _lazy_import(name)
        elapsed = time.perf_counter() - start

        total_lookups = 10 * len(sample_nodes)
        avg_time_us = (elapsed / total_lookups) * 1_000_000

        # Cached lookups should be very fast (< 100 microseconds)
        assert (
            avg_time_us < 100
        ), f"Average cached lookup {avg_time_us:.1f}us exceeds 100us threshold"


class TestGetAllNodesPerformance:
    """Test performance of loading all nodes."""

    def test_load_all_nodes_time(self) -> None:
        """
        Test time to load all node classes.

        This is a worst-case scenario where all nodes are imported.
        Should complete in reasonable time.
        """
        # Clear cache
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        from casare_rpa.nodes import get_all_node_classes, _NODE_REGISTRY

        registry_size = len(_NODE_REGISTRY)

        start = time.perf_counter()
        all_classes = get_all_node_classes()
        elapsed = time.perf_counter() - start

        assert (
            len(all_classes) == registry_size
        ), f"Expected {registry_size} classes, got {len(all_classes)}"

        assert elapsed < MAX_FIRST_IMPORT_TIME_S, (
            f"Loading all {registry_size} nodes took {elapsed:.2f}s "
            f"(threshold: {MAX_FIRST_IMPORT_TIME_S}s)"
        )

    def test_subsequent_get_all_nodes_time(self) -> None:
        """Test that subsequent get_all_node_classes is fast (cached)."""
        from casare_rpa.nodes import get_all_node_classes

        # First call (loads all)
        _ = get_all_node_classes()

        # Second call (cached)
        start = time.perf_counter()
        all_classes = get_all_node_classes()
        elapsed = time.perf_counter() - start

        assert elapsed < MAX_SUBSEQUENT_IMPORT_TIME_S, (
            f"Cached get_all_node_classes took {elapsed:.3f}s "
            f"(threshold: {MAX_SUBSEQUENT_IMPORT_TIME_S}s)"
        )


class TestNodeRegistryMemory:
    """Test memory usage of node registry."""

    def test_memory_footprint_with_all_nodes(self) -> None:
        """
        Test memory usage with all nodes loaded.

        Loads all node classes and measures peak memory usage.
        """
        gc.collect()
        tracemalloc.start()

        from casare_rpa.nodes import get_all_node_classes

        # Load all classes
        all_classes = get_all_node_classes()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)

        assert peak_mb < MAX_MEMORY_MB, (
            f"Memory usage {peak_mb:.1f}MB exceeds {MAX_MEMORY_MB}MB threshold "
            f"({len(all_classes)} nodes loaded)"
        )

    def test_memory_per_node_class(self) -> None:
        """Test average memory per node class is reasonable."""
        gc.collect()
        tracemalloc.start()

        from casare_rpa.nodes import get_all_node_classes

        # Load all classes
        all_classes = get_all_node_classes()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if len(all_classes) > 0:
            memory_per_node_kb = (peak / 1024) / len(all_classes)

            # Expect < 50KB per node class on average
            assert memory_per_node_kb < 50, (
                f"Average memory per node {memory_per_node_kb:.1f}KB "
                "exceeds 50KB threshold"
            )

    def test_lazy_loading_memory_savings(self) -> None:
        """
        Test that lazy loading saves memory.

        Compares memory with few nodes loaded vs all nodes loaded.
        """
        # Clear cache
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        # Measure memory with few nodes
        tracemalloc.start()
        from casare_rpa.nodes import StartNode, EndNode, SetVariableNode

        _, few_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        gc.collect()

        # Measure memory with all nodes
        tracemalloc.start()
        from casare_rpa.nodes import get_all_node_classes

        _ = get_all_node_classes()
        _, all_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # All nodes should use more memory than few nodes
        assert (
            all_peak > few_peak
        ), "Loading all nodes should use more memory than loading few nodes"

        # Memory savings should be significant (at least 2x)
        ratio = all_peak / few_peak if few_peak > 0 else 0
        assert ratio > 2, f"Expected at least 2x memory difference, got {ratio:.1f}x"


class TestRegistryIntegrity:
    """Test registry integrity and correctness."""

    def test_registry_node_count(self) -> None:
        """Verify registry contains expected number of nodes."""
        from casare_rpa.nodes import _NODE_REGISTRY

        count = len(_NODE_REGISTRY)

        # Should have many nodes (at least 200)
        assert count >= 200, f"Registry has only {count} nodes, expected at least 200"

        # Should not be unreasonably large
        assert (
            count < MAX_REGISTRY_SIZE
        ), f"Registry has {count} nodes, exceeds max {MAX_REGISTRY_SIZE}"

    def test_all_registry_entries_are_valid(self) -> None:
        """Test that all registry entries can be loaded."""
        from casare_rpa.nodes import _NODE_REGISTRY, _lazy_import

        failed_nodes: List[str] = []

        for name in list(_NODE_REGISTRY.keys())[:50]:  # Test first 50
            try:
                cls = _lazy_import(name)
                assert cls is not None
            except Exception as e:
                failed_nodes.append(f"{name}: {e}")

        assert len(failed_nodes) == 0, f"Failed to load nodes: {failed_nodes}"

    def test_node_types_are_classes(self) -> None:
        """Verify loaded nodes are actual classes."""
        from casare_rpa.nodes import _lazy_import, _NODE_REGISTRY

        sample_nodes = ["StartNode", "EndNode", "ClickElementNode", "SetVariableNode"]

        for name in sample_nodes:
            if name in _NODE_REGISTRY:
                cls = _lazy_import(name)
                assert isinstance(cls, type), f"{name} is not a class"


class TestPreloadPerformance:
    """Test preload functionality performance."""

    def test_preload_specific_nodes(self) -> None:
        """Test preloading specific nodes is fast."""
        # Clear cache
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        from casare_rpa.nodes import preload_nodes, _loaded_classes

        nodes_to_preload = [
            "StartNode",
            "EndNode",
            "SetVariableNode",
            "ClickElementNode",
            "TypeTextNode",
            "GoToURLNode",
        ]

        start = time.perf_counter()
        preload_nodes(nodes_to_preload)
        elapsed = time.perf_counter() - start

        # Preloading 6 nodes should be < 1 second
        assert (
            elapsed < 1.0
        ), f"Preloading {len(nodes_to_preload)} nodes took {elapsed:.2f}s"

        # Verify nodes are loaded
        for name in nodes_to_preload:
            assert name in _loaded_classes, f"{name} not preloaded"

    def test_preload_all_nodes(self) -> None:
        """Test preloading all nodes."""
        # Clear cache
        modules_to_remove = [
            key for key in sys.modules.keys() if key.startswith("casare_rpa.nodes")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        gc.collect()

        from casare_rpa.nodes import preload_nodes, _loaded_classes, _NODE_REGISTRY

        start = time.perf_counter()
        preload_nodes()  # Preload all
        elapsed = time.perf_counter() - start

        assert elapsed < MAX_FIRST_IMPORT_TIME_S, (
            f"Preloading all nodes took {elapsed:.2f}s "
            f"(threshold: {MAX_FIRST_IMPORT_TIME_S}s)"
        )

        # Verify all nodes are loaded
        assert len(_loaded_classes) == len(
            _NODE_REGISTRY
        ), f"Expected {len(_NODE_REGISTRY)} loaded, got {len(_loaded_classes)}"
