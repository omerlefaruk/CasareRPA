"""
Tests for utils/hotkey_settings.py - Hotkey configuration module.
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestDefaultHotkeys:
    """Test default hotkey configuration."""

    def test_default_hotkeys_defined(self):
        """Test that DEFAULT_HOTKEYS contains expected actions."""
        from casare_rpa.utils.hotkey_settings import DEFAULT_HOTKEYS

        expected_actions = [
            "new", "open", "save", "save_as", "exit",
            "undo", "redo", "cut", "copy", "paste", "delete",
            "select_all", "deselect_all",
            "zoom_in", "zoom_out", "zoom_reset", "fit_view",
            "run", "stop", "hotkey_manager"
        ]

        for action in expected_actions:
            assert action in DEFAULT_HOTKEYS, f"Missing default hotkey for: {action}"

    def test_default_hotkeys_are_lists(self):
        """Test that all default hotkey values are lists."""
        from casare_rpa.utils.hotkey_settings import DEFAULT_HOTKEYS

        for action, shortcuts in DEFAULT_HOTKEYS.items():
            assert isinstance(shortcuts, list), f"Hotkey for {action} should be a list"
            for shortcut in shortcuts:
                assert isinstance(shortcut, str), f"Shortcut should be a string"

    def test_common_shortcuts_correct(self):
        """Test that common shortcuts are correctly defined."""
        from casare_rpa.utils.hotkey_settings import DEFAULT_HOTKEYS

        assert "Ctrl+S" in DEFAULT_HOTKEYS["save"]
        assert "Ctrl+O" in DEFAULT_HOTKEYS["open"]
        assert "Ctrl+N" in DEFAULT_HOTKEYS["new"]
        assert "Ctrl+Z" in DEFAULT_HOTKEYS["undo"]
        assert "Ctrl+C" in DEFAULT_HOTKEYS["copy"]
        assert "Ctrl+V" in DEFAULT_HOTKEYS["paste"]


class TestHotkeySettings:
    """Test HotkeySettings class."""

    @pytest.fixture
    def temp_settings_file(self, tmp_path):
        """Create a temporary settings file path."""
        return tmp_path / "test_hotkeys.json"

    @pytest.fixture
    def settings_instance(self, temp_settings_file):
        """Create a HotkeySettings instance with a temp file."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings
        return HotkeySettings(temp_settings_file)

    def test_init_with_no_file(self, temp_settings_file):
        """Test initialization when no settings file exists."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings, DEFAULT_HOTKEYS

        assert not temp_settings_file.exists()
        settings = HotkeySettings(temp_settings_file)

        # Should use defaults
        assert settings.get_all_hotkeys() == DEFAULT_HOTKEYS

    def test_init_with_existing_file(self, temp_settings_file):
        """Test initialization with an existing settings file."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings

        # Create a custom settings file
        custom_hotkeys = {"custom_action": ["Ctrl+X"]}
        temp_settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_file, 'w') as f:
            json.dump(custom_hotkeys, f)

        settings = HotkeySettings(temp_settings_file)

        # Should load custom settings
        assert settings.get_all_hotkeys() == custom_hotkeys

    def test_init_with_corrupt_file(self, temp_settings_file):
        """Test initialization with a corrupt settings file."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings, DEFAULT_HOTKEYS

        # Create a corrupt file
        temp_settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_settings_file, 'w') as f:
            f.write("not valid json {{{")

        settings = HotkeySettings(temp_settings_file)

        # Should fall back to defaults
        assert settings.get_all_hotkeys() == DEFAULT_HOTKEYS

    def test_get_shortcuts(self, settings_instance):
        """Test getting shortcuts for an action."""
        # Get existing shortcuts
        shortcuts = settings_instance.get_shortcuts("save")
        assert "Ctrl+S" in shortcuts

        # Get non-existent action
        shortcuts = settings_instance.get_shortcuts("nonexistent")
        assert shortcuts == []

    def test_set_shortcuts(self, settings_instance):
        """Test setting shortcuts for an action."""
        new_shortcuts = ["Alt+S", "F5"]
        settings_instance.set_shortcuts("custom_action", new_shortcuts)

        assert settings_instance.get_shortcuts("custom_action") == new_shortcuts

    def test_set_empty_shortcuts_removes_action(self, settings_instance):
        """Test that setting empty shortcuts removes the action."""
        settings_instance.set_shortcuts("save", ["Ctrl+S"])
        assert "save" in settings_instance.get_all_hotkeys()

        settings_instance.set_shortcuts("save", [])
        assert "save" not in settings_instance.get_all_hotkeys()

    def test_save_and_load(self, temp_settings_file):
        """Test saving and loading settings."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings

        # Create and modify settings
        settings1 = HotkeySettings(temp_settings_file)
        settings1.set_shortcuts("custom_action", ["Ctrl+K"])
        settings1.save()

        # Load in new instance
        settings2 = HotkeySettings(temp_settings_file)
        assert settings2.get_shortcuts("custom_action") == ["Ctrl+K"]

    def test_reset_to_defaults(self, settings_instance):
        """Test resetting hotkeys to defaults."""
        from casare_rpa.utils.hotkey_settings import DEFAULT_HOTKEYS

        # Modify settings
        settings_instance.set_shortcuts("custom_action", ["Ctrl+K"])

        # Reset
        settings_instance.reset_to_defaults()

        # Should be back to defaults
        assert settings_instance.get_all_hotkeys() == DEFAULT_HOTKEYS
        assert settings_instance.get_shortcuts("custom_action") == []

    def test_get_all_hotkeys_returns_copy(self, settings_instance):
        """Test that get_all_hotkeys returns a copy."""
        hotkeys = settings_instance.get_all_hotkeys()
        hotkeys["modified"] = ["test"]

        # Original should be unchanged
        assert "modified" not in settings_instance.get_all_hotkeys()


class TestGlobalHotkeySettings:
    """Test global hotkey settings accessor."""

    def test_get_hotkey_settings_returns_instance(self):
        """Test that get_hotkey_settings returns a HotkeySettings instance."""
        from casare_rpa.utils.hotkey_settings import get_hotkey_settings, HotkeySettings

        settings = get_hotkey_settings()
        assert isinstance(settings, HotkeySettings)

    def test_get_hotkey_settings_is_singleton(self):
        """Test that get_hotkey_settings returns the same instance."""
        from casare_rpa.utils.hotkey_settings import get_hotkey_settings

        settings1 = get_hotkey_settings()
        settings2 = get_hotkey_settings()

        assert settings1 is settings2
