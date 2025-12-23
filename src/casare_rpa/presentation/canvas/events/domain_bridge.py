"""
Domain-to-Presentation Event Bridge.

Bridges events from the domain EventBus to the presentation EventBus,
allowing Canvas UI components to receive execution events from the domain layer.

This maintains clean architecture separation:
- Domain layer publishes simple execution events
- Presentation layer receives and handles them via this bridge
- No direct dependency from domain to presentation

Usage:
    from casare_rpa.presentation.canvas.events.domain_bridge import DomainEventBridge

    # Create and start bridge (typically in MainWindow initialization)
    bridge = DomainEventBridge()
    bridge.start()

    # Stop when closing application
    bridge.stop()
"""

from typing import Optional, Type

from loguru import logger

from casare_rpa.domain.events import (
    DomainEvent,
    LogMessage,
    NodeCompleted,
    NodeFailed,
    NodeSkipped,
    NodeStarted,
    VariableSet,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowPaused,
    WorkflowResumed,
    WorkflowStarted,
    WorkflowStopped,
)
from casare_rpa.domain.events import (
    EventBus as DomainEventBus,
)
from casare_rpa.domain.events import (
    get_event_bus as get_domain_event_bus,
)
from casare_rpa.presentation.canvas.events.event import Event as PresentationEvent
from casare_rpa.presentation.canvas.events.event import EventPriority
from casare_rpa.presentation.canvas.events.event_bus import (
    EventBus as PresentationEventBus,
)
from casare_rpa.presentation.canvas.events.event_types import (
    EventType as PresentationEventType,
)

# Mapping from typed domain event classes to presentation event types
DOMAIN_TO_PRESENTATION_MAP: dict[type[DomainEvent], PresentationEventType] = {
    NodeStarted: PresentationEventType.NODE_EXECUTION_STARTED,
    NodeCompleted: PresentationEventType.NODE_EXECUTION_COMPLETED,
    NodeFailed: PresentationEventType.NODE_EXECUTION_FAILED,
    NodeSkipped: PresentationEventType.NODE_EXECUTION_SKIPPED,
    WorkflowStarted: PresentationEventType.EXECUTION_STARTED,
    WorkflowCompleted: PresentationEventType.EXECUTION_COMPLETED,
    WorkflowFailed: PresentationEventType.EXECUTION_FAILED,
    WorkflowPaused: PresentationEventType.EXECUTION_PAUSED,
    WorkflowResumed: PresentationEventType.EXECUTION_RESUMED,
    WorkflowStopped: PresentationEventType.EXECUTION_STOPPED,
    VariableSet: PresentationEventType.VARIABLE_SET,
    LogMessage: PresentationEventType.LOG_MESSAGE,
}


class DomainEventBridge:
    """
    Bridges domain events to presentation events.

    Subscribes to all relevant domain events and re-publishes them as
    presentation events with appropriate type mapping and data transformation.

    This allows:
    - Canvas UI to react to execution events
    - Debug panels to show real-time execution status
    - Logging panel to display execution logs

    Thread Safety:
        This bridge runs on the main thread and forwards events synchronously.
        Domain events published from async code are still delivered correctly
        because the domain EventBus handlers are called synchronously.

    Example:
        # In MainWindow.__init__()
        self._domain_bridge = DomainEventBridge()
        self._domain_bridge.start()

        # In MainWindow.closeEvent()
        self._domain_bridge.stop()
    """

    _instance: Optional["DomainEventBridge"] = None

    def __new__(cls) -> "DomainEventBridge":
        """Singleton pattern - only one bridge needed."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        domain_bus: DomainEventBus | None = None,
        presentation_bus: PresentationEventBus | None = None,
    ) -> None:
        """
        Initialize domain event bridge.

        Args:
            domain_bus: Domain EventBus instance (defaults to global)
            presentation_bus: Presentation EventBus instance (defaults to singleton)
        """
        if self._initialized:
            return

        self._domain_bus = domain_bus or get_domain_event_bus()
        self._presentation_bus = presentation_bus or PresentationEventBus()
        self._running = False
        self._initialized = True

        logger.debug("DomainEventBridge initialized")

    def start(self) -> None:
        """
        Start bridging domain events to presentation.

        Subscribes to all mapped domain event types.
        """
        if self._running:
            logger.warning("DomainEventBridge already running")
            return

        for domain_event_class in DOMAIN_TO_PRESENTATION_MAP.keys():
            self._domain_bus.subscribe(domain_event_class, self._on_domain_event)

        self._running = True
        event_count = len(DOMAIN_TO_PRESENTATION_MAP)
        logger.info(f"DomainEventBridge started, bridging {event_count} event types")

    def stop(self) -> None:
        """
        Stop bridging domain events.

        Unsubscribes from all domain event types.
        """
        if not self._running:
            return

        for domain_event_class in DOMAIN_TO_PRESENTATION_MAP.keys():
            self._domain_bus.unsubscribe(domain_event_class, self._on_domain_event)

        self._running = False
        logger.info("DomainEventBridge stopped")

    def _on_domain_event(self, event: DomainEvent) -> None:
        """
        Handle domain event and forward to presentation.

        Args:
            event: Domain event to forward
        """
        event_class = type(event)
        presentation_type = DOMAIN_TO_PRESENTATION_MAP.get(event_class)
        if presentation_type is None:
            logger.warning(f"No mapping for domain event type: {event_class.__name__}")
            return

        # Determine priority based on event type
        priority = self._get_priority(event_class)

        # Transform data if needed
        data = self._transform_data(event)

        # Get node_id from typed event if available
        node_id = getattr(event, "node_id", None)

        # Create presentation event
        presentation_event = PresentationEvent(
            type=presentation_type,
            source="DomainEventBridge",
            data=data,
            priority=priority,
            correlation_id=node_id,
        )

        # Publish to presentation bus
        self._presentation_bus.publish(presentation_event)

    def _get_priority(self, event_class: type[DomainEvent]) -> EventPriority:
        """
        Determine event priority based on type.

        Args:
            event_class: Domain event class

        Returns:
            Appropriate EventPriority
        """
        if event_class in (NodeFailed, WorkflowFailed):
            return EventPriority.HIGH

        if event_class in (WorkflowStarted, WorkflowCompleted, WorkflowStopped):
            return EventPriority.HIGH

        return EventPriority.NORMAL

    def _transform_data(self, event: DomainEvent) -> dict:
        """
        Transform domain event data to presentation format.

        Args:
            event: Domain event with data

        Returns:
            Transformed data dict for presentation event
        """
        # Convert typed event attributes to dict
        data = {}

        # Extract common attributes from typed events
        for attr in [
            "node_id",
            "node_type",
            "workflow_id",
            "workflow_name",
            "error_message",
            "execution_time_ms",
            "output_data",
            "variable_name",
            "value",
            "message",
            "level",
            "source",
        ]:
            if hasattr(event, attr):
                val = getattr(event, attr)
                if val is not None:
                    data[attr] = val

        # Add timestamp as ISO string
        if hasattr(event, "timestamp") and event.timestamp:
            data["timestamp"] = event.timestamp.isoformat()

        return data

    @property
    def is_running(self) -> bool:
        """Check if bridge is currently running."""
        return self._running

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        if cls._instance is not None:
            cls._instance.stop()
            cls._instance = None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DomainEventBridge("
            f"running={self._running}, "
            f"mappings={len(DOMAIN_TO_PRESENTATION_MAP)}"
            f")"
        )


# Convenience function for one-liner start
def start_domain_bridge() -> DomainEventBridge:
    """
    Start the domain event bridge.

    Convenience function to create and start the bridge in one call.

    Returns:
        Running DomainEventBridge instance
    """
    bridge = DomainEventBridge()
    bridge.start()
    return bridge
