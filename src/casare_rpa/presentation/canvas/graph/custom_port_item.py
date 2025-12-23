"""
Custom Port Item for CasareRPA.

Provides specialized port rendering with different shapes based on DataType.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from NodeGraphQt.qgraphics.port import PortItem
from NodeGraphQt.constants import PortTypeEnum, PortEnum

from casare_rpa.presentation.canvas.graph.port_shapes import draw_port_shape
from casare_rpa.domain.value_objects.types import DataType


class CasarePortItem(PortItem):
    """
    CasareRPA specialized PortItem with shape-based data type visualization.
    """

    def paint(self, painter, option, widget):
        """
        Draw the port with shape based on data type.
        """
        painter.save()

        # Calculate port rect (same as original NodeGraphQt)
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

        # Determine data type and if it's an exec port
        data_type = None
        is_exec = False
        is_output = self.port_type == PortTypeEnum.OUT.value

        try:
            # Get parent node item
            node_item = self.node
            if node_item:
                # Get visual node via NodeGraphQt's internal _node attribute or .node
                visual_node = getattr(node_item, "_node", None) or getattr(node_item, "node", None)
                if visual_node and hasattr(visual_node, "get_port_type"):
                    port_name = self.name
                    data_type = visual_node.get_port_type(port_name)

                    # Check if it's an exec port
                    if hasattr(visual_node, "is_exec_port"):
                        is_exec = visual_node.is_exec_port(port_name)
                    elif data_type is None:
                        is_exec = True
        except Exception:
            pass  # Fall back to default circle if type detection fails

        # Draw port shape using the centralized drawing utility
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

        # Draw inner connection indicator for non-hovered connected ports
        if self.connected_pipes and not self._hovered:
            inner_size = size * 0.4
            border_qcolor = QColor(*border_color)
            painter.setPen(QPen(border_qcolor, 1.6))
            painter.setBrush(border_qcolor)
            painter.drawEllipse(center, inner_size, inner_size)
        elif self._hovered:
            # Hover indicator (inner circle)
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


# =============================================================================
# MODERNIZATION: Patch NodeGraphQt.PortItem.paint to use our custom logic
# This ensures all ports (even in non-Casare nodes) benefit from typed shapes.
# =============================================================================
try:
    from NodeGraphQt.qgraphics.port import PortItem as OriginalPortItem

    OriginalPortItem.paint = CasarePortItem.paint
except Exception as e:
    from loguru import logger

    logger.warning(f"Could not patch PortItem.paint: {e}")
