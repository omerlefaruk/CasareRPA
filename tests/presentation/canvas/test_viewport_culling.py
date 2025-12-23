from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QRectF

from casare_rpa.presentation.canvas.graph.viewport_culling import ViewportCullingManager


class MockPipeItem:
    def __init__(self, rect=None):
        self._rect = rect
        self._visible = True
        self._scene = MagicMock()

    def sceneBoundingRect(self):
        return self._rect if self._rect else QRectF()

    def setVisible(self, visible):
        self._visible = visible

    def isVisible(self):
        return self._visible

    def scene(self):
        return self._scene


class TestViewportCullingManager:
    @pytest.fixture
    def manager(self):
        return ViewportCullingManager(cell_size=100, margin=10)

    def test_initialization(self, manager):
        assert manager.is_enabled()
        # Check internal margin if accessible or infer from behavior

    def test_pipe_visibility_both_nodes_visible(self, manager):
        # Setup
        manager.register_node("node1", MagicMock(), QRectF(0, 0, 50, 50))
        manager.register_node("node2", MagicMock(), QRectF(100, 0, 50, 50))

        pipe_item = MockPipeItem(QRectF(0, 0, 150, 50))
        manager.register_pipe("pipe1", "node1", "node2", pipe_item)

        # Viewport covering both
        viewport = QRectF(0, 0, 200, 200)
        manager.update_viewport(viewport)

        assert pipe_item.isVisible() is True

    def test_pipe_visibility_one_node_visible(self, manager):
        # node1 visible, node2 hidden
        manager.register_node("node1", MagicMock(), QRectF(0, 0, 50, 50))
        manager.register_node("node2", MagicMock(), QRectF(1000, 0, 50, 50))

        pipe_item = MockPipeItem(QRectF(0, 0, 1050, 50))
        manager.register_pipe("pipe1", "node1", "node2", pipe_item)

        # Viewport covering only node1
        viewport = QRectF(0, 0, 200, 200)
        manager.update_viewport(viewport)

        # Should be visible because node1 is visible
        assert pipe_item.isVisible() is True

    def test_pipe_visibility_intersection(self, manager):
        # Both nodes hidden, but pipe crosses viewport
        manager.register_node("node1", MagicMock(), QRectF(-500, 0, 50, 50))
        manager.register_node("node2", MagicMock(), QRectF(500, 0, 50, 50))

        # Pipe spans from -500 to 500
        pipe_item = MockPipeItem(QRectF(-500, 0, 1000, 50))
        manager.register_pipe("pipe1", "node1", "node2", pipe_item)

        # Viewport in the middle (0,0)
        viewport = QRectF(0, 0, 100, 100)
        manager.update_viewport(viewport)

        # Nodes are not visible
        visible_nodes = manager.get_visible_nodes()
        assert "node1" not in visible_nodes
        assert "node2" not in visible_nodes

        # But pipe MUST be visible because it intersects
        assert pipe_item.isVisible() is True

    def test_pipe_visibility_completely_hidden(self, manager):
        # Everything far away
        manager.register_node("node1", MagicMock(), QRectF(1000, 0, 50, 50))
        manager.register_node("node2", MagicMock(), QRectF(1100, 0, 50, 50))

        pipe_item = MockPipeItem(QRectF(1000, 0, 150, 50))
        manager.register_pipe("pipe1", "node1", "node2", pipe_item)

        # Viewport at 0,0
        viewport = QRectF(0, 0, 100, 100)
        manager.update_viewport(viewport)

        assert pipe_item.isVisible() is False
