"""
Comprehensive tests for MenuController.

Tests menu and action management including:
- Action state updates
- Recent files menu
- Hotkey management
- Menu/toolbar synchronization
- About dialog
- Desktop selector builder
- Help menu operations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.menu_controller import MenuController


@pytest.fixture
def mock_main_window(qtbot) -> None:
    """Create a mock MainWindow based on QMainWindow."""
    # Use a real QMainWindow as base to satisfy PySide6's QObject requirements
    window = QMainWindow()

    # Add mock attributes
    window._recent_files_menu = Mock()
    window._recent_files_menu.clear = Mock()
    window._recent_files_menu.addAction = Mock(return_value=Mock())
    window.get_recent_files_menu = Mock(return_value=window._recent_files_menu)
    window.show_status = Mock()
    window.workflow_open = Mock()
    window.workflow_open.emit = Mock()
    window.set_current_file = Mock()
    window.set_modified = Mock()
    window._workflow_controller = Mock()
    window._workflow_controller.check_unsaved_changes = Mock(return_value=True)

    return window


@pytest.fixture
def menu_controller(mock_main_window) -> None:
    """Create a MenuController instance."""
    controller = MenuController(mock_main_window)
    controller.initialize()
    return controller


class TestMenuControllerInitialization:
    """Tests for MenuController initialization."""

    def test_initialization(self, mock_main_window) -> None:
        """Test controller initializes."""
        controller = MenuController(mock_main_window)
        assert controller.main_window == mock_main_window
        assert controller._actions == {}

    def test_initialize_sets_flag(self, mock_main_window) -> None:
        """Test initialize sets initialized flag."""
        controller = MenuController(mock_main_window)
        controller.initialize()
        assert controller._initialized is True

    def test_cleanup(self, menu_controller) -> None:
        """Test cleanup."""
        menu_controller._actions = {"test": Mock()}

        menu_controller.cleanup()

        assert menu_controller._initialized is False
        assert menu_controller._actions == {}


class TestUpdateActionState:
    """Tests for updating action states."""

    def test_update_action_state_enable(self, menu_controller) -> None:
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

    def test_update_action_state_disable(self, menu_controller) -> None:
        """Test disabling action."""
        mock_action = Mock(spec=QAction)
        menu_controller._actions["run"] = mock_action

        menu_controller.update_action_state("run", False)

        mock_action.setEnabled.assert_called_with(False)

    def test_update_action_state_not_found(self, menu_controller) -> None:
        """Test updating non-existent action."""
        # Should not raise error, just log warning
        menu_controller.update_action_state("nonexistent", True)


class TestRecentFilesMenu:
    """Tests for recent files menu."""

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_update_recent_files_menu_empty(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
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

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_update_recent_files_menu_with_files(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
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

    def test_update_recent_files_menu_no_menu(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test updating when recent files menu not available."""
        mock_main_window.get_recent_files_menu.return_value = None

        # Should not raise error
        menu_controller.update_recent_files_menu()

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_get_recent_files(self, mock_manager_func, menu_controller) -> None:
        """Test getting recent files list."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = [
            {
                "path": "/path/to/file.json",
                "name": "file.json",
                "last_opened": "2024-01-01",
            }
        ]
        mock_manager_func.return_value = mock_manager

        result = menu_controller.get_recent_files()

        assert len(result) == 1
        assert result[0]["name"] == "file.json"

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_add_recent_file(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test adding a file to recent files."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        menu_controller.add_recent_file(Path("/path/to/file.json"))

        mock_manager.add_file.assert_called_once()

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_clear_recent_files(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test clearing recent files list."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        signal_emitted = []
        menu_controller.recent_files_cleared.connect(
            lambda: signal_emitted.append(True)
        )

        menu_controller.clear_recent_files()

        mock_manager.clear.assert_called_once()
        mock_main_window.show_status.assert_called_with("Recent files cleared", 3000)
        assert len(signal_emitted) == 1

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    @patch("PySide6.QtWidgets.QMessageBox.warning")
    def test_open_recent_file_not_exists(
        self, mock_warning, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test opening a recent file that doesn't exist."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        menu_controller.open_recent_file("/nonexistent/path/file.json")
        mock_warning.assert_called_once()

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_open_recent_file_exists(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test opening a recent file that exists."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        with patch.object(Path, "exists", return_value=True):
            signal_emitted = []
            menu_controller.recent_file_opened.connect(
                lambda path: signal_emitted.append(path)
            )

            menu_controller.open_recent_file("/existing/path/file.json")

            mock_main_window.workflow_open.emit.assert_called_once()
            assert len(signal_emitted) == 1


class TestAboutDialog:
    """Tests for about dialog functionality."""

    def test_show_about_dialog(self, menu_controller, mock_main_window) -> None:
        """Test showing about dialog."""
        signal_emitted = []
        menu_controller.about_dialog_shown.connect(lambda: signal_emitted.append(True))

        with patch(
            "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
        ) as mock_msgbox:
            menu_controller.show_about_dialog()
            mock_msgbox.about.assert_called_once()
            assert len(signal_emitted) == 1

    def test_show_about_dialog_contains_app_name(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test about dialog contains app name."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
        ) as mock_msgbox:
            menu_controller.show_about_dialog()
            call_args = mock_msgbox.about.call_args
            assert "CasareRPA" in call_args[0][1]  # Title contains app name


class TestDesktopSelectorBuilder:
    """Tests for desktop selector builder functionality."""

    def test_show_desktop_selector_builder(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test showing desktop selector builder."""
        signal_emitted = []
        menu_controller.desktop_selector_shown.connect(
            lambda: signal_emitted.append(True)
        )

        with patch(
            "casare_rpa.canvas.selectors.desktop_selector_builder.DesktopSelectorBuilder"
        ) as mock_builder:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = False
            mock_builder.return_value = mock_dialog

            menu_controller.show_desktop_selector_builder()

            mock_builder.assert_called_once_with(parent=mock_main_window)
            assert len(signal_emitted) == 1

    def test_show_desktop_selector_builder_with_selection(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test desktop selector builder with successful selection."""
        with patch(
            "casare_rpa.canvas.selectors.desktop_selector_builder.DesktopSelectorBuilder"
        ) as mock_builder:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = True
            mock_dialog.get_selected_selector.return_value = "test_selector"
            mock_builder.return_value = mock_dialog

            menu_controller.show_desktop_selector_builder()

            mock_dialog.get_selected_selector.assert_called_once()

    def test_show_desktop_selector_builder_error(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test desktop selector builder error handling."""
        with patch(
            "casare_rpa.canvas.selectors.desktop_selector_builder.DesktopSelectorBuilder"
        ) as mock_builder:
            mock_builder.side_effect = Exception("Test error")

            with patch(
                "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
            ) as mock_msgbox:
                menu_controller.show_desktop_selector_builder()
                mock_msgbox.critical.assert_called_once()


class TestHelpMenuOperations:
    """Tests for help menu operations."""

    def test_show_documentation(self, menu_controller, mock_main_window) -> None:
        """Test opening documentation."""
        with patch("webbrowser.open") as mock_webbrowser:
            with patch.object(Path, "exists", return_value=False):
                menu_controller.show_documentation()
                mock_webbrowser.assert_called_once()

    def test_show_documentation_local_docs(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test opening local documentation."""
        with patch("webbrowser.open") as mock_webbrowser:
            with patch.object(Path, "exists", return_value=True):
                menu_controller.show_documentation()
                mock_webbrowser.assert_called_once()

    def test_show_keyboard_shortcuts(self, menu_controller, mock_main_window) -> None:
        """Test showing keyboard shortcuts dialog."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
        ) as mock_msgbox:
            menu_controller.show_keyboard_shortcuts()
            mock_msgbox.information.assert_called_once()
            # Check that shortcuts content contains expected shortcuts
            call_args = mock_msgbox.information.call_args
            assert "Keyboard Shortcuts" in call_args[0][1]

    def test_check_for_updates(self, menu_controller, mock_main_window) -> None:
        """Test checking for updates."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
        ) as mock_msgbox:
            menu_controller.check_for_updates()
            mock_msgbox.information.assert_called_once()
            mock_main_window.show_status.assert_called_with(
                "Update check complete", 3000
            )


class TestHotkeyManagement:
    """Tests for hotkey management."""

    def test_open_hotkey_manager(self, menu_controller, mock_main_window) -> None:
        """Test opening hotkey manager dialog."""
        with patch(
            "casare_rpa.canvas.toolbar.hotkey_manager.HotkeyManagerDialog"
        ) as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = False
            mock_dialog_class.return_value = mock_dialog

            menu_controller.open_hotkey_manager()

            mock_dialog_class.assert_called_once()

    def test_open_hotkey_manager_saves_changes(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test hotkey manager saves changes when accepted."""
        with patch(
            "casare_rpa.canvas.toolbar.hotkey_manager.HotkeyManagerDialog"
        ) as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = True
            mock_dialog_class.return_value = mock_dialog

            with patch.object(menu_controller, "_reload_hotkeys") as mock_reload:
                menu_controller.open_hotkey_manager()
                mock_reload.assert_called_once()


class TestPreferences:
    """Tests for preferences dialog."""

    def test_open_preferences(self, menu_controller, mock_main_window) -> None:
        """Test opening preferences dialog."""
        with patch(
            "casare_rpa.canvas.dialogs.preferences_dialog.PreferencesDialog"
        ) as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = 0  # Rejected
            mock_dialog_class.return_value = mock_dialog

            menu_controller.open_preferences()

            mock_dialog_class.assert_called_once_with(mock_main_window)

    def test_open_preferences_saves(self, menu_controller, mock_main_window) -> None:
        """Test preferences saves and emits signal."""
        mock_main_window.preferences_saved = Mock()
        mock_main_window.preferences_saved.emit = Mock()

        with patch(
            "casare_rpa.canvas.dialogs.preferences_dialog.PreferencesDialog"
        ) as mock_dialog_class:
            from PySide6.QtWidgets import QDialog

            mock_dialog = Mock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
            mock_dialog_class.return_value = mock_dialog

            menu_controller.open_preferences()

            mock_main_window.preferences_saved.emit.assert_called_once()


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_collect_actions(self, menu_controller, mock_main_window) -> None:
        """Test _collect_actions collects actions from main window."""
        mock_action = Mock(spec=QAction)
        mock_main_window.action_new = mock_action
        mock_main_window.action_open = mock_action
        mock_main_window.action_save = mock_action
        mock_main_window.action_save_as = mock_action

        menu_controller._collect_actions()

        # Actions should be collected
        assert "new" in menu_controller._actions
        assert "save" in menu_controller._actions

    def test_reload_hotkeys(self, menu_controller) -> None:
        """Test _reload_hotkeys updates action shortcuts."""
        mock_action = Mock(spec=QAction)
        menu_controller._actions["test_action"] = mock_action

        signal_emitted = []
        menu_controller.hotkey_changed.connect(
            lambda name, key: signal_emitted.append((name, key))
        )

        with patch(
            "casare_rpa.utils.hotkey_settings.get_hotkey_settings"
        ) as mock_settings:
            mock_hotkey_obj = Mock()
            mock_hotkey_obj.get.return_value = "Ctrl+T"
            mock_settings.return_value = mock_hotkey_obj
            menu_controller._reload_hotkeys()

            mock_action.setShortcut.assert_called_once()
            assert len(signal_emitted) == 1


class TestSignals:
    """Tests for signal emissions."""

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_recent_file_opened_signal(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test recent_file_opened signal is emitted."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        signal_received = []
        menu_controller.recent_file_opened.connect(
            lambda path: signal_received.append(path)
        )

        with patch.object(Path, "exists", return_value=True):
            menu_controller.open_recent_file("/test/path.json")

        assert len(signal_received) == 1
        assert signal_received[0] == "/test/path.json"

    def test_about_dialog_shown_signal(self, menu_controller) -> None:
        """Test about_dialog_shown signal is emitted."""
        signal_received = []
        menu_controller.about_dialog_shown.connect(lambda: signal_received.append(True))

        with patch(
            "casare_rpa.presentation.canvas.controllers.menu_controller.QMessageBox"
        ):
            menu_controller.show_about_dialog()

        assert len(signal_received) == 1

    def test_desktop_selector_shown_signal(
        self, menu_controller, mock_main_window
    ) -> None:
        """Test desktop_selector_shown signal is emitted."""
        signal_received = []
        menu_controller.desktop_selector_shown.connect(
            lambda: signal_received.append(True)
        )

        with patch(
            "casare_rpa.canvas.selectors.desktop_selector_builder.DesktopSelectorBuilder"
        ) as mock_builder:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = False
            mock_builder.return_value = mock_dialog
            menu_controller.show_desktop_selector_builder()

        assert len(signal_received) == 1

    @patch("casare_rpa.canvas.workflow.recent_files.get_recent_files_manager")
    def test_recent_files_cleared_signal(
        self, mock_manager_func, menu_controller, mock_main_window
    ) -> None:
        """Test recent_files_cleared signal is emitted."""
        mock_manager = Mock()
        mock_manager.get_recent_files.return_value = []
        mock_manager_func.return_value = mock_manager

        signal_received = []
        menu_controller.recent_files_cleared.connect(
            lambda: signal_received.append(True)
        )

        menu_controller.clear_recent_files()

        assert len(signal_received) == 1
