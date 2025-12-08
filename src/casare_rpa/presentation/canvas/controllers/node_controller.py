"""
Node operations controller.

Handles all node-related operations:
- Node selection and navigation
- Node enable/disable state
- Node search and filtering
- Property updates
- Node registry initialization and management
"""

from typing import TYPE_CHECKING
from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor
from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class NodeController(BaseController):
    """
    Manages node operations in the workflow graph.

    Single Responsibility: Node manipulation and state management.

    Signals:
        node_selected: Emitted when a node is selected (str: node_id)
        node_deselected: Emitted when a node is deselected (str: node_id)
        node_disabled: Emitted when a node is disabled (str: node_id)
        node_enabled: Emitted when a node is enabled (str: node_id)
        node_navigated: Emitted when navigating to a node (str: node_id)
        node_property_changed: Emitted when node property changes (str: node_id, str: property, Any: value)
    """

    # Signals
    node_selected = Signal(str)  # node_id
    node_deselected = Signal(str)  # node_id
    node_disabled = Signal(str)  # node_id
    node_enabled = Signal(str)  # node_id
    node_navigated = Signal(str)  # node_id
    node_property_changed = Signal(str, str, object)  # node_id, property, value

    def __init__(self, main_window: "MainWindow"):
        """Initialize node controller."""
        super().__init__(main_window)

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        # Initialize node registry
        self._initialize_node_registry()

    def _initialize_node_registry(self) -> None:
        """
        Initialize node registry and register all node types.

        Extracted from: canvas/components/node_registry_component.py
        Registers all visual node types with the graph and pre-builds node mapping cache.
        """
        try:
            from ..graph.node_registry import get_node_registry, get_casare_node_mapping

            # Get the graph from main window
            graph = self._get_graph()
            if not graph:
                logger.warning("Graph not available for node registry initialization")
                return

            # Register all node types with the graph
            node_registry = get_node_registry()
            node_registry.register_all_nodes(graph)

            # Pre-build node mapping to avoid delay on first node creation
            get_casare_node_mapping()

        except ImportError as e:
            logger.error(f"Failed to import node registry: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize node registry: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("NodeController cleanup")

    def _get_nearest_node(self, max_distance: float = 300.0, use_title: bool = False):
        """
        Find the nearest node to cursor.

        Args:
            max_distance: Maximum distance in pixels. Returns None if no node within range.
            use_title: If True, calculate distance from title bar center. Otherwise use node center.

        Returns:
            Nearest node or None if no nodes or none within range.
        """
        graph = self._get_graph()
        if not graph:
            return None

        viewer = graph.viewer()
        if not viewer:
            return None

        # Get mouse position in scene coordinates
        global_pos = QCursor.pos()
        view_pos = viewer.mapFromGlobal(global_pos)
        scene_pos = viewer.mapToScene(view_pos)

        all_nodes = graph.all_nodes()
        if not all_nodes:
            return None

        nearest_node = None
        min_distance = float("inf")

        for node in all_nodes:
            node_pos = node.pos()  # Top-left corner
            if hasattr(node, "view") and node.view:
                rect = node.view.boundingRect()
                center_x = node_pos[0] + rect.width() / 2
                if use_title:
                    # Title bar is ~26px tall, center at ~13px from top
                    center_y = node_pos[1] + 13
                else:
                    center_y = node_pos[1] + rect.height() / 2
            else:
                # Fallback estimate
                center_x = node_pos[0] + 80
                center_y = node_pos[1] + (13 if use_title else 40)

            dx = scene_pos.x() - center_x
            dy = scene_pos.y() - center_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_node = node

        return nearest_node

    def select_nearest_node(self) -> None:
        """Select the nearest node to the current mouse cursor position (hotkey 2)."""
        logger.debug("Selecting nearest node to mouse")

        graph = self._get_graph()
        if not graph:
            return

        nearest_node = self._get_nearest_node(max_distance=300.0)
        if not nearest_node:
            self.main_window.show_status("No node nearby", 2000)
            return

        # Clear current selection and select the nearest node
        graph.clear_selection()
        nearest_node.set_selected(True)

        node_id = nearest_node.get_property("node_id")
        if node_id:
            self.node_selected.emit(node_id)

        node_name = nearest_node.name() if hasattr(nearest_node, "name") else "Node"
        self.main_window.show_status(f"Selected: {node_name}", 2000)

    def toggle_collapse_nearest_node(self) -> None:
        """Toggle collapse/expand on the nearest node to mouse cursor (hotkey 1)."""
        logger.debug("Toggling collapse on nearest node")

        nearest_node = self._get_nearest_node(max_distance=150.0, use_title=True)
        if not nearest_node:
            self.main_window.show_status("No node nearby", 2000)
            return

        if hasattr(nearest_node, "toggle_collapse"):
            nearest_node.toggle_collapse()
            is_collapsed = getattr(nearest_node, "_collapsed", False)
            state = "Collapsed" if is_collapsed else "Expanded"
            node_name = nearest_node.name() if hasattr(nearest_node, "name") else "Node"
            self.main_window.show_status(f"{state}: {node_name}", 2000)

    def toggle_disable_node(self) -> None:
        """
        Toggle disable state on nearest node to mouse (hotkey 4).

        Disabled nodes are bypassed during execution.
        """
        logger.debug("Toggling disable on nearest node")

        graph = self._get_graph()
        if not graph:
            return

        nearest_node = self._get_nearest_node(max_distance=300.0)
        if not nearest_node:
            self.main_window.show_status("No node nearby", 2000)
            return

        # Select and toggle disable on the nearest node
        graph.clear_selection()
        nearest_node.set_selected(True)

        # Use view.set_disabled() for proper visual overlay (same as Ctrl+E)
        view = nearest_node.view
        if view and hasattr(view, "set_disabled") and hasattr(view, "is_disabled"):
            # Toggle the disabled state using view methods
            current_disabled = view.is_disabled()
            new_disabled = not current_disabled
            view.set_disabled(new_disabled)

            # Also sync to casare node config for execution
            casare_node = (
                nearest_node.get_casare_node()
                if hasattr(nearest_node, "get_casare_node")
                else None
            )
            if casare_node:
                casare_node.config["_disabled"] = new_disabled

            # Also set on visual node property for serialization
            try:
                nearest_node.set_property("_disabled", new_disabled)
            except Exception:
                pass  # Property might not exist, that's OK

            node_id = nearest_node.get_property("node_id")
            node_name = nearest_node.name() if hasattr(nearest_node, "name") else "Node"
            state = "disabled" if new_disabled else "enabled"

            # Emit appropriate signal
            if new_disabled:
                if node_id:
                    self.node_disabled.emit(node_id)
            else:
                if node_id:
                    self.node_enabled.emit(node_id)

            self.main_window.show_status(f"{node_name} {state}", 2000)
        else:
            # Fallback for nodes without set_disabled method
            self.main_window.show_status("Cannot disable this node type", 2000)

    def navigate_to_node(self, node_id: str) -> None:
        """
        Navigate to and select a specific node.

        Args:
            node_id: ID of node to navigate to
        """
        logger.debug(f"Navigating to node: {node_id}")

        graph = self._get_graph()
        if not graph:
            return

        # Find node by ID
        all_nodes = graph.all_nodes()
        target_node = None

        for node in all_nodes:
            if node.get_property("node_id") == node_id:
                target_node = node
                break

        if not target_node:
            logger.warning(f"Node not found: {node_id}")
            return

        # Clear selection and select target node
        graph.clear_selection()
        target_node.set_selected(True)

        # Center view on node
        viewer = graph.viewer()
        if viewer and hasattr(viewer, "center_on"):
            viewer.center_on([target_node])

        self.node_navigated.emit(node_id)

        node_name = target_node.name() if hasattr(target_node, "name") else "Node"
        self.main_window.show_status(f"Navigated to: {node_name}", 2000)

    def find_node(self) -> None:
        """Open the node search dialog (Ctrl+F)."""
        logger.info("Opening node search dialog")

        graph = self._get_graph()
        if not graph:
            self.main_window.show_status("No graph available", 3000)
            return

        from ..search.node_search import NodeSearchDialog

        dialog = NodeSearchDialog(graph, self.main_window)
        dialog.show_search()

    def update_node_property(self, node_id: str, property_name: str, value) -> None:
        """
        Update a node's property.

        Args:
            node_id: ID of node to update
            property_name: Name of property to change
            value: New property value
        """
        logger.debug(f"Updating node property: {node_id}.{property_name} = {value}")

        graph = self._get_graph()
        if not graph:
            return

        # Find node by ID
        all_nodes = graph.all_nodes()
        for node in all_nodes:
            if node.get_property("node_id") == node_id:
                # Update property
                if hasattr(node, "set_property"):
                    node.set_property(property_name, value)

                # Emit signal
                self.node_property_changed.emit(node_id, property_name, value)

                logger.info(f"Node property updated: {node_id}.{property_name}")
                return

        logger.warning(f"Node not found for property update: {node_id}")

    def get_nearest_exec_out(self) -> None:
        """
        Find and select the closest exec_out port to cursor (hotkey 3).

        Searches all nodes for exec_out ports and finds the one closest
        to the mouse cursor position, then starts a live connection from it.
        """
        logger.debug("Getting closest exec_out port to cursor")

        graph = self._get_graph()
        if not graph:
            return

        viewer = graph.viewer()
        if not viewer:
            return

        # Get mouse position in scene coordinates
        global_pos = QCursor.pos()
        view_pos = viewer.mapFromGlobal(global_pos)
        scene_pos = viewer.mapToScene(view_pos)
        cursor_x, cursor_y = scene_pos.x(), scene_pos.y()

        # Find closest exec_out port across ALL nodes
        all_nodes = graph.all_nodes()
        if not all_nodes:
            self.main_window.show_status("No nodes in graph", 2000)
            return

        closest_port = None
        closest_node = None
        min_distance = float("inf")

        exec_port_names = ("exec_out", "exec", "body", "completed", "true", "false")

        for node in all_nodes:
            for port in node.output_ports():
                port_name = port.name().lower() if hasattr(port, "name") else ""
                if port_name not in exec_port_names:
                    continue

                # Get port position from view
                view_port = port.view if hasattr(port, "view") else None
                if view_port:
                    port_pos = view_port.scenePos()
                    dx = cursor_x - port_pos.x()
                    dy = cursor_y - port_pos.y()
                else:
                    # Fallback: estimate from node position
                    node_pos = node.pos()
                    dx = cursor_x - (node_pos[0] + 150)  # Approx right side
                    dy = cursor_y - node_pos[1]

                distance = (dx * dx + dy * dy) ** 0.5

                if distance < min_distance and distance <= 300.0:
                    min_distance = distance
                    closest_port = port
                    closest_node = node

        if not closest_port:
            self.main_window.show_status("No exec_out port nearby", 2000)
            return

        # Select the node
        graph.clear_selection()
        closest_node.set_selected(True)

        # Start connection from the closest port
        node_name = closest_node.name() if hasattr(closest_node, "name") else "Node"
        port_name = closest_port.name() if hasattr(closest_port, "name") else "exec_out"
        self.main_window.show_status(f"{node_name} → {port_name}", 2000)

        if hasattr(viewer, "start_live_connection"):
            view_port = closest_port.view if hasattr(closest_port, "view") else None
            if view_port:
                viewer.start_live_connection(view_port)

    def get_selected_nodes(self) -> list:
        """
        Get list of currently selected node IDs.

        Returns:
            List of node_id strings for selected nodes
        """
        graph = self._get_graph()
        if not graph:
            return []

        selected_ids = []
        for node in graph.selected_nodes():
            node_id = node.get_property("node_id")
            if node_id:
                selected_ids.append(node_id)
        return selected_ids

    def disable_all_selected(self) -> None:
        """
        Toggle disable state on all selected nodes (hotkey 5).

        If any selected node is enabled, disables all.
        If all selected nodes are disabled, enables all.
        """
        logger.debug("Toggling disable on all selected nodes")

        graph = self._get_graph()
        if not graph:
            return

        selected_nodes = graph.selected_nodes()
        if not selected_nodes:
            self.main_window.show_status("No nodes selected", 2000)
            return

        # Check if any node is currently enabled
        any_enabled = False
        for node in selected_nodes:
            casare_node = (
                node.get_casare_node() if hasattr(node, "get_casare_node") else None
            )
            if casare_node:
                if not casare_node.config.get("_disabled", False):
                    any_enabled = True
                    break

        # If any is enabled, disable all. Otherwise enable all.
        new_disabled = any_enabled

        count = 0
        for node in selected_nodes:
            casare_node = (
                node.get_casare_node() if hasattr(node, "get_casare_node") else None
            )
            if casare_node:
                casare_node.config["_disabled"] = new_disabled

                # Also set on visual node property for serialization consistency
                try:
                    node.set_property("_disabled", new_disabled)
                except Exception:
                    pass  # Property might not exist, that's OK

                # Update visual appearance
                if hasattr(node, "view") and node.view:
                    node.view.setOpacity(0.4 if new_disabled else 1.0)

                node_id = node.get_property("node_id")
                if node_id:
                    if new_disabled:
                        self.node_disabled.emit(node_id)
                    else:
                        self.node_enabled.emit(node_id)
                count += 1

        state = "disabled" if new_disabled else "enabled"
        self.main_window.show_status(f"{count} node(s) {state}", 2000)

    def _get_graph(self):
        """
        Get the node graph from central widget.

        Returns:
            NodeGraph instance or None if not available
        """
        return self.main_window.get_graph()
