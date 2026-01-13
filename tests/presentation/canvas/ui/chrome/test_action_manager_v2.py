"""
Tests for ActionManagerV2 - centralized action/shortcut management.

Epic 1.2: Test coverage for:
- Action registration (64 actions)
- Shortcut persistence (load/save)
- Action lookup and retrieval
- Category-based enable/disable
- Reset to defaults
- Signal emission
- Import/export shortcuts
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMainWindow

from casare_rpa.presentation.canvas.ui.chrome.action_manager_v2 import (
    ActionCategory,
    ActionManagerV2,
    DEFAULT_SHORTCUTS,
    get_action,
    _get_shortcuts_settings_path,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def qapp():
    """Ensure QApplication exists for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def clean_settings():
    """Clean QSettings before and after tests."""
    settings_path = _get_shortcuts_settings_path()
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    settings.beginGroup("shortcuts")
    settings.remove("")
    settings.endGroup()
    yield
    settings.beginGroup("shortcuts")
    settings.remove("")
    settings.endGroup()


@pytest.fixture
def settings_preserve():
    """Clean QSettings only before test, preserve after for testing persistence."""
    settings_path = _get_shortcuts_settings_path()
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    settings.beginGroup("shortcuts")
    settings.remove("")
    settings.endGroup()
    yield
    # Don't clean after - allows testing persistence


class MainWindowLike(QMainWindow):
    """Minimal IMainWindow implementation for testing."""

    workflow_new = Signal()
    workflow_open = Signal(str)
    workflow_save = Signal()
    workflow_save_as = Signal(str)
    workflow_import = Signal(str)
    workflow_import_json = Signal(str)
    workflow_export_selected = Signal(str)
    workflow_run = Signal()
    workflow_run_all = Signal()
    workflow_run_to_node = Signal(str)
    workflow_run_single_node = Signal(str)
    workflow_pause = Signal()
    workflow_resume = Signal()
    workflow_stop = Signal()
    preferences_saved = Signal()
    trigger_workflow_requested = Signal()


@pytest.fixture
def real_main_window(qapp) -> MainWindowLike:
    """Create real QMainWindow implementing IMainWindow."""
    return MainWindowLike()


@pytest.fixture
def action_manager(real_main_window, clean_settings):
    """Create ActionManagerV2 instance for testing."""
    manager = ActionManagerV2(real_main_window)
    manager.register_all_actions()
    return manager


# Fixture for persistence tests (settings preserved between managers)
@pytest.fixture
def action_manager_persist(real_main_window, settings_preserve):
    """Create ActionManagerV2 with settings preserved for persistence testing."""
    manager = ActionManagerV2(real_main_window)
    manager.register_all_actions()
    return manager


# Alias for backward compatibility with existing tests
@pytest.fixture
def real_action_manager(action_manager):
    """Alias for action_manager (both use real main window)."""
    return action_manager


# =============================================================================
# Registration Tests
# =============================================================================


class TestActionRegistration:
    """Tests for action registration."""

    def test_registers_all_actions(self, action_manager):
        """All 64 actions should be registered."""
        actions = action_manager.get_all_actions()
        assert len(actions) >= 60  # At least 60 actions
        assert "new" in actions
        assert "save" in actions
        assert "run" in actions
        assert "undo" in actions

    def test_file_actions_registered(self, action_manager):
        """File category actions should be registered."""
        file_actions = action_manager.get_actions_by_category(ActionCategory.FILE)
        assert "new" in file_actions
        assert "open" in file_actions
        assert "save" in file_actions
        assert "save_as" in file_actions
        assert "exit" in file_actions
        assert "save_layout" in file_actions
        assert "reset_layout" in file_actions

    def test_edit_actions_registered(self, action_manager):
        """Edit category actions should be registered."""
        edit_actions = action_manager.get_actions_by_category(ActionCategory.EDIT)
        assert "undo" in edit_actions
        assert "redo" in edit_actions
        assert "cut" in edit_actions
        assert "copy" in edit_actions
        assert "paste" in edit_actions
        assert "delete" in edit_actions

    def test_view_actions_registered(self, action_manager):
        """View category actions should be registered."""
        view_actions = action_manager.get_actions_by_category(ActionCategory.VIEW)
        assert "focus_view" in view_actions
        assert "home_all" in view_actions
        assert "toggle_minimap" in view_actions

    def test_run_actions_registered(self, action_manager):
        """Run category actions should be registered."""
        run_actions = action_manager.get_actions_by_category(ActionCategory.RUN)
        assert "run" in run_actions
        assert "pause" in run_actions
        assert "stop" in run_actions
        assert "restart" in run_actions

    def test_node_actions_registered(self, action_manager):
        """Node category actions should be registered."""
        node_actions = action_manager.get_actions_by_category(ActionCategory.NODE)
        assert "create_frame" in node_actions
        assert "auto_connect" in node_actions
        assert "auto_layout" in node_actions

    def test_checkable_actions_marked_correctly(self, action_manager):
        """Checkable actions should have correct state."""
        auto_connect = action_manager.get_action("auto_connect")
        assert auto_connect is not None
        assert auto_connect.isCheckable()
        assert auto_connect.isChecked()  # Default checked

        grid_snap = action_manager.get_action("toggle_grid_snap")
        assert grid_snap is not None
        assert grid_snap.isCheckable()
        assert grid_snap.isChecked()

    def test_disabled_actions_marked_correctly(self, action_manager):
        """Actions that start disabled should be disabled."""
        undo = action_manager.get_action("undo")
        assert undo is not None
        assert not undo.isEnabled()

        redo = action_manager.get_action("redo")
        assert redo is not None
        assert not redo.isEnabled()

        pause = action_manager.get_action("pause")
        assert pause is not None
        assert not pause.isEnabled()

        stop = action_manager.get_action("stop")
        assert stop is not None
        assert not stop.isEnabled()


# =============================================================================
# Lookup Tests
# =============================================================================


class TestActionLookup:
    """Tests for action lookup and retrieval."""

    def test_get_existing_action(self, action_manager):
        """Should return action for valid name."""
        action = action_manager.get_action("save")
        assert action is not None
        assert isinstance(action, QAction)

    def test_get_nonexistent_action(self, action_manager):
        """Should return None for invalid name."""
        action = action_manager.get_action("nonexistent")
        assert action is None

    def test_get_all_actions_returns_copy(self, action_manager):
        """get_all_actions should return a copy, not internal dict."""
        actions1 = action_manager.get_all_actions()
        actions2 = action_manager.get_all_actions()

        # Modify one dict
        actions1["test"] = "value"

        # Other should be unchanged
        assert "test" not in actions2

    def test_get_actions_by_category_filters_correctly(self, action_manager):
        """Should only return actions in the specified category."""
        file_actions = action_manager.get_actions_by_category(ActionCategory.FILE)
        edit_actions = action_manager.get_actions_by_category(ActionCategory.EDIT)

        # Categories should not overlap
        assert set(file_actions.keys()).isdisjoint(set(edit_actions.keys()))

        # All returned should be in correct category
        for name in file_actions:
            assert action_manager._categories[name] == ActionCategory.FILE


# =============================================================================
# Shortcut Tests
# =============================================================================


class TestShortcuts:
    """Tests for shortcut management."""

    def test_default_shortcuts_assigned(self, action_manager):
        """Default shortcuts should be assigned to actions."""
        new_action = action_manager.get_action("new")
        assert new_action is not None
        assert new_action.shortcut().toString() == "Ctrl+N"

        save_action = action_manager.get_action("save")
        assert save_action is not None
        assert save_action.shortcut().toString() == "Ctrl+S"

    def test_run_shortcuts(self, action_manager):
        """Run actions should have correct shortcuts."""
        run = action_manager.get_action("run")
        assert run.shortcut().toString() == "F5"

        pause = action_manager.get_action("pause")
        assert pause.shortcut().toString() == "F6"

        stop = action_manager.get_action("stop")
        assert stop.shortcut().toString() == "F7"

        restart = action_manager.get_action("restart")
        assert restart.shortcut().toString() == "F8"

    def test_get_shortcut(self, action_manager):
        """get_shortcut should return current shortcut."""
        assert action_manager.get_shortcut("new") == "Ctrl+N"
        assert action_manager.get_shortcut("save") == "Ctrl+S"
        assert action_manager.get_shortcut("nonexistent") == ""

    def test_get_default_shortcut(self, action_manager):
        """get_default_shortcut should return default shortcut."""
        assert action_manager.get_default_shortcut("new") == "Ctrl+N"
        assert action_manager.get_default_shortcut("save") == "Ctrl+S"
        assert action_manager.get_default_shortcut("nonexistent") is None

    def test_set_custom_shortcut(self, real_action_manager):
        """Should be able to set custom shortcut."""
        # Set custom shortcut
        result = real_action_manager.set_shortcut("save", "Ctrl+Shift+S")
        assert result is True

        # Verify shortcut changed
        save_action = real_action_manager.get_action("save")
        assert save_action is not None
        assert save_action.shortcut().toString() == "Ctrl+Shift+S"

    def test_set_shortcut_emits_signal(self, real_action_manager):
        """Setting shortcut should emit signal."""
        signal_received = []

        def on_changed(name, old, new):
            signal_received.append((name, old, new))

        real_action_manager.shortcut_changed.connect(on_changed)

        real_action_manager.set_shortcut("save", "Ctrl+Shift+S")

        assert len(signal_received) == 1
        assert signal_received[0][0] == "save"
        assert signal_received[0][1] == "Ctrl+S"
        assert signal_received[0][2] == "Ctrl+Shift+S"

    def test_set_shortcut_invalid_action(self, action_manager):
        """Should return False for invalid action name."""
        result = action_manager.set_shortcut("nonexistent", "Ctrl+X")
        assert result is False

    def test_set_shortcut_empty_resets_to_default(self, real_action_manager):
        """Empty string should reset to default shortcut."""
        # First set custom
        real_action_manager.set_shortcut("save", "Ctrl+Shift+S")

        # Reset to default
        real_action_manager.set_shortcut("save", "")

        # Should be back to default
        save_action = real_action_manager.get_action("save")
        assert save_action.shortcut().toString() == "Ctrl+S"

    def test_custom_shortcuts_persist(self, action_manager_persist, real_main_window):
        """Custom shortcuts should persist across manager instances."""
        # Set custom shortcut
        action_manager_persist.set_shortcut("save", "Ctrl+Shift+S")

        # Create new manager with same main window
        new_manager = ActionManagerV2(real_main_window)
        new_manager.register_all_actions()

        # Custom shortcut should be loaded
        save_action = new_manager.get_action("save")
        assert save_action.shortcut().toString() == "Ctrl+Shift+S"

        # Cleanup
        new_manager.reset_shortcuts()


# =============================================================================
# Reset Tests
# =============================================================================


class TestReset:
    """Tests for resetting shortcuts."""

    def test_reset_shortcuts(self, real_action_manager):
        """Should reset all shortcuts to defaults."""
        # Set custom shortcuts
        real_action_manager.set_shortcut("save", "Ctrl+Shift+S")
        real_action_manager.set_shortcut("open", "Ctrl+Shift+O")

        # Reset
        real_action_manager.reset_shortcuts()

        # Verify defaults restored
        assert real_action_manager.get_shortcut("save") == "Ctrl+S"
        assert real_action_manager.get_shortcut("open") == "Ctrl+O"

    def test_reset_clears_settings(self, real_action_manager, real_main_window):
        """Reset should clear QSettings."""
        # Set custom shortcut
        real_action_manager.set_shortcut("save", "Ctrl+Shift+S")

        # Reset
        real_action_manager.reset_shortcuts()

        # Create new manager - should have defaults
        new_manager = ActionManagerV2(real_main_window)
        new_manager.register_all_actions()

        assert new_manager.get_shortcut("save") == "Ctrl+S"

        # Cleanup
        new_manager.reset_shortcuts()


# =============================================================================
# Category Tests
# =============================================================================


class TestCategories:
    """Tests for category-based operations."""

    def test_enable_category(self, action_manager):
        """Enable category should enable all actions in category."""
        # Disable some edit actions first
        for name, action in action_manager.get_actions_by_category(ActionCategory.EDIT).items():
            action.setEnabled(False)

        # Enable category
        action_manager.enable_category(ActionCategory.EDIT)

        # All should be enabled
        for action in action_manager.get_actions_by_category(ActionCategory.EDIT).values():
            assert action.isEnabled()

    def test_disable_category(self, action_manager):
        """Disable category should disable all actions in category."""
        # Disable category
        action_manager.disable_category(ActionCategory.EDIT)

        # All edit actions should be disabled
        for action in action_manager.get_actions_by_category(ActionCategory.EDIT).values():
            assert not action.isEnabled()

    def test_get_all_categories(self, action_manager):
        """Should return all used categories."""
        categories = action_manager.get_all_categories()
        assert ActionCategory.FILE in categories
        assert ActionCategory.EDIT in categories
        assert ActionCategory.VIEW in categories
        assert ActionCategory.RUN in categories
        assert ActionCategory.NODE in categories


# =============================================================================
# Action State Tests
# =============================================================================


class TestActionState:
    """Tests for action state management."""

    def test_set_action_enabled(self, action_manager):
        """Should be able to enable/disable specific action."""
        # Disable
        result = action_manager.set_action_enabled("save", False)
        assert result is True
        assert not action_manager.get_action("save").isEnabled()

        # Enable
        result = action_manager.set_action_enabled("save", True)
        assert result is True
        assert action_manager.get_action("save").isEnabled()

    def test_set_action_enabled_invalid(self, action_manager):
        """Should return False for invalid action."""
        result = action_manager.set_action_enabled("nonexistent", False)
        assert result is False

    def test_set_action_checked(self, action_manager):
        """Should be able to set checked state."""
        result = action_manager.set_action_checked("auto_connect", False)
        assert result is True
        assert not action_manager.get_action("auto_connect").isChecked()

        result = action_manager.set_action_checked("auto_connect", True)
        assert result is True
        assert action_manager.get_action("auto_connect").isChecked()

    def test_set_action_checked_non_checkable(self, action_manager):
        """Should return False for non-checkable action."""
        result = action_manager.set_action_checked("save", True)
        assert result is False

    def test_set_action_checked_invalid(self, action_manager):
        """Should return False for invalid action."""
        result = action_manager.set_action_checked("nonexistent", True)
        assert result is False


# =============================================================================
# Handler Connection Tests
# =============================================================================


class TestHandlerConnection:
    """Tests for connecting handlers to actions."""

    def test_connect_handler(self, action_manager):
        """Should be able to connect handler to action."""
        called = []

        def handler():
            called.append(True)

        result = action_manager.connect_handler("save", handler)
        assert result is True

        # Trigger the action
        action_manager.get_action("save").trigger()

        assert len(called) == 1

    def test_connect_handler_invalid_action(self, action_manager):
        """Should return False for invalid action."""
        result = action_manager.connect_handler("nonexistent", lambda: None)
        assert result is False

    def test_connect_slot(self, action_manager):
        """Should be able to connect @Slot decorated method."""
        called = []

        def slot():
            called.append(True)

        result = action_manager.connect_slot("save", slot)
        assert result is True

        action_manager.get_action("save").trigger()

        assert len(called) == 1

    def test_connect_slot_with_checkable_handler(self, action_manager):
        """Checkable handler should receive bool arg."""
        received = []

        def checkable_handler(checked: bool):
            received.append(checked)

        result = action_manager.connect_slot("auto_connect", lambda: None, checkable_handler)
        assert result is True

        # Trigger action (should emit with checked state)
        action_manager.get_action("auto_connect").trigger()

        # Handler should receive bool
        assert len(received) == 1
        assert isinstance(received[0], bool)


# =============================================================================
# Export/Import Tests
# =============================================================================


class TestExportImport:
    """Tests for export/import functionality."""

    def test_export_shortcuts(self, action_manager):
        """Should export all current shortcuts."""
        shortcuts = action_manager.export_shortcuts()

        assert isinstance(shortcuts, dict)
        assert len(shortcuts) >= 60
        assert "new" in shortcuts
        assert "save" in shortcuts
        assert "run" in shortcuts

    def test_export_shortcuts_includes_custom(self, real_action_manager):
        """Export should include custom shortcuts."""
        real_action_manager.set_shortcut("save", "Ctrl+Shift+S")

        shortcuts = real_action_manager.export_shortcuts()

        assert shortcuts["save"] == "Ctrl+Shift+S"

        # Cleanup
        real_action_manager.reset_shortcuts()

    def test_import_shortcuts(self, real_action_manager):
        """Should import shortcuts from dict."""
        new_shortcuts = {
            "save": "Ctrl+Shift+S",
            "open": "Ctrl+Shift+O",
            "new": "Ctrl+Shift+N",
            "nonexistent": "Ctrl+X",  # Should be ignored
        }

        count = real_action_manager.import_shortcuts(new_shortcuts)

        assert count == 3  # Only valid actions imported
        assert real_action_manager.get_shortcut("save") == "Ctrl+Shift+S"
        assert real_action_manager.get_shortcut("open") == "Ctrl+Shift+O"
        assert real_action_manager.get_shortcut("new") == "Ctrl+Shift+N"

        # Cleanup
        real_action_manager.reset_shortcuts()

    def test_import_empty_dict(self, action_manager):
        """Import empty dict should do nothing."""
        count = action_manager.import_shortcuts({})
        assert count == 0


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_action_from_manager(self, real_action_manager, real_main_window):
        """get_action should retrieve from action manager."""
        # Set the _action_manager_v2 attribute that get_action looks for
        real_main_window._action_manager_v2 = real_action_manager
        action = get_action(real_main_window, "save")
        assert action is not None
        assert isinstance(action, QAction)

    def test_get_action_none_if_no_manager(self, real_main_window):
        """Should return None if main window has no action manager."""
        action = get_action(real_main_window, "save")
        assert action is None


# =============================================================================
# DEFAULT_SHORTCUTS Tests
# =============================================================================


class TestDefaultShortcuts:
    """Tests for DEFAULT_SHORTCUTS constant."""

    def test_default_shortcuts_is_dict(self):
        """DEFAULT_SHORTCUTS should be a dict."""
        assert isinstance(DEFAULT_SHORTCUTS, dict)

    def test_default_shortcuts_has_entries(self):
        """Should have at least 60 entries."""
        assert len(DEFAULT_SHORTCUTS) >= 60

    def test_default_shortcuts_has_required_actions(self):
        """Should have all required actions."""
        required = ["new", "open", "save", "run", "pause", "stop", "undo", "redo"]
        for action in required:
            assert action in DEFAULT_SHORTCUTS

    def test_default_shortcuts_values_are_valid(self):
        """All shortcut values should be valid types."""
        for key, value in DEFAULT_SHORTCUTS.items():
            assert isinstance(value, (QKeySequence.StandardKey, str, list, type(None)))


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for ActionManagerV2."""

    def test_full_workflow(self, action_manager_persist, real_main_window):
        """Test complete workflow: customize, save, load, reset."""
        # 1. Customize shortcuts
        action_manager_persist.set_shortcut("save", "Ctrl+Shift+S")
        action_manager_persist.set_shortcut("open", "Ctrl+Shift+O")

        # 2. Export
        exported = action_manager_persist.export_shortcuts()
        assert exported["save"] == "Ctrl+Shift+S"

        # 3. Create new manager (simulates app restart)
        new_manager = ActionManagerV2(real_main_window)
        new_manager.register_all_actions()

        # 4. Verify shortcuts persisted
        assert new_manager.get_shortcut("save") == "Ctrl+Shift+S"
        assert new_manager.get_shortcut("open") == "Ctrl+Shift+O"

        # 5. Reset
        new_manager.reset_shortcuts()

        # 6. Verify defaults restored
        assert new_manager.get_shortcut("save") == "Ctrl+S"
        assert new_manager.get_shortcut("open") == "Ctrl+O"

    def test_category_workflow(self, action_manager):
        """Test category-based workflow."""
        # Disable all run actions (simulating not running state)
        action_manager.disable_category(ActionCategory.RUN)

        run = action_manager.get_action("run")
        assert not run.isEnabled()

        pause = action_manager.get_action("pause")
        assert not pause.isEnabled()

        # Enable all run actions
        action_manager.enable_category(ActionCategory.RUN)

        assert run.isEnabled()
        assert pause.isEnabled()
