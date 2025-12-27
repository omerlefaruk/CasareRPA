"""
Frame Renderer

Handles all painting/rendering logic for NodeFrame.
Separates rendering concerns from state management and user interaction.

Following Single Responsibility Principle - this module handles ONLY
visual rendering of frames.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QFont, QPainter, QPen

from casare_rpa.presentation.canvas.graph.style_manager import (
    FrameStyleManager,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame


class FrameRenderer:
    """
    Renders NodeFrame visuals.

    Responsible for:
    - Drawing frame background and border
    - Selection highlight
    - Drop target highlight
    - Collapsed state appearance
    - Node count indicator
    """

    # Constants
    CORNER_RADIUS = 10
    NODE_COUNT_FONT_SIZE = 9
    NODE_COUNT_FONT_FAMILY = "Segoe UI"

    def __init__(self, frame: "NodeFrame"):
        """
        Initialize renderer.

        Args:
            frame: NodeFrame to render
        """
        self._frame = frame

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """
        Paint the frame.

        Handles all visual states:
        - Normal state
        - Selected state
        - Drop target state
        - Collapsed state

        Args:
            painter: QPainter to draw with
            option: Style options (unused)
            widget: Widget being painted on (unused)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self._frame.rect()
        pen, brush = self._get_pen_and_brush()

        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, self.CORNER_ self.CORNER_RADIUS)

        # Draw node count when collapsed
        if self._frame.is_collapsed and self._frame.contained_nodes:
            self._draw_node_count(painter, rect)

    def _get_pen_and_brush(self) -> tuple[QPen, QBrush]:
        """
        Get pen and brush based on current frame state.

        Returns:
            Tuple of (QPen, QBrush) for current state
        """
        frame_color = self._frame.frame_color

        if self._frame._is_drop_target:
            # Drop target state: green highlight
            return (
                FrameStyleManager.get_drop_target_pen(),
                FrameStyleManager.get_drop_target_brush(),
            )

        if self._frame.isSelected():
            # Selected state: yellow border, normal fill
            return (FrameStyleManager.get_selection_pen(), self._frame.brush())

        if self._frame.is_collapsed:
            # Collapsed state: solid border, darker fill
            return (
                FrameStyleManager.get_collapsed_pen(frame_color),
                FrameStyleManager.get_collapsed_brush(frame_color),
            )

        # Normal state: dashed border, normal fill
        return (FrameStyleManager.create_frame_pen(frame_color), self._frame.brush())

    def _draw_node_count(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw node count indicator when collapsed.

        Args:
            painter: QPainter to draw with
            rect: Frame rectangle
        """
        count_text = f"{len(self._frame.contained_nodes)} nodes"
        color = FrameStyleManager.get_node_count_color(self._frame.frame_color)

        painter.setPen(QPen(color))
        font = QFont(self.NODE_COUNT_FONT_FAMILY, self.NODE_COUNT_FONT_SIZE)
        painter.setFont(font)

        text_rect = QRectF(rect.left() + 10, rect.bottom() - 20, rect.width() - 20, 15)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            count_text,
        )


class TitleRenderer:
    """
    Renders and manages frame title label.

    Responsible for:
    - Title text rendering
    - Font scaling based on frame size
    - Title positioning
    """

    # Constants
    BASE_FONT_SIZE = 14
    MIN_FONT_SIZE = 12
    MAX_FONT_SIZE = 48
    BASE_WIDTH = 400
    FONT_FAMILY = "Segoe UI"
    LEFT_MARGIN = 10
    RIGHT_MARGIN = 44  # Account for collapse button

    @classmethod
    def calculate_font_size(cls, frame_width: float) -> int:
        """
        Calculate appropriate font size based on frame width.

        Args:
            frame_width: Width of the frame

        Returns:
            Font size in points
        """
        scale_factor = frame_width / cls.BASE_WIDTH
        font_size = int(cls.BASE_FONT_SIZE * scale_factor)
        return max(cls.MIN_FONT_SIZE, min(cls.MAX_FONT_SIZE, font_size))

    @classmethod
    def get_available_width(cls, frame_width: float) -> float:
        """
        Calculate available width for title text.

        Args:
            frame_width: Width of the frame

        Returns:
            Available width for title
        """
        return frame_width - cls.LEFT_MARGIN - cls.RIGHT_MARGIN

    @classmethod
    def create_font(cls, frame_width: float) -> QFont:
        """
        Create font for title based on frame width.

        Args:
            frame_width: Width of the frame

        Returns:
            QFont sized appropriately
        """
        font_size = cls.calculate_font_size(frame_width)
        return QFont(cls.FONT_FAMILY, font_size, QFont.Weight.Bold)
