"""
Graph event handling module for NodeGraphWidget.

Extracts event filtering and keyboard/mouse handling from NodeGraphWidget.
Handles:
- Qt event filtering for the graph viewer
- Keyboard shortcuts (Tab, Delete, X, Ctrl+D, Ctrl+E, F1, F2, V, C, Escape)
- Mouse events (Alt+drag duplicate, right-click context menu)
- Drag-drop operations (node library, workflow files, variables)
- Chain selection (Shift+Click, Ctrl+Shift+Click)
"""

from typing import TYPE_CHECKING, Optional, Callable

from PySide6.QtCore import QEvent, Qt, QObject
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit

from loguru import logger

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph
    from casare_rpa.presentation.canvas.graph.node_selection_handler import (
        NodeSelectionHandler,
    )


class GraphEventHandler(QObject):
    """
    Handles event filtering and dispatch for the node graph widget.

    Extracted from NodeGraphWidget to improve code organization.
    """

    def __init__(
        self,
        graph: "NodeGraph",
        selection_handler: "NodeSelectionHandler",
        parent: Optional[QObject] = None,
    ):
        """
        Initialize graph event handler.

        Args:
            graph: The NodeGraph instance
            selection_handler: The node selection handler
            parent: Parent QObject
        """
        super().__init__(parent)
        self._graph = graph
        self._selection_handler = selection_handler

        # Alt+drag state tracking
        self._alt_drag_node = None
        self._alt_drag_offset_x = 0.0
        self._alt_drag_offset_y = 0.0

        # Callbacks for actions
        self._on_tab_pressed: Optional[Callable] = None
        self._on_escape_pressed: Optional[Callable] = None
        self._on_delete_frames: Optional[Callable] = None
        self._on_toggle_port_legend: Optional[Callable] = None
        self._on_subflow_dive_in: Optional[Callable] = None
        self._on_subflow_go_back: Optional[Callable] = None
        self._on_close_output_popup: Optional[Callable] = None

    def set_callbacks(
        self,
        on_tab: Callable = None,
        on_escape: Callable = None,
        on_delete_frames: Callable = None,
        on_toggle_port_legend: Callable = None,
        on_subflow_dive_in: Callable = None,
        on_subflow_go_back: Callable = None,
        on_close_output_popup: Callable = None,
    ) -> None:
        """
        Set callback functions for various events.

        Args:
            on_tab: Called when Tab key is pressed
            on_escape: Called when Escape key is pressed
            on_delete_frames: Called to delete selected frames
            on_toggle_port_legend: Called to toggle port legend
            on_subflow_dive_in: Called when V key pressed (dive into subflow)
            on_subflow_go_back: Called when C key pressed (go back from subflow)
            on_close_output_popup: Called to close output popup
        """
        self._on_tab_pressed = on_tab
        self._on_escape_pressed = on_escape
        self._on_delete_frames = on_delete_frames
        self._on_toggle_port_legend = on_toggle_port_legend
        self._on_subflow_dive_in = on_subflow_dive_in
        self._on_subflow_go_back = on_subflow_go_back
        self._on_close_output_popup = on_close_output_popup

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Event filter to capture keyboard and mouse events.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            True if event was handled, False otherwise
        """
        event_type = event.type()

        # Handle drag events
        if event_type == QEvent.Type.DragEnter:
            return False  # Let parent handle
        elif event_type == QEvent.Type.DragMove:
            return False
        elif event_type == QEvent.Type.Drop:
            return False

        # Clear focus from text widgets when entering canvas
        if event_type == QEvent.Type.Enter:
            self._handle_enter_event()

        # Handle mouse button press
        if event_type == QEvent.Type.MouseButtonPress:
            result = self._handle_mouse_press(event)
            if result:
                return True

        # Handle mouse button release
        if event_type == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self._alt_drag_node:
                self._alt_drag_node = None

        # Handle mouse move for Alt+drag
        if event_type == QEvent.Type.MouseMove:
            if self._alt_drag_node:
                self._handle_alt_drag_move(event)
                return True

        # Handle key press
        if event_type == QEvent.Type.KeyPress:
            result = self._handle_key_press(event)
            if result:
                return True

        return False

    def _handle_enter_event(self) -> None:
        """Clear focus from canvas-embedded text widgets when entering canvas."""
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, (QLineEdit, QTextEdit)):
            parent = focus_widget.parent()
            while parent:
                if hasattr(parent, "scene") and callable(parent.scene):
                    focus_widget.clearFocus()
                    break
                parent = getattr(parent, "parent", lambda: None)()

    def _handle_mouse_press(self, event) -> bool:
        """
        Handle mouse button press events.

        Args:
            event: The mouse press event

        Returns:
            True if event was handled
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Close output popup if clicking outside
            if self._on_close_output_popup:
                self._on_close_output_popup()

            modifiers = event.modifiers()

            # Ctrl+Shift+LMB: Select entire chain (upstream + downstream)
            if (modifiers & Qt.KeyboardModifier.ControlModifier) and (
                modifiers & Qt.KeyboardModifier.ShiftModifier
            ):
                if self._handle_chain_selection(event, full_chain=True):
                    return True

            # Shift+LMB: Select downstream chain only
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                if self._handle_chain_selection(event, full_chain=False):
                    return True

            # Alt+LMB: Houdini-style drag duplicate
            elif modifiers & Qt.KeyboardModifier.AltModifier:
                if self._handle_alt_drag_duplicate(event):
                    return True

        if event.button() == Qt.MouseButton.RightButton:
            return self._handle_right_click(event)

        return False

    def _handle_chain_selection(self, event, full_chain: bool = False) -> bool:
        """
        Handle chain selection (Shift+Click or Ctrl+Shift+Click).

        Selects connected nodes based on the logical flow:
        - Shift+Click: Select downstream chain (nodes that depend on clicked node)
        - Ctrl+Shift+Click: Select full chain (upstream + downstream)

        Args:
            event: The mouse event
            full_chain: If True, select upstream + downstream. If False, downstream only.

        Returns:
            True if chain selection was performed
        """
        try:
            viewer = self._graph.viewer()
            view_pos = event.position().toPoint()
            scene_pos = viewer.mapToScene(view_pos)

            # Find node at click position
            item = viewer.scene().itemAt(scene_pos, viewer.transform())
            if not item:
                return False

            # Walk up parent chain to find NodeItem
            from NodeGraphQt.qgraphics.node_base import NodeItem

            node_item = None
            current = item
            while current:
                if isinstance(current, NodeItem):
                    node_item = current
                    break
                current = current.parentItem()

            if not node_item:
                return False

            # Find the actual node object
            clicked_node = None
            for node in self._graph.all_nodes():
                if hasattr(node, "view") and node.view == node_item:
                    clicked_node = node
                    break

            if not clicked_node:
                return False

            # Perform chain selection
            if full_chain:
                chain = self._chain_selector.select_full_chain(clicked_node)
                logger.info(f"Selected full chain: {len(chain)} nodes")
            else:
                chain = self._chain_selector.select_downstream_chain(clicked_node)
                logger.info(f"Selected downstream chain: {len(chain)} nodes")

            return len(chain) > 0

        except Exception as e:
            logger.debug(f"Chain selection error: {e}")
            return False

    def _handle_right_click(self, event) -> bool:
        """
        Handle right-click for context menu and connection cancellation.

        Args:
            event: The mouse event

        Returns:
            True if event was handled
        """
        viewer = self._graph.viewer()

        # Cancel live connection on right-click
        if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
            viewer.end_live_connection()
            logger.debug("Right-click - cancelled live connection")
            return True

        # Capture position for context menu
        if hasattr(event, "globalPos"):
            global_pos = event.globalPos()
        else:
            global_pos = event.globalPosition().toPoint()
        scene_pos = viewer.mapToScene(viewer.mapFromGlobal(global_pos))

        context_menu = self._graph.get_context_menu("graph")
        if context_menu and context_menu.qmenu:
            context_menu.qmenu._initial_scene_pos = scene_pos

        return False  # Let event propagate to show menu

    def _handle_key_press(self, event) -> bool:
        """
        Handle keyboard shortcuts.

        Args:
            event: The key press event

        Returns:
            True if event was handled
        """
        key = event.key()
        modifiers = event.modifiers()

        # Tab - show context menu
        if key == Qt.Key.Key_Tab:
            if self._on_tab_pressed:
                self._on_tab_pressed()
            return True

        # Escape - cancel live connection
        if key == Qt.Key.Key_Escape:
            if self._on_escape_pressed:
                return self._on_escape_pressed()
            return False

        # Delete or X - delete selection
        # Skip X key if focus is on a text input widget (allow typing 'x')
        focus_widget = QApplication.focusWidget()
        text_has_focus = isinstance(focus_widget, (QLineEdit, QTextEdit))

        if key == Qt.Key.Key_Delete:
            if self._on_delete_frames and self._on_delete_frames():
                return True
            if self._selection_handler.delete_selected_nodes():
                return True
        elif not text_has_focus and (key == Qt.Key.Key_X or event.text().lower() == "x"):
            if self._on_delete_frames and self._on_delete_frames():
                return True
            if self._selection_handler.delete_selected_nodes():
                return True

        # Ctrl+D - duplicate
        if key == Qt.Key.Key_D and modifiers == Qt.KeyboardModifier.ControlModifier:
            if self._selection_handler.duplicate_selected_nodes():
                return True

        # Ctrl+E - toggle enabled
        if key == Qt.Key.Key_E and modifiers == Qt.KeyboardModifier.ControlModifier:
            if self._selection_handler.toggle_selected_nodes_enabled():
                return True

        # F2 - rename
        if key == Qt.Key.Key_F2:
            if self._selection_handler.rename_selected_node():
                return True

        # F1 - toggle port legend
        if key == Qt.Key.Key_F1:
            if self._on_toggle_port_legend:
                self._on_toggle_port_legend()
            return True

        # Ctrl+G - create subflow
        if key == Qt.Key.Key_G and modifiers == Qt.KeyboardModifier.ControlModifier:
            # Handled by parent widget
            return False

        # V - dive into subflow
        if key == Qt.Key.Key_V and not modifiers:
            if self._on_subflow_dive_in and self._on_subflow_dive_in():
                return True

        # C - go back from subflow
        if key == Qt.Key.Key_C and not modifiers:
            if self._on_subflow_go_back and self._on_subflow_go_back():
                return True

        return False

    def _handle_alt_drag_duplicate(self, event) -> bool:
        """
        Handle Alt+LMB drag to duplicate node under cursor.

        Args:
            event: Mouse press event

        Returns:
            True if handled
        """
        try:
            viewer = self._graph.viewer()
            view_pos = viewer.mapFromGlobal(event.globalPosition().toPoint())
            node = self._selection_handler.get_node_at_view_pos(view_pos)

            if not node:
                return False

            scene_pos = viewer.mapToScene(view_pos)
            orig_x, orig_y = node.pos()

            # Duplicate the node
            self._graph.copy_nodes([node])
            self._graph.paste_nodes()

            # Find the duplicate
            selected = self._graph.selected_nodes()
            new_node = None
            for n in selected:
                if n != node:
                    new_node = n
                    break

            if not new_node:
                for n in self._graph.all_nodes():
                    if n != node and hasattr(n, "view"):
                        nx, ny = n.pos()
                        if abs(nx - orig_x) < 150 and abs(ny - orig_y) < 150:
                            new_node = n
                            break

            if not new_node:
                return False

            # Set up drag state
            self._alt_drag_offset_x = scene_pos.x() - orig_x
            self._alt_drag_offset_y = scene_pos.y() - orig_y
            self._alt_drag_node = new_node

            # Position and select the duplicate
            new_node.set_pos(
                scene_pos.x() - self._alt_drag_offset_x,
                scene_pos.y() - self._alt_drag_offset_y,
            )

            view_item = new_node.view
            if view_item:
                view_item.setZValue(view_item.zValue() + 1000)
                view_item.prepareGeometryChange()
                view_item.update()

            self._graph.clear_selection()
            new_node.set_selected(True)
            if view_item:
                view_item.setSelected(True)

            logger.debug(f"Alt+drag duplicated node: {node.name()} -> {new_node.name()}")
            return True

        except Exception as e:
            logger.error(f"Alt+drag duplicate failed: {e}")
            return False

    def _handle_alt_drag_move(self, event) -> bool:
        """
        Update position of Alt+drag duplicate node during mouse move.

        Args:
            event: Mouse move event

        Returns:
            True if handled
        """
        if not self._alt_drag_node:
            return False

        try:
            viewer = self._graph.viewer()
            view_pos = viewer.mapFromGlobal(event.globalPosition().toPoint())
            scene_pos = viewer.mapToScene(view_pos)

            self._alt_drag_node.set_pos(
                scene_pos.x() - self._alt_drag_offset_x,
                scene_pos.y() - self._alt_drag_offset_y,
            )
            return True
        except Exception as e:
            logger.debug(f"Alt+drag move error: {e}")
            return False

    @property
    def alt_drag_node(self):
        """Get the currently Alt+dragged node."""
        return self._alt_drag_node

    @alt_drag_node.setter
    def alt_drag_node(self, value):
        """Set the Alt+dragged node."""
        self._alt_drag_node = value

    @property
    def alt_drag_offset_x(self) -> float:
        """Get Alt+drag X offset."""
        return self._alt_drag_offset_x

    @property
    def alt_drag_offset_y(self) -> float:
        """Get Alt+drag Y offset."""
        return self._alt_drag_offset_y
