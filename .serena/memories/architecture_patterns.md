# Architecture Patterns - CasareRPA

## DDD 2025 Layers
| Layer | Responsibility | Path |
|-------|----------------|------|
| Domain | Pure logic, entities, aggregates, events | `domain/` |
| Application | Use cases, queries (CQRS) | `application/` |
| Infrastructure | Persistence, HTTP, adapters | `infrastructure/` |
| Presentation | Qt UI, coordinators | `presentation/` |

## Domain Layer Patterns

### EventBus (Typed Events)
```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
bus.subscribe(NodeCompleted, handler_function)  # Use named function, NOT lambda
```

### Workflow Aggregate
```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

workflow = Workflow(id=WorkflowId.generate(), name="My Flow")
node_id = workflow.add_node("ClickNode", Position(100, 200))
events = workflow.collect_events()  # [NodeAdded]
```

### Unit of Work
```python
async with JsonUnitOfWork(path, event_bus) as uow:
    uow.track(workflow)
    await uow.commit()  # Publishes collected events
```

## Node System (Modern Standard 2025)

All nodes follow **Schema-Driven Logic**:
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for optional properties (dual-source: port → config)
- Explicit `DataType` on all ports (ANY is valid)
- NEVER use `self.config.get()` (LEGACY)

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")              # required
        timeout = self.get_parameter("timeout", 30000)  # optional
```

## Port Definition (CRITICAL)

### Data Ports
```python
# CORRECT - 2 args: name, DataType
self.add_input_port("url", DataType.STRING)
self.add_output_port("result", DataType.DICT)
```

### Exec Ports
```python
# CORRECT - Use dedicated methods
self.add_exec_input("exec_in")
self.add_exec_output("exec_out")
```

## Key Patterns Reference
| Pattern | Location |
|---------|----------|
| EventBus | `domain/events.py` |
| Typed Events | `domain/events/*.py` |
| Aggregates | `domain/aggregates/workflow.py` |
| Unit of Work | `infrastructure/persistence/unit_of_work.py` |
| CQRS Queries | `application/queries/` |
| Qt Event Bridge | `presentation/canvas/coordinators/event_bridge.py` |
| UnifiedHttpClient | `infrastructure/http/` |
| SignalCoordinator | `presentation/canvas/coordinators/` |
| Theme | `presentation/canvas/theme.py` |

## Node Categories
| Category | Base Class | Context |
|----------|------------|---------|
| browser | BrowserBaseNode | PlaywrightPage |
| desktop | DesktopNodeBase | DesktopContext |
| data | BaseNode | None |
| http | BaseNode | UnifiedHttpClient |
| system | BaseNode | None |
| control_flow | BaseNode | None |
| variable | BaseNode | ExecutionContext |
