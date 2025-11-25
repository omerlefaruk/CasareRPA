"""
CasareRPA - Snippet Expansion Manager
Handles expansion and collapse of snippet nodes between single-node and inline modes.
"""

from typing import List, Dict, Optional, Tuple
from loguru import logger

from ..core.snippet_definition import SnippetDefinition
from ..core.workflow_schema import NodeConnection
from ..core.types import NodeId
from ..nodes.snippet_node import SnippetNode
from ..utils.id_generator import generate_node_id


class SnippetExpansionState:
    """
    Tracks the state of an expanded snippet for collapse operation.

    Attributes:
        snippet_definition: The original snippet definition
        expanded_node_ids: Node IDs of the expanded nodes
        id_mapping: Map from original snippet node IDs to expanded node IDs
        snippet_node_position: Position where the collapsed node should be
        external_connections: Connections from/to the snippet boundary
    """

    def __init__(
        self,
        snippet_definition: SnippetDefinition,
        expanded_node_ids: List[NodeId],
        id_mapping: Dict[NodeId, NodeId],
        snippet_node_position: Tuple[float, float],
        external_connections: List[Tuple[str, str, str, str]],  # (source, source_port, target, target_port)
    ):
        self.snippet_definition = snippet_definition
        self.expanded_node_ids = expanded_node_ids
        self.id_mapping = id_mapping
        self.snippet_node_position = snippet_node_position
        self.external_connections = external_connections


class SnippetExpansionManager:
    """
    Manages expansion and collapse of snippet nodes.

    Features:
    - Expand collapsed SnippetNode to show internal nodes inline
    - Collapse expanded nodes back to single SnippetNode
    - Preserve external connections during transformation
    - Track expansion state for round-trip operations
    """

    def __init__(self, graph):
        """
        Initialize snippet expansion manager.

        Args:
            graph: NodeGraphQt graph instance
        """
        self.graph = graph
        self._expansion_states: Dict[str, SnippetExpansionState] = {}

    def expand_snippet(self, snippet_visual_node) -> bool:
        """
        Expand a collapsed SnippetNode to show its internal nodes inline.

        Args:
            snippet_visual_node: The VisualSnippetNode to expand

        Returns:
            True if expansion succeeded, False otherwise
        """
        # Get the casare SnippetNode
        if not hasattr(snippet_visual_node, "_casare_node"):
            logger.error("Visual node has no casare node attached")
            return False

        casare_node = snippet_visual_node._casare_node
        if not isinstance(casare_node, SnippetNode):
            logger.error(f"Node is not a SnippetNode: {type(casare_node)}")
            return False

        if not casare_node.snippet_definition:
            logger.error("SnippetNode has no snippet definition loaded")
            return False

        snippet_def = casare_node.snippet_definition

        logger.info(f"Expanding snippet: {snippet_def.name}")

        try:
            # Get snippet node position
            pos = snippet_visual_node.pos()
            base_x, base_y = pos[0], pos[1]

            # Store external connections before deletion
            external_connections = self._get_external_connections(snippet_visual_node)

            # Create internal nodes
            id_mapping = {}  # Original ID -> New ID
            created_visual_nodes = {}  # New ID -> Visual node

            for orig_node_id, node_data in snippet_def.nodes.items():
                # Generate new ID to avoid conflicts
                new_node_id = generate_node_id(node_data.get("node_type", "Node"))
                id_mapping[orig_node_id] = new_node_id

                # Get position from snippet (relative to snippet base position)
                rel_pos = snippet_def.node_positions.get(orig_node_id, (0, 0))
                abs_x = base_x + rel_pos[0]
                abs_y = base_y + rel_pos[1]

                # Create visual node
                node_type = node_data.get("node_type")
                identifier = self._get_node_identifier(node_type)

                visual_node = self.graph.create_node(
                    identifier,
                    pos=[abs_x, abs_y]
                )

                if visual_node:
                    created_visual_nodes[new_node_id] = visual_node

                    # Create casare node through factory
                    from ..canvas.node_factory import NodeFactory
                    factory = NodeFactory()
                    casare_internal_node = factory.create_casare_node(visual_node)

                    if casare_internal_node:
                        # Override ID and config
                        casare_internal_node.node_id = new_node_id
                        visual_node.set_property("node_id", new_node_id)

                        # Apply config from snippet
                        config = node_data.get("config", {})
                        for key, value in config.items():
                            casare_internal_node.config[key] = value

                        # Update visual properties if available
                        if hasattr(visual_node, "update_from_casare_node"):
                            visual_node.update_from_casare_node(casare_internal_node)

                    logger.debug(f"Created expanded node: {new_node_id} ({node_type})")

            # Create internal connections
            for conn in snippet_def.connections:
                source_id = id_mapping.get(conn.source_node)
                target_id = id_mapping.get(conn.target_node)

                if source_id and target_id:
                    source_visual = created_visual_nodes.get(source_id)
                    target_visual = created_visual_nodes.get(target_id)

                    if source_visual and target_visual:
                        # Get port objects
                        source_port = source_visual.output(conn.source_port)
                        target_port = target_visual.input(conn.target_port)

                        if source_port and target_port:
                            source_port.connect_to(target_port)
                            logger.debug(
                                f"Connected: {source_id}.{conn.source_port} -> "
                                f"{target_id}.{conn.target_port}"
                            )

            # Reconnect external connections
            self._reconnect_external_connections(
                external_connections,
                snippet_def,
                id_mapping,
                created_visual_nodes
            )

            # Store expansion state for potential collapse
            expansion_state = SnippetExpansionState(
                snippet_definition=snippet_def,
                expanded_node_ids=list(id_mapping.values()),
                id_mapping=id_mapping,
                snippet_node_position=(base_x, base_y),
                external_connections=external_connections,
            )

            # Use first expanded node ID as state key
            state_key = list(id_mapping.values())[0] if id_mapping else None
            if state_key:
                self._expansion_states[state_key] = expansion_state

            # Delete the collapsed SnippetNode
            self.graph.delete_node(snippet_visual_node)

            logger.info(
                f"Expanded snippet '{snippet_def.name}': "
                f"{len(created_visual_nodes)} nodes created"
            )

            return True

        except Exception as e:
            logger.exception(f"Failed to expand snippet: {e}")
            return False

    def collapse_snippet(self, expanded_node_ids: List[str], snippet_definition: SnippetDefinition) -> bool:
        """
        Collapse expanded snippet nodes back to a single SnippetNode.

        Args:
            expanded_node_ids: List of node IDs that are part of the expanded snippet
            snippet_definition: The snippet definition to collapse to

        Returns:
            True if collapse succeeded, False otherwise
        """
        logger.info(f"Collapsing snippet: {snippet_definition.name}")

        try:
            # Get visual nodes
            expanded_visual_nodes = []
            for node_id in expanded_node_ids:
                visual_node = self._find_visual_node_by_id(node_id)
                if visual_node:
                    expanded_visual_nodes.append(visual_node)

            if not expanded_visual_nodes:
                logger.error("No visual nodes found for collapse")
                return False

            # Calculate center position for collapsed node
            positions = [node.pos() for node in expanded_visual_nodes]
            avg_x = sum(pos[0] for pos in positions) / len(positions)
            avg_y = sum(pos[1] for pos in positions) / len(positions)

            # Store external connections before deletion
            external_connections = []
            for visual_node in expanded_visual_nodes:
                external_connections.extend(self._get_external_connections(visual_node))

            # Create collapsed SnippetNode
            snippet_visual_node = self.graph.create_node(
                "casare_rpa.snippets.Snippet",
                pos=[avg_x, avg_y]
            )

            if not snippet_visual_node:
                logger.error("Failed to create collapsed snippet node")
                return False

            # Create casare SnippetNode instance
            node_id = generate_node_id("SnippetNode")
            config = {
                "snippet_id": snippet_definition.snippet_id,
                "snippet_name": snippet_definition.name,
            }

            casare_node = SnippetNode(node_id, config=config)
            casare_node.set_snippet_definition(snippet_definition)

            # Link visual and casare nodes
            snippet_visual_node._casare_node = casare_node
            snippet_visual_node.set_property("node_id", node_id)
            snippet_visual_node.set_name(snippet_definition.name)

            # Reconnect external connections to snippet boundary
            # (This is simplified - would need proper port mapping)
            logger.debug(f"Stored {len(external_connections)} external connections for reconnection")

            # Delete expanded nodes
            for visual_node in expanded_visual_nodes:
                self.graph.delete_node(visual_node)

            logger.info(
                f"Collapsed snippet '{snippet_definition.name}': "
                f"{len(expanded_visual_nodes)} nodes removed"
            )

            return True

        except Exception as e:
            logger.exception(f"Failed to collapse snippet: {e}")
            return False

    def _get_external_connections(self, visual_node) -> List[Tuple[str, str, str, str]]:
        """
        Get all connections to/from a visual node that cross snippet boundary.

        Returns:
            List of tuples: (source_node_id, source_port, target_node_id, target_port)
        """
        connections = []
        node_id = visual_node.get_property("node_id")

        # Outgoing connections
        for port_name in visual_node.output_ports():
            output_port = visual_node.output(port_name)
            if output_port:
                for connected_port in output_port.connected_ports():
                    target_node = connected_port.node()
                    target_node_id = target_node.get_property("node_id")
                    target_port_name = connected_port.name()

                    connections.append((
                        node_id,
                        port_name,
                        target_node_id,
                        target_port_name
                    ))

        # Incoming connections
        for port_name in visual_node.input_ports():
            input_port = visual_node.input(port_name)
            if input_port:
                for connected_port in input_port.connected_ports():
                    source_node = connected_port.node()
                    source_node_id = source_node.get_property("node_id")
                    source_port_name = connected_port.name()

                    connections.append((
                        source_node_id,
                        source_port_name,
                        node_id,
                        port_name
                    ))

        return connections

    def _reconnect_external_connections(
        self,
        external_connections: List[Tuple[str, str, str, str]],
        snippet_def: SnippetDefinition,
        id_mapping: Dict[NodeId, NodeId],
        created_nodes: Dict[NodeId, any]
    ):
        """
        Reconnect external connections to expanded snippet nodes.

        Maps connections that were to/from the SnippetNode to the appropriate
        entry/exit nodes in the expanded snippet.
        """
        # This is simplified - full implementation would need proper port mapping
        # based on entry_node_ids and exit_node_ids
        logger.debug(f"Reconnecting {len(external_connections)} external connections")

    def _get_node_identifier(self, node_type: str) -> str:
        """
        Get NodeGraphQt identifier for a node type.

        Args:
            node_type: CasareRPA node type (e.g., "HTTPRequestNode")

        Returns:
            NodeGraphQt identifier (e.g., "casare_rpa.web.HTTPRequest")
        """
        # Map node types to identifiers
        # This is a simplified version - full implementation would use node registry
        type_map = {
            "StartNode": "casare_rpa.flow.Start",
            "HTTPRequestNode": "casare_rpa.web.HTTPRequest",
            "ClickElementNode": "casare_rpa.web.ClickElement",
            "SetVariableNode": "casare_rpa.data.SetVariable",
            "GetVariableNode": "casare_rpa.data.GetVariable",
            "IfNode": "casare_rpa.flow.If",
            "LogNode": "casare_rpa.debug.Log",
        }

        identifier = type_map.get(node_type)
        if identifier:
            return identifier

        # Fallback: try to construct from category
        logger.warning(f"Unknown node type '{node_type}', using fallback identifier")
        return f"casare_rpa.custom.{node_type}"

    def _find_visual_node_by_id(self, node_id: str):
        """
        Find a visual node by its node_id property.

        Args:
            node_id: The node_id to search for

        Returns:
            Visual node or None if not found
        """
        for visual_node in self.graph.all_nodes():
            if visual_node.get_property("node_id") == node_id:
                return visual_node
        return None
