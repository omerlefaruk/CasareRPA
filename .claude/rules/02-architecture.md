---
description: DDD 2025 architecture, agents, triggers, events, and indexes
---

# Architecture & DDD

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

## Key Patterns

| Pattern | Location | Description |
|---------|----------|-------------|
| **EventBus** | `domain/events.py` | `get_event_bus()` singleton |
| **Typed Events** | `domain/events/*.py` | Frozen dataclass events |
| **Aggregates** | `domain/aggregates/workflow.py` | Consistency boundaries |
| **Unit of Work** | `infrastructure/persistence/unit_of_work.py` | Transactions + events |
| **CQRS Queries** | `application/queries/` | Read-optimized DTOs |
| **Qt Event Bridge** | `presentation/canvas/coordinators/event_bridge.py` | Domain→Qt signals |

### EventBus Usage

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.subscribe(NodeCompleted, handler_function)
bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
```

### Workflow Aggregate

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

workflow = Workflow(id=WorkflowId.generate(), name="My Flow")
node_id = workflow.add_node("ClickNode", Position(100, 200))
events = workflow.collect_events()  # [NodeAdded]
```

## Modern Node Standard (2025)

All 430+ nodes follow **Schema-Driven Logic**:

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

**Requirements:**
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for optional properties (dual-source: port → config)
- Explicit DataType on all ports (ANY is valid)
- **NEVER use `self.config.get()`** (LEGACY)

## Agent & Skill Registry

### Agents (Workflow Phases)

| Agent | Purpose |
|-------|---------|
| architect | System design, planning |
| builder | Code writing (KISS & DDD) |
| quality | Testing, performance |
| reviewer | Code review gate |
| docs | Documentation |
| researcher | Web research |
| ui | PySide6 UI |
| general | General tasks |

### Skills (Utilities)

| Skill | Purpose |
|-------|---------|
| explorer | Codebase search |
| refactor | Safe refactoring |
| integrations | External APIs |
| test-generator | Test templates |
| ui-specialist | Widget styling |
| ci-cd | GitHub Actions |
| security-auditor | Security review |

### Phase Mapping

| Phase | Agent/Skill |
|-------|-------------|
| RESEARCH | explorer(skill) + researcher(agent) |
| PLAN | architect |
| TESTS FIRST | quality |
| IMPLEMENT | builder / ui / refactor(skill) / integrations(skill) |
| CODE REVIEW | reviewer |
| DOCS | docs |

### Standard Flow

```
explorer(skill) → architect → builder → quality → reviewer → docs
```

## Triggers

| Type | Description |
|------|-------------|
| Manual | User clicks run |
| Schedule | Cron-based execution |
| Event | File system or external event |
| API | HTTP webhook trigger |

Triggers initiate workflow execution via `ExecutionOrchestrator`. Must handle their own error logging.

## DDD Events Reference

### Node Events

| Event | When Fired |
|-------|------------|
| `NodeStarted` | Node begins execution |
| `NodeCompleted` | Node completes successfully |
| `NodeFailed` | Node encounters error |
| `NodeSkipped` | Node skipped (conditional) |
| `NodeStatusChanged` | Any status transition |

### Workflow Events

| Event | When Fired |
|-------|------------|
| `WorkflowStarted` | Workflow begins |
| `WorkflowCompleted` | Workflow succeeds |
| `WorkflowFailed` | Workflow fails |
| `WorkflowStopped` | User stops workflow |
| `WorkflowProgress` | Progress update |

### System Events

| Event | When Fired |
|-------|------------|
| `VariableSet` | Variable changed |
| `BrowserPageReady` | Browser page ready |
| `LogMessage` | Log emitted |

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
