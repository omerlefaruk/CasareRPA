"""
Element selector integration component.

This component handles browser/desktop element selection:
- Browser element picker
- Desktop element selector
- Selector integration with nodes
"""

from typing import TYPE_CHECKING
from loguru import logger

from .base_component import BaseComponent
from ..selectors.selector_integration import SelectorIntegration

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SelectorComponent(BaseComponent):
    """
    Manages element selector functionality.

    Responsibilities:
    - Browser element picker
    - Desktop element selector
    - Selector integration with nodes
    - Selector caching
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)
        self._selector_integration: SelectorIntegration = None

    def _do_initialize(self) -> None:
        """Initialize the selector component."""
        # Create selector integration
        self._selector_integration = SelectorIntegration(self._main_window)
        logger.info("SelectorComponent initialized")

    def get_selector_integration(self) -> SelectorIntegration:
        """Get the selector integration instance."""
        return self._selector_integration

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._selector_integration:
            # Cleanup selector resources if needed
            pass
        logger.debug("SelectorComponent cleaned up")
