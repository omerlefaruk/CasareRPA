"""
Selector controller for element picker functionality.

Handles browser and desktop element selection:
- Desktop element picker
- Browser element picker (via SelectorIntegration)
- Selector management and updates
"""

import asyncio
from typing import Optional, TYPE_CHECKING, Any, Dict
from PySide6.QtCore import Signal
from loguru import logger

from .base_controller import BaseController
from ..events.event_bus import EventBus
from ..events.event import Event
from ..events.event_types import EventType

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SelectorController(BaseController):
    """
    Manages element selector functionality.

    Single Responsibility: Coordinate element picking and selector updates.

    Signals:
        selector_picked: Emitted when selector is picked (str: selector_value, str: selector_type)
        picker_started: Emitted when picker mode starts
        picker_stopped: Emitted when picker mode stops
    """

    # Signals
    selector_picked = Signal(str, str)  # (selector_value, selector_type)
    picker_started = Signal()
    picker_stopped = Signal()

    def __init__(self, main_window: "MainWindow"):
        """Initialize selector controller."""
        super().__init__(main_window)
        self._selector_integration = None
        self._event_bus = EventBus()

    def initialize(self) -> None:
        """Initialize controller and setup event subscriptions."""
        super().initialize()

        # Import here to avoid circular dependency
        from ..selectors.selector_integration import SelectorIntegration

        # Create selector integration
        self._selector_integration = SelectorIntegration(self.main_window)

        # Connect selector integration signals
        self._selector_integration.selector_picked.connect(self._on_selector_picked)
        self._selector_integration.recording_complete.connect(
            self._on_recording_complete
        )

        # Subscribe to EventBus events
        self._event_bus.subscribe(
            EventType.SELECTOR_PICKER_OPENED, self._on_picker_opened_event
        )

        logger.info("SelectorController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._selector_integration:
            # Cleanup selector integration if needed
            pass

        super().cleanup()
        logger.info("SelectorController cleanup")

    # =========================================================================
    # Public API
    # =========================================================================

    async def start_picker(
        self, target_node: Optional[Any] = None, target_property: str = "selector"
    ) -> None:
        """
        Start element picker mode.

        Args:
            target_node: Optional node to update with picked selector
            target_property: Property name to update (default: "selector")
        """
        if not self._selector_integration:
            logger.error("Selector integration not initialized")
            return

        logger.info(
            f"Starting selector picker (target_node={target_node}, property={target_property})"
        )

        try:
            await self._selector_integration.start_picking(target_node, target_property)
            self.picker_started.emit()

            # Publish event
            event = Event(
                type=EventType.SELECTOR_PICKER_OPENED,
                source="SelectorController",
                data={"target_node": target_node, "target_property": target_property},
            )
            self._event_bus.publish(event)

        except Exception as e:
            logger.error(f"Failed to start picker: {e}")

    async def stop_picker(self) -> None:
        """Stop selector picker mode."""
        if not self._selector_integration:
            return

        logger.info("Stopping selector picker")

        try:
            await self._selector_integration.stop_selector_mode()
            self.picker_stopped.emit()

        except Exception as e:
            logger.error(f"Failed to stop picker: {e}")

    async def start_recording(self) -> None:
        """Start workflow recording mode."""
        if not self._selector_integration:
            logger.error("Selector integration not initialized")
            return

        logger.info("Starting workflow recording")

        try:
            await self._selector_integration.start_recording()
            self.picker_started.emit()

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")

    async def initialize_for_page(self, page: Any) -> None:
        """
        Initialize selector functionality for a Playwright page.

        Args:
            page: Playwright Page object
        """
        if not self._selector_integration:
            logger.error("Selector integration not initialized")
            return

        logger.info("Initializing selector for page")

        try:
            await self._selector_integration.initialize_for_page(page)
        except Exception as e:
            logger.error(f"Failed to initialize for page: {e}")

    def get_selector_integration(self):
        """
        Get the selector integration instance.

        Returns:
            SelectorIntegration instance
        """
        return self._selector_integration

    def is_picker_active(self) -> bool:
        """
        Check if picker mode is currently active.

        Returns:
            bool: True if picker is active
        """
        if not self._selector_integration:
            return False
        return self._selector_integration.is_active

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_selector_picked(self, selector_value: str, selector_type: str) -> None:
        """
        Handle selector picked from integration.

        Args:
            selector_value: The selector value
            selector_type: Type of selector (css, xpath, etc.)
        """
        logger.info(f"Selector picked: {selector_value} (type: {selector_type})")

        # Emit signal
        self.selector_picked.emit(selector_value, selector_type)

        # Publish event
        event = Event(
            type=EventType.SELECTOR_PICKED,
            source="SelectorController",
            data={"selector_value": selector_value, "selector_type": selector_type},
        )
        self._event_bus.publish(event)

    def _on_recording_complete(self, actions: list) -> None:
        """
        Handle recording completion.

        Args:
            actions: List of recorded actions
        """
        logger.info(f"Recording complete: {len(actions)} actions")

        # Could publish an event here if needed
        # For now just log it

    def _on_picker_opened_event(self, event: Event) -> None:
        """
        Handle selector picker opened event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Picker opened event received: {event.data}")
