"""
Tests for CasareRPA Canvas MainWindow.

Tests window initialization, actions, menus, and workflow operations.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from conftest import click_action, get_menu_action


class TestMainWindowInitialization:
    """Tests for MainWindow initialization."""

    def test_window_created(self, main_window):
        """Test that main window is created successfully."""
        assert main_window is not None

    def test_window_title_contains_app_name(self, main_window):
        """Test window title contains application name."""
        assert "CasareRPA" in main_window.windowTitle()

    def test_initial_modified_state_is_false(self, main_window):
        """Test workflow is not modified on startup."""
        assert main_window.is_modified() is False

    def test_initial_current_file_is_none(self, main_window):
        """Test no file is open on startup."""
        assert main_window.get_current_file() is None

    def test_window_has_menubar(self, main_window):
        """Test main window has a menu bar."""
        assert main_window.menuBar() is not None

    def test_window_has_statusbar(self, main_window):
        """Test main window has a status bar."""
        assert main_window.statusBar() is not None


class TestMainWindowActions:
    """Tests for MainWindow actions."""

    def test_new_action_exists(self, main_window):
        """Test new workflow action exists."""
        assert main_window.action_new is not None

    def test_open_action_exists(self, main_window):
        """Test open workflow action exists."""
        assert main_window.action_open is not None

    def test_save_action_exists(self, main_window):
        """Test save workflow action exists."""
        assert main_window.action_save is not None

    def test_save_as_action_exists(self, main_window):
        """Test save as action exists."""
        assert main_window.action_save_as is not None

    def test_run_action_exists(self, main_window):
        """Test run workflow action exists."""
        assert main_window.action_run is not None

    def test_pause_action_exists(self, main_window):
        """Test pause workflow action exists."""
        assert main_window.action_pause is not None

    def test_stop_action_exists(self, main_window):
        """Test stop workflow action exists."""
        assert main_window.action_stop is not None

    def test_schedule_action_exists(self, main_window):
        """Test schedule action exists."""
        assert main_window.action_schedule is not None

    def test_manage_schedules_action_exists(self, main_window):
        """Test manage schedules action exists."""
        assert main_window.action_manage_schedules is not None

    def test_save_action_initially_disabled(self, main_window):
        """Test save action is disabled when not modified."""
        assert main_window.action_save.isEnabled() is False

    def test_pause_action_initially_disabled(self, main_window):
        """Test pause action is disabled when not running."""
        assert main_window.action_pause.isEnabled() is False

    def test_stop_action_initially_disabled(self, main_window):
        """Test stop action is disabled when not running."""
        assert main_window.action_stop.isEnabled() is False


class TestMainWindowMenuStructure:
    """Tests for menu structure."""

    def test_file_menu_exists(self, main_window):
        """Test File menu exists."""
        action = get_menu_action(main_window, "&File", "&New Workflow")
        assert action is not None

    def test_edit_menu_exists(self, main_window):
        """Test Edit menu exists."""
        action = get_menu_action(main_window, "&Edit", "&Undo")
        assert action is not None

    def test_view_menu_exists(self, main_window):
        """Test View menu exists."""
        action = get_menu_action(main_window, "&View", "Zoom &In")
        assert action is not None

    def test_workflow_menu_exists(self, main_window):
        """Test Workflow menu exists."""
        action = get_menu_action(main_window, "&Workflow", "&Run Workflow")
        assert action is not None

    def test_tools_menu_exists(self, main_window):
        """Test Tools menu exists."""
        # Tools menu contains selector picker
        action = get_menu_action(main_window, "&Tools", "&Keyboard Shortcuts...")
        assert action is not None

    def test_help_menu_exists(self, main_window):
        """Test Help menu exists."""
        action = get_menu_action(main_window, "&Help", "&About")
        assert action is not None


class TestModifiedState:
    """Tests for workflow modified state handling."""

    def test_set_modified_updates_state(self, main_window):
        """Test setting modified state."""
        main_window.set_modified(True)
        assert main_window.is_modified() is True

    def test_set_modified_updates_title(self, main_window):
        """Test modified state adds asterisk to title."""
        main_window.set_modified(True)
        assert main_window.windowTitle().startswith("*")

    def test_unset_modified_removes_asterisk(self, main_window):
        """Test clearing modified state removes asterisk."""
        main_window.set_modified(True)
        main_window.set_modified(False)
        assert not main_window.windowTitle().startswith("*")

    def test_set_modified_enables_save_action(self, main_window):
        """Test modified state enables save action."""
        main_window.set_modified(True)
        # Call _update_actions which is normally called automatically
        main_window._update_actions()
        assert main_window.action_save.isEnabled() is True


class TestCurrentFile:
    """Tests for current file handling."""

    def test_set_current_file(self, main_window, tmp_path):
        """Test setting current file path."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        main_window.set_current_file(test_file)

        assert main_window.get_current_file() == test_file

    def test_set_current_file_updates_title(self, main_window, tmp_path):
        """Test setting current file updates window title."""
        test_file = tmp_path / "my_workflow.json"
        test_file.write_text("{}")

        main_window.set_current_file(test_file)

        assert "my_workflow.json" in main_window.windowTitle()

    def test_clear_current_file(self, main_window, tmp_path):
        """Test clearing current file."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        main_window.set_current_file(test_file)
        main_window.set_current_file(None)

        assert main_window.get_current_file() is None
        assert "Untitled" in main_window.windowTitle()


class TestWorkflowSignals:
    """Tests for workflow operation signals."""

    def test_new_workflow_emits_signal(self, main_window, qtbot):
        """Test new workflow action emits signal."""
        with qtbot.waitSignal(main_window.workflow_new, timeout=1000):
            main_window.action_new.trigger()

    def test_run_workflow_emits_signal(self, main_window, qtbot):
        """Test run workflow action emits signal."""
        with qtbot.waitSignal(main_window.workflow_run, timeout=1000):
            main_window.action_run.trigger()

    def test_run_enables_pause_and_stop(self, main_window, qtbot):
        """Test running workflow enables pause and stop actions."""
        main_window.action_run.trigger()

        assert main_window.action_pause.isEnabled() is True
        assert main_window.action_stop.isEnabled() is True

    def test_run_disables_run_action(self, main_window, qtbot):
        """Test running workflow disables run action."""
        main_window.action_run.trigger()

        assert main_window.action_run.isEnabled() is False

    def test_stop_workflow_emits_signal(self, main_window, qtbot):
        """Test stop action emits signal."""
        # First run to enable stop
        main_window.action_run.trigger()

        with qtbot.waitSignal(main_window.workflow_stop, timeout=1000):
            main_window.action_stop.trigger()

    def test_stop_restores_action_states(self, main_window, qtbot):
        """Test stopping workflow restores action states."""
        main_window.action_run.trigger()
        main_window.action_stop.trigger()

        assert main_window.action_run.isEnabled() is True
        assert main_window.action_pause.isEnabled() is False
        assert main_window.action_stop.isEnabled() is False

    def test_pause_emits_signal_when_checked(self, main_window, qtbot):
        """Test pause action emits pause signal when checked."""
        main_window.action_run.trigger()

        with qtbot.waitSignal(main_window.workflow_pause, timeout=1000):
            main_window.action_pause.trigger()

    def test_pause_emits_resume_when_unchecked(self, main_window, qtbot):
        """Test pause action emits resume signal when unchecked."""
        main_window.action_run.trigger()
        main_window.action_pause.setChecked(True)

        with qtbot.waitSignal(main_window.workflow_resume, timeout=1000):
            main_window.action_pause.trigger()


class TestFileOperations:
    """Tests for file operation dialogs."""

    def test_open_shows_file_dialog(self, main_window, qtbot, mock_file_dialog):
        """Test open action shows file dialog."""
        mock_file_dialog.getOpenFileName.return_value = ("", "")

        main_window.action_open.trigger()

        mock_file_dialog.getOpenFileName.assert_called_once()

    def test_open_emits_signal_with_file_path(self, main_window, qtbot, mock_file_dialog, tmp_path):
        """Test open emits signal with selected file path."""
        test_file = tmp_path / "workflow.json"
        test_file.write_text("{}")
        mock_file_dialog.getOpenFileName.return_value = (str(test_file), "")

        with qtbot.waitSignal(main_window.workflow_open, timeout=1000) as blocker:
            main_window.action_open.trigger()

        assert blocker.args == [str(test_file)]

    def test_save_as_shows_file_dialog(self, main_window, qtbot, mock_file_dialog):
        """Test save as action shows file dialog."""
        mock_file_dialog.getSaveFileName.return_value = ("", "")

        main_window.action_save_as.trigger()

        mock_file_dialog.getSaveFileName.assert_called_once()

    def test_save_without_file_triggers_save_as(self, main_window, qtbot, mock_file_dialog):
        """Test save without current file triggers save as dialog."""
        mock_file_dialog.getSaveFileName.return_value = ("", "")
        main_window.set_modified(True)

        main_window.action_save.trigger()

        mock_file_dialog.getSaveFileName.assert_called_once()

    def test_save_with_file_emits_signal(self, main_window_with_file, qtbot):
        """Test save with current file emits save signal."""
        main_window_with_file.set_modified(True)

        with qtbot.waitSignal(main_window_with_file.workflow_save, timeout=1000):
            main_window_with_file.action_save.trigger()


class TestUnsavedChangesDialog:
    """Tests for unsaved changes prompt."""

    def test_new_with_changes_shows_dialog(self, main_window, qtbot, mock_message_box):
        """Test new workflow with changes shows confirmation dialog."""
        mock_message_box.question.return_value = QMessageBox.StandardButton.Discard
        main_window.set_modified(True)

        main_window.action_new.trigger()

        mock_message_box.question.assert_called_once()

    def test_discard_changes_proceeds(self, main_window, qtbot, mock_message_box):
        """Test discarding changes allows proceeding."""
        mock_message_box.question.return_value = QMessageBox.StandardButton.Discard
        main_window.set_modified(True)

        with qtbot.waitSignal(main_window.workflow_new, timeout=1000):
            main_window.action_new.trigger()

    def test_cancel_prevents_action(self, main_window, qtbot, mock_message_box):
        """Test canceling prevents the action."""
        mock_message_box.question.return_value = QMessageBox.StandardButton.Cancel
        main_window.set_modified(True)

        # Should not emit signal within timeout
        with pytest.raises(Exception):  # waitSignal raises on timeout
            with qtbot.waitSignal(main_window.workflow_new, timeout=100):
                main_window.action_new.trigger()


class TestDebugComponents:
    """Tests for debug toolbar and panels."""

    def test_debug_toolbar_created(self, main_window):
        """Test debug toolbar is created."""
        toolbar = main_window.get_debug_toolbar()
        assert toolbar is not None

    def test_variable_inspector_created(self, main_window):
        """Test variable inspector panel is created."""
        inspector = main_window.get_variable_inspector()
        assert inspector is not None

    def test_execution_history_viewer_created(self, main_window):
        """Test execution history viewer is created."""
        history = main_window.get_execution_history_viewer()
        assert history is not None


class TestLogViewer:
    """Tests for execution log viewer."""

    def test_log_viewer_created(self, main_window):
        """Test log viewer is created."""
        viewer = main_window.get_log_viewer()
        assert viewer is not None

    def test_toggle_log_shows_viewer(self, main_window, qtbot):
        """Test toggle log action shows log viewer."""
        main_window.action_toggle_log.setChecked(True)
        main_window.action_toggle_log.trigger()

        # The log dock should be visible
        assert main_window._log_dock.isVisible() is True

    def test_toggle_log_hides_viewer(self, main_window, qtbot):
        """Test toggle log action hides log viewer."""
        main_window.show_log_viewer()
        main_window.action_toggle_log.setChecked(False)
        main_window.action_toggle_log.trigger()

        assert main_window._log_dock.isVisible() is False


class TestBrowserActions:
    """Tests for browser-dependent actions."""

    def test_pick_selector_initially_disabled(self, main_window):
        """Test pick selector is disabled when browser not running."""
        assert main_window.action_pick_selector.isEnabled() is False

    def test_record_workflow_initially_disabled(self, main_window):
        """Test record workflow is disabled when browser not running."""
        assert main_window.action_record_workflow.isEnabled() is False

    def test_set_browser_running_enables_actions(self, main_window):
        """Test setting browser running enables related actions."""
        main_window.set_browser_running(True)

        assert main_window.action_pick_selector.isEnabled() is True
        assert main_window.action_record_workflow.isEnabled() is True

    def test_set_browser_not_running_disables_actions(self, main_window):
        """Test setting browser not running disables related actions."""
        main_window.set_browser_running(True)
        main_window.set_browser_running(False)

        assert main_window.action_pick_selector.isEnabled() is False
        assert main_window.action_record_workflow.isEnabled() is False


class TestCloseEvent:
    """Tests for window close behavior."""

    def test_close_without_changes_succeeds(self, main_window, qtbot):
        """Test closing window without changes succeeds."""
        # Not modified, should close
        assert main_window._check_unsaved_changes() is True

    def test_close_with_changes_shows_dialog(self, main_window, qtbot, mock_message_box):
        """Test closing window with changes shows dialog."""
        mock_message_box.question.return_value = QMessageBox.StandardButton.Cancel
        main_window.set_modified(True)

        result = main_window._check_unsaved_changes()

        mock_message_box.question.assert_called_once()
        assert result is False


class TestAboutDialog:
    """Tests for about dialog."""

    def test_about_action_exists(self, main_window):
        """Test about action exists."""
        assert main_window.action_about is not None

    def test_about_action_triggers(self, main_window, mock_message_box):
        """Test about action triggers about dialog."""
        main_window.action_about.trigger()

        mock_message_box.about.assert_called_once()
