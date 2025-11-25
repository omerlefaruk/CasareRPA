"""
Variables Tab for the Bottom Panel.

Provides global workflow variable management with UiPath-style inline editing.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMenu,
    QMessageBox,
    QLabel,
    QAbstractItemView,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from PySide6.QtCore import Qt, Signal, QModelIndex, QTimer
from PySide6.QtGui import QColor, QBrush, QAction, QFont
from loguru import logger


# Variable type definitions
VARIABLE_TYPES = [
    "String",
    "Integer",
    "Float",
    "Boolean",
    "List",
    "Dict",
    "DataTable",
]

# Default values for each type
TYPE_DEFAULTS = {
    "String": "",
    "Integer": 0,
    "Float": 0.0,
    "Boolean": False,
    "List": [],
    "Dict": {},
    "DataTable": None,
}


class TypeComboDelegate(QStyledItemDelegate):
    """Delegate for type selection dropdown in table."""

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(VARIABLE_TYPES)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: none;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class VariablesTab(QWidget):
    """
    Variables tab widget with UiPath-style interface.

    Features:
    - Inline "Create variable" row for instant variable creation
    - Inline editing of all fields
    - Type dropdown selector
    - Design/Runtime modes

    Signals:
        variables_changed: Emitted when variables are modified
        refresh_requested: Emitted when user requests manual refresh (runtime mode)
    """

    variables_changed = Signal(dict)  # {name: variable_definition}
    refresh_requested = Signal()

    # Table columns
    COL_NAME = 0
    COL_TYPE = 1
    COL_SCOPE = 2
    COL_DEFAULT = 3
    COL_CURRENT = 4  # Current runtime value (visible in runtime mode)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Variables tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._is_runtime_mode = False
        self._variables: Dict[str, Dict[str, Any]] = {}
        self._is_creating = False
        self._variable_counter = 1

        # Auto-refresh timer for runtime mode
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        self._auto_refresh_interval = 500  # ms

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Runtime header (hidden in design mode)
        self._runtime_header = QWidget()
        runtime_layout = QHBoxLayout(self._runtime_header)
        runtime_layout.setContentsMargins(5, 5, 5, 5)

        self._label_count = QLabel("Variables: 0")
        runtime_layout.addWidget(self._label_count)

        runtime_layout.addStretch()

        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.setFixedSize(42, 14)
        self._btn_refresh.setToolTip("Refresh variable values")
        self._btn_refresh.clicked.connect(self._on_refresh)
        runtime_layout.addWidget(self._btn_refresh)

        self._btn_auto_refresh = QPushButton("Auto")
        self._btn_auto_refresh.setFixedSize(30, 14)
        self._btn_auto_refresh.setCheckable(True)
        self._btn_auto_refresh.setToolTip("Automatically refresh variables during execution")
        self._btn_auto_refresh.toggled.connect(self._on_auto_refresh_toggled)
        runtime_layout.addWidget(self._btn_auto_refresh)

        layout.addWidget(self._runtime_header)
        self._runtime_header.setVisible(False)  # Hidden by default (design mode)

        # Variables table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Name", "Data Type", "Scope", "Default Value", "Current Value"
        ])

        # Configure table
        self._table.setAlternatingRowColors(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellChanged.connect(self._on_cell_changed)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.setShowGrid(False)

        # Set type column delegate
        self._type_delegate = TypeComboDelegate()
        self._table.setItemDelegateForColumn(self.COL_TYPE, self._type_delegate)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_SCOPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DEFAULT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_CURRENT, QHeaderView.ResizeMode.Stretch)

        # Set minimum column widths
        self._table.setColumnWidth(self.COL_TYPE, 100)
        self._table.setColumnWidth(self.COL_SCOPE, 80)

        # Current Value column is always visible (side-by-side with Default Value)
        # Shows "-" when not in runtime mode, actual values during execution

        # Hide vertical header
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

        # Add the "Create variable" row
        self._add_create_variable_row()

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #404040;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #2d2d2d;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
            QTableWidget::item:hover {
                background-color: #2a2d2e;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #888888;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #404040;
                font-weight: normal;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: 1px solid #4b6eaf;
                padding: 2px 4px;
            }
            QComboBox {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: 1px solid #404040;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 1px;
                padding: 0px 1px;
                font-size: 8px;
            }
            QPushButton:hover {
                background-color: #4c4f51;
            }
            QPushButton:checked {
                background-color: #094771;
                border-color: #1177bb;
            }
        """)

    def _add_create_variable_row(self) -> None:
        """Add the 'Create variable' placeholder row at the top."""
        self._table.blockSignals(True)

        row = 0
        self._table.insertRow(row)

        # Create variable placeholder
        create_item = QTableWidgetItem("Create variable")
        create_item.setForeground(QBrush(QColor("#6a9955")))  # Green italic
        font = create_item.font()
        font.setItalic(True)
        create_item.setFont(font)
        create_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        create_item.setData(Qt.ItemDataRole.UserRole, "CREATE_PLACEHOLDER")

        # Empty cells for other columns
        type_item = QTableWidgetItem("")
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        type_item.setData(Qt.ItemDataRole.UserRole, "CREATE_PLACEHOLDER")

        scope_item = QTableWidgetItem("")
        scope_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        scope_item.setData(Qt.ItemDataRole.UserRole, "CREATE_PLACEHOLDER")

        default_item = QTableWidgetItem("")
        default_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        default_item.setData(Qt.ItemDataRole.UserRole, "CREATE_PLACEHOLDER")

        current_item = QTableWidgetItem("")
        current_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        current_item.setData(Qt.ItemDataRole.UserRole, "CREATE_PLACEHOLDER")

        self._table.setItem(row, self.COL_NAME, create_item)
        self._table.setItem(row, self.COL_TYPE, type_item)
        self._table.setItem(row, self.COL_SCOPE, scope_item)
        self._table.setItem(row, self.COL_DEFAULT, default_item)
        self._table.setItem(row, self.COL_CURRENT, current_item)

        self._table.blockSignals(False)

    def _on_cell_clicked(self, row: int, column: int) -> None:
        """Handle cell click - create new variable if clicking placeholder."""
        item = self._table.item(row, self.COL_NAME)
        if item and item.data(Qt.ItemDataRole.UserRole) == "CREATE_PLACEHOLDER":
            self._create_new_variable()

    def _create_new_variable(self) -> None:
        """Create a new variable with instant inline editing."""
        if self._is_runtime_mode or self._is_creating:
            return

        self._is_creating = True
        self._table.blockSignals(True)

        # Generate unique variable name
        var_name = self._generate_variable_name()

        # Insert new row after the "Create variable" row
        row = 1
        self._table.insertRow(row)

        # Name with {x} prefix visual
        name_item = QTableWidgetItem(f"{{x}}{var_name}")
        name_item.setForeground(QBrush(QColor("#4fc3f7")))  # Light blue
        name_item.setData(Qt.ItemDataRole.UserRole, var_name)  # Store actual name

        # Type dropdown
        type_item = QTableWidgetItem("String")
        type_item.setData(Qt.ItemDataRole.UserRole, "String")

        # Scope
        scope_item = QTableWidgetItem("Main")
        scope_item.setForeground(QBrush(QColor("#d4d4d4")))

        # Default value
        default_item = QTableWidgetItem("{}")
        default_item.setForeground(QBrush(QColor("#888888")))

        # Current runtime value (empty initially)
        current_item = QTableWidgetItem("-")
        current_item.setForeground(QBrush(QColor("#666666")))
        current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self._table.setItem(row, self.COL_NAME, name_item)
        self._table.setItem(row, self.COL_TYPE, type_item)
        self._table.setItem(row, self.COL_SCOPE, scope_item)
        self._table.setItem(row, self.COL_DEFAULT, default_item)
        self._table.setItem(row, self.COL_CURRENT, current_item)

        # Add to variables dict
        self._variables[var_name] = {
            "name": var_name,
            "type": "String",
            "default_value": "",
            "description": "",
            "scope": "Main",
        }

        self._table.blockSignals(False)

        # Select and edit the name cell immediately
        self._table.setCurrentCell(row, self.COL_NAME)
        self._table.editItem(name_item)

        self._is_creating = False
        self._variable_counter += 1

        # Emit change
        self.variables_changed.emit(self._variables)

    def _generate_variable_name(self) -> str:
        """Generate a unique variable name."""
        while True:
            name = f"variable{self._variable_counter}"
            if name not in self._variables:
                return name
            self._variable_counter += 1

    def _on_cell_changed(self, row: int, column: int) -> None:
        """Handle cell value changes."""
        if self._is_creating:
            return

        item = self._table.item(row, self.COL_NAME)
        if not item or item.data(Qt.ItemDataRole.UserRole) == "CREATE_PLACEHOLDER":
            return

        # Get the original variable name
        old_name = item.data(Qt.ItemDataRole.UserRole)
        if not old_name or old_name not in self._variables:
            return

        if column == self.COL_NAME:
            # Name changed
            new_text = item.text()
            # Remove {x} prefix if user included it
            new_name = new_text.replace("{x}", "").replace("{X}", "").strip()

            if new_name and new_name != old_name:
                # Check if name is valid
                if not new_name.isidentifier():
                    self._table.blockSignals(True)
                    item.setText(f"{{x}}{old_name}")
                    self._table.blockSignals(False)
                    return

                # Check if name already exists
                if new_name in self._variables and new_name != old_name:
                    self._table.blockSignals(True)
                    item.setText(f"{{x}}{old_name}")
                    self._table.blockSignals(False)
                    return

                # Update variable
                var_data = self._variables.pop(old_name)
                var_data["name"] = new_name
                self._variables[new_name] = var_data

                # Update display
                self._table.blockSignals(True)
                item.setText(f"{{x}}{new_name}")
                item.setData(Qt.ItemDataRole.UserRole, new_name)
                self._table.blockSignals(False)
            else:
                # Restore display format
                self._table.blockSignals(True)
                item.setText(f"{{x}}{old_name}")
                self._table.blockSignals(False)

        elif column == self.COL_TYPE:
            # Type changed
            type_item = self._table.item(row, self.COL_TYPE)
            if type_item:
                new_type = type_item.text()
                if new_type in VARIABLE_TYPES:
                    self._variables[old_name]["type"] = new_type
                    # Update default value based on type
                    default_item = self._table.item(row, self.COL_DEFAULT)
                    if default_item:
                        default_val = TYPE_DEFAULTS.get(new_type, "")
                        default_item.setText(self._format_default_value(default_val))
                        self._variables[old_name]["default_value"] = default_val

        elif column == self.COL_DEFAULT:
            # Default value changed
            default_item = self._table.item(row, self.COL_DEFAULT)
            if default_item:
                var_type = self._variables[old_name].get("type", "String")
                new_value = self._parse_default_value(default_item.text(), var_type)
                self._variables[old_name]["default_value"] = new_value

        # Emit change
        self.variables_changed.emit(self._variables)

    def _format_default_value(self, value: Any) -> str:
        """Format default value for display."""
        if value is None:
            return "{}"
        if value == "":
            return "{}"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (list, dict)):
            import json
            try:
                return json.dumps(value)
            except Exception:
                return "{}"
        return str(value) if value else "{}"

    def _parse_default_value(self, text: str, var_type: str) -> Any:
        """Parse default value from text based on type."""
        text = text.strip()
        if text == "{}" or text == "":
            return TYPE_DEFAULTS.get(var_type, "")

        try:
            if var_type == "Integer":
                return int(text)
            elif var_type == "Float":
                return float(text)
            elif var_type == "Boolean":
                return text.lower() in ("true", "1", "yes")
            elif var_type in ("List", "Dict"):
                import json
                return json.loads(text)
            else:
                return text
        except Exception:
            return TYPE_DEFAULTS.get(var_type, "")

    def _show_context_menu(self, position) -> None:
        """Show context menu for table."""
        if self._is_runtime_mode:
            return

        row = self._table.rowAt(position.y())
        if row < 0:
            return

        item = self._table.item(row, self.COL_NAME)
        if item and item.data(Qt.ItemDataRole.UserRole) == "CREATE_PLACEHOLDER":
            return

        menu = QMenu(self)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_variable(row))
        menu.addAction(delete_action)

        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self._duplicate_variable(row))
        menu.addAction(duplicate_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    def _delete_variable(self, row: int) -> None:
        """Delete variable at row."""
        item = self._table.item(row, self.COL_NAME)
        if not item:
            return

        var_name = item.data(Qt.ItemDataRole.UserRole)
        if var_name and var_name in self._variables:
            del self._variables[var_name]
            self._table.removeRow(row)
            self.variables_changed.emit(self._variables)

    def _duplicate_variable(self, row: int) -> None:
        """Duplicate variable at row."""
        item = self._table.item(row, self.COL_NAME)
        if not item:
            return

        var_name = item.data(Qt.ItemDataRole.UserRole)
        if var_name and var_name in self._variables:
            # Create duplicate
            new_name = self._generate_variable_name()
            var_data = self._variables[var_name].copy()
            var_data["name"] = new_name
            self._variables[new_name] = var_data

            # Add row
            self._add_variable_row(var_data)
            self.variables_changed.emit(self._variables)

    def _add_variable_row(self, variable: Dict[str, Any]) -> None:
        """Add a variable row to the table."""
        self._table.blockSignals(True)

        row = self._table.rowCount()
        self._table.insertRow(row)

        var_name = variable.get("name", "")

        # Name with {x} prefix
        name_item = QTableWidgetItem(f"{{x}}{var_name}")
        name_item.setForeground(QBrush(QColor("#4fc3f7")))
        name_item.setData(Qt.ItemDataRole.UserRole, var_name)

        # Type
        type_item = QTableWidgetItem(variable.get("type", "String"))

        # Scope
        scope_item = QTableWidgetItem(variable.get("scope", "Main"))

        # Default value
        default_val = variable.get("default_value", "")
        default_item = QTableWidgetItem(self._format_default_value(default_val))
        default_item.setForeground(QBrush(QColor("#888888")))

        # Current runtime value (empty initially)
        current_item = QTableWidgetItem("-")
        current_item.setForeground(QBrush(QColor("#666666")))
        current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self._table.setItem(row, self.COL_NAME, name_item)
        self._table.setItem(row, self.COL_TYPE, type_item)
        self._table.setItem(row, self.COL_SCOPE, scope_item)
        self._table.setItem(row, self.COL_DEFAULT, default_item)
        self._table.setItem(row, self.COL_CURRENT, current_item)

        self._table.blockSignals(False)

    # ==================== Public API ====================

    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set the workflow variables.

        Args:
            variables: Dict of variable definitions
        """
        self._variables = {}

        # Clear table except "Create variable" row
        self._table.blockSignals(True)
        while self._table.rowCount() > 1:
            self._table.removeRow(1)
        self._table.blockSignals(False)

        for name, var_data in variables.items():
            if isinstance(var_data, dict):
                variable = {
                    "name": name,
                    "type": var_data.get("type", "String"),
                    "default_value": var_data.get("default_value", ""),
                    "description": var_data.get("description", ""),
                    "scope": var_data.get("scope", "Main"),
                }
            else:
                # Simple value format
                variable = {
                    "name": name,
                    "type": self._infer_type(var_data),
                    "default_value": var_data,
                    "description": "",
                    "scope": "Main",
                }

            self._variables[name] = variable
            self._add_variable_row(variable)

    def get_variables(self) -> Dict[str, Any]:
        """
        Get current variables.

        Returns:
            Dict of variable definitions
        """
        return self._variables.copy()

    def update_runtime_values(self, values: Dict[str, Any]) -> None:
        """
        Update current values during runtime.

        Args:
            values: Dict of {name: current_value}
        """
        for row in range(1, self._table.rowCount()):  # Skip "Create variable" row
            item = self._table.item(row, self.COL_NAME)
            if item:
                var_name = item.data(Qt.ItemDataRole.UserRole)
                if var_name in values:
                    # Update the Current Value column (side-by-side with Default)
                    current_item = self._table.item(row, self.COL_CURRENT)
                    if current_item:
                        current_item.setText(self._format_default_value(values[var_name]))
                        current_item.setForeground(QBrush(QColor("#4CAF50")))  # Green for active

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Switch between design and runtime mode.

        Args:
            enabled: True for runtime mode
        """
        self._is_runtime_mode = enabled

        # Show/hide runtime header
        self._runtime_header.setVisible(enabled)

        # Current Value column is always visible (side-by-side with Default Value)

        # Update "Create variable" row visibility/editability
        if enabled:
            # Hide create row in runtime mode
            self._table.setRowHidden(0, True)
            self._update_variable_count()
        else:
            self._table.setRowHidden(0, False)
            # Stop auto-refresh when leaving runtime mode
            if self._auto_refresh_timer.isActive():
                self._auto_refresh_timer.stop()
                self._btn_auto_refresh.setChecked(False)
            # Reset Current Value column to "-" when exiting runtime mode
            for row in range(1, self._table.rowCount()):
                current_item = self._table.item(row, self.COL_CURRENT)
                if current_item:
                    current_item.setText("-")
                    current_item.setForeground(QBrush(QColor("#666666")))

        # Make table read-only in runtime mode (except Current Value which is always read-only)
        for row in range(1, self._table.rowCount()):
            for col in range(self._table.columnCount()):
                if col == self.COL_CURRENT:
                    continue  # Current value is always read-only
                item = self._table.item(row, col)
                if item:
                    if enabled:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

    def clear(self) -> None:
        """Clear all variables."""
        self._variables = {}
        self._table.blockSignals(True)
        while self._table.rowCount() > 1:
            self._table.removeRow(1)
        self._table.blockSignals(False)
        self._variable_counter = 1

    def _infer_type(self, value: Any) -> str:
        """Infer variable type from value."""
        if isinstance(value, bool):
            return "Boolean"
        if isinstance(value, int):
            return "Integer"
        if isinstance(value, float):
            return "Float"
        if isinstance(value, list):
            return "List"
        if isinstance(value, dict):
            return "Dict"
        return "String"

    def _update_variable_count(self) -> None:
        """Update the variable count label."""
        count = len(self._variables)
        self._label_count.setText(f"Variables: {count}")

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        logger.debug("Variable refresh requested")
        self.refresh_requested.emit()

    def _on_auto_refresh(self) -> None:
        """Handle auto-refresh timer tick."""
        self.refresh_requested.emit()

    def _on_auto_refresh_toggled(self, checked: bool) -> None:
        """Handle auto-refresh toggle."""
        if checked:
            self._btn_auto_refresh.setText("Stop Auto")
            self._auto_refresh_timer.start(self._auto_refresh_interval)
            logger.debug(f"Auto-refresh enabled ({self._auto_refresh_interval}ms)")
        else:
            self._btn_auto_refresh.setText("Auto-Refresh")
            self._auto_refresh_timer.stop()
            logger.debug("Auto-refresh disabled")

    def set_auto_refresh_interval(self, interval_ms: int) -> None:
        """
        Set the auto-refresh interval.

        Args:
            interval_ms: Refresh interval in milliseconds
        """
        self._auto_refresh_interval = interval_ms
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.start(interval_ms)
        logger.debug(f"Auto-refresh interval set to {interval_ms}ms")
