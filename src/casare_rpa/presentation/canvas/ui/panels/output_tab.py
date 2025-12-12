"""
Output Tab for the Bottom Panel.

Displays workflow outputs and return values with improved UX:
- Empty state guidance when no outputs exist
- Color-coded type badges
- Improved toolbar with tooltips
- Context menu for copy/export
- Better visual hierarchy
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
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QTextEdit,
    QSplitter,
    QStackedWidget,
    QApplication,
    QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    ToolbarButton,
    StatusBadge,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)


class OutputTab(QWidget):
    """
    Output tab widget for displaying workflow outputs.

    Features:
    - Empty state when no outputs
    - Output variables set by nodes
    - Final workflow result/status with color-coded badge
    - Timestamps for each output
    - Value preview panel with JSON formatting
    - Context menu for copy/export
    - Type-colored badges
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("outputToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(12)

        # Status/count label
        self._status_label = QLabel("No outputs")
        self._status_label.setProperty("muted", True)

        # Copy all button
        copy_btn = ToolbarButton(
            text="Copy All",
            tooltip="Copy all outputs to clipboard (Ctrl+C)",
        )
        copy_btn.clicked.connect(self._on_copy_all)

        # Clear button
        clear_btn = ToolbarButton(
            text="Clear",
            tooltip="Clear all outputs",
        )
        clear_btn.clicked.connect(self.clear)

        toolbar.addWidget(self._status_label)
        toolbar.addStretch()
        toolbar.addWidget(copy_btn)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content area with stacked widget for empty state
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",  # Output/export icon
            title="No Outputs Yet",
            description=(
                "Workflow outputs will appear here when:\n"
                "- A workflow completes execution\n"
                "- Nodes produce output values"
            ),
        )
        self._content_stack.addWidget(self._empty_state)

        # Main content (index 1)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 4, 8, 8)
        content_layout.setSpacing(4)

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
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.verticalHeader().setVisible(False)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(
            self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(
            self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_VALUE, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths
        self._table.setColumnWidth(self.COL_NAME, 120)

        splitter.addWidget(self._table)

        # Preview panel
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 4, 0, 0)
        preview_layout.setSpacing(4)

        preview_header = QLabel("VALUE PREVIEW")
        preview_header.setObjectName("previewHeader")
        preview_layout.addWidget(preview_header)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMinimumHeight(60)
        self._preview_text.setMaximumHeight(120)
        self._preview_text.setPlaceholderText(
            "Select an output to preview its value..."
        )
        preview_layout.addWidget(self._preview_text)

        splitter.addWidget(preview_container)

        # Set initial splitter sizes (table gets more space)
        splitter.setSizes([200, 80])
        splitter.setCollapsible(1, True)

        content_layout.addWidget(splitter)

        # Result bar (hidden by default)
        self._result_bar = QWidget()
        self._result_bar.setObjectName("resultBar")
        result_layout = QHBoxLayout(self._result_bar)
        result_layout.setContentsMargins(8, 6, 8, 6)
        result_layout.setSpacing(8)

        self._result_badge = StatusBadge("", "idle")
        self._result_message = QLabel("")
        self._result_message.setObjectName("resultMessage")

        result_layout.addWidget(self._result_badge)
        result_layout.addWidget(self._result_message)
        result_layout.addStretch()

        self._result_bar.hide()
        content_layout.addWidget(self._result_bar)

        self._content_stack.addWidget(content_widget)

        layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        # Apply toolbar styles
        self.setStyleSheet(f"""
            OutputTab, QWidget, QStackedWidget, QFrame, QSplitter {{
                background-color: {THEME.bg_panel};
            }}
            #outputToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            {get_panel_table_stylesheet()}
            #previewHeader {{
                color: {THEME.text_header};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                padding: 4px 0;
            }}
            QTextEdit {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 4px;
            }}
            #resultBar {{
                background-color: {THEME.bg_header};
                border-top: 1px solid {THEME.border_dark};
            }}
            #resultMessage {{
                color: {THEME.text_primary};
                font-size: 11px;
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

    def _on_context_menu(self, pos) -> None:
        """Show context menu for table."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {THEME.accent_primary};
                color: #ffffff;
            }}
        """)

        # Copy name
        name_item = self._table.item(row, self.COL_NAME)
        if name_item:
            copy_name = menu.addAction("Copy Name")
            copy_name.triggered.connect(
                lambda: QApplication.clipboard().setText(name_item.text())
            )

        # Copy value
        value_item = self._table.item(row, self.COL_VALUE)
        if value_item:
            full_value = value_item.data(Qt.ItemDataRole.UserRole)
            copy_value = menu.addAction("Copy Value")
            copy_value.triggered.connect(
                lambda: QApplication.clipboard().setText(
                    self._format_value_for_preview(full_value)
                )
            )

        # Copy as JSON
        if name_item and value_item:
            menu.addSeparator()
            copy_json = menu.addAction("Copy as JSON")
            copy_json.triggered.connect(lambda: self._copy_row_as_json(row))

        menu.exec_(self._table.mapToGlobal(pos))

    def _copy_row_as_json(self, row: int) -> None:
        """Copy a row as JSON to clipboard."""
        name_item = self._table.item(row, self.COL_NAME)
        value_item = self._table.item(row, self.COL_VALUE)
        if name_item and value_item:
            name = name_item.text()
            value = value_item.data(Qt.ItemDataRole.UserRole)
            try:
                json_str = json.dumps({name: value}, indent=2, default=str)
                QApplication.clipboard().setText(json_str)
            except Exception:
                QApplication.clipboard().setText(f'{{"{name}": "{value}"}}')

    def _on_copy_all(self) -> None:
        """Copy all outputs to clipboard."""
        outputs = self.get_outputs()
        if outputs:
            try:
                json_str = json.dumps(outputs, indent=2, default=str)
                QApplication.clipboard().setText(json_str)
            except Exception:
                # Fallback to simple format
                lines = [f"{k}: {v}" for k, v in outputs.items()]
                QApplication.clipboard().setText("\n".join(lines))

    def _format_value(self, value: Any) -> str:
        """Format a value for table display (truncated)."""
        if value is None:
            return "(None)"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (list, dict)):
            try:
                text = json.dumps(value, default=str)
                if len(text) > 80:
                    return text[:77] + "..."
                return text
            except Exception:
                return str(value)[:80]
        text = str(value)
        if len(text) > 80:
            return text[:77] + "..."
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

    def _get_type_color(self, type_name: str) -> str:
        """Get color for type name (VSCode syntax colors)."""
        colors = {
            "None": THEME.text_muted,
            "Boolean": THEME.wire_bool,
            "Integer": THEME.wire_number,
            "Float": THEME.wire_number,
            "String": THEME.wire_string,
            "List": THEME.wire_list,
            "Dict": THEME.wire_dict,
        }
        return colors.get(type_name, THEME.text_primary)

    def _update_status(self) -> None:
        """Update status label and show/hide empty state."""
        count = self._table.rowCount()
        if count == 0:
            self._status_label.setText("No outputs")
            self._status_label.setProperty("muted", True)
            self._content_stack.setCurrentIndex(0)  # Show empty state
        else:
            self._status_label.setText(f"{count} output{'s' if count != 1 else ''}")
            self._status_label.setProperty("muted", False)
            self._content_stack.setCurrentIndex(1)  # Show table

        # Refresh style
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

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

        # Name (with accent color)
        name_item = QTableWidgetItem(name)
        name_item.setForeground(QBrush(QColor(THEME.accent_primary)))
        name_item.setToolTip(f"Output: {name}")

        # Type (with type-specific color)
        type_name = self._get_type_name(value)
        type_item = QTableWidgetItem(type_name)
        type_color = self._get_type_color(type_name)
        type_item.setForeground(QBrush(QColor(type_color)))
        type_item.setToolTip(f"Type: {type_name}")

        # Value (truncated for display, full stored in user data)
        value_item = QTableWidgetItem(self._format_value(value))
        value_item.setData(Qt.ItemDataRole.UserRole, value)
        value_item.setToolTip("Double-click or select to preview full value")

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
            self._result_badge.set_status("success", "SUCCESS")
            self._result_bar.setStyleSheet(f"""
                #resultBar {{
                    background-color: #1a3d1a;
                    border-top: 1px solid {THEME.status_success};
                }}
                #resultMessage {{
                    color: {THEME.status_success};
                }}
            """)
        else:
            self._result_badge.set_status("error", "FAILED")
            self._result_bar.setStyleSheet(f"""
                #resultBar {{
                    background-color: #3d1a1a;
                    border-top: 1px solid {THEME.status_error};
                }}
                #resultMessage {{
                    color: {THEME.status_error};
                }}
            """)

        self._result_message.setText(message)

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
