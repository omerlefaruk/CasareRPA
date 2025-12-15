# Architecture & Agents

## DDD 2025 Layers
| Layer | Responsibility | Path |
|-------|----------------|------|
| Domain | Pure logic, entities, aggregates, events | `domain/` |
| Application | Use cases, queries (CQRS) | `application/` |
| Infrastructure | Persistence, HTTP, adapters | `infrastructure/` |
| Presentation | Qt UI, coordinators | `presentation/` |

## Three Applications
1. **Canvas** (Designer): `presentation/canvas/`
2. **Robot** (Executor): `infrastructure/robot/`
3. **Orchestrator** (Manager): `infrastructure/orchestrator/`

## DDD 2025 Key Patterns

| Pattern | Location | Description |
|---------|----------|-------------|
| **EventBus** | `domain/events.py` | `get_event_bus()` singleton |
| **Typed Events** | `domain/events/*.py` | Frozen dataclass events |
| **Aggregates** | `domain/aggregates/workflow.py` | Consistency boundaries |
| **Unit of Work** | `infrastructure/persistence/unit_of_work.py` | Transactions + events |
| **CQRS Queries** | `application/queries/` | Read-optimized DTOs |
| **Qt Event Bridge** | `presentation/canvas/coordinators/event_bridge.py` | Domain→Qt signals |

### Typed Events (MANDATORY)
```python
# CORRECT
from casare_rpa.domain.events import NodeCompleted, get_event_bus
bus = get_event_bus()
bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))

# Subscribe
bus.subscribe(NodeCompleted, handler_function)
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

## Other Key Patterns
| Pattern | Location |
|---------|----------|
| UnifiedHttpClient | `infrastructure/http/` |
| SignalCoordinator | `presentation/canvas/coordinators/` |
| Theme | `presentation/canvas/ui/theme.py` |

## Agent Registry

### By Phase
| Phase | Agent | Purpose |
|-------|-------|---------|
| RESEARCH | explore | Codebase search |
| RESEARCH | researcher | Web research (exa/Ref) |
| PLAN | architect | Design strategy |
| EXECUTE | builder | Write code (KISS & DDD) |
| EXECUTE | refactor | Code cleanup |
| EXECUTE | ui | Qt/Canvas UI |
| EXECUTE | integrations | External APIs |
| VALIDATE | quality | Tests, performance |
| VALIDATE | reviewer | Code review (APPROVED/ISSUES) |
| DOCS | docs | Documentation |

### Standard Flow
```
explore → architect → builder → quality → reviewer → docs
```

### MCP Tools
- **exa**: Research, best practices, library docs
- **Ref**: API signatures, SDK reference

Use exa/Ref before writing unfamiliar code.

## Index Locations (Priority)

| P0 (Always) | Purpose |
|-------------|---------|
| `nodes/_index.md` | Node registry |
| `visual_nodes/_index.md` | Visual nodes |
| `domain/_index.md` | Core entities, aggregates, events |

| P1 (Common) | Purpose |
|-------------|---------|
| `infrastructure/_index.md` | Adapters |
| `application/_index.md` | Use cases, queries |
| `canvas/ui/_index.md` | Theme, widgets |

## Brain Protocol

| File | When to Load |
|------|--------------|
| `.brain/context/current.md` | Session start (always) |
| `.brain/projectRules.md` | Implementing |
| `.brain/systemPatterns.md` | Designing |
| `.brain/docs/*` | Specific tasks |
