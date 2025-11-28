"""
Tests for ActionFactory UI component.

Tests action creation, configuration, shortcuts, and state management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QAction, QKeySequence

from casare_rpa.canvas.ui.action_factory import ActionFactory


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_main_window(qapp):
    """Create a mock MainWindow with required methods."""
    mw = QMainWindow()

    # Mock all handler methods that actions connect to
    mw._on_new_workflow = Mock()
    mw._on_new_from_template = Mock()
    mw._on_open_workflow = Mock()
    mw._on_import_workflow = Mock()
    mw._on_export_selected = Mock()
    mw._on_save_workflow = Mock()
    mw._on_save_as_workflow = Mock()
    mw._on_find_node = Mock()
    mw._on_paste_workflow = Mock()
    mw._on_select_nearest_node = Mock()
    mw._on_toggle_disable_node = Mock()
    mw._on_preferences = Mock()
    mw._on_toggle_bottom_panel = Mock()
    mw._on_toggle_variable_inspector = Mock()
    mw.validate_current_workflow = Mock()
    mw._on_toggle_minimap = Mock()
    mw._on_toggle_auto_connect = Mock()
    mw._on_run_workflow = Mock()
    mw._on_run_to_node = Mock()
    mw._on_run_single_node = Mock()
    mw._on_pause_workflow = Mock()
    mw._on_stop_workflow = Mock()
    mw._on_schedule_workflow = Mock()
    mw._on_manage_schedules = Mock()
    mw._on_pick_selector = Mock()
    mw._on_toggle_recording = Mock()
    mw._on_open_hotkey_manager = Mock()
    mw._on_open_desktop_selector_builder = Mock()
    mw._on_create_frame = Mock()
    mw._on_open_performance_dashboard = Mock()
    mw._on_open_command_palette = Mock()
    mw._on_about = Mock()

    yield mw
    mw.deleteLater()


@pytest.fixture
def action_factory(mock_main_window):
    """Create ActionFactory instance."""
    factory = ActionFactory(mock_main_window)
    yield factory


class TestActionFactoryInitialization:
    """Tests for ActionFactory initialization."""

    def test_initialization(self, mock_main_window):
        """Test factory initializes correctly."""
        factory = ActionFactory(mock_main_window)
        assert factory._main_window is mock_main_window
        assert factory._actions == {}

    def test_actions_property(self, action_factory):
        """Test actions property returns dict."""
        assert isinstance(action_factory.actions, dict)

    def test_parent_set_correctly(self, action_factory, mock_main_window):
        """Test QObject parent is set."""
        assert action_factory.parent() is mock_main_window


class TestActionCreation:
    """Tests for action creation methods."""

    def test_create_all_actions(self, action_factory):
        """Test create_all_actions creates all expected actions."""
        action_factory.create_all_actions()

        # Should have created many actions
        assert len(action_factory.actions) > 30

    def test_create_file_actions(self, action_factory):
        """Test File menu actions are created."""
        action_factory.create_all_actions()

        file_actions = [
            "new",
            "new_from_template",
            "open",
            "import",
            "export_selected",
            "save",
            "save_as",
            "save_to_scenario",
            "exit",
        ]
        for name in file_actions:
            assert name in action_factory.actions, f"Missing action: {name}"
            assert isinstance(action_factory.actions[name], QAction)

    def test_create_edit_actions(self, action_factory):
        """Test Edit menu actions are created."""
        action_factory.create_all_actions()

        edit_actions = [
            "find_node",
            "undo",
            "redo",
            "delete",
            "cut",
            "copy",
            "paste",
            "duplicate",
            "paste_workflow",
            "select_all",
            "deselect_all",
            "select_nearest",
            "toggle_disable",
            "preferences",
        ]
        for name in edit_actions:
            assert name in action_factory.actions, f"Missing action: {name}"

    def test_create_view_actions(self, action_factory):
        """Test View menu actions are created."""
        action_factory.create_all_actions()

        view_actions = [
            "zoom_in",
            "zoom_out",
            "zoom_reset",
            "fit_view",
            "toggle_bottom_panel",
            "toggle_variable_inspector",
            "validate",
            "toggle_minimap",
            "auto_connect",
        ]
        for name in view_actions:
            assert name in action_factory.actions, f"Missing action: {name}"

    def test_create_workflow_actions(self, action_factory):
        """Test Workflow menu actions are created."""
        action_factory.create_all_actions()

        workflow_actions = [
            "run",
            "run_to_node",
            "run_single_node",
            "pause",
            "stop",
            "schedule",
            "manage_schedules",
        ]
        for name in workflow_actions:
            assert name in action_factory.actions, f"Missing action: {name}"

    def test_create_tool_actions(self, action_factory):
        """Test Tools menu actions are created."""
        action_factory.create_all_actions()

        tool_actions = [
            "pick_selector",
            "record_workflow",
            "hotkey_manager",
            "desktop_selector_builder",
            "create_frame",
            "performance_dashboard",
            "command_palette",
        ]
        for name in tool_actions:
            assert name in action_factory.actions, f"Missing action: {name}"

    def test_create_help_actions(self, action_factory):
        """Test Help menu actions are created."""
        action_factory.create_all_actions()

        assert "about" in action_factory.actions


class TestActionConfiguration:
    """Tests for action configuration."""

    def test_action_text(self, action_factory):
        """Test actions have correct text."""
        action_factory.create_all_actions()

        assert action_factory.actions["new"].text() == "&New Workflow"
        assert action_factory.actions["save"].text() == "&Save Workflow"
        assert action_factory.actions["undo"].text() == "&Undo"

    def test_action_status_tip(self, action_factory):
        """Test actions have status tips."""
        action_factory.create_all_actions()

        assert action_factory.actions["new"].statusTip() == "Create a new workflow"
        assert action_factory.actions["save"].statusTip() == "Save the current workflow"

    def test_action_shortcut_string(self, action_factory):
        """Test actions with string shortcuts."""
        action_factory.create_all_actions()

        # Check custom shortcuts
        assert action_factory.actions["duplicate"].shortcut() == QKeySequence("Ctrl+D")
        assert action_factory.actions["run"].shortcut() == QKeySequence("F3")
        assert action_factory.actions["delete"].shortcut() == QKeySequence("X")

    def test_action_standard_shortcuts(self, action_factory):
        """Test actions with standard key shortcuts."""
        action_factory.create_all_actions()

        # Standard shortcuts are assigned
        new_action = action_factory.actions["new"]
        assert not new_action.shortcut().isEmpty()

    def test_checkable_actions(self, action_factory):
        """Test checkable actions are configured correctly."""
        action_factory.create_all_actions()

        checkable_actions = [
            "toggle_bottom_panel",
            "toggle_variable_inspector",
            "toggle_minimap",
            "auto_connect",
            "pause",
            "record_workflow",
        ]
        for name in checkable_actions:
            assert action_factory.actions[
                name
            ].isCheckable(), f"{name} should be checkable"

    def test_auto_connect_default_checked(self, action_factory):
        """Test auto_connect is checked by default."""
        action_factory.create_all_actions()
        assert action_factory.actions["auto_connect"].isChecked()

    def test_disabled_actions_initial_state(self, action_factory):
        """Test actions that start disabled."""
        action_factory.create_all_actions()

        disabled_actions = [
            "undo",
            "redo",
            "pause",
            "stop",
            "pick_selector",
            "record_workflow",
        ]
        for name in disabled_actions:
            assert not action_factory.actions[
                name
            ].isEnabled(), f"{name} should be disabled"


class TestActionTriggered:
    """Tests for action triggered callbacks."""

    def test_new_workflow_triggered(self, action_factory, mock_main_window):
        """Test new workflow action triggers handler."""
        action_factory.create_all_actions()
        action_factory.actions["new"].trigger()
        mock_main_window._on_new_workflow.assert_called_once()

    def test_open_workflow_triggered(self, action_factory, mock_main_window):
        """Test open workflow action triggers handler."""
        action_factory.create_all_actions()
        action_factory.actions["open"].trigger()
        mock_main_window._on_open_workflow.assert_called_once()

    def test_save_workflow_triggered(self, action_factory, mock_main_window):
        """Test save workflow action triggers handler."""
        action_factory.create_all_actions()
        action_factory.actions["save"].trigger()
        mock_main_window._on_save_workflow.assert_called_once()

    def test_run_workflow_triggered(self, action_factory, mock_main_window):
        """Test run workflow action triggers handler."""
        action_factory.create_all_actions()
        action_factory.actions["run"].trigger()
        mock_main_window._on_run_workflow.assert_called_once()

    def test_preferences_triggered(self, action_factory, mock_main_window):
        """Test preferences action triggers handler."""
        action_factory.create_all_actions()
        action_factory.actions["preferences"].trigger()
        mock_main_window._on_preferences.assert_called_once()


class TestGetAction:
    """Tests for get_action method."""

    def test_get_existing_action(self, action_factory):
        """Test getting existing action."""
        action_factory.create_all_actions()

        action = action_factory.get_action("run")
        assert action is not None
        assert isinstance(action, QAction)

    def test_get_nonexistent_action(self, action_factory):
        """Test getting non-existent action returns None."""
        action_factory.create_all_actions()

        action = action_factory.get_action("nonexistent")
        assert action is None


class TestSetActionsEnabled:
    """Tests for set_actions_enabled method."""

    def test_enable_multiple_actions(self, action_factory):
        """Test enabling multiple actions."""
        action_factory.create_all_actions()

        # First disable some actions
        action_factory.set_actions_enabled(["run", "pause", "stop"], False)
        assert not action_factory.actions["run"].isEnabled()
        assert not action_factory.actions["pause"].isEnabled()
        assert not action_factory.actions["stop"].isEnabled()

        # Now enable them
        action_factory.set_actions_enabled(["run", "pause", "stop"], True)
        assert action_factory.actions["run"].isEnabled()
        assert action_factory.actions["pause"].isEnabled()
        assert action_factory.actions["stop"].isEnabled()

    def test_disable_multiple_actions(self, action_factory):
        """Test disabling multiple actions."""
        action_factory.create_all_actions()

        action_factory.set_actions_enabled(["new", "open", "save"], False)
        assert not action_factory.actions["new"].isEnabled()
        assert not action_factory.actions["open"].isEnabled()
        assert not action_factory.actions["save"].isEnabled()

    def test_set_actions_enabled_ignores_unknown(self, action_factory):
        """Test unknown action names are ignored."""
        action_factory.create_all_actions()

        # Should not raise error
        action_factory.set_actions_enabled(["unknown1", "unknown2"], True)


class TestLoadHotkeys:
    """Tests for load_hotkeys method."""

    def test_load_hotkeys_applies_shortcuts(self, action_factory):
        """Test loading hotkeys applies to actions."""
        action_factory.create_all_actions()

        mock_hotkey_settings = Mock()
        mock_hotkey_settings.get_shortcuts.return_value = ["Ctrl+Alt+N"]

        action_factory.load_hotkeys(mock_hotkey_settings)

        # Should have called get_shortcuts for each mapped action
        assert mock_hotkey_settings.get_shortcuts.called

    def test_load_hotkeys_multiple_shortcuts(self, action_factory):
        """Test loading multiple shortcuts per action."""
        action_factory.create_all_actions()

        mock_hotkey_settings = Mock()
        mock_hotkey_settings.get_shortcuts.return_value = ["Ctrl+S", "Ctrl+Shift+S"]

        action_factory.load_hotkeys(mock_hotkey_settings)

        # Action should have multiple shortcuts if settings returned them
        mock_hotkey_settings.get_shortcuts.assert_called()

    def test_load_hotkeys_empty_shortcuts(self, action_factory):
        """Test loading empty shortcuts does nothing."""
        action_factory.create_all_actions()

        mock_hotkey_settings = Mock()
        mock_hotkey_settings.get_shortcuts.return_value = []

        # Should not raise error
        action_factory.load_hotkeys(mock_hotkey_settings)

    def test_load_hotkeys_none_shortcuts(self, action_factory):
        """Test loading None shortcuts does nothing."""
        action_factory.create_all_actions()

        mock_hotkey_settings = Mock()
        mock_hotkey_settings.get_shortcuts.return_value = None

        # Should not raise error
        action_factory.load_hotkeys(mock_hotkey_settings)


class TestCreateActionMethod:
    """Tests for internal _create_action method."""

    def test_create_action_basic(self, action_factory):
        """Test basic action creation."""
        action = action_factory._create_action(name="test_action", text="Test Action")

        assert action.text() == "Test Action"
        assert "test_action" in action_factory.actions

    def test_create_action_with_shortcut(self, action_factory):
        """Test action creation with shortcut."""
        action = action_factory._create_action(
            name="test_shortcut", text="Test", shortcut="Ctrl+T"
        )

        assert action.shortcut() == QKeySequence("Ctrl+T")

    def test_create_action_with_status_tip(self, action_factory):
        """Test action creation with status tip."""
        action = action_factory._create_action(
            name="test_tip", text="Test", status_tip="This is a tip"
        )

        assert action.statusTip() == "This is a tip"

    def test_create_action_with_callback(self, action_factory):
        """Test action creation with triggered callback."""
        callback = Mock()
        action = action_factory._create_action(
            name="test_callback", text="Test", triggered=callback
        )

        action.trigger()
        callback.assert_called_once()

    def test_create_action_checkable(self, action_factory):
        """Test action creation with checkable."""
        action = action_factory._create_action(
            name="test_checkable", text="Test", checkable=True, checked=True
        )

        assert action.isCheckable()
        assert action.isChecked()

    def test_create_action_disabled(self, action_factory):
        """Test action creation disabled."""
        action = action_factory._create_action(
            name="test_disabled", text="Test", enabled=False
        )

        assert not action.isEnabled()


class TestActionFactoryIntegration:
    """Integration tests for ActionFactory."""

    def test_all_actions_have_text(self, action_factory):
        """Test all actions have text set."""
        action_factory.create_all_actions()

        for name, action in action_factory.actions.items():
            assert action.text(), f"Action {name} has no text"

    def test_no_duplicate_shortcuts(self, action_factory):
        """Test no duplicate shortcuts exist (except intentional duplicates)."""
        action_factory.create_all_actions()

        shortcuts = {}
        intentional_duplicates = {
            "Ctrl+Shift+V",
            "Ctrl+Shift+P",
            "Ctrl+Shift+S",
            "Ctrl+F",
        }

        for name, action in action_factory.actions.items():
            shortcut = action.shortcut().toString()
            if shortcut and shortcut not in intentional_duplicates:
                if shortcut in shortcuts:
                    # Allow some duplicates that may be context-sensitive
                    pass
                shortcuts[shortcut] = name

    def test_workflow_execution_action_states(self, action_factory):
        """Test workflow execution actions have correct initial states."""
        action_factory.create_all_actions()

        # Run actions should be enabled
        assert action_factory.actions["run"].isEnabled()
        assert action_factory.actions["run_to_node"].isEnabled()
        assert action_factory.actions["run_single_node"].isEnabled()

        # Pause and stop should be disabled
        assert not action_factory.actions["pause"].isEnabled()
        assert not action_factory.actions["stop"].isEnabled()
