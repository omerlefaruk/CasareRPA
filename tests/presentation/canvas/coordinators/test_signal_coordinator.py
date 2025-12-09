"""
Tests for SignalCoordinator.

Tests cover:
- Action callbacks fire correctly
- Methods delegate to proper controllers
- Error handling in callbacks
- All action handler categories (workflow, execution, debug, node, view, etc.)

Note: These tests mock all Qt dependencies to avoid Qt initialization issues.
The pytest-qt plugin is disabled for this module.
"""

import sys
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

# Mark entire module to skip Qt processing
pytestmark = pytest.mark.qt_no_exception_capture


# Patch Qt modules before any imports that might load them
_qt_mock = MagicMock()
_qt_mock.QTimer = MagicMock()
_qt_mock.QApplication = MagicMock()
_qt_mock.QApplication.focusWidget = MagicMock(return_value=None)
_qt_mock.QLineEdit = type("QLineEdit", (), {})
_qt_mock.QTextEdit = type("QTextEdit", (), {})

# Patch sys.modules before SignalCoordinator is imported
_pyside6_patches = {
    "PySide6": _qt_mock,
    "PySide6.QtCore": _qt_mock,
    "PySide6.QtWidgets": _qt_mock,
    "PySide6.QtGui": _qt_mock,
}

for mod_name, mod_mock in _pyside6_patches.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mod_mock


@pytest.fixture
def mock_qt():
    """Mock Qt modules to avoid Qt initialization."""
    # Already patched at module level
    yield


@pytest.fixture
def mock_main_window(mock_qt):
    """Create a mock MainWindow with all expected controllers."""
    mw = Mock()

    # Controllers
    mw._workflow_controller = Mock()
    mw._execution_controller = Mock()
    mw._node_controller = Mock()
    mw._viewport_controller = Mock()
    mw._menu_controller = Mock()
    mw._selector_controller = Mock()
    mw._ui_state_controller = Mock()
    mw._panel_controller = Mock()
    mw._project_controller = Mock()
    mw._quick_node_manager = Mock()

    # UI elements
    mw._debug_panel = Mock()
    mw._bottom_panel = Mock()
    mw._central_widget = Mock()
    mw.graph = Mock()
    mw._auto_connect_enabled = False
    mw._status_bar_manager = Mock()
    mw._fleet_dashboard_manager = Mock()

    # Methods
    mw.show_status = Mock()
    mw.show_minimap = Mock()
    mw.hide_minimap = Mock()
    mw.get_graph = Mock(return_value=mw.graph)
    mw.set_modified = Mock()
    mw.validate_current_workflow = Mock()

    # Signals
    mw.save_as_scenario_requested = Mock()
    mw.save_as_scenario_requested.emit = Mock()

    # Actions
    mw.action_record_workflow = Mock()
    mw.action_record_workflow.setChecked = Mock()
    mw.action_record_workflow.blockSignals = Mock()
    mw.action_start_listening = Mock()
    mw.action_stop_listening = Mock()

    return mw


@pytest.fixture
def signal_coordinator(mock_main_window, mock_qt):
    """Create a SignalCoordinator with mocked MainWindow."""
    with (
        patch("casare_rpa.presentation.canvas.coordinators.signal_coordinator.QTimer"),
        patch(
            "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QApplication"
        ),
        patch(
            "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QLineEdit"
        ),
        patch(
            "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QTextEdit"
        ),
    ):
        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        return SignalCoordinator(mock_main_window)


# ============================================================================
# Workflow Actions Tests
# ============================================================================


class TestWorkflowActions:
    """Tests for workflow action handlers."""

    def test_on_new_workflow(self, signal_coordinator, mock_main_window):
        """on_new_workflow should delegate to workflow controller."""
        signal_coordinator.on_new_workflow()
        mock_main_window._workflow_controller.new_workflow.assert_called_once()

    def test_on_open_workflow(self, signal_coordinator, mock_main_window):
        """on_open_workflow should delegate to workflow controller."""
        signal_coordinator.on_open_workflow()
        mock_main_window._workflow_controller.open_workflow.assert_called_once()

    def test_on_import_workflow(self, signal_coordinator, mock_main_window):
        """on_import_workflow should delegate to workflow controller."""
        signal_coordinator.on_import_workflow()
        mock_main_window._workflow_controller.import_workflow.assert_called_once()

    def test_on_export_selected(self, signal_coordinator, mock_main_window):
        """on_export_selected should delegate to workflow controller."""
        signal_coordinator.on_export_selected()
        mock_main_window._workflow_controller.export_selected_nodes.assert_called_once()

    def test_on_paste_workflow(self, signal_coordinator, mock_main_window):
        """on_paste_workflow should delegate to workflow controller."""
        signal_coordinator.on_paste_workflow()
        mock_main_window._workflow_controller.paste_workflow.assert_called_once()

    def test_on_save_workflow(self, signal_coordinator, mock_main_window):
        """on_save_workflow should delegate to workflow controller."""
        signal_coordinator.on_save_workflow()
        mock_main_window._workflow_controller.save_workflow.assert_called_once()

    def test_on_save_workflow_no_controller(self, signal_coordinator, mock_main_window):
        """on_save_workflow should handle missing controller gracefully."""
        mock_main_window._workflow_controller = None
        # Should not raise
        signal_coordinator.on_save_workflow()

    def test_on_save_as_workflow(self, signal_coordinator, mock_main_window):
        """on_save_as_workflow should delegate to workflow controller."""
        signal_coordinator.on_save_as_workflow()
        mock_main_window._workflow_controller.save_workflow_as.assert_called_once()

    def test_on_save_as_scenario(self, signal_coordinator, mock_main_window):
        """on_save_as_scenario should emit signal."""
        signal_coordinator.on_save_as_scenario()
        mock_main_window.save_as_scenario_requested.emit.assert_called_once()


# ============================================================================
# Execution Actions Tests
# ============================================================================


class TestExecutionActions:
    """Tests for execution action handlers."""

    def test_on_run_workflow(self, signal_coordinator, mock_main_window):
        """on_run_workflow should delegate to execution controller."""
        signal_coordinator.on_run_workflow()
        mock_main_window._execution_controller.run_workflow.assert_called_once()

    def test_on_run_to_node(self, signal_coordinator, mock_main_window):
        """on_run_to_node should delegate to execution controller."""
        signal_coordinator.on_run_to_node()
        mock_main_window._execution_controller.run_to_node.assert_called_once()

    def test_on_run_single_node(self, signal_coordinator, mock_main_window):
        """on_run_single_node should delegate to execution controller."""
        signal_coordinator.on_run_single_node()
        mock_main_window._execution_controller.run_single_node.assert_called_once()

    def test_on_run_all_workflows(self, signal_coordinator, mock_main_window):
        """on_run_all_workflows should delegate to execution controller."""
        signal_coordinator.on_run_all_workflows()
        mock_main_window._execution_controller.run_all_workflows.assert_called_once()

    def test_on_pause_workflow(self, signal_coordinator, mock_main_window):
        """on_pause_workflow should toggle pause state."""
        signal_coordinator.on_pause_workflow(True)
        mock_main_window._execution_controller.toggle_pause.assert_called_once_with(
            True
        )

    def test_on_stop_workflow(self, signal_coordinator, mock_main_window):
        """on_stop_workflow should delegate to execution controller."""
        signal_coordinator.on_stop_workflow()
        mock_main_window._execution_controller.stop_workflow.assert_called_once()

    def test_on_restart_workflow(self, signal_coordinator, mock_main_window):
        """on_restart_workflow should delegate to execution controller."""
        signal_coordinator.on_restart_workflow()
        mock_main_window._execution_controller.restart_workflow.assert_called_once()

    def test_on_start_listening(self, signal_coordinator, mock_main_window):
        """on_start_listening should start trigger listening."""
        signal_coordinator.on_start_listening()
        mock_main_window._execution_controller.start_trigger_listening.assert_called_once()

    def test_on_stop_listening(self, signal_coordinator, mock_main_window):
        """on_stop_listening should stop trigger listening."""
        signal_coordinator.on_stop_listening()
        mock_main_window._execution_controller.stop_trigger_listening.assert_called_once()


# ============================================================================
# Debug Actions Tests
# ============================================================================


class TestDebugActions:
    """Tests for debug action handlers."""

    def test_on_debug_workflow(self, signal_coordinator, mock_main_window):
        """on_debug_workflow should delegate to execution controller."""
        signal_coordinator.on_debug_workflow()
        mock_main_window._execution_controller.debug_workflow.assert_called_once()

    def test_on_debug_mode_toggled_enabled(self, signal_coordinator, mock_main_window):
        """on_debug_mode_toggled should enable debug mode."""
        signal_coordinator.on_debug_mode_toggled(True)
        mock_main_window._execution_controller.set_debug_mode.assert_called_once_with(
            True
        )
        mock_main_window._debug_panel.show.assert_called_once()

    def test_on_debug_mode_toggled_disabled(self, signal_coordinator, mock_main_window):
        """on_debug_mode_toggled should disable debug mode."""
        signal_coordinator.on_debug_mode_toggled(False)
        mock_main_window._execution_controller.set_debug_mode.assert_called_once_with(
            False
        )
        mock_main_window._debug_panel.hide.assert_called_once()

    def test_on_debug_step_over(self, signal_coordinator, mock_main_window):
        """on_debug_step_over should delegate to execution controller."""
        signal_coordinator.on_debug_step_over()
        mock_main_window._execution_controller.step_over.assert_called_once()

    def test_on_debug_step_into(self, signal_coordinator, mock_main_window):
        """on_debug_step_into should delegate to execution controller."""
        signal_coordinator.on_debug_step_into()
        mock_main_window._execution_controller.step_into.assert_called_once()

    def test_on_debug_step_out(self, signal_coordinator, mock_main_window):
        """on_debug_step_out should delegate to execution controller."""
        signal_coordinator.on_debug_step_out()
        mock_main_window._execution_controller.step_out.assert_called_once()

    def test_on_debug_continue(self, signal_coordinator, mock_main_window):
        """on_debug_continue should delegate to execution controller."""
        signal_coordinator.on_debug_continue()
        mock_main_window._execution_controller.continue_execution.assert_called_once()

    def test_on_toggle_breakpoint(self, signal_coordinator, mock_main_window):
        """on_toggle_breakpoint should toggle breakpoint on selected node."""
        mock_main_window._node_controller.get_selected_nodes.return_value = ["node_1"]
        signal_coordinator.on_toggle_breakpoint()
        mock_main_window._execution_controller.toggle_breakpoint.assert_called_once_with(
            "node_1"
        )

    def test_on_toggle_breakpoint_no_selection(
        self, signal_coordinator, mock_main_window
    ):
        """on_toggle_breakpoint should do nothing with no selection."""
        mock_main_window._node_controller.get_selected_nodes.return_value = []
        signal_coordinator.on_toggle_breakpoint()
        mock_main_window._execution_controller.toggle_breakpoint.assert_not_called()

    def test_on_clear_breakpoints(self, signal_coordinator, mock_main_window):
        """on_clear_breakpoints should delegate to execution controller."""
        signal_coordinator.on_clear_breakpoints()
        mock_main_window._execution_controller.clear_breakpoints.assert_called_once()


# ============================================================================
# Node Actions Tests
# ============================================================================


class TestNodeActions:
    """Tests for node action handlers."""

    def test_on_select_nearest_node(self, signal_coordinator, mock_main_window):
        """on_select_nearest_node should delegate to node controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_select_nearest_node()
            mock_main_window._node_controller.select_nearest_node.assert_called_once()

    def test_on_select_nearest_node_text_focused(
        self, signal_coordinator, mock_main_window
    ):
        """on_select_nearest_node should not fire when text widget focused."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=True
        ):
            signal_coordinator.on_select_nearest_node()
            mock_main_window._node_controller.select_nearest_node.assert_not_called()

    def test_on_toggle_collapse_nearest(self, signal_coordinator, mock_main_window):
        """on_toggle_collapse_nearest should delegate to node controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_toggle_collapse_nearest()
            mock_main_window._node_controller.toggle_collapse_nearest_node.assert_called_once()

    def test_on_toggle_disable_node(self, signal_coordinator, mock_main_window):
        """on_toggle_disable_node should delegate to node controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_toggle_disable_node()
            mock_main_window._node_controller.toggle_disable_node.assert_called_once()

    def test_on_disable_all_selected(self, signal_coordinator, mock_main_window):
        """on_disable_all_selected should delegate to node controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_disable_all_selected()
            mock_main_window._node_controller.disable_all_selected.assert_called_once()

    def test_on_get_exec_out(self, signal_coordinator, mock_main_window):
        """on_get_exec_out should delegate to node controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_get_exec_out()
            mock_main_window._node_controller.get_nearest_exec_out.assert_called_once()

    def test_on_find_node(self, signal_coordinator, mock_main_window):
        """on_find_node should delegate to node controller."""
        signal_coordinator.on_find_node()
        mock_main_window._node_controller.find_node.assert_called_once()


# ============================================================================
# View/UI Actions Tests
# ============================================================================


class TestViewActions:
    """Tests for view/UI action handlers."""

    def test_on_focus_view(self, signal_coordinator, mock_main_window):
        """on_focus_view should delegate to viewport controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_focus_view()
            mock_main_window._viewport_controller.focus_view.assert_called_once()

    def test_on_home_all(self, signal_coordinator, mock_main_window):
        """on_home_all should delegate to viewport controller."""
        with patch.object(
            signal_coordinator, "_is_text_widget_focused", return_value=False
        ):
            signal_coordinator.on_home_all()
            mock_main_window._viewport_controller.home_all.assert_called_once()

    def test_on_toggle_minimap_enabled(self, signal_coordinator, mock_main_window):
        """on_toggle_minimap should show minimap when enabled."""
        signal_coordinator.on_toggle_minimap(True)
        mock_main_window._viewport_controller.toggle_minimap.assert_called_once_with(
            True
        )

    def test_on_toggle_minimap_disabled(self, signal_coordinator, mock_main_window):
        """on_toggle_minimap should hide minimap when disabled."""
        signal_coordinator.on_toggle_minimap(False)
        mock_main_window._viewport_controller.toggle_minimap.assert_called_once_with(
            False
        )

    def test_on_create_frame(self, signal_coordinator, mock_main_window):
        """on_create_frame should delegate to viewport controller."""
        signal_coordinator.on_create_frame()
        mock_main_window._viewport_controller.create_frame.assert_called_once()

    def test_on_save_ui_layout(self, signal_coordinator, mock_main_window):
        """on_save_ui_layout should delegate to UI state controller."""
        signal_coordinator.on_save_ui_layout()
        mock_main_window._ui_state_controller.save_state.assert_called_once()
        mock_main_window.show_status.assert_called()


# ============================================================================
# Mode Toggle Tests
# ============================================================================


class TestModeToggles:
    """Tests for mode toggle handlers."""

    def test_on_toggle_auto_connect_enabled(self, signal_coordinator, mock_main_window):
        """on_toggle_auto_connect should enable auto-connect."""
        mock_main_window._central_widget.set_auto_connect_enabled = Mock()

        signal_coordinator.on_toggle_auto_connect(True)

        assert mock_main_window._auto_connect_enabled is True
        mock_main_window.show_status.assert_called()

    def test_on_toggle_auto_connect_disabled(
        self, signal_coordinator, mock_main_window
    ):
        """on_toggle_auto_connect should disable auto-connect."""
        signal_coordinator.on_toggle_auto_connect(False)

        assert mock_main_window._auto_connect_enabled is False

    def test_on_toggle_high_performance_mode(
        self, signal_coordinator, mock_main_window
    ):
        """on_toggle_high_performance_mode should set performance mode."""
        mock_main_window._central_widget.set_high_performance_mode = Mock()

        signal_coordinator.on_toggle_high_performance_mode(True)

        mock_main_window._central_widget.set_high_performance_mode.assert_called_once_with(
            True
        )
        mock_main_window.show_status.assert_called()

    def test_on_toggle_quick_node_mode(self, signal_coordinator, mock_main_window):
        """on_toggle_quick_node_mode should enable/disable quick node mode."""
        signal_coordinator.on_toggle_quick_node_mode(True)

        mock_main_window._quick_node_manager.set_enabled.assert_called_once_with(True)
        mock_main_window.show_status.assert_called()


# ============================================================================
# Menu Actions Tests
# ============================================================================


class TestMenuActions:
    """Tests for menu action handlers."""

    def test_on_preferences(self, signal_coordinator, mock_main_window):
        """on_preferences should delegate to menu controller."""
        signal_coordinator.on_preferences()
        mock_main_window._menu_controller.open_preferences.assert_called_once()

    def test_on_open_hotkey_manager(self, signal_coordinator, mock_main_window):
        """on_open_hotkey_manager should delegate to menu controller."""
        signal_coordinator.on_open_hotkey_manager()
        mock_main_window._menu_controller.open_hotkey_manager.assert_called_once()

    def test_on_open_performance_dashboard(self, signal_coordinator, mock_main_window):
        """on_open_performance_dashboard should delegate to menu controller."""
        signal_coordinator.on_open_performance_dashboard()
        mock_main_window._menu_controller.open_performance_dashboard.assert_called_once()

    def test_on_open_command_palette(self, signal_coordinator, mock_main_window):
        """on_open_command_palette should delegate to menu controller."""
        signal_coordinator.on_open_command_palette()
        mock_main_window._menu_controller.open_command_palette.assert_called_once()

    def test_on_open_recent_file(self, signal_coordinator, mock_main_window):
        """on_open_recent_file should delegate to menu controller."""
        signal_coordinator.on_open_recent_file("/path/to/file.json")
        mock_main_window._menu_controller.open_recent_file.assert_called_once_with(
            "/path/to/file.json"
        )

    def test_on_clear_recent_files(self, signal_coordinator, mock_main_window):
        """on_clear_recent_files should delegate to menu controller."""
        signal_coordinator.on_clear_recent_files()
        mock_main_window._menu_controller.clear_recent_files.assert_called_once()

    def test_on_about(self, signal_coordinator, mock_main_window):
        """on_about should delegate to menu controller."""
        signal_coordinator.on_about()
        mock_main_window._menu_controller.show_about_dialog.assert_called_once()

    def test_on_show_documentation(self, signal_coordinator, mock_main_window):
        """on_show_documentation should delegate to menu controller."""
        signal_coordinator.on_show_documentation()
        mock_main_window._menu_controller.show_documentation.assert_called_once()

    def test_on_show_keyboard_shortcuts(self, signal_coordinator, mock_main_window):
        """on_show_keyboard_shortcuts should delegate to menu controller."""
        signal_coordinator.on_show_keyboard_shortcuts()
        mock_main_window._menu_controller.show_keyboard_shortcuts.assert_called_once()

    def test_on_check_updates(self, signal_coordinator, mock_main_window):
        """on_check_updates should delegate to menu controller."""
        signal_coordinator.on_check_updates()
        mock_main_window._menu_controller.check_for_updates.assert_called_once()


# ============================================================================
# Selector/Picker Actions Tests
# ============================================================================


class TestSelectorActions:
    """Tests for selector/picker action handlers."""

    def test_on_pick_selector(self, signal_coordinator, mock_main_window):
        """on_pick_selector should delegate to pick_element."""
        signal_coordinator.on_pick_element = Mock()
        signal_coordinator.on_pick_selector()
        signal_coordinator.on_pick_element.assert_called_once()

    def test_on_pick_element(self, signal_coordinator, mock_main_window):
        """on_pick_element should show unified selector dialog."""
        signal_coordinator.on_pick_element()
        mock_main_window._selector_controller.show_unified_selector_dialog.assert_called_once()

    def test_on_pick_element_desktop(self, signal_coordinator, mock_main_window):
        """on_pick_element_desktop should show selector dialog in desktop mode."""
        signal_coordinator.on_pick_element_desktop()
        mock_main_window._selector_controller.show_unified_selector_dialog.assert_called_once()
        # Verify desktop mode was specified
        call_kwargs = mock_main_window._selector_controller.show_unified_selector_dialog.call_args[
            1
        ]
        assert call_kwargs.get("initial_mode") == "desktop"


# ============================================================================
# Project Management Tests
# ============================================================================


class TestProjectManagement:
    """Tests for project management action handlers."""

    def test_on_project_manager(self, signal_coordinator, mock_main_window):
        """on_project_manager should delegate to project controller."""
        signal_coordinator.on_project_manager()
        mock_main_window._project_controller.show_project_manager.assert_called_once()

    def test_on_project_opened(self, signal_coordinator, mock_main_window):
        """on_project_opened should load the project."""
        signal_coordinator.on_project_opened("project_123")
        mock_main_window._project_controller.load_project.assert_called_once_with(
            "project_123"
        )

    def test_on_fleet_dashboard(self, signal_coordinator, mock_main_window):
        """on_fleet_dashboard should open fleet dashboard."""
        signal_coordinator.on_fleet_dashboard()
        mock_main_window._fleet_dashboard_manager.open_dashboard.assert_called_once()


# ============================================================================
# Validation/Navigation Tests
# ============================================================================


class TestValidationNavigation:
    """Tests for validation and navigation action handlers."""

    def test_on_validate_workflow(self, signal_coordinator, mock_main_window):
        """on_validate_workflow should delegate to main window."""
        signal_coordinator.on_validate_workflow()
        mock_main_window.validate_current_workflow.assert_called_once()

    def test_on_validation_issue_clicked(self, signal_coordinator, mock_main_window):
        """on_validation_issue_clicked should navigate to node."""
        with patch.object(signal_coordinator, "_select_node_by_id") as mock_select:
            signal_coordinator.on_validation_issue_clicked("node:test_node_id")
            mock_select.assert_called_once_with("test_node_id")

    def test_on_validation_issue_clicked_invalid_location(
        self, signal_coordinator, mock_main_window
    ):
        """on_validation_issue_clicked should ignore non-node locations."""
        with patch.object(signal_coordinator, "_select_node_by_id") as mock_select:
            signal_coordinator.on_validation_issue_clicked("other:location")
            mock_select.assert_not_called()

    def test_on_navigate_to_node(self, signal_coordinator, mock_main_window):
        """on_navigate_to_node should select and navigate to node."""
        with patch.object(signal_coordinator, "_select_node_by_id") as mock_select:
            signal_coordinator.on_navigate_to_node("test_node_id")
            mock_select.assert_called_once_with("test_node_id")


# ============================================================================
# Property Panel Tests
# ============================================================================


class TestPropertyPanel:
    """Tests for property panel action handlers."""

    def test_on_property_panel_changed(self, signal_coordinator, mock_main_window):
        """on_property_panel_changed should mark workflow as modified."""
        mock_node = Mock()
        mock_node.get_property.return_value = "node_123"
        mock_casare_node = Mock()
        mock_casare_node.config = {}
        mock_node.get_casare_node.return_value = mock_casare_node
        mock_main_window.graph.all_nodes.return_value = [mock_node]

        signal_coordinator.on_property_panel_changed("node_123", "selector", "#btn")

        mock_main_window.set_modified.assert_called_once_with(True)

    def test_on_panel_variables_changed(self, signal_coordinator, mock_main_window):
        """on_panel_variables_changed should mark workflow as modified."""
        signal_coordinator.on_panel_variables_changed({"var1": "value1"})
        mock_main_window.set_modified.assert_called_once_with(True)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in callbacks."""

    def test_controller_none_does_not_raise(self, signal_coordinator, mock_main_window):
        """Methods should handle None controllers gracefully."""
        mock_main_window._workflow_controller = None
        mock_main_window._execution_controller = None
        mock_main_window._node_controller = None

        # These should not raise
        signal_coordinator.on_new_workflow()
        signal_coordinator.on_run_workflow()
        signal_coordinator.on_toggle_breakpoint()

    def test_save_ui_layout_no_controller(self, signal_coordinator, mock_main_window):
        """on_save_ui_layout should handle missing controller."""
        mock_main_window._ui_state_controller = None

        # Should not raise
        signal_coordinator.on_save_ui_layout()
