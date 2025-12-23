"""
Custom node graphics item for CasareRPA.

Provides custom styling including:
- Bright yellow border on selection
- Animated running state indicator
- Completion checkmark
- Icon display

Now uses centralized AnimationCoordinator for performance with many nodes.
All colors are sourced from the unified theme system (theme.py).

References:
- "Designing Data-Intensive Applications" - Resource pooling
"""

import math
from typing import Callable, Dict, Set, Optional
from PySide6.QtCore import Qt, QRectF, QTimer, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QPixmap, QFont
from NodeGraphQt.qgraphics.node_base import NodeItem, PortTypeEnum, ITEM_CACHE_MODE
from PySide6.QtWidgets import QGraphicsItem, QGraphicsOpacityEffect, QGraphicsTextItem

# Import GPU optimization managers (lazy import to avoid circular deps)
# These are imported at module level for performance - no function call overhead
from casare_rpa.presentation.canvas.graph.lod_manager import get_lod_manager, LODLevel
from casare_rpa.presentation.canvas.graph.icon_atlas import get_icon_atlas

# Import unified theme system for all colors
from casare_rpa.presentation.canvas.ui.theme import (
    Theme,
    NODE_DISABLED_OPACITY,
    NODE_DISABLED_BG_ALPHA,
    NODE_DISABLED_WASH_ALPHA,
    NODE_DISABLED_BORDER_WIDTH,
)

# ============================================================================
# PERFORMANCE: Module-level enum caching
# Avoids per-paint attribute lookup overhead for frequently used enums
# ============================================================================
_ANTIALIASING = QPainter.RenderHint.Antialiasing
_PEN_STYLE_NONE = Qt.PenStyle.NoPen
_PEN_STYLE_SOLID = Qt.PenStyle.SolidLine
_PEN_STYLE_DASH = Qt.PenStyle.DashLine
_PEN_STYLE_DOT = Qt.PenStyle.DotLine  # For disabled state
_BRUSH_STYLE_NONE = Qt.BrushStyle.NoBrush
_ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
_PEN_CAP_ROUND = Qt.PenCapStyle.RoundCap
_PEN_JOIN_ROUND = Qt.PenJoinStyle.RoundJoin

# Port label truncation constants
PORT_LABEL_MAX_LENGTH = 12
PORT_LABEL_MAX_WIDTH_PX = 80
_WHITE = Qt.GlobalColor.white


# ============================================================================
# PERFORMANCE: Pre-cached paint objects to avoid allocation in paint()
# Colors are now sourced from Theme.get_status_qcolor() with caching.
# These module-level references are for backward compatibility only.
# ============================================================================


# Status indicator colors - now delegating to theme (cached internally)
def _get_success_green() -> QColor:
    return Theme.get_status_qcolor("success")


def _get_error_red() -> QColor:
    return Theme.get_status_qcolor("error")


def _get_warning_orange() -> QColor:
    return Theme.get_status_qcolor("warning")


def _get_disabled_gray() -> QColor:
    return Theme.get_status_qcolor("disabled")


def _get_skipped_gray() -> QColor:
    return Theme.get_status_qcolor("skipped")


# Legacy aliases for backward compatibility (lazy evaluation)
_SUCCESS_GREEN = None  # Will be initialized on first use
_ERROR_RED = None
_WARNING_ORANGE = None
_DISABLED_GRAY = None
_SKIPPED_GRAY = None


def _init_legacy_colors():
    """Initialize legacy color variables on first access."""
    global _SUCCESS_GREEN, _ERROR_RED, _WARNING_ORANGE, _DISABLED_GRAY, _SKIPPED_GRAY
    if _SUCCESS_GREEN is None:
        _SUCCESS_GREEN = _get_success_green()
        _ERROR_RED = _get_error_red()
        _WARNING_ORANGE = _get_warning_orange()
        _DISABLED_GRAY = _get_disabled_gray()
        _SKIPPED_GRAY = _get_skipped_gray()


# Text colors from theme
def _get_secondary_text_color() -> QColor:
    cc = Theme.get_canvas_colors()
    from casare_rpa.presentation.canvas.ui.theme import _hex_to_qcolor

    return _hex_to_qcolor(cc.node_text_secondary)


def _get_port_label_color() -> QColor:
    cc = Theme.get_canvas_colors()
    from casare_rpa.presentation.canvas.ui.theme import _hex_to_qcolor

    return _hex_to_qcolor(cc.node_text_port)


# Legacy text color aliases
_SECONDARY_TEXT_COLOR = None
_PORT_LABEL_COLOR = None


def _init_legacy_text_colors():
    """Initialize legacy text color variables."""
    global _SECONDARY_TEXT_COLOR, _PORT_LABEL_COLOR
    if _SECONDARY_TEXT_COLOR is None:
        _SECONDARY_TEXT_COLOR = _get_secondary_text_color()
        _PORT_LABEL_COLOR = _get_port_label_color()


# Initialize colors at module load time to avoid None during paint()
_init_legacy_colors()
_init_legacy_text_colors()


# ============================================================================
# PERFORMANCE: Module-level cached theme colors for CasareNodeItem
# Avoids Theme method calls on every node instantiation
# ============================================================================
_CACHED_NORMAL_BORDER: Optional[QColor] = None
_CACHED_SELECTED_BORDER: Optional[QColor] = None
_CACHED_RUNNING_BORDER: Optional[QColor] = None
_CACHED_NODE_BG: Optional[QColor] = None
_CACHED_ROBOT_OVERRIDE: Optional[QColor] = None
_CACHED_CAPABILITY_OVERRIDE: Optional[QColor] = None


def _init_node_item_theme_colors() -> None:
    """
    Initialize cached theme colors for CasareNodeItem.

    PERFORMANCE: These colors are used by every node instance.
    Caching at module level avoids Theme method calls during node construction.
    """
    global _CACHED_NORMAL_BORDER, _CACHED_SELECTED_BORDER, _CACHED_RUNNING_BORDER
    global _CACHED_NODE_BG, _CACHED_ROBOT_OVERRIDE, _CACHED_CAPABILITY_OVERRIDE
    if _CACHED_NORMAL_BORDER is None:
        _CACHED_NORMAL_BORDER = Theme.get_node_border_qcolor("normal")
        _CACHED_SELECTED_BORDER = Theme.get_node_border_qcolor("selected")
        _CACHED_RUNNING_BORDER = Theme.get_node_border_qcolor("running")
        _CACHED_NODE_BG = Theme.get_node_bg_qcolor()
        # Robot/capability override colors
        cc = Theme.get_canvas_colors()
        from casare_rpa.presentation.canvas.ui.theme import _hex_to_qcolor

        _CACHED_ROBOT_OVERRIDE = _hex_to_qcolor(cc.category_database)  # Teal
        _CACHED_CAPABILITY_OVERRIDE = _hex_to_qcolor(cc.category_triggers)  # Purple


# ============================================================================
# HIGH PERFORMANCE MODE
# ============================================================================
# When enabled, forces LOD rendering at all zoom levels and disables expensive
# visual effects. Auto-enabled when node count >= 50.

_high_performance_mode: bool = False
_HIGH_PERF_NODE_THRESHOLD: int = 50


def set_high_performance_mode(enabled: bool) -> None:
    """
    Enable or disable high performance mode globally.

    When enabled:
    - Forces simplified LOD rendering at all zoom levels
    - Disables antialiasing
    - Skips icons, badges, and text rendering

    Args:
        enabled: True to enable high performance mode
    """
    global _high_performance_mode
    _high_performance_mode = enabled


def get_high_performance_mode() -> bool:
    """
    Check if high performance mode is enabled.

    Returns:
        True if high performance mode is active
    """
    return _high_performance_mode


def get_high_perf_node_threshold() -> int:
    """
    Get the node count threshold for auto-enabling high performance mode.

    Returns:
        Node count threshold (default: 50)
    """
    return _HIGH_PERF_NODE_THRESHOLD


# ============================================================================
# BADGE AND HEADER COLORS - Now from unified theme
# ============================================================================


def _get_badge_bg_color() -> QColor:
    """Get badge background color from theme."""
    bg, _, _ = Theme.get_badge_colors()
    # Add alpha for semi-transparency
    color = QColor(bg)
    color.setAlpha(100)
    return color


def _get_badge_text_color() -> QColor:
    """Get badge text color from theme."""
    _, text, _ = Theme.get_badge_colors()
    color = QColor(text)
    color.setAlpha(200)
    return color


# Legacy badge color references
_BADGE_BG_COLOR = None
_BADGE_TEXT_COLOR = None


def _init_badge_colors():
    """Initialize badge color variables."""
    global _BADGE_BG_COLOR, _BADGE_TEXT_COLOR
    if _BADGE_BG_COLOR is None:
        _BADGE_BG_COLOR = _get_badge_bg_color()
        _BADGE_TEXT_COLOR = _get_badge_text_color()


# Header text color - always white for maximum contrast on colored headers
# No longer uses cached global; QColor(255, 255, 255) is used directly in _draw_text()


# ============================================================================
# CATEGORY HEADER COLORS - Now from unified theme
# ============================================================================
# Category colors are now centralized in theme.py (CATEGORY_COLOR_MAP).
# This function delegates to Theme.get_category_qcolor() for consistency
# across nodes, icons, and wires.


def get_category_header_color(category: str) -> QColor:
    """
    Get the header color for a node category.

    For hierarchical categories (e.g., "google/gmail/send"), uses the root category color.
    Colors are sourced from the unified theme system.

    Args:
        category: Category string (may be hierarchical with '/')

    Returns:
        QColor for the category header (cached for performance)
    """
    return Theme.get_category_qcolor(category)


# ============================================================================
# COLLAPSE BUTTON COLORS - Now from unified theme
# ============================================================================


def _get_collapse_btn_bg() -> QColor:
    """Get collapse button background from theme."""
    cc = Theme.get_canvas_colors()
    from casare_rpa.presentation.canvas.ui.theme import _hex_to_qcolor

    color = _hex_to_qcolor(cc.collapse_btn_bg)
    result = QColor(color)
    result.setAlpha(180)
    return result


def _get_collapse_btn_symbol() -> QColor:
    """Get collapse button symbol color from theme."""
    cc = Theme.get_canvas_colors()
    from casare_rpa.presentation.canvas.ui.theme import _hex_to_qcolor

    return _hex_to_qcolor(cc.collapse_btn_symbol)


# Legacy collapse button colors
_COLLAPSE_BTN_BG = None
_COLLAPSE_BTN_SYMBOL = None


def _init_collapse_btn_colors():
    """Initialize collapse button colors."""
    global _COLLAPSE_BTN_BG, _COLLAPSE_BTN_SYMBOL
    if _COLLAPSE_BTN_BG is None:
        _COLLAPSE_BTN_BG = _get_collapse_btn_bg()
        _COLLAPSE_BTN_SYMBOL = _get_collapse_btn_symbol()


# Pre-cached fonts
_TITLE_FONT: Optional[QFont] = None


def _get_title_font() -> QFont:
    """Get cached title font for node name display."""
    global _TITLE_FONT
    if _TITLE_FONT is None:
        _TITLE_FONT = QFont("Segoe UI", 9)
        _TITLE_FONT.setWeight(QFont.Weight.Medium)
    return _TITLE_FONT


# ============================================================================
# ANIMATION COORDINATOR (Centralized Timer)
# ============================================================================


class AnimationCoordinator:
    """
    Singleton coordinator for all node animations.

    Instead of each node having its own timer, this coordinator uses a
    single timer to drive all animated nodes. This significantly reduces
    CPU usage when many nodes are running simultaneously.

    Supports multiple animation types:
    - "running": Animated border for executing nodes
    - "selection": Pulsing glow for selected nodes

    Usage:
        coordinator = AnimationCoordinator.get_instance()
        coordinator.register(node_item, "running")  # Start running animation
        coordinator.register(node_item, "selection")  # Start selection glow
        coordinator.unregister(node_item, "running")  # Stop specific animation
        coordinator.unregister_all(node_item)  # Stop all animations
    """

    _instance: Optional["AnimationCoordinator"] = None

    @classmethod
    def get_instance(cls) -> "AnimationCoordinator":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the animation coordinator."""
        # Separate sets for different animation types
        self._running_nodes: Set["CasareNodeItem"] = set()
        self._selected_nodes: Set["CasareNodeItem"] = set()
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._offset = 0
        self._selection_phase = 0.0  # 0.0 to 1.0 for pulsing
        self._interval = 16  # 60 FPS for smooth animations

    def register(self, node: "CasareNodeItem", animation_type: str = "running") -> None:
        """
        Start animating a node.

        Args:
            node: The CasareNodeItem to animate
            animation_type: Type of animation ("running" or "selection")
        """
        if animation_type == "running":
            self._running_nodes.add(node)
        elif animation_type == "selection":
            self._selected_nodes.add(node)

        if not self._timer.isActive():
            self._timer.start(self._interval)

    def unregister(self, node: "CasareNodeItem", animation_type: str = "running") -> None:
        """
        Stop a specific animation for a node.

        Args:
            node: The CasareNodeItem to stop animating
            animation_type: Type of animation to stop
        """
        if animation_type == "running":
            self._running_nodes.discard(node)
        elif animation_type == "selection":
            self._selected_nodes.discard(node)

        self._check_stop_timer()

    def unregister_all(self, node: "CasareNodeItem") -> None:
        """
        Stop all animations for a node.

        Args:
            node: The CasareNodeItem to stop animating
        """
        self._running_nodes.discard(node)
        self._selected_nodes.discard(node)
        self._check_stop_timer()

    def _check_stop_timer(self) -> None:
        """Stop timer if no nodes are being animated."""
        if not self._running_nodes and not self._selected_nodes and self._timer.isActive():
            self._timer.stop()
            self._offset = 0
            self._selection_phase = 0.0

    def _tick(self) -> None:
        """Update all animated nodes."""
        # Update running animation offset (dash pattern)
        self._offset = (self._offset + 1) % 8

        # Update selection pulse phase (sine wave, ~1.5 second cycle)
        self._selection_phase = (self._selection_phase + 0.04) % 1.0

        # Update running nodes
        for node in self._running_nodes:
            node._animation_offset = self._offset
            node.update()

        # Update selected nodes with pulse
        for node in self._selected_nodes:
            node._selection_glow_phase = self._selection_phase
            node.update()

    @property
    def animated_count(self) -> int:
        """Get the total number of currently animated nodes."""
        return len(self._running_nodes) + len(self._selected_nodes)

    @property
    def running_count(self) -> int:
        """Get the number of nodes with running animation."""
        return len(self._running_nodes)

    @property
    def selected_count(self) -> int:
        """Get the number of nodes with selection animation."""
        return len(self._selected_nodes)

    @property
    def is_running(self) -> bool:
        """Check if the animation timer is running."""
        return self._timer.isActive()

    @classmethod
    def cleanup(cls) -> None:
        """
        Clean up the singleton instance and release all resources.

        Call this when shutting down the application or clearing all nodes
        to prevent memory leaks from accumulated node references.
        """
        if cls._instance is not None:
            if cls._instance._timer.isActive():
                cls._instance._timer.stop()
            cls._instance._running_nodes.clear()
            cls._instance._selected_nodes.clear()
            cls._instance = None


class CasareNodeItem(NodeItem):
    """
    Custom node item with enhanced visual feedback.

    Features:
    - Yellow border on selection
    - Animated dotted border when running
    - Checkmark overlay when completed
    - Error icon when failed
    - Execution time badge
    - Icon display
    """

    # Class-level font cache for execution time (single instance for all nodes)
    _time_font: Optional[QFont] = None

    @classmethod
    def get_time_font(cls) -> QFont:
        """Get cached font for execution time display."""
        if cls._time_font is None:
            cls._time_font = QFont("Segoe UI", 8)
        return cls._time_font

    # Height reserved above node for execution time badge
    BADGE_AREA_HEIGHT = 24

    def __init__(self, name="node", parent=None):
        super().__init__(name, parent)
        # Ensure geometry change callbacks fire for culling updates.
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Execution state
        self._is_running = False
        self._is_completed = False
        self._has_error = False
        self._execution_time_ms: Optional[float] = None
        self._animation_offset = 0

        # New status states for Phase 1 UI overhaul
        self._is_disabled = False  # Gray diagonal lines overlay, 50% opacity
        self._is_skipped = False  # Gray fast-forward icon in corner
        self._has_warning = False  # Yellow triangle, orange border
        self._cache_enabled = False  # Cache icon overlay

        # MMB click detection (for output inspector popup)
        self._mmb_press_pos = None
        self._mmb_press_scene_pos = None

        # Robot override state
        self._has_robot_override = False
        self._override_is_capability_based = False

        # Use centralized animation coordinator instead of per-node timer
        # This significantly improves performance when many nodes are running
        self._animation_coordinator = AnimationCoordinator.get_instance()

        # Selection glow animation state (updated by AnimationCoordinator)
        self._selection_glow_phase: float = 0.0
        self._selection_glow_enabled: bool = False

        # Custom icon pixmap (separate from parent's _icon_item)
        self._custom_icon_pixmap = None

        # Node type identifier for icon atlas lookups
        self._node_type_name: str = ""

        # PERFORMANCE: Use module-level cached theme colors
        # Ensures colors are initialized on first node creation
        if _CACHED_NORMAL_BORDER is None:
            _init_node_item_theme_colors()
        self._normal_border_color = _CACHED_NORMAL_BORDER
        self._selected_border_color = _CACHED_SELECTED_BORDER
        self._running_border_color = _CACHED_RUNNING_BORDER
        self._node_bg_color = _CACHED_NODE_BG
        self._robot_override_color = _CACHED_ROBOT_OVERRIDE
        self._capability_override_color = _CACHED_CAPABILITY_OVERRIDE

        # Category for header coloring (set via set_category method)
        self._category: str = ""
        self._cached_header_color: Optional[QColor] = None

        # Cached opacity effects for disabled state (prevents leak from creating new effects)
        self._opacity_effects: Dict[str, QGraphicsOpacityEffect] = {}

        # Collapse state
        self._is_collapsed = False
        self._collapse_button_rect: Optional[QRectF] = None

        # PERFORMANCE: Callback for position updates (used by viewport culling)
        self._on_position_changed: Optional[callable] = None

        # Hide parent's text item to avoid double title
        if hasattr(self, "_text_item") and self._text_item:
            self._text_item.setVisible(False)

        # Hide parent's icon item - we don't show icons
        if hasattr(self, "_icon_item") and self._icon_item:
            self._icon_item.setVisible(False)

    def boundingRect(self) -> QRectF:
        """
        Override bounding rect to include space above for execution time badge.

        Only extends when execution time is shown (not for status icons).
        Status icons are drawn in a fixed position that doesn't require rect extension.
        """
        rect = super().boundingRect()
        # Only extend for execution time badge (status icons fit within normal bounds)
        if self._execution_time_ms is not None:
            return QRectF(
                rect.x(),
                rect.y() - self.BADGE_AREA_HEIGHT,
                rect.width(),
                rect.height() + self.BADGE_AREA_HEIGHT,
            )
        return rect

    def _get_node_rect(self) -> QRectF:
        """Get the actual node rectangle (without badge area)."""
        return super().boundingRect()

    def calc_size(self, add_w=0.0, add_h=0.0):
        """
        Override to ensure minimum width for port labels AND embedded widgets.

        FIX: NodeGraphQt's default calc_size may not account for port labels
        or embedded widgets properly, causing:
        1. Input and output labels to overlap in the middle of the node
        2. Widgets (like selector widgets with labels) to extend beyond node bounds

        This fix ensures the node is wide enough to contain:
        - Port labels on both sides with proper padding
        - All embedded widgets (including their labels) with margins
        """
        width, height = super().calc_size(add_w, add_h)

        # Calculate actual required width for port labels
        port_label_padding = 20  # Padding between input and output labels

        # Get max input port label width
        max_input_width = 0.0
        for port, text in self._input_items.items():
            if port.isVisible() and text.isVisible():
                max_input_width = max(max_input_width, text.boundingRect().width())

        # Get max output port label width
        max_output_width = 0.0
        for port, text in self._output_items.items():
            if port.isVisible() and text.isVisible():
                max_output_width = max(max_output_width, text.boundingRect().width())

        # Ensure node is wide enough for both labels plus padding
        # Port circles are about 10px each (on left and right edges)
        min_required_width = max_input_width + max_output_width + port_label_padding + 20

        if width < min_required_width:
            width = min_required_width

        # FIX: Also account for embedded widget widths
        # Widgets are stored in self._widgets dict and include their labels
        # in their boundingRect(). We need the node to be wide enough for them.
        #
        # CRITICAL FIX: boundingRect() may return incorrect values before the widget
        # is fully laid out. We need to:
        # 1. Force the widget to calculate its size first
        # 2. Use the underlying QWidget's sizeHint for accurate measurement
        # 3. Add sufficient margin for label + content
        widget_margin = 40  # 20px left + 20px right margin for widgets inside node
        max_widget_width = 0.0
        if hasattr(self, "_widgets") and self._widgets:
            for widget in self._widgets.values():
                if widget and widget.isVisible():
                    # Get the underlying QWidget (the _NodeGroupBox)
                    qwidget = widget.widget()
                    if qwidget:
                        # Force layout calculation to get accurate size
                        qwidget.adjustSize()
                        # Use sizeHint which includes label + content
                        size_hint = qwidget.sizeHint()
                        widget_width = max(size_hint.width(), 200)  # Min 200px for file widgets
                    else:
                        # Fallback to boundingRect if no QWidget
                        widget_width = widget.boundingRect().width()

                    if widget_width > max_widget_width:
                        max_widget_width = widget_width

        # Ensure node is at least as wide as the widest widget plus margins
        min_widget_required = max_widget_width + widget_margin
        if width < min_widget_required:
            width = min_widget_required

        return width, height

    def draw_node(self):
        """
        Override to ensure prepareGeometryChange() is called before layout changes.

        CRITICAL FIX: Qt's scene caching requires prepareGeometryChange() to be
        called BEFORE any changes to the bounding rect. Without this, the scene
        keeps stale cached data which causes rendering artifacts when:
        - Node widgets are hidden/shown (expand/collapse)
        - Node size changes due to port/widget visibility
        - Panning/scrolling the canvas

        This fix ensures proper scene invalidation before the parent class
        recalculates and repositions all child items.
        """
        self.prepareGeometryChange()
        super().draw_node()
        # Notify culling after geometry changes (size/shape updates).
        if self._on_position_changed:
            try:
                self._on_position_changed(self)
            except Exception:
                pass

    def _align_widgets_horizontal(self, v_offset):
        """
        Override to use actual node rect and custom header height.

        FIX: Parent class calculates v_offset from _text_item which we hide.
        Instead, use our custom header height (26px) for consistent widget positioning.
        Also use _get_node_rect() to avoid badge area offset issues.

        Additional FIX: Clamp widget positions to ensure they stay within node bounds.
        This prevents widgets from floating outside the node when their labels are long.
        """
        if not self._widgets:
            return
        # Use actual node rect, not extended boundingRect
        rect = self._get_node_rect()
        # Use our custom header height (26px) instead of parent's v_offset
        # which may be wrong since we hide _text_item
        custom_header_height = 26
        y = rect.y() + custom_header_height
        inputs = [p for p in self.inputs if p.isVisible()]
        outputs = [p for p in self.outputs if p.isVisible()]

        # Calculate safe bounds for widget positioning
        # Leave 10px margin on each side for aesthetics
        margin = 10
        min_x = rect.left() + margin
        max_x = rect.right() - margin

        for widget in self._widgets.values():
            if not widget.isVisible():
                continue

            # Get accurate widget width using sizeHint (matches calc_size logic)
            qwidget = widget.widget()
            if qwidget:
                qwidget.adjustSize()
                size_hint = qwidget.sizeHint()
                widget_width = max(size_hint.width(), 200)
                widget_height = size_hint.height()
            else:
                widget_rect = widget.boundingRect()
                widget_width = widget_rect.width()
                widget_height = widget_rect.height()

            if not inputs:
                x = rect.left() + margin
                widget.widget().setTitleAlign("left")
            elif not outputs:
                x = rect.right() - widget_width - margin
                widget.widget().setTitleAlign("right")
            else:
                # Center the widget
                x = rect.center().x() - (widget_width / 2)
                widget.widget().setTitleAlign("center")

            # Clamp x position to keep widget within node bounds
            # This prevents widgets from floating outside the node
            if x < min_x:
                x = min_x
            if x + widget_width > max_x:
                x = max_x - widget_width
                # If widget is still wider than available space, align to left
                if x < min_x:
                    x = min_x

            widget.setPos(x, y)
            y += widget_height

    def _paint_lod(self, painter: QPainter, lod_level: LODLevel = LODLevel.LOW) -> None:
        """
        Paint simplified LOD version for low zoom levels.

        PERFORMANCE: At low zoom levels, skip expensive rendering (icons, text,
        badges, status indicators) and draw simple colored rectangles.
        This significantly reduces CPU when viewing large workflows zoomed out.

        Args:
            lod_level: The LOD level to render at (ULTRA_LOW or LOW)
        """
        painter.save()

        # Use LOD manager to determine antialiasing
        lod_manager = get_lod_manager()
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing, lod_manager.should_use_antialiasing()
        )

        rect = self._get_node_rect()

        # Always use normal node background color (status colors removed)
        fill_color = self._node_bg_color

        # ULTRA_LOW: Just fill rect, no rounded corners
        if lod_level == LODLevel.ULTRA_LOW:
            painter.fillRect(rect, fill_color)
        else:
            # LOW: Simple rounded rect
            painter.setBrush(QBrush(fill_color))
            painter.setPen(_PEN_STYLE_NONE)
            painter.drawRoundedRect(rect, 4, 4)

        # Simple border based on status
        if self.selected or self._is_running:
            painter.setPen(QPen(self._selected_border_color, 2))
        elif self._has_warning:
            painter.setPen(QPen(_WARNING_ORANGE, 2))
        elif self._is_disabled:
            # LOD: Use solid bright border (dots too small at low zoom)
            painter.setPen(QPen(QColor("#A1A1AA"), 2.5))  # Zinc 400 - bright
        else:
            painter.setPen(QPen(self._normal_border_color, 1))

        painter.setBrush(_BRUSH_STYLE_NONE)
        if lod_level == LODLevel.ULTRA_LOW:
            painter.drawRect(rect)
        else:
            painter.drawRoundedRect(rect, 4, 4)

        # LOD disabled: Draw X pattern overlay for clear indication
        if self._is_disabled:
            overlay_color = QColor("#71717A")  # Zinc 500
            overlay_color.setAlpha(200)
            painter.setPen(QPen(overlay_color, 1.5))
            # Draw X across the node
            painter.drawLine(rect.topLeft(), rect.bottomRight())
            painter.drawLine(rect.topRight(), rect.bottomLeft())

        # Always draw the node title (LOW level only, ULTRA_LOW too small)
        if lod_level != LODLevel.ULTRA_LOW:
            self._draw_text(painter, rect)

        painter.restore()

    def _paint_as_dot(self, painter) -> None:
        """
        Paint node as a simple colored dot for ULTRA_LOW semantic zoom.

        When zoomed out < 25%, nodes become simple dots showing just the
        workflow structure and category colors. This is ideal for navigation
        and understanding the overall workflow layout.
        """
        painter.save()
        rect = self._get_node_rect()

        # Get category color for the dot (status colors removed)
        if self._cached_header_color:
            dot_color = self._cached_header_color
        else:
            dot_color = get_category_header_color(self._category)

        # Draw as a centered circle/dot
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 3  # Proportional dot size

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setBrush(QBrush(dot_color))

        # Selection ring
        if self.selected:
            painter.setPen(QPen(self._selected_border_color, 2))
        else:
            painter.setPen(_PEN_STYLE_NONE)

        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def paint(self, painter, option, widget):
        """
        Custom paint method for the node.

        PERFORMANCE: Uses centralized LOD manager to determine rendering detail.
        The LOD level is computed once per frame (in viewport update timer),
        not per-node. This eliminates redundant zoom calculations.

        HIGH PERFORMANCE MODE: When enabled (manually or auto-enabled at 50+ nodes),
        forces LOD rendering at all zoom levels for maximum performance.
        """
        # PERFORMANCE: Lazy widget initialization on first paint
        # This defers the expensive QGraphicsProxyWidget embedding from
        # node construction to first render, making node creation instant
        node = getattr(self, "_node", None)
        if node and hasattr(node, "_ensure_widgets_initialized"):
            node._ensure_widgets_initialized()

        # Get LOD level from centralized manager (computed once per frame)
        lod_manager = get_lod_manager()
        lod_level = lod_manager.current_lod

        # HIGH PERFORMANCE MODE: Force LOD rendering at all zoom levels
        if _high_performance_mode:
            self._paint_lod(painter, LODLevel.LOW)
            return

        # LOD check - at low zoom, render simplified version
        if lod_level in (LODLevel.ULTRA_LOW, LODLevel.LOW):
            self._paint_lod(painter, lod_level)
            return

        # SEMANTIC ZOOM: ULTRA_LOW shows dots/blocks for structure overview
        if lod_manager.should_show_node_as_dot():
            self._paint_as_dot(painter)
            return

        painter.save()
        painter.setRenderHint(_ANTIALIASING, True)

        # Get node rectangle (actual node area, not including badge space)
        rect = self._get_node_rect()
        border_width = 2.0

        # Determine border color and style based on status states
        # Disabled state uses dotted border for clear visual feedback
        if self._is_running:
            border_color = QColor("#FBBF24")  # Amber 400 (brighter running highlight)
            border_style = _PEN_STYLE_DASH
            border_width = 3
        elif self._has_warning:
            border_color = _WARNING_ORANGE
            border_style = _PEN_STYLE_SOLID
        elif self._is_disabled:
            # Use brighter gray for dotted border to stand out against dark bg
            border_color = QColor("#71717A")  # Zinc 500 - more visible
            border_style = _PEN_STYLE_DOT
        elif self.selected:
            border_color = self._selected_border_color
            border_style = _PEN_STYLE_SOLID
        else:
            border_color = self._normal_border_color
            border_style = _PEN_STYLE_SOLID

        # Create rounded rectangle path
        radius = 8.0
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Fill background - with opacity reduction for disabled state
        if self._is_disabled:
            bg_color = QColor(self._node_bg_color)
            bg_color.setAlpha(NODE_DISABLED_BG_ALPHA)  # Theme-defined opacity
            painter.fillPath(path, QBrush(bg_color))
        else:
            painter.fillPath(path, QBrush(self._node_bg_color))

        # Draw selection glow effect (pulsing outer glow when selected)
        if self._selection_glow_enabled and self.selected:
            self._draw_selection_glow(painter, rect, radius)

        # Draw border - disabled state gets thicker dotted border for visibility
        if self._is_disabled:
            pen = QPen(border_color, NODE_DISABLED_BORDER_WIDTH)
            pen.setStyle(_PEN_STYLE_DOT)
            pen.setDashPattern([2, 3])  # Shorter dots, more visible pattern
        else:
            pen = QPen(border_color, border_width)
            pen.setStyle(border_style)
            if self._is_running:
                # Animated dash pattern for running state
                pen.setDashOffset(self._animation_offset)
                pen.setDashPattern([2.5, 2.5])
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.strokePath(path, pen)

        # Draw node text (name) FIRST - header bar goes behind icons
        self._draw_text(painter, rect)

        # Draw collapse button in header
        self._draw_collapse_button(painter, rect)

        # Draw execution time badge at bottom
        self._draw_execution_time(painter, rect)

        # Draw robot override indicator (bottom-left corner)
        if self._has_robot_override:
            self._draw_robot_override_icon(painter, rect)

        # Draw disabled overlay (diagonal gray lines)
        if self._is_disabled:
            self._draw_disabled_overlay(painter, rect)

        # Draw status indicator LAST so it's always on top
        # Priority: error > warning > skipped > completed
        if self._has_error:
            self._draw_error_icon(painter, rect)
        elif self._has_warning:
            self._draw_warning_icon(painter, rect)
        elif self._is_skipped:
            self._draw_skipped_icon(painter, rect)
        elif self._is_completed:
            self._draw_checkmark(painter, rect)

        # Draw cache indicator (top-left corner, always visible if enabled)
        if self._cache_enabled:
            self._draw_cache_icon(painter, rect)

        painter.restore()

    def _get_status_icon_position(self, rect) -> tuple:
        """Get position for status icons (above node, next to execution time badge)."""
        size = 16
        # Position above the node, to the right of center (where time badge is)
        # This places the icon next to the execution time badge
        x = rect.center().x() + 30  # Right of the centered time badge
        y = rect.top() - size - 6  # Above node, same height as time badge
        return x, y, size

    def _draw_checkmark(self, painter, rect):
        """Draw a checkmark above node, next to execution time badge."""
        x, y, size = self._get_status_icon_position(rect)

        # Background circle (using cached color)
        painter.setBrush(QBrush(_SUCCESS_GREEN))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size / 2, y + size / 2), size / 2, size / 2)

        # Checkmark symbol
        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw checkmark path
        check_path = QPainterPath()
        check_path.moveTo(x + size * 0.25, y + size * 0.5)
        check_path.lineTo(x + size * 0.45, y + size * 0.7)
        check_path.lineTo(x + size * 0.75, y + size * 0.3)
        painter.drawPath(check_path)

    def _draw_error_icon(self, painter, rect):
        """Draw an error X icon above node, next to execution time badge."""
        x, y, size = self._get_status_icon_position(rect)

        # Red circle background (using cached color)
        painter.setBrush(QBrush(_ERROR_RED))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size / 2, y + size / 2), size / 2, size / 2)

        # White X symbol
        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        inset = size * 0.3
        painter.drawLine(QPointF(x + inset, y + inset), QPointF(x + size - inset, y + size - inset))
        painter.drawLine(QPointF(x + size - inset, y + inset), QPointF(x + inset, y + size - inset))

    def _draw_warning_icon(self, painter: QPainter, rect: QRectF) -> None:
        """Draw a warning triangle icon above node, next to execution time badge."""
        x, y, size = self._get_status_icon_position(rect)

        # Yellow/orange triangle background
        painter.setBrush(QBrush(_WARNING_ORANGE))
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw triangle pointing up
        triangle_path = QPainterPath()
        triangle_path.moveTo(x + size / 2, y)  # Top point
        triangle_path.lineTo(x + size, y + size)  # Bottom right
        triangle_path.lineTo(x, y + size)  # Bottom left
        triangle_path.closeSubpath()
        painter.drawPath(triangle_path)

        # White exclamation mark
        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                2.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        # Exclamation line
        painter.drawLine(
            QPointF(x + size / 2, y + size * 0.3),
            QPointF(x + size / 2, y + size * 0.6),
        )
        # Exclamation dot
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(QPointF(x + size / 2, y + size * 0.78), 2, 2)

    def _draw_skipped_icon(self, painter: QPainter, rect: QRectF) -> None:
        """Draw a fast-forward (skip) icon above node, next to execution time badge."""
        x, y, size = self._get_status_icon_position(rect)

        # Gray circle background
        painter.setBrush(QBrush(_SKIPPED_GRAY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size / 2, y + size / 2), size / 2, size / 2)

        # White fast-forward symbol (two triangles pointing right)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))

        # First triangle
        tri1_path = QPainterPath()
        tri1_path.moveTo(x + size * 0.2, y + size * 0.25)
        tri1_path.lineTo(x + size * 0.5, y + size * 0.5)
        tri1_path.lineTo(x + size * 0.2, y + size * 0.75)
        tri1_path.closeSubpath()
        painter.drawPath(tri1_path)

        # Second triangle
        tri2_path = QPainterPath()
        tri2_path.moveTo(x + size * 0.45, y + size * 0.25)
        tri2_path.lineTo(x + size * 0.75, y + size * 0.5)
        tri2_path.lineTo(x + size * 0.45, y + size * 0.75)
        tri2_path.closeSubpath()
        painter.drawPath(tri2_path)

    def _draw_cache_icon(self, painter: QPainter, rect: QRectF) -> None:
        """Draw a cache/lightning bolt icon in the top-left corner of the node."""
        size = 14
        # Position in top-left corner of header area
        x = rect.left() + 6
        y = rect.top() + 6

        # Cyan/teal circle background for cache indicator
        cache_color = QColor(0, 188, 212)  # Cyan/teal color
        painter.setBrush(QBrush(cache_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size / 2, y + size / 2), size / 2, size / 2)

        # White lightning bolt symbol
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))

        bolt_path = QPainterPath()
        # Lightning bolt shape
        bolt_path.moveTo(x + size * 0.55, y + size * 0.15)  # Top
        bolt_path.lineTo(x + size * 0.35, y + size * 0.5)  # Middle left
        bolt_path.lineTo(x + size * 0.5, y + size * 0.5)  # Middle center
        bolt_path.lineTo(x + size * 0.45, y + size * 0.85)  # Bottom
        bolt_path.lineTo(x + size * 0.65, y + size * 0.5)  # Middle right
        bolt_path.lineTo(x + size * 0.5, y + size * 0.5)  # Middle center
        bolt_path.closeSubpath()
        painter.drawPath(bolt_path)

    def _draw_disabled_overlay(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw gray wash and diagonal lines overlay for disabled state.

        Visual feedback consists of:
        - Semi-transparent gray wash for desaturation effect
        - Diagonal hatching lines for clear "disabled" indication
        - Combined with dotted border from paint() method

        Uses theme constants NODE_DISABLED_WASH_ALPHA and NODE_DISABLED_OPACITY
        for consistent styling across the application.
        """
        painter.save()

        # Apply overall opacity reduction for grayscale effect
        painter.setOpacity(NODE_DISABLED_OPACITY)

        # Clip to node bounds
        radius = 8.0
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(clip_path)

        # Draw gray wash overlay first (desaturation effect)
        # Using theme-derived disabled colors with centralized alpha
        cc = Theme.get_canvas_colors()
        wash_color = QColor(cc.status_disabled)
        wash_color.setAlpha(NODE_DISABLED_WASH_ALPHA)
        painter.fillRect(rect, wash_color)

        # Draw diagonal lines (hatching pattern for clear disabled indication)
        line_spacing = 8  # Balanced spacing for visibility without clutter
        line_color = QColor(cc.node_border_normal)
        line_color.setAlpha(160)
        painter.setPen(QPen(line_color, 1.5, _PEN_STYLE_SOLID))

        # Draw lines from top-left to bottom-right direction
        start_x = rect.left() - rect.height()
        while start_x < rect.right():
            painter.drawLine(
                QPointF(start_x, rect.bottom()),
                QPointF(start_x + rect.height(), rect.top()),
            )
            start_x += line_spacing

        painter.restore()

    def _draw_selection_glow(self, painter: QPainter, rect: QRectF, radius: float) -> None:
        """
        Draw pulsing selection glow effect around the node.

        Uses sine wave modulation for smooth pulse effect.
        Draws multiple semi-transparent borders for glow illusion.

        Args:
            painter: QPainter instance
            rect: Node bounding rectangle
            radius: Corner radius
        """
        # Calculate pulse intensity using sine wave (0.3 to 1.0 range)
        pulse = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._selection_glow_phase * 2 * math.pi))

        # Glow color (selection color with pulsing alpha)
        glow_color = QColor(self._selected_border_color)  # From theme

        # Draw multiple glow layers for soft effect
        glow_layers = [
            (6.0, int(40 * pulse)),  # Outer glow
            (4.0, int(60 * pulse)),  # Middle glow
            (2.0, int(100 * pulse)),  # Inner glow
        ]

        for offset, alpha in glow_layers:
            glow_rect = rect.adjusted(-offset, -offset, offset, offset)
            glow_path = QPainterPath()
            glow_path.addRoundedRect(glow_rect, radius + offset, radius + offset)

            glow_color.setAlpha(alpha)
            pen = QPen(glow_color, 2.0)
            painter.strokePath(glow_path, pen)

    def _draw_execution_time(self, painter, rect):
        """Draw execution time badge above the node."""
        if self._execution_time_ms is None:
            return

        # Format time appropriately
        if self._execution_time_ms < 1000:
            time_text = f"{int(self._execution_time_ms)}ms"
        elif self._execution_time_ms < 60000:
            time_text = f"{self._execution_time_ms / 1000:.1f}s"
        else:
            mins = int(self._execution_time_ms // 60000)
            secs = int((self._execution_time_ms % 60000) // 1000)
            time_text = f"{mins}:{secs:02d}"

        # Measure text for badge sizing
        painter.setFont(self.get_time_font())
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(time_text)
        text_height = fm.height()

        # Badge dimensions
        padding_h = 6
        padding_v = 2
        badge_width = text_width + padding_h * 2
        badge_height = text_height + padding_v * 2
        badge_radius = 4

        # Position above the node (centered horizontally)
        badge_x = rect.center().x() - badge_width / 2
        badge_y = rect.top() - badge_height - 6

        badge_rect = QRectF(badge_x, badge_y, badge_width, badge_height)

        # Draw badge background (using cached color, with fallback)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, badge_radius, badge_radius)
        bg_color = _BADGE_BG_COLOR if _BADGE_BG_COLOR is not None else _get_badge_bg_color()
        painter.fillPath(badge_path, QBrush(bg_color))

        # Draw text (using cached color, with fallback)
        text_color = _BADGE_TEXT_COLOR if _BADGE_TEXT_COLOR is not None else _get_badge_text_color()
        painter.setPen(text_color)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, time_text)

    def _draw_text(self, painter, rect):
        """Draw node name with SOLID category-colored header background."""
        # Header dimensions
        header_height = 26
        radius = 8.0

        # Draw header background with category color
        header_rect = QRectF(rect.left(), rect.top(), rect.width(), header_height)
        header_path = QPainterPath()
        # Only round top corners
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

        # Get category-based header color (cached for performance)
        # Use SOLID color at FULL opacity - no gradient, no transparency
        if self._cached_header_color is None:
            self._cached_header_color = get_category_header_color(self._category)

        # Fill with SOLID color (no gradient)
        painter.fillPath(header_path, QBrush(self._cached_header_color))

        # Draw separator line (slightly darker than header)
        sep_color = QColor(self._cached_header_color)
        # Darken the separator by reducing brightness
        sep_color.setRed(max(0, int(sep_color.red() * 0.7)))
        sep_color.setGreen(max(0, int(sep_color.green() * 0.7)))
        sep_color.setBlue(max(0, int(sep_color.blue() * 0.7)))
        painter.setPen(QPen(sep_color, 1))
        painter.drawLine(
            QPointF(header_rect.left(), header_rect.bottom()),
            QPointF(header_rect.right(), header_rect.bottom()),
        )

        # Draw node name (centered, using cached font and color)
        # Use bright white for maximum contrast on colored headers
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(_get_title_font())

        # Get node name
        node_name = self.name if hasattr(self, "name") else "Node"
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, node_name)

    def _draw_collapse_button(self, painter, rect):
        """Draw collapse/expand button in the header."""
        global _COLLAPSE_BTN_BG, _COLLAPSE_BTN_SYMBOL

        # Ensure collapse button colors are initialized
        if _COLLAPSE_BTN_BG is None:
            _init_collapse_btn_colors()

        # Button dimensions
        btn_size = 16
        margin = 6
        x = rect.right() - btn_size - margin
        y = rect.top() + 5  # Centered in header

        # Store button rect for click detection
        self._collapse_button_rect = QRectF(x, y, btn_size, btn_size)

        # Draw button background (using cached color)
        btn_path = QPainterPath()
        btn_path.addRoundedRect(self._collapse_button_rect, 3, 3)
        painter.fillPath(btn_path, QBrush(_COLLAPSE_BTN_BG))

        # Draw +/- symbol (using cached color)
        painter.setPen(
            QPen(_COLLAPSE_BTN_SYMBOL, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )

        center_x = x + btn_size / 2
        center_y = y + btn_size / 2
        line_len = btn_size * 0.35

        # Horizontal line (always drawn)
        painter.drawLine(
            QPointF(center_x - line_len, center_y),
            QPointF(center_x + line_len, center_y),
        )

        # Vertical line (only when collapsed - shows "+")
        if self._is_collapsed:
            painter.drawLine(
                QPointF(center_x, center_y - line_len),
                QPointF(center_x, center_y + line_len),
            )

    def set_collapsed(self, collapsed: bool):
        """Set collapsed state for visual update.

        CRITICAL: Must call prepareGeometryChange() before the geometry changes
        via post_init()/draw_node() because when widgets are hidden/shown,
        the node's bounding rect changes size.
        """
        if self._is_collapsed == collapsed:
            return

        self._is_collapsed = collapsed

        # CRITICAL: Notify Qt scene that bounding rect will change
        # This must happen BEFORE draw_node() recalculates the size
        # Without this, Qt's scene caching causes rendering artifacts during pan/scroll
        self.prepareGeometryChange()
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events, including collapse button clicks and middle-click."""
        from PySide6.QtCore import Qt
        from loguru import logger

        # Middle-click: Record press position for click detection
        # Only show popup on release if it was a click (not a drag/pan)
        if event.button() == Qt.MouseButton.MiddleButton:
            # Verify click is actually within node bounds
            if not self.boundingRect().contains(event.pos()):
                event.ignore()
                return

            # Store press position and scene pos for click vs drag detection
            self._mmb_press_pos = event.pos()
            self._mmb_press_scene_pos = event.scenePos()
            # Accept to receive release event
            event.accept()
            return

        # Check if click is on collapse button
        # Use expanded hit area for easier clicking
        if self._collapse_button_rect and event.button() == Qt.MouseButton.LeftButton:
            # Expand hit area by 4px on each side for easier clicking
            hit_rect = self._collapse_button_rect.adjusted(-4, -4, 4, 4)
            click_pos = event.pos()
            if hit_rect.contains(click_pos):
                # Get the VisualNode instance via NodeGraphQt's internal _node attribute
                node = getattr(self, "_node", None)
                if node and hasattr(node, "toggle_collapse"):
                    node.toggle_collapse()
                    event.accept()
                    return
                else:
                    logger.warning(f"Node not found or no toggle_collapse: {node}")

        # Call parent implementation for normal behavior
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events, including MMB click for output inspector."""
        from PySide6.QtCore import Qt

        # MMB release: Show popup only if it was a click (not a drag/pan)
        if event.button() == Qt.MouseButton.MiddleButton:
            if hasattr(self, "_mmb_press_scene_pos") and self._mmb_press_scene_pos is not None:
                # Check distance in scene coords (more accurate if view moved)
                delta = event.scenePos() - self._mmb_press_scene_pos
                distance = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

                if distance < 10:
                    # It's a click - show output inspector
                    view = (
                        self.scene().views()[0] if self.scene() and self.scene().views() else None
                    )
                    if view:
                        node_rect = self.sceneBoundingRect()
                        bottom_center_scene = node_rect.bottomLeft()
                        view_pos = view.mapFromScene(bottom_center_scene)
                        global_pos = view.mapToGlobal(view_pos)
                        self._emit_output_inspector_signal(global_pos)

                # Clear press positions
                self._mmb_press_pos = None
                self._mmb_press_scene_pos = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _emit_output_inspector_signal(self, global_pos):
        """
        Emit signal to show output inspector for this node.

        The signal is routed through the NodeGraphWidget which handles
        creating and positioning the popup.

        Args:
            global_pos: Global screen position for popup
        """
        from loguru import logger

        # Get the VisualNode instance
        node = getattr(self, "_node", None)
        if not node:
            logger.debug("Cannot show output inspector: no visual node attached")
            return

        # Get output data from the visual node
        output_data = None
        if hasattr(node, "_last_output"):
            output_data = node._last_output

        # Find the graph widget and emit the signal
        # The graph viewer is the parent of the scene
        scene = self.scene()
        if not scene:
            return

        views = scene.views()
        if not views:
            return

        view = views[0]

        # Look for NodeGraphWidget parent
        from casare_rpa.presentation.canvas.graph.node_graph_widget import (
            NodeGraphWidget,
        )

        parent = view.parent()
        while parent:
            if isinstance(parent, NodeGraphWidget):
                # Call the show_output_inspector method
                if hasattr(parent, "show_output_inspector"):
                    node_id = (
                        node.get_property("node_id") if hasattr(node, "get_property") else node.id
                    )
                    node_name = node.name() if callable(node.name) else str(node.name)
                    # Pass self (the node item) for position tracking
                    parent.show_output_inspector(node_id, node_name, output_data, global_pos, self)
                    logger.debug(f"Showing output inspector for {node_name}")
                    return
                break
            parent = (
                parent.parent() if hasattr(parent, "parent") and callable(parent.parent) else None
            )

        logger.debug("Could not find NodeGraphWidget to show output inspector")

    def itemChange(self, change, value):
        """
        Handle item changes, particularly position changes.

        PERFORMANCE: Notifies viewport culling when node position changes
        so the spatial hash can be updated for efficient viewport queries.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Notify callback for viewport culling spatial hash update
            if self._on_position_changed:
                try:
                    self._on_position_changed(self)
                except Exception:
                    pass  # Don't let callback errors break node movement
        return super().itemChange(change, value)

    def set_position_callback(self, callback: callable) -> None:
        """Set callback for position change notifications (used by viewport culling)."""
        self._on_position_changed = callback

    def set_running(self, running: bool):
        """
        Set node running state.

        Uses centralized AnimationCoordinator for efficient animation.

        Args:
            running: True to show running animation, False to stop
        """
        self._is_running = running
        if running:
            self._animation_coordinator.register(self, "running")
        else:
            self._animation_coordinator.unregister(self, "running")
            self._animation_offset = 0
        self.update()

    def set_completed(self, completed: bool):
        """Set node completed state."""
        self._is_completed = completed
        self.update()

    def set_error(self, has_error: bool):
        """Set node error state."""
        self._has_error = has_error
        if has_error:
            self._is_completed = False  # Error takes precedence
        self.update()

    def set_disabled(self, disabled: bool) -> None:
        """
        Set node disabled state.

        Disabled nodes show a gray diagonal lines overlay and reduced opacity.
        Disabled nodes are skipped during workflow execution.
        Widget parameters also get dimmed with reduced opacity.

        Args:
            disabled: True to disable the node, False to enable
        """
        self._is_disabled = disabled

        # Apply disabled styling to all widget parameters
        self._apply_widget_disabled_styling(disabled)

        self.update()

    def _apply_widget_disabled_styling(self, disabled: bool) -> None:
        """
        Apply or remove disabled styling from widget parameters.

        Disabled widgets get reduced opacity (40%) to match the node background.
        Opacity effects are cached to prevent memory leaks from repeated creation.

        Args:
            disabled: True to apply disabled styling, False to restore normal
        """
        try:
            for widget_name, widget in self.widgets.items():
                if widget is None:
                    continue

                if disabled:
                    # Get or create cached opacity effect for this widget
                    if widget_name not in self._opacity_effects:
                        opacity_effect = QGraphicsOpacityEffect()
                        opacity_effect.setOpacity(0.4)  # 40% opacity (very dimmed)
                        self._opacity_effects[widget_name] = opacity_effect
                    widget.setGraphicsEffect(self._opacity_effects[widget_name])
                else:
                    # Remove opacity effect (but keep cached for reuse)
                    widget.setGraphicsEffect(None)
        except Exception:
            # Silently handle any widget access errors
            pass

    def is_disabled(self) -> bool:
        """
        Check if node is disabled.

        Returns:
            True if node is disabled
        """
        return self._is_disabled

    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Set node cache state.

        Cached nodes show a cyan lightning bolt icon in the top-left corner.
        Cached nodes store execution results and return them instantly
        on subsequent calls with the same inputs.

        Args:
            enabled: True to enable caching, False to disable
        """
        self._cache_enabled = enabled
        self.update()

    def is_cache_enabled(self) -> bool:
        """
        Check if node has caching enabled.

        Returns:
            True if caching is enabled for this node
        """
        return self._cache_enabled

    def set_skipped(self, skipped: bool) -> None:
        """
        Set node skipped state.

        Skipped nodes show a gray fast-forward icon above the node.
        This indicates the node was skipped during execution (e.g., condition not met).

        Args:
            skipped: True to show skipped indicator, False to hide
        """
        self._is_skipped = skipped
        self.update()

    def is_skipped(self) -> bool:
        """
        Check if node is in skipped state.

        Returns:
            True if node was skipped
        """
        return self._is_skipped

    def set_warning(self, has_warning: bool) -> None:
        """
        Set node warning state.

        Warning nodes show a yellow triangle icon above the node and orange border.
        This indicates validation warnings or potential issues.

        Args:
            has_warning: True to show warning indicator, False to hide
        """
        self._has_warning = has_warning
        self.update()

    def has_warning(self) -> bool:
        """
        Check if node has warning state.

        Returns:
            True if node has a warning
        """
        return self._has_warning

    def set_execution_time(self, time_seconds: Optional[float]):
        """
        Set execution time to display.

        Args:
            time_seconds: Execution time in seconds, or None to clear
        """
        # Notify Qt that bounding rect will change (badge area above node)
        self.prepareGeometryChange()
        if time_seconds is not None:
            self._execution_time_ms = time_seconds * 1000
        else:
            self._execution_time_ms = None
        # Update only this item (not the entire scene) for better performance
        self.update()

    def clear_execution_state(self):
        """Reset all execution state for workflow restart.

        Note: Robot override state and disabled state are NOT cleared here
        as they are configuration, not execution state. They persist across runs.
        """
        self.prepareGeometryChange()  # Bounding rect changes when badge is removed
        self._is_running = False
        self._is_completed = False
        self._has_error = False
        self._is_skipped = False  # Clear skipped (execution result)
        self._has_warning = False  # Clear warning (execution result)
        # Note: _is_disabled is NOT cleared - it's configuration
        self._execution_time_ms = None
        self._animation_offset = 0
        # Stop running animation but preserve selection glow
        self._animation_coordinator.unregister(self, "running")
        self.update()

    def clear_robot_override(self):
        """Clear robot override state for this node."""
        self._has_robot_override = False
        self._override_is_capability_based = False
        self.update()

    def _draw_robot_override_icon(self, painter, rect):
        """Draw robot override indicator in the bottom-left corner.

        Shows a small robot icon when this node has a robot override configured.
        Different colors indicate specific robot (teal) vs capability-based (purple).
        """
        size = 18
        margin = 6
        x = rect.left() + margin
        y = rect.bottom() - size - margin

        # Choose color based on override type
        if self._override_is_capability_based:
            bg_color = self._capability_override_color  # Purple for capability
        else:
            bg_color = self._robot_override_color  # Teal for specific robot

        # Background circle
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size / 2, y + size / 2), size / 2, size / 2)

        # Draw robot icon (simplified)
        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                1.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Robot head (rectangle)
        head_w = size * 0.5
        head_h = size * 0.35
        head_x = x + (size - head_w) / 2
        head_y = y + size * 0.2
        painter.drawRect(QRectF(head_x, head_y, head_w, head_h))

        # Robot eyes (two small circles)
        eye_r = size * 0.06
        eye_y = head_y + head_h * 0.4
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(QPointF(head_x + head_w * 0.3, eye_y), eye_r, eye_r)
        painter.drawEllipse(QPointF(head_x + head_w * 0.7, eye_y), eye_r, eye_r)

        # Robot antenna
        antenna_x = x + size / 2
        painter.drawLine(QPointF(antenna_x, head_y), QPointF(antenna_x, head_y - size * 0.12))
        painter.drawEllipse(QPointF(antenna_x, head_y - size * 0.15), size * 0.04, size * 0.04)

        # Robot body (rectangle below head)
        body_y = head_y + head_h + size * 0.05
        body_h = size * 0.25
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(head_x, body_y, head_w, body_h))

    def set_robot_override(self, has_override: bool, is_capability_based: bool = False) -> None:
        """Set robot override state for this node.

        Args:
            has_override: Whether this node has a robot override
            is_capability_based: True if override is capability-based, False if specific robot
        """
        self._has_robot_override = has_override
        self._override_is_capability_based = is_capability_based
        self.update()

    def get_robot_override_tooltip(self) -> Optional[str]:
        """Get tooltip text for robot override indicator.

        Returns:
            Tooltip text if override exists, None otherwise
        """
        if not self._has_robot_override:
            return None
        if self._override_is_capability_based:
            return "This node requires specific capabilities"
        return "This node is assigned to a specific robot"

    def set_icon(self, pixmap: QPixmap) -> None:
        """
        Set custom node icon.

        Also registers with icon atlas for GPU-efficient rendering
        if node_type_name is set.

        Args:
            pixmap: The icon pixmap to use
        """
        self._custom_icon_pixmap = pixmap

        # Register with icon atlas for GPU-efficient rendering
        if self._node_type_name and pixmap and not pixmap.isNull():
            icon_atlas = get_icon_atlas()
            if not icon_atlas.has_icon(self._node_type_name):
                icon_atlas.add_icon(self._node_type_name, pixmap)

        self.update()

    def set_node_type_name(self, type_name: str) -> None:
        """
        Set the node type name for icon atlas lookups.

        Args:
            type_name: The node type identifier (e.g., "ClickNode")
        """
        self._node_type_name = type_name

        # If icon already set, register it with atlas
        if self._custom_icon_pixmap and not self._custom_icon_pixmap.isNull():
            icon_atlas = get_icon_atlas()
            if not icon_atlas.has_icon(type_name):
                icon_atlas.add_icon(type_name, self._custom_icon_pixmap)

    def get_node_type_name(self) -> str:
        """
        Get the node type name.

        Returns:
            The node type identifier
        """
        return self._node_type_name

    def set_category(self, category: str) -> None:
        """
        Set the node category for header coloring.

        The category determines the header gradient color.
        Call this after node creation to apply category-specific styling.

        Args:
            category: Category string (e.g., "browser", "data", "control_flow")
        """
        if self._category != category:
            self._category = category
            self._cached_header_color = None  # Invalidate cached color
            self.update()

    def get_category(self) -> str:
        """
        Get the node category.

        Returns:
            Category string
        """
        return self._category

    def borderColor(self):
        """Get current border color based on state."""
        if self._is_running or self.selected:
            return self._selected_border_color.getRgb()
        return self._normal_border_color.getRgb()

    def setBorderColor(self, r, g, b, a=255):
        """Set normal border color."""
        self._normal_border_color = QColor(r, g, b, a)
        if not self.selected and not self._is_running:
            self.update()

    # =========================================================================
    # LIFECYCLE ANIMATIONS (no-ops - animations removed)
    # =========================================================================

    def animate_creation(self) -> None:
        """No-op - animations removed."""
        pass

    def animate_deletion(self, on_complete: Optional[Callable] = None) -> None:
        """No-op - animations removed. Calls callback immediately."""
        if on_complete:
            on_complete()

    def animate_selection(self, selected: bool) -> None:
        """No-op - animations removed."""
        pass

    def _start_selection_glow(self) -> None:
        """No-op - animations removed."""
        self._selection_glow_enabled = False

    def _stop_selection_glow(self) -> None:
        """No-op - animations removed."""
        self._selection_glow_enabled = False
        self._selection_glow_phase = 0.0

    def setSelected(self, selected: bool) -> None:
        """Override selection without animation."""
        super().setSelected(selected)

    def _add_port(self, port):
        """
        Custom _add_port with font fix and port label truncation.
        """
        port_name = port.name
        display_name = port_name

        # Create font with explicit size
        font = QFont()
        font.setPointSize(8)

        # Use QFontMetrics for accurate text measurement
        from PySide6.QtGui import QFontMetrics

        fm = QFontMetrics(font)

        # Calculate actual text width
        text_width = fm.horizontalAdvance(port_name)

        # Truncate if text exceeds max width OR max character count
        if text_width > PORT_LABEL_MAX_WIDTH_PX or len(port_name) > PORT_LABEL_MAX_LENGTH:
            # Use the smaller of the two constraints
            max_width = min(
                PORT_LABEL_MAX_WIDTH_PX,
                fm.horizontalAdvance("x" * PORT_LABEL_MAX_LENGTH),
            )
            display_name = fm.elidedText(port_name, Qt.TextElideMode.ElideRight, max_width)

        text = QGraphicsTextItem(display_name, self)
        text.setFont(font)
        text.setVisible(port.display_name)
        text.setCacheMode(ITEM_CACHE_MODE)

        # Set tooltip with full port name for truncated labels
        if display_name != port_name:
            text.setToolTip(f"{port_name}")
        else:
            # Standard tooltip for non-truncated labels
            conn_type = "multi" if port.multi_connection else "single"
            text.setToolTip(f"{port_name}: ({conn_type})")

        if port.port_type == PortTypeEnum.IN.value:
            self._input_items[port] = text
        elif port.port_type == PortTypeEnum.OUT.value:
            self._output_items[port] = text

        if self.scene():
            self.post_init()
        return port
