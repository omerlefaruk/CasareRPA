"""
Workflow Deserializer for Canvas.

Loads workflow JSON and recreates visual nodes in NodeGraphQt graph.
This is the inverse of WorkflowSerializer.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from pathlib import Path
import orjson
from loguru import logger
from pydantic import ValidationError

from casare_rpa.infrastructure.security.workflow_schema import validate_workflow_json
from casare_rpa.nodes.file.file_security import (
    validate_path_security_readonly,
    PathSecurityError,
)

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class WorkflowDeserializer:
    """
    Deserializes workflow JSON back into NodeGraphQt visual graph.

    Reads workflow JSON files and recreates:
    - Visual nodes with their properties
    - Connections between nodes
    - Node positions
    - Variables and settings
    """

    def __init__(self, graph: "NodeGraph", main_window):
        """
        Initialize the deserializer.

        Args:
            graph: NodeGraphQt NodeGraph instance
            main_window: MainWindow for accessing bottom panel
        """
        self._graph = graph
        self._main_window = main_window

        # Map from node type names to registered NodeGraphQt node identifiers
        # This maps CasareRPA node types to their visual counterparts
        # Built lazily on first use (after nodes are registered)
        self._node_type_map: Optional[Dict[str, str]] = None

    def _get_node_type_map(self) -> Dict[str, str]:
        """
        Get node type map, building it lazily on first use.

        Returns:
            Dict mapping node_type to NodeGraphQt identifier
        """
        if self._node_type_map is None:
            self._node_type_map = self._build_node_type_map()
        return self._node_type_map

    def _build_node_type_map(self) -> Dict[str, str]:
        """
        Build mapping from CasareRPA node types to NodeGraphQt identifiers.

        Returns:
            Dict mapping node_type to NodeGraphQt identifier
        """
        # Get all registered node types from the graph
        registered = {}

        try:
            # NodeGraphQt stores registered nodes by their identifier
            # Format: "category.VisualNodeName"
            for identifier in self._graph.registered_nodes():
                # Extract the node type from the identifier
                # e.g., "casare_rpa.browser.VisualLaunchBrowserNode" -> "LaunchBrowserNode"
                parts = identifier.split(".")
                if parts:
                    visual_name = parts[-1]
                    # Convert VisualXxxNode to XxxNode
                    if visual_name.startswith("Visual"):
                        node_type = visual_name[6:]  # Remove "Visual" prefix
                        registered[node_type] = identifier

        except Exception as e:
            logger.warning(f"Could not enumerate registered nodes: {e}")

        logger.debug(f"Built node type map with {len(registered)} entries")
        return registered

    def load_from_file(self, file_path: str) -> bool:
        """
        Load workflow from JSON file.

        Args:
            file_path: Path to the workflow JSON file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # SECURITY: Validate path before reading to prevent path traversal attacks
            try:
                validated_path = validate_path_security_readonly(
                    file_path, operation="load_workflow"
                )
            except PathSecurityError as e:
                logger.error(f"Security violation loading workflow: {e}")
                return False

            path = Path(validated_path)
            if not path.exists():
                logger.error(f"Workflow file not found: {file_path}")
                return False

            with open(path, "rb") as f:
                data = orjson.loads(f.read())

            return self.deserialize(data)

        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workflow file: {e}")
            return False
        except Exception as e:
            logger.exception(f"Failed to load workflow: {e}")
            return False

    def deserialize(self, workflow_data: Dict) -> bool:
        """
        Deserialize workflow dict into visual graph.

        Args:
            workflow_data: Workflow dictionary (from WorkflowSerializer format)

        Returns:
            True if deserialized successfully, False otherwise
        """
        logger.info("Deserializing workflow into canvas graph")

        try:
            # SECURITY: Validate workflow JSON against schema before processing
            # This prevents code injection and resource exhaustion attacks
            try:
                validate_workflow_json(workflow_data)
                logger.debug("Workflow schema validation passed")
            except ValidationError as e:
                logger.error(f"Workflow schema validation failed: {e}")
                return False
            except Exception as e:
                logger.warning(f"Schema validation skipped (non-standard format): {e}")
                # Continue anyway for backwards compatibility with older formats

            # Clear existing graph
            self._graph.clear_session()

            # Create nodes
            node_map = {}  # Maps node_id to visual node
            nodes_data = workflow_data.get("nodes", {})

            for node_id, node_data in nodes_data.items():
                visual_node = self._create_node(node_id, node_data)
                if visual_node:
                    node_map[node_id] = visual_node

            logger.info(f"Created {len(node_map)} nodes")

            # Create connections
            connections_data = workflow_data.get("connections", [])
            connection_count = self._create_connections(connections_data, node_map)
            logger.info(f"Created {connection_count} connections")

            # Restore variables
            variables = workflow_data.get("variables", {})
            self._restore_variables(variables)

            # Restore frames
            frames = workflow_data.get("frames", [])
            self._restore_frames(frames, node_map)

            # Center view on nodes
            if node_map:
                self._graph.center_on(list(node_map.values()))

            logger.info("Workflow deserialization complete")
            return True

        except Exception as e:
            logger.exception(f"Failed to deserialize workflow: {e}")
            return False

    def _create_node(self, node_id: str, node_data: Dict) -> Optional[Any]:
        """
        Create a single visual node from data.

        Args:
            node_id: Unique node identifier
            node_data: Node data dict with node_type, position, config

        Returns:
            Created visual node or None if failed
        """
        node_type = node_data.get("node_type")
        if not node_type:
            logger.warning(f"Node {node_id} has no node_type")
            return None

        # Find the NodeGraphQt identifier for this node type
        identifier = self._get_node_type_map().get(node_type)

        if not identifier:
            # Try to find by searching registered nodes
            identifier = self._find_node_identifier(node_type)

        if not identifier:
            logger.warning(f"Unknown node type: {node_type} (node_id: {node_id})")
            return None

        try:
            # Get position
            position = node_data.get("position", [0, 0])
            if isinstance(position, (list, tuple)) and len(position) >= 2:
                pos = [float(position[0]), float(position[1])]
            else:
                pos = [0.0, 0.0]

            # Create the node
            visual_node = self._graph.create_node(identifier, pos=pos)

            if not visual_node:
                logger.error(f"Failed to create node: {identifier}")
                return None

            # Set node_id property (critical for connections and execution)
            visual_node.set_property("node_id", node_id)

            # Get the CasareRPA backing node and set its ID too
            if hasattr(visual_node, "_casare_node") and visual_node._casare_node:
                visual_node._casare_node.node_id = node_id

            # Apply config to node properties
            config = node_data.get("config", {})
            self._apply_config(visual_node, config)

            logger.debug(f"Created node: {node_type} at {pos} with id {node_id}")
            return visual_node

        except Exception as e:
            logger.error(f"Failed to create node {node_id} ({node_type}): {e}")
            return None

    def _find_node_identifier(self, node_type: str) -> Optional[str]:
        """
        Find NodeGraphQt identifier for a node type by searching.

        Args:
            node_type: CasareRPA node type name (e.g., "LaunchBrowserNode")

        Returns:
            NodeGraphQt identifier or None
        """
        try:
            # Search through all registered nodes
            for identifier in self._graph.registered_nodes():
                # Check if the identifier ends with Visual{node_type}
                expected_visual = f"Visual{node_type}"
                if identifier.endswith(expected_visual):
                    # Cache for future lookups
                    node_map = self._get_node_type_map()
                    node_map[node_type] = identifier
                    return identifier

                # Also check for exact match without Visual prefix
                if identifier.endswith(node_type):
                    node_map = self._get_node_type_map()
                    node_map[node_type] = identifier
                    return identifier

        except Exception as e:
            logger.debug(f"Error searching for node identifier: {e}")

        return None

    def _apply_config(self, visual_node, config: Dict) -> None:
        """
        Apply config values to visual node properties.

        Args:
            visual_node: NodeGraphQt visual node
            config: Config dictionary from workflow
        """
        if not config:
            return

        # Get list of custom properties that can be set
        try:
            model = visual_node.model
            custom_props = list(model.custom_properties.keys()) if model else []
        except Exception:
            custom_props = []

        for key, value in config.items():
            # Skip internal/meta properties
            if key.startswith("_"):
                # Handle disabled state
                if key == "_disabled" and value:
                    visual_node.set_disabled(True)
                continue

            # Skip node_id as it's already set
            if key == "node_id":
                continue

            try:
                # Try to set as property
                if key in custom_props or self._has_property(visual_node, key):
                    visual_node.set_property(key, value)

                # Also update CasareRPA node config
                if hasattr(visual_node, "_casare_node") and visual_node._casare_node:
                    visual_node._casare_node.config[key] = value

            except Exception as e:
                logger.debug(f"Could not set property {key}={value}: {e}")

    def _has_property(self, visual_node, prop_name: str) -> bool:
        """Check if visual node has a property."""
        try:
            visual_node.get_property(prop_name)
            return True
        except Exception:
            return False

    def _create_connections(self, connections: List[Dict], node_map: Dict) -> int:
        """
        Create connections between nodes.

        Args:
            connections: List of connection dicts
            node_map: Map of node_id to visual nodes

        Returns:
            Number of connections created
        """
        created = 0

        for conn in connections:
            try:
                source_id = conn.get("source_node")
                source_port = conn.get("source_port")
                target_id = conn.get("target_node")
                target_port = conn.get("target_port")

                # Get the visual nodes
                source_node = node_map.get(source_id)
                target_node = node_map.get(target_id)

                if not source_node:
                    logger.warning(f"Source node not found: {source_id}")
                    continue
                if not target_node:
                    logger.warning(f"Target node not found: {target_id}")
                    continue

                # Get the ports
                output_port = source_node.get_output(source_port)
                input_port = target_node.get_input(target_port)

                if not output_port:
                    logger.warning(f"Output port not found: {source_id}.{source_port}")
                    continue
                if not input_port:
                    logger.warning(f"Input port not found: {target_id}.{target_port}")
                    continue

                # Create connection
                output_port.connect_to(input_port)
                created += 1

            except Exception as e:
                logger.warning(f"Failed to create connection: {e}")
                continue

        return created

    def _restore_variables(self, variables: Dict) -> None:
        """
        Restore workflow variables to the variables panel.

        Args:
            variables: Variables dictionary
        """
        if not variables:
            return

        try:
            if (
                hasattr(self._main_window, "_bottom_panel")
                and self._main_window._bottom_panel
            ):
                variables_tab = self._main_window._bottom_panel.get_variables_tab()
                if variables_tab and hasattr(variables_tab, "set_variables"):
                    variables_tab.set_variables(variables)
                    logger.debug(f"Restored {len(variables)} variables")
        except Exception as e:
            logger.debug(f"Could not restore variables: {e}")

    def _restore_frames(self, frames: List[Dict], node_map: Dict) -> None:
        """
        Restore visual frames/groups.

        Args:
            frames: List of frame data dicts
            node_map: Map of node_id to visual nodes
        """
        if not frames:
            return

        try:
            from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame

            viewer = self._graph.viewer()
            scene = viewer.scene()

            for frame_data in frames:
                try:
                    title = frame_data.get("title", "Group")
                    position = frame_data.get("position", [0, 0])
                    size = frame_data.get("size", [400, 300])
                    color = frame_data.get("color")
                    node_ids = frame_data.get("node_ids", [])

                    # Get contained nodes
                    contained_nodes = [
                        node_map[nid] for nid in node_ids if nid in node_map
                    ]

                    # Create frame
                    frame = NodeFrame(
                        title=title,
                        nodes=contained_nodes,
                    )

                    # Set position and size
                    from PySide6.QtCore import QPointF, QRectF

                    frame.setPos(QPointF(position[0], position[1]))
                    frame.setRect(QRectF(0, 0, size[0], size[1]))

                    if color:
                        from PySide6.QtGui import QColor

                        frame.set_color(
                            QColor(*color)
                            if isinstance(color, (list, tuple))
                            else QColor(color)
                        )

                    scene.addItem(frame)
                    logger.debug(f"Restored frame: {title}")

                except Exception as e:
                    logger.warning(f"Failed to restore frame: {e}")

        except ImportError:
            logger.debug("NodeFrame not available, skipping frame restoration")
        except Exception as e:
            logger.debug(f"Could not restore frames: {e}")
