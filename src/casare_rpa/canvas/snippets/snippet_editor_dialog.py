"""
CasareRPA - Snippet Editor Dialog
UI for editing existing snippet metadata and configuration.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QListWidget,
)
from loguru import logger

from ...core.snippet_definition import SnippetDefinition
from ...core.snippet_library import get_snippet_library


class SnippetEditorDialog(QDialog):
    """
    Dialog for editing existing snippet metadata.

    Features:
    - Edit name, description, category, author
    - Modify variable scope settings
    - Update tags
    - View snippet structure (read-only)
    - Save changes with version bumping
    """

    def __init__(self, snippet_definition: SnippetDefinition, parent=None):
        """
        Initialize snippet editor dialog.

        Args:
            snippet_definition: The snippet to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.snippet = snippet_definition
        self.library = get_snippet_library()

        self.setWindowTitle(f"Edit Snippet: {snippet_definition.name}")
        self.setModal(True)
        self.resize(700, 600)

        self._init_ui()
        self._populate_from_snippet()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Metadata section
        metadata_group = QGroupBox("Snippet Metadata")
        metadata_layout = QFormLayout()

        self.name_edit = QLineEdit()
        metadata_layout.addRow("Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        metadata_layout.addRow("Description:", self.description_edit)

        self.category_combo = QComboBox()
        self._populate_categories()
        self.category_combo.setEditable(True)
        metadata_layout.addRow("Category:", self.category_combo)

        self.author_edit = QLineEdit()
        metadata_layout.addRow("Author:", self.author_edit)

        # Version info (read-only)
        self.version_label = QLabel()
        self.version_label.setStyleSheet("color: #888;")
        metadata_layout.addRow("Current Version:", self.version_label)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Tags section
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()

        tags_info = QLabel("Enter tags separated by commas (e.g., web, automation, data)")
        tags_info.setStyleSheet("color: #888; font-size: 9pt;")
        tags_layout.addWidget(tags_info)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        tags_layout.addWidget(self.tags_edit)

        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        # Variable scope section
        scope_group = QGroupBox("Variable Scope")
        scope_layout = QVBoxLayout()

        self.inherit_scope_check = QCheckBox("Inherit parent workflow variables")
        self.inherit_scope_check.setToolTip(
            "If checked, the snippet can access variables from the parent workflow"
        )
        scope_layout.addWidget(self.inherit_scope_check)

        self.export_vars_check = QCheckBox("Export local variables back to parent")
        self.export_vars_check.setToolTip(
            "If checked, variables created/modified in the snippet will be visible to the parent workflow"
        )
        scope_layout.addWidget(self.export_vars_check)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Structure info (read-only)
        structure_group = QGroupBox("Snippet Structure (Read-Only)")
        structure_layout = QVBoxLayout()

        self.structure_label = QLabel()
        self.structure_label.setWordWrap(True)
        self.structure_label.setStyleSheet(
            "background: #2a2a2a; padding: 8px; border-radius: 4px;"
        )
        structure_layout.addWidget(self.structure_label)

        # Parameters list
        params_label = QLabel("Parameters:")
        params_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        structure_layout.addWidget(params_label)

        self.params_list = QListWidget()
        self.params_list.setMaximumHeight(100)
        self.params_list.setStyleSheet("background: #2a2a2a;")
        structure_layout.addWidget(self.params_list)

        structure_group.setLayout(structure_layout)
        layout.addWidget(structure_group)

        # Dialog buttons
        button_layout = QHBoxLayout()

        # Info about version bumping
        version_info = QLabel("💡 Saving will increment the patch version")
        version_info.setStyleSheet("color: #888; font-size: 9pt; font-style: italic;")
        button_layout.addWidget(version_info)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _populate_categories(self):
        """Populate category combo box with existing categories."""
        categories = self.library.get_categories()

        # Add default categories
        default_categories = ["custom", "web", "desktop", "data", "flow"]
        for cat in default_categories:
            if cat not in categories:
                self.category_combo.addItem(cat)

        # Add existing categories
        for cat in categories:
            if cat not in default_categories:
                self.category_combo.addItem(cat)

    def _populate_from_snippet(self):
        """Populate form fields from the snippet definition."""
        # Metadata
        self.name_edit.setText(self.snippet.name)
        self.description_edit.setPlainText(self.snippet.description)
        self.category_combo.setCurrentText(self.snippet.category)
        self.author_edit.setText(self.snippet.author or "")

        # Version
        self.version_label.setText(
            f"{self.snippet.version} (will become {self._get_next_version()} if saved)"
        )

        # Tags
        if self.snippet.tags:
            self.tags_edit.setText(", ".join(self.snippet.tags))

        # Variable scope
        self.inherit_scope_check.setChecked(
            self.snippet.variable_scope.inherit_parent_scope
        )
        self.export_vars_check.setChecked(
            self.snippet.variable_scope.export_local_vars
        )

        # Structure info
        structure_text = (
            f"<b>Nodes:</b> {len(self.snippet.nodes)}<br>"
            f"<b>Connections:</b> {len(self.snippet.connections)}<br>"
            f"<b>Entry Points:</b> {len(self.snippet.entry_node_ids)}<br>"
            f"<b>Exit Points:</b> {len(self.snippet.exit_node_ids)}"
        )
        self.structure_label.setText(structure_text)

        # Parameters
        self.params_list.clear()
        for param in self.snippet.parameters:
            required = " (required)" if param.required else ""
            self.params_list.addItem(
                f"{param.snippet_param_name}{required}: {param.description or 'No description'}"
            )

        if not self.snippet.parameters:
            self.params_list.addItem("No parameters defined")

    def _get_next_version(self) -> str:
        """
        Get the next version number (patch increment).

        Returns:
            Next version string
        """
        try:
            parts = self.snippet.version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0

            # Increment patch
            patch += 1

            return f"{major}.{minor}.{patch}"

        except (ValueError, IndexError):
            return "1.0.1"

    def _save_changes(self):
        """Save changes to the snippet."""
        # Validate inputs
        new_name = self.name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a name for the snippet."
            )
            self.name_edit.setFocus()
            return

        # Check if anything changed
        has_changes = (
            new_name != self.snippet.name
            or self.description_edit.toPlainText().strip() != self.snippet.description
            or self.category_combo.currentText().strip() != self.snippet.category
            or self.author_edit.text().strip() != (self.snippet.author or "")
            or self._parse_tags() != self.snippet.tags
            or self.inherit_scope_check.isChecked() != self.snippet.variable_scope.inherit_parent_scope
            or self.export_vars_check.isChecked() != self.snippet.variable_scope.export_local_vars
        )

        if not has_changes:
            QMessageBox.information(
                self,
                "No Changes",
                "No changes were made to the snippet."
            )
            return

        # Update snippet
        self.snippet.name = new_name
        self.snippet.description = self.description_edit.toPlainText().strip()
        self.snippet.category = self.category_combo.currentText().strip() or "custom"
        self.snippet.author = self.author_edit.text().strip()
        self.snippet.tags = self._parse_tags()

        # Update variable scope
        self.snippet.variable_scope.inherit_parent_scope = self.inherit_scope_check.isChecked()
        self.snippet.variable_scope.export_local_vars = self.export_vars_check.isChecked()

        # Version will be auto-bumped by library.save_snippet() if there are changes

        try:
            # Save to library
            file_path = self.library.save_snippet(self.snippet)

            logger.info(f"Snippet '{self.snippet.name}' updated and saved")

            # Show success message
            QMessageBox.information(
                self,
                "Snippet Updated",
                f"Snippet '{self.snippet.name}' has been updated successfully!\n\n"
                f"New version: {self.snippet.version}\n"
                f"Saved to: {file_path.name}"
            )

            # Close dialog
            self.accept()

        except Exception as e:
            logger.exception(f"Failed to save snippet: {e}")
            QMessageBox.critical(
                self,
                "Save Failed",
                f"An error occurred while saving the snippet:\n\n{str(e)}"
            )

    def _parse_tags(self) -> list[str]:
        """
        Parse tags from the tags edit field.

        Returns:
            List of tag strings
        """
        tags_text = self.tags_edit.text().strip()
        if not tags_text:
            return []

        # Split by comma and clean up
        tags = [tag.strip() for tag in tags_text.split(",")]
        tags = [tag for tag in tags if tag]  # Remove empty strings

        return tags
