"""
CasareRPA - Parameter Drop Zone
Drop zone widget for creating snippet parameters by dragging node properties.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QPainter, QColor, QPen, QDragEnterEvent, QDropEvent
from loguru import logger


class ParameterDropZone(QWidget):
    """
    Drop zone for creating snippet parameters from node properties.

    Usage:
    - When inside a snippet, this widget appears at the top of the canvas
    - Drag a property from any node's properties panel
    - Drop it here to expose as a snippet parameter

    Signals:
        parameter_requested: Emitted when user drops a property (node_id, property_key, property_type)
    """

    parameter_requested = Signal(str, str, str, object)  # node_id, property_key, data_type, current_value

    def __init__(self, parent=None):
        """Initialize the parameter drop zone."""
        super().__init__(parent)

        # Setup UI
        self._setup_ui()

        # Drag state
        self._is_dragging = False

        # Enable drops
        self.setAcceptDrops(True)

        logger.debug("ParameterDropZone initialized")

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Label
        self.label = QLabel("📌 Drag property here to expose as snippet parameter")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # VSCode Dark+ styling
        self.setStyleSheet("""
            ParameterDropZone {
                background: #1E1E1E;
                border: 2px dashed #3E3E42;
                border-radius: 4px;
            }
            QLabel {
                color: #858585;
                font-size: 12px;
                padding: 8px;
            }
        """)

        layout.addWidget(self.label)
        self.setFixedHeight(40)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - check if it's a property drag."""
        mime_data = event.mimeData()

        # Check if it's a property drag (we'll define this format)
        if mime_data.hasFormat("application/x-casare-property"):
            event.acceptProposedAction()
            self._is_dragging = True
            self._update_style(True)
            logger.debug("Property drag entered drop zone")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave - restore normal appearance."""
        self._is_dragging = False
        self._update_style(False)

    def dropEvent(self, event: QDropEvent):
        """Handle drop - create parameter from property."""
        mime_data = event.mimeData()

        if not mime_data.hasFormat("application/x-casare-property"):
            event.ignore()
            return

        # Parse property data (format: "node_id|property_key|data_type|current_value")
        try:
            data_str = bytes(mime_data.data("application/x-casare-property")).decode('utf-8')
            parts = data_str.split('|', 3)  # Split into max 4 parts

            if len(parts) >= 3:
                node_id = parts[0]
                property_key = parts[1]
                data_type = parts[2]
                current_value = parts[3] if len(parts) > 3 else None

                logger.info(f"Property dropped: {node_id}.{property_key} (type: {data_type})")

                # Emit signal to request parameter creation
                self.parameter_requested.emit(node_id, property_key, data_type, current_value)

                event.acceptProposedAction()
            else:
                logger.warning(f"Invalid property data format: {data_str}")
                event.ignore()

        except Exception as e:
            logger.exception(f"Error parsing dropped property: {e}")
            event.ignore()

        finally:
            self._is_dragging = False
            self._update_style(False)

    def _update_style(self, is_active: bool):
        """Update visual style based on drag state."""
        if is_active:
            # Highlight during drag
            self.setStyleSheet("""
                ParameterDropZone {
                    background: #264F78;
                    border: 2px dashed #007ACC;
                    border-radius: 4px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-size: 12px;
                    padding: 8px;
                    font-weight: bold;
                }
            """)
        else:
            # Normal appearance
            self.setStyleSheet("""
                ParameterDropZone {
                    background: #1E1E1E;
                    border: 2px dashed #3E3E42;
                    border-radius: 4px;
                }
                QLabel {
                    color: #858585;
                    font-size: 12px;
                    padding: 8px;
                }
            """)

    def set_visible_for_snippet(self, is_inside_snippet: bool):
        """Show/hide based on whether we're inside a snippet."""
        self.setVisible(is_inside_snippet)
        if is_inside_snippet:
            logger.debug("Parameter drop zone shown (inside snippet)")
        else:
            logger.debug("Parameter drop zone hidden (root workflow)")
