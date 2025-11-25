"""
Variables Tab for the Bottom Panel.

Provides global workflow variable management with design and runtime modes.
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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QAction
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


class VariablesTab(QWidget):
    """
    Variables tab widget for managing global workflow variables.

    Features:
    - Design Mode: Add, edit, delete variables
    - Runtime Mode: Read-only view of current values
    - Double-click to edit
    - Context menu for quick actions

    Signals:
        variables_changed: Emitted when variables are modified
    """

    variables_changed = Signal(dict)  # {name: variable_definition}

    # Table columns
    COL_NAME = 0
    COL_TYPE = 1
    COL_DEFAULT = 2
    COL_CURRENT = 3
    COL_DESCRIPTION = 4

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Variables tab.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._is_runtime_mode = False
        self._variables: Dict[str, Dict[str, Any]] = {}

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        # Mode indicator
        self._mode_label = QLabel("Design Mode")
        self._mode_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Add button
        self._add_btn = QPushButton("+ Add")
        self._add_btn.setFixedWidth(70)
        self._add_btn.clicked.connect(self._on_add_variable)
        self._add_btn.setToolTip("Add new variable")

        # Edit button
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setFixedWidth(60)
        self._edit_btn.clicked.connect(self._on_edit_variable)
        self._edit_btn.setEnabled(False)
        self._edit_btn.setToolTip("Edit selected variable")

        # Delete button
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setFixedWidth(60)
        self._delete_btn.clicked.connect(self._on_delete_variable)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setToolTip("Delete selected variable")

        # Import/Export buttons
        self._import_btn = QPushButton("Import")
        self._import_btn.setFixedWidth(60)
        self._import_btn.clicked.connect(self._on_import_variables)
        self._import_btn.setToolTip("Import variables from JSON")

        self._export_btn = QPushButton("Export")
        self._export_btn.setFixedWidth(60)
        self._export_btn.clicked.connect(self._on_export_variables)
        self._export_btn.setToolTip("Export variables to JSON")

        toolbar.addWidget(self._mode_label)
        toolbar.addStretch()
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addWidget(self._import_btn)
        toolbar.addWidget(self._export_btn)

        layout.addLayout(toolbar)

        # Variables table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Name", "Type", "Default Value", "Current Value", "Description"
        ])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(self._on_double_click)

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DEFAULT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_CURRENT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_DESCRIPTION, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                gridline-color: #3d3d3d;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #4b6eaf;
            }
            QTableWidget::item:hover {
                background-color: #3c3f41;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #1e1e1e;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4c4f51;
            }
            QPushButton:disabled {
                color: #666666;
                background-color: #2d2d2d;
            }
        """)

    def _on_selection_changed(self) -> None:
        """Handle selection change in table."""
        has_selection = len(self._table.selectedItems()) > 0
        # Enable/disable buttons only in design mode
        if not self._is_runtime_mode:
            self._edit_btn.setEnabled(has_selection)
            self._delete_btn.setEnabled(has_selection)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        """Handle double-click on table item."""
        if not self._is_runtime_mode:
            self._on_edit_variable()

    def _show_context_menu(self, position) -> None:
        """Show context menu for table."""
        if self._is_runtime_mode:
            return

        menu = QMenu(self)

        add_action = QAction("Add Variable", self)
        add_action.triggered.connect(self._on_add_variable)
        menu.addAction(add_action)

        if self._table.selectedItems():
            edit_action = QAction("Edit Variable", self)
            edit_action.triggered.connect(self._on_edit_variable)
            menu.addAction(edit_action)

            delete_action = QAction("Delete Variable", self)
            delete_action.triggered.connect(self._on_delete_variable)
            menu.addAction(delete_action)

            menu.addSeparator()

            duplicate_action = QAction("Duplicate Variable", self)
            duplicate_action.triggered.connect(self._on_duplicate_variable)
            menu.addAction(duplicate_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    def _on_add_variable(self) -> None:
        """Add a new variable."""
        from .variable_editor_dialog import VariableEditorDialog

        dialog = VariableEditorDialog(
            existing_names=list(self._variables.keys()),
            parent=self
        )

        if dialog.exec():
            variable = dialog.get_variable()
            self._add_variable_to_table(variable)
            self._variables[variable["name"]] = variable
            self.variables_changed.emit(self._variables)
            logger.debug(f"Added variable: {variable['name']}")

    def _on_edit_variable(self) -> None:
        """Edit selected variable."""
        row = self._table.currentRow()
        if row < 0:
            return

        name = self._table.item(row, self.COL_NAME).text()
        variable = self._variables.get(name)
        if not variable:
            return

        from .variable_editor_dialog import VariableEditorDialog

        dialog = VariableEditorDialog(
            variable=variable,
            existing_names=[n for n in self._variables.keys() if n != name],
            parent=self
        )

        if dialog.exec():
            updated = dialog.get_variable()

            # Remove old entry if name changed
            if updated["name"] != name:
                del self._variables[name]

            self._variables[updated["name"]] = updated
            self._update_row(row, updated)
            self.variables_changed.emit(self._variables)
            logger.debug(f"Updated variable: {updated['name']}")

    def _on_delete_variable(self) -> None:
        """Delete selected variable."""
        row = self._table.currentRow()
        if row < 0:
            return

        name = self._table.item(row, self.COL_NAME).text()

        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Are you sure you want to delete variable '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._table.removeRow(row)
            if name in self._variables:
                del self._variables[name]
            self.variables_changed.emit(self._variables)
            logger.debug(f"Deleted variable: {name}")

    def _on_duplicate_variable(self) -> None:
        """Duplicate selected variable."""
        row = self._table.currentRow()
        if row < 0:
            return

        name = self._table.item(row, self.COL_NAME).text()
        variable = self._variables.get(name)
        if not variable:
            return

        # Create duplicate with unique name
        new_name = f"{name}_copy"
        counter = 1
        while new_name in self._variables:
            new_name = f"{name}_copy{counter}"
            counter += 1

        duplicate = variable.copy()
        duplicate["name"] = new_name

        self._add_variable_to_table(duplicate)
        self._variables[new_name] = duplicate
        self.variables_changed.emit(self._variables)
        logger.debug(f"Duplicated variable: {name} -> {new_name}")

    def _on_import_variables(self) -> None:
        """Import variables from JSON file."""
        from PySide6.QtWidgets import QFileDialog
        import json

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Variables",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    for name, var_data in data.items():
                        if isinstance(var_data, dict) and "type" in var_data:
                            variable = {
                                "name": name,
                                "type": var_data.get("type", "String"),
                                "default_value": var_data.get("default_value", ""),
                                "description": var_data.get("description", ""),
                            }
                            self._variables[name] = variable
                            self._add_variable_to_table(variable)

                self.variables_changed.emit(self._variables)
                logger.info(f"Imported variables from {file_path}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Failed to import variables:\n{str(e)}"
                )
                logger.error(f"Failed to import variables: {e}")

    def _on_export_variables(self) -> None:
        """Export variables to JSON file."""
        from PySide6.QtWidgets import QFileDialog
        import json

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Variables",
            "variables.json",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if file_path:
            try:
                export_data = {}
                for name, var in self._variables.items():
                    export_data[name] = {
                        "type": var.get("type", "String"),
                        "default_value": var.get("default_value", ""),
                        "description": var.get("description", ""),
                    }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)

                logger.info(f"Exported variables to {file_path}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export variables:\n{str(e)}"
                )
                logger.error(f"Failed to export variables: {e}")

    def _add_variable_to_table(self, variable: Dict[str, Any]) -> None:
        """Add a variable to the table."""
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._update_row(row, variable)

    def _update_row(self, row: int, variable: Dict[str, Any]) -> None:
        """Update a table row with variable data."""
        name_item = QTableWidgetItem(variable.get("name", ""))
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        type_item = QTableWidgetItem(variable.get("type", "String"))
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        default_val = variable.get("default_value", "")
        default_item = QTableWidgetItem(self._format_value(default_val))
        default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Current value - initially same as default
        current_item = QTableWidgetItem(self._format_value(default_val))
        current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        current_item.setForeground(QBrush(QColor("#888888")))

        desc_item = QTableWidgetItem(variable.get("description", ""))
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self._table.setItem(row, self.COL_NAME, name_item)
        self._table.setItem(row, self.COL_TYPE, type_item)
        self._table.setItem(row, self.COL_DEFAULT, default_item)
        self._table.setItem(row, self.COL_CURRENT, current_item)
        self._table.setItem(row, self.COL_DESCRIPTION, desc_item)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "(None)"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (list, dict)):
            import json
            try:
                return json.dumps(value, default=str)
            except Exception:
                return str(value)
        return str(value)

    # ==================== Public API ====================

    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set the workflow variables.

        Args:
            variables: Dict of variable definitions
        """
        self._variables = {}
        self._table.setRowCount(0)

        for name, var_data in variables.items():
            if isinstance(var_data, dict):
                variable = {
                    "name": name,
                    "type": var_data.get("type", "String"),
                    "default_value": var_data.get("default_value", ""),
                    "description": var_data.get("description", ""),
                }
            else:
                # Simple value format
                variable = {
                    "name": name,
                    "type": self._infer_type(var_data),
                    "default_value": var_data,
                    "description": "",
                }

            self._variables[name] = variable
            self._add_variable_to_table(variable)

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
        for row in range(self._table.rowCount()):
            name = self._table.item(row, self.COL_NAME).text()
            if name in values:
                current_item = self._table.item(row, self.COL_CURRENT)
                if current_item:
                    current_item.setText(self._format_value(values[name]))
                    current_item.setForeground(QBrush(QColor("#4CAF50")))

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Switch between design and runtime mode.

        Args:
            enabled: True for runtime mode
        """
        self._is_runtime_mode = enabled

        # Update UI
        if enabled:
            self._mode_label.setText("Runtime Mode")
            self._mode_label.setStyleSheet("color: #FFA500; font-weight: bold;")
        else:
            self._mode_label.setText("Design Mode")
            self._mode_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Disable editing buttons in runtime mode
        self._add_btn.setEnabled(not enabled)
        self._edit_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
        self._import_btn.setEnabled(not enabled)
        self._export_btn.setEnabled(not enabled)

        # Reset current values when entering runtime mode
        if enabled:
            for row in range(self._table.rowCount()):
                current_item = self._table.item(row, self.COL_CURRENT)
                default_item = self._table.item(row, self.COL_DEFAULT)
                if current_item and default_item:
                    current_item.setText(default_item.text())
                    current_item.setForeground(QBrush(QColor("#888888")))

    def clear(self) -> None:
        """Clear all variables."""
        self._variables = {}
        self._table.setRowCount(0)

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
