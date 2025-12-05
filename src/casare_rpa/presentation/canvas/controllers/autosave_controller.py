"""
Autosave controller for automatic workflow saving.

Handles automatic workflow saving functionality:
- Periodic autosave based on settings
- Autosave timer management
- Settings synchronization
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import QTimer, Signal
from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_types import EventType

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class AutosaveController(BaseController):
    """
    Manages automatic workflow saving.

    Single Responsibility: Periodic autosave execution and timer management.

    Signals:
        autosave_triggered: Emitted when autosave is triggered
        autosave_completed: Emitted when autosave completes successfully
        autosave_failed: Emitted when autosave fails (str: error_message)
    """

    # Signals
    autosave_triggered = Signal()
    autosave_completed = Signal()
    autosave_failed = Signal(str)  # error_message

    def __init__(self, main_window: "MainWindow"):
        """Initialize autosave controller."""
        super().__init__(main_window)
        self._autosave_timer: Optional[QTimer] = None
        self._event_bus = EventBus()

    def initialize(self) -> None:
        """Initialize controller and setup autosave timer."""
        super().initialize()

        # Create autosave timer
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._on_autosave_timer)

        # Configure timer based on settings
        self._update_timer_from_settings()

        # Subscribe to EventBus events
        self._event_bus.subscribe(
            EventType.PREFERENCES_UPDATED, self._on_preferences_updated
        )
        self._event_bus.subscribe(EventType.WORKFLOW_SAVED, self._on_workflow_saved)
        self._event_bus.subscribe(EventType.WORKFLOW_OPENED, self._on_workflow_opened)
        self._event_bus.subscribe(EventType.WORKFLOW_CLOSED, self._on_workflow_closed)

    def cleanup(self) -> None:
        """Clean up resources."""
        # Stop timer
        if self._autosave_timer:
            self._autosave_timer.stop()
            self._autosave_timer = None

        # Unsubscribe from events
        self._event_bus.unsubscribe(
            EventType.PREFERENCES_UPDATED, self._on_preferences_updated
        )
        self._event_bus.unsubscribe(EventType.WORKFLOW_SAVED, self._on_workflow_saved)
        self._event_bus.unsubscribe(EventType.WORKFLOW_OPENED, self._on_workflow_opened)
        self._event_bus.unsubscribe(EventType.WORKFLOW_CLOSED, self._on_workflow_closed)

        super().cleanup()
        logger.info("AutosaveController cleanup")

    # =========================================================================
    # Public API
    # =========================================================================

    def enable_autosave(self, interval_minutes: int) -> None:
        """
        Enable autosave with specified interval.

        Args:
            interval_minutes: Autosave interval in minutes
        """
        logger.debug(f"Enabling autosave: every {interval_minutes} minute(s)")

        if not self._autosave_timer:
            logger.error("Autosave timer not initialized")
            return

        # Convert minutes to milliseconds
        interval_ms = interval_minutes * 60 * 1000

        # Start timer
        self._autosave_timer.start(interval_ms)

    def disable_autosave(self) -> None:
        """Disable autosave."""
        logger.info("Disabling autosave")

        if self._autosave_timer:
            self._autosave_timer.stop()

    def update_interval(self, interval_minutes: int) -> None:
        """
        Update autosave interval.

        Args:
            interval_minutes: New interval in minutes
        """
        logger.info(f"Updating autosave interval: {interval_minutes} minute(s)")

        if not self._autosave_timer:
            logger.error("Autosave timer not initialized")
            return

        # Check if timer is active
        was_active = self._autosave_timer.isActive()

        # Stop timer
        self._autosave_timer.stop()

        # Restart with new interval if was active
        if was_active:
            self.enable_autosave(interval_minutes)

    def is_enabled(self) -> bool:
        """
        Check if autosave is currently enabled.

        Returns:
            bool: True if autosave timer is active
        """
        if not self._autosave_timer:
            return False
        return self._autosave_timer.isActive()

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _update_timer_from_settings(self) -> None:
        """Update autosave timer based on current settings."""
        from ....utils.settings_manager import get_settings_manager

        settings = get_settings_manager()

        if settings.is_autosave_enabled():
            interval_minutes = settings.get_autosave_interval()
            self.enable_autosave(interval_minutes)
        else:
            self.disable_autosave()

    def _perform_autosave(self) -> None:
        """
        Perform autosave operation.

        Only saves if:
        - Autosave is enabled in settings
        - A workflow file is currently open
        """
        try:
            from ....utils.settings_manager import get_settings_manager

            settings = get_settings_manager()

            # Check if autosave is still enabled
            if not settings.is_autosave_enabled():
                self.disable_autosave()
                logger.debug("Autosave skipped: disabled in settings")
                return

            # Check if there's a current file to save
            current_file = self.main_window.get_current_file()
            if not current_file:
                logger.debug("Autosave skipped: no file currently open")
                return

            # Emit signal
            self.autosave_triggered.emit()

            # Publish event
            event = Event(
                type=EventType.AUTOSAVE_TRIGGERED,
                source="AutosaveController",
                data={"file_path": str(current_file)},
            )
            self._event_bus.publish(event)

            logger.info(f"Auto-saving workflow: {current_file}")

            # Trigger save through main window
            # This delegates to WorkflowController
            if hasattr(self.main_window, "workflow_save"):
                self.main_window.workflow_save.emit()

                # Emit success signal
                self.autosave_completed.emit()

                # Publish success event
                success_event = Event(
                    type=EventType.AUTOSAVE_COMPLETED,
                    source="AutosaveController",
                    data={"file_path": str(current_file)},
                )
                self._event_bus.publish(success_event)

            else:
                logger.error("MainWindow does not have workflow_save signal")
                self._handle_autosave_failure("workflow_save signal not found")

        except Exception as e:
            logger.error(f"Autosave failed: {e}")
            self._handle_autosave_failure(str(e))

    def _handle_autosave_failure(self, error_message: str) -> None:
        """
        Handle autosave failure.

        Args:
            error_message: Error description
        """
        # Emit failure signal
        self.autosave_failed.emit(error_message)

        # Publish failure event
        event = Event(
            type=EventType.AUTOSAVE_FAILED,
            source="AutosaveController",
            data={"error": error_message},
        )
        self._event_bus.publish(event)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_autosave_timer(self) -> None:
        """Handle autosave timer timeout."""
        self._perform_autosave()

    def _on_preferences_updated(self, event: Event) -> None:
        """
        Handle preferences updated event.

        Re-synchronizes autosave timer with current settings.

        Args:
            event: The event object
        """
        logger.debug("Preferences updated, re-synchronizing autosave timer")

        # Stop current timer
        if self._autosave_timer:
            self._autosave_timer.stop()

        # Update from settings
        self._update_timer_from_settings()

    def _on_workflow_saved(self, event: Event) -> None:
        """
        Handle workflow saved event.

        Args:
            event: The event object
        """
        logger.debug("Workflow saved event received")
        # Could reset autosave timer here if desired

    def _on_workflow_opened(self, event: Event) -> None:
        """
        Handle workflow opened event.

        Args:
            event: The event object
        """
        logger.debug("Workflow opened event received")
        # Could restart autosave timer here if desired

    def _on_workflow_closed(self, event: Event) -> None:
        """
        Handle workflow closed event.

        Args:
            event: The event object
        """
        logger.debug("Workflow closed event received")
        # Autosave will be skipped automatically when no file is open
