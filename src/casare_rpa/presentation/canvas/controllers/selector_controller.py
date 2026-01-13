"""
Selector controller for element picker functionality.

Handles browser and desktop element selection via UnifiedSelectorDialog:
- Browser element picking (CSS, XPath, ARIA)
- Desktop element picking (AutomationId, Name, Path)
- OCR text detection
- Image/template matching
- Healing context capture
"""

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Signal

from ..events.event import Event
from ..events.event_bus import EventBus
from ..events.event_types import EventType
from ..interfaces import IMainWindow
from .base_controller import BaseController

if TYPE_CHECKING:
    from playwright.async_api import Page


class SelectorController(BaseController):
    """
    Manages element selector functionality.

    Single Responsibility: Coordinate element picking and selector updates
    via the UnifiedSelectorDialog.

    Signals:
        selector_picked: Emitted when selector is picked (str: selector_value, str: selector_type)
        picker_started: Emitted when picker mode starts
        picker_stopped: Emitted when picker mode stops
    """

    # Signals
    selector_picked = Signal(str, str)  # (selector_value, selector_type)
    picker_started = Signal()
    picker_stopped = Signal()

    def __init__(self, main_window: "IMainWindow"):
        """Initialize selector controller."""
        super().__init__(main_window)
        self._selector_integration = None
        self._event_bus = EventBus()
        self._browser_page: Page | None = None
        self._unified_dialog = None

    def initialize(self) -> None:
        """Initialize controller and setup event subscriptions."""
        super().initialize()

        # Import here to avoid circular dependency
        from ..selectors.selector_integration import SelectorIntegration

        # Create selector integration
        self._selector_integration = SelectorIntegration(self.main_window)

        # Connect selector integration signals
        self._selector_integration.selector_picked.connect(self._on_selector_picked)
        self._selector_integration.recording_complete.connect(self._on_recording_complete)

        # Subscribe to EventBus events
        self._event_bus.subscribe(EventType.SELECTOR_PICKER_OPENED, self._on_picker_opened_event)

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

    def show_unified_selector_dialog(
        self,
        target_node: Any | None = None,
        target_property: str = "selector",
        initial_mode: str = "browser",
    ) -> None:
        """
        Show the element selector dialog.

        This is the main entry point for element picking.

        Args:
            target_node: Optional node to update with picked selector
            target_property: Property name to update (default: "selector")
            initial_mode: Which mode to show first ("browser", "desktop")
        """
        from ..selectors.element_selector_dialog import ElementSelectorDialog

        logger.info(
            f"Opening element selector dialog (mode={initial_mode}, "
            f"target_node={target_node}, property={target_property}, "
            f"browser_page_available={self._browser_page is not None})"
        )

        # Create dialog
        dialog = ElementSelectorDialog(
            parent=self.main_window,
            mode=initial_mode,
            browser_page=self._browser_page,
            target_node=target_node,
            property_name=target_property,
        )

        # Connect signals
        dialog.selector_confirmed.connect(self._on_unified_selector_picked)

        self.picker_started.emit()

        # Publish event
        event = Event(
            type=EventType.SELECTOR_PICKER_OPENED,
            source="SelectorController",
            data={
                "target_node": target_node,
                "target_property": target_property,
                "mode": initial_mode,
            },
        )
        self._event_bus.publish(event)

        # Show dialog (modal)
        dialog.exec()

        self.picker_stopped.emit()

    def _on_unified_selector_picked(self, result) -> None:
        """
        Handle selector picked from unified dialog.

        Args:
            result: SelectorResult object
        """
        logger.info(
            f"Unified selector picked: {result.selector_value[:50]}... "
            f"(type: {result.selector_type})"
        )

        # Emit signal
        self.selector_picked.emit(result.selector_value, result.selector_type)

        # Publish event with full result including healing context
        event = Event(
            type=EventType.SELECTOR_PICKED,
            source="SelectorController",
            data={
                "selector_value": result.selector_value,
                "selector_type": result.selector_type,
                "confidence": result.confidence,
                "is_unique": result.is_unique,
                "healing_context": result.healing_context,
                "metadata": result.metadata,
            },
        )
        self._event_bus.publish(event)

    def pick_element(
        self, target_node: Any | None = None, target_property: str = "selector"
    ) -> None:
        """
        Pick a browser element selector.

        Opens the unified selector dialog in browser mode.

        Args:
            target_node: Optional node to update with picked selector
            target_property: Property name to update (default: "selector")
        """
        self.show_unified_selector_dialog(
            target_node=target_node,
            target_property=target_property,
            initial_mode="browser",
        )

    def pick_desktop_element(
        self, target_node: Any | None = None, target_property: str = "selector"
    ) -> None:
        """
        Pick a desktop element selector.

        Opens the unified selector dialog in desktop mode.

        Args:
            target_node: Optional node to update with picked selector
            target_property: Property name to update (default: "selector")
        """
        self.show_unified_selector_dialog(
            target_node=target_node,
            target_property=target_property,
            initial_mode="desktop",
        )

    def stop_picker(self) -> None:
        """Stop selector picker mode."""
        if not self._selector_integration:
            return

        logger.info("Stopping selector picker")
        self.picker_stopped.emit()

    def initialize_for_page(self, page: Any) -> None:
        """
        Initialize selector functionality for a Playwright page.

        Args:
            page: Playwright Page object
        """
        logger.info(
            f"SelectorController.initialize_for_page called: "
            f"page={page is not None}, url={getattr(page, 'url', 'N/A')}"
        )
        self._browser_page = page

    def set_browser_page(self, page: Any) -> None:
        """
        Set the browser page for selector operations (sync version).

        Args:
            page: Playwright Page object
        """
        self._browser_page = page
        logger.debug("Browser page set for selector controller")

    def get_browser_page(self) -> Any:
        """
        Get the current browser page.

        Returns:
            Playwright Page object or None if not set
        """
        return self._browser_page

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
