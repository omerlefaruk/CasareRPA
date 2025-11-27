"""
Node Frame/Group System

Allows users to create visual frames around groups of nodes for organization.

Now uses centralized FrameBoundsManager for better performance with many frames.

References:
- "Designing Data-Intensive Applications" - Resource pooling
"""

from typing import Any, List, Optional, Tuple, Set, Dict
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QMenu,
    QInputDialog,
)
from PySide6.QtCore import QRectF, Qt, QPointF, QTimer, QObject
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter
from NodeGraphQt.base.node import NodeObject


# ============================================================================
# FRAME COLOR PALETTE
# ============================================================================

# Predefined colors for frame grouping (semi-transparent for background)
FRAME_COLOR_PALETTE = {
    "Gray": QColor(100, 100, 100, 80),
    "Blue": QColor(60, 120, 180, 100),
    "Green": QColor(60, 160, 80, 100),
    "Yellow": QColor(180, 160, 60, 100),
    "Orange": QColor(200, 120, 60, 100),
    "Red": QColor(180, 70, 70, 100),
    "Purple": QColor(140, 80, 160, 100),
    "Teal": QColor(60, 150, 150, 100),
    "Pink": QColor(180, 100, 140, 100),
}


# ============================================================================
# UNDO COMMANDS
# ============================================================================


class FrameDeletedCmd(QUndoCommand):
    """
    Undo command for frame deletion.

    Stores all frame state to allow restoring the frame on undo.
    """

    def __init__(self, frame: "NodeFrame", scene, description: str = "Delete Frame"):
        super().__init__(description)
        self._scene = scene
        self._frame_data = None
        self._frame = frame
        self._was_deleted = False

        # Store frame state before deletion
        self._store_frame_state()

    def _store_frame_state(self):
        """Store all frame state for restoration."""
        self._frame_data = {
            "title": self._frame.frame_title,
            "color": self._frame.frame_color,
            "pos": (self._frame.pos().x(), self._frame.pos().y()),
            "rect": (self._frame.rect().width(), self._frame.rect().height()),
            "contained_node_ids": [
                node.id if hasattr(node, "id") else id(node)
                for node in self._frame.contained_nodes
            ],
            "is_collapsed": self._frame._is_collapsed,
            "expanded_rect": (
                self._frame._expanded_rect.width(),
                self._frame._expanded_rect.height(),
            )
            if self._frame._expanded_rect
            else None,
        }

    def undo(self):
        """Restore the deleted frame."""
        if not self._was_deleted or not self._frame_data:
            return

        # Re-add frame to scene
        if self._scene and self._frame:
            self._scene.addItem(self._frame)

            # Re-register with bounds manager
            if hasattr(self._frame, "_bounds_manager") and self._frame._bounds_manager:
                self._frame._bounds_manager.register_frame(self._frame)

            self._was_deleted = False

    def redo(self):
        """Delete the frame again."""
        if self._frame and self._frame.scene():
            # Unregister from bounds manager
            if hasattr(self._frame, "_bounds_manager") and self._frame._bounds_manager:
                self._frame._bounds_manager.unregister_frame(self._frame)

            # Remove from scene (but keep the frame object)
            self._scene.removeItem(self._frame)
            self._was_deleted = True


# ============================================================================
# FRAME BOUNDS MANAGER (Centralized Timer)
# ============================================================================


class FrameBoundsManager(QObject):
    """
    Centralized manager for all frame bounds checking.

    Instead of each frame having its own 100ms timer, this manager uses
    a single timer to check all frames. This significantly reduces CPU
    usage when there are many frames.

    Usage:
        manager = FrameBoundsManager.get_instance()
        manager.register_frame(frame)
        manager.unregister_frame(frame)
    """

    _instance: Optional["FrameBoundsManager"] = None

    @classmethod
    def get_instance(cls) -> "FrameBoundsManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the bounds manager."""
        super().__init__(parent)
        self._frames: Set["NodeFrame"] = set()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._batch_check)
        self._interval = 150  # ms - check every 150ms

    def register_frame(self, frame: "NodeFrame") -> None:
        """
        Register a frame for bounds checking.

        Args:
            frame: The NodeFrame to check
        """
        self._frames.add(frame)
        if not self._timer.isActive():
            self._timer.start(self._interval)

    def unregister_frame(self, frame: "NodeFrame") -> None:
        """
        Unregister a frame from bounds checking.

        Args:
            frame: The NodeFrame to stop checking
        """
        self._frames.discard(frame)
        if not self._frames and self._timer.isActive():
            self._timer.stop()

    def _batch_check(self) -> None:
        """Check all frames in a single pass."""
        if not self._frames:
            return

        # Check each frame
        for frame in list(self._frames):  # Copy to avoid modification during iteration
            try:
                if frame.scene():  # Frame still in scene
                    frame._check_node_bounds()
            except Exception:
                pass

    @property
    def frame_count(self) -> int:
        """Get the number of registered frames."""
        return len(self._frames)

    @property
    def is_running(self) -> bool:
        """Check if the timer is running."""
        return self._timer.isActive()


# ============================================================================
# COLLAPSE BUTTON
# ============================================================================


class CollapseButton(QGraphicsRectItem):
    """
    A clickable button to collapse/expand a frame.

    Visual design:
    - Rounded square button in frame header
    - Shows "-" when expanded (click to collapse)
    - Shows "+" when collapsed (click to expand)
    - Hover highlight for better UX
    """

    def __init__(self, parent: "NodeFrame"):
        """
        Initialize collapse button.

        Args:
            parent: Parent NodeFrame
        """
        super().__init__(parent)
        self._parent_frame = parent
        self._is_hovered = False

        # Button size and position
        self._size = 18
        self.setRect(0, 0, self._size, self._size)

        # Position in top-right of frame header
        self._update_position()

        # Make clickable
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        # Z-value above frame
        self.setZValue(1)

    def _update_position(self) -> None:
        """Update button position based on frame rect."""
        frame_rect = self._parent_frame.rect()
        margin = 8
        x = frame_rect.right() - self._size - margin
        y = frame_rect.top() + margin
        self.setPos(x, y)

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the collapse button."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Background color
        if self._is_hovered:
            bg_color = QColor(80, 80, 80, 200)
        else:
            bg_color = QColor(60, 60, 60, 180)

        # Draw rounded rectangle background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Draw +/- symbol
        painter.setPen(QPen(QColor(220, 220, 220), 2))

        center_x = rect.center().x()
        center_y = rect.center().y()
        symbol_size = 6

        # Horizontal line (always present)
        painter.drawLine(
            QPointF(center_x - symbol_size, center_y),
            QPointF(center_x + symbol_size, center_y),
        )

        # Vertical line (only when collapsed - shows "+")
        if self._parent_frame.is_collapsed:
            painter.drawLine(
                QPointF(center_x, center_y - symbol_size),
                QPointF(center_x, center_y + symbol_size),
            )

    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Handle click to toggle collapse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._parent_frame.toggle_collapse()
            event.accept()
        else:
            super().mousePressEvent(event)


# ============================================================================
# EXPOSED PORT INDICATOR
# ============================================================================


class ExposedPortIndicator(QGraphicsEllipseItem):
    """
    Visual indicator for exposed ports on collapsed frames.

    Shows which ports are connected externally when frame is collapsed.
    Color-coded by port type for consistency with the type system.
    """

    def __init__(
        self, port_name: str, is_output: bool, color: QColor, parent: QGraphicsItem
    ):
        """
        Initialize exposed port indicator.

        Args:
            port_name: Name of the port
            is_output: True if output port, False if input
            color: Port type color
            parent: Parent graphics item
        """
        super().__init__(parent)
        self.port_name = port_name
        self.is_output = is_output
        self.port_color = color

        # Indicator size
        size = 10
        self.setRect(-size / 2, -size / 2, size, size)

        # Styling
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(130), 1.5))

        # Tooltip showing port name
        self.setToolTip(f"{'Output' if is_output else 'Input'}: {port_name}")

        # Accept hover for tooltip
        self.setAcceptHoverEvents(True)


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
    - Collapsible to hide internal nodes
    """

    # Collapsed frame dimensions
    COLLAPSED_WIDTH = 200
    COLLAPSED_HEIGHT = 50

    # Class-level reference to the graph (set when first frame is created)
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

        # Collapse state
        self._is_collapsed = False
        self._expanded_rect = QRectF(0, 0, width, height)  # Store expanded size
        self._exposed_ports: List[
            ExposedPortIndicator
        ] = []  # Indicators for external connections
        self._hidden_node_views: List[Any] = []  # Store references to hidden node views
        self._hidden_pipes: Set[Any] = set()  # Store references to hidden pipes

        # Set frame properties
        self.setRect(0, 0, width, height)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
            | QGraphicsItem.GraphicsItemFlag.ItemAcceptsInputMethod
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

        # Create collapse button
        self._collapse_button = CollapseButton(self)

        # Use centralized FrameBoundsManager instead of per-frame timer
        # This significantly reduces CPU usage when there are many frames
        self._bounds_manager = FrameBoundsManager.get_instance()
        self._bounds_manager.register_frame(self)

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

        # Style the title - use a light color for better visibility
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        self.title_label.setFont(font)
        # Use a light, semi-transparent white that's visible on any frame color
        self.title_label.setDefaultTextColor(QColor(255, 255, 255, 200))

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
        # Title stays light white for visibility regardless of frame color

    # =========================================================================
    # COLLAPSE FUNCTIONALITY
    # =========================================================================

    @property
    def is_collapsed(self) -> bool:
        """Check if frame is collapsed."""
        return self._is_collapsed

    def toggle_collapse(self) -> None:
        """Toggle between collapsed and expanded state."""
        if self._is_collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self) -> None:
        """
        Collapse the frame to hide internal nodes.

        When collapsed:
        - Stores current expanded size
        - Shrinks to compact dimensions
        - Hides all contained nodes
        - Shows exposed port indicators for external connections
        """
        if self._is_collapsed:
            return

        # First, capture any nodes that are inside the frame bounds but not yet tracked
        self._capture_nodes_in_bounds()

        # Store current expanded rect
        self._expanded_rect = QRectF(self.rect())

        # Clear previously stored views and pipes
        self._hidden_node_views.clear()
        self._hidden_pipes.clear()

        # Collect all pipes FIRST (before hiding nodes)
        for node in self.contained_nodes:
            self._collect_pipes(node)

        # Hide node views FIRST - this is critical because pipe visibility
        # in NodeGraphQt depends on node visibility
        for node in self.contained_nodes:
            try:
                if hasattr(node, "view") and node.view:
                    self._hidden_node_views.append(node.view)
                    node.view.setVisible(False)
            except Exception:
                pass

        # Force pipe visibility update by triggering redraw through ports
        # This is more reliable than calling draw_path directly
        for node in self.contained_nodes:
            try:
                for port in node.input_ports():
                    if hasattr(port, "view") and port.view:
                        if hasattr(port.view, "redraw_connected_pipes"):
                            port.view.redraw_connected_pipes()
                for port in node.output_ports():
                    if hasattr(port, "view") and port.view:
                        if hasattr(port.view, "redraw_connected_pipes"):
                            port.view.redraw_connected_pipes()
            except Exception:
                pass

        # Resize to collapsed dimensions
        self.prepareGeometryChange()
        self.setRect(0, 0, self.COLLAPSED_WIDTH, self.COLLAPSED_HEIGHT)

        # Update collapse button position
        if hasattr(self, "_collapse_button"):
            self._collapse_button._update_position()

        # Create exposed port indicators
        self._create_exposed_ports()

        self._is_collapsed = True
        self.update()

        # Force full scene invalidation to ensure all visibility changes are applied
        if self.scene():
            self.scene().invalidate()

    def expand(self) -> None:
        """
        Expand the frame to show internal nodes.

        When expanded:
        - Restores original size
        - Shows all contained nodes
        - Removes exposed port indicators
        """
        if not self._is_collapsed:
            return

        # Remove exposed port indicators
        self._clear_exposed_ports()

        # Restore expanded rect
        self.prepareGeometryChange()
        self.setRect(self._expanded_rect)

        # Update collapse button position
        if hasattr(self, "_collapse_button"):
            self._collapse_button._update_position()

        # Show all node views FIRST
        for node_view in self._hidden_node_views:
            try:
                if node_view:
                    node_view.setVisible(True)
            except Exception:
                pass

        # Also ensure all contained nodes are visible
        for node in self.contained_nodes:
            try:
                if hasattr(node, "view") and node.view:
                    node.view.setVisible(True)
            except Exception:
                pass

        # Force pipe visibility update by triggering redraw through ports
        # This is more reliable than calling draw_path directly
        for node in self.contained_nodes:
            try:
                for port in node.input_ports():
                    if hasattr(port, "view") and port.view:
                        if hasattr(port.view, "redraw_connected_pipes"):
                            port.view.redraw_connected_pipes()
                for port in node.output_ports():
                    if hasattr(port, "view") and port.view:
                        if hasattr(port.view, "redraw_connected_pipes"):
                            port.view.redraw_connected_pipes()
            except Exception:
                pass

        # Clear the stored views and pipes
        self._hidden_node_views.clear()
        self._hidden_pipes.clear()

        self._is_collapsed = False
        self.update()

        # Force full scene invalidation to ensure all visibility changes are applied
        if self.scene():
            self.scene().invalidate()

    def _capture_nodes_in_bounds(self) -> None:
        """
        Find and capture any nodes that are inside the frame bounds.

        This ensures nodes are properly tracked even if they weren't
        explicitly added via drag-and-drop.
        """
        if not self.scene():
            return

        frame_rect = self.sceneBoundingRect()

        # Get all nodes from the graph reference
        all_nodes = []
        if NodeFrame._graph_ref:
            try:
                all_nodes = NodeFrame._graph_ref.all_nodes()
            except Exception:
                pass
                return

        # Check each node
        for node in all_nodes:
            # Skip if already in contained_nodes
            if node in self.contained_nodes:
                continue

            # Check if node has a view and position
            if hasattr(node, "view") and node.view and hasattr(node, "pos"):
                try:
                    node_view = node.view
                    if hasattr(node_view, "sceneBoundingRect"):
                        node_rect = node_view.sceneBoundingRect()

                        # Check if node center is inside the frame
                        node_center = node_rect.center()
                        if frame_rect.contains(node_center):
                            self.add_node(node)
                except Exception:
                    pass

    def _collect_pipes(self, node) -> None:
        """Collect all pipes from a node and store them (without hiding)."""
        if not hasattr(node, "input_ports") or not hasattr(node, "output_ports"):
            return

        try:
            # Collect pipes from input ports
            for port in node.input_ports():
                if hasattr(port, "view") and port.view:
                    for pipe in port.view.connected_pipes():
                        self._hidden_pipes.add(pipe)

            # Collect pipes from output ports
            for port in node.output_ports():
                if hasattr(port, "view") and port.view:
                    for pipe in port.view.connected_pipes():
                        self._hidden_pipes.add(pipe)
        except Exception:
            pass

    def _create_exposed_ports(self) -> None:
        """Create indicators for ports connected to nodes outside this frame."""
        self._clear_exposed_ports()

        # Collect external connections
        input_ports = []
        output_ports = []

        for node in self.contained_nodes:
            if not hasattr(node, "input_ports") or not hasattr(node, "output_ports"):
                continue

            try:
                # Check input ports for external connections
                for port in node.input_ports():
                    for connected_port in port.connected_ports():
                        connected_node = connected_port.node()
                        if connected_node not in self.contained_nodes:
                            input_ports.append(
                                (port.name(), self._get_port_color(port))
                            )

                # Check output ports for external connections
                for port in node.output_ports():
                    for connected_port in port.connected_ports():
                        connected_node = connected_port.node()
                        if connected_node not in self.contained_nodes:
                            output_ports.append(
                                (port.name(), self._get_port_color(port))
                            )
            except Exception:
                pass

        # Create indicators
        rect = self.rect()
        margin = 12
        port_spacing = 14

        # Input ports on left side
        y_start = (
            rect.top() + rect.height() / 2 - (len(input_ports) - 1) * port_spacing / 2
        )
        for i, (port_name, color) in enumerate(input_ports):
            indicator = ExposedPortIndicator(port_name, False, color, self)
            indicator.setPos(rect.left() + margin, y_start + i * port_spacing)
            self._exposed_ports.append(indicator)

        # Output ports on right side
        y_start = (
            rect.top() + rect.height() / 2 - (len(output_ports) - 1) * port_spacing / 2
        )
        for i, (port_name, color) in enumerate(output_ports):
            indicator = ExposedPortIndicator(port_name, True, color, self)
            indicator.setPos(rect.right() - margin, y_start + i * port_spacing)
            self._exposed_ports.append(indicator)

    def _clear_exposed_ports(self) -> None:
        """Remove all exposed port indicators."""
        for indicator in self._exposed_ports:
            if indicator.scene():
                indicator.scene().removeItem(indicator)
        self._exposed_ports.clear()

    def _get_port_color(self, port) -> QColor:
        """Get color for a port based on its type."""
        # Default color
        default_color = QColor(100, 181, 246)  # Light blue

        try:
            # Try to get port type from node
            node = port.node()
            if hasattr(node, "get_port_type"):
                data_type = node.get_port_type(port.name())
                if data_type:
                    # Import type registry to get color
                    from ...core.port_type_system import get_port_type_registry

                    registry = get_port_type_registry()
                    color_tuple = registry.get_type_color(data_type)
                    return QColor(*color_tuple)
        except Exception:
            pass

        return default_color

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint method with selection highlight (no visual resize handles)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Determine pen and brush based on state
        if self._is_drop_target:
            # Drop target: green highlight with lighter background
            pen = QPen(QColor(76, 175, 80), 3)  # Green border
            pen.setStyle(Qt.PenStyle.SolidLine)
            # Lighten the frame color for drop target
            drop_color = QColor(76, 175, 80, 40)  # Semi-transparent green
            brush = QBrush(drop_color)
        elif self.isSelected():
            pen = QPen(QColor(255, 215, 0), 3)  # Bright yellow, 3px thick
            pen.setStyle(Qt.PenStyle.SolidLine)
            brush = self.brush()
        elif self._is_collapsed:
            # Collapsed state: solid border, darker background
            pen = QPen(self.frame_color.darker(150), 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            brush = QBrush(self.frame_color.darker(110))
        else:
            pen = QPen(self.frame_color.darker(120), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            brush = self.brush()

        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 10, 10)

        # Draw node count indicator when collapsed
        if self._is_collapsed and self.contained_nodes:
            count_text = f"{len(self.contained_nodes)} nodes"
            painter.setPen(QPen(self.frame_color.lighter(180)))
            font = QFont("Segoe UI", 9)
            painter.setFont(font)
            text_rect = QRectF(
                rect.left() + 10, rect.bottom() - 20, rect.width() - 20, 15
            )
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                count_text,
            )

    def add_node(self, node):
        """
        Add a node to this frame's group.

        Args:
            node: Node to add to the frame
        """
        if node not in self.contained_nodes:
            self.contained_nodes.append(node)
            # Store the node's relative position to the frame
            if hasattr(node, "pos"):
                node_pos = node.pos()
                frame_pos = self.pos()
                # Store original position for movement tracking
                if not hasattr(node, "_frame_offset"):
                    node._frame_offset = (
                        node_pos[0] - frame_pos.x(),
                        node_pos[1] - frame_pos.y(),
                    )
                    node._parent_frame = self

    def remove_node(self, node):
        """
        Remove a node from this frame's group.

        Args:
            node: Node to remove from the frame
        """
        if node in self.contained_nodes:
            self.contained_nodes.remove(node)
            if hasattr(node, "_frame_offset"):
                delattr(node, "_frame_offset")
            if hasattr(node, "_parent_frame"):
                delattr(node, "_parent_frame")

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
                    if hasattr(node, "set_pos"):
                        current_pos = node.pos()
                        node.set_pos(current_pos[0] + delta_x, current_pos[1] + delta_y)
                        # Update the offset
                        if hasattr(node, "_frame_offset"):
                            node._frame_offset = (
                                current_pos[0] + delta_x - new_pos.x(),
                                current_pos[1] + delta_y - new_pos.y(),
                            )

        return super().itemChange(change, value)

    def _get_resize_corner(self, pos):
        """Determine if the position is at the bottom-right resize corner."""
        # Disable resizing when collapsed
        if self._is_collapsed:
            return None

        rect = self.rect()
        handle_size = self._resize_handle_size

        # Only check bottom-right corner
        br_rect = QRectF(
            rect.right() - handle_size,
            rect.bottom() - handle_size,
            handle_size,
            handle_size,
        )

        if br_rect.contains(pos):
            return "BR"
        return None

    def mousePressEvent(self, event):
        """Handle mouse press to track frame movement or start resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Ensure frame receives keyboard focus for key events (like X for delete)
            self.setFocus()

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
            if "R" in self._resize_corner:  # Right side
                new_rect.setRight(self._resize_start_rect.right() + delta.x())
            if "L" in self._resize_corner:  # Left side
                new_rect.setLeft(self._resize_start_rect.left() + delta.x())
            if "T" in self._resize_corner:  # Top side
                new_rect.setTop(self._resize_start_rect.top() + delta.y())
            if "B" in self._resize_corner:  # Bottom side
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
            else:
                self._is_moving = False
                # Check for nodes that should be ungrouped
                self._check_node_bounds()
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """Change cursor when hovering over the bottom-right resize corner."""
        if self.isSelected():
            corner = self._get_resize_corner(event.pos())
            if corner == "BR":
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
        # Skip bounds checking when collapsed - nodes are hidden and shouldn't be ungrouped
        if self._is_collapsed:
            return

        if not self.scene():
            return

        frame_rect = self.sceneBoundingRect()

        # Get all nodes from the graph reference
        all_nodes = []
        if NodeFrame._graph_ref:
            try:
                all_nodes = NodeFrame._graph_ref.all_nodes()
            except Exception:
                pass

        # Track if any node is being dragged over this frame
        has_hovering_node = False

        # Check contained nodes for ungrouping (moved outside frame)
        for node in list(self.contained_nodes):
            if hasattr(node, "view") and node.view:
                node_view = node.view
                if hasattr(node_view, "sceneBoundingRect"):
                    node_rect = node_view.sceneBoundingRect()

                    # Check if node is mostly outside the frame
                    intersection = frame_rect.intersected(node_rect)
                    node_area = node_rect.width() * node_rect.height()

                    if node_area > 0:
                        overlap_ratio = (
                            intersection.width() * intersection.height()
                        ) / node_area
                        if overlap_ratio < 0.25:
                            self.remove_node(node)

        # Check for nodes being dragged over the frame (for highlighting and auto-grouping)
        for node in all_nodes:
            if node in self.contained_nodes:
                continue  # Skip nodes already in this frame

            if not hasattr(node, "view") or not node.view:
                continue

            node_view = node.view
            if not hasattr(node_view, "sceneBoundingRect"):
                continue

            node_rect = node_view.sceneBoundingRect()

            # Check if node overlaps with frame
            intersection = frame_rect.intersected(node_rect)
            if intersection.width() <= 0 or intersection.height() <= 0:
                # Node doesn't overlap - remove from tracking
                node_id = id(node)
                if node_id in self._last_overlap_check:
                    del self._last_overlap_check[node_id]
                continue

            node_area = node_rect.width() * node_rect.height()
            if node_area <= 0:
                continue

            overlap_ratio = (intersection.width() * intersection.height()) / node_area
            node_id = id(node)

            try:
                current_pos = (float(node.pos()[0]), float(node.pos()[1]))
            except Exception:
                continue

            # If more than 25% of the node is inside the frame, show highlight
            if overlap_ratio > 0.25:
                has_hovering_node = True

                # Track this node's position
                if node_id in self._last_overlap_check:
                    last_pos, _ = self._last_overlap_check[node_id]
                    pos_changed = (
                        abs(last_pos[0] - current_pos[0]) > 2
                        or abs(last_pos[1] - current_pos[1]) > 2
                    )

                    # If position changed and overlap is very significant (70%+), add the node
                    # This higher threshold allows the green highlight to stay visible longer
                    if pos_changed and overlap_ratio > 0.7:
                        if not self._is_moving:
                            self.add_node(node)
                            if node_id in self._last_overlap_check:
                                del self._last_overlap_check[node_id]
                            continue

                # Update position tracking
                self._last_overlap_check[node_id] = (current_pos, overlap_ratio)
            else:
                # Remove from tracking if no longer overlapping
                if node_id in self._last_overlap_check:
                    del self._last_overlap_check[node_id]

        # Always update highlight state (force repaint if hovering)
        if self._is_drop_target != has_hovering_node:
            self._is_drop_target = has_hovering_node
            self.update()
        elif has_hovering_node:
            # Force update while hovering to keep visual state current
            self.update()

    def _edit_title(self):
        """Open a dialog to edit the frame title."""

        # Get the main window or any widget to parent the dialog
        parent = None
        if self.scene() and self.scene().views():
            parent = self.scene().views()[0]

        new_title, ok = QInputDialog.getText(
            parent, "Edit Frame Title", "Frame title:", text=self.frame_title
        )

        if ok and new_title:
            self.set_title(new_title)

    def contextMenuEvent(self, event):
        """Show context menu with frame options."""
        menu = QMenu()

        # Collapse/Expand action
        if self._is_collapsed:
            collapse_action = menu.addAction("Expand Frame")
            collapse_action.triggered.connect(self.expand)
        else:
            collapse_action = menu.addAction("Collapse Frame")
            collapse_action.triggered.connect(self.collapse)

        menu.addSeparator()

        # Rename action
        rename_action = menu.addAction("Rename Frame")
        rename_action.triggered.connect(self._edit_title)

        # Color submenu
        color_menu = menu.addMenu("Change Color")
        for name, color in FRAME_COLOR_PALETTE.items():
            action = color_menu.addAction(f"  {name}")
            # Use a lambda with default arg to capture the color value
            action.triggered.connect(lambda checked, c=color: self.set_color(c))

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
        if event.key() == Qt.Key.Key_X:
            self._delete_frame()
            event.accept()
        elif event.key() == Qt.Key.Key_C:
            # Toggle collapse with 'C' key
            self.toggle_collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _delete_frame(self, use_undo: bool = True):
        """
        Delete this frame from the scene.

        Args:
            use_undo: If True and graph is available, push to undo stack
        """
        scene = self.scene()
        if not scene:
            return

        # Try to use undo stack if available
        if use_undo and NodeFrame._graph_ref:
            try:
                undo_stack = NodeFrame._graph_ref.undo_stack()
                if undo_stack:
                    # Create and push undo command
                    cmd = FrameDeletedCmd(
                        self, scene, f"Delete Frame '{self.frame_title}'"
                    )
                    undo_stack.push(cmd)
                    return  # The redo() of the command will do the actual deletion
            except Exception:
                pass

        # Direct deletion (no undo)
        self._do_delete()

    def _do_delete(self):
        """Perform the actual frame deletion (used by undo command)."""
        # Unregister from centralized bounds manager
        if hasattr(self, "_bounds_manager") and self._bounds_manager:
            self._bounds_manager.unregister_frame(self)

        # Ungroup all contained nodes (but keep them in the scene)
        for node in list(self.contained_nodes):
            self.remove_node(node)

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize frame to dictionary for saving.

        Returns:
            Dictionary with frame data including position, size, color, and collapse state
        """
        pos = self.pos()
        rect = self.rect() if not self._is_collapsed else self._expanded_rect

        # Get color name from FRAME_COLORS or save RGBA
        color_name = None
        for name, color in FRAME_COLORS.items():
            if color == self.frame_color:
                color_name = name
                break

        # Get contained node IDs
        contained_node_ids = []
        for node in self.contained_nodes:
            if hasattr(node, "get_property"):
                node_id = node.get_property("node_id")
                if node_id:
                    contained_node_ids.append(node_id)

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
            "contained_nodes": contained_node_ids,
        }

    @classmethod
    def deserialize(
        cls, data: Dict[str, Any], node_map: Optional[Dict[str, Any]] = None
    ) -> "NodeFrame":
        """
        Create a frame from serialized data.

        Args:
            data: Serialized frame data
            node_map: Optional mapping of node_id to node objects for restoring containment

        Returns:
            NodeFrame instance
        """
        # Get color
        color_data = data.get("color", "gray")
        if isinstance(color_data, str):
            color = FRAME_COLORS.get(color_data, FRAME_COLORS["gray"])
        else:
            color = QColor(
                color_data.get("r", 100),
                color_data.get("g", 100),
                color_data.get("b", 100),
                color_data.get("a", 80),
            )

        # Get size
        size = data.get("size", {"width": 400, "height": 300})

        # Create frame
        frame = cls(
            title=data.get("title", "Group"),
            color=color,
            width=size.get("width", 400),
            height=size.get("height", 300),
        )

        # Set position
        pos = data.get("position", {"x": 0, "y": 0})
        frame.setPos(pos.get("x", 0), pos.get("y", 0))

        # Restore contained nodes if node_map provided
        if node_map:
            for node_id in data.get("contained_nodes", []):
                if node_id in node_map:
                    frame.add_node(node_map[node_id])

        # Restore collapsed state
        if data.get("is_collapsed", False):
            frame.collapse()

        return frame


# Pre-defined frame color themes
FRAME_COLORS = {
    "blue": QColor(100, 181, 246, 60),
    "purple": QColor(156, 39, 176, 60),
    "green": QColor(102, 187, 106, 60),
    "orange": QColor(255, 167, 38, 60),
    "red": QColor(239, 83, 80, 60),
    "yellow": QColor(255, 202, 40, 60),
    "teal": QColor(77, 182, 172, 60),
    "pink": QColor(236, 64, 122, 60),
    "gray": QColor(120, 120, 120, 60),
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
    size: Tuple[float, float] = (400, 300),
    graph=None,
) -> NodeFrame:
    """
    Create a node frame in the graph view.

    Args:
        graph_view: NodeGraph view to add frame to
        title: Frame title
        color_name: Color theme name from FRAME_COLORS
        position: (x, y) position tuple
        size: (width, height) size tuple
        graph: NodeGraph instance for node lookup (optional, will try to detect)

    Returns:
        Created NodeFrame instance
    """
    color = FRAME_COLORS.get(color_name, FRAME_COLORS["gray"])

    # Try to get graph reference if not provided
    if graph is None and hasattr(graph_view, "parent") and graph_view.parent():
        parent = graph_view.parent()
        if hasattr(parent, "graph"):
            graph = parent.graph
        elif hasattr(parent, "_graph"):
            graph = parent._graph

    # Set graph reference for all frames
    if graph:
        NodeFrame.set_graph(graph)

    frame = NodeFrame(title=title, color=color, width=size[0], height=size[1])

    # Add to scene
    scene = graph_view.scene()
    scene.addItem(frame)

    # Position the frame
    frame.setPos(position[0], position[1])

    return frame


def group_selected_nodes(
    graph_view, title: str = "Group", selected_nodes: List = None
) -> Optional[NodeFrame]:
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
        if hasattr(graph_view, "selected_nodes"):
            selected_nodes = graph_view.selected_nodes()
        else:
            return None

    if not selected_nodes:
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
    frame = create_frame(graph_view, title=title, position=(x, y), size=(width, height))

    # Add all selected nodes to the frame
    for node in selected_nodes:
        frame.add_node(node)

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
    group_action.triggered.connect(
        lambda: group_selected_nodes(graph_menu.graph, "Group")
    )
    frame_menu.addAction(group_action)

    frame_menu.addSeparator()

    # Add color theme actions
    for color_name in FRAME_COLORS.keys():
        action = QAction(f"Create {color_name.capitalize()} Frame", graph_menu)
        action.triggered.connect(
            lambda checked, c=color_name: create_frame(
                graph_menu.graph, title="Group", color_name=c, position=(0, 0)
            )
        )
        frame_menu.addAction(action)
