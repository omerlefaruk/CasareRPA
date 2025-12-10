"""
Animated tooltip widget with fade in/out animations.

Provides a custom tooltip with smooth opacity transitions and optional
slide-up effect while respecting accessibility settings.

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_tooltip import (
        AnimatedToolTip,
        show_animated_tooltip,
    )

    # Direct usage
    tooltip = AnimatedToolTip()
    tooltip.showAt(widget.mapToGlobal(QPoint(0, 30)), "Tooltip text")

    # Factory function
    show_animated_tooltip(button, "Save changes")

    # With mouse tracking
    tooltip.setFollowMouse(True)
"""

from typing import Optional

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
)
from PySide6.QtGui import QCursor, QEnterEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QLabel,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedToolTip(QLabel):
    """
    Custom tooltip widget with fade in/out animations.

    Features:
        - Fade in animation on show (100ms)
        - Fade out animation on hide (80ms)
        - Optional slide-up effect on show
        - Respects AccessibilitySettings.prefers_reduced_motion()
        - Auto-hide after delay
        - Mouse tracking support
        - Dark themed appearance matching CasareRPA style

    The tooltip uses QGraphicsOpacityEffect for smooth fading
    and QPropertyAnimation for the transition.
    """

    # Animation durations
    FADE_IN_DURATION = ANIMATIONS.fast  # 100ms
    FADE_OUT_DURATION = 80  # Slightly faster fade out
    SLIDE_OFFSET = 8  # Pixels to slide up

    # Auto-hide delay
    DEFAULT_HIDE_DELAY = 3000  # 3 seconds

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated tooltip.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Animation state
        self._opacity_effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self)
        self._fade_anim: Optional[QPropertyAnimation] = None
        self._slide_anim: Optional[QPropertyAnimation] = None
        self._anim_group: Optional[QSequentialAnimationGroup] = None
        self._is_visible: bool = False
        self._follow_mouse: bool = False
        self._target_widget: Optional[QWidget] = None
        self._base_pos: QPoint = QPoint()
        self._auto_hide_timer: QTimer = QTimer(self)

        # Setup
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        """Setup the tooltip appearance."""
        # Window flags for tooltip behavior
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Apply opacity effect
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        # Apply theme styling
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dark theme styling matching CasareRPA."""
        colors = Theme.get_colors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                font-family: 'Segoe UI', 'SF Pro Text', system-ui, sans-serif;
            }}
        """)

    def _setup_timer(self) -> None:
        """Setup auto-hide timer."""
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hideAnimated)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def showAt(
        self,
        point: QPoint,
        text: str,
        delay: int = DEFAULT_HIDE_DELAY,
        slide: bool = True,
    ) -> None:
        """
        Show the tooltip at the specified position with animation.

        Args:
            point: Global screen position for the tooltip.
            text: Tooltip text to display.
            delay: Auto-hide delay in milliseconds (0 to disable).
            slide: Whether to include slide-up effect.
        """
        # Stop any running animations
        self._stop_animations()

        # Update text and adjust size
        self.setText(text)
        self.adjustSize()

        # Calculate position with screen bounds checking
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_rect = screen.availableGeometry()
            x = point.x()
            y = point.y()

            # Adjust if tooltip would go off screen
            if x + self.width() > screen_rect.right():
                x = screen_rect.right() - self.width() - 5
            if y + self.height() > screen_rect.bottom():
                y = screen_rect.bottom() - self.height() - 5
            if x < screen_rect.left():
                x = screen_rect.left() + 5
            if y < screen_rect.top():
                y = screen_rect.top() + 5

            point = QPoint(x, y)

        self._base_pos = point

        # Start animation or show instantly
        if AccessibilitySettings.prefers_reduced_motion():
            self._show_instant(point)
        else:
            self._animate_show(point, slide)

        # Setup auto-hide timer
        if delay > 0:
            self._auto_hide_timer.start(delay)

        self._is_visible = True

    def hideAnimated(self) -> None:
        """Hide the tooltip with fade out animation."""
        if not self._is_visible:
            return

        self._auto_hide_timer.stop()

        if AccessibilitySettings.prefers_reduced_motion():
            self._hide_instant()
        else:
            self._animate_hide()

    def setFollowMouse(self, follow: bool) -> None:
        """
        Enable or disable mouse tracking.

        When enabled, the tooltip follows the mouse cursor.

        Args:
            follow: Whether to follow mouse movement.
        """
        self._follow_mouse = follow

        if follow:
            self.setMouseTracking(True)
            if self._target_widget is not None:
                self._target_widget.setMouseTracking(True)

    def setTargetWidget(self, widget: Optional[QWidget]) -> None:
        """
        Set the target widget for mouse tracking.

        Args:
            widget: Widget to track mouse events on.
        """
        self._target_widget = widget

    # =========================================================================
    # ANIMATION METHODS
    # =========================================================================

    def _stop_animations(self) -> None:
        """Stop all running animations."""
        if self._fade_anim is not None:
            self._fade_anim.stop()
            self._fade_anim = None

        if self._slide_anim is not None:
            self._slide_anim.stop()
            self._slide_anim = None

        if self._anim_group is not None:
            self._anim_group.stop()
            self._anim_group = None

    def _show_instant(self, point: QPoint) -> None:
        """Show tooltip instantly without animation."""
        self._opacity_effect.setOpacity(1.0)
        self.move(point)
        self.show()
        logger.debug(f"Tooltip shown instantly at {point}")

    def _hide_instant(self) -> None:
        """Hide tooltip instantly without animation."""
        self._opacity_effect.setOpacity(0.0)
        self.hide()
        self._is_visible = False
        logger.debug("Tooltip hidden instantly")

    def _animate_show(self, point: QPoint, slide: bool) -> None:
        """
        Animate tooltip appearance.

        Args:
            point: Target position.
            slide: Whether to include slide effect.
        """
        # Position tooltip
        if slide:
            # Start slightly below target for slide-up effect
            start_pos = QPoint(point.x(), point.y() + self.SLIDE_OFFSET)
            self.move(start_pos)
        else:
            self.move(point)

        # Reset opacity and show
        self._opacity_effect.setOpacity(0.0)
        self.show()

        # Create fade animation
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(self.FADE_IN_DURATION)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if slide:
            # Create slide animation (position)
            self._slide_anim = QPropertyAnimation(self, b"pos", self)
            self._slide_anim.setDuration(self.FADE_IN_DURATION)
            self._slide_anim.setStartValue(
                QPoint(point.x(), point.y() + self.SLIDE_OFFSET)
            )
            self._slide_anim.setEndValue(point)
            self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            # Run both animations in parallel by starting them together
            self._fade_anim.start()
            self._slide_anim.start()
        else:
            self._fade_anim.start()

        logger.debug(f"Tooltip animation started at {point}, slide={slide}")

    def _animate_hide(self) -> None:
        """Animate tooltip fade out."""
        self._stop_animations()

        # Create fade out animation
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(self.FADE_OUT_DURATION)
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self._on_fade_out_finished)
        self._fade_anim.start()

        logger.debug("Tooltip fade out started")

    def _on_fade_out_finished(self) -> None:
        """Handle fade out animation completion."""
        self.hide()
        self._is_visible = False
        self._fade_anim = None
        logger.debug("Tooltip fade out completed")

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - stop auto-hide timer."""
        super().enterEvent(event)
        self._auto_hide_timer.stop()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - restart auto-hide timer."""
        super().leaveEvent(event)
        if self._is_visible:
            self._auto_hide_timer.start(self.DEFAULT_HIDE_DELAY)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for tracking."""
        super().mouseMoveEvent(event)

        if self._follow_mouse and self._is_visible:
            cursor_pos = QCursor.pos()
            # Offset from cursor to avoid obscuring target
            self.move(cursor_pos.x() + 15, cursor_pos.y() + 15)


def show_animated_tooltip(
    widget: QWidget,
    text: str,
    offset: QPoint = QPoint(0, 25),
    delay: int = AnimatedToolTip.DEFAULT_HIDE_DELAY,
    slide: bool = True,
) -> AnimatedToolTip:
    """
    Factory function to show an animated tooltip near a widget.

    Creates and displays an AnimatedToolTip positioned relative to the
    specified widget.

    Args:
        widget: Widget to show tooltip near.
        text: Tooltip text.
        offset: Offset from widget's top-left corner (default below widget).
        delay: Auto-hide delay in milliseconds (0 to disable).
        slide: Whether to include slide-up animation effect.

    Returns:
        The AnimatedToolTip instance for further customization.

    Example:
        # Show tooltip below a button
        show_animated_tooltip(save_button, "Save changes (Ctrl+S)")

        # Show tooltip to the right of a widget
        show_animated_tooltip(icon, "Status: Active", offset=QPoint(30, 0))

        # Show tooltip without auto-hide
        tooltip = show_animated_tooltip(widget, "Click to edit", delay=0)
        # ... later ...
        tooltip.hideAnimated()
    """
    tooltip = AnimatedToolTip()

    # Calculate global position
    global_pos = widget.mapToGlobal(offset)

    # Show the tooltip
    tooltip.showAt(global_pos, text, delay=delay, slide=slide)

    return tooltip
