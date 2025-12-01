"""Tests for viewport culling performance optimization.

Tests the ViewportCullingManager for efficient spatial queries
and visibility management in large canvas workflows.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtCore import QRectF


class TestSpatialHash:
    """Tests for SpatialHash spatial partitioning."""

    def test_insert_and_query_single_node(self):
        """Test inserting and querying a single node."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import SpatialHash

        spatial = SpatialHash(cell_size=100)

        # Insert a node at position (50, 50) with size 100x100
        spatial.insert("node_1", QRectF(50, 50, 100, 100))

        # Query should find the node
        result = spatial.query(QRectF(0, 0, 200, 200))
        assert "node_1" in result

        # Query far away should not find the node
        result = spatial.query(QRectF(1000, 1000, 100, 100))
        assert "node_1" not in result

    def test_insert_updates_position(self):
        """Test that re-inserting a node updates its position."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import SpatialHash

        spatial = SpatialHash(cell_size=100)

        # Insert node at original position
        spatial.insert("node_1", QRectF(50, 50, 100, 100))

        # Move node to new position
        spatial.insert("node_1", QRectF(500, 500, 100, 100))

        # Old position should not find node
        result = spatial.query(QRectF(0, 0, 200, 200))
        assert "node_1" not in result

        # New position should find node
        result = spatial.query(QRectF(400, 400, 200, 200))
        assert "node_1" in result

    def test_remove_node(self):
        """Test removing a node from spatial hash."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import SpatialHash

        spatial = SpatialHash(cell_size=100)

        spatial.insert("node_1", QRectF(50, 50, 100, 100))
        spatial.remove("node_1")

        # Should not find removed node
        result = spatial.query(QRectF(0, 0, 200, 200))
        assert "node_1" not in result

    def test_query_large_area_multiple_nodes(self):
        """Test querying a large area with multiple nodes."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import SpatialHash

        spatial = SpatialHash(cell_size=100)

        # Insert 100 nodes in a grid
        for i in range(10):
            for j in range(10):
                node_id = f"node_{i}_{j}"
                spatial.insert(node_id, QRectF(i * 100, j * 100, 80, 80))

        # Query covering all nodes
        result = spatial.query(QRectF(0, 0, 1000, 1000))
        assert len(result) == 100

        # Query covering only part of the grid
        result = spatial.query(QRectF(0, 0, 300, 300))
        assert len(result) >= 9  # At least the 3x3 corner nodes

    def test_performance_100_nodes_1000_queries(self):
        """Test performance with 100 nodes and 1000 queries."""
        import time
        from casare_rpa.presentation.canvas.graph.viewport_culling import SpatialHash

        spatial = SpatialHash(cell_size=200)

        # Insert 100 nodes
        for i in range(100):
            x = (i % 10) * 200
            y = (i // 10) * 200
            spatial.insert(f"node_{i}", QRectF(x, y, 150, 100))

        # Run 1000 queries
        start = time.perf_counter()
        for i in range(1000):
            x = (i % 20) * 100
            y = ((i // 20) % 20) * 100
            spatial.query(QRectF(x, y, 400, 400))
        elapsed = time.perf_counter() - start

        # Should complete in under 100ms
        assert (
            elapsed < 0.1
        ), f"1000 queries took {elapsed * 1000:.1f}ms (expected <100ms)"


class TestViewportCullingManager:
    """Tests for ViewportCullingManager visibility management."""

    def test_register_node(self):
        """Test registering a node."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=100, margin=50)

        mock_item = MagicMock()
        culler.register_node("node_1", mock_item, QRectF(0, 0, 100, 100))

        stats = culler.get_stats()
        assert stats["total_nodes"] == 1

    def test_unregister_node(self):
        """Test unregistering a node."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=100, margin=50)

        mock_item = MagicMock()
        culler.register_node("node_1", mock_item, QRectF(0, 0, 100, 100))
        culler.unregister_node("node_1")

        stats = culler.get_stats()
        assert stats["total_nodes"] == 0

    def test_update_viewport_shows_visible_nodes(self):
        """Test that viewport update correctly identifies visible nodes."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=100, margin=0)

        # Create mock items with required methods
        def create_mock_item():
            item = MagicMock()
            item.scene.return_value = MagicMock()  # Not None
            item.setVisible = MagicMock()
            return item

        # Register nodes
        item1 = create_mock_item()
        item2 = create_mock_item()
        culler.register_node("visible", item1, QRectF(100, 100, 50, 50))
        culler.register_node("hidden", item2, QRectF(1000, 1000, 50, 50))

        # Update viewport to see only first node
        newly_visible, newly_hidden = culler.update_viewport(QRectF(0, 0, 300, 300))

        # visible node should be in visible set
        assert "visible" in culler.get_visible_nodes()

    def test_pipe_culling(self):
        """Test that pipes are hidden when connected nodes are hidden."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=100, margin=0)

        def create_mock_item():
            item = MagicMock()
            item.scene.return_value = MagicMock()
            item.setVisible = MagicMock()
            return item

        # Register nodes
        node1_item = create_mock_item()
        node2_item = create_mock_item()
        pipe_item = create_mock_item()

        culler.register_node("node1", node1_item, QRectF(100, 100, 50, 50))
        culler.register_node("node2", node2_item, QRectF(1000, 1000, 50, 50))
        culler.register_pipe("pipe1", "node1", "node2", pipe_item)

        stats = culler.get_stats()
        assert stats["total_pipes"] == 1

        # Update viewport (node1 visible, node2 hidden)
        culler.update_viewport(QRectF(0, 0, 300, 300))

        # Pipe should be hidden (node2 is outside viewport)
        stats = culler.get_stats()
        assert stats["visible_pipes"] == 0

    def test_clear_resets_all(self):
        """Test that clear() resets all state."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager()

        mock_item = MagicMock()
        culler.register_node("node1", mock_item, QRectF(0, 0, 100, 100))
        culler.register_pipe("pipe1", "node1", "node2", mock_item)

        culler.clear()

        stats = culler.get_stats()
        assert stats["total_nodes"] == 0
        assert stats["total_pipes"] == 0

    def test_disabled_culling_shows_all(self):
        """Test that disabling culling shows all nodes."""
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=100, margin=0)

        def create_mock_item():
            item = MagicMock()
            item.scene.return_value = MagicMock()
            item.setVisible = MagicMock()
            return item

        item = create_mock_item()
        culler.register_node("node1", item, QRectF(1000, 1000, 50, 50))

        # Disable culling
        culler.set_enabled(False)

        # Node should be visible
        item.setVisible.assert_called_with(True)


class TestViewportCullingPerformance:
    """Performance tests for viewport culling."""

    def test_update_viewport_500_nodes_under_10ms(self):
        """Test viewport update performance with 500 nodes."""
        import time
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=200, margin=100)

        # Register 500 nodes in a grid
        def create_mock_item():
            item = MagicMock()
            item.scene.return_value = MagicMock()
            item.setVisible = MagicMock()
            return item

        for i in range(500):
            x = (i % 25) * 200
            y = (i // 25) * 200
            item = create_mock_item()
            culler.register_node(f"node_{i}", item, QRectF(x, y, 150, 100))

        # Measure viewport update time
        start = time.perf_counter()
        for _ in range(100):
            culler.update_viewport(QRectF(0, 0, 1000, 800))
        elapsed = (time.perf_counter() - start) / 100 * 1000  # Convert to ms

        assert elapsed < 10, f"Update took {elapsed:.2f}ms (expected <10ms)"

    def test_update_viewport_with_pipes_under_20ms(self):
        """Test viewport update with nodes and pipes."""
        import time
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        culler = ViewportCullingManager(cell_size=200, margin=100)

        def create_mock_item():
            item = MagicMock()
            item.scene.return_value = MagicMock()
            item.setVisible = MagicMock()
            return item

        # Register 100 nodes
        for i in range(100):
            x = (i % 10) * 200
            y = (i // 10) * 200
            item = create_mock_item()
            culler.register_node(f"node_{i}", item, QRectF(x, y, 150, 100))

        # Register 150 pipes (linear connections plus some cross-connections)
        for i in range(99):
            pipe_item = create_mock_item()
            culler.register_pipe(f"pipe_{i}", f"node_{i}", f"node_{i+1}", pipe_item)
        for i in range(50):
            pipe_item = create_mock_item()
            culler.register_pipe(
                f"pipe_cross_{i}", f"node_{i}", f"node_{i+10}", pipe_item
            )

        # Measure viewport update time
        start = time.perf_counter()
        for _ in range(100):
            culler.update_viewport(QRectF(0, 0, 1000, 800))
        elapsed = (time.perf_counter() - start) / 100 * 1000

        assert elapsed < 20, f"Update took {elapsed:.2f}ms (expected <20ms)"
