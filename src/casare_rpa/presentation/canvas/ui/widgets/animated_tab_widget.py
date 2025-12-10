"""
Tab widget with animated tab transitions.

Provides smooth crossfade and optional slide animations
when switching between tabs.

Usage:
    tabs = AnimatedTabWidget()
    tabs.addTab(widget1, "Tab 1")
    tabs.addTab(widget2, "Tab 2")
    # Switching tabs will now animate smoothly
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedTabBar(QTabBar):
    """Tab bar with animated indicator underline."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._indicator_animation: Optional[QPropertyAnimation] = None

    def tabSizeHint(self, index: int) -> "QSize":
        """Return size hint for tab."""
        from PySide6.QtCore import QSize

        hint = super().tabSizeHint(index)
        return QSize(max(hint.width(), 80), hint.height())


class AnimatedTabWidget(QTabWidget):
    """
    Tab widget with animated transitions between tabs.

    Provides smooth crossfade animation when switching tabs.
    Optional slide animation based on tab direction.
    Respects OS accessibility settings for reduced motion.

    Signals:
        transitionStarted: Emitted when tab transition animation begins
        transitionFinished: Emitted when tab transition animation completes
    """

    transitionStarted = Signal()
    transitionFinished = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._animation_group: Optional[QParallelAnimationGroup] = None
        self._previous_index: int = 0
        self._animation_enabled: bool = True
        self._slide_enabled: bool = False
        self._slide_distance: int = 30

        # Track effects for cleanup
        self._active_effects: list[QGraphicsOpacityEffect] = []

        # Connect tab change signal
        self.currentChanged.connect(self._on_tab_changed)

        logger.debug("AnimatedTabWidget initialized")

    def setAnimationEnabled(self, enabled: bool) -> None:
        """
        Enable or disable tab animations.

        Args:
            enabled: True to enable animations, False to disable.
        """
        self._animation_enabled = enabled
        logger.debug(f"Tab animation enabled: {enabled}")

    def isAnimationEnabled(self) -> bool:
        """Return whether animations are enabled."""
        return self._animation_enabled

    def setSlideEnabled(self, enabled: bool) -> None:
        """
        Enable or disable slide animation on tab switch.

        Args:
            enabled: True to enable slide effect, False for crossfade only.
        """
        self._slide_enabled = enabled

    def isSlideEnabled(self) -> bool:
        """Return whether slide animation is enabled."""
        return self._slide_enabled

    def setSlideDistance(self, distance: int) -> None:
        """
        Set the slide distance in pixels.

        Args:
            distance: Pixels to slide during transition.
        """
        self._slide_distance = max(0, distance)

    def slideDistance(self) -> int:
        """Return the slide distance in pixels."""
        return self._slide_distance

    def _should_animate(self) -> bool:
        """Check if animation should run based on settings."""
        if not self._animation_enabled:
            return False
        if AccessibilitySettings.prefers_reduced_motion():
            return False
        return True

    def _cleanup_effects(self) -> None:
        """Remove all active graphics effects."""
        for effect in self._active_effects:
            try:
                if effect.parent():
                    widget = effect.parent()
                    if isinstance(widget, QWidget):
                        widget.setGraphicsEffect(None)
            except RuntimeError:
                pass  # Widget already deleted
        self._active_effects.clear()

    def _stop_current_animation(self) -> None:
        """Stop any running animation and cleanup."""
        if (
            self._animation_group
            and self._animation_group.state() == QParallelAnimationGroup.State.Running
        ):
            self._animation_group.stop()
        self._cleanup_effects()

    def _on_tab_changed(self, index: int) -> None:
        """
        Handle tab change with animation.

        Args:
            index: New tab index.
        """
        if not self._should_animate():
            self._previous_index = index
            return

        # Get widgets for transition
        outgoing_widget = self.widget(self._previous_index)
        incoming_widget = self.widget(index)

        # Validate widgets
        if not outgoing_widget or not incoming_widget:
            self._previous_index = index
            return

        if outgoing_widget == incoming_widget:
            self._previous_index = index
            return

        # Stop any running animation
        self._stop_current_animation()

        # Determine direction for slide
        direction = 1 if index > self._previous_index else -1

        # Setup opacity effects
        outgoing_effect = QGraphicsOpacityEffect(outgoing_widget)
        incoming_effect = QGraphicsOpacityEffect(incoming_widget)

        outgoing_widget.setGraphicsEffect(outgoing_effect)
        incoming_widget.setGraphicsEffect(incoming_effect)

        self._active_effects = [outgoing_effect, incoming_effect]

        # Start with incoming invisible
        incoming_effect.setOpacity(0.0)
        outgoing_effect.setOpacity(1.0)

        # Create animation group
        self._animation_group = QParallelAnimationGroup(self)

        # Fade out old widget
        fade_out = QPropertyAnimation(outgoing_effect, b"opacity")
        fade_out.setDuration(ANIMATIONS.fast)  # 100ms
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._animation_group.addAnimation(fade_out)

        # Fade in new widget
        fade_in = QPropertyAnimation(incoming_effect, b"opacity")
        fade_in.setDuration(ANIMATIONS.normal)  # 150ms
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation_group.addAnimation(fade_in)

        # Optional slide animations
        if self._slide_enabled and self._slide_distance > 0:
            # Store original positions
            outgoing_pos = outgoing_widget.pos()
            incoming_pos = incoming_widget.pos()

            # Slide out animation
            slide_out = QPropertyAnimation(outgoing_widget, b"pos")
            slide_out.setDuration(ANIMATIONS.fast)
            slide_out.setStartValue(outgoing_pos)
            slide_out.setEndValue(
                QPoint(
                    outgoing_pos.x() - (direction * self._slide_distance),
                    outgoing_pos.y(),
                )
            )
            slide_out.setEasingCurve(QEasingCurve.Type.InCubic)
            self._animation_group.addAnimation(slide_out)

            # Slide in animation
            slide_in = QPropertyAnimation(incoming_widget, b"pos")
            slide_in.setDuration(ANIMATIONS.normal)
            slide_in.setStartValue(
                QPoint(
                    incoming_pos.x() + (direction * self._slide_distance),
                    incoming_pos.y(),
                )
            )
            slide_in.setEndValue(incoming_pos)
            slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation_group.addAnimation(slide_in)

        # Connect signals
        self._animation_group.finished.connect(self._on_animation_finished)

        # Emit started signal and run
        self.transitionStarted.emit()
        self._animation_group.start()

        # Update previous index
        self._previous_index = index

    def _on_animation_finished(self) -> None:
        """Handle animation completion and cleanup."""
        self._cleanup_effects()
        self.transitionFinished.emit()
        logger.debug("Tab transition animation finished")

    def setCurrentIndex(self, index: int) -> None:
        """
        Set current tab index with animation.

        Args:
            index: Tab index to switch to.
        """
        if index == self.currentIndex():
            return
        super().setCurrentIndex(index)

    def setCurrentWidget(self, widget: QWidget) -> None:
        """
        Set current tab by widget with animation.

        Args:
            widget: Widget to make current.
        """
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)


def create_animated_tab_widget(
    parent: Optional[QWidget] = None,
    slide_enabled: bool = False,
    slide_distance: int = 30,
) -> AnimatedTabWidget:
    """
    Factory function to create an AnimatedTabWidget.

    Args:
        parent: Parent widget.
        slide_enabled: Enable slide animation.
        slide_distance: Pixels to slide during transition.

    Returns:
        Configured AnimatedTabWidget instance.
    """
    widget = AnimatedTabWidget(parent)
    widget.setSlideEnabled(slide_enabled)
    widget.setSlideDistance(slide_distance)
    return widget
