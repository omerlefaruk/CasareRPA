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

from typing import Optional

from loguru import logger

from casare_rpa.domain.events import Event as DomainEvent
from casare_rpa.domain.events import EventBus as DomainEventBus
from casare_rpa.domain.events import get_event_bus as get_domain_event_bus
from casare_rpa.domain.value_objects.types import EventType as DomainEventType

from casare_rpa.presentation.canvas.events.event import Event as PresentationEvent
from casare_rpa.presentation.canvas.events.event import EventPriority
from casare_rpa.presentation.canvas.events.event_bus import (
    EventBus as PresentationEventBus,
)
from casare_rpa.presentation.canvas.events.event_types import (
    EventType as PresentationEventType,
)

# Mapping from domain event types to presentation event types
DOMAIN_TO_PRESENTATION_MAP: dict[DomainEventType, PresentationEventType] = {
    DomainEventType.NODE_STARTED: PresentationEventType.NODE_EXECUTION_STARTED,
    DomainEventType.NODE_COMPLETED: PresentationEventType.NODE_EXECUTION_COMPLETED,
    DomainEventType.NODE_ERROR: PresentationEventType.NODE_EXECUTION_FAILED,
    DomainEventType.NODE_SKIPPED: PresentationEventType.NODE_EXECUTION_SKIPPED,
    DomainEventType.WORKFLOW_STARTED: PresentationEventType.EXECUTION_STARTED,
    DomainEventType.WORKFLOW_COMPLETED: PresentationEventType.EXECUTION_COMPLETED,
    DomainEventType.WORKFLOW_ERROR: PresentationEventType.EXECUTION_FAILED,
    DomainEventType.WORKFLOW_PAUSED: PresentationEventType.EXECUTION_PAUSED,
    DomainEventType.WORKFLOW_RESUMED: PresentationEventType.EXECUTION_RESUMED,
    DomainEventType.WORKFLOW_STOPPED: PresentationEventType.EXECUTION_STOPPED,
    DomainEventType.VARIABLE_SET: PresentationEventType.VARIABLE_SET,
    DomainEventType.LOG_MESSAGE: PresentationEventType.LOG_MESSAGE,
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
        domain_bus: Optional[DomainEventBus] = None,
        presentation_bus: Optional[PresentationEventBus] = None,
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

        for domain_event_type in DOMAIN_TO_PRESENTATION_MAP.keys():
            self._domain_bus.subscribe(domain_event_type, self._on_domain_event)

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

        for domain_event_type in DOMAIN_TO_PRESENTATION_MAP.keys():
            self._domain_bus.unsubscribe(domain_event_type, self._on_domain_event)

        self._running = False
        logger.info("DomainEventBridge stopped")

    def _on_domain_event(self, event: DomainEvent) -> None:
        """
        Handle domain event and forward to presentation.

        Args:
            event: Domain event to forward
        """
        presentation_type = DOMAIN_TO_PRESENTATION_MAP.get(event.event_type)
        if presentation_type is None:
            logger.warning(f"No mapping for domain event type: {event.event_type}")
            return

        # Determine priority based on event type
        priority = self._get_priority(event.event_type)

        # Transform data if needed
        data = self._transform_data(event)

        # Create presentation event
        presentation_event = PresentationEvent(
            type=presentation_type,
            source="DomainEventBridge",
            data=data,
            priority=priority,
            correlation_id=event.node_id,
        )

        # Publish to presentation bus
        self._presentation_bus.publish(presentation_event)

    def _get_priority(self, event_type: DomainEventType) -> EventPriority:
        """
        Determine event priority based on type.

        Args:
            event_type: Domain event type

        Returns:
            Appropriate EventPriority
        """
        if event_type in (
            DomainEventType.NODE_ERROR,
            DomainEventType.WORKFLOW_ERROR,
        ):
            return EventPriority.HIGH

        if event_type in (
            DomainEventType.WORKFLOW_STARTED,
            DomainEventType.WORKFLOW_COMPLETED,
            DomainEventType.WORKFLOW_STOPPED,
        ):
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
        data = dict(event.data) if event.data else {}

        # Add node_id to data if present
        if event.node_id and "node_id" not in data:
            data["node_id"] = event.node_id

        # Add timestamp as ISO string if not present
        if "timestamp" not in data:
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
