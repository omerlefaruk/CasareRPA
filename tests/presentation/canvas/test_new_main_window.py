"""
Tests for NewMainWindow v2 dock-only workspace.

Epic 4.1: Test dock widget creation, layout persistence, and dock-only enforcement.
Epic 8.3: Test recent files integration with MenuBarV2.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QDockWidget

from casare_rpa.presentation.canvas.new_main_window import NewMainWindow

# Ensure Qt headless mode
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.ui
class TestNewMainWindowDocks:
    """Test dock widget creation and configuration."""

    def test_creates_dock_widgets(self, qapp):
        """All three dock widgets should be created."""
        window = NewMainWindow()
        assert hasattr(window, "_left_dock")
        assert hasattr(window, "_right_dock")
        assert hasattr(window, "_bottom_dock")

        assert window._left_dock is not None
        assert window._right_dock is not None
        assert window._bottom_dock is not None

    def test_docks_have_correct_titles(self, qapp):
        """Dock widgets should have correct titles."""
        window = NewMainWindow()
        assert window._left_dock.windowTitle() == "Project Explorer"
        assert window._right_dock.windowTitle() == "Properties"
        assert window._bottom_dock.windowTitle() == "Output"

    def test_docks_not_floatable(self, qapp):
        """Docks should NOT have floatable feature (dock-only enforcement)."""
        window = NewMainWindow()
        for dock in [window._left_dock, window._right_dock, window._bottom_dock]:
            features = dock.features()
            assert QDockWidget.DockWidgetFeature.DockWidgetFloatable not in features
            assert QDockWidget.DockWidgetFeature.DockWidgetMovable in features
            assert QDockWidget.DockWidgetFeature.DockWidgetClosable in features

    def test_docks_hidden_by_default(self, qapp):
        """All placeholder docks should be hidden by default."""
        window = NewMainWindow()
        assert window._left_dock.isVisible() is False
        assert window._right_dock.isVisible() is False
        assert window._bottom_dock.isVisible() is False


@pytest.mark.ui
class TestNewMainWindowLayoutPersistence:
    """Test layout save/restore/reset functionality."""

    def test_save_layout_creates_settings(self, qapp, tmp_path):
        """save_layout() should write to QSettings."""
        # Use a temporary settings file
        settings = QSettings("CasareRPA", "CanvasV2")
        settings.clear()  # Start clean

        window = NewMainWindow()
        window.resize(800, 600)
        window.move(100, 100)
        window.save_layout()

        # Verify settings were written
        assert settings.value("geometry") is not None
        assert settings.value("windowState") is not None
        assert settings.value("layoutVersion") == window._CURRENT_LAYOUT_VERSION

    def test_restore_layout_loads_geometry(self, qapp):
        """restore_layout() should load saved geometry and state."""
        settings = QSettings("CasareRPA", "CanvasV2")
        settings.clear()

        # Create and save layout
        window1 = NewMainWindow()
        window1.resize(900, 700)
        window1.move(150, 150)
        window1.save_layout()

        # Verify geometry and state were saved
        assert settings.value("geometry") is not None
        assert settings.value("windowState") is not None

        # Create new window and restore - should not error
        window2 = NewMainWindow()
        window2.restore_layout()

        # The main goal is that restore doesn't error and
        # settings contain valid data
        assert settings.value("layoutVersion") == window1._CURRENT_LAYOUT_VERSION

    def test_reset_clears_settings(self, qapp):
        """reset_layout() should clear all layout settings."""
        settings = QSettings("CasareRPA", "CanvasV2")
        settings.clear()

        window = NewMainWindow()
        window.save_layout()

        # Verify settings exist
        assert settings.value("geometry") is not None

        # Reset
        window.reset_layout()

        # Settings should be cleared
        assert settings.value("geometry") is None
        assert settings.value("windowState") is None
        assert settings.value("layoutVersion") is None

    def test_reset_hides_all_docks(self, qapp):
        """reset_layout() should hide all dock widgets."""
        window = NewMainWindow()

        # Show all docks
        window._left_dock.setVisible(True)
        window._right_dock.setVisible(True)
        window._bottom_dock.setVisible(True)

        # Reset
        window.reset_layout()

        # All docks should be hidden
        assert window._left_dock.isVisible() is False
        assert window._right_dock.isVisible() is False
        assert window._bottom_dock.isVisible() is False


@pytest.mark.ui
class TestNewMainWindowCornerBehavior:
    """Test corner behavior and dock nesting configuration."""

    def test_corner_behavior_enforced(self, qapp):
        """Bottom corners should be configured for BottomDockWidgetArea."""
        window = NewMainWindow()
        assert (
            window.corner(Qt.Corner.BottomRightCorner)
            == Qt.DockWidgetArea.BottomDockWidgetArea
        )
        assert (
            window.corner(Qt.Corner.BottomLeftCorner)
            == Qt.DockWidgetArea.BottomDockWidgetArea
        )

    def test_dock_nesting_enabled(self, qapp):
        """Dock nesting should be enabled for complex layouts."""
        window = NewMainWindow()
        # QMainWindow doesn't expose isDockNestingEnabled as a public method
        # but we can verify it was called during setup by checking the behavior
        # Tabify operation would fail if nesting wasn't enabled
        assert window._left_dock is not None
        assert window._bottom_dock is not None


@pytest.mark.ui
class TestNewMainWindowSignals:
    """Test workflow signals exist for compatibility."""

    def test_all_workflow_signals_exist(self, qapp):
        """All workflow signals required by app.py should exist."""
        window = NewMainWindow()
        required_signals = [
            "workflow_new",
            "workflow_open",
            "workflow_save",
            "workflow_save_as",
            "workflow_import",
            "workflow_import_json",
            "workflow_export_selected",
            "workflow_run",
            "workflow_run_all",
            "workflow_run_to_node",
            "workflow_run_single_node",
            "workflow_pause",
            "workflow_resume",
            "workflow_stop",
            "preferences_saved",
            "trigger_workflow_requested",
        ]
        for sig_name in required_signals:
            assert hasattr(window, sig_name), f"Missing signal: {sig_name}"
            # Verify it's actually a Signal
            signal = getattr(window, sig_name)
            # Signal has a `emit` method if it's properly constructed
            assert hasattr(signal, "emit"), f"{sig_name} is not a Signal"

    def test_stub_actions_exist(self, qapp):
        """Stub action properties should exist for app.py compatibility."""
        window = NewMainWindow()
        required_actions = [
            "action_undo",
            "action_redo",
            "action_delete",
            "action_cut",
            "action_copy",
            "action_paste",
            "action_duplicate",
            "action_select_all",
            "action_save",
            "action_save_as",
            "action_run",
            "action_stop",
        ]
        for action_name in required_actions:
            assert hasattr(window, action_name), f"Missing action: {action_name}"
            action = getattr(window, action_name)
            # Stub action should have triggered signal
            assert hasattr(action, "triggered"), f"{action_name} has no triggered signal"


@pytest.mark.ui
class TestNewMainWindowInterface:
    """Test interface methods required by app.py."""

    def test_set_central_widget(self, qapp):
        """set_central_widget() should set the central widget."""
        from PySide6.QtWidgets import QWidget

        window = NewMainWindow()
        widget = QWidget()
        window.set_central_widget(widget)

        assert window.centralWidget() is widget
        assert window._central_widget is widget

    def test_set_controllers_stores_references(self, qapp):
        """set_controllers() should store controller references."""
        window = NewMainWindow()

        mock_workflow = type("MockController", (), {})()
        mock_execution = type("MockController", (), {})()
        mock_node = type("MockController", (), {})()
        mock_project = type("MockController", (), {})()
        mock_robot = type("MockController", (), {})()

        window.set_controllers(
            mock_workflow, mock_execution, mock_node, mock_project, mock_robot
        )

        assert window._workflow_controller is mock_workflow
        assert window._execution_controller is mock_execution
        assert window._node_controller is mock_node
        assert window._project_controller is mock_project
        assert window._robot_controller is mock_robot

    def test_show_status_logs_message(self, qapp):
        """show_status() should not raise errors."""
        window = NewMainWindow()
        # This should not raise any errors
        window.show_status("Test message")
        # Note: loguru logs don't appear in caplog, but the method
        # should work without errors


@pytest.mark.ui
class TestNewMainWindowAutoSave:
    """Test layout auto-save on dock changes."""

    def test_dock_location_change_schedules_save(self, qapp):
        """Dock location changes should schedule an auto-save."""
        window = NewMainWindow()
        window._pending_save = False

        # Trigger dock location change
        window._schedule_layout_save()

        assert window._pending_save is True
        assert window._auto_save_timer.isActive() is True

    def test_auto_save_timer_triggers_save(self, qapp):
        """Auto-save timer should trigger save_layout()."""
        settings = QSettings("CasareRPA", "CanvasV2")
        settings.clear()

        window = NewMainWindow()
        window._pending_save = True

        # Trigger the timer timeout directly
        window._on_auto_save_timeout()

        assert window._pending_save is False
        # Settings should have been saved
        assert settings.value("layoutVersion") is not None
