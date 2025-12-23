"""
EventBatcher for high-frequency event batching.

Batches high-frequency events (VARIABLE_UPDATED, NODE_PROPERTY_CHANGED,
NODE_POSITION_CHANGED) to reduce handler calls and improve UI responsiveness.

Uses a 16ms batching interval targeting 60fps UI updates.

Usage:
    from casare_rpa.presentation.canvas.events import EventBatcher, Event, EventType

    batcher = EventBatcher(interval_ms=16)

    # Batch high-frequency events
    batcher.batch(Event(
        type=EventType.VARIABLE_UPDATED,
        source="VariableController",
        data={"name": "counter", "value": 1}
    ))

    # Non-batchable events publish immediately
    batcher.batch(Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    ))
"""

from typing import Dict, List, Set

from loguru import logger
from PySide6.QtCore import QTimer

from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event_types import EventType

# Maximum pending events per type before overflow warning
MAX_PENDING_EVENTS = 10000

# Batching interval in milliseconds (60fps = 16.67ms)
DEFAULT_BATCH_INTERVAL_MS = 16


class EventBatcher:
    """
    Batches high-frequency events to reduce handler calls.

    High-frequency events like VARIABLE_UPDATED, NODE_PROPERTY_CHANGED, and
    NODE_POSITION_CHANGED are batched over a configurable interval (default 16ms
    for 60fps). When the interval elapses, a single batched event is published
    containing all accumulated events.

    Non-batchable events are published immediately without batching.

    Attributes:
        interval_ms: Batching interval in milliseconds (default 16 for 60fps)
        pending: Map of event types to lists of pending events
        timer: QTimer for flush scheduling

    Thread Safety:
        This class is designed for use on the Qt main thread only.
        QTimer ensures proper Qt event loop integration.
    """

    BATCHABLE_EVENTS: set[EventType] = {
        EventType.VARIABLE_UPDATED,
        EventType.NODE_PROPERTY_CHANGED,
        EventType.NODE_POSITION_CHANGED,
    }
    """Event types eligible for batching."""

    def __init__(self, interval_ms: int = DEFAULT_BATCH_INTERVAL_MS) -> None:
        """
        Initialize EventBatcher.

        Args:
            interval_ms: Batching interval in milliseconds.
                        Default is 16ms (~60fps).
        """
        self.interval_ms = interval_ms
        self.pending: dict[EventType, list[Event]] = {}
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._flush)

    def batch(self, event: Event) -> None:
        """
        Submit event for batching or immediate publication.

        If event type is in BATCHABLE_EVENTS, the event is queued and will
        be published as part of a batched event when the timer fires.

        If event type is not batchable, the event is published immediately
        to ensure critical events are not delayed.

        Args:
            event: Event to batch or publish immediately
        """
        if event.type not in self.BATCHABLE_EVENTS:
            EventBus().publish(event)
            return

        if event.type not in self.pending:
            self.pending[event.type] = []

        # Check for overflow before adding
        event_list = self.pending[event.type]
        if len(event_list) >= MAX_PENDING_EVENTS:
            logger.warning(
                f"EventBatcher overflow: {event.type.name} has {len(event_list)} pending events. "
                f"Forcing flush to prevent memory leak."
            )
            self.flush_now()
            # Re-initialize after flush
            if event.type not in self.pending:
                self.pending[event.type] = []

        self.pending[event.type].append(event)

        if not self.timer.isActive():
            self.timer.start(self.interval_ms)

    def _flush(self) -> None:
        """
        Flush all pending events as batched events.

        Called when timer fires. Publishes one batched event per event type
        containing all accumulated events since last flush.
        """
        for event_type, events in self.pending.items():
            if events:
                EventBus().publish(
                    Event(
                        type=event_type,
                        source="EventBatcher",
                        data={
                            "batched_events": events,
                            "count": len(events),
                        },
                    )
                )
        self.pending.clear()
        self.timer.stop()

    def flush_now(self) -> None:
        """
        Force immediate flush of all pending events.

        Useful for testing or when immediate processing is required.
        """
        if self.timer.isActive():
            self.timer.stop()
        self._flush()

    def clear(self) -> None:
        """
        Clear all pending events without publishing.

        Useful for cleanup or when pending events should be discarded.
        """
        self.pending.clear()
        if self.timer.isActive():
            self.timer.stop()

    def has_pending(self) -> bool:
        """
        Check if there are pending events.

        Returns:
            bool: True if there are events waiting to be flushed
        """
        return bool(self.pending)

    def pending_count(self) -> int:
        """
        Get total count of pending events.

        Returns:
            int: Total number of pending events across all types
        """
        return sum(len(events) for events in self.pending.values())

    def __repr__(self) -> str:
        """String representation of EventBatcher."""
        return (
            f"EventBatcher("
            f"interval_ms={self.interval_ms}, "
            f"pending={self.pending_count()}, "
            f"active={self.timer.isActive()}"
            f")"
        )
