"""
Event data structures for the Canvas event system.

This module defines the Event class and related data structures used
for event-driven communication between components.

Events are immutable, timestamped objects that carry information about
what happened, where it happened, and any associated data.

Usage:
    from casare_rpa.presentation.canvas.events import Event, EventType, EventPriority

    # Create an event
    event = Event(
        type=EventType.WORKFLOW_NEW,
        source="WorkflowController",
        data={"workflow_id": "123", "name": "My Workflow"}
    )

    # Access event properties
    print(event.type)       # EventType.WORKFLOW_NEW
    print(event.source)     # "WorkflowController"
    print(event.timestamp)  # 1234567890.123
    print(event.data)       # {"workflow_id": "123", "name": "My Workflow"}
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum
import time

from .event_types import EventType, EventCategory


class EventPriority(Enum):
    """
    Priority levels for event handling.

    Higher priority events are processed before lower priority events
    when multiple events are queued.
    """

    LOW = 0
    """Low priority - non-critical events."""

    NORMAL = 1
    """Normal priority - most events."""

    HIGH = 2
    """High priority - important UI updates."""

    CRITICAL = 3
    """Critical priority - system events, errors."""

    def __lt__(self, other: "EventPriority") -> bool:
        """Compare priorities (higher value = higher priority)."""
        if not isinstance(other, EventPriority):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other: "EventPriority") -> bool:
        """Compare priorities (higher value = higher priority)."""
        if not isinstance(other, EventPriority):
            return NotImplemented
        return self.value > other.value


@dataclass(frozen=True)
class Event:
    """
    Immutable event object.

    Events represent something that has happened in the system that
    other components may want to react to.

    Attributes:
        type: The type of event (from EventType enum)
        source: Component/controller that emitted the event
        data: Optional payload data associated with the event
        timestamp: Unix timestamp when event was created
        priority: Priority level for event processing
        event_id: Unique identifier for this event instance
        correlation_id: ID linking related events together

    Examples:
        # Simple event
        event = Event(
            type=EventType.NODE_ADDED,
            source="NodeController"
        )

        # Event with data
        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source="WorkflowController",
            data={"file_path": "/path/to/workflow.json"}
        )

        # High priority event
        event = Event(
            type=EventType.ERROR_OCCURRED,
            source="SystemMonitor",
            data={"error": "Out of memory"},
            priority=EventPriority.CRITICAL
        )

        # Correlated events
        event1 = Event(
            type=EventType.EXECUTION_STARTED,
            source="ExecutionController",
            correlation_id="exec-123"
        )
        event2 = Event(
            type=EventType.EXECUTION_COMPLETED,
            source="ExecutionController",
            correlation_id="exec-123"
        )
    """

    type: EventType
    source: str
    data: Optional[dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    event_id: str = field(default_factory=lambda: _generate_event_id())
    correlation_id: Optional[str] = None

    def __post_init__(self):
        """Validate event after initialization."""
        if not isinstance(self.type, EventType):
            raise TypeError(f"type must be EventType, got {type(self.type)}")

        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")

        if self.data is not None and not isinstance(self.data, dict):
            raise TypeError(f"data must be dict or None, got {type(self.data)}")

        if not isinstance(self.priority, EventPriority):
            raise TypeError(
                f"priority must be EventPriority, got {type(self.priority)}"
            )

    @property
    def category(self) -> EventCategory:
        """
        Get the category of this event.

        Returns:
            EventCategory: The category this event belongs to
        """
        return self.type.category

    @property
    def datetime(self) -> datetime:
        """
        Get timestamp as datetime object.

        Returns:
            datetime: Event timestamp as datetime
        """
        return datetime.fromtimestamp(self.timestamp)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from event data.

        Args:
            key: Data key to retrieve
            default: Default value if key not found

        Returns:
            Value from data dict or default
        """
        if self.data is None:
            return default
        return self.data.get(key, default)

    def has_data(self, key: str) -> bool:
        """
        Check if event has specific data key.

        Args:
            key: Data key to check

        Returns:
            bool: True if key exists in data
        """
        return self.data is not None and key in self.data

    def is_high_priority(self) -> bool:
        """
        Check if this is a high or critical priority event.

        Returns:
            bool: True if priority is HIGH or CRITICAL
        """
        return self.priority in (EventPriority.HIGH, EventPriority.CRITICAL)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary.

        Useful for serialization and logging.

        Returns:
            dict: Event as dictionary
        """
        return {
            "event_id": self.event_id,
            "type": self.type.name,
            "category": self.category.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
            "datetime": self.datetime.isoformat(),
            "priority": self.priority.name,
            "correlation_id": self.correlation_id,
        }

    def __str__(self) -> str:
        """String representation of event."""
        data_str = f", data={self.data}" if self.data else ""
        return f"Event({self.type.name}, source={self.source}{data_str})"

    def __repr__(self) -> str:
        """Detailed representation of event."""
        return (
            f"Event("
            f"type={self.type!r}, "
            f"source={self.source!r}, "
            f"data={self.data!r}, "
            f"timestamp={self.timestamp}, "
            f"priority={self.priority!r}, "
            f"event_id={self.event_id!r}, "
            f"correlation_id={self.correlation_id!r}"
            f")"
        )


def _generate_event_id() -> str:
    """
    Generate unique event ID.

    Format: evt_<timestamp>_<counter>

    Returns:
        str: Unique event ID
    """
    import uuid

    # Use UUID4 for guaranteed uniqueness
    return f"evt_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


@dataclass
class EventFilter:
    """
    Filter for subscribing to specific events.

    Allows subscribing to events based on type, category, source, or priority.

    Examples:
        # Filter by type
        filter = EventFilter(types=[EventType.WORKFLOW_NEW, EventType.WORKFLOW_SAVED])

        # Filter by category
        filter = EventFilter(categories=[EventCategory.WORKFLOW])

        # Filter by source
        filter = EventFilter(sources=["WorkflowController"])

        # Filter by priority
        filter = EventFilter(min_priority=EventPriority.HIGH)

        # Combined filters (AND logic)
        filter = EventFilter(
            categories=[EventCategory.EXECUTION],
            min_priority=EventPriority.NORMAL
        )
    """

    types: Optional[list[EventType]] = None
    categories: Optional[list[EventCategory]] = None
    sources: Optional[list[str]] = None
    min_priority: Optional[EventPriority] = None
    max_priority: Optional[EventPriority] = None

    def matches(self, event: Event) -> bool:
        """
        Check if event matches this filter.

        All specified criteria must match (AND logic).

        Args:
            event: Event to check

        Returns:
            bool: True if event matches filter
        """
        # Check type filter
        if self.types is not None and event.type not in self.types:
            return False

        # Check category filter
        if self.categories is not None and event.category not in self.categories:
            return False

        # Check source filter
        if self.sources is not None and event.source not in self.sources:
            return False

        # Check min priority
        if self.min_priority is not None and event.priority < self.min_priority:
            return False

        # Check max priority
        if self.max_priority is not None and event.priority > self.max_priority:
            return False

        return True

    def __str__(self) -> str:
        """String representation of filter."""
        criteria = []
        if self.types:
            criteria.append(f"types={[t.name for t in self.types]}")
        if self.categories:
            criteria.append(f"categories={[c.value for c in self.categories]}")
        if self.sources:
            criteria.append(f"sources={self.sources}")
        if self.min_priority:
            criteria.append(f"min_priority={self.min_priority.name}")
        if self.max_priority:
            criteria.append(f"max_priority={self.max_priority.name}")

        return f"EventFilter({', '.join(criteria)})"
