"""
Loading State Components v2 - Epic 5.1 Component Library.

Visual indicators for loading and placeholder states.
Provides Skeleton (loading placeholder) and Spinner (activity indicator) components.

Components:
    Skeleton: Static loading placeholder with band pattern (no shimmer animation)
    Spinner: Static circular arc indicator (no rotation per zero-motion policy)

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.loading import (
        Skeleton,
        SkeletonVariant,
        Spinner,
        create_skeleton,
        create_spinner,
    )

    # Skeleton for text placeholder
    text_skeleton = Skeleton(variant="text", width=200, height=16)

    # Skeleton for circular avatar placeholder
    avatar_skeleton = Skeleton(variant="circle", width=40, height=40)

    # Skeleton for rectangular card placeholder
    card_skeleton = Skeleton(variant="rect", width=100, height=100)

    # Spinner with default size
    spinner = Spinner()

    # Large spinner
    large_spinner = Spinner(size=32, stroke_width=3)

    # Custom color spinner
    custom_spinner = Spinner(size=24, stroke_width=2, color=THEME_V2.success)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import (
    BasePrimitive,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


# =============================================================================
# TYPE ALIASES
# =============================================================================

SkeletonVariant = Literal["rect", "circle", "text"]


# =============================================================================
# SKELETON
# =============================================================================


class Skeleton(BasePrimitive):
    """
    Loading placeholder with static band pattern.

    Displays a placeholder that indicates content is loading.
    No shimmer animation per zero-motion policy - uses colored bands instead.

    Props:
        width: Width in pixels (default: 100)
        height: Height in pixels (default: 16)
        variant: Shape variant - "rect", "circle", or "text" (default: "rect")

    Variants:
        "rect": Rectangle with horizontal band pattern
        "circle": Circular placeholder with band pattern
        "text": Multiple horizontal lines simulating text (3 lines)

    Example:
        # Rectangular skeleton for card placeholder
        skeleton = Skeleton(variant="rect", width=200, height=100)

        # Circular skeleton for avatar placeholder
        avatar = Skeleton(variant="circle", width=40, height=40)

        # Text skeleton for content placeholder
        text = Skeleton(variant="text", width=300, height=40)
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        width: int = 100,
        height: int = 16,
        variant: SkeletonVariant = "rect",
    ) -> None:
        """
        Initialize the skeleton.

        Args:
            parent: Optional parent widget
            width: Width in pixels
            height: Height in pixels
            variant: Shape variant ("rect", "circle", or "text")
        """
        self._width: int = max(1, width)
        self._height: int = max(1, height)
        self._variant: SkeletonVariant = variant

        # Band configuration (alternating colors)
        self._band_height: int = 4  # Height of each band
        self._base_color = QColor(THEME_V2.bg_component)
        self._band_color = QColor(THEME_V2.bg_elevated)

        super().__init__(parent)

        logger.debug(f"{self.__class__.__name__} created: variant={variant}, size={width}x{height}")

    def setup_ui(self) -> None:
        """Setup skeleton widget (no child widgets needed)."""
        # Set fixed size
        self.setFixedSize(self._width, self._height)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """
        Paint the skeleton with band pattern.

        Draws alternating horizontal bands to create visual interest
        without using animation (per zero-motion policy).
        """
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._variant == "circle":
            self._paint_circle(painter)
        elif self._variant == "text":
            self._paint_text_lines(painter)
        else:  # rect
            self._paint_rect(painter)

    def _paint_rect(self, painter: QPainter) -> None:
        """Paint rectangular skeleton with band pattern."""
        rect = self.rect()

        # Clip to rounded rectangle
        radius = TOKENS_V2.radius.sm
        painter.setClipRoundedRect(rect, radius, radius, Qt.Corner.AllCorners)

        # Draw alternating bands
        y = 0
        band_index = 0
        while y < rect.height():
            band_h = min(self._band_height, rect.height() - y)
            band_rect = QRectF(0, y, rect.width(), band_h)

            # Alternate between base and band colors
            if band_index % 2 == 0:
                painter.fillRect(band_rect, self._base_color)
            else:
                painter.fillRect(band_rect, self._band_color)

            y += band_h
            band_index += 1

    def _paint_circle(self, painter: QPainter) -> None:
        """Paint circular skeleton with band pattern."""
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        radius = min(rect.width(), rect.height()) / 2

        # Draw circular clipping region
        from PySide6.QtGui import QPainterPath

        clip_path = QPainterPath()
        clip_path.addEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        painter.setClipPath(clip_path)

        # Draw alternating horizontal bands
        y = 0
        band_index = 0
        while y < rect.height():
            band_h = min(self._band_height, rect.height() - y)
            band_rect = QRectF(0, y, rect.width(), band_h)

            if band_index % 2 == 0:
                painter.fillRect(band_rect, self._base_color)
            else:
                painter.fillRect(band_rect, self._band_color)

            y += band_h
            band_index += 1

    def _paint_text_lines(self, painter: QPainter) -> None:
        """Paint text-like skeleton with multiple lines."""
        rect = self.rect()
        line_height = TOKENS_V2.typography.body + TOKENS_V2.spacing.xs
        line_spacing = TOKENS_V2.spacing.xs

        y = 0
        line_num = 0
        # Draw up to 3 lines or until we run out of space
        while y + line_height <= rect.height() and line_num < 3:
            # First line is full width, subsequent are shorter
            if line_num == 0:
                line_width = rect.width()
            elif line_num == 1:
                line_width = rect.width() * 0.8
            else:
                line_width = rect.width() * 0.6

            line_rect = QRectF(0, y, line_width, line_height)

            # Clip to rounded rect for each line
            radius = TOKENS_V2.radius.xs
            from PySide6.QtGui import QPainterPath

            clip_path = QPainterPath()
            clip_path.addRoundedRect(line_rect, radius, radius)
            painter.setClipPath(clip_path)

            # Draw base color
            painter.fillRect(line_rect, self._base_color)

            # Draw band pattern on the line
            band_y = y
            band_index = 0
            while band_y < y + line_height:
                band_h = min(2, y + line_height - band_y)
                band_rect = QRectF(0, band_y, line_width, band_h)

                if band_index % 2 == 1:
                    painter.fillRect(band_rect, self._band_color)

                band_y += band_h
                band_index += 1

            y += line_height + line_spacing
            line_num += 1

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet (transparent background)."""
        return """
            Skeleton {
                background: transparent;
            }
        """

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def set_size(self, width: int, height: int) -> None:
        """
        Set the skeleton size.

        Args:
            width: New width in pixels
            height: New height in pixels
        """
        self._width = max(1, width)
        self._height = max(1, height)
        self.setFixedSize(self._width, self._height)
        self.update()

    def set_variant(self, variant: SkeletonVariant) -> None:
        """
        Set the skeleton variant.

        Args:
            variant: New variant ("rect", "circle", or "text")
        """
        self._variant = variant
        self.update()

    def variant(self) -> SkeletonVariant:
        """Get the current variant."""
        return self._variant


# =============================================================================
# SPINNER
# =============================================================================


class Spinner(BasePrimitive):
    """
    Static circular arc indicating activity.

    Displays a circular arc as a loading indicator.
    No rotation animation per zero-motion policy - shows static arc instead.

    Props:
        size: Diameter in pixels (default: 20)
        stroke_width: Stroke width in pixels (default: 2)
        color: Arc color (default: THEME_V2.primary)

    Example:
        # Default spinner
        spinner = Spinner()

        # Large spinner
        large = Spinner(size=32, stroke_width=3)

        # Custom color spinner
        success_spinner = Spinner(size=24, stroke_width=2, color=THEME_V2.success)
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        size: int = 20,
        stroke_width: int = 2,
        color: str | None = None,
    ) -> None:
        """
        Initialize the spinner.

        Args:
            parent: Optional parent widget
            size: Diameter in pixels
            stroke_width: Stroke width in pixels
            color: Arc color string (None for default THEME_V2.primary)
        """
        self._size: int = max(1, size)
        self._stroke_width: int = max(1, stroke_width)
        self._color: QColor = QColor(color if color else THEME_V2.primary)

        # Arc configuration (static arc at top-right position)
        self._arc_angle: int = 270  # Degrees of arc to draw
        self._start_angle: int = 0  # Starting angle (top, clockwise)

        super().__init__(parent)

        logger.debug(f"{self.__class__.__name__} created: size={size}, stroke_width={stroke_width}")

    def setup_ui(self) -> None:
        """Setup spinner widget (no child widgets needed)."""
        self.setFixedSize(self._size, self._size)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """
        Paint the spinner arc.

        Draws a static circular arc to indicate loading state
        without rotation (per zero-motion policy).
        """
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate dimensions
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        diameter = min(rect.width(), rect.height()) - self._stroke_width
        radius = diameter / 2

        # Draw background circle (subtle)
        bg_pen = QPen(QColor(THEME_V2.bg_component), self._stroke_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(
            int(center_x - radius), int(center_y - radius), int(diameter), int(diameter)
        )

        # Draw arc (loading indicator)
        pen = QPen(self._color, self._stroke_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw arc from start_angle for arc_angle degrees
        # Qt draws counter-clockwise from 3 o'clock, so we adjust
        span_angle = -self._arc_angle  # Negative for counter-clockwise
        painter.drawArc(
            int(center_x - radius),
            int(center_y - radius),
            int(diameter),
            int(diameter),
            self._start_angle * 16,  # Qt uses 1/16th degree units
            span_angle * 16,
        )

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet (transparent background)."""
        return """
            Spinner {
                background: transparent;
            }
        """

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def set_size(self, size: int) -> None:
        """
        Set the spinner size.

        Args:
            size: New diameter in pixels
        """
        self._size = max(1, size)
        self.setFixedSize(self._size, self._size)
        self.update()

    def set_stroke_width(self, stroke_width: int) -> None:
        """
        Set the stroke width.

        Args:
            stroke_width: New stroke width in pixels
        """
        self._stroke_width = max(1, stroke_width)
        self.update()

    def set_color(self, color: str) -> None:
        """
        Set the arc color.

        Args:
            color: New color as hex string or named color
        """
        self._color = QColor(color)
        self.update()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_skeleton(
    variant: SkeletonVariant = "rect",
    width: int = 100,
    height: int = 16,
    parent: QWidget | None = None,
) -> Skeleton:
    """
    Convenience function to create a skeleton.

    Args:
        variant: Shape variant ("rect", "circle", or "text")
        width: Width in pixels
        height: Height in pixels
        parent: Optional parent widget

    Returns:
        Configured Skeleton widget
    """
    return Skeleton(
        variant=variant,
        width=width,
        height=height,
        parent=parent,
    )


def create_spinner(
    size: int = 20,
    stroke_width: int = 2,
    color: str | None = None,
    parent: QWidget | None = None,
) -> Spinner:
    """
    Convenience function to create a spinner.

    Args:
        size: Diameter in pixels
        stroke_width: Stroke width in pixels
        color: Arc color (None for default THEME_V2.primary)
        parent: Optional parent widget

    Returns:
        Configured Spinner widget
    """
    return Spinner(
        size=size,
        stroke_width=stroke_width,
        color=color,
        parent=parent,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Components
    "Skeleton",
    "Spinner",
    # Types
    "SkeletonVariant",
    # Convenience functions
    "create_skeleton",
    "create_spinner",
]
