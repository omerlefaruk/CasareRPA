---
description: Typed events reference for DDD architecture
---

# DDD Events Reference

## Typed Event System (DDD 2025)

CasareRPA uses typed domain events (frozen dataclasses) for all event-driven communication.

## Quick Reference

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

def handle_node_completed(event: NodeCompleted) -> None:
    print(f"Node {event.node_id} done in {event.execution_time_ms}ms")

bus = get_event_bus()
bus.subscribe(NodeCompleted, handle_node_completed)  # Use named function, NOT lambda
bus.publish(NodeCompleted(node_id="x", node_type="MyNode", workflow_id="wf1", execution_time_ms=100))
```

## Event Classes

### Node Events (`domain/events/node_events.py`)
| Event | Attributes | When Fired |
|-------|------------|------------|
| `NodeStarted` | node_id, node_type, workflow_id | Node begins execution |
| `NodeCompleted` | node_id, node_type, workflow_id, execution_time_ms, output_data | Node completes successfully |
| `NodeFailed` | node_id, node_type, workflow_id, error_code, error_message, is_retryable | Node encounters error |
| `NodeSkipped` | node_id, node_type, workflow_id, reason | Node skipped (conditional) |
| `NodeStatusChanged` | node_id, old_status, new_status | Any status transition |

### Workflow Events (`domain/events/workflow_events.py`)
| Event | Attributes | When Fired |
|-------|------------|------------|
| `WorkflowStarted` | workflow_id, workflow_name, execution_mode, triggered_by, total_nodes | Workflow begins |
| `WorkflowCompleted` | workflow_id, workflow_name, execution_time_ms, nodes_executed, nodes_skipped | Workflow succeeds |
| `WorkflowFailed` | workflow_id, workflow_name, failed_node_id, error_code, error_message | Workflow fails |
| `WorkflowStopped` | workflow_id, stopped_at_node_id, reason | User stops workflow |
| `WorkflowPaused` | workflow_id, paused_at_node_id, reason | Debug pause |
| `WorkflowResumed` | workflow_id, resume_from_node_id | Debug resume |
| `WorkflowProgress` | workflow_id, current_node_id, completed_nodes, total_nodes, percentage | Progress update |

### Aggregate Events (from Workflow Aggregate)
| Event | Attributes | When Fired |
|-------|------------|------------|
| `NodeAdded` | workflow_id, node_id, node_type, position_x, position_y | Node added to workflow |
| `NodeRemoved` | workflow_id, node_id | Node removed from workflow |
| `NodeConnected` | workflow_id, source_node, source_port, target_node, target_port | Connection created |
| `NodeDisconnected` | workflow_id, source_node, source_port, target_node, target_port | Connection removed |

### System Events (`domain/events/system_events.py`)
| Event | Attributes | When Fired |
|-------|------------|------------|
| `VariableSet` | variable_name, variable_value, workflow_id, source_node_id | Variable changed |
| `BrowserPageReady` | page_id, url, title, browser_type | Browser page ready |
| `LogMessage` | level, message, source, node_id, workflow_id, extra_data | Log emitted |
| `DebugBreakpointHit` | node_id, workflow_id, variables | Breakpoint hit |
| `ResourceAcquired` | resource_type, resource_id, workflow_id | Resource acquired |
| `ResourceReleased` | resource_type, resource_id, workflow_id | Resource released |

## EventBus API

```python
from casare_rpa.domain.events import EventBus, get_event_bus

bus = get_event_bus()  # Singleton

# Subscribe to event type
bus.subscribe(NodeCompleted, handler_function)

# Publish event
bus.publish(NodeCompleted(node_id="x", execution_time_ms=150))

# Unsubscribe
bus.unsubscribe(NodeCompleted, handler_function)

# Wildcard subscription (all events)
bus.subscribe_all(log_handler)

# Get event history
history = bus.get_history(NodeCompleted, limit=10)
```

## Creating Custom Events

```python
from dataclasses import dataclass
from casare_rpa.domain.events.base import DomainEvent

@dataclass(frozen=True)
class MyCustomEvent(DomainEvent):
    """Describe when this event fires."""
    my_field: str = ""

    def to_dict(self) -> dict:
        result = super().to_dict()
        result["my_field"] = self.my_field
        return result
```

## Best Practices

1. **Immutable**: Events are frozen dataclasses - never modify after creation
2. **Self-describing**: Event class name indicates what happened
3. **Type-safe**: IDE autocomplete and type checking for event attributes
4. **Aggregate Events**: Collect events, publish after transaction via Unit of Work
