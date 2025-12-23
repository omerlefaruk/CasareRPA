"""
Reroute Node Item - Custom graphics item for Houdini-style reroute dots.

Provides a minimal diamond-shaped node for organizing wire routing.
Ports are invisible and positioned at center for clean wire connections.

Key features:
- 16px diamond shape (no header, no widgets)
- Ports invisible but functional at center
- Wire color inheritance from connected type
- Selection glow matching other nodes

All colors are sourced from the unified theme system (theme.py).
"""

from typing import Optional

from NodeGraphQt.qgraphics.node_base import NodeItem
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsItem

# Import unified theme system for all colors
from casare_rpa.presentation.canvas.ui.theme import Theme, _hex_to_qcolor

# ============================================================================
# REROUTE NODE VISUAL CONSTANTS - Delegated to unified theme
# ============================================================================
# Colors are lazily initialized from theme to ensure consistency and
# avoid import-time QApplication dependency issues.

# =========================
# CONTROLLERS - Adjust these (geometry, not colors)
# =========================

# Diamond size controller (total width/height in pixels)
_DIAMOND_SIZE = 30.0

# Circle gap controller - space between input circle edge and output circle edge
_CIRCLE_GAP = 30.0

# Diamond offset controller - fine-tune diamond position
# Positive X = move right, Negative X = move left
_DIAMOND_OFFSET_X = 7.0
_DIAMOND_OFFSET_Y = 0.0

# =========================
# Calculated values (don't modify)
# =========================

_REROUTE_SIZE = _DIAMOND_SIZE
_REROUTE_HALF = _REROUTE_SIZE / 2.0

# NodeGraphQt port dimensions
_PORT_WIDTH = 22.0
_PORT_HALF = _PORT_WIDTH / 2.0
_PORT_RADIUS = 5.0  # Visual circle radius

# Port positions calculated from gap
_INPUT_PORT_X = 0.0
_INPUT_CIRCLE_X = _INPUT_PORT_X + _PORT_HALF  # = 11

# Output port positioned to create the specified gap
# Gap is measured from input circle right edge to output circle left edge
_OUTPUT_CIRCLE_X = _INPUT_CIRCLE_X + _PORT_RADIUS + _CIRCLE_GAP + _PORT_RADIUS
_OUTPUT_PORT_X = _OUTPUT_CIRCLE_X - _PORT_HALF

# Node dimensions
_NODE_WIDTH = _OUTPUT_PORT_X + _PORT_WIDTH
_NODE_HEIGHT = 22.0

# Diamond center - exactly between the two circles
_NODE_CENTER_X = (_INPUT_CIRCLE_X + _OUTPUT_CIRCLE_X) / 2.0
_NODE_CENTER_Y = _NODE_HEIGHT / 2.0


# ============================================================================
# COLOR CACHES - Initialized lazily from theme
# ============================================================================

_REROUTE_FILL_COLOR: QColor | None = None
_REROUTE_BORDER_COLOR: QColor | None = None
_REROUTE_SELECTED_COLOR: QColor | None = None
_REROUTE_HOVER_COLOR: QColor | None = None
_DEFAULT_TYPE_COLOR: QColor | None = None


def _get_reroute_fill_color() -> QColor:
    """Get reroute fill color from theme."""
    cc = Theme.get_canvas_colors()
    return _hex_to_qcolor(cc.node_bg)


def _get_reroute_border_color() -> QColor:
    """Get reroute border color from theme."""
    return Theme.get_node_border_qcolor("normal")


def _get_reroute_selected_color() -> QColor:
    """Get reroute selection color from theme."""
    return Theme.get_node_border_qcolor("selected")


def _get_reroute_hover_color() -> QColor:
    """Get reroute hover color from theme."""
    return Theme.get_node_border_qcolor("hover")


def _get_default_type_color() -> QColor:
    """Get default type color (ANY) from theme."""
    cc = Theme.get_canvas_colors()
    return _hex_to_qcolor(cc.wire_any)


def _init_reroute_colors():
    """Initialize all reroute color variables from theme."""
    global _REROUTE_FILL_COLOR, _REROUTE_BORDER_COLOR, _REROUTE_SELECTED_COLOR
    global _REROUTE_HOVER_COLOR, _DEFAULT_TYPE_COLOR

    if _REROUTE_FILL_COLOR is None:
        _REROUTE_FILL_COLOR = _get_reroute_fill_color()
        _REROUTE_BORDER_COLOR = _get_reroute_border_color()
        _REROUTE_SELECTED_COLOR = _get_reroute_selected_color()
        _REROUTE_HOVER_COLOR = _get_reroute_hover_color()
        _DEFAULT_TYPE_COLOR = _get_default_type_color()


class RerouteNodeItem(NodeItem):
    """
    Custom graphics item for reroute/dot nodes.

    Renders as a small diamond shape without header, widgets, or visible ports.
    Connections attach to the visual center of the diamond.
    """

    def __init__(self, name: str = "reroute", parent: QGraphicsItem | None = None):
        """
        Initialize reroute node item.

        Args:
            name: Node name
            parent: Parent graphics item
        """
        super().__init__(name, parent)

        # Initialize colors from unified theme (lazy initialization)
        _init_reroute_colors()

        # Reroute-specific state
        self._type_color: QColor = QColor(_DEFAULT_TYPE_COLOR)
        self._is_hovered: bool = False

        # Override size to fit diamond with ports on sides
        self._width = _NODE_WIDTH
        self._height = _NODE_HEIGHT

        # Bring node to front so diamond renders on top of port circles
        self.setZValue(10)

        # Disable text drawing
        if hasattr(self, "_text_item") and self._text_item:
            self._text_item.setVisible(False)

        # Disable icon
        if hasattr(self, "_icon_item") and self._icon_item:
            self._icon_item.setVisible(False)

        # Accept hover events
        self.setAcceptHoverEvents(True)

    def post_init(self, viewer: object | None = None, selected: bool = False) -> None:
        """
        Post-initialization to center ports.

        Called after the node is added to scene.

        Args:
            viewer: Optional viewer reference
            selected: Initial selection state
        """
        super().post_init(viewer, selected)

        # Position ports on left/right of diamond
        self._position_ports()

        # Defer positioning to catch any late-added ports
        QTimer.singleShot(0, self._position_ports)

    def _position_ports(self) -> None:
        """
        Position ports on left/right of diamond.

        Ports draw their own circles at rect.center(), so we position the
        port's top-left corner such that the center aligns with our layout.
        """
        # Port Y position (centered vertically, accounting for port height)
        port_y = _NODE_CENTER_Y - _PORT_HALF

        # Access ports via node reference
        if hasattr(self, "_node") and self._node:
            try:
                for port in self._node.input_ports():
                    if hasattr(port, "view") and port.view:
                        port.view.setPos(_INPUT_PORT_X, port_y)
                        port.view.setFlag(
                            QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True
                        )
                for port in self._node.output_ports():
                    if hasattr(port, "view") and port.view:
                        port.view.setPos(_OUTPUT_PORT_X, port_y)
                        port.view.setFlag(
                            QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True
                        )
            except Exception:
                pass

        # Fallback: Check child items by type
        for port_item in self.childItems():
            port_class = type(port_item).__name__
            if "PortIn" in port_class or "Input" in port_class:
                port_item.setPos(_INPUT_PORT_X, port_y)
                port_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)
            elif "PortOut" in port_class or "Output" in port_class:
                port_item.setPos(_OUTPUT_PORT_X, port_y)
                port_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)

    def boundingRect(self) -> QRectF:
        """
        Return bounding rect for the reroute node.

        Includes space for diamond and port circles on sides.
        """
        return QRectF(0, 0, _NODE_WIDTH, _NODE_HEIGHT)

    def shape(self) -> QPainterPath:
        """
        Return the shape for hit testing - only the diamond area.

        This prevents the diamond from intercepting hover/click events
        meant for the port circles on the sides.
        """
        path = QPainterPath()
        center = QPointF(_NODE_CENTER_X + _DIAMOND_OFFSET_X, _NODE_CENTER_Y + _DIAMOND_OFFSET_Y)
        path.moveTo(center.x(), center.y() - _REROUTE_HALF)  # Top
        path.lineTo(center.x() + _REROUTE_HALF, center.y())  # Right
        path.lineTo(center.x(), center.y() + _REROUTE_HALF)  # Bottom
        path.lineTo(center.x() - _REROUTE_HALF, center.y())  # Left
        path.closeSubpath()
        return path

    def paint(
        self,
        painter: QPainter,
        option: object | None,
        widget: object | None,
    ) -> None:
        """
        Paint the reroute diamond only.

        Port circles are drawn by the port painter_func for perfect wire alignment.

        Args:
            painter: QPainter to draw with
            option: Style option (unused)
            widget: Widget being painted on (unused)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Diamond center with offset
        center = QPointF(_NODE_CENTER_X + _DIAMOND_OFFSET_X, _NODE_CENTER_Y + _DIAMOND_OFFSET_Y)

        # Create diamond path
        diamond = QPainterPath()
        diamond.moveTo(center.x(), center.y() - _REROUTE_HALF)  # Top
        diamond.lineTo(center.x() + _REROUTE_HALF, center.y())  # Right
        diamond.lineTo(center.x(), center.y() + _REROUTE_HALF)  # Bottom
        diamond.lineTo(center.x() - _REROUTE_HALF, center.y())  # Left
        diamond.closeSubpath()

        # Determine colors based on state
        if self.isSelected():
            # Selected - use yellow border with glow
            glow_radius = _REROUTE_SIZE
            glow_gradient = QRadialGradient(center, glow_radius)
            glow_gradient.setColorAt(0, QColor(255, 215, 0, 100))
            glow_gradient.setColorAt(1, QColor(255, 215, 0, 0))
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, glow_radius, glow_radius)

            # Diamond with yellow border
            painter.setBrush(QBrush(self._type_color.darker(130)))
            painter.setPen(QPen(_REROUTE_SELECTED_COLOR, 2))
            painter.drawPath(diamond)

        elif self._is_hovered:
            # Hovered - lighter fill
            painter.setBrush(QBrush(_REROUTE_HOVER_COLOR))
            painter.setPen(QPen(self._type_color, 1.5))
            painter.drawPath(diamond)

        else:
            # Normal state - use type color for border
            painter.setBrush(QBrush(_REROUTE_FILL_COLOR))
            painter.setPen(QPen(self._type_color, 1.5))
            painter.drawPath(diamond)

    def set_type_color(self, color: QColor) -> None:
        """
        Set the type color for this reroute node.

        The border color will match the connected wire type.

        Args:
            color: QColor for the wire type
        """
        self._type_color = color
        self.update()

    def get_type_color(self) -> QColor:
        """Get the current type color."""
        return self._type_color

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter."""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave."""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for selection and dragging."""
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        super().mouseReleaseEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """
        Handle item changes.

        Re-position ports after position changes to maintain correct wire attachment.
        """
        result = super().itemChange(change, value)

        # Re-position ports after any position change
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._position_ports()

        return result
