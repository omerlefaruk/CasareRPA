"""
Integration Tests for MainWindow Component Integration.

Tests the integration of:
- MainWindow with SignalCoordinator
- MainWindow with PanelManager
- Actions delegate correctly from MainWindow to SignalCoordinator
- Panel operations delegate to PanelManager

All Qt components are mocked to avoid requiring a display.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_qt_app():
    """Mock Qt application and widgets."""
    with patch.dict(
        "sys.modules",
        {
            "PySide6": MagicMock(),
            "PySide6.QtCore": MagicMock(),
            "PySide6.QtWidgets": MagicMock(),
            "PySide6.QtGui": MagicMock(),
        },
    ):
        yield


@pytest.fixture
def mock_main_window_deps(mocker):
    """Mock all MainWindow dependencies."""
    # Mock PySide6
    mock_qt_core = MagicMock()
    mock_qt_widgets = MagicMock()
    mock_qt_gui = MagicMock()

    # Create mock QMainWindow class
    mock_qmainwindow = MagicMock()
    mock_qt_widgets.QMainWindow = mock_qmainwindow

    # Create mock Signal
    mock_signal = MagicMock()
    mock_qt_core.Signal = mock_signal

    mocker.patch.dict(
        "sys.modules",
        {
            "PySide6": MagicMock(),
            "PySide6.QtCore": mock_qt_core,
            "PySide6.QtWidgets": mock_qt_widgets,
            "PySide6.QtGui": mock_qt_gui,
        },
    )

    return {
        "qt_core": mock_qt_core,
        "qt_widgets": mock_qt_widgets,
        "qt_gui": mock_qt_gui,
    }


@pytest.fixture
def signal_coordinator_mock():
    """Create a mock SignalCoordinator."""
    mock = MagicMock()

    # Workflow actions
    mock.on_new_workflow = MagicMock()
    mock.on_open_workflow = MagicMock()
    mock.on_save_workflow = MagicMock()
    mock.on_save_as_workflow = MagicMock()
    mock.on_import_workflow = MagicMock()
    mock.on_export_selected = MagicMock()
    mock.on_paste_workflow = MagicMock()

    # Execution actions
    mock.on_run_workflow = MagicMock()
    mock.on_pause_workflow = MagicMock()
    mock.on_stop_workflow = MagicMock()
    mock.on_restart_workflow = MagicMock()
    mock.on_run_to_node = MagicMock()
    mock.on_run_single_node = MagicMock()
    mock.on_run_all_workflows = MagicMock()

    # Debug actions
    mock.on_debug_workflow = MagicMock()
    mock.on_debug_mode_toggled = MagicMock()
    mock.on_debug_step_over = MagicMock()
    mock.on_debug_step_into = MagicMock()
    mock.on_debug_step_out = MagicMock()
    mock.on_debug_continue = MagicMock()
    mock.on_toggle_breakpoint = MagicMock()
    mock.on_clear_breakpoints = MagicMock()

    # Node actions
    mock.on_select_nearest_node = MagicMock()
    mock.on_toggle_collapse_nearest = MagicMock()
    mock.on_toggle_disable_node = MagicMock()
    mock.on_disable_all_selected = MagicMock()
    mock.on_rename_node = MagicMock()
    mock.on_get_exec_out = MagicMock()
    mock.on_find_node = MagicMock()

    # View actions
    mock.on_focus_view = MagicMock()
    mock.on_home_all = MagicMock()
    mock.on_toggle_minimap = MagicMock()
    mock.on_create_frame = MagicMock()
    mock.on_save_ui_layout = MagicMock()

    # Mode toggles
    mock.on_toggle_auto_connect = MagicMock()
    mock.on_toggle_high_performance_mode = MagicMock()
    mock.on_toggle_quick_node_mode = MagicMock()

    # Menu actions
    mock.on_preferences = MagicMock()
    mock.on_about = MagicMock()
    mock.on_show_documentation = MagicMock()
    mock.on_show_keyboard_shortcuts = MagicMock()
    mock.on_check_updates = MagicMock()
    mock.on_open_hotkey_manager = MagicMock()
    mock.on_open_performance_dashboard = MagicMock()
    mock.on_open_command_palette = MagicMock()

    # Selector/Picker actions
    mock.on_pick_selector = MagicMock()
    mock.on_pick_element = MagicMock()
    mock.on_pick_element_desktop = MagicMock()

    # Recording actions
    mock.on_toggle_browser_recording = MagicMock()

    # Project management
    mock.on_project_manager = MagicMock()
    mock.on_fleet_dashboard = MagicMock()

    # Validation
    mock.on_validate_workflow = MagicMock()
    mock.on_validation_issue_clicked = MagicMock()
    mock.on_navigate_to_node = MagicMock()

    return mock


@pytest.fixture
def panel_manager_mock():
    """Create a mock PanelManager."""
    mock = MagicMock()

    # Bottom panel
    mock.bottom_panel = MagicMock()
    mock.get_bottom_panel = MagicMock(return_value=MagicMock())
    mock.show_bottom_panel = MagicMock()
    mock.hide_bottom_panel = MagicMock()
    mock.toggle_bottom_panel = MagicMock()
    mock.toggle_panel_tab = MagicMock()

    # Side panel
    mock.side_panel = MagicMock()
    mock.get_side_panel = MagicMock(return_value=MagicMock())
    mock.show_side_panel = MagicMock()
    mock.hide_side_panel = MagicMock()
    mock.toggle_side_panel = MagicMock()
    mock.show_debug_tab = MagicMock()
    mock.show_analytics_tab = MagicMock()
    mock.show_process_mining_tab = MagicMock()
    mock.show_robot_picker_tab = MagicMock()

    # Specific panels
    mock.validation_panel = MagicMock()
    mock.get_validation_panel = MagicMock(return_value=MagicMock())
    mock.show_validation_panel = MagicMock()
    mock.hide_validation_panel = MagicMock()
    mock.log_viewer = MagicMock()
    mock.get_log_viewer = MagicMock(return_value=MagicMock())
    mock.show_log_viewer = MagicMock()
    mock.hide_log_viewer = MagicMock()
    mock.show_execution_history = MagicMock()
    mock.get_execution_history_viewer = MagicMock(return_value=MagicMock())
    mock.debug_panel = MagicMock()
    mock.get_debug_panel = MagicMock(return_value=MagicMock())

    # Status
    mock.update_status_bar_buttons = MagicMock()
    mock.is_bottom_panel_visible = MagicMock(return_value=True)
    mock.is_side_panel_visible = MagicMock(return_value=False)
    mock.get_active_bottom_tab = MagicMock(return_value="log")
    mock.get_active_side_tab = MagicMock(return_value=None)

    return mock


# =============================================================================
# SIGNAL COORDINATOR INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestSignalCoordinatorIntegration:
    """Tests for SignalCoordinator integration with MainWindow."""

    def test_signal_coordinator_initialization(self, signal_coordinator_mock):
        """Test SignalCoordinator accepts MainWindow reference."""
        # Create mock main window
        main_window = MagicMock()

        # Import and test real SignalCoordinator
        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)
            assert coordinator._mw is main_window

        except ImportError:
            # Qt not available, use mock
            pytest.skip("Qt/SignalCoordinator not available")

    def test_workflow_actions_delegate_to_controller(self, signal_coordinator_mock):
        """Test workflow actions delegate to workflow controller."""
        main_window = MagicMock()
        main_window._workflow_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Test new workflow
            coordinator.on_new_workflow()
            main_window._workflow_controller.new_workflow.assert_called_once()

            # Test open workflow
            coordinator.on_open_workflow()
            main_window._workflow_controller.open_workflow.assert_called_once()

            # Test save workflow
            coordinator.on_save_workflow()
            main_window._workflow_controller.save_workflow.assert_called_once()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_execution_actions_delegate_to_controller(self, signal_coordinator_mock):
        """Test execution actions delegate to execution controller."""
        main_window = MagicMock()
        main_window._execution_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Test run workflow
            coordinator.on_run_workflow()
            main_window._execution_controller.run_workflow.assert_called_once()

            # Test stop workflow
            coordinator.on_stop_workflow()
            main_window._execution_controller.stop_workflow.assert_called_once()

            # Test pause workflow
            coordinator.on_pause_workflow(True)
            main_window._execution_controller.toggle_pause.assert_called_with(True)

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_node_actions_delegate_to_controller(self, signal_coordinator_mock):
        """Test node actions delegate to node controller."""
        main_window = MagicMock()
        main_window._node_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            # Mock QApplication.focusWidget to return None (not text widget)
            with patch(
                "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QApplication"
            ) as mock_qapp:
                mock_qapp.focusWidget.return_value = None

                coordinator = SignalCoordinator(main_window)

                # Test select nearest
                coordinator.on_select_nearest_node()
                main_window._node_controller.select_nearest_node.assert_called_once()

                # Test toggle collapse
                coordinator.on_toggle_collapse_nearest()
                main_window._node_controller.toggle_collapse_nearest_node.assert_called_once()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_menu_actions_delegate_to_controller(self, signal_coordinator_mock):
        """Test menu actions delegate to menu controller."""
        main_window = MagicMock()
        main_window._menu_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Test preferences
            coordinator.on_preferences()
            main_window._menu_controller.open_preferences.assert_called_once()

            # Test about
            coordinator.on_about()
            main_window._menu_controller.show_about_dialog.assert_called_once()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_text_widget_focus_suppresses_hotkeys(self, signal_coordinator_mock):
        """Test hotkeys are suppressed when text widget has focus."""
        main_window = MagicMock()
        main_window._node_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )
            from PySide6.QtWidgets import QLineEdit

            # Mock QApplication.focusWidget to return text widget
            with patch(
                "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QApplication"
            ) as mock_qapp:
                mock_qapp.focusWidget.return_value = MagicMock(spec=QLineEdit)

                coordinator = SignalCoordinator(main_window)

                # Node action should NOT be called when text widget focused
                coordinator.on_select_nearest_node()
                main_window._node_controller.select_nearest_node.assert_not_called()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_selector_actions_delegate_to_controller(self, signal_coordinator_mock):
        """Test selector actions delegate to selector controller."""
        main_window = MagicMock()
        main_window._selector_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Test pick element (browser)
            coordinator.on_pick_element()
            main_window._selector_controller.show_unified_selector_dialog.assert_called()

            # Reset mock
            main_window._selector_controller.reset_mock()

            # Test pick element (desktop)
            coordinator.on_pick_element_desktop()
            main_window._selector_controller.show_unified_selector_dialog.assert_called()
            # Verify desktop mode was requested
            call_kwargs = main_window._selector_controller.show_unified_selector_dialog.call_args.kwargs
            assert call_kwargs.get("initial_mode") == "desktop"

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")


# =============================================================================
# PANEL MANAGER INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestPanelManagerIntegration:
    """Tests for PanelManager integration with MainWindow."""

    def test_panel_manager_initialization(self, panel_manager_mock):
        """Test PanelManager accepts MainWindow reference."""
        main_window = MagicMock()

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)
            assert manager._mw is main_window

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_bottom_panel_operations(self, panel_manager_mock):
        """Test bottom panel show/hide/toggle operations."""
        main_window = MagicMock()
        main_window._bottom_panel = MagicMock()
        main_window._panel_controller = None

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Show
            manager.show_bottom_panel()
            main_window._bottom_panel.show.assert_called()

            # Hide
            manager.hide_bottom_panel()
            main_window._bottom_panel.hide.assert_called()

            # Toggle True
            main_window._bottom_panel.reset_mock()
            manager.toggle_bottom_panel(True)
            main_window._bottom_panel.show.assert_called()

            # Toggle False
            main_window._bottom_panel.reset_mock()
            manager.toggle_bottom_panel(False)
            main_window._bottom_panel.hide.assert_called()

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_bottom_panel_tab_operations(self, panel_manager_mock):
        """Test bottom panel tab switching."""
        main_window = MagicMock()
        main_window._bottom_panel = MagicMock()
        main_window._panel_controller = None

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Toggle to variables tab
            main_window._bottom_panel.show_variables_tab = MagicMock()
            manager.toggle_panel_tab("variables")
            main_window._bottom_panel.show_variables_tab.assert_called()
            main_window._bottom_panel.show.assert_called()

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_side_panel_operations(self, panel_manager_mock):
        """Test side panel show/hide operations."""
        main_window = MagicMock()
        main_window._side_panel = MagicMock()

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Show
            manager.show_side_panel()
            main_window._side_panel.show.assert_called()

            # Hide
            manager.hide_side_panel()
            main_window._side_panel.hide.assert_called()

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_side_panel_tab_operations(self, panel_manager_mock):
        """Test side panel tab switching."""
        main_window = MagicMock()
        main_window._side_panel = MagicMock()

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Show debug tab
            manager.show_debug_tab()
            main_window._side_panel.show_debug_tab.assert_called()

            # Show analytics tab
            manager.show_analytics_tab()
            main_window._side_panel.show_analytics_tab.assert_called()

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_panel_visibility_checks(self, panel_manager_mock):
        """Test panel visibility status checks."""
        main_window = MagicMock()
        main_window._bottom_panel = MagicMock()
        main_window._side_panel = MagicMock()
        main_window._bottom_panel.isVisible.return_value = True
        main_window._side_panel.isVisible.return_value = False

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            assert manager.is_bottom_panel_visible() is True
            assert manager.is_side_panel_visible() is False

        except ImportError:
            pytest.skip("Qt/PanelManager not available")

    def test_panel_manager_delegates_to_controller(self, panel_manager_mock):
        """Test PanelManager delegates to PanelController when available."""
        main_window = MagicMock()
        main_window._panel_controller = MagicMock()
        main_window._status_bar_manager = MagicMock()

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Should delegate to controller
            manager.show_bottom_panel()
            main_window._panel_controller.show_bottom_panel.assert_called()

            # Toggle tab should also delegate
            manager.toggle_panel_tab("log")
            main_window._panel_controller.toggle_panel_tab.assert_called_with("log")

        except ImportError:
            pytest.skip("Qt/PanelManager not available")


# =============================================================================
# MAINWINDOW INITIALIZATION TESTS
# =============================================================================


@pytest.mark.integration
class TestMainWindowInitialization:
    """Tests for MainWindow initialization sequence."""

    def test_main_window_creates_coordinators(self):
        """Test MainWindow creates SignalCoordinator and PanelManager."""
        try:
            # We can't actually instantiate MainWindow without Qt
            # Instead, verify the class has the expected attributes
            from casare_rpa.presentation.canvas.main_window import MainWindow

            # Check class definition includes coordinator/manager creation
            import inspect

            source = inspect.getsource(MainWindow.__init__)

            assert "SignalCoordinator" in source
            assert "PanelManager" in source
            assert "_signal_coordinator" in source
            assert "_panel_manager" in source

        except ImportError:
            pytest.skip("Qt/MainWindow not available")

    def test_main_window_has_expected_signals(self):
        """Test MainWindow defines expected signals."""
        try:
            from casare_rpa.presentation.canvas.main_window import MainWindow

            # Check class has signal attributes (as class-level descriptors)
            expected_signals = [
                "workflow_new",
                "workflow_open",
                "workflow_save",
                "workflow_save_as",
                "workflow_run",
                "workflow_pause",
                "workflow_resume",
                "workflow_stop",
            ]

            for signal_name in expected_signals:
                assert hasattr(
                    MainWindow, signal_name
                ), f"Missing signal: {signal_name}"

        except ImportError:
            pytest.skip("Qt/MainWindow not available")

    def test_main_window_has_component_managers(self):
        """Test MainWindow creates component managers."""
        try:
            from casare_rpa.presentation.canvas.main_window import MainWindow

            import inspect

            source = inspect.getsource(MainWindow.__init__)

            # Check component managers are created
            expected_managers = [
                "ActionManager",
                "MenuBuilder",
                "ToolbarBuilder",
                "StatusBarManager",
                "DockCreator",
            ]

            for manager in expected_managers:
                assert manager in source, f"Missing manager: {manager}"

        except ImportError:
            pytest.skip("Qt/MainWindow not available")


# =============================================================================
# ACTION DELEGATION TESTS
# =============================================================================


@pytest.mark.integration
class TestActionDelegation:
    """Tests for action delegation from MainWindow to coordinators."""

    def test_workflow_action_flow(self):
        """Test complete workflow action flow."""
        # This tests the expected integration pattern:
        # User clicks action -> ActionManager triggers -> SignalCoordinator handles -> Controller executes

        main_window = MagicMock()
        main_window._workflow_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Simulate action trigger
            coordinator.on_new_workflow()

            # Verify controller was called
            main_window._workflow_controller.new_workflow.assert_called_once()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_execution_action_flow(self):
        """Test complete execution action flow."""
        main_window = MagicMock()
        main_window._execution_controller = MagicMock()

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Run
            coordinator.on_run_workflow()
            main_window._execution_controller.run_workflow.assert_called_once()

            # Stop
            coordinator.on_stop_workflow()
            main_window._execution_controller.stop_workflow.assert_called_once()

            # Debug
            coordinator.on_debug_workflow()
            main_window._execution_controller.debug_workflow.assert_called_once()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_panel_action_flow(self):
        """Test panel action delegates to PanelManager."""
        main_window = MagicMock()
        main_window._bottom_panel = MagicMock()
        main_window._side_panel = MagicMock()
        main_window._panel_controller = None

        try:
            from casare_rpa.presentation.canvas.managers.panel_manager import (
                PanelManager,
            )

            manager = PanelManager(main_window)

            # Verify panel operations work
            manager.show_bottom_panel()
            main_window._bottom_panel.show.assert_called()

            manager.show_side_panel()
            main_window._side_panel.show.assert_called()

        except ImportError:
            pytest.skip("Qt/PanelManager not available")


# =============================================================================
# CONTROLLER NULL SAFETY TESTS
# =============================================================================


@pytest.mark.integration
class TestControllerNullSafety:
    """Tests that SignalCoordinator handles missing controllers gracefully."""

    def test_missing_workflow_controller(self):
        """Test actions handle missing workflow controller."""
        main_window = MagicMock()
        main_window._workflow_controller = None

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Should not raise
            coordinator.on_new_workflow()
            coordinator.on_open_workflow()
            coordinator.on_save_workflow()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_missing_execution_controller(self):
        """Test actions handle missing execution controller."""
        main_window = MagicMock()
        main_window._execution_controller = None

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Should not raise
            coordinator.on_run_workflow()
            coordinator.on_stop_workflow()
            coordinator.on_pause_workflow(True)

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_missing_node_controller(self):
        """Test actions handle missing node controller."""
        main_window = MagicMock()
        main_window._node_controller = None

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            with patch(
                "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QApplication"
            ) as mock_qapp:
                mock_qapp.focusWidget.return_value = None

                coordinator = SignalCoordinator(main_window)

                # Should not raise
                coordinator.on_select_nearest_node()
                coordinator.on_toggle_collapse_nearest()
                coordinator.on_toggle_disable_node()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")

    def test_missing_menu_controller(self):
        """Test actions handle missing menu controller."""
        main_window = MagicMock()
        main_window._menu_controller = None

        try:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(main_window)

            # Should not raise
            coordinator.on_preferences()
            coordinator.on_about()

        except ImportError:
            pytest.skip("Qt/SignalCoordinator not available")
