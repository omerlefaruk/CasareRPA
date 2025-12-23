"""
Example Workflow Controller demonstrating EventBus usage.

This controller showcases best practices for using the EventBus system:
    - Inherits from EventHandler for automatic subscription management
    - Uses @event_handler decorator for clean event handling
    - Publishes events for state changes
    - Minimal coupling to other components

This serves as a template for other controllers to follow.
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from casare_rpa.presentation.canvas.events import (
    Event,
    EventHandler,
    EventType,
    event_handler,
)


class ExampleWorkflowController(EventHandler):
    """
    Example controller for workflow lifecycle management.

    Demonstrates EventBus usage patterns:
        - Event subscription via @event_handler decorator
        - Event publishing for state changes
        - Automatic cleanup via EventHandler base class

    Responsibilities:
        - Create new workflows
        - Open existing workflows
        - Save workflows
        - Track workflow state (modified, current file)

    Events Published:
        - WORKFLOW_NEW: When new workflow is created
        - WORKFLOW_OPENED: When workflow is loaded from file
        - WORKFLOW_SAVED: When workflow is saved to file
        - WORKFLOW_MODIFIED: When workflow has unsaved changes

    Events Subscribed:
        - NODE_ADDED: Marks workflow as modified
        - NODE_REMOVED: Marks workflow as modified
        - CONNECTION_ADDED: Marks workflow as modified
        - CONNECTION_REMOVED: Marks workflow as modified

    Example:
        # Create controller
        controller = ExampleWorkflowController()

        # Controller automatically subscribes to events
        # and publishes events when state changes

        # Create new workflow
        await controller.new_workflow("My Workflow")

        # Save workflow
        await controller.save_workflow(Path("workflow.json"))

        # Cleanup when done
        controller.cleanup()
    """

    def __init__(self):
        """Initialize workflow controller."""
        super().__init__()

        # State
        self._current_file: Path | None = None
        self._is_modified = False
        self._workflow_name: str | None = None

        # Auto-subscribe to decorated event handlers
        self._auto_subscribe_decorated_handlers()

        logger.info("ExampleWorkflowController initialized")

    # =========================================================================
    # Public API
    # =========================================================================

    async def new_workflow(self, name: str = "Untitled") -> None:
        """
        Create a new workflow.

        Args:
            name: Name for the new workflow

        Events Published:
            WORKFLOW_NEW: When workflow is created
        """
        logger.info(f"Creating new workflow: {name}")

        # Update state
        self._workflow_name = name
        self._current_file = None
        self._is_modified = False

        # Publish event
        event = Event(
            type=EventType.WORKFLOW_NEW,
            source=self.__class__.__name__,
            data={
                "name": name,
            },
        )
        self.publish(event)

        logger.info(f"New workflow created: {name}")

    async def open_workflow(self, file_path: Path) -> None:
        """
        Open an existing workflow from file.

        Args:
            file_path: Path to workflow file

        Events Published:
            WORKFLOW_OPENED: When workflow is loaded

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        logger.info(f"Opening workflow: {file_path}")

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        # Example stub: actual file loading uses WorkflowStorage.load()
        # This example demonstrates controller pattern only

        # Update state
        self._current_file = file_path
        self._workflow_name = file_path.stem
        self._is_modified = False

        # Publish event
        event = Event(
            type=EventType.WORKFLOW_OPENED,
            source=self.__class__.__name__,
            data={
                "file_path": str(file_path),
                "name": self._workflow_name,
            },
        )
        self.publish(event)

        logger.info(f"Workflow opened: {file_path}")

    async def save_workflow(self, file_path: Path | None = None) -> None:
        """
        Save workflow to file.

        Args:
            file_path: Path to save to (uses current file if None)

        Events Published:
            WORKFLOW_SAVED: When workflow is saved
            WORKFLOW_SAVE_AS: When workflow is saved with new filename

        Raises:
            ValueError: If no file path specified and no current file
        """
        # Use current file if not specified
        if file_path is None:
            file_path = self._current_file

        if file_path is None:
            raise ValueError("No file path specified for save")

        logger.info(f"Saving workflow to: {file_path}")

        # Example stub: actual file saving uses WorkflowStorage.save()
        # This example demonstrates controller pattern only

        # Determine event type
        is_save_as = self._current_file != file_path
        event_type = EventType.WORKFLOW_SAVE_AS if is_save_as else EventType.WORKFLOW_SAVED

        # Update state
        self._current_file = file_path
        self._is_modified = False

        # Publish event
        event = Event(
            type=event_type,
            source=self.__class__.__name__,
            data={
                "file_path": str(file_path),
                "name": self._workflow_name,
            },
        )
        self.publish(event)

        logger.info(f"Workflow saved: {file_path}")

    async def close_workflow(self) -> None:
        """
        Close current workflow.

        Events Published:
            WORKFLOW_CLOSED: When workflow is closed
        """
        logger.info("Closing workflow")

        # Store data for event
        file_path = str(self._current_file) if self._current_file else None
        name = self._workflow_name

        # Reset state
        self._current_file = None
        self._workflow_name = None
        self._is_modified = False

        # Publish event
        event = Event(
            type=EventType.WORKFLOW_CLOSED,
            source=self.__class__.__name__,
            data={
                "file_path": file_path,
                "name": name,
            },
        )
        self.publish(event)

        logger.info("Workflow closed")

    def mark_modified(self) -> None:
        """
        Mark workflow as having unsaved changes.

        Events Published:
            WORKFLOW_MODIFIED: When workflow is marked modified
        """
        if not self._is_modified:
            self._is_modified = True

            event = Event(
                type=EventType.WORKFLOW_MODIFIED,
                source=self.__class__.__name__,
                data={
                    "is_modified": True,
                },
            )
            self.publish(event)

            logger.debug("Workflow marked as modified")

    # =========================================================================
    # Event Handlers (using @event_handler decorator)
    # =========================================================================

    @event_handler(EventType.NODE_ADDED)
    def _on_node_added(self, event: Event) -> None:
        """
        Handle node added event - mark workflow as modified.

        Args:
            event: NODE_ADDED event
        """
        logger.debug(f"Node added: {event.data.get('node_id')}")
        self.mark_modified()

    @event_handler(EventType.NODE_REMOVED)
    def _on_node_removed(self, event: Event) -> None:
        """
        Handle node removed event - mark workflow as modified.

        Args:
            event: NODE_REMOVED event
        """
        logger.debug(f"Node removed: {event.data.get('node_id')}")
        self.mark_modified()

    @event_handler(EventType.CONNECTION_ADDED)
    def _on_connection_added(self, event: Event) -> None:
        """
        Handle connection added event - mark workflow as modified.

        Args:
            event: CONNECTION_ADDED event
        """
        logger.debug("Connection added")
        self.mark_modified()

    @event_handler(EventType.CONNECTION_REMOVED)
    def _on_connection_removed(self, event: Event) -> None:
        """
        Handle connection removed event - mark workflow as modified.

        Args:
            event: CONNECTION_REMOVED event
        """
        logger.debug("Connection removed")
        self.mark_modified()

    @event_handler(EventType.NODE_PROPERTY_CHANGED)
    def _on_node_property_changed(self, event: Event) -> None:
        """
        Handle node property changed event - mark workflow as modified.

        Args:
            event: NODE_PROPERTY_CHANGED event
        """
        logger.debug(
            f"Node property changed: {event.data.get('node_id')} - " f"{event.data.get('property')}"
        )
        self.mark_modified()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def current_file(self) -> Path | None:
        """Get current workflow file path."""
        return self._current_file

    @property
    def is_modified(self) -> bool:
        """Check if workflow has unsaved changes."""
        return self._is_modified

    @property
    def workflow_name(self) -> str | None:
        """Get current workflow name."""
        return self._workflow_name

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self) -> None:
        """
        Cleanup controller resources.

        Automatically unsubscribes from all events via EventHandler base class.
        """
        super().cleanup()
        logger.info("ExampleWorkflowController cleaned up")
