"""
Tests for PanelManager.

Tests cover:
- Panel show/hide toggles
- Tab switching
- Panel access methods
- Bottom panel operations
- Side panel operations
- Status bar button state updates

Note: These tests mock all Qt dependencies to avoid Qt initialization issues.
The pytest-qt plugin is disabled for this module.
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock, patch

# Mark entire module to skip Qt processing
pytestmark = pytest.mark.qt_no_exception_capture


# Patch Qt modules before any imports that might load them
_qt_mock = MagicMock()

# Patch sys.modules before PanelManager is imported
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
    """Create a mock MainWindow with panel components."""
    mw = Mock()

    # Bottom panel
    mw._bottom_panel = Mock()
    mw._bottom_panel.show = Mock()
    mw._bottom_panel.hide = Mock()
    mw._bottom_panel.isVisible = Mock(return_value=True)
    mw._bottom_panel.show_variables_tab = Mock()
    mw._bottom_panel.show_output_tab = Mock()
    mw._bottom_panel.show_log_tab = Mock()
    mw._bottom_panel.show_validation_tab = Mock()
    mw._bottom_panel.show_history_tab = Mock()
    mw._bottom_panel.get_validation_tab = Mock(return_value=Mock())
    mw._bottom_panel.get_log_tab = Mock(return_value=Mock())
    mw._bottom_panel.get_history_tab = Mock(return_value=Mock())
    mw._bottom_panel.current_tab_name = Mock(return_value="variables")

    # Side panel
    mw._side_panel = Mock()
    mw._side_panel.show = Mock()
    mw._side_panel.hide = Mock()
    mw._side_panel.isVisible = Mock(return_value=False)
    mw._side_panel.show_debug_tab = Mock()
    mw._side_panel.show_analytics_tab = Mock()
    mw._side_panel.show_process_mining_tab = Mock()
    mw._side_panel.show_robot_picker_tab = Mock()
    mw._side_panel.current_tab_name = Mock(return_value="debug")

    # Other panel references
    mw._debug_panel = Mock()
    mw._process_mining_panel = Mock()
    mw._robot_picker_panel = Mock()
    mw._analytics_panel = Mock()

    # Controllers
    mw._panel_controller = Mock()
    mw._panel_controller.show_bottom_panel = Mock()
    mw._panel_controller.hide_bottom_panel = Mock()
    mw._panel_controller.toggle_panel_tab = Mock()

    # Status bar manager
    mw._status_bar_manager = Mock()
    mw._status_bar_manager.update_button_states = Mock()

    # Actions for toggle state
    mw.action_toggle_panel = Mock()
    mw.action_toggle_panel.setChecked = Mock()
    mw.action_toggle_side_panel = Mock()
    mw.action_toggle_side_panel.setChecked = Mock()

    return mw


@pytest.fixture
def panel_manager(mock_main_window, mock_qt):
    """Create a PanelManager with mocked MainWindow."""
    from casare_rpa.presentation.canvas.managers.panel_manager import PanelManager

    return PanelManager(mock_main_window)


# ============================================================================
# Bottom Panel Tests
# ============================================================================


class TestBottomPanel:
    """Tests for bottom panel operations."""

    def test_bottom_panel_property(self, panel_manager, mock_main_window):
        """bottom_panel property should return the bottom panel."""
        assert panel_manager.bottom_panel == mock_main_window._bottom_panel

    def test_get_bottom_panel_method(self, panel_manager, mock_main_window):
        """get_bottom_panel should return the bottom panel."""
        assert panel_manager.get_bottom_panel() == mock_main_window._bottom_panel

    def test_show_bottom_panel_with_controller(self, panel_manager, mock_main_window):
        """show_bottom_panel should delegate to panel controller."""
        panel_manager.show_bottom_panel()
        mock_main_window._panel_controller.show_bottom_panel.assert_called_once()

    def test_show_bottom_panel_without_controller(
        self, panel_manager, mock_main_window
    ):
        """show_bottom_panel should show panel directly if no controller."""
        mock_main_window._panel_controller = None
        panel_manager.show_bottom_panel()
        mock_main_window._bottom_panel.show.assert_called_once()

    def test_hide_bottom_panel_with_controller(self, panel_manager, mock_main_window):
        """hide_bottom_panel should delegate to panel controller."""
        panel_manager.hide_bottom_panel()
        mock_main_window._panel_controller.hide_bottom_panel.assert_called_once()

    def test_hide_bottom_panel_without_controller(
        self, panel_manager, mock_main_window
    ):
        """hide_bottom_panel should hide panel directly if no controller."""
        mock_main_window._panel_controller = None
        panel_manager.hide_bottom_panel()
        mock_main_window._bottom_panel.hide.assert_called_once()

    def test_toggle_bottom_panel_show(self, panel_manager):
        """toggle_bottom_panel(True) should show panel."""
        panel_manager.show_bottom_panel = Mock()
        panel_manager.toggle_bottom_panel(True)
        panel_manager.show_bottom_panel.assert_called_once()

    def test_toggle_bottom_panel_hide(self, panel_manager):
        """toggle_bottom_panel(False) should hide panel."""
        panel_manager.hide_bottom_panel = Mock()
        panel_manager.toggle_bottom_panel(False)
        panel_manager.hide_bottom_panel.assert_called_once()

    def test_is_bottom_panel_visible_true(self, panel_manager, mock_main_window):
        """is_bottom_panel_visible should return True when visible."""
        mock_main_window._bottom_panel.isVisible.return_value = True
        assert panel_manager.is_bottom_panel_visible() is True

    def test_is_bottom_panel_visible_false(self, panel_manager, mock_main_window):
        """is_bottom_panel_visible should return False when hidden."""
        mock_main_window._bottom_panel.isVisible.return_value = False
        assert panel_manager.is_bottom_panel_visible() is False

    def test_is_bottom_panel_visible_no_panel(self, panel_manager, mock_main_window):
        """is_bottom_panel_visible should return False when no panel."""
        mock_main_window._bottom_panel = None
        assert panel_manager.is_bottom_panel_visible() is False


# ============================================================================
# Side Panel Tests
# ============================================================================


class TestSidePanel:
    """Tests for side panel operations."""

    def test_side_panel_property(self, panel_manager, mock_main_window):
        """side_panel property should return the side panel."""
        assert panel_manager.side_panel == mock_main_window._side_panel

    def test_get_side_panel_method(self, panel_manager, mock_main_window):
        """get_side_panel should return the side panel."""
        assert panel_manager.get_side_panel() == mock_main_window._side_panel

    def test_show_side_panel(self, panel_manager, mock_main_window):
        """show_side_panel should show the side panel."""
        panel_manager.show_side_panel()
        mock_main_window._side_panel.show.assert_called_once()

    def test_hide_side_panel(self, panel_manager, mock_main_window):
        """hide_side_panel should hide the side panel."""
        panel_manager.hide_side_panel()
        mock_main_window._side_panel.hide.assert_called_once()

    def test_toggle_side_panel_show(self, panel_manager):
        """toggle_side_panel(True) should show panel."""
        panel_manager.show_side_panel = Mock()
        panel_manager.toggle_side_panel(True)
        panel_manager.show_side_panel.assert_called_once()

    def test_toggle_side_panel_hide(self, panel_manager):
        """toggle_side_panel(False) should hide panel."""
        panel_manager.hide_side_panel = Mock()
        panel_manager.toggle_side_panel(False)
        panel_manager.hide_side_panel.assert_called_once()

    def test_is_side_panel_visible_true(self, panel_manager, mock_main_window):
        """is_side_panel_visible should return True when visible."""
        mock_main_window._side_panel.isVisible.return_value = True
        assert panel_manager.is_side_panel_visible() is True

    def test_is_side_panel_visible_false(self, panel_manager, mock_main_window):
        """is_side_panel_visible should return False when hidden."""
        mock_main_window._side_panel.isVisible.return_value = False
        assert panel_manager.is_side_panel_visible() is False

    def test_is_side_panel_visible_no_panel(self, panel_manager, mock_main_window):
        """is_side_panel_visible should return False when no panel."""
        mock_main_window._side_panel = None
        assert panel_manager.is_side_panel_visible() is False


# ============================================================================
# Side Panel Tab Tests
# ============================================================================


class TestSidePanelTabs:
    """Tests for side panel tab switching."""

    def test_show_debug_tab(self, panel_manager, mock_main_window):
        """show_debug_tab should show debug tab and panel."""
        panel_manager.show_debug_tab()
        mock_main_window._side_panel.show_debug_tab.assert_called_once()

    def test_show_analytics_tab(self, panel_manager, mock_main_window):
        """show_analytics_tab should show analytics tab and panel."""
        panel_manager.show_analytics_tab()
        mock_main_window._side_panel.show_analytics_tab.assert_called_once()

    def test_show_process_mining_tab(self, panel_manager, mock_main_window):
        """show_process_mining_tab should show process mining tab and panel."""
        panel_manager.show_process_mining_tab()
        mock_main_window._side_panel.show_process_mining_tab.assert_called_once()

    def test_show_robot_picker_tab(self, panel_manager, mock_main_window):
        """show_robot_picker_tab should show robot picker tab and panel."""
        panel_manager.show_robot_picker_tab()
        mock_main_window._side_panel.show_robot_picker_tab.assert_called_once()


# ============================================================================
# Tab Switching Tests
# ============================================================================


class TestTabSwitching:
    """Tests for bottom panel tab switching."""

    def test_toggle_panel_tab_with_controller(self, panel_manager, mock_main_window):
        """toggle_panel_tab should delegate to panel controller."""
        panel_manager.toggle_panel_tab("variables")
        mock_main_window._panel_controller.toggle_panel_tab.assert_called_once_with(
            "variables"
        )
        mock_main_window._status_bar_manager.update_button_states.assert_called_once()

    def test_toggle_panel_tab_without_controller(self, panel_manager, mock_main_window):
        """toggle_panel_tab should call tab method directly if no controller."""
        mock_main_window._panel_controller = None
        panel_manager.toggle_panel_tab("variables")
        mock_main_window._bottom_panel.show_variables_tab.assert_called_once()
        mock_main_window._bottom_panel.show.assert_called_once()

    def test_toggle_panel_tab_output(self, panel_manager, mock_main_window):
        """toggle_panel_tab('output') should show output tab."""
        mock_main_window._panel_controller = None
        panel_manager.toggle_panel_tab("output")
        mock_main_window._bottom_panel.show_output_tab.assert_called_once()

    def test_toggle_panel_tab_log(self, panel_manager, mock_main_window):
        """toggle_panel_tab('log') should show log tab."""
        mock_main_window._panel_controller = None
        panel_manager.toggle_panel_tab("log")
        mock_main_window._bottom_panel.show_log_tab.assert_called_once()

    def test_toggle_panel_tab_validation(self, panel_manager, mock_main_window):
        """toggle_panel_tab('validation') should show validation tab."""
        mock_main_window._panel_controller = None
        panel_manager.toggle_panel_tab("validation")
        mock_main_window._bottom_panel.show_validation_tab.assert_called_once()

    def test_toggle_panel_tab_history(self, panel_manager, mock_main_window):
        """toggle_panel_tab('history') should show history tab."""
        mock_main_window._panel_controller = None
        panel_manager.toggle_panel_tab("history")
        mock_main_window._bottom_panel.show_history_tab.assert_called_once()

    def test_get_active_bottom_tab(self, panel_manager, mock_main_window):
        """get_active_bottom_tab should return current tab name."""
        mock_main_window._bottom_panel.current_tab_name.return_value = "log"
        assert panel_manager.get_active_bottom_tab() == "log"

    def test_get_active_bottom_tab_no_panel(self, panel_manager, mock_main_window):
        """get_active_bottom_tab should return None when no panel."""
        mock_main_window._bottom_panel = None
        assert panel_manager.get_active_bottom_tab() is None

    def test_get_active_side_tab(self, panel_manager, mock_main_window):
        """get_active_side_tab should return current tab name."""
        mock_main_window._side_panel.current_tab_name.return_value = "analytics"
        assert panel_manager.get_active_side_tab() == "analytics"

    def test_get_active_side_tab_no_panel(self, panel_manager, mock_main_window):
        """get_active_side_tab should return None when no panel."""
        mock_main_window._side_panel = None
        assert panel_manager.get_active_side_tab() is None


# ============================================================================
# Panel Access Tests
# ============================================================================


class TestPanelAccess:
    """Tests for panel access methods."""

    def test_validation_panel_property(self, panel_manager, mock_main_window):
        """validation_panel property should return validation tab."""
        result = panel_manager.validation_panel
        mock_main_window._bottom_panel.get_validation_tab.assert_called_once()
        assert result is not None

    def test_validation_panel_no_bottom_panel(self, panel_manager, mock_main_window):
        """validation_panel should return None if no bottom panel."""
        mock_main_window._bottom_panel = None
        assert panel_manager.validation_panel is None

    def test_get_validation_panel(self, panel_manager, mock_main_window):
        """get_validation_panel should return validation tab."""
        result = panel_manager.get_validation_panel()
        assert result is not None

    def test_show_validation_panel(self, panel_manager, mock_main_window):
        """show_validation_panel should show validation tab."""
        panel_manager.show_validation_panel()
        mock_main_window._bottom_panel.show_validation_tab.assert_called_once()

    def test_hide_validation_panel(self, panel_manager, mock_main_window):
        """hide_validation_panel should hide bottom panel."""
        panel_manager.hide_validation_panel()
        mock_main_window._bottom_panel.hide.assert_called_once()

    def test_log_viewer_property(self, panel_manager, mock_main_window):
        """log_viewer property should return log tab."""
        result = panel_manager.log_viewer
        mock_main_window._bottom_panel.get_log_tab.assert_called_once()
        assert result is not None

    def test_log_viewer_no_bottom_panel(self, panel_manager, mock_main_window):
        """log_viewer should return None if no bottom panel."""
        mock_main_window._bottom_panel = None
        assert panel_manager.log_viewer is None

    def test_get_log_viewer(self, panel_manager, mock_main_window):
        """get_log_viewer should return log tab."""
        result = panel_manager.get_log_viewer()
        assert result is not None

    def test_show_log_viewer(self, panel_manager, mock_main_window):
        """show_log_viewer should show log tab."""
        panel_manager.show_log_viewer()
        mock_main_window._bottom_panel.show_log_tab.assert_called_once()

    def test_hide_log_viewer(self, panel_manager, mock_main_window):
        """hide_log_viewer should hide bottom panel."""
        panel_manager.hide_log_viewer()
        mock_main_window._bottom_panel.hide.assert_called_once()

    def test_show_execution_history(self, panel_manager, mock_main_window):
        """show_execution_history should show history tab."""
        panel_manager.show_execution_history()
        mock_main_window._bottom_panel.show_history_tab.assert_called_once()

    def test_get_execution_history_viewer(self, panel_manager, mock_main_window):
        """get_execution_history_viewer should return history tab."""
        result = panel_manager.get_execution_history_viewer()
        mock_main_window._bottom_panel.get_history_tab.assert_called_once()
        assert result is not None

    def test_get_execution_history_viewer_no_panel(
        self, panel_manager, mock_main_window
    ):
        """get_execution_history_viewer should return None if no panel."""
        mock_main_window._bottom_panel = None
        assert panel_manager.get_execution_history_viewer() is None


# ============================================================================
# Debug Panel Access Tests
# ============================================================================


class TestDebugPanelAccess:
    """Tests for debug panel access."""

    def test_debug_panel_property(self, panel_manager, mock_main_window):
        """debug_panel property should return debug panel."""
        assert panel_manager.debug_panel == mock_main_window._debug_panel

    def test_get_debug_panel(self, panel_manager, mock_main_window):
        """get_debug_panel should return debug panel."""
        assert panel_manager.get_debug_panel() == mock_main_window._debug_panel

    def test_process_mining_panel_property(self, panel_manager, mock_main_window):
        """process_mining_panel property should return process mining panel."""
        assert (
            panel_manager.process_mining_panel == mock_main_window._process_mining_panel
        )

    def test_get_process_mining_panel(self, panel_manager, mock_main_window):
        """get_process_mining_panel should return process mining panel."""
        assert (
            panel_manager.get_process_mining_panel()
            == mock_main_window._process_mining_panel
        )

    def test_robot_picker_panel_property(self, panel_manager, mock_main_window):
        """robot_picker_panel property should return robot picker panel."""
        assert panel_manager.robot_picker_panel == mock_main_window._robot_picker_panel

    def test_get_robot_picker_panel(self, panel_manager, mock_main_window):
        """get_robot_picker_panel should return robot picker panel."""
        assert (
            panel_manager.get_robot_picker_panel()
            == mock_main_window._robot_picker_panel
        )

    def test_analytics_panel_property(self, panel_manager, mock_main_window):
        """analytics_panel property should return analytics panel."""
        assert panel_manager.analytics_panel == mock_main_window._analytics_panel

    def test_get_analytics_panel(self, panel_manager, mock_main_window):
        """get_analytics_panel should return analytics panel."""
        assert panel_manager.get_analytics_panel() == mock_main_window._analytics_panel


# ============================================================================
# Status Bar Button Tests
# ============================================================================


class TestStatusBarButtons:
    """Tests for status bar button state updates."""

    def test_update_status_bar_buttons(self, panel_manager, mock_main_window):
        """update_status_bar_buttons should delegate to status bar manager."""
        panel_manager.update_status_bar_buttons()
        mock_main_window._status_bar_manager.update_button_states.assert_called_once()


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_update_toggle_action_checked(self, panel_manager, mock_main_window):
        """_update_toggle_action should set action checked state."""
        panel_manager._update_toggle_action("action_toggle_panel", True)
        mock_main_window.action_toggle_panel.setChecked.assert_called_once_with(True)

    def test_update_toggle_action_unchecked(self, panel_manager, mock_main_window):
        """_update_toggle_action should set action unchecked state."""
        panel_manager._update_toggle_action("action_toggle_panel", False)
        mock_main_window.action_toggle_panel.setChecked.assert_called_once_with(False)

    def test_update_toggle_action_no_action(self, panel_manager, mock_main_window):
        """_update_toggle_action should handle missing action gracefully."""
        # Should not raise
        panel_manager._update_toggle_action("nonexistent_action", True)


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and null handling."""

    def test_bottom_panel_none(self, panel_manager, mock_main_window):
        """Methods should handle None bottom panel gracefully."""
        mock_main_window._bottom_panel = None
        mock_main_window._panel_controller = None

        # These should not raise
        panel_manager.show_bottom_panel()
        panel_manager.hide_bottom_panel()
        panel_manager.toggle_panel_tab("variables")

    def test_side_panel_none(self, panel_manager, mock_main_window):
        """Methods should handle None side panel gracefully."""
        mock_main_window._side_panel = None

        # These should not raise
        panel_manager.show_side_panel()
        panel_manager.hide_side_panel()
        panel_manager.show_debug_tab()
        panel_manager.show_analytics_tab()

    def test_panel_controller_none(self, panel_manager, mock_main_window):
        """Methods should work without panel controller."""
        mock_main_window._panel_controller = None

        # Should fall back to direct panel manipulation
        panel_manager.show_bottom_panel()
        mock_main_window._bottom_panel.show.assert_called()

    def test_status_bar_manager_called(self, panel_manager, mock_main_window):
        """toggle_panel_tab should update status bar."""
        panel_manager.toggle_panel_tab("log")
        mock_main_window._status_bar_manager.update_button_states.assert_called()
