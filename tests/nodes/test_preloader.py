"""
Tests for node preloader module.

Tests verify that the preloader correctly loads commonly-used nodes
in the background without blocking the main thread.
"""

import time
import threading

import pytest


class TestNodePreloader:
    """Test node preloading functionality."""

    def test_preload_completes_without_error(self):
        """Preloading should complete without raising exceptions."""
        from casare_rpa.nodes.preloader import (
            start_node_preload,
            wait_for_preload,
            is_preload_complete,
        )

        # Reset state for test isolation
        import casare_rpa.nodes.preloader as preloader

        preloader._preload_started = False
        preloader._preload_complete = False
        preloader._preload_thread = None

        start_node_preload()
        completed = wait_for_preload(timeout=30.0)

        assert completed, "Preload should complete within timeout"
        assert is_preload_complete(), "is_preload_complete should return True"

    def test_preload_is_idempotent(self):
        """Calling start_node_preload multiple times should be safe."""
        from casare_rpa.nodes.preloader import start_node_preload

        # Reset state
        import casare_rpa.nodes.preloader as preloader

        preloader._preload_started = False
        preloader._preload_complete = False
        preloader._preload_thread = None

        # Call multiple times - should not raise
        start_node_preload()
        start_node_preload()
        start_node_preload()

        # Wait for completion
        from casare_rpa.nodes.preloader import wait_for_preload

        wait_for_preload(timeout=30.0)

    def test_preload_runs_in_background(self):
        """Preloading should not block the calling thread."""
        from casare_rpa.nodes.preloader import start_node_preload

        # Reset state
        import casare_rpa.nodes.preloader as preloader

        preloader._preload_started = False
        preloader._preload_complete = False
        preloader._preload_thread = None

        start_time = time.perf_counter()
        start_node_preload()
        call_duration = time.perf_counter() - start_time

        # start_node_preload should return immediately (< 100ms)
        assert call_duration < 0.1, f"Preload blocked for {call_duration:.3f}s"

        # Wait for background completion
        from casare_rpa.nodes.preloader import wait_for_preload

        wait_for_preload(timeout=30.0)

    def test_preload_loads_common_nodes(self):
        """After preload, common nodes should be accessible without import lag."""
        from casare_rpa.nodes.preloader import start_node_preload, wait_for_preload

        # Reset state
        import casare_rpa.nodes.preloader as preloader

        preloader._preload_started = False
        preloader._preload_complete = False
        preloader._preload_thread = None

        start_node_preload()
        wait_for_preload(timeout=30.0)

        # Common nodes should be cached now
        from casare_rpa import nodes

        # Access should be fast (cached)
        start = time.perf_counter()
        _ = nodes.StartNode
        _ = nodes.EndNode
        _ = nodes.IfNode
        access_time = time.perf_counter() - start

        # Accessing cached nodes should be very fast (< 10ms)
        assert access_time < 0.01, f"Cached node access took {access_time:.3f}s"

    def test_preload_uses_daemon_thread(self):
        """Preload thread should be a daemon so it doesn't block app exit."""
        from casare_rpa.nodes.preloader import start_node_preload

        # Reset state
        import casare_rpa.nodes.preloader as preloader

        preloader._preload_started = False
        preloader._preload_complete = False
        preloader._preload_thread = None

        start_node_preload()

        # Thread should be daemon
        assert preloader._preload_thread is not None
        assert preloader._preload_thread.daemon, "Preload thread should be daemon"

        # Cleanup
        from casare_rpa.nodes.preloader import wait_for_preload

        wait_for_preload(timeout=30.0)


class TestPreloadIntegration:
    """Integration tests for preloader with nodes package."""

    def test_nodes_package_exports_preload_functions(self):
        """Preload functions should be exported from nodes package."""
        from casare_rpa import nodes

        assert hasattr(nodes, "start_node_preload")
        assert hasattr(nodes, "is_preload_complete")
        assert hasattr(nodes, "wait_for_preload")
        assert callable(nodes.start_node_preload)
        assert callable(nodes.is_preload_complete)
        assert callable(nodes.wait_for_preload)

    def test_preload_nodes_list_is_valid(self):
        """All nodes in PRELOAD_NODES should exist in registry."""
        from casare_rpa.nodes.preloader import PRELOAD_NODES
        from casare_rpa.nodes import _NODE_REGISTRY

        for node_name in PRELOAD_NODES:
            assert (
                node_name in _NODE_REGISTRY
            ), f"Preload node '{node_name}' not found in registry"
