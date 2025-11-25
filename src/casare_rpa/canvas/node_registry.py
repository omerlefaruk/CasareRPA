"""
Node registry and factory for creating and managing nodes.

This module provides the NodeRegistry for registering visual nodes
and the NodeFactory for creating node instances.

AUTO-DISCOVERY SYSTEM:
When adding new nodes, you only need to:
1. Create the CasareRPA node class in nodes/ directory
2. Create the visual node class in visual_nodes.py with CASARE_NODE_CLASS attribute
3. That's it! The mapping is built automatically.

The CASARE_NODE_CLASS attribute on visual nodes specifies the CasareRPA node class name.
For desktop nodes, set CASARE_NODE_MODULE = "desktop" to look up from desktop_nodes module.
"""

from typing import Dict, Type, Optional, List, Tuple, Any
from NodeGraphQt import NodeGraph
from loguru import logger


def _build_casare_node_mapping() -> Dict[Type, Type]:
    """
    Dynamically build the mapping from visual node classes to CasareRPA node classes.

    This uses the CASARE_NODE_CLASS attribute on visual nodes to find the corresponding
    CasareRPA node class. The mapping is built once at module load time.

    Returns:
        Dictionary mapping visual node classes to CasareRPA node classes
    """
    from .visual_nodes import VISUAL_NODE_CLASSES, VisualNode

    mapping = {}

    for visual_class in VISUAL_NODE_CLASSES:
        # Skip the base class
        if visual_class is VisualNode:
            continue

        # Get the CasareRPA node class name from attribute or derive from class name
        casare_class_name = getattr(visual_class, 'CASARE_NODE_CLASS', None)
        casare_module = getattr(visual_class, 'CASARE_NODE_MODULE', None)

        if casare_class_name is None:
            # Derive from visual node class name: VisualFooNode -> FooNode
            visual_name = visual_class.__name__
            if visual_name.startswith('Visual') and visual_name.endswith('Node'):
                casare_class_name = visual_name[6:]  # Remove "Visual" prefix
            else:
                logger.warning(f"Cannot derive CasareRPA node name for {visual_name}")
                continue

        # Look up the CasareRPA node class
        try:
            if casare_module == "desktop":
                # Import from desktop_nodes
                from ..nodes import desktop_nodes
                casare_class = getattr(desktop_nodes, casare_class_name, None)
            elif casare_module == "file":
                # Import from file_nodes
                from ..nodes import file_nodes
                casare_class = getattr(file_nodes, casare_class_name, None)
            elif casare_module == "utility":
                # Import from utility_nodes
                from ..nodes import utility_nodes
                casare_class = getattr(utility_nodes, casare_class_name, None)
            elif casare_module == "office":
                # Import from desktop_nodes.office_nodes
                from ..nodes.desktop_nodes import office_nodes
                casare_class = getattr(office_nodes, casare_class_name, None)
            else:
                # Import from main nodes module (uses lazy loading)
                from ..nodes import _lazy_import, _NODE_REGISTRY
                if casare_class_name in _NODE_REGISTRY:
                    casare_class = _lazy_import(casare_class_name)
                else:
                    casare_class = None

            if casare_class is not None:
                mapping[visual_class] = casare_class
                logger.debug(f"Mapped {visual_class.__name__} -> {casare_class_name}")
            else:
                logger.warning(f"CasareRPA node class '{casare_class_name}' not found for {visual_class.__name__}")

        except Exception as e:
            logger.warning(f"Failed to load CasareRPA node class '{casare_class_name}': {e}")

    logger.info(f"Auto-discovered {len(mapping)} node mappings")
    return mapping


# Lazily built mapping - populated on first access
_casare_node_mapping: Optional[Dict[Type, Type]] = None


def get_casare_node_mapping() -> Dict[Type, Type]:
    """
    Get the mapping from visual node classes to CasareRPA node classes.

    The mapping is built lazily on first access using auto-discovery.

    Returns:
        Dictionary mapping visual node classes to CasareRPA node classes
    """
    global _casare_node_mapping
    if _casare_node_mapping is None:
        _casare_node_mapping = _build_casare_node_mapping()
    return _casare_node_mapping


# Legacy alias for backwards compatibility
CASARE_NODE_MAPPING = property(lambda self: get_casare_node_mapping())


class NodeRegistry:
    """
    Registry for visual nodes.

    Manages node type registration with NodeGraphQt and provides
    node discovery functionality.
    """

    def __init__(self) -> None:
        """Initialize node registry."""
        self._registered_nodes: Dict[str, Type] = {}
        self._categories: Dict[str, List[Type]] = {}

    def register_node(
        self,
        node_class: Type,
        graph: Optional[NodeGraph] = None
    ) -> None:
        """
        Register a visual node class.

        Args:
            node_class: Visual node class to register
            graph: Optional NodeGraph instance to register with
        """
        node_name = node_class.NODE_NAME
        category = node_class.NODE_CATEGORY

        # Store in registry
        self._registered_nodes[node_name] = node_class

        # Store in category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(node_class)

        # Register with NodeGraphQt if graph provided
        if graph is not None:
            graph.register_node(node_class)

        logger.debug(f"Registered node: {node_name} (category: {category})")

    def register_all_nodes(self, graph: NodeGraph) -> None:
        """
        Register all CasareRPA nodes with a NodeGraph.

        Args:
            graph: NodeGraph instance to register nodes with
        """
        from .visual_nodes import VISUAL_NODE_CLASSES

        # Register all nodes with NodeGraphQt
        for node_class in VISUAL_NODE_CLASSES:
            self.register_node(node_class, graph)

        # Get the graph's context menu (right-click on canvas to add nodes)
        graph_menu = graph.get_context_menu('graph')

        # Get the underlying QMenu and enhance it with search functionality
        from .searchable_menu import SearchableNodeMenu
        qmenu = graph_menu.qmenu

        # Clear the existing menu
        qmenu.clear()

        # Add search functionality to the existing QMenu
        from PySide6.QtWidgets import QWidgetAction, QLineEdit
        from PySide6.QtCore import Qt

        # Create search input widget with Enter key handler
        class SearchLineEdit(QLineEdit):
            def keyPressEvent(self, event):
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Create first matched node when Enter is pressed
                    if hasattr(qmenu, '_first_match') and qmenu._first_match:
                        logger.info(f"⏎ Enter pressed - creating node: {qmenu._first_match.NODE_NAME}")
                        # Use the initial mouse position captured when menu opened
                        pos = qmenu._initial_scene_pos
                        if pos is None:
                            # Fallback to current position if not captured
                            viewer = graph.viewer()
                            pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))

                        node = graph.create_node(
                            f'{qmenu._first_match.__identifier__}.{qmenu._first_match.__name__}',
                            name=qmenu._first_match.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30]
                        )
                        # Attach CasareRPA node immediately with unique ID
                        factory = get_node_factory()
                        casare_node = factory.create_casare_node(node)
                        if casare_node:
                            node.set_casare_node(casare_node)
                        qmenu.close()
                    event.accept()
                else:
                    super().keyPressEvent(event)

        search_input = SearchLineEdit()
        search_input.setPlaceholderText("Search nodes... (Press Enter to add first match)")
        search_input.setStyleSheet("""
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

        # Add search input as the first item in menu
        search_action = QWidgetAction(qmenu)
        search_action.setDefaultWidget(search_input)
        qmenu.addAction(search_action)
        qmenu.addSeparator()

        # Store node information and actions for search (as menu attributes to prevent deletion)
        qmenu._node_items = []  # (category, name, description)
        qmenu._all_actions = []  # List of all QAction objects
        qmenu._category_menus = {}  # category -> QMenu
        qmenu._first_match = None  # Store first matched node for Enter key
        qmenu._initial_scene_pos = None  # Store initial mouse position when menu opens

        # Organize nodes by category and add to menu (sorted A-Z, case-insensitive)
        for category, nodes in sorted(self._categories.items(), key=lambda x: x[0].lower()):
            category_label = category.replace('_', ' ').title()
            category_menu = qmenu.addMenu(category_label)
            qmenu._category_menus[category_label] = category_menu

            for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                # Get description from node class
                description = ""
                if node_class.__doc__:
                    description = node_class.__doc__.strip().split('\n')[0]

                qmenu._node_items.append((category_label, node_class.NODE_NAME, description))

                # Create a function to instantiate this specific node class
                def make_creator(cls):
                    def create_node():
                        # Use the initial mouse position captured when menu opened
                        pos = qmenu._initial_scene_pos
                        if pos is None:
                            # Fallback to current position if not captured
                            viewer = graph.viewer()
                            pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                            logger.info(f"📍 Creating node at FALLBACK position: ({pos.x()}, {pos.y()})")
                        else:
                            logger.info(f"📍 Creating node at STORED position: ({pos.x()}, {pos.y()})")

                        # Create node at initial mouse position (centered)
                        node = graph.create_node(
                            f'{cls.__identifier__}.{cls.__name__}',
                            name=cls.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30]
                        )
                        # Attach CasareRPA node immediately with unique ID
                        factory = get_node_factory()
                        casare_node = factory.create_casare_node(node)
                        if casare_node:
                            node.set_casare_node(casare_node)
                        return node
                    return create_node

                action = category_menu.addAction(node_class.NODE_NAME)
                action.triggered.connect(make_creator(node_class))
                action.setData({'category': category_label, 'name': node_class.NODE_NAME})
                qmenu._all_actions.append(action)

        # Store references needed for search functionality
        qmenu._search_input = search_input
        qmenu._graph = graph
        qmenu._category_data = {}  # Map node name -> (category, node_class)

        # Build mapping of node names to their classes for quick lookup
        for category, nodes in self._categories.items():
            category_label = category.replace('_', ' ').title()
            for node_class in nodes:
                qmenu._category_data[node_class.NODE_NAME] = (category_label, node_class)

        # Connect search functionality
        def on_search_changed(text):
            """Rebuild menu as flat list during search, categorized when empty."""
            from ..utils.fuzzy_search import fuzzy_search

            logger.info(f"🔍 Search text changed: '{text}'")

            # Remove all menu items except search widget and separator
            actions_to_remove = []
            for action in qmenu.actions():
                if action != search_action and not action.isSeparator():
                    actions_to_remove.append(action)

            for action in actions_to_remove:
                qmenu.removeAction(action)

            if not text.strip():
                # Restore full categorized menu structure
                logger.info("Empty search - restoring categorized menu")

                for category, nodes in self._categories.items():
                    category_label = category.replace('_', ' ').title()
                    category_menu = qmenu.addMenu(category_label)

                    for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                        def make_creator(cls):
                            def create_node():
                                # Use the initial mouse position captured when menu opened
                                pos = qmenu._initial_scene_pos
                                if pos is None:
                                    # Fallback to current position if not captured
                                    viewer = graph.viewer()
                                    pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))

                                node = graph.create_node(
                                    f'{cls.__identifier__}.{cls.__name__}',
                                    name=cls.NODE_NAME,
                                    pos=[pos.x() - 100, pos.y() - 30]
                                )
                                # Attach CasareRPA node immediately with unique ID
                                factory = get_node_factory()
                                casare_node = factory.create_casare_node(node)
                                if casare_node:
                                    node.set_casare_node(casare_node)
                                return node
                            return create_node

                        action = category_menu.addAction(node_class.NODE_NAME)
                        action.triggered.connect(make_creator(node_class))

                qmenu._first_match = None
                return

            # Perform fuzzy search and show ALL matching nodes in flat list
            results = fuzzy_search(text, qmenu._node_items)
            logger.info(f"Found {len(results)} matching nodes")

            if not results:
                no_results_action = qmenu.addAction("No matching nodes found")
                no_results_action.setEnabled(False)
                qmenu._first_match = None
                return

            # Add all matching nodes as flat list (no categories)
            for i, (category, name, description, score, positions) in enumerate(results):
                # Get the node class for this match
                if name in qmenu._category_data:
                    _, node_class = qmenu._category_data[name]

                    def make_creator(cls):
                        def create_node():
                            # Use the initial mouse position captured when menu opened
                            pos = qmenu._initial_scene_pos
                            if pos is None:
                                # Fallback to current position if not captured
                                viewer = graph.viewer()
                                pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))

                            node = graph.create_node(
                                f'{cls.__identifier__}.{cls.__name__}',
                                name=cls.NODE_NAME,
                                pos=[pos.x() - 100, pos.y() - 30]
                            )
                            # Attach CasareRPA node immediately with unique ID
                            factory = get_node_factory()
                            casare_node = factory.create_casare_node(node)
                            if casare_node:
                                node.set_casare_node(casare_node)
                            qmenu.close()  # Close menu after adding node
                            return node
                        return create_node

                    # Create action with category prefix for clarity
                    action_text = f"{name} ({category})"
                    action = qmenu.addAction(action_text)
                    action.triggered.connect(make_creator(node_class))
                    action.setData({'node_class': node_class, 'name': name})

                    # Mark first match visually
                    if i == 0:
                        font = action.font()
                        font.setBold(True)
                        action.setFont(font)
                        qmenu._first_match = node_class

            logger.info(f"Added {len(results)} nodes to flat list, first match: {qmenu._first_match.NODE_NAME if qmenu._first_match else 'None'}")

        search_input.textChanged.connect(on_search_changed)

        # Focus search when menu is shown and capture initial mouse position if not already set
        def on_menu_shown():
            # Only capture position if not already set by event filter (right-click or Tab)
            if qmenu._initial_scene_pos is None:
                viewer = graph.viewer()
                qmenu._initial_scene_pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                logger.info(f"📍 Menu opened (fallback) at scene position: ({qmenu._initial_scene_pos.x()}, {qmenu._initial_scene_pos.y()})")
            else:
                logger.info(f"📍 Menu opened with pre-captured position: ({qmenu._initial_scene_pos.x()}, {qmenu._initial_scene_pos.y()})")
            search_input.setFocus()
            search_input.clear()

        qmenu.aboutToShow.connect(on_menu_shown)

        # Note: Don't reset position on aboutToHide because it fires BEFORE
        # the action's triggered signal, which would cause the position to be None
        # when create_node() is called. The position will be overwritten on each
        # new right-click anyway.

        logger.info(f"Registered {len(VISUAL_NODE_CLASSES)} node types in context menu")

    def get_node_class(self, node_name: str) -> Optional[Type]:
        """
        Get a node class by name.

        Args:
            node_name: Name of the node

        Returns:
            Node class or None if not found
        """
        return self._registered_nodes.get(node_name)

    def get_nodes_by_category(self, category: str) -> List[Type]:
        """
        Get all nodes in a category.

        Args:
            category: Category name

        Returns:
            List of node classes in the category
        """
        return self._categories.get(category, [])

    def get_categories(self) -> List[str]:
        """
        Get all registered categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_all_nodes(self) -> List[Type]:
        """
        Get all registered node classes.

        Returns:
            List of all node classes
        """
        return list(self._registered_nodes.values())


class NodeFactory:
    """
    Factory for creating node instances.

    Handles creation of both visual and CasareRPA node instances
    and links them together.
    """

    def __init__(self) -> None:
        """Initialize node factory."""
        self._node_counter = 0

    def create_visual_node(
        self,
        graph: NodeGraph,
        node_class: Type,
        pos: Optional[Tuple[int, int]] = None
    ) -> Any:
        """
        Create a visual node instance in the graph.

        Args:
            graph: NodeGraph instance
            node_class: Visual node class
            pos: Optional position (x, y) for the node

        Returns:
            Created visual node instance
        """
        # Create visual node
        visual_node = graph.create_node(
            f"{node_class.__identifier__}.{node_class.NODE_NAME}",
            pos=pos
        )

        # Setup ports
        visual_node.setup_ports()

        logger.debug(f"Created visual node: {node_class.NODE_NAME}")

        return visual_node

    def create_casare_node(
        self,
        visual_node: Any,
        **kwargs
    ) -> Optional[object]:
        """
        Create a CasareRPA node instance for a visual node.

        Args:
            visual_node: Visual node instance
            **kwargs: Additional arguments for node creation

        Returns:
            Created CasareRPA node instance or None
        """
        # Get the CasareRPA node class from auto-discovered mapping
        mapping = get_casare_node_mapping()
        node_class = mapping.get(type(visual_node))

        if node_class is None:
            logger.error(f"No CasareRPA node mapping for {type(visual_node).__name__}")
            return None

        # Generate unique node ID
        self._node_counter += 1
        node_id = f"{node_class.__name__}_{self._node_counter}"

        # Create CasareRPA node
        casare_node = node_class(node_id=node_id, **kwargs)

        # Link nodes
        visual_node.set_casare_node(casare_node)

        logger.debug(f"Created CasareRPA node: {node_class.__name__} (id: {node_id})")

        return casare_node

    def create_linked_node(
        self,
        graph: NodeGraph,
        node_class: Type,
        pos: Optional[Tuple[int, int]] = None,
        **kwargs
    ) -> Tuple[Any, object]:
        """
        Create both visual and CasareRPA nodes and link them.

        Args:
            graph: NodeGraph instance
            node_class: Visual node class
            pos: Optional position (x, y) for the node
            **kwargs: Additional arguments for CasareRPA node creation

        Returns:
            Tuple of (visual_node, casare_node)
        """
        # Create visual node
        visual_node = self.create_visual_node(graph, node_class, pos)

        # Create CasareRPA node
        casare_node = self.create_casare_node(visual_node, **kwargs)

        return visual_node, casare_node


# Global instances
_node_registry = NodeRegistry()
_node_factory = NodeFactory()


def get_node_registry() -> NodeRegistry:
    """
    Get the global node registry instance.

    Returns:
        NodeRegistry instance
    """
    return _node_registry


def get_node_factory() -> NodeFactory:
    """
    Get the global node factory instance.

    Returns:
        NodeFactory instance
    """
    return _node_factory
