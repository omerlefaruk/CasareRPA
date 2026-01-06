"""
Integration tests for Unit of Work and Domain Events.

Tests the JsonUnitOfWork with real EventBus and domain event publishing.
"""

import pytest

from casare_rpa.domain.events import (
    NodeCompleted,
    WorkflowCompleted,
    WorkflowStarted,
    get_event_bus,
)
from casare_rpa.domain.events.bus import reset_event_bus
from casare_rpa.infrastructure.persistence.unit_of_work import JsonUnitOfWork


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_commit_publishes_events(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that committing UoW publishes collected domain events."""
    # Arrange: Create UoW with event bus
    storage_path = integration_sandbox / "uow_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    # Track published events
    published = []

    def event_handler(event):
        published.append(event)

    fresh_event_bus.subscribe(WorkflowStarted, event_handler)
    fresh_event_bus.subscribe(NodeCompleted, event_handler)

    # Act: Use UoW context
    async with await uow.__aenter__():
        # Add events to UoW
        uow.add_event(
            WorkflowStarted(
                workflow_id="wf_001",
                workflow_name="TestWorkflow",
            )
        )
        uow.add_event(
            NodeCompleted(
                node_id="node_001",
                node_type="LogNode",
                workflow_id="wf_001",
                execution_time_ms=10.0,
                output_data={"success": True},
            )
        )

        # Commit
        await uow.commit()

    # Assert: Events were published
    assert len(published) == 2
    assert isinstance(published[0], WorkflowStarted)
    assert isinstance(published[1], NodeCompleted)
    assert published[0].workflow_id == "wf_001"
    assert published[1].node_id == "node_001"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_rollback_discards_events(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that rolling back UoW discards pending events."""
    # Arrange
    storage_path = integration_sandbox / "uow_rollback_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    published = []

    def event_handler(event):
        published.append(event)

    fresh_event_bus.subscribe(WorkflowStarted, event_handler)

    # Act: Use UoW but exit without commit
    async with await uow.__aenter__():
        uow.add_event(
            WorkflowStarted(
                workflow_id="wf_rollback",
                workflow_name="RollbackTest",
            )
        )
        # No commit - should rollback on exit

    # Assert: No events published
    assert len(published) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_creates_storage_directory(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that UoW creates storage directory on entry."""
    # Arrange: Non-existent directory
    storage_path = integration_sandbox / "new_uow_storage"
    assert not storage_path.exists()

    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    # Act: Enter UoW context
    async with await uow.__aenter__():
        # Assert: Directory created
        assert storage_path.exists()

    await uow.rollback()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_track_aggregate_events(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that events from tracked aggregates are collected."""
    # Arrange: Create an aggregate that collects events
    from dataclasses import dataclass, field

    @dataclass
    class TestAggregate:
        """Test aggregate that implements collect_events."""

        _events: list = field(default_factory=list)

        def add_event(self, event):
            self._events.append(event)

        def collect_events(self):
            events = self._events.copy()
            self._events.clear()
            return events

    storage_path = integration_sandbox / "aggregate_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    published = []

    def event_handler(event):
        published.append(event)

    fresh_event_bus.subscribe(NodeCompleted, event_handler)

    # Act: Track aggregate and commit
    async with await uow.__aenter__():
        aggregate = TestAggregate()
        aggregate.add_event(
            NodeCompleted(
                node_id="agg_node",
                node_type="LogNode",
                workflow_id="wf_agg",
                execution_time_ms=10.0,
                output_data={"success": True},
            )
        )

        uow.track(aggregate)
        await uow.commit()

    # Assert: Event from aggregate was published
    assert len(published) == 1
    assert published[0].node_id == "agg_node"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_multiple_commits(
    fresh_event_bus,
    integration_sandbox,
):
    """Test behavior of multiple commits in same context."""
    # Arrange
    storage_path = integration_sandbox / "multi_commit_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    published = []

    def event_handler(event):
        published.append(event)

    fresh_event_bus.subscribe(WorkflowStarted, event_handler)

    # Act: Multiple commits
    async with await uow.__aenter__():
        uow.add_event(WorkflowStarted(workflow_id="wf1", workflow_name="W1"))
        await uow.commit()

        uow.add_event(WorkflowStarted(workflow_id="wf2", workflow_name="W2"))
        await uow.commit()

    # Assert: All events published
    assert len(published) == 2
    assert published[0].workflow_id == "wf1"
    assert published[1].workflow_id == "wf2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that multiple subscribers receive events."""
    # Arrange
    storage_path = integration_sandbox / "multi_sub_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    subscriber1_calls = []
    subscriber2_calls = []

    def handler1(event):
        subscriber1_calls.append(event)

    def handler2(event):
        subscriber2_calls.append(event)

    fresh_event_bus.subscribe(WorkflowCompleted, handler1)
    fresh_event_bus.subscribe(WorkflowCompleted, handler2)

    # Act
    async with await uow.__aenter__():
        uow.add_event(
            WorkflowCompleted(
                workflow_id="wf_multi",
                workflow_name="MultiSubTest",
                execution_time_ms=1500,
                nodes_executed=5,
                nodes_skipped=0,
            )
        )
        await uow.commit()

    # Assert: Both subscribers received the event
    assert len(subscriber1_calls) == 1
    assert len(subscriber2_calls) == 1
    assert subscriber1_calls[0].workflow_id == "wf_multi"
    assert subscriber2_calls[0].workflow_id == "wf_multi"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unit_of_work_commit_idempotent(
    fresh_event_bus,
    integration_sandbox,
):
    """Test that multiple commits don't re-publish same events."""
    # Arrange
    storage_path = integration_sandbox / "idempotent_test"
    uow = JsonUnitOfWork(storage_path, fresh_event_bus)

    published = []

    def event_handler(event):
        published.append(event)

    fresh_event_bus.subscribe(WorkflowStarted, event_handler)

    # Act: Commit same events twice
    async with await uow.__aenter__():
        uow.add_event(WorkflowStarted(workflow_id="wf_idem", workflow_name="IdemTest"))

        await uow.commit()
        await uow.commit()  # Second commit - no new events added

    # Assert: Events published only once
    assert len(published) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_bus_reset_between_tests(
    fresh_event_bus,
):
    """Test that reset_event_bus properly clears state."""
    # Arrange: Subscribe to an event
    calls_before = []

    def handler(event):
        calls_before.append(event)

    fresh_event_bus.subscribe(WorkflowStarted, handler)

    # Act: Publish event
    fresh_event_bus.publish(
        WorkflowStarted(
            workflow_id="before_reset",
            workflow_name="BeforeReset",
        )
    )

    # Assert: Event received
    assert len(calls_before) == 1

    # Act: Reset bus
    reset_event_bus()
    new_bus = get_event_bus()

    calls_after = []

    def new_handler(event):
        calls_after.append(event)

    new_bus.subscribe(WorkflowStarted, new_handler)

    # Act: Publish on new bus
    new_bus.publish(
        WorkflowStarted(
            workflow_id="after_reset",
            workflow_name="AfterReset",
        )
    )

    # Assert: Only new handler receives (old handler was cleared)
    assert len(calls_after) == 1
    # Old handler should NOT be called
    assert len(calls_before) == 1  # Still 1, not incremented
