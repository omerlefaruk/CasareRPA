"""
Collapse Components for NodeFrame

Contains UI components related to frame collapse/expand functionality:
- CollapseButton: Clickable button to toggle collapse state
- ExposedPortIndicator: Visual indicator for external port connections

Following Single Responsibility Principle - these components handle ONLY
collapse-related UI elements.
"""

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QPainter

from casare_rpa.presentation.canvas.graph.style_manager import (
    CollapseButtonStyle,
    ExposedPortStyle,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame


class CollapseButton(QGraphicsRectItem):
    """
    A clickable button to collapse/expand a frame.

    Visual design:
    - Rounded square button in frame header
    - Shows "-" when expanded (click to collapse)
    - Shows "+" when collapsed (click to expand)
    - Hover highlight for better UX
    """

    def __init__(self, parent: "NodeFrame"):
        """
        Initialize collapse button.

        Args:
            parent: Parent NodeFrame
        """
        super().__init__(parent)
        self._parent_frame = parent
        self._is_hovered = False

        # Button size from style
        self._size = CollapseButtonStyle.SIZE
        self.setRect(0, 0, self._size, self._size)

        # Position in top-right of frame header
        self._update_position()

        # Make clickable
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        # Z-value above frame
        self.setZValue(1)

    def _update_position(self) -> None:
        """Update button position based on frame rect."""
        frame_rect = self._parent_frame.rect()
        margin = CollapseButtonStyle.MARGIN
        x = frame_rect.right() - self._size - margin
        y = frame_rect.top() + margin
        self.setPos(x, y)

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the collapse button."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Background color based on hover state
        bg_color = CollapseButtonStyle.get_background_color(self._is_hovered)

        # Draw rounded rectangle background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(CollapseButtonStyle.BORDER_COLOR, 1))
        painter.drawRoundedRect(
            rect, CollapseButtonStyle.CORNER_RADIUS, CollapseButtonStyle.CORNER_RADIUS
        )

        # Draw +/- symbol
        painter.setPen(QPen(CollapseButtonStyle.SYMBOL_COLOR, 2))

        center_x = rect.center().x()
        center_y = rect.center().y()
        symbol_size = CollapseButtonStyle.SYMBOL_SIZE

        # Horizontal line (always present for "-")
        painter.drawLine(
            QPointF(center_x - symbol_size, center_y),
            QPointF(center_x + symbol_size, center_y),
        )

        # Vertical line (only when collapsed - shows "+")
        if self._parent_frame.is_collapsed:
            painter.drawLine(
                QPointF(center_x, center_y - symbol_size),
                QPointF(center_x, center_y + symbol_size),
            )

    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Handle click to toggle collapse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._parent_frame.toggle_collapse()
            event.accept()
        else:
            super().mousePressEvent(event)


class ExposedPortIndicator(QGraphicsEllipseItem):
    """
    Visual indicator for exposed ports on collapsed frames.

    Shows which ports are connected externally when frame is collapsed.
    Color-coded by port type for consistency with the type system.
    """

    def __init__(
        self, port_name: str, is_output: bool, color: QColor, parent: QGraphicsItem
    ):
        """
        Initialize exposed port indicator.

        Args:
            port_name: Name of the port
            is_output: True if output port, False if input
            color: Port type color
            parent: Parent graphics item
        """
        super().__init__(parent)
        self.port_name = port_name
        self.is_output = is_output
        self.port_color = color

        # Indicator size from style
        size = ExposedPortStyle.SIZE
        self.setRect(-size / 2, -size / 2, size, size)

        # Styling
        self.setBrush(QBrush(color))
        self.setPen(
            QPen(
                color.darker(ExposedPortStyle.BORDER_DARKEN),
                ExposedPortStyle.BORDER_WIDTH,
            )
        )

        # Tooltip showing port name
        self.setToolTip(f"{'Output' if is_output else 'Input'}: {port_name}")

        # Accept hover for tooltip
        self.setAcceptHoverEvents(True)


class ExposedPortManager:
    """
    Manages exposed port indicators for a NodeFrame.

    Responsible for:
    - Creating indicators for external connections
    - Positioning indicators on frame edges
    - Clearing indicators on expand
    """

    def __init__(self, frame: "NodeFrame"):
        """
        Initialize port manager.

        Args:
            frame: Parent NodeFrame
        """
        self._frame = frame
        self._indicators: list[ExposedPortIndicator] = []

    @property
    def indicators(self) -> list[ExposedPortIndicator]:
        """Get list of current indicators."""
        return self._indicators

    def create_exposed_ports(self) -> None:
        """Create indicators for ports connected to nodes outside this frame."""
        self.clear()

        # Collect external connections
        input_ports = []
        output_ports = []

        for node in self._frame.contained_nodes:
            if not hasattr(node, "input_ports") or not hasattr(node, "output_ports"):
                continue

            try:
                # Check input ports for external connections
                for port in node.input_ports():
                    for connected_port in port.connected_ports():
                        connected_node = connected_port.node()
                        if connected_node not in self._frame.contained_nodes:
                            input_ports.append(
                                (port.name(), self._get_port_color(port))
                            )

                # Check output ports for external connections
                for port in node.output_ports():
                    for connected_port in port.connected_ports():
                        connected_node = connected_port.node()
                        if connected_node not in self._frame.contained_nodes:
                            output_ports.append(
                                (port.name(), self._get_port_color(port))
                            )
            except Exception:
                pass

        # Create indicators
        rect = self._frame.rect()
        margin = ExposedPortStyle.MARGIN
        port_spacing = ExposedPortStyle.SPACING

        # Input ports on left side
        y_start = (
            rect.top() + rect.height() / 2 - (len(input_ports) - 1) * port_spacing / 2
        )
        for i, (port_name, color) in enumerate(input_ports):
            indicator = ExposedPortIndicator(port_name, False, color, self._frame)
            indicator.setPos(rect.left() + margin, y_start + i * port_spacing)
            self._indicators.append(indicator)

        # Output ports on right side
        y_start = (
            rect.top() + rect.height() / 2 - (len(output_ports) - 1) * port_spacing / 2
        )
        for i, (port_name, color) in enumerate(output_ports):
            indicator = ExposedPortIndicator(port_name, True, color, self._frame)
            indicator.setPos(rect.right() - margin, y_start + i * port_spacing)
            self._indicators.append(indicator)

    def clear(self) -> None:
        """Remove all exposed port indicators."""
        for indicator in self._indicators:
            if indicator.scene():
                indicator.scene().removeItem(indicator)
        self._indicators.clear()

    def _get_port_color(self, port) -> QColor:
        """Get color for a port based on its type."""
        from casare_rpa.presentation.canvas.graph.style_manager import (
            FrameStyleManager,
        )

        return FrameStyleManager.get_port_color(port)
