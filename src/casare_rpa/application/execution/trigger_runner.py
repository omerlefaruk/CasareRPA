"""
CasareRPA - Canvas Trigger Runner

Manages trigger lifecycle in the Canvas application.
Starts/stops triggers and handles trigger events by running workflows.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from ...triggers.base import BaseTriggerConfig, BaseTrigger, TriggerEvent, TriggerType
from ...triggers.registry import get_trigger_registry

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.app import CasareRPAApp


class CanvasTriggerRunner:
    """
    Manages triggers for the Canvas application.

    When triggers are started, they actively monitor for events
    and run the workflow when triggered.
    """

    def __init__(self, app: "CasareRPAApp") -> None:
        """
        Initialize the trigger runner.

        Args:
            app: The Canvas application instance
        """
        self._app = app
        self._active_triggers: Dict[str, BaseTrigger] = {}
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if triggers are running."""
        return self._running

    @property
    def active_trigger_count(self) -> int:
        """Get the number of active triggers."""
        return len(self._active_triggers)

    async def start_triggers(self, triggers: List[Dict[str, Any]]) -> int:
        """
        Start all enabled triggers.

        Args:
            triggers: List of trigger configurations from the scenario

        Returns:
            Number of triggers successfully started
        """
        if self._running:
            logger.warning("Triggers already running")
            return 0

        started_count = 0
        registry = get_trigger_registry()

        for trigger_config in triggers:
            if not trigger_config.get("enabled", True):
                logger.debug(f"Skipping disabled trigger: {trigger_config.get('name')}")
                continue

            try:
                trigger_type_str = trigger_config.get("type", "manual")
                trigger_type = TriggerType(trigger_type_str)

                # Get the trigger class from registry
                trigger_class = registry.get(trigger_type)
                if not trigger_class:
                    logger.warning(f"Unknown trigger type: {trigger_type_str}")
                    continue

                # Create config - merge max_runs into nested config if present
                nested_config = trigger_config.get("config", {}).copy()
                if "max_runs" in trigger_config:
                    nested_config["max_runs"] = trigger_config["max_runs"]

                config = BaseTriggerConfig(
                    id=trigger_config.get("id", ""),
                    name=trigger_config.get("name", "Unnamed"),
                    trigger_type=trigger_type_str,
                    scenario_id=trigger_config.get("scenario_id", ""),
                    workflow_id=trigger_config.get("workflow_id", ""),
                    enabled=True,
                    priority=trigger_config.get("priority", 1),
                    cooldown_seconds=trigger_config.get("cooldown_seconds", 0),
                    config=nested_config,
                )

                # Create trigger instance with callback
                trigger = trigger_class(config, event_callback=self._on_trigger_event)

                # Validate config
                valid, error = trigger.validate_config()
                if not valid:
                    logger.error(f"Invalid trigger config '{config.name}': {error}")
                    continue

                # Start the trigger
                success = await trigger.start()
                if success:
                    self._active_triggers[config.id] = trigger
                    started_count += 1
                    logger.info(f"Started trigger: {config.name} ({trigger_type_str})")
                else:
                    logger.error(f"Failed to start trigger: {config.name}")

            except Exception as e:
                logger.exception(f"Error starting trigger: {e}")

        self._running = started_count > 0
        logger.info(f"Started {started_count} triggers")
        return started_count

    async def stop_triggers(self) -> None:
        """Stop all active triggers."""
        for trigger_id, trigger in list(self._active_triggers.items()):
            try:
                await trigger.stop()
                logger.debug(f"Stopped trigger: {trigger.config.name}")
            except Exception as e:
                logger.error(f"Error stopping trigger {trigger_id}: {e}")

        self._active_triggers.clear()
        self._running = False
        logger.info("All triggers stopped")

    async def _on_trigger_event(self, event: TriggerEvent) -> None:
        """
        Handle a trigger event by running the workflow.

        Args:
            event: The trigger event
        """
        logger.info(f"Trigger fired: {event.trigger_id} ({event.trigger_type})")
        logger.debug(f"Trigger payload: {event.payload}")

        try:
            # Update trigger stats in the bottom panel
            self._update_trigger_stats(event.trigger_id)

            # Run the workflow
            # We need to do this on the main thread via Qt signal
            from PySide6.QtCore import QMetaObject, Qt

            # Store the trigger payload for the workflow
            self._last_trigger_event = event

            # Emit the workflow run signal on the main thread
            # This will be picked up by the app's _on_run_workflow method
            main_window = self._app._main_window
            if main_window:
                # Use invokeMethod to call on the main thread
                QMetaObject.invokeMethod(
                    main_window,
                    "trigger_workflow_run",
                    Qt.ConnectionType.QueuedConnection,
                )

        except Exception as e:
            logger.exception(f"Error handling trigger event: {e}")

    def _update_trigger_stats(self, trigger_id: str) -> None:
        """
        Update trigger statistics (count and last_triggered) in the UI.

        Args:
            trigger_id: The ID of the trigger that fired
        """
        from datetime import datetime
        from PySide6.QtCore import QTimer

        try:
            main_window = self._app._main_window
            if not main_window:
                logger.warning("No main window for trigger stats update")
                return

            bottom_panel = main_window.get_bottom_panel()
            if not bottom_panel:
                logger.warning("No bottom panel for trigger stats update")
                return

            triggers_tab = bottom_panel.get_triggers_tab()
            if not triggers_tab:
                logger.warning("No triggers tab for trigger stats update")
                return

            # Get current count for this trigger
            triggers = triggers_tab.get_triggers()
            current_count = 0
            for trigger in triggers:
                if trigger.get("id") == trigger_id:
                    current_count = trigger.get("trigger_count", 0)
                    break

            new_count = current_count + 1
            timestamp = datetime.now().isoformat()

            logger.debug(
                f"Scheduling trigger stats update: {trigger_id} -> count={new_count}"
            )

            # Store values to avoid closure issues
            _trigger_id = trigger_id
            _new_count = new_count
            _timestamp = timestamp
            _tab = triggers_tab

            def do_update():
                logger.debug(
                    f"Executing trigger stats update: {_trigger_id} -> {_new_count}"
                )
                _tab.update_trigger_stats(_trigger_id, _new_count, _timestamp)

            # Update the UI on the main thread using QTimer.singleShot
            QTimer.singleShot(0, do_update)

        except Exception as e:
            logger.error(f"Error updating trigger stats: {e}")

    def get_last_trigger_event(self) -> Optional[TriggerEvent]:
        """Get the last trigger event (for injecting into workflow variables)."""
        return getattr(self, "_last_trigger_event", None)

    def clear_last_trigger_event(self) -> None:
        """Clear the last trigger event."""
        self._last_trigger_event = None
