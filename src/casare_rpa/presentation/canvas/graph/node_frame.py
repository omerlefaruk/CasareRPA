"""
Node Frame/Group System

Allows users to create visual frames around groups of nodes for organization.

Rendering logic delegated to specialized renderer modules:
- style_manager.py: Color palettes and styling
- collapse_components.py: Collapse button and port indicators
- frame_renderer.py: Paint logic
- frame_managers.py: Bounds manager and undo commands
- frame_factory.py: Factory functions

References:
- "Designing Data-Intensive Applications" - Resource pooling
"""

from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QInputDialog,
    QMenu,
)

# Re-export collapse components for backward compatibility
from casare_rpa.presentation.canvas.graph.collapse_components import (  # noqa: F401
    CollapseButton,
    ExposedPortIndicator,
    ExposedPortManager,
)

# Re-export for backward compatibility
from casare_rpa.presentation.canvas.graph.frame_factory import (  # noqa: F401
    FrameNode,
    add_frame_menu_actions,
    create_frame,
    group_selected_nodes,
)
from casare_rpa.presentation.canvas.graph.frame_managers import (
    FrameBoundsManager,
    FrameDeletedCmd,
)
from casare_rpa.presentation.canvas.graph.frame_renderer import (
    FrameRenderer,
    TitleRenderer,
)

# Import from extracted modules
from casare_rpa.presentation.canvas.graph.style_manager import (
    DEFAULT_FRAME_COLOR,
    FRAME_COLOR_PALETTE,
    FRAME_COLORS,
    FrameStyleManager,
)

__all__ = [
    "NodeFrame",
    "FrameNode",
    "FrameBoundsManager",
    "FrameDeletedCmd",
    "FRAME_COLOR_PALETTE",
    "FRAME_COLORS",
    "create_frame",
    "group_selected_nodes",
    "add_frame_menu_actions",
]


class NodeFrame(QGraphicsRectItem):
    """
    A visual frame/backdrop for grouping nodes.

    Features:
    - Resizable colored rectangle
    - Editable title label (double-click to edit)
    - Multiple color themes
    - Nodes can be grouped within the frame
    - Collapsible to hide internal nodes
    """

    COLLAPSED_WIDTH = 200
    COLLAPSED_HEIGHT = 50

    _graph_ref = None

    @classmethod
    def set_graph(cls, graph):
        """Set the graph reference for all frames to use for node lookup."""
        cls._graph_ref = graph

    def __init__(
        self,
        title: str = "Group",
        color: QColor = None,
        width: float = 400,
        height: float = 300,
        parent=None,
    ):
        super().__init__(parent)

        self.frame_title = title
        self.frame_color = color or DEFAULT_FRAME_COLOR
        self.contained_nodes = []
        self._is_moving = False
        self._old_pos = QPointF(0, 0)
        self._is_drop_target = False
        self._last_overlap_check = {}
        self._resize_handle_size = 12
        self._resizing = False
        self._resize_corner = None
        self._resize_start_pos = None
        self._resize_start_rect = None

        # Collapse state
        self._is_collapsed = False
        self._expanded_rect = QRectF(0, 0, width, height)
        self._hidden_node_views: list[Any] = []
        self._hidden_pipes: set[Any] = set()

        # Delegated components
        self._renderer = FrameRenderer(self)
        self._port_manager = ExposedPortManager(self)

        # Configure graphics item
        self.setRect(0, 0, width, height)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
            | QGraphicsItem.GraphicsItemFlag.ItemAcceptsInputMethod
        )
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setZValue(-10)

        # Initialize visual components
        self._apply_style()
        self._create_title_label()
        self._collapse_button = CollapseButton(self)

        # Register with bounds manager
        self._bounds_manager = FrameBoundsManager.get_instance()
        self._bounds_manager.register_frame(self)

    # =========================================================================
    # STYLING
    # =========================================================================

    def _apply_style(self):
        """Apply visual styling to the frame."""
        self.setBrush(FrameStyleManager.create_frame_brush(self.frame_color))
        self.setPen(FrameStyleManager.create_frame_pen(self.frame_color))

    def _create_title_label(self):
        """Create title label for the frame."""
        self.title_label = QGraphicsTextItem(self.frame_title, self)
        self.title_label.setFont(TitleRenderer.create_font(self.rect().width()))
        self.title_label.setDefaultTextColor(FrameStyleManager.get_title_color())
        self.title_label.setPos(10, 5)
        self._update_title_geometry()

    def _update_title_geometry(self):
        """Update title label geometry based on frame size."""
        if not self.title_label:
            return
        rect = self.rect()
        self.title_label.setFont(TitleRenderer.create_font(rect.width()))
        available_width = TitleRenderer.get_available_width(rect.width())
        if available_width > 0:
            self.title_label.setTextWidth(available_width)

    def set_title(self, title: str):
        """Update the frame title."""
        self.frame_title = title
        if self.title_label:
            self.title_label.setPlainText(title)

    def set_color(self, color: QColor):
        """Change the frame color."""
        self.frame_color = color
        self._apply_style()

    # =========================================================================
    # COLLAPSE FUNCTIONALITY
    # =========================================================================

    @property
    def is_collapsed(self) -> bool:
        """Check if frame is collapsed."""
        return self._is_collapsed

    def toggle_collapse(self) -> None:
        """Toggle between collapsed and expanded state."""
        self.expand() if self._is_collapsed else self.collapse()

    def collapse(self) -> None:
        """Collapse the frame to hide internal nodes."""
        if self._is_collapsed:
            return

        self._capture_nodes_in_bounds()
        self._expanded_rect = QRectF(self.rect())
        self._hidden_node_views.clear()
        self._hidden_pipes.clear()

        for node in self.contained_nodes:
            self._collect_pipes(node)

        for node in self.contained_nodes:
            try:
                if hasattr(node, "view") and node.view:
                    self._hidden_node_views.append(node.view)
                    node.view.setVisible(False)
            except Exception:
                pass

        self._update_pipe_visibility()
        self.prepareGeometryChange()
        self.setRect(0, 0, self.COLLAPSED_WIDTH, self.COLLAPSED_HEIGHT)
        self._update_title_geometry()

        if hasattr(self, "_collapse_button"):
            self._collapse_button._update_position()

        self._port_manager.create_exposed_ports()
        self._is_collapsed = True
        self.update()

        if self.scene():
            self.scene().invalidate()

    def expand(self) -> None:
        """Expand the frame to show internal nodes."""
        if not self._is_collapsed:
            return

        self._port_manager.clear()
        self.prepareGeometryChange()
        self.setRect(self._expanded_rect)
        self._update_title_geometry()

        if hasattr(self, "_collapse_button"):
            self._collapse_button._update_position()

        for node_view in self._hidden_node_views:
            try:
                if node_view:
                    node_view.setVisible(True)
            except Exception:
                pass

        for node in self.contained_nodes:
            try:
                if hasattr(node, "view") and node.view:
                    node.view.setVisible(True)
            except Exception:
                pass

        self._update_pipe_visibility()
        self._hidden_node_views.clear()
        self._hidden_pipes.clear()
        self._is_collapsed = False
        self.update()

        if self.scene():
            self.scene().invalidate()

    def _update_pipe_visibility(self) -> None:
        """Force pipe visibility update through port redraw."""
        for node in self.contained_nodes:
            try:
                for port in node.input_ports() + node.output_ports():
                    if hasattr(port, "view") and port.view:
                        if hasattr(port.view, "redraw_connected_pipes"):
                            port.view.redraw_connected_pipes()
            except Exception:
                pass

    def _capture_nodes_in_bounds(self) -> None:
        """Find and capture any nodes inside the frame bounds."""
        if not self.scene() or not NodeFrame._graph_ref:
            return

        frame_rect = self.sceneBoundingRect()
        try:
            all_nodes = NodeFrame._graph_ref.all_nodes()
        except Exception:
            return

        for node in all_nodes:
            if node in self.contained_nodes:
                continue
            if hasattr(node, "view") and node.view and hasattr(node, "pos"):
                try:
                    node_rect = node.view.sceneBoundingRect()
                    if frame_rect.contains(node_rect.center()):
                        self.add_node(node)
                except Exception:
                    pass

    def _collect_pipes(self, node) -> None:
        """Collect all pipes from a node."""
        if not hasattr(node, "input_ports") or not hasattr(node, "output_ports"):
            return
        try:
            for port in node.input_ports() + node.output_ports():
                if hasattr(port, "view") and port.view:
                    for pipe in port.view.connected_pipes():
                        self._hidden_pipes.add(pipe)
        except Exception:
            pass

    # =========================================================================
    # RENDERING
    # =========================================================================

    def paint(self, painter: QPainter, option, widget=None):
        """Delegate painting to the renderer."""
        self._renderer.paint(painter, option, widget)

    # =========================================================================
    # NODE MANAGEMENT
    # =========================================================================

    def add_node(self, node):
        """Add a node to this frame's group."""
        if node not in self.contained_nodes:
            self.contained_nodes.append(node)
            if hasattr(node, "pos"):
                node_pos = node.pos()
                frame_pos = self.pos()
                if not hasattr(node, "_frame_offset"):
                    node._frame_offset = (
                        node_pos[0] - frame_pos.x(),
                        node_pos[1] - frame_pos.y(),
                    )
                    node._parent_frame = self

    def remove_node(self, node):
        """Remove a node from this frame's group."""
        if node in self.contained_nodes:
            self.contained_nodes.remove(node)
            for attr in ("_frame_offset", "_parent_frame"):
                if hasattr(node, attr):
                    delattr(node, attr)

    # =========================================================================
    # EVENT HANDLING
    # =========================================================================

    def itemChange(self, change, value):
        """Handle item changes, particularly position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self._old_pos = self.pos()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self._is_moving:
            delta_x = value.x() - self._old_pos.x()
            delta_y = value.y() - self._old_pos.y()
            for node in list(self.contained_nodes):
                if hasattr(node, "set_pos"):
                    pos = node.pos()
                    node.set_pos(pos[0] + delta_x, pos[1] + delta_y)
                    if hasattr(node, "_frame_offset"):
                        node._frame_offset = (
                            pos[0] + delta_x - value.x(),
                            pos[1] + delta_y - value.y(),
                        )
        return super().itemChange(change, value)

    def _get_resize_corner(self, pos):
        """Determine if position is at the bottom-right resize corner."""
        if self._is_collapsed:
            return None
        rect = self.rect()
        handle_size = self._resize_handle_size
        br_rect = QRectF(
            rect.right() - handle_size,
            rect.bottom() - handle_size,
            handle_size,
            handle_size,
        )
        return "BR" if br_rect.contains(pos) else None

    def mousePressEvent(self, event):
        """Handle mouse press for movement or resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self._resize_corner = self._get_resize_corner(event.pos())
            if self._resize_corner:
                self._resizing = True
                self._resize_start_pos = event.scenePos()
                self._resize_start_rect = self.rect()
                event.accept()
                return
            self._is_moving = True
            self._old_pos = self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing."""
        if self._resizing and self._resize_corner:
            delta = event.scenePos() - self._resize_start_pos
            new_rect = QRectF(self._resize_start_rect)
            if "R" in self._resize_corner:
                new_rect.setRight(self._resize_start_rect.right() + delta.x())
            if "B" in self._resize_corner:
                new_rect.setBottom(self._resize_start_rect.bottom() + delta.y())
            if new_rect.width() >= 100 and new_rect.height() >= 60:
                self.prepareGeometryChange()
                self.setRect(new_rect)
                self._update_title_geometry()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._resizing:
                self._resizing = False
                self._resize_corner = None
            else:
                self._is_moving = False
                self._check_node_bounds()
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """Change cursor when hovering over resize corner."""
        if self.isSelected():
            cursor = (
                Qt.CursorShape.SizeFDiagCursor
                if self._get_resize_corner(event.pos()) == "BR"
                else Qt.CursorShape.ArrowCursor
            )
            self.setCursor(cursor)
        super().hoverMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to edit title."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._edit_title()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def _check_node_bounds(self):
        """Check node bounds for ungrouping/grouping."""
        if self._is_collapsed or not self.scene():
            return

        frame_rect = self.sceneBoundingRect()
        all_nodes = []
        if NodeFrame._graph_ref:
            try:
                all_nodes = NodeFrame._graph_ref.all_nodes()
            except Exception:
                pass

        has_hovering_node = False

        # Check contained nodes for ungrouping
        for node in list(self.contained_nodes):
            if hasattr(node, "view") and node.view and hasattr(node.view, "sceneBoundingRect"):
                node_rect = node.view.sceneBoundingRect()
                node_area = node_rect.width() * node_rect.height()
                if node_area > 0:
                    intersection = frame_rect.intersected(node_rect)
                    overlap = (intersection.width() * intersection.height()) / node_area
                    if overlap < 0.25:
                        self.remove_node(node)

        # Check for nodes being dragged over frame
        for node in all_nodes:
            if node in self.contained_nodes or not hasattr(node, "view") or not node.view:
                continue
            if not hasattr(node.view, "sceneBoundingRect"):
                continue

            node_rect = node.view.sceneBoundingRect()
            intersection = frame_rect.intersected(node_rect)
            if intersection.width() <= 0 or intersection.height() <= 0:
                self._last_overlap_check.pop(id(node), None)
                continue

            node_area = node_rect.width() * node_rect.height()
            if node_area <= 0:
                continue

            overlap = (intersection.width() * intersection.height()) / node_area
            node_id = id(node)

            try:
                current_pos = (float(node.pos()[0]), float(node.pos()[1]))
            except Exception:
                continue

            if overlap > 0.25:
                has_hovering_node = True
                if node_id in self._last_overlap_check:
                    last_pos, _ = self._last_overlap_check[node_id]
                    pos_changed = (
                        abs(last_pos[0] - current_pos[0]) > 2
                        or abs(last_pos[1] - current_pos[1]) > 2
                    )
                    if pos_changed and overlap > 0.7 and not self._is_moving:
                        self.add_node(node)
                        self._last_overlap_check.pop(node_id, None)
                        continue
                self._last_overlap_check[node_id] = (current_pos, overlap)
            else:
                self._last_overlap_check.pop(node_id, None)

        if self._is_drop_target != has_hovering_node:
            self._is_drop_target = has_hovering_node
            self.update()
        elif has_hovering_node:
            self.update()

    def _edit_title(self):
        """Open dialog to edit frame title."""
        parent = self.scene().views()[0] if self.scene() and self.scene().views() else None
        new_title, ok = QInputDialog.getText(
            parent, "Edit Frame Title", "Frame title:", text=self.frame_title
        )
        if ok and new_title:
            self.set_title(new_title)

    def contextMenuEvent(self, event):
        """Show context menu with frame options."""
        menu = QMenu()
        action_text = "Expand Frame" if self._is_collapsed else "Collapse Frame"
        collapse_action = menu.addAction(action_text)
        collapse_action.triggered.connect(self.expand if self._is_collapsed else self.collapse)
        menu.addSeparator()
        menu.addAction("Rename Frame").triggered.connect(self._edit_title)

        color_menu = menu.addMenu("Change Color")
        for name, color in FRAME_COLOR_PALETTE.items():
            color_menu.addAction(f"  {name}").triggered.connect(lambda c=color: self.set_color(c))

        menu.addSeparator()
        menu.addAction("Delete Frame").triggered.connect(self._delete_frame)

        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            menu.exec(view.mapToGlobal(view.mapFromScene(event.scenePos())))

    def keyPressEvent(self, event):
        """Handle key press events."""
        from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit

        # Don't process X shortcut if text widget has focus
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, QLineEdit | QTextEdit):
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_X:
            self._delete_frame()
            event.accept()
        elif event.key() == Qt.Key.Key_C:
            self.toggle_collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _delete_frame(self, use_undo: bool = True):
        """Delete this frame from the scene."""
        scene = self.scene()
        if not scene:
            return
        if use_undo and NodeFrame._graph_ref:
            try:
                undo_stack = NodeFrame._graph_ref.undo_stack()
                if undo_stack:
                    undo_stack.push(
                        FrameDeletedCmd(self, scene, f"Delete Frame '{self.frame_title}'")
                    )
                    return
            except Exception:
                pass
        self._do_delete()

    def _do_delete(self):
        """Perform actual frame deletion."""
        if self._bounds_manager:
            self._bounds_manager.unregister_frame(self)
        for node in list(self.contained_nodes):
            self.remove_node(node)
        if self.scene():
            self.scene().removeItem(self)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def serialize(self) -> dict[str, Any]:
        """Serialize frame to dictionary."""
        pos = self.pos()
        rect = self.rect() if not self._is_collapsed else self._expanded_rect

        color_name = None
        for name, color in FRAME_COLORS.items():
            if color == self.frame_color:
                color_name = name
                break

        contained_ids = []
        for node in self.contained_nodes:
            if hasattr(node, "get_property"):
                node_id = node.get_property("node_id")
                if node_id:
                    contained_ids.append(node_id)

        return {
            "title": self.frame_title,
            "position": {"x": pos.x(), "y": pos.y()},
            "size": {"width": rect.width(), "height": rect.height()},
            "color": color_name
            or {
                "r": self.frame_color.red(),
                "g": self.frame_color.green(),
                "b": self.frame_color.blue(),
                "a": self.frame_color.alpha(),
            },
            "is_collapsed": self._is_collapsed,
            "contained_nodes": contained_ids,
        }

    @classmethod
    def deserialize(
        cls, data: dict[str, Any], node_map: dict[str, Any] | None = None
    ) -> "NodeFrame":
        """Create frame from serialized data."""
        color_data = data.get("color", "gray")
        color = (
            FRAME_COLORS.get(color_data, FRAME_COLORS["gray"])
            if isinstance(color_data, str)
            else QColor(
                color_data.get("r", 100),
                color_data.get("g", 100),
                color_data.get("b", 100),
                color_data.get("a", 80),
            )
        )

        size = data.get("size", {"width": 400, "height": 300})
        frame = cls(
            title=data.get("title", "Group"),
            color=color,
            width=size.get("width", 400),
            height=size.get("height", 300),
        )

        pos = data.get("position", {"x": 0, "y": 0})
        frame.setPos(pos.get("x", 0), pos.get("y", 0))

        if node_map:
            for node_id in data.get("contained_nodes", []):
                if node_id in node_map:
                    frame.add_node(node_map[node_id])

        if data.get("is_collapsed", False):
            frame.collapse()

        return frame
