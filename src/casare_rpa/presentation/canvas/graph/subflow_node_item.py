"""
Subflow Node Item - Custom graphics item for subflow nodes.

Provides visual representation of a collapsed subflow:
- Stack visual effect to indicate nested nodes
- Node count badge showing internal node count
- Expand button to open subflow editor
- Blue-gray header tint for visual distinction

Key features:
- Collapsed view: Single node representing entire subflow
- Dynamic ports based on subflow inputs/outputs
- Double-click to expand/edit subflow
"""

from typing import Optional

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QPainterPath,
    QFont,
    QLinearGradient,
)
from PySide6.QtWidgets import QGraphicsItem

from casare_rpa.presentation.canvas.graph.custom_node_item import (
    CasareNodeItem,
    LODLevel,
    get_lod_manager,
    _high_performance_mode,
)


# ============================================================================
# SUBFLOW NODE VISUAL CONSTANTS
# ============================================================================

# Subflow header color (blue-gray)
_SUBFLOW_HEADER_COLOR = QColor(0x4A, 0x55, 0x68)  # #4A5568 - Blue-gray
_SUBFLOW_HEADER_ALPHA = 153  # 60% opacity

# Badge colors
_BADGE_BG_COLOR = QColor(0x2D, 0x37, 0x48)  # Dark blue-gray
_BADGE_TEXT_COLOR = QColor(0xFF, 0xFF, 0xFF)  # White

# Expand button colors
_EXPAND_BTN_BG = QColor(60, 65, 75, 180)
_EXPAND_BTN_SYMBOL = QColor(200, 200, 200)
_EXPAND_BTN_HOVER = QColor(80, 85, 95, 200)

# Configure button colors (for parameter promotion)
_CONFIG_BTN_BG = QColor(55, 80, 55, 180)  # Green tint
_CONFIG_BTN_HOVER = QColor(75, 110, 75, 200)

# Border width
_BORDER_WIDTH = 2.0

# Stack visual effect (layers behind main node)
_STACK_LAYER_COUNT = 2
_STACK_OFFSET = 4  # pixels per layer
_STACK_COLORS = [
    QColor(0x2A, 0x35, 0x46),  # Furthest back (darkest)
    QColor(0x3A, 0x45, 0x56),  # Middle layer
]


class SubflowNodeItem(CasareNodeItem):
    """
    Custom graphics item for subflow nodes.

    Extends CasareNodeItem with:
    - Stack visual effect to indicate nested nodes
    - Node count badge
    - Expand button
    """

    # Font for badge text (cached at class level)
    _badge_font: Optional[QFont] = None

    @classmethod
    def get_badge_font(cls) -> QFont:
        """Get cached font for node count badge."""
        if cls._badge_font is None:
            cls._badge_font = QFont("Segoe UI", 8)
            cls._badge_font.setWeight(QFont.Weight.Medium)
        return cls._badge_font

    def __init__(self, name: str = "subflow", parent: Optional[QGraphicsItem] = None):
        """
        Initialize subflow node item.

        Args:
            name: Node display name
            parent: Parent graphics item
        """
        super().__init__(name, parent)

        # Subflow-specific state
        self._node_count: int = 0
        self._expand_button_rect: Optional[QRectF] = None
        self._expand_btn_hovered: bool = False
        self._config_button_rect: Optional[QRectF] = None
        self._config_btn_hovered: bool = False

        # Override cached header color to blue-gray
        self._cached_header_color = QColor(_SUBFLOW_HEADER_COLOR)
        self._cached_header_color.setAlpha(_SUBFLOW_HEADER_ALPHA)

        # Accept hover events for expand button
        self.setAcceptHoverEvents(True)

    def set_node_count(self, count: int) -> None:
        """
        Set the number of nodes inside this subflow.

        Args:
            count: Number of nodes in the subflow
        """
        self._node_count = count
        self.update()

    def get_node_count(self) -> int:
        """Get the number of nodes in this subflow."""
        return self._node_count

    def boundingRect(self) -> QRectF:
        """
        Override bounding rect to include space for stack layers.

        Stack layers extend to the right and bottom of the main node.
        """
        rect = super().boundingRect()
        # Add space for stack layers (extend right and bottom)
        stack_extension = _STACK_OFFSET * _STACK_LAYER_COUNT
        return QRectF(
            rect.x(),
            rect.y(),
            rect.width() + stack_extension,
            rect.height() + stack_extension,
        )

    def _draw_stack_layers(
        self, painter: QPainter, rect: QRectF, radius: float = 8.0
    ) -> None:
        """
        Draw stack layers behind the main node.

        Creates a visual "stacked papers" effect to indicate
        this node contains multiple internal nodes (a subflow).

        Args:
            painter: QPainter to draw with
            rect: The main node rectangle
            radius: Corner radius for rounded rects
        """
        # Draw layers from back (furthest) to front (closest to main node)
        for i in range(_STACK_LAYER_COUNT):
            # Calculate offset - furthest layer has largest offset
            layer_offset = _STACK_OFFSET * (_STACK_LAYER_COUNT - i)

            # Create offset rect for this layer
            layer_rect = QRectF(
                rect.x() + layer_offset,
                rect.y() + layer_offset,
                rect.width(),
                rect.height(),
            )

            # Get color for this layer
            layer_color = QColor(_STACK_COLORS[i])
            if self._is_disabled:
                layer_color.setAlpha(64)

            # Draw the layer (no border, just filled)
            layer_path = QPainterPath()
            layer_path.addRoundedRect(layer_rect, radius, radius)
            painter.fillPath(layer_path, QBrush(layer_color))

    def _draw_stack_layers_lod(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw simplified stack layers for LOD rendering.

        Args:
            painter: QPainter to draw with
            rect: The main node rectangle
        """
        # Simplified: just draw 2 offset rectangles without rounded corners
        for i in range(_STACK_LAYER_COUNT):
            layer_offset = _STACK_OFFSET * (_STACK_LAYER_COUNT - i)
            layer_rect = QRectF(
                rect.x() + layer_offset,
                rect.y() + layer_offset,
                rect.width(),
                rect.height(),
            )

            layer_color = QColor(_STACK_COLORS[i])
            if self._is_disabled:
                layer_color.setAlpha(64)

            painter.fillRect(layer_rect, layer_color)

    def _paint_lod(self, painter: QPainter, lod_level: LODLevel = LODLevel.LOW) -> None:
        """
        Paint simplified LOD version for low zoom levels.

        Subflow nodes use stack visual and solid border at LOD levels.
        Includes simplified stack layers for visual distinction.

        Args:
            lod_level: The LOD level to render at
        """
        painter.save()

        lod_manager = get_lod_manager()
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing, lod_manager.should_use_antialiasing()
        )

        rect = self._get_node_rect()

        # Draw stack layers BEFORE main node (simplified version)
        self._draw_stack_layers_lod(painter, rect)

        # Subflow-specific blue-gray fill
        fill_color = QColor(0x3A, 0x45, 0x56)  # Slightly lighter than header

        # Apply very transparent fill for disabled state (more grayed out)
        if self._is_disabled:
            fill_color.setAlpha(64)

        if lod_level == LODLevel.ULTRA_LOW:
            painter.fillRect(rect, fill_color)
        else:
            painter.setBrush(QBrush(fill_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

        # Solid border for subflow nodes
        pen = QPen(_SUBFLOW_HEADER_COLOR, _BORDER_WIDTH)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if lod_level == LODLevel.ULTRA_LOW:
            painter.drawRect(rect)
        else:
            painter.drawRoundedRect(rect, 4, 4)

        # Draw disabled overlay even at LOD
        if self._is_disabled:
            self._draw_disabled_overlay(painter, rect)

        painter.restore()

    def paint(self, painter: QPainter, option, widget) -> None:
        """
        Custom paint method for subflow node.

        Draws with stack visual effect and subflow-specific elements.
        """
        # Get LOD level from centralized manager
        lod_manager = get_lod_manager()
        lod_level = lod_manager.current_lod

        # HIGH PERFORMANCE MODE: Force LOD rendering
        if _high_performance_mode:
            self._paint_lod(painter, LODLevel.LOW)
            return

        # LOD check - at low zoom, render simplified version
        if lod_level in (LODLevel.ULTRA_LOW, LODLevel.LOW):
            self._paint_lod(painter, lod_level)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self._get_node_rect()
        border_width = _BORDER_WIDTH
        radius = 8.0

        # Draw stack layers BEFORE main node body
        self._draw_stack_layers(painter, rect, radius)

        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Fill background with subflow blue-gray
        bg_color = QColor(self._node_bg_color)
        if self._is_disabled:
            bg_color.setAlpha(64)  # 25% opacity for disabled (more grayed out)
        painter.fillPath(path, QBrush(bg_color))

        # Solid border for subflow nodes
        pen = QPen(_SUBFLOW_HEADER_COLOR.lighter(120), border_width)

        # Selection state modifies border color
        if self.isSelected() or self._is_running:
            pen.setColor(self._selected_border_color)

        painter.strokePath(path, pen)

        # Draw header with subflow icon
        self._draw_subflow_header(painter, rect)

        # Draw node count badge
        if self._node_count > 0:
            self._draw_node_count_badge(painter, rect)

        # Draw expand button
        self._draw_expand_button(painter, rect)

        # Draw configure button (for parameter promotion)
        self._draw_config_button(painter, rect)

        # Draw execution time badge if available
        self._draw_execution_time(painter, rect)

        # Draw disabled overlay (diagonal gray lines) - same as CasareNodeItem
        if self._is_disabled:
            self._draw_disabled_overlay(painter, rect)

        # Draw status indicators
        if self._has_error:
            self._draw_error_icon(painter, rect)
        elif self._has_warning:
            self._draw_warning_icon(painter, rect)
        elif self._is_skipped:
            self._draw_skipped_icon(painter, rect)
        elif self._is_completed:
            self._draw_checkmark(painter, rect)

        painter.restore()

    def _draw_subflow_header(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw header with subflow icon and name.

        Args:
            painter: QPainter to draw with
            rect: Node bounding rect
        """
        header_height = 26
        radius = 8.0

        # Header rect
        header_rect = QRectF(rect.left(), rect.top(), rect.width(), header_height)

        # Create header path with rounded top corners only
        header_path = QPainterPath()
        header_path.moveTo(header_rect.left() + radius, header_rect.top())
        header_path.lineTo(header_rect.right() - radius, header_rect.top())
        header_path.arcTo(
            header_rect.right() - radius * 2,
            header_rect.top(),
            radius * 2,
            radius * 2,
            90,
            -90,
        )
        header_path.lineTo(header_rect.right(), header_rect.bottom())
        header_path.lineTo(header_rect.left(), header_rect.bottom())
        header_path.lineTo(header_rect.left(), header_rect.top() + radius)
        header_path.arcTo(
            header_rect.left(), header_rect.top(), radius * 2, radius * 2, 180, -90
        )
        header_path.closeSubpath()

        # Header gradient (blue-gray at 60% opacity)
        gradient = QLinearGradient(
            header_rect.left(),
            header_rect.top(),
            header_rect.left(),
            header_rect.bottom(),
        )
        header_color = QColor(_SUBFLOW_HEADER_COLOR)
        header_color.setAlpha(_SUBFLOW_HEADER_ALPHA)
        gradient.setColorAt(0.0, header_color)

        # Darker at bottom
        darker_color = QColor(_SUBFLOW_HEADER_COLOR)
        darker_color.setRed(max(0, int(darker_color.red() * 0.8)))
        darker_color.setGreen(max(0, int(darker_color.green() * 0.8)))
        darker_color.setBlue(max(0, int(darker_color.blue() * 0.8)))
        darker_color.setAlpha(_SUBFLOW_HEADER_ALPHA)
        gradient.setColorAt(1.0, darker_color)

        painter.fillPath(header_path, QBrush(gradient))

        # Separator line
        sep_color = QColor(_SUBFLOW_HEADER_COLOR)
        sep_color.setAlpha(180)
        painter.setPen(QPen(sep_color, 1))
        painter.drawLine(
            QPointF(header_rect.left(), header_rect.bottom()),
            QPointF(header_rect.right(), header_rect.bottom()),
        )

        # Draw node name
        from casare_rpa.presentation.canvas.graph.custom_node_item import (
            _get_title_font,
            _HEADER_TEXT_COLOR,
        )

        painter.setPen(_HEADER_TEXT_COLOR)
        painter.setFont(_get_title_font())

        node_name = self.name if hasattr(self, "name") else "Subflow"
        # Room for badge, config btn, expand btn on right
        text_rect = QRectF(
            header_rect.left() + 10,
            header_rect.top(),
            header_rect.width() - 80,
            header_height,
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, node_name)

    def _draw_node_count_badge(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw badge showing the number of nodes in this subflow.

        Args:
            painter: QPainter to draw with
            rect: Node bounding rect
        """
        badge_text = str(self._node_count)
        font = self.get_badge_font()
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(badge_text)
        text_height = fm.height()

        # Badge dimensions
        padding_h = 5
        padding_v = 2
        badge_width = max(text_width + padding_h * 2, 22)  # Minimum width
        badge_height = text_height + padding_v * 2
        badge_radius = badge_height / 2

        # Position in header (right of name, before config and expand buttons)
        # Config button is at -42, expand button is at -22
        badge_x = rect.right() - badge_width - 48  # Leave room for both buttons
        badge_y = rect.top() + (26 - badge_height) / 2  # Centered in header

        badge_rect = QRectF(badge_x, badge_y, badge_width, badge_height)

        # Draw badge background
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, badge_radius, badge_radius)
        painter.fillPath(badge_path, QBrush(_BADGE_BG_COLOR))

        # Draw count text
        painter.setPen(_BADGE_TEXT_COLOR)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

    def _draw_expand_button(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw expand button to open subflow editor.

        Args:
            painter: QPainter to draw with
            rect: Node bounding rect
        """
        btn_size = 16
        margin = 6
        x = rect.right() - btn_size - margin
        y = rect.top() + 5  # Centered in header

        self._expand_button_rect = QRectF(x, y, btn_size, btn_size)

        # Button background
        btn_path = QPainterPath()
        btn_path.addRoundedRect(self._expand_button_rect, 3, 3)

        if self._expand_btn_hovered:
            painter.fillPath(btn_path, QBrush(_EXPAND_BTN_HOVER))
        else:
            painter.fillPath(btn_path, QBrush(_EXPAND_BTN_BG))

        # Draw play symbol (expand/open subflow)
        painter.setPen(
            QPen(
                _EXPAND_BTN_SYMBOL, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
        )

        center_x = x + btn_size / 2
        center_y = y + btn_size / 2

        # Triangle pointing right (play/expand)
        triangle_path = QPainterPath()
        triangle_path.moveTo(center_x - 3, center_y - 4)
        triangle_path.lineTo(center_x + 4, center_y)
        triangle_path.lineTo(center_x - 3, center_y + 4)
        triangle_path.closeSubpath()

        painter.fillPath(triangle_path, QBrush(_EXPAND_BTN_SYMBOL))

    def _draw_config_button(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw configure button for parameter promotion.

        Args:
            painter: QPainter to draw with
            rect: Node bounding rect
        """
        btn_size = 16
        margin = 6
        # Position to the left of expand button
        x = rect.right() - btn_size * 2 - margin - 4
        y = rect.top() + 5  # Centered in header

        self._config_button_rect = QRectF(x, y, btn_size, btn_size)

        # Button background
        btn_path = QPainterPath()
        btn_path.addRoundedRect(self._config_button_rect, 3, 3)

        if self._config_btn_hovered:
            painter.fillPath(btn_path, QBrush(_CONFIG_BTN_HOVER))
        else:
            painter.fillPath(btn_path, QBrush(_CONFIG_BTN_BG))

        # Draw gear/settings symbol
        painter.setPen(
            QPen(
                _EXPAND_BTN_SYMBOL, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
        )

        center_x = x + btn_size / 2
        center_y = y + btn_size / 2

        # Draw simplified gear: a small circle with lines
        gear_radius = 4
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QPointF(center_x, center_y), gear_radius - 1, gear_radius - 1
        )

        # Draw 4 spokes
        for angle in [0, 90, 180, 270]:
            from math import radians, cos, sin

            rad = radians(angle)
            inner = 2
            outer = 5
            x1 = center_x + inner * cos(rad)
            y1 = center_y + inner * sin(rad)
            x2 = center_x + outer * cos(rad)
            y2 = center_y + outer * sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events, including expand and config button clicks."""
        from PySide6.QtCore import Qt

        click_pos = event.pos()

        # Check if click is on config button (parameter promotion)
        if self._config_button_rect and event.button() == Qt.MouseButton.LeftButton:
            hit_rect = self._config_button_rect.adjusted(-4, -4, 4, 4)
            if hit_rect.contains(click_pos):
                node = getattr(self, "_node", None)
                if node and hasattr(node, "promote_parameters"):
                    node.promote_parameters()
                    event.accept()
                    return

        # Check if click is on expand button
        if self._expand_button_rect and event.button() == Qt.MouseButton.LeftButton:
            hit_rect = self._expand_button_rect.adjusted(-4, -4, 4, 4)
            if hit_rect.contains(click_pos):
                # Get the VisualNode instance via NodeGraphQt's internal _node attribute
                node = getattr(self, "_node", None)
                if node and hasattr(node, "expand_subflow"):
                    node.expand_subflow()
                    event.accept()
                    return

        # Call parent for normal behavior (collapse button, selection, etc.)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to expand subflow."""
        from PySide6.QtCore import Qt

        if event.button() == Qt.MouseButton.LeftButton:
            node = getattr(self, "_node", None)
            if node and hasattr(node, "expand_subflow"):
                node.expand_subflow()
                event.accept()
                return

        super().mouseDoubleClickEvent(event)

    def hoverMoveEvent(self, event) -> None:
        """Track hover over expand and config buttons."""
        needs_update = False
        pos = event.pos()

        # Track expand button hover
        if self._expand_button_rect:
            hit_rect = self._expand_button_rect.adjusted(-4, -4, 4, 4)
            was_hovered = self._expand_btn_hovered
            self._expand_btn_hovered = hit_rect.contains(pos)
            if was_hovered != self._expand_btn_hovered:
                needs_update = True

        # Track config button hover
        if self._config_button_rect:
            hit_rect = self._config_button_rect.adjusted(-4, -4, 4, 4)
            was_hovered = self._config_btn_hovered
            self._config_btn_hovered = hit_rect.contains(pos)
            if was_hovered != self._config_btn_hovered:
                needs_update = True

        if needs_update:
            self.update()

        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Clear hover state on leave."""
        needs_update = False

        if self._expand_btn_hovered:
            self._expand_btn_hovered = False
            needs_update = True

        if self._config_btn_hovered:
            self._config_btn_hovered = False
            needs_update = True

        if needs_update:
            self.update()

        super().hoverLeaveEvent(event)
