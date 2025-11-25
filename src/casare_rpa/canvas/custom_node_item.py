"""
Custom node graphics item for CasareRPA.

Provides custom styling including:
- Bright yellow border on selection
- Animated running state indicator
- Completion checkmark
- Icon display

Now uses centralized AnimationCoordinator for performance with many nodes.

References:
- "Designing Data-Intensive Applications" - Resource pooling
"""

from typing import Set, Optional
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, QTimer, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QLinearGradient, QPixmap, QFont
from NodeGraphQt.qgraphics.node_base import NodeItem
from NodeGraphQt.constants import Z_VAL_NODE, ITEM_CACHE_MODE

from loguru import logger


# ============================================================================
# ANIMATION COORDINATOR (Centralized Timer)
# ============================================================================


class AnimationCoordinator:
    """
    Singleton coordinator for all node animations.

    Instead of each node having its own timer, this coordinator uses a
    single timer to drive all animated nodes. This significantly reduces
    CPU usage when many nodes are running simultaneously.

    Usage:
        coordinator = AnimationCoordinator.get_instance()
        coordinator.register(node_item)  # Start animating
        coordinator.unregister(node_item)  # Stop animating
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
        self._animated_nodes: Set["CasareNodeItem"] = set()
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._offset = 0
        self._interval = 50  # 20 FPS

    def register(self, node: "CasareNodeItem") -> None:
        """
        Start animating a node.

        Args:
            node: The CasareNodeItem to animate
        """
        self._animated_nodes.add(node)
        if not self._timer.isActive():
            self._timer.start(self._interval)

    def unregister(self, node: "CasareNodeItem") -> None:
        """
        Stop animating a node.

        Args:
            node: The CasareNodeItem to stop animating
        """
        self._animated_nodes.discard(node)
        if not self._animated_nodes and self._timer.isActive():
            self._timer.stop()
            self._offset = 0

    def _tick(self) -> None:
        """Update all animated nodes."""
        self._offset = (self._offset + 1) % 8

        for node in self._animated_nodes:
            node._animation_offset = self._offset
            node.update()

    @property
    def animated_count(self) -> int:
        """Get the number of currently animated nodes."""
        return len(self._animated_nodes)

    @property
    def is_running(self) -> bool:
        """Check if the animation timer is running."""
        return self._timer.isActive()


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

    def __init__(self, name='node', parent=None):
        super().__init__(name, parent)

        # Execution state
        self._is_running = False
        self._is_completed = False
        self._has_error = False
        self._execution_time_ms: Optional[float] = None
        self._animation_offset = 0

        # Use centralized animation coordinator instead of per-node timer
        # This significantly improves performance when many nodes are running
        self._animation_coordinator = AnimationCoordinator.get_instance()

        # Custom icon pixmap (separate from parent's _icon_item)
        self._custom_icon_pixmap = None

        # Colors matching the reference image
        self._normal_border_color = QColor(68, 68, 68)  # Dark gray border
        self._selected_border_color = QColor(255, 215, 0)  # Bright yellow
        self._running_border_color = QColor(255, 215, 0)  # Bright yellow animated
        self._node_bg_color = QColor(45, 45, 45)  # Dark background

        # Hide parent's text item to avoid double title
        if hasattr(self, '_text_item') and self._text_item:
            self._text_item.setVisible(False)

    def boundingRect(self) -> QRectF:
        """
        Override bounding rect to include space above for execution time badge.
        """
        rect = super().boundingRect()
        # Extend the bounding rect upward to include badge area
        if self._execution_time_ms is not None:
            return QRectF(
                rect.x(),
                rect.y() - self.BADGE_AREA_HEIGHT,
                rect.width(),
                rect.height() + self.BADGE_AREA_HEIGHT
            )
        return rect

    def _get_node_rect(self) -> QRectF:
        """Get the actual node rectangle (without badge area)."""
        return super().boundingRect()

    def paint(self, painter, option, widget):
        """
        Custom paint method for the node.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Get node rectangle (actual node area, not including badge space)
        rect = self._get_node_rect()
        border_width = 2.0
        
        # Determine border color and style
        if self._is_running:
            border_color = self._running_border_color
            border_style = Qt.PenStyle.DashLine
        elif self.selected:
            border_color = self._selected_border_color
            border_style = Qt.PenStyle.SolidLine
        else:
            border_color = self._normal_border_color
            border_style = Qt.PenStyle.SolidLine
        
        # Create rounded rectangle path
        radius = 8.0
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        
        # Fill background
        painter.fillPath(path, QBrush(self._node_bg_color))
        
        # Draw border
        pen = QPen(border_color, border_width)
        pen.setStyle(border_style)
        
        if self._is_running:
            # Animated dash pattern for running state
            pen.setDashOffset(self._animation_offset)
            pen.setDashPattern([4, 4])
        
        painter.strokePath(path, pen)
        
        # Draw custom icon if available
        if self._custom_icon_pixmap and not self._custom_icon_pixmap.isNull():
            icon_size = 24
            icon_x = rect.left() + 12
            icon_y = rect.top() + 12
            icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)
            painter.drawPixmap(icon_rect.toRect(), self._custom_icon_pixmap)
        
        # Draw status indicator (mutually exclusive - error takes precedence)
        if self._has_error:
            self._draw_error_icon(painter, rect)
        elif self._is_completed:
            self._draw_checkmark(painter, rect)

        # Draw execution time badge at bottom
        self._draw_execution_time(painter, rect)

        # Draw node text (name)
        self._draw_text(painter, rect)

        painter.restore()
    
    def _draw_checkmark(self, painter, rect):
        """Draw a checkmark in the top-right corner."""
        size = 20
        margin = 8
        x = rect.right() - size - margin
        y = rect.top() + margin
        
        # Background circle
        painter.setBrush(QBrush(QColor(76, 175, 80)))  # Green
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size/2, y + size/2), size/2, size/2)
        
        # Checkmark symbol
        painter.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw checkmark path
        check_path = QPainterPath()
        check_path.moveTo(x + size * 0.25, y + size * 0.5)
        check_path.lineTo(x + size * 0.45, y + size * 0.7)
        check_path.lineTo(x + size * 0.75, y + size * 0.3)
        painter.drawPath(check_path)

    def _draw_error_icon(self, painter, rect):
        """Draw an error X icon in the top-right corner."""
        size = 20
        margin = 8
        x = rect.right() - size - margin
        y = rect.top() + margin

        # Red circle background
        painter.setBrush(QBrush(QColor(244, 67, 54)))  # Material Red
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x + size/2, y + size/2), size/2, size/2)

        # White X symbol
        painter.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        inset = size * 0.3
        painter.drawLine(QPointF(x + inset, y + inset),
                         QPointF(x + size - inset, y + size - inset))
        painter.drawLine(QPointF(x + size - inset, y + inset),
                         QPointF(x + inset, y + size - inset))

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

        # Draw badge background (lower opacity - more transparent)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, badge_radius, badge_radius)
        painter.fillPath(badge_path, QBrush(QColor(0, 0, 0, 100)))  # Lower opacity (100 vs 160)

        # Draw text (light gray, slightly transparent)
        painter.setPen(QColor(220, 220, 220, 200))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, time_text)

    def _draw_text(self, painter, rect):
        """Draw node name text."""
        text_rect = QRectF(rect.left() + 45, rect.top() + 10, rect.width() - 55, 30)
        
        painter.setPen(QColor(220, 220, 220))  # Light gray text
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        
        # Get node name
        node_name = self.name if hasattr(self, 'name') else "Node"
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, node_name)
    
    def set_running(self, running: bool):
        """
        Set node running state.

        Uses centralized AnimationCoordinator for efficient animation.

        Args:
            running: True to show running animation, False to stop
        """
        self._is_running = running
        if running:
            self._animation_coordinator.register(self)
        else:
            self._animation_coordinator.unregister(self)
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
        """Reset all execution state for workflow restart."""
        self.prepareGeometryChange()  # Bounding rect changes when badge is removed
        self._is_running = False
        self._is_completed = False
        self._has_error = False
        self._execution_time_ms = None
        self._animation_offset = 0
        self._animation_coordinator.unregister(self)
        self.update()

    def set_icon(self, pixmap: QPixmap):
        """Set custom node icon."""
        self._custom_icon_pixmap = pixmap
        self.update()
    
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
