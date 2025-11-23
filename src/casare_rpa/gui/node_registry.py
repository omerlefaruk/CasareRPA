"""
Node registry and factory for creating and managing nodes.

This module provides the NodeRegistry for registering visual nodes
and the NodeFactory for creating node instances.
"""

from typing import Dict, Type, Optional, List, Tuple
from NodeGraphQt import NodeGraph
from loguru import logger

from .visual_nodes import (
    VisualNode,
    VISUAL_NODE_CLASSES,
    # Basic
    VisualStartNode,
    VisualEndNode,
    VisualCommentNode,
    # Browser
    VisualLaunchBrowserNode,
    VisualCloseBrowserNode,
    VisualNewTabNode,
    # Navigation
    VisualGoToURLNode,
    VisualGoBackNode,
    VisualGoForwardNode,
    VisualRefreshPageNode,
    # Interaction
    VisualClickElementNode,
    VisualTypeTextNode,
    VisualSelectDropdownNode,
    # Data
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualScreenshotNode,
    # Wait
    VisualWaitNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
    # Variable
    VisualSetVariableNode,
    VisualGetVariableNode,
    VisualIncrementVariableNode,
    # Control Flow
    VisualIfNode,
    VisualForLoopNode,
    VisualWhileLoopNode,
    VisualBreakNode,
    VisualContinueNode,
    VisualSwitchNode,
    # Error Handling
    VisualTryNode,
    VisualRetryNode,
    VisualRetrySuccessNode,
    VisualRetryFailNode,
    VisualThrowErrorNode,
)

from ..nodes import (
    # Basic
    StartNode,
    EndNode,
    CommentNode,
    # Browser
    LaunchBrowserNode,
    CloseBrowserNode,
    NewTabNode,
    # Navigation
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode,
    # Interaction
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode,
    # Data
    ExtractTextNode,
    GetAttributeNode,
    ScreenshotNode,
    # Wait
    WaitNode,
    WaitForElementNode,
    WaitForNavigationNode,
    # Variable
    SetVariableNode,
    GetVariableNode,
    IncrementVariableNode,
    # Control flow
    IfNode,
    ForLoopNode,
    WhileLoopNode,
    BreakNode,
    ContinueNode,
    SwitchNode,
    # Error handling
    TryNode,
    RetryNode,
    RetrySuccessNode,
    RetryFailNode,
    ThrowErrorNode,
)


# Mapping from visual node classes to CasareRPA node classes
CASARE_NODE_MAPPING = {
    # Basic
    VisualStartNode: StartNode,
    VisualEndNode: EndNode,
    VisualCommentNode: CommentNode,
    # Browser
    VisualLaunchBrowserNode: LaunchBrowserNode,
    VisualCloseBrowserNode: CloseBrowserNode,
    VisualNewTabNode: NewTabNode,
    # Navigation
    VisualGoToURLNode: GoToURLNode,
    VisualGoBackNode: GoBackNode,
    VisualGoForwardNode: GoForwardNode,
    VisualRefreshPageNode: RefreshPageNode,
    # Interaction
    VisualClickElementNode: ClickElementNode,
    VisualTypeTextNode: TypeTextNode,
    VisualSelectDropdownNode: SelectDropdownNode,
    # Data
    VisualExtractTextNode: ExtractTextNode,
    VisualGetAttributeNode: GetAttributeNode,
    VisualScreenshotNode: ScreenshotNode,
    # Wait
    VisualWaitNode: WaitNode,
    VisualWaitForElementNode: WaitForElementNode,
    VisualWaitForNavigationNode: WaitForNavigationNode,
    # Variable
    VisualSetVariableNode: SetVariableNode,
    VisualGetVariableNode: GetVariableNode,
    VisualIncrementVariableNode: IncrementVariableNode,
    # Control Flow
    VisualIfNode: IfNode,
    VisualForLoopNode: ForLoopNode,
    VisualWhileLoopNode: WhileLoopNode,
    VisualBreakNode: BreakNode,
    VisualContinueNode: ContinueNode,
    VisualSwitchNode: SwitchNode,
    # Error Handling
    VisualTryNode: TryNode,
    VisualRetryNode: RetryNode,
    VisualRetrySuccessNode: RetrySuccessNode,
    VisualRetryFailNode: RetryFailNode,
    VisualThrowErrorNode: ThrowErrorNode,
}


class NodeRegistry:
    """
    Registry for visual nodes.
    
    Manages node type registration with NodeGraphQt and provides
    node discovery functionality.
    """
    
    def __init__(self) -> None:
        """Initialize node registry."""
        self._registered_nodes: Dict[str, Type[VisualNode]] = {}
        self._categories: Dict[str, List[Type[VisualNode]]] = {}
    
    def register_node(
        self,
        node_class: Type[VisualNode],
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
        # Register all nodes with NodeGraphQt
        from .visual_nodes import VisualStartNode
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
                        viewer = graph.viewer()
                        pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                        node = graph.create_node(
                            f'{qmenu._first_match.__identifier__}.{qmenu._first_match.__name__}',
                            name=qmenu._first_match.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30]
                        )
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
        
        # Organize nodes by category and add to menu
        for category, nodes in self._categories.items():
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
                        # Get the current mouse position in scene coordinates
                        viewer = graph.viewer()
                        pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                        
                        # Create node at mouse cursor position (centered)
                        node = graph.create_node(
                            f'{cls.__identifier__}.{cls.__name__}',
                            name=cls.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30]
                        )
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
                                viewer = graph.viewer()
                                pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                                node = graph.create_node(
                                    f'{cls.__identifier__}.{cls.__name__}',
                                    name=cls.NODE_NAME,
                                    pos=[pos.x() - 100, pos.y() - 30]
                                )
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
                            viewer = graph.viewer()
                            pos = viewer.mapToScene(viewer.mapFromGlobal(viewer.cursor().pos()))
                            node = graph.create_node(
                                f'{cls.__identifier__}.{cls.__name__}',
                                name=cls.NODE_NAME,
                                pos=[pos.x() - 100, pos.y() - 30]
                            )
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
        
        # Focus search when menu is shown
        def on_menu_shown():
            search_input.setFocus()
            search_input.clear()
        
        qmenu.aboutToShow.connect(on_menu_shown)
        
        logger.info(f"Registered {len(VISUAL_NODE_CLASSES)} node types in context menu")
    
    def get_node_class(self, node_name: str) -> Optional[Type[VisualNode]]:
        """
        Get a node class by name.
        
        Args:
            node_name: Name of the node
            
        Returns:
            Node class or None if not found
        """
        return self._registered_nodes.get(node_name)
    
    def get_nodes_by_category(self, category: str) -> List[Type[VisualNode]]:
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
    
    def get_all_nodes(self) -> List[Type[VisualNode]]:
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
        node_class: Type[VisualNode],
        pos: Optional[Tuple[int, int]] = None
    ) -> VisualNode:
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
        visual_node: VisualNode,
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
        # Get the CasareRPA node class
        node_class = CASARE_NODE_MAPPING.get(type(visual_node))
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
        node_class: Type[VisualNode],
        pos: Optional[Tuple[int, int]] = None,
        **kwargs
    ) -> Tuple[VisualNode, object]:
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
