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

All colors are sourced from the unified theme system (theme.py).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QGraphicsItem

from casare_rpa.presentation.canvas.graph.custom_node_item import (
    CasareNodeItem,
    LODLevel,
    _high_performance_mode,
    get_lod_manager,
)
from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME

# Icon cache for subflow buttons
_subflow_icon_cache = {"expand": None, "config": None}


def _get_subflow_icon(name: str) -> QPixmap:
    """Get cached subflow icon pixmap."""
    global _subflow_icon_cache

    if _subflow_icon_cache[name] is None:
        from casare_rpa.presentation.canvas.theme.icons_v2 import get_pixmap

        icon_map = {
            "expand": "play",  # Play icon for expand
            "config": "settings",  # Settings icon for config
        }
        _subflow_icon_cache[name] = get_pixmap(icon_map[name], size=14)

    return _subflow_icon_cache[name]


# ============================================================================
# SUBFLOW NODE VISUAL CONSTANTS - Delegated to unified theme
# ============================================================================
# Colors are lazily initialized from theme to ensure consistency and
# avoid import-time QApplication dependency issues.

# Border width (geometry, not a color)
_BORDER_WIDTH = 2.0

# Stack visual effect (layers behind main node)
_STACK_LAYER_COUNT = 2
_STACK_OFFSET = 4  # pixels per layer

# Color caches - initialized lazily
_SUBFLOW_HEADER_COLOR: QColor | None = None
_SUBFLOW_HEADER_ALPHA = 153  # 60% opacity
_BADGE_BG_COLOR: QColor | None = None
_BADGE_TEXT_COLOR: QColor | None = None
_STACK_COLORS: list | None = None


def _get_subflow_header_color() -> QColor:
    """Get subflow header color from theme."""
    return QColor(THEME.category_utility)


def _get_badge_bg_color() -> QColor:
    """Get badge background color from theme."""
    return QColor(THEME.primary)


def _get_badge_text_color() -> QColor:
    """Get badge text color from theme."""
    return QColor(THEME.text_on_primary)


def _get_stack_colors() -> list:
    """Get stack layer colors from theme."""
    # Derive stack colors from node background, making them darker
    base_color = QColor(THEME.bg_node)
    # Furthest back (darkest)
    dark = QColor(base_color)
    dark.setRed(max(0, dark.red() - 20))
    dark.setGreen(max(0, dark.green() - 20))
    dark.setBlue(max(0, dark.blue() - 20))
    # Middle layer
    mid = QColor(base_color)
    mid.setRed(max(0, mid.red() - 10))
    mid.setGreen(max(0, mid.green() - 10))
    mid.setBlue(max(0, mid.blue() - 10))
    return [dark, mid]


def _init_subflow_colors():
    """Initialize all subflow color variables from theme."""
    global _SUBFLOW_HEADER_COLOR, _BADGE_BG_COLOR, _BADGE_TEXT_COLOR, _STACK_COLORS

    if _SUBFLOW_HEADER_COLOR is None:
        _SUBFLOW_HEADER_COLOR = _get_subflow_header_color()
        _BADGE_BG_COLOR = _get_badge_bg_color()
        _BADGE_TEXT_COLOR = _get_badge_text_color()
        _STACK_COLORS = _get_stack_colors()


class SubflowNodeItem(CasareNodeItem):
    """
    Custom graphics item for subflow nodes.

    Extends CasareNodeItem with:
    - Stack visual effect to indicate nested nodes
    - Node count badge
    - Expand button
    """

    # Font for badge text (cached at class level)
    _badge_font: QFont | None = None

    @classmethod
    def get_badge_font(cls) -> QFont:
        """Get cached font for node count badge."""
        if cls._badge_font is None:
            cls._badge_font = QFont("Segoe UI", 8)
            cls._badge_font.setWeight(QFont.Weight.Medium)
        return cls._badge_font

    def __init__(self, name: str = "subflow", parent: QGraphicsItem | None = None):
        """
        Initialize subflow node item.

        Args:
            name: Node display name
            parent: Parent graphics item
        """
        super().__init__(name, parent)

        # Initialize colors from unified theme (lazy initialization)
        _init_subflow_colors()

        # Subflow-specific state
        self._node_count: int = 0
        self._expand_button_rect: QRectF | None = None
        self._config_button_rect: QRectF | None = None

        # Override cached header color to blue-gray (from theme)
        self._cached_header_color = QColor(_SUBFLOW_HEADER_COLOR)
        self._cached_header_color.setAlpha(_SUBFLOW_HEADER_ALPHA)

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

    def _draw_stack_layers(self, painter: QPainter, rect: QRectF, radius: float = 8.0) -> None:
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
        fill_color = QColor(THEME.category_basic).lighter(110)  # Slightly lighter than header

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
        header_path.arcTo(header_rect.left(), header_rect.top(), radius * 2, radius * 2, 180, -90)
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
        )

        # Use bright white for maximum contrast on colored headers
        painter.setPen(QColor(255, 255, 255))
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
        icon_size = 14
        margin = 6
        x = rect.right() - icon_size - margin
        y = rect.top() + 4  # Centered in header

        self._expand_button_rect = QRectF(x, y, icon_size, icon_size)

        # Draw the expand/play icon
        icon_pixmap = _get_subflow_icon("expand")
        painter.drawPixmap(int(x), int(y), icon_pixmap)

    def _draw_config_button(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw configure button for parameter promotion.

        Args:
            painter: QPainter to draw with
            rect: Node bounding rect
        """
        icon_size = 14
        margin = 6
        # Position to the left of expand button
        x = rect.right() - icon_size * 2 - margin - 4
        y = rect.top() + 4  # Centered in header

        self._config_button_rect = QRectF(x, y, icon_size, icon_size)

        # Draw the config/settings icon
        icon_pixmap = _get_subflow_icon("config")
        painter.drawPixmap(int(x), int(y), icon_pixmap)

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
