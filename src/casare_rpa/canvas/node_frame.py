"""
Node Frame/Group System

Allows users to create visual frames around groups of nodes for organization.
"""

from typing import List, Optional, Tuple
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QMenu, QInputDialog
from PySide6.QtCore import QRectF, Qt, QPointF, QTimer, QObject, Signal
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter, QKeyEvent
from NodeGraphQt import BaseNode
from NodeGraphQt.base.node import NodeObject
from loguru import logger


class FrameTimerHelper(QObject):
    """Helper QObject to host the timer for NodeFrame."""

    check_bounds = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_bounds.emit)

    def start(self, interval):
        self.timer.start(interval)

    def stop(self):
        self.timer.stop()


class NodeFrame(QGraphicsRectItem):
    """
    A visual frame/backdrop for grouping nodes.

    Features:
    - Resizable colored rectangle
    - Editable title label (double-click to edit)
    - Adjustable transparency
    - Multiple color themes
    - Nodes can be grouped within the frame
    - Deletable (Delete key or context menu)
    """

    def __init__(
        self,
        title: str = "Group",
        color: QColor = None,
        width: float = 400,
        height: float = 300,
        parent=None
    ):
        super().__init__(parent)

        self.frame_title = title
        self.frame_color = color or QColor(100, 100, 100, 80)  # Semi-transparent gray
        self.contained_nodes = []  # List of nodes grouped in this frame
        self._is_moving = False  # Track if frame is being moved
        self._old_pos = QPointF(0, 0)  # Store previous position
        self._is_drop_target = False  # Track if a node is being dragged over this frame
        self._selected = False  # Track selection state for custom rendering
        self._last_overlap_check = {}  # Track node positions for drag detection
        self._resize_handle_size = 12  # Size of resize handles
        self._resizing = False  # Track if currently resizing
        self._resize_corner = None  # Which corner is being resized (TR, BR, BL, TL)
        self._resize_start_pos = None  # Mouse position when resize started
        self._resize_start_rect = None  # Frame rect when resize started

        # Set frame properties
        self.setRect(0, 0, width, height)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges |
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable |
            QGraphicsItem.GraphicsItemFlag.ItemAcceptsInputMethod
        )

        # Accept hover and drag events
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

        # Z-value: behind nodes but above grid
        self.setZValue(-10)  # Behind nodes but still selectable

        # Apply styling
        self._apply_style()

        # Create title label
        self._create_title_label()

        # Create timer helper to check for nodes moved outside/inside the frame
        self._timer_helper = FrameTimerHelper()
        self._timer_helper.check_bounds.connect(self._check_node_bounds)
        self._timer_helper.start(100)  # Check every 100ms for responsive highlighting

        logger.info(f"Created node frame: {title} with timer")

    def _apply_style(self):
        """Apply visual styling to the frame."""
        # Semi-transparent fill
        brush = QBrush(self.frame_color)
        self.setBrush(brush)

        # Subtle border
        pen = QPen(self.frame_color.darker(120), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)

    def _create_title_label(self):
        """Create title label for the frame."""
        self.title_label = QGraphicsTextItem(self.frame_title, self)

        # Style the title
        font = QFont("Arial", 14, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setDefaultTextColor(self.frame_color.darker(200))

        # Position at top-left
        self.title_label.setPos(10, 5)

    def set_title(self, title: str):
        """Update the frame title."""
        self.frame_title = title
        if self.title_label:
            self.title_label.setPlainText(title)

    def set_color(self, color: QColor):
        """Change the frame color."""
        self.frame_color = color
        self._apply_style()
        if self.title_label:
            self.title_label.setDefaultTextColor(color.darker(200))

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint method with selection highlight (no visual resize handles)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle
        rect = self.rect()

        # Use bright yellow border when selected or when drop target
        if self.isSelected() or self._is_drop_target:
            pen = QPen(QColor(255, 215, 0), 3)  # Bright yellow, 3px thick
            pen.setStyle(Qt.PenStyle.SolidLine)
        else:
            pen = QPen(self.frame_color.darker(120), 2)
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setBrush(self.brush())
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 10, 10)

        # Note: No visual resize handles drawn - only cursor changes indicate resize capability

    def add_node(self, node):
        """
        Add a node to this frame's group.

        Args:
            node: Node to add to the frame
        """
        if node not in self.contained_nodes:
            self.contained_nodes.append(node)
            # Store the node's relative position to the frame
            if hasattr(node, 'pos'):
                node_pos = node.pos()
                frame_pos = self.pos()
                # Store original position for movement tracking
                if not hasattr(node, '_frame_offset'):
                    node._frame_offset = (node_pos[0] - frame_pos.x(), node_pos[1] - frame_pos.y())
                    node._parent_frame = self

    def remove_node(self, node):
        """
        Remove a node from this frame's group.

        Args:
            node: Node to remove from the frame
        """
        if node in self.contained_nodes:
            self.contained_nodes.remove(node)
            if hasattr(node, '_frame_offset'):
                delattr(node, '_frame_offset')
            if hasattr(node, '_parent_frame'):
                delattr(node, '_parent_frame')

    def itemChange(self, change, value):
        """Handle item changes, particularly position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Track position before change
            self._old_pos = self.pos()

        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Only move nodes if the frame itself is being moved
            if self._is_moving:
                new_pos = value
                # Calculate the delta movement
                delta_x = new_pos.x() - self._old_pos.x()
                delta_y = new_pos.y() - self._old_pos.y()

                # Move all contained nodes with the frame
                for node in list(self.contained_nodes):
                    if hasattr(node, 'set_pos'):
                        current_pos = node.pos()
                        node.set_pos(current_pos[0] + delta_x, current_pos[1] + delta_y)
                        # Update the offset
                        if hasattr(node, '_frame_offset'):
                            node._frame_offset = (current_pos[0] + delta_x - new_pos.x(),
                                                current_pos[1] + delta_y - new_pos.y())

        return super().itemChange(change, value)

    def _get_resize_corner(self, pos):
        """Determine if the position is at the bottom-right resize corner."""
        rect = self.rect()
        handle_size = self._resize_handle_size

        # Only check bottom-right corner
        br_rect = QRectF(rect.right() - handle_size, rect.bottom() - handle_size, handle_size, handle_size)

        if br_rect.contains(pos):
            return 'BR'
        return None

    def mousePressEvent(self, event):
        """Handle mouse press to track frame movement or start resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Ensure frame receives keyboard focus for key events (like X for delete)
            self.setFocus()
            logger.info(f"🎯 Frame '{self.frame_title}' received focus")

            # Check if clicking on a resize handle
            self._resize_corner = self._get_resize_corner(event.pos())

            if self._resize_corner:
                # Start resizing
                self._resizing = True
                self._resize_start_pos = event.scenePos()
                self._resize_start_rect = self.rect()
                event.accept()
                return
            else:
                # Start moving
                self._is_moving = True
                self._old_pos = self.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing."""
        if self._resizing and self._resize_corner:
            delta = event.scenePos() - self._resize_start_pos
            new_rect = QRectF(self._resize_start_rect)

            # Adjust rect based on which corner is being dragged
            if 'R' in self._resize_corner:  # Right side
                new_rect.setRight(self._resize_start_rect.right() + delta.x())
            if 'L' in self._resize_corner:  # Left side
                new_rect.setLeft(self._resize_start_rect.left() + delta.x())
            if 'T' in self._resize_corner:  # Top side
                new_rect.setTop(self._resize_start_rect.top() + delta.y())
            if 'B' in self._resize_corner:  # Bottom side
                new_rect.setBottom(self._resize_start_rect.bottom() + delta.y())

            # Enforce minimum size
            if new_rect.width() >= 100 and new_rect.height() >= 60:
                self.prepareGeometryChange()
                self.setRect(new_rect)

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop tracking frame movement or resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._resizing:
                self._resizing = False
                self._resize_corner = None
                logger.info(f"Frame resized to: {self.rect().width()}x{self.rect().height()}")
            else:
                self._is_moving = False
                # Check for nodes that should be ungrouped
                self._check_node_bounds()
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """Change cursor when hovering over the bottom-right resize corner."""
        if self.isSelected():
            corner = self._get_resize_corner(event.pos())
            if corner == 'BR':
                # Bottom-right corner uses diagonal resize cursor
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)  # \ diagonal
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to edit title."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._edit_title()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def _check_node_bounds(self):
        """Check node bounds for ungrouping/grouping and highlight during drag."""
        logger.info(f"⏰ Timer tick - checking bounds for frame '{self.frame_title}'")

        if not self.scene():
            logger.info("❌ No scene, skipping check")
            return

        frame_rect = self.sceneBoundingRect()
        logger.info(f"📐 Frame rect: {frame_rect.width()}x{frame_rect.height()}")

        # Get all nodes in the scene
        all_nodes = []
        for item in self.scene().items():
            # Check if item is a node (has the necessary attributes)
            if hasattr(item, 'view') and hasattr(item, 'pos') and item != self:
                all_nodes.append(item)

        # Track if any node is being dragged over this frame
        has_hovering_node = False

        # Check contained nodes for ungrouping
        for node in list(self.contained_nodes):
            if hasattr(node, 'view'):
                node_view = node.view
                if hasattr(node_view, 'sceneBoundingRect'):
                    node_rect = node_view.sceneBoundingRect()

                    # Check if node is mostly outside the frame
                    intersection = frame_rect.intersected(node_rect)
                    node_area = node_rect.width() * node_rect.height()

                    if node_area > 0:
                        overlap_ratio = (intersection.width() * intersection.height()) / node_area
                        if overlap_ratio < 0.25:
                            self.remove_node(node)
                            logger.debug(f"Ungrouped node from frame (moved outside)")

        # Check for nodes being dragged over the frame (for highlighting and auto-grouping)
        for node in all_nodes:
            if node not in self.contained_nodes and hasattr(node, 'view'):
                node_view = node.view
                if hasattr(node_view, 'sceneBoundingRect'):
                    node_rect = node_view.sceneBoundingRect()

                    # Check if node overlaps with frame
                    intersection = frame_rect.intersected(node_rect)
                    if intersection.width() > 0 and intersection.height() > 0:
                        node_area = node_rect.width() * node_rect.height()
                        if node_area > 0:
                            overlap_ratio = (intersection.width() * intersection.height()) / node_area

                            # Get node ID for tracking
                            node_id = id(node)
                            try:
                                current_pos = (float(node.pos()[0]), float(node.pos()[1]))
                            except:
                                continue

                            # If more than 40% of the node is inside the frame, highlight
                            if overlap_ratio > 0.4:
                                has_hovering_node = True
                                logger.info(f"🔍 Node hovering over frame: overlap={overlap_ratio:.1%}")

                                # Check if node position changed (being dragged)
                                if node_id in self._last_overlap_check:
                                    last_pos, last_overlap = self._last_overlap_check[node_id]
                                    pos_changed = (abs(last_pos[0] - current_pos[0]) > 1 or
                                                 abs(last_pos[1] - current_pos[1]) > 1)

                                    # If position changed and overlap is significant, add the node
                                    if pos_changed and overlap_ratio > 0.5:
                                        if not self._is_moving:
                                            self.add_node(node)
                                            logger.info(f"✅ Node added to frame by dragging (overlap: {overlap_ratio:.1%})")
                                            # Remove from tracking after adding
                                            if node_id in self._last_overlap_check:
                                                del self._last_overlap_check[node_id]
                                    else:
                                        logger.info(f"📍 Node tracked but not moving enough: pos_changed={pos_changed}, overlap={overlap_ratio:.1%}")
                                else:
                                    # First time seeing this node overlap - just track it
                                    logger.info(f"🆕 Started tracking node at position {current_pos}")

                                # Update position tracking
                                self._last_overlap_check[node_id] = (current_pos, overlap_ratio)
                            else:
                                # Remove from tracking if no longer overlapping significantly
                                if node_id in self._last_overlap_check:
                                    del self._last_overlap_check[node_id]

        # Update highlight state
        if self._is_drop_target != has_hovering_node:
            self._is_drop_target = has_hovering_node
            logger.info(f"💡 Frame highlight state changed: {has_hovering_node}")
            self.update()  # Trigger repaint

    def _edit_title(self):
        """Open a dialog to edit the frame title."""
        from PySide6.QtWidgets import QApplication

        # Get the main window or any widget to parent the dialog
        parent = None
        if self.scene() and self.scene().views():
            parent = self.scene().views()[0]

        new_title, ok = QInputDialog.getText(
            parent,
            "Edit Frame Title",
            "Frame title:",
            text=self.frame_title
        )

        if ok and new_title:
            self.set_title(new_title)
            logger.info(f"Frame title changed to: {new_title}")

    def contextMenuEvent(self, event):
        """Show context menu with frame options."""
        menu = QMenu()

        # Rename action
        rename_action = menu.addAction("Rename Frame")
        rename_action.triggered.connect(self._edit_title)

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete Frame")
        delete_action.triggered.connect(self._delete_frame)

        # Show menu at cursor position
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            menu.exec(view.mapToGlobal(view.mapFromScene(event.scenePos())))

    def keyPressEvent(self, event):
        """Handle key press events."""
        logger.info(f"🔑 Frame keyPressEvent: key={event.key()}, Qt.Key_X={Qt.Key.Key_X}")

        if event.key() == Qt.Key.Key_X:
            logger.info(f"❌ X key pressed - deleting frame '{self.frame_title}'")
            self._delete_frame()
            event.accept()
        else:
            logger.info(f"⏩ Other key pressed, passing to parent")
            super().keyPressEvent(event)

    def _delete_frame(self):
        """Delete this frame from the scene."""
        # Stop the timer helper
        if hasattr(self, '_timer_helper'):
            self._timer_helper.stop()
            self._timer_helper.deleteLater()

        # Ungroup all contained nodes
        for node in list(self.contained_nodes):
            self.remove_node(node)

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)
            logger.info(f"Deleted frame: {self.frame_title}")


# Pre-defined frame color themes
FRAME_COLORS = {
    'blue': QColor(100, 181, 246, 60),
    'purple': QColor(156, 39, 176, 60),
    'green': QColor(102, 187, 106, 60),
    'orange': QColor(255, 167, 38, 60),
    'red': QColor(239, 83, 80, 60),
    'yellow': QColor(255, 202, 40, 60),
    'teal': QColor(77, 182, 172, 60),
    'pink': QColor(236, 64, 122, 60),
    'gray': QColor(120, 120, 120, 60),
}


class FrameNode(NodeObject):
    """
    NodeGraphQt-compatible frame node for grouping.

    This is a special node type that appears as a backdrop/frame.
    """

    __identifier__ = "casare_rpa.frame"
    NODE_NAME = "Frame"

    def __init__(self):
        super().__init__()

        # Frame-specific properties
        self.create_property("frame_title", "Group", widget_type=0)
        self.create_property("frame_color", "blue", widget_type=3)  # ComboBox
        self.create_property("frame_width", 400.0, widget_type=2)
        self.create_property("frame_height", 300.0, widget_type=2)

        # Hide standard node appearance (no ports, minimal chrome)
        self.set_color(0, 0, 0, 0)  # Transparent

        logger.info("Frame node created")

    def get_frame_rect(self) -> QRectF:
        """Get the frame's bounding rectangle."""
        width = self.get_property("frame_width")
        height = self.get_property("frame_height")
        pos = self.pos()
        return QRectF(pos[0], pos[1], width, height)


def create_frame(
    graph_view,
    title: str = "Group",
    color_name: str = "blue",
    position: Tuple[float, float] = (0, 0),
    size: Tuple[float, float] = (400, 300)
) -> NodeFrame:
    """
    Create a node frame in the graph view.

    Args:
        graph_view: NodeGraph view to add frame to
        title: Frame title
        color_name: Color theme name from FRAME_COLORS
        position: (x, y) position tuple
        size: (width, height) size tuple

    Returns:
        Created NodeFrame instance
    """
    color = FRAME_COLORS.get(color_name, FRAME_COLORS['gray'])

    frame = NodeFrame(
        title=title,
        color=color,
        width=size[0],
        height=size[1]
    )

    # Add to scene
    scene = graph_view.scene()
    scene.addItem(frame)

    # Position the frame
    frame.setPos(position[0], position[1])

    logger.info(f"Created frame '{title}' at {position}")
    return frame


def group_selected_nodes(graph_view, title: str = "Group", selected_nodes: List = None) -> Optional[NodeFrame]:
    """
    Create a frame around currently selected nodes.

    Args:
        graph_view: NodeGraph viewer
        title: Frame title
        selected_nodes: List of selected nodes (if None, will be fetched from graph_view)

    Returns:
        Created frame or None if no nodes selected
    """
    if selected_nodes is None:
        if hasattr(graph_view, 'selected_nodes'):
            selected_nodes = graph_view.selected_nodes()
        else:
            logger.warning("No nodes provided and graph_view has no selected_nodes method")
            return None

    if not selected_nodes:
        logger.warning("No nodes selected for grouping")
        return None

    # Calculate bounding box of selected nodes
    # node.pos() returns a tuple (x, y)
    min_x = min(node.pos()[0] for node in selected_nodes)
    min_y = min(node.pos()[1] for node in selected_nodes)
    max_x = max(node.pos()[0] + node.view.width for node in selected_nodes)
    max_y = max(node.pos()[1] + node.view.height for node in selected_nodes)

    # Add padding
    padding = 30
    x = min_x - padding
    y = min_y - padding
    width = max_x - min_x + padding * 2
    height = max_y - min_y + padding * 2

    # Create frame
    frame = create_frame(
        graph_view,
        title=title,
        position=(x, y),
        size=(width, height)
    )

    # Add all selected nodes to the frame
    for node in selected_nodes:
        frame.add_node(node)

    logger.info(f"Created frame around {len(selected_nodes)} nodes and grouped them")
    return frame


def add_frame_menu_actions(graph_menu):
    """
    Add frame-related actions to the graph context menu.

    Args:
        graph_menu: Context menu to add actions to
    """
    from PySide6.QtGui import QAction

    # Create Frame submenu
    frame_menu = graph_menu.addMenu("Frame")

    # Add "Group Selected Nodes" action
    group_action = QAction("Group Selected Nodes", graph_menu)
    group_action.triggered.connect(lambda: group_selected_nodes(graph_menu.graph, "Group"))
    frame_menu.addAction(group_action)

    frame_menu.addSeparator()

    # Add color theme actions
    for color_name in FRAME_COLORS.keys():
        action = QAction(f"Create {color_name.capitalize()} Frame", graph_menu)
        action.triggered.connect(
            lambda checked, c=color_name: create_frame(
                graph_menu.graph,
                title="Group",
                color_name=c,
                position=(0, 0)
            )
        )
        frame_menu.addAction(action)

    logger.debug("Frame menu actions added")
