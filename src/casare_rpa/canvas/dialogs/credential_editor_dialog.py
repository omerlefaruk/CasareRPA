"""
CasareRPA - Credential Editor Dialog
Dialog for managing credential bindings (global or project-scoped).
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QWidget,
    QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..theme import THEME
from ...project.project_manager import get_project_manager
from casare_rpa.domain.project_schema import CredentialBinding


class CredentialEditorDialog(QDialog):
    """
    Dialog for editing credential bindings.

    Supports both global and project-scoped credentials.
    """

    CREDENTIAL_TYPES = [
        "username_password",
        "api_key",
        "oauth2_token",
        "ssh_key",
        "certificate",
        "custom",
    ]

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

        title = "Global Credentials" if scope == "global" else "Project Credentials"
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._load_credentials()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_text = (
            "Global Credentials" if self._scope == "global" else "Project Credentials"
        )
        header = QLabel(header_text)
        header.setFont(QFont(header.font().family(), 14, QFont.Bold))
        layout.addWidget(header)

        # Description
        if self._scope == "global":
            desc = (
                "Global credential bindings are available across all projects. "
                "Map friendly aliases to HashiCorp Vault paths."
            )
        else:
            desc = (
                "Project credential bindings are available to all scenarios in this project. "
                "They override global bindings with the same alias."
            )
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Add credential form
        add_group = QGroupBox("Add Credential Binding")
        add_layout = QFormLayout(add_group)
        add_layout.setSpacing(8)

        self._alias_input = QLineEdit()
        self._alias_input.setPlaceholderText("e.g., erp_login, api_key")
        add_layout.addRow("Alias:", self._alias_input)

        self._vault_path_input = QLineEdit()
        self._vault_path_input.setPlaceholderText("e.g., secret/prod/erp/credentials")
        add_layout.addRow("Vault Path:", self._vault_path_input)

        self._type_combo = QComboBox()
        self._type_combo.addItems(self.CREDENTIAL_TYPES)
        add_layout.addRow("Type:", self._type_combo)

        self._description_input = QLineEdit()
        self._description_input.setPlaceholderText("Description (optional)")
        add_layout.addRow("Description:", self._description_input)

        self._required_checkbox = QCheckBox("Required for workflow execution")
        self._required_checkbox.setChecked(True)
        add_layout.addRow("", self._required_checkbox)

        # Add button
        add_btn_row = QHBoxLayout()
        add_btn_row.addStretch()
        self._add_btn = QPushButton("Add Credential")
        self._add_btn.clicked.connect(self._on_add_credential)
        add_btn_row.addWidget(self._add_btn)
        add_layout.addRow("", add_btn_row)

        layout.addWidget(add_group)

        # Credentials table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Alias", "Vault Path", "Type", "Required", "Actions"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
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
        self._alias_input.returnPressed.connect(self._on_add_credential)
        self._vault_path_input.returnPressed.connect(self._on_add_credential)

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
        """)

    def _load_credentials(self) -> None:
        """Load credentials into the table."""
        self._table.setRowCount(0)

        if self._scope == "global":
            credentials = self._manager.get_global_credentials()
        else:
            credentials = self._manager.get_project_credentials()

        for alias, binding in credentials.items():
            self._add_table_row(binding)

    def _add_table_row(self, binding: CredentialBinding) -> None:
        """Add a row to the table."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Alias
        alias_item = QTableWidgetItem(binding.alias)
        alias_item.setFlags(alias_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, 0, alias_item)

        # Vault Path
        path_item = QTableWidgetItem(binding.vault_path)
        path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
        path_item.setToolTip(binding.description or binding.vault_path)
        self._table.setItem(row, 1, path_item)

        # Type
        type_item = QTableWidgetItem(binding.credential_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, 2, type_item)

        # Required
        required_item = QTableWidgetItem("Yes" if binding.required else "No")
        required_item.setFlags(required_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, 3, required_item)

        # Actions - Delete button
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        actions_layout.setSpacing(4)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(
            lambda checked, a=binding.alias: self._on_delete_credential(a)
        )
        actions_layout.addWidget(delete_btn)

        self._table.setCellWidget(row, 4, actions_widget)

    def _on_add_credential(self) -> None:
        """Handle add credential button."""
        alias = self._alias_input.text().strip()
        vault_path = self._vault_path_input.text().strip()
        cred_type = self._type_combo.currentText()
        description = self._description_input.text().strip()
        required = self._required_checkbox.isChecked()

        if not alias:
            QMessageBox.warning(self, "Invalid Input", "Please enter an alias.")
            self._alias_input.setFocus()
            return

        if not vault_path:
            QMessageBox.warning(self, "Invalid Input", "Please enter a Vault path.")
            self._vault_path_input.setFocus()
            return

        # Validate alias (alphanumeric and underscore only)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", alias):
            QMessageBox.warning(
                self,
                "Invalid Alias",
                "Alias must start with a letter or underscore, "
                "and contain only letters, numbers, and underscores.",
            )
            self._alias_input.setFocus()
            return

        # Create binding
        binding = CredentialBinding(
            alias=alias,
            vault_path=vault_path,
            credential_type=cred_type,
            description=description,
            required=required,
        )

        # Add to manager
        try:
            if self._scope == "global":
                self._manager.set_global_credential(binding)
            else:
                self._manager.set_project_credential(binding)

            # Clear inputs
            self._alias_input.clear()
            self._vault_path_input.clear()
            self._type_combo.setCurrentIndex(0)
            self._description_input.clear()
            self._required_checkbox.setChecked(True)
            self._alias_input.setFocus()

            # Reload table
            self._load_credentials()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add credential: {e}")

    def _on_delete_credential(self, alias: str) -> None:
        """Handle delete credential."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete credential binding '{alias}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if self._scope == "global":
                    self._manager.remove_global_credential(alias)
                else:
                    self._manager.remove_project_credential(alias)
                self._load_credentials()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete credential: {e}")
