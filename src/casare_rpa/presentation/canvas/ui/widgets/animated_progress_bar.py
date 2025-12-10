"""
Animated Progress Bar Widget for CasareRPA.

Provides smooth value transitions and completion animations for progress bars.

Features:
- Smooth animated value transitions using QPropertyAnimation
- Completion pulse effect when reaching 100%
- Respects AccessibilitySettings.prefers_reduced_motion()
- Uses ANIMATIONS from theme.py for consistent timing

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_progress_bar import (
        AnimatedProgressBar,
        create_animated_progress_bar,
    )

    # Create with factory function
    progress = create_animated_progress_bar()
    progress.setValue(50)  # Animates to 50%
    progress.setValue(100)  # Animates to 100% with pulse effect

    # Or create directly
    progress = AnimatedProgressBar()
    progress.setAnimatedValue(75)  # Explicit animated method
    progress.setValue(100, animate=False)  # Skip animation
"""

from typing import Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QProgressBar, QWidget

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedProgressBar(QProgressBar):
    """
    Progress bar with smooth value transitions and completion animations.

    Extends QProgressBar to provide:
    - Smooth animated transitions between values
    - Pulse/glow effect when reaching 100%
    - Accessibility support (reduced motion preference)

    The default setValue() method animates transitions. Use setValue(value, animate=False)
    to skip animation for immediate updates.

    Attributes:
        COMPLETION_VALUE: Value that triggers completion animation (100 by default)
    """

    COMPLETION_VALUE = 100

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated progress bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._value_animation: Optional[QPropertyAnimation] = None
        self._completion_animation: Optional[QSequentialAnimationGroup] = None
        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._target_value: int = 0
        self._animating: bool = False

        # Store the actual display value for animation
        self._display_value: int = 0

    def _get_display_value(self) -> int:
        """Get the current display value for animation."""
        return self._display_value

    def _set_display_value(self, value: int) -> None:
        """
        Set the display value and update the progress bar.

        This is the slot connected to QPropertyAnimation.
        Calls the parent setValue to actually update the visual.

        Args:
            value: The progress value to display
        """
        self._display_value = value
        super().setValue(value)

    # Qt property for animation binding
    displayValue = Property(
        int,
        _get_display_value,
        _set_display_value,
    )

    def setValue(self, value: int, animate: bool = True) -> None:
        """
        Set the progress value with optional animation.

        Overrides QProgressBar.setValue() to animate by default.
        When value reaches COMPLETION_VALUE (100), triggers a pulse effect.

        Args:
            value: The new progress value (0-100 typically)
            animate: If True (default), animate the transition.
                     If False, set value immediately without animation.
        """
        # Clamp value to valid range
        value = max(self.minimum(), min(value, self.maximum()))
        self._target_value = value

        # Check if animation should be skipped
        if not animate or AccessibilitySettings.prefers_reduced_motion():
            self._stop_animations()
            self._display_value = value
            super().setValue(value)
            return

        # Animate the value transition
        self._animate_to_value(value)

    def setAnimatedValue(self, value: int) -> None:
        """
        Explicitly set value with animation.

        Convenience method that always animates (respecting accessibility).
        Equivalent to setValue(value, animate=True).

        Args:
            value: The new progress value
        """
        self.setValue(value, animate=True)

    def _animate_to_value(self, value: int) -> None:
        """
        Animate progress bar to the target value.

        Args:
            value: Target value to animate to
        """
        # Stop any existing animation
        self._stop_animations()

        # Create value animation
        self._value_animation = QPropertyAnimation(self, b"displayValue")
        self._value_animation.setDuration(ANIMATIONS.medium)  # 200ms
        self._value_animation.setStartValue(self._display_value)
        self._value_animation.setEndValue(value)
        self._value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Connect completion handler for pulse effect
        self._value_animation.finished.connect(
            lambda: self._on_value_animation_finished(value)
        )

        self._animating = True
        self._value_animation.start()

        logger.debug(
            f"AnimatedProgressBar: Animating from {self._display_value} to {value}"
        )

    def _on_value_animation_finished(self, final_value: int) -> None:
        """
        Handle completion of value animation.

        Triggers pulse effect if progress reached 100%.

        Args:
            final_value: The value that was animated to
        """
        self._animating = False

        # Check if completion pulse should be triggered
        if final_value >= self.COMPLETION_VALUE:
            self._trigger_completion_pulse()

    def _trigger_completion_pulse(self) -> None:
        """
        Trigger a pulse animation to indicate completion.

        Creates a subtle opacity pulse effect (100% -> 70% -> 100%)
        to draw attention to the completed progress bar.
        """
        # Skip if reduced motion preferred
        if AccessibilitySettings.prefers_reduced_motion():
            return

        # Create opacity effect if not exists
        if self._opacity_effect is None:
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        # Stop any existing completion animation
        if self._completion_animation is not None:
            self._completion_animation.stop()

        # Create pulse sequence: 1.0 -> 0.7 -> 1.0
        self._completion_animation = QSequentialAnimationGroup(self)

        # Fade down
        fade_down = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_down.setDuration(ANIMATIONS.fast)  # 100ms
        fade_down.setStartValue(1.0)
        fade_down.setEndValue(0.7)
        fade_down.setEasingCurve(QEasingCurve.Type.InQuad)

        # Fade up
        fade_up = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_up.setDuration(ANIMATIONS.fast)  # 100ms
        fade_up.setStartValue(0.7)
        fade_up.setEndValue(1.0)
        fade_up.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._completion_animation.addAnimation(fade_down)
        self._completion_animation.addAnimation(fade_up)

        self._completion_animation.start()

        logger.debug("AnimatedProgressBar: Completion pulse triggered")

    def _stop_animations(self) -> None:
        """Stop all running animations."""
        if self._value_animation is not None:
            self._value_animation.stop()
            self._value_animation = None

        if self._completion_animation is not None:
            self._completion_animation.stop()
            self._completion_animation = None

        self._animating = False

    def reset(self) -> None:
        """
        Reset the progress bar to 0.

        Stops any running animations and resets to initial state.
        """
        self._stop_animations()
        self._display_value = 0
        self._target_value = 0
        super().reset()

    @property
    def is_animating(self) -> bool:
        """Check if an animation is currently in progress."""
        return self._animating

    @property
    def target_value(self) -> int:
        """Get the target value being animated to."""
        return self._target_value


def create_animated_progress_bar(
    parent: Optional[QWidget] = None,
) -> AnimatedProgressBar:
    """
    Factory function to create a styled animated progress bar.

    Creates an AnimatedProgressBar with theme-consistent styling.

    Args:
        parent: Parent widget

    Returns:
        Configured AnimatedProgressBar instance

    Example:
        progress = create_animated_progress_bar()
        layout.addWidget(progress)
        progress.setValue(75)  # Smooth animation to 75%
    """
    progress_bar = AnimatedProgressBar(parent)

    # Apply theme styling
    colors = Theme.get_colors()
    progress_bar.setStyleSheet(f"""
        QProgressBar {{
            background-color: {colors.surface};
            border: 1px solid {colors.border_dark};
            border-radius: 3px;
            height: 18px;
            text-align: center;
            color: {colors.text_primary};
            font-size: 10px;
            font-weight: 600;
        }}
        QProgressBar::chunk {{
            background-color: {colors.accent};
            border-radius: 2px;
        }}
    """)

    return progress_bar
