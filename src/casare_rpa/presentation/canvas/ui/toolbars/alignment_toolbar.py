"""
Alignment toolbar for quick node alignment operations.

Provides toolbar buttons for aligning and distributing selected nodes.

Epic 7.5: Migrated to THEME_V2/TOKENS_V2 design system.
- Uses THEME_V2/TOKENS_V2 for all styling
- Uses icon_v2 singleton for Lucide SVG icons
- Zero hardcoded colors
- Zero animations/shadows
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QToolBar, QWidget

from casare_rpa.presentation.canvas.graph.auto_layout_manager import (
    get_auto_layout_manager,
)
from casare_rpa.presentation.canvas.graph.node_aligner import (
    get_node_aligner,
)

# Epic 7.5: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme_system import (
    TOKENS_V2,
    get_toolbar_styles_v2,
    icon_v2,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_graph_widget import NodeGraphWidget


class AlignmentToolbar(QToolBar):
    """
    Toolbar for node alignment and distribution operations.

    Provides quick access to:
    - Align Left/Right/Top/Bottom
    - Align Center (Horizontal/Vertical)
    - Distribute Horizontal/Vertical
    - Auto-Layout

    Shortcuts use Alt+A prefix followed by direction key.
    """

    # Signals for action tracking
    alignment_performed = Signal(str)  # alignment_type
    layout_performed = Signal(str)  # layout_direction

    # Mapping of alignment names to v2 icon names (Epic 2.2)
    # Uses Lucide SVG icons when available, falls back to custom drawing
    _V2_ICON_MAP = {
        "align_left": "align-left",      # Need to add this SVG
        "align_right": "align-right",    # Need to add this SVG
        "align_top": "align-top",        # Need to add this SVG
        "align_bottom": "align-bottom",  # Need to add this SVG
        "align_center_h": "minus",
        "align_center_v": "minus",
        "distribute_h": "more-horizontal",
        "distribute_v": "more-vertical",
        "auto_layout": "branch",
        "layout_selection": "check",
    }

    def __init__(
        self,
        graph_widget: Optional["NodeGraphWidget"] = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the alignment toolbar.

        Args:
            graph_widget: NodeGraphWidget instance
            parent: Parent widget
        """
        super().__init__("Alignment", parent)

        self._graph_widget = graph_widget
        self._aligner = get_node_aligner()
        self._layout_manager = get_auto_layout_manager()

        self.setObjectName("AlignmentToolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(TOKENS_V2.sizes.icon_sm, TOKENS_V2.sizes.icon_sm))

        self._setup_styling()
        self._create_actions()
        self._create_layout()

    def set_graph_widget(self, graph_widget: "NodeGraphWidget") -> None:
        """Set the graph widget reference."""
        self._graph_widget = graph_widget
        if graph_widget and hasattr(graph_widget, "graph"):
            self._aligner.set_graph(graph_widget.graph)
            self._layout_manager.set_graph(graph_widget.graph)

    def _setup_styling(self) -> None:
        """Apply v2 dark theme using THEME_V2/TOKENS_V2 and get_toolbar_styles_v2()."""
        # Use the standardized v2 toolbar styles
        self.setStyleSheet(get_toolbar_styles_v2())

    def _create_actions(self) -> None:
        """Create all alignment actions."""
        # Alignment actions
        self.action_align_left = self._create_action(
            "align_left",
            "Align Left",
            "Alt+A, L",
            "Align selected nodes to left edge",
            self._on_align_left,
        )
        self.action_align_right = self._create_action(
            "align_right",
            "Align Right",
            "Alt+A, R",
            "Align selected nodes to right edge",
            self._on_align_right,
        )
        self.action_align_top = self._create_action(
            "align_top",
            "Align Top",
            "Alt+A, T",
            "Align selected nodes to top edge",
            self._on_align_top,
        )
        self.action_align_bottom = self._create_action(
            "align_bottom",
            "Align Bottom",
            "Alt+A, B",
            "Align selected nodes to bottom edge",
            self._on_align_bottom,
        )
        self.action_align_center_h = self._create_action(
            "align_center_h",
            "Align Center Horizontal",
            "Alt+A, C",
            "Align selected nodes to horizontal center",
            self._on_align_center_h,
        )
        self.action_align_center_v = self._create_action(
            "align_center_v",
            "Align Center Vertical",
            "Alt+A, M",
            "Align selected nodes to vertical center (middle)",
            self._on_align_center_v,
        )

        # Distribution actions
        self.action_distribute_h = self._create_action(
            "distribute_h",
            "Distribute Horizontal",
            "Alt+A, H",
            "Distribute selected nodes evenly horizontally",
            self._on_distribute_h,
        )
        self.action_distribute_v = self._create_action(
            "distribute_v",
            "Distribute Vertical",
            "Alt+A, V",
            "Distribute selected nodes evenly vertically",
            self._on_distribute_v,
        )

        # Auto-layout actions
        self.action_auto_layout = self._create_action(
            "auto_layout",
            "Auto-Layout",
            "Ctrl+L",
            "Automatically arrange all nodes",
            self._on_auto_layout,
        )
        self.action_layout_selection = self._create_action(
            "layout_selection",
            "Layout Selection",
            "Ctrl+Shift+L",
            "Automatically arrange selected nodes",
            self._on_layout_selection,
        )

    def _create_action(
        self, name: str, text: str, shortcut: str | None, tooltip: str, handler
    ) -> QAction:
        """Create a toolbar action with icon."""
        action = QAction(text, self)
        action.setIcon(self._create_icon(name))

        if shortcut:
            action.setShortcut(QKeySequence(shortcut))

        action.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)
        action.triggered.connect(handler)

        return action

    def _create_icon(self, name: str) -> QIcon:
        """Create icon for alignment actions using icon_v2."""
        # Epic 7.5: Use v2 icons (Lucide SVG)
        v2_name = self._V2_ICON_MAP.get(name)
        if v2_name and icon_v2.has_icon(v2_name):
            return icon_v2.get_icon(v2_name, size=TOKENS_V2.sizes.icon_sm, state="normal")
        # Fallback to custom drawing if v2 icon not available
        logger.debug(f"V2 icon not found: {v2_name}, using custom drawing")
        size = TOKENS_V2.sizes.icon_sm
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#a0a0a0"), 1.5)
        painter.setPen(pen)

        # Draw icon based on name
        if name == "align_left":
            self._draw_align_left_icon(painter, size)
        elif name == "align_right":
            self._draw_align_right_icon(painter, size)
        elif name == "align_top":
            self._draw_align_top_icon(painter, size)
        elif name == "align_bottom":
            self._draw_align_bottom_icon(painter, size)
        elif name == "align_center_h":
            self._draw_align_center_h_icon(painter, size)
        elif name == "align_center_v":
            self._draw_align_center_v_icon(painter, size)
        elif name == "distribute_h":
            self._draw_distribute_h_icon(painter, size)
        elif name == "distribute_v":
            self._draw_distribute_v_icon(painter, size)
        elif name == "auto_layout":
            self._draw_auto_layout_icon(painter, size)
        elif name == "layout_selection":
            self._draw_layout_selection_icon(painter, size)

        painter.end()
        return QIcon(pixmap)

    def _draw_align_left_icon(self, p: QPainter, s: int) -> None:
        """Draw align left icon."""
        # Vertical line on left
        p.drawLine(2, 2, 2, s - 2)
        # Two rectangles aligned to left
        p.drawRect(4, 3, 8, 4)
        p.drawRect(4, 9, 5, 4)

    def _draw_align_right_icon(self, p: QPainter, s: int) -> None:
        """Draw align right icon."""
        # Vertical line on right
        p.drawLine(s - 3, 2, s - 3, s - 2)
        # Two rectangles aligned to right
        p.drawRect(4, 3, 8, 4)
        p.drawRect(7, 9, 5, 4)

    def _draw_align_top_icon(self, p: QPainter, s: int) -> None:
        """Draw align top icon."""
        # Horizontal line on top
        p.drawLine(2, 2, s - 2, 2)
        # Two rectangles aligned to top
        p.drawRect(3, 4, 4, 8)
        p.drawRect(9, 4, 4, 5)

    def _draw_align_bottom_icon(self, p: QPainter, s: int) -> None:
        """Draw align bottom icon."""
        # Horizontal line on bottom
        p.drawLine(2, s - 3, s - 2, s - 3)
        # Two rectangles aligned to bottom
        p.drawRect(3, 4, 4, 8)
        p.drawRect(9, 7, 4, 5)

    def _draw_align_center_h_icon(self, p: QPainter, s: int) -> None:
        """Draw align center horizontal icon."""
        # Horizontal center line
        center_y = s // 2
        p.drawLine(2, center_y, s - 2, center_y)
        # Two rectangles centered vertically
        p.drawRect(3, center_y - 4, 4, 8)
        p.drawRect(9, center_y - 3, 4, 6)

    def _draw_align_center_v_icon(self, p: QPainter, s: int) -> None:
        """Draw align center vertical icon."""
        # Vertical center line
        center_x = s // 2
        p.drawLine(center_x, 2, center_x, s - 2)
        # Two rectangles centered horizontally
        p.drawRect(center_x - 4, 3, 8, 4)
        p.drawRect(center_x - 3, 9, 6, 4)

    def _draw_distribute_h_icon(self, p: QPainter, s: int) -> None:
        """Draw distribute horizontal icon."""
        # Three rectangles evenly spaced
        p.drawRect(1, 4, 3, 8)
        p.drawRect(6, 4, 3, 8)
        p.drawRect(11, 4, 3, 8)
        # Spacing indicators
        p.drawLine(4, s // 2, 6, s // 2)
        p.drawLine(9, s // 2, 11, s // 2)

    def _draw_distribute_v_icon(self, p: QPainter, s: int) -> None:
        """Draw distribute vertical icon."""
        # Three rectangles evenly spaced
        p.drawRect(4, 1, 8, 3)
        p.drawRect(4, 6, 8, 3)
        p.drawRect(4, 11, 8, 3)
        # Spacing indicators
        p.drawLine(s // 2, 4, s // 2, 6)
        p.drawLine(s // 2, 9, s // 2, 11)

    def _draw_auto_layout_icon(self, p: QPainter, s: int) -> None:
        """Draw auto-layout icon (tree-like structure)."""
        # Root node
        p.drawRect(s // 2 - 2, 1, 4, 3)
        # Level 2 nodes
        p.drawRect(2, 6, 4, 3)
        p.drawRect(s - 6, 6, 4, 3)
        # Level 3 nodes
        p.drawRect(1, 11, 3, 3)
        p.drawRect(4, 11, 3, 3)
        # Connection lines
        p.drawLine(s // 2, 4, s // 2, 5)
        p.drawLine(4, 5, s - 4, 5)
        p.drawLine(4, 5, 4, 6)
        p.drawLine(s - 4, 5, s - 4, 6)

    def _draw_layout_selection_icon(self, p: QPainter, s: int) -> None:
        """Draw layout selection icon."""
        # Similar to auto-layout but with selection indicator
        self._draw_auto_layout_icon(p, s)
        # Add selection border (solid)
        pen = p.pen()
        pen.setStyle(Qt.PenStyle.SolidLine)
        p.setPen(pen)
        p.drawRect(0, 0, s - 1, s - 1)

    def _create_layout(self) -> None:
        """Add actions to toolbar."""
        # Alignment group
        self.addAction(self.action_align_left)
        self.addAction(self.action_align_center_v)
        self.addAction(self.action_align_right)

        self.addSeparator()

        self.addAction(self.action_align_top)
        self.addAction(self.action_align_center_h)
        self.addAction(self.action_align_bottom)

        self.addSeparator()

        # Distribution group
        self.addAction(self.action_distribute_h)
        self.addAction(self.action_distribute_v)

        self.addSeparator()

        # Auto-layout group
        self.addAction(self.action_auto_layout)
        self.addAction(self.action_layout_selection)

    def _get_selected_nodes(self) -> list:
        """Get currently selected nodes from graph."""
        if not self._graph_widget:
            return []

        try:
            return self._graph_widget.graph.selected_nodes()
        except Exception as e:
            logger.debug(f"Error getting selected nodes: {e}")
            return []

    def _check_selection(self, min_count: int = 2) -> bool:
        """Check if enough nodes are selected for operation."""
        nodes = self._get_selected_nodes()
        if len(nodes) < min_count:
            logger.info(f"Need at least {min_count} selected nodes for this operation")
            return False
        return True

    # =========================================================================
    # ACTION HANDLERS
    # =========================================================================

    def _on_align_left(self) -> None:
        """Handle align left action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_left(nodes)
        self.alignment_performed.emit("left")
        logger.debug("Aligned nodes to left")

    def _on_align_right(self) -> None:
        """Handle align right action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_right(nodes)
        self.alignment_performed.emit("right")
        logger.debug("Aligned nodes to right")

    def _on_align_top(self) -> None:
        """Handle align top action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_top(nodes)
        self.alignment_performed.emit("top")
        logger.debug("Aligned nodes to top")

    def _on_align_bottom(self) -> None:
        """Handle align bottom action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_bottom(nodes)
        self.alignment_performed.emit("bottom")
        logger.debug("Aligned nodes to bottom")

    def _on_align_center_h(self) -> None:
        """Handle align center horizontal action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_center_horizontal(nodes)
        self.alignment_performed.emit("center_h")
        logger.debug("Aligned nodes to horizontal center")

    def _on_align_center_v(self) -> None:
        """Handle align center vertical action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._aligner.align_center_vertical(nodes)
        self.alignment_performed.emit("center_v")
        logger.debug("Aligned nodes to vertical center")

    def _on_distribute_h(self) -> None:
        """Handle distribute horizontal action."""
        if not self._check_selection(3):
            return

        nodes = self._get_selected_nodes()
        self._aligner.distribute_horizontal(nodes)
        self.alignment_performed.emit("distribute_h")
        logger.debug("Distributed nodes horizontally")

    def _on_distribute_v(self) -> None:
        """Handle distribute vertical action."""
        if not self._check_selection(3):
            return

        nodes = self._get_selected_nodes()
        self._aligner.distribute_vertical(nodes)
        self.alignment_performed.emit("distribute_v")
        logger.debug("Distributed nodes vertically")

    def _on_auto_layout(self) -> None:
        """Handle auto-layout action."""
        if not self._graph_widget:
            return

        self._layout_manager.layout_workflow(direction="LR")
        self.layout_performed.emit("auto")
        logger.debug("Applied auto-layout to workflow")

    def _on_layout_selection(self) -> None:
        """Handle layout selection action."""
        if not self._check_selection(2):
            return

        nodes = self._get_selected_nodes()
        self._layout_manager.layout_selection(nodes, direction="LR")
        self.layout_performed.emit("selection")
        logger.debug("Applied auto-layout to selection")

    def update_enabled_state(self) -> None:
        """Update action enabled states based on selection."""
        nodes = self._get_selected_nodes()
        has_selection = len(nodes) >= 2
        has_distribution = len(nodes) >= 3

        # Alignment needs 2+ nodes
        self.action_align_left.setEnabled(has_selection)
        self.action_align_right.setEnabled(has_selection)
        self.action_align_top.setEnabled(has_selection)
        self.action_align_bottom.setEnabled(has_selection)
        self.action_align_center_h.setEnabled(has_selection)
        self.action_align_center_v.setEnabled(has_selection)
        self.action_layout_selection.setEnabled(has_selection)

        # Distribution needs 3+ nodes
        self.action_distribute_h.setEnabled(has_distribution)
        self.action_distribute_v.setEnabled(has_distribution)
