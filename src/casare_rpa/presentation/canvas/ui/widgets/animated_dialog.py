"""
Animated dialog base class for smooth dialog transitions.

All dialogs in CasareRPA should inherit from this class to get
consistent open/close animations.

Usage:
    class MyDialog(AnimatedDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            # Setup your dialog UI...

    # Dialog will automatically animate when shown/closed
    dialog = MyDialog()
    dialog.exec()  # Fades in
    dialog.accept()  # Fades out then closes
"""

from typing import Callable, Optional

from loguru import logger
from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation
from PySide6.QtWidgets import QDialog, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.animation_pool import AnimationPool
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedDialog(QDialog):
    """
    Base dialog class with smooth open/close animations.

    Features:
        - Fade in + scale animation on show (0.95 -> 1.0 scale effect via opacity)
        - Fade out animation on close
        - Respects AccessibilitySettings (reduced motion preference)
        - Uses AnimationPool for efficient animation object reuse

    Subclasses can override _get_open_duration() and _get_close_duration()
    to customize animation timing.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated dialog.

        Args:
            parent: Parent widget for the dialog.
        """
        super().__init__(parent)
        self._opening_animation: Optional[QParallelAnimationGroup] = None
        self._closing_animation: Optional[QParallelAnimationGroup] = None
        self._close_callback: Optional[Callable[[], None]] = None
        self._fade_anim: Optional[QPropertyAnimation] = None

        # Apply theme styling
        self.setStyleSheet(Theme.message_box_style())

    def showEvent(self, event) -> None:
        """Override to animate dialog opening."""
        super().showEvent(event)
        self._animate_open()

    def _get_open_duration(self) -> int:
        """
        Get the duration for open animation.

        Override in subclasses for custom timing.

        Returns:
            Duration in milliseconds.
        """
        return ANIMATIONS.slow  # 300ms

    def _get_close_duration(self) -> int:
        """
        Get the duration for close animation.

        Override in subclasses for custom timing.

        Returns:
            Duration in milliseconds.
        """
        return ANIMATIONS.normal  # 150ms

    def _animate_open(self) -> None:
        """Fade in with subtle scale effect."""
        if AccessibilitySettings.prefers_reduced_motion():
            self.setWindowOpacity(1.0)
            return

        # Start invisible
        self.setWindowOpacity(0.0)

        # Acquire animation from pool
        self._fade_anim = AnimationPool.acquire("fade")
        self._fade_anim.setTargetObject(self)
        self._fade_anim.setPropertyName(b"windowOpacity")
        self._fade_anim.setDuration(self._get_open_duration())
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Create animation group
        self._opening_animation = QParallelAnimationGroup(self)
        self._opening_animation.addAnimation(self._fade_anim)
        self._opening_animation.finished.connect(self._on_open_finished)
        self._opening_animation.start()

    def _on_open_finished(self) -> None:
        """Called when open animation completes."""
        # Release animation back to pool
        if self._fade_anim is not None:
            AnimationPool.release(self._fade_anim, "fade")
            self._fade_anim = None

        self._opening_animation = None

    def accept(self) -> None:
        """Override to animate before accepting."""
        self._animate_close(super().accept)

    def reject(self) -> None:
        """Override to animate before rejecting."""
        self._animate_close(super().reject)

    def _animate_close(self, callback: Callable[[], None]) -> None:
        """
        Fade out then call callback.

        Args:
            callback: Function to call after animation completes
                     (typically super().accept or super().reject).
        """
        if AccessibilitySettings.prefers_reduced_motion():
            callback()
            return

        self._close_callback = callback

        # Acquire animation from pool
        self._fade_anim = AnimationPool.acquire("fade")
        self._fade_anim.setTargetObject(self)
        self._fade_anim.setPropertyName(b"windowOpacity")
        self._fade_anim.setDuration(self._get_close_duration())
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        # Create animation group
        self._closing_animation = QParallelAnimationGroup(self)
        self._closing_animation.addAnimation(self._fade_anim)
        self._closing_animation.finished.connect(self._on_close_finished)
        self._closing_animation.start()

    def _on_close_finished(self) -> None:
        """Called when close animation completes."""
        # Release animation back to pool
        if self._fade_anim is not None:
            AnimationPool.release(self._fade_anim, "fade")
            self._fade_anim = None

        self._closing_animation = None

        # Execute the close callback
        if self._close_callback is not None:
            self._close_callback()
            self._close_callback = None

    def closeEvent(self, event) -> None:
        """
        Handle window close button (X) clicks.

        Intercepts the close event to animate before closing.
        """
        if AccessibilitySettings.prefers_reduced_motion():
            super().closeEvent(event)
            return

        # Prevent immediate close
        event.ignore()

        # Animate then reject
        self._animate_close(lambda: super(AnimatedDialog, self).closeEvent(event))
