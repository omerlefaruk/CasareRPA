"""
CasareRPA - Snippet Browser Dialog
UI for browsing, searching, and inserting snippets from the library.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QGroupBox,
    QTextBrowser,
    QCheckBox,
    QSplitter,
    QMessageBox,
)
from PySide6.QtGui import QFont
from loguru import logger

from ..core.snippet_library import get_snippet_library, SnippetInfo
from ..core.snippet_definition import SnippetDefinition


class SnippetBrowserDialog(QDialog):
    """
    Dialog for browsing and inserting snippets from the library.

    Features:
    - Search with fuzzy matching
    - Category filtering
    - Snippet preview with metadata
    - Insert modes (collapsed/expanded)
    - Delete and edit actions
    """

    # Signal emitted when snippet is selected for insertion
    snippet_insert_requested = Signal(SnippetDefinition, bool)  # (snippet, is_collapsed)

    def __init__(self, parent=None):
        """
        Initialize snippet browser dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.library = get_snippet_library()
        self.selected_snippet: Optional[SnippetInfo] = None

        self.setWindowTitle("Snippet Library")
        self.setModal(True)
        self.resize(900, 600)

        self._init_ui()
        self._load_snippets()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Search and filter section
        search_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search snippets by name, description, or tags...")
        self.search_edit.textChanged.connect(self._filter_snippets)
        search_layout.addWidget(self.search_edit, stretch=3)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        search_layout.addWidget(QLabel("Category:"))
        search_layout.addWidget(self.category_filter, stretch=1)
        self.category_filter.currentTextChanged.connect(self._filter_snippets)

        layout.addLayout(search_layout)

        # Main content: split between list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Snippet list
        list_container = QGroupBox("Available Snippets")
        list_layout = QVBoxLayout()

        self.snippet_list = QListWidget()
        self.snippet_list.setAlternatingRowColors(True)
        self.snippet_list.currentItemChanged.connect(self._on_snippet_selected)
        self.snippet_list.itemDoubleClicked.connect(self._on_insert_clicked)
        list_layout.addWidget(self.snippet_list)

        # Snippet count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #888; font-size: 9pt;")
        list_layout.addWidget(self.count_label)

        list_container.setLayout(list_layout)
        splitter.addWidget(list_container)

        # Right: Details panel
        details_container = QGroupBox("Snippet Details")
        details_layout = QVBoxLayout()

        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(False)
        details_layout.addWidget(self.details_browser)

        # Insert options
        options_layout = QHBoxLayout()

        self.collapsed_check = QCheckBox("Insert as collapsed node")
        self.collapsed_check.setChecked(True)
        self.collapsed_check.setToolTip(
            "If checked, snippet will be inserted as a single collapsed node.\n"
            "If unchecked, snippet nodes will be expanded inline."
        )
        options_layout.addWidget(self.collapsed_check)

        options_layout.addStretch()
        details_layout.addLayout(options_layout)

        details_container.setLayout(details_layout)
        splitter.addWidget(details_container)

        # Set splitter proportions
        splitter.setSizes([300, 600])

        layout.addWidget(splitter)

        # Dialog buttons
        button_layout = QHBoxLayout()

        # Left side buttons
        self.delete_btn = QPushButton("Delete Snippet")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        self.edit_btn = QPushButton("Edit Snippet...")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)

        button_layout.addStretch()

        # Right side buttons
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.insert_btn = QPushButton("Insert Snippet")
        self.insert_btn.setDefault(True)
        self.insert_btn.clicked.connect(self._on_insert_clicked)
        self.insert_btn.setEnabled(False)
        button_layout.addWidget(self.insert_btn)

        layout.addLayout(button_layout)

    def _load_snippets(self):
        """Load snippets from library and populate UI."""
        # Discover snippets
        self.library.discover_snippets()

        # Populate category filter
        categories = self.library.get_categories()
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for cat in categories:
            self.category_filter.addItem(cat)

        # Populate snippet list
        self._filter_snippets()

    def _filter_snippets(self):
        """Filter snippets based on search and category."""
        search_query = self.search_edit.text().strip()
        selected_category = self.category_filter.currentText()

        # Get category filter (None if "All Categories")
        category_filter = None if selected_category == "All Categories" else selected_category

        # Search snippets
        if search_query:
            snippets = self.library.search_snippets(
                query=search_query,
                category=category_filter,
                max_results=50
            )
        else:
            # No search query, list by category
            if category_filter:
                snippets = self.library.list_snippets_by_category(category_filter)
            else:
                snippets = self.library.list_all_snippets()

        # Clear and populate list
        self.snippet_list.clear()

        for snippet_info in snippets:
            item = QListWidgetItem(f"{snippet_info.name}")
            item.setData(Qt.ItemDataRole.UserRole, snippet_info)

            # Add category as subtitle
            font = QFont()
            font.setPointSize(9)
            item.setFont(font)

            # Tooltip with description
            if snippet_info.description:
                item.setToolTip(snippet_info.description)

            self.snippet_list.addItem(item)

        # Update count label
        self.count_label.setText(f"{len(snippets)} snippet(s) found")

    def _on_snippet_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Handle snippet selection in list."""
        if not current:
            self.selected_snippet = None
            self.details_browser.clear()
            self.insert_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            return

        # Get snippet info
        self.selected_snippet = current.data(Qt.ItemDataRole.UserRole)

        # Enable action buttons
        self.insert_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)

        # Display details
        self._display_snippet_details(self.selected_snippet)

    def _display_snippet_details(self, snippet_info: SnippetInfo):
        """Display snippet details in the details panel."""
        # Load full snippet definition
        snippet = self.library.load_snippet(snippet_info.snippet_id)

        if not snippet:
            self.details_browser.setHtml("<p>Error loading snippet details.</p>")
            return

        # Build HTML details
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 10pt; }}
                h2 {{ color: #5DADE2; margin-top: 0; }}
                h3 {{ color: #AAA; font-size: 9pt; margin-top: 12px; margin-bottom: 4px; }}
                .info {{ background: #2a2a2a; padding: 8px; border-radius: 4px; margin: 4px 0; }}
                .label {{ color: #888; font-weight: bold; }}
                .value {{ color: #DDD; }}
                ul {{ margin: 4px 0; padding-left: 20px; }}
                li {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
            <h2>{snippet.name}</h2>
            <div class="info">
                <span class="label">Category:</span> <span class="value">{snippet.category}</span><br>
                <span class="label">Version:</span> <span class="value">{snippet.version}</span><br>
                <span class="label">Author:</span> <span class="value">{snippet.author or 'Unknown'}</span>
            </div>
        """

        if snippet.description:
            html += f"<p>{snippet.description}</p>"

        # Structure info
        html += f"""
            <h3>Structure</h3>
            <div class="info">
                <span class="label">Nodes:</span> <span class="value">{len(snippet.nodes)}</span><br>
                <span class="label">Connections:</span> <span class="value">{len(snippet.connections)}</span><br>
                <span class="label">Entry Points:</span> <span class="value">{len(snippet.entry_node_ids)}</span><br>
                <span class="label">Exit Points:</span> <span class="value">{len(snippet.exit_node_ids)}</span>
            </div>
        """

        # Parameters
        if snippet.parameters:
            html += "<h3>Parameters</h3><ul>"
            for param in snippet.parameters:
                required = " (required)" if param.required else ""
                html += f"<li><b>{param.snippet_param_name}</b>{required}: {param.description}</li>"
            html += "</ul>"

        # Variable scope
        html += "<h3>Variable Scope</h3><ul>"
        html += f"<li>Inherits parent variables: {'Yes' if snippet.variable_scope.inherit_parent_scope else 'No'}</li>"
        html += f"<li>Exports local variables: {'Yes' if snippet.variable_scope.export_local_vars else 'No'}</li>"
        html += "</ul>"

        # Tags
        if snippet.tags:
            html += f"<h3>Tags</h3><p>{', '.join(snippet.tags)}</p>"

        # Timestamps
        html += f"""
            <div class="info" style="margin-top: 12px; font-size: 8pt;">
                <span class="label">Created:</span> <span class="value">{snippet.created_at or 'Unknown'}</span><br>
                <span class="label">Modified:</span> <span class="value">{snippet.modified_at or 'Unknown'}</span>
            </div>
        """

        html += "</body></html>"

        self.details_browser.setHtml(html)

    def _on_insert_clicked(self):
        """Handle insert snippet button click."""
        if not self.selected_snippet:
            return

        # Load full snippet definition
        snippet = self.library.load_snippet(self.selected_snippet.snippet_id)

        if not snippet:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to load snippet definition."
            )
            return

        # Get insert mode
        is_collapsed = self.collapsed_check.isChecked()

        # Emit signal with snippet and mode
        self.snippet_insert_requested.emit(snippet, is_collapsed)

        # Close dialog
        self.accept()

    def _on_delete_clicked(self):
        """Handle delete snippet button click."""
        if not self.selected_snippet:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the snippet '{self.selected_snippet.name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete from library
            success = self.library.delete_snippet(self.selected_snippet.snippet_id)

            if success:
                logger.info(f"Deleted snippet: {self.selected_snippet.name}")
                QMessageBox.information(
                    self,
                    "Snippet Deleted",
                    f"Snippet '{self.selected_snippet.name}' has been deleted."
                )

                # Reload snippets
                self._load_snippets()
            else:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Failed to delete snippet '{self.selected_snippet.name}'."
                )

    def _on_edit_clicked(self):
        """Handle edit snippet button click."""
        if not self.selected_snippet:
            return

        from .snippet_editor_dialog import SnippetEditorDialog

        # Load full snippet definition
        snippet = self.library.load_snippet(self.selected_snippet.snippet_id)

        if not snippet:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to load snippet definition for editing."
            )
            return

        # Open editor dialog
        editor_dialog = SnippetEditorDialog(snippet, parent=self)

        if editor_dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info(f"Snippet '{snippet.name}' updated successfully")

            # Reload snippets to reflect changes
            self._load_snippets()

            # Show success message in status
            QMessageBox.information(
                self,
                "Snippet Updated",
                f"Snippet '{snippet.name}' has been updated."
            )
        else:
            logger.info("Snippet editing cancelled")
