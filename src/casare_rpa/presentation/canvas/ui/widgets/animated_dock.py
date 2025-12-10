"""
Animated dock widget for smooth panel transitions.

Provides slide-in/slide-out animations for dock panels.

Usage:
    class MyPanel(AnimatedDockWidget):
        def __init__(self, parent=None):
            super().__init__("My Panel", parent)
            # Setup panel UI...
"""

from typing import Callable, Optional

from loguru import logger
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS


class AnimatedDockWidget(QDockWidget):
    """
    Dock widget with slide animations.

    Automatically slides in from the appropriate edge when shown,
    based on which dock area the widget is placed in.

    Respects OS-level reduced motion accessibility settings.
    """

    def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
        """
        Initialize animated dock widget.

        Args:
            title: Dock widget title displayed in title bar.
            parent: Parent widget, typically QMainWindow.
        """
        super().__init__(title, parent)
        self._slide_animation: Optional[QPropertyAnimation] = None
        self._original_pos: Optional[QPoint] = None
        self._is_animating: bool = False

    def showEvent(self, event) -> None:
        """Animate slide in when shown."""
        super().showEvent(event)
        if (
            not self._is_animating
            and not AccessibilitySettings.prefers_reduced_motion()
        ):
            self._animate_slide_in()

    def _animate_slide_in(self) -> None:
        """Slide in from appropriate edge based on dock area."""
        main_window = self._get_main_window()
        if not main_window:
            return

        area = main_window.dockWidgetArea(self)
        if area == Qt.DockWidgetArea.NoDockWidgetArea:
            return

        # Store target position
        target_pos = self.pos()
        self._original_pos = target_pos

        # Calculate start position (off-screen)
        start_pos = self._calculate_offscreen_pos(area, target_pos, slide_out=False)
        if start_pos == target_pos:
            return

        # Set start position
        self.move(start_pos)

        # Animate to target
        self._start_slide_animation(start_pos, target_pos, ANIMATIONS.medium)

    def _calculate_offscreen_pos(
        self, area: Qt.DockWidgetArea, current_pos: QPoint, slide_out: bool
    ) -> QPoint:
        """
        Calculate off-screen position based on dock area.

        Args:
            area: The dock widget area (Left, Right, Top, Bottom).
            current_pos: Current position of the dock widget.
            slide_out: If True, calculate where to slide to (exit).
                       If False, calculate where to slide from (enter).

        Returns:
            Off-screen QPoint position.
        """
        width = self.width()
        height = self.height()

        if area == Qt.DockWidgetArea.LeftDockWidgetArea:
            return QPoint(current_pos.x() - width, current_pos.y())
        elif area == Qt.DockWidgetArea.RightDockWidgetArea:
            return QPoint(current_pos.x() + width, current_pos.y())
        elif area == Qt.DockWidgetArea.BottomDockWidgetArea:
            return QPoint(current_pos.x(), current_pos.y() + height)
        elif area == Qt.DockWidgetArea.TopDockWidgetArea:
            return QPoint(current_pos.x(), current_pos.y() - height)

        return current_pos

    def _start_slide_animation(
        self,
        start_pos: QPoint,
        end_pos: QPoint,
        duration: int,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Start slide animation between two positions.

        Args:
            start_pos: Starting position.
            end_pos: Ending position.
            duration: Animation duration in milliseconds.
            on_finished: Optional callback when animation completes.
        """
        # Stop any existing animation
        if self._slide_animation is not None:
            self._slide_animation.stop()
            self._slide_animation.deleteLater()

        self._is_animating = True

        self._slide_animation = QPropertyAnimation(self, b"pos")
        self._slide_animation.setDuration(duration)
        self._slide_animation.setStartValue(start_pos)
        self._slide_animation.setEndValue(end_pos)
        self._slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        def finish() -> None:
            self._is_animating = False
            if on_finished:
                on_finished()

        self._slide_animation.finished.connect(finish)
        self._slide_animation.start()

    def _get_main_window(self) -> Optional[QMainWindow]:
        """
        Find parent QMainWindow.

        Returns:
            Parent QMainWindow or None if not found.
        """
        parent = self.parent()
        while parent:
            if isinstance(parent, QMainWindow):
                return parent
            parent = parent.parent()
        return None

    def animate_hide(self, on_complete: Optional[Callable[[], None]] = None) -> None:
        """
        Slide out then hide the dock widget.

        Use this instead of hide() for animated exit.

        Args:
            on_complete: Optional callback after hide completes.
        """
        if AccessibilitySettings.prefers_reduced_motion():
            self.hide()
            if on_complete:
                on_complete()
            return

        main_window = self._get_main_window()
        if not main_window:
            self.hide()
            if on_complete:
                on_complete()
            return

        area = main_window.dockWidgetArea(self)
        if area == Qt.DockWidgetArea.NoDockWidgetArea:
            self.hide()
            if on_complete:
                on_complete()
            return

        start_pos = self.pos()
        end_pos = self._calculate_offscreen_pos(area, start_pos, slide_out=True)

        def finish() -> None:
            self.hide()
            self.move(start_pos)  # Reset position for next show
            if on_complete:
                on_complete()

        # Use InCubic for exit (accelerate out)
        if self._slide_animation is not None:
            self._slide_animation.stop()
            self._slide_animation.deleteLater()

        self._is_animating = True

        self._slide_animation = QPropertyAnimation(self, b"pos")
        self._slide_animation.setDuration(ANIMATIONS.normal)
        self._slide_animation.setStartValue(start_pos)
        self._slide_animation.setEndValue(end_pos)
        self._slide_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        def on_finish() -> None:
            self._is_animating = False
            finish()

        self._slide_animation.finished.connect(on_finish)
        self._slide_animation.start()

    def is_animating(self) -> bool:
        """
        Check if animation is currently running.

        Returns:
            True if slide animation is in progress.
        """
        return self._is_animating
