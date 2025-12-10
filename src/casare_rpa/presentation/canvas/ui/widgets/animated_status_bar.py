"""
Animated Status Bar Widget for CasareRPA.

Provides smooth message transitions with crossfade and slide-in animations.

Features:
- Crossfade animation between messages
- Slide-in effect for new messages from bottom
- Respects AccessibilitySettings.prefers_reduced_motion()
- Uses ANIMATIONS from theme.py for consistent timing

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_status_bar import (
        AnimatedStatusBar,
        create_animated_status_bar,
    )

    # Create with factory function
    status_bar = create_animated_status_bar()
    status_bar.showAnimatedMessage("File saved", timeout=3000)

    # Or create directly
    status_bar = AnimatedStatusBar()
    layout.addWidget(status_bar)
    status_bar.showAnimatedMessage("Ready", timeout=0)  # Permanent message
"""

from typing import Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QStatusBar,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedStatusBar(QStatusBar):
    """
    Status bar with smooth message transition animations.

    Extends QStatusBar to provide:
    - Crossfade animation when messages change
    - Slide-in effect from bottom for new messages
    - Automatic timeout handling
    - Accessibility support (reduced motion preference)

    The showAnimatedMessage() method should be used instead of showMessage()
    to get animated transitions.

    Attributes:
        MESSAGE_SLIDE_OFFSET: Vertical pixels for slide animation (default 8)
    """

    MESSAGE_SLIDE_OFFSET = 8

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated status bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Animation state
        self._fade_animation: Optional[QPropertyAnimation] = None
        self._slide_animation: Optional[QPropertyAnimation] = None
        self._animation_group: Optional[QParallelAnimationGroup] = None
        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._message_timeout_timer: Optional[QTimer] = None

        # Current message label for animation
        self._message_label: Optional[QLabel] = None
        self._pending_message: Optional[str] = None
        self._pending_timeout: int = 0
        self._is_animating: bool = False

        # Slide position tracking
        self._slide_offset: float = 0.0

        # Initialize opacity effect on the status bar itself
        self._setup_opacity_effect()

    def _setup_opacity_effect(self) -> None:
        """Setup the opacity effect for fade animations."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

    def _get_slide_offset(self) -> float:
        """Get current slide offset for animation."""
        return self._slide_offset

    def _set_slide_offset(self, value: float) -> None:
        """
        Set slide offset and update label position.

        The slide offset moves the content vertically to create
        a slide-in effect from the bottom.

        Args:
            value: Vertical offset in pixels (0 = normal position)
        """
        self._slide_offset = value
        if self._message_label is not None:
            # Apply vertical offset through margin
            margin = int(value)
            self._message_label.setContentsMargins(0, margin, 0, 0)
        self.update()

    slideOffset = Property(float, _get_slide_offset, _set_slide_offset)

    def showAnimatedMessage(
        self,
        message: str,
        timeout: int = 0,
    ) -> None:
        """
        Show a message with fade and slide animation.

        If an animation is already in progress, the new message is queued
        and will be shown after the current animation completes.

        Args:
            message: Message text to display
            timeout: Auto-clear timeout in milliseconds. 0 = permanent.
        """
        logger.debug(f"AnimatedStatusBar: showAnimatedMessage('{message}', {timeout})")

        # Handle reduced motion preference
        if AccessibilitySettings.prefers_reduced_motion():
            self._show_message_immediate(message, timeout)
            return

        # If currently animating, queue the message
        if self._is_animating:
            self._pending_message = message
            self._pending_timeout = timeout
            logger.debug("AnimatedStatusBar: Message queued during animation")
            return

        # Start crossfade transition
        self._animate_message_transition(message, timeout)

    def _show_message_immediate(self, message: str, timeout: int) -> None:
        """
        Show message immediately without animation.

        Used when reduced motion is preferred or as fallback.

        Args:
            message: Message text
            timeout: Auto-clear timeout in milliseconds
        """
        self._stop_animations()
        super().showMessage(message, timeout)

    def _animate_message_transition(self, message: str, timeout: int) -> None:
        """
        Animate transition to new message.

        Creates a parallel animation group with:
        - Fade out current (if visible) then fade in new
        - Slide in from bottom

        Args:
            message: New message text
            timeout: Auto-clear timeout
        """
        self._stop_animations()
        self._is_animating = True

        # Store timeout for later
        self._pending_timeout = timeout

        # Ensure opacity effect exists
        if self._opacity_effect is None:
            self._setup_opacity_effect()

        # Get current opacity (might be mid-animation)
        current_opacity = self._opacity_effect.opacity()

        # Create animation group for parallel fade + slide
        self._animation_group = QParallelAnimationGroup(self)

        # Fade out animation (brief fade to 0)
        duration = ANIMATIONS.fast  # 100ms

        # Check if there's already visible content
        has_content = bool(self.currentMessage())

        if has_content and current_opacity > 0:
            # Fade out first, then set message and fade in
            self._create_crossfade_animation(message, timeout, duration)
        else:
            # No content - just fade in with slide
            self._create_fade_in_animation(message, timeout, duration)

    def _create_crossfade_animation(
        self,
        message: str,
        timeout: int,
        duration: int,
    ) -> None:
        """
        Create crossfade animation for message transition.

        Fades out current message, sets new message, then fades in.

        Args:
            message: New message text
            timeout: Auto-clear timeout
            duration: Animation duration in ms
        """
        # Fade out
        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_out.setDuration(duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InQuad)

        # Connect to set message at end of fade out
        fade_out.finished.connect(
            lambda: self._on_fade_out_complete(message, timeout, duration)
        )

        self._fade_animation = fade_out
        fade_out.start()

        logger.debug("AnimatedStatusBar: Starting crossfade animation")

    def _on_fade_out_complete(
        self,
        message: str,
        timeout: int,
        duration: int,
    ) -> None:
        """
        Handle completion of fade out - set new message and fade in.

        Args:
            message: New message to display
            timeout: Auto-clear timeout
            duration: Fade in duration
        """
        # Set the new message (invisible at this point)
        super().showMessage(message, 0)  # We handle timeout ourselves

        # Fade in with slide
        self._create_fade_in_animation(message, timeout, duration)

    def _create_fade_in_animation(
        self,
        message: str,
        timeout: int,
        duration: int,
    ) -> None:
        """
        Create fade-in animation with slide effect.

        Args:
            message: Message text (already set or to be set)
            timeout: Auto-clear timeout
            duration: Animation duration
        """
        # Set message if not already set
        if self.currentMessage() != message:
            super().showMessage(message, 0)

        # Reset slide offset to start position
        self._slide_offset = self.MESSAGE_SLIDE_OFFSET

        # Create parallel animation group
        self._animation_group = QParallelAnimationGroup(self)

        # Fade in animation
        fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_in.setDuration(duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide up animation
        slide_up = QPropertyAnimation(self, b"slideOffset")
        slide_up.setDuration(duration)
        slide_up.setStartValue(float(self.MESSAGE_SLIDE_OFFSET))
        slide_up.setEndValue(0.0)
        slide_up.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._animation_group.addAnimation(fade_in)
        self._animation_group.addAnimation(slide_up)

        # Connect completion handler
        self._animation_group.finished.connect(
            lambda: self._on_animation_complete(timeout)
        )

        self._animation_group.start()

        logger.debug("AnimatedStatusBar: Starting fade-in with slide animation")

    def _on_animation_complete(self, timeout: int) -> None:
        """
        Handle animation completion.

        Sets up timeout timer if specified and processes queued messages.

        Args:
            timeout: Auto-clear timeout in milliseconds
        """
        self._is_animating = False

        # Setup timeout if specified
        if timeout > 0:
            self._start_timeout_timer(timeout)

        # Check for pending message
        if self._pending_message is not None:
            pending_msg = self._pending_message
            pending_timeout = self._pending_timeout
            self._pending_message = None
            self._pending_timeout = 0

            # Schedule next message (use QTimer to avoid recursion)
            QTimer.singleShot(
                0, lambda: self.showAnimatedMessage(pending_msg, pending_timeout)
            )

        logger.debug("AnimatedStatusBar: Animation complete")

    def _start_timeout_timer(self, timeout: int) -> None:
        """
        Start timer to clear message after timeout.

        Args:
            timeout: Timeout in milliseconds
        """
        # Cancel any existing timer
        if self._message_timeout_timer is not None:
            self._message_timeout_timer.stop()
            self._message_timeout_timer = None

        self._message_timeout_timer = QTimer(self)
        self._message_timeout_timer.setSingleShot(True)
        self._message_timeout_timer.timeout.connect(self._on_timeout)
        self._message_timeout_timer.start(timeout)

    def _on_timeout(self) -> None:
        """Handle message timeout - fade out and clear."""
        if AccessibilitySettings.prefers_reduced_motion():
            self.clearMessage()
            return

        # Fade out current message
        self._animate_fade_out_clear()

    def _animate_fade_out_clear(self) -> None:
        """Animate fade out and clear the message."""
        if self._opacity_effect is None:
            self.clearMessage()
            return

        self._stop_animations()

        # Fade out
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(ANIMATIONS.fast)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_animation.finished.connect(self._on_clear_fade_complete)
        self._fade_animation.start()

    def _on_clear_fade_complete(self) -> None:
        """Handle completion of fade out for clear - reset state."""
        self.clearMessage()
        # Reset opacity for next message
        if self._opacity_effect is not None:
            self._opacity_effect.setOpacity(1.0)

    def _stop_animations(self) -> None:
        """Stop all running animations."""
        if self._fade_animation is not None:
            self._fade_animation.stop()
            # Disconnect signals safely
            try:
                self._fade_animation.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            self._fade_animation = None

        if self._slide_animation is not None:
            self._slide_animation.stop()
            try:
                self._slide_animation.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            self._slide_animation = None

        if self._animation_group is not None:
            self._animation_group.stop()
            try:
                self._animation_group.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            self._animation_group = None

        self._is_animating = False

        # Reset opacity to full
        if self._opacity_effect is not None:
            self._opacity_effect.setOpacity(1.0)

        # Reset slide offset
        self._slide_offset = 0.0

    def clearMessage(self) -> None:
        """
        Clear the current message.

        Stops any running animations and clears immediately.
        """
        self._stop_animations()

        # Cancel timeout timer
        if self._message_timeout_timer is not None:
            self._message_timeout_timer.stop()
            self._message_timeout_timer = None

        # Clear pending message
        self._pending_message = None
        self._pending_timeout = 0

        super().clearMessage()

    @property
    def is_animating(self) -> bool:
        """Check if an animation is currently in progress."""
        return self._is_animating


def create_animated_status_bar(
    parent: Optional[QWidget] = None,
) -> AnimatedStatusBar:
    """
    Factory function to create a themed animated status bar.

    Creates an AnimatedStatusBar with theme-consistent styling.

    Args:
        parent: Parent widget

    Returns:
        Configured AnimatedStatusBar instance

    Example:
        status_bar = create_animated_status_bar()
        main_window.setStatusBar(status_bar)
        status_bar.showAnimatedMessage("Ready", timeout=0)
    """
    status_bar = AnimatedStatusBar(parent)

    # Apply theme styling consistent with get_canvas_stylesheet()
    colors = Theme.get_colors()
    status_bar.setStyleSheet(f"""
        QStatusBar {{
            background-color: {colors.accent};
            border-top: none;
            color: #FFFFFF;
            font-size: 11px;
            padding: 2px 8px;
        }}
        QStatusBar::item {{
            border: none;
        }}
    """)

    return status_bar
