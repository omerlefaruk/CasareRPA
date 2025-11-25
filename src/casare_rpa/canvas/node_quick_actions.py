"""
Node Quick Actions for CasareRPA.

Provides a context menu with quick actions when right-clicking on nodes.
"""

from typing import TYPE_CHECKING, Optional, Callable
from PySide6.QtWidgets import QMenu, QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class NodeQuickActions(QObject):
    """
    Manages quick actions context menu for nodes.

    Provides common operations like run, duplicate, delete, copy
    when right-clicking on nodes in the canvas.

    Signals:
        run_node_requested: Emitted when user wants to run a node (node_id)
        run_to_node_requested: Emitted when user wants to run to a node (node_id)
        duplicate_requested: Emitted when user wants to duplicate nodes
        delete_requested: Emitted when user wants to delete nodes
        rename_requested: Emitted when user wants to rename a node (node_id)
        copy_requested: Emitted when user wants to copy nodes
        paste_requested: Emitted when user wants to paste nodes
        center_view_requested: Emitted when user wants to center on node (node_id)
    """

    run_node_requested = Signal(str)
    run_to_node_requested = Signal(str)
    duplicate_requested = Signal()
    delete_requested = Signal()
    rename_requested = Signal(str)
    copy_requested = Signal()
    paste_requested = Signal()
    center_view_requested = Signal(str)

    def __init__(self, graph: 'NodeGraph', parent: Optional[QObject] = None) -> None:
        """
        Initialize the quick actions manager.

        Args:
            graph: The NodeGraph instance
            parent: Optional parent object
        """
        super().__init__(parent)
        self._graph = graph
        self._setup_context_menu()

    def _setup_context_menu(self) -> None:
        """Setup the node context menu."""
        # Get or create the nodes context menu
        try:
            # NodeGraphQt has a context menu system
            # We need to add our custom menu items to the "nodes" context menu
            nodes_menu = self._graph.get_context_menu("nodes")
            if nodes_menu:
                self._add_quick_actions_to_menu(nodes_menu.qmenu)
                logger.debug("Quick actions added to existing nodes context menu")
            else:
                # Create new nodes context menu
                nodes_menu = self._graph.set_context_menu_from_file(None, "nodes")
                if nodes_menu:
                    self._add_quick_actions_to_menu(nodes_menu.qmenu)
                    logger.debug("Quick actions added to new nodes context menu")
        except Exception as e:
            logger.warning(f"Could not setup node context menu: {e}")
            # Fallback: connect to the viewer's context menu event
            self._setup_fallback_menu()

    def _setup_fallback_menu(self) -> None:
        """Setup fallback context menu handling."""
        # Install event filter on viewer to intercept right-clicks on nodes
        viewer = self._graph.viewer()
        viewer.setContextMenuPolicy(viewer.contextMenuPolicy())
        logger.debug("Using fallback context menu approach")

    def _add_quick_actions_to_menu(self, menu: QMenu) -> None:
        """
        Add quick action items to the context menu.

        Args:
            menu: The QMenu to add actions to
        """
        # Clear existing items and add our custom ones
        menu.clear()

        # === Execution Actions ===
        run_node_action = QAction("▶ Run This Node (F5)", menu)
        run_node_action.triggered.connect(self._on_run_node)
        menu.addAction(run_node_action)

        run_to_action = QAction("▷ Run To Here (F4)", menu)
        run_to_action.triggered.connect(self._on_run_to_node)
        menu.addAction(run_to_action)

        menu.addSeparator()

        # === Edit Actions ===
        copy_action = QAction("Copy (Ctrl+C)", menu)
        copy_action.triggered.connect(self._on_copy)
        menu.addAction(copy_action)

        duplicate_action = QAction("Duplicate (Ctrl+D)", menu)
        duplicate_action.triggered.connect(self._on_duplicate)
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete (X)", menu)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.addSeparator()

        # === Node Actions ===
        rename_action = QAction("Rename (F2)", menu)
        rename_action.triggered.connect(self._on_rename)
        menu.addAction(rename_action)

        center_action = QAction("Center in View", menu)
        center_action.triggered.connect(self._on_center_view)
        menu.addAction(center_action)

        menu.addSeparator()

        # === Info Actions ===
        copy_id_action = QAction("Copy Node ID", menu)
        copy_id_action.triggered.connect(self._on_copy_node_id)
        menu.addAction(copy_id_action)

        properties_action = QAction("Show Properties", menu)
        properties_action.triggered.connect(self._on_show_properties)
        menu.addAction(properties_action)

    def _get_selected_node_id(self) -> Optional[str]:
        """Get the ID of the first selected node."""
        selected = self._graph.selected_nodes()
        if selected:
            node = selected[0]
            return node.get_property("node_id") or node.id()
        return None

    def _on_run_node(self) -> None:
        """Handle run node action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Run node {node_id}")
            self.run_node_requested.emit(node_id)

    def _on_run_to_node(self) -> None:
        """Handle run to node action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Run to node {node_id}")
            self.run_to_node_requested.emit(node_id)

    def _on_copy(self) -> None:
        """Handle copy action."""
        logger.debug("Quick action: Copy")
        self.copy_requested.emit()

    def _on_duplicate(self) -> None:
        """Handle duplicate action."""
        logger.debug("Quick action: Duplicate")
        self.duplicate_requested.emit()

    def _on_delete(self) -> None:
        """Handle delete action."""
        logger.debug("Quick action: Delete")
        self.delete_requested.emit()

    def _on_rename(self) -> None:
        """Handle rename action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Rename node {node_id}")
            self.rename_requested.emit(node_id)
            # Trigger rename dialog
            self._show_rename_dialog()

    def _show_rename_dialog(self) -> None:
        """Show dialog to rename the selected node."""
        from PySide6.QtWidgets import QInputDialog

        selected = self._graph.selected_nodes()
        if not selected:
            return

        node = selected[0]
        current_name = node.name() if hasattr(node, 'name') else "Node"

        # Get the main window as parent for the dialog
        viewer = self._graph.viewer()

        new_name, ok = QInputDialog.getText(
            viewer,
            "Rename Node",
            "Enter new name:",
            text=current_name
        )

        if ok and new_name and new_name != current_name:
            node.set_name(new_name)
            logger.info(f"Renamed node to: {new_name}")

    def _on_center_view(self) -> None:
        """Handle center view action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Center on node {node_id}")
            self.center_view_requested.emit(node_id)
            # Center view on selected nodes
            self._graph.fit_to_selection()

    def _on_copy_node_id(self) -> None:
        """Copy the node ID to clipboard."""
        node_id = self._get_selected_node_id()
        if node_id:
            clipboard = QApplication.clipboard()
            clipboard.setText(node_id)
            logger.debug(f"Copied node ID to clipboard: {node_id}")

    def _on_show_properties(self) -> None:
        """Show the properties panel for the selected node."""
        # This will be handled by the main window
        selected = self._graph.selected_nodes()
        if selected:
            # Trigger node selection signal to update properties panel
            # The main window should already handle this via node_selected signal
            logger.debug("Quick action: Show properties")


def setup_node_quick_actions(graph: 'NodeGraph') -> NodeQuickActions:
    """
    Setup quick actions for a node graph.

    Args:
        graph: The NodeGraph instance

    Returns:
        NodeQuickActions manager instance
    """
    return NodeQuickActions(graph)
