"""
Project management component.

This component handles project and scenario management:
- Project hierarchy navigation
- Scenario management
- Project context
"""

from typing import TYPE_CHECKING
from loguru import logger

from .base_component import BaseComponent
from ...project.project_manager import get_project_manager

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ProjectComponent(BaseComponent):
    """
    Manages project and scenario functionality.

    Responsibilities:
    - Project management
    - Scenario management
    - Hierarchy navigation
    - Project context maintenance
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)
        self._project_manager = None

    def _do_initialize(self) -> None:
        """Initialize the project component."""
        # Get project manager instance
        self._project_manager = get_project_manager()

        logger.info("ProjectComponent initialized")

    def get_project_manager(self):
        """Get the project manager instance."""
        return self._project_manager

    def get_current_project(self):
        """Get the current active project."""
        if self._project_manager:
            return self._project_manager.current_project
        return None

    def get_current_scenario(self):
        """Get the current active scenario."""
        if self._project_manager:
            return self._project_manager.current_scenario
        return None

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.debug("ProjectComponent cleaned up")
