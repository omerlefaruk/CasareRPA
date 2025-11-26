"""
CasareRPA - Variable Editor Dialog
Dialog for managing variables (global or project-scoped).
"""

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..theme import THEME
from ...project.project_manager import get_project_manager
from ...core.project_schema import ProjectVariable


class VariableEditorDialog(QDialog):
    """
    Dialog for editing variables.

    Supports both global and project-scoped variables.
    """

    VARIABLE_TYPES = ["String", "Integer", "Float", "Boolean", "List", "Dict"]

    def __init__(self, scope: str = "global", parent: Optional[QWidget] = None):
        """
        Initialize the dialog.

        Args:
            scope: "global" or "project"
            parent: Parent widget
        """
        super().__init__(parent)

        self._scope = scope
        self._manager = get_project_manager()

        title = "Global Variables" if scope == "global" else "Project Variables"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._load_variables()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_text = (
            "Global Variables" if self._scope == "global"
            else f"Project Variables"
        )
        header = QLabel(header_text)
        header.setFont(QFont(header.font().family(), 14, QFont.Bold))
        layout.addWidget(header)

        # Description
        if self._scope == "global":
            desc = "Global variables are available across all projects and scenarios."
        else:
            desc = "Project variables are available to all scenarios in this project."
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Add variable row
        add_row = QHBoxLayout()

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Variable name")
        self._name_input.setMinimumWidth(150)
        add_row.addWidget(self._name_input)

        self._value_input = QLineEdit()
        self._value_input.setPlaceholderText("Value")
        self._value_input.setMinimumWidth(200)
        add_row.addWidget(self._value_input)

        self._type_combo = QComboBox()
        self._type_combo.addItems(self.VARIABLE_TYPES)
        self._type_combo.setMinimumWidth(100)
        add_row.addWidget(self._type_combo)

        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._on_add_variable)
        add_row.addWidget(self._add_btn)

        layout.addLayout(add_row)

        # Variables table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Name", "Value", "Type", "Actions"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # Bottom buttons
        button_row = QHBoxLayout()
        button_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

        # Connect enter key
        self._name_input.returnPressed.connect(self._on_add_variable)
        self._value_input.returnPressed.connect(self._on_add_variable)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}

            QLineEdit, QComboBox {{
                background: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 8px;
            }}

            QLineEdit:focus, QComboBox:focus {{
                border-color: {THEME.border_focus};
            }}

            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {THEME.text_muted};
            }}

            QTableWidget {{
                background: {THEME.bg_dark};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                gridline-color: {THEME.border};
            }}

            QTableWidget::item {{
                padding: 8px;
            }}

            QTableWidget::item:selected {{
                background: {THEME.bg_selected};
            }}

            QTableWidget::item:alternate {{
                background: {THEME.bg_darkest};
            }}

            QHeaderView::section {{
                background: {THEME.bg_medium};
                color: {THEME.text_header};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {THEME.border};
                font-weight: bold;
            }}

            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 60px;
            }}

            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}

            QPushButton:pressed {{
                background: {THEME.accent_primary};
            }}

            QLabel {{
                color: {THEME.text_primary};
            }}
        """)

    def _load_variables(self) -> None:
        """Load variables into the table."""
        self._table.setRowCount(0)

        if self._scope == "global":
            variables = self._manager.get_global_variables()
        else:
            variables = self._manager.get_project_variables()

        for name, var_data in variables.items():
            self._add_table_row(name, var_data)

    def _add_table_row(self, name: str, variable: ProjectVariable) -> None:
        """Add a row to the table."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Name
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, 0, name_item)

        # Value
        value = variable.default_value
        if isinstance(value, (list, dict)):
            import json
            value = json.dumps(value)
        value_item = QTableWidgetItem(str(value))
        self._table.setItem(row, 1, value_item)

        # Type
        var_type = variable.type
        type_item = QTableWidgetItem(var_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, 2, type_item)

        # Actions - Delete button
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        actions_layout.setSpacing(4)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(lambda checked, n=name: self._on_delete_variable(n))
        actions_layout.addWidget(delete_btn)

        self._table.setCellWidget(row, 3, actions_widget)

    def _on_add_variable(self) -> None:
        """Handle add variable button."""
        name = self._name_input.text().strip()
        value = self._value_input.text().strip()
        var_type = self._type_combo.currentText()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a variable name.")
            self._name_input.setFocus()
            return

        # Validate name (alphanumeric and underscore only)
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            QMessageBox.warning(
                self, "Invalid Name",
                "Variable name must start with a letter or underscore, "
                "and contain only letters, numbers, and underscores."
            )
            self._name_input.setFocus()
            return

        # Convert value based on type
        try:
            converted_value = self._convert_value(value, var_type)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Value", str(e))
            self._value_input.setFocus()
            return

        # Create variable object
        variable = ProjectVariable(
            name=name,
            type=var_type,
            default_value=converted_value,
        )

        # Add to manager
        try:
            if self._scope == "global":
                self._manager.set_global_variable(variable)
            else:
                self._manager.set_project_variable(variable)

            # Clear inputs
            self._name_input.clear()
            self._value_input.clear()
            self._type_combo.setCurrentIndex(0)
            self._name_input.setFocus()

            # Reload table
            self._load_variables()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add variable: {e}")

    def _convert_value(self, value: str, var_type: str) -> Any:
        """Convert string value to the specified type."""
        if var_type == "String":
            return value
        elif var_type == "Integer":
            try:
                return int(value) if value else 0
            except ValueError:
                raise ValueError(f"'{value}' is not a valid integer.")
        elif var_type == "Float":
            try:
                return float(value) if value else 0.0
            except ValueError:
                raise ValueError(f"'{value}' is not a valid float.")
        elif var_type == "Boolean":
            return value.lower() in ("true", "yes", "1", "on")
        elif var_type == "List":
            import json
            try:
                result = json.loads(value) if value else []
                if not isinstance(result, list):
                    raise ValueError("Value must be a JSON array.")
                return result
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON array. Example: [\"a\", \"b\", \"c\"]")
        elif var_type == "Dict":
            import json
            try:
                result = json.loads(value) if value else {}
                if not isinstance(result, dict):
                    raise ValueError("Value must be a JSON object.")
                return result
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON object. Example: {\"key\": \"value\"}")
        return value

    def _on_delete_variable(self, name: str) -> None:
        """Handle delete variable."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete variable '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if self._scope == "global":
                    self._manager.remove_global_variable(name)
                else:
                    self._manager.remove_project_variable(name)
                self._load_variables()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete variable: {e}")
