"""
CasareRPA - Property Drag Enabler
Patches NodeGraphQt property widgets to support dragging properties to create snippet parameters.
"""

from typing import Optional
from PySide6.QtCore import Qt, QMimeData, QByteArray
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QWidget
from loguru import logger

try:
    from NodeGraphQt.widgets.node_widgets import (
        NodeLineEdit,
        NodeComboBox,
        NodeCheckBox,
        _NodeGroupBox
    )
    HAS_NODE_WIDGETS = True
except ImportError:
    HAS_NODE_WIDGETS = False
    logger.warning("NodeGraphQt widgets not available - property drag disabled")


def enable_property_dragging():
    """
    Enable drag-drop support for NodeGraphQt property widgets.

    Patches property widgets to:
    - Detect drag gesture (mouse press + move with threshold)
    - Create MIME data with property information
    - Start QDrag operation to allow dropping on ParameterDropZone
    """
    if not HAS_NODE_WIDGETS:
        logger.warning("Cannot enable property dragging - NodeGraphQt widgets not available")
        return

    # Track drag state
    _drag_state = {
        "start_pos": None,
        "widget": None,
        "node_id": None,
        "property_key": None,
        "data_type": None,
        "current_value": None
    }

    def _get_node_id(widget: QWidget) -> Optional[str]:
        """Get node ID from property widget hierarchy."""
        # Walk up the widget hierarchy to find the node item
        parent = widget
        while parent:
            # Check if parent is a NodeItem or has _node attribute
            if hasattr(parent, 'id'):
                return parent.id
            if hasattr(parent, '_node') and hasattr(parent._node, 'id'):
                return parent._node.id()
            parent = parent.parent() if hasattr(parent, 'parent') else None
        return None

    def _get_property_info(widget) -> tuple:
        """Get property key, data type, and current value from widget."""
        property_key = getattr(widget, 'name', None) or getattr(widget, '_name', 'unknown')

        # Determine data type and get current value
        if isinstance(widget, NodeLineEdit):
            data_type = "string"
            current_value = widget.get_value() if hasattr(widget, 'get_value') else ""
        elif isinstance(widget, NodeComboBox):
            data_type = "enum"
            current_value = widget.get_value() if hasattr(widget, 'get_value') else ""
        elif isinstance(widget, NodeCheckBox):
            data_type = "boolean"
            current_value = widget.get_value() if hasattr(widget, 'get_value') else False
        else:
            data_type = "unknown"
            current_value = None

        return property_key, data_type, current_value

    # =========================================================================
    # Patch NodeLineEdit for drag support
    # =========================================================================
    if hasattr(NodeLineEdit, 'mousePressEvent'):
        _original_line_press = NodeLineEdit.mousePressEvent

        def patched_line_press(self, event):
            """Store drag start position."""
            if event.button() == Qt.MouseButton.LeftButton:
                _drag_state["start_pos"] = event.pos()
                _drag_state["widget"] = self
            _original_line_press(self, event)

        NodeLineEdit.mousePressEvent = patched_line_press

    if hasattr(NodeLineEdit, 'mouseMoveEvent'):
        _original_line_move = NodeLineEdit.mouseMoveEvent

        def patched_line_move(self, event):
            """Start drag operation if drag threshold exceeded."""
            if (event.buttons() == Qt.MouseButton.LeftButton and
                _drag_state["start_pos"] is not None and
                _drag_state["widget"] == self):

                # Check if drag threshold exceeded
                drag_distance = (event.pos() - _drag_state["start_pos"]).manhattanLength()
                if drag_distance < 10:  # Threshold to distinguish drag from click
                    _original_line_move(self, event)
                    return

                # Get node and property info
                node_id = _get_node_id(self)
                if not node_id:
                    logger.warning("Cannot drag property - node ID not found")
                    _original_line_move(self, event)
                    return

                property_key, data_type, current_value = _get_property_info(self)

                logger.debug(f"Starting drag: {node_id}.{property_key} (type: {data_type})")

                # Create MIME data
                mime_data = QMimeData()
                data_str = f"{node_id}|{property_key}|{data_type}|{current_value}"
                mime_data.setData("application/x-casare-property", QByteArray(data_str.encode('utf-8')))

                # Start drag operation
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.CopyAction)

                # Clear drag state
                _drag_state["start_pos"] = None
                _drag_state["widget"] = None

                return

            _original_line_move(self, event)

        NodeLineEdit.mouseMoveEvent = patched_line_move

    # =========================================================================
    # Patch NodeComboBox for drag support
    # =========================================================================
    if hasattr(NodeComboBox, 'mousePressEvent'):
        _original_combo_press = NodeComboBox.mousePressEvent

        def patched_combo_press(self, event):
            """Store drag start position."""
            if event.button() == Qt.MouseButton.LeftButton:
                _drag_state["start_pos"] = event.pos()
                _drag_state["widget"] = self
            _original_combo_press(self, event)

        NodeComboBox.mousePressEvent = patched_combo_press

    if hasattr(NodeComboBox, 'mouseMoveEvent'):
        _original_combo_move = NodeComboBox.mouseMoveEvent

        def patched_combo_move(self, event):
            """Start drag operation if drag threshold exceeded."""
            if (event.buttons() == Qt.MouseButton.LeftButton and
                _drag_state["start_pos"] is not None and
                _drag_state["widget"] == self):

                # Check if drag threshold exceeded
                drag_distance = (event.pos() - _drag_state["start_pos"]).manhattanLength()
                if drag_distance < 10:
                    _original_combo_move(self, event)
                    return

                # Get node and property info
                node_id = _get_node_id(self)
                if not node_id:
                    logger.warning("Cannot drag property - node ID not found")
                    _original_combo_move(self, event)
                    return

                property_key, data_type, current_value = _get_property_info(self)

                logger.debug(f"Starting drag: {node_id}.{property_key} (type: {data_type})")

                # Create MIME data
                mime_data = QMimeData()
                data_str = f"{node_id}|{property_key}|{data_type}|{current_value}"
                mime_data.setData("application/x-casare-property", QByteArray(data_str.encode('utf-8')))

                # Start drag operation
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.CopyAction)

                # Clear drag state
                _drag_state["start_pos"] = None
                _drag_state["widget"] = None

                return

            _original_combo_move(self, event)

        NodeComboBox.mouseMoveEvent = patched_combo_move

    # =========================================================================
    # Patch NodeCheckBox for drag support
    # =========================================================================
    if hasattr(NodeCheckBox, 'mousePressEvent'):
        _original_check_press = NodeCheckBox.mousePressEvent

        def patched_check_press(self, event):
            """Store drag start position."""
            if event.button() == Qt.MouseButton.LeftButton:
                _drag_state["start_pos"] = event.pos()
                _drag_state["widget"] = self
            _original_check_press(self, event)

        NodeCheckBox.mousePressEvent = patched_check_press

    if hasattr(NodeCheckBox, 'mouseMoveEvent'):
        _original_check_move = NodeCheckBox.mouseMoveEvent

        def patched_check_move(self, event):
            """Start drag operation if drag threshold exceeded."""
            if (event.buttons() == Qt.MouseButton.LeftButton and
                _drag_state["start_pos"] is not None and
                _drag_state["widget"] == self):

                # Check if drag threshold exceeded
                drag_distance = (event.pos() - _drag_state["start_pos"]).manhattanLength()
                if drag_distance < 10:
                    _original_check_move(self, event)
                    return

                # Get node and property info
                node_id = _get_node_id(self)
                if not node_id:
                    logger.warning("Cannot drag property - node ID not found")
                    _original_check_move(self, event)
                    return

                property_key, data_type, current_value = _get_property_info(self)

                logger.debug(f"Starting drag: {node_id}.{property_key} (type: {data_type})")

                # Create MIME data
                mime_data = QMimeData()
                data_str = f"{node_id}|{property_key}|{data_type}|{current_value}"
                mime_data.setData("application/x-casare-property", QByteArray(data_str.encode('utf-8')))

                # Start drag operation
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.CopyAction)

                # Clear drag state
                _drag_state["start_pos"] = None
                _drag_state["widget"] = None

                return

            _original_check_move(self, event)

        NodeCheckBox.mouseMoveEvent = patched_check_move

    logger.info("Property dragging enabled for NodeGraphQt widgets")
