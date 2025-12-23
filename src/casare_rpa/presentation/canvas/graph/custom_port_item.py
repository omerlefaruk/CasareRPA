"""
Custom modernized PortItem for NodeGraphQt.

Implements data-type-based port shapes and handles label truncation.
"""

from NodeGraphQt.constants import ITEM_CACHE_MODE, PortEnum, PortTypeEnum
from NodeGraphQt.qgraphics.port import PortItem
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsTextItem

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.graph.port_shapes import draw_port_shape

# Port label truncation constants
PORT_LABEL_MAX_LENGTH = 12
PORT_LABEL_MAX_WIDTH_PX = 80


class CasarePortItem(PortItem):
    """
    Subclass of PortItem that implements custom shape rendering and label truncation.
    """

    def paint(self, painter, option, widget):
        """Draw the port with shape based on data type."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Calculate port rect
        rect_w = self._width / 1.8
        rect_h = self._height / 1.8
        rect_x = self.boundingRect().center().x() - (rect_w / 2)
        rect_y = self.boundingRect().center().y() - (rect_h / 2)
        port_rect = QRectF(rect_x, rect_y, rect_w, rect_h)
        center = port_rect.center()
        size = rect_w / 2

        # Determine colors based on state
        if self._hovered:
            fill_color = PortEnum.HOVER_COLOR.value
            border_color = PortEnum.HOVER_BORDER_COLOR.value
        elif self.connected_pipes:
            fill_color = PortEnum.ACTIVE_COLOR.value
            border_color = PortEnum.ACTIVE_BORDER_COLOR.value
        else:
            fill_color = self.color
            border_color = self.border_color

        # Try to get data type from visual node
        data_type = None
        is_exec = False
        is_output = self.port_type == PortTypeEnum.OUT.value

        try:
            node_item = self.node
            if node_item:
                visual_node = getattr(node_item, "_node", None)
                if visual_node and hasattr(visual_node, "get_port_type"):
                    port_name = self.name
                    data_type = visual_node.get_port_type(port_name)
                    if hasattr(visual_node, "is_exec_port"):
                        is_exec = visual_node.is_exec_port(port_name)
                    elif data_type is None:
                        is_exec = True
        except Exception:
            pass

        # Draw port shape
        draw_port_shape(
            painter=painter,
            center=QPointF(center.x(), center.y()),
            size=size,
            data_type=data_type,
            fill_color=fill_color,
            border_color=border_color,
            is_exec=is_exec,
            is_output=is_output,
        )

        # Draw connected indicator
        if self.connected_pipes and not self._hovered:
            inner_size = size * 0.4
            border_qcolor = QColor(*border_color)
            painter.setPen(QPen(border_qcolor, 1.6))
            painter.setBrush(border_qcolor)
            painter.drawEllipse(center, inner_size, inner_size)
        elif self._hovered:
            if self.multi_connection:
                inner_size = size * 0.55
                border_qcolor = QColor(*border_color)
                fill_qcolor = QColor(*fill_color)
                painter.setPen(QPen(border_qcolor, 1.4))
                painter.setBrush(fill_qcolor)
            else:
                inner_size = size * 0.3
                border_qcolor = QColor(*border_color)
                painter.setPen(QPen(border_qcolor, 1.6))
                painter.setBrush(border_qcolor)
            painter.drawEllipse(center, inner_size, inner_size)

        painter.restore()


# Apply class-level patch to PortItem to use our modernized paint logic
try:
    from NodeGraphQt.qgraphics.port import PortItem as OriginalPortItem

    OriginalPortItem.paint = CasarePortItem.paint
except Exception as e:
    from loguru import logger

    logger.warning(f"Could not patch PortItem.paint: {e}")
