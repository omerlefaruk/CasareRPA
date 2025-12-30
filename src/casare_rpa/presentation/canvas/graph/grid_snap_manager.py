"""
Grid snap manager for node alignment during drag operations.

Provides visual alignment guidelines and snap-to-grid functionality
for precise node positioning on the canvas.
"""

from dataclasses import dataclass
from enum import Enum

from loguru import logger
from PySide6.QtCore import QObject, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen


class GuidelineType(Enum):
    """Types of alignment guidelines."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    CENTER_H = "center_horizontal"
    CENTER_V = "center_vertical"


@dataclass
class AlignmentGuideline:
    """
    Represents an alignment guideline to display during drag.

    Attributes:
        start: Start point of the guideline
        end: End point of the guideline
        guideline_type: Type of alignment (horizontal, vertical, center)
        reference_node_id: ID of the node this guideline references
        distance: Distance to snap (smaller = closer alignment)
    """

    start: QPointF
    end: QPointF
    guideline_type: GuidelineType
    reference_node_id: str
    distance: float = 0.0


class GridSnapManager(QObject):
    """
    Manages grid snapping and alignment guidelines for node positioning.

    Features:
    - Snap-to-grid with configurable grid size
    - Visual alignment guidelines when nodes align
    - Snap to other node edges (left, right, top, bottom, center)
    - Toggle with Ctrl+Shift+G shortcut

    Usage:
        manager = GridSnapManager(grid_size=50)
        manager.set_enabled(True)

        # During node drag:
        snapped_pos = manager.snap_position(cursor_pos)
        guidelines = manager.get_alignment_guidelines(dragging_rect, other_rects)
    """

    # Signal emitted when snap state changes
    snap_state_changed = Signal(bool)

    # Alignment threshold in pixels
    SNAP_THRESHOLD = 10

    # Guideline extension beyond node edges
    GUIDELINE_EXTENSION = 30

    def __init__(self, grid_size: int = 50, parent: QObject | None = None) -> None:
        """
        Initialize the grid snap manager.

        Args:
            grid_size: Size of the grid cells in pixels
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._grid_size = grid_size
        self._enabled = True
        self._show_guidelines = True
        self._snap_to_grid = True
        self._snap_to_nodes = True

        # Cache for node rectangles during drag operation
        self._node_rects: dict[str, QRectF] = {}

        # Current guidelines to display
        self._current_guidelines: list[AlignmentGuideline] = []

        # Guideline colors from theme
        self._guideline_color = self._get_guideline_color()
        self._snap_color = self._get_snap_color()

    def _get_guideline_color(self) -> QColor:
        """Get guideline color from theme."""
        cc = Theme.get_canvas_colors()
        color = QColor(cc.status_running)  # Amber
        color.setAlpha(180)
        return color

    def _get_snap_color(self) -> QColor:
        """Get snap indicator color from theme."""
        cc = Theme.get_canvas_colors()
        color = QColor(cc.status_success)  # Green
        color.setAlpha(200)
        return color

    @property
    def grid_size(self) -> int:
        """Get the current grid size."""
        return self._grid_size

    @grid_size.setter
    def grid_size(self, value: int) -> None:
        """Set the grid size."""
        self._grid_size = max(10, min(200, value))  # Clamp between 10-200

    @property
    def enabled(self) -> bool:
        """Check if snap-to-grid is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable snap-to-grid."""
        if self._enabled != enabled:
            self._enabled = enabled
            self.snap_state_changed.emit(enabled)
            logger.debug(f"Grid snap {'enabled' if enabled else 'disabled'}")

    def toggle(self) -> bool:
        """Toggle snap-to-grid state."""
        self.set_enabled(not self._enabled)
        return self._enabled

    @property
    def show_guidelines(self) -> bool:
        """Check if alignment guidelines are shown."""
        return self._show_guidelines

    def set_show_guidelines(self, show: bool) -> None:
        """Enable or disable guideline display."""
        self._show_guidelines = show

    @property
    def snap_to_grid(self) -> bool:
        """Check if snap-to-grid is active."""
        return self._snap_to_grid

    def set_snap_to_grid(self, enabled: bool) -> None:
        """Enable or disable grid snapping."""
        self._snap_to_grid = enabled

    @property
    def snap_to_nodes(self) -> bool:
        """Check if snap-to-nodes is active."""
        return self._snap_to_nodes

    def set_snap_to_nodes(self, enabled: bool) -> None:
        """Enable or disable node edge snapping."""
        self._snap_to_nodes = enabled

    def snap_position(self, pos: QPointF) -> QPointF:
        """
        Snap a position to the grid.

        Args:
            pos: Original position

        Returns:
            Snapped position (or original if snapping disabled)
        """
        if not self._enabled or not self._snap_to_grid:
            return pos

        x = round(pos.x() / self._grid_size) * self._grid_size
        y = round(pos.y() / self._grid_size) * self._grid_size
        return QPointF(x, y)

    def snap_position_with_node_alignment(
        self,
        dragging_rect: QRectF,
        other_rects: dict[str, QRectF],
        exclude_ids: list[str] | None = None,
    ) -> tuple[QPointF, list[AlignmentGuideline]]:
        """
        Snap position considering both grid and other node alignments.

        Args:
            dragging_rect: Rectangle of the node being dragged
            other_rects: Dictionary of node_id -> QRectF for other nodes
            exclude_ids: Node IDs to exclude from alignment checks

        Returns:
            Tuple of (snapped_position, list_of_guidelines)
        """
        if not self._enabled:
            return QPointF(dragging_rect.x(), dragging_rect.y()), []

        exclude_ids = exclude_ids or []
        guidelines: list[AlignmentGuideline] = []

        snap_x: float | None = None
        snap_y: float | None = None
        snap_x_dist = float("inf")
        snap_y_dist = float("inf")

        # Key positions of dragging node
        drag_left = dragging_rect.left()
        drag_right = dragging_rect.right()
        drag_top = dragging_rect.top()
        drag_bottom = dragging_rect.bottom()
        drag_center_x = dragging_rect.center().x()
        drag_center_y = dragging_rect.center().y()

        # Check alignment with other nodes
        if self._snap_to_nodes:
            for node_id, rect in other_rects.items():
                if node_id in exclude_ids:
                    continue

                # Reference positions
                ref_left = rect.left()
                ref_right = rect.right()
                ref_top = rect.top()
                ref_bottom = rect.bottom()
                ref_center_x = rect.center().x()
                ref_center_y = rect.center().y()

                # Check vertical alignments (X axis)
                x_alignments = [
                    (drag_left, ref_left, GuidelineType.VERTICAL),
                    (drag_left, ref_right, GuidelineType.VERTICAL),
                    (drag_right, ref_left, GuidelineType.VERTICAL),
                    (drag_right, ref_right, GuidelineType.VERTICAL),
                    (drag_center_x, ref_center_x, GuidelineType.CENTER_V),
                ]

                for drag_pos, ref_pos, guide_type in x_alignments:
                    dist = abs(drag_pos - ref_pos)
                    if dist < self.SNAP_THRESHOLD and dist < snap_x_dist:
                        snap_x = dragging_rect.x() + (ref_pos - drag_pos)
                        snap_x_dist = dist

                        # Create guideline
                        y_min = min(drag_top, ref_top) - self.GUIDELINE_EXTENSION
                        y_max = max(drag_bottom, ref_bottom) + self.GUIDELINE_EXTENSION
                        guidelines = [
                            g
                            for g in guidelines
                            if g.guideline_type
                            not in (GuidelineType.VERTICAL, GuidelineType.CENTER_V)
                        ]
                        guidelines.append(
                            AlignmentGuideline(
                                start=QPointF(ref_pos, y_min),
                                end=QPointF(ref_pos, y_max),
                                guideline_type=guide_type,
                                reference_node_id=node_id,
                                distance=dist,
                            )
                        )

                # Check horizontal alignments (Y axis)
                y_alignments = [
                    (drag_top, ref_top, GuidelineType.HORIZONTAL),
                    (drag_top, ref_bottom, GuidelineType.HORIZONTAL),
                    (drag_bottom, ref_top, GuidelineType.HORIZONTAL),
                    (drag_bottom, ref_bottom, GuidelineType.HORIZONTAL),
                    (drag_center_y, ref_center_y, GuidelineType.CENTER_H),
                ]

                for drag_pos, ref_pos, guide_type in y_alignments:
                    dist = abs(drag_pos - ref_pos)
                    if dist < self.SNAP_THRESHOLD and dist < snap_y_dist:
                        snap_y = dragging_rect.y() + (ref_pos - drag_pos)
                        snap_y_dist = dist

                        # Create guideline
                        x_min = min(drag_left, ref_left) - self.GUIDELINE_EXTENSION
                        x_max = max(drag_right, ref_right) + self.GUIDELINE_EXTENSION
                        guidelines = [
                            g
                            for g in guidelines
                            if g.guideline_type
                            not in (GuidelineType.HORIZONTAL, GuidelineType.CENTER_H)
                        ]
                        guidelines.append(
                            AlignmentGuideline(
                                start=QPointF(x_min, ref_pos),
                                end=QPointF(x_max, ref_pos),
                                guideline_type=guide_type,
                                reference_node_id=node_id,
                                distance=dist,
                            )
                        )

        # Apply grid snap if no node alignment found
        if self._snap_to_grid:
            if snap_x is None:
                snap_x = round(dragging_rect.x() / self._grid_size) * self._grid_size
            if snap_y is None:
                snap_y = round(dragging_rect.y() / self._grid_size) * self._grid_size
        else:
            if snap_x is None:
                snap_x = dragging_rect.x()
            if snap_y is None:
                snap_y = dragging_rect.y()

        self._current_guidelines = guidelines if self._show_guidelines else []
        return QPointF(snap_x, snap_y), guidelines

    def get_alignment_guidelines(
        self,
        dragging_rect: QRectF,
        other_rects: dict[str, QRectF],
        exclude_ids: list[str] | None = None,
    ) -> list[AlignmentGuideline]:
        """
        Get alignment guidelines without snapping.

        Use this for preview during drag without affecting position.

        Args:
            dragging_rect: Rectangle of the node being dragged
            other_rects: Dictionary of node_id -> QRectF for other nodes
            exclude_ids: Node IDs to exclude from alignment checks

        Returns:
            List of AlignmentGuideline objects to display
        """
        if not self._enabled or not self._show_guidelines:
            return []

        _, guidelines = self.snap_position_with_node_alignment(
            dragging_rect, other_rects, exclude_ids
        )
        return guidelines

    def get_current_guidelines(self) -> list[AlignmentGuideline]:
        """Get the current guidelines from the last snap operation."""
        return self._current_guidelines

    def clear_guidelines(self) -> None:
        """Clear current guidelines."""
        self._current_guidelines = []

    def draw_guidelines(self, painter: QPainter, viewport_rect: QRectF | None = None) -> None:
        """
        Draw alignment guidelines on the painter.

        Args:
            painter: QPainter to draw on
            viewport_rect: Optional viewport rectangle for clipping
        """
        if not self._current_guidelines or not self._show_guidelines:
            return

        painter.save()

        # Dashed line for guidelines
        pen = QPen(self._guideline_color, 1.5)
        pen.setStyle(pen.DashLine)
        pen.setDashPattern([4, 4])
        painter.setPen(pen)

        for guideline in self._current_guidelines:
            start = guideline.start
            end = guideline.end

            # Clip to viewport if provided
            if viewport_rect:
                if guideline.guideline_type in (
                    GuidelineType.VERTICAL,
                    GuidelineType.CENTER_V,
                ):
                    start = QPointF(start.x(), max(start.y(), viewport_rect.top()))
                    end = QPointF(end.x(), min(end.y(), viewport_rect.bottom()))
                else:
                    start = QPointF(max(start.x(), viewport_rect.left()), start.y())
                    end = QPointF(min(end.x(), viewport_rect.right()), end.y())

            painter.drawLine(start, end)

            # Draw snap indicator at intersection
            if guideline.distance < 3:
                snap_pen = QPen(self._snap_color, 2)
                painter.setPen(snap_pen)
                center = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
                painter.drawEllipse(center, 4, 4)

        painter.restore()

    def update_node_rects(self, node_rects: dict[str, QRectF]) -> None:
        """
        Update the cached node rectangles.

        Call this when nodes are added, removed, or moved.

        Args:
            node_rects: Dictionary mapping node_id to QRectF
        """
        self._node_rects = node_rects.copy()

    def get_node_rects(self) -> dict[str, QRectF]:
        """Get the cached node rectangles."""
        return self._node_rects.copy()


# Module-level singleton for global access
_grid_snap_manager: GridSnapManager | None = None


def get_grid_snap_manager() -> GridSnapManager:
    """Get the global GridSnapManager instance."""
    global _grid_snap_manager
    if _grid_snap_manager is None:
        _grid_snap_manager = GridSnapManager()
    return _grid_snap_manager


def set_grid_snap_manager(manager: GridSnapManager) -> None:
    """Set the global GridSnapManager instance."""
    global _grid_snap_manager
    _grid_snap_manager = manager
