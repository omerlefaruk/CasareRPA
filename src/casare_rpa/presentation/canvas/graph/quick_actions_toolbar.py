"""
Quick Actions Toolbar for CasareRPA Nodes.

Provides a floating toolbar that appears on node hover with quick access to:
- Delete node
- Duplicate node
- Disable/Enable toggle

Appears after 500ms hover delay, positioned above the node.
Uses a cached/pooled toolbar instance for performance.

Design follows VSCode dark theme styling.
"""

from typing import Optional, Callable, TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsProxyWidget,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
)

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.custom_node_item import CasareNodeItem


# =============================================================================
# Toolbar Styling
# =============================================================================

TOOLBAR_BUTTON_STYLE = """
QPushButton {{
    background: {bg};
    border: none;
    border-radius: 3px;
    color: {fg};
    font-size: 12px;
    font-weight: bold;
    min-width: 24px;
    min-height: 24px;
    padding: 2px;
}}
QPushButton:hover {{
    background: {hover_bg};
    color: {hover_fg};
}}
QPushButton:pressed {{
    background: {pressed_bg};
}}
"""

# Colors for different button types
BUTTON_COLORS = {
    "delete": {
        "bg": "#3c3c4a",
        "fg": "#cccccc",
        "hover_bg": "#f44336",
        "hover_fg": "#ffffff",
        "pressed_bg": "#d32f2f",
    },
    "duplicate": {
        "bg": "#3c3c4a",
        "fg": "#cccccc",
        "hover_bg": "#4CAF50",
        "hover_fg": "#ffffff",
        "pressed_bg": "#388E3C",
    },
    "disable": {
        "bg": "#3c3c4a",
        "fg": "#cccccc",
        "hover_bg": "#FF9800",
        "hover_fg": "#ffffff",
        "pressed_bg": "#F57C00",
    },
}

TOOLBAR_BG_COLOR = QColor(45, 45, 55, 230)  # Semi-transparent dark
TOOLBAR_BORDER_COLOR = QColor(80, 80, 90)


# =============================================================================
# Quick Action Button
# =============================================================================


class QuickActionButton(QPushButton):
    """
    Individual quick action button with icon and tooltip.

    Uses Unicode symbols for icons to avoid external dependencies.
    """

    def __init__(
        self,
        symbol: str,
        tooltip: str,
        button_type: str = "default",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the button.

        Args:
            symbol: Unicode symbol or text to display
            tooltip: Tooltip text
            button_type: Type key for color scheme (delete, duplicate, disable)
            parent: Parent widget
        """
        super().__init__(symbol, parent)

        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Apply styling based on button type
        colors = BUTTON_COLORS.get(button_type, BUTTON_COLORS["duplicate"])
        self.setStyleSheet(TOOLBAR_BUTTON_STYLE.format(**colors))


# =============================================================================
# Quick Actions Toolbar Widget
# =============================================================================


class QuickActionsToolbarWidget(QWidget):
    """
    Widget containing quick action buttons.

    This widget is embedded in a QGraphicsProxyWidget for use in the node graph.

    Signals:
        delete_clicked: Emitted when delete button is clicked
        duplicate_clicked: Emitted when duplicate button is clicked
        disable_clicked: Emitted when disable/enable button is clicked
    """

    delete_clicked = Signal()
    duplicate_clicked = Signal()
    disable_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the toolbar widget."""
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(32)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Delete button (X symbol)
        self._delete_btn = QuickActionButton(
            symbol="X",
            tooltip="Delete node (Del)",
            button_type="delete",
        )
        self._delete_btn.clicked.connect(self.delete_clicked.emit)
        layout.addWidget(self._delete_btn)

        # Duplicate button (copy symbol)
        self._duplicate_btn = QuickActionButton(
            symbol="+",
            tooltip="Duplicate node (Ctrl+D)",
            button_type="duplicate",
        )
        self._duplicate_btn.clicked.connect(self.duplicate_clicked.emit)
        layout.addWidget(self._duplicate_btn)

        # Disable/Enable button (eye symbol)
        self._disable_btn = QuickActionButton(
            symbol="D",
            tooltip="Disable/Enable node",
            button_type="disable",
        )
        self._disable_btn.clicked.connect(self.disable_clicked.emit)
        layout.addWidget(self._disable_btn)

        # Adjust minimum width to fit all buttons
        self.setMinimumWidth(
            len([self._delete_btn, self._duplicate_btn, self._disable_btn]) * 28 + 16
        )

    def update_disable_button(self, is_disabled: bool) -> None:
        """
        Update the disable button appearance based on node state.

        Args:
            is_disabled: True if node is currently disabled
        """
        if is_disabled:
            self._disable_btn.setText("E")  # Enable
            self._disable_btn.setToolTip("Enable node")
        else:
            self._disable_btn.setText("D")  # Disable
            self._disable_btn.setToolTip("Disable node")


# =============================================================================
# Quick Actions Toolbar Graphics Item
# =============================================================================


class QuickActionsToolbar(QGraphicsProxyWidget):
    """
    Graphics proxy widget for the quick actions toolbar.

    This is the actual item that gets added to the scene and positioned
    above nodes on hover.

    Features:
    - Appears after 500ms hover delay
    - Positioned above the hovered node
    - Hides when mouse leaves node
    - Cached/reused instance for performance
    """

    # Hover delay in milliseconds
    HOVER_DELAY_MS = 500

    # Singleton instance for reuse
    _instance: Optional["QuickActionsToolbar"] = None
    _target_node: Optional["CasareNodeItem"] = None

    @classmethod
    def get_instance(cls, scene=None) -> "QuickActionsToolbar":
        """
        Get or create the singleton toolbar instance.

        Args:
            scene: QGraphicsScene to add toolbar to (only needed on first call)

        Returns:
            The singleton QuickActionsToolbar instance
        """
        if cls._instance is None:
            cls._instance = cls()
            if scene:
                scene.addItem(cls._instance)
        return cls._instance

    @classmethod
    def has_instance(cls) -> bool:
        """Check if an instance exists."""
        return cls._instance is not None

    def __init__(self, parent: Optional[QGraphicsItem] = None) -> None:
        """Initialize the toolbar graphics item."""
        super().__init__(parent)

        # Create the widget
        self._toolbar_widget = QuickActionsToolbarWidget()
        self.setWidget(self._toolbar_widget)

        # Hide by default
        self.setVisible(False)

        # High Z-value to appear above nodes
        self.setZValue(10000)

        # Timer for hover delay
        self._hover_timer = QTimer()
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._on_hover_timeout)

        # Pending target node (set on hover start, used on timeout)
        self._pending_node: Optional["CasareNodeItem"] = None

        # Action callbacks
        self._on_delete: Optional[Callable] = None
        self._on_duplicate: Optional[Callable] = None
        self._on_disable: Optional[Callable] = None

        # Connect widget signals to internal handlers
        self._toolbar_widget.delete_clicked.connect(self._handle_delete)
        self._toolbar_widget.duplicate_clicked.connect(self._handle_duplicate)
        self._toolbar_widget.disable_clicked.connect(self._handle_disable)

    def set_action_callbacks(
        self,
        on_delete: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        on_disable: Optional[Callable] = None,
    ) -> None:
        """
        Set callbacks for toolbar actions.

        Args:
            on_delete: Callback when delete is clicked (receives node)
            on_duplicate: Callback when duplicate is clicked (receives node)
            on_disable: Callback when disable is clicked (receives node)
        """
        self._on_delete = on_delete
        self._on_duplicate = on_duplicate
        self._on_disable = on_disable

    def start_hover(self, node: "CasareNodeItem") -> None:
        """
        Start the hover delay timer for a node.

        Called when mouse enters a node's bounding rect.

        Args:
            node: The CasareNodeItem being hovered
        """
        # If already showing for this node, do nothing
        if self.isVisible() and QuickActionsToolbar._target_node == node:
            return

        # Cancel any pending hover
        self._hover_timer.stop()

        # Set pending node and start timer
        self._pending_node = node
        self._hover_timer.start(self.HOVER_DELAY_MS)

    def cancel_hover(self) -> None:
        """
        Cancel the hover delay timer.

        Called when mouse leaves a node's bounding rect.
        """
        self._hover_timer.stop()
        self._pending_node = None

    def hide_toolbar(self) -> None:
        """
        Hide the toolbar immediately.

        Called when the mouse leaves both the node and the toolbar.
        """
        self._hover_timer.stop()
        self._pending_node = None
        QuickActionsToolbar._target_node = None
        self.setVisible(False)

    def _on_hover_timeout(self) -> None:
        """Handle hover timer timeout - show the toolbar."""
        if self._pending_node is None:
            return

        # Store target node
        QuickActionsToolbar._target_node = self._pending_node

        # Update disable button state
        is_disabled = self._pending_node.is_disabled()
        self._toolbar_widget.update_disable_button(is_disabled)

        # Position above the node
        self._position_above_node(self._pending_node)

        # Show toolbar
        self.setVisible(True)

        # Clear pending
        self._pending_node = None

    def _position_above_node(self, node: "CasareNodeItem") -> None:
        """
        Position the toolbar above the given node.

        Args:
            node: The node to position above
        """
        node_rect = node.boundingRect()
        node_pos = node.pos()

        # Calculate position (centered above node)
        toolbar_width = self._toolbar_widget.width()
        x = node_pos.x() + node_rect.center().x() - toolbar_width / 2
        y = node_pos.y() + node_rect.top() - self._toolbar_widget.height() - 8

        self.setPos(x, y)

    def _handle_delete(self) -> None:
        """Handle delete button click."""
        if QuickActionsToolbar._target_node and self._on_delete:
            try:
                self._on_delete(QuickActionsToolbar._target_node)
            except Exception as e:
                logger.error(f"Error in delete callback: {e}")
        self.hide_toolbar()

    def _handle_duplicate(self) -> None:
        """Handle duplicate button click."""
        if QuickActionsToolbar._target_node and self._on_duplicate:
            try:
                self._on_duplicate(QuickActionsToolbar._target_node)
            except Exception as e:
                logger.error(f"Error in duplicate callback: {e}")
        self.hide_toolbar()

    def _handle_disable(self) -> None:
        """Handle disable button click."""
        if QuickActionsToolbar._target_node and self._on_disable:
            try:
                self._on_disable(QuickActionsToolbar._target_node)
            except Exception as e:
                logger.error(f"Error in disable callback: {e}")

            # Update button text after toggling
            if QuickActionsToolbar._target_node:
                is_disabled = QuickActionsToolbar._target_node.is_disabled()
                self._toolbar_widget.update_disable_button(is_disabled)

    def is_over_toolbar(self, scene_pos: QPointF) -> bool:
        """
        Check if a scene position is over the toolbar.

        Args:
            scene_pos: Position in scene coordinates

        Returns:
            True if position is over the toolbar
        """
        if not self.isVisible():
            return False
        return self.sceneBoundingRect().contains(scene_pos)

    @classmethod
    def get_target_node(cls) -> Optional["CasareNodeItem"]:
        """Get the currently targeted node."""
        return cls._target_node


# =============================================================================
# Hover Manager for Node Graph
# =============================================================================


class NodeHoverManager:
    """
    Manages hover detection and toolbar display for nodes.

    This class handles:
    - Tracking mouse movement over nodes
    - Managing the 500ms hover delay
    - Keeping toolbar visible when mouse moves to toolbar
    - Hiding toolbar when mouse leaves both node and toolbar

    Usage:
        manager = NodeHoverManager(graph_widget)
        manager.set_action_callbacks(on_delete=..., on_duplicate=..., on_disable=...)
        # Manager automatically handles hover events via graph widget event filter
    """

    def __init__(self, graph_widget: "QGraphicsView") -> None:
        """
        Initialize the hover manager.

        Args:
            graph_widget: The NodeGraphQt graph widget
        """
        self._graph_widget = graph_widget
        self._toolbar: Optional[QuickActionsToolbar] = None
        self._current_hover_node: Optional["CasareNodeItem"] = None

        # Initialize toolbar with scene
        scene = graph_widget.scene()
        if scene:
            self._toolbar = QuickActionsToolbar.get_instance(scene)

    def set_action_callbacks(
        self,
        on_delete: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        on_disable: Optional[Callable] = None,
    ) -> None:
        """
        Set callbacks for toolbar actions.

        Args:
            on_delete: Callback when delete is clicked (receives node item)
            on_duplicate: Callback when duplicate is clicked (receives node item)
            on_disable: Callback when disable is clicked (receives node item)
        """
        if self._toolbar:
            self._toolbar.set_action_callbacks(on_delete, on_duplicate, on_disable)

    def on_mouse_move(self, scene_pos: QPointF) -> None:
        """
        Handle mouse movement in the scene.

        Call this from the graph widget's mouse move handler.

        Args:
            scene_pos: Mouse position in scene coordinates
        """
        if not self._toolbar:
            return

        # Check if over toolbar
        if self._toolbar.is_over_toolbar(scene_pos):
            # Keep toolbar visible
            return

        # Find node under cursor
        scene = self._graph_widget.scene()
        if not scene:
            return

        items = scene.items(scene_pos)
        node_item = None
        for item in items:
            # Check if item is a CasareNodeItem
            if hasattr(item, "is_disabled") and hasattr(item, "set_running"):
                node_item = item
                break

        if node_item:
            if node_item != self._current_hover_node:
                # New node - start hover delay
                self._current_hover_node = node_item
                self._toolbar.start_hover(node_item)
        else:
            # Not over any node
            if self._current_hover_node:
                self._current_hover_node = None
                self._toolbar.cancel_hover()

            # Hide toolbar if not over it
            if self._toolbar.isVisible() and not self._toolbar.is_over_toolbar(
                scene_pos
            ):
                self._toolbar.hide_toolbar()

    def on_mouse_leave(self) -> None:
        """
        Handle mouse leaving the graph widget.

        Call this from the graph widget's leave event handler.
        """
        if self._toolbar:
            self._current_hover_node = None
            self._toolbar.hide_toolbar()

    def hide_toolbar(self) -> None:
        """Force hide the toolbar."""
        if self._toolbar:
            self._toolbar.hide_toolbar()
            self._current_hover_node = None


__all__ = [
    "QuickActionsToolbar",
    "QuickActionsToolbarWidget",
    "QuickActionButton",
    "NodeHoverManager",
]
