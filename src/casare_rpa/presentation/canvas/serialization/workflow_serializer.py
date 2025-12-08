"""
Workflow Serializer for Canvas.

Converts NodeGraphQt visual graph to workflow JSON dict matching
the format expected by load_workflow_from_dict().
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph
    from casare_rpa.presentation.main_window import MainWindow


class WorkflowSerializer:
    """
    Serializes NodeGraphQt graph to workflow JSON.

    Extracts nodes, connections, variables, and frames from the visual graph
    and converts them to the workflow schema format used by the execution engine.
    """

    def __init__(self, graph: "NodeGraph", main_window: "MainWindow"):
        """
        Initialize the serializer.

        Args:
            graph: NodeGraphQt NodeGraph instance
            main_window: MainWindow for accessing bottom panel variables
        """
        self._graph = graph
        self._main_window = main_window

    def serialize(self) -> dict:
        """
        Serialize the entire graph to workflow dict.

        Returns:
            Complete workflow dict matching WorkflowSchema format
        """
        logger.debug("Serializing workflow from canvas graph")

        try:
            workflow_data = {
                "metadata": self._get_metadata(),
                "nodes": self._serialize_nodes(),
                "connections": self._serialize_connections(),
                "variables": self._get_variables(),
                "frames": self._serialize_frames(),
                "settings": self._get_settings(),
            }

            node_count = len(workflow_data["nodes"])
            connection_count = len(workflow_data["connections"])
            logger.debug(
                f"Serialization complete: {node_count} nodes, {connection_count} connections"
            )

            return workflow_data

        except Exception as e:
            logger.exception(f"Failed to serialize workflow: {e}")
            # Return minimal valid structure on error
            return {
                "metadata": {"name": "", "description": "", "version": "1.0.0"},
                "nodes": {},
                "connections": [],
                "variables": {},
                "frames": [],
                "settings": {},
            }

    def _get_metadata(self) -> Dict[str, str]:
        """Get workflow metadata."""
        # Get current file info from WorkflowController if available
        current_file = getattr(self._main_window, "_current_file", None)
        workflow_name = ""

        if current_file:
            from pathlib import Path

            workflow_name = Path(current_file).stem

        return {
            "name": workflow_name or "Untitled Workflow",
            "description": "",
            "version": "1.0.0",
            "author": "",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }

    def _serialize_nodes(self) -> Dict[str, dict]:
        """
        Serialize all nodes from the graph.

        Returns:
            Dict mapping node_id to node data
        """
        nodes_dict = {}

        for visual_node in self._graph.all_nodes():
            try:
                node_data = self._serialize_node(visual_node)
                if node_data:
                    nodes_dict[node_data["node_id"]] = node_data
            except Exception as e:
                logger.warning(f"Failed to serialize node {visual_node.name()}: {e}")
                continue

        return nodes_dict

    def _serialize_node(self, visual_node) -> Optional[dict]:
        """
        Serialize a single visual node.

        Args:
            visual_node: NodeGraphQt node instance

        Returns:
            Node data dict or None if node should be skipped
        """
        # Skip visual-only annotation nodes
        if not hasattr(visual_node, "_casare_node") or visual_node._casare_node is None:
            logger.debug(
                f"Skipping visual-only node: {visual_node.name()} (no CasareRPA backing)"
            )
            return None

        casare_node = visual_node._casare_node

        # Get node ID
        node_id = visual_node.get_property("node_id")
        if not node_id:
            logger.warning(f"Node {visual_node.name()} has no node_id property")
            return None

        # Get node type from CasareRPA node class
        node_type = casare_node.__class__.__name__

        # Get position
        position = visual_node.pos()  # Returns [x, y]

        # Get config from CasareRPA node
        config = casare_node.config.copy() if hasattr(casare_node, "config") else {}

        # CRITICAL BUG FIX: Sync widget values from visual node to config
        #
        # Problem: Widget values (URL in LaunchBrowser, Duration in Wait, Message in MessageBox)
        # were entered by users but never persisted to casare_node.config, causing only default
        # values to execute instead of custom values.
        #
        # Root Cause: Visual nodes store widget values as NodeGraphQt properties, but these
        # were never synchronized to the domain node's config dict before serialization.
        #
        # Solution: Iterate through all custom properties on the visual node and copy their
        # values to the config dict that will be serialized and executed.
        #
        # This ensures: User inputs → Visual node properties → Config dict → Execution
        for prop_name in visual_node.model.custom_properties:
            # Skip internal properties
            if prop_name.startswith("_") or prop_name in (
                "node_id",
                "name",
                "color",
                "pos",
                # Subflow internal properties (stored as instance vars, not widgets)
                "subflow_id",
                "subflow_path",
                "subflow_name",
                "node_count",
            ):
                continue

            prop_value = visual_node.get_property(prop_name)
            if prop_value is not None:
                config[prop_name] = prop_value

        # Check if node is disabled - from casare_node.config (set by toggle_disable_node)
        # Note: _disabled should already be in config from casare_node.config.copy() above
        # This additional check is for visual node property if it exists
        disabled_from_visual = visual_node.get_property("_disabled")
        disabled_from_config = config.get("_disabled", False)

        if disabled_from_visual and not disabled_from_config:
            config["_disabled"] = True

        # Get custom display name (if user renamed the node)
        display_name = visual_node.name()
        # Default name is typically "{NodeType}_1" or similar - only save if customized
        default_prefix = node_type.replace("Node", "")
        is_custom_name = display_name and not display_name.startswith(default_prefix)

        # Special handling for subflow nodes - add internal properties to config
        # These are stored as instance variables but need to be serialized for loading
        if node_type == "SubflowNode" or "Subflow" in visual_node.__class__.__name__:
            for internal_prop in ("subflow_id", "subflow_path", "subflow_name"):
                try:
                    val = visual_node.get_property(internal_prop)
                    if val:
                        config[internal_prop] = val
                except Exception:
                    pass

        node_dict = {
            "node_id": node_id,
            "node_type": node_type,
            "position": position,
            "config": config,
        }

        # Only include name if it's a custom user-defined name
        if is_custom_name:
            node_dict["name"] = display_name

        return node_dict

    def _serialize_connections(self) -> List[dict]:
        """
        Serialize all connections between nodes.

        Returns:
            List of connection dicts
        """
        connections = []
        processed = set()  # Track processed connections to avoid duplicates

        for node in self._graph.all_nodes():
            # Skip visual-only nodes
            if not hasattr(node, "_casare_node") or node._casare_node is None:
                continue

            # Get output ports and their connections
            for port_item in node.output_ports():
                # output_ports() returns Port objects, not port names
                # Get the port name from the Port object
                if hasattr(port_item, "name"):
                    port_name = port_item.name()
                    output_port = port_item
                else:
                    # Fallback: if it's already a string (port name)
                    port_name = str(port_item)
                    output_port = node.output(port_name)

                if not output_port:
                    continue

                # Get connected input ports
                for connected_port in output_port.connected_ports():
                    try:
                        target_node = connected_port.node()

                        # Skip if target is visual-only
                        if (
                            not hasattr(target_node, "_casare_node")
                            or target_node._casare_node is None
                        ):
                            continue

                        # Create connection key to avoid duplicates
                        source_id = node.get_property("node_id")
                        target_id = target_node.get_property("node_id")
                        conn_key = (
                            source_id,
                            port_name,
                            target_id,
                            connected_port.name(),
                        )

                        if conn_key in processed:
                            continue
                        processed.add(conn_key)

                        connection = {
                            "source_node": source_id,
                            "source_port": port_name,
                            "target_node": target_id,
                            "target_port": connected_port.name(),
                        }

                        connections.append(connection)

                    except Exception as e:
                        logger.warning(f"Failed to serialize connection: {e}")
                        continue

        return connections

    def _get_variables(self) -> Dict[str, dict]:
        """
        Get variables from the bottom panel variables tab.

        Returns:
            Dict mapping variable name to variable data
        """
        try:
            # Try to get variables from bottom panel
            if (
                hasattr(self._main_window, "_bottom_panel")
                and self._main_window._bottom_panel
            ):
                variables_tab = self._main_window._bottom_panel.get_variables_tab()
                if variables_tab and hasattr(variables_tab, "get_variables"):
                    variables = variables_tab.get_variables()
                    logger.debug(f"Retrieved {len(variables)} variables from panel")
                    return variables
        except Exception as e:
            logger.debug(f"Could not retrieve variables from panel: {e}")

        return {}

    def _serialize_frames(self) -> List[dict]:
        """
        Serialize frames (node grouping boxes).

        Returns:
            List of frame dicts
        """
        frames = []

        try:
            # NodeGraphQt stores frames in the scene
            # Access via graph._viewer._scene if available
            if hasattr(self._graph, "_viewer") and hasattr(
                self._graph._viewer, "_scene"
            ):
                scene = self._graph._viewer._scene

                # Look for frame items in the scene
                from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame

                for item in scene.items():
                    if isinstance(item, NodeFrame):
                        try:
                            # Use public properties/getattr with defaults to avoid
                            # breaking if NodeFrame API changes (defensive access)
                            title = getattr(item, "frame_title", None) or getattr(
                                item, "_title", "Group"
                            )
                            color = getattr(item, "frame_color", None) or getattr(
                                item, "_color", None
                            )
                            # Get rect via public rect() method or fallback to _rect
                            rect = (
                                item.rect()
                                if hasattr(item, "rect")
                                else getattr(item, "_rect", None)
                            )
                            # Get contained nodes via public property or fallback
                            contained_nodes = getattr(
                                item, "contained_nodes", None
                            ) or getattr(item, "_nodes", [])

                            frame_data = {
                                "title": title,
                                "color": color,
                                "position": [item.pos().x(), item.pos().y()],
                                "size": [
                                    rect.width() if rect else 400,
                                    rect.height() if rect else 300,
                                ],
                                "node_ids": [
                                    node.get_property("node_id")
                                    for node in contained_nodes
                                    if hasattr(node, "_casare_node")
                                ],
                            }
                            frames.append(frame_data)
                        except Exception as e:
                            logger.debug(f"Failed to serialize frame: {e}")
                            continue

        except Exception as e:
            logger.debug(f"Could not access frames: {e}")

        return frames

    def _get_settings(self) -> Dict[str, Any]:
        """
        Get workflow execution settings.

        Reads from main_window preferences if available, falls back to defaults.

        Returns:
            Settings dict
        """
        # Defaults
        settings = {
            "stop_on_error": True,
            "timeout": 120,
            "retry_count": 0,
        }

        # Try to read from main_window preferences
        try:
            if hasattr(self._main_window, "get_preferences"):
                prefs = self._main_window.get_preferences()
                if prefs and isinstance(prefs, dict):
                    execution_prefs = prefs.get("execution", {})
                    if "stop_on_error" in execution_prefs:
                        settings["stop_on_error"] = bool(
                            execution_prefs["stop_on_error"]
                        )
                    if "timeout" in execution_prefs:
                        settings["timeout"] = int(execution_prefs["timeout"])
                    if "retry_count" in execution_prefs:
                        settings["retry_count"] = int(execution_prefs["retry_count"])
                    logger.debug("Loaded execution settings from preferences")
        except Exception as e:
            logger.debug(
                f"Could not load settings from preferences, using defaults: {e}"
            )

        return settings
