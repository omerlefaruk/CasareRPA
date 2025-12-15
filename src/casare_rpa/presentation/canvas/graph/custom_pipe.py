"""
Custom pipe styling for node connections.

Provides:
- Dotted line style when dragging connections
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

from typing import Optional
from PySide6.QtCore import Qt, QRectF, QTimer, QPointF
from PySide6.QtGui import (
    QPen,
    QFont,
    QFontMetrics,
    QColor,
    QPainter,
    QPainterPath,
    QBrush,
    QRadialGradient,
)
from NodeGraphQt.qgraphics.pipe import PipeItem

# Import high performance mode flag from custom_node_item
from casare_rpa.presentation.canvas.graph.custom_node_item import (
    get_high_performance_mode,
)

# Import LOD manager for centralized zoom-based rendering decisions
from casare_rpa.presentation.canvas.graph.lod_manager import (
    get_lod_manager,
    LODLevel,
)

# Import DataType for type-based coloring
from casare_rpa.domain.value_objects.types import DataType

# Import unified theme system
from casare_rpa.presentation.canvas.ui.theme import Theme, _hex_to_qcolor


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
# EXECUTION FLOW ANIMATION CONSTANTS
# ============================================================================
# Animation settings for the flowing dot during execution.
# The dot travels continuously along the wire path while the connected node executes.

# Animation timing
_ANIMATION_INTERVAL_MS = 16  # ~60fps for smooth animation
_ANIMATION_CYCLE_MS = 500  # One full cycle (dot travels wire length) in 500ms
_ANIMATION_STEP = _ANIMATION_INTERVAL_MS / _ANIMATION_CYCLE_MS  # Progress per tick

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
    global \
        TYPE_WIRE_COLORS, \
        _EXEC_WIRE_COLOR, \
        _DEFAULT_WIRE_COLOR, \
        _INCOMPATIBLE_WIRE_COLOR

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


def get_type_wire_color(data_type: Optional[DataType]) -> QColor:
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


def check_type_compatibility(
    source_type: Optional[DataType], target_type: Optional[DataType]
) -> bool:
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


# ============================================================================
# OPENGL-COMPATIBLE DASHED LINE DRAWING
# ============================================================================
# Qt's DashLine pen style doesn't render correctly with OpenGL viewport.
# This helper draws dashed lines manually using line segments.

_DASH_LENGTH = 8.0  # Length of each dash segment
_GAP_LENGTH = 6.0  # Length of gap between dashes


def _draw_dashed_path(painter: QPainter, path: QPainterPath, pen: QPen) -> None:
    """
    Draw a path with dashed line style (OpenGL compatible).

    Instead of using QPen.DashLine (which doesn't work with OpenGL),
    this draws the path as a series of short line segments.

    Args:
        painter: QPainter to draw with
        path: The path to draw
        pen: Pen to use (solid style will be used)
    """
    if path.isEmpty():
        return

    # Use solid pen for manual dash drawing
    solid_pen = QPen(pen)
    solid_pen.setStyle(Qt.PenStyle.SolidLine)
    painter.setPen(solid_pen)

    # Get path length
    path_length = path.length()
    if path_length < 1:
        return

    # Draw dashes along the path
    segment_length = _DASH_LENGTH + _GAP_LENGTH
    current_pos = 0.0

    while current_pos < path_length:
        # Calculate dash start and end positions
        dash_start = current_pos
        dash_end = min(current_pos + _DASH_LENGTH, path_length)

        # Get points along the path
        start_percent = dash_start / path_length
        end_percent = dash_end / path_length

        try:
            start_point = path.pointAtPercent(start_percent)
            end_point = path.pointAtPercent(end_percent)
            painter.drawLine(start_point, end_point)
        except Exception:
            pass

        # Move to next segment (dash + gap)
        current_pos += segment_length


class CasarePipe(PipeItem):
    """
    Custom pipe with:
    - Dotted style when being dragged
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
        self._cached_wire_color: Optional[QColor] = None
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
        self._animation_timer: Optional[QTimer] = None

        # ============================================================
        # SMART WIRE ROUTING STATE
        # ============================================================
        # Cached routed control points (invalidated on node move)
        self._routed_ctrl1: Optional[QPointF] = None
        self._routed_ctrl2: Optional[QPointF] = None
        # Hash of last positions to detect when to recalculate
        self._last_position_hash: int = 0

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
        """
        if self._is_animating:
            return  # Already animating

        self._is_animating = True
        self._animation_progress = 0.0
        self._show_completion_glow = False

        # Create timer lazily
        if self._animation_timer is None:
            self._animation_timer = QTimer()
            self._animation_timer.timeout.connect(self._on_animation_tick)

        self._animation_timer.start(_ANIMATION_INTERVAL_MS)
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

        self._animation_progress += _ANIMATION_STEP
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

        # Draw solid dot
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

        path = self.path()
        if path.isEmpty():
            return

        # Draw glowing wire on completion
        glow_pen = QPen(_COMPLETION_GLOW_COLOR, self._get_wire_thickness() + 4)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(path)

    def _get_port_data_type(self) -> Optional[DataType]:
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

        # Get start position (center of port)
        pos1 = start_port.scenePos()
        pos1.setX(pos1.x() + (start_port.boundingRect().width() / 2))
        pos1.setY(pos1.y() + (start_port.boundingRect().height() / 2))

        # Get end position
        if cursor_pos:
            pos2 = cursor_pos
        elif end_port:
            pos2 = end_port.scenePos()
            pos2.setX(pos2.x() + (start_port.boundingRect().width() / 2))
            pos2.setY(pos2.y() + (start_port.boundingRect().height() / 2))
        else:
            return

        # Visibility check removed: caused connected pipes to disappear
        # This check was too aggressive and hid pipes when ports returned isVisible()=False
        # which happens in some valid states. Standard NodeGraphQt handles visibility.

        # Use smart routing for completed connections (not live dragging)
        # and only when smart routing is globally enabled
        if (
            is_smart_routing_enabled()
            and self.input_port
            and self.output_port
            and not cursor_pos
        ):
            # Use smart routed path
            path = self._get_smart_routed_path(pos1, pos2)
            self.setPath(path)
            self._draw_direction_pointer()
            return

        # Fall back to parent implementation for live dragging
        # or when smart routing is disabled
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
            target_type: Optional[DataType] = None
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

        # Draw dashed for live connections, solid for complete
        is_live = not self.input_port or not self.output_port

        if is_live:
            # Use OpenGL-compatible manual dashed line drawing
            _draw_dashed_path(painter, path, pen)
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

    def paint(self, painter, option, widget):
        """
        Paint the pipe with custom styling.

        Features:
        - Type-colored wires based on output port DataType
        - Variable thickness (exec=3px, data=1.5px)
        - Dashed line for incompatible connections during drag
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
            # Connection is being dragged - use OpenGL-compatible dashed line
            if self._is_incompatible:
                pen = QPen(_INCOMPATIBLE_WIRE_COLOR, wire_thickness)
            else:
                pen = QPen(wire_color, wire_thickness)
            _draw_dashed_path(painter, self.path(), pen)
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
                    return (
                        data_type.value
                        if hasattr(data_type, "value")
                        else str(data_type)
                    )

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


# Global setting to enable/disable connection labels
_show_connection_labels = True


def set_show_connection_labels(show: bool) -> None:
    """Enable or disable connection labels globally."""
    global _show_connection_labels
    _show_connection_labels = show


def get_show_connection_labels() -> bool:
    """Check if connection labels are enabled."""
    return _show_connection_labels
