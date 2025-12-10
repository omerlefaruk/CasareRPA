"""
Combo box with animated hover effects.

Provides smooth hover highlight animation for combo boxes.
Qt's native popup is used (cannot be easily animated), so this
focuses on hover feedback only.

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_combo_box import (
        AnimatedComboBox,
        create_animated_combo_box,
    )

    combo = create_animated_combo_box()
    combo.addItems(["Option 1", "Option 2", "Option 3"])
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Property,
    Signal,
)
from PySide6.QtGui import QColor, QEnterEvent
from PySide6.QtWidgets import QComboBox, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedComboBox(QComboBox):
    """
    Combo box with animated hover highlight effect.

    Features:
    - Smooth border color transition on hover
    - Respects OS accessibility settings for reduced motion
    - Uses theme colors for consistent styling

    Note:
        Qt's native popup dropdown cannot be easily animated, so
        this class focuses on hover feedback only.

    Signals:
        hoverStarted: Emitted when mouse enters the widget
        hoverEnded: Emitted when mouse leaves the widget
    """

    hoverStarted = Signal()
    hoverEnded = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Animation state
        self._hover_animation: Optional[QPropertyAnimation] = None
        self._animation_enabled: bool = True

        # Color interpolation value (0.0 = normal, 1.0 = hovered)
        self._hover_progress: float = 0.0

        # Cache theme colors
        self._update_theme_colors()

        # Apply initial style
        self._apply_style()

        # Enable mouse tracking for hover detection
        self.setMouseTracking(True)

        logger.debug("AnimatedComboBox initialized")

    def _update_theme_colors(self) -> None:
        """Cache colors from current theme."""
        colors = Theme.get_colors()
        self._bg_color = QColor(colors.background)
        self._border_color = QColor(colors.border)
        self._border_hover_color = QColor(colors.border_focus)
        self._text_color = QColor(colors.text_primary)
        self._text_secondary_color = QColor(colors.text_secondary)

    def setAnimationEnabled(self, enabled: bool) -> None:
        """
        Enable or disable hover animations.

        Args:
            enabled: True to enable animations, False to disable.
        """
        self._animation_enabled = enabled
        logger.debug(f"ComboBox animation enabled: {enabled}")

    def isAnimationEnabled(self) -> bool:
        """Return whether animations are enabled."""
        return self._animation_enabled

    def _should_animate(self) -> bool:
        """Check if animation should run based on settings."""
        if not self._animation_enabled:
            return False
        if AccessibilitySettings.prefers_reduced_motion():
            return False
        return True

    def _get_hover_progress(self) -> float:
        """Get current hover animation progress."""
        return self._hover_progress

    def _set_hover_progress(self, value: float) -> None:
        """
        Set hover animation progress and update style.

        Args:
            value: Progress from 0.0 (normal) to 1.0 (hovered).
        """
        self._hover_progress = value
        self._apply_style()

    # Qt Property for animation
    hoverProgress = Property(
        float,
        _get_hover_progress,
        _set_hover_progress,
    )

    def _interpolate_color(self, c1: QColor, c2: QColor, t: float) -> str:
        """
        Interpolate between two colors.

        Args:
            c1: Start color.
            c2: End color.
            t: Interpolation factor (0.0 = c1, 1.0 = c2).

        Returns:
            Hex color string.
        """
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _apply_style(self) -> None:
        """Apply stylesheet based on current hover progress."""
        # Interpolate border color based on hover progress
        border_color = self._interpolate_color(
            self._border_color,
            self._border_hover_color,
            self._hover_progress,
        )

        colors = Theme.get_colors()
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors.background};
                color: {colors.text_primary};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
            }}
            QComboBox:focus {{
                border-color: {colors.border_focus};
            }}
            QComboBox:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                selection-background-color: {colors.accent};
                outline: none;
            }}
        """)

    def _stop_current_animation(self) -> None:
        """Stop any running animation."""
        if (
            self._hover_animation
            and self._hover_animation.state() == QPropertyAnimation.State.Running
        ):
            self._hover_animation.stop()

    def _animate_hover(self, entering: bool) -> None:
        """
        Animate hover state transition.

        Args:
            entering: True if mouse entering, False if leaving.
        """
        if not self._should_animate():
            # No animation: instant state change
            self._hover_progress = 1.0 if entering else 0.0
            self._apply_style()
            return

        # Stop any running animation
        self._stop_current_animation()

        # Create animation
        self._hover_animation = QPropertyAnimation(self, b"hoverProgress")
        self._hover_animation.setDuration(ANIMATIONS.fast)  # 100ms
        self._hover_animation.setStartValue(self._hover_progress)
        self._hover_animation.setEndValue(1.0 if entering else 0.0)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_animation.start()

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter event."""
        self.hoverStarted.emit()
        self._animate_hover(entering=True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave event."""
        self.hoverEnded.emit()
        self._animate_hover(entering=False)
        super().leaveEvent(event)

    def showEvent(self, event) -> None:
        """Handle show event - update theme colors."""
        self._update_theme_colors()
        self._apply_style()
        super().showEvent(event)


def create_animated_combo_box(
    parent: Optional[QWidget] = None,
    items: Optional[list[str]] = None,
    animation_enabled: bool = True,
) -> AnimatedComboBox:
    """
    Factory function to create an AnimatedComboBox.

    Args:
        parent: Parent widget.
        items: Optional list of items to add.
        animation_enabled: Enable hover animation.

    Returns:
        Configured AnimatedComboBox instance.
    """
    combo = AnimatedComboBox(parent)
    combo.setAnimationEnabled(animation_enabled)

    if items:
        combo.addItems(items)

    return combo
