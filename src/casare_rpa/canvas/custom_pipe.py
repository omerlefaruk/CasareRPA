"""
Custom pipe styling for node connections.

Provides dotted line style when dragging connections.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen
from NodeGraphQt.qgraphics.pipe import Pipe


class CasarePipe(Pipe):
    """
    Custom pipe with dotted style when being dragged.
    """
    
    def paint(self, painter, option, widget):
        """
        Paint the pipe with custom styling.
        """
        # Use dotted line when pipe is being drawn (live mode)
        if not self.input_port or not self.output_port:
            # Connection is being dragged - use dotted line
            pen = QPen(self.color, self.pen_width)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 4])
            painter.setPen(pen)
        else:
            # Connection is complete - use solid line
            pen = QPen(self.color, self.pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
        
        # Draw the path
        painter.drawPath(self.path())
