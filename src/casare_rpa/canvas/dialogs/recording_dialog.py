"""
Recording Preview Dialog

Shows recorded actions and allows editing before generating workflow.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from loguru import logger


class RecordingPreviewDialog(QDialog):
    """Dialog for previewing and editing recorded actions."""

    def __init__(self, actions: list, parent=None):
        """
        Initialize recording preview dialog.

        Args:
            actions: List of recorded action dictionaries
            parent: Parent widget
        """
        super().__init__(parent)

        self.actions = actions.copy()

        self.setWindowTitle("Recording Preview")
        self.setMinimumSize(800, 500)

        self._setup_ui()
        self._load_actions()

        logger.info(f"Recording preview dialog opened with {len(actions)} actions")

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Review Recorded Actions")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(title_label)

        # Info label
        info_label = QLabel(
            f"Recorded {len(self.actions)} actions. "
            "Review and edit before generating workflow."
        )
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Action", "Selector", "Value", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Action buttons
        action_layout = QHBoxLayout()

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._on_delete_selected)
        action_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._on_clear_all)
        action_layout.addWidget(self.clear_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.generate_btn = QPushButton("Generate Workflow")
        self.generate_btn.setDefault(True)
        self.generate_btn.clicked.connect(self.accept)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.generate_btn)

        layout.addLayout(button_layout)

    def _load_actions(self):
        """Load actions into the table."""
        self.table.setRowCount(len(self.actions))

        for i, action in enumerate(self.actions):
            # Action type
            action_type = action.get("action", "unknown").upper()
            action_item = QTableWidgetItem(action_type)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, action_item)

            # Selector - handle both dict and ElementFingerprint
            element_info = action.get("element", {})

            # Check if element_info is an ElementFingerprint object
            if hasattr(element_info, "selectors"):
                # It's an ElementFingerprint object - selectors is a List[SelectorStrategy]
                selector = ""
                if element_info.selectors:
                    # Try to find xpath or css selector
                    for strat in element_info.selectors:
                        if strat.selector_type.value == "xpath":
                            selector = strat.value
                            break
                    if not selector:
                        # Fallback to first available selector
                        selector = element_info.selectors[0].value
            elif isinstance(element_info, dict):
                # It's a dictionary
                selectors = element_info.get("selectors", {})
                selector = selectors.get("xpath", selectors.get("css", ""))
            else:
                selector = ""

            selector_item = QTableWidgetItem(self._truncate(selector, 50))
            selector_item.setToolTip(selector)
            self.table.setItem(i, 1, selector_item)

            # Value
            value = action.get("value", "")
            value_item = QTableWidgetItem(str(value) if value else "-")
            self.table.setItem(i, 2, value_item)

            # Timestamp
            timestamp = action.get("timestamp", 0)
            from datetime import datetime

            time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 3, time_item)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text for display."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _on_delete_selected(self):
        """Delete selected rows."""
        selected_rows = sorted(
            set(item.row() for item in self.table.selectedItems()), reverse=True
        )

        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select actions to delete."
            )
            return

        for row in selected_rows:
            self.table.removeRow(row)
            del self.actions[row]

        logger.info(f"Deleted {len(selected_rows)} actions")

    def _on_clear_all(self):
        """Clear all actions."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all recorded actions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)
            self.actions.clear()
            logger.info("Cleared all actions")

    def get_actions(self) -> list:
        """
        Get the edited actions.

        Returns:
            List of action dictionaries
        """
        # Update values from table
        result = []
        for i in range(self.table.rowCount()):
            if i < len(self.actions):
                action = self.actions[i].copy()

                # Update value if edited
                value_item = self.table.item(i, 2)
                if value_item and value_item.text() != "-":
                    action["value"] = value_item.text()

                result.append(action)

        return result
