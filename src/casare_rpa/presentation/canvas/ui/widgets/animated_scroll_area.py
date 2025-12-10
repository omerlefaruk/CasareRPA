"""
Animated Scroll Area widget with smooth scroll animations.

Provides a QScrollArea with smooth scrolling instead of instant jumps:
- smoothScrollTo(x, y): Animate to absolute position
- smoothScrollToWidget(widget): Animate to make widget visible
- Configurable animation duration and easing

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_scroll_area import (
        AnimatedScrollArea,
        create_animated_scroll_area,
    )

    # Basic usage
    scroll_area = AnimatedScrollArea()
    scroll_area.setWidget(content_widget)

    # Smooth scroll to position
    scroll_area.smoothScrollTo(0, 500)

    # Smooth scroll to make widget visible
    scroll_area.smoothScrollToWidget(target_widget)

    # Disable animations
    scroll_area.setScrollAnimationEnabled(False)

    # Factory function
    scroll = create_animated_scroll_area(widget_resizable=True)
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PySide6.QtWidgets import QScrollArea, QScrollBar, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS


# =============================================================================
# CONSTANTS
# =============================================================================

# Default scroll animation duration (uses ANIMATIONS.medium = 200ms)
DEFAULT_SCROLL_DURATION = ANIMATIONS.medium

# Margin around widget when scrolling to make it visible (pixels)
SCROLL_TO_WIDGET_MARGIN = 20


# =============================================================================
# ANIMATED SCROLL AREA
# =============================================================================


class AnimatedScrollArea(QScrollArea):
    """
    QScrollArea with smooth scroll animations.

    Features:
        - smoothScrollTo(x, y): Animate to position with easing
        - smoothScrollToWidget(widget): Scroll to make widget visible
        - setScrollAnimationEnabled(bool): Enable/disable animations
        - Respects AccessibilitySettings.prefers_reduced_motion()

    All animations use QEasingCurve.Type.OutCubic for natural deceleration.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated scroll area.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Animation state
        self._h_scroll_animation: Optional[QPropertyAnimation] = None
        self._v_scroll_animation: Optional[QPropertyAnimation] = None
        self._animation_enabled: bool = True
        self._scroll_duration: int = DEFAULT_SCROLL_DURATION

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def setScrollAnimationEnabled(self, enabled: bool) -> None:
        """
        Enable or disable scroll animations.

        Args:
            enabled: True to enable smooth scrolling, False for instant jumps.

        Note:
            Even when enabled, animations are skipped if user prefers
            reduced motion (accessibility setting).
        """
        self._animation_enabled = enabled
        logger.debug(f"Scroll animation enabled: {enabled}")

    def isScrollAnimationEnabled(self) -> bool:
        """
        Check if scroll animations are enabled.

        Returns:
            True if animations are enabled and reduced motion is not preferred.
        """
        return (
            self._animation_enabled
            and not AccessibilitySettings.prefers_reduced_motion()
        )

    def setScrollDuration(self, duration: int) -> None:
        """
        Set the scroll animation duration.

        Args:
            duration: Animation duration in milliseconds.
        """
        self._scroll_duration = max(0, duration)

    def scrollDuration(self) -> int:
        """
        Get the scroll animation duration.

        Returns:
            Animation duration in milliseconds.
        """
        return self._scroll_duration

    # =========================================================================
    # SMOOTH SCROLL TO POSITION
    # =========================================================================

    def smoothScrollTo(self, x: int, y: int) -> None:
        """
        Smoothly scroll to the specified position.

        Args:
            x: Horizontal scroll position (0 = left).
            y: Vertical scroll position (0 = top).

        If animations are disabled or reduced motion is preferred,
        scrolls instantly without animation.
        """
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()

        # Clamp values to valid range
        x = max(h_bar.minimum(), min(x, h_bar.maximum()))
        y = max(v_bar.minimum(), min(y, v_bar.maximum()))

        # Check if animation should be used
        if not self.isScrollAnimationEnabled():
            # Instant scroll
            h_bar.setValue(x)
            v_bar.setValue(y)
            return

        # Animate horizontal scroll if position changed
        if h_bar.value() != x:
            self._animate_scrollbar(h_bar, x, is_horizontal=True)

        # Animate vertical scroll if position changed
        if v_bar.value() != y:
            self._animate_scrollbar(v_bar, y, is_horizontal=False)

    def smoothScrollToPoint(self, point: QPoint) -> None:
        """
        Smoothly scroll to the specified point.

        Args:
            point: Target scroll position.
        """
        self.smoothScrollTo(point.x(), point.y())

    # =========================================================================
    # SMOOTH SCROLL TO WIDGET
    # =========================================================================

    def smoothScrollToWidget(
        self, widget: QWidget, margin: int = SCROLL_TO_WIDGET_MARGIN
    ) -> None:
        """
        Smoothly scroll to make a widget visible within the viewport.

        Args:
            widget: The widget to scroll into view.
            margin: Extra padding around the widget (pixels).

        If the widget is already fully visible, no scrolling occurs.
        If the widget is partially visible, scrolls minimally to fully reveal it.
        """
        if widget is None:
            logger.warning("smoothScrollToWidget called with None widget")
            return

        content = self.widget()
        if content is None:
            logger.warning("smoothScrollToWidget called with no content widget set")
            return

        # Get widget position relative to scroll area content
        widget_pos = widget.mapTo(content, QPoint(0, 0))
        widget_rect_left = widget_pos.x()
        widget_rect_top = widget_pos.y()
        widget_rect_right = widget_rect_left + widget.width()
        widget_rect_bottom = widget_rect_top + widget.height()

        # Get current viewport bounds
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        viewport_left = h_bar.value()
        viewport_top = v_bar.value()
        viewport_right = viewport_left + self.viewport().width()
        viewport_bottom = viewport_top + self.viewport().height()

        # Calculate target scroll position (scroll minimally to reveal widget)
        target_x = viewport_left
        target_y = viewport_top

        # Horizontal adjustment
        if widget_rect_left - margin < viewport_left:
            # Widget is left of viewport
            target_x = widget_rect_left - margin
        elif widget_rect_right + margin > viewport_right:
            # Widget is right of viewport
            target_x = widget_rect_right + margin - self.viewport().width()

        # Vertical adjustment
        if widget_rect_top - margin < viewport_top:
            # Widget is above viewport
            target_y = widget_rect_top - margin
        elif widget_rect_bottom + margin > viewport_bottom:
            # Widget is below viewport
            target_y = widget_rect_bottom + margin - self.viewport().height()

        # Only scroll if position changed
        if target_x != viewport_left or target_y != viewport_top:
            self.smoothScrollTo(target_x, target_y)
            logger.debug(f"Smooth scroll to widget: ({target_x}, {target_y})")

    def ensureWidgetVisibleSmooth(
        self,
        widget: QWidget,
        x_margin: int = SCROLL_TO_WIDGET_MARGIN,
        y_margin: int = SCROLL_TO_WIDGET_MARGIN,
    ) -> None:
        """
        Smoothly ensure a widget is visible (API compatible with QScrollArea).

        Args:
            widget: The widget to scroll into view.
            x_margin: Horizontal margin around the widget (pixels).
            y_margin: Vertical margin around the widget (pixels).

        Uses the larger of x_margin and y_margin as the margin for
        smoothScrollToWidget for simplicity.
        """
        margin = max(x_margin, y_margin)
        self.smoothScrollToWidget(widget, margin)

    # =========================================================================
    # ANIMATION HELPERS
    # =========================================================================

    def _animate_scrollbar(
        self, scrollbar: QScrollBar, target_value: int, is_horizontal: bool
    ) -> None:
        """
        Animate a scrollbar to the target value.

        Args:
            scrollbar: The scrollbar to animate.
            target_value: Target scroll position.
            is_horizontal: True for horizontal, False for vertical.
        """
        # Get the appropriate animation reference
        if is_horizontal:
            # Stop any existing horizontal animation
            if self._h_scroll_animation is not None:
                self._h_scroll_animation.stop()

            self._h_scroll_animation = self._create_scrollbar_animation(
                scrollbar, target_value
            )
            self._h_scroll_animation.finished.connect(
                self._on_h_scroll_animation_finished
            )
            self._h_scroll_animation.start()
        else:
            # Stop any existing vertical animation
            if self._v_scroll_animation is not None:
                self._v_scroll_animation.stop()

            self._v_scroll_animation = self._create_scrollbar_animation(
                scrollbar, target_value
            )
            self._v_scroll_animation.finished.connect(
                self._on_v_scroll_animation_finished
            )
            self._v_scroll_animation.start()

    def _create_scrollbar_animation(
        self, scrollbar: QScrollBar, target_value: int
    ) -> QPropertyAnimation:
        """
        Create a property animation for a scrollbar.

        Args:
            scrollbar: The scrollbar to animate.
            target_value: Target scroll position.

        Returns:
            Configured QPropertyAnimation.
        """
        animation = QPropertyAnimation(scrollbar, b"value")
        animation.setDuration(self._scroll_duration)
        animation.setStartValue(scrollbar.value())
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    def _on_h_scroll_animation_finished(self) -> None:
        """Clean up after horizontal scroll animation finishes."""
        self._h_scroll_animation = None

    def _on_v_scroll_animation_finished(self) -> None:
        """Clean up after vertical scroll animation finishes."""
        self._v_scroll_animation = None

    # =========================================================================
    # SCROLL BY DELTA
    # =========================================================================

    def smoothScrollBy(self, dx: int, dy: int) -> None:
        """
        Smoothly scroll by a delta from current position.

        Args:
            dx: Horizontal delta (positive = right, negative = left).
            dy: Vertical delta (positive = down, negative = up).
        """
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        self.smoothScrollTo(h_bar.value() + dx, v_bar.value() + dy)

    def smoothScrollToTop(self) -> None:
        """Smoothly scroll to the top of the content."""
        self.smoothScrollTo(self.horizontalScrollBar().value(), 0)

    def smoothScrollToBottom(self) -> None:
        """Smoothly scroll to the bottom of the content."""
        self.smoothScrollTo(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().maximum(),
        )

    def smoothScrollToLeft(self) -> None:
        """Smoothly scroll to the left of the content."""
        self.smoothScrollTo(0, self.verticalScrollBar().value())

    def smoothScrollToRight(self) -> None:
        """Smoothly scroll to the right of the content."""
        self.smoothScrollTo(
            self.horizontalScrollBar().maximum(),
            self.verticalScrollBar().value(),
        )

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def stopScrollAnimations(self) -> None:
        """
        Stop all running scroll animations.

        Call this before destroying the widget or when animations
        need to be cancelled immediately.
        """
        if self._h_scroll_animation is not None:
            self._h_scroll_animation.stop()
            self._h_scroll_animation = None

        if self._v_scroll_animation is not None:
            self._v_scroll_animation.stop()
            self._v_scroll_animation = None


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_animated_scroll_area(
    parent: Optional[QWidget] = None,
    widget_resizable: bool = True,
    horizontal_scrollbar_policy: Qt.ScrollBarPolicy = Qt.ScrollBarPolicy.ScrollBarAsNeeded,
    vertical_scrollbar_policy: Qt.ScrollBarPolicy = Qt.ScrollBarPolicy.ScrollBarAsNeeded,
    scroll_duration: int = DEFAULT_SCROLL_DURATION,
) -> AnimatedScrollArea:
    """
    Create an AnimatedScrollArea with common configuration.

    Args:
        parent: Parent widget.
        widget_resizable: If True, the scroll area will resize its widget
                          to fit the viewport (default True).
        horizontal_scrollbar_policy: Horizontal scrollbar policy.
        vertical_scrollbar_policy: Vertical scrollbar policy.
        scroll_duration: Animation duration in milliseconds.

    Returns:
        Configured AnimatedScrollArea instance.

    Example:
        scroll = create_animated_scroll_area(
            widget_resizable=True,
            scroll_duration=300,
        )
        scroll.setWidget(my_content)
        scroll.smoothScrollTo(0, 500)
    """
    scroll_area = AnimatedScrollArea(parent)
    scroll_area.setWidgetResizable(widget_resizable)
    scroll_area.setHorizontalScrollBarPolicy(horizontal_scrollbar_policy)
    scroll_area.setVerticalScrollBarPolicy(vertical_scrollbar_policy)
    scroll_area.setScrollDuration(scroll_duration)

    return scroll_area


__all__ = [
    "AnimatedScrollArea",
    "create_animated_scroll_area",
    "DEFAULT_SCROLL_DURATION",
    "SCROLL_TO_WIDGET_MARGIN",
]
