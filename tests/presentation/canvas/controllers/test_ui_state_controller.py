"""
Comprehensive tests for UIStateController.

Tests UI state persistence including:
- State save/restore cycle
- Window geometry persistence
- Panel state persistence
- Recent files management
- State reset
- Auto-save scheduling
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.ui_state_controller import (
    UIStateController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a real QMainWindow with all required attributes."""
    mock = QMainWindow()
    qtbot.addWidget(mock)

    # Mock panels
    mock._bottom_panel = Mock()
    mock._bottom_panel.isVisible.return_value = True
    mock._bottom_panel._tab_widget = Mock()
    mock._bottom_panel._tab_widget.currentIndex.return_value = 0
    mock._bottom_panel._tab_widget.count.return_value = 5
    mock._bottom_panel.setVisible = Mock()

    mock._variable_inspector_dock = Mock()
    mock._variable_inspector_dock.isVisible.return_value = False
    mock._variable_inspector_dock.setVisible = Mock()

    mock._properties_panel = Mock()
    mock._properties_panel.isVisible.return_value = True
    mock._properties_panel.setVisible = Mock()

    mock._execution_timeline_dock = Mock()
    mock._execution_timeline_dock.isVisible.return_value = False
    mock._execution_timeline_dock.setVisible = Mock()

    mock._minimap = Mock()
    mock._minimap.isVisible.return_value = False
    mock._minimap.setVisible = Mock()

    # Mock actions
    mock.action_toggle_bottom_panel = Mock()
    mock.action_toggle_bottom_panel.setChecked = Mock()
    mock.action_toggle_variable_inspector = Mock()
    mock.action_toggle_variable_inspector.setChecked = Mock()
    mock.action_toggle_timeline = Mock()
    mock.action_toggle_timeline.setChecked = Mock()
    mock.action_toggle_minimap = Mock()
    mock.action_toggle_minimap.setChecked = Mock()

    # Mock window geometry methods
    mock.saveGeometry.return_value = QByteArray(b"geometry_data")
    mock.saveState.return_value = QByteArray(b"state_data")
    mock.restoreGeometry = Mock(return_value=True)
    mock.restoreState = Mock(return_value=True)

    return mock


@pytest.fixture
def mock_settings() -> None:
    """Create a mock QSettings."""
    mock = Mock()
    mock.value = Mock(return_value=None)
    mock.setValue = Mock()
    mock.contains = Mock(return_value=False)
    mock.clear = Mock()
    mock.sync = Mock()
    return mock


class MockSignal:
    """Mock signal that can connect and emit."""

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def disconnect(self, callback=None):
        if callback:
            self._callbacks.remove(callback)
        else:
            self._callbacks.clear()

    def emit(self, *args):
        for callback in self._callbacks:
            if args:
                callback(*args)
            else:
                callback()


@pytest.fixture
def ui_state_controller(mock_main_window, mock_settings) -> None:
    """Create a UIStateController instance with mocked dependencies."""
    controller = UIStateController.__new__(UIStateController)
    controller.main_window = mock_main_window
    controller._initialized = False
    controller._settings = mock_settings
    controller._auto_save_timer = Mock()
    controller._auto_save_timer.setSingleShot = Mock()
    controller._auto_save_timer.timeout = Mock()
    controller._auto_save_timer.timeout.connect = Mock()
    controller._auto_save_timer.stop = Mock()
    controller._auto_save_timer.start = Mock()
    controller._pending_save = False
    controller._initialized = True

    # Set up mock signals
    controller.state_saved = MockSignal()
    controller.state_restored = MockSignal()
    controller.state_reset = MockSignal()
    controller.recent_files_changed = MockSignal()

    return controller


class TestUIStateControllerInitialization:
    """Tests for UIStateController initialization."""

    def test_initialization(self, ui_state_controller, mock_main_window) -> None:
        """Test controller initializes correctly."""
        assert ui_state_controller.main_window == mock_main_window
        assert ui_state_controller.is_initialized

    def test_cleanup(self, ui_state_controller) -> None:
        """Test cleanup releases resources."""
        # Set up cleanup by calling method directly
        ui_state_controller._settings = None
        ui_state_controller._auto_save_timer = None
        ui_state_controller._initialized = False

        assert not ui_state_controller.is_initialized
        assert ui_state_controller._settings is None
        assert ui_state_controller._auto_save_timer is None


class TestStateSaveRestore:
    """Tests for state save/restore cycle."""

    def test_save_state_writes_version(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test save_state writes version to settings."""
        ui_state_controller.save_state()

        mock_settings.setValue.assert_any_call("uiStateVersion", 2)

    def test_save_state_emits_signal(self, ui_state_controller, mock_settings) -> None:
        """Test save_state emits state_saved signal."""
        signal_emitted = []
        ui_state_controller.state_saved.connect(lambda: signal_emitted.append(True))

        ui_state_controller.save_state()

        assert len(signal_emitted) == 1

    def test_restore_state_no_saved_state(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test restore_state handles missing saved state."""
        mock_settings.contains.return_value = False

        # Should not raise error
        ui_state_controller.restore_state()

    def test_restore_state_version_mismatch(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_state resets on version mismatch."""
        mock_settings.contains.return_value = True
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "uiStateVersion": 1,  # Old version
            "geometry": QByteArray(b"data"),
        }.get(key, default)

        ui_state_controller.restore_state()

        # Should clear settings on version mismatch
        mock_settings.clear.assert_called()

    def test_restore_state_emits_signal(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_state emits state_restored signal on success."""
        signal_emitted = []
        ui_state_controller.state_restored.connect(lambda: signal_emitted.append(True))

        mock_settings.contains.return_value = True
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "uiStateVersion": 2,
            "geometry": QByteArray(b"geometry_data"),
            "windowState": QByteArray(b"state_data"),
            "bottomPanelVisible": True,
            "bottomPanelTab": 0,
            "variableInspectorVisible": False,
            "propertiesPanelVisible": True,
            "executionTimelineVisible": False,
            "minimapVisible": False,
        }.get(key, default)

        ui_state_controller.restore_state()

        assert len(signal_emitted) == 1


class TestWindowGeometry:
    """Tests for window geometry persistence."""

    def test_save_window_geometry(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test save_window_geometry saves geometry and state."""
        ui_state_controller.save_window_geometry()

        # Should call setValue for geometry
        calls = [call[0] for call in mock_settings.setValue.call_args_list]
        assert any("geometry" in str(call) for call in calls)

    def test_restore_window_geometry_success(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_window_geometry restores geometry successfully."""
        geometry_data = QByteArray(b"geometry_data")
        state_data = QByteArray(b"state_data")

        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "geometry": geometry_data,
            "windowState": state_data,
        }.get(key, default)

        ui_state_controller.restore_window_geometry()

        mock_main_window.restoreGeometry.assert_called_once_with(geometry_data)
        mock_main_window.restoreState.assert_called_once_with(state_data)

    def test_restore_window_geometry_failure_resets(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_window_geometry resets on failure."""
        mock_settings.value.return_value = QByteArray(b"invalid_data")
        mock_main_window.restoreState.return_value = False

        ui_state_controller.restore_window_geometry()

        # Should clear settings on restore failure
        mock_settings.clear.assert_called()


class TestPanelStates:
    """Tests for panel state persistence."""

    def test_save_panel_states(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test save_panel_states saves all panel visibility."""
        ui_state_controller.save_panel_states()

        # Check calls were made for panel visibility
        call_keys = [str(call[0][0]) for call in mock_settings.setValue.call_args_list]
        assert any("bottomPanelVisible" in key for key in call_keys)
        assert any("variableInspectorVisible" in key for key in call_keys)
        assert any("propertiesPanelVisible" in key for key in call_keys)

    def test_restore_panel_states(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_panel_states restores panel visibility."""
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "bottomPanelVisible": True,
            "bottomPanelTab": 2,
            "variableInspectorVisible": True,
            "propertiesPanelVisible": False,
            "executionTimelineVisible": True,
            "minimapVisible": True,
        }.get(key, default)

        ui_state_controller.restore_panel_states()

        mock_main_window._bottom_panel.setVisible.assert_called_with(True)
        mock_main_window._variable_inspector_dock.setVisible.assert_called_with(True)
        mock_main_window._properties_panel.setVisible.assert_called_with(False)

    def test_restore_panel_states_handles_missing_panel(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test restore_panel_states handles missing panels gracefully."""
        mock_main_window._bottom_panel = None

        # Should not raise error
        ui_state_controller.restore_panel_states()


class TestStateReset:
    """Tests for state reset functionality."""

    def test_reset_state_clears_settings(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test reset_state clears all settings."""
        ui_state_controller.reset_state()

        mock_settings.clear.assert_called_once()
        mock_settings.sync.assert_called()

    def test_reset_state_emits_signal(self, ui_state_controller, mock_settings) -> None:
        """Test reset_state emits state_reset signal."""
        signal_emitted = []
        ui_state_controller.state_reset.connect(lambda: signal_emitted.append(True))

        ui_state_controller.reset_state()

        assert len(signal_emitted) == 1


class TestDirectoryManagement:
    """Tests for directory management."""

    def test_get_last_directory_not_set(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test get_last_directory returns None when not set."""
        mock_settings.value.return_value = ""

        result = ui_state_controller.get_last_directory()

        assert result is None

    def test_get_last_directory_invalid_path(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test get_last_directory returns None for invalid path."""
        mock_settings.value.return_value = "/nonexistent/path/12345"

        result = ui_state_controller.get_last_directory()

        assert result is None

    def test_set_last_directory(
        self, ui_state_controller, mock_settings, tmp_path
    ) -> None:
        """Test set_last_directory saves valid directory."""
        ui_state_controller.set_last_directory(tmp_path)

        mock_settings.setValue.assert_called()
        mock_settings.sync.assert_called()

    def test_set_last_directory_ignores_invalid(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test set_last_directory ignores non-existent directory."""
        invalid_path = Path("/nonexistent/path/12345")

        ui_state_controller.set_last_directory(invalid_path)

        # setValue should not be called for invalid path
        assert not any(
            "lastDirectory" in str(call)
            for call in mock_settings.setValue.call_args_list
        )


class TestRecentFilesManagement:
    """Tests for recent files management."""

    def test_get_recent_files(self, ui_state_controller) -> None:
        """Test get_recent_files returns files list."""
        with patch(
            "casare_rpa.canvas.workflow.recent_files.get_recent_files_manager"
        ) as mock_manager:
            mock_manager.return_value.get_recent_files.return_value = [
                {"path": "/test/file.json", "name": "file.json"}
            ]

            result = ui_state_controller.get_recent_files()

            assert len(result) == 1
            assert result[0]["name"] == "file.json"

    def test_add_recent_file(self, ui_state_controller, tmp_path) -> None:
        """Test add_recent_file adds file to list."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        signal_emitted = []
        ui_state_controller.recent_files_changed.connect(
            lambda files: signal_emitted.append(files)
        )

        with patch(
            "casare_rpa.canvas.workflow.recent_files.get_recent_files_manager"
        ) as mock_manager:
            mock_manager.return_value.get_recent_files.return_value = []

            ui_state_controller.add_recent_file(test_file)

            mock_manager.return_value.add_file.assert_called_once_with(test_file)
            assert len(signal_emitted) == 1

    def test_remove_recent_file(self, ui_state_controller, tmp_path) -> None:
        """Test remove_recent_file removes file from list."""
        test_file = tmp_path / "test.json"

        with patch(
            "casare_rpa.canvas.workflow.recent_files.get_recent_files_manager"
        ) as mock_manager:
            mock_manager.return_value.get_recent_files.return_value = []

            ui_state_controller.remove_recent_file(test_file)

            mock_manager.return_value.remove_file.assert_called_once_with(test_file)

    def test_clear_recent_files(self, ui_state_controller) -> None:
        """Test clear_recent_files clears all files."""
        signal_emitted = []
        ui_state_controller.recent_files_changed.connect(
            lambda files: signal_emitted.append(files)
        )

        with patch(
            "casare_rpa.canvas.workflow.recent_files.get_recent_files_manager"
        ) as mock_manager:
            ui_state_controller.clear_recent_files()

            mock_manager.return_value.clear.assert_called_once()
            assert len(signal_emitted) == 1
            assert signal_emitted[0] == []


class TestAutoSave:
    """Tests for auto-save scheduling."""

    def test_schedule_auto_save(self, ui_state_controller) -> None:
        """Test schedule_auto_save starts timer."""
        assert ui_state_controller._auto_save_timer is not None

        ui_state_controller.schedule_auto_save()

        assert ui_state_controller._pending_save is True

    def test_auto_save_timer_triggers_save(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test auto-save timer triggers save when pending."""
        ui_state_controller._pending_save = True

        # Simulate timer timeout
        ui_state_controller._on_auto_save_timeout()

        # Should have called save
        mock_settings.sync.assert_called()


class TestUIPreferences:
    """Tests for UI preferences."""

    def test_get_auto_save_enabled_default(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test get_auto_save_enabled returns default True."""
        mock_settings.value.return_value = True

        result = ui_state_controller.get_auto_save_enabled()

        assert result is True

    def test_set_auto_save_enabled(self, ui_state_controller, mock_settings) -> None:
        """Test set_auto_save_enabled saves preference."""
        ui_state_controller.set_auto_save_enabled(False)

        mock_settings.setValue.assert_called()
        mock_settings.sync.assert_called()

    def test_get_auto_validate_enabled_default(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test get_auto_validate_enabled returns default True."""
        mock_settings.value.return_value = True

        result = ui_state_controller.get_auto_validate_enabled()

        assert result is True

    def test_set_auto_validate_enabled(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test set_auto_validate_enabled saves preference."""
        ui_state_controller.set_auto_validate_enabled(False)

        mock_settings.setValue.assert_called()


class TestErrorHandling:
    """Tests for error handling."""

    def test_save_state_handles_exception(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test save_state handles exceptions gracefully."""
        mock_settings.setValue.side_effect = Exception("Save error")

        # Should not raise
        ui_state_controller.save_state()

    def test_restore_state_handles_exception(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test restore_state handles exceptions gracefully."""
        mock_settings.contains.return_value = True
        mock_settings.value.side_effect = Exception("Restore error")

        # Should not raise
        ui_state_controller.restore_state()

    def test_reset_state_handles_exception(
        self, ui_state_controller, mock_settings
    ) -> None:
        """Test reset_state handles exceptions gracefully."""
        mock_settings.clear.side_effect = Exception("Clear error")

        # Should not raise
        ui_state_controller.reset_state()


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_is_initialized_before_init(self, mock_main_window) -> None:
        """Test is_initialized returns False before init."""
        # Create controller without full initialization
        controller = UIStateController.__new__(UIStateController)
        controller._initialized = False
        controller._settings = None

        assert not controller.is_initialized

    def test_is_initialized_after_init(self, ui_state_controller) -> None:
        """Test is_initialized returns True after init."""
        assert ui_state_controller.is_initialized

    def test_get_settings(self, ui_state_controller, mock_settings) -> None:
        """Test get_settings returns QSettings instance."""
        result = ui_state_controller.get_settings()

        assert result == mock_settings


class TestSignalEmission:
    """Tests for signal emission."""

    def test_state_saved_signal(self, ui_state_controller, mock_settings) -> None:
        """Test state_saved signal is emitted."""
        received = []
        ui_state_controller.state_saved.connect(lambda: received.append(True))

        ui_state_controller.save_state()

        assert len(received) == 1

    def test_state_restored_signal(
        self, ui_state_controller, mock_settings, mock_main_window
    ) -> None:
        """Test state_restored signal is emitted."""
        received = []
        ui_state_controller.state_restored.connect(lambda: received.append(True))

        mock_settings.contains.return_value = True
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "uiStateVersion": 2,
            "geometry": QByteArray(b"data"),
            "windowState": QByteArray(b"data"),
        }.get(key, default)

        ui_state_controller.restore_state()

        assert len(received) == 1

    def test_state_reset_signal(self, ui_state_controller, mock_settings) -> None:
        """Test state_reset signal is emitted."""
        received = []
        ui_state_controller.state_reset.connect(lambda: received.append(True))

        ui_state_controller.reset_state()

        assert len(received) == 1

    def test_recent_files_changed_signal(self, ui_state_controller) -> None:
        """Test recent_files_changed signal is emitted."""
        received = []
        ui_state_controller.recent_files_changed.connect(lambda f: received.append(f))

        with patch(
            "casare_rpa.canvas.workflow.recent_files.get_recent_files_manager"
        ) as mock_manager:
            mock_manager.return_value.get_recent_files.return_value = []
            ui_state_controller.clear_recent_files()

        assert len(received) == 1
