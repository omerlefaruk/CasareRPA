"""
Tests for PreferencesController.

Tests preferences and settings management including:
- Settings get/set
- Theme management
- Hotkey configuration
- Event publishing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QObject

from casare_rpa.presentation.canvas.controllers.preferences_controller import (
    PreferencesController,
)
from casare_rpa.presentation.canvas.events.event_types import EventType


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QObject()
    return main_window


@pytest.fixture
def mock_settings_manager():
    """Create a mock settings manager."""
    manager = Mock()
    manager.get = Mock(return_value=None)
    manager.set = Mock()
    manager.is_autosave_enabled = Mock(return_value=True)
    manager.get_autosave_interval = Mock(return_value=5)
    return manager


@pytest.fixture
def preferences_controller(mock_main_window, mock_settings_manager):
    """Create a PreferencesController instance."""
    with patch(
        "casare_rpa.utils.settings_manager.get_settings_manager",
        return_value=mock_settings_manager,
    ):
        controller = PreferencesController(mock_main_window)
        controller.initialize()
        yield controller
        controller.cleanup()


class TestPreferencesControllerInitialization:
    """Test controller initialization and cleanup."""

    def test_initialization(self, preferences_controller):
        """Test controller initializes correctly."""
        assert preferences_controller.is_initialized
        assert preferences_controller._settings_manager is not None

    def test_cleanup(self, preferences_controller):
        """Test controller cleanup."""
        preferences_controller.cleanup()
        assert not preferences_controller.is_initialized


class TestSettingsManagement:
    """Test settings get/set operations."""

    def test_get_settings_manager(self, preferences_controller, mock_settings_manager):
        """Test getting settings manager instance."""
        assert preferences_controller.get_settings_manager() == mock_settings_manager

    def test_get_setting_success(self, preferences_controller, mock_settings_manager):
        """Test getting a setting value."""
        mock_settings_manager.get.return_value = "test_value"

        result = preferences_controller.get_setting("test_key")

        assert result == "test_value"
        mock_settings_manager.get.assert_called_once_with("test_key", None)

    def test_get_setting_with_default(
        self, preferences_controller, mock_settings_manager
    ):
        """Test getting a setting with default value."""
        mock_settings_manager.get.return_value = None

        result = preferences_controller.get_setting("test_key", "default")

        assert result is None
        mock_settings_manager.get.assert_called_once_with("test_key", "default")

    def test_get_setting_when_not_initialized(self, mock_main_window):
        """Test getting setting when manager not initialized."""
        controller = PreferencesController(mock_main_window)
        # Don't call initialize()

        result = controller.get_setting("test_key", "default")

        assert result == "default"

    def test_set_setting_success(self, preferences_controller, mock_settings_manager):
        """Test setting a setting value."""
        result = preferences_controller.set_setting("test_key", "test_value")

        assert result is True
        mock_settings_manager.set.assert_called_once_with("test_key", "test_value")

    def test_set_setting_emits_signal(self, preferences_controller):
        """Test set setting emits signal."""
        signal_received = []

        def on_changed(key, value):
            signal_received.append((key, value))

        preferences_controller.setting_changed.connect(on_changed)

        preferences_controller.set_setting("test_key", "test_value")

        assert signal_received == [("test_key", "test_value")]

    def test_set_setting_publishes_event(self, preferences_controller):
        """Test set setting publishes event."""
        with patch.object(preferences_controller._event_bus, "publish") as mock_publish:
            preferences_controller.set_setting("test_key", "test_value")

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.PREFERENCES_UPDATED
            assert event.data["key"] == "test_key"
            assert event.data["value"] == "test_value"

    def test_set_setting_when_not_initialized(self, mock_main_window):
        """Test setting when manager not initialized."""
        controller = PreferencesController(mock_main_window)
        # Don't call initialize()

        result = controller.set_setting("test_key", "test_value")

        assert result is False


class TestPreferencesOperations:
    """Test preferences save/reset operations."""

    def test_save_preferences_success(self, preferences_controller):
        """Test saving preferences successfully."""
        signal_received = []

        def on_updated():
            signal_received.append(True)

        preferences_controller.preferences_updated.connect(on_updated)

        result = preferences_controller.save_preferences()

        assert result is True
        assert signal_received == [True]

    def test_save_preferences_publishes_event(self, preferences_controller):
        """Test save preferences publishes event."""
        with patch.object(preferences_controller._event_bus, "publish") as mock_publish:
            preferences_controller.save_preferences()

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.PREFERENCES_UPDATED
            assert event.data["action"] == "saved"

    def test_reset_preferences_success(self, preferences_controller):
        """Test resetting preferences successfully."""
        signal_received = []

        def on_updated():
            signal_received.append(True)

        preferences_controller.preferences_updated.connect(on_updated)

        result = preferences_controller.reset_preferences()

        assert result is True
        assert signal_received == [True]

    def test_reset_preferences_publishes_event(self, preferences_controller):
        """Test reset preferences publishes event."""
        with patch.object(preferences_controller._event_bus, "publish") as mock_publish:
            preferences_controller.reset_preferences()

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.PREFERENCES_UPDATED
            assert event.data["action"] == "reset"


class TestThemeManagement:
    """Test theme management."""

    def test_set_theme_success(self, preferences_controller):
        """Test setting theme successfully."""
        signal_received = []

        def on_changed(theme_name):
            signal_received.append(theme_name)

        preferences_controller.theme_changed.connect(on_changed)

        result = preferences_controller.set_theme("dark")

        assert result is True
        assert signal_received == ["dark"]

    def test_set_theme_publishes_event(self, preferences_controller):
        """Test set theme publishes event."""
        with patch.object(preferences_controller._event_bus, "publish") as mock_publish:
            preferences_controller.set_theme("dark")

            # Verify theme changed event was published
            events_published = [call[0][0] for call in mock_publish.call_args_list]
            event_types = [e.type for e in events_published]

            assert EventType.THEME_CHANGED in event_types
            # Find the theme changed event
            theme_event = next(
                e for e in events_published if e.type == EventType.THEME_CHANGED
            )
            assert theme_event.data["theme_name"] == "dark"


class TestHotkeyManagement:
    """Test hotkey management."""

    def test_update_hotkey_success(self, preferences_controller, mock_settings_manager):
        """Test updating a hotkey successfully."""
        mock_settings_manager.get.return_value = {}
        signal_received = []

        def on_updated(action, hotkey):
            signal_received.append((action, hotkey))

        preferences_controller.hotkey_updated.connect(on_updated)

        result = preferences_controller.update_hotkey("save", "Ctrl+S")

        assert result is True
        assert signal_received == [("save", "Ctrl+S")]

    def test_get_hotkeys(self, preferences_controller, mock_settings_manager):
        """Test getting all hotkeys."""
        mock_settings_manager.get.return_value = {"save": "Ctrl+S"}

        result = preferences_controller.get_hotkeys()

        assert result == {"save": "Ctrl+S"}


class TestAutosaveSettings:
    """Test autosave-related settings."""

    def test_is_autosave_enabled_true(
        self, preferences_controller, mock_settings_manager
    ):
        """Test checking if autosave is enabled."""
        mock_settings_manager.is_autosave_enabled.return_value = True

        assert preferences_controller.is_autosave_enabled() is True

    def test_is_autosave_enabled_false(
        self, preferences_controller, mock_settings_manager
    ):
        """Test checking if autosave is disabled."""
        mock_settings_manager.is_autosave_enabled.return_value = False

        assert preferences_controller.is_autosave_enabled() is False

    def test_is_autosave_enabled_when_not_initialized(self, mock_main_window):
        """Test checking autosave when manager not initialized."""
        controller = PreferencesController(mock_main_window)
        # Don't call initialize()

        assert controller.is_autosave_enabled() is False

    def test_get_autosave_interval(self, preferences_controller, mock_settings_manager):
        """Test getting autosave interval."""
        mock_settings_manager.get_autosave_interval.return_value = 10

        result = preferences_controller.get_autosave_interval()

        assert result == 10

    def test_get_autosave_interval_when_not_initialized(self, mock_main_window):
        """Test getting autosave interval when manager not initialized."""
        controller = PreferencesController(mock_main_window)
        # Don't call initialize()

        result = controller.get_autosave_interval()

        assert result == 5  # Default


class TestEventHandlers:
    """Test event handlers."""

    def test_preferences_updated_event_handler(self, preferences_controller):
        """Test preferences updated event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(
            type=EventType.PREFERENCES_UPDATED, source="Test", data={"key": "test"}
        )

        # Should not raise exception
        preferences_controller._on_preferences_updated_event(event)

    def test_theme_changed_event_handler(self, preferences_controller):
        """Test theme changed event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(
            type=EventType.THEME_CHANGED, source="Test", data={"theme_name": "dark"}
        )

        # Should not raise exception
        preferences_controller._on_theme_changed_event(event)


class TestErrorHandling:
    """Test error handling."""

    def test_get_setting_with_exception(
        self, preferences_controller, mock_settings_manager
    ):
        """Test getting setting with exception."""
        mock_settings_manager.get.side_effect = Exception("Test error")

        result = preferences_controller.get_setting("test_key", "default")

        assert result == "default"

    def test_set_setting_with_exception(
        self, preferences_controller, mock_settings_manager
    ):
        """Test setting setting with exception."""
        mock_settings_manager.set.side_effect = Exception("Test error")

        result = preferences_controller.set_setting("test_key", "value")

        assert result is False

    def test_is_autosave_enabled_with_exception(
        self, preferences_controller, mock_settings_manager
    ):
        """Test checking autosave with exception."""
        mock_settings_manager.is_autosave_enabled.side_effect = Exception("Test error")

        result = preferences_controller.is_autosave_enabled()

        assert result is False
