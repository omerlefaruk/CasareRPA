"""
Selector Integration Module.

Connects selector picking to the main application and node graph.
Uses the unified SelectorFacade for consistent selector management.
"""

import asyncio

from loguru import logger
from PySide6.QtCore import QObject, Signal

from casare_rpa.domain.entities.selector import ElementFingerprint
from casare_rpa.utils.selectors import SelectorFacade

from .unified_selector_dialog import UnifiedSelectorDialog


class SelectorIntegration(QObject):
    """
    Integrates selector picking with the main application.

    Uses the singleton SelectorFacade for all selector operations
    to ensure consistent behavior across the application.
    """

    selector_picked = Signal(str, str)  # (selector_value, selector_type)
    recording_complete = Signal(list)  # List of recorded actions

    def __init__(self, parent=None):
        super().__init__(parent)

        # Use singleton facade - ensures consistent state across app
        self._facade = SelectorFacade.get_instance()
        self._active_page = None
        self._target_node = None  # Node that will receive the selector
        self._target_property = None  # Property name to update
        self._is_picking = False
        self._is_recording = False

    async def initialize_for_page(self, page):
        """
        Initialize selector functionality for a Playwright page

        Args:
            page: Playwright Page object
        """
        self._active_page = page
        await self._facade.inject_picker(page)
        logger.info("Selector integration initialized for page")

    async def start_picking(self, target_node=None, target_property: str = "selector"):
        """
        Start selector picking mode

        Args:
            target_node: Optional node to update with selected selector
            target_property: Property name to update (default: "selector")
        """
        if self._is_picking or self._is_recording:
            logger.debug("Stopping existing selector mode before starting new one")
            await self.stop_selector_mode()

        self._target_node = target_node
        self._target_property = target_property
        self._is_picking = True

        # Start selector mode in browser via facade
        await self._facade.activate_picker(
            recording=False, on_element_selected=self._handle_element_selected
        )

        logger.info("Selector picking mode started")

    async def start_recording(self):
        """Start workflow recording mode"""
        if self._is_picking or self._is_recording:
            logger.debug("Stopping existing selector mode before starting recording")
            await self.stop_selector_mode()

        self._is_recording = True

        # Start recording mode in browser via facade
        await self._facade.activate_picker(
            recording=True, on_recording_complete=self._handle_recording_complete
        )

        logger.info("Workflow recording mode started")

    async def stop_selector_mode(self):
        """Stop any active selector mode"""
        if not self._is_picking and not self._is_recording:
            return

        await self._facade.deactivate_picker()

        self._is_picking = False
        self._is_recording = False
        self._target_node = None
        self._target_property = None

        logger.info("Selector mode stopped")

    def _handle_element_selected(self, fingerprint: ElementFingerprint):
        """
        Handle element selection from browser
        Shows selector dialog for user to choose
        """
        logger.info(f"Element selected: {fingerprint.tag_name}")

        # Show the unified selector dialog
        dialog = UnifiedSelectorDialog(
            parent=None,  # Will use default parent
            initial_fingerprint=fingerprint,
            target_node=self._target_node,
            target_property=self._target_property,
        )

        # Show dialog
        if dialog.exec():
            result = dialog.get_result()
            if result and result.primary_selector:
                selector_value = result.primary_selector
                selector_type = result.selector_type or "css"

                # Emit signal (node already updated by dialog if target was provided)
                self.selector_picked.emit(selector_value, selector_type)

            logger.info(f"Selector confirmed: {selector_value}")

        # Clean up selector mode after dialog closes (accepted or cancelled)
        asyncio.ensure_future(self.stop_selector_mode())

    def _handle_dialog_action(self, selector_value: str, action: str):
        """Handle actions from selector dialog (highlight, etc.)"""
        if action.startswith("highlight:"):
            selector_type = action.split(":")[1]

            # Highlight elements in browser
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    self.selector_manager.highlight_elements(selector_value, selector_type)
                )

    def _handle_recording_complete(self, actions: list):
        """
        Handle completed workflow recording
        Emits signal with recorded actions
        """
        logger.info(f"Recording complete: {len(actions)} actions")

        self._is_recording = False
        self._is_picking = False
        self.recording_complete.emit(actions)

        # Also deactivate selector mode in browser
        asyncio.ensure_future(self.selector_manager.deactivate_selector_mode())

    def _update_node_property(self, selector_value: str):
        """Update the target node's property with the selector"""
        if not self._target_node:
            return

        try:
            # Get the widget
            widget = self._target_node.get_widget(self._target_property)
            if widget:
                widget.set_value(selector_value)
                logger.info(
                    f"Updated {self._target_node.name()}.{self._target_property} = {selector_value}"
                )
            else:
                logger.warning(f"Widget '{self._target_property}' not found on node")
        except Exception as e:
            logger.error(f"Failed to update node property: {e}")

    @property
    def is_active(self) -> bool:
        """Check if any selector mode is active"""
        return self._is_picking or self._is_recording

    @property
    def is_picking(self) -> bool:
        """Check if picking mode is active"""
        return self._is_picking

    @property
    def is_recording(self) -> bool:
        """Check if recording mode is active"""
        return self._is_recording
