"""
Menu and action management controller.

Handles all menu-related operations:
- Menu bar creation and updates
- Toolbar creation and updates
- Action state management
- Hotkey management
- Recent files menu
"""

from typing import Dict, Optional, TYPE_CHECKING
from pathlib import Path
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from loguru import logger

from .base_controller import BaseController

if TYPE_CHECKING:
    from ....canvas.main_window import MainWindow


class MenuController(BaseController):
    """
    Manages menus, toolbars, and actions.

    Single Responsibility: Menu/action lifecycle and state management.

    Signals:
        action_state_changed: Emitted when an action's enabled state changes (str: action_name, bool: enabled)
        recent_files_updated: Emitted when recent files list is updated
        hotkey_changed: Emitted when a hotkey is modified (str: action_name, str: new_shortcut)
    """

    # Signals
    action_state_changed = Signal(str, bool)  # action_name, enabled
    recent_files_updated = Signal()
    hotkey_changed = Signal(str, str)  # action_name, new_shortcut

    def __init__(self, main_window: "MainWindow"):
        """Initialize menu controller."""
        super().__init__(main_window)
        self._actions: Dict[str, QAction] = {}

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("MenuController initialized")
        self._collect_actions()

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

        from ....canvas.workflow.recent_files import get_recent_files_manager

        menu.clear()

        manager = get_recent_files_manager()
        recent = manager.get_recent_files()

        if not recent:
            action = menu.addAction("(No recent files)")
            action.setEnabled(False)
            self.recent_files_updated.emit()
            return

        # Add up to 10 recent files
        for i, file_info in enumerate(recent[:10]):
            path = file_info["path"]
            name = file_info["name"]
            action = menu.addAction(f"&{i+1}. {name}")
            action.setToolTip(path)
            action.triggered.connect(
                lambda checked, p=path: self._on_open_recent_file(p)
            )

        self.recent_files_updated.emit()

    def open_hotkey_manager(self) -> None:
        """Open the hotkey manager dialog."""
        logger.info("Opening hotkey manager")

        from ....canvas.toolbar.hotkey_manager import HotkeyManagerDialog

        dialog = HotkeyManagerDialog(self._actions, self.main_window)
        if dialog.exec():
            logger.info("Hotkey settings updated")
            self._reload_hotkeys()

    def open_preferences(self) -> None:
        """Open the preferences dialog."""
        logger.info("Opening preferences dialog")

        from ....canvas.dialogs.preferences_dialog import PreferencesDialog
        from PySide6.QtWidgets import QDialog

        dialog = PreferencesDialog(self.main_window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("Preferences saved")
            # Emit signal so app can update settings
            if hasattr(self.main_window, "preferences_saved"):
                self.main_window.preferences_saved.emit()

    def open_performance_dashboard(self) -> None:
        """Open the performance dashboard dialog."""
        logger.info("Opening performance dashboard")

        from ....canvas.execution.performance_dashboard import (
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

        # File actions
        self._actions["new"] = self.main_window.action_new
        self._actions["open"] = self.main_window.action_open
        self._actions["save"] = self.main_window.action_save
        self._actions["save_as"] = self.main_window.action_save_as

        # Edit actions
        if hasattr(self.main_window, "action_undo"):
            self._actions["undo"] = self.main_window.action_undo
        if hasattr(self.main_window, "action_redo"):
            self._actions["redo"] = self.main_window.action_redo
        if hasattr(self.main_window, "action_cut"):
            self._actions["cut"] = self.main_window.action_cut
        if hasattr(self.main_window, "action_copy"):
            self._actions["copy"] = self.main_window.action_copy
        if hasattr(self.main_window, "action_paste"):
            self._actions["paste"] = self.main_window.action_paste
        if hasattr(self.main_window, "action_delete"):
            self._actions["delete"] = self.main_window.action_delete

        # View actions
        if hasattr(self.main_window, "action_zoom_in"):
            self._actions["zoom_in"] = self.main_window.action_zoom_in
        if hasattr(self.main_window, "action_zoom_out"):
            self._actions["zoom_out"] = self.main_window.action_zoom_out
        if hasattr(self.main_window, "action_zoom_reset"):
            self._actions["zoom_reset"] = self.main_window.action_zoom_reset
        if hasattr(self.main_window, "action_fit_view"):
            self._actions["fit_view"] = self.main_window.action_fit_view

        # Execution actions
        if hasattr(self.main_window, "action_run"):
            self._actions["run"] = self.main_window.action_run
        if hasattr(self.main_window, "action_run_to_node"):
            self._actions["run_to_node"] = self.main_window.action_run_to_node
        if hasattr(self.main_window, "action_pause"):
            self._actions["pause"] = self.main_window.action_pause
        if hasattr(self.main_window, "action_stop"):
            self._actions["stop"] = self.main_window.action_stop

        logger.info(f"Collected {len(self._actions)} actions")

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

    def _on_open_recent_file(self, file_path: str) -> None:
        """
        Handle opening a recent file.

        Args:
            file_path: Path to file to open
        """
        logger.info(f"Opening recent file: {file_path}")

        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.main_window,
                "File Not Found",
                f"The file no longer exists:\n{file_path}",
            )

            # Remove from recent files
            from ....canvas.workflow.recent_files import get_recent_files_manager

            manager = get_recent_files_manager()
            manager.remove_file(file_path)
            self.update_recent_files_menu()
            return

        # Delegate to workflow controller
        if hasattr(self.main_window, "_workflow_controller"):
            # Set the file directly and emit the load signal
            self.main_window.workflow_open.emit(file_path)
