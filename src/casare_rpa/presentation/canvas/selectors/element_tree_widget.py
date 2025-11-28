"""
Element Tree Widget

Hierarchical tree view for displaying desktop UI element structure
with lazy loading and custom styling.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QBrush
from loguru import logger

from casare_rpa.desktop.element import DesktopElement


class ElementTreeItem(QTreeWidgetItem):
    """Custom tree item that holds a DesktopElement reference"""

    def __init__(self, element: DesktopElement, parent=None):
        self.element = element
        self._children_loaded = False

        # Get element info
        control_type = element.get_property("ControlTypeName") or "Unknown"
        if control_type.endswith("Control"):
            control_type = control_type[:-7]  # Remove "Control" suffix

        name = element.get_property("Name") or element.get_text() or "<no name>"
        automation_id = element.get_property("AutomationId")

        # Build display text
        display_text = f"{control_type}: {name}"
        if automation_id:
            display_text += f" [#{automation_id}]"

        # Initialize tree item
        super().__init__(parent, [display_text])

        # Set icon based on control type
        self._set_control_type_icon(control_type)

        # Set styling
        self._apply_styling(element)

        # Add dummy child if element might have children
        if self._may_have_children(element):
            dummy = QTreeWidgetItem(self, ["Loading..."])
            dummy.setDisabled(True)

    def _set_control_type_icon(self, control_type: str):
        """Set icon based on control type"""
        # Icon mapping (using unicode symbols since we don't have actual icon files)
        icon_map = {
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
            "MenuItem": "▸",
            "CheckBox": "☑️",
            "RadioButton": "⚪",
            "ComboBox": "▼",
            "TabControl": "📑",
            "TabItem": "📄",
            "ToolBar": "🔧",
            "StatusBar": "ℹ️",
            "Slider": "━━●━━",
            "ProgressBar": "▓▓▒▒░░",
            "Spinner": "↻",
            "Image": "🖼️",
            "Separator": "│",
            "ScrollBar": "⇅",
            "Table": "⊞",
            "DataGrid": "⊞",
            "HeaderItem": "▭",
            "Calendar": "📅",
            "Document": "📄",
            "SplitButton": "⏷",
            "Hyperlink": "🔗",
        }

        icon_text = icon_map.get(control_type, "▪")

        # Set icon using text (PySide6 doesn't support emoji icons directly)
        # We'll just prepend it to the text
        current_text = self.text(0)
        if not current_text.startswith(icon_text):
            self.setText(0, f"{icon_text} {current_text}")

    def _apply_styling(self, element: DesktopElement):
        """Apply styling based on element properties"""
        # Check if element is enabled/visible
        is_enabled = element.is_enabled()
        is_visible = element.is_visible()

        if not is_enabled:
            # Grayed out for disabled elements
            self.setForeground(0, QBrush(QColor("#888888")))
            font = self.font(0)
            font.setItalic(True)
            self.setFont(0, font)
        elif not is_visible:
            # Lighter color for invisible elements
            self.setForeground(0, QBrush(QColor("#aaaaaa")))

    def _may_have_children(self, element: DesktopElement) -> bool:
        """Check if element might have children"""
        control_type = element.get_property("ControlTypeName") or ""

        # These types typically don't have children
        leaf_types = [
            "ButtonControl",
            "EditControl",
            "TextControl",
            "ImageControl",
            "CheckBoxControl",
            "RadioButtonControl",
            "HyperlinkControl",
            "ProgressBarControl",
            "SliderControl",
            "SeparatorControl",
        ]

        return control_type not in leaf_types

    def load_children(self):
        """Lazy load children elements"""
        if self._children_loaded:
            return

        # Remove dummy child
        self.takeChildren()

        try:
            # Get children from control
            control = self.element._control
            children = control.GetChildren()

            # Add child items
            for child in children[:50]:  # Limit to first 50 children
                try:
                    child_element = DesktopElement(child)
                    child_item = ElementTreeItem(child_element, self)
                except Exception as e:
                    logger.warning(f"Failed to create tree item for child: {e}")

            self._children_loaded = True
            logger.debug(f"Loaded {len(children)} children for {self.text(0)}")

        except Exception as e:
            logger.error(f"Failed to load children: {e}")
            # Add error indicator
            error_item = QTreeWidgetItem(self, ["<error loading children>"])
            error_item.setDisabled(True)
            error_item.setForeground(0, QBrush(QColor("#ff6666")))


class ElementTreeWidget(QWidget):
    """
    Widget containing element tree view with search functionality
    """

    element_selected = Signal(object)  # Emits DesktopElement when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_element: Optional[DesktopElement] = None
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search elements...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.setToolTip("Refresh tree")
        refresh_btn.clicked.connect(self.refresh)
        search_layout.addWidget(refresh_btn)

        layout.addLayout(search_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.tree)

    def _apply_styles(self):
        """Apply dark theme styling"""
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            QTreeWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #0d7ebd;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #2a2a2a;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: none;
                border: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: none;
                border: none;
            }
        """)

        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border-color: #0d7ebd;
            }
        """)

    def load_tree(self, root_element: DesktopElement):
        """
        Load element tree starting from root element

        Args:
            root_element: Root DesktopElement to display
        """
        logger.info("Loading element tree")
        self.root_element = root_element

        # Clear existing tree
        self.tree.clear()

        try:
            # Create root item
            root_item = ElementTreeItem(root_element)
            self.tree.addTopLevelItem(root_item)

            # Expand root by default
            root_item.setExpanded(True)
            root_item.load_children()

            logger.info("Element tree loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load element tree: {e}")
            error_item = QTreeWidgetItem(["<error loading tree>"])
            error_item.setForeground(0, QBrush(QColor("#ff6666")))
            self.tree.addTopLevelItem(error_item)

    def refresh(self):
        """Refresh the tree from current root element"""
        if self.root_element:
            self.load_tree(self.root_element)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - lazy load children"""
        if isinstance(item, ElementTreeItem):
            item.load_children()

    def _on_selection_changed(self):
        """Handle tree item selection"""
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, ElementTreeItem):
                logger.debug(f"Element selected: {item.text(0)}")
                self.element_selected.emit(item.element)

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        text = text.lower().strip()

        if not text:
            # Show all items
            self._show_all_items()
            return

        # Hide items that don't match
        self._filter_items(text)

    def _show_all_items(self):
        """Show all tree items"""
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setHidden(False)
            iterator += 1

    def _filter_items(self, search_text: str):
        """Filter tree items by search text"""
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item_text = item.text(0).lower()

            # Check if item matches search
            matches = search_text in item_text

            # Also check if any child matches (don't hide parents of matches)
            if not matches:
                matches = self._has_matching_child(item, search_text)

            item.setHidden(not matches)
            iterator += 1

    def _has_matching_child(self, item: QTreeWidgetItem, search_text: str) -> bool:
        """Check if any child item matches search text"""
        for i in range(item.childCount()):
            child = item.child(i)
            if search_text in child.text(0).lower():
                return True
            if self._has_matching_child(child, search_text):
                return True
        return False

    def get_selected_element(self) -> Optional[DesktopElement]:
        """Get the currently selected element"""
        selected_items = self.tree.selectedItems()
        if selected_items and isinstance(selected_items[0], ElementTreeItem):
            return selected_items[0].element
        return None

    def expand_to_element(self, target_element: DesktopElement) -> None:
        """
        Expand tree to show and select a specific element.

        Requires walking up the tree to find the path from root to target.
        Currently not implemented - would need parent tracking in DesktopElement.

        Args:
            target_element: Element to expand to
        """
        # Path-based expansion requires parent tracking in DesktopElement
        logger.debug(f"expand_to_element called for {target_element}, not implemented")
