"""
Custom pipe styling for node connections.

Provides:
- Dotted line style when dragging connections
- Connection labels showing data type
- Output preview on hover
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QFont, QFontMetrics, QColor, QPainter, QBrush
from NodeGraphQt.qgraphics.pipe import PipeItem


class CasarePipe(PipeItem):
    """
    Custom pipe with:
    - Dotted style when being dragged
    - Optional data type label on the connection
    - Output preview on hover
    - Insert highlight when node is dragged over
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

        # Enable hover events
        self.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget):
        """
        Paint the pipe with custom styling.
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get current pen width
        pen_width = self.pen().widthF() if self.pen() else 2.0

        # Use dotted line when pipe is being drawn (live mode)
        if not self.input_port or not self.output_port:
            # Connection is being dragged - use dotted line
            pen = QPen(self.color, pen_width)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 4])
            painter.setPen(pen)
        else:
            # Connection is complete - use solid line
            # Priority: insert highlight > hover > normal
            if self._insert_highlight:
                # Orange highlight when node is being dragged over
                pen = QPen(QColor(255, 140, 0), pen_width + 2)
            elif self._hovered:
                pen = QPen(QColor(100, 200, 255), pen_width + 0.5)
            else:
                pen = QPen(self.color, pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)

        # Draw the path
        painter.drawPath(self.path())

        # Draw label if enabled and connection is complete
        if self._show_label and self.input_port and self.output_port:
            self._draw_label(painter)

        # Draw output preview on hover
        if self._hovered and self._output_value is not None:
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

        # Setup font
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        # Calculate text bounds
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(self._label_text)
        padding = 4

        # Background rectangle
        bg_rect = QRectF(
            midpoint.x() - text_rect.width() / 2 - padding,
            midpoint.y() - text_rect.height() / 2 - padding,
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2,
        )

        # Draw background
        painter.setBrush(QBrush(QColor(40, 40, 40, 200)))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(bg_rect, 3, 3)

        # Draw text
        painter.setPen(QPen(QColor(180, 180, 180)))
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

        # Setup font
        font = QFont("Consolas", 9)
        painter.setFont(font)

        # Calculate text bounds
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(value_str)
        padding = 6

        # Background rectangle
        bg_rect = QRectF(
            pos.x() + 10,
            pos.y() - text_rect.height() / 2 - padding,
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2,
        )

        # Draw background with slight yellow tint
        painter.setBrush(QBrush(QColor(50, 50, 40, 230)))
        painter.setPen(QPen(QColor(100, 100, 80), 1))
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Draw text
        painter.setPen(QPen(QColor(220, 220, 180)))
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
