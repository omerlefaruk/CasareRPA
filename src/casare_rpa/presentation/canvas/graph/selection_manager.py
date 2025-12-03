"""
Selection Manager for CasareRPA Canvas.

Handles all node and frame selection operations for the node graph widget.
Follows Single Responsibility Principle - manages selection state only.
"""

from typing import List, Optional, TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class SelectionManager(QObject):
    """
    Manages selection operations for the node graph.

    Provides a clean interface for:
    - Selecting/deselecting nodes
    - Multi-selection handling
    - Frame selection
    - Selection queries

    Usage:
        manager = SelectionManager(graph)
        manager.select_nodes([node1, node2])
        selected = manager.get_selected_nodes()
    """

    # Signals
    selection_changed = Signal(list)  # Emits list of selected node IDs
    frame_selected = Signal(str)  # Emits frame title when selected
    frame_deselected = Signal(str)  # Emits frame title when deselected

    def __init__(self, graph: "NodeGraph", parent: Optional[QObject] = None) -> None:
        """
        Initialize selection manager.

        Args:
            graph: The NodeGraphQt NodeGraph instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph

    @property
    def graph(self) -> "NodeGraph":
        """Get the underlying graph."""
        return self._graph

    def get_selected_nodes(self) -> List:
        """
        Get the currently selected nodes.

        Returns:
            List of selected node objects
        """
        return self._graph.selected_nodes()

    def get_selected_node_ids(self) -> List[str]:
        """
        Get IDs of currently selected nodes.

        Returns:
            List of selected node IDs
        """
        selected = self._graph.selected_nodes()
        ids = []
        for node in selected:
            node_id = node.get_property("node_id")
            if node_id:
                ids.append(node_id)
        return ids

    def clear_selection(self) -> None:
        """Clear all node and frame selection."""
        self._graph.clear_selection()

    def select_node(self, node) -> None:
        """
        Select a single node, clearing other selections.

        Args:
            node: The node to select
        """
        self._graph.clear_selection()
        if node:
            node.set_selected(True)

    def select_nodes(self, nodes: List) -> None:
        """
        Select multiple nodes.

        Args:
            nodes: List of nodes to select
        """
        self._graph.clear_selection()
        for node in nodes:
            if node:
                node.set_selected(True)

    def add_to_selection(self, node) -> None:
        """
        Add a node to the current selection without clearing.

        Args:
            node: The node to add to selection
        """
        if node:
            node.set_selected(True)

    def remove_from_selection(self, node) -> None:
        """
        Remove a node from the current selection.

        Args:
            node: The node to remove from selection
        """
        if node:
            node.set_selected(False)

    def toggle_selection(self, node) -> None:
        """
        Toggle selection state of a node.

        Args:
            node: The node to toggle
        """
        if node:
            node.set_selected(not node.selected())

    def select_all(self) -> None:
        """Select all nodes in the graph."""
        for node in self._graph.all_nodes():
            node.set_selected(True)

    def is_selected(self, node) -> bool:
        """
        Check if a node is selected.

        Args:
            node: The node to check

        Returns:
            True if node is selected
        """
        return node.selected() if node else False

    def get_selection_count(self) -> int:
        """
        Get the number of selected nodes.

        Returns:
            Number of selected nodes
        """
        return len(self._graph.selected_nodes())

    def has_selection(self) -> bool:
        """
        Check if any nodes are selected.

        Returns:
            True if at least one node is selected
        """
        return len(self._graph.selected_nodes()) > 0

    def delete_selected_frames(self) -> bool:
        """
        Delete any selected frames in the scene.

        Returns:
            True if any frames were deleted, False otherwise
        """
        from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame

        viewer = self._graph.viewer()
        if not viewer:
            return False

        scene = viewer.scene()
        if not scene:
            return False

        deleted_any = False

        # Find and delete selected frames
        for item in scene.selectedItems():
            if isinstance(item, NodeFrame):
                logger.info(f"Deleting selected frame: {item.frame_title}")
                self.frame_deselected.emit(item.frame_title)
                item._delete_frame()
                deleted_any = True

        return deleted_any

    def get_selected_frames(self) -> List:
        """
        Get all selected frames.

        Returns:
            List of selected NodeFrame items
        """
        from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame

        viewer = self._graph.viewer()
        if not viewer:
            return []

        scene = viewer.scene()
        if not scene:
            return []

        frames = []
        for item in scene.selectedItems():
            if isinstance(item, NodeFrame):
                frames.append(item)

        return frames

    def select_nodes_in_frame(self, frame) -> None:
        """
        Select all nodes contained within a frame.

        Args:
            frame: The NodeFrame to get nodes from
        """
        if hasattr(frame, "get_nodes"):
            nodes = frame.get_nodes()
            self.select_nodes(nodes)

    def center_on_selection(self) -> None:
        """Center the view on the currently selected nodes."""
        selected = self._graph.selected_nodes()
        if selected:
            self._graph.center_on(selected)

    def fit_to_selection(self) -> None:
        """Fit the view to show all selected nodes."""
        self._graph.fit_to_selection()
