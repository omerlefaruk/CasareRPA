"""
CasareRPA - Application Execution Interfaces

Protocols (interfaces) for trigger execution that the presentation layer implements.
This allows the application layer to remain decoupled from presentation concerns.

Architecture:
    Presentation → implements → Application (Protocol) ← uses ← TriggerRunner
"""

from collections.abc import Callable
from typing import Optional, Protocol, runtime_checkable

from loguru import logger


@runtime_checkable
class TriggerEventHandler(Protocol):
    """
    Protocol for handling trigger events from the application layer.

    The presentation layer (Canvas app) implements this protocol to:
    1. Request workflow execution when a trigger fires
    2. Update trigger statistics in the UI

    This abstraction allows CanvasTriggerRunner to work without
    knowing about Qt, MainWindow, or any presentation details.
    """

    def request_workflow_run(self) -> None:
        """
        Request the application to run the current workflow.

        This should be called on the main thread (for Qt applications).
        The implementation handles thread-safety internally.
        """
        ...

    def update_trigger_stats(self, trigger_id: str, count: int, last_triggered: str) -> None:
        """
        Update the UI with trigger statistics.

        Args:
            trigger_id: The ID of the trigger that fired
            count: The new execution count
            last_triggered: ISO timestamp of when the trigger last fired
        """
        ...

    def get_trigger_count(self, trigger_id: str) -> int:
        """
        Get the current execution count for a trigger.

        Args:
            trigger_id: The ID of the trigger

        Returns:
            Current execution count, or 0 if not found
        """
        ...


class NullTriggerEventHandler:
    """
    Null implementation of TriggerEventHandler for headless/test environments.

    Logs events but takes no action. Useful for:
    - Unit testing without UI dependencies
    - Robot-only execution without Canvas
    - Development/debugging
    """

    def request_workflow_run(self) -> None:
        """Log workflow run request (no-op in headless mode)."""
        logger.debug("NullTriggerEventHandler: workflow run requested (no-op)")

    def update_trigger_stats(self, trigger_id: str, count: int, last_triggered: str) -> None:
        """Log stats update (no-op in headless mode)."""
        logger.debug(
            f"NullTriggerEventHandler: trigger {trigger_id} stats updated - "
            f"count={count}, last_triggered={last_triggered}"
        )

    def get_trigger_count(self, trigger_id: str) -> int:
        """Return 0 for headless mode (no persistent stats)."""
        return 0


class CallbackTriggerEventHandler:
    """
    Callback-based implementation of TriggerEventHandler.

    Allows injecting custom callbacks for each operation.
    Useful for testing or custom integrations.
    """

    def __init__(
        self,
        on_workflow_run: Callable[[], None] | None = None,
        on_stats_update: Callable[[str, int, str], None] | None = None,
        on_get_count: Callable[[str], int] | None = None,
    ) -> None:
        """
        Initialize with optional callbacks.

        Args:
            on_workflow_run: Called when workflow run is requested
            on_stats_update: Called with (trigger_id, count, timestamp)
            on_get_count: Called with trigger_id, returns count
        """
        self._on_workflow_run = on_workflow_run
        self._on_stats_update = on_stats_update
        self._on_get_count = on_get_count

    def request_workflow_run(self) -> None:
        """Invoke the workflow run callback if set."""
        if self._on_workflow_run:
            self._on_workflow_run()
        else:
            logger.debug("CallbackTriggerEventHandler: no workflow run callback set")

    def update_trigger_stats(self, trigger_id: str, count: int, last_triggered: str) -> None:
        """Invoke the stats update callback if set."""
        if self._on_stats_update:
            self._on_stats_update(trigger_id, count, last_triggered)
        else:
            logger.debug(
                f"CallbackTriggerEventHandler: no stats callback, "
                f"trigger {trigger_id} count={count}"
            )

    def get_trigger_count(self, trigger_id: str) -> int:
        """Invoke the get count callback if set, else return 0."""
        if self._on_get_count:
            return self._on_get_count(trigger_id)
        return 0
