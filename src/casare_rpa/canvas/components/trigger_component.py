"""
Trigger management component.

This component handles trigger functionality:
- Trigger management
- Trigger execution
- Scenario coordination
"""

import asyncio
from typing import TYPE_CHECKING
from loguru import logger

from .base_component import BaseComponent

if TYPE_CHECKING:
    from ..main_window import MainWindow


class TriggerComponent(BaseComponent):
    """
    Manages workflow triggers.

    Responsibilities:
    - Trigger management
    - Trigger execution
    - Scenario coordination
    - Trigger lifecycle
    """

    def __init__(self, main_window: "MainWindow", app_instance) -> None:
        super().__init__(main_window)
        self._app_instance = app_instance
        self._trigger_runner = None

    def _do_initialize(self) -> None:
        """Initialize the trigger component."""
        # Create trigger runner
        from ..execution.trigger_runner import CanvasTriggerRunner

        self._trigger_runner = CanvasTriggerRunner(self._app_instance)

        # Connect signals
        self._main_window.trigger_workflow_requested.connect(
            self._on_trigger_run_workflow
        )

        logger.info("TriggerComponent initialized")

    def _on_trigger_run_workflow(self) -> None:
        """Handle workflow execution triggered by a trigger."""
        logger.info("Workflow execution triggered by trigger")

        # Get trigger event data to inject as variables
        trigger_event = self._trigger_runner.get_last_trigger_event()
        if trigger_event:
            logger.debug(f"Trigger payload: {trigger_event.payload}")

        # Signal the execution component to run the workflow
        self._main_window.workflow_run.emit()

        # Clear the event after processing
        self._trigger_runner.clear_last_trigger_event()

    def start_triggers(self) -> None:
        """Start all triggers for the current scenario."""
        bottom_panel = self._main_window.get_bottom_panel()
        if not bottom_panel:
            logger.warning("No bottom panel available")
            return

        triggers = bottom_panel.get_triggers()
        if not triggers:
            self._main_window.statusBar().showMessage("No triggers configured", 3000)
            bottom_panel.set_triggers_running(False)
            return

        async def _start():
            count = await self._trigger_runner.start_triggers(triggers)
            self._main_window.statusBar().showMessage(f"Started {count} triggers", 3000)
            bottom_panel.set_triggers_running(count > 0)

        asyncio.ensure_future(_start())

    def stop_triggers(self) -> None:
        """Stop all active triggers."""
        bottom_panel = self._main_window.get_bottom_panel()

        async def _stop():
            await self._trigger_runner.stop_triggers()
            self._main_window.statusBar().showMessage("Triggers stopped", 3000)
            if bottom_panel:
                bottom_panel.set_triggers_running(False)

        asyncio.ensure_future(_stop())

    def are_triggers_running(self) -> bool:
        """Check if triggers are currently running."""
        return self._trigger_runner.is_running if self._trigger_runner else False

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._trigger_runner:
            # Stop triggers if running
            if self._trigger_runner.is_running:
                asyncio.ensure_future(self._trigger_runner.stop_triggers())
        logger.debug("TriggerComponent cleaned up")
