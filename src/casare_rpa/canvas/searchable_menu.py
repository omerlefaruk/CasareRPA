"""
Searchable context menu for node creation.

Provides a context menu with search functionality at the top.
"""

from typing import List, Tuple, Optional, Callable
from PySide6.QtWidgets import QMenu, QWidgetAction, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QAction

from ..utils.fuzzy_search import fuzzy_search, highlight_matches


class SearchableNodeMenu(QMenu):
    """
    Context menu with integrated search functionality.

    Features:
    - Search field at the top of the menu
    - Real-time filtering of menu items as you type
    - Fuzzy matching (e.g., "b l" matches "Browser Launch")
    - Keyboard navigation
    - Shift+Enter to create node and auto-connect to last node
    """

    # Signal emitted when a node should be created with auto-connect
    # Parameters: (category, name, auto_connect)
    node_creation_requested = Signal(str, str, bool)

    def __init__(self, title: str = "", parent=None):
        """Initialize the searchable menu."""
        super().__init__(title, parent)

        self._node_items: List[Tuple[str, str, str, Callable]] = []  # (category, name, description, callback)
        self._category_actions: dict = {}  # category -> list of QAction
        self._search_input: Optional[QLineEdit] = None
        self._all_actions: List[QAction] = []
        self._auto_connect_requested: bool = False  # Track if Shift+Enter was pressed
        
    def setup_search(self):
        """Setup the search input at the top of the menu."""
        # Create search input widget
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search nodes... (e.g., 'b l' for Browser Launch)")
        self._search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #FFA500;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #FFD700;
            }
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.installEventFilter(self)
        
        # Add search input as the first item in menu
        search_action = QWidgetAction(self)
        search_action.setDefaultWidget(self._search_input)
        self.addAction(search_action)
        self.addSeparator()
    
    def add_node_item(self, category: str, name: str, description: str, callback: Callable):
        """
        Add a node item to the menu.
        
        Args:
            category: Node category
            name: Node name
            description: Node description
            callback: Function to call when node is selected
        """
        self._node_items.append((category, name, description, callback))
    
    def build_menu(self):
        """Build the menu structure with all node items organized by category."""
        # Group by category
        categories = {}
        for category, name, description, callback in self._node_items:
            if category not in categories:
                categories[category] = []
            categories[category].append((name, description, callback))
        
        # Create submenus for each category
        for category in sorted(categories.keys()):
            category_menu = self.addMenu(category)
            self._category_actions[category] = []
            
            for name, description, callback in sorted(categories[category], key=lambda x: x[0]):
                action = category_menu.addAction(name)
                action.triggered.connect(callback)
                action.setData({'category': category, 'name': name, 'description': description})
                self._category_actions[category].append(action)
                self._all_actions.append(action)
    
    def _on_search_changed(self, text: str):
        """Handle search text changes and filter menu items."""
        if not text.strip():
            # Show all items when search is empty
            self._show_all_items()
            return
        
        # Perform fuzzy search
        search_items = [(cat, name, desc) for cat, name, desc, _ in self._node_items]
        results = fuzzy_search(text, search_items)
        
        # Hide all category menus first
        for action in self.actions():
            if action.menu():  # It's a submenu
                action.setVisible(False)
        
        # Show only matching items
        matched_categories = set()
        for category, name, description, score, positions in results:
            matched_categories.add(category)
            
            # Find the action for this node
            for action in self._all_actions:
                data = action.data()
                if data and data['name'] == name and data['category'] == category:
                    action.setVisible(True)
                    
                    # Update action text with highlighting
                    highlighted_name = highlight_matches(name, positions)
                    # Remove HTML tags for menu text (Qt doesn't support HTML in QAction text directly)
                    # Instead, we'll just show the name as-is
                    action.setText(name)
                    break
        
        # Show only categories that have matches
        for action in self.actions():
            if action.menu():
                menu = action.menu()
                # Check if any action in this submenu is visible
                has_visible = any(a.isVisible() for a in menu.actions())
                action.setVisible(has_visible)
    
    def _show_all_items(self):
        """Show all menu items and categories."""
        for action in self.actions():
            if action.menu():  # It's a submenu
                action.setVisible(True)
                # Show all actions in submenu
                for sub_action in action.menu().actions():
                    sub_action.setVisible(True)
    
    def eventFilter(self, obj, event):
        """Handle keyboard events in the search input."""
        if obj == self._search_input and event.type() == event.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Down:
                # Move focus to first visible menu item
                self._focus_first_visible_item()
                return True
            elif key == Qt.Key.Key_Escape:
                self.close()
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                # Check if Shift is held for auto-connect mode
                modifiers = event.modifiers()
                auto_connect = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
                self._auto_connect_requested = auto_connect
                # Execute first visible item
                self._execute_first_visible_item(auto_connect)
                return True

        return super().eventFilter(obj, event)
    
    def _focus_first_visible_item(self):
        """Set focus to the first visible menu item."""
        for action in self.actions():
            if action.menu() and action.isVisible():
                # Find first visible action in submenu
                for sub_action in action.menu().actions():
                    if sub_action.isVisible():
                        action.menu().setActiveAction(sub_action)
                        self.setActiveAction(action)
                        break
                break
    
    def _execute_first_visible_item(self, auto_connect: bool = False):
        """
        Execute the first visible menu item.

        Args:
            auto_connect: If True, emit signal to auto-connect to last node
        """
        for action in self.actions():
            if action.menu() and action.isVisible():
                # Find first visible action in submenu
                for sub_action in action.menu().actions():
                    if sub_action.isVisible():
                        # Get node data for signal
                        data = sub_action.data()
                        if data and auto_connect:
                            # Emit signal with auto-connect flag
                            self.node_creation_requested.emit(
                                data.get('category', ''),
                                data.get('name', ''),
                                True
                            )
                        # Always trigger the action (creates the node)
                        sub_action.trigger()
                        self.close()
                        return
                break
    
    def showEvent(self, event):
        """Focus search input when menu is shown."""
        super().showEvent(event)
        if self._search_input:
            self._search_input.setFocus()
            self._search_input.clear()
