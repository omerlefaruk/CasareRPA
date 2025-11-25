"""
CasareRPA - Parameter Naming Dialog
Dialog for naming and configuring snippet parameters when exposing properties.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QCheckBox, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from loguru import logger


class ParameterNamingDialog(QDialog):
    """
    Dialog for configuring a new snippet parameter.

    Prompts user for:
    - Parameter name (snake_case identifier)
    - Description (user-friendly explanation)
    - Required checkbox (whether parameter must be provided)
    """

    def __init__(self, node_id: str, property_key: str, property_type: str,
                 current_value: Optional[object] = None, parent=None):
        """
        Initialize parameter naming dialog.

        Args:
            node_id: ID of the node containing the property
            property_key: Key of the property being exposed
            property_type: Data type of the property
            current_value: Current value of the property
            parent: Parent widget
        """
        super().__init__(parent)

        self.node_id = node_id
        self.property_key = property_key
        self.property_type = property_type
        self.current_value = current_value

        self.setWindowTitle("Expose Property as Parameter")
        self.setModal(True)
        self.resize(500, 300)

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Info section
        info_label = QLabel(
            f"<b>Exposing property:</b> {self.property_key}<br>"
            f"<b>From node:</b> {self.node_id}<br>"
            f"<b>Type:</b> {self.property_type}"
        )
        info_label.setStyleSheet("color: #CCCCCC; padding: 8px; background: #2A2A2A; border-radius: 4px;")
        layout.addWidget(info_label)

        # Form
        form_layout = QFormLayout()

        # Parameter name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., website_url, max_retries")
        self.name_edit.setText(self._suggest_parameter_name())
        form_layout.addRow("Parameter Name*:", self.name_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Describe what this parameter controls...\n"
            "Example: URL of the website to navigate to"
        )
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_edit)

        # Required checkbox
        self.required_check = QCheckBox("Required parameter")
        self.required_check.setChecked(True)
        self.required_check.setToolTip("If checked, users must provide a value for this parameter")
        form_layout.addRow("", self.required_check)

        # Default value display (read-only)
        self.default_value_label = QLabel(str(self.current_value) if self.current_value is not None else "(none)")
        self.default_value_label.setStyleSheet("color: #888888; font-style: italic;")
        form_layout.addRow("Current Value:", self.default_value_label)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Parameter")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._on_create)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

        # Style
        self.setStyleSheet("""
            QDialog {
                background: #1E1E1E;
            }
            QLabel {
                color: #CCCCCC;
            }
            QLineEdit, QTextEdit {
                background: #252526;
                border: 1px solid #3E3E42;
                border-radius: 3px;
                color: #CCCCCC;
                padding: 4px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #007ACC;
            }
            QPushButton {
                background: #0E639C;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #1177BB;
            }
            QPushButton:pressed {
                background: #005A9E;
            }
            QCheckBox {
                color: #CCCCCC;
            }
        """)

    def _suggest_parameter_name(self) -> str:
        """
        Suggest a parameter name based on the property key.

        Returns:
            Suggested parameter name in snake_case
        """
        # Convert property_key to snake_case suggestion
        suggested = self.property_key.lower().replace(' ', '_').replace('-', '_')

        # Remove special characters
        suggested = ''.join(c for c in suggested if c.isalnum() or c == '_')

        return suggested

    def _on_create(self):
        """Handle create button click - validate and accept."""
        param_name = self.name_edit.text().strip()

        if not param_name:
            # TODO: Show validation error
            logger.warning("Parameter name is required")
            return

        # Validate name format (should be valid identifier)
        if not param_name.replace('_', '').isalnum():
            logger.warning(f"Invalid parameter name: {param_name}")
            return

        self.accept()

    # Getters for results

    def get_parameter_name(self) -> str:
        """Get the entered parameter name."""
        return self.name_edit.text().strip()

    def get_description(self) -> str:
        """Get the entered description."""
        return self.description_edit.toPlainText().strip()

    def is_required(self) -> bool:
        """Check if parameter is marked as required."""
        return self.required_check.isChecked()

    def get_default_value(self) -> Optional[object]:
        """Get the default value (current value)."""
        return self.current_value
