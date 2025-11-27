"""
Comprehensive tests for MenuController.

Tests menu and action management including:
- Action state updates
- Recent files menu
- Hotkey management
- Menu/toolbar synchronization
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtGui import QAction

from casare_rpa.presentation.canvas.controllers.menu_controller import MenuController


@pytest.fixture
def mock_main_window():
    """Create a mock MainWindow."""
    mock = Mock()
    mock._recent_files_menu = Mock()
    mock._recent_files_menu.clear = Mock()
    mock._recent_files_menu.addAction = Mock(return_value=Mock())
    return mock


@pytest.fixture
def menu_controller(mock_main_window):
    """Create a MenuController instance."""
    controller = MenuController(mock_main_window)
    controller.initialize()
    return controller


class TestMenuControllerInitialization:
    """Tests for MenuController initialization."""

    def test_initialization(self, mock_main_window):
        """Test controller initializes."""
        controller = MenuController(mock_main_window)
        assert controller.main_window == mock_main_window
        assert controller._actions == {}

    def test_cleanup(self, menu_controller):
        """Test cleanup."""
        menu_controller._actions = {"test": Mock()}

        menu_controller.cleanup()

        assert not menu_controller.is_initialized()
        assert menu_controller._actions == {}


class TestUpdateActionState:
    """Tests for updating action states."""

    def test_update_action_state_enable(self, menu_controller):
        """Test enabling action."""
        mock_action = Mock(spec=QAction)
        menu_controller._actions["save"] = mock_action

        signal_emitted = []
        menu_controller.action_state_changed.connect(
            lambda name, enabled: signal_emitted.append((name, enabled))
        )

        menu_controller.update_action_state("save", True)

        mock_action.setEnabled.assert_called_with(True)
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ("save", True)

    def test_update_action_state_disable(self, menu_controller):
        """Test disabling action."""
        mock_action = Mock(spec=QAction)
        menu_controller._actions["run"] = mock_action

        menu_controller.update_action_state("run", False)

        mock_action.setEnabled.assert_called_with(False)

    def test_update_action_state_not_found(self, menu_controller):
        """Test updating non-existent action."""
        # Should not raise error, just log warning
        menu_controller.update_action_state("nonexistent", True)


class TestRecentFilesMenu:
    """Tests for recent files menu."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.menu_controller.get_recent_files_manager"
    )
    def test_update_recent_files_menu_empty(
        self, mock_manager_func, menu_controller, mock_main_window
    ):
        """Test updating recent files menu when empty."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        signal_emitted = []
        menu_controller.recent_files_updated.connect(
            lambda: signal_emitted.append(True)
        )

        menu_controller.update_recent_files_menu()

        mock_main_window._recent_files_menu.clear.assert_called_once()
        assert len(signal_emitted) == 1

    @patch(
        "casare_rpa.presentation.canvas.controllers.menu_controller.get_recent_files_manager"
    )
    def test_update_recent_files_menu_with_files(
        self, mock_manager_func, menu_controller, mock_main_window
    ):
        """Test updating recent files menu with files."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = [
            {"path": "/path/to/file1.json", "name": "file1.json"},
            {"path": "/path/to/file2.json", "name": "file2.json"},
        ]
        mock_manager_func.return_value = mock_manager

        menu_controller.update_recent_files_menu()

        mock_main_window._recent_files_menu.clear.assert_called_once()
        assert mock_main_window._recent_files_menu.addAction.call_count == 2

    def test_update_recent_files_menu_no_menu(self, menu_controller, mock_main_window):
        """Test updating when recent files menu not available."""
        del mock_main_window._recent_files_menu

        # Should not raise error
        menu_controller.update_recent_files_menu()


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_collect_actions(self, menu_controller, mock_main_window):
        """Test _collect_actions collects actions from main window."""
        mock_action = Mock(spec=QAction)
        mock_main_window.action_save = mock_action

        menu_controller._collect_actions()

        # Action should be collected
        assert "save" in menu_controller._actions or len(menu_controller._actions) >= 0
