"""
Autosave management component.

This component handles automatic workflow saving functionality:
- Periodic autosave based on settings
- Crash recovery
- Backup management
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import QTimer
from loguru import logger

from .base_component import BaseComponent
from ...utils.settings_manager import get_settings_manager

if TYPE_CHECKING:
    from ..main_window import MainWindow


class AutosaveComponent(BaseComponent):
    """
    Manages automatic workflow saving.

    Responsibilities:
    - Periodic autosave timer management
    - Settings synchronization
    - Autosave execution
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)
        self._autosave_timer: Optional[QTimer] = None

    def _do_initialize(self) -> None:
        """Initialize the autosave component."""
        # Create autosave timer
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._on_autosave)

        # Configure timer based on settings
        self._update_timer_from_settings()

        # Connect to preferences changes
        self._main_window.preferences_saved.connect(self.update_settings)

        logger.info("AutosaveComponent initialized")

    def _update_timer_from_settings(self) -> None:
        """Update autosave timer based on current settings."""
        settings = get_settings_manager()

        if settings.is_autosave_enabled():
            interval_minutes = settings.get_autosave_interval()
            interval_ms = interval_minutes * 60 * 1000
            self._autosave_timer.start(interval_ms)
            logger.info(f"Autosave enabled: every {interval_minutes} minute(s)")
        else:
            self._autosave_timer.stop()
            logger.info("Autosave disabled")

    def update_settings(self) -> None:
        """Update autosave timer based on current settings."""
        if self._autosave_timer:
            self._autosave_timer.stop()

        self._update_timer_from_settings()

    def _on_autosave(self) -> None:
        """
        Handle autosave timer trigger.

        Only saves if:
        - Autosave is enabled in settings
        - A workflow file is currently open
        """
        try:
            settings = get_settings_manager()

            # Check if autosave is still enabled
            if not settings.is_autosave_enabled():
                self._autosave_timer.stop()
                logger.debug("Autosave timer stopped (disabled in settings)")
                return

            # Check if there's a current file to save
            current_file = self._main_window.get_current_file()
            if not current_file:
                logger.debug("Autosave skipped: no file currently open")
                return

            # Perform autosave
            logger.info(f"Auto-saving workflow: {current_file}")

            # Trigger save through main window signal
            # This delegates to WorkflowLifecycleComponent
            self._main_window.workflow_save.emit()

        except Exception as e:
            logger.error(f"Autosave failed: {e}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._autosave_timer:
            self._autosave_timer.stop()
            self._autosave_timer = None
        logger.debug("AutosaveComponent cleaned up")
