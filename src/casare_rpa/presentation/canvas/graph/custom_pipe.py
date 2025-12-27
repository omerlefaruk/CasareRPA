"""
Custom pipe styling for node connections.

Provides:
- Solid line style with visual feedback when dragging connections
- Type-colored wires (like Unreal Blueprints)
- Variable wire thickness by data type
- Connection labels showing data type
- Output preview on hover
- Connection compatibility feedback
- High Performance Mode support (simplified rendering)
- Execution flow animation (continuous dot animation during execution)
- Smart wire routing with bezier obstacle avoidance

All colors are sourced from the unified theme system (theme.py).
"""

from loguru import logger
from NodeGraphQt.qgraphics.pipe import (
    LayoutDirectionEnum,
    LivePipeItem,
    PipeEnum,
    PipeItem,
    PortTypeEnum,
)
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
    QTransform,
)

# Import DataType for type-based coloring
from casare_rpa.domain.value_objects.types import DataType

# Import high performance mode flag from custom_node_item
from casare_rpa.presentation.canvas.graph.custom_node_item import (
    get_high_performance_mode,
)

# Import LOD manager for centralized zoom-based rendering decisions
from casare_rpa.presentation.canvas.graph.lod_manager import (
    LODLevel,
    get_lod_manager,
)

# Import unified theme system
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS

# ============================================================================
# SMART WIRE ROUTING
# ============================================================================
# Global flag to enable/disable smart wire routing.
# When enabled, wires automatically route around node bounding boxes.
# Disabled by default - can be enabled via View menu.

_smart_routing_enabled: bool = False


def set_smart_routing_enabled(enabled: bool) -> None:
    """Enable or disable smart wire routing globally."""
    global _smart_routing_enabled
    _smart_routing_enabled = enabled


def is_smart_routing_enabled() -> bool:
    """Check if smart wire routing is enabled."""
    return _smart_routing_enabled


# ============================================================================
# PAINT OBJECT INITIALIZATION - Colors from unified theme
# ============================================================================
# These are lazily initialized on first access to ensure theme is loaded.
# Using theme provides consistency across all canvas components.

_INSERT_HIGHLIGHT_COLOR = None
_HOVER_COLOR = None
_LABEL_BG_COLOR = None
_LABEL_BORDER_COLOR = None
_LABEL_TEXT_COLOR = None
_PREVIEW_BG_COLOR = None
_PREVIEW_BORDER_COLOR = None
_PREVIEW_TEXT_COLOR = None
_LABEL_FONT = QFont("Segoe UI", 8)
_PREVIEW_FONT = QFont("Consolas", 9)


def _init_pipe_colors():
    """Initialize pipe colors from theme (lazy initialization)."""
    global _INSERT_HIGHLIGHT_COLOR, _HOVER_COLOR
    global _LABEL_BG_COLOR, _LABEL_BORDER_COLOR, _LABEL_TEXT_COLOR
    global _PREVIEW_BG_COLOR, _PREVIEW_BORDER_COLOR, _PREVIEW_TEXT_COLOR

    if _INSERT_HIGHLIGHT_COLOR is not None:
        return  # Already initialized

    cc = Theme.get_canvas_colors()
    _INSERT_HIGHLIGHT_COLOR = _hex_to_qcolor(cc.wire_insert_highlight)
    _HOVER_COLOR = _hex_to_qcolor(cc.wire_hover)
    _LABEL_BG_COLOR = _hex_to_qcolor(cc.label_bg)
    _LABEL_BG_COLOR.setAlpha(200)
    _LABEL_BORDER_COLOR = _hex_to_qcolor(cc.label_border)
    _LABEL_TEXT_COLOR = _hex_to_qcolor(cc.label_text)
    _PREVIEW_BG_COLOR = _hex_to_qcolor(cc.preview_bg)
    _PREVIEW_BG_COLOR.setAlpha(230)
    _PREVIEW_BORDER_COLOR = _hex_to_qcolor(cc.preview_border)
    _PREVIEW_TEXT_COLOR = _hex_to_qcolor(cc.preview_text)


# ============================================================================
# PHANTOM VALUES (Last Execution State)
# ============================================================================
# Show last known values on output wires after execution completes.
# Semi-transparent text appears above wires showing what data passed through.

_PHANTOM_FONT = QFont("Consolas", 8)
_PHANTOM_FONT.setWeight(QFont.Weight.Medium)
_PHANTOM_BG_ALPHA = 140  # Semi-transparent background
_PHANTOM_TEXT_ALPHA = 200  # Semi-transparent text

# Global toggle for phantom values
_show_phantom_values: bool = True


def set_show_phantom_values(enabled: bool) -> None:
    """Enable or disable phantom values globally."""
    global _show_phantom_values
    _show_phantom_values = enabled


def get_show_phantom_values() -> bool:
    """Check if phantom values are enabled."""
    return _show_phantom_values


# ============================================================================
# EXECUTION FLOW ANIMATION CONSTANTS
# ============================================================================
# Animation settings for the flowing dot during execution.
# The dot travels continuously along the wire path while the connected node executes.

# Animation timing
_ANIMATION_INTERVAL_MS = 16  # ~60fps for smooth animation
_ANIMATION_INTERVAL_MS_SLOW = 50  # ~20fps for high performance mode (reduces CPU load)
_ANIMATION_CYCLE_MS = 500  # One full cycle (dot travels wire length) in 500ms
_ANIMATION_STEP = _ANIMATION_INTERVAL_MS / _ANIMATION_CYCLE_MS  # Progress per tick
_ANIMATION_STEP_SLOW = _ANIMATION_INTERVAL_MS_SLOW / _ANIMATION_CYCLE_MS  # Progress per tick (slow)

# Completion glow duration
_COMPLETION_GLOW_MS = 300  # Brief glow effect when execution completes

# Flow dot visual settings
_FLOW_DOT_RADIUS = 4.0  # Base radius of the flowing dot
_FLOW_DOT_GLOW_RADIUS = 8.0  # Glow radius around the dot

# Flow colors - lazily initialized from theme
_FLOW_DOT_COLOR = None
_FLOW_DOT_GLOW_COLOR = None
_COMPLETION_GLOW_COLOR = None


def _init_flow_colors():
    """Initialize flow animation colors from theme."""
    global _FLOW_DOT_COLOR, _FLOW_DOT_GLOW_COLOR, _COMPLETION_GLOW_COLOR

    if _FLOW_DOT_COLOR is not None:
        return  # Already initialized

    cc = Theme.get_canvas_colors()
    _FLOW_DOT_COLOR = _hex_to_qcolor(cc.wire_flow_dot)
    _FLOW_DOT_COLOR.setAlpha(220)
    _FLOW_DOT_GLOW_COLOR = _hex_to_qcolor(cc.wire_flow_glow)
    _COMPLETION_GLOW_COLOR = _hex_to_qcolor(cc.wire_completion_glow)


# ============================================================================
# TYPE-COLORED WIRE SYSTEM - Now from unified theme
# ============================================================================
# Wire colors match data types for visual identification (like Unreal Blueprints).
# Colors are sourced from Theme.get_wire_qcolor() for consistency.

# TYPE_WIRE_COLORS is built lazily from theme to avoid circular imports
TYPE_WIRE_COLORS: dict[DataType, QColor] = {}
_EXEC_WIRE_COLOR = None
_DEFAULT_WIRE_COLOR = None
_INCOMPATIBLE_WIRE_COLOR = None


def _init_wire_colors():
    """Initialize wire colors from unified theme."""
    global TYPE_WIRE_COLORS, _EXEC_WIRE_COLOR, _DEFAULT_WIRE_COLOR, _INCOMPATIBLE_WIRE_COLOR

    if _EXEC_WIRE_COLOR is not None:
        return  # Already initialized

    cc = Theme.get_canvas_colors()

    # Build TYPE_WIRE_COLORS from theme
    TYPE_WIRE_COLORS.update(
        {
            DataType.STRING: _hex_to_qcolor(cc.wire_string),
            DataType.INTEGER: _hex_to_qcolor(cc.wire_integer),
            DataType.FLOAT: _hex_to_qcolor(cc.wire_float),
            DataType.BOOLEAN: _hex_to_qcolor(cc.wire_boolean),
            DataType.LIST: _hex_to_qcolor(cc.wire_list),
            DataType.DICT: _hex_to_qcolor(cc.wire_dict),
            DataType.PAGE: _hex_to_qcolor(cc.wire_page),
            DataType.ELEMENT: _hex_to_qcolor(cc.wire_element),
            DataType.BROWSER: _hex_to_qcolor(cc.wire_page),
            DataType.WINDOW: _hex_to_qcolor(cc.wire_window),
            DataType.DESKTOP_ELEMENT: _hex_to_qcolor(cc.wire_desktop_element),
            DataType.DB_CONNECTION: _hex_to_qcolor(cc.wire_db_connection),
            DataType.WORKBOOK: _hex_to_qcolor(cc.wire_workbook),
            DataType.WORKSHEET: _hex_to_qcolor(cc.wire_worksheet),
            DataType.DOCUMENT: _hex_to_qcolor(cc.wire_document),
            DataType.OBJECT: _hex_to_qcolor(cc.wire_any),
            DataType.ANY: _hex_to_qcolor(cc.wire_any),
        }
    )

    _EXEC_WIRE_COLOR = _hex_to_qcolor(cc.wire_exec)
    _DEFAULT_WIRE_COLOR = _hex_to_qcolor(cc.wire_default)
    _INCOMPATIBLE_WIRE_COLOR = _hex_to_qcolor(cc.wire_incompatible)


# Wire thickness constants (dimensions, not colors - keep as-is)
WIRE_THICKNESS = {
    "exec": 3.0,  # Execution - most prominent
    "data_active": 2.0,  # Data that was used during execution
    "data_idle": 1.5,  # Default data connections
    "optional": 1.0,  # Optional connections (not implemented yet)
}


def get_type_wire_color(data_type: DataType | None) -> QColor:
    """
    Get wire color for a data type from unified theme.

    Args:
        data_type: The DataType enum value, or None for execution ports

    Returns:
        QColor for the wire (cached from theme)
    """
    _init_wire_colors()  # Ensure colors are initialized

    if data_type is None:
        # Execution port
        return _EXEC_WIRE_COLOR
    return TYPE_WIRE_COLORS.get(data_type, _DEFAULT_WIRE_COLOR)


def check_type_compatibility(source_type: DataType | None, target_type: DataType | None) -> bool:
    """
    Check if two port types are compatible for connection.

    Args:
        source_type: DataType of source port (None for exec)
        target_type: DataType of target port (None for exec)

    Returns:
        True if connection is allowed
    """
    # Both exec - always compatible
    if source_type is None and target_type is None:
        return True

    # Mixed exec/data - never compatible
    if (source_type is None) != (target_type is None):
        return False

    # Check type compatibility using port type registry
    try:
        from casare_rpa.application.services.port_type_service import (
            get_port_type_registry,
        )

        registry = get_port_type_registry()
        return registry.is_compatible(source_type, target_type)
    except Exception:
        # On error, allow connection (permissive fallback)
        return True


class CasarePipe(PipeItem):
    """
    Custom pipe with:
    - Solid style with lighter color when being dragged
    - Type-colored wires (like Unreal Blueprints)
    - Variable thickness by port type
    - Optional data type label on the connection
    - Output preview on hover
    - Insert highlight when node is dragged over
    - Connection compatibility feedback during drag
    - Execution flow animation (continuous dot animation during execution)
    - Smart wire routing with bezier obstacle avoidance
    """

    def __init__(self):
        """Initialize custom pipe."""
        super().__init__()
        self._show_label = True
        self._label_text = ""
        self._output_value = None
        self._show_output_preview = False
        self._hovered = False
        self._insert_highlight = False  # Highlight when node dragged over

        # Type-colored wire caching (computed once per connection)
        self._cached_wire_color: QColor | None = None
        self._cached_wire_thickness: float = WIRE_THICKNESS["data_idle"]
        self._is_exec_connection: bool = False

        # Connection compatibility feedback
        self._is_incompatible: bool = False

        # ============================================================
        # EXECUTION FLOW ANIMATION STATE
        # ============================================================
        # Animation progress: 0.0 = at source, 1.0 = at target
        self._animation_progress: float = 0.0
        # Whether animation is currently running
        self._is_animating: bool = False
        # Brief glow effect after completion
        self._show_completion_glow: bool = False
        # Timer for animation updates (created lazily to avoid overhead)
        self._animation_timer: QTimer | None = None
        # Per-instance step (kept for future extensions)
        self._animation_step: float = _ANIMATION_STEP

        # ============================================================
        # SMART WIRE ROUTING STATE
        # ============================================================
        # Cached routed control points (invalidated on node move)
        self._routed_ctrl1: QPointF | None = None
        self._routed_ctrl2: QPointF | None = None
        # Hash of last positions to detect when to recalculate
        self._last_position_hash: int = 0

        # ============================================================
        # PHANTOM VALUES STATE
        # ============================================================
        # Last known value that passed through this wire (persists after execution)
        self._phantom_value: str | None = None
        # Whether phantom value has been set (vs. never executed)
        self._has_phantom: bool = False

        # Endpoint overrides for collapsed frames
        # Maps PortItem -> QGraphicsItem (the visual proxy)
        self._endpoint_overrides = {}

        # Enable hover events
        self.setAcceptHoverEvents(True)

    # =========================================================================
    # EXECUTION FLOW ANIMATION METHODS
    # =========================================================================

    def start_flow_animation(self) -> None:
        """
        Start continuous flow animation.

        Call this when the source node starts execution to show
        data flowing along the wire.

        PERFORMANCE: Uses slower animation interval (50ms vs 16ms) when
        high performance mode is enabled to reduce CPU load from multiple
        animating pipes.
        """
        if self._is_animating:
            return  # Already animating

        self._is_animating = True
        self._animation_progress = 0.0
        self._show_completion_glow = False

        # Use slower animation in high performance mode
        is_high_perf = get_high_performance_mode()
        self._animation_step = _ANIMATION_STEP_SLOW if is_high_perf else _ANIMATION_STEP
        interval_ms = _ANIMATION_INTERVAL_MS_SLOW if is_high_perf else _ANIMATION_INTERVAL_MS

        # Create timer lazily
        if self._animation_timer is None:
            self._animation_timer = QTimer()
            self._animation_timer.timeout.connect(self._on_animation_tick)

        self._animation_timer.start(interval_ms)
        logger.debug(f"Pipe animation started for connection: {self} (interval={interval_ms}ms)")
        self.update()

    def stop_flow_animation(self, show_completion_glow: bool = True) -> None:
        """
        Stop animation with optional brief glow effect.

        Args:
            show_completion_glow: If True, show brief green glow on completion
        """
        if self._animation_timer is not None:
            self._animation_timer.stop()

        self._is_animating = False
        self._animation_progress = 0.0

        if show_completion_glow:
            # Show brief completion glow
            self._show_completion_glow = True
            QTimer.singleShot(_COMPLETION_GLOW_MS, self._clear_completion_glow)

        self.update()
        logger.debug(f"Pipe animation stopped for connection: {self}")

    def _clear_completion_glow(self) -> None:
        """Clear the completion glow effect."""
        self._show_completion_glow = False
        self.update()

    def _on_animation_tick(self) -> None:
        """
        Animation timer callback.

        Advances the animation progress and triggers repaint.
        """
        if not self._is_animating:
            return

        self._animation_progress += self._animation_step
        if self._animation_progress >= 1.0:
            self._animation_progress = 0.0  # Loop back to start

        self.update()

    def is_animating(self) -> bool:
        """Check if flow animation is currently active."""
        return self._is_animating

    def _draw_flow_dot(self, painter: QPainter) -> None:
        """
        Draw the animated flow dot traveling along the wire.

        The dot appears as a glowing white circle that moves from
        source to target port continuously during execution.

        Args:
            painter: QPainter to draw with
        """
        if not self._is_animating:
            return

        _init_flow_colors()

        path = self.path()
        if path.isEmpty():
            return

        # Get position along the path
        try:
            pos = path.pointAtPercent(self._animation_progress)
        except Exception:
            return

        # Draw glow behind the dot (subtle)
        glow_gradient = QRadialGradient(pos, _FLOW_DOT_GLOW_RADIUS)
        glow_gradient.setColorAt(0, _FLOW_DOT_GLOW_COLOR)
        glow_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(pos, _FLOW_DOT_GLOW_RADIUS, _FLOW_DOT_GLOW_RADIUS)

        # Draw solid dot (use wire color during pulses for higher contrast)
        painter.setBrush(QBrush(_FLOW_DOT_COLOR))
        painter.drawEllipse(pos, _FLOW_DOT_RADIUS, _FLOW_DOT_RADIUS)

    def _draw_completion_glow(self, painter: QPainter) -> None:
        """
        Draw brief completion glow effect along the entire wire.

        This provides visual feedback when execution completes successfully.

        Args:
            painter: QPainter to draw with
        """
        if not self._show_completion_glow:
            return

        _init_flow_colors()

        path = self.path()
        if path.isEmpty():
            return

        # Draw glowing wire on completion
        glow_pen = QPen(_COMPLETION_GLOW_COLOR, self._get_wire_thickness() + 4)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(path)

    def _draw_phantom_value(self, painter: QPainter) -> None:
        """
        Draw the phantom value (last known value) above the wire.

        Semi-transparent text appears near the output port showing what
        data last passed through this connection. Turns the static graph
        into a snapshot of the last execution state.

        Args:
            painter: QPainter to draw with
        """
        if not _show_phantom_values or not self._has_phantom or not self._phantom_value:
            return

        path = self.path()
        if path.isEmpty():
            return

        # Position at 20% along the path (near source port)
        try:
            pos = path.pointAtPercent(0.20)
        except Exception:
            return

        # Setup font
        painter.setFont(_PHANTOM_FONT)

        # Calculate text bounds
        fm = QFontMetrics(_PHANTOM_FONT)
        text_rect = fm.boundingRect(self._phantom_value)
        padding = 3

        # Position above the wire
        bg_rect = QRectF(
            pos.x() - text_rect.width() / 2 - padding,
            pos.y() - text_rect.height() - 8 - padding,  # 8px above wire
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2,
        )

        # Get wire color for tinting
        wire_color = self._get_wire_color()

        # Semi-transparent background (use theme dark background)
        cc = Theme.get_canvas_colors()
        bg_color = _hex_to_qcolor(cc.background)
        bg_color.setAlpha(_PHANTOM_BG_ALPHA)
        painter.setBrush(QBrush(bg_color))

        # Border matches wire color but semi-transparent
        border_color = QColor(wire_color)
        border_color.setAlpha(_PHANTOM_BG_ALPHA)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(bg_rect, 3, 3)

        # Text in wire color but semi-transparent
        text_color = QColor(wire_color)
        text_color.setAlpha(_PHANTOM_TEXT_ALPHA)
        painter.setPen(QPen(text_color))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, self._phantom_value)

    def set_phantom_value(self, value: any) -> None:
        """
        Set the phantom value (last execution result) for this wire.

        Args:
            value: The value that passed through this connection
        """
        if value is None:
            self._phantom_value = None
            self._has_phantom = False
        else:
            # Format the value for display
            try:
                str_val = str(value)
                # Truncate long values
                if len(str_val) > 30:
                    str_val = str_val[:27] + "..."
                self._phantom_value = str_val
                self._has_phantom = True
            except Exception:
                self._phantom_value = "<value>"
                self._has_phantom = True
        self.update()

    def clear_phantom_value(self) -> None:
        """Clear the phantom value."""
        self._phantom_value = None
        self._has_phantom = False
        self.update()

    def has_phantom_value(self) -> bool:
        """Check if this wire has a phantom value."""
        return self._has_phantom

    def _get_port_data_type(self) -> DataType | None:
        """
        Get the DataType from the output port.

        Returns:
            DataType enum value, or None for execution ports
        """
        if not self.output_port:
            return DataType.ANY

        try:
            # Get the node from the output port
            node = self.output_port.node()
            if not node:
                return DataType.ANY

            # Get port type from node's _port_types dict
            port_name = self.output_port.name()
            if hasattr(node, "_port_types"):
                # CRITICAL FIX: Check if key EXISTS before getting value
                # Previously used .get() which returns None for both:
                # - Exec ports (intentionally set to None)
                # - Missing keys (port not registered)
                # Both cases were treated as exec ports, making all wires white
                if port_name in node._port_types:
                    # Key exists - return its value (None for exec, DataType for data)
                    return node._port_types[port_name]
                # Key doesn't exist - fall through to name-based detection

            # Check if it's an exec port by name
            if port_name and ("exec" in port_name.lower()):
                return None  # Execution port

            return DataType.ANY
        except Exception:
            return DataType.ANY

    def _compute_wire_color_and_thickness(self) -> tuple[QColor, float]:
        """
        Compute wire color and thickness based on output port data type.

        Caches the result for performance.

        Returns:
            Tuple of (QColor, thickness)
        """
        data_type = self._get_port_data_type()

        # Get color based on type
        wire_color = get_type_wire_color(data_type)

        # Get thickness based on whether it's exec or data
        if data_type is None:
            # Execution wire - thick white
            thickness = WIRE_THICKNESS["exec"]
            self._is_exec_connection = True
        else:
            # Data wire - normal thickness
            thickness = WIRE_THICKNESS["data_idle"]
            self._is_exec_connection = False

        return wire_color, thickness

    def _get_wire_color(self) -> QColor:
        """
        Get the wire color for this connection.

        Uses cached value if available, otherwise computes it.

        Returns:
            QColor for the wire
        """
        # Return incompatible color if connection is invalid
        if self._is_incompatible:
            return _INCOMPATIBLE_WIRE_COLOR

        # Use cached color if available
        if self._cached_wire_color is not None:
            return self._cached_wire_color

        # Compute and cache
        self._cached_wire_color, self._cached_wire_thickness = (
            self._compute_wire_color_and_thickness()
        )
        return self._cached_wire_color

    def _get_wire_thickness(self) -> float:
        """
        Get the wire thickness for this connection.

        Uses cached value if available.

        Returns:
            Thickness in pixels
        """
        # Ensure color/thickness are computed
        if self._cached_wire_color is None:
            self._cached_wire_color, self._cached_wire_thickness = (
                self._compute_wire_color_and_thickness()
            )
        return self._cached_wire_thickness

    def invalidate_cache(self) -> None:
        """
        Invalidate cached wire color/thickness.

        Call this when the connection changes.
        """
        self._cached_wire_color = None
        self._cached_wire_thickness = WIRE_THICKNESS["data_idle"]
        self._is_exec_connection = False
        # Also invalidate routed path cache
        self._routed_ctrl1 = None
        self._routed_ctrl2 = None
        self._last_position_hash = 0

    # =========================================================================
    # SMART WIRE ROUTING METHODS
    # =========================================================================

    def invalidate_routing_cache(self) -> None:
        """
        Invalidate the smart routing cache.

        Call this when nodes move and paths need recalculation.
        """
        self._routed_ctrl1 = None
        self._routed_ctrl2 = None
        self._last_position_hash = 0

    def _calculate_position_hash(self, pos1: QPointF, pos2: QPointF) -> int:
        """Calculate hash of endpoint positions for cache invalidation."""
        return hash(
            (
                round(pos1.x(), 1),
                round(pos1.y(), 1),
                round(pos2.x(), 1),
                round(pos2.y(), 1),
            )
        )

    def _get_smart_routed_path(
        self,
        pos1: QPointF,
        pos2: QPointF,
    ) -> QPainterPath:
        """
        Calculate bezier path with smart obstacle avoidance.

        Uses SmartRouter to find control points that route around nodes.
        Caches result for performance.

        Args:
            pos1: Start position (source port)
            pos2: End position (target port)

        Returns:
            QPainterPath with routed bezier curve
        """
        # Check if we need to recalculate
        current_hash = self._calculate_position_hash(pos1, pos2)

        if (
            self._routed_ctrl1 is not None
            and self._routed_ctrl2 is not None
            and self._last_position_hash == current_hash
        ):
            # Use cached control points
            path = QPainterPath()
            path.moveTo(pos1)
            path.cubicTo(self._routed_ctrl1, self._routed_ctrl2, pos2)
            return path

        # Calculate new routed path
        try:
            from casare_rpa.presentation.canvas.connections.smart_routing import (
                get_routing_manager,
            )

            manager = get_routing_manager()
            if manager and manager.is_enabled():
                # Get source and target node IDs for exclusion
                source_node_id = None
                target_node_id = None

                if self.output_port and hasattr(self.output_port, "node"):
                    node = self.output_port.node()
                    if node and hasattr(node, "id"):
                        source_node_id = node.id

                if self.input_port and hasattr(self.input_port, "node"):
                    node = self.input_port.node()
                    if node and hasattr(node, "id"):
                        target_node_id = node.id

                # Calculate routed path
                p0, ctrl1, ctrl2, p3 = manager.calculate_path(
                    pos1, pos2, source_node_id, target_node_id
                )

                # Cache the control points
                self._routed_ctrl1 = ctrl1
                self._routed_ctrl2 = ctrl2
                self._last_position_hash = current_hash

                path = QPainterPath()
                path.moveTo(p0)
                path.cubicTo(ctrl1, ctrl2, p3)
                return path

        except ImportError:
            pass  # Smart routing not available
        except Exception:
            pass  # Fall through to standard path

        # Fallback: standard bezier path (same as NodeGraphQt)
        return self._get_standard_bezier_path(pos1, pos2)

    def _get_standard_bezier_path(
        self,
        pos1: QPointF,
        pos2: QPointF,
    ) -> QPainterPath:
        """
        Calculate standard bezier path without obstacle avoidance.

        This matches NodeGraphQt's default behavior for curved pipes.

        Args:
            pos1: Start position
            pos2: End position

        Returns:
            QPainterPath with standard bezier curve
        """
        path = QPainterPath()
        path.moveTo(pos1)

        # Calculate control points (horizontal offset like NodeGraphQt)
        dx = pos2.x() - pos1.x()
        tangent = abs(dx)

        # Limit tangent based on port node width (approximate)
        max_tangent = 150.0  # Default max
        tangent = min(tangent, max_tangent)

        # Control points offset horizontally
        ctrl1 = QPointF(pos1.x() + tangent, pos1.y())
        ctrl2 = QPointF(pos2.x() - tangent, pos2.y())

        path.cubicTo(ctrl1, ctrl2, pos2)
        return path

    def draw_path(self, start_port, end_port=None, cursor_pos=None):
        """
        Draw the connection path with optional smart routing.

        Overrides NodeGraphQt's draw_path to add smart routing capability.
        When smart routing is enabled, calculates bezier control points
        that route around node obstacles.

        Args:
            start_port: Port used to draw the starting point
            end_port: Port used to draw the end point
            cursor_pos: Cursor position for live connection dragging
        """
        if not start_port:
            return

        # Check if viewer is available - prevents crash during loading/undo
        viewer = self.viewer()
        if viewer is None and not cursor_pos:
            return

        # Get start position (handle override)
        start_override = self._endpoint_overrides.get(start_port)
        if start_override:
            pos1 = start_override.sceneBoundingRect().center()
        else:
            pos1 = start_port.scenePos()
            pos1.setX(pos1.x() + (start_port.boundingRect().width() / 2))
            pos1.setY(pos1.y() + (start_port.boundingRect().height() / 2))

        # Get end position (handle override)
        if cursor_pos:
            pos2 = cursor_pos
        elif end_port:
            end_override = self._endpoint_overrides.get(end_port)
            if end_override:
                pos2 = end_override.sceneBoundingRect().center()
            else:
                pos2 = end_port.scenePos()
                pos2.setX(pos2.x() + (end_port.boundingRect().width() / 2))
                pos2.setY(pos2.y() + (end_port.boundingRect().height() / 2))
        else:
            return

        # Visibility check removed: caused connected pipes to disappear
        # This check was too aggressive and hid pipes when ports returned isVisible()=False
        # which happens in some valid states. Standard NodeGraphQt handles visibility.

        # Use smart routing for completed connections (not live dragging)
        # and only when smart routing is globally enabled
        if is_smart_routing_enabled() and self.input_port and self.output_port and not cursor_pos:
            # Use smart routed path
            path = self._get_smart_routed_path(pos1, pos2)
            self.setPath(path)
            self._draw_direction_pointer()
            return

        # If we have overrides, we MUST calculate the path ourselves because
        # super().draw_path() will use the ports' positions, ignoring our overrides.
        if start_override or (end_port and self._endpoint_overrides.get(end_port)):
            path = self._get_standard_bezier_path(pos1, pos2)
            self.setPath(path)
            self._draw_direction_pointer()
            return

        # Fall back to parent implementation for live dragging
        # or when smart routing is disabled AND no overrides are present
        super().draw_path(start_port, end_port, cursor_pos)

    def set_incompatible(self, incompatible: bool) -> None:
        """
        Set whether this connection is incompatible (for drag feedback).

        Args:
            incompatible: True if connection types don't match
        """
        if self._is_incompatible != incompatible:
            self._is_incompatible = incompatible
            self.update()

    def is_incompatible(self) -> bool:
        """Check if connection is marked as incompatible."""
        return self._is_incompatible

    def check_target_compatibility(self, target_port) -> bool:
        """
        Check if the current drag source is compatible with a target port.

        Used during connection dragging to provide visual feedback.

        Args:
            target_port: The potential target input port

        Returns:
            True if connection would be valid
        """
        if not self.output_port or not target_port:
            return True  # Can't check - assume compatible

        try:
            # Get source node and type
            source_node = self.output_port.node()
            target_node = target_port.node()

            if not source_node or not target_node:
                return True

            # Same node - not compatible
            if source_node == target_node:
                return False

            # Get port types
            source_type = self._get_port_data_type()

            # Get target port type
            target_type: DataType | None = None
            if hasattr(target_node, "_port_types"):
                target_type = target_node._port_types.get(target_port.name())

            # Check compatibility
            return check_type_compatibility(source_type, target_type)

        except Exception:
            return True  # On error, assume compatible

    def update_compatibility_for_target(self, target_port) -> None:
        """
        Update the incompatible state based on a target port.

        Call this during drag to update visual feedback.

        Args:
            target_port: The potential target port (or None to clear)
        """
        if target_port is None:
            self.set_incompatible(False)
        else:
            is_compatible = self.check_target_compatibility(target_port)
            self.set_incompatible(not is_compatible)

    def _paint_lod(self, painter: QPainter, lod_level: LODLevel = LODLevel.LOW) -> None:
        """
        Paint simplified LOD version for low zoom levels.

        PERFORMANCE: At low zoom levels, skip bezier curves, antialiasing,
        labels, and previews. Draw simple straight lines instead.
        Still uses type-colored wires for visual consistency.

        Args:
            lod_level: The LOD level (ULTRA_LOW or LOW)
        """
        path = self.path()

        # Handle empty path - fall back to parent's paint for live dragging
        if path.isEmpty():
            # During live dragging, path may be incomplete - let parent handle it
            super().paint(painter, None, None)
            return

        # Use LOD manager to determine antialiasing
        lod_manager = get_lod_manager()
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing, lod_manager.should_use_antialiasing()
        )

        # Use type-colored wire even in LOD mode
        wire_color = self._get_wire_color()

        # ULTRA_LOW: Thinner line, no type distinction
        if lod_level == LODLevel.ULTRA_LOW:
            pen = QPen(wire_color, 1)
        else:
            # LOW: Keep type-based thickness but simplified
            pen = QPen(wire_color, max(1.0, self._get_wire_thickness() * 0.75))

        # Draw standard solid lines for connections (live or complete)
        is_live = not self.input_port or not self.output_port

        # Completion glow (keep in LOD for feedback)
        if self._show_completion_glow:
            self._draw_completion_glow(painter)

        if is_live:
            # Make live connection more visible at low zoom
            live_pen = QPen(pen)
            try:
                live_color = QColor(live_pen.color()).lighter(150)
                live_color.setAlpha(255)
                live_pen.setColor(live_color)
            except Exception:
                pass
            live_pen.setWidthF(max(live_pen.widthF(), 2.5))
            live_pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(live_pen)
            painter.drawPath(path)
        else:
            # Solid line for complete connections
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            # Draw straight line from start to end instead of bezier path
            try:
                start = path.pointAtPercent(0)
                end = path.pointAtPercent(1)
                painter.drawLine(start, end)
            except Exception:
                painter.drawPath(path)

        # Flow dot (keep in LOW LOD so pulses remain visible in high performance mode)
        if self._is_animating and lod_level != LODLevel.ULTRA_LOW:
            self._draw_flow_dot(painter)

    def paint(self, painter, option, widget):
        """
        Paint the pipe with custom styling.

        Features:
        - Type-colored wires based on output port DataType
        - Variable thickness (exec=3px, data=1.5px)
        - High-contrast lines for incompatible connections during drag
        - LOD rendering at low zoom levels

        PERFORMANCE: Uses centralized LOD manager to determine rendering detail.
        The LOD level is computed once per frame (in viewport update timer),
        not per-pipe. This eliminates redundant zoom calculations.

        HIGH PERFORMANCE MODE: When enabled, forces LOD rendering at all
        zoom levels for maximum performance with large workflows.
        """
        # Get LOD level from centralized manager (computed once per frame)
        lod_manager = get_lod_manager()
        lod_level = lod_manager.current_lod

        # HIGH PERFORMANCE MODE: Force LOD rendering at all zoom levels
        if get_high_performance_mode():
            self._paint_lod(painter, LODLevel.LOW)
            return

        # LOD check - at low zoom, render simplified version
        if lod_level in (LODLevel.ULTRA_LOW, LODLevel.LOW):
            self._paint_lod(painter, lod_level)
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get type-based wire color and thickness
        wire_color = self._get_wire_color()
        wire_thickness = self._get_wire_thickness()

        # Check if this is a live connection (being dragged)
        is_live = not self.input_port or not self.output_port

        # Draw completion glow first (behind the wire)
        if self._show_completion_glow:
            self._draw_completion_glow(painter)

        if is_live:
            # Connection is being dragged - use lighter solid line for contrast
            if self._is_incompatible:
                pen = QPen(_INCOMPATIBLE_WIRE_COLOR, wire_thickness)
            else:
                live_color = QColor(wire_color).lighter(150)
                live_color.setAlpha(255)
                pen = QPen(live_color, wire_thickness)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPath(self.path())
        else:
            # Connection is complete - use solid line with type color
            # Priority: insert highlight > hover > type-colored
            if self._insert_highlight:
                pen = QPen(_INSERT_HIGHLIGHT_COLOR, wire_thickness + 2)
            elif self._hovered:
                hover_color = QColor(wire_color)
                hover_color = hover_color.lighter(130)
                pen = QPen(hover_color, wire_thickness + 0.5)
            else:
                pen = QPen(wire_color, wire_thickness)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPath(self.path())

        # Draw flow animation dot (during execution)
        if self._is_animating:
            self._draw_flow_dot(painter)

        # Draw label if enabled and connection is complete
        # PERFORMANCE: Only draw labels at FULL LOD
        if self._show_label and self.input_port and self.output_port:
            if lod_manager.should_render_labels():
                self._draw_label(painter)

        # Draw output preview on hover
        # PERFORMANCE: Only draw preview at FULL LOD
        if self._hovered and self._output_value is not None:
            if lod_manager.should_render_labels():
                self._draw_output_preview(painter)

        # Draw phantom value (last execution state) when not animating
        # Show at HIGH and FULL LOD levels for better visibility
        if not self._is_animating and self.input_port and self.output_port:
            current_lod = lod_manager.get_lod_level()
            if current_lod in (LODLevel.HIGH, LODLevel.FULL, LODLevel.EXPANDED):
                self._draw_phantom_value(painter)

    def _draw_label(self, painter: QPainter) -> None:
        """Draw the data type label on the connection."""
        if not self._label_text:
            # Try to get label from port data type
            self._label_text = self._get_port_type_label()

        if not self._label_text:
            return

        # Calculate midpoint of the path
        path = self.path()
        if path.isEmpty():
            return

        # Get midpoint along the path
        midpoint = path.pointAtPercent(0.5)

        # Setup font (using cached font)
        painter.setFont(_LABEL_FONT)

        # Calculate text bounds
        fm = QFontMetrics(_LABEL_FONT)
        text_rect = fm.boundingRect(self._label_text)
        padding = 4

        # Background rectangle
        bg_rect = QRectF(
            midpoint.x() - text_rect.width() / 2 - padding,
            midpoint.y() - text_rect.height() / 2 - padding,
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2,
        )

        # Draw background (using cached colors)
        painter.setBrush(QBrush(_LABEL_BG_COLOR))
        painter.setPen(QPen(_LABEL_BORDER_COLOR, 1))
        painter.drawRoundedRect(bg_rect, 3, 3)

        # Draw text (using cached color)
        painter.setPen(QPen(_LABEL_TEXT_COLOR))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, self._label_text)

    def _draw_output_preview(self, painter: QPainter) -> None:
        """Draw the output value preview near the connection."""
        if self._output_value is None:
            return

        # Format the output value
        value_str = self._format_output_value(self._output_value)
        if not value_str:
            return

        # Calculate position near the source port
        path = self.path()
        if path.isEmpty():
            return

        # Position near the start (25% along the path)
        pos = path.pointAtPercent(0.25)

        # Setup font (using cached font)
        painter.setFont(_PREVIEW_FONT)

        # Calculate text bounds
        fm = QFontMetrics(_PREVIEW_FONT)
        text_rect = fm.boundingRect(value_str)
        padding = 6

        # Background rectangle
        bg_rect = QRectF(
            pos.x() + 10,
            pos.y() - text_rect.height() / 2 - padding,
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2,
        )

        # Draw background with slight yellow tint (using cached colors)
        painter.setBrush(QBrush(_PREVIEW_BG_COLOR))
        painter.setPen(QPen(_PREVIEW_BORDER_COLOR, 1))
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Draw text (using cached color)
        painter.setPen(QPen(_PREVIEW_TEXT_COLOR))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, value_str)

    def _get_port_type_label(self) -> str:
        """Get the data type label from the source port."""
        if not self.output_port:
            return ""

        try:
            # Get the node
            node = self.output_port.node()
            if not node:
                return ""

            # Get port type from node if available
            port_name = self.output_port.name()
            if hasattr(node, "_port_types"):
                data_type = node._port_types.get(port_name)
                if data_type:
                    return data_type.value if hasattr(data_type, "value") else str(data_type)

            # Use port name as fallback
            if port_name in ("exec_out", "exec_in"):
                return ""  # Don't show label for exec ports
            return port_name
        except Exception:
            return ""

    def _format_output_value(self, value) -> str:
        """Format the output value for display."""
        if value is None:
            return ""

        try:
            str_val = str(value)
            # Truncate long strings
            if len(str_val) > 50:
                str_val = str_val[:47] + "..."
            return str_val
        except Exception:
            return ""

    def set_label(self, text: str) -> None:
        """Set the connection label text."""
        self._label_text = text
        self.update()

    def set_show_label(self, show: bool) -> None:
        """Enable or disable label display."""
        self._show_label = show
        self.update()

    def set_output_value(self, value) -> None:
        """Set the output value for preview."""
        self._output_value = value
        self.update()

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter."""
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave."""
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def set_insert_highlight(self, highlight: bool) -> None:
        """Set insert highlight state (when node is dragged over this pipe)."""
        if self._insert_highlight != highlight:
            self._insert_highlight = highlight
            self.update()

    def is_insert_highlighted(self) -> bool:
        """Check if pipe is currently insert-highlighted."""
        return self._insert_highlight

    def set_endpoint_override(self, port, item) -> None:
        """
        Override the visual position of a port with another item.

        Used when nodes are collapsed inside a frame, allowing the pipe
        to connect to the frame's edge indicator instead of the hidden port.

        Args:
            port: The PortItem to override
            item: The QGraphicsItem (e.g. ExposedPortIndicator) to use as visual anchor
        """
        self._endpoint_overrides[port] = item
        # Force visible if we are overriding (since the original port might be hidden)
        self.setVisible(True)
        # Force path redraw
        self.draw_path(self.input_port, self.output_port)

    def clear_endpoint_override(self, port) -> None:
        """
        Clear visual override for a port.

        Args:
            port: The PortItem to clear override for
        """
        if port in self._endpoint_overrides:
            del self._endpoint_overrides[port]
            # Redraw with original ports
            self.draw_path(self.input_port, self.output_port)


# Global setting to enable/disable connection labels
_show_connection_labels = True


def set_show_connection_labels(show: bool) -> None:
    """Enable or disable connection labels globally."""
    global _show_connection_labels
    _show_connection_labels = show


def get_show_connection_labels() -> bool:
    """Check if connection labels are enabled."""
    return _show_connection_labels


class CasareLivePipe(LivePipeItem):
    """
    Custom LivePipeItem that fixes:
    1. draw_index_pointer text_pos bug (undefined when layout_direction is None)
    """

    def paint(self, painter, option, widget):
        """
        Paint method for live connection dragging (uses solid line).
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = self.pen()
        path = self.path()

        # Use solid line style
        pen.setStyle(Qt.PenStyle.SolidLine)

        # Determine thickness based on port type if possible
        # Exec ports are 3.0, Data ports are 1.5
        thickness = 1.5

        # In NodeGraphQt, LivePipeItem doesn't always have _start_port exposed nicely.
        # But we can check if the width already looks like an exec wire (from pen setup)
        if pen.widthF() > 2.0:
            thickness = 3.0

        pen.setWidthF(thickness)

        painter.setPen(pen)

        if not path.isEmpty():
            painter.drawPath(path)

        painter.restore()

    def draw_index_pointer(self, start_port, cursor_pos, color=None):
        """Fixed version that always initializes text_pos."""
        if start_port is None:
            return

        # Set text first so boundingRect is correct for positioning
        self._idx_text.setPlainText(f"{start_port.name}")
        text_rect = self._idx_text.boundingRect()

        transform = QTransform()
        transform.translate(cursor_pos.x(), cursor_pos.y())

        layout_dir = self.viewer_layout_direction()

        # FIXED: Always initialize text_pos with default value
        text_pos = (
            cursor_pos.x() - (text_rect.width() / 2),
            cursor_pos.y() - (text_rect.height() * 1.25),
        )

        # Use == instead of 'is' for reliable enum comparison
        if layout_dir == LayoutDirectionEnum.VERTICAL.value:
            text_pos = (
                cursor_pos.x() + (text_rect.width() / 2.5),
                cursor_pos.y() - (text_rect.height() / 2),
            )
            if start_port.port_type == PortTypeEnum.OUT.value:
                transform.rotate(180)
        elif layout_dir == LayoutDirectionEnum.HORIZONTAL.value:
            text_pos = (
                cursor_pos.x() - (text_rect.width() / 2),
                cursor_pos.y() - (text_rect.height() * 1.25),
            )
            if start_port.port_type == PortTypeEnum.IN.value:
                transform.rotate(-90)
            else:
                transform.rotate(90)

        self._idx_text.setPos(*text_pos)
        self._idx_pointer.setPolygon(transform.map(self._poly))

        pen_color = QColor(*PipeEnum.HIGHLIGHT_COLOR.value)
        if isinstance(color, list | tuple):
            pen_color = QColor(*color)

        pen = self._idx_pointer.pen()
        pen.setColor(pen_color)
        self._idx_pointer.setBrush(pen_color.darker(300))
        self._idx_pointer.setPen(pen)
