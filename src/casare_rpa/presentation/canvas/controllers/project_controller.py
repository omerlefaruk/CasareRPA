"""
Project controller for project and scenario management.

Handles project hierarchy and scenario operations:
- Project management (create, open, close)
- Scenario management (create, switch, delete)
- Project context maintenance
"""

from typing import Optional, TYPE_CHECKING, Any
from PySide6.QtCore import Signal
from loguru import logger

from .base_controller import BaseController
from ..events.event_bus import EventBus
from ..events.event import Event
from ..events.event_types import EventType

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ProjectController(BaseController):
    """
    Manages project and scenario functionality.

    Single Responsibility: Project hierarchy and scenario management.

    Signals:
        project_created: Emitted when project is created (str: project_name)
        project_opened: Emitted when project is opened (str: project_path)
        project_closed: Emitted when project is closed
        scenario_created: Emitted when scenario is created (str: scenario_name)
        scenario_switched: Emitted when scenario is switched (str: scenario_name)
        project_context_changed: Emitted when project context changes
    """

    # Signals
    project_created = Signal(str)  # project_name
    project_opened = Signal(str)  # project_path
    project_closed = Signal()
    scenario_created = Signal(str)  # scenario_name
    scenario_switched = Signal(str)  # scenario_name
    project_context_changed = Signal()

    def __init__(self, main_window: "MainWindow"):
        """Initialize project controller."""
        super().__init__(main_window)
        self._project_manager = None
        self._event_bus = EventBus()

    def initialize(self) -> None:
        """Initialize controller and setup event subscriptions."""
        super().initialize()

        # Import and get project manager instance
        from ....project.project_manager import get_project_manager

        self._project_manager = get_project_manager()

        # Subscribe to EventBus events
        self._event_bus.subscribe(
            EventType.PROJECT_CREATED, self._on_project_created_event
        )
        self._event_bus.subscribe(
            EventType.PROJECT_OPENED, self._on_project_opened_event
        )
        self._event_bus.subscribe(
            EventType.PROJECT_CLOSED, self._on_project_closed_event
        )
        self._event_bus.subscribe(
            EventType.SCENARIO_CREATED, self._on_scenario_created_event
        )
        self._event_bus.subscribe(
            EventType.SCENARIO_OPENED, self._on_scenario_opened_event
        )

        logger.info("ProjectController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        # Unsubscribe from events
        self._event_bus.unsubscribe(
            EventType.PROJECT_CREATED, self._on_project_created_event
        )
        self._event_bus.unsubscribe(
            EventType.PROJECT_OPENED, self._on_project_opened_event
        )
        self._event_bus.unsubscribe(
            EventType.PROJECT_CLOSED, self._on_project_closed_event
        )
        self._event_bus.unsubscribe(
            EventType.SCENARIO_CREATED, self._on_scenario_created_event
        )
        self._event_bus.unsubscribe(
            EventType.SCENARIO_OPENED, self._on_scenario_opened_event
        )

        super().cleanup()
        logger.info("ProjectController cleanup")

    # =========================================================================
    # Public API
    # =========================================================================

    def get_project_manager(self) -> Any:
        """
        Get the project manager instance.

        Returns:
            ProjectManager instance
        """
        return self._project_manager

    def get_current_project(self) -> Optional[Any]:
        """
        Get the current active project.

        Returns:
            Current project or None
        """
        if self._project_manager:
            return self._project_manager.current_project
        return None

    def get_current_scenario(self) -> Optional[Any]:
        """
        Get the current active scenario.

        Returns:
            Current scenario or None
        """
        if self._project_manager:
            return self._project_manager.current_scenario
        return None

    def create_project(self, project_name: str, project_path: str) -> bool:
        """
        Create a new project.

        Args:
            project_name: Name of the project
            project_path: Path where project will be created

        Returns:
            bool: True if successful
        """
        logger.info(f"Creating project: {project_name} at {project_path}")

        try:
            if not self._project_manager:
                logger.error("Project manager not initialized")
                return False

            # Create project via project manager
            # Note: Actual implementation depends on ProjectManager API
            # This is a placeholder for the controller interface

            # Emit signal
            self.project_created.emit(project_name)

            # Publish event
            event = Event(
                type=EventType.PROJECT_CREATED,
                source="ProjectController",
                data={"project_name": project_name, "project_path": project_path},
            )
            self._event_bus.publish(event)

            return True

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return False

    def open_project(self, project_path: str) -> bool:
        """
        Open an existing project.

        Args:
            project_path: Path to the project

        Returns:
            bool: True if successful
        """
        logger.info(f"Opening project: {project_path}")

        try:
            if not self._project_manager:
                logger.error("Project manager not initialized")
                return False

            # Open project via project manager
            # Note: Actual implementation depends on ProjectManager API

            # Emit signal
            self.project_opened.emit(project_path)

            # Publish event
            event = Event(
                type=EventType.PROJECT_OPENED,
                source="ProjectController",
                data={"project_path": project_path},
            )
            self._event_bus.publish(event)

            self.project_context_changed.emit()

            return True

        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            return False

    def close_project(self) -> bool:
        """
        Close the current project.

        Returns:
            bool: True if successful
        """
        logger.info("Closing current project")

        try:
            if not self._project_manager:
                logger.error("Project manager not initialized")
                return False

            # Close project via project manager
            # Note: Actual implementation depends on ProjectManager API

            # Emit signal
            self.project_closed.emit()

            # Publish event
            event = Event(
                type=EventType.PROJECT_CLOSED, source="ProjectController", data={}
            )
            self._event_bus.publish(event)

            self.project_context_changed.emit()

            return True

        except Exception as e:
            logger.error(f"Failed to close project: {e}")
            return False

    def create_scenario(self, scenario_name: str) -> bool:
        """
        Create a new scenario in the current project.

        Args:
            scenario_name: Name of the scenario

        Returns:
            bool: True if successful
        """
        logger.info(f"Creating scenario: {scenario_name}")

        try:
            if not self._project_manager:
                logger.error("Project manager not initialized")
                return False

            # Create scenario via project manager
            # Note: Actual implementation depends on ProjectManager API

            # Emit signal
            self.scenario_created.emit(scenario_name)

            # Publish event
            event = Event(
                type=EventType.SCENARIO_CREATED,
                source="ProjectController",
                data={"scenario_name": scenario_name},
            )
            self._event_bus.publish(event)

            return True

        except Exception as e:
            logger.error(f"Failed to create scenario: {e}")
            return False

    def switch_scenario(self, scenario_name: str) -> bool:
        """
        Switch to a different scenario.

        Args:
            scenario_name: Name of the scenario to switch to

        Returns:
            bool: True if successful
        """
        logger.info(f"Switching to scenario: {scenario_name}")

        try:
            if not self._project_manager:
                logger.error("Project manager not initialized")
                return False

            # Switch scenario via project manager
            # Note: Actual implementation depends on ProjectManager API

            # Emit signal
            self.scenario_switched.emit(scenario_name)

            # Publish event
            event = Event(
                type=EventType.SCENARIO_OPENED,
                source="ProjectController",
                data={"scenario_name": scenario_name},
            )
            self._event_bus.publish(event)

            self.project_context_changed.emit()

            return True

        except Exception as e:
            logger.error(f"Failed to switch scenario: {e}")
            return False

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_project_created_event(self, event: Event) -> None:
        """
        Handle project created event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Project created event received: {event.data}")

    def _on_project_opened_event(self, event: Event) -> None:
        """
        Handle project opened event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Project opened event received: {event.data}")

    def _on_project_closed_event(self, event: Event) -> None:
        """
        Handle project closed event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Project closed event received: {event.data}")

    def _on_scenario_created_event(self, event: Event) -> None:
        """
        Handle scenario created event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Scenario created event received: {event.data}")

    def _on_scenario_opened_event(self, event: Event) -> None:
        """
        Handle scenario opened event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Scenario opened event received: {event.data}")
