"""
CasareRPA - Snippet Navigation Manager
Manages hierarchical navigation into snippet nodes with breadcrumb tracking and state persistence.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from loguru import logger

from ..core.snippet_definition import SnippetDefinition
from ..core.types import NodeId


@dataclass
class NavigationLevel:
    """
    Represents one level in the navigation hierarchy.

    Attributes:
        name: Display name (e.g., "Workflow", "Login Automation")
        context_type: "workflow" or "snippet"
        snippet_node_id: ID of the snippet node if this is a snippet level
        snippet_definition: Full snippet data if this is a snippet
        graph_state: Saved graph state (nodes, connections, viewport)
    """
    name: str
    context_type: str  # "workflow" or "snippet"
    snippet_node_id: Optional[NodeId] = None
    snippet_definition: Optional[SnippetDefinition] = None
    graph_state: Dict[str, Any] = field(default_factory=dict)

    def is_workflow(self) -> bool:
        """Check if this level represents the root workflow."""
        return self.context_type == "workflow"

    def is_snippet(self) -> bool:
        """Check if this level represents a snippet."""
        return self.context_type == "snippet"


class SnippetNavigationManager(QObject):
    """
    Manages navigation stack and graph state for hierarchical snippet editing.

    Features:
    - Push/pop navigation levels
    - Save/restore graph state
    - Emit signals for UI updates (breadcrumb refresh)
    - Track current editing context

    Signals:
        navigation_changed: Emitted when navigation stack changes
        snippet_entered: Emitted when entering a snippet (snippet_name)
        snippet_exited: Emitted when exiting a snippet (snippet_name)
    """

    # Signals
    navigation_changed = Signal()  # Stack changed, update breadcrumb
    snippet_entered = Signal(str)  # Entered snippet with name
    snippet_exited = Signal(str)  # Exited snippet with name

    def __init__(self, graph_widget) -> None:
        """
        Initialize navigation manager.

        Args:
            graph_widget: NodeGraphWidget instance to manage
        """
        super().__init__()
        self.graph_widget = graph_widget
        self.graph = graph_widget.graph

        # Navigation stack (root workflow is always level 0)
        self._stack: List[NavigationLevel] = [
            NavigationLevel(
                name="Workflow",
                context_type="workflow"
            )
        ]

        logger.info("SnippetNavigationManager initialized")

    def get_current_level(self) -> NavigationLevel:
        """Get the current navigation level."""
        return self._stack[-1]

    def get_depth(self) -> int:
        """Get current navigation depth (0 = root workflow)."""
        return len(self._stack) - 1

    def is_at_root(self) -> bool:
        """Check if we're at the root workflow level."""
        return len(self._stack) == 1

    def get_breadcrumb_path(self) -> List[Tuple[str, str]]:
        """
        Get breadcrumb path as list of (name, context_type) tuples.

        Returns:
            List of (name, context_type) for each level
            Example: [("Workflow", "workflow"), ("Login", "snippet"), ("Form Fill", "snippet")]
        """
        return [(level.name, level.context_type) for level in self._stack]

    def enter_snippet(self, visual_snippet_node) -> bool:
        """
        Navigate into a snippet node.

        Args:
            visual_snippet_node: VisualSnippetNode instance to enter

        Returns:
            True if navigation succeeded, False otherwise
        """
        from .visual_nodes import VisualSnippetNode

        # Validate input
        if not isinstance(visual_snippet_node, VisualSnippetNode):
            logger.error(f"Invalid node type: {type(visual_snippet_node)}")
            return False

        # Get casare node and snippet definition
        casare_node = visual_snippet_node.get_casare_node()
        if not casare_node:
            logger.error("Snippet node has no casare node")
            return False

        snippet_def = casare_node.snippet_definition
        if not snippet_def:
            logger.error("Snippet node has no snippet definition loaded")
            return False

        # Save current graph state
        logger.info(f"Entering snippet '{snippet_def.name}' (depth: {self.get_depth()} -> {self.get_depth() + 1})")

        current_level = self.get_current_level()
        current_level.graph_state = self._save_graph_state()

        # Create new navigation level
        new_level = NavigationLevel(
            name=snippet_def.name,
            context_type="snippet",
            snippet_node_id=visual_snippet_node.id,
            snippet_definition=snippet_def,
            graph_state={}  # Will be filled when we exit or navigate further
        )

        # Push onto stack
        self._stack.append(new_level)

        # Load snippet nodes into graph
        if not self._load_snippet_into_graph(snippet_def):
            # Failed to load, pop back
            self._stack.pop()
            logger.error("Failed to load snippet into graph")
            return False

        # Emit signals
        self.navigation_changed.emit()
        self.snippet_entered.emit(snippet_def.name)

        logger.info(f"Successfully entered snippet '{snippet_def.name}'")
        return True

    def navigate_back_to_level(self, target_level_index: int) -> bool:
        """
        Navigate back to a specific level in the stack.

        Args:
            target_level_index: Index of level to return to (0 = root)

        Returns:
            True if navigation succeeded
        """
        if target_level_index < 0 or target_level_index >= len(self._stack):
            logger.error(f"Invalid level index: {target_level_index}")
            return False

        if target_level_index == len(self._stack) - 1:
            logger.debug("Already at target level")
            return True

        # Save current graph state before navigating
        current_level = self.get_current_level()
        if current_level.is_snippet():
            current_level.graph_state = self._save_graph_state()
            # TODO: Prompt user to save changes if modified

        # Pop levels until we reach target
        while len(self._stack) > target_level_index + 1:
            popped = self._stack.pop()
            logger.debug(f"Popped level: {popped.name}")
            if popped.is_snippet():
                self.snippet_exited.emit(popped.name)

        # Restore graph state for target level
        target_level = self._stack[target_level_index]
        self._restore_graph_state(target_level.graph_state)

        # Emit signal
        self.navigation_changed.emit()

        logger.info(f"Navigated back to level {target_level_index}: '{target_level.name}'")
        return True

    def navigate_back(self) -> bool:
        """
        Navigate back one level (shortcut for navigate_back_to_level(depth - 1)).

        Returns:
            True if navigation succeeded
        """
        if self.is_at_root():
            logger.warning("Already at root, cannot navigate back")
            return False

        return self.navigate_back_to_level(self.get_depth() - 1)

    def _save_graph_state(self) -> Dict[str, Any]:
        """
        Save current graph state (nodes, connections, viewport).

        Returns:
            Dictionary with complete graph state
        """
        logger.debug("Saving graph state...")

        state = {
            "nodes": [],
            "connections": [],
            "viewport": {}
        }

        try:
            # Save nodes
            for node in self.graph.all_nodes():
                node_data = {
                    "id": node.id,
                    "type": node.type_,
                    "name": node.name(),
                    "pos": [node.x_pos(), node.y_pos()],
                    "properties": {}
                }

                # Save properties
                for prop_name, prop_widget in node.widgets().items():
                    try:
                        node_data["properties"][prop_name] = node.get_property(prop_name)
                    except:
                        pass  # Skip properties that can't be serialized

                state["nodes"].append(node_data)

            # Save connections
            for node in self.graph.all_nodes():
                for output_port in node.output_ports():
                    for connected_port in output_port.connected_ports():
                        state["connections"].append({
                            "source_node": node.id,
                            "source_port": output_port.name(),
                            "target_node": connected_port.node().id,
                            "target_port": connected_port.name()
                        })

            # Save viewport state
            viewer = self.graph.viewer()
            state["viewport"] = {
                "zoom": viewer.get_zoom(),
                "center_x": viewer.sceneRect().center().x(),
                "center_y": viewer.sceneRect().center().y()
            }

            logger.debug(f"Saved {len(state['nodes'])} nodes, {len(state['connections'])} connections")

        except Exception as e:
            logger.exception(f"Error saving graph state: {e}")

        return state

    def _restore_graph_state(self, state: Dict[str, Any]) -> None:
        """
        Restore graph from saved state.

        Args:
            state: Saved graph state dictionary
        """
        if not state:
            logger.warning("No state to restore")
            return

        logger.debug(f"Restoring graph state: {len(state.get('nodes', []))} nodes...")

        try:
            # Clear current graph
            self.graph.clear_session()

            # Recreate nodes
            node_map = {}  # old_id -> new_node

            for node_data in state.get("nodes", []):
                node = self.graph.create_node(
                    node_data["type"],
                    name=node_data.get("name"),
                    pos=node_data.get("pos", [0, 0])
                )

                if node:
                    node_map[node_data["id"]] = node

                    # Restore properties
                    for prop_name, prop_value in node_data.get("properties", {}).items():
                        try:
                            node.set_property(prop_name, prop_value)
                        except:
                            pass  # Skip if property doesn't exist

            # Recreate connections
            for conn_data in state.get("connections", []):
                source_node = node_map.get(conn_data["source_node"])
                target_node = node_map.get(conn_data["target_node"])

                if source_node and target_node:
                    try:
                        source_port = source_node.get_output(conn_data["source_port"])
                        target_port = target_node.get_input(conn_data["target_port"])

                        if source_port and target_port:
                            source_port.connect_to(target_port)
                    except Exception as e:
                        logger.warning(f"Failed to restore connection: {e}")

            # Restore viewport
            viewport_data = state.get("viewport", {})
            if viewport_data:
                viewer = self.graph.viewer()
                viewer.set_zoom(viewport_data.get("zoom", 1.0))
                # TODO: Center viewport on saved position

            logger.info("Graph state restored successfully")

        except Exception as e:
            logger.exception(f"Error restoring graph state: {e}")

    def _load_snippet_into_graph(self, snippet_def: SnippetDefinition) -> bool:
        """
        Load snippet's internal nodes into the graph.

        Args:
            snippet_def: Snippet definition to load

        Returns:
            True if loading succeeded
        """
        logger.info(f"Loading snippet '{snippet_def.name}' with {len(snippet_def.nodes)} nodes")

        try:
            # Clear current graph
            self.graph.clear_session()

            # Import node type mapping
            from ..utils.workflow_loader import NODE_TYPE_MAP

            # Create visual nodes from serialized data
            node_map = {}  # snippet node_id -> visual node

            for node_id, node_data in snippet_def.nodes.items():
                node_type = node_data.get("node_type")
                config = node_data.get("config", {})

                # Get visual node type (e.g., "casare_rpa.browser.VisualNavigateNode")
                # We need to map CasareRPA node type to visual node type
                visual_node_type = self._get_visual_node_type(node_type)

                if not visual_node_type:
                    logger.warning(f"Unknown node type: {node_type}, skipping")
                    continue

                # Get position
                pos = snippet_def.node_positions.get(node_id, (0, 0))

                # Create visual node
                visual_node = self.graph.create_node(
                    visual_node_type,
                    pos=[pos[0], pos[1]]
                )

                if visual_node:
                    node_map[node_id] = visual_node

                    # Set properties from config
                    for key, value in config.items():
                        try:
                            if visual_node.has_property(key):
                                visual_node.set_property(key, value)
                        except:
                            pass

            # Create connections
            for conn in snippet_def.connections:
                source_node = node_map.get(conn.source_node_id)
                target_node = node_map.get(conn.target_node_id)

                if source_node and target_node:
                    try:
                        source_port = source_node.get_output(conn.source_port)
                        target_port = target_node.get_input(conn.target_port)

                        if source_port and target_port:
                            source_port.connect_to(target_port)
                    except Exception as e:
                        logger.warning(f"Failed to create connection: {e}")

            logger.info(f"Loaded {len(node_map)} nodes into graph")
            return True

        except Exception as e:
            logger.exception(f"Error loading snippet into graph: {e}")
            return False

    def _get_visual_node_type(self, casare_node_type: str) -> Optional[str]:
        """
        Map CasareRPA node type to visual node type.

        Args:
            casare_node_type: CasareRPA node type (e.g., "NavigateNode")

        Returns:
            Visual node type string (e.g., "casare_rpa.browser.VisualNavigateNode")
        """
        # This mapping should ideally come from a registry
        # For now, we'll use a simple heuristic: Visual + NodeType

        # Check if it's already a visual node type
        if "Visual" in casare_node_type:
            return casare_node_type

        # Try to construct visual node type
        # TODO: This needs proper mapping from node_registry.py
        # For now, return None and let the caller handle missing types

        logger.warning(f"Need to implement visual node type mapping for: {casare_node_type}")
        return None


# Global singleton instance
_navigation_manager: Optional[SnippetNavigationManager] = None


def get_navigation_manager() -> Optional[SnippetNavigationManager]:
    """Get the global navigation manager instance."""
    return _navigation_manager


def set_navigation_manager(manager: SnippetNavigationManager) -> None:
    """Set the global navigation manager instance."""
    global _navigation_manager
    _navigation_manager = manager
    logger.debug("Global navigation manager set")
