"""
Visual Tree Panel for UI Explorer.

Hierarchical tree view displaying DOM/UI element structure with:
- Lazy loading of children on expand
- Search/filter functionality
- Element type icons
- Mode switching (browser/desktop)
"""

from collections.abc import Callable
from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.element_model import (
    ElementSource,
    UIExplorerElement,
)
from casare_rpa.presentation.canvas.theme_system import THEME

# Icon mapping for element types
BROWSER_ELEMENT_ICONS: dict[str, str] = {
    # Structural
    "html": "📄",
    "head": "🗂️",
    "body": "📋",
    "div": "📦",
    "span": "📝",
    "section": "📑",
    "article": "📰",
    "header": "🔝",
    "footer": "🔚",
    "nav": "🧭",
    "aside": "📎",
    "main": "🏠",
    # Interactive
    "button": "🔘",
    "a": "🔗",
    "input": "✏️",
    "textarea": "📝",
    "select": "▼",
    "option": "•",
    "form": "📋",
    "label": "🏷️",
    # Media
    "img": "🖼️",
    "video": "🎬",
    "audio": "🔊",
    "canvas": "🎨",
    "svg": "🔷",
    "iframe": "🖼️",
    # Table
    "table": "⊞",
    "tr": "▭",
    "td": "▫",
    "th": "▪",
    "thead": "⬆️",
    "tbody": "📋",
    # List
    "ul": "📃",
    "ol": "📃",
    "li": "•",
    # Text
    "p": "¶",
    "h1": "H1",
    "h2": "H2",
    "h3": "H3",
    "h4": "H4",
    "h5": "H5",
    "h6": "H6",
    "strong": "B",
    "em": "I",
    "code": "</>",
    "pre": "📜",
}

DESKTOP_ELEMENT_ICONS: dict[str, str] = {
    "Button": "🔘",
    "Edit": "✏️",
    "Text": "📝",
    "Window": "🪟",
    "Pane": "📋",
    "Group": "📦",
    "List": "📃",
    "ListItem": "•",
    "TreeView": "🌲",
    "TreeItem": "🔹",
    "MenuBar": "☰",
    "Menu": "☰",
    "MenuItem": "▸",
    "CheckBox": "☑️",
    "RadioButton": "⚪",
    "ComboBox": "▼",
    "TabControl": "📑",
    "TabItem": "📄",
    "ToolBar": "🔧",
    "StatusBar": "ℹ️",
    "Slider": "━●━",
    "ProgressBar": "▓▒░",
    "Spinner": "↻",
    "Image": "🖼️",
    "Separator": "│",
    "ScrollBar": "⇅",
    "Table": "⊞",
    "DataGrid": "⊞",
    "DataItem": "▫",
    "Header": "▭",
    "HeaderItem": "▭",
    "Calendar": "📅",
    "Document": "📄",
    "SplitButton": "⏷",
    "Hyperlink": "🔗",
    "Thumb": "◯",
    "TitleBar": "▬",
    "Custom": "◆",
}


class VisualTreeItem(QTreeWidgetItem):
    """
    Custom tree item holding UIExplorerElement reference.

    Supports lazy loading of children when expanded.
    """

    def __init__(
        self,
        element: UIExplorerElement,
        parent: QTreeWidgetItem | None = None,
        load_children_callback: Callable[[UIExplorerElement], list[UIExplorerElement]]
        | None = None,
    ) -> None:
        """
        Initialize tree item.

        Args:
            element: UIExplorerElement data
            parent: Parent tree item (None for root)
            load_children_callback: Callback to load children on expand
        """
        self.element = element
        self._load_children_callback = load_children_callback
        self._children_loaded = element.children_loaded

        # Build display text
        display_text = self._build_display_text()

        # Initialize with parent
        if parent:
            super().__init__(parent, [display_text])
        else:
            super().__init__([display_text])

        # Apply styling
        self._apply_element_styling()

        # Add dummy child if element might have children
        if element.has_children_hint() and not self._children_loaded:
            dummy = QTreeWidgetItem(self, ["Loading..."])
            dummy.setDisabled(True)
            dummy.setForeground(0, QBrush(QColor(THEME.text_disabled)))

    def _build_display_text(self) -> str:
        """Build display text with icon."""
        element = self.element

        # Get icon
        if element.source == ElementSource.BROWSER:
            icon = BROWSER_ELEMENT_ICONS.get(element.tag_or_control.lower(), "▪")
        else:
            control = element.tag_or_control
            if control.endswith("Control"):
                control = control[:-7]
            icon = DESKTOP_ELEMENT_ICONS.get(control, "▪")

        # Build text
        return f"{icon} {element.display_name}"

    def _apply_element_styling(self) -> None:
        """Apply styling based on element attributes."""
        element = self.element

        # Check for disabled/hidden elements
        is_enabled = element.get_attribute("IsEnabled", "True") != "False"
        is_offscreen = element.get_attribute("IsOffscreen", "False") == "True"

        if not is_enabled:
            self.setForeground(0, QBrush(QColor(THEME.text_disabled)))
            font = self.font(0)
            font.setItalic(True)
            self.setFont(0, font)
        elif is_offscreen:
            self.setForeground(0, QBrush(QColor(THEME.text_muted)))

        # Highlight elements with id or data-testid
        if element.element_id or element.get_attribute("data-testid"):
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)

    def load_children(self) -> None:
        """Lazy load children when item is expanded."""
        if self._children_loaded:
            return

        # Remove dummy child
        self.takeChildren()

        try:
            # Get children via callback or from element
            if self._load_children_callback:
                children = self._load_children_callback(self.element)
            elif self.element.children:
                children = self.element.children
            else:
                children = []

            # Add child items
            for child_element in children[:100]:  # Limit to 100 children
                VisualTreeItem(
                    child_element, parent=self, load_children_callback=self._load_children_callback
                )

            self._children_loaded = True
            self.element.children_loaded = True

            logger.debug(f"Loaded {len(children)} children for {self.element.short_name}")

        except Exception as e:
            logger.error(f"Failed to load children: {e}")
            error_item = QTreeWidgetItem(self, ["<error loading children>"])
            error_item.setDisabled(True)
            error_item.setForeground(0, QBrush(QColor(THEME.status_error)))


class VisualTreePanel(QFrame):
    """
    Visual Tree Panel showing DOM/UI element hierarchy.

    Features:
    - QTreeWidget with lazy loading
    - Search/filter input
    - Icons for element types
    - Selection signals

    Signals:
        element_selected: Emitted when user clicks an element (dict: element data)
        element_double_clicked: Emitted on double-click for quick select
    """

    element_selected = Signal(dict)
    element_double_clicked = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the visual tree panel."""
        super().__init__(parent)

        self._mode: str = "browser"
        self._root_element: UIExplorerElement | None = None
        self._load_children_callback: Callable | None = None
        self._all_items: list[VisualTreeItem] = []

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with title
        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 4)

        title_label = QLabel("VISUAL TREE")
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

        # Mode indicator
        self._mode_label = QLabel("Browser")
        self._mode_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.accent_primary};
                font-size: 10px;
                padding: 2px 6px;
                background: {THEME.bg_darkest};
                border-radius: 3px;
            }}
        """)
        header.addWidget(self._mode_label)

        layout.addLayout(header)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 0, 8, 4)
        search_layout.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter elements...")
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.setClearButtonEnabled(True)
        search_layout.addWidget(self._search_input)

        # Refresh button
        self._refresh_btn = QPushButton("↻")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.setToolTip("Refresh tree (F5)")
        self._refresh_btn.clicked.connect(self._on_refresh)
        search_layout.addWidget(self._refresh_btn)

        layout.addLayout(search_layout)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAlternatingRowColors(False)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.setExpandsOnDoubleClick(False)  # We handle double-click separately
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._tree)

        # Element count label
        self._count_label = QLabel("0 elements")
        self._count_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.text_disabled};
                font-size: 10px;
                padding: 4px 8px;
            }}
        """)
        layout.addWidget(self._count_label)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            VisualTreePanel {{
                background: {THEME.bg_darkest};
                border: 1px solid {THEME.border};
                border-radius: 4px;
            }}
        """)

        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 8px;
                color: {THEME.text_primary};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {THEME.accent_primary};
            }}
            QLineEdit::placeholder {{
                color: {THEME.text_disabled};
            }}
        """)

        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_medium};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                color: {THEME.text_primary};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {THEME.border};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_dark};
            }}
        """)

        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {THEME.bg_darkest};
                border: none;
                color: {THEME.text_primary};
                font-size: 12px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 4px;
                border-radius: 2px;
            }}
            QTreeWidget::item:hover {{
                background: {THEME.bg_hover};
            }}
            QTreeWidget::item:selected {{
                background: {THEME.accent_primary};
                color: white;
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QScrollBar:vertical {{
                background: {THEME.bg_darkest};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME.border};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME.bg_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {THEME.bg_darkest};
                height: 10px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {THEME.border};
                border-radius: 5px;
                min-width: 30px;
            }}
        """)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_mode(self, mode: str) -> None:
        """
        Set the explorer mode.

        Args:
            mode: "browser" or "desktop"
        """
        self._mode = mode
        self._mode_label.setText(mode.capitalize())

        # Update mode label styling
        if mode == "browser":
            self._mode_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME.accent_primary};
                    font-size: 10px;
                    padding: 2px 6px;
                    background: {THEME.bg_darkest};
                    border-radius: 3px;
                }}
            """)
        else:
            self._mode_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME.status_warning};
                    font-size: 10px;
                    padding: 2px 6px;
                    background: {THEME.error_subtle};
                    border-radius: 3px;
                }}
            """)

        logger.debug(f"VisualTreePanel mode set to: {mode}")

    def load_tree(self, root_element: dict[str, Any]) -> None:
        """
        Populate tree from element data dictionary.

        Args:
            root_element: Root element data dict with:
                - source: "browser" or "desktop"
                - tag_or_control: Element type
                - element_id: Unique ID
                - name: Display name
                - attributes: Dict of attributes
                - children: List of child elements
        """
        self.clear()

        try:
            # Convert dict to UIExplorerElement
            if self._mode == "browser":
                element = UIExplorerElement.from_browser_data(root_element)
            else:
                element = UIExplorerElement.from_desktop_data(root_element)

            self._root_element = element

            # Recursively load children from dict
            if "children" in root_element:
                self._load_children_from_dict(element, root_element["children"])

            # Create root item
            root_item = VisualTreeItem(element, load_children_callback=self._load_children_callback)
            self._tree.addTopLevelItem(root_item)
            self._all_items.append(root_item)

            # Expand root
            root_item.setExpanded(True)
            if not element.children_loaded:
                root_item.load_children()

            # Update count
            self._update_count()

            logger.info(f"Visual tree loaded with root: {element.short_name}")

        except Exception as e:
            logger.error(f"Failed to load visual tree: {e}")
            error_item = QTreeWidgetItem(["<error loading tree>"])
            error_item.setForeground(0, QBrush(QColor(THEME.status_error)))
            self._tree.addTopLevelItem(error_item)

    def load_tree_from_element(self, element: UIExplorerElement) -> None:
        """
        Populate tree from UIExplorerElement.

        Args:
            element: Root UIExplorerElement
        """
        self.clear()

        try:
            self._root_element = element

            # Create root item
            root_item = VisualTreeItem(element, load_children_callback=self._load_children_callback)
            self._tree.addTopLevelItem(root_item)
            self._all_items.append(root_item)

            # Expand root
            root_item.setExpanded(True)
            if not element.children_loaded:
                root_item.load_children()

            # Update count
            self._update_count()

            logger.info(f"Visual tree loaded with root: {element.short_name}")

        except Exception as e:
            logger.error(f"Failed to load visual tree: {e}")

    def set_load_children_callback(
        self, callback: Callable[[UIExplorerElement], list[UIExplorerElement]]
    ) -> None:
        """
        Set callback for lazy loading children.

        Args:
            callback: Function that takes UIExplorerElement and returns list of children
        """
        self._load_children_callback = callback

    def select_element(self, element_id: str) -> bool:
        """
        Programmatically select element by ID.

        Args:
            element_id: Element ID to select

        Returns:
            True if element was found and selected
        """
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if isinstance(item, VisualTreeItem):
                if item.element.element_id == element_id:
                    self._tree.setCurrentItem(item)
                    self._tree.scrollToItem(item)
                    return True
            iterator += 1
        return False

    def clear(self) -> None:
        """Clear the tree."""
        self._tree.clear()
        self._root_element = None
        self._all_items.clear()
        self._count_label.setText("0 elements")

    def filter_tree(self, query: str) -> None:
        """
        Filter visible tree items by query.

        Args:
            query: Search query string
        """
        self._on_search_changed(query)

    def get_selected_element(self) -> UIExplorerElement | None:
        """Get currently selected element."""
        items = self._tree.selectedItems()
        if items and isinstance(items[0], VisualTreeItem):
            return items[0].element
        return None

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _load_children_from_dict(
        self, parent: UIExplorerElement, children_data: list[dict[str, Any]]
    ) -> None:
        """Recursively load children from dict data."""
        for child_data in children_data:
            if self._mode == "browser":
                child = UIExplorerElement.from_browser_data(child_data, parent)
            else:
                child = UIExplorerElement.from_desktop_data(child_data, parent)

            parent.children.append(child)

            # Recursively load grandchildren
            if "children" in child_data:
                self._load_children_from_dict(child, child_data["children"])

        parent.children_loaded = True

    def _update_count(self) -> None:
        """Update element count label."""
        count = self._count_all_items()
        self._count_label.setText(f"{count} element{'s' if count != 1 else ''}")

    def _count_all_items(self) -> int:
        """Count all items in tree."""
        count = 0
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if isinstance(item, VisualTreeItem):
                count += 1
            iterator += 1
        return count

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle item expansion - trigger lazy loading."""
        if isinstance(item, VisualTreeItem):
            item.load_children()

    def _on_selection_changed(self) -> None:
        """Handle tree selection change."""
        items = self._tree.selectedItems()
        if items and isinstance(items[0], VisualTreeItem):
            element = items[0].element
            logger.debug(f"Element selected: {element.short_name}")
            self.element_selected.emit(element.to_dict())

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on item."""
        if isinstance(item, VisualTreeItem):
            element = item.element
            logger.debug(f"Element double-clicked: {element.short_name}")
            self.element_double_clicked.emit(element.to_dict())

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        query = text.lower().strip()

        if not query:
            self._show_all_items()
            return

        self._filter_items(query)

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        if self._root_element:
            # Reset children loaded flag
            self._reset_children_loaded(self._root_element)
            self.load_tree_from_element(self._root_element)

    def _reset_children_loaded(self, element: UIExplorerElement) -> None:
        """Recursively reset children_loaded flag."""
        element.children_loaded = False
        element.children.clear()

    def _show_all_items(self) -> None:
        """Show all tree items."""
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            item.setHidden(False)
            iterator += 1

    def _filter_items(self, query: str) -> None:
        """Filter tree items by search query."""
        # First pass: mark items that match
        matching_items = set()
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if isinstance(item, VisualTreeItem):
                item_text = item.text(0).lower()
                element = item.element

                # Check text, id, and attributes
                matches = (
                    query in item_text
                    or query in element.element_id.lower()
                    or query in element.name.lower()
                    or any(query in v.lower() for v in element.attributes.values())
                )

                if matches:
                    matching_items.add(id(item))
                    # Also mark all ancestors as matching
                    parent = item.parent()
                    while parent:
                        matching_items.add(id(parent))
                        parent = parent.parent()

            iterator += 1

        # Second pass: show/hide based on matches
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            item.setHidden(id(item) not in matching_items)
            iterator += 1
