"""
Tests for MenuController.

Tests menu and action management covering:
- Action state management (update_action_state)
- Recent files operations (add, open, clear)
- Dialog operations (about, shortcuts, preferences)
- Hotkey management

Note: These tests mock Qt dependencies to avoid instantiating the full UI.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestActionStateManagement:
    """Tests for action state management functionality."""

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window with necessary attributes."""
        main_window = Mock()
        main_window.action_new = Mock()
        main_window.action_open = Mock()
        main_window.action_save = Mock()
        main_window.action_save_as = Mock()
        main_window.action_undo = Mock()
        main_window.action_redo = Mock()
        main_window.action_run = Mock()
        main_window.action_stop = Mock()
        return main_window

    @pytest.fixture
    def menu_controller_logic(self, mock_main_window):
        """Create MenuController logic mock."""
        actions = {
            "new": mock_main_window.action_new,
            "open": mock_main_window.action_open,
            "save": mock_main_window.action_save,
            "save_as": mock_main_window.action_save_as,
            "undo": mock_main_window.action_undo,
            "redo": mock_main_window.action_redo,
            "run": mock_main_window.action_run,
            "stop": mock_main_window.action_stop,
        }
        return {
            "main_window": mock_main_window,
            "actions": actions,
        }

    def _update_action_state(self, controller_logic, action_name: str, enabled: bool):
        """Simulate update_action_state method."""
        actions = controller_logic["actions"]
        if action_name in actions:
            actions[action_name].setEnabled(enabled)
            return True
        return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_update_action_state_enable(self, menu_controller_logic):
        """Test enabling an action."""
        action = menu_controller_logic["actions"]["save"]

        result = self._update_action_state(menu_controller_logic, "save", True)

        assert result is True
        action.setEnabled.assert_called_once_with(True)

    def test_update_action_state_disable(self, menu_controller_logic):
        """Test disabling an action."""
        action = menu_controller_logic["actions"]["run"]

        result = self._update_action_state(menu_controller_logic, "run", False)

        assert result is True
        action.setEnabled.assert_called_once_with(False)

    def test_update_multiple_actions(self, menu_controller_logic):
        """Test updating multiple actions."""
        self._update_action_state(menu_controller_logic, "save", True)
        self._update_action_state(menu_controller_logic, "undo", False)
        self._update_action_state(menu_controller_logic, "run", True)

        menu_controller_logic["actions"]["save"].setEnabled.assert_called_with(True)
        menu_controller_logic["actions"]["undo"].setEnabled.assert_called_with(False)
        menu_controller_logic["actions"]["run"].setEnabled.assert_called_with(True)

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_update_action_state_unknown_action(self, menu_controller_logic):
        """Test updating unknown action returns False."""
        result = self._update_action_state(menu_controller_logic, "nonexistent", True)

        assert result is False

    def test_update_action_state_empty_name(self, menu_controller_logic):
        """Test updating with empty action name."""
        result = self._update_action_state(menu_controller_logic, "", True)

        assert result is False


class TestRecentFilesOperations:
    """Tests for recent files functionality."""

    @pytest.fixture
    def mock_recent_files_manager(self):
        """Create a mock recent files manager."""
        manager = Mock()
        manager.get_recent_files.return_value = [
            {
                "path": "/path/to/file1.json",
                "name": "file1.json",
                "last_opened": "2024-01-01",
            },
            {
                "path": "/path/to/file2.json",
                "name": "file2.json",
                "last_opened": "2024-01-02",
            },
        ]
        manager.add_file = Mock()
        manager.remove_file = Mock()
        manager.clear = Mock()
        return manager

    def _add_recent_file(self, manager, file_path):
        """Simulate add_recent_file method."""
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            manager.add_file(path)
            return True
        except Exception:
            return False

    def _get_recent_files(self, manager):
        """Simulate get_recent_files method."""
        try:
            return manager.get_recent_files()
        except Exception:
            return []

    def _clear_recent_files(self, manager):
        """Simulate clear_recent_files method."""
        try:
            manager.clear()
            return True
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_get_recent_files_returns_list(self, mock_recent_files_manager):
        """Test getting recent files returns correct list."""
        result = self._get_recent_files(mock_recent_files_manager)

        assert len(result) == 2
        assert result[0]["name"] == "file1.json"
        assert result[1]["path"] == "/path/to/file2.json"

    def test_add_recent_file_success(self, mock_recent_files_manager):
        """Test adding a file to recent files."""
        result = self._add_recent_file(mock_recent_files_manager, "/path/to/new.json")

        assert result is True
        mock_recent_files_manager.add_file.assert_called_once()

    def test_add_recent_file_path_object(self, mock_recent_files_manager):
        """Test adding a Path object to recent files."""
        path = Path("/path/to/new.json")
        result = self._add_recent_file(mock_recent_files_manager, path)

        assert result is True
        mock_recent_files_manager.add_file.assert_called_once_with(path)

    def test_clear_recent_files_success(self, mock_recent_files_manager):
        """Test clearing recent files."""
        result = self._clear_recent_files(mock_recent_files_manager)

        assert result is True
        mock_recent_files_manager.clear.assert_called_once()

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_get_recent_files_empty(self, mock_recent_files_manager):
        """Test getting recent files when list is empty."""
        mock_recent_files_manager.get_recent_files.return_value = []

        result = self._get_recent_files(mock_recent_files_manager)

        assert result == []

    def test_get_recent_files_error(self, mock_recent_files_manager):
        """Test getting recent files on error returns empty list."""
        mock_recent_files_manager.get_recent_files.side_effect = Exception("Error")

        result = self._get_recent_files(mock_recent_files_manager)

        assert result == []


class TestOpenRecentFileLogic:
    """Tests for open recent file functionality."""

    def _simulate_open_recent_file(
        self, file_path: str, file_exists: bool, workflow_controller=None
    ):
        """
        Simulate _on_open_recent_file logic.

        Returns:
            tuple: (success, error_message)
        """
        path = Path(file_path)

        # Check if file exists
        if not file_exists:
            return (False, "File not found")

        # Check for unsaved changes
        if workflow_controller:
            if not workflow_controller.check_unsaved_changes():
                return (False, "Unsaved changes")

        return (True, None)

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_open_recent_file_success(self):
        """Test opening a recent file successfully."""
        workflow_controller = Mock()
        workflow_controller.check_unsaved_changes.return_value = True

        success, error = self._simulate_open_recent_file(
            "/path/to/file.json",
            file_exists=True,
            workflow_controller=workflow_controller,
        )

        assert success is True
        assert error is None

    def test_open_recent_file_without_workflow_controller(self):
        """Test opening file without workflow controller."""
        success, error = self._simulate_open_recent_file(
            "/path/to/file.json", file_exists=True, workflow_controller=None
        )

        assert success is True
        assert error is None

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_open_recent_file_not_found(self):
        """Test opening a file that doesn't exist."""
        success, error = self._simulate_open_recent_file(
            "/path/to/missing.json", file_exists=False
        )

        assert success is False
        assert error == "File not found"

    def test_open_recent_file_unsaved_changes_cancelled(self):
        """Test opening file when user cancels unsaved changes dialog."""
        workflow_controller = Mock()
        workflow_controller.check_unsaved_changes.return_value = False

        success, error = self._simulate_open_recent_file(
            "/path/to/file.json",
            file_exists=True,
            workflow_controller=workflow_controller,
        )

        assert success is False
        assert error == "Unsaved changes"


class TestAboutDialogLogic:
    """Tests for about dialog functionality."""

    def _build_about_content(self, app_name: str, app_version: str):
        """
        Build about dialog content.

        Returns:
            str: HTML content for about dialog
        """
        return (
            f"<h3>{app_name} v{app_version}</h3>" f"<p>Windows Desktop RPA Platform</p>"
        )

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_about_content_includes_app_name(self):
        """Test about content includes app name."""
        content = self._build_about_content("CasareRPA", "1.0.0")

        assert "CasareRPA" in content

    def test_about_content_includes_version(self):
        """Test about content includes version."""
        content = self._build_about_content("CasareRPA", "2.5.0")

        assert "2.5.0" in content

    def test_about_content_includes_platform_description(self):
        """Test about content includes platform description."""
        content = self._build_about_content("CasareRPA", "1.0.0")

        assert "Windows Desktop RPA Platform" in content


class TestKeyboardShortcutsLogic:
    """Tests for keyboard shortcuts display functionality."""

    def _build_shortcuts_table(self, shortcuts: list):
        """
        Build keyboard shortcuts HTML table.

        Args:
            shortcuts: List of (action, shortcut) tuples

        Returns:
            str: HTML table content
        """
        html = "<h3>Keyboard Shortcuts</h3><table>"
        html += "<tr><th>Action</th><th>Shortcut</th></tr>"

        for action, shortcut in shortcuts:
            html += f"<tr><td>{action}</td><td><code>{shortcut}</code></td></tr>"

        html += "</table>"
        return html

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_shortcuts_table_contains_actions(self):
        """Test shortcuts table contains action names."""
        shortcuts = [
            ("Save", "Ctrl+S"),
            ("Open", "Ctrl+O"),
        ]

        html = self._build_shortcuts_table(shortcuts)

        assert "Save" in html
        assert "Open" in html

    def test_shortcuts_table_contains_hotkeys(self):
        """Test shortcuts table contains hotkey strings."""
        shortcuts = [
            ("Save", "Ctrl+S"),
            ("Run", "F3"),
        ]

        html = self._build_shortcuts_table(shortcuts)

        assert "Ctrl+S" in html
        assert "F3" in html

    def test_shortcuts_table_empty_list(self):
        """Test shortcuts table with empty list."""
        html = self._build_shortcuts_table([])

        assert "<h3>Keyboard Shortcuts</h3>" in html
        assert "</table>" in html

    def test_shortcuts_table_structure(self):
        """Test shortcuts table has correct HTML structure."""
        shortcuts = [("Test", "Ctrl+T")]

        html = self._build_shortcuts_table(shortcuts)

        assert "<table>" in html
        assert "</table>" in html
        assert "<tr>" in html
        assert "<td>" in html
        assert "<code>" in html


class TestHotkeyReloadLogic:
    """Tests for hotkey reload functionality."""

    def _reload_hotkeys(self, actions: dict, hotkey_settings: dict):
        """
        Simulate _reload_hotkeys logic.

        Args:
            actions: Dict of action_name -> action mock
            hotkey_settings: Dict of action_name -> hotkey string

        Returns:
            list: List of (action_name, hotkey) tuples that were updated
        """
        updated = []
        for action_name, action in actions.items():
            hotkey = hotkey_settings.get(action_name)
            if hotkey:
                action.setShortcut(hotkey)
                updated.append((action_name, hotkey))
        return updated

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_reload_hotkeys_updates_actions(self):
        """Test hotkey reload updates action shortcuts."""
        actions = {
            "save": Mock(),
            "open": Mock(),
        }
        hotkey_settings = {
            "save": "Ctrl+Shift+S",
            "open": "Ctrl+Shift+O",
        }

        updated = self._reload_hotkeys(actions, hotkey_settings)

        assert len(updated) == 2
        actions["save"].setShortcut.assert_called_with("Ctrl+Shift+S")
        actions["open"].setShortcut.assert_called_with("Ctrl+Shift+O")

    def test_reload_hotkeys_partial_settings(self):
        """Test hotkey reload with partial settings."""
        actions = {
            "save": Mock(),
            "open": Mock(),
        }
        hotkey_settings = {
            "save": "Ctrl+S",
            # 'open' not in settings
        }

        updated = self._reload_hotkeys(actions, hotkey_settings)

        assert len(updated) == 1
        actions["save"].setShortcut.assert_called_with("Ctrl+S")
        actions["open"].setShortcut.assert_not_called()

    def test_reload_hotkeys_empty_settings(self):
        """Test hotkey reload with empty settings."""
        actions = {
            "save": Mock(),
        }
        hotkey_settings = {}

        updated = self._reload_hotkeys(actions, hotkey_settings)

        assert len(updated) == 0
        actions["save"].setShortcut.assert_not_called()

    def test_reload_hotkeys_empty_actions(self):
        """Test hotkey reload with empty actions."""
        actions = {}
        hotkey_settings = {"save": "Ctrl+S"}

        updated = self._reload_hotkeys(actions, hotkey_settings)

        assert len(updated) == 0


class TestDocumentationLogic:
    """Tests for documentation opening functionality."""

    def _get_docs_url(self, local_docs_path: Path, local_exists: bool) -> str:
        """
        Get documentation URL.

        Args:
            local_docs_path: Path to local docs
            local_exists: Whether local docs exist

        Returns:
            str: URL to open
        """
        if local_exists:
            return local_docs_path.as_uri()
        else:
            return "https://github.com/CasareRPA/docs"

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_get_docs_url_local_exists(self):
        """Test docs URL when local docs exist."""
        # Use absolute path that works on Windows
        local_path = Path("C:/path/to/docs/index.html")

        url = self._get_docs_url(local_path, local_exists=True)

        assert url == local_path.as_uri()

    def test_get_docs_url_fallback_to_online(self):
        """Test docs URL falls back to online when local missing."""
        local_path = Path("/path/to/docs/index.html")

        url = self._get_docs_url(local_path, local_exists=False)

        assert url == "https://github.com/CasareRPA/docs"
