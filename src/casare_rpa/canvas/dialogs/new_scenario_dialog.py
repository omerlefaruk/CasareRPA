"""
CasareRPA - New Scenario Dialog
Dialog for creating a new scenario within a project.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QDialogButtonBox,
    QGroupBox,
    QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..theme import THEME


class NewScenarioDialog(QDialog):
    """
    Dialog for creating a new scenario within a project.

    Collects:
    - Scenario name
    - Scenario description
    - Option to copy current canvas content
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New Scenario")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Create New Scenario")
        header.setFont(QFont(header.font().family(), 14, QFont.Bold))
        layout.addWidget(header)

        # Info text
        info = QLabel(
            "A scenario bundles a workflow with specific variable values "
            "and credential bindings for a particular run configuration."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info)

        # Form section
        form_group = QGroupBox("Scenario Details")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)

        # Name input
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Invoice Processing - Production")
        form_layout.addRow("Name:", self._name_input)

        # Description input
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText(
            "Describe this scenario's purpose, input data, or special conditions..."
        )
        self._description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self._description_input)

        layout.addWidget(form_group)

        # Options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self._copy_canvas_checkbox = QCheckBox("Copy current canvas workflow")
        self._copy_canvas_checkbox.setToolTip(
            "If checked, the new scenario will contain a copy of the current canvas. "
            "Otherwise, it will start empty."
        )
        self._copy_canvas_checkbox.setChecked(True)
        options_layout.addWidget(self._copy_canvas_checkbox)

        self._copy_variables_checkbox = QCheckBox("Include current variable values")
        self._copy_variables_checkbox.setToolTip(
            "If checked, the current Variable Tab values will be saved as scenario defaults."
        )
        self._copy_variables_checkbox.setChecked(True)
        options_layout.addWidget(self._copy_variables_checkbox)

        layout.addWidget(options_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        self._ok_button = button_box.button(QDialogButtonBox.Ok)
        self._ok_button.setText("Create Scenario")
        self._ok_button.setEnabled(False)

        layout.addWidget(button_box)

        # Focus on name input
        self._name_input.setFocus()

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._name_input.textChanged.connect(self._on_input_changed)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}

            QGroupBox {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {THEME.text_header};
            }}

            QLineEdit, QTextEdit {{
                background: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 8px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border-color: {THEME.border_focus};
            }}

            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }}

            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}

            QPushButton:pressed {{
                background: {THEME.accent_primary};
            }}

            QPushButton:disabled {{
                background: {THEME.bg_dark};
                color: {THEME.text_disabled};
            }}

            QLabel {{
                color: {THEME.text_primary};
            }}

            QCheckBox {{
                color: {THEME.text_primary};
                spacing: 8px;
            }}

            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {THEME.border};
                border-radius: 3px;
                background: {THEME.bg_darkest};
            }}

            QCheckBox::indicator:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}

            QCheckBox::indicator:hover {{
                border-color: {THEME.border_focus};
            }}
        """)

    def _on_input_changed(self) -> None:
        """Handle input change - validate."""
        is_valid = self._validate()
        self._ok_button.setEnabled(is_valid)

    def _validate(self) -> bool:
        """Validate inputs."""
        name = self._name_input.text().strip()
        return len(name) > 0

    def _on_accept(self) -> None:
        """Handle accept button click."""
        if self._validate():
            self.accept()

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_name(self) -> str:
        """Get the scenario name."""
        return self._name_input.text().strip()

    def get_description(self) -> str:
        """Get the scenario description."""
        return self._description_input.toPlainText().strip()

    def should_copy_canvas(self) -> bool:
        """Check if canvas should be copied."""
        return self._copy_canvas_checkbox.isChecked()

    def should_copy_variables(self) -> bool:
        """Check if variables should be copied."""
        return self._copy_variables_checkbox.isChecked()
