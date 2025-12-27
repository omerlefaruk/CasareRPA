"""
Node Quick Actions for CasareRPA.

Provides a context menu with quick actions when right-clicking on nodes.
"""

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS

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
    create_subflow_requested = Signal()  # Create subflow from selection
    toggle_cache_requested = Signal(str)  # Toggle cache on node (node_id)

    def __init__(self, graph: "NodeGraph", parent: QObject | None = None) -> None:
        """
        Initialize the quick actions manager.

        Args:
            graph: The NodeGraph instance
            parent: Optional parent object
        """
        super().__init__(parent)
        self._graph = graph
        self._auto_connect_manager = None  # Will be set by NodeGraphWidget

        self._setup_context_menu()

    def set_auto_connect_manager(self, manager) -> None:
        """
        Set reference to AutoConnectManager for drag state checking.

        Args:
            manager: The AutoConnectManager instance
        """
        self._auto_connect_manager = manager

    def _setup_context_menu(self) -> None:
        """Setup node context menu.

        Node context menus are invoked explicitly by `NodeGraphWidget` so we don't
        install a viewport event filter here (keeps mouse behavior centralized).
        """
        return

    def _get_node_at_pos(self, pos: QPointF):
        """
        Get the node at the given scene position.

        Args:
            pos: Position in view coordinates

        Returns:
            Node object if found, None otherwise
        """
        try:
            viewer = self._graph.viewer()
            # Convert view pos to scene pos
            scene_pos = viewer.mapToScene(pos.toPoint())

            # Get item at position
            item = viewer.scene().itemAt(scene_pos, viewer.transform())
            if not item:
                return None

            # Check if item is a node or part of a node
            # NodeGraphQt nodes have a specific structure
            from NodeGraphQt.qgraphics.node_base import NodeItem

            # Walk up the parent chain to find a NodeItem
            current = item
            while current:
                if isinstance(current, NodeItem):
                    # Found a node item, get the actual node object
                    for node in self._graph.all_nodes():
                        if hasattr(node, "view") and node.view == current:
                            return node
                    break
                current = current.parentItem()

            return None
        except Exception as e:
            logger.debug(f"Error getting node at position: {e}")
            return None

    def eventFilter(self, obj, event) -> bool:
        """
        Event filter to intercept right-clicks on nodes.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            True if event was handled, False otherwise
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                # If auto-connect is in drag mode, let it handle the RMB event
                # for connection confirmation
                if self._auto_connect_manager and self._auto_connect_manager._dragging_node:
                    return False  # Pass through to AutoConnectManager

                # Check if click is directly on a node
                node = self._get_node_at_pos(event.position())
                if node:
                    # Right-click on nodes is disabled - just consume the event
                    return True

        return False  # Let other events pass through (including canvas right-clicks)

    def show_context_menu(self, global_pos) -> None:
        """Show quick actions for current selection."""
        self._show_node_context_menu(global_pos)

    def _show_node_context_menu(self, pos) -> None:
        """
        Show the node context menu at the given position.

        Args:
            pos: Global position for the menu
        """
        menu = QMenu()
        menu.setStyleSheet(Theme.context_menu_style())

        # === Execution Actions ===
        run_node_action = menu.addAction("Run This Node (F5)")
        run_node_action.triggered.connect(self._on_run_node)

        run_to_action = menu.addAction("Run To Here (F4)")
        run_to_action.triggered.connect(self._on_run_to_node)

        menu.addSeparator()

        # === Edit Actions ===
        copy_action = menu.addAction("Copy (Ctrl+C)")
        copy_action.triggered.connect(self._on_copy)

        duplicate_action = menu.addAction("Duplicate (Ctrl+D)")
        duplicate_action.triggered.connect(self._on_duplicate)

        delete_action = menu.addAction("Delete (X)")
        delete_action.triggered.connect(self._on_delete)

        menu.addSeparator()

        # === Node Actions ===
        rename_action = menu.addAction("Rename (F2)")
        rename_action.triggered.connect(self._on_rename)

        center_action = menu.addAction("Center in View")
        center_action.triggered.connect(self._on_center_view)

        menu.addSeparator()

        # === Subflow Actions ===
        selected = self._graph.selected_nodes()
        if len(selected) >= 2:
            create_subflow_action = menu.addAction("Create Subflow (Ctrl+G)")
            create_subflow_action.triggered.connect(self._on_create_subflow)
            menu.addSeparator()

        # === Cache Actions ===
        cache_enabled = self._is_node_cache_enabled()
        cache_text = "⚡ Disable Cache" if cache_enabled else "⚡ Enable Cache (Ctrl+K)"
        toggle_cache_action = menu.addAction(cache_text)
        toggle_cache_action.triggered.connect(self._on_toggle_cache)

        menu.addSeparator()

        # === Info Actions ===
        copy_id_action = menu.addAction("Copy Node ID")
        copy_id_action.triggered.connect(self._on_copy_node_id)

        # Show the menu
        menu.exec(pos)

    def _get_selected_node_id(self) -> str | None:
        """Get the ID of the first selected node."""
        selected = self._graph.selected_nodes()
        if selected:
            node = selected[0]
            return node.get_property("node_id") or node.id()
        return None

    @Slot(bool)
    def _on_run_node(self, checked: bool = False) -> None:
        """Handle run node action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Run node {node_id}")
            self.run_node_requested.emit(node_id)

    @Slot(bool)
    def _on_run_to_node(self, checked: bool = False) -> None:
        """Handle run to node action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Run to node {node_id}")
            self.run_to_node_requested.emit(node_id)

    @Slot(bool)
    def _on_copy(self, checked: bool = False) -> None:
        """Handle copy action."""
        logger.debug("Quick action: Copy")
        self.copy_requested.emit()

    @Slot(bool)
    def _on_duplicate(self, checked: bool = False) -> None:
        """Handle duplicate action."""
        logger.debug("Quick action: Duplicate")
        self.duplicate_requested.emit()

    @Slot(bool)
    def _on_delete(self, checked: bool = False) -> None:
        """Handle delete action."""
        logger.debug("Quick action: Delete")
        self.delete_requested.emit()

    @Slot(bool)
    def _on_rename(self, checked: bool = False) -> None:
        """Handle rename action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Rename node {node_id}")
            self.rename_requested.emit(node_id)
            # Trigger rename dialog
            self._show_rename_dialog()

    def _show_rename_dialog(self) -> None:
        """Show dialog to rename the selected node."""
        selected = self._graph.selected_nodes()
        if not selected:
            return

        node = selected[0]
        current_name = node.name() if hasattr(node, "name") else "Node"

        # Get the main window as parent for the dialog
        viewer = self._graph.viewer()

        new_name, ok = QInputDialog.getText(
            viewer, "Rename Node", "Enter new name:", text=current_name
        )

        if ok and new_name and new_name != current_name:
            node.set_name(new_name)
            logger.info(f"Renamed node to: {new_name}")

    @Slot(bool)
    def _on_center_view(self, checked: bool = False) -> None:
        """Handle center view action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Center on node {node_id}")
            self.center_view_requested.emit(node_id)
            # Center view on selected nodes
            self._graph.fit_to_selection()

    @Slot(bool)
    def _on_copy_node_id(self, checked: bool = False) -> None:
        """Copy the node ID to clipboard."""
        node_id = self._get_selected_node_id()
        if node_id:
            clipboard = QApplication.clipboard()
            clipboard.setText(node_id)
            logger.debug(f"Copied node ID to clipboard: {node_id}")

    @Slot(bool)
    def _on_create_subflow(self, checked: bool = False) -> None:
        """Handle create subflow action."""
        logger.debug("Quick action: Create Subflow")
        self.create_subflow_requested.emit()

    def _is_node_cache_enabled(self) -> bool:
        """Check if the selected node has cache enabled."""
        selected = self._graph.selected_nodes()
        if not selected:
            return False
        node = selected[0]
        # Get the graphics item to check cache state
        view = node.view
        if view and hasattr(view, "is_cache_enabled"):
            return view.is_cache_enabled()
        return False

    @Slot(bool)
    def _on_toggle_cache(self, checked: bool = False) -> None:
        """Handle toggle cache action."""
        node_id = self._get_selected_node_id()
        if node_id:
            logger.debug(f"Quick action: Toggle cache on node {node_id}")
            self.toggle_cache_requested.emit(node_id)


def setup_node_quick_actions(graph: "NodeGraph") -> NodeQuickActions:
    """
    Setup quick actions for a node graph.

    Args:
        graph: The NodeGraph instance

    Returns:
        NodeQuickActions manager instance
    """
    return NodeQuickActions(graph)
