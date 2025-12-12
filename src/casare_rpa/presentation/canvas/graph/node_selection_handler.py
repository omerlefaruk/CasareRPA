"""
Node selection handling module for NodeGraphWidget.

Extracts selection-related operations from NodeGraphWidget for better maintainability.
Handles:
- Node selection retrieval and management
- Node deletion (single and multi-select)
- Node duplication
- Node enable/disable toggling
- Node renaming
- Subflow creation from selection
- Frame deletion
"""

from typing import TYPE_CHECKING, List

from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph
    from casare_rpa.presentation.canvas.graph.selection_manager import SelectionManager


class NodeSelectionHandler:
    """
    Handles node selection operations for the node graph.

    Extracted from NodeGraphWidget to improve code organization and testability.
    """

    def __init__(self, graph: "NodeGraph", selection_manager: "SelectionManager"):
        """
        Initialize node selection handler.

        Args:
            graph: The NodeGraph instance
            selection_manager: The selection manager instance
        """
        self._graph = graph
        self._selection = selection_manager

    def get_selected_nodes(self) -> List:
        """
        Get the currently selected nodes.

        Returns:
            List of selected node objects
        """
        return self._selection.get_selected_nodes()

    def clear_selection(self) -> None:
        """Clear node selection."""
        self._selection.clear_selection()

    def delete_selected_nodes(self) -> bool:
        """
        Delete all selected nodes in the graph.

        Returns:
            True if any nodes were deleted, False otherwise
        """
        try:
            selected = self._graph.selected_nodes()
            if not selected:
                return False

            logger.debug(f"Deleting {len(selected)} selected nodes")
            self._graph.delete_nodes(selected)
            return True
        except Exception as e:
            logger.error(f"Failed to delete selected nodes: {e}")
            return False

    def delete_selected_frames(self) -> bool:
        """
        Delete any selected frames in the scene.

        Returns:
            True if any frames were deleted, False otherwise
        """
        return self._selection.delete_selected_frames()

    def duplicate_selected_nodes(self) -> bool:
        """
        Duplicate all selected nodes with slight position offset.

        Returns:
            True if nodes were duplicated, False otherwise
        """
        try:
            selected = self._graph.selected_nodes()
            if not selected:
                return False

            logger.debug(f"Duplicating {len(selected)} selected nodes")

            if hasattr(self._graph, "duplicate_nodes"):
                self._graph.duplicate_nodes(selected)
                return True

            # Fallback: Copy/paste approach
            self._graph.copy_nodes(selected)
            self._graph.paste_nodes()
            return True
        except Exception as e:
            logger.error(f"Failed to duplicate selected nodes: {e}")
            return False

    def toggle_selected_nodes_enabled(self) -> bool:
        """
        Toggle the enabled/disabled state of all selected nodes.

        Returns:
            True if any nodes were toggled, False otherwise
        """
        try:
            selected = self._graph.selected_nodes()
            if not selected:
                return False

            logger.debug(f"Toggling enabled state for {len(selected)} selected nodes")

            for node in selected:
                view = node.view
                if (
                    view
                    and hasattr(view, "set_disabled")
                    and hasattr(view, "is_disabled")
                ):
                    current_disabled = view.is_disabled()
                    new_disabled = not current_disabled
                    view.set_disabled(new_disabled)

                    casare_node = (
                        node.get_casare_node()
                        if hasattr(node, "get_casare_node")
                        else None
                    )
                    if casare_node:
                        casare_node.config["_disabled"] = new_disabled

                    try:
                        node.set_property("_disabled", new_disabled)
                    except Exception:
                        pass

                    logger.debug(f"Node {node.name()} disabled: {new_disabled}")

            return True
        except Exception as e:
            logger.error(f"Failed to toggle node enabled state: {e}")
            return False

    def rename_selected_node(self) -> bool:
        """
        Start rename mode for the first selected node.

        Only works when exactly one node is selected.

        Returns:
            True if rename mode was started, False otherwise
        """
        try:
            selected = self._graph.selected_nodes()
            if len(selected) != 1:
                if len(selected) > 1:
                    logger.debug("Cannot rename: multiple nodes selected")
                return False

            node = selected[0]
            view = node.view

            if view and hasattr(view, "_text_item"):
                text_item = view._text_item
                if hasattr(text_item, "set_editable"):
                    text_item.set_editable(True)
                    text_item.setFocus()
                    logger.debug(f"Started rename mode for node: {node.name()}")
                    return True

            logger.debug("Node does not support inline rename")
            return False
        except Exception as e:
            logger.error(f"Failed to start node rename: {e}")
            return False

    def create_subflow_from_selection(self, widget) -> bool:
        """
        Create a subflow from the currently selected nodes.

        Args:
            widget: The NodeGraphWidget instance (for action context)

        Returns:
            True if subflow was created, False otherwise
        """
        try:
            selected = self._graph.selected_nodes()
            if len(selected) < 2:
                logger.debug("Create Subflow: Need at least 2 nodes selected")
                return False

            from casare_rpa.presentation.canvas.actions.create_subflow import (
                CreateSubflowAction,
            )

            action = CreateSubflowAction(widget, widget)
            subflow_node = action.execute(selected)

            if subflow_node:
                logger.info(f"Created subflow from {len(selected)} nodes")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to create subflow: {e}")
            return False

    def get_node_at_view_pos(self, view_pos):
        """
        Get node at given view coordinates.

        Args:
            view_pos: Position in view coordinates (QPoint or QPointF)

        Returns:
            Node object if found, None otherwise
        """
        try:
            from NodeGraphQt.qgraphics.node_base import NodeItem

            viewer = self._graph.viewer()
            scene_pos = viewer.mapToScene(
                view_pos.toPoint() if hasattr(view_pos, "toPoint") else view_pos
            )
            item = viewer.scene().itemAt(scene_pos, viewer.transform())

            if not item:
                return None

            current = item
            while current:
                if isinstance(current, NodeItem):
                    for node in self._graph.all_nodes():
                        if hasattr(node, "view") and node.view == current:
                            return node
                    break
                current = current.parentItem()

            return None
        except Exception as e:
            logger.debug(f"Error getting node at position: {e}")
            return None
