"""
Menu and action management controller.

Handles all menu-related operations:
- Menu bar creation and updates
- Toolbar creation and updates
- Action state management
- Hotkey management
- Recent files menu
- About and help dialogs
- Desktop selector builder
"""

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController
from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system import TOKENS

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class MenuController(BaseController):
    """
    Manages menus, toolbars, and actions.

    Single Responsibility: Menu/action lifecycle and state management.

    Signals:
        action_state_changed: Emitted when an action's enabled state changes (str: action_name, bool: enabled)
        recent_files_updated: Emitted when recent files list is updated
        hotkey_changed: Emitted when a hotkey is modified (str: action_name, str: new_shortcut)
        recent_file_opened: Emitted when a recent file is opened (str: file_path)
        recent_files_cleared: Emitted when recent files list is cleared
        about_dialog_shown: Emitted when about dialog is displayed
        desktop_selector_shown: Emitted when desktop selector builder is displayed
    """

    # Signals
    action_state_changed = Signal(str, bool)  # action_name, enabled
    recent_files_updated = Signal()
    hotkey_changed = Signal(str, str)  # action_name, new_shortcut
    recent_file_opened = Signal(str)  # file_path
    recent_files_cleared = Signal()
    about_dialog_shown = Signal()
    desktop_selector_shown = Signal()

    def __init__(self, main_window: "MainWindow"):
        """Initialize menu controller."""
        super().__init__(main_window)
        self._actions: dict[str, QAction] = {}

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        self._collect_actions()
        # Populate recent files menu on startup
        self.update_recent_files_menu()

    def _show_styled_message(
        self,
        title: str,
        text: str,
        info: str = "",
        icon: QMessageBox.Icon = QMessageBox.Icon.Warning,
    ) -> None:
        """Show a styled QMessageBox matching UI Explorer theme."""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle(title)
        msg.setText(text)
        if info:
            msg.setInformativeText(info)
        msg.setIcon(icon)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {THEME.bg_darkest}; }}
            QMessageBox QLabel {{ color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px; }}
            QPushButton {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: 0 16px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
                font-weight: TOKENS.sizes.dialog_md_width;
                min-height: {TOKENS.sizes.button_lg}px;
                min-width: {TOKENS.sizes.button_min_width}px;
            }}
            QPushButton:hover {{ background: {THEME.bg_medium}; border-color: {THEME.accent_primary}; color: white; }}
            QPushButton:default {{ background: {THEME.accent_primary}; border-color: {THEME.accent_primary}; color: white; }}
        """)
        msg.exec()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("MenuController cleanup")
        self._actions.clear()

    def update_action_state(self, action_name: str, enabled: bool) -> None:
        """
        Update an action's enabled state.

        Args:
            action_name: Name of action (e.g., "save", "run", "pause")
            enabled: True to enable, False to disable
        """
        logger.debug(f"Updating action state: {action_name} = {enabled}")

        action = self._actions.get(action_name)
        if action:
            action.setEnabled(enabled)
            self.action_state_changed.emit(action_name, enabled)
        else:
            logger.warning(f"Action not found: {action_name}")

    def update_recent_files_menu(self) -> None:
        """Update the recent files submenu."""
        logger.debug("Updating recent files menu")

        menu = self.main_window.get_recent_files_menu()
        if not menu:
            return

        from ....application.workflow.recent_files import get_recent_files_manager

        menu.clear()

        manager = get_recent_files_manager()
        recent = manager.get_recent_files()

        if not recent:
            action = menu.addAction("(No recent files)")
            action.setEnabled(False)
            self.recent_files_updated.emit()
            return

        from functools import partial

        # Add up to 10 recent files
        for i, file_info in enumerate(recent[:10]):
            path = file_info["path"]
            name = file_info["name"]
            action = menu.addAction(f"&{i+1}. {name}")
            action.setToolTip(path)
            action.triggered.connect(partial(self._on_open_recent_file, path))

        self.recent_files_updated.emit()

    def open_hotkey_manager(self) -> None:
        """Open the hotkey manager dialog."""
        logger.info("Opening hotkey manager")

        from ..ui.toolbars.hotkey_manager import HotkeyManagerDialog

        # Use ActionManager's actions which are always populated
        actions = self.main_window._action_manager.get_all_actions()
        dialog = HotkeyManagerDialog(actions, self.main_window)
        if dialog.exec():
            logger.info("Hotkey settings updated")
            self._reload_hotkeys()

    def open_preferences(self) -> None:
        """Open the preferences dialog."""
        logger.info("Opening preferences dialog")

        from PySide6.QtWidgets import QDialog

        from ....utils.settings_manager import get_settings_manager
        from ..ui.dialogs.preferences_dialog import PreferencesDialog

        # Get current settings
        settings_manager = get_settings_manager()
        current_prefs = self._get_all_preferences(settings_manager)

        dialog = PreferencesDialog(preferences=current_prefs, parent=self.main_window)

        # Connect preferences_changed signal to save settings
        dialog.preferences_changed.connect(
            lambda prefs: self._save_preferences(settings_manager, prefs)
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("Preferences saved")
            # Emit signal so app can update settings
            if hasattr(self.main_window, "preferences_saved"):
                self.main_window.preferences_saved.emit()

    def _get_all_preferences(self, settings_manager) -> dict:
        """Get all preferences from settings manager."""
        return {
            # General
            "theme": settings_manager.get("ui.theme", "Dark"),
            "language": settings_manager.get("general.language", "English"),
            "restore_session": settings_manager.get("general.restore_session", True),
            "check_updates": settings_manager.get("general.check_updates", True),
            # Autosave
            "autosave_enabled": settings_manager.get("autosave.enabled", True),
            "autosave_interval": settings_manager.get("autosave.interval_minutes", 5),
            "create_backups": settings_manager.get("autosave.create_backups", True),
            "max_backups": settings_manager.get("autosave.max_backups", 5),
            # Editor
            "show_grid": settings_manager.get("editor.show_grid", True),
            "snap_to_grid": settings_manager.get("editor.snap_to_grid", True),
            "grid_size": settings_manager.get("editor.grid_size", 20),
            "auto_align": settings_manager.get("editor.auto_align", False),
            "show_node_ids": settings_manager.get("editor.show_node_ids", False),
            "connection_style": settings_manager.get("editor.connection_style", "Curved"),
            "show_port_labels": settings_manager.get("editor.show_port_labels", True),
            # Performance
            "enable_antialiasing": settings_manager.get("performance.antialiasing", True),
            "enable_shadows": settings_manager.get("performance.shadows", False),
            "fps_limit": settings_manager.get("performance.fps_limit", 60),
            "max_undo_steps": settings_manager.get("performance.max_undo_steps", 100),
            "cache_size": settings_manager.get(
                "performance.cache_size_mb", TOKENS.sizes.panel_min_width
            ),
        }

    def _save_preferences(self, settings_manager, prefs: dict) -> None:
        """Save preferences to settings manager."""
        # General
        settings_manager.set("ui.theme", prefs.get("theme", "Dark"))
        settings_manager.set("general.language", prefs.get("language", "English"))
        settings_manager.set("general.restore_session", prefs.get("restore_session", True))
        settings_manager.set("general.check_updates", prefs.get("check_updates", True))
        # Autosave
        settings_manager.set("autosave.enabled", prefs.get("autosave_enabled", True))
        settings_manager.set("autosave.interval_minutes", prefs.get("autosave_interval", 5))
        settings_manager.set("autosave.create_backups", prefs.get("create_backups", True))
        settings_manager.set("autosave.max_backups", prefs.get("max_backups", 5))
        # Editor
        settings_manager.set("editor.show_grid", prefs.get("show_grid", True))
        settings_manager.set("editor.snap_to_grid", prefs.get("snap_to_grid", True))
        settings_manager.set("editor.grid_size", prefs.get("grid_size", 20))
        settings_manager.set("editor.auto_align", prefs.get("auto_align", False))
        settings_manager.set("editor.show_node_ids", prefs.get("show_node_ids", False))
        settings_manager.set("editor.connection_style", prefs.get("connection_style", "Curved"))
        settings_manager.set("editor.show_port_labels", prefs.get("show_port_labels", True))
        # Performance
        settings_manager.set("performance.antialiasing", prefs.get("enable_antialiasing", True))
        settings_manager.set("performance.shadows", prefs.get("enable_shadows", False))
        settings_manager.set("performance.fps_limit", prefs.get("fps_limit", 60))
        settings_manager.set("performance.max_undo_steps", prefs.get("max_undo_steps", 100))
        settings_manager.set(
            "performance.cache_size_mb", prefs.get("cache_size", TOKENS.sizes.panel_min_width)
        )

        logger.info("Preferences saved to settings manager")

    def open_performance_dashboard(self) -> None:
        """Open the performance dashboard dialog."""
        logger.info("Opening performance dashboard")

        from ..ui.widgets.performance_dashboard import (
            PerformanceDashboardDialog,
        )

        dialog = PerformanceDashboardDialog(self.main_window)
        dialog.exec()

    def open_command_palette(self) -> None:
        """Open the command palette dialog."""
        logger.info("Opening command palette")

        command_palette = self.main_window.get_command_palette()
        if command_palette:
            command_palette.show_palette()

    def _collect_actions(self) -> None:
        """Collect all actions from main window."""
        if not hasattr(self.main_window, "action_new"):
            return

        mw = self.main_window

        # File actions
        self._actions["new"] = mw.action_new
        self._actions["open"] = mw.action_open
        self._actions["save"] = mw.action_save
        self._actions["save_as"] = mw.action_save_as

        # Edit actions
        if hasattr(mw, "action_undo"):
            self._actions["undo"] = mw.action_undo
        if hasattr(mw, "action_redo"):
            self._actions["redo"] = mw.action_redo
        if hasattr(mw, "action_cut"):
            self._actions["cut"] = mw.action_cut
        if hasattr(mw, "action_copy"):
            self._actions["copy"] = mw.action_copy
        if hasattr(mw, "action_paste"):
            self._actions["paste"] = mw.action_paste
        if hasattr(mw, "action_delete"):
            self._actions["delete"] = mw.action_delete
        if hasattr(mw, "action_select_all"):
            self._actions["select_all"] = mw.action_select_all
        if hasattr(mw, "action_find_node"):
            self._actions["find_node"] = mw.action_find_node

        # Run actions
        if hasattr(mw, "action_run"):
            self._actions["run"] = mw.action_run
        if hasattr(mw, "action_pause"):
            self._actions["pause"] = mw.action_pause
        if hasattr(mw, "action_stop"):
            self._actions["stop"] = mw.action_stop
        if hasattr(mw, "action_debug"):
            self._actions["debug"] = mw.action_debug

        # Automation actions
        if hasattr(mw, "action_validate"):
            self._actions["validate"] = mw.action_validate
        if hasattr(mw, "action_record_workflow"):
            self._actions["record"] = mw.action_record_workflow
        if hasattr(mw, "action_pick_selector"):
            self._actions["pick_browser"] = mw.action_pick_selector
        if hasattr(mw, "action_desktop_selector_builder"):
            self._actions["pick_desktop"] = mw.action_desktop_selector_builder
        if hasattr(mw, "action_schedule"):
            self._actions["schedule"] = mw.action_schedule

    def _reload_hotkeys(self) -> None:
        """Reload hotkeys from settings."""
        from ....utils.hotkey_settings import get_hotkey_settings

        hotkey_settings = get_hotkey_settings()

        for action_name, action in self._actions.items():
            hotkey = hotkey_settings.get(action_name)
            if hotkey:
                from PySide6.QtGui import QKeySequence

                action.setShortcut(QKeySequence(hotkey))
                self.hotkey_changed.emit(action_name, hotkey)
                logger.debug(f"Updated hotkey: {action_name} -> {hotkey}")

    @Slot(str)
    def _on_open_recent_file(self, file_path: str) -> None:
        """Handle recent file selection."""

        logger.info(f"Opening recent file: {file_path}")

        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            self._show_styled_message(
                "File Not Found",
                f"The file no longer exists:\n{file_path}",
            )

            # Remove from recent files
            from ....application.workflow.recent_files import get_recent_files_manager

            manager = get_recent_files_manager()
            manager.remove_file(file_path)
            self.update_recent_files_menu()
            return

        # Delegate to workflow controller
        if hasattr(self.main_window, "_workflow_controller"):
            # Check for unsaved changes first
            workflow_controller = self.main_window._workflow_controller
            if not workflow_controller.check_unsaved_changes():
                return

            # Emit the load signal
            self.main_window.workflow_open.emit(file_path)
            self.main_window.set_current_file(path)
            self.main_window.set_modified(False)
            self.main_window.show_status(f"Opened: {path.name}", 3000)
            self.recent_file_opened.emit(file_path)

    # ==================== About Dialog ====================

    def show_about_dialog(self) -> None:
        """
        Show the About dialog with application information.

        Displays version info, credits, and application description.
        """
        logger.info("Showing about dialog")

        try:
            from casare_rpa.config import APP_NAME, APP_VERSION

            QMessageBox.about(
                self.main_window,
                f"About {APP_NAME}",
                f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
                f"<p>Windows Desktop RPA Platform</p>"
                f"<p>Visual workflow automation with node-based editor</p>"
                f"<p>Built with PySide6, NodeGraphQt, and Playwright</p>"
                f"<hr>"
                f"<p><b>Features:</b></p>"
                f"<ul>"
                f"<li>140+ automation nodes</li>"
                f"<li>Web automation with Playwright</li>"
                f"<li>Desktop automation with UIAutomation</li>"
                f"<li>Scheduling and triggers</li>"
                f"</ul>",
            )
            self.about_dialog_shown.emit()
        except Exception as e:
            logger.error(f"Failed to show about dialog: {e}")
            self._show_styled_message(
                "Error",
                f"Failed to show about dialog:\n{str(e)}",
                icon=QMessageBox.Icon.Critical,
            )

    # ==================== Desktop Selector Builder ====================

    def show_desktop_selector_builder(self) -> None:
        """
        Show the Desktop Selector Builder dialog.

        Opens the visual tool for building desktop element selectors.
        """
        logger.info("Opening desktop selector builder")

        try:
            from ..selectors.desktop_selector_builder import (
                DesktopSelectorBuilder,
            )

            dialog = DesktopSelectorBuilder(parent=self.main_window)

            if dialog.exec():
                selector = dialog.get_selected_selector()
                if selector:
                    logger.info(f"Selector selected from builder: {selector}")
                    # User can copy selector from here

            self.desktop_selector_shown.emit()
        except Exception as e:
            logger.error(f"Failed to open desktop selector builder: {e}")
            self._show_styled_message(
                "Error",
                f"Failed to open Desktop Selector Builder:\n{str(e)}",
                icon=QMessageBox.Icon.Critical,
            )

    # ==================== Recent Files Management ====================

    def add_recent_file(self, file_path: Path) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the workflow file to add
        """
        logger.debug(f"Adding to recent files: {file_path}")

        try:
            from ....application.workflow.recent_files import get_recent_files_manager

            manager = get_recent_files_manager()
            path = Path(file_path) if isinstance(file_path, str) else file_path
            manager.add_file(path)
            self.update_recent_files_menu()
        except Exception as e:
            logger.error(f"Failed to add recent file: {e}")

    def get_recent_files(self) -> list[dict]:
        """
        Get the list of recent files.

        Returns:
            List of dicts with 'path', 'name', 'last_opened' keys
        """
        try:
            from ....application.workflow.recent_files import get_recent_files_manager

            manager = get_recent_files_manager()
            return manager.get_recent_files()
        except Exception as e:
            logger.error(f"Failed to get recent files: {e}")
            return []

    def open_recent_file(self, file_path: str) -> None:
        """
        Open a recent file by path.

        Args:
            file_path: Path to the file to open
        """
        self._on_open_recent_file(file_path)

    def clear_recent_files(self) -> None:
        """
        Clear the recent files list.

        Removes all entries from the recent files list and updates the menu.
        """
        logger.info("Clearing recent files")

        try:
            from ....application.workflow.recent_files import get_recent_files_manager

            manager = get_recent_files_manager()
            manager.clear()
            self.update_recent_files_menu()
            self.main_window.show_status("Recent files cleared", 3000)
            self.recent_files_cleared.emit()
        except Exception as e:
            logger.error(f"Failed to clear recent files: {e}")
            self._show_styled_message(
                "Error",
                f"Failed to clear recent files:\n{str(e)}",
            )

    # ==================== Help Menu Operations ====================

    def show_documentation(self) -> None:
        """
        Open the documentation in the default web browser.

        Opens the online documentation or local docs if available.
        """
        logger.info("Opening documentation")

        try:
            import webbrowser

            # Try local docs first, then online
            from casare_rpa.config import PROJECT_ROOT

            # MkDocs builds to site/ directory at project root
            local_docs = PROJECT_ROOT / "site" / "index.html"
            if local_docs.exists():
                webbrowser.open(local_docs.as_uri())
            else:
                # Fallback to online docs (placeholder URL)
                webbrowser.open("https://github.com/CasareRPA/docs")

            self.main_window.show_status("Documentation opened in browser", 3000)
        except Exception as e:
            logger.error(f"Failed to open documentation: {e}")
            self._show_styled_message(
                "Error",
                f"Failed to open documentation:\n{str(e)}",
            )

    def show_keyboard_shortcuts(self) -> None:
        """
        Show the keyboard shortcuts dialog.

        Displays a reference dialog with all available keyboard shortcuts.
        """
        logger.info("Showing keyboard shortcuts")

        try:
            # Build shortcuts list from collected actions
            shortcuts_text = "<h3>Keyboard Shortcuts</h3><table>"
            shortcuts_text += "<tr><th>Action</th><th>Shortcut</th></tr>"

            shortcut_list = [
                ("New Workflow", "Ctrl+N"),
                ("Open Workflow", "Ctrl+O"),
                ("Save Workflow", "Ctrl+S"),
                ("Save As", "Ctrl+Shift+S"),
                ("Undo", "Ctrl+Z"),
                ("Redo", "Ctrl+Y / Ctrl+Shift+Z"),
                ("Cut", "Ctrl+X"),
                ("Copy", "Ctrl+C"),
                ("Paste", "Ctrl+V"),
                ("Delete", "X"),
                ("Select All", "Ctrl+A"),
                ("Find Node", "Ctrl+F"),
                ("Run Workflow", "F3"),
                ("Run to Node", "F4"),
                ("Run Single Node", "F5"),
                ("Pause/Resume", "F6"),
                ("Stop", "F7"),
                ("Zoom In", "Ctrl++"),
                ("Zoom Out", "Ctrl+-"),
                ("Reset Zoom", "Ctrl+0"),
                ("Toggle Minimap", "Ctrl+M"),
                ("Command Palette", "Ctrl+Shift+P"),
                ("Preferences", "Ctrl+,"),
            ]

            for action, shortcut in shortcut_list:
                shortcuts_text += f"<tr><td>{action}</td><td><code>{shortcut}</code></td></tr>"

            shortcuts_text += "</table>"

            self._show_styled_message(
                "Keyboard Shortcuts",
                shortcuts_text,
                icon=QMessageBox.Icon.Information,
            )
        except Exception as e:
            logger.error(f"Failed to show keyboard shortcuts: {e}")

    def check_for_updates(self) -> None:
        """
        Check for application updates.

        Checks for newer versions and notifies the user.
        """
        logger.info("Checking for updates")

        try:
            from casare_rpa.config import APP_VERSION

            # This is a placeholder implementation
            # In a real implementation, this would check a server for updates
            self._show_styled_message(
                "Check for Updates",
                f"<p>Current version: <b>{APP_VERSION}</b></p>"
                f"<p>You are running the latest version.</p>"
                f"<p><i>Note: Automatic update checking is not yet implemented.</i></p>",
                icon=QMessageBox.Icon.Information,
            )
            self.main_window.show_status("Update check complete", 3000)
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            self._show_styled_message(
                "Error",
                f"Failed to check for updates:\n{str(e)}",
            )
