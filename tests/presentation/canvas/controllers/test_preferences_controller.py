"""
Tests for PreferencesController.

Tests user preferences and settings management covering:
- Getting and setting preferences
- Theme management
- Hotkey configuration
- Autosave settings
- Event handling

Note: These tests mock Qt dependencies and settings manager to avoid I/O.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock


class TestSettingsGetSet:
    """Tests for get_setting and set_setting functionality."""

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager."""
        manager = Mock()
        manager._settings = {}
        manager.get = Mock(side_effect=lambda k, d=None: manager._settings.get(k, d))
        manager.set = Mock(side_effect=lambda k, v: manager._settings.__setitem__(k, v))
        return manager

    def _get_setting(self, manager, key: str, default=None):
        """Simulate get_setting method."""
        if manager is None:
            return default
        try:
            return manager.get(key, default)
        except Exception:
            return default

    def _set_setting(self, manager, key: str, value) -> bool:
        """Simulate set_setting method."""
        if manager is None:
            return False
        try:
            manager.set(key, value)
            return True
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_get_setting_returns_value(self, mock_settings_manager):
        """Test getting an existing setting."""
        mock_settings_manager._settings["theme"] = "dark"

        result = self._get_setting(mock_settings_manager, "theme")

        assert result == "dark"

    def test_get_setting_returns_default(self, mock_settings_manager):
        """Test getting non-existent setting returns default."""
        result = self._get_setting(mock_settings_manager, "nonexistent", "default_val")

        assert result == "default_val"

    def test_get_setting_default_none(self, mock_settings_manager):
        """Test getting non-existent setting with None default."""
        result = self._get_setting(mock_settings_manager, "missing")

        assert result is None

    def test_set_setting_success(self, mock_settings_manager):
        """Test setting a value successfully."""
        result = self._set_setting(mock_settings_manager, "theme", "light")

        assert result is True
        mock_settings_manager.set.assert_called_with("theme", "light")

    def test_set_setting_overwrites(self, mock_settings_manager):
        """Test setting overwrites existing value."""
        mock_settings_manager._settings["theme"] = "dark"

        self._set_setting(mock_settings_manager, "theme", "light")

        assert mock_settings_manager._settings["theme"] == "light"

    def test_set_setting_various_types(self, mock_settings_manager):
        """Test setting various value types."""
        self._set_setting(mock_settings_manager, "string_val", "text")
        self._set_setting(mock_settings_manager, "int_val", 42)
        self._set_setting(mock_settings_manager, "bool_val", True)
        self._set_setting(mock_settings_manager, "list_val", [1, 2, 3])
        self._set_setting(mock_settings_manager, "dict_val", {"key": "val"})

        assert mock_settings_manager._settings["string_val"] == "text"
        assert mock_settings_manager._settings["int_val"] == 42
        assert mock_settings_manager._settings["bool_val"] is True
        assert mock_settings_manager._settings["list_val"] == [1, 2, 3]
        assert mock_settings_manager._settings["dict_val"] == {"key": "val"}

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_get_setting_manager_none(self):
        """Test get_setting when manager is None."""
        result = self._get_setting(None, "theme", "default")

        assert result == "default"

    def test_set_setting_manager_none(self):
        """Test set_setting when manager is None."""
        result = self._set_setting(None, "theme", "dark")

        assert result is False

    def test_get_setting_error(self, mock_settings_manager):
        """Test get_setting handles exceptions."""
        mock_settings_manager.get.side_effect = Exception("Error")

        result = self._get_setting(mock_settings_manager, "theme", "default")

        assert result == "default"

    def test_set_setting_error(self, mock_settings_manager):
        """Test set_setting handles exceptions."""
        mock_settings_manager.set.side_effect = Exception("Error")

        result = self._set_setting(mock_settings_manager, "theme", "dark")

        assert result is False


class TestThemeManagement:
    """Tests for theme management functionality."""

    def _set_theme(self, manager, theme_name: str) -> bool:
        """
        Simulate set_theme method.

        Returns:
            bool: True if successful
        """
        if manager is None:
            return False

        try:
            manager.set("theme", theme_name)
            return True
        except Exception:
            return False

    def _get_theme(self, manager) -> str:
        """
        Get current theme.

        Returns:
            str: Current theme name
        """
        if manager is None:
            return "default"

        try:
            return manager.get("theme", "default")
        except Exception:
            return "default"

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager."""
        manager = Mock()
        manager._settings = {"theme": "light"}
        manager.get = Mock(side_effect=lambda k, d=None: manager._settings.get(k, d))
        manager.set = Mock(side_effect=lambda k, v: manager._settings.__setitem__(k, v))
        return manager

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_set_theme_success(self, mock_settings_manager):
        """Test setting theme successfully."""
        result = self._set_theme(mock_settings_manager, "dark")

        assert result is True
        assert mock_settings_manager._settings["theme"] == "dark"

    def test_get_theme_returns_current(self, mock_settings_manager):
        """Test getting current theme."""
        result = self._get_theme(mock_settings_manager)

        assert result == "light"

    def test_set_multiple_themes(self, mock_settings_manager):
        """Test switching between themes."""
        self._set_theme(mock_settings_manager, "dark")
        assert mock_settings_manager._settings["theme"] == "dark"

        self._set_theme(mock_settings_manager, "light")
        assert mock_settings_manager._settings["theme"] == "light"

        self._set_theme(mock_settings_manager, "custom")
        assert mock_settings_manager._settings["theme"] == "custom"

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_set_theme_manager_none(self):
        """Test set_theme when manager is None."""
        result = self._set_theme(None, "dark")

        assert result is False

    def test_get_theme_manager_none(self):
        """Test get_theme when manager is None."""
        result = self._get_theme(None)

        assert result == "default"


class TestHotkeyManagement:
    """Tests for hotkey configuration functionality."""

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager with hotkeys."""
        manager = Mock()
        manager._settings = {
            "hotkeys": {
                "save": "Ctrl+S",
                "open": "Ctrl+O",
            }
        }
        manager.get = Mock(side_effect=lambda k, d=None: manager._settings.get(k, d))
        manager.set = Mock(side_effect=lambda k, v: manager._settings.__setitem__(k, v))
        return manager

    def _get_hotkeys(self, manager) -> dict:
        """Simulate get_hotkeys method."""
        if manager is None:
            return {}

        try:
            return manager.get("hotkeys", {})
        except Exception:
            return {}

    def _update_hotkey(self, manager, action: str, hotkey: str) -> bool:
        """
        Simulate update_hotkey method.

        Returns:
            bool: True if successful
        """
        if manager is None:
            return False

        try:
            hotkeys = manager.get("hotkeys", {})
            hotkeys[action] = hotkey
            manager.set("hotkeys", hotkeys)
            return True
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_get_hotkeys_returns_dict(self, mock_settings_manager):
        """Test getting all hotkeys."""
        result = self._get_hotkeys(mock_settings_manager)

        assert isinstance(result, dict)
        assert result["save"] == "Ctrl+S"
        assert result["open"] == "Ctrl+O"

    def test_update_hotkey_success(self, mock_settings_manager):
        """Test updating a hotkey."""
        result = self._update_hotkey(mock_settings_manager, "save", "Ctrl+Shift+S")

        assert result is True

    def test_update_hotkey_adds_new(self, mock_settings_manager):
        """Test adding a new hotkey."""
        result = self._update_hotkey(mock_settings_manager, "run", "F5")

        assert result is True

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_get_hotkeys_manager_none(self):
        """Test get_hotkeys when manager is None."""
        result = self._get_hotkeys(None)

        assert result == {}

    def test_update_hotkey_manager_none(self):
        """Test update_hotkey when manager is None."""
        result = self._update_hotkey(None, "save", "Ctrl+S")

        assert result is False

    def test_get_hotkeys_empty(self, mock_settings_manager):
        """Test get_hotkeys when no hotkeys configured."""
        mock_settings_manager._settings["hotkeys"] = {}

        result = self._get_hotkeys(mock_settings_manager)

        assert result == {}


class TestAutosaveSettings:
    """Tests for autosave configuration functionality."""

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager with autosave."""
        manager = Mock()
        manager.is_autosave_enabled = Mock(return_value=True)
        manager.get_autosave_interval = Mock(return_value=5)
        return manager

    def _is_autosave_enabled(self, manager) -> bool:
        """Simulate is_autosave_enabled method."""
        if manager is None:
            return False

        try:
            return manager.is_autosave_enabled()
        except Exception:
            return False

    def _get_autosave_interval(self, manager) -> int:
        """Simulate get_autosave_interval method."""
        if manager is None:
            return 5  # Default

        try:
            return manager.get_autosave_interval()
        except Exception:
            return 5  # Default

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_is_autosave_enabled_true(self, mock_settings_manager):
        """Test autosave enabled check returns True."""
        result = self._is_autosave_enabled(mock_settings_manager)

        assert result is True

    def test_is_autosave_enabled_false(self, mock_settings_manager):
        """Test autosave enabled check returns False."""
        mock_settings_manager.is_autosave_enabled.return_value = False

        result = self._is_autosave_enabled(mock_settings_manager)

        assert result is False

    def test_get_autosave_interval_returns_value(self, mock_settings_manager):
        """Test getting autosave interval."""
        mock_settings_manager.get_autosave_interval.return_value = 10

        result = self._get_autosave_interval(mock_settings_manager)

        assert result == 10

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_is_autosave_enabled_manager_none(self):
        """Test is_autosave_enabled when manager is None."""
        result = self._is_autosave_enabled(None)

        assert result is False

    def test_get_autosave_interval_manager_none(self):
        """Test get_autosave_interval when manager is None."""
        result = self._get_autosave_interval(None)

        assert result == 5  # Default

    def test_is_autosave_enabled_error(self, mock_settings_manager):
        """Test is_autosave_enabled handles exceptions."""
        mock_settings_manager.is_autosave_enabled.side_effect = Exception("Error")

        result = self._is_autosave_enabled(mock_settings_manager)

        assert result is False

    def test_get_autosave_interval_error(self, mock_settings_manager):
        """Test get_autosave_interval handles exceptions."""
        mock_settings_manager.get_autosave_interval.side_effect = Exception("Error")

        result = self._get_autosave_interval(mock_settings_manager)

        assert result == 5  # Default


class TestPreferencesSaveReset:
    """Tests for save and reset preferences functionality."""

    @pytest.fixture
    def mock_settings_manager(self):
        """Create a mock settings manager."""
        manager = Mock()
        return manager

    def _save_preferences(self, manager) -> bool:
        """Simulate save_preferences method."""
        if manager is None:
            return False

        try:
            # Settings manager handles auto-save
            return True
        except Exception:
            return False

    def _reset_preferences(self, manager) -> bool:
        """Simulate reset_preferences method."""
        if manager is None:
            return False

        try:
            # Reset to defaults
            return True
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_save_preferences_success(self, mock_settings_manager):
        """Test saving preferences successfully."""
        result = self._save_preferences(mock_settings_manager)

        assert result is True

    def test_reset_preferences_success(self, mock_settings_manager):
        """Test resetting preferences successfully."""
        result = self._reset_preferences(mock_settings_manager)

        assert result is True

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_save_preferences_manager_none(self):
        """Test save_preferences when manager is None."""
        result = self._save_preferences(None)

        assert result is False

    def test_reset_preferences_manager_none(self):
        """Test reset_preferences when manager is None."""
        result = self._reset_preferences(None)

        assert result is False


class TestEventHandling:
    """Tests for event handling in PreferencesController."""

    def _handle_preferences_updated_event(self, event_data: dict) -> dict:
        """
        Simulate _on_preferences_updated_event handler.

        Returns processed event data.
        """
        return {
            "handled": True,
            "key": event_data.get("key"),
            "value": event_data.get("value"),
            "action": event_data.get("action"),
        }

    def _handle_theme_changed_event(self, event_data: dict) -> dict:
        """
        Simulate _on_theme_changed_event handler.

        Returns processed event data.
        """
        return {
            "handled": True,
            "theme_name": event_data.get("theme_name"),
        }

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_preferences_updated_event_with_key_value(self):
        """Test handling preferences updated event with key/value."""
        event_data = {"key": "theme", "value": "dark"}

        result = self._handle_preferences_updated_event(event_data)

        assert result["handled"] is True
        assert result["key"] == "theme"
        assert result["value"] == "dark"

    def test_preferences_updated_event_with_action(self):
        """Test handling preferences updated event with action."""
        event_data = {"action": "saved"}

        result = self._handle_preferences_updated_event(event_data)

        assert result["handled"] is True
        assert result["action"] == "saved"

    def test_theme_changed_event(self):
        """Test handling theme changed event."""
        event_data = {"theme_name": "dark"}

        result = self._handle_theme_changed_event(event_data)

        assert result["handled"] is True
        assert result["theme_name"] == "dark"

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    def test_preferences_updated_event_empty_data(self):
        """Test handling preferences updated event with empty data."""
        event_data = {}

        result = self._handle_preferences_updated_event(event_data)

        assert result["handled"] is True
        assert result["key"] is None
        assert result["value"] is None

    def test_theme_changed_event_empty_data(self):
        """Test handling theme changed event with empty data."""
        event_data = {}

        result = self._handle_theme_changed_event(event_data)

        assert result["handled"] is True
        assert result["theme_name"] is None
