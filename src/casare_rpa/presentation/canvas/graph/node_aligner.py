"""
Node alignment utility for quick alignment operations.

Provides functions to align selected nodes to common edges
(left, right, top, bottom, center) and distribute them evenly.
"""

from enum import Enum
from typing import Any

from loguru import logger
from PySide6.QtCore import QEasingCurve, QObject, QPointF, QPropertyAnimation, Signal
from PySide6.QtWidgets import QGraphicsItem


class AlignmentType(Enum):
    """Types of alignment operations."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER_HORIZONTAL = "center_h"
    CENTER_VERTICAL = "center_v"


class DistributeType(Enum):
    """Types of distribution operations."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class NodeAligner(QObject):
    """
    Utility class for node alignment operations.

    Provides methods to:
    - Align nodes to edges (left, right, top, bottom, center)
    - Distribute nodes evenly (horizontal, vertical)
    - Support animated transitions

    Usage:
        aligner = NodeAligner(graph)

        # Align selected nodes to left edge
        aligner.align_left(selected_nodes)

        # Distribute nodes horizontally
        aligner.distribute_horizontal(selected_nodes)
    """

    # Signal emitted when alignment completes
    alignment_completed = Signal()

    # Signal emitted for undo support
    positions_changed = Signal(dict)  # Dict[node_id, Tuple[old_pos, new_pos]]

    def __init__(
        self,
        graph: Any = None,
        animate: bool = True,
        animation_duration: int = 200,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the node aligner.

        Args:
            graph: NodeGraph instance (optional)
            animate: Whether to animate position changes
            animation_duration: Duration of animation in milliseconds
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph
        self._animate = animate
        self._animation_duration = animation_duration
        self._animations: list[QPropertyAnimation] = []
        self._pending_animations = 0

    def set_graph(self, graph: Any) -> None:
        """Set the graph instance."""
        self._graph = graph

    @property
    def animate(self) -> bool:
        """Check if animation is enabled."""
        return self._animate

    def set_animate(self, enabled: bool) -> None:
        """Enable or disable animation."""
        self._animate = enabled

    @property
    def animation_duration(self) -> int:
        """Get animation duration in milliseconds."""
        return self._animation_duration

    def set_animation_duration(self, duration: int) -> None:
        """Set animation duration in milliseconds."""
        self._animation_duration = max(50, min(1000, duration))

    # =========================================================================
    # ALIGNMENT OPERATIONS
    # =========================================================================

    def align_left(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the leftmost node's left edge.

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        if not positions:
            return {}

        # Find minimum X (leftmost edge)
        min_x = min(pos.x() for pos in positions.values())

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions:
                continue

            old_pos = positions[node_id]
            new_pos = QPointF(min_x, old_pos.y())

            if old_pos.x() != min_x:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    def align_right(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the rightmost node's right edge.

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Find maximum right edge
        max_right = max(rect.right() for rect in rects.values())

        # Calculate new positions (align right edges)
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions or node_id not in rects:
                continue

            old_pos = positions[node_id]
            node_width = rects[node_id].width()
            new_x = max_right - node_width
            new_pos = QPointF(new_x, old_pos.y())

            if abs(old_pos.x() - new_x) > 0.5:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    def align_top(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the topmost node's top edge.

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        if not positions:
            return {}

        # Find minimum Y (topmost edge)
        min_y = min(pos.y() for pos in positions.values())

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions:
                continue

            old_pos = positions[node_id]
            new_pos = QPointF(old_pos.x(), min_y)

            if old_pos.y() != min_y:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    def align_bottom(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the bottommost node's bottom edge.

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Find maximum bottom edge
        max_bottom = max(rect.bottom() for rect in rects.values())

        # Calculate new positions (align bottom edges)
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions or node_id not in rects:
                continue

            old_pos = positions[node_id]
            node_height = rects[node_id].height()
            new_y = max_bottom - node_height
            new_pos = QPointF(old_pos.x(), new_y)

            if abs(old_pos.y() - new_y) > 0.5:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    def align_center_horizontal(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the horizontal center (same Y center).

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Calculate average center Y
        centers = [rect.center().y() for rect in rects.values()]
        avg_center_y = sum(centers) / len(centers)

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions or node_id not in rects:
                continue

            old_pos = positions[node_id]
            node_height = rects[node_id].height()
            new_y = avg_center_y - node_height / 2
            new_pos = QPointF(old_pos.x(), new_y)

            if abs(old_pos.y() - new_y) > 0.5:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    def align_center_vertical(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Align nodes to the vertical center (same X center).

        Args:
            nodes: List of node items to align

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 2:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Calculate average center X
        centers = [rect.center().x() for rect in rects.values()]
        avg_center_x = sum(centers) / len(centers)

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            if node_id not in positions or node_id not in rects:
                continue

            old_pos = positions[node_id]
            node_width = rects[node_id].width()
            new_x = avg_center_x - node_width / 2
            new_pos = QPointF(new_x, old_pos.y())

            if abs(old_pos.x() - new_x) > 0.5:
                changes[node_id] = (old_pos, new_pos)

        self._apply_positions(nodes, changes)
        return changes

    # =========================================================================
    # DISTRIBUTION OPERATIONS
    # =========================================================================

    def distribute_horizontal(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Distribute nodes evenly horizontally.

        Keeps leftmost and rightmost nodes in place,
        distributes others evenly between them.

        Args:
            nodes: List of node items to distribute

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 3:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Sort nodes by X position
        sorted_nodes = sorted(
            [
                (node, self._get_node_id(node), positions[self._get_node_id(node)].x())
                for node in nodes
                if self._get_node_id(node) in positions
            ],
            key=lambda x: x[2],
        )

        if len(sorted_nodes) < 3:
            return {}

        # Get bounds
        first_node, first_id, first_x = sorted_nodes[0]
        last_node, last_id, last_x = sorted_nodes[-1]
        first_right = rects[first_id].right()
        last_left = rects[last_id].left()

        # Calculate total width of middle nodes
        middle_total_width = sum(
            rects[self._get_node_id(node)].width() for node, _, _ in sorted_nodes[1:-1]
        )

        # Calculate spacing
        available_space = last_left - first_right
        num_gaps = len(sorted_nodes) - 1
        gap_width = (available_space - middle_total_width) / num_gaps if num_gaps > 0 else 0

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        current_x = first_right + gap_width

        for _node, node_id, _ in sorted_nodes[1:-1]:
            old_pos = positions[node_id]
            new_pos = QPointF(current_x, old_pos.y())

            if abs(old_pos.x() - current_x) > 0.5:
                changes[node_id] = (old_pos, new_pos)

            current_x += rects[node_id].width() + gap_width

        self._apply_positions(nodes, changes)
        return changes

    def distribute_vertical(self, nodes: list[Any]) -> dict[str, tuple[QPointF, QPointF]]:
        """
        Distribute nodes evenly vertically.

        Keeps topmost and bottommost nodes in place,
        distributes others evenly between them.

        Args:
            nodes: List of node items to distribute

        Returns:
            Dictionary of node_id -> (old_pos, new_pos) for undo support
        """
        if len(nodes) < 3:
            return {}

        positions = self._get_node_positions(nodes)
        rects = self._get_node_rects(nodes)

        if not positions or not rects:
            return {}

        # Sort nodes by Y position
        sorted_nodes = sorted(
            [
                (node, self._get_node_id(node), positions[self._get_node_id(node)].y())
                for node in nodes
                if self._get_node_id(node) in positions
            ],
            key=lambda x: x[2],
        )

        if len(sorted_nodes) < 3:
            return {}

        # Get bounds
        first_node, first_id, first_y = sorted_nodes[0]
        last_node, last_id, last_y = sorted_nodes[-1]
        first_bottom = rects[first_id].bottom()
        last_top = rects[last_id].top()

        # Calculate total height of middle nodes
        middle_total_height = sum(
            rects[self._get_node_id(node)].height() for node, _, _ in sorted_nodes[1:-1]
        )

        # Calculate spacing
        available_space = last_top - first_bottom
        num_gaps = len(sorted_nodes) - 1
        gap_height = (available_space - middle_total_height) / num_gaps if num_gaps > 0 else 0

        # Calculate new positions
        changes: dict[str, tuple[QPointF, QPointF]] = {}
        current_y = first_bottom + gap_height

        for _node, node_id, _ in sorted_nodes[1:-1]:
            old_pos = positions[node_id]
            new_pos = QPointF(old_pos.x(), current_y)

            if abs(old_pos.y() - current_y) > 0.5:
                changes[node_id] = (old_pos, new_pos)

            current_y += rects[node_id].height() + gap_height

        self._apply_positions(nodes, changes)
        return changes

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_node_id(self, node: Any) -> str:
        """Extract node ID from a node object."""
        if hasattr(node, "id"):
            return str(node.id)
        if hasattr(node, "get_property"):
            try:
                return node.get_property("node_id") or str(id(node))
            except Exception:
                pass
        return str(id(node))

    def _get_node_positions(self, nodes: list[Any]) -> dict[str, QPointF]:
        """Get current positions of nodes."""
        positions: dict[str, QPointF] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            try:
                if hasattr(node, "pos"):
                    pos = node.pos()
                    if callable(pos):
                        x, y = pos()
                        positions[node_id] = QPointF(x, y)
                    else:
                        positions[node_id] = QPointF(pos.x(), pos.y())
            except Exception as e:
                logger.debug(f"Error getting position for {node_id}: {e}")
        return positions

    def _get_node_rects(self, nodes: list[Any]) -> dict[str, Any]:
        """Get bounding rectangles of nodes."""
        from PySide6.QtCore import QRectF

        rects: dict[str, QRectF] = {}
        for node in nodes:
            node_id = self._get_node_id(node)
            try:
                # Get node view/item
                view_item = node.view if hasattr(node, "view") else node

                if hasattr(view_item, "sceneBoundingRect"):
                    rect = view_item.sceneBoundingRect()
                elif hasattr(view_item, "boundingRect"):
                    rect = view_item.boundingRect()
                    if hasattr(node, "pos"):
                        pos = node.pos()
                        if callable(pos):
                            x, y = pos()
                        else:
                            x, y = pos.x(), pos.y()
                        rect.translate(x, y)
                else:
                    # Default rect
                    pos = self._get_node_positions([node]).get(node_id, QPointF(0, 0))
                    rect = QRectF(pos.x(), pos.y(), 200, 100)

                rects[node_id] = rect
            except Exception as e:
                logger.debug(f"Error getting rect for {node_id}: {e}")

        return rects

    def _apply_positions(
        self, nodes: list[Any], changes: dict[str, tuple[QPointF, QPointF]]
    ) -> None:
        """Apply position changes to nodes."""
        if not changes:
            return

        # Build node lookup
        node_lookup = {self._get_node_id(n): n for n in nodes}

        # Stop running animations
        self._stop_animations()

        if self._animate:
            self._animate_positions(node_lookup, changes)
        else:
            self._set_positions_immediate(node_lookup, changes)

        # Emit for undo support
        self.positions_changed.emit(changes)
        self.alignment_completed.emit()

    def _set_positions_immediate(
        self, node_lookup: dict[str, Any], changes: dict[str, tuple[QPointF, QPointF]]
    ) -> None:
        """Set positions immediately without animation."""
        for node_id, (_old_pos, new_pos) in changes.items():
            if node_id not in node_lookup:
                continue

            node = node_lookup[node_id]
            try:
                if hasattr(node, "set_pos"):
                    node.set_pos(new_pos.x(), new_pos.y())
                elif hasattr(node, "setPos"):
                    node.setPos(new_pos)
            except Exception as e:
                logger.debug(f"Error setting position for {node_id}: {e}")

    def _animate_positions(
        self, node_lookup: dict[str, Any], changes: dict[str, tuple[QPointF, QPointF]]
    ) -> None:
        """Animate nodes to their new positions."""
        self._pending_animations = len(changes)

        for node_id, (old_pos, new_pos) in changes.items():
            if node_id not in node_lookup:
                self._pending_animations -= 1
                continue

            node = node_lookup[node_id]

            try:
                # Get view item for animation
                view_item = node.view if hasattr(node, "view") else node

                if not isinstance(view_item, QGraphicsItem):
                    if hasattr(node, "set_pos"):
                        node.set_pos(new_pos.x(), new_pos.y())
                    self._pending_animations -= 1
                    continue

                # Create animation
                animation = QPropertyAnimation(view_item, b"pos")
                animation.setDuration(self._animation_duration)
                animation.setStartValue(old_pos)
                animation.setEndValue(new_pos)
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)

                animation.finished.connect(self._on_animation_finished)

                self._animations.append(animation)
                animation.start()

            except Exception as e:
                logger.debug(f"Error animating {node_id}: {e}")
                self._pending_animations -= 1

    def _on_animation_finished(self) -> None:
        """Handle animation completion."""
        self._pending_animations -= 1

    def _stop_animations(self) -> None:
        """Stop all running animations."""
        for anim in self._animations:
            if anim.state() == QPropertyAnimation.State.Running:
                anim.stop()
        self._animations.clear()
        self._pending_animations = 0

    def is_animating(self) -> bool:
        """Check if animation is in progress."""
        return self._pending_animations > 0


# Module-level singleton
_node_aligner: NodeAligner | None = None


def get_node_aligner() -> NodeAligner:
    """Get the global NodeAligner instance."""
    global _node_aligner
    if _node_aligner is None:
        _node_aligner = NodeAligner()
    return _node_aligner


def set_node_aligner(aligner: NodeAligner) -> None:
    """Set the global NodeAligner instance."""
    global _node_aligner
    _node_aligner = aligner
