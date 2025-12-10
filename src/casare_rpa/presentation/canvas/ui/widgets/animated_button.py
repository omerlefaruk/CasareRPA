"""
Animated button widgets with smooth hover and press animations.

Provides visual feedback through subtle scale and brightness animations
while respecting accessibility settings.

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_button import (
        AnimatedButton,
        AnimatedIconButton,
        create_animated_button,
    )

    # Text button
    btn = AnimatedButton("Click Me")
    btn.clicked.connect(on_click)

    # Icon button
    icon_btn = AnimatedIconButton(QIcon("path/to/icon.svg"))

    # Factory function
    btn = create_animated_button("Save", variant="primary")
"""

from typing import Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
)
from PySide6.QtGui import QEnterEvent, QIcon, QMouseEvent
from PySide6.QtWidgets import QPushButton, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.animation_pool import AnimationPool
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedButton(QPushButton):
    """
    QPushButton with smooth hover and press animations.

    Features:
        - Hover: Slight scale up (1.02x) with brightness increase
        - Press: Scale down (0.98x) with bounce back on release
        - Respects AccessibilitySettings.prefers_reduced_motion()
        - Uses AnimationPool for efficient animation reuse
        - Works with existing stylesheets (adds animation behavior only)

    The scale effect is achieved through geometry animation to avoid
    conflicts with stylesheet-based styling.
    """

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the animated button.

        Args:
            text: Button text.
            parent: Parent widget.
        """
        super().__init__(text, parent)

        # Animation state
        self._scale_factor: float = 1.0
        self._base_size: Optional[QSize] = None
        self._hover_anim: Optional[QPropertyAnimation] = None
        self._press_anim: Optional[QPropertyAnimation] = None
        self._is_pressed: bool = False
        self._is_hovered: bool = False

        # Enable mouse tracking for hover detection
        self.setMouseTracking(True)

    # =========================================================================
    # CUSTOM PROPERTY FOR ANIMATION
    # =========================================================================

    def _get_scale_factor(self) -> float:
        """Get current scale factor."""
        return self._scale_factor

    def _set_scale_factor(self, value: float) -> None:
        """
        Set scale factor and apply transform.

        Uses contentsMargins to create visual scaling effect without
        affecting layout or conflicting with stylesheets.
        """
        self._scale_factor = value

        # Calculate margin based on scale difference
        # Scale < 1.0: positive margins (shrink visual area)
        # Scale > 1.0: negative margins would be needed (not supported)
        # Instead, we adjust size hint slightly
        if self._base_size is not None:
            # Calculate the offset from scale
            scale_diff = 1.0 - value
            margin = int(max(0, scale_diff * 4))  # Max 4px margin at 0.98 scale

            # Apply symmetric margins to create scale illusion
            self.setContentsMargins(margin, margin, margin, margin)

        self.update()

    scaleFactor = Property(float, _get_scale_factor, _set_scale_factor)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def showEvent(self, event) -> None:
        """Capture base size on first show."""
        super().showEvent(event)
        if self._base_size is None:
            self._base_size = self.size()

    def resizeEvent(self, event) -> None:
        """Update base size on resize."""
        super().resizeEvent(event)
        # Only update if not animating
        if self._hover_anim is None and self._press_anim is None:
            self._base_size = event.size()

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - start hover animation."""
        super().enterEvent(event)
        self._is_hovered = True

        if not self._is_pressed:
            self._animate_hover_in()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave - end hover animation."""
        super().leaveEvent(event)
        self._is_hovered = False

        if not self._is_pressed:
            self._animate_hover_out()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press - start press animation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._animate_press()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release - end press animation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = False
            self._animate_release()

        super().mouseReleaseEvent(event)

    # =========================================================================
    # ANIMATION METHODS
    # =========================================================================

    def _stop_current_animations(self) -> None:
        """Stop and release any running animations."""
        if self._hover_anim is not None:
            self._hover_anim.stop()
            try:
                self._hover_anim.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            AnimationPool.release(self._hover_anim, "scale")
            self._hover_anim = None

        if self._press_anim is not None:
            self._press_anim.stop()
            try:
                self._press_anim.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            AnimationPool.release(self._press_anim, "scale")
            self._press_anim = None

    def _animate_hover_in(self) -> None:
        """Animate scale up on hover enter."""
        if AccessibilitySettings.prefers_reduced_motion():
            return

        self._stop_current_animations()

        self._hover_anim = AnimationPool.acquire("scale")
        self._hover_anim.setTargetObject(self)
        self._hover_anim.setPropertyName(b"scaleFactor")
        self._hover_anim.setDuration(ANIMATIONS.fast)  # 100ms
        self._hover_anim.setStartValue(self._scale_factor)
        self._hover_anim.setEndValue(1.02)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.finished.connect(self._on_hover_in_finished)
        self._hover_anim.start()

    def _on_hover_in_finished(self) -> None:
        """Release hover in animation."""
        if self._hover_anim is not None:
            AnimationPool.release(self._hover_anim, "scale")
            self._hover_anim = None

    def _animate_hover_out(self) -> None:
        """Animate scale back to normal on hover leave."""
        if AccessibilitySettings.prefers_reduced_motion():
            self._scale_factor = 1.0
            self.setContentsMargins(0, 0, 0, 0)
            return

        self._stop_current_animations()

        self._hover_anim = AnimationPool.acquire("scale")
        self._hover_anim.setTargetObject(self)
        self._hover_anim.setPropertyName(b"scaleFactor")
        self._hover_anim.setDuration(ANIMATIONS.fast)  # 100ms
        self._hover_anim.setStartValue(self._scale_factor)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.finished.connect(self._on_hover_out_finished)
        self._hover_anim.start()

    def _on_hover_out_finished(self) -> None:
        """Release hover out animation and reset margins."""
        if self._hover_anim is not None:
            AnimationPool.release(self._hover_anim, "scale")
            self._hover_anim = None
        self.setContentsMargins(0, 0, 0, 0)

    def _animate_press(self) -> None:
        """Animate scale down on press."""
        if AccessibilitySettings.prefers_reduced_motion():
            return

        self._stop_current_animations()

        self._press_anim = AnimationPool.acquire("scale")
        self._press_anim.setTargetObject(self)
        self._press_anim.setPropertyName(b"scaleFactor")
        self._press_anim.setDuration(ANIMATIONS.instant)  # 50ms
        self._press_anim.setStartValue(self._scale_factor)
        self._press_anim.setEndValue(0.98)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._press_anim.finished.connect(self._on_press_finished)
        self._press_anim.start()

    def _on_press_finished(self) -> None:
        """Release press animation."""
        if self._press_anim is not None:
            AnimationPool.release(self._press_anim, "scale")
            self._press_anim = None

    def _animate_release(self) -> None:
        """Animate bounce back on release."""
        if AccessibilitySettings.prefers_reduced_motion():
            self._scale_factor = 1.0
            self.setContentsMargins(0, 0, 0, 0)
            return

        self._stop_current_animations()

        # Determine target scale based on hover state
        target_scale = 1.02 if self._is_hovered else 1.0

        self._press_anim = AnimationPool.acquire("scale")
        self._press_anim.setTargetObject(self)
        self._press_anim.setPropertyName(b"scaleFactor")
        self._press_anim.setDuration(ANIMATIONS.fast)  # 100ms
        self._press_anim.setStartValue(self._scale_factor)
        self._press_anim.setEndValue(target_scale)
        # OutBack gives a nice bounce effect
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._press_anim.finished.connect(self._on_release_finished)
        self._press_anim.start()

    def _on_release_finished(self) -> None:
        """Release release animation and reset margins if needed."""
        if self._press_anim is not None:
            AnimationPool.release(self._press_anim, "scale")
            self._press_anim = None

        if not self._is_hovered:
            self.setContentsMargins(0, 0, 0, 0)


class AnimatedIconButton(AnimatedButton):
    """
    Animated button optimized for icon-only display.

    Same animation behavior as AnimatedButton but with
    icon-specific sizing defaults.
    """

    def __init__(
        self,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the animated icon button.

        Args:
            icon: Button icon.
            parent: Parent widget.
        """
        super().__init__("", parent)

        if icon is not None:
            self.setIcon(icon)

        # Icon button defaults
        self.setFixedSize(32, 32)
        self.setIconSize(QSize(20, 20))


def create_animated_button(
    text: str = "",
    icon: Optional[QIcon] = None,
    variant: str = "default",
    size: str = "md",
    parent: Optional[QWidget] = None,
) -> AnimatedButton:
    """
    Factory function to create an animated button with theme styling.

    Args:
        text: Button text.
        icon: Optional button icon.
        variant: Style variant ("default", "primary", "danger").
        size: Button size ("sm", "md", "lg").
        parent: Parent widget.

    Returns:
        Configured AnimatedButton instance.

    Example:
        save_btn = create_animated_button("Save", variant="primary")
        cancel_btn = create_animated_button("Cancel")
        delete_btn = create_animated_button("Delete", variant="danger")
    """
    button = AnimatedButton(text, parent)

    if icon is not None:
        button.setIcon(icon)

    # Apply theme styling
    button.setStyleSheet(Theme.button_style(size=size, variant=variant))

    return button
