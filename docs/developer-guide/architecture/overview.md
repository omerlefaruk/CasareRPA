# CasareRPA Architecture Overview

CasareRPA is a Windows RPA platform built on Domain-Driven Design (DDD) 2025 patterns. This document provides a high-level overview of the architecture.

## DDD 2025 Architecture

The architecture follows strict layer separation with dependency inversion. Inner layers have no knowledge of outer layers.

```
+------------------+
|   Presentation   |  Qt UI (PySide6)
+------------------+
        |
        v
+------------------+
|   Application    |  Use Cases, CQRS Queries
+------------------+
        |
        v
+------------------+
|   Domain         |  Pure Business Logic
+------------------+
        ^
        |
+------------------+
| Infrastructure   |  Adapters (DB, HTTP, Browser)
+------------------+
```

## Dependency Rule

Dependencies flow inward only:

- **Domain Layer**: No dependencies on other layers. Pure Python.
- **Application Layer**: Depends only on Domain.
- **Infrastructure Layer**: Depends on Domain and Application. Implements interfaces defined in Domain.
- **Presentation Layer**: Can depend on all layers.

## Three Applications

CasareRPA consists of three distinct applications:

### 1. Canvas (Designer)

The visual workflow designer built with PySide6 and NodeGraphQt.

- **Path**: `src/casare_rpa/presentation/canvas/`
- **Purpose**: Create and edit RPA workflows visually
- **Technology**: PySide6, NodeGraphQt
- **Key Components**:
  - Visual node editor
  - Property panels
  - Execution controller
  - Debug panel

### 2. Robot (Executor)

Headless workflow execution engine for running automations.

- **Path**: `src/casare_rpa/infrastructure/agent/`
- **Purpose**: Execute workflows without UI
- **Technology**: Playwright, uiautomation
- **Key Components**:
  - RobotAgent
  - JobExecutor
  - HeartbeatService

### 3. Orchestrator (Manager)

Distributed workflow management and scheduling.

- **Path**: `src/casare_rpa/infrastructure/orchestrator/`
- **Purpose**: Manage robots, schedule jobs, distribute work
- **Technology**: FastAPI, PostgreSQL (via pgqueuer)
- **Key Components**:
  - Job queue
  - Robot registry
  - Schedule manager
  - WebSocket notifications

## Key Architectural Patterns

### Typed Domain Events

All inter-component communication uses typed, frozen dataclass events:

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.subscribe(NodeCompleted, handler)
bus.publish(NodeCompleted(node_id="x", execution_time_ms=150))
```

### Workflow Aggregate

Workflows are DDD aggregates with strict consistency boundaries:

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

workflow = Workflow(id=WorkflowId.generate(), name="My Automation")
node_id = workflow.add_node("ClickElementNode", Position(100, 200))
events = workflow.collect_events()  # Domain events raised
```

### Unit of Work

Transactions and event publishing are managed through Unit of Work:

```python
from casare_rpa.infrastructure.persistence import JsonUnitOfWork

async with JsonUnitOfWork(path, event_bus) as uow:
    uow.track(workflow)
    await uow.commit()  # Persists and publishes events
```

### CQRS (Command Query Responsibility Segregation)

Commands (use cases) and queries are separated:

- **Commands**: `application/use_cases/` - Modify state
- **Queries**: `application/queries/` - Read-only DTOs

### Qt Event Bridge

Domain events are bridged to Qt signals for UI updates:

```python
from casare_rpa.presentation.canvas.coordinators import QtDomainEventBridge

bridge = QtDomainEventBridge(get_event_bus())
bridge.node_completed.connect(on_node_completed)
```

## Directory Structure

```
src/casare_rpa/
    domain/                  # Pure business logic
        aggregates/          # Workflow aggregate root
        entities/            # BaseNode, Variable, Project
        events/              # Typed domain events
        interfaces/          # INode, IExecutionContext
        schemas/             # PropertyDef, PropertyType
        services/            # Domain services
        value_objects/       # DataType, NodeStatus, Port

    application/             # Use cases and queries
        use_cases/           # ExecuteWorkflowUseCase, NodeExecutor
        queries/             # CQRS read queries
        services/            # ExecutionLifecycleManager

    infrastructure/          # External adapters
        agent/               # RobotAgent, JobExecutor
        browser/             # PlaywrightManager
        http/                # UnifiedHttpClient
        persistence/         # JsonUnitOfWork, ProjectStorage

    presentation/            # UI layer
        canvas/              # PySide6 designer
            controllers/     # MVC controllers
            coordinators/    # Signal coordination
            visual_nodes/    # 405 visual node classes
            ui/              # Widgets and panels

    nodes/                   # 413+ automation nodes
        browser/             # Web automation
        desktop_nodes/       # Windows UI automation
        control_flow/        # If, Loop, Switch
        http/                # REST API calls
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| UI Framework | PySide6 (Qt 6) |
| Node Editor | NodeGraphQt |
| Browser Automation | Playwright |
| Desktop Automation | uiautomation |
| HTTP Client | httpx (via UnifiedHttpClient) |
| API Framework | FastAPI |
| Job Queue | pgqueuer (PostgreSQL) |
| Logging | loguru |
| Type System | Strict typing with dataclasses |

## Related Documentation

- [Layers](layers.md) - Detailed layer documentation
- [Events](events.md) - Typed domain events reference
- [Aggregates](aggregates.md) - Workflow aggregate pattern
- [Diagrams](diagrams.md) - Architecture diagrams
