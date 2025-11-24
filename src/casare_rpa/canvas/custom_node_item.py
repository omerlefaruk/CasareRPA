"""
Custom node graphics item for CasareRPA.

Provides custom styling including:
- Bright yellow border on selection
- Animated running state indicator
- Completion checkmark
- Icon display
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, QTimer, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QLinearGradient, QPixmap, QFont
from NodeGraphQt.qgraphics.node_base import NodeItem
from NodeGraphQt.constants import (
    Z_VAL_NODE,
    ITEM_CACHE_MODE,
    NODE_SEL_COLOR,
    NODE_SEL_BORDER_COLOR
)


class CasareNodeItem(NodeItem):
    """
    Custom node item with enhanced visual feedback.
    
    Features:
    - Yellow border on selection
    - Animated dotted border when running
    - Checkmark overlay when completed
    - Icon display
    """
    
    def __init__(self, name='node', parent=None):
        super().__init__(name, parent)
        
        # Execution state
        self._is_running = False
        self._is_completed = False
        self._animation_offset = 0
        
        # Animation timer for running state
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_border)
        self._animation_timer.setInterval(50)  # 20 FPS
        
        # Icon
        self._icon_pixmap = None
        self._icon_item = None
        
        # Checkmark for completed state
        self._checkmark_item = None
        
        # Colors matching the reference image
        self._normal_border_color = QColor(68, 68, 68)  # Dark gray border
        self._selected_border_color = QColor(255, 215, 0)  # Bright yellow
        self._running_border_color = QColor(255, 215, 0)  # Bright yellow animated
        self._node_bg_color = QColor(45, 45, 45)  # Dark background
        
    def paint(self, painter, option, widget):
        """
        Custom paint method for the node.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Get node rectangle
        rect = self.boundingRect()
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
        
        # Draw icon if available
        if self._icon_pixmap and not self._icon_pixmap.isNull():
            icon_size = 24
            icon_x = rect.left() + 12
            icon_y = rect.top() + 12
            icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)
            painter.drawPixmap(icon_rect.toRect(), self._icon_pixmap)
        
        # Draw completion checkmark
        if self._is_completed:
            self._draw_checkmark(painter, rect)
        
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
    
    def _animate_border(self):
        """Animate the border for running state."""
        self._animation_offset += 1
        if self._animation_offset > 8:
            self._animation_offset = 0
        self.update()
    
    def set_running(self, running: bool):
        """Set node running state."""
        self._is_running = running
        if running:
            self._animation_timer.start()
        else:
            self._animation_timer.stop()
            self._animation_offset = 0
        self.update()
    
    def set_completed(self, completed: bool):
        """Set node completed state."""
        self._is_completed = completed
        self.update()
    
    def set_icon(self, pixmap: QPixmap):
        """Set node icon."""
        self._icon_pixmap = pixmap
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
