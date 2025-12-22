"""
CasareRPA - Domain Event Base Class

Base class for all typed domain events following DDD 2025 patterns.
All domain events are immutable value objects (frozen dataclasses).
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for all domain events.

    Domain events are immutable facts about something that happened in the domain.
    They are used for:
    - Cross-aggregate communication
    - Event-driven architecture
    - Audit logging
    - UI updates via Qt signal bridge

    All events are frozen (immutable) and include:
    - event_id: Unique identifier for deduplication
    - occurred_on: Timestamp when the event occurred

    Example:
        @dataclass(frozen=True)
        class OrderPlaced(DomainEvent):
            order_id: str
            customer_id: str
            total: float
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize event to dictionary.

        Subclasses should call super().to_dict() and add their fields.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": self.__class__.__name__,
            "event_id": str(self.event_id),
            "occurred_on": self.occurred_on.isoformat(),
        }

    @property
    def event_type_name(self) -> str:
        """Get the event type name (class name)."""
        return self.__class__.__name__


@dataclass(frozen=True)
class AggregateEvent(DomainEvent):
    """
    Base class for events raised by aggregates.

    Includes the aggregate_id for routing and correlation.
    """

    aggregate_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize including aggregate_id."""
        result = super().to_dict()
        result["aggregate_id"] = self.aggregate_id
        return result


__all__ = [
    "DomainEvent",
    "AggregateEvent",
]
