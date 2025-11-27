"""
Node operations controller.

Handles all node-related operations:
- Node selection and navigation
- Node enable/disable state
- Node search and filtering
- Property updates
"""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor
from loguru import logger

from .base_controller import BaseController


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

    def __init__(self, main_window):
        """Initialize node controller."""
        super().__init__(main_window)

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("NodeController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("NodeController cleanup")

    def select_nearest_node(self) -> None:
        """Select the nearest node to the current mouse cursor position (hotkey 2)."""
        logger.debug("Selecting nearest node to mouse")

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

        # Find nearest node
        all_nodes = graph.all_nodes()
        if not all_nodes:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage("No nodes in graph", 2000)
            return

        nearest_node = None
        min_distance = float("inf")

        for node in all_nodes:
            node_pos = node.pos()
            # Calculate distance from mouse to node center
            dx = scene_pos.x() - node_pos[0]
            dy = scene_pos.y() - node_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        if nearest_node:
            # Clear current selection and select the nearest node
            graph.clear_selection()
            nearest_node.set_selected(True)

            node_id = nearest_node.get_property("node_id")
            if node_id:
                self.node_selected.emit(node_id)

            node_name = (
                nearest_node.name() if hasattr(nearest_node, "name") else "Node"
            )
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(f"Selected: {node_name}", 2000)

    def toggle_disable_node(self) -> None:
        """
        Toggle disable state on nearest node to mouse (hotkey 4).

        Disabled nodes are bypassed during execution.
        """
        logger.debug("Toggling disable on nearest node")

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

        # Find nearest node to mouse
        all_nodes = graph.all_nodes()
        if not all_nodes:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage("No nodes in graph", 2000)
            return

        nearest_node = None
        min_distance = float("inf")

        for node in all_nodes:
            node_pos = node.pos()
            dx = scene_pos.x() - node_pos[0]
            dy = scene_pos.y() - node_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        if not nearest_node:
            return

        # Select and toggle disable on the nearest node
        graph.clear_selection()
        nearest_node.set_selected(True)

        # Get the casare node instance
        casare_node = (
            nearest_node.get_casare_node()
            if hasattr(nearest_node, "get_casare_node")
            else None
        )

        if casare_node:
            # Toggle the disabled state
            current_disabled = casare_node.config.get("_disabled", False)
            new_disabled = not current_disabled
            casare_node.config["_disabled"] = new_disabled

            # Update visual appearance
            if hasattr(nearest_node, "view") and nearest_node.view:
                if new_disabled:
                    # Make node semi-transparent when disabled
                    nearest_node.view.setOpacity(0.4)
                else:
                    nearest_node.view.setOpacity(1.0)

            node_id = nearest_node.get_property("node_id")
            node_name = (
                nearest_node.name() if hasattr(nearest_node, "name") else "Node"
            )
            state = "disabled" if new_disabled else "enabled"

            # Emit appropriate signal
            if new_disabled:
                if node_id:
                    self.node_disabled.emit(node_id)
            else:
                if node_id:
                    self.node_enabled.emit(node_id)

            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"{node_name} {state}", 2000
                )

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
        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                f"Navigated to: {node_name}", 2000
            )

    def find_node(self) -> None:
        """Open the node search dialog (Ctrl+F)."""
        logger.info("Opening node search dialog")

        graph = self._get_graph()
        if not graph:
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage("No graph available", 3000)
            return

        from ....canvas.search.node_search import NodeSearchDialog

        dialog = NodeSearchDialog(graph, self.main_window)
        dialog.show_search()

    def update_node_property(
        self, node_id: str, property_name: str, value
    ) -> None:
        """
        Update a node's property.

        Args:
            node_id: ID of node to update
            property_name: Name of property to change
            value: New property value
        """
        logger.debug(
            f"Updating node property: {node_id}.{property_name} = {value}"
        )

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

    def _get_graph(self):
        """
        Get the node graph from central widget.

        Returns:
            NodeGraph instance or None if not available
        """
        central_widget = self.main_window._central_widget
        if not central_widget or not hasattr(central_widget, "graph"):
            return None
        return central_widget.graph
