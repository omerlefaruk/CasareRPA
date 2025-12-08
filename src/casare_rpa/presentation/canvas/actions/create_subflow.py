"""
Create Subflow from Selection Action.

Converts a selection of nodes into a reusable subflow:
1. Analyzes connections to detect inputs/outputs
2. Auto-generates unique name (Subflow 1, Subflow 2, etc.)
3. Creates Subflow entity with detected ports
4. Saves to workflows/subflows/{id}.json
5. Replaces selected nodes with SubflowVisualNode
6. Reconnects external connections
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


@dataclass
class ExternalConnection:
    """Represents a connection to/from a node outside the selection."""

    external_node_id: str
    external_port_name: str
    internal_node_id: str
    internal_port_name: str
    is_input: bool  # True if external -> internal (input to subflow)


@dataclass
class AnalyzedConnections:
    """Result of analyzing connections for selected nodes."""

    internal_connections: List[Dict[str, Any]]  # Connections between selected nodes
    external_inputs: List[
        ExternalConnection
    ]  # External -> internal (become subflow inputs)
    external_outputs: List[
        ExternalConnection
    ]  # Internal -> external (become subflow outputs)


class CreateSubflowAction(QObject):
    """
    Action to create a subflow from selected nodes.

    Usage:
        action = CreateSubflowAction(graph_widget)
        subflow_node = action.execute(selected_nodes)
    """

    def __init__(self, graph_widget, parent: Optional[QObject] = None) -> None:
        """
        Initialize the action.

        Args:
            graph_widget: The NodeGraphWidget instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph_widget = graph_widget
        self._graph: "NodeGraph" = graph_widget.graph

    def execute(self, selected_nodes: List) -> Optional[Any]:
        """
        Execute the create subflow action.

        Args:
            selected_nodes: List of selected visual nodes

        Returns:
            The created SubflowVisualNode or None if cancelled/failed
        """
        if not selected_nodes:
            logger.warning("Create Subflow: No nodes selected")
            return None

        if len(selected_nodes) < 2:
            QMessageBox.warning(
                None,
                "Create Subflow",
                "Please select at least 2 nodes to create a subflow.",
            )
            return None

        try:
            # Step 1: Analyze connections
            analysis = self._analyze_connections(selected_nodes)
            logger.info(
                f"Create Subflow: {len(analysis.internal_connections)} internal, "
                f"{len(analysis.external_inputs)} inputs, "
                f"{len(analysis.external_outputs)} outputs"
            )

            # Step 2: Auto-generate unique name (no dialog)
            name = self._generate_unique_name()

            # Step 3: Create subflow entity
            subflow = self._create_subflow(name, selected_nodes, analysis)
            if not subflow:
                return None

            # Step 4: Save to file
            subflow_path = self._get_subflow_path(subflow.id)
            subflow.save_to_file(subflow_path)
            logger.info(f"Created subflow '{name}' at {subflow_path}")

            # Step 5: Calculate center position of selection
            center_pos = self._get_selection_center(selected_nodes)

            # Step 6: Remove selected nodes from canvas
            self._remove_selected_nodes(selected_nodes)

            # Step 7: Create SubflowVisualNode
            subflow_node = self._create_subflow_node(subflow, center_pos, subflow_path)
            if not subflow_node:
                logger.error("Create Subflow: Failed to create subflow node")
                return None

            # Step 8: Reconnect external connections
            self._reconnect_external(subflow_node, analysis)

            logger.info(
                f"Subflow '{name}' created successfully with {len(selected_nodes)} nodes"
            )
            return subflow_node

        except Exception as e:
            logger.error(f"Create Subflow failed: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Create Subflow Error",
                f"Failed to create subflow: {str(e)}",
            )
            return None

    def _analyze_connections(self, selected_nodes: List) -> AnalyzedConnections:
        """
        Analyze connections to categorize as internal or external.

        Args:
            selected_nodes: List of selected visual nodes

        Returns:
            AnalyzedConnections with categorized connections
        """

        # Helper to get proper node_id (not memory address)
        def get_node_id(node) -> str:
            # Try property first
            prop_id = node.get_property("node_id")
            if prop_id and isinstance(prop_id, str) and prop_id.strip():
                # Verify it's not a memory address (starts with 0x)
                if not prop_id.startswith("0x"):
                    return prop_id

            # Try getting from casare_node
            if hasattr(node, "get_casare_node"):
                casare_node = node.get_casare_node()
                if casare_node and hasattr(casare_node, "node_id"):
                    casare_id = casare_node.node_id
                    if casare_id and not casare_id.startswith("0x"):
                        return casare_id

            # Last resort: use graph id (will be memory address)
            logger.warning(f"Could not get proper node_id for {node}, using graph id")
            return node.id

        # Build mapping of NodeGraphQt id -> proper node_id
        graph_id_to_node_id = {node.id: get_node_id(node) for node in selected_nodes}
        logger.debug(f"Node ID mapping: {graph_id_to_node_id}")
        selected_graph_ids = set(graph_id_to_node_id.keys())

        internal_connections = []
        external_inputs = []
        external_outputs = []

        # Iterate through all selected nodes and their ports
        for node in selected_nodes:
            node_id = get_node_id(node)

            # Check input ports for external connections
            for port in node.input_ports():
                connected_ports = port.connected_ports()
                for connected_port in connected_ports:
                    connected_node = connected_port.node()
                    connected_graph_id = connected_node.id

                    if connected_graph_id in selected_graph_ids:
                        # Internal connection - use proper node_id
                        connected_node_id = graph_id_to_node_id[connected_graph_id]
                        conn_data = {
                            "source_node": connected_node_id,
                            "source_port": connected_port.name(),
                            "target_node": node_id,
                            "target_port": port.name(),
                        }
                        internal_connections.append(conn_data)
                    else:
                        # External input (external -> internal)
                        # For external nodes, use graph id (they're not in our mapping)
                        external_inputs.append(
                            ExternalConnection(
                                external_node_id=connected_graph_id,
                                external_port_name=connected_port.name(),
                                internal_node_id=node_id,
                                internal_port_name=port.name(),
                                is_input=True,
                            )
                        )

            # Check output ports for external connections
            for port in node.output_ports():
                connected_ports = port.connected_ports()
                for connected_port in connected_ports:
                    connected_node = connected_port.node()
                    connected_graph_id = connected_node.id

                    if connected_graph_id not in selected_graph_ids:
                        # External output (internal -> external)
                        external_outputs.append(
                            ExternalConnection(
                                external_node_id=connected_graph_id,
                                external_port_name=connected_port.name(),
                                internal_node_id=node_id,
                                internal_port_name=port.name(),
                                is_input=False,
                            )
                        )

        # Deduplicate internal connections (they get added from both ends)
        seen_connections: Set[Tuple[str, str, str, str]] = set()
        unique_internal = []
        for conn in internal_connections:
            key = (
                conn["source_node"],
                conn["source_port"],
                conn["target_node"],
                conn["target_port"],
            )
            if key not in seen_connections:
                seen_connections.add(key)
                unique_internal.append(conn)

        return AnalyzedConnections(
            internal_connections=unique_internal,
            external_inputs=external_inputs,
            external_outputs=external_outputs,
        )

    def _generate_unique_name(self) -> str:
        """
        Generate a unique subflow name by checking existing subflows.

        Returns:
            Unique name like "Subflow 1", "Subflow 2", etc.
        """
        import json

        base_dir = Path.cwd() / "workflows" / "subflows"

        # Collect existing subflow names
        existing_names: set = set()
        if base_dir.exists():
            for subflow_file in base_dir.glob("*.json"):
                try:
                    with open(subflow_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "name" in data:
                            existing_names.add(data["name"])
                except Exception:
                    pass  # Skip files that can't be read

        # Also check nodes on canvas for existing subflow names
        if self._graph:
            for node in self._graph.all_nodes():
                if hasattr(node, "get_property"):
                    subflow_name = node.get_property("subflow_name")
                    if subflow_name:
                        existing_names.add(subflow_name)

        # Generate unique name: Subflow 1, Subflow 2, etc.
        counter = 1
        while True:
            name = f"Subflow {counter}"
            if name not in existing_names:
                return name
            counter += 1

    def _create_subflow(
        self,
        name: str,
        selected_nodes: List,
        analysis: AnalyzedConnections,
    ):
        """
        Create Subflow entity from selected nodes.

        Args:
            name: User-provided name
            selected_nodes: List of selected visual nodes
            analysis: Analyzed connections

        Returns:
            Subflow entity
        """
        from casare_rpa.domain.entities.subflow import (
            Subflow,
            SubflowPort,
            generate_subflow_id,
        )

        # Generate unique ID
        subflow_id = generate_subflow_id()

        # Create subflow
        subflow = Subflow(
            id=subflow_id,
            name=name,
            description=f"Subflow created from {len(selected_nodes)} nodes",
            category="subflows",
        )

        # Add input ports from external inputs (skip exec ports)
        input_names_used: Set[str] = set()
        for ext_input in analysis.external_inputs:
            # Detect port type
            is_exec, data_type = self._detect_port_type(
                ext_input.internal_node_id,
                ext_input.internal_port_name,
                selected_nodes,
                is_input=True,
            )

            # Skip exec ports - handled by default exec_in/exec_out
            if is_exec:
                continue

            # Generate unique port name
            base_name = ext_input.internal_port_name
            port_name = base_name
            counter = 1
            while port_name in input_names_used:
                port_name = f"{base_name}_{counter}"
                counter += 1
            input_names_used.add(port_name)

            subflow.add_input(
                SubflowPort(
                    name=port_name,
                    data_type=data_type,  # DataType enum
                    description=f"Input from {ext_input.internal_port_name}",
                    internal_node_id=ext_input.internal_node_id,
                    internal_port_name=ext_input.internal_port_name,
                )
            )

        # Add output ports from external outputs (skip exec ports)
        output_names_used: Set[str] = set()
        for ext_output in analysis.external_outputs:
            # Detect port type
            is_exec, data_type = self._detect_port_type(
                ext_output.internal_node_id,
                ext_output.internal_port_name,
                selected_nodes,
                is_input=False,
            )

            # Skip exec ports - handled by default exec_in/exec_out
            if is_exec:
                continue

            # Generate unique port name
            base_name = ext_output.internal_port_name
            port_name = base_name
            counter = 1
            while port_name in output_names_used:
                port_name = f"{base_name}_{counter}"
                counter += 1
            output_names_used.add(port_name)

            subflow.add_output(
                SubflowPort(
                    name=port_name,
                    data_type=data_type,  # DataType enum
                    description=f"Output from {ext_output.internal_port_name}",
                    internal_node_id=ext_output.internal_node_id,
                    internal_port_name=ext_output.internal_port_name,
                )
            )

        # Serialize and add nodes
        for node in selected_nodes:
            node_data = self._serialize_node(node)
            if node_data:
                subflow.add_node(node_data)

        # Add internal connections
        for conn in analysis.internal_connections:
            from casare_rpa.domain.entities.node_connection import NodeConnection

            connection = NodeConnection(
                source_node=conn["source_node"],
                source_port=conn["source_port"],
                target_node=conn["target_node"],
                target_port=conn["target_port"],
            )
            subflow.add_connection(connection)

        # Store bounds
        bounds = self._get_selection_bounds(selected_nodes)
        subflow.bounds = bounds

        return subflow

    def _detect_port_type(
        self,
        node_id: str,
        port_name: str,
        selected_nodes: List,
        is_input: bool,
    ):
        """
        Detect the type of a port and return DataType enum.

        Args:
            node_id: ID of the node containing the port (proper node_id, not graph ID)
            port_name: Name of the port
            selected_nodes: List of selected visual nodes
            is_input: Whether this is an input port

        Returns:
            Tuple of (is_exec_port, data_type) where data_type is DataType enum
        """
        from casare_rpa.domain.value_objects.types import DataType

        # Helper to get proper node_id (not memory address)
        def get_node_id(node) -> str:
            prop_id = node.get_property("node_id")
            if prop_id and isinstance(prop_id, str) and prop_id.strip():
                if not prop_id.startswith("0x"):
                    return prop_id
            if hasattr(node, "get_casare_node"):
                casare_node = node.get_casare_node()
                if casare_node and hasattr(casare_node, "node_id"):
                    casare_id = casare_node.node_id
                    if casare_id and not casare_id.startswith("0x"):
                        return casare_id
            return node.id

        # Find the node by its node_id property (not graph ID)
        node = None
        for n in selected_nodes:
            n_node_id = get_node_id(n)
            if n_node_id == node_id:
                node = n
                break

        if not node:
            return (False, DataType.ANY)

        # Check if node has get_port_type method
        if hasattr(node, "get_port_type"):
            data_type = node.get_port_type(port_name)
            if data_type is None:
                # Exec port - skip it (handled separately)
                return (True, DataType.ANY)
            # Data type is already a DataType enum from get_port_type
            if isinstance(data_type, DataType):
                return (False, data_type)
            return (False, DataType.ANY)

        # Check if it's an exec port by name
        exec_patterns = ["exec", "body", "true", "false", "completed", "error"]
        if any(pattern in port_name.lower() for pattern in exec_patterns):
            return (True, DataType.ANY)

        return (False, DataType.ANY)

    def _serialize_node(self, node) -> Optional[Dict[str, Any]]:
        """
        Serialize a visual node to dictionary.

        Args:
            node: Visual node to serialize

        Returns:
            Serialized node data or None
        """
        try:
            # Get casare node for proper node_id and type
            casare_node = (
                node.get_casare_node() if hasattr(node, "get_casare_node") else None
            )

            # Get node_id - prefer casare_node.node_id, fallback to property
            node_id = None
            if casare_node and hasattr(casare_node, "node_id"):
                node_id = casare_node.node_id
            if not node_id or node_id.startswith("0x"):
                prop_id = node.get_property("node_id")
                if (
                    prop_id
                    and isinstance(prop_id, str)
                    and prop_id.strip()
                    and not prop_id.startswith("0x")
                ):
                    node_id = prop_id
            if not node_id or node_id.startswith("0x"):
                node_id = node.id  # Last resort

            # Get node type
            node_type = node.__class__.__name__
            if casare_node:
                node_type = getattr(casare_node, "node_type", node_type)

            # Collect properties
            properties = {}
            if hasattr(node, "model") and node.model:
                for prop_name in node.model.custom_properties.keys():
                    try:
                        properties[prop_name] = node.get_property(prop_name)
                    except Exception:
                        pass

            # Get position
            pos = node.pos()

            return {
                "node_id": node_id,
                "type": node_type,
                "name": node.name() if hasattr(node, "name") else node_type,
                "position": {"x": pos[0], "y": pos[1]},
                "properties": properties,
            }

        except Exception as e:
            logger.error(f"Failed to serialize node: {e}")
            return None

    def _get_selection_center(self, selected_nodes: List) -> Tuple[float, float]:
        """
        Calculate the center position of selected nodes.

        Args:
            selected_nodes: List of selected visual nodes

        Returns:
            Tuple of (center_x, center_y)
        """
        if not selected_nodes:
            return (0.0, 0.0)

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for node in selected_nodes:
            pos = node.pos()
            x, y = pos[0], pos[1]
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        return (center_x, center_y)

    def _get_selection_bounds(self, selected_nodes: List) -> Dict[str, float]:
        """
        Get bounding box of selected nodes.

        Args:
            selected_nodes: List of selected visual nodes

        Returns:
            Dict with x, y, width, height
        """
        if not selected_nodes:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for node in selected_nodes:
            pos = node.pos()
            x, y = pos[0], pos[1]
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + 200)  # Approximate node width
            max_y = max(max_y, y + 100)  # Approximate node height

        return {
            "x": min_x,
            "y": min_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }

    def _get_subflow_path(self, subflow_id: str) -> str:
        """
        Get the file path for a subflow.

        Args:
            subflow_id: Unique subflow ID

        Returns:
            Path to subflow JSON file
        """
        # Use project directory if available
        base_dir = Path.cwd() / "workflows" / "subflows"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir / f"{subflow_id}.json")

    def _remove_selected_nodes(self, selected_nodes: List) -> None:
        """
        Remove selected nodes from the graph.

        Args:
            selected_nodes: List of nodes to remove
        """
        try:
            self._graph.delete_nodes(selected_nodes)
            logger.debug(f"Removed {len(selected_nodes)} nodes from graph")
        except Exception as e:
            logger.error(f"Failed to remove nodes: {e}")
            raise

    def _create_subflow_node(
        self,
        subflow,
        position: Tuple[float, float],
        subflow_path: str,
    ):
        """
        Create a SubflowVisualNode on the canvas.

        Args:
            subflow: The Subflow entity
            position: (x, y) position for the node
            subflow_path: Path to the subflow file

        Returns:
            The created SubflowVisualNode or None
        """
        try:
            # Try to create the subflow visual node
            subflow_node = self._graph.create_node(
                "casare_rpa.subflows.VisualSubflowNode",
                pos=[position[0], position[1]],
            )

            if subflow_node:
                # Configure the node with subflow data
                subflow_node.set_property("subflow_id", subflow.id)
                subflow_node.set_property("subflow_path", subflow_path)
                subflow_node.set_property("subflow_name", subflow.name)

                # Set display name
                if hasattr(subflow_node, "set_name"):
                    subflow_node.set_name(f"Subflow: {subflow.name}")

                # Configure from subflow to add dynamic ports
                if hasattr(subflow_node, "configure_from_subflow"):
                    subflow_node.configure_from_subflow(subflow)

                logger.info(f"Created SubflowVisualNode for '{subflow.name}'")
                return subflow_node

            logger.warning("Failed to create SubflowVisualNode")
            return None

        except Exception as e:
            logger.error(f"Failed to create subflow node: {e}")
            return None

    def _reconnect_external(
        self,
        subflow_node,
        analysis: AnalyzedConnections,
    ) -> None:
        """
        Reconnect external connections to the new subflow node.

        Args:
            subflow_node: The created SubflowVisualNode
            analysis: The analyzed connections
        """
        try:
            # Reconnect inputs: external output -> subflow input
            for ext_input in analysis.external_inputs:
                # Find external node
                external_node = self._graph.get_node_by_id(ext_input.external_node_id)
                if not external_node:
                    logger.warning(
                        f"External node not found: {ext_input.external_node_id}"
                    )
                    continue

                # Get external output port
                external_port = external_node.get_output(ext_input.external_port_name)
                if not external_port:
                    logger.warning(
                        f"External port not found: {ext_input.external_port_name}"
                    )
                    continue

                # Get subflow input port
                subflow_port = subflow_node.get_input(ext_input.internal_port_name)
                if not subflow_port:
                    # Try with generated name
                    subflow_port = subflow_node.get_input("exec_in")

                if subflow_port:
                    try:
                        external_port.connect_to(subflow_port)
                        logger.debug(
                            f"Reconnected input: {ext_input.external_node_id}."
                            f"{ext_input.external_port_name} -> subflow"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to reconnect input: {e}")

            # Reconnect outputs: subflow output -> external input
            for ext_output in analysis.external_outputs:
                # Find external node
                external_node = self._graph.get_node_by_id(ext_output.external_node_id)
                if not external_node:
                    logger.warning(
                        f"External node not found: {ext_output.external_node_id}"
                    )
                    continue

                # Get external input port
                external_port = external_node.get_input(ext_output.external_port_name)
                if not external_port:
                    logger.warning(
                        f"External port not found: {ext_output.external_port_name}"
                    )
                    continue

                # Get subflow output port
                subflow_port = subflow_node.get_output(ext_output.internal_port_name)
                if not subflow_port:
                    # Try with generated name
                    subflow_port = subflow_node.get_output("exec_out")

                if subflow_port:
                    try:
                        subflow_port.connect_to(external_port)
                        logger.debug(
                            f"Reconnected output: subflow -> {ext_output.external_node_id}."
                            f"{ext_output.external_port_name}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to reconnect output: {e}")

        except Exception as e:
            logger.error(f"Failed to reconnect external connections: {e}")

    def can_create_subflow(self, selected_nodes: List) -> bool:
        """
        Check if a subflow can be created from the selection.

        Args:
            selected_nodes: List of selected visual nodes

        Returns:
            True if subflow creation is possible
        """
        if len(selected_nodes) < 2:
            return False

        # Check for trigger nodes (can't include in subflow)
        for node in selected_nodes:
            node_type = node.__class__.__name__
            if "Trigger" in node_type or "Start" in node_type:
                return False

        return True
