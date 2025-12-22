import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QTransform, QFont
from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget, QGraphicsTextItem

from casare_rpa.presentation.canvas.graph.custom_pipe import CasareLivePipe
from NodeGraphQt.qgraphics.pipe import PortTypeEnum, LayoutDirectionEnum, PipeEnum


class MockPort:
    def __init__(self, name="port_1", port_type=PortTypeEnum.IN.value):
        self.name = name
        self.port_type = port_type

    def scenePos(self):
        return QPointF(0, 0)

    def boundingRect(self):
        return QRectF(0, 0, 10, 10)

    def node(self):
        return None


class MockViewer:
    def __init__(self, layout_direction=LayoutDirectionEnum.HORIZONTAL.value):
        self._layout_direction = layout_direction

    def get_layout_direction(self):
        return self._layout_direction


class TestCasareLivePipe:
    @pytest.fixture
    def pipe_item(self, qtbot):
        """Create a CasareLivePipe instance."""
        item = CasareLivePipe()
        # Initialize internal items that might be expected
        if not hasattr(item, "_idx_text"):
            item._idx_text = QGraphicsTextItem(item)
        if not hasattr(item, "_poly"):
            from PySide6.QtGui import QPolygonF

            item._poly = QPolygonF()
        if not hasattr(item, "_idx_pointer"):
            from PySide6.QtWidgets import QGraphicsPolygonItem

            item._idx_pointer = QGraphicsPolygonItem(item)

        return item

    def test_paint_empty_path(self, pipe_item):
        """Test painting with an empty path does not crash."""
        painter = QPainter()
        option = QStyleOptionGraphicsItem()
        widget = QWidget()

        # Should return early without error
        pipe_item.paint(painter, option, widget)

    def test_paint_with_path(self, pipe_item, qtbot):
        """Test painting with a valid path (solid line rendering)."""
        # Setup path
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(100, 100)
        pipe_item.setPath(path)

        # Mock painter is hard in PySide6 tests without a real engine,
        # but we can try to run it and ensure no exceptions.
        # Ideally we would mock QPainter to verify drawLine calls,
        # but PySide6 classes are C++ wrappers and hard to mock fully.
        # We rely on "no crash" = "fix employed" + visual verification later.

        # Create a real painter on an image
        from PySide6.QtGui import QImage

        image = QImage(200, 200, QImage.Format_ARGB32)
        painter = QPainter(image)

        option = QStyleOptionGraphicsItem()
        widget = QWidget()

        try:
            pipe_item.paint(painter, option, widget)
        finally:
            painter.end()

    def test_draw_index_pointer_horizontal(self, pipe_item):
        """Test start point indicator drawing in horizontal mode."""
        port = MockPort("test_port", PortTypeEnum.IN.value)
        cursor_pos = QPointF(50, 50)

        # Mock viewer method
        pipe_item.viewer_layout_direction = lambda: LayoutDirectionEnum.HORIZONTAL.value

        # Run method
        pipe_item.draw_index_pointer(port, cursor_pos)

        # Check text was set
        assert pipe_item._idx_text.toPlainText() == "test_port"

        # Check position was set (logic check)
        # Horizontal: x - width/2
        text_rect = pipe_item._idx_text.boundingRect()
        expected_x = 50 - (text_rect.width() / 2)
        assert abs(pipe_item._idx_text.x() - expected_x) < 1.0

    def test_draw_index_pointer_vertical(self, pipe_item):
        """Test start point indicator drawing in vertical mode."""
        port = MockPort("test_port", PortTypeEnum.OUT.value)
        cursor_pos = QPointF(50, 50)

        # Mock viewer method
        pipe_item.viewer_layout_direction = lambda: LayoutDirectionEnum.VERTICAL.value

        # Run method
        pipe_item.draw_index_pointer(port, cursor_pos)

        # Check text
        assert pipe_item._idx_text.toPlainText() == "test_port"

        # Check position logic for vertical
        # Vertical: x + width/2.5
        text_rect = pipe_item._idx_text.boundingRect()
        expected_x = 50 + (text_rect.width() / 2.5)
        # Note: floating point comparison
        assert abs(pipe_item._idx_text.x() - expected_x) < 1.0

    def test_draw_index_pointer_none_port(self, pipe_item):
        """Test safe return when port is None."""
        pipe_item.draw_index_pointer(None, QPointF(0, 0))
        # Should not throw


class TestCasarePipe:
    """Tests for the standard CasarePipe."""

    @pytest.fixture
    def pipe_item(self, qtbot):
        from casare_rpa.presentation.canvas.graph.custom_pipe import CasarePipe

        item = CasarePipe()
        return item

    def test_draw_path_no_viewer(self, pipe_item):
        """Test draw_path safe return when viewer is None (undo/redo crash fix)."""
        from unittest.mock import MagicMock

        # Patch the viewer method on the instance to return None
        pipe_item.viewer = MagicMock(return_value=None)

        # Create mock ports
        start_port = MockPort("start", PortTypeEnum.OUT.value)
        end_port = MockPort("end", PortTypeEnum.IN.value)

        # This calls draw_path.
        # If the fix works, it returns None early.
        # If the fix fails, it calls super().draw_path(), which calls self.viewer() (returning None),
        # and then likely tries to access .acyclic or .layout_direction on None, raising AttributeError.
        result = pipe_item.draw_path(start_port, end_port, None)

        assert result is None
