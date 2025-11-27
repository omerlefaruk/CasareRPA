"""
CasareRPA - Snippet Creator
Converts selected nodes into reusable snippet definitions.
"""

from typing import List, Set, Dict, Tuple, Optional
from datetime import datetime
from loguru import logger

from ...core.base_node import BaseNode
from ...core.workflow_schema import NodeConnection
from ...core.snippet_definition import SnippetDefinition, ParameterMapping, VariableScopeConfig
from ...core.types import NodeId, DataType
from ...core.snippet_library import get_snippet_library
from ...utils.id_generator import generate_node_id


class SnippetCreator:
    """
    Creates snippet definitions from selected nodes.

    Handles:
    - Boundary node detection (entry/exit points)
    - Connection analysis
    - Position normalization
    - Parameter extraction (optional)
    """

    def __init__(self):
        """Initialize snippet creator."""
        pass

    def create_from_selection(
        self,
        selected_visual_nodes: List,
        all_connections: List[NodeConnection],
        snippet_name: str,
        description: str = "",
        category: str = "custom",
        author: str = "",
        parameters: Optional[List[ParameterMapping]] = None,
        variable_scope: Optional[VariableScopeConfig] = None,
    ) -> SnippetDefinition:
        """
        Create snippet definition from selected visual nodes.

        Args:
            selected_visual_nodes: List of selected NodeGraphQt visual nodes
            all_connections: List of all connections in the graph
            snippet_name: Name for the snippet
            description: Optional description
            category: Category for organization
            author: Author name
            parameters: Optional parameter mappings
            variable_scope: Optional variable scope configuration

        Returns:
            SnippetDefinition instance

        Raises:
            ValueError: If selection is invalid
        """
        if not selected_visual_nodes:
            raise ValueError("No nodes selected")

        logger.info(f"Creating snippet '{snippet_name}' from {len(selected_visual_nodes)} nodes")

        # Get node IDs and casare nodes
        selected_node_ids = set()
        casare_nodes = {}
        visual_node_map = {}

        for visual_node in selected_visual_nodes:
            # Get node_id property
            node_id = visual_node.get_property("node_id")
            if node_id:
                selected_node_ids.add(node_id)
                visual_node_map[node_id] = visual_node

                # Get casare node if available
                if hasattr(visual_node, "_casare_node") and visual_node._casare_node:
                    casare_nodes[node_id] = visual_node._casare_node

        # Extract internal connections
        internal_connections = self._extract_internal_connections(
            selected_node_ids, all_connections
        )

        # Find entry and exit nodes
        entry_node_ids, exit_node_ids = self._find_boundary_nodes(
            selected_node_ids, all_connections
        )

        # Extract node positions (relative to selection bounding box)
        node_positions = self._calculate_relative_positions(visual_node_map)

        # Serialize nodes
        serialized_nodes = {}
        for node_id, casare_node in casare_nodes.items():
            serialized_nodes[node_id] = casare_node.serialize()

        # Create snippet definition
        snippet_id = generate_node_id("Snippet")

        snippet = SnippetDefinition(
            snippet_id=snippet_id,
            name=snippet_name,
            description=description,
            category=category,
            author=author,
        )

        snippet.nodes = serialized_nodes
        snippet.connections = internal_connections
        snippet.node_positions = node_positions
        snippet.entry_node_ids = entry_node_ids
        snippet.exit_node_ids = exit_node_ids

        # Set parameters if provided
        if parameters:
            snippet.parameters = parameters
        else:
            snippet.parameters = []

        # Set variable scope if provided
        if variable_scope:
            snippet.variable_scope = variable_scope
        else:
            # Default: inherit parent scope, don't export
            snippet.variable_scope = VariableScopeConfig(
                inherit_parent_scope=True,
                export_local_vars=False
            )

        logger.info(
            f"Created snippet '{snippet_name}': {len(serialized_nodes)} nodes, "
            f"{len(internal_connections)} connections, "
            f"{len(entry_node_ids)} entry points, {len(exit_node_ids)} exit points"
        )

        return snippet

    def _extract_internal_connections(
        self,
        selected_node_ids: Set[NodeId],
        all_connections: List[NodeConnection],
    ) -> List[NodeConnection]:
        """
        Extract connections that are internal to the selection.

        Args:
            selected_node_ids: Set of selected node IDs
            all_connections: All connections in the graph

        Returns:
            List of internal connections
        """
        internal = []

        for conn in all_connections:
            if conn.source_node in selected_node_ids and conn.target_node in selected_node_ids:
                internal.append(conn)

        logger.debug(f"Found {len(internal)} internal connections")
        return internal

    def _find_boundary_nodes(
        self,
        selected_node_ids: Set[NodeId],
        all_connections: List[NodeConnection],
    ) -> Tuple[List[NodeId], List[NodeId]]:
        """
        Find entry and exit nodes for the snippet.

        Entry nodes: Have incoming connections from outside selection
        Exit nodes: Have outgoing connections to outside selection

        Args:
            selected_node_ids: Set of selected node IDs
            all_connections: All connections in the graph

        Returns:
            Tuple of (entry_node_ids, exit_node_ids)
        """
        entry_nodes = set()
        exit_nodes = set()

        for conn in all_connections:
            # Entry: connection from outside → inside
            if conn.source_node not in selected_node_ids and conn.target_node in selected_node_ids:
                # Only consider execution connections for entry points
                if conn.target_port in ["exec_in", "loop_body", "then", "else"]:
                    entry_nodes.add(conn.target_node)

            # Exit: connection from inside → outside
            if conn.source_node in selected_node_ids and conn.target_node not in selected_node_ids:
                # Only consider execution connections for exit points
                if conn.source_port in ["exec_out", "completed", "loop_body"]:
                    exit_nodes.add(conn.source_node)

        # If no entry nodes found, use all nodes without incoming exec connections
        if not entry_nodes:
            # Find nodes with no incoming exec connections within selection
            has_incoming = set()
            for conn in all_connections:
                if (conn.source_node in selected_node_ids and
                    conn.target_node in selected_node_ids and
                    conn.target_port in ["exec_in", "loop_body", "then", "else"]):
                    has_incoming.add(conn.target_node)

            entry_nodes = selected_node_ids - has_incoming

        # If no exit nodes found, use all nodes without outgoing exec connections
        if not exit_nodes:
            # Find nodes with no outgoing exec connections within selection
            has_outgoing = set()
            for conn in all_connections:
                if (conn.source_node in selected_node_ids and
                    conn.target_node in selected_node_ids and
                    conn.source_port in ["exec_out", "completed", "loop_body"]):
                    has_outgoing.add(conn.source_node)

            exit_nodes = selected_node_ids - has_outgoing

        logger.info(f"Boundary detection: {len(entry_nodes)} entry, {len(exit_nodes)} exit nodes")

        return list(entry_nodes), list(exit_nodes)

    def _calculate_relative_positions(
        self,
        visual_node_map: Dict[NodeId, any],
    ) -> Dict[NodeId, Tuple[float, float]]:
        """
        Calculate node positions relative to selection bounding box.

        Normalizes positions so snippet can be placed anywhere.

        Args:
            visual_node_map: Mapping of node_id to visual node

        Returns:
            Dictionary mapping node_id to (x, y) relative positions
        """
        if not visual_node_map:
            return {}

        # Find bounding box
        min_x = float('inf')
        min_y = float('inf')

        for visual_node in visual_node_map.values():
            x, y = visual_node.pos()
            min_x = min(min_x, x)
            min_y = min(min_y, y)

        # Calculate relative positions
        positions = {}
        for node_id, visual_node in visual_node_map.items():
            x, y = visual_node.pos()
            rel_x = x - min_x
            rel_y = y - min_y
            positions[node_id] = (rel_x, rel_y)

        logger.debug(f"Calculated positions with offset ({min_x}, {min_y})")

        return positions

    def save_snippet(self, snippet: SnippetDefinition) -> str:
        """
        Save snippet to library.

        Args:
            snippet: SnippetDefinition to save

        Returns:
            Path to saved file
        """
        library = get_snippet_library()
        file_path = library.save_snippet(snippet)

        logger.info(f"Snippet '{snippet.name}' saved to {file_path}")

        return str(file_path)

    def auto_detect_parameters(
        self,
        serialized_nodes: Dict[NodeId, dict],
    ) -> List[ParameterMapping]:
        """
        Automatically detect potential parameters from node configurations.

        Looks for commonly parameterized config values like URLs, file paths, etc.

        Args:
            serialized_nodes: Dictionary of serialized node data

        Returns:
            List of suggested ParameterMapping objects
        """
        suggested_params = []

        # Common config keys that should be parameterized
        parameterizable_keys = {
            "url": (DataType.STRING, "URL"),
            "file_path": (DataType.STRING, "File Path"),
            "timeout": (DataType.INTEGER, "Timeout"),
            "text": (DataType.STRING, "Text"),
            "selector": (DataType.STRING, "Selector"),
            "xpath": (DataType.STRING, "XPath"),
        }

        for node_id, node_data in serialized_nodes.items():
            config = node_data.get("config", {})
            node_type = node_data.get("node_type", "Unknown")

            for config_key, config_value in config.items():
                if config_key in parameterizable_keys and config_value:
                    data_type, label = parameterizable_keys[config_key]

                    # Create parameter mapping
                    param = ParameterMapping(
                        snippet_param_name=f"{node_type.lower()}_{config_key}",
                        target_node_id=node_id,
                        target_config_key=config_key,
                        param_type=data_type,
                        default_value=config_value,
                        description=f"{label} for {node_type}",
                        required=False,
                    )

                    suggested_params.append(param)

        logger.debug(f"Auto-detected {len(suggested_params)} potential parameters")

        return suggested_params
