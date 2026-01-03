"""
Shared pytest fixtures for Expression Editor tests.

Provides Qt application fixtures and common mocks for testing
expression editor components without full Qt integration.
"""

from unittest.mock import MagicMock, patch

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


@pytest.fixture
def mock_document():
    """Create a mock QTextDocument for highlighter tests."""
    mock = MagicMock()
    mock.defaultFont.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_theme():
    """
    Mock the Theme class to avoid actual theme loading.

    Returns a mock theme colors object that provides necessary color values.
    """
    mock_colors = MagicMock()
    mock_colors.background = "#1e1e1e"
    mock_colors.background_alt = "#252526"
    mock_colors.surface = "#2d2d30"
    mock_colors.surface_hover = "#3e3e42"
    mock_colors.header = "#323232"
    mock_colors.text_primary = "#e0e0e0"
    mock_colors.text_secondary = "#9d9d9d"
    mock_colors.border = "#454545"
    mock_colors.border_light = "#555555"
    mock_colors.border_dark = "#333333"
    mock_colors.border_focus = "#007acc"
    mock_colors.accent = "#0e639c"
    mock_colors.accent_hover = "#1177bb"
    mock_colors.secondary_hover = "#4a4a4a"
    mock_colors.selection = "#264f78"
    mock_colors.error = "#f14c4c"
    mock_colors.warning = "#cca700"
    mock_colors.info = "#3794ff"

    with patch(
        "casare_rpa.presentation.canvas.ui.theme.Theme.get_colors",
        return_value=mock_colors,
    ):
        yield mock_colors


@pytest.fixture
def mock_variable_provider():
    """
    Mock the VariableProvider singleton for autocomplete tests.

    Returns a provider that returns test variables.
    """
    from unittest.mock import MagicMock

    mock_provider = MagicMock()
    mock_provider.get_all_variables.return_value = []

    with patch(
        "casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets.variable_autocomplete.VariableProvider.get_instance",
        return_value=mock_provider,
    ):
        yield mock_provider


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
