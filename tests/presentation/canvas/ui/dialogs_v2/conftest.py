"""
Test fixtures for dialogs_v2 tests.

Provides:
- qapp: QApplication instance (singleton)
- signal_capture: Context manager for capturing signal emissions
- qtbot_like: Helper for widget testing without pytest-qt dependency
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# QApplication FIXTURE
# =============================================================================


def qapp() -> QApplication:
    """
    Get or create QApplication instance.

    Returns:
        Singleton QApplication instance
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# =============================================================================
# SIGNAL CAPTURE
# =============================================================================


@contextmanager
def signal_capture(signal) -> Generator[list, None, None]:
    """
    Context manager to capture signal emissions.

    Args:
        signal: Qt Signal to capture

    Yields:
        List of emitted arguments

    Example:
        with signal_capture(dialog.accepted) as captured:
            dialog.accept()
        assert len(captured) == 1
    """
    captured: list = []

    def capture(*args: Any, **kwargs: Any) -> None:
        captured.append(list(args) if args else [])

    signal.connect(capture)
    try:
        yield captured
    finally:
        signal.disconnect(capture)


# =============================================================================
# QTBOT-LIKE HELPER
# =============================================================================


class QtBotLike:
    """
    Helper class for widget testing without pytest-qt.

    Provides methods similar to pytest-qt's qtbot fixture.
    """

    def __init__(self, app: QApplication | None = None) -> None:
        """
        Initialize qtbot-like helper.

        Args:
            app: Optional QApplication instance
        """
        self._app = app or qapp()

    def wait(self, ms: int) -> None:
        """
        Wait for specified milliseconds.

        Args:
            ms: Milliseconds to wait
        """
        from PySide6.QtCore import QElapsedTimer, QEventLoop

        loop = QEventLoop()
        timer = QElapsedTimer()
        timer.start()

        while timer.elapsed() < ms:
            self._app.processEvents()
            if loop.processEvents(
                QEventLoop.ProcessEventsFlag.AllEvents,
                maxDuration=10,
            ):
                break

    def wait_exposed(self, widget, timeout: int = 1000) -> bool:
        """
        Wait until widget is exposed (shown on screen).

        Args:
            widget: Widget to wait for
            timeout: Maximum wait time in milliseconds

        Returns:
            True if widget was exposed, False on timeout
        """
        from PySide6.QtCore import QElapsedTimer

        widget.show()
        timer = QElapsedTimer()
        timer.start()

        while not widget.isVisible() or not widget.testAttribute(
            widget.WidgetAttribute.WA_WState_Visible
        ):
            self._app.processEvents()
            if timer.elapsed() > timeout:
                return False
        return True

    def add_widget(self, widget) -> None:
        """
        Add widget for cleanup (in a real test scenario).

        Args:
            widget: Widget to track
        """
        # In real pytest-qt, this queues widget for deletion
        # Here we just ensure it's shown
        widget.show()

    def mouse_click(self, widget, button: str = "left") -> None:
        """
        Simulate mouse click on widget.

        Args:
            widget: Widget to click
            button: Mouse button ("left" or "right")
        """
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QMouseEvent

        if button == "left":
            qt_button = Qt.MouseButton.LeftButton
        else:
            qt_button = Qt.MouseButton.RightButton

        pos = widget.rect().center()
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            pos,
            qt_button,
            qt_button,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.mousePressEvent(event)

        event_release = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            pos,
            qt_button,
            qt_button,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.mouseReleaseEvent(event_release)

    def key_click(self, widget, key: str) -> None:
        """
        Simulate key press on widget.

        Args:
            widget: Widget to send key to
            key: Key name ("Enter", "Escape", etc.)
        """
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent

        key_map = {
            "Enter": Qt.Key.Key_Return,
            "Return": Qt.Key.Key_Return,
            "Escape": Qt.Key.Key_Escape,
            "Esc": Qt.Key.Key_Escape,
            "Tab": Qt.Key.Key_Tab,
            "Backspace": Qt.Key.Key_Backspace,
            "Space": Qt.Key.Key_Space,
        }

        qt_key = key_map.get(key, Qt.Key.Key_unknown)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            qt_key,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.keyPressEvent(event)


# =============================================================================
# PYTEST FIXTURES (if pytest is available)
# =============================================================================


def pytest_configure(config) -> None:
    """Pytest configuration hook."""
    import sys
    from pathlib import Path

    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "qapp",
    "signal_capture",
    "QtBotLike",
]
