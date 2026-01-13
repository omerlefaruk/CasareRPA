"""
Output Tab for the Bottom Panel.

Displays workflow outputs and return values with improved UX:
- Empty state guidance when no outputs exist
- Color-coded type badges
- Improved toolbar with tooltips
- Context menu for copy/export
- Better visual hierarchy

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

import json
from datetime import datetime
from typing import Any

from PySide6.QtCore import QPoint, Qt, Slot
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import (
    _get_header_stylesheet,
    _get_table_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import EmptyState


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

    def __init__(self, parent: QWidget | None = None) -> None:
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
        toolbar.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        toolbar.setSpacing(TOKENS_V2.spacing.xs)

        # Status/count label
        self._status_label = QLabel("No outputs")
        self._status_label.setProperty("muted", True)

        # Copy all button (v2 PushButton)
        copy_btn = PushButton(
            text="Copy All",
            variant="secondary",
            size="sm",
        )
        copy_btn.setToolTip("Copy all outputs to clipboard (Ctrl+C)")
        copy_btn.clicked.connect(self._on_copy_all)

        # Clear button (v2 PushButton)
        clear_btn = PushButton(
            text="Clear",
            variant="ghost",
            size="sm",
        )
        clear_btn.setToolTip("Clear all outputs")
        clear_btn.clicked.connect(self.clear)

        toolbar.addWidget(self._status_label)
        toolbar.addStretch()
        toolbar.addWidget(copy_btn)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar_widget)

        # Content area with stacked widget for empty state
        self._content_stack = QStackedWidget()

        # Empty state (index 0) - v2 EmptyState component
        empty_container = QWidget()
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setContentsMargins(0, 0, 0, 0)

        self._empty_state = EmptyState(
            icon="database",
            text="No Outputs Yet",
            action_text="",
        )
        # Set custom description for empty state
        self._empty_state.set_text(
            "Workflow outputs will appear here when:\n"
            "- A workflow completes execution\n"
            "- Nodes produce output values"
        )
        empty_layout.addWidget(self._empty_state)
        self._content_stack.addWidget(empty_container)

        # Main content (index 1)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(
            TOKENS_V2.spacing.sm, TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.sm, TOKENS_V2.spacing.sm
        )
        content_layout.setSpacing(TOKENS_V2.spacing.xs)

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
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_VALUE, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths using v2 tokens
        self._table.setColumnWidth(self.COL_NAME, TOKENS_V2.sizes.input_max_width)

        splitter.addWidget(self._table)

        # Preview panel
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, TOKENS_V2.spacing.xs, 0, 0)
        preview_layout.setSpacing(TOKENS_V2.spacing.xs)

        preview_header = QLabel("VALUE PREVIEW")
        preview_header.setObjectName("previewHeader")
        preview_layout.addWidget(preview_header)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMinimumHeight(TOKENS_V2.sizes.row_height * 2)
        self._preview_text.setMaximumHeight(TOKENS_V2.sizes.row_height * 4)
        self._preview_text.setPlaceholderText("Select an output to preview its value...")
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
        result_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
        )
        result_layout.setSpacing(TOKENS_V2.spacing.sm)

        self._result_badge = _StatusBadge("", "idle")
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
        """Apply v2 theme styling."""
        # Apply table and header styles from lists.py
        self._table.setStyleSheet(_get_table_stylesheet())
        self._table.horizontalHeader().setStyleSheet(_get_header_stylesheet())

        # Main widget styling
        self.setStyleSheet(f"""
            OutputTab, QWidget, QStackedWidget, QFrame, QSplitter {{
                background-color: {THEME_V2.bg_surface};
            }}
            #outputToolbar {{
                background-color: {THEME_V2.bg_header};
                border-bottom: 1px solid {THEME_V2.border};
            }}
            QLabel {{
                background: transparent;
                color: {THEME_V2.text_secondary};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QLabel[muted="true"] {{
                color: {THEME_V2.text_muted};
            }}
            #previewHeader {{
                color: {THEME_V2.text_header};
                font-size: {TOKENS_V2.typography.caption}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                letter-spacing: 0.5px;
                padding: {TOKENS_V2.spacing.xs}px 0;
            }}
            QTextEdit {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                font-family: {TOKENS_V2.typography.mono};
                font-size: {TOKENS_V2.typography.body_sm}px;
                padding: {TOKENS_V2.spacing.xs}px;
            }}
            #resultBar {{
                background-color: {THEME_V2.bg_elevated};
                border-top: 1px solid {THEME_V2.border};
            }}
            #resultMessage {{
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
        """)

    @Slot()
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
                    self._preview_text.setText(self._format_value_for_preview(full_value))
                else:
                    self._preview_text.setText(value_item.text())
        else:
            self._preview_text.clear()

    @Slot(QPoint)
    def _on_context_menu(self, pos: QPoint) -> None:
        """Show context menu for table."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        # Store row data for slot methods
        self._context_menu_row = row
        self._context_menu_name_item = self._table.item(row, self.COL_NAME)
        self._context_menu_value_item = self._table.item(row, self.COL_VALUE)

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME_V2.bg_elevated};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px;
            }}
            QMenu::item {{
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_V2.bg_selected};
            }}
        """)

        # Copy name
        if self._context_menu_name_item:
            copy_name = menu.addAction("Copy Name")
            copy_name.triggered.connect(self._on_context_copy_name)

        # Copy value
        if self._context_menu_value_item:
            copy_value = menu.addAction("Copy Value")
            copy_value.triggered.connect(self._on_context_copy_value)

        # Copy as JSON
        if self._context_menu_name_item and self._context_menu_value_item:
            menu.addSeparator()
            copy_json = menu.addAction("Copy as JSON")
            copy_json.triggered.connect(self._on_context_copy_json)

        menu.exec_(self._table.mapToGlobal(pos))

    @Slot()
    def _on_context_copy_name(self) -> None:
        """Copy name to clipboard from context menu."""
        if hasattr(self, "_context_menu_name_item") and self._context_menu_name_item:
            QApplication.clipboard().setText(self._context_menu_name_item.text())

    @Slot()
    def _on_context_copy_value(self) -> None:
        """Copy value to clipboard from context menu."""
        if hasattr(self, "_context_menu_value_item") and self._context_menu_value_item:
            full_value = self._context_menu_value_item.data(Qt.ItemDataRole.UserRole)
            QApplication.clipboard().setText(self._format_value_for_preview(full_value))

    @Slot()
    def _on_context_copy_json(self) -> None:
        """Copy row as JSON from context menu."""
        if hasattr(self, "_context_menu_row"):
            self._copy_row_as_json(self._context_menu_row)

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

    @Slot()
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
        if isinstance(value, list | dict):
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
        if isinstance(value, list | dict):
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
        """Get color for type name using v2 wire colors."""
        colors = {
            "None": THEME_V2.text_muted,
            "Boolean": THEME_V2.wire_bool,
            "Integer": THEME_V2.wire_number,
            "Float": THEME_V2.wire_number,
            "String": THEME_V2.wire_string,
            "List": THEME_V2.wire_list,
            "Dict": THEME_V2.wire_dict,
        }
        return colors.get(type_name, THEME_V2.text_primary)

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

    def add_output(self, name: str, value: Any, timestamp: str | None = None) -> None:
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
        time_item.setForeground(QBrush(QColor(THEME_V2.text_muted)))

        # Name (with accent color)
        name_item = QTableWidgetItem(name)
        name_item.setForeground(QBrush(QColor(THEME_V2.primary)))
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
                    background-color: {THEME_V2.bg_elevated};
                    border-top: 1px solid {THEME_V2.success};
                }}
                #resultMessage {{
                    color: {THEME_V2.success};
                }}
            """)
        else:
            self._result_badge.set_status("error", "FAILED")
            self._result_bar.setStyleSheet(f"""
                #resultBar {{
                    background-color: {THEME_V2.bg_elevated};
                    border-top: 1px solid {THEME_V2.error};
                }}
                #resultMessage {{
                    color: {THEME_V2.error};
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


# =============================================================================
# HELPER: STATUS BADGE (v2)
# =============================================================================


class _StatusBadge(QLabel):
    """
    Status badge label with color-coded backgrounds (v2 version).

    Used to display status indicators like SUCCESS, ERROR, WARNING.
    """

    def __init__(
        self,
        text: str = "",
        status: str = "info",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize status badge.

        Args:
            text: Badge text
            status: Status type (success, error, warning, info, idle)
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.set_status(status)
        self._apply_base_styles()

    def _apply_base_styles(self) -> None:
        """Apply base badge styling."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(TOKENS_V2.sizes.combo_dropdown_width)

    def set_status(self, status: str, text: str | None = None) -> None:
        """
        Set badge status and optionally update text.

        Args:
            status: Status type (success, error, warning, info, idle, running)
            text: Optional new text
        """
        if text is not None:
            self.setText(text)

        # Color mappings: (fg_color, bg_color) - None bg means no badge styling
        colors = {
            "success": (THEME_V2.success, f"{THEME_V2.success}20"),
            "error": (THEME_V2.error, f"{THEME_V2.error}20"),
            "warning": (THEME_V2.warning, f"{THEME_V2.warning}20"),
            "info": (THEME_V2.info, f"{THEME_V2.info}20"),
            "idle": (THEME_V2.text_muted, None),  # No badge, just plain text
            "running": (THEME_V2.warning, f"{THEME_V2.warning}20"),
        }

        fg_color, bg_color = colors.get(status.lower(), colors["info"])

        if bg_color is None:
            # Idle: plain text, no background at all
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet(f"""
                QLabel {{
                    background: none;
                    border: none;
                    color: {fg_color};
                    font-size: {TOKENS_V2.typography.caption}px;
                    font-weight: {TOKENS_V2.typography.weight_semibold};
                    text-transform: uppercase;
                    font-family: {TOKENS_V2.typography.family};
                }}
            """)
        else:
            # Active states: badge with colored background
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    color: {fg_color};
                    padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
                    border-radius: {TOKENS_V2.radius.xs}px;
                    font-size: {TOKENS_V2.typography.caption}px;
                    font-weight: {TOKENS_V2.typography.weight_semibold};
                    text-transform: uppercase;
                    font-family: {TOKENS_V2.typography.family};
                }}
            """)
