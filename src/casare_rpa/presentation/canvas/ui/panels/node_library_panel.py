"""
Node Library Panel - Activity/Node Browser.

Provides a dockable panel with a categorized tree view of all available
nodes that can be dragged onto the canvas or double-clicked to create.

Features:
- Tree view organized by category (browser, desktop, data, etc.)
- Search/filter bar with fuzzy matching
- Drag-and-drop to canvas
- Double-click to create at center
- Category colors matching node colors
- Expandable/collapsible categories
"""

from typing import Optional, Dict, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QColor, QBrush, QFont

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_registry import NodeRegistry


# Category display names (more user-friendly)
CATEGORY_DISPLAY_NAMES = {
    "basic": "Basic",
    "browser": "Browser Automation",
    "control_flow": "Control Flow",
    "data_operations": "Data Operations",
    "database": "Database",
    "desktop_automation": "Desktop Automation",
    "email": "Email",
    "error_handling": "Error Handling",
    "file_operations": "File Operations",
    "office_automation": "Office Automation",
    "rest_api": "REST API / HTTP",
    "scripts": "Scripts",
    "system": "System",
    "utility": "Utility",
    "variable": "Variables",
}

# Category sort order (most common first)
CATEGORY_ORDER = [
    "basic",
    "browser",
    "desktop_automation",
    "control_flow",
    "data_operations",
    "variable",
    "file_operations",
    "rest_api",
    "database",
    "error_handling",
    "email",
    "office_automation",
    "scripts",
    "system",
    "utility",
]


class NodeLibraryPanel(QDockWidget):
    """
    Dockable panel showing all available nodes organized by category.

    Users can:
    - Browse nodes by category in tree view
    - Search/filter nodes by name
    - Drag nodes to canvas to create them
    - Double-click to create at canvas center

    Signals:
        node_requested: Emitted when user wants to create a node
            Args: (node_type: str, node_identifier: str)
        node_drag_started: Emitted when user starts dragging a node
            Args: (node_type: str, node_identifier: str)
    """

    node_requested = Signal(str, str)  # node_type, identifier
    node_drag_started = Signal(str, str)  # node_type, identifier

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the node library panel."""
        super().__init__("Node Library", parent)
        self.setObjectName("NodeLibraryDock")

        self._node_registry: Optional["NodeRegistry"] = None
        self._category_items: Dict[str, QTreeWidgetItem] = {}
        self._node_items: Dict[str, QTreeWidgetItem] = {}
        self._drag_start_pos = None

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        # Defer population until shown
        self._populated = False

        logger.debug("NodeLibraryPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(220)
        self.setMinimumHeight(300)

    def _setup_ui(self) -> None:
        """Create the panel UI."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search bar
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search nodes...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)

        # Tree view
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setExpandsOnDoubleClick(False)  # We handle double-click
        self._tree.setDragEnabled(True)
        self._tree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Connect signals
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemCollapsed.connect(self._on_item_collapsed)

        # Enable custom drag handling
        self._tree.startDrag = self._start_drag

        layout.addWidget(self._tree)

        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #1e1e1e;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
                font-weight: bold;
            }
            QLineEdit {
                background: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #569cd6;
            }
            QTreeWidget {
                background: #252526;
                color: #e0e0e0;
                border: none;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                border-radius: 2px;
            }
            QTreeWidget::item:hover {
                background: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background: #094771;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
        """)

    def showEvent(self, event) -> None:
        """Populate tree when first shown."""
        super().showEvent(event)
        if not self._populated:
            self._populate_tree()
            self._populated = True

    def _get_registry(self) -> "NodeRegistry":
        """Get or create node registry."""
        if self._node_registry is None:
            from casare_rpa.presentation.canvas.graph.node_registry import (
                get_node_registry,
            )

            self._node_registry = get_node_registry()
        return self._node_registry

    def _get_category_color(self, category: str) -> QColor:
        """Get color for a category."""
        try:
            from casare_rpa.presentation.canvas.graph.node_icons import CATEGORY_COLORS

            return CATEGORY_COLORS.get(category, QColor(0x80, 0x80, 0x80))
        except ImportError:
            # Fallback colors
            colors = {
                "basic": QColor(0x56, 0x9C, 0xD6),
                "browser": QColor(0xC5, 0x86, 0xC0),
                "control_flow": QColor(0xF4, 0x87, 0x71),
                "data_operations": QColor(0x89, 0xD1, 0x85),
                "desktop_automation": QColor(0xC5, 0x86, 0xC0),
                "error_handling": QColor(0xF4, 0x87, 0x71),
                "file_operations": QColor(0xDC, 0xDC, 0xAA),
                "rest_api": QColor(0x4E, 0xC9, 0xB0),
                "database": QColor(0x4E, 0xC9, 0xB0),
                "variable": QColor(0x9C, 0xDC, 0xFE),
            }
            return colors.get(category, QColor(0x80, 0x80, 0x80))

    def _populate_tree(self) -> None:
        """Populate the tree with all available nodes."""
        self._tree.clear()
        self._category_items.clear()
        self._node_items.clear()

        registry = self._get_registry()
        categories = registry.get_categories()

        # Sort categories by preferred order
        def sort_key(cat):
            try:
                return CATEGORY_ORDER.index(cat)
            except ValueError:
                return 999

        categories = sorted(categories, key=sort_key)

        for category in categories:
            nodes = registry.get_nodes_by_category(category)
            if not nodes:
                continue

            # Create category item
            display_name = CATEGORY_DISPLAY_NAMES.get(category, category.title())
            category_item = QTreeWidgetItem([f"{display_name} ({len(nodes)})"])
            category_item.setData(
                0, Qt.ItemDataRole.UserRole, {"type": "category", "name": category}
            )

            # Style category
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)

            color = self._get_category_color(category)
            category_item.setForeground(0, QBrush(color))

            self._category_items[category] = category_item

            # Sort nodes by name
            nodes = sorted(nodes, key=lambda n: getattr(n, "NODE_NAME", n.__name__))

            # Add node items
            for node_class in nodes:
                node_name = getattr(node_class, "NODE_NAME", node_class.__name__)
                node_type = node_class.__name__
                identifier = getattr(node_class, "__identifier__", "")

                node_item = QTreeWidgetItem([node_name])
                node_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {
                        "type": "node",
                        "node_type": node_type,
                        "identifier": identifier,
                        "name": node_name,
                        "category": category,
                    },
                )

                # Lighter color for nodes
                lighter_color = QColor(color)
                lighter_color.setAlpha(180)
                node_item.setForeground(0, QBrush(lighter_color))

                category_item.addChild(node_item)
                self._node_items[node_type] = node_item

            self._tree.addTopLevelItem(category_item)

        # Expand first few categories
        for i, category in enumerate(categories[:3]):
            if category in self._category_items:
                self._category_items[category].setExpanded(True)

        logger.info(
            f"Node library populated with {len(self._node_items)} nodes in {len(self._category_items)} categories"
        )

    def _on_search_changed(self, text: str) -> None:
        """Filter tree based on search text."""
        search_text = text.lower().strip()

        if not search_text:
            # Show all items
            for category_item in self._category_items.values():
                category_item.setHidden(False)
                for i in range(category_item.childCount()):
                    category_item.child(i).setHidden(False)
            return

        # Filter nodes
        for category, category_item in self._category_items.items():
            visible_children = 0
            for i in range(category_item.childCount()):
                child = category_item.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                node_name = data.get("name", "").lower()
                node_type = data.get("node_type", "").lower()

                # Match against name or type
                matches = search_text in node_name or search_text in node_type
                child.setHidden(not matches)
                if matches:
                    visible_children += 1

            # Hide category if no visible children
            category_item.setHidden(visible_children == 0)

            # Expand categories with matches
            if visible_children > 0:
                category_item.setExpanded(True)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click to create node."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data.get("type") == "node":
            node_type = data.get("node_type", "")
            identifier = data.get("identifier", "")
            logger.debug(f"Node requested: {node_type}")
            self.node_requested.emit(node_type, identifier)
        elif data.get("type") == "category":
            # Toggle expand/collapse for categories
            item.setExpanded(not item.isExpanded())

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle item expansion."""
        pass

    def _on_item_collapsed(self, item: QTreeWidgetItem) -> None:
        """Handle item collapse."""
        pass

    def _start_drag(self, supported_actions) -> None:
        """Custom drag handler to set proper mime data."""
        item = self._tree.currentItem()
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "node":
            return

        node_type = data.get("node_type", "")
        identifier = data.get("identifier", "")
        node_name = data.get("name", node_type)

        # Create drag with mime data
        drag = QDrag(self._tree)
        mime_data = QMimeData()

        # Set mime data - format used by NodeGraphWidget
        mime_data.setText(f"casare_node:{node_type}:{identifier}")
        mime_data.setData(
            "application/x-casare-node", f"{node_type}|{identifier}".encode()
        )

        drag.setMimeData(mime_data)

        # Emit signal
        self.node_drag_started.emit(node_type, identifier)

        logger.debug(f"Started drag for node: {node_name}")

        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)

    def refresh(self) -> None:
        """Refresh the node list (e.g., after plugins loaded)."""
        self._node_registry = None
        self._populate_tree()

    def expand_all(self) -> None:
        """Expand all categories."""
        self._tree.expandAll()

    def collapse_all(self) -> None:
        """Collapse all categories."""
        self._tree.collapseAll()

    def select_node_type(self, node_type: str) -> None:
        """Select and reveal a specific node type."""
        if node_type in self._node_items:
            item = self._node_items[node_type]
            # Expand parent
            parent = item.parent()
            if parent:
                parent.setExpanded(True)
            # Select and scroll to
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)
