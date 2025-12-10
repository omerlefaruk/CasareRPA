"""
Animated SpinBox widgets with smooth value change animations.

Provides QSpinBox and QDoubleSpinBox subclasses with visual feedback
on value changes. Features subtle color flash animation when values update.

Accessibility:
- Respects AccessibilitySettings.prefers_reduced_motion()
- Falls back to instant changes when motion is reduced

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_spin_box import (
        AnimatedSpinBox,
        AnimatedDoubleSpinBox,
        create_animated_spin_box,
        create_animated_double_spin_box,
    )

    # Basic usage
    spin_box = AnimatedSpinBox()
    spin_box.setRange(0, 100)

    # With label
    spin_box = create_animated_spin_box(
        minimum=0,
        maximum=100,
        initial_value=50,
        suffix=" ms",
    )

    # Double spin box
    double_spin = create_animated_double_spin_box(
        minimum=0.0,
        maximum=1.0,
        initial_value=0.5,
        decimals=2,
    )
"""

from typing import Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QWidget

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedSpinBox(QSpinBox):
    """
    QSpinBox with smooth value change animation.

    Features:
    - Subtle background color flash on value change
    - Respects reduced motion preferences
    - Uses theme colors for consistency

    The animation is a brief pulse from accent color back to normal,
    providing visual confirmation that the value was updated.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated spin box.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._animation: Optional[QPropertyAnimation] = None
        self._flash_color: QColor = QColor(Theme.get_colors().background)

        # Track previous value to detect actual changes
        self._previous_value: int = 0

        # Connect value changed signal
        self.valueChanged.connect(self._on_value_changed)

        # Apply initial styling
        self._update_style_for_color(self._flash_color)

    def _get_flash_color(self) -> QColor:
        """Get the current flash color."""
        return self._flash_color

    def _set_flash_color(self, color: QColor) -> None:
        """Set the flash color and update stylesheet."""
        self._flash_color = color
        self._update_style_for_color(color)

    # Property for QPropertyAnimation
    flashColor = Property(QColor, _get_flash_color, _set_flash_color)

    def _update_style_for_color(self, color: QColor) -> None:
        """
        Update the stylesheet with the given background color.

        Args:
            color: Background color to apply
        """
        colors = Theme.get_colors()
        self.setStyleSheet(f"""
            QSpinBox {{
                background-color: {color.name()};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: 4px;
                padding: 6px;
            }}
            QSpinBox:focus {{
                border-color: {colors.border_focus};
            }}
            QSpinBox:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 16px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {colors.surface_hover};
            }}
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
                background-color: {colors.primary_pressed};
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {colors.text_secondary};
                width: 0;
                height: 0;
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                width: 0;
                height: 0;
            }}
        """)

    def _on_value_changed(self, value: int) -> None:
        """
        Handle value change and trigger animation.

        Args:
            value: New value
        """
        # Skip animation if value hasn't actually changed
        if value == self._previous_value:
            return

        self._previous_value = value

        # Check accessibility preference
        if AccessibilitySettings.prefers_reduced_motion():
            return

        self._animate_flash()

    def _animate_flash(self) -> None:
        """Animate a color flash to indicate value change."""
        colors = Theme.get_colors()

        # Stop any existing animation
        if self._animation is not None:
            self._animation.stop()

        # Create flash animation
        self._animation = QPropertyAnimation(self, b"flashColor")
        self._animation.setDuration(ANIMATIONS.normal)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Flash from accent highlight to normal background
        highlight_color = QColor(colors.selection)
        highlight_color.setAlpha(180)
        normal_color = QColor(colors.background)

        self._animation.setStartValue(highlight_color)
        self._animation.setEndValue(normal_color)

        try:
            self._animation.start()
        except RuntimeError:
            # Widget may have been deleted
            logger.debug("SpinBox animation failed - widget may be deleted")


class AnimatedDoubleSpinBox(QDoubleSpinBox):
    """
    QDoubleSpinBox with smooth value change animation.

    Features:
    - Subtle background color flash on value change
    - Respects reduced motion preferences
    - Uses theme colors for consistency

    The animation is a brief pulse from accent color back to normal,
    providing visual confirmation that the value was updated.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated double spin box.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._animation: Optional[QPropertyAnimation] = None
        self._flash_color: QColor = QColor(Theme.get_colors().background)

        # Track previous value to detect actual changes
        self._previous_value: float = 0.0

        # Connect value changed signal
        self.valueChanged.connect(self._on_value_changed)

        # Apply initial styling
        self._update_style_for_color(self._flash_color)

    def _get_flash_color(self) -> QColor:
        """Get the current flash color."""
        return self._flash_color

    def _set_flash_color(self, color: QColor) -> None:
        """Set the flash color and update stylesheet."""
        self._flash_color = color
        self._update_style_for_color(color)

    # Property for QPropertyAnimation
    flashColor = Property(QColor, _get_flash_color, _set_flash_color)

    def _update_style_for_color(self, color: QColor) -> None:
        """
        Update the stylesheet with the given background color.

        Args:
            color: Background color to apply
        """
        colors = Theme.get_colors()
        self.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {color.name()};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: 4px;
                padding: 6px;
            }}
            QDoubleSpinBox:focus {{
                border-color: {colors.border_focus};
            }}
            QDoubleSpinBox:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 16px;
            }}
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {colors.surface_hover};
            }}
            QDoubleSpinBox::up-button:pressed, QDoubleSpinBox::down-button:pressed {{
                background-color: {colors.primary_pressed};
            }}
            QDoubleSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {colors.text_secondary};
                width: 0;
                height: 0;
            }}
            QDoubleSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                width: 0;
                height: 0;
            }}
        """)

    def _on_value_changed(self, value: float) -> None:
        """
        Handle value change and trigger animation.

        Args:
            value: New value
        """
        # Skip animation if value hasn't actually changed (within floating point tolerance)
        if abs(value - self._previous_value) < 1e-10:
            return

        self._previous_value = value

        # Check accessibility preference
        if AccessibilitySettings.prefers_reduced_motion():
            return

        self._animate_flash()

    def _animate_flash(self) -> None:
        """Animate a color flash to indicate value change."""
        colors = Theme.get_colors()

        # Stop any existing animation
        if self._animation is not None:
            self._animation.stop()

        # Create flash animation
        self._animation = QPropertyAnimation(self, b"flashColor")
        self._animation.setDuration(ANIMATIONS.normal)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Flash from accent highlight to normal background
        highlight_color = QColor(colors.selection)
        highlight_color.setAlpha(180)
        normal_color = QColor(colors.background)

        self._animation.setStartValue(highlight_color)
        self._animation.setEndValue(normal_color)

        try:
            self._animation.start()
        except RuntimeError:
            # Widget may have been deleted
            logger.debug("DoubleSpinBox animation failed - widget may be deleted")


def create_animated_spin_box(
    minimum: int = 0,
    maximum: int = 100,
    initial_value: int = 0,
    step: int = 1,
    suffix: str = "",
    prefix: str = "",
    parent: Optional[QWidget] = None,
) -> AnimatedSpinBox:
    """
    Factory function to create a configured AnimatedSpinBox.

    Args:
        minimum: Minimum value
        maximum: Maximum value
        initial_value: Initial value to set
        step: Step size for increment/decrement
        suffix: Suffix text to display after value
        prefix: Prefix text to display before value
        parent: Parent widget

    Returns:
        Configured AnimatedSpinBox instance
    """
    spin_box = AnimatedSpinBox(parent)
    spin_box.setRange(minimum, maximum)
    spin_box.setValue(initial_value)
    spin_box.setSingleStep(step)

    if suffix:
        spin_box.setSuffix(suffix)
    if prefix:
        spin_box.setPrefix(prefix)

    return spin_box


def create_animated_double_spin_box(
    minimum: float = 0.0,
    maximum: float = 100.0,
    initial_value: float = 0.0,
    step: float = 1.0,
    decimals: int = 2,
    suffix: str = "",
    prefix: str = "",
    parent: Optional[QWidget] = None,
) -> AnimatedDoubleSpinBox:
    """
    Factory function to create a configured AnimatedDoubleSpinBox.

    Args:
        minimum: Minimum value
        maximum: Maximum value
        initial_value: Initial value to set
        step: Step size for increment/decrement
        decimals: Number of decimal places to display
        suffix: Suffix text to display after value
        prefix: Prefix text to display before value
        parent: Parent widget

    Returns:
        Configured AnimatedDoubleSpinBox instance
    """
    spin_box = AnimatedDoubleSpinBox(parent)
    spin_box.setRange(minimum, maximum)
    spin_box.setValue(initial_value)
    spin_box.setSingleStep(step)
    spin_box.setDecimals(decimals)

    if suffix:
        spin_box.setSuffix(suffix)
    if prefix:
        spin_box.setPrefix(prefix)

    return spin_box
