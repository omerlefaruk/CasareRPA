"""
Recording Review Dialog.

Dialog for reviewing and editing recorded browser actions before adding to canvas.
Allows reordering, editing parameters, setting wait times, and deleting actions.
"""

from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QWidget,
    QFrame,
    QScrollArea,
)

from loguru import logger
from PySide6.QtWidgets import QDialog


# Node type display configuration
NODE_DISPLAY_CONFIG = {
    "ClickElementNode": {"name": "Click Element", "icon": "pointer"},
    "TypeTextNode": {"name": "Type Text", "icon": "keyboard"},
    "PressEnterNode": {"name": "Press Enter", "icon": "corner-down-left"},
    "SelectDropdownNode": {"name": "Select Option", "icon": "chevron-down"},
    "SelectOptionNode": {"name": "Select Option", "icon": "chevron-down"},
    "CheckboxNode": {"name": "Toggle Checkbox", "icon": "check-square"},
    "SendHotKeyNode": {"name": "Send Hotkey", "icon": "command"},
}


class ActionRowWidget(QFrame):
    """
    Widget representing a single recorded action row.

    Features:
    - Drag handle for reordering
    - Node type display
    - Editable selector/text field
    - Wait time spinner
    - Delete button
    """

    delete_requested = Signal(object)  # Emits self when delete clicked

    def __init__(
        self, action_data: Dict[str, Any], index: int, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize action row widget.

        Args:
            action_data: The recorded action data dictionary
            index: Row index for display
            parent: Parent widget
        """
        super().__init__(parent)

        self.action_data = action_data.copy()
        self.index = index

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setObjectName("actionRow")

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the row user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # Drag handle
        self._drag_handle = QLabel("\u2261")  # Triple horizontal bar
        self._drag_handle.setObjectName("dragHandle")
        self._drag_handle.setFixedWidth(20)
        self._drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_handle.setToolTip("Drag to reorder")
        layout.addWidget(self._drag_handle)

        # Node type label
        node_type = self.action_data.get("node_type", "Unknown")
        display_info = NODE_DISPLAY_CONFIG.get(node_type, {"name": node_type, "icon": "circle"})

        self._type_label = QLabel(display_info["name"])
        self._type_label.setObjectName("nodeTypeLabel")
        self._type_label.setFixedWidth(120)
        layout.addWidget(self._type_label)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setObjectName("separator")
        layout.addWidget(sep1)

        # Parameter field (selector or text)
        config = self.action_data.get("config", {})

        # Determine which parameter to show
        if "selector" in config:
            param_value = config.get("selector", "")
            param_placeholder = "CSS/XPath selector..."
            self._param_key = "selector"
        elif "text" in config:
            param_value = config.get("text", "")
            param_placeholder = "Text to type..."
            self._param_key = "text"
        elif "key" in config:
            param_value = config.get("key", "")
            param_placeholder = "Key combination..."
            self._param_key = "key"
        else:
            param_value = ""
            param_placeholder = "Parameter..."
            self._param_key = None

        self._param_input = QLineEdit(str(param_value))
        self._param_input.setPlaceholderText(param_placeholder)
        self._param_input.setObjectName("paramInput")
        self._param_input.textChanged.connect(self._on_param_changed)
        self._param_input.setToolTip(str(param_value) if len(str(param_value)) > 40 else "")
        layout.addWidget(self._param_input, stretch=1)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setObjectName("separator")
        layout.addWidget(sep2)

        # Wait time spinner
        wait_layout = QHBoxLayout()
        wait_layout.setSpacing(4)

        self._wait_spinner = QSpinBox()
        self._wait_spinner.setRange(0, 10000)
        self._wait_spinner.setValue(config.get("wait_after", 500))
        self._wait_spinner.setSuffix(" ms")
        self._wait_spinner.setObjectName("waitSpinner")
        self._wait_spinner.setFixedWidth(90)
        self._wait_spinner.setToolTip("Wait time after action (milliseconds)")
        self._wait_spinner.valueChanged.connect(self._on_wait_changed)
        wait_layout.addWidget(self._wait_spinner)

        layout.addLayout(wait_layout)

        # Delete button
        self._delete_btn = QPushButton("\u2715")  # X symbol
        self._delete_btn.setObjectName("deleteButton")
        self._delete_btn.setFixedSize(28, 28)
        self._delete_btn.setToolTip("Remove this action")
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self._delete_btn)

    def _apply_styles(self) -> None:
        """Apply styling to the row."""
        self.setStyleSheet("""
            QFrame#actionRow {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QFrame#actionRow:hover {
                border-color: #4a4a4d;
                background-color: #333336;
            }
            QLabel#dragHandle {
                color: #666666;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#dragHandle:hover {
                color: #888888;
            }
            QLabel#nodeTypeLabel {
                color: #4a9eff;
                font-weight: bold;
                font-size: 12px;
            }
            QFrame#separator {
                background-color: #3c3c3c;
            }
            QLineEdit#paramInput {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 4px 8px;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            QLineEdit#paramInput:focus {
                border-color: #007acc;
            }
            QSpinBox#waitSpinner {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 2px 4px;
                color: #d4d4d4;
            }
            QSpinBox#waitSpinner:focus {
                border-color: #007acc;
            }
            QPushButton#deleteButton {
                background-color: transparent;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                color: #888888;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#deleteButton:hover {
                background-color: #f44336;
                border-color: #f44336;
                color: white;
            }
            QPushButton#deleteButton:pressed {
                background-color: #d32f2f;
            }
        """)

    def _on_param_changed(self, text: str) -> None:
        """Handle parameter field change."""
        if self._param_key and "config" in self.action_data:
            self.action_data["config"][self._param_key] = text

    def _on_wait_changed(self, value: int) -> None:
        """Handle wait time change."""
        if "config" not in self.action_data:
            self.action_data["config"] = {}
        self.action_data["config"]["wait_after"] = value

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        self.delete_requested.emit(self)

    def get_action_data(self) -> Dict[str, Any]:
        """Get the current action data."""
        return self.action_data

    def set_wait_time(self, value: int) -> None:
        """Set the wait time value."""
        self._wait_spinner.setValue(value)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for drag initiation."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on drag handle area
            handle_rect = self._drag_handle.geometry()
            if handle_rect.contains(event.pos()):
                self._start_drag(event)
                return
        super().mousePressEvent(event)

    def _start_drag(self, event) -> None:
        """Start drag operation."""

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.index))
        drag.setMimeData(mime_data)

        # Create drag pixmap - use grab() instead of render()
        pixmap = self.grab()
        # Make semi-transparent
        transparent_pixmap = QPixmap(pixmap.size())
        transparent_pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(transparent_pixmap)
        painter.setOpacity(0.7)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        drag.setPixmap(transparent_pixmap)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)


class RecordingReviewDialog(QDialog):
    """
    Dialog for reviewing recorded browser actions before adding to canvas.

    Features:
    - Display all recorded actions in an editable list
    - Drag-and-drop reordering
    - Edit selectors/text parameters
    - Set wait times between actions
    - Delete unwanted actions

    Signals:
        accepted_with_data: Emitted when user clicks Add to Canvas
                           (nodes_data: list, include_waits: bool)
    """

    accepted_with_data = Signal(list, bool)

    def __init__(
        self, recorded_nodes: List[Dict[str, Any]], parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize recording review dialog.

        Args:
            recorded_nodes: List of node data dictionaries from workflow generator
            parent: Parent widget
        """
        super().__init__(parent)

        self._recorded_nodes = [node.copy() for node in recorded_nodes]
        self._action_rows: List[ActionRowWidget] = []

        self.setWindowTitle("Review Recorded Actions")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._load_actions()
        self._apply_styles()

        logger.info(f"RecordingReviewDialog opened with {len(recorded_nodes)} actions")

    def _setup_ui(self) -> None:
        """Set up the dialog user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title_label = QLabel("Review Recorded Actions")
        title_label.setObjectName("dialogTitle")
        header_layout.addWidget(title_label)

        self._info_label = QLabel(
            f"Recorded {len(self._recorded_nodes)} actions. "
            "Edit parameters before adding to canvas."
        )
        self._info_label.setObjectName("infoLabel")
        header_layout.addWidget(self._info_label)

        layout.addLayout(header_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("headerSeparator")
        layout.addWidget(sep)

        # Actions list area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("actionsScrollArea")
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._actions_container = QWidget()
        self._actions_layout = QVBoxLayout(self._actions_container)
        self._actions_layout.setContentsMargins(0, 0, 8, 0)
        self._actions_layout.setSpacing(8)
        self._actions_layout.addStretch()

        scroll_area.setWidget(self._actions_container)
        layout.addWidget(scroll_area, stretch=1)

        # Wait time controls
        wait_frame = QFrame()
        wait_frame.setObjectName("waitControlsFrame")
        wait_layout = QHBoxLayout(wait_frame)
        wait_layout.setContentsMargins(8, 8, 8, 8)

        self._add_waits_checkbox = QCheckBox("Add wait times between actions")
        self._add_waits_checkbox.setChecked(True)
        self._add_waits_checkbox.setObjectName("addWaitsCheckbox")
        self._add_waits_checkbox.toggled.connect(self._on_add_waits_toggled)
        wait_layout.addWidget(self._add_waits_checkbox)

        wait_layout.addStretch()

        default_wait_label = QLabel("Default wait:")
        default_wait_label.setObjectName("defaultWaitLabel")
        wait_layout.addWidget(default_wait_label)

        self._default_wait_spinner = QSpinBox()
        self._default_wait_spinner.setRange(0, 10000)
        self._default_wait_spinner.setValue(500)
        self._default_wait_spinner.setSuffix(" ms")
        self._default_wait_spinner.setObjectName("defaultWaitSpinner")
        self._default_wait_spinner.setFixedWidth(100)
        self._default_wait_spinner.setToolTip("Default wait time for all actions")
        wait_layout.addWidget(self._default_wait_spinner)

        apply_default_btn = QPushButton("Apply to All")
        apply_default_btn.setObjectName("applyDefaultButton")
        apply_default_btn.setToolTip("Apply default wait time to all actions")
        apply_default_btn.clicked.connect(self._apply_default_wait_to_all)
        wait_layout.addWidget(apply_default_btn)

        layout.addWidget(wait_frame)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setObjectName("footerSeparator")
        layout.addWidget(sep2)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancelButton")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._add_btn = QPushButton("Add to Canvas")
        self._add_btn.setObjectName("addButton")
        self._add_btn.setDefault(True)
        self._add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self._add_btn)

        layout.addLayout(button_layout)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _apply_styles(self) -> None:
        """Apply dark theme styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLabel#dialogTitle {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#infoLabel {
                color: #888888;
                font-size: 12px;
            }
            QFrame#headerSeparator, QFrame#footerSeparator {
                background-color: #3c3c3c;
                max-height: 1px;
            }
            QScrollArea#actionsScrollArea {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QScrollArea#actionsScrollArea > QWidget > QWidget {
                background-color: #252526;
            }
            QFrame#waitControlsFrame {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QCheckBox#addWaitsCheckbox {
                color: #d4d4d4;
                font-size: 12px;
            }
            QCheckBox#addWaitsCheckbox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox#addWaitsCheckbox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
            }
            QCheckBox#addWaitsCheckbox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
                border-radius: 3px;
            }
            QLabel#defaultWaitLabel {
                color: #888888;
                font-size: 12px;
            }
            QSpinBox#defaultWaitSpinner {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 4px 8px;
                color: #d4d4d4;
            }
            QSpinBox#defaultWaitSpinner:focus {
                border-color: #007acc;
            }
            QPushButton#applyDefaultButton {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px 12px;
                color: #d4d4d4;
            }
            QPushButton#applyDefaultButton:hover {
                background-color: #4a4a4d;
                border-color: #6c6c6c;
            }
            QPushButton#cancelButton {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 8px 20px;
                color: #d4d4d4;
                font-size: 12px;
            }
            QPushButton#cancelButton:hover {
                background-color: #4a4a4d;
                border-color: #6c6c6c;
            }
            QPushButton#addButton {
                background-color: #0e639c;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#addButton:hover {
                background-color: #1177bb;
            }
            QPushButton#addButton:pressed {
                background-color: #094771;
            }
            QPushButton#addButton:disabled {
                background-color: #3c3c3c;
                color: #666666;
            }
            QScrollBar:vertical {
                background-color: #252526;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #5c5c5c;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c6c6c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def _load_actions(self) -> None:
        """Load actions into the list."""
        # Clear existing rows
        for row in self._action_rows:
            row.deleteLater()
        self._action_rows.clear()

        # Create rows for each action
        for i, node_data in enumerate(self._recorded_nodes):
            row = ActionRowWidget(node_data, i, self._actions_container)
            row.delete_requested.connect(self._on_row_delete_requested)

            # Insert before the stretch
            self._actions_layout.insertWidget(
                self._actions_layout.count() - 1,  # Before stretch
                row,
            )
            self._action_rows.append(row)

        self._update_info_label()
        self._update_add_button_state()

    def _update_info_label(self) -> None:
        """Update the info label with current action count."""
        count = len(self._action_rows)
        if count == 0:
            self._info_label.setText("No actions recorded. Close this dialog to cancel.")
        elif count == 1:
            self._info_label.setText("1 action recorded. Edit parameters before adding to canvas.")
        else:
            self._info_label.setText(
                f"{count} actions recorded. Edit parameters before adding to canvas."
            )

    def _update_add_button_state(self) -> None:
        """Update the Add to Canvas button state."""
        self._add_btn.setEnabled(len(self._action_rows) > 0)

    def _on_row_delete_requested(self, row: ActionRowWidget) -> None:
        """Handle row deletion request."""
        if row in self._action_rows:
            index = self._action_rows.index(row)
            self._action_rows.remove(row)
            self._recorded_nodes.pop(index)
            row.deleteLater()

            # Update indices for remaining rows
            for i, remaining_row in enumerate(self._action_rows):
                remaining_row.index = i

            self._update_info_label()
            self._update_add_button_state()

            logger.debug(f"Removed action at index {index}, {len(self._action_rows)} remaining")

    def _on_add_waits_toggled(self, checked: bool) -> None:
        """Handle add waits checkbox toggle."""
        self._default_wait_spinner.setEnabled(checked)
        # Enable/disable wait spinners in rows
        for row in self._action_rows:
            row._wait_spinner.setEnabled(checked)

    def _apply_default_wait_to_all(self) -> None:
        """Apply default wait time to all action rows."""
        default_wait = self._default_wait_spinner.value()
        for row in self._action_rows:
            row.set_wait_time(default_wait)
        logger.debug(f"Applied default wait time {default_wait}ms to all actions")

    def _on_add_clicked(self) -> None:
        """Handle Add to Canvas button click."""
        # Collect final node data from rows
        nodes_data = []
        for row in self._action_rows:
            node_data = row.get_action_data()
            nodes_data.append(node_data)

        include_waits = self._add_waits_checkbox.isChecked()

        logger.info(
            f"Adding {len(nodes_data)} actions to canvas " f"(include_waits={include_waits})"
        )

        self.accepted_with_data.emit(nodes_data, include_waits)
        self.accept()

    def get_nodes_data(self) -> List[Dict[str, Any]]:
        """
        Get the final list of node data.

        Returns:
            List of node data dictionaries with user edits applied
        """
        return [row.get_action_data() for row in self._action_rows]

    def get_include_waits(self) -> bool:
        """
        Get whether to include wait times.

        Returns:
            True if wait times should be included
        """
        return self._add_waits_checkbox.isChecked()

    # Drag and drop support
    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move event."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Handle drop event for reordering."""
        if not event.mimeData().hasText():
            return

        try:
            source_index = int(event.mimeData().text())
        except ValueError:
            return

        # Find drop target index
        drop_pos = event.position().toPoint()
        target_index = self._find_drop_target_index(drop_pos)

        if target_index == -1 or source_index == target_index:
            return

        # Reorder
        self._reorder_action(source_index, target_index)
        event.acceptProposedAction()

    def _find_drop_target_index(self, pos) -> int:
        """Find the target index for a drop at the given position."""
        # Map position to scroll area content
        scroll_area = self.findChild(QScrollArea, "actionsScrollArea")
        if not scroll_area:
            return -1

        content_pos = scroll_area.widget().mapFrom(self, pos)

        for i, row in enumerate(self._action_rows):
            row_rect = row.geometry()
            row_center_y = row_rect.y() + row_rect.height() // 2

            if content_pos.y() < row_center_y:
                return i

        return len(self._action_rows) - 1

    def _reorder_action(self, from_index: int, to_index: int) -> None:
        """Reorder an action from one index to another."""
        if from_index == to_index:
            return

        # Reorder data
        node_data = self._recorded_nodes.pop(from_index)
        self._recorded_nodes.insert(to_index, node_data)

        # Reorder row widgets
        row = self._action_rows.pop(from_index)
        self._action_rows.insert(to_index, row)

        # Update layout
        self._actions_layout.removeWidget(row)
        self._actions_layout.insertWidget(to_index, row)

        # Update indices
        for i, r in enumerate(self._action_rows):
            r.index = i

        logger.debug(f"Reordered action from {from_index} to {to_index}")
