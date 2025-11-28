"""
Template Browser Dialog

Provides a dialog for browsing and selecting workflow templates.
Users can filter by category, search, and preview template descriptions.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QSplitter,
    QWidget,
    QGroupBox,
)
from PySide6.QtGui import QFont

from casare_rpa.utils.workflow.template_loader import TemplateInfo, get_template_loader
from loguru import logger


class TemplateBrowserDialog(QDialog):
    """
    Dialog for browsing and selecting workflow templates.

    Signals:
        template_selected: Emitted when a template is selected (TemplateInfo)
    """

    template_selected = Signal(object)  # TemplateInfo

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the template browser dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Browse Workflow Templates")
        self.resize(800, 600)

        # Get template loader
        self._loader = get_template_loader()
        self._selected_template: Optional[TemplateInfo] = None

        # Create UI
        self._create_ui()

        # Load templates
        self._load_templates()

    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Select a Workflow Template")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Filter controls
        filter_layout = QHBoxLayout()

        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "")
        self.category_combo.currentIndexChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.category_combo)

        # Search box
        filter_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search templates...")
        self.search_box.textChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.search_box, 1)

        layout.addLayout(filter_layout)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Template list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("Templates:")
        list_layout.addWidget(list_label)

        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self._on_template_selected)
        self.template_list.itemDoubleClicked.connect(self._on_template_double_clicked)
        list_layout.addWidget(self.template_list)

        splitter.addWidget(list_widget)

        # Template details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("Details:")
        details_layout.addWidget(details_label)

        # Details group box
        details_group = QGroupBox()
        details_group_layout = QVBoxLayout(details_group)

        # Template name
        self.name_label = QLabel("<b>Name:</b> (Select a template)")
        self.name_label.setWordWrap(True)
        details_group_layout.addWidget(self.name_label)

        # Category
        self.category_label = QLabel("<b>Category:</b> -")
        details_group_layout.addWidget(self.category_label)

        # Tags
        self.tags_label = QLabel("<b>Tags:</b> -")
        self.tags_label.setWordWrap(True)
        details_group_layout.addWidget(self.tags_label)

        # Description
        desc_label = QLabel("<b>Description:</b>")
        details_group_layout.addWidget(desc_label)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(150)
        self.description_text.setText("Select a template to see its description.")
        details_group_layout.addWidget(self.description_text)

        # File path
        self.path_label = QLabel("<b>File:</b> -")
        self.path_label.setWordWrap(True)
        details_group_layout.addWidget(self.path_label)

        details_group_layout.addStretch()

        details_layout.addWidget(details_group)

        splitter.addWidget(details_widget)

        # Set splitter sizes (40% list, 60% details)
        splitter.setSizes([320, 480])

        layout.addWidget(splitter, 1)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.use_button = QPushButton("Use Template")
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self._on_use_template)
        button_layout.addWidget(self.use_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _load_templates(self):
        """Load templates from the loader."""
        try:
            # Discover templates
            templates_by_category = self._loader.discover_templates()

            # Populate category combo
            for category in sorted(self._loader.get_categories()):
                # Format category name nicely
                category_display = category.replace("_", " ").title()
                self.category_combo.addItem(category_display, category)

            # Populate template list
            self._update_template_list()

            logger.info(f"Loaded {len(self._loader.get_all_templates())} templates")

        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self.description_text.setText(f"Error loading templates: {e}")

    def _update_template_list(self):
        """Update the template list based on current filters."""
        self.template_list.clear()

        # Get selected category
        category_data = self.category_combo.currentData()
        search_query = self.search_box.text().strip()

        # Get templates
        if search_query:
            # Search mode
            templates = self._loader.search_templates(search_query)
            if category_data:
                # Filter by category too
                templates = [t for t in templates if t.category == category_data]
        elif category_data:
            # Category filter
            templates = self._loader.get_templates_by_category(category_data)
        else:
            # All templates
            templates = self._loader.get_all_templates()

        # Sort templates by name
        templates.sort(key=lambda t: t.name)

        # Add to list
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

        # Update count
        count = self.template_list.count()
        self.template_list.setToolTip(f"{count} template(s)")

    def _filter_templates(self):
        """Filter templates based on category and search."""
        self._update_template_list()

    def _on_template_selected(self):
        """Handle template selection."""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            self.use_button.setEnabled(False)
            self._selected_template = None
            return

        # Get selected template
        item = selected_items[0]
        template: TemplateInfo = item.data(Qt.ItemDataRole.UserRole)
        self._selected_template = template

        # Update details
        self.name_label.setText(f"<b>Name:</b> {template.name}")
        self.category_label.setText(
            f"<b>Category:</b> {template.category.replace('_', ' ').title()}"
        )
        self.tags_label.setText(
            f"<b>Tags:</b> {', '.join(template.tags) if template.tags else 'None'}"
        )
        self.description_text.setText(template.description)
        self.path_label.setText(f"<b>File:</b> {template.file_path.name}")

        # Enable use button
        self.use_button.setEnabled(True)

    def _on_template_double_clicked(self, item: QListWidgetItem):
        """Handle template double-click (use template)."""
        self._on_use_template()

    def _on_use_template(self):
        """Handle use template button click."""
        if self._selected_template:
            self.template_selected.emit(self._selected_template)
            self.accept()

    def get_selected_template(self) -> Optional[TemplateInfo]:
        """
        Get the selected template.

        Returns:
            Selected TemplateInfo or None
        """
        return self._selected_template


def show_template_browser(parent: Optional[QWidget] = None) -> Optional[TemplateInfo]:
    """
    Show the template browser dialog and return the selected template.

    Args:
        parent: Parent widget

    Returns:
        Selected TemplateInfo or None if cancelled
    """
    dialog = TemplateBrowserDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_selected_template()
    return None
