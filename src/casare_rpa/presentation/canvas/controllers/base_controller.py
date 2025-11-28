"""
Base controller class for Canvas controllers.

All controllers follow the same pattern for consistency and lifecycle management.
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject
from loguru import logger

if TYPE_CHECKING:
    from ..main_window import MainWindow


# Create a metaclass that combines QObject's metaclass with ABCMeta
class QABCMeta(type(QObject), ABCMeta):
    """Metaclass that combines QObject and ABC."""

    pass


class BaseController(QObject, metaclass=QABCMeta):
    """
    Base class for all Canvas controllers.

    Controllers are responsible for:
    - Handling user interactions from UI
    - Updating model/state
    - Coordinating between components
    - Emitting signals for UI updates

    Controllers should NOT:
    - Directly manipulate UI widgets (use signals instead)
    - Contain domain logic (delegate to use cases/services)
    - Access infrastructure directly (use dependency injection)

    Lifecycle:
        1. __init__: Store references, initialize state
        2. initialize: Setup connections, load resources
        3. cleanup: Release resources, disconnect signals
    """

    def __init__(self, main_window: "MainWindow", parent: Optional[QObject] = None):
        """
        Initialize base controller.

        Args:
            main_window: Reference to main window for accessing shared components
            parent: Optional parent QObject for Qt ownership
        """
        super().__init__(parent or main_window)
        self.main_window = main_window
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize controller resources and connections.

        Called after all controllers are instantiated.
        Override to setup signal/slot connections and load initial state.
        """
        self._initialized = True
        logger.debug(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up controller resources.

        Called when main window is closing.
        Override to disconnect signals and release resources.
        """
        logger.debug(f"{self.__class__.__name__} cleanup")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if controller is initialized."""
        return self._initialized
