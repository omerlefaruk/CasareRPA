"""
Shared utility functions for v2 popup variants.

Provides:
- Position calculation helpers
- Screen boundary clamping
- Toast stacking manager
- Common styling helpers
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from PySide6.QtCore import QObject, QPoint, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

if TYPE_CHECKING:
    from collections.abc import Callable


# =============================================================================
# Position Helpers
# =============================================================================


def clamp_to_screen(
    pos: QPoint,
    size: tuple[int, int] | None = None,
    margin: int = 0,
) -> QPoint:
    """
    Clamp position to screen boundaries.

    Args:
        pos: Desired position
        size: Optional (width, height) of widget for right/bottom clamping
        margin: Additional margin from screen edge

    Returns:
        Clamped position that stays on screen
    """
    screen = QApplication.primaryScreen().availableGeometry()
    x, y = pos.x(), pos.y()

    # Clamp right and bottom (if size provided)
    if size:
        width, height = size
        if x + width > screen.right() - margin:
            x = screen.right() - width - margin
        if y + height > screen.bottom() - margin:
            y = screen.bottom() - height - margin

    # Clamp left and top
    if x < screen.left() + margin:
        x = screen.left() + margin
    if y < screen.top() + margin:
        y = screen.top() + margin

    return QPoint(x, y)


def position_below_widget(
    widget: QWidget,
    popup_width: int,
    popup_height: int,
    offset: QPoint | None = None,
) -> QPoint:
    """
    Calculate position for popup below a widget.

    Args:
        widget: Anchor widget
        popup_width: Popup width for boundary clamping
        popup_height: Popup height for boundary clamping
        offset: Optional offset from anchor

    Returns:
        Global position for popup
    """
    if offset is None:
        offset = QPoint(0, 0)

    widget_rect = widget.geometry()
    widget_bottom_left = widget.mapToGlobal(widget_rect.bottomLeft())

    pos = widget_bottom_left + offset

    # Check if fits below, if not show above
    screen = QApplication.primaryScreen().availableGeometry()
    if pos.y() + popup_height > screen.bottom():
        widget_top_left = widget.mapToGlobal(widget_rect.topLeft())
        pos = widget_top_left - QPoint(0, popup_height) + offset

    return clamp_to_screen(pos, (popup_width, popup_height))


def position_above_widget(
    widget: QWidget,
    popup_width: int,
    popup_height: int,
    offset: QPoint | None = None,
) -> QPoint:
    """
    Calculate position for popup above a widget.

    Args:
        widget: Anchor widget
        popup_width: Popup width for boundary clamping
        popup_height: Popup height for boundary clamping
        offset: Optional offset from anchor

    Returns:
        Global position for popup
    """
    if offset is None:
        offset = QPoint(0, 0)

    widget_rect = widget.geometry()
    widget_top_left = widget.mapToGlobal(widget_rect.topLeft())

    pos = widget_top_left - QPoint(0, popup_height) + offset

    return clamp_to_screen(pos, (popup_width, popup_height))


def position_right_of_widget(
    widget: QWidget,
    popup_width: int,
    popup_height: int,
    offset: QPoint | None = None,
) -> QPoint:
    """
    Calculate position for popup to the right of a widget.

    Args:
        widget: Anchor widget
        popup_width: Popup width for boundary clamping
        popup_height: Popup height for boundary clamping
        offset: Optional offset from anchor

    Returns:
        Global position for popup
    """
    if offset is None:
        offset = QPoint(0, 0)

    widget_rect = widget.geometry()
    widget_top_right = widget.mapToGlobal(widget_rect.topRight())

    pos = widget_top_right + offset

    # Check if fits to right, if not show to left
    screen = QApplication.primaryScreen().availableGeometry()
    if pos.x() + popup_width > screen.right():
        widget_top_left = widget.mapToGlobal(widget_rect.topLeft())
        pos = widget_top_left - QPoint(popup_width, 0) + offset

    return clamp_to_screen(pos, (popup_width, popup_height))


def position_at_cursor(
    popup_width: int,
    popup_height: int,
    offset: QPoint | None = None,
) -> QPoint:
    """
    Calculate position for popup at cursor.

    Args:
        popup_width: Popup width for boundary clamping
        popup_height: Popup height for boundary clamping
        offset: Optional offset from cursor

    Returns:
        Global position for popup
    """
    if offset is None:
        offset = QPoint(0, TOKENS_V2.spacing.sm)

    pos = QCursor.pos() + offset
    return clamp_to_screen(pos, (popup_width, popup_height))


def get_center_of_screen() -> QPoint:
    """
    Get center point of primary screen.

    Returns:
        Center position of screen
    """
    screen = QApplication.primaryScreen().availableGeometry()
    return QPoint(
        (screen.left() + screen.right()) // 2,
        (screen.top() + screen.bottom()) // 2,
    )


# =============================================================================
# QCursor import (lazy load to avoid issues)
# =============================================================================


def QCursor() -> QObject:
    """Lazy load QCursor."""
    from PySide6.QtGui import QCursor as _QCursor

    return _QCursor()


# =============================================================================
# Toast Stacking Manager
# =============================================================================


class ToastManager(QObject):
    """
    Singleton manager for toast popup stacking.

    Tracks active toasts and calculates vertical offsets
    to prevent overlap. Toasts stack from top-right corner.
    """

    _instance: ToastManager | None = None

    def __init__(self) -> None:
        """Initialize toast manager."""
        super().__init__()
        self._active_toasts: list[QWidget] = []
        self._toast_heights: dict[int, int] = {}

    @classmethod
    def instance(cls) -> ToastManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_toast(self, toast: QWidget, height: int) -> QPoint:
        """
        Register a toast and get its position.

        Args:
            toast: Toast widget
            height: Toast height

        Returns:
            Position for toast (top-right corner, stacked)
        """
        self._active_toasts.append(toast)
        self._toast_heights[id(toast)] = height

        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - TOKENS_V2.spacing.xl
        y = screen.top() + TOKENS_V2.spacing.xl

        # Add offset for existing toasts
        offset = 0
        for existing in self._active_toasts:
            if existing is not toast and existing.isVisible():
                h = self._toast_heights.get(id(existing), 0)
                offset += h + TOKENS_V2.spacing.xs

        return QPoint(x, y) + QPoint(0, offset)

    def unregister_toast(self, toast: QWidget) -> None:
        """
        Unregister a toast.

        Args:
            toast: Toast widget to remove
        """
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
        self._toast_heights.pop(id(toast), None)

    def reposition_toasts(self) -> None:
        """Reposition all active toasts (call after toast closes)."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - TOKENS_V2.spacing.xl
        y = screen.top() + TOKENS_V2.spacing.xl

        for toast in self._active_toasts:
            if not toast.isVisible():
                continue

            toast.move(x, y)
            h = self._toast_heights.get(id(toast), 0)
            y += h + TOKENS_V2.spacing.xs


# =============================================================================
# Styling Helpers
# =============================================================================


def get_scrollbar_style_v2() -> str:
    """
    Get v2 dark theme scrollbar stylesheet.

    Returns:
        QSS string for consistent scrollbars
    """
    return f"""
        QScrollBar:vertical {{
            background-color: {THEME_V2.scrollbar_bg};
            width: {TOKENS_V2.sizes.scrollbar_width}px;
            border: none;
            border-radius: {TOKENS_V2.radius.xs}px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {THEME_V2.scrollbar_handle};
            min-height: {TOKENS_V2.sizes.scrollbar_min_height}px;
            border-radius: {TOKENS_V2.radius.xs}px;
            margin: 1px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {THEME_V2.scrollbar_hover};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {THEME_V2.scrollbar_bg};
            height: {TOKENS_V2.sizes.scrollbar_width}px;
            border: none;
            border-radius: {TOKENS_V2.radius.xs}px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {THEME_V2.scrollbar_handle};
            min-width: {TOKENS_V2.sizes.scrollbar_min_height}px;
            border-radius: {TOKENS_V2.radius.xs}px;
            margin: 1px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {THEME_V2.scrollbar_hover};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """


def get_input_style_v2(
    focused: bool = False,
    error: bool = False,
) -> str:
    """
    Get v2 dark theme input field stylesheet.

    Args:
        focused: Whether input has focus
        error: Whether input has error state

    Returns:
        QSS string for input field
    """
    from casare_rpa.presentation.canvas.theme import THEME_V2

    border_color = (
        THEME_V2.error if error else (THEME_V2.border_focus if focused else THEME_V2.input_border)
    )

    return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {THEME_V2.input_bg};
            border: 1px solid {border_color};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: 0px {TOKENS_V2.spacing.sm}px;
            color: {THEME_V2.text_primary};
            font-size: {TOKENS_V2.typography.body}px;
            selection-background-color: {THEME_V2.bg_selected};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {THEME_V2.border_focus};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {THEME_V2.bg_component};
            color: {THEME_V2.text_disabled};
        }}
        QScrollBar {{ {get_scrollbar_style_v2()} }}
    """


# =============================================================================
# Debounce Helper
# =============================================================================


class Debounce(QObject):
    """
    Simple debounce utility for delaying function calls.

    Useful for search/filter inputs where you want to wait
    for user to stop typing before executing expensive operations.
    """

    def __init__(self, delay_ms: int = 150, parent: QObject | None = None) -> None:
        """
        Initialize debounce.

        Args:
            delay_ms: Delay in milliseconds
            parent: Parent object
        """
        super().__init__(parent)
        self._delay_ms = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._pending_callback: Callable[[], None] | None = None

    def call(self, callback: Callable[[], None]) -> None:
        """
        Schedule callback to run after delay (resets on repeated calls).

        Args:
            callback: Function to call after delay
        """
        self._pending_callback = callback
        self._timer.stop()
        self._timer.timeout.connect(self._execute)
        self._timer.start(self._delay_ms)

    def _execute(self) -> None:
        """Execute pending callback."""
        if self._pending_callback:
            self._pending_callback()
            self._pending_callback = None

    def cancel(self) -> None:
        """Cancel pending callback."""
        self._timer.stop()
        self._pending_callback = None

    @contextmanager
    def immediate(self) -> Generator[None, None, None]:
        """
        Context manager to temporarily disable debouncing.

        Usage:
            with debounce.immediate():
                callback()
        """
        self.cancel()
        yield
        # Reset timer after context exits


__all__ = [
    "Debounce",
    "ToastManager",
    "clamp_to_screen",
    "get_center_of_screen",
    "get_input_style_v2",
    "get_scrollbar_style_v2",
    "position_above_widget",
    "position_at_cursor",
    "position_below_widget",
    "position_right_of_widget",
]

