"""
CasareRPA - Domain Aggregates

Aggregates are clusters of domain objects that are treated as a unit
for data changes. Each aggregate has a root entity through which all
modifications must flow.

Following DDD 2025 patterns:
- Aggregates reference other aggregates by ID only
- Domain events are collected in aggregate, published after transaction
- Strong consistency within aggregate boundary
- Eventual consistency between aggregates

Usage:
    from casare_rpa.domain.aggregates import (
        Workflow,
        WorkflowId,
        WorkflowNode,
        Position,
        NodeAdded,
    )

    # Create workflow aggregate
    workflow = Workflow(
        id=WorkflowId.generate(),
        name="My Workflow",
    )

    # Add node through aggregate root
    node_id = workflow.add_node(
        node_type="ClickElementNode",
        position=Position(x=100, y=200),
        config={"selector": "#button"},
    )

    # Collect and publish events
    events = workflow.collect_events()
    for event in events:
        event_bus.publish(event)
"""

from casare_rpa.domain.aggregates.workflow import (
    Connection,
    NodeIdValue,
    PortReference,
    # Aggregate Root
    Workflow,
    # Value Objects
    WorkflowId,
    # Entities
    WorkflowNode,
)

# Re-export workflow structure events from events module
from casare_rpa.domain.events.workflow_events import (
    NodeAdded,
    NodeConnected,
    NodeDisconnected,
    NodeRemoved,
)

# Re-export Position from value_objects for convenience
from casare_rpa.domain.value_objects.position import Position

__all__ = [
    # Aggregate Root
    "Workflow",
    # Value Objects
    "WorkflowId",
    "NodeIdValue",
    "PortReference",
    "Connection",
    "Position",
    # Events
    "NodeAdded",
    "NodeRemoved",
    "NodeConnected",
    "NodeDisconnected",
    # Entities
    "WorkflowNode",
]
