"""
Output Tab for the Bottom Panel.

Displays workflow outputs and return values.
"""

from typing import Optional, Any
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QTextEdit,
    QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

from ..theme import THEME


class OutputTab(QWidget):
    """
    Output tab widget for displaying workflow outputs.

    Features:
    - Output variables set by nodes
    - Final workflow result/status
    - Timestamps for each output
    - Value preview panel
    """

    # Table columns
    COL_TIME = 0
    COL_NAME = 1
    COL_TYPE = 2
    COL_VALUE = 3

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Output tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Status label
        self._status_label = QLabel("No outputs")
        self._status_label.setStyleSheet(f"color: {THEME.text_muted};")

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(40, 16)
        clear_btn.clicked.connect(self.clear)

        toolbar.addWidget(self._status_label)
        toolbar.addStretch()
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Splitter for table and preview
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Output table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Time", "Name", "Type", "Value"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(
            self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_NAME, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_VALUE, QHeaderView.ResizeMode.Stretch)

        splitter.addWidget(self._table)

        # Preview panel
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(2)

        preview_label = QLabel("Value Preview:")
        preview_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 9pt;")
        preview_layout.addWidget(preview_label)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMaximumHeight(100)
        self._preview_text.setPlaceholderText("Select an output to preview its value")
        preview_layout.addWidget(self._preview_text)

        splitter.addWidget(preview_container)

        # Set initial splitter sizes
        splitter.setSizes([250, 100])

        layout.addWidget(splitter)

        # Result bar
        self._result_bar = QLabel("")
        self._result_bar.setStyleSheet(f"""
            QLabel {{
                background-color: {THEME.bg_light};
                color: {THEME.text_muted};
                padding: 6px 8px;
                font-size: 9pt;
            }}
        """)
        self._result_bar.hide()
        layout.addWidget(self._result_bar)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                gridline-color: {THEME.border_dark};
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_header};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTextEdit {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                padding: 0px 2px;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QLabel {{
                color: {THEME.text_secondary};
            }}
        """)

    def _on_selection_changed(self) -> None:
        """Handle selection change in table."""
        selected = self._table.selectedItems()
        if selected:
            row = selected[0].row()
            value_item = self._table.item(row, self.COL_VALUE)
            if value_item:
                # Get full value from user data
                full_value = value_item.data(Qt.ItemDataRole.UserRole)
                if full_value is not None:
                    self._preview_text.setText(
                        self._format_value_for_preview(full_value)
                    )
                else:
                    self._preview_text.setText(value_item.text())
        else:
            self._preview_text.clear()

    def _format_value(self, value: Any) -> str:
        """Format a value for table display (truncated)."""
        if value is None:
            return "(None)"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (list, dict)):
            try:
                text = json.dumps(value, default=str)
                if len(text) > 100:
                    return text[:97] + "..."
                return text
            except Exception:
                return str(value)[:100]
        text = str(value)
        if len(text) > 100:
            return text[:97] + "..."
        return text

    def _format_value_for_preview(self, value: Any) -> str:
        """Format a value for preview panel (full)."""
        if value is None:
            return "(None)"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (list, dict)):
            try:
                return json.dumps(value, indent=2, default=str)
            except Exception:
                return str(value)
        return str(value)

    def _get_type_name(self, value: Any) -> str:
        """Get human-readable type name."""
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "Boolean"
        if isinstance(value, int):
            return "Integer"
        if isinstance(value, float):
            return "Float"
        if isinstance(value, str):
            return "String"
        if isinstance(value, list):
            return "List"
        if isinstance(value, dict):
            return "Dict"
        return type(value).__name__

    def _update_status(self) -> None:
        """Update status label."""
        count = self._table.rowCount()
        if count == 0:
            self._status_label.setText("No outputs")
        else:
            self._status_label.setText(f"{count} output(s)")

    # ==================== Public API ====================

    def add_output(
        self, name: str, value: Any, timestamp: Optional[str] = None
    ) -> None:
        """
        Add an output to the table.

        Args:
            name: Output name/key
            value: Output value
            timestamp: Optional timestamp string
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Time
        time_str = timestamp or datetime.now().strftime("%H:%M:%S.%f")[:-3]
        time_item = QTableWidgetItem(time_str)
        time_item.setForeground(QBrush(QColor(THEME.text_muted)))

        # Name
        name_item = QTableWidgetItem(name)
        name_item.setForeground(QBrush(QColor(THEME.accent_primary)))  # VSCode blue

        # Type
        type_name = self._get_type_name(value)
        type_item = QTableWidgetItem(type_name)
        type_item.setForeground(
            QBrush(QColor(THEME.wire_dict))
        )  # VSCode teal for types

        # Value (truncated for display, full stored in user data)
        value_item = QTableWidgetItem(self._format_value(value))
        value_item.setData(Qt.ItemDataRole.UserRole, value)

        self._table.setItem(row, self.COL_TIME, time_item)
        self._table.setItem(row, self.COL_NAME, name_item)
        self._table.setItem(row, self.COL_TYPE, type_item)
        self._table.setItem(row, self.COL_VALUE, value_item)

        self._update_status()

        # Scroll to new item
        self._table.scrollToBottom()

    def set_workflow_result(self, success: bool, message: str) -> None:
        """
        Set the final workflow result.

        Args:
            success: Whether workflow completed successfully
            message: Result message
        """
        self._result_bar.show()

        if success:
            self._result_bar.setStyleSheet("""
                QLabel {
                    background-color: #2d4a2d;
                    color: #6bff6b;
                    padding: 6px 8px;
                    font-size: 9pt;
                    font-weight: bold;
                }
            """)
            self._result_bar.setText(f"SUCCESS: {message}")
        else:
            self._result_bar.setStyleSheet("""
                QLabel {
                    background-color: #4a2d2d;
                    color: #ff6b6b;
                    padding: 6px 8px;
                    font-size: 9pt;
                    font-weight: bold;
                }
            """)
            self._result_bar.setText(f"FAILED: {message}")

    def clear(self) -> None:
        """Clear all outputs."""
        self._table.setRowCount(0)
        self._preview_text.clear()
        self._result_bar.hide()
        self._update_status()

    def get_output_count(self) -> int:
        """Get the number of outputs."""
        return self._table.rowCount()

    def get_outputs(self) -> dict:
        """
        Get all outputs as a dictionary.

        Returns:
            Dict of {name: value}
        """
        outputs = {}
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, self.COL_NAME)
            value_item = self._table.item(row, self.COL_VALUE)
            if name_item and value_item:
                name = name_item.text()
                value = value_item.data(Qt.ItemDataRole.UserRole)
                outputs[name] = value
        return outputs
