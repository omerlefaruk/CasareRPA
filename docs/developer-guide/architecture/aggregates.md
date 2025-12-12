# Workflow Aggregate Pattern

This document describes the DDD Aggregate pattern as implemented in CasareRPA, focusing on the Workflow aggregate root.

## What is an Aggregate?

An aggregate is a cluster of domain objects treated as a single unit for data changes. Each aggregate has:

- **Aggregate Root**: The single entry point for all modifications
- **Consistency Boundary**: All invariants enforced within the aggregate
- **Identity**: A unique identifier for the aggregate
- **Domain Events**: Events raised (but not published) during modifications

## DDD 2025 Principles

CasareRPA follows these aggregate principles:

1. **Reference by ID only**: Aggregates reference other aggregates by ID, not object reference
2. **Single transaction**: All modifications within an aggregate are atomic
3. **Event collection**: Domain events are collected during modification, published after transaction
4. **Strong consistency within**: All business rules enforced inside aggregate boundary
5. **Eventual consistency between**: Different aggregates communicate via events

## Workflow Aggregate

**Location**: `src/casare_rpa/domain/aggregates/workflow.py`

The `Workflow` class is the aggregate root for workflow operations.

### Class Structure

```python
from casare_rpa.domain.aggregates import (
    Workflow,           # Aggregate Root
    WorkflowId,         # Strongly-typed ID
    WorkflowNode,       # Entity within aggregate
    Position,           # Value object
    NodeAdded,          # Domain event
    NodeConnected,      # Domain event
)
```

### Creating a Workflow

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

# Generate a new workflow
workflow = Workflow(
    id=WorkflowId.generate(),  # Generates "wf_<12-char-hex>"
    name="Login Automation",
    description="Automates user login process",
)

# Or from existing ID
workflow = Workflow(
    id=WorkflowId.from_string("wf_abc123def456"),
    name="Existing Workflow",
)
```

### Adding Nodes

All node additions go through the aggregate root:

```python
# Add a node - raises NodeAdded event internally
node_id = workflow.add_node(
    node_type="ClickElementNode",
    position=Position(x=100, y=200),
    config={"selector": "#login-btn", "timeout": 30000},
)

# Node ID is returned (e.g., "node_xyz789abc456")
print(f"Created node: {node_id}")
```

### Connecting Nodes

```python
# Create connection - raises NodeConnected event internally
workflow.connect(
    source_node=start_node_id,
    source_port="exec_out",
    target_node=click_node_id,
    target_port="exec_in",
)
```

### Removing Nodes

```python
# Remove node - also removes all its connections
# Raises NodeRemoved event
workflow.remove_node(node_id)
```

### Modifying Nodes

```python
# Move node to new position
workflow.move_node(node_id, Position(x=300, y=400))

# Update node configuration
workflow.update_node_config(node_id, {
    "selector": "#submit-btn",
    "click_type": "double",
})
```

### Querying the Aggregate

```python
# Check if node exists
if workflow.has_node(node_id):
    node = workflow.get_node(node_id)

# Get all nodes
all_nodes = workflow.get_all_nodes()

# Get connections
outgoing = workflow.get_connections_from(node_id)
incoming = workflow.get_connections_to(node_id)
all_connections = workflow.get_all_connections()

# Properties
print(f"Nodes: {workflow.node_count}")
print(f"Connections: {workflow.connection_count}")
```

## Domain Event Collection

A key DDD pattern is that aggregates collect events during modifications but do not publish them immediately. Events are published after the transaction succeeds.

### How It Works

```python
# Create workflow and modify it
workflow = Workflow(id=WorkflowId.generate(), name="Test")

# Each operation raises events internally
node1 = workflow.add_node("StartNode", Position(0, 0))      # NodeAdded
node2 = workflow.add_node("ClickNode", Position(100, 100))  # NodeAdded
workflow.connect(node1, "exec_out", node2, "exec_in")       # NodeConnected

# Check pending events
print(workflow.has_pending_events())  # True

# Collect events (clears internal list)
events = workflow.collect_events()

# Events: [NodeAdded, NodeAdded, NodeConnected]
for event in events:
    print(f"Event: {event.event_type_name}")
```

### Why Collect, Not Publish?

This pattern ensures:

1. **Atomicity**: If transaction fails, no events are published
2. **Ordering**: Events are published in correct order after success
3. **Testability**: Can inspect events without side effects
4. **Flexibility**: Caller decides when/how to publish

## Unit of Work Integration

The Unit of Work pattern manages event publishing after successful persistence.

**Location**: `src/casare_rpa/infrastructure/persistence/unit_of_work.py`

### Basic Usage

```python
from casare_rpa.infrastructure.persistence import JsonUnitOfWork
from casare_rpa.domain.events import get_event_bus
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

event_bus = get_event_bus()

async with JsonUnitOfWork(storage_path, event_bus) as uow:
    # Create workflow
    workflow = Workflow(id=WorkflowId.generate(), name="New Workflow")

    # Modify it
    node_id = workflow.add_node("StartNode", Position(0, 0))

    # Track the aggregate
    uow.track(workflow)

    # Commit - persists data, then publishes events
    await uow.commit()
```

### How It Works

1. **Track Aggregates**: Call `uow.track(aggregate)` for each modified aggregate
2. **Collect Events**: On commit, UoW collects events from all tracked aggregates
3. **Persist First**: UoW persists changes to storage
4. **Publish After**: Only after successful persistence, events are published
5. **Rollback on Failure**: If persistence fails, events are discarded

### Unit of Work Interface

```python
from casare_rpa.domain.interfaces import AbstractUnitOfWork

class AbstractUnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction and publish domain events."""

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction, discard events."""
```

### Adding Events Manually

For events not tied to aggregates:

```python
from casare_rpa.domain.events import VariableSet

async with JsonUnitOfWork(storage_path, event_bus) as uow:
    # ... do work ...

    # Add event manually
    uow.add_event(VariableSet(
        variable_name="result",
        variable_value="success",
        workflow_id="wf_xyz",
    ))

    await uow.commit()  # Publishes the event
```

## Value Objects

### WorkflowId

Strongly-typed identifier preventing ID confusion:

```python
from casare_rpa.domain.aggregates import WorkflowId

# Generate new ID
wf_id = WorkflowId.generate()  # "wf_abc123def456"

# From string
wf_id = WorkflowId.from_string("wf_existing_id")

# Use as string
str(wf_id)  # "wf_abc123def456"
```

### NodeIdValue

Internal node identifier:

```python
from casare_rpa.domain.aggregates.workflow import NodeIdValue

node_id = NodeIdValue.generate()  # "node_xyz789abc456"
```

### Position

Node coordinates:

```python
from casare_rpa.domain.aggregates import Position

pos = Position(x=100.0, y=200.0)
pos_dict = pos.to_dict()  # {"x": 100.0, "y": 200.0}
pos_from_dict = Position.from_dict(pos_dict)
```

### Connection

Immutable connection between ports:

```python
from casare_rpa.domain.aggregates.workflow import Connection, PortReference

connection = Connection(
    source=PortReference(node_id="node_a", port_name="exec_out"),
    target=PortReference(node_id="node_b", port_name="exec_in"),
)

conn_dict = connection.to_dict()
# {
#     "source_node": "node_a",
#     "source_port": "exec_out",
#     "target_node": "node_b",
#     "target_port": "exec_in",
# }
```

## WorkflowNode Entity

`WorkflowNode` is an entity within the aggregate boundary:

```python
from casare_rpa.domain.aggregates.workflow import WorkflowNode, NodeIdValue
from casare_rpa.domain.aggregates import Position

# Created through aggregate root, not directly
# This is internal to the aggregate

node = WorkflowNode(
    id=NodeIdValue.generate(),
    node_type="ClickElementNode",
    position=Position(100, 200),
    config={"selector": "#btn"},
)

# Mutable within aggregate boundary
node.move_to(Position(300, 400))
node.update_config("timeout", 5000)
```

## Serialization

### To Dictionary

```python
workflow = Workflow(id=WorkflowId.generate(), name="Test")
node = workflow.add_node("StartNode", Position(0, 0))

data = workflow.to_dict()
# {
#     "id": "wf_abc123def456",
#     "name": "Test",
#     "description": "",
#     "nodes": {
#         "node_xyz789": {
#             "node_id": "node_xyz789",
#             "node_type": "StartNode",
#             "position": {"x": 0.0, "y": 0.0},
#             "config": {},
#         }
#     },
#     "connections": [],
#     "settings": {"stop_on_error": True, "timeout": 30, "retry_count": 0},
# }
```

### From Dictionary

```python
# Restore from dict (does not replay events)
restored = Workflow.from_dict(data)

# Events from loading are cleared automatically
assert not restored.has_pending_events()
```

## Validation

The aggregate enforces invariants:

```python
# Empty node type
try:
    workflow.add_node("", Position(0, 0))
except ValueError as e:
    print(e)  # "Node type cannot be empty"

# Self-connection
try:
    workflow.connect(node_id, "out", node_id, "in")
except ValueError as e:
    print(e)  # "Cannot connect node to itself"

# Non-existent node
try:
    workflow.remove_node("invalid_id")
except KeyError as e:
    print(e)  # "Node invalid_id not found in workflow"
```

## Complete Example

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position
from casare_rpa.domain.events import get_event_bus
from casare_rpa.infrastructure.persistence import JsonUnitOfWork
from pathlib import Path

async def create_login_workflow() -> Workflow:
    """Create a login automation workflow."""
    event_bus = get_event_bus()
    storage = Path("./workflows")

    async with JsonUnitOfWork(storage, event_bus) as uow:
        # Create workflow
        workflow = Workflow(
            id=WorkflowId.generate(),
            name="Login Automation",
            description="Automates login to example.com",
        )

        # Add nodes
        start = workflow.add_node("StartNode", Position(0, 100))

        launch = workflow.add_node(
            "LaunchBrowserNode",
            Position(200, 100),
            config={"browser_type": "chromium", "headless": False},
        )

        goto = workflow.add_node(
            "GoToURLNode",
            Position(400, 100),
            config={"url": "https://example.com/login"},
        )

        username = workflow.add_node(
            "TypeTextNode",
            Position(600, 100),
            config={"selector": "#username", "text": "{{username}}"},
        )

        password = workflow.add_node(
            "TypeTextNode",
            Position(800, 100),
            config={"selector": "#password", "text": "{{password}}"},
        )

        click = workflow.add_node(
            "ClickElementNode",
            Position(1000, 100),
            config={"selector": "#login-btn"},
        )

        end = workflow.add_node("EndNode", Position(1200, 100))

        # Connect nodes
        workflow.connect(start, "exec_out", launch, "exec_in")
        workflow.connect(launch, "exec_out", goto, "exec_in")
        workflow.connect(goto, "exec_out", username, "exec_in")
        workflow.connect(username, "exec_out", password, "exec_in")
        workflow.connect(password, "exec_out", click, "exec_in")
        workflow.connect(click, "exec_out", end, "exec_in")

        # Track and commit
        uow.track(workflow)
        await uow.commit()

        # Events published: 7x NodeAdded, 6x NodeConnected
        return workflow
```

## Best Practices

1. **Always use aggregate root**: Never modify `WorkflowNode` directly from outside
2. **Collect events after success**: Call `collect_events()` only after persistence succeeds
3. **Use Unit of Work**: Let UoW manage event publication
4. **Reference by ID**: Store `WorkflowId`, not `Workflow` object references
5. **Keep aggregates small**: Workflow contains only nodes and connections
6. **Clear events on load**: When deserializing, clear events to avoid replaying

## Related Documentation

- [Overview](overview.md) - Architecture overview
- [Layers](layers.md) - Layer documentation
- [Events](events.md) - Typed domain events reference
- [Diagrams](diagrams.md) - Architecture diagrams
