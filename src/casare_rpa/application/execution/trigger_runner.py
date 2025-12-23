"""
CasareRPA - Canvas Trigger Runner

Manages trigger lifecycle in the Canvas application.
Starts/stops triggers and handles trigger events by running workflows.

Architecture:
    This is an APPLICATION layer component. It MUST NOT import from presentation.
    The TriggerEventHandler protocol allows presentation to inject callbacks.
"""

from datetime import datetime
from typing import Any

from loguru import logger

from casare_rpa.application.execution.interfaces import (
    NullTriggerEventHandler,
    TriggerEventHandler,
)
from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerEvent,
    TriggerType,
)
from casare_rpa.triggers.registry import get_trigger_registry


class CanvasTriggerRunner:
    """
    Manages triggers for the Canvas application.

    When triggers are started, they actively monitor for events
    and run the workflow when triggered.

    The trigger runner uses a TriggerEventHandler to communicate
    with the presentation layer without depending on it directly.
    """

    def __init__(self, event_handler: TriggerEventHandler | None = None) -> None:
        """
        Initialize the trigger runner.

        Args:
            event_handler: Handler for trigger events. If None, uses
                           NullTriggerEventHandler (logs but takes no action).
        """
        self._event_handler = event_handler or NullTriggerEventHandler()
        self._active_triggers: dict[str, BaseTrigger] = {}
        self._running = False
        self._last_trigger_event: TriggerEvent | None = None

    @property
    def is_running(self) -> bool:
        """Check if triggers are running."""
        return self._running

    @property
    def active_trigger_count(self) -> int:
        """Get the number of active triggers."""
        return len(self._active_triggers)

    def set_event_handler(self, handler: TriggerEventHandler) -> None:
        """
        Set or update the event handler.

        Args:
            handler: New event handler to use
        """
        self._event_handler = handler
        logger.debug(f"Trigger runner event handler set to {type(handler).__name__}")

    async def start_triggers(self, triggers: list[dict[str, Any]]) -> int:
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
            # Store the trigger payload for the workflow
            self._last_trigger_event = event

            # Update trigger stats via the event handler
            self._update_trigger_stats(event.trigger_id)

            # Request workflow execution via the event handler
            # The handler is responsible for thread-safety (e.g., Qt main thread)
            self._event_handler.request_workflow_run()

        except Exception as e:
            logger.exception(f"Error handling trigger event: {e}")

    def _update_trigger_stats(self, trigger_id: str) -> None:
        """
        Update trigger statistics (count and last_triggered).

        Args:
            trigger_id: The ID of the trigger that fired
        """
        try:
            # Get current count from the event handler
            current_count = self._event_handler.get_trigger_count(trigger_id)
            new_count = current_count + 1
            timestamp = datetime.now().isoformat()

            logger.debug(f"Updating trigger stats: {trigger_id} -> count={new_count}")

            # Update via the event handler (handles thread-safety)
            self._event_handler.update_trigger_stats(trigger_id, new_count, timestamp)

        except Exception as e:
            logger.error(f"Error updating trigger stats: {e}")

    def get_last_trigger_event(self) -> TriggerEvent | None:
        """Get the last trigger event (for injecting into workflow variables)."""
        return self._last_trigger_event

    def clear_last_trigger_event(self) -> None:
        """Clear the last trigger event."""
        self._last_trigger_event = None
