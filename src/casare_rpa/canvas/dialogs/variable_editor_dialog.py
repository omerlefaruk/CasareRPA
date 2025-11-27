"""
Variable Editor Dialog for the Bottom Panel.

Dialog for adding and editing workflow variables with type-specific editors.
"""

from typing import Optional, Dict, Any, List
import json

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QWidget,
    QStackedWidget,
)


# Variable types
VARIABLE_TYPES = [
    "String",
    "Integer",
    "Float",
    "Boolean",
    "List",
    "Dict",
    "DataTable",
]


class VariableEditorDialog(QDialog):
    """
    Dialog for adding or editing a workflow variable.

    Provides type-specific editors for each variable type.
    """

    def __init__(
        self,
        variable: Optional[Dict[str, Any]] = None,
        existing_names: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the dialog.

        Args:
            variable: Existing variable to edit, or None for new
            existing_names: List of existing variable names (for validation)
            parent: Parent widget
        """
        super().__init__(parent)

        self._variable = variable
        self._existing_names = existing_names or []
        self._is_edit_mode = variable is not None

        self._setup_ui()
        self._apply_styles()

        if variable:
            self._load_variable(variable)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Edit Variable" if self._is_edit_mode else "Add Variable")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Form layout for fields
        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter variable name")
        form.addRow("Name:", self._name_edit)

        # Type dropdown
        self._type_combo = QComboBox()
        self._type_combo.addItems(VARIABLE_TYPES)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type:", self._type_combo)

        layout.addLayout(form)

        # Value editor section
        value_label = QLabel("Default Value:")
        layout.addWidget(value_label)

        # Stacked widget for different value editors
        self._value_stack = QStackedWidget()
        self._setup_value_editors()
        layout.addWidget(self._value_stack)

        # Description field
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)

        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(60)
        self._description_edit.setPlaceholderText(
            "Optional description for this variable"
        )
        layout.addWidget(self._description_edit)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_accept)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _setup_value_editors(self) -> None:
        """Create value editors for each type."""
        # String editor
        self._string_edit = QLineEdit()
        self._string_edit.setPlaceholderText("Enter text value")
        self._value_stack.addWidget(self._string_edit)

        # Integer editor
        self._int_edit = QSpinBox()
        self._int_edit.setRange(-2147483648, 2147483647)
        self._value_stack.addWidget(self._int_edit)

        # Float editor
        self._float_edit = QDoubleSpinBox()
        self._float_edit.setRange(-1e10, 1e10)
        self._float_edit.setDecimals(6)
        self._value_stack.addWidget(self._float_edit)

        # Boolean editor
        bool_container = QWidget()
        bool_layout = QHBoxLayout(bool_container)
        bool_layout.setContentsMargins(0, 0, 0, 0)
        self._bool_check = QCheckBox("True")
        bool_layout.addWidget(self._bool_check)
        bool_layout.addStretch()
        self._value_stack.addWidget(bool_container)

        # List editor (JSON)
        self._list_edit = QTextEdit()
        self._list_edit.setPlaceholderText(
            'Enter JSON array, e.g.: ["item1", "item2", 3]'
        )
        self._list_edit.setMaximumHeight(80)
        self._value_stack.addWidget(self._list_edit)

        # Dict editor (JSON)
        self._dict_edit = QTextEdit()
        self._dict_edit.setPlaceholderText('Enter JSON object, e.g.: {"key": "value"}')
        self._dict_edit.setMaximumHeight(80)
        self._value_stack.addWidget(self._dict_edit)

        # DataTable editor (placeholder)
        datatable_container = QWidget()
        dt_layout = QVBoxLayout(datatable_container)
        dt_layout.setContentsMargins(0, 0, 0, 0)
        dt_label = QLabel(
            "DataTable variables are initialized as empty.\nLoad data at runtime using nodes."
        )
        dt_label.setStyleSheet("color: #888888; font-style: italic;")
        dt_layout.addWidget(dt_label)
        self._value_stack.addWidget(datatable_container)

    def _on_type_changed(self, type_name: str) -> None:
        """Handle type change."""
        type_indices = {
            "String": 0,
            "Integer": 1,
            "Float": 2,
            "Boolean": 3,
            "List": 4,
            "Dict": 5,
            "DataTable": 6,
        }
        self._value_stack.setCurrentIndex(type_indices.get(type_name, 0))

    def _load_variable(self, variable: Dict[str, Any]) -> None:
        """Load variable data into the form."""
        self._name_edit.setText(variable.get("name", ""))
        self._description_edit.setText(variable.get("description", ""))

        var_type = variable.get("type", "String")
        index = self._type_combo.findText(var_type)
        if index >= 0:
            self._type_combo.setCurrentIndex(index)

        default_value = variable.get("default_value", "")
        self._set_value(var_type, default_value)

    def _set_value(self, var_type: str, value: Any) -> None:
        """Set the value in the appropriate editor."""
        if var_type == "String":
            self._string_edit.setText(str(value) if value else "")
        elif var_type == "Integer":
            try:
                self._int_edit.setValue(int(value) if value else 0)
            except (ValueError, TypeError):
                self._int_edit.setValue(0)
        elif var_type == "Float":
            try:
                self._float_edit.setValue(float(value) if value else 0.0)
            except (ValueError, TypeError):
                self._float_edit.setValue(0.0)
        elif var_type == "Boolean":
            self._bool_check.setChecked(bool(value))
        elif var_type == "List":
            if isinstance(value, list):
                self._list_edit.setText(json.dumps(value, indent=2))
            elif value:
                self._list_edit.setText(str(value))
            else:
                self._list_edit.setText("[]")
        elif var_type == "Dict":
            if isinstance(value, dict):
                self._dict_edit.setText(json.dumps(value, indent=2))
            elif value:
                self._dict_edit.setText(str(value))
            else:
                self._dict_edit.setText("{}")

    def _get_value(self) -> Any:
        """Get the value from the current editor."""
        var_type = self._type_combo.currentText()

        if var_type == "String":
            return self._string_edit.text()
        elif var_type == "Integer":
            return self._int_edit.value()
        elif var_type == "Float":
            return self._float_edit.value()
        elif var_type == "Boolean":
            return self._bool_check.isChecked()
        elif var_type == "List":
            text = self._list_edit.toPlainText().strip()
            if not text:
                return []
            try:
                value = json.loads(text)
                if not isinstance(value, list):
                    raise ValueError("Value must be a list")
                return value
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        elif var_type == "Dict":
            text = self._dict_edit.toPlainText().strip()
            if not text:
                return {}
            try:
                value = json.loads(text)
                if not isinstance(value, dict):
                    raise ValueError("Value must be a dictionary")
                return value
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        elif var_type == "DataTable":
            return None

        return ""

    def _validate(self) -> bool:
        """Validate the form input."""
        name = self._name_edit.text().strip()

        # Check name is provided
        if not name:
            QMessageBox.warning(self, "Validation Error", "Variable name is required.")
            self._name_edit.setFocus()
            return False

        # Check name is valid identifier
        if not name.isidentifier():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Variable name must be a valid identifier "
                "(letters, numbers, and underscores, not starting with a number).",
            )
            self._name_edit.setFocus()
            return False

        # Check name is unique
        if name in self._existing_names:
            QMessageBox.warning(
                self, "Validation Error", f"A variable named '{name}' already exists."
            )
            self._name_edit.setFocus()
            return False

        # Validate value
        try:
            self._get_value()
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid default value: {e}")
            return False

        return True

    def _on_accept(self) -> None:
        """Handle OK button click."""
        if self._validate():
            self.accept()

    def get_variable(self) -> Dict[str, Any]:
        """
        Get the variable definition.

        Returns:
            Variable definition dict
        """
        return {
            "name": self._name_edit.text().strip(),
            "type": self._type_combo.currentText(),
            "default_value": self._get_value(),
            "description": self._description_edit.toPlainText().strip(),
        }

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #d4d4d4;
            }
            QLabel {
                color: #cccccc;
            }
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
            QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #4b6eaf;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QPushButton {
                background-color: #4b6eaf;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a7fc0;
            }
            QCheckBox {
                color: #cccccc;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
