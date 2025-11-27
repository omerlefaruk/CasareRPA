"""
Base class for Canvas components.

This module provides the BaseComponent class which all Canvas components
inherit from, establishing a common lifecycle and interface pattern.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import QObject
from loguru import logger

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from ..graph.node_graph_widget import NodeGraphWidget


class BaseComponent(QObject):
    """
    Base class for all Canvas components.

    Components are responsible for:
    - Encapsulating related functionality
    - Managing their own lifecycle
    - Exposing clean interfaces

    Components should:
    - Be independently testable
    - Have minimal coupling
    - Follow single responsibility principle
    - Use dependency injection for dependencies
    """

    def __init__(
        self, main_window: "MainWindow", parent: Optional[QObject] = None
    ) -> None:
        """
        Initialize the component.

        Args:
            main_window: Reference to the main window
            parent: Optional Qt parent object
        """
        super().__init__(parent)
        self._main_window = main_window
        self._initialized = False

    @property
    def main_window(self) -> "MainWindow":
        """Get the main window reference."""
        return self._main_window

    @property
    def node_graph(self) -> "NodeGraphWidget":
        """Get the node graph widget from main window."""
        return self._main_window._central_widget

    @property
    def initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized

    def initialize(self) -> None:
        """
        Initialize component.

        Called after all components are constructed.
        This method ensures initialization happens only once.
        """
        if self._initialized:
            logger.warning(f"{self.__class__.__name__} already initialized")
            return

        logger.debug(f"Initializing {self.__class__.__name__}...")
        self._do_initialize()
        self._initialized = True
        logger.debug(f"{self.__class__.__name__} initialized successfully")

    def _do_initialize(self) -> None:
        """
        Actual initialization logic.

        Override in subclasses to implement component-specific initialization.
        This is called exactly once during the component lifecycle.
        """
        pass

    def cleanup(self) -> None:
        """
        Cleanup resources.

        Called when component is destroyed or application is shutting down.
        Override in subclasses to implement cleanup logic.
        """
        pass

    def __del__(self) -> None:
        """Destructor - ensure cleanup is called."""
        try:
            if self._initialized:
                self.cleanup()
        except Exception as e:
            logger.error(f"Error during {self.__class__.__name__} cleanup: {e}")
