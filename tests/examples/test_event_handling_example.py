"""
Example: Event System Usage

AI-HINT: Copy this pattern when working with domain events.
AI-CONTEXT: Shows how to publish and subscribe to typed events.

Run: pytest tests/examples/test_event_handling_example.py -v
"""

import pytest
from dataclasses import dataclass
from typing import List

# =============================================================================
# STEP 1: Import the event system
# =============================================================================

from casare_rpa.domain.events import (
    get_event_bus,
    reset_event_bus,
)
from casare_rpa.domain.events.base import DomainEvent


# =============================================================================
# STEP 2: Define custom events (if needed)
# =============================================================================


# Note: Python 3.10+ allows kw_only=True to handle inheritance with defaults
@dataclass(frozen=True, kw_only=True)
class ExampleTaskStarted(DomainEvent):
    """
    AI-HINT: Custom event example.
    AI-CONTEXT: Events are frozen dataclasses with typed fields.
    AI-WARNING: Use kw_only=True when extending DomainEvent (parent has defaults).

    Emitted when an example task begins.
    """

    task_id: str
    task_name: str
    priority: int = 1


@dataclass(frozen=True, kw_only=True)
class ExampleTaskCompleted(DomainEvent):
    """Emitted when an example task completes."""

    task_id: str
    result: str
    duration_ms: int


@dataclass(frozen=True, kw_only=True)
class ExampleTaskFailed(DomainEvent):
    """Emitted when an example task fails."""

    task_id: str
    error_message: str
    is_retryable: bool = True


# =============================================================================
# STEP 3: Create event handlers
# =============================================================================


class ExampleEventCollector:
    """
    AI-HINT: Example handler that collects events.
    AI-CONTEXT: Useful for testing event flow.
    """

    def __init__(self):
        self.events: List[DomainEvent] = []
        self.started_count = 0
        self.completed_count = 0
        self.failed_count = 0

    def on_task_started(self, event: ExampleTaskStarted):
        """Handler for task started events."""
        self.events.append(event)
        self.started_count += 1

    def on_task_completed(self, event: ExampleTaskCompleted):
        """Handler for task completed events."""
        self.events.append(event)
        self.completed_count += 1

    def on_task_failed(self, event: ExampleTaskFailed):
        """Handler for task failed events."""
        self.events.append(event)
        self.failed_count += 1

    def on_any_event(self, event: DomainEvent):
        """Wildcard handler for any event."""
        # This captures ALL events
        pass


# =============================================================================
# STEP 4: Test fixtures
# =============================================================================


@pytest.fixture
def event_bus():
    """
    AI-HINT: Reset event bus before each test.
    AI-CONTEXT: Prevents test pollution from leftover subscriptions.
    """
    reset_event_bus()
    return get_event_bus()


@pytest.fixture
def collector():
    """Create fresh event collector."""
    return ExampleEventCollector()


# =============================================================================
# STEP 5: Test the event system
# =============================================================================


class TestEventPublishSubscribe:
    """
    AI-HINT: Tests demonstrate pub/sub pattern.
    AI-CONTEXT: Events are the backbone of loose coupling.
    """

    def test_subscribe_and_publish_single_event(self, event_bus, collector):
        """
        Basic pub/sub flow.

        AI-HINT: This is the most common pattern.
        """
        # Arrange - subscribe handler
        event_bus.subscribe(ExampleTaskStarted, collector.on_task_started)

        # Act - publish event
<<<<<<< HEAD
        event = ExampleTaskStarted(
            task_id="task_1", task_name="Example Task", priority=2
        )
=======
        event = ExampleTaskStarted(task_id="task_1", task_name="Example Task", priority=2)
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        event_bus.publish(event)

        # Assert
        assert collector.started_count == 1
        assert len(collector.events) == 1
        assert collector.events[0].task_id == "task_1"

    def test_multiple_subscribers_same_event(self, event_bus):
        """Multiple handlers can subscribe to same event type."""
        results = []

        def handler_a(event):
            results.append(("a", event.task_id))

        def handler_b(event):
            results.append(("b", event.task_id))

        # Arrange - two subscribers
        event_bus.subscribe(ExampleTaskStarted, handler_a)
        event_bus.subscribe(ExampleTaskStarted, handler_b)

        # Act
        event_bus.publish(ExampleTaskStarted(task_id="t1", task_name="Test"))

        # Assert - both handlers called
        assert len(results) == 2
        assert ("a", "t1") in results
        assert ("b", "t1") in results

    def test_different_event_types_routed_correctly(self, event_bus, collector):
        """Events are routed to correct handlers by type."""
        # Arrange
        event_bus.subscribe(ExampleTaskStarted, collector.on_task_started)
        event_bus.subscribe(ExampleTaskCompleted, collector.on_task_completed)
        event_bus.subscribe(ExampleTaskFailed, collector.on_task_failed)

        # Act - publish different events
        event_bus.publish(ExampleTaskStarted(task_id="t1", task_name="Task 1"))
<<<<<<< HEAD
        event_bus.publish(
            ExampleTaskCompleted(task_id="t1", result="ok", duration_ms=100)
        )
=======
        event_bus.publish(ExampleTaskCompleted(task_id="t1", result="ok", duration_ms=100))
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        event_bus.publish(ExampleTaskFailed(task_id="t2", error_message="oops"))

        # Assert - each handler got correct event type
        assert collector.started_count == 1
        assert collector.completed_count == 1
        assert collector.failed_count == 1

    def test_subscribe_all_receives_everything(self, event_bus):
        """
        Wildcard subscription captures all events.

        AI-HINT: Use for logging, metrics, or debugging.
        """
        all_events = []

        def capture_all(event):
            all_events.append(event)

        # Arrange - subscribe to all
        event_bus.subscribe_all(capture_all)

        # Act - publish various events
        event_bus.publish(ExampleTaskStarted(task_id="t1", task_name="A"))
<<<<<<< HEAD
        event_bus.publish(
            ExampleTaskCompleted(task_id="t1", result="done", duration_ms=50)
        )
=======
        event_bus.publish(ExampleTaskCompleted(task_id="t1", result="done", duration_ms=50))
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        # Assert
        assert len(all_events) == 2

    def test_unsubscribe(self, event_bus, collector):
        """Handler can be unsubscribed."""
        # Arrange
        event_bus.subscribe(ExampleTaskStarted, collector.on_task_started)

        # Publish once - should be received
        event_bus.publish(ExampleTaskStarted(task_id="t1", task_name="Test"))
        assert collector.started_count == 1

        # Act - unsubscribe
        event_bus.unsubscribe(ExampleTaskStarted, collector.on_task_started)

        # Publish again - should NOT be received
        event_bus.publish(ExampleTaskStarted(task_id="t2", task_name="Test 2"))

        # Assert - count unchanged
        assert collector.started_count == 1


class TestEventImmutability:
    """
    AI-HINT: Events must be immutable (frozen=True).
    AI-CONTEXT: This ensures event integrity across handlers.
    """

    def test_event_is_frozen(self):
        """Cannot modify event after creation."""
        event = ExampleTaskStarted(task_id="t1", task_name="Test")

        with pytest.raises(AttributeError):
            event.task_id = "modified"  # Should fail

    def test_event_has_timestamp(self):
        """Events automatically get occurred_on timestamp."""
        event = ExampleTaskStarted(task_id="t1", task_name="Test")

        # DomainEvent base class adds occurred_on (timestamp when event was created)
        assert hasattr(event, "occurred_on")


class TestEventUsagePatterns:
    """Common patterns for using events in real code."""

    def test_event_driven_workflow(self, event_bus):
        """
        AI-HINT: Example of event-driven task coordination.
        AI-CONTEXT: This pattern is used in workflow execution.
        """
        execution_log = []

        def on_start(event):
            execution_log.append(f"Started: {event.task_name}")

        def on_complete(event):
            execution_log.append(f"Completed in {event.duration_ms}ms")

        def on_fail(event):
            execution_log.append(f"Failed: {event.error_message}")

        # Subscribe handlers
        event_bus.subscribe(ExampleTaskStarted, on_start)
        event_bus.subscribe(ExampleTaskCompleted, on_complete)
        event_bus.subscribe(ExampleTaskFailed, on_fail)

        # Simulate workflow execution
        event_bus.publish(ExampleTaskStarted(task_id="wf1", task_name="My Workflow"))
<<<<<<< HEAD
        event_bus.publish(
            ExampleTaskCompleted(task_id="wf1", result="success", duration_ms=150)
        )
=======
        event_bus.publish(ExampleTaskCompleted(task_id="wf1", result="success", duration_ms=150))
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        # Verify log
        assert execution_log == ["Started: My Workflow", "Completed in 150ms"]


# =============================================================================
# USAGE NOTES FOR AI AGENTS
# =============================================================================
"""
AI-HINT: Event system key points.

1. CREATING EVENTS:
   - Use @dataclass(frozen=True)
   - Extend DomainEvent base class
   - Keep events small and focused

2. PUBLISHING:
   ```python
   from casare_rpa.domain.events import get_event_bus
   bus = get_event_bus()
   bus.publish(MyEvent(field1="value", field2=123))
   ```

3. SUBSCRIBING:
   ```python
   bus.subscribe(MyEvent, my_handler_function)
   bus.subscribe_all(wildcard_handler)  # All events
   ```

4. COMMON EVENTS (already defined):
   - NodeStarted, NodeCompleted, NodeFailed
   - WorkflowStarted, WorkflowCompleted, WorkflowFailed
   - VariableSet, BrowserPageReady

5. TESTING:
   - Always reset_event_bus() in fixtures
   - Use collector pattern to verify events
"""
