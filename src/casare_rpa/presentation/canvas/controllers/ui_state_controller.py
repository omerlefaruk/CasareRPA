"""
UI State Controller for Canvas.

Manages persistence and restoration of UI state including:
- Window geometry (size, position)
- Dock widget positions and visibility
- Panel states
- Recent files list
- Last opened directory
- UI preferences
"""

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QByteArray, QSettings, QTimer, Signal

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class UIStateController(BaseController):
    """
    Controller for managing UI state persistence.

    Handles saving and restoring:
    - Window geometry and state
    - Dock widget positions and visibility
    - Panel tab selections
    - Recent files list
    - Last opened directory
    - Various UI preferences

    Signals:
        state_saved: Emitted after state is successfully saved
        state_restored: Emitted after state is successfully restored
        state_reset: Emitted after state is reset to defaults
        recent_files_changed: Emitted when recent files list changes (list[dict])
    """

    # Signals
    state_saved = Signal()
    state_restored = Signal()
    state_reset = Signal()
    recent_files_changed = Signal(list)

    # Settings keys
    _KEY_VERSION = "uiStateVersion"
    _KEY_GEOMETRY = "geometry"
    _KEY_WINDOW_STATE = "windowState"
    _KEY_BOTTOM_PANEL_VISIBLE = "bottomPanelVisible"
    _KEY_BOTTOM_PANEL_TAB = "bottomPanelTab"
    _KEY_EXECUTION_TIMELINE_VISIBLE = "executionTimelineVisible"
    _KEY_MINIMAP_VISIBLE = "minimapVisible"
    _KEY_LAST_DIRECTORY = "lastDirectory"
    _KEY_AUTO_SAVE_ENABLED = "autoSaveEnabled"
    _KEY_AUTO_VALIDATE_ENABLED = "autoValidateEnabled"

    # Current version - increment when settings structure changes incompatibly
    _CURRENT_VERSION = 2

    # Auto-save delay in milliseconds
    _AUTO_SAVE_DELAY_MS = 1000

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize UI state controller.

        Args:
            main_window: Reference to main window
        """
        super().__init__(main_window)
        self._settings: QSettings | None = None
        self._auto_save_timer: QTimer | None = None
        self._pending_save: bool = False

    def initialize(self) -> None:
        """Initialize controller resources and connections."""
        super().initialize()

        # Create QSettings instance
        self._settings = QSettings("CasareRPA", "Canvas")

        # Create auto-save timer
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._on_auto_save_timeout)

        # Connect dock widget signals for auto-save
        self._connect_dock_signals()

        logger.debug("UIStateController initialized")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        # Stop and clean up timer
        if self._auto_save_timer:
            self._auto_save_timer.stop()
            self._auto_save_timer = None

        # Save state before cleanup
        if self._pending_save:
            self.save_state()

        self._settings = None
        super().cleanup()

    def _connect_dock_signals(self) -> None:
        """Connect dock widget signals for auto-save on state changes."""
        mw = self.main_window

        # Bottom panel - use property accessor
        # Timeline is now a tab in bottom panel, no separate dock needed
        if mw.bottom_panel:
            mw.bottom_panel.dockLocationChanged.connect(self.schedule_auto_save)
            mw.bottom_panel.visibilityChanged.connect(self.schedule_auto_save)
            mw.bottom_panel.topLevelChanged.connect(self.schedule_auto_save)

    # ==================== Core State Methods ====================

    def save_state(self) -> None:
        """
        Save all UI state to QSettings.

        Saves window geometry, dock positions, panel visibility,
        and other UI preferences.
        """
        if not self._settings:
            logger.warning("Cannot save UI state: settings not initialized")
            return

        try:
            # Save version for compatibility checking
            self._settings.setValue(self._KEY_VERSION, self._CURRENT_VERSION)

            # Save window geometry and state
            self.save_window_geometry()

            # Save panel states
            self.save_panel_states()

            # Sync to disk
            self._settings.sync()

            self._pending_save = False
            self.state_saved.emit()
            logger.debug("UI state saved successfully")

        except Exception as e:
            logger.warning(f"Failed to save UI state: {e}")

    def restore_state(self) -> None:
        """
        Restore all UI state from QSettings.

        Restores window geometry, dock positions, panel visibility,
        and other UI preferences from the previous session.
        """
        if not self._settings:
            logger.warning("Cannot restore UI state: settings not initialized")
            return

        try:
            # Check if there's saved state
            if not self._settings.contains(self._KEY_GEOMETRY):
                logger.debug("No saved UI state found, using defaults")
                return

            # Check version compatibility
            saved_version = self._settings.value(self._KEY_VERSION, 0, type=int)
            if saved_version != self._CURRENT_VERSION:
                logger.info(
                    f"UI state version mismatch ({saved_version} vs "
                    f"{self._CURRENT_VERSION}), using defaults"
                )
                self.reset_state()
                return

            # Restore window geometry
            self.restore_window_geometry()

            # Restore panel states
            self.restore_panel_states()

            self.state_restored.emit()
            logger.debug("UI state restored from previous session")

        except Exception as e:
            logger.warning(f"Failed to restore UI state: {e}")
            # Reset on failure to prevent broken UI
            try:
                self.reset_state()
            except Exception:
                pass

    def reset_state(self) -> None:
        """
        Clear all saved UI state and reset to defaults.

        This removes all persisted settings and allows the UI
        to use its default layout and configuration.
        """
        if not self._settings:
            logger.warning("Cannot reset UI state: settings not initialized")
            return

        try:
            self._settings.clear()
            self._settings.sync()
            self.state_reset.emit()
            logger.info("UI state settings cleared and reset to defaults")
        except Exception as e:
            logger.warning(f"Failed to clear UI state: {e}")

    def schedule_auto_save(self) -> None:
        """
        Schedule an automatic state save.

        Uses debouncing to avoid excessive saves when multiple
        state changes occur in quick succession.
        """
        if self._auto_save_timer:
            self._pending_save = True
            self._auto_save_timer.start(self._AUTO_SAVE_DELAY_MS)

    def _on_auto_save_timeout(self) -> None:
        """Handle auto-save timer timeout."""
        if self._pending_save:
            self.save_state()

    # ==================== Window Geometry ====================

    def save_window_geometry(self) -> None:
        """Save window size and position to settings."""
        if not self._settings:
            return

        try:
            self._settings.setValue(self._KEY_GEOMETRY, self.main_window.saveGeometry())
            self._settings.setValue(self._KEY_WINDOW_STATE, self.main_window.saveState())
        except Exception as e:
            logger.warning(f"Failed to save window geometry: {e}")

    def restore_window_geometry(self) -> None:
        """Restore dock/toolbar layout from settings (not window size/position).

        Note: Window geometry (size, position, maximized state) is intentionally
        NOT restored to avoid slow startup from auto-maximize behavior.
        Window always starts at default size (1280x720) for faster startup.
        """
        if not self._settings:
            return

        try:
            # NOTE: Geometry restore disabled - window starts at default size
            # Users can maximize manually if desired
            # geometry = self._settings.value(self._KEY_GEOMETRY)
            # if geometry and isinstance(geometry, QByteArray):
            #     self.main_window.restoreGeometry(geometry)

            # Restore window state (dock positions, toolbars, etc.) - keep this
            state = self._settings.value(self._KEY_WINDOW_STATE)
            if state and isinstance(state, QByteArray):
                if not self.main_window.restoreState(state):
                    logger.warning("Failed to restore window state, using defaults")
                    self.reset_state()
                    return

        except Exception as e:
            logger.warning(f"Failed to restore window geometry: {e}")
            self.reset_state()

    # ==================== Panel States ====================

    def save_panel_states(self) -> None:
        """Save all panel visibility states to settings."""
        if not self._settings:
            return

        mw = self.main_window

        try:
            # Bottom panel - use property accessor
            if mw.bottom_panel:
                self._settings.setValue(self._KEY_BOTTOM_PANEL_VISIBLE, mw.bottom_panel.isVisible())
                # Tab widget is internal to bottom panel, keep private access
                if hasattr(mw.bottom_panel, "_tab_widget"):
                    self._settings.setValue(
                        self._KEY_BOTTOM_PANEL_TAB,
                        mw.bottom_panel._tab_widget.currentIndex(),
                    )

            # Execution timeline is now a tab in bottom panel (no separate dock)

            # Minimap - use property accessor
            if mw.minimap:
                self._settings.setValue(self._KEY_MINIMAP_VISIBLE, mw.minimap.isVisible())

        except Exception as e:
            logger.warning(f"Failed to save panel states: {e}")

    def restore_panel_states(self) -> None:
        """Restore all panel visibility states from settings."""
        if not self._settings:
            return

        mw = self.main_window

        try:
            # Bottom panel - use property accessor
            if mw.bottom_panel:
                visible = self._settings.value(self._KEY_BOTTOM_PANEL_VISIBLE, True, type=bool)
                mw.bottom_panel.setVisible(visible)

                # Restore selected tab (internal to bottom panel)
                tab_index = self._settings.value(self._KEY_BOTTOM_PANEL_TAB, 0, type=int)
                if hasattr(mw.bottom_panel, "_tab_widget"):
                    tab_count = mw.bottom_panel._tab_widget.count()
                    if 0 <= tab_index < tab_count:
                        mw.bottom_panel._tab_widget.setCurrentIndex(tab_index)

            # Execution timeline is now a tab in bottom panel (no separate dock)

            # Minimap - use property accessor
            if mw.minimap:
                visible = self._settings.value(self._KEY_MINIMAP_VISIBLE, False, type=bool)
                mw.minimap.setVisible(visible)
                if hasattr(mw, "action_toggle_minimap"):
                    mw.action_toggle_minimap.setChecked(visible)

        except Exception as e:
            logger.warning(f"Failed to restore panel states: {e}")

    # ==================== Directory Management ====================

    def get_last_directory(self) -> Path | None:
        """
        Get the last opened directory.

        Returns:
            Path to last directory, or None if not set or invalid
        """
        if not self._settings:
            return None

        try:
            path_str = self._settings.value(self._KEY_LAST_DIRECTORY, "", type=str)
            if path_str:
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    return path
        except Exception as e:
            logger.debug(f"Could not get last directory: {e}")

        return None

    def set_last_directory(self, directory: Path) -> None:
        """
        Set the last opened directory.

        Args:
            directory: Path to directory
        """
        if not self._settings:
            return

        try:
            if directory.exists() and directory.is_dir():
                self._settings.setValue(self._KEY_LAST_DIRECTORY, str(directory.absolute()))
                self._settings.sync()
        except Exception as e:
            logger.debug(f"Could not set last directory: {e}")

    # ==================== Recent Files Management ====================

    def get_recent_files(self) -> list[dict]:
        """
        Get the recent files list.

        Returns:
            List of dicts with 'path', 'name', 'last_opened' keys
        """
        from ....application.workflow.recent_files import get_recent_files_manager

        try:
            manager = get_recent_files_manager()
            return manager.get_recent_files()
        except Exception as e:
            logger.warning(f"Could not get recent files: {e}")
            return []

    def add_recent_file(self, file_path: Path) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the workflow file
        """
        from ....application.workflow.recent_files import get_recent_files_manager

        try:
            manager = get_recent_files_manager()
            manager.add_file(file_path)

            # Also update last directory
            if file_path.parent.exists():
                self.set_last_directory(file_path.parent)

            self.recent_files_changed.emit(self.get_recent_files())
        except Exception as e:
            logger.warning(f"Could not add recent file: {e}")

    def remove_recent_file(self, file_path: Path) -> None:
        """
        Remove a file from the recent files list.

        Args:
            file_path: Path to remove
        """
        from ....application.workflow.recent_files import get_recent_files_manager

        try:
            manager = get_recent_files_manager()
            manager.remove_file(file_path)
            self.recent_files_changed.emit(self.get_recent_files())
        except Exception as e:
            logger.warning(f"Could not remove recent file: {e}")

    def clear_recent_files(self) -> None:
        """Clear the entire recent files list."""
        from ....application.workflow.recent_files import get_recent_files_manager

        try:
            manager = get_recent_files_manager()
            manager.clear()
            self.recent_files_changed.emit([])
            logger.info("Recent files list cleared")
        except Exception as e:
            logger.warning(f"Could not clear recent files: {e}")

    # ==================== UI Preferences ====================

    def get_auto_save_enabled(self) -> bool:
        """
        Check if auto-save is enabled.

        Returns:
            True if auto-save is enabled
        """
        if not self._settings:
            return True  # Default to enabled

        return self._settings.value(self._KEY_AUTO_SAVE_ENABLED, True, type=bool)

    def set_auto_save_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto-save.

        Args:
            enabled: Whether to enable auto-save
        """
        if not self._settings:
            return

        self._settings.setValue(self._KEY_AUTO_SAVE_ENABLED, enabled)
        self._settings.sync()

    def get_auto_validate_enabled(self) -> bool:
        """
        Check if auto-validation is enabled.

        Returns:
            True if auto-validation is enabled
        """
        if not self._settings:
            return True  # Default to enabled

        return self._settings.value(self._KEY_AUTO_VALIDATE_ENABLED, True, type=bool)

    def set_auto_validate_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto-validation.

        Args:
            enabled: Whether to enable auto-validation
        """
        if not self._settings:
            return

        self._settings.setValue(self._KEY_AUTO_VALIDATE_ENABLED, enabled)
        self._settings.sync()

    # ==================== Utility Methods ====================

    def is_initialized(self) -> bool:
        """Check if controller is initialized."""
        return self._initialized and self._settings is not None

    def get_settings(self) -> QSettings | None:
        """
        Get the QSettings instance for advanced usage.

        Returns:
            QSettings instance or None
        """
        return self._settings
