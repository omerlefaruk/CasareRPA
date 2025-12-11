"""
Node registry and factory for creating and managing nodes.

This module provides the NodeRegistry for registering visual nodes
and the NodeFactory for creating node instances.

AUTO-DISCOVERY SYSTEM:
When adding new nodes, you only need to:
1. Create the CasareRPA node class in nodes/ directory
2. Create the visual node class in presentation/canvas/visual_nodes/ with CASARE_NODE_CLASS attribute
3. That's it! The mapping is built automatically.

The CASARE_NODE_CLASS attribute on visual nodes specifies the CasareRPA node class name.
For desktop nodes, set CASARE_NODE_MODULE = "desktop" to look up from desktop_nodes module.

PERFORMANCE OPTIMIZATION:
Node mapping is cached to disk at ~/.casare_rpa/cache/node_mapping_cache.json.
Cache is invalidated when the visual node registry changes (hash-based).
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Type, Optional, List, Tuple, Any, TYPE_CHECKING
from functools import lru_cache
from NodeGraphQt import NodeGraph
from loguru import logger

if TYPE_CHECKING:
    pass


# =============================================================================
# DISK CACHING CONSTANTS
# =============================================================================
_CACHE_DIR = Path.home() / ".casare_rpa" / "cache"
_MAPPING_CACHE_FILE = _CACHE_DIR / "node_mapping_cache.json"
_CACHE_VERSION = "1.0"  # Increment when node structure changes


# =============================================================================
# ESSENTIAL NODES FOR FAST STARTUP
# =============================================================================
# Only these nodes are registered at startup. Others are deferred.
# PERFORMANCE: Loads ~8 nodes instead of 300+ for faster boot time.

ESSENTIAL_NODE_NAMES = [
    "VisualStartNode",
    "VisualEndNode",
    "VisualCommentNode",
    "VisualIfNode",
    "VisualForLoopNode",
    "VisualMessageBoxNode",
    "VisualSetVariableNode",
    "VisualGetVariableNode",
]


# =============================================================================
# DISK CACHING FUNCTIONS
# =============================================================================


def _get_registry_hash() -> str:
    """
    Get hash of the visual node registry to detect changes.

    Returns:
        MD5 hash of sorted registry keys (first 12 chars)
    """
    from casare_rpa.presentation.canvas.visual_nodes import _VISUAL_NODE_REGISTRY

    registry_str = json.dumps(sorted(_VISUAL_NODE_REGISTRY.keys()))
    return hashlib.md5(registry_str.encode()).hexdigest()[:12]


def _load_mapping_from_cache() -> Optional[Dict[str, str]]:
    """
    Load node mapping from disk cache.

    Returns:
        Dict mapping visual class name to casare class name, or None if cache invalid
    """
    try:
        if not _MAPPING_CACHE_FILE.exists():
            return None

        with open(_MAPPING_CACHE_FILE, "r") as f:
            cache_data = json.load(f)

        # Validate cache version and hash
        if cache_data.get("version") != _CACHE_VERSION:
            logger.debug("Cache version mismatch, rebuilding")
            return None

        if cache_data.get("registry_hash") != _get_registry_hash():
            logger.debug("Registry hash mismatch, rebuilding")
            return None

        logger.debug(
            f"Loaded node mapping from cache ({len(cache_data.get('mapping', {}))} entries)"
        )
        return cache_data.get("mapping", {})

    except Exception as e:
        logger.debug(f"Failed to load mapping cache: {e}")
        return None


def _save_mapping_to_cache(mapping: Dict[Type, Type]) -> None:
    """
    Save node mapping to disk cache.

    Args:
        mapping: Dict mapping visual class to casare class
    """
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format (class names only)
        serializable_mapping = {
            visual_cls.__name__: casare_cls.__name__
            for visual_cls, casare_cls in mapping.items()
        }

        cache_data = {
            "version": _CACHE_VERSION,
            "registry_hash": _get_registry_hash(),
            "mapping": serializable_mapping,
        }

        with open(_MAPPING_CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.debug(f"Saved node mapping cache ({len(serializable_mapping)} entries)")

    except Exception as e:
        logger.warning(f"Failed to save mapping cache: {e}")


def _build_casare_node_mapping_with_cache() -> Dict[Type, Type]:
    """
    Build the casare node mapping with disk caching.

    PERFORMANCE: Uses disk cache to avoid expensive imports on subsequent starts.
    Cache is invalidated when the visual node registry changes.

    Returns:
        Dictionary mapping visual node classes to CasareRPA node classes
    """
    # Try loading from cache first
    cached_mapping = _load_mapping_from_cache()

    if cached_mapping is not None:
        # Reconstruct the full mapping from cached class names
        from casare_rpa.presentation.canvas.visual_nodes import (
            _lazy_import as visual_lazy_import,
            _VISUAL_NODE_REGISTRY,
        )

        mapping = {}
        success_count = 0

        for visual_name, casare_name in cached_mapping.items():
            try:
                # Get visual class
                if visual_name not in _VISUAL_NODE_REGISTRY:
                    continue

                visual_cls = visual_lazy_import(visual_name)

                # Get casare class module info from visual class
                casare_module = getattr(visual_cls, "CASARE_NODE_MODULE", None)

                # Look up the CasareRPA node class based on module
                casare_class = None
                if casare_module == "desktop":
                    from casare_rpa.nodes import desktop_nodes

                    casare_class = getattr(desktop_nodes, casare_name, None)
                elif casare_module == "file":
                    from casare_rpa.nodes import file_nodes

                    casare_class = getattr(file_nodes, casare_name, None)
                elif casare_module == "utility":
                    from casare_rpa.nodes import utility_nodes

                    casare_class = getattr(utility_nodes, casare_name, None)
                elif casare_module == "office":
                    from casare_rpa.nodes.desktop_nodes import office_nodes

                    casare_class = getattr(office_nodes, casare_name, None)
                else:
                    # Import from main nodes module (uses lazy loading)
                    from casare_rpa.nodes import (
                        _lazy_import as nodes_lazy_import,
                        _NODE_REGISTRY,
                    )

                    if casare_name in _NODE_REGISTRY:
                        casare_class = nodes_lazy_import(casare_name)

                if casare_class is not None:
                    mapping[visual_cls] = casare_class
                    success_count += 1

            except Exception:
                pass  # Skip failed lookups, will be rebuilt

        # At least 80% success rate to use cache
        if success_count > len(cached_mapping) * 0.8:
            logger.debug(
                f"Reconstructed mapping from cache ({success_count}/{len(cached_mapping)} entries)"
            )
            return mapping

        logger.debug("Cache reconstruction had too many failures, rebuilding")

    # Build from scratch
    mapping = _build_casare_node_mapping()

    # Save to cache for next time
    _save_mapping_to_cache(mapping)

    return mapping


def _build_casare_node_mapping() -> Dict[Type, Type]:
    """
    Dynamically build the mapping from visual node classes to CasareRPA node classes.

    This uses the CASARE_NODE_CLASS attribute on visual nodes to find the corresponding
    CasareRPA node class. The mapping is built once at module load time.

    Returns:
        Dictionary mapping visual node classes to CasareRPA node classes
    """
    # Lazy import to avoid circular dependency
    from casare_rpa.presentation.canvas.visual_nodes import ALL_VISUAL_NODE_CLASSES
    from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

    # Visual-only nodes that don't need CasareRPA logic counterparts
    # These are annotation/documentation nodes for organizing workflows
    VISUAL_ONLY_NODES = {
        "VisualRichCommentNode",
        "VisualStickyNoteNode",
        "VisualHeaderCommentNode",
    }

    mapping = {}

    for visual_class in ALL_VISUAL_NODE_CLASSES:
        # Skip the base class
        if visual_class is VisualNode:
            continue

        # Skip visual-only nodes (annotation/documentation nodes)
        if visual_class.__name__ in VISUAL_ONLY_NODES:
            logger.debug(f"Skipping visual-only node: {visual_class.__name__}")
            continue

        # Skip composite marker nodes (they create multiple real nodes)
        if getattr(visual_class, "COMPOSITE_NODE", False):
            logger.debug(f"Skipping composite marker node: {visual_class.__name__}")
            continue

        # Skip reroute nodes - they're purely visual (wire routing), no execution
        if "Reroute" in visual_class.__name__:
            logger.debug(f"Skipping reroute node: {visual_class.__name__}")
            continue

        # Get the CasareRPA node class name from attribute or derive from class name
        casare_class_name = getattr(visual_class, "CASARE_NODE_CLASS", None)
        casare_module = getattr(visual_class, "CASARE_NODE_MODULE", None)

        if casare_class_name is None:
            # Derive from visual node class name: VisualFooNode -> FooNode
            visual_name = visual_class.__name__
            if visual_name.startswith("Visual") and visual_name.endswith("Node"):
                casare_class_name = visual_name[6:]  # Remove "Visual" prefix
            else:
                logger.warning(f"Cannot derive CasareRPA node name for {visual_name}")
                continue

        # Look up the CasareRPA node class
        try:
            if casare_module == "desktop":
                # Import from desktop_nodes
                from casare_rpa.nodes import desktop_nodes

                casare_class = getattr(desktop_nodes, casare_class_name, None)
            elif casare_module == "file":
                # Import from file_nodes
                from casare_rpa.nodes import file_nodes

                casare_class = getattr(file_nodes, casare_class_name, None)
            elif casare_module == "utility":
                # Import from utility_nodes
                from casare_rpa.nodes import utility_nodes

                casare_class = getattr(utility_nodes, casare_class_name, None)
            elif casare_module == "office":
                # Import from desktop_nodes.office_nodes
                from casare_rpa.nodes.desktop_nodes import office_nodes

                casare_class = getattr(office_nodes, casare_class_name, None)
            else:
                # Import from main nodes module (uses lazy loading)
                from casare_rpa.nodes import _lazy_import, _NODE_REGISTRY

                if casare_class_name in _NODE_REGISTRY:
                    casare_class = _lazy_import(casare_class_name)
                else:
                    casare_class = None

            if casare_class is not None:
                mapping[visual_class] = casare_class
                logger.debug(f"Mapped {visual_class.__name__} -> {casare_class_name}")
            else:
                logger.warning(
                    f"CasareRPA node class '{casare_class_name}' not found for {visual_class.__name__}"
                )

        except Exception as e:
            logger.warning(
                f"Failed to load CasareRPA node class '{casare_class_name}': {e}"
            )

    return mapping


# Lazily built mappings - populated on first access
_casare_node_mapping: Optional[Dict[Type, Type]] = None
_node_type_mapping: Optional[Dict[str, tuple]] = None


def get_casare_node_mapping() -> Dict[Type, Type]:
    """
    Get the mapping from visual node classes to CasareRPA node classes.

    The mapping is built lazily on first access using auto-discovery.
    PERFORMANCE: Uses disk caching to avoid rebuilding on subsequent starts.

    Returns:
        Dictionary mapping visual node classes to CasareRPA node classes
    """
    global _casare_node_mapping
    if _casare_node_mapping is None:
        _casare_node_mapping = _build_casare_node_mapping_with_cache()
    return _casare_node_mapping


# Legacy alias for backwards compatibility
CASARE_NODE_MAPPING = property(lambda self: get_casare_node_mapping())


# =============================================================================
# UNIFIED NODE TYPE LOOKUP SYSTEM
# =============================================================================
# These functions provide a single source of truth for looking up nodes by type.
# Use these instead of building your own mappings!


def _build_node_type_mapping() -> Dict[str, tuple]:
    """
    Build unified mapping from node type name to all related classes/identifiers.

    Returns:
        Dict mapping node_type (e.g., "MessageBoxNode") to tuple of:
        (visual_class, identifier_for_create_node, casare_class_or_None)
    """
    # Lazy import to avoid circular dependency
    from casare_rpa.presentation.canvas.visual_nodes import ALL_VISUAL_NODE_CLASSES

    mapping = {}
    casare_mapping = get_casare_node_mapping()

    for visual_class in ALL_VISUAL_NODE_CLASSES:
        visual_name = visual_class.__name__

        # Derive node type from visual class name: VisualXxxNode -> XxxNode
        if visual_name.startswith("Visual") and visual_name.endswith("Node"):
            node_type = visual_name[6:]  # Remove "Visual" prefix

            # Build identifier for graph.create_node()
            identifier = f"{visual_class.__identifier__}.{visual_name}"

            # Get CasareRPA class from auto-discovery
            casare_class = casare_mapping.get(visual_class)

            mapping[node_type] = (visual_class, identifier, casare_class)

    logger.debug(f"Built unified node type mapping with {len(mapping)} types")
    return mapping


def get_node_type_mapping() -> Dict[str, tuple]:
    """
    Get the unified mapping from node type names to classes.

    This is the SINGLE SOURCE OF TRUTH for node lookups.
    Use this instead of building your own mappings!

    Returns:
        Dict mapping node_type (e.g., "MessageBoxNode") to tuple of:
        (visual_class, identifier_for_create_node, casare_class_or_None)

    Example:
        mapping = get_node_type_mapping()
        visual_class, identifier, casare_class = mapping["MessageBoxNode"]
        node = graph.create_node(identifier)
    """
    global _node_type_mapping
    if _node_type_mapping is None:
        _node_type_mapping = _build_node_type_mapping()
    return _node_type_mapping


@lru_cache(maxsize=256)
def get_visual_class_for_type(node_type: str) -> Optional[Type]:
    """
    Get the visual node class for a node type name.

    Uses LRU caching for performance (256 entries).

    Args:
        node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

    Returns:
        Visual node class or None if not found
    """
    mapping = get_node_type_mapping()
    entry = mapping.get(node_type)
    return entry[0] if entry else None


@lru_cache(maxsize=256)
def get_identifier_for_type(node_type: str) -> Optional[str]:
    """
    Get the graph.create_node() identifier for a node type.

    Uses LRU caching for performance (256 entries).

    Args:
        node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

    Returns:
        Identifier string for graph.create_node() or None if not found

    Example:
        identifier = get_identifier_for_type("MessageBoxNode")
        node = graph.create_node(identifier)
    """
    mapping = get_node_type_mapping()
    entry = mapping.get(node_type)
    return entry[1] if entry else None


@lru_cache(maxsize=256)
def get_casare_class_for_type(node_type: str) -> Optional[Type]:
    """
    Get the CasareRPA node class for a node type name.

    Uses LRU caching for performance (256 entries).

    Args:
        node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

    Returns:
        CasareRPA node class or None if not found
    """
    mapping = get_node_type_mapping()
    entry = mapping.get(node_type)
    return entry[2] if entry else None


def get_all_node_types() -> List[str]:
    """
    Get list of all registered node type names.

    Returns:
        List of node type names (e.g., ["StartNode", "EndNode", "MessageBoxNode", ...])
    """
    return list(get_node_type_mapping().keys())


def is_valid_node_type(node_type: str) -> bool:
    """
    Check if a node type name is valid/registered.

    Args:
        node_type: Node type name to check

    Returns:
        True if node type exists, False otherwise
    """
    return node_type in get_node_type_mapping()


def create_node_from_type(
    graph,
    node_type: str,
    node_id: Optional[str] = None,
    config: Optional[dict] = None,
    position: Optional[tuple] = None,
) -> Optional[Any]:
    """
    Create a visual node with linked CasareRPA node from node type name.

    This is the recommended way to create nodes programmatically.

    Args:
        graph: NodeGraph instance
        node_type: Node type name (e.g., "MessageBoxNode")
        node_id: Optional specific node ID (auto-generated if not provided)
        config: Optional config dict for the CasareRPA node
        position: Optional (x, y) position tuple

    Returns:
        Created visual node with linked CasareRPA node, or None on failure

    Example:
        node = create_node_from_type(
            graph, "MessageBoxNode",
            config={"message": "Hello!"},
            position=(100, 200)
        )
    """
    mapping = get_node_type_mapping()
    entry = mapping.get(node_type)

    if not entry:
        logger.error(f"Unknown node type: {node_type}")
        return None

    visual_class, identifier, casare_class = entry

    try:
        # Create visual node
        pos = list(position) if position else None
        visual_node = graph.create_node(identifier, pos=pos)

        if not visual_node:
            logger.error(f"Failed to create visual node for {node_type}")
            return None

        # Create CasareRPA node
        if casare_class:
            # Generate node ID if not provided
            if not node_id:
                from casare_rpa.utils.id_generator import generate_node_id

                node_id = generate_node_id(casare_class.__name__)

            casare_node = casare_class(node_id, config or {})
            visual_node.set_casare_node(casare_node)
        else:
            logger.warning(f"No CasareRPA class for {node_type} - visual-only node")

        return visual_node

    except Exception as e:
        logger.error(f"Failed to create node {node_type}: {e}")
        return None


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
        self, node_class: Type, graph: Optional[NodeGraph] = None
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
        # Lazy import to avoid circular dependency
        from casare_rpa.presentation.canvas.visual_nodes import ALL_VISUAL_NODE_CLASSES

        # Register all nodes with NodeGraphQt (including internal nodes for programmatic creation)
        for node_class in ALL_VISUAL_NODE_CLASSES:
            self.register_node(node_class, graph)

        # Get the graph's context menu (right-click on canvas to add nodes)
        graph_menu = graph.get_context_menu("graph")

        # Get the underlying QMenu and enhance it with search functionality
        qmenu = graph_menu.qmenu

        # Clear the existing menu
        qmenu.clear()

        # Add search functionality to the existing QMenu
        from PySide6.QtWidgets import QWidgetAction, QLineEdit
        from PySide6.QtCore import Qt

        # Track last created node ID for chaining with Shift+Enter
        qmenu._last_created_node_id = None

        # Create search input widget with Enter key handler
        class SearchLineEdit(QLineEdit):
            def _find_node_by_id(self, node_id):
                """Find a node in the graph by its ID."""
                for n in graph.all_nodes():
                    n_id = n.id() if callable(n.id) else n.id
                    if n_id == node_id:
                        return n
                return None

            def keyPressEvent(self, event):
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Check if Shift is held for auto-connect mode
                    auto_connect = bool(event.modifiers() & Qt.ShiftModifier)

                    # Create first matched node when Enter is pressed
                    if hasattr(qmenu, "_first_match") and qmenu._first_match:
                        # Determine source node for auto-connect
                        source_node = None
                        if auto_connect:
                            # First try: use last created node (for chaining)
                            if qmenu._last_created_node_id:
                                source_node = self._find_node_by_id(
                                    qmenu._last_created_node_id
                                )
                            # Fallback: use selected node
                            if not source_node:
                                selected_nodes = graph.selected_nodes()
                                if selected_nodes:
                                    source_node = selected_nodes[-1]

                        # Calculate position
                        if auto_connect and source_node:
                            # Place to the right of the source node
                            source_pos = source_node.pos()
                            # Get node width + spacing
                            node_width = 220
                            spacing = 80
                            pos_x = source_pos[0] + node_width + spacing
                            pos_y = source_pos[1]
                        else:
                            # Use mouse position
                            pos = qmenu._initial_scene_pos
                            if pos is None:
                                viewer = graph.viewer()
                                pos = viewer.mapToScene(
                                    viewer.mapFromGlobal(viewer.cursor().pos())
                                )
                            pos_x = pos.x() - 100
                            pos_y = pos.y() - 30

                        node = graph.create_node(
                            f"{qmenu._first_match.__identifier__}.{qmenu._first_match.__name__}",
                            name=qmenu._first_match.NODE_NAME,
                            pos=[pos_x, pos_y],
                        )
                        # Skip CasareRPA node for composite nodes (they create multiple nodes)
                        if not getattr(qmenu._first_match, "COMPOSITE_NODE", False):
                            # Attach CasareRPA node immediately with unique ID
                            factory = get_node_factory()
                            casare_node = factory.create_casare_node(node)
                            if casare_node:
                                node.set_casare_node(casare_node)

                        # Auto-connect to source node if Shift+Enter
                        if auto_connect and source_node:
                            self._auto_connect_nodes(graph, source_node, node)

                        # Track this node's ID for chaining (use graph ID, not custom ID)
                        # NodeGraphQt nodes: id() is a method, but handle both cases
                        node_id = node.id() if callable(node.id) else node.id
                        qmenu._last_created_node_id = node_id
                        logger.debug(f"Stored last created node ID: {node_id}")

                        # Select the new node
                        graph.clear_selection()
                        node.set_selected(True)

                        qmenu.close()
                    event.accept()
                else:
                    super().keyPressEvent(event)

            def _auto_connect_nodes(self, graph, source_node, target_node):
                """Auto-connect exec output of source to exec input of target."""
                try:
                    # Find exec_out port on source node (output_ports() returns list)
                    source_output = None
                    output_ports = source_node.output_ports()
                    for port in output_ports:
                        port_name = port.name().lower()
                        if "exec" in port_name or port_name in (
                            "exec_out",
                            "output",
                            "out",
                        ):
                            source_output = port
                            break
                    # Fallback: use first output port
                    if not source_output and output_ports:
                        source_output = output_ports[0]

                    # Find exec_in port on target node (input_ports() returns list)
                    target_input = None
                    input_ports = target_node.input_ports()
                    for port in input_ports:
                        port_name = port.name().lower()
                        if "exec" in port_name or port_name in (
                            "exec_in",
                            "input",
                            "in",
                        ):
                            target_input = port
                            break
                    # Fallback: use first input port
                    if not target_input and input_ports:
                        target_input = input_ports[0]

                    # Connect if both ports found
                    if source_output and target_input:
                        source_output.connect_to(target_input)
                        logger.info(
                            f"Auto-connected {source_node.name()} -> {target_node.name()}"
                        )
                except Exception as e:
                    logger.warning(f"Auto-connect failed: {e}")

        search_input = SearchLineEdit()
        search_input.setPlaceholderText("Search... Enter=add, Shift+Enter=add+connect")
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

        # Import category utilities for display names
        try:
            from casare_rpa.presentation.canvas.graph.category_utils import (
                get_display_name,
                get_category_sort_key,
            )

            use_hierarchy = True
        except ImportError:
            use_hierarchy = False

        def get_or_create_submenu(parent_menu, category_path: str):
            """Get or create nested submenu for category path."""
            if category_path in qmenu._category_menus:
                return qmenu._category_menus[category_path]

            parts = category_path.split("/")
            if len(parts) == 1:
                # Root category
                if use_hierarchy:
                    label = get_display_name(category_path)
                else:
                    label = category_path.replace("_", " ").title()
                menu = parent_menu.addMenu(label)
                qmenu._category_menus[category_path] = menu
                return menu
            else:
                # Nested category - ensure parent exists first
                parent_path = "/".join(parts[:-1])
                parent_submenu = get_or_create_submenu(parent_menu, parent_path)
                if use_hierarchy:
                    label = get_display_name(category_path)
                else:
                    label = parts[-1].replace("_", " ").title()
                menu = parent_submenu.addMenu(label)
                qmenu._category_menus[category_path] = menu
                return menu

        # Sort categories by hierarchy (root categories first, then alphabetically)
        if use_hierarchy:
            sorted_categories = sorted(
                self._categories.items(), key=lambda x: get_category_sort_key(x[0])
            )
        else:
            sorted_categories = sorted(
                self._categories.items(), key=lambda x: x[0].lower()
            )

        # Organize nodes by category and add to nested menus
        for category, nodes in sorted_categories:
            if use_hierarchy:
                category_label = get_display_name(category)
            else:
                category_label = category.replace("_", " ").title()

            category_menu = get_or_create_submenu(qmenu, category)

            for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                # Skip internal nodes (created programmatically, not from menu)
                if getattr(node_class, "INTERNAL_NODE", False):
                    continue

                # Get description from node class
                description = ""
                if node_class.__doc__:
                    description = node_class.__doc__.strip().split("\n")[0]

                qmenu._node_items.append(
                    (category_label, node_class.NODE_NAME, description)
                )

                # Create a function to instantiate this specific node class
                def make_creator(cls):
                    def create_node():
                        # Use the initial mouse position captured when menu opened
                        pos = qmenu._initial_scene_pos
                        if pos is None:
                            # Fallback to current position if not captured
                            viewer = graph.viewer()
                            pos = viewer.mapToScene(
                                viewer.mapFromGlobal(viewer.cursor().pos())
                            )

                        # Create node at initial mouse position (centered)
                        node = graph.create_node(
                            f"{cls.__identifier__}.{cls.__name__}",
                            name=cls.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30],
                        )
                        # Skip CasareRPA node for composite nodes (they create multiple nodes)
                        # The composite handling in node_graph_widget will create the real nodes
                        if not getattr(cls, "COMPOSITE_NODE", False):
                            # Attach CasareRPA node immediately with unique ID
                            factory = get_node_factory()
                            casare_node = factory.create_casare_node(node)
                            if casare_node:
                                node.set_casare_node(casare_node)
                        return node

                    return create_node

                action = category_menu.addAction(node_class.NODE_NAME)
                action.triggered.connect(make_creator(node_class))
                action.setData(
                    {"category": category_label, "name": node_class.NODE_NAME}
                )
                qmenu._all_actions.append(action)

        # Store references needed for search functionality
        qmenu._search_input = search_input
        qmenu._graph = graph
        qmenu._category_data = {}  # Map node name -> (category, node_class)

        # Build mapping of node names to their classes for quick lookup
        for category, nodes in self._categories.items():
            category_label = category.replace("_", " ").title()
            for node_class in nodes:
                # Skip internal nodes from search/menu
                if getattr(node_class, "INTERNAL_NODE", False):
                    continue
                qmenu._category_data[node_class.NODE_NAME] = (
                    category_label,
                    node_class,
                )

        # Pre-build SearchIndex for lightning-fast search (avoids rebuilding on every keystroke)
        from casare_rpa.utils.fuzzy_search import SearchIndex

        qmenu._search_index = SearchIndex(qmenu._node_items)

        # Connect search functionality
        def on_search_changed(text):
            """Rebuild menu as flat list during search, categorized when empty."""

            # Remove all menu items except search widget and separator
            actions_to_remove = []
            for action in qmenu.actions():
                if action != search_action and not action.isSeparator():
                    actions_to_remove.append(action)

            for action in actions_to_remove:
                qmenu.removeAction(action)

            if not text.strip():
                # Restore full hierarchical categorized menu structure
                # Clear and rebuild category menus cache
                qmenu._category_menus.clear()

                # Sort categories hierarchically
                if use_hierarchy:
                    sorted_cats = sorted(
                        self._categories.items(),
                        key=lambda x: get_category_sort_key(x[0]),
                    )
                else:
                    sorted_cats = sorted(
                        self._categories.items(), key=lambda x: x[0].lower()
                    )

                for category, nodes in sorted_cats:
                    # Use hierarchical submenu creation
                    category_menu = get_or_create_submenu(qmenu, category)

                    for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                        # Skip internal nodes (created programmatically, not from menu)
                        if getattr(node_class, "INTERNAL_NODE", False):
                            continue

                        def make_creator(cls):
                            def create_node():
                                # Use the initial mouse position captured when menu opened
                                pos = qmenu._initial_scene_pos
                                if pos is None:
                                    # Fallback to current position if not captured
                                    viewer = graph.viewer()
                                    pos = viewer.mapToScene(
                                        viewer.mapFromGlobal(viewer.cursor().pos())
                                    )

                                node = graph.create_node(
                                    f"{cls.__identifier__}.{cls.__name__}",
                                    name=cls.NODE_NAME,
                                    pos=[pos.x() - 100, pos.y() - 30],
                                )
                                # Skip CasareRPA node for composite nodes (they create multiple nodes)
                                if not getattr(cls, "COMPOSITE_NODE", False):
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

            # Perform fuzzy search using pre-built SearchIndex (lightning-fast, top 15 results)
            results = qmenu._search_index.search(text)

            if not results:
                no_results_action = qmenu.addAction("No matching nodes found")
                no_results_action.setEnabled(False)
                qmenu._first_match = None
                return

            # Add all matching nodes as flat list (no categories)
            for i, (category, name, description, score, positions) in enumerate(
                results
            ):
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
                                pos = viewer.mapToScene(
                                    viewer.mapFromGlobal(viewer.cursor().pos())
                                )

                            node = graph.create_node(
                                f"{cls.__identifier__}.{cls.__name__}",
                                name=cls.NODE_NAME,
                                pos=[pos.x() - 100, pos.y() - 30],
                            )
                            # Skip CasareRPA node for composite nodes (they create multiple nodes)
                            if not getattr(cls, "COMPOSITE_NODE", False):
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
                    action.setData({"node_class": node_class, "name": name})

                    # Mark first match visually
                    if i == 0:
                        font = action.font()
                        font.setBold(True)
                        action.setFont(font)
                        qmenu._first_match = node_class

        # Connect search directly for instant results (SearchIndex makes it fast enough)
        search_input.textChanged.connect(on_search_changed)

        # Focus search when menu is shown and capture initial mouse position if not already set
        def on_menu_shown():
            # Only capture position if not already set by event filter (right-click or Tab)
            if qmenu._initial_scene_pos is None:
                viewer = graph.viewer()
                qmenu._initial_scene_pos = viewer.mapToScene(
                    viewer.mapFromGlobal(viewer.cursor().pos())
                )
            search_input.setFocus()
            search_input.clear()

        qmenu.aboutToShow.connect(on_menu_shown)

        # Note: Don't reset position on aboutToHide because it fires BEFORE
        # the action's triggered signal, which would cause the position to be None
        # when create_node() is called. The position will be overwritten on each
        # new right-click anyway.

        logger.debug(
            f"Registered {len(ALL_VISUAL_NODE_CLASSES)} node types in context menu"
        )

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
        Get all nodes in a specific category (exact match only).

        Args:
            category: Category path (e.g., "google/gmail")

        Returns:
            List of node classes in the exact category
        """
        return self._categories.get(category, [])

    def get_all_nodes_in_category(self, category: str) -> List[Type]:
        """
        Get all nodes in a category including all subcategories.

        Args:
            category: Category path (e.g., "google" returns nodes from
                      google, google/gmail, google/sheets, etc.)

        Returns:
            List of node classes in the category and all subcategories
        """
        result = []

        # Get direct nodes
        if category in self._categories:
            result.extend(self._categories[category])

        # Get nodes from subcategories
        prefix = category + "/"
        for cat_path, nodes in self._categories.items():
            if cat_path.startswith(prefix):
                result.extend(nodes)

        return result

    def get_subcategories(self, parent: str) -> List[str]:
        """
        Get immediate subcategories of a parent category.

        Args:
            parent: Parent category path (e.g., "google")

        Returns:
            List of immediate subcategory names (e.g., ["gmail", "sheets", "docs"])
        """
        subcategories = set()
        prefix = parent + "/" if parent else ""

        for cat_path in self._categories.keys():
            if parent:
                if cat_path.startswith(prefix):
                    # Extract immediate child name
                    remainder = cat_path[len(prefix) :]
                    immediate_child = remainder.split("/")[0]
                    if immediate_child:
                        subcategories.add(immediate_child)
            else:
                # Get root categories
                root = cat_path.split("/")[0]
                subcategories.add(root)

        return sorted(subcategories)

    def get_root_categories(self) -> List[str]:
        """
        Get all root (top-level) categories.

        Returns:
            List of root category names
        """
        roots = set()
        for cat_path in self._categories.keys():
            root = cat_path.split("/")[0]
            roots.add(root)
        return sorted(roots)

    def get_categories(self) -> List[str]:
        """
        Get all registered categories.

        Returns:
            List of category names (all levels)
        """
        return list(self._categories.keys())

    def get_all_nodes(self) -> List[Type]:
        """
        Get all registered node classes.

        Returns:
            List of all node classes
        """
        return list(self._registered_nodes.values())

    def register_essential_nodes(self, graph: NodeGraph) -> None:
        """
        Register only essential nodes for fast startup.

        PERFORMANCE: Only loads ~8 essential nodes instead of 300+.
        Other nodes are registered lazily when complete_node_registration() is called.

        Args:
            graph: NodeGraph instance to register nodes with
        """
        from casare_rpa.presentation.canvas.visual_nodes import _lazy_import

        registered_count = 0
        for name in ESSENTIAL_NODE_NAMES:
            try:
                node_class = _lazy_import(name)
                self.register_node(node_class, graph)
                registered_count += 1
            except Exception as e:
                logger.warning(f"Failed to load essential node {name}: {e}")

        logger.debug(f"Registered {registered_count} essential nodes for fast startup")

    def register_remaining_nodes(self, graph: NodeGraph) -> None:
        """
        Register all remaining nodes (called after startup).

        PERFORMANCE: Called via QTimer.singleShot after window is shown.
        Also rebuilds the context menu with all nodes.

        Args:
            graph: NodeGraph instance to register nodes with
        """
        from casare_rpa.presentation.canvas.visual_nodes import ALL_VISUAL_NODE_CLASSES

        # Get already registered names to avoid duplicates
        already_registered = set(self._registered_nodes.keys())
        new_count = 0

        for node_class in ALL_VISUAL_NODE_CLASSES:
            if node_class.NODE_NAME not in already_registered:
                self.register_node(node_class, graph)
                new_count += 1

        logger.debug(
            f"Registered {new_count} additional nodes "
            f"(total: {len(self._registered_nodes)})"
        )

        # Rebuild the context menu with all nodes
        self._rebuild_context_menu(graph)

    def _rebuild_context_menu(self, graph: NodeGraph) -> None:
        """
        Rebuild the context menu with all registered nodes.

        This is called after deferred node registration to ensure
        the right-click menu shows all available nodes.

        Args:
            graph: NodeGraph instance
        """
        # Get the graph's context menu
        graph_menu = graph.get_context_menu("graph")
        qmenu = graph_menu.qmenu

        # Store essential menu attributes before clearing
        initial_scene_pos = getattr(qmenu, "_initial_scene_pos", None)
        last_created_node_id = getattr(qmenu, "_last_created_node_id", None)

        # Clear all existing menu items
        qmenu.clear()

        # Re-add search functionality and all nodes
        from PySide6.QtWidgets import QWidgetAction, QLineEdit
        from PySide6.QtCore import Qt

        # Restore stored attributes
        qmenu._last_created_node_id = last_created_node_id
        qmenu._initial_scene_pos = initial_scene_pos

        # Create search input widget with Enter key handler
        class SearchLineEdit(QLineEdit):
            def _find_node_by_id(self, node_id):
                """Find a node in the graph by its ID."""
                for n in graph.all_nodes():
                    n_id = n.id() if callable(n.id) else n.id
                    if n_id == node_id:
                        return n
                return None

            def keyPressEvent(self, event):
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    auto_connect = bool(event.modifiers() & Qt.ShiftModifier)
                    if hasattr(qmenu, "_first_match") and qmenu._first_match:
                        source_node = None
                        if auto_connect:
                            if qmenu._last_created_node_id:
                                source_node = self._find_node_by_id(
                                    qmenu._last_created_node_id
                                )
                            if not source_node:
                                selected_nodes = graph.selected_nodes()
                                if selected_nodes:
                                    source_node = selected_nodes[-1]

                        if auto_connect and source_node:
                            source_pos = source_node.pos()
                            node_width = 220
                            spacing = 80
                            pos_x = source_pos[0] + node_width + spacing
                            pos_y = source_pos[1]
                        else:
                            pos = qmenu._initial_scene_pos
                            if pos is None:
                                viewer = graph.viewer()
                                pos = viewer.mapToScene(
                                    viewer.mapFromGlobal(viewer.cursor().pos())
                                )
                            pos_x = pos.x() - 100
                            pos_y = pos.y() - 30

                        node = graph.create_node(
                            f"{qmenu._first_match.__identifier__}.{qmenu._first_match.__name__}",
                            name=qmenu._first_match.NODE_NAME,
                            pos=[pos_x, pos_y],
                        )
                        if not getattr(qmenu._first_match, "COMPOSITE_NODE", False):
                            factory = get_node_factory()
                            casare_node = factory.create_casare_node(node)
                            if casare_node:
                                node.set_casare_node(casare_node)

                        if auto_connect and source_node:
                            self._auto_connect_nodes(graph, source_node, node)

                        node_id = node.id() if callable(node.id) else node.id
                        qmenu._last_created_node_id = node_id

                        graph.clear_selection()
                        node.set_selected(True)
                        qmenu.close()
                    event.accept()
                else:
                    super().keyPressEvent(event)

            def _auto_connect_nodes(self, graph, source_node, target_node):
                """Auto-connect exec output of source to exec input of target."""
                try:
                    source_output = None
                    output_ports = source_node.output_ports()
                    for port in output_ports:
                        port_name = port.name().lower()
                        if "exec" in port_name or port_name in (
                            "exec_out",
                            "output",
                            "out",
                        ):
                            source_output = port
                            break
                    if not source_output and output_ports:
                        source_output = output_ports[0]

                    target_input = None
                    input_ports = target_node.input_ports()
                    for port in input_ports:
                        port_name = port.name().lower()
                        if "exec" in port_name or port_name in (
                            "exec_in",
                            "input",
                            "in",
                        ):
                            target_input = port
                            break
                    if not target_input and input_ports:
                        target_input = input_ports[0]

                    if source_output and target_input:
                        source_output.connect_to(target_input)
                        logger.info(
                            f"Auto-connected {source_node.name()} -> {target_node.name()}"
                        )
                except Exception as e:
                    logger.warning(f"Auto-connect failed: {e}")

        search_input = SearchLineEdit()
        search_input.setPlaceholderText("Search... Enter=add, Shift+Enter=add+connect")
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

        search_action = QWidgetAction(qmenu)
        search_action.setDefaultWidget(search_input)
        qmenu.addAction(search_action)
        qmenu.addSeparator()

        # Initialize menu data structures
        qmenu._node_items = []
        qmenu._all_actions = []
        qmenu._category_menus = {}
        qmenu._first_match = None
        qmenu._search_input = search_input
        qmenu._graph = graph
        qmenu._category_data = {}

        # Import category utilities
        try:
            from casare_rpa.presentation.canvas.graph.category_utils import (
                get_display_name,
                get_category_sort_key,
            )

            use_hierarchy = True
        except ImportError:
            use_hierarchy = False

        def get_or_create_submenu(parent_menu, category_path: str):
            """Get or create nested submenu for category path."""
            if category_path in qmenu._category_menus:
                return qmenu._category_menus[category_path]

            parts = category_path.split("/")
            if len(parts) == 1:
                if use_hierarchy:
                    label = get_display_name(category_path)
                else:
                    label = category_path.replace("_", " ").title()
                menu = parent_menu.addMenu(label)
                qmenu._category_menus[category_path] = menu
                return menu
            else:
                parent_path = "/".join(parts[:-1])
                parent_submenu = get_or_create_submenu(parent_menu, parent_path)
                if use_hierarchy:
                    label = get_display_name(category_path)
                else:
                    label = parts[-1].replace("_", " ").title()
                menu = parent_submenu.addMenu(label)
                qmenu._category_menus[category_path] = menu
                return menu

        # Sort categories
        if use_hierarchy:
            sorted_categories = sorted(
                self._categories.items(), key=lambda x: get_category_sort_key(x[0])
            )
        else:
            sorted_categories = sorted(
                self._categories.items(), key=lambda x: x[0].lower()
            )

        # Build menu structure
        for category, nodes in sorted_categories:
            if use_hierarchy:
                category_label = get_display_name(category)
            else:
                category_label = category.replace("_", " ").title()

            category_menu = get_or_create_submenu(qmenu, category)

            for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                if getattr(node_class, "INTERNAL_NODE", False):
                    continue

                description = ""
                if node_class.__doc__:
                    description = node_class.__doc__.strip().split("\n")[0]

                qmenu._node_items.append(
                    (category_label, node_class.NODE_NAME, description)
                )

                def make_creator(cls):
                    def create_node():
                        pos = qmenu._initial_scene_pos
                        if pos is None:
                            viewer = graph.viewer()
                            pos = viewer.mapToScene(
                                viewer.mapFromGlobal(viewer.cursor().pos())
                            )
                        node = graph.create_node(
                            f"{cls.__identifier__}.{cls.__name__}",
                            name=cls.NODE_NAME,
                            pos=[pos.x() - 100, pos.y() - 30],
                        )
                        if not getattr(cls, "COMPOSITE_NODE", False):
                            factory = get_node_factory()
                            casare_node = factory.create_casare_node(node)
                            if casare_node:
                                node.set_casare_node(casare_node)
                        return node

                    return create_node

                action = category_menu.addAction(node_class.NODE_NAME)
                action.triggered.connect(make_creator(node_class))
                action.setData(
                    {"category": category_label, "name": node_class.NODE_NAME}
                )
                qmenu._all_actions.append(action)

                # Build category data for search
                qmenu._category_data[node_class.NODE_NAME] = (
                    category_label,
                    node_class,
                )

        # Build search index
        from casare_rpa.utils.fuzzy_search import SearchIndex

        qmenu._search_index = SearchIndex(qmenu._node_items)

        def on_search_changed(text):
            """Handle search text changes."""
            actions_to_remove = []
            for action in qmenu.actions():
                if action != search_action and not action.isSeparator():
                    actions_to_remove.append(action)
            for action in actions_to_remove:
                qmenu.removeAction(action)

            if not text.strip():
                qmenu._category_menus.clear()
                if use_hierarchy:
                    sorted_cats = sorted(
                        self._categories.items(),
                        key=lambda x: get_category_sort_key(x[0]),
                    )
                else:
                    sorted_cats = sorted(
                        self._categories.items(), key=lambda x: x[0].lower()
                    )

                for cat, cat_nodes in sorted_cats:
                    cat_menu = get_or_create_submenu(qmenu, cat)
                    for nc in sorted(cat_nodes, key=lambda x: x.NODE_NAME):
                        if getattr(nc, "INTERNAL_NODE", False):
                            continue

                        def make_creator(cls):
                            def create_node():
                                pos = qmenu._initial_scene_pos
                                if pos is None:
                                    viewer = graph.viewer()
                                    pos = viewer.mapToScene(
                                        viewer.mapFromGlobal(viewer.cursor().pos())
                                    )
                                node = graph.create_node(
                                    f"{cls.__identifier__}.{cls.__name__}",
                                    name=cls.NODE_NAME,
                                    pos=[pos.x() - 100, pos.y() - 30],
                                )
                                if not getattr(cls, "COMPOSITE_NODE", False):
                                    factory = get_node_factory()
                                    casare_node = factory.create_casare_node(node)
                                    if casare_node:
                                        node.set_casare_node(casare_node)
                                return node

                            return create_node

                        act = cat_menu.addAction(nc.NODE_NAME)
                        act.triggered.connect(make_creator(nc))

                qmenu._first_match = None
                return

            results = qmenu._search_index.search(text)
            if not results:
                no_results_action = qmenu.addAction("No matching nodes found")
                no_results_action.setEnabled(False)
                qmenu._first_match = None
                return

            for i, (cat, name, desc, score, positions) in enumerate(results):
                if name in qmenu._category_data:
                    _, node_class = qmenu._category_data[name]

                    def make_creator(cls):
                        def create_node():
                            pos = qmenu._initial_scene_pos
                            if pos is None:
                                viewer = graph.viewer()
                                pos = viewer.mapToScene(
                                    viewer.mapFromGlobal(viewer.cursor().pos())
                                )
                            node = graph.create_node(
                                f"{cls.__identifier__}.{cls.__name__}",
                                name=cls.NODE_NAME,
                                pos=[pos.x() - 100, pos.y() - 30],
                            )
                            if not getattr(cls, "COMPOSITE_NODE", False):
                                factory = get_node_factory()
                                casare_node = factory.create_casare_node(node)
                                if casare_node:
                                    node.set_casare_node(casare_node)
                            qmenu.close()
                            return node

                        return create_node

                    action_text = f"{name} ({cat})"
                    act = qmenu.addAction(action_text)
                    act.triggered.connect(make_creator(node_class))
                    act.setData({"node_class": node_class, "name": name})

                    if i == 0:
                        font = act.font()
                        font.setBold(True)
                        act.setFont(font)
                        qmenu._first_match = node_class

        search_input.textChanged.connect(on_search_changed)

        def on_menu_shown():
            if qmenu._initial_scene_pos is None:
                viewer = graph.viewer()
                qmenu._initial_scene_pos = viewer.mapToScene(
                    viewer.mapFromGlobal(viewer.cursor().pos())
                )
            search_input.setFocus()
            search_input.clear()

        qmenu.aboutToShow.connect(on_menu_shown)

        logger.debug(
            f"Rebuilt context menu with {len(self._registered_nodes)} node types"
        )


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
        self, graph: NodeGraph, node_class: Type, pos: Optional[Tuple[int, int]] = None
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
            f"{node_class.__identifier__}.{node_class.NODE_NAME}", pos=pos
        )

        # Setup ports
        visual_node.setup_ports()

        logger.debug(f"Created visual node: {node_class.NODE_NAME}")

        return visual_node

    def create_casare_node(self, visual_node: Any, **kwargs) -> Optional[object]:
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

        # Generate unique node ID using UUID
        from casare_rpa.utils.id_generator import generate_node_id

        node_id = generate_node_id(node_class.__name__)

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
        **kwargs,
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


def clear_node_type_caches(clear_disk_cache: bool = False) -> None:
    """
    Clear all LRU caches for node type lookups.

    Use this when the node registry is modified or during testing.

    Args:
        clear_disk_cache: If True, also delete the disk cache file
    """
    get_visual_class_for_type.cache_clear()
    get_identifier_for_type.cache_clear()
    get_casare_class_for_type.cache_clear()

    if clear_disk_cache:
        try:
            if _MAPPING_CACHE_FILE.exists():
                _MAPPING_CACHE_FILE.unlink()
                logger.debug("Disk cache file deleted")
        except Exception as e:
            logger.warning(f"Failed to delete disk cache: {e}")

    logger.debug("Node type lookup caches cleared")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics for all node type lookup caches.

    Returns:
        Dictionary with cache info for each cached function
    """
    return {
        "get_visual_class_for_type": get_visual_class_for_type.cache_info()._asdict(),
        "get_identifier_for_type": get_identifier_for_type.cache_info()._asdict(),
        "get_casare_class_for_type": get_casare_class_for_type.cache_info()._asdict(),
    }
