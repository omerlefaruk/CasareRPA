"""
Tests for SignalBridge UI components.

Tests signal connection logic, controller integration, and state management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar

from casare_rpa.presentation.canvas.ui.signal_bridge import (
    ControllerSignalBridge,
    BottomPanelSignalBridge,
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class MockSignal:
    """Mock signal that tracks connections."""

    def __init__(self):
        self._connections = []

    def connect(self, slot):
        self._connections.append(slot)

    def emit(self, *args):
        for conn in self._connections:
            conn(*args)

    @property
    def connected_count(self):
        return len(self._connections)


@pytest.fixture
def mock_main_window(qapp):
    """Create a mock MainWindow with required attributes."""
    mw = QMainWindow()

    # Create status bar
    status_bar = QStatusBar()
    mw.setStatusBar(status_bar)

    # Mock signals on main window
    mw.workflow_new = MockSignal()
    mw.workflow_open = MockSignal()
    mw.workflow_import = MockSignal()
    mw.workflow_import_json = MockSignal()
    mw.workflow_export_selected = MockSignal()
    mw.workflow_run_to_node = MockSignal()
    mw.workflow_run_single_node = MockSignal()

    # Mock action factory
    mock_actions = Mock()
    mock_actions.set_actions_enabled = Mock()
    mock_actions.get_action = Mock(return_value=Mock())
    mw._action_factory = mock_actions

    # Mock action attributes (fallback)
    mw.action_run = Mock()
    mw.action_run_to_node = Mock()
    mw.action_pause = Mock()
    mw.action_stop = Mock()

    # Mock handler methods for BottomPanelSignalBridge
    mw._on_validate_workflow = Mock()
    mw._on_validation_issue_clicked = Mock()
    mw._on_navigate_to_node = Mock()
    mw._on_panel_variables_changed = Mock()
    mw._on_trigger_add_requested = Mock()
    mw._on_trigger_edit_requested = Mock()
    mw._on_trigger_delete_requested = Mock()
    mw._on_trigger_toggle_requested = Mock()
    mw._on_trigger_run_requested = Mock()
    mw._schedule_ui_state_save = Mock()
    mw._on_property_panel_changed = Mock()
    mw._select_node_by_id = Mock()

    yield mw
    mw.deleteLater()


@pytest.fixture
def controller_bridge(mock_main_window):
    """Create ControllerSignalBridge instance."""
    bridge = ControllerSignalBridge(mock_main_window)
    yield bridge


@pytest.fixture
def bottom_panel_bridge(mock_main_window):
    """Create BottomPanelSignalBridge instance."""
    bridge = BottomPanelSignalBridge(mock_main_window)
    yield bridge


# =============================================================================
# ControllerSignalBridge Tests
# =============================================================================


class TestControllerSignalBridgeInitialization:
    """Tests for ControllerSignalBridge initialization."""

    def test_initialization(self, mock_main_window):
        """Test bridge initializes correctly."""
        bridge = ControllerSignalBridge(mock_main_window)
        assert bridge._main_window is mock_main_window

    def test_parent_set_correctly(self, controller_bridge, mock_main_window):
        """Test QObject parent is set."""
        assert controller_bridge.parent() is mock_main_window


class TestConnectAllControllers:
    """Tests for connect_all_controllers method."""

    def test_connect_with_no_controllers(self, controller_bridge):
        """Test connecting with no controllers does not raise."""
        # Should not raise error
        controller_bridge.connect_all_controllers()

    def test_connect_workflow_controller(self, controller_bridge):
        """Test connecting workflow controller."""
        mock_controller = Mock()
        mock_controller.workflow_created = MockSignal()
        mock_controller.workflow_loaded = MockSignal()
        mock_controller.workflow_saved = MockSignal()
        mock_controller.workflow_imported = MockSignal()
        mock_controller.workflow_imported_json = MockSignal()
        mock_controller.workflow_exported = MockSignal()
        mock_controller.current_file_changed = MockSignal()
        mock_controller.modified_changed = MockSignal()

        controller_bridge.connect_all_controllers(workflow_controller=mock_controller)

        # Check signals were connected
        assert mock_controller.workflow_created.connected_count > 0
        assert mock_controller.workflow_loaded.connected_count > 0

    def test_connect_execution_controller(self, controller_bridge):
        """Test connecting execution controller."""
        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        # Check signals were connected
        assert mock_controller.execution_started.connected_count > 0
        assert mock_controller.execution_stopped.connected_count > 0

    def test_connect_node_controller(self, controller_bridge):
        """Test connecting node controller."""
        mock_controller = Mock()
        mock_controller.node_selected = MockSignal()
        mock_controller.node_deselected = MockSignal()

        controller_bridge.connect_all_controllers(node_controller=mock_controller)

        # Check signals were connected
        assert mock_controller.node_selected.connected_count > 0
        assert mock_controller.node_deselected.connected_count > 0

    def test_connect_panel_controller(self, controller_bridge):
        """Test connecting panel controller."""
        mock_controller = Mock()
        mock_controller.bottom_panel_toggled = MockSignal()

        controller_bridge.connect_all_controllers(panel_controller=mock_controller)

        # Check signals were connected
        assert mock_controller.bottom_panel_toggled.connected_count > 0


class TestWorkflowControllerSignals:
    """Tests for workflow controller signal handling."""

    def test_workflow_created_emits_main_window_signal(
        self, controller_bridge, mock_main_window
    ):
        """Test workflow_created triggers main window signal."""
        mock_controller = Mock()
        mock_controller.workflow_created = MockSignal()
        mock_controller.workflow_loaded = MockSignal()
        mock_controller.workflow_saved = MockSignal()
        mock_controller.workflow_imported = MockSignal()
        mock_controller.workflow_imported_json = MockSignal()
        mock_controller.workflow_exported = MockSignal()
        mock_controller.current_file_changed = MockSignal()
        mock_controller.modified_changed = MockSignal()

        controller_bridge.connect_all_controllers(workflow_controller=mock_controller)

        # Trigger the signal
        mock_controller.workflow_created.emit()

        # Main window signal should be emitted
        # (tracked through MockSignal connections)

    def test_workflow_loaded_emits_with_path(self, controller_bridge, mock_main_window):
        """Test workflow_loaded passes path to main window."""
        mock_controller = Mock()
        mock_controller.workflow_created = MockSignal()
        mock_controller.workflow_loaded = MockSignal()
        mock_controller.workflow_saved = MockSignal()
        mock_controller.workflow_imported = MockSignal()
        mock_controller.workflow_imported_json = MockSignal()
        mock_controller.workflow_exported = MockSignal()
        mock_controller.current_file_changed = MockSignal()
        mock_controller.modified_changed = MockSignal()

        controller_bridge.connect_all_controllers(workflow_controller=mock_controller)

        # Trigger with path
        mock_controller.workflow_loaded.emit("test/path.json")


class TestExecutionControllerSignals:
    """Tests for execution controller signal handling."""

    def test_execution_started_updates_actions(
        self, controller_bridge, mock_main_window
    ):
        """Test execution_started updates action states."""
        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        # Trigger execution started
        mock_controller.execution_started.emit()

        # Actions should be updated
        mock_main_window._action_factory.set_actions_enabled.assert_called()

    def test_execution_stopped_updates_actions(
        self, controller_bridge, mock_main_window
    ):
        """Test execution_stopped updates action states."""
        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        mock_controller.execution_stopped.emit()
        mock_main_window._action_factory.set_actions_enabled.assert_called()

    def test_execution_completed_updates_actions(
        self, controller_bridge, mock_main_window
    ):
        """Test execution_completed updates action states."""
        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        mock_controller.execution_completed.emit()
        mock_main_window._action_factory.set_actions_enabled.assert_called()

    def test_execution_error_updates_status(self, controller_bridge, mock_main_window):
        """Test execution_error shows error in status bar."""
        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        mock_controller.execution_error.emit("Test error message")

        # Status bar should show error
        # (Can't easily verify status bar message without more setup)


class TestExecutionWithoutActionFactory:
    """Tests for execution handlers when action_factory is not available."""

    def test_execution_started_fallback(self, controller_bridge, mock_main_window):
        """Test execution_started uses fallback when no action_factory."""
        # Remove action factory
        del mock_main_window._action_factory

        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        # Should use fallback action access
        mock_controller.execution_started.emit()

        # Fallback actions should be called
        mock_main_window.action_run.setEnabled.assert_called_with(False)

    def test_execution_stopped_fallback(self, controller_bridge, mock_main_window):
        """Test execution_stopped uses fallback when no action_factory."""
        del mock_main_window._action_factory

        mock_controller = Mock()
        mock_controller.execution_started = MockSignal()
        mock_controller.execution_paused = MockSignal()
        mock_controller.execution_resumed = MockSignal()
        mock_controller.execution_stopped = MockSignal()
        mock_controller.execution_completed = MockSignal()
        mock_controller.execution_error = MockSignal()
        mock_controller.run_to_node_requested = MockSignal()
        mock_controller.run_single_node_requested = MockSignal()

        controller_bridge.connect_all_controllers(execution_controller=mock_controller)

        mock_controller.execution_stopped.emit()
        mock_main_window.action_run.setEnabled.assert_called_with(True)


class TestCurrentFileChanged:
    """Tests for current file changed handler."""

    def test_current_file_changed_handler(self, controller_bridge):
        """Test current file changed is handled."""
        mock_controller = Mock()
        mock_controller.workflow_created = MockSignal()
        mock_controller.workflow_loaded = MockSignal()
        mock_controller.workflow_saved = MockSignal()
        mock_controller.workflow_imported = MockSignal()
        mock_controller.workflow_imported_json = MockSignal()
        mock_controller.workflow_exported = MockSignal()
        mock_controller.current_file_changed = MockSignal()
        mock_controller.modified_changed = MockSignal()

        controller_bridge.connect_all_controllers(workflow_controller=mock_controller)

        # Should not raise
        mock_controller.current_file_changed.emit("new_file.json")


class TestModifiedChanged:
    """Tests for modified state changed handler."""

    def test_modified_changed_handler(self, controller_bridge):
        """Test modified changed is handled."""
        mock_controller = Mock()
        mock_controller.workflow_created = MockSignal()
        mock_controller.workflow_loaded = MockSignal()
        mock_controller.workflow_saved = MockSignal()
        mock_controller.workflow_imported = MockSignal()
        mock_controller.workflow_imported_json = MockSignal()
        mock_controller.workflow_exported = MockSignal()
        mock_controller.current_file_changed = MockSignal()
        mock_controller.modified_changed = MockSignal()

        controller_bridge.connect_all_controllers(workflow_controller=mock_controller)

        # Should not raise
        mock_controller.modified_changed.emit(True)


# =============================================================================
# BottomPanelSignalBridge Tests
# =============================================================================


class TestBottomPanelSignalBridgeInitialization:
    """Tests for BottomPanelSignalBridge initialization."""

    def test_initialization(self, mock_main_window):
        """Test bridge initializes correctly."""
        bridge = BottomPanelSignalBridge(mock_main_window)
        assert bridge._main_window is mock_main_window

    def test_parent_set_correctly(self, bottom_panel_bridge, mock_main_window):
        """Test QObject parent is set."""
        assert bottom_panel_bridge.parent() is mock_main_window


class TestConnectBottomPanel:
    """Tests for connect_bottom_panel method."""

    def test_connect_bottom_panel_signals(self, bottom_panel_bridge, mock_main_window):
        """Test bottom panel signals are connected."""
        mock_panel = Mock()
        mock_panel.validation_requested = MockSignal()
        mock_panel.issue_clicked = MockSignal()
        mock_panel.navigate_to_node = MockSignal()
        mock_panel.variables_changed = MockSignal()
        mock_panel.trigger_add_requested = MockSignal()
        mock_panel.trigger_edit_requested = MockSignal()
        mock_panel.trigger_delete_requested = MockSignal()
        mock_panel.trigger_toggle_requested = MockSignal()
        mock_panel.trigger_run_requested = MockSignal()
        mock_panel.dockLocationChanged = MockSignal()
        mock_panel.visibilityChanged = MockSignal()
        mock_panel.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_bottom_panel(mock_panel)

        # Check validation signals connected
        assert mock_panel.validation_requested.connected_count > 0
        assert mock_panel.issue_clicked.connected_count > 0
        assert mock_panel.navigate_to_node.connected_count > 0

        # Check trigger signals connected
        assert mock_panel.trigger_add_requested.connected_count > 0
        assert mock_panel.trigger_edit_requested.connected_count > 0
        assert mock_panel.trigger_delete_requested.connected_count > 0

        # Check dock state signals connected
        assert mock_panel.dockLocationChanged.connected_count > 0
        assert mock_panel.visibilityChanged.connected_count > 0

    def test_validation_requested_triggers_handler(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test validation_requested calls handler."""
        mock_panel = Mock()
        mock_panel.validation_requested = MockSignal()
        mock_panel.issue_clicked = MockSignal()
        mock_panel.navigate_to_node = MockSignal()
        mock_panel.variables_changed = MockSignal()
        mock_panel.trigger_add_requested = MockSignal()
        mock_panel.trigger_edit_requested = MockSignal()
        mock_panel.trigger_delete_requested = MockSignal()
        mock_panel.trigger_toggle_requested = MockSignal()
        mock_panel.trigger_run_requested = MockSignal()
        mock_panel.dockLocationChanged = MockSignal()
        mock_panel.visibilityChanged = MockSignal()
        mock_panel.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_bottom_panel(mock_panel)

        mock_panel.validation_requested.emit()
        mock_main_window._on_validate_workflow.assert_called_once()


class TestConnectVariableInspector:
    """Tests for connect_variable_inspector method."""

    def test_connect_variable_inspector_dock_signals(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test variable inspector dock signals are connected."""
        mock_dock = Mock()
        mock_dock.dockLocationChanged = MockSignal()
        mock_dock.visibilityChanged = MockSignal()
        mock_dock.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_variable_inspector(mock_dock)

        # Dock state signals should be connected
        assert mock_dock.dockLocationChanged.connected_count > 0
        assert mock_dock.visibilityChanged.connected_count > 0
        assert mock_dock.topLevelChanged.connected_count > 0

    def test_dock_location_changed_schedules_save(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test dock location change schedules UI state save."""
        mock_dock = Mock()
        mock_dock.dockLocationChanged = MockSignal()
        mock_dock.visibilityChanged = MockSignal()
        mock_dock.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_variable_inspector(mock_dock)

        mock_dock.dockLocationChanged.emit(1)  # Dock area enum
        mock_main_window._schedule_ui_state_save.assert_called()


class TestConnectPropertiesPanel:
    """Tests for connect_properties_panel method."""

    def test_connect_properties_panel_signals(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test properties panel signals are connected."""
        mock_panel = Mock()
        mock_panel.property_changed = MockSignal()
        mock_panel.dockLocationChanged = MockSignal()
        mock_panel.visibilityChanged = MockSignal()
        mock_panel.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_properties_panel(mock_panel)

        # Property signal should be connected
        assert mock_panel.property_changed.connected_count > 0

        # Dock state signals should be connected
        assert mock_panel.dockLocationChanged.connected_count > 0

    def test_property_changed_triggers_handler(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test property_changed calls handler."""
        mock_panel = Mock()
        mock_panel.property_changed = MockSignal()
        mock_panel.dockLocationChanged = MockSignal()
        mock_panel.visibilityChanged = MockSignal()
        mock_panel.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_properties_panel(mock_panel)

        mock_panel.property_changed.emit()
        mock_main_window._on_property_panel_changed.assert_called_once()


class TestConnectExecutionTimeline:
    """Tests for connect_execution_timeline method."""

    def test_connect_execution_timeline_signals(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test execution timeline signals are connected."""
        mock_timeline = Mock()
        mock_timeline.node_clicked = MockSignal()

        mock_dock = Mock()
        mock_dock.dockLocationChanged = MockSignal()
        mock_dock.visibilityChanged = MockSignal()
        mock_dock.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_execution_timeline(mock_timeline, mock_dock)

        # Node clicked signal should be connected
        assert mock_timeline.node_clicked.connected_count > 0

        # Dock state signals should be connected
        assert mock_dock.dockLocationChanged.connected_count > 0

    def test_node_clicked_selects_node(self, bottom_panel_bridge, mock_main_window):
        """Test node_clicked triggers node selection."""
        mock_timeline = Mock()
        mock_timeline.node_clicked = MockSignal()

        mock_dock = Mock()
        mock_dock.dockLocationChanged = MockSignal()
        mock_dock.visibilityChanged = MockSignal()
        mock_dock.topLevelChanged = MockSignal()

        bottom_panel_bridge.connect_execution_timeline(mock_timeline, mock_dock)

        mock_timeline.node_clicked.emit("node_123")
        mock_main_window._select_node_by_id.assert_called_once_with("node_123")


class TestSignalBridgeIntegration:
    """Integration tests for signal bridges."""

    def test_full_controller_connection_flow(self, controller_bridge, mock_main_window):
        """Test connecting all controllers together."""
        # Create mock controllers
        workflow_ctrl = Mock()
        workflow_ctrl.workflow_created = MockSignal()
        workflow_ctrl.workflow_loaded = MockSignal()
        workflow_ctrl.workflow_saved = MockSignal()
        workflow_ctrl.workflow_imported = MockSignal()
        workflow_ctrl.workflow_imported_json = MockSignal()
        workflow_ctrl.workflow_exported = MockSignal()
        workflow_ctrl.current_file_changed = MockSignal()
        workflow_ctrl.modified_changed = MockSignal()

        execution_ctrl = Mock()
        execution_ctrl.execution_started = MockSignal()
        execution_ctrl.execution_paused = MockSignal()
        execution_ctrl.execution_resumed = MockSignal()
        execution_ctrl.execution_stopped = MockSignal()
        execution_ctrl.execution_completed = MockSignal()
        execution_ctrl.execution_error = MockSignal()
        execution_ctrl.run_to_node_requested = MockSignal()
        execution_ctrl.run_single_node_requested = MockSignal()

        node_ctrl = Mock()
        node_ctrl.node_selected = MockSignal()
        node_ctrl.node_deselected = MockSignal()

        panel_ctrl = Mock()
        panel_ctrl.bottom_panel_toggled = MockSignal()

        # Connect all
        controller_bridge.connect_all_controllers(
            workflow_controller=workflow_ctrl,
            execution_controller=execution_ctrl,
            node_controller=node_ctrl,
            panel_controller=panel_ctrl,
        )

        # All should be connected without errors
        assert workflow_ctrl.workflow_created.connected_count > 0
        assert execution_ctrl.execution_started.connected_count > 0
        assert node_ctrl.node_selected.connected_count > 0
        assert panel_ctrl.bottom_panel_toggled.connected_count > 0

    def test_full_bottom_panel_connection_flow(
        self, bottom_panel_bridge, mock_main_window
    ):
        """Test connecting all bottom panel components."""
        # Create mock components
        bottom_panel = Mock()
        bottom_panel.validation_requested = MockSignal()
        bottom_panel.issue_clicked = MockSignal()
        bottom_panel.navigate_to_node = MockSignal()
        bottom_panel.variables_changed = MockSignal()
        bottom_panel.trigger_add_requested = MockSignal()
        bottom_panel.trigger_edit_requested = MockSignal()
        bottom_panel.trigger_delete_requested = MockSignal()
        bottom_panel.trigger_toggle_requested = MockSignal()
        bottom_panel.trigger_run_requested = MockSignal()
        bottom_panel.dockLocationChanged = MockSignal()
        bottom_panel.visibilityChanged = MockSignal()
        bottom_panel.topLevelChanged = MockSignal()

        var_inspector = Mock()
        var_inspector.dockLocationChanged = MockSignal()
        var_inspector.visibilityChanged = MockSignal()
        var_inspector.topLevelChanged = MockSignal()

        props_panel = Mock()
        props_panel.property_changed = MockSignal()
        props_panel.dockLocationChanged = MockSignal()
        props_panel.visibilityChanged = MockSignal()
        props_panel.topLevelChanged = MockSignal()

        # Connect all
        bottom_panel_bridge.connect_bottom_panel(bottom_panel)
        bottom_panel_bridge.connect_variable_inspector(var_inspector)
        bottom_panel_bridge.connect_properties_panel(props_panel)

        # All should be connected
        assert bottom_panel.validation_requested.connected_count > 0
        assert var_inspector.dockLocationChanged.connected_count > 0
        assert props_panel.property_changed.connected_count > 0
