"""
Selected Attributes Panel for UI Explorer.

UiPath-style split view showing:
- Selected Items: Attributes included in selector (checked)
- Unselected Items: Available but not included (unchecked)

Clicking checkbox moves items between sections.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import (
    SelectorAttribute,
    SelectorModel,
)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS


class SelectedAttributesPanel(QFrame):
    """
    Selected Attributes Panel with UiPath-style split view.

    Shows two collapsible sections:
    - Selected Items: Attributes included in selector (checked)
    - Unselected Items: Available but not included (unchecked)

    Each row shows: [checkbox] attribute_name    value

    Signals:
        attribute_toggled: Emitted when checkbox is toggled (name, is_checked)
    """

    attribute_toggled = Signal(str, bool)  # attribute_name, is_checked

    def __init__(
        self,
        model: SelectorModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the selected attributes panel.

        Args:
            model: SelectorModel to sync with (can be set later)
            parent: Parent widget
        """
        super().__init__(parent)

        self._model = model
        self._items: dict[str, QTreeWidgetItem] = {}
        self._updating = False  # Prevent signal loops

        self._setup_ui()
        self._apply_styles()

        # Connect to model if provided
        if model:
            self.set_model(model)

    def _setup_ui(self) -> None:
        """Build the panel UI with split view."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 4)
        header.setSpacing(8)

        # Title
        title_label = QLabel("ATTRIBUTES")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.text_muted};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: {THEME.border}; max-height: 1px;")
        layout.addWidget(separator)

        # Tree widget with two columns: Attribute, Value
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Attribute", "Value"])
        self._tree.setFrameShape(QFrame.Shape.NoFrame)
        self._tree.setRootIsDecorated(True)
        self._tree.setIndentation(16)
        self._tree.setAlternatingRowColors(False)
        self._tree.itemChanged.connect(self._on_item_changed)

        # Configure columns
        header_view = self._tree.header()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setMinimumSectionSize(80)

        layout.addWidget(self._tree, 1)

        # Create section headers (top-level items)
        self._selected_section = QTreeWidgetItem(self._tree)
        self._selected_section.setText(0, "Selected Items")
        self._selected_section.setExpanded(True)
        self._selected_section.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self._apply_section_style(self._selected_section, is_selected=True)

        self._unselected_section = QTreeWidgetItem(self._tree)
        self._unselected_section.setText(0, "Unselected Items")
        self._unselected_section.setExpanded(True)
        self._unselected_section.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self._apply_section_style(self._unselected_section, is_selected=False)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(8, 4, 8, 8)

        self._count_label = QLabel("0 selected")
        self._count_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.selector_text};
                font-size: 10px;
            }}
        """)
        footer.addWidget(self._count_label)
        footer.addStretch()

        layout.addLayout(footer)

    def _apply_section_style(self, item: QTreeWidgetItem, is_selected: bool) -> None:
        """Apply styling to section header."""
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        item.setFont(0, font)

        if is_selected:
            item.setForeground(0, QBrush(QColor(THEME.success)))  # Green
        else:
            item.setForeground(0, QBrush(QColor(THEME.text_muted)))  # Gray

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            SelectedAttributesPanel {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: 4px;
            }}
        """)

        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 4px;
                border-radius: 3px;
            }}
            QTreeWidget::item:hover {{
                background: {THEME.bg_hover};
            }}
            QTreeWidget::item:selected {{
                background: {THEME.bg_selected};
                color: white;
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url(none);
                border-image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url(none);
                border-image: none;
            }}
            QHeaderView::section {{
                background: {THEME.bg_surface};
                color: {THEME.text_muted};
                font-size: 10px;
                font-weight: bold;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {THEME.border};
            }}
            QScrollBar:vertical {{
                background: {THEME.bg_surface};
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME.border};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME.bg_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    def set_model(self, model: SelectorModel) -> None:
        """
        Set the selector model to sync with.

        Args:
            model: SelectorModel instance
        """
        # Disconnect from old model (suppress warnings with filterwarnings)
        if self._model:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self._model.changed.disconnect(self._on_model_changed)
                except (RuntimeError, TypeError):
                    pass
                try:
                    self._model.attribute_toggled.disconnect(self._on_model_attribute_toggled)
                except (RuntimeError, TypeError):
                    pass

        self._model = model

        # Connect to new model
        if model:
            model.changed.connect(self._on_model_changed)
            model.attribute_toggled.connect(self._on_model_attribute_toggled)

            # Initial load
            self._refresh_from_model()

    def get_model(self) -> SelectorModel | None:
        """Get the current model."""
        return self._model

    def clear(self) -> None:
        """Clear all items from both sections."""
        # Remove children from sections, not the sections themselves
        while self._selected_section.childCount() > 0:
            self._selected_section.removeChild(self._selected_section.child(0))

        while self._unselected_section.childCount() > 0:
            self._unselected_section.removeChild(self._unselected_section.child(0))

        self._items.clear()
        self._update_count()

    def get_checked_names(self) -> list[str]:
        """
        Get list of checked attribute names.

        Returns:
            List of checked attribute names
        """
        checked = []
        for name, item in self._items.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                checked.append(name)
        return checked

    def _refresh_from_model(self) -> None:
        """Refresh list from current model state."""
        self._updating = True
        self.clear()

        if not self._model:
            self._updating = False
            return

        # Add items for each attribute to the appropriate section
        for attr in self._model.attributes:
            self._add_item(attr)

        # Update section labels with counts
        self._update_section_labels()
        self._update_count()
        self._updating = False

    def _add_item(self, attribute: SelectorAttribute) -> None:
        """
        Add an item for an attribute to the appropriate section.

        Args:
            attribute: SelectorAttribute to add
        """
        # Determine which section
        if attribute.included:
            parent_section = self._selected_section
        else:
            parent_section = self._unselected_section

        # Create tree item
        item = QTreeWidgetItem(parent_section)
        item.setText(0, attribute.name)
        item.setText(1, attribute.display_value)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        # Set check state
        if attribute.included:
            item.setCheckState(0, Qt.CheckState.Checked)
        else:
            item.setCheckState(0, Qt.CheckState.Unchecked)

        # Style based on state
        self._apply_item_style(item, attribute)

        # Store reference
        self._items[attribute.name] = item

    def _apply_item_style(
        self,
        item: QTreeWidgetItem,
        attribute: SelectorAttribute,
    ) -> None:
        """Apply styling to an item based on attribute state."""
        # Name column styling
        if attribute.required:
            item.setForeground(0, QBrush(QColor(THEME.success)))  # Green for required
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
        elif attribute.included:
            item.setForeground(0, QBrush(QColor(THEME.selector_text)))  # Blue for included
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
        else:
            item.setForeground(0, QBrush(QColor(THEME.text_muted)))  # Gray for excluded
            font = QFont()
            font.setBold(False)
            item.setFont(0, font)

        # Value column styling
        if attribute.is_empty:
            item.setForeground(1, QBrush(QColor(THEME.text_disabled)))  # Dark gray for empty
            font = QFont()
            font.setItalic(True)
            item.setFont(1, font)
        elif attribute.computed:
            # TODO: Add THEME.computed or THEME.syntax_keyword for computed values
            # Using purple from VSCode syntax highlighting theme
            item.setForeground(1, QBrush(QColor("#a78bfa")))  # Purple for computed
        else:
            item.setForeground(1, QBrush(QColor(THEME.text_primary)))  # Light for normal

    def _update_section_labels(self) -> None:
        """Update section header labels with counts."""
        selected_count = self._selected_section.childCount()
        unselected_count = self._unselected_section.childCount()

        self._selected_section.setText(0, f"Selected Items ({selected_count})")
        self._unselected_section.setText(0, f"Unselected Items ({unselected_count})")

    def _update_count(self) -> None:
        """Update the count label."""
        count = len(self.get_checked_names())
        total = len(self._items)
        self._count_label.setText(f"{count} of {total} selected")

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item checkbox change."""
        if self._updating:
            return

        # Only handle checkbox column
        if column != 0:
            return

        # Skip section headers (use getattr to handle initialization race)
        selected = getattr(self, "_selected_section", None)
        unselected = getattr(self, "_unselected_section", None)
        if item in (selected, unselected):
            return

        name = item.text(0)
        is_checked = item.checkState(0) == Qt.CheckState.Checked

        # Find attribute and check if required
        if self._model:
            attr = self._model.get_attribute(name)
            if attr and attr.required and not is_checked:
                # Cannot uncheck required - revert
                self._updating = True
                item.setCheckState(0, Qt.CheckState.Checked)
                self._updating = False
                return

            # Update model
            self._model.set_attribute_included(name, is_checked)

        # Move item between sections
        self._move_item_to_section(item, name, is_checked)

        self._update_section_labels()
        self._update_count()

        # Emit signal
        self.attribute_toggled.emit(name, is_checked)

    def _move_item_to_section(self, item: QTreeWidgetItem, name: str, is_checked: bool) -> None:
        """
        Move an item between Selected and Unselected sections.

        Args:
            item: The tree item to move
            name: Attribute name
            is_checked: Whether it should be in Selected section
        """
        self._updating = True

        # Get parent and index
        current_parent = item.parent()
        if current_parent is None:
            self._updating = False
            return

        target_parent = self._selected_section if is_checked else self._unselected_section

        # Only move if parent is different
        if current_parent != target_parent:
            # Remove from current parent
            index = current_parent.indexOfChild(item)
            current_parent.takeChild(index)

            # Add to target parent
            target_parent.addChild(item)

            # Re-apply style (attribute state changed)
            if self._model:
                attr = self._model.get_attribute(name)
                if attr:
                    self._apply_item_style(item, attr)

        self._updating = False

    def _on_model_changed(self) -> None:
        """Handle model changed signal."""
        self._refresh_from_model()

    def _on_model_attribute_toggled(self, name: str, included: bool) -> None:
        """Handle model attribute toggled signal."""
        if self._updating:
            return

        self._updating = True

        if name in self._items:
            item = self._items[name]
            new_state = Qt.CheckState.Checked if included else Qt.CheckState.Unchecked
            if item.checkState(0) != new_state:
                item.setCheckState(0, new_state)

            # Move to appropriate section
            self._move_item_to_section(item, name, included)

            # Update style
            if self._model:
                attr = self._model.get_attribute(name)
                if attr:
                    self._apply_item_style(item, attr)

        self._update_section_labels()
        self._update_count()
        self._updating = False

    def set_attribute_checked(self, name: str, checked: bool) -> None:
        """
        Set a specific attribute's checked state.

        Args:
            name: Attribute name
            checked: Whether to check it
        """
        if name not in self._items:
            return

        item = self._items[name]

        # Check if required
        if self._model:
            attr = self._model.get_attribute(name)
            if attr and attr.required and not checked:
                return  # Cannot uncheck required

        self._updating = True
        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

        # Move to appropriate section
        self._move_item_to_section(item, name, checked)

        # Update style
        if self._model:
            attr = self._model.get_attribute(name)
            if attr:
                self._apply_item_style(item, attr)

        self._updating = False
        self._update_section_labels()
        self._update_count()
