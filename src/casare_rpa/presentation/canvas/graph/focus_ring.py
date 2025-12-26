"""
Focus ring visualization for keyboard navigation.

Provides a visual indicator around the currently focused node
during keyboard navigation, distinct from the selection highlight.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsItem,
    QGraphicsRectItem,
    QStyleOptionGraphicsItem,
    QWidget,
)
from casare_rpa.presentation.canvas.ui.theme import Theme

if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsScene


class FocusRing(QGraphicsRectItem):
    """
    Animated focus ring around keyboard-navigated nodes.

    Features:
    - Distinct from selection (uses cyan/teal color)
    - Pulsing glow animation
    - Auto-positions around target node
    - High contrast for accessibility
    """

    # Focus ring colors (distinct from selection gold)
    RING_COLOR = Theme.get_colors().info  # Cyan-400
    RING_COLOR_HIGH_CONTRAST = Theme.get_colors().text_primary  # White for high contrast

    RING_WIDTH = 3
    RING_PADDING = 6
    CORNER_RADIUS = 8

    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize focus ring.

        Args:
            parent: Optional parent graphics item
        """
        super().__init__(parent)

        self._target_item: QGraphicsItem | None = None
        self._glow_opacity: float = 1.0
        self._pulse_animation: QPropertyAnimation | None = None
        self._high_contrast: bool = False

        # Setup appearance
        self.setPen(Qt.PenStyle.NoPen)
        self.setBrush(Qt.BrushStyle.NoBrush)
        self.setZValue(10000)  # Above nodes but below popups

        # Setup glow effect
        self._setup_glow_effect()

        # Initially hidden
        self.hide()

    def _setup_glow_effect(self) -> None:
        """Configure the drop shadow glow effect."""
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        glow.setColor(self.RING_COLOR)
        self.setGraphicsEffect(glow)

    def set_high_contrast(self, enabled: bool) -> None:
        """
        Enable or disable high contrast mode.

        Args:
            enabled: True for high contrast (white ring)
        """
        self._high_contrast = enabled
        color = self.RING_COLOR_HIGH_CONTRAST if enabled else self.RING_COLOR

        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setColor(color)
            if enabled:
                effect.setBlurRadius(25)
            else:
                effect.setBlurRadius(20)

        self.update()

    def attach_to(self, item: QGraphicsItem) -> None:
        """
        Attach focus ring to a graphics item.

        Args:
            item: Target item to surround
        """
        if item == self._target_item:
            return

        self._target_item = item

        if item is None:
            self.hide()
            self._stop_pulse()
            return

        # Position around target
        self._update_position()
        self.show()
        self._start_pulse()

    def detach(self) -> None:
        """Remove focus ring from current target."""
        self._target_item = None
        self.hide()
        self._stop_pulse()

    def _update_position(self) -> None:
        """Update ring position to surround target item."""
        if not self._target_item:
            return

        try:
            # Get target bounding rect in scene coordinates
            target_rect = self._target_item.sceneBoundingRect()

            # Expand by padding
            expanded = target_rect.adjusted(
                -self.RING_PADDING,
                -self.RING_PADDING,
                self.RING_PADDING,
                self.RING_PADDING,
            )

            self.setRect(expanded)
        except Exception:
            pass

    def _start_pulse(self) -> None:
        """Start the pulsing glow animation."""
        if self._pulse_animation:
            self._pulse_animation.stop()

        # Create property animation for glow opacity
        self._pulse_animation = QPropertyAnimation(self, b"glowOpacity")
        self._pulse_animation.setDuration(1500)
        self._pulse_animation.setStartValue(0.6)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        self._pulse_animation.start()

    def _stop_pulse(self) -> None:
        """Stop the pulsing animation."""
        if self._pulse_animation:
            self._pulse_animation.stop()
            self._pulse_animation = None

    def _get_glow_opacity(self) -> float:
        """Property getter for animation."""
        return self._glow_opacity

    def _set_glow_opacity(self, value: float) -> None:
        """Property setter for animation."""
        self._glow_opacity = value

        # Update glow effect
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            color = self.RING_COLOR_HIGH_CONTRAST if self._high_contrast else self.RING_COLOR
            color.setAlphaF(value)
            effect.setColor(color)

        self.update()

    # Qt property for animation
    glowOpacity = Property(float, _get_glow_opacity, _set_glow_opacity)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """
        Paint the focus ring.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Target widget
        """
        if not self._target_item:
            return

        # Update position in case target moved
        self._update_position()

        rect = self.rect()
        if rect.isEmpty():
            return

        # Choose color based on contrast mode
        color = self.RING_COLOR_HIGH_CONTRAST if self._high_contrast else self.RING_COLOR
        color = QColor(color)
        color.setAlphaF(self._glow_opacity)

        # Draw rounded rect ring
        pen = QPen(color, self.RING_WIDTH)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)


class FocusRingManager:
    """
    Manager for focus ring lifecycle in a graphics scene.

    Handles:
    - Creating/removing focus ring from scene
    - Tracking focused node
    - Accessibility features
    """

    def __init__(self, scene: "QGraphicsScene") -> None:
        """
        Initialize focus ring manager.

        Args:
            scene: Graphics scene to manage focus ring in
        """
        self._scene = scene
        self._focus_ring: FocusRing | None = None
        self._current_node_item: QGraphicsItem | None = None

    def show_focus(self, node_item: QGraphicsItem) -> None:
        """
        Show focus ring around a node.

        Args:
            node_item: Node graphics item to focus
        """
        if self._focus_ring is None:
            self._focus_ring = FocusRing()
            self._scene.addItem(self._focus_ring)

        self._current_node_item = node_item
        self._focus_ring.attach_to(node_item)

    def hide_focus(self) -> None:
        """Hide the focus ring."""
        if self._focus_ring:
            self._focus_ring.detach()
        self._current_node_item = None

    def remove(self) -> None:
        """Remove focus ring from scene entirely."""
        if self._focus_ring:
            self._focus_ring.detach()
            if self._focus_ring.scene():
                self._scene.removeItem(self._focus_ring)
            self._focus_ring = None
        self._current_node_item = None

    def set_high_contrast(self, enabled: bool) -> None:
        """
        Set high contrast mode for accessibility.

        Args:
            enabled: True for high contrast
        """
        if self._focus_ring:
            self._focus_ring.set_high_contrast(enabled)

    @property
    def current_node_item(self) -> QGraphicsItem | None:
        """Get the currently focused node item."""
        return self._current_node_item

    @property
    def is_visible(self) -> bool:
        """Check if focus ring is currently visible."""
        return self._focus_ring is not None and self._focus_ring.isVisible()
