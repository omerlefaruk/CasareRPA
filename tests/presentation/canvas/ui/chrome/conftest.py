"""
Shared pytest fixtures for Chrome v2 tests.

Provides Qt application fixtures and signal capture helpers for testing
ToolbarV2 and StatusBarV2 components.

Run: pytest tests/presentation/canvas/ui/chrome/ -v
"""

import pytest


@pytest.fixture(scope="session")
def qapp():
    """
    Create or get a QApplication for the entire test session.

    Qt requires exactly one QApplication instance. This fixture ensures
    we reuse the same instance across all tests.
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't clean up - let pytest handle it


@pytest.fixture
def qtbot_like(qapp):
    """
    Simple fixture that provides basic Qt event processing.

    For tests that don't need full pytest-qt functionality,
    this provides minimal event loop processing.
    """

    class QtBotLike:
        def __init__(self, app):
            self._app = app

        def process_events(self):
            """Process pending Qt events."""
            self._app.processEvents()

        def add_widget(self, widget):
            """Register a widget (no-op for cleanup tracking)."""
            pass

    return QtBotLike(qapp)


# =============================================================================
# Signal Capture Helpers
# =============================================================================


class SignalCapture:
    """Helper class to capture Qt signals for testing."""

    def __init__(self):
        self.signals: list = []

    def slot(self, *args):
        """Slot to capture signal emissions."""
        self.signals.append(args)

    @property
    def called(self) -> bool:
        """Check if signal was emitted at least once."""
        return len(self.signals) > 0

    @property
    def call_count(self) -> int:
        """Get number of signal emissions."""
        return len(self.signals)

    @property
    def last_args(self) -> tuple:
        """Get arguments from last signal emission."""
        if self.signals:
            return self.signals[-1]
        return ()

    def clear(self):
        """Clear captured signals."""
        self.signals.clear()


@pytest.fixture
def signal_capture():
    """Provide a SignalCapture instance for signal testing."""
    return SignalCapture()
