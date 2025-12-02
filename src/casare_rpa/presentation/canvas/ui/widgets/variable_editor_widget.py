"""
Variable Editor Widget UI Component.

Provides inline variable editing functionality.
"""

from typing import Optional, Any, Dict

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
)
from PySide6.QtCore import Signal

from loguru import logger
from ..base_widget import BaseWidget


class VariableEditorWidget(BaseWidget):
    """
    Widget for editing a single variable.

    Features:
    - Variable name input
    - Type selection
    - Value input
    - Validation

    Signals:
        variable_changed: Emitted when variable changes (str: name, str: type, Any: value)
    """

    variable_changed = Signal(str, str, object)

    def __init__(
        self,
        name: str = "",
        var_type: str = "String",
        value: Any = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize variable editor widget.

        Args:
            name: Variable name
            var_type: Variable type
            value: Variable value
            parent: Optional parent widget
        """
        self._var_name = name
        self._var_type = var_type
        self._var_value = value

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Name input
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Variable name")
        self._name_edit.setText(self._var_name)
        self._name_edit.setMinimumWidth(150)
        self._name_edit.textChanged.connect(self._on_value_changed)
        layout.addWidget(self._name_edit)

        # Type selector
        self._type_combo = QComboBox()
        self._type_combo.addItems(
            [
                "String",
                "Integer",
                "Float",
                "Boolean",
                "List",
                "Dict",
                "DataTable",
            ]
        )
        self._type_combo.setCurrentText(self._var_type)
        self._type_combo.setMinimumWidth(100)
        self._type_combo.currentTextChanged.connect(self._on_value_changed)
        layout.addWidget(self._type_combo)

        # Value input
        self._value_edit = QLineEdit()
        self._value_edit.setPlaceholderText("Value")
        self._value_edit.setText(str(self._var_value))
        self._value_edit.textChanged.connect(self._on_value_changed)
        layout.addWidget(self._value_edit)

        # Remove button
        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(24, 24)
        self._remove_btn.setToolTip("Remove variable")
        self._remove_btn.setStyleSheet("""
            QPushButton {
                background: #d32f2f;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background: #f44336;
            }
        """)
        layout.addWidget(self._remove_btn)

    def _on_value_changed(self) -> None:
        """Handle value change in any field."""
        name = self._name_edit.text()
        var_type = self._type_combo.currentText()
        value = self._value_edit.text()

        # Convert value based on type
        converted_value = self._convert_value(value, var_type)

        self.variable_changed.emit(name, var_type, converted_value)
        logger.debug(f"Variable changed: {name} ({var_type}) = {converted_value}")

    def _convert_value(self, value: str, var_type: str) -> Any:
        """
        Convert string value to appropriate type.

        Args:
            value: String value
            var_type: Target variable type

        Returns:
            Converted value
        """
        try:
            if var_type == "Integer":
                return int(value) if value else 0
            elif var_type == "Float":
                return float(value) if value else 0.0
            elif var_type == "Boolean":
                return value.lower() in ("true", "1", "yes")
            elif var_type == "List":
                if value.startswith("[") and value.endswith("]"):
                    import json

                    return json.loads(value)
                return [item.strip() for item in value.split(",") if item.strip()]
            elif var_type == "Dict":
                if value.startswith("{") and value.endswith("}"):
                    import json

                    return json.loads(value)
                return {}
            else:
                return value
        except Exception as e:
            logger.warning(f"Failed to convert value: {e}")
            return value

    def get_variable(self) -> Dict[str, Any]:
        """
        Get variable data.

        Returns:
            Dictionary with name, type, and value
        """
        return {
            "name": self._name_edit.text(),
            "type": self._type_combo.currentText(),
            "value": self._convert_value(
                self._value_edit.text(), self._type_combo.currentText()
            ),
        }

    def set_variable(self, name: str, var_type: str, value: Any) -> None:
        """
        Set variable data.

        Args:
            name: Variable name
            var_type: Variable type
            value: Variable value
        """
        self._name_edit.setText(name)
        self._type_combo.setCurrentText(var_type)
        self._value_edit.setText(str(value))

    def get_remove_button(self) -> QPushButton:
        """
        Get the remove button for connecting signals.

        Returns:
            Remove button widget
        """
        return self._remove_btn
