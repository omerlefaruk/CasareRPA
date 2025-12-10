"""
Animated Line Edit widget with smooth focus animations.

Provides a QLineEdit with visual feedback animations:
- Focus glow: Subtle drop shadow appears on focus, fades on blur
- Shake: Horizontal shake animation for validation errors
- Pulse success: Green glow pulse for successful validation

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_line_edit import (
        AnimatedLineEdit,
        create_animated_line_edit,
    )

    # Basic usage
    line_edit = AnimatedLineEdit()
    line_edit.show()

    # Validation feedback
    if not is_valid:
        line_edit.shake()
    else:
        line_edit.pulse_success()

    # Factory function with placeholder
    input_field = create_animated_line_edit(placeholder="Enter value...")
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


# =============================================================================
# CONSTANTS
# =============================================================================

# Shadow effect parameters
SHADOW_BLUR_RADIUS_FOCUSED = 12
SHADOW_BLUR_RADIUS_UNFOCUSED = 0
SHADOW_OFFSET_X = 0
SHADOW_OFFSET_Y = 0

# Shake animation parameters
SHAKE_AMPLITUDE = 6  # pixels
SHAKE_CYCLES = 3

# Success pulse parameters
SUCCESS_PULSE_COLOR = "#89D185"  # Theme success color


# =============================================================================
# ANIMATED LINE EDIT
# =============================================================================


class AnimatedLineEdit(QLineEdit):
    """
    QLineEdit with smooth focus and validation animations.

    Features:
        - Focus glow: Drop shadow appears/fades on focus/blur
        - shake(): Horizontal shake for invalid input feedback
        - pulse_success(): Green glow pulse for successful validation
        - Respects AccessibilitySettings.prefers_reduced_motion()

    All animations use durations from ANIMATIONS theme constants.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated line edit.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Animation state
        self._focus_animation: Optional[QPropertyAnimation] = None
        self._shake_animation: Optional[QSequentialAnimationGroup] = None
        self._pulse_animation: Optional[QPropertyAnimation] = None
        self._is_animating: bool = False

        # Setup shadow effect
        self._shadow_effect = QGraphicsDropShadowEffect(self)
        self._shadow_effect.setOffset(SHADOW_OFFSET_X, SHADOW_OFFSET_Y)
        self._shadow_effect.setBlurRadius(SHADOW_BLUR_RADIUS_UNFOCUSED)
        self._shadow_effect.setColor(self._get_focus_color())
        self.setGraphicsEffect(self._shadow_effect)

        # Apply base styling
        self._apply_base_style()

    def _apply_base_style(self) -> None:
        """Apply base theme styling."""
        self.setStyleSheet(Theme.input_style())

    def _get_focus_color(self) -> QColor:
        """Get the focus glow color from theme."""
        colors = Theme.get_colors()
        return QColor(colors.border_focus)

    def _get_success_color(self) -> QColor:
        """Get the success glow color from theme."""
        colors = Theme.get_colors()
        return QColor(colors.success)

    # =========================================================================
    # FOCUS ANIMATION
    # =========================================================================

    def focusInEvent(self, event) -> None:
        """Handle focus in with glow animation."""
        super().focusInEvent(event)
        self._animate_focus_glow(focused=True)

    def focusOutEvent(self, event) -> None:
        """Handle focus out with fade animation."""
        super().focusOutEvent(event)
        self._animate_focus_glow(focused=False)

    def _animate_focus_glow(self, focused: bool) -> None:
        """
        Animate the focus glow effect.

        Args:
            focused: True for focus in, False for focus out.
        """
        # Skip animation if reduced motion preferred
        if AccessibilitySettings.prefers_reduced_motion():
            target_blur = (
                SHADOW_BLUR_RADIUS_FOCUSED if focused else SHADOW_BLUR_RADIUS_UNFOCUSED
            )
            self._shadow_effect.setBlurRadius(target_blur)
            return

        # Stop any running focus animation
        if self._focus_animation is not None:
            self._focus_animation.stop()

        # Set color for focus glow
        self._shadow_effect.setColor(self._get_focus_color())

        # Create and configure animation
        self._focus_animation = QPropertyAnimation(self._shadow_effect, b"blurRadius")
        self._focus_animation.setDuration(ANIMATIONS.normal)

        if focused:
            self._focus_animation.setStartValue(self._shadow_effect.blurRadius())
            self._focus_animation.setEndValue(SHADOW_BLUR_RADIUS_FOCUSED)
            self._focus_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        else:
            self._focus_animation.setStartValue(self._shadow_effect.blurRadius())
            self._focus_animation.setEndValue(SHADOW_BLUR_RADIUS_UNFOCUSED)
            self._focus_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        self._focus_animation.finished.connect(self._on_focus_animation_finished)
        self._focus_animation.start()

    def _on_focus_animation_finished(self) -> None:
        """Clean up after focus animation finishes."""
        self._focus_animation = None

    # =========================================================================
    # SHAKE ANIMATION (Validation Error)
    # =========================================================================

    def shake(self) -> None:
        """
        Trigger shake animation for validation error feedback.

        Creates a horizontal shake effect (left-right oscillation).
        Respects accessibility settings for reduced motion.
        """
        # Skip animation if reduced motion preferred
        if AccessibilitySettings.prefers_reduced_motion():
            logger.debug("Shake animation skipped: reduced motion preferred")
            return

        # Prevent overlapping shake animations
        if self._is_animating:
            return

        self._is_animating = True

        # Stop any existing shake animation
        if self._shake_animation is not None:
            self._shake_animation.stop()

        # Store original position
        original_pos = self.pos()

        # Create sequential animation group
        self._shake_animation = QSequentialAnimationGroup(self)

        # Calculate duration per movement
        total_duration = ANIMATIONS.emphasis  # 400ms
        movements = SHAKE_CYCLES * 2  # left-right for each cycle
        duration_per_move = total_duration // (movements + 1)  # +1 for return

        # Create shake movements
        for i in range(SHAKE_CYCLES):
            # Move left
            left_anim = QPropertyAnimation(self, b"pos")
            left_anim.setDuration(duration_per_move)
            left_anim.setEndValue(
                original_pos + type(original_pos)(-SHAKE_AMPLITUDE, 0)
            )
            left_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            self._shake_animation.addAnimation(left_anim)

            # Move right
            right_anim = QPropertyAnimation(self, b"pos")
            right_anim.setDuration(duration_per_move)
            right_anim.setEndValue(
                original_pos + type(original_pos)(SHAKE_AMPLITUDE, 0)
            )
            right_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            self._shake_animation.addAnimation(right_anim)

        # Return to original position
        return_anim = QPropertyAnimation(self, b"pos")
        return_anim.setDuration(duration_per_move)
        return_anim.setEndValue(original_pos)
        return_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._shake_animation.addAnimation(return_anim)

        # Connect cleanup
        self._shake_animation.finished.connect(self._on_shake_animation_finished)
        self._shake_animation.start()

        logger.debug("Shake animation started")

    def _on_shake_animation_finished(self) -> None:
        """Clean up after shake animation finishes."""
        self._is_animating = False
        self._shake_animation = None
        logger.debug("Shake animation finished")

    # =========================================================================
    # SUCCESS PULSE ANIMATION
    # =========================================================================

    def pulse_success(self) -> None:
        """
        Trigger success pulse animation for validation feedback.

        Creates a green glow pulse effect that fades in then out.
        Respects accessibility settings for reduced motion.
        """
        # Skip animation if reduced motion preferred
        if AccessibilitySettings.prefers_reduced_motion():
            logger.debug("Success pulse skipped: reduced motion preferred")
            return

        # Stop any existing pulse animation
        if self._pulse_animation is not None:
            self._pulse_animation.stop()

        # Set success color for the pulse
        self._shadow_effect.setColor(self._get_success_color())

        # Create pulse animation (grow then shrink)
        self._pulse_animation = QPropertyAnimation(self._shadow_effect, b"blurRadius")
        self._pulse_animation.setDuration(ANIMATIONS.emphasis)  # 400ms

        # Use keyframes for pulse effect (0 -> max -> 0)
        self._pulse_animation.setStartValue(0)
        self._pulse_animation.setEndValue(0)

        # We'll use a custom update to create the pulse effect
        # Since QPropertyAnimation doesn't support keyframes directly,
        # we simulate it with valueChanged
        self._pulse_max_reached = False
        self._pulse_animation.valueChanged.connect(self._on_pulse_value_changed)
        self._pulse_animation.finished.connect(self._on_pulse_animation_finished)

        # Actually, let's use a simpler approach: sequential animations
        self._pulse_animation.deleteLater()
        self._pulse_animation = None

        # Create sequential animation: fade in then fade out
        from PySide6.QtCore import QSequentialAnimationGroup

        self._pulse_animation = QSequentialAnimationGroup(self)

        # Fade in glow
        pulse_in = QPropertyAnimation(self._shadow_effect, b"blurRadius")
        pulse_in.setDuration(ANIMATIONS.emphasis // 2)
        pulse_in.setStartValue(0)
        pulse_in.setEndValue(SHADOW_BLUR_RADIUS_FOCUSED * 1.5)
        pulse_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pulse_animation.addAnimation(pulse_in)

        # Fade out glow
        pulse_out = QPropertyAnimation(self._shadow_effect, b"blurRadius")
        pulse_out.setDuration(ANIMATIONS.emphasis // 2)
        pulse_out.setStartValue(SHADOW_BLUR_RADIUS_FOCUSED * 1.5)
        pulse_out.setEndValue(0)
        pulse_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._pulse_animation.addAnimation(pulse_out)

        self._pulse_animation.finished.connect(self._on_pulse_animation_finished)
        self._pulse_animation.start()

        logger.debug("Success pulse animation started")

    def _on_pulse_value_changed(self, value: float) -> None:
        """Handle pulse animation value changes (unused in current implementation)."""
        pass

    def _on_pulse_animation_finished(self) -> None:
        """Clean up after pulse animation finishes."""
        # Reset shadow color to focus color
        self._shadow_effect.setColor(self._get_focus_color())
        self._pulse_animation = None
        logger.debug("Success pulse animation finished")

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def stop_animations(self) -> None:
        """
        Stop all running animations.

        Call this before destroying the widget or when animations
        need to be cancelled immediately.
        """
        if self._focus_animation is not None:
            self._focus_animation.stop()
            self._focus_animation = None

        if self._shake_animation is not None:
            self._shake_animation.stop()
            self._shake_animation = None
            self._is_animating = False

        if self._pulse_animation is not None:
            self._pulse_animation.stop()
            self._pulse_animation = None

        # Reset shadow to unfocused state
        self._shadow_effect.setBlurRadius(SHADOW_BLUR_RADIUS_UNFOCUSED)
        self._shadow_effect.setColor(self._get_focus_color())


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_animated_line_edit(
    placeholder: str = "",
    parent: Optional[QWidget] = None,
) -> AnimatedLineEdit:
    """
    Create an AnimatedLineEdit with common configuration.

    Args:
        placeholder: Placeholder text to display when empty.
        parent: Parent widget.

    Returns:
        Configured AnimatedLineEdit instance.

    Example:
        name_input = create_animated_line_edit(
            placeholder="Enter your name...",
            parent=self,
        )
    """
    line_edit = AnimatedLineEdit(parent)

    if placeholder:
        line_edit.setPlaceholderText(placeholder)

    return line_edit


__all__ = [
    "AnimatedLineEdit",
    "create_animated_line_edit",
]
