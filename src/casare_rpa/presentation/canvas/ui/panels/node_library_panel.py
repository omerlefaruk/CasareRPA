"""
Node Library Panel - Activity/Node Browser.

Provides a dockable panel with a hierarchical categorized tree view of all
available nodes that can be dragged onto the canvas or double-clicked to create.

Features:
- Tree view organized by category with subcategory support
- Arbitrary nesting depth (e.g., google/gmail/send)
- Independent expand/collapse for each level
- Search/filter bar with fuzzy matching
- Drag-and-drop to canvas
- Double-click to create at center
- Category colors with distinct subcategory shades
"""

from typing import Optional, Dict, List, TYPE_CHECKING, Set

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QBrush

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_registry import NodeRegistry


class NodeLibraryPanel(QDockWidget):
    """
    Dockable panel showing all available nodes organized by category.

    Users can:
    - Browse nodes by category/subcategory in tree view
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
        self._category_items: Dict[str, QTreeWidgetItem] = {}  # path -> item
        self._node_items: Dict[str, QTreeWidgetItem] = {}  # node_type -> item
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

    def _get_category_color(self, category_path: str):
        """Get color for a category path."""
        try:
            from casare_rpa.presentation.canvas.graph.category_utils import (
                get_category_color,
            )

            return get_category_color(category_path)
        except ImportError:
            # Fallback
            from PySide6.QtGui import QColor

            return QColor(0x80, 0x80, 0x80)

    def _get_display_name(self, category_path: str) -> str:
        """Get display name for a category path."""
        try:
            from casare_rpa.presentation.canvas.graph.category_utils import (
                get_display_name,
            )

            return get_display_name(category_path)
        except ImportError:
            # Fallback
            return category_path.split("/")[-1].replace("_", " ").title()

    def _populate_tree(self) -> None:
        """Populate the tree with all available nodes organized hierarchically."""
        self._tree.clear()
        self._category_items.clear()
        self._node_items.clear()

        registry = self._get_registry()
        categories = registry.get_categories()

        # Import category utilities
        try:
            from casare_rpa.presentation.canvas.graph.category_utils import (
                CategoryPath,
                build_category_tree,
                update_category_counts,
                get_category_sort_key,
            )
        except ImportError:
            # Fallback to flat display
            self._populate_tree_flat(categories)
            return

        # Build category tree structure
        tree = build_category_tree(categories)

        # Count nodes per category
        category_counts = {}
        for category in categories:
            nodes = registry.get_nodes_by_category(category)
            if nodes:
                category_counts[category] = len(nodes)

        update_category_counts(tree, category_counts)

        # Sort root categories
        sorted_roots = sorted(
            tree.children.keys(), key=lambda k: get_category_sort_key(k)
        )

        # Build tree items recursively
        for root_name in sorted_roots:
            root_node = tree.children[root_name]
            if root_node.total_count > 0:  # Only show categories with nodes
                self._build_tree_items(root_node, None, registry)

        # Expand first 3 top-level categories
        top_items = [
            self._tree.topLevelItem(i)
            for i in range(min(3, self._tree.topLevelItemCount()))
        ]
        for item in top_items:
            if item:
                item.setExpanded(True)

        logger.info(
            f"Node library populated with {len(self._node_items)} nodes "
            f"in {len(self._category_items)} categories"
        )

    def _build_tree_items(
        self,
        category_node,
        parent_item: Optional[QTreeWidgetItem],
        registry: "NodeRegistry",
    ) -> Optional[QTreeWidgetItem]:
        """
        Recursively build tree items for a category node.

        Args:
            category_node: CategoryNode from category_utils
            parent_item: Parent QTreeWidgetItem (None for root)
            registry: Node registry

        Returns:
            Created QTreeWidgetItem or None if empty
        """
        # Skip empty categories (no nodes in self or descendants)
        if category_node.total_count == 0:
            return None

        category_path = category_node.path
        display_name = self._get_display_name(category_path)

        # Create category item
        if category_node.total_count > 0:
            label = f"{display_name} ({category_node.total_count})"
        else:
            label = display_name

        category_item = QTreeWidgetItem([label])
        category_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {"type": "category", "path": category_path, "name": category_node.name},
        )

        # Style category
        font = category_item.font(0)
        font.setBold(True)
        category_item.setFont(0, font)

        color = self._get_category_color(category_path)
        category_item.setForeground(0, QBrush(color))

        self._category_items[category_path] = category_item

        # Add to parent or as top-level
        if parent_item:
            parent_item.addChild(category_item)
        else:
            self._tree.addTopLevelItem(category_item)

        # Add child subcategories (sorted alphabetically)
        child_names = sorted(category_node.children.keys())
        for child_name in child_names:
            child_node = category_node.children[child_name]
            self._build_tree_items(child_node, category_item, registry)

        # Add direct nodes in this category (sorted by name)
        nodes = registry.get_nodes_by_category(category_path)
        if nodes:
            nodes = sorted(nodes, key=lambda n: getattr(n, "NODE_NAME", n.__name__))

            for node_class in nodes:
                self._add_node_item(node_class, category_item, category_path)

        return category_item

    def _add_node_item(
        self, node_class, parent_item: QTreeWidgetItem, category_path: str
    ) -> QTreeWidgetItem:
        """
        Add a node item to the tree.

        Args:
            node_class: Visual node class
            parent_item: Parent category item
            category_path: Full category path

        Returns:
            Created node item
        """
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
                "category": category_path,
            },
        )

        # Lighter color for nodes (with alpha)
        color = self._get_category_color(category_path)
        color.setAlpha(180)
        node_item.setForeground(0, QBrush(color))

        parent_item.addChild(node_item)
        self._node_items[node_type] = node_item

        return node_item

    def _populate_tree_flat(self, categories: List[str]) -> None:
        """
        Fallback flat tree population (legacy).

        Used when category_utils is not available.
        """
        # Legacy flat population
        from casare_rpa.presentation.canvas.graph.node_icons import CATEGORY_COLORS
        from PySide6.QtGui import QColor

        # Legacy display names
        LEGACY_DISPLAY_NAMES = {
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
            "triggers": "Triggers",
            "messaging": "Messaging",
            "ai_ml": "AI / Machine Learning",
            "document": "Document AI",
            "google": "Google Workspace",
        }

        LEGACY_ORDER = [
            "basic",
            "triggers",
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
            "messaging",
            "office_automation",
            "google",
            "ai_ml",
            "document",
            "scripts",
            "system",
            "utility",
        ]

        registry = self._get_registry()

        def sort_key(cat):
            try:
                return LEGACY_ORDER.index(cat)
            except ValueError:
                return 999

        categories = sorted(categories, key=sort_key)

        for category in categories:
            nodes = registry.get_nodes_by_category(category)
            if not nodes:
                continue

            display_name = LEGACY_DISPLAY_NAMES.get(category, category.title())
            category_item = QTreeWidgetItem([f"{display_name} ({len(nodes)})"])
            category_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"type": "category", "path": category, "name": category},
            )

            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)

            color = CATEGORY_COLORS.get(category, QColor(0x80, 0x80, 0x80))
            category_item.setForeground(0, QBrush(color))

            self._category_items[category] = category_item

            nodes = sorted(nodes, key=lambda n: getattr(n, "NODE_NAME", n.__name__))

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

                lighter_color = QColor(color)
                lighter_color.setAlpha(180)
                node_item.setForeground(0, QBrush(lighter_color))

                category_item.addChild(node_item)
                self._node_items[node_type] = node_item

            self._tree.addTopLevelItem(category_item)

        for i, category in enumerate(categories[:3]):
            if category in self._category_items:
                self._category_items[category].setExpanded(True)

    def _on_search_changed(self, text: str) -> None:
        """Filter tree based on search text with hierarchical support."""
        search_text = text.lower().strip()

        if not search_text:
            # Show all items and reset visibility
            self._reset_visibility()
            return

        # Track which categories have visible nodes
        categories_with_matches: Set[str] = set()

        # First pass: hide/show nodes based on search
        for node_type, node_item in self._node_items.items():
            data = node_item.data(0, Qt.ItemDataRole.UserRole)
            node_name = data.get("name", "").lower()
            node_type_lower = data.get("node_type", "").lower()
            category = data.get("category", "")

            matches = search_text in node_name or search_text in node_type_lower
            node_item.setHidden(not matches)

            if matches:
                # Track all ancestor categories
                self._add_ancestor_categories(category, categories_with_matches)

        # Second pass: update category visibility
        for category_path, category_item in self._category_items.items():
            has_matches = category_path in categories_with_matches
            category_item.setHidden(not has_matches)

            if has_matches:
                category_item.setExpanded(True)

    def _add_ancestor_categories(
        self, category_path: str, category_set: Set[str]
    ) -> None:
        """Add category and all its ancestors to the set."""
        category_set.add(category_path)

        # Add parent paths
        parts = category_path.split("/")
        for i in range(len(parts)):
            ancestor = "/".join(parts[: i + 1])
            category_set.add(ancestor)

    def _reset_visibility(self) -> None:
        """Reset all items to visible state and collapse to default."""
        for category_item in self._category_items.values():
            category_item.setHidden(False)
            category_item.setExpanded(False)

        for node_item in self._node_items.values():
            node_item.setHidden(False)

        # Re-expand only first 3 top-level categories (default state)
        for i in range(min(3, self._tree.topLevelItemCount())):
            item = self._tree.topLevelItem(i)
            if item:
                item.setExpanded(True)

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
        self._populated = False
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
            # Expand all ancestors
            parent = item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            # Select and scroll to
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)
