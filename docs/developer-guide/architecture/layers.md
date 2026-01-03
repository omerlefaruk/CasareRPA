# CasareRPA Architecture Layers

This document provides detailed documentation for each architectural layer in CasareRPA.

## Layer Overview

| Layer | Path | Dependencies | Purpose |
|-------|------|--------------|---------|
| Domain | `domain/` | None | Pure business logic |
| Application | `application/` | Domain | Use cases, orchestration |
| Infrastructure | `infrastructure/` | Domain, Application | External adapters |
| Presentation | `presentation/` | All layers | Qt UI |

## Domain Layer

**Path**: `src/casare_rpa/domain/`

The domain layer contains pure business logic with zero external dependencies. It is framework-agnostic and testable in isolation.

### Entities (`domain/entities/`)

Domain objects with unique identity.

| Entity | File | Purpose |
|--------|------|---------|
| `BaseNode` | `base_node.py` | Abstract base class for all automation nodes |
| `WorkflowSchema` | `workflow.py` | Workflow definition and metadata |
| `Variable` | `variable.py` | Variable definitions |
| `Subflow` | `subflow.py` | Reusable workflow blocks |
| `Project` | `project/project.py` | RPA project container |
| `Scenario` | `project/scenario.py` | Workflow scenario |

```python
from casare_rpa.domain.entities import BaseNode, Variable, Project, Subflow
```

### Aggregates (`domain/aggregates/`)

DDD aggregate roots that enforce consistency boundaries.

| Aggregate | File | Purpose |
|-----------|------|---------|
| `Workflow` | `workflow.py` | Workflow aggregate root |
| `WorkflowId` | `workflow.py` | Strongly-typed workflow ID |
| `WorkflowNode` | `workflow.py` | Node within workflow aggregate |
| `Position` | Value object from `value_objects/` | Node position |

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

# Create workflow
workflow = Workflow(id=WorkflowId.generate(), name="My Automation")

# Add node (raises NodeAdded event internally)
node_id = workflow.add_node(
    node_type="ClickElementNode",
    position=Position(x=100, y=200),
    config={"selector": "#submit-btn"},
)

# Connect nodes (raises NodeConnected event internally)
workflow.connect(
    source_node=start_node,
    source_port="exec_out",
    target_node=node_id,
    target_port="exec_in",
)

# Collect events after transaction
events = workflow.collect_events()
```

### Value Objects (`domain/value_objects/`)

Immutable types defined by their attributes, not identity.

| Type | File | Values/Purpose |
|------|------|----------------|
| `DataType` | `types.py` | STRING, INTEGER, FLOAT, BOOLEAN, LIST, DICT, ANY, EXEC, PAGE, ELEMENT |
| `NodeStatus` | `types.py` | IDLE, RUNNING, SUCCESS, ERROR, SKIPPED |
| `PortType` | `types.py` | INPUT, OUTPUT, EXEC_INPUT, EXEC_OUTPUT |
| `Port` | `types.py` | Port definition with name, type, data type |
| `LogEntry` | `log_entry.py` | Log message with level, timestamp |
| `Connection` | `types.py` | Connection between ports |
| `Position` | `position.py` | X/Y coordinates |
| `ExecutionResult` | `types.py` | Node execution result |

```python
from casare_rpa.domain.value_objects import (
    DataType,
    NodeStatus,
    PortType,
    Port,
    ExecutionResult,
)
```

### Events (`domain/events/`)

Typed domain events as frozen dataclasses.

| Module | Events |
|--------|--------|
| `node_events.py` | `NodeStarted`, `NodeCompleted`, `NodeFailed`, `NodeSkipped`, `NodeStatusChanged` |
| `workflow_events.py` | `WorkflowStarted`, `WorkflowCompleted`, `WorkflowFailed`, `WorkflowPaused`, `WorkflowResumed`, `WorkflowProgress`, `NodeAdded`, `NodeRemoved`, `NodeConnected`, `NodeDisconnected` |
| `system_events.py` | `VariableSet`, `BrowserPageReady`, `LogMessage`, `DebugBreakpointHit`, `ResourceAcquired`, `ResourceReleased` |
| `bus.py` | `EventBus`, `get_event_bus()` |

See [Events Reference](events.md) for complete documentation.

### Schemas (`domain/schemas/`)

Property and node schema definitions for declarative configuration.

| Type | File | Purpose |
|------|------|---------|
| `PropertyDef` | `property_schema.py` | Property definition with validation |
| `PropertyType` | `property_types.py` | STRING, INTEGER, BOOLEAN, CHOICE, FILE_PATH, SELECTOR, etc. |
| `NodeSchema` | `property_schema.py` | Complete node schema with properties |

```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000, min_value=0),
    PropertyDef("click_type", PropertyType.CHOICE, default="single",
                choices=["single", "double", "right"]),
)
@node(category="browser")
class ClickElementNode(BaseNode):
    pass
```

### Interfaces (`domain/interfaces/`)

Core protocols for dependency inversion.

| Interface | File | Purpose |
|-----------|------|---------|
| `INode` | `__init__.py` | Node execution interface |
| `IExecutionContext` | `__init__.py` | Execution context protocol |
| `IFolderStorage` | `__init__.py` | Folder storage protocol |
| `AbstractUnitOfWork` | `unit_of_work.py` | Unit of Work pattern interface |

```python
from casare_rpa.domain.interfaces import INode, IExecutionContext, AbstractUnitOfWork
```

---

## Application Layer

**Path**: `src/casare_rpa/application/`

The application layer contains use cases, queries, and cross-cutting services. It orchestrates domain logic but contains no business rules itself.

### Use Cases (`application/use_cases/`)

Command-side operations that modify state.

| Use Case | File | Purpose |
|----------|------|---------|
| `ExecuteWorkflowUseCase` | `execute_workflow.py` | Main workflow execution |
| `NodeExecutor` | `node_executor.py` | Execute individual nodes |
| `VariableResolver` | `variable_resolver.py` | Resolve variables in properties |
| `SubflowExecutor` | `subflow_executor.py` | Execute subflows |
| `ValidateWorkflowUseCase` | `validate_workflow.py` | Workflow validation |
| `CreateProjectUseCase` | `project_management.py` | Create new project |
| `GenerateWorkflowUseCase` | `generate_workflow.py` | AI workflow generation |

```python
from casare_rpa.application.use_cases import (
    ExecuteWorkflowUseCase,
    NodeExecutor,
    VariableResolver,
    ValidateWorkflowUseCase,
)
```

### Queries (`application/queries/`)

Query-side operations (CQRS read queries) that return DTOs.

| Query Service | Purpose |
|---------------|---------|
| `WorkflowQueryService` | Query workflows with filtering |
| `ExecutionQueryService` | Query execution logs |

```python
from casare_rpa.application.queries import (
    WorkflowQueryService,
    WorkflowListItemDTO,
    WorkflowFilter,
    ExecutionQueryService,
    ExecutionLogDTO,
)

# Read-optimized queries bypass domain model
query_service = WorkflowQueryService(storage_path)
workflows = await query_service.list_workflows(
    filter=WorkflowFilter(category="browser")
)
```

### Services (`application/services/`)

Cross-cutting application services.

| Service | File | Purpose |
|---------|------|---------|
| `ExecutionLifecycleManager` | `execution_lifecycle_manager.py` | Manage execution state |
| `BrowserRecordingService` | `browser_recording_service.py` | Record browser actions |
| `OrchestratorClient` | `orchestrator_client.py` | Connect to orchestrator |

```python
from casare_rpa.application.services import (
    ExecutionLifecycleManager,
    ExecutionState,
    ExecutionSession,
    OrchestratorClient,
)
```

### Dependency Injection (`application/dependency_injection/`)

DI container for managing dependencies.

```python
from casare_rpa.application.dependency_injection import (
    DIContainer,
    Lifecycle,
    Singleton,
    LazySingleton,
)
```

---

## Infrastructure Layer

**Path**: `src/casare_rpa/infrastructure/`

The infrastructure layer contains external adapters and framework integrations. It implements interfaces defined in the domain layer.

### Agent (`infrastructure/agent/`)

Robot agent for headless execution.

| Component | File | Purpose |
|-----------|------|---------|
| `RobotAgent` | `robot_agent.py` | Main agent class |
| `JobExecutor` | `job_executor.py` | Execute jobs from queue |
| `HeartbeatService` | `heartbeat_service.py` | Agent health monitoring |

```python
from casare_rpa.infrastructure import RobotAgent, RobotConfig
```

### Browser (`infrastructure/browser/`)

Playwright browser automation integration.

| Component | Purpose |
|-----------|---------|
| `PlaywrightManager` | Singleton browser lifecycle |
| `SelectorHealingChain` | Self-healing selectors |

```python
from casare_rpa.infrastructure.browser import (
    PlaywrightManager,
    get_playwright_singleton,
)
```

### HTTP (`infrastructure/http/`)

Resilient HTTP client with circuit breaker.

```python
from casare_rpa.infrastructure import (
    UnifiedHttpClient,
    get_unified_http_client,
)

# ALWAYS use UnifiedHttpClient, never raw httpx
async with get_unified_http_client() as client:
    response = await client.get("https://api.example.com/data")
```

### Persistence (`infrastructure/persistence/`)

File system repositories and Unit of Work.

| Component | File | Purpose |
|-----------|------|---------|
| `JsonUnitOfWork` | `unit_of_work.py` | Unit of Work for JSON storage |
| `ProjectStorage` | `project_storage.py` | Project persistence |
| `FolderStorage` | `folder_storage.py` | Folder-based storage |

```python
from casare_rpa.infrastructure.persistence import JsonUnitOfWork
from casare_rpa.domain.events import get_event_bus

async with JsonUnitOfWork(storage_path, get_event_bus()) as uow:
    workflow = await uow.workflows.get(workflow_id)
    workflow.add_node(node)
    await uow.commit()  # Persists and publishes domain events
```

### Execution (`infrastructure/execution/`)

Execution context and runtime.

| Component | Purpose |
|-----------|---------|
| `ExecutionContext` | Runtime context for node execution |

### Security (`infrastructure/security/`)

Authentication, authorization, and credential management.

| Component | Purpose |
|-----------|---------|
| `VaultClient` | Credential storage |
| `AuthorizationService` | RBAC |

### Resources (`infrastructure/resources/`)

External resource managers.

| Component | Purpose |
|-----------|---------|
| `LLMResourceManager` | AI/LLM API management |
| `GoogleAPIClient` | Google services integration |
| `TelegramClient` | Telegram messaging |

---

## Presentation Layer

**Path**: `src/casare_rpa/presentation/`

The presentation layer contains the Qt UI. It can depend on all other layers.

### Canvas (`presentation/canvas/`)

The main visual workflow designer.

| Directory | Purpose |
|-----------|---------|
| `controllers/` | MVC controllers |
| `coordinators/` | Signal coordination, event bridge |
| `visual_nodes/` | 405 visual node classes |
| `ui/` | Widgets, panels, theme |
| `graph/` | NodeGraphQt integration |
| `selectors/` | Element picker UI |

### Visual Nodes (`presentation/canvas/visual_nodes/`)

Visual representations of automation nodes.

| Category | Count | Examples |
|----------|-------|----------|
| browser | 23 | LaunchBrowser, ClickElement, TypeText |
| desktop_automation | 36 | LaunchApplication, ActivateWindow |
| control_flow | 16 | If, ForLoop, Switch, TryCatch |
| google | 79 | Gmail, Sheets, Drive, Calendar |
| system | 67 | Dialogs, Clipboard, Services |
| file_operations | 40 | ReadFile, WriteFile, CSV, JSON |

**Total: 405 visual nodes across 21 categories**

```python
from casare_rpa.presentation.canvas.visual_nodes import (
    VisualStartNode,
    VisualEndNode,
    VisualClickElementNode,
)
```

### Coordinators (`presentation/canvas/coordinators/`)

Event and signal coordination.

| Component | Purpose |
|-----------|---------|
| `SignalCoordinator` | Central signal hub |
| `QtDomainEventBridge` | Bridge domain events to Qt signals |

```python
from casare_rpa.presentation.canvas.coordinators import QtDomainEventBridge
from casare_rpa.domain.events import get_event_bus

# Bridge domain events to Qt
bridge = QtDomainEventBridge(get_event_bus())
bridge.node_started.connect(self._on_node_started)
bridge.node_completed.connect(self._on_node_completed)
bridge.workflow_progress.connect(self._on_progress)
```

### Theme (`presentation/canvas/theme.py`)

All UI colors must use theme constants (unified theme system):

```python
from casare_rpa.presentation.canvas.theme import THEME

# CORRECT
background = THEME.BACKGROUND_PRIMARY
text_color = THEME.TEXT_PRIMARY

# WRONG - Never hardcode colors
background = "#1a1a2e"  # NO!
```

---

## Nodes Package

**Path**: `src/casare_rpa/nodes/`

Contains 413+ automation nodes across 18 categories.

| Category | Path | Key Nodes |
|----------|------|-----------|
| browser | `browser/` | BrowserBaseNode, NavigationNodes, InteractionNodes |
| desktop | `desktop_nodes/` | FindElementNode, ClickElementNode, TypeTextNode |
| control_flow | `control_flow/` | IfNode, ForLoopNode, SwitchNode, TryCatchNode |
| http | `http/` | HttpRequestNode, DownloadFileNode |
| file | `file/` | ReadFileNode, WriteFileNode, CSVNode, JSONNode |
| email | `email/` | SendEmailNode, IMAPNode |
| google | `google/` | SheetsNode, DriveNode, GmailNode, CalendarNode |
| trigger | `trigger_nodes/` | ScheduleTriggerNode, WebhookTriggerNode |

```python
from casare_rpa.nodes import LaunchBrowserNode, ClickElementNode, TypeInputNode
from casare_rpa.nodes.control_flow import IfNode, ForLoopStartNode, BreakNode
```

---

## Design Principles

1. **Pure Domain Logic**: No external dependencies in domain layer
2. **Framework Agnostic**: Domain has no PySide6, Playwright, etc.
3. **Testable in Isolation**: All domain logic unit testable
4. **Dependency Inversion**: Infrastructure implements domain interfaces
5. **Typed Events**: Frozen dataclass events for communication
6. **Aggregate Boundaries**: Workflow is the consistency boundary

## Related Documentation

- [Overview](overview.md) - Architecture overview
- [Events](events.md) - Typed domain events reference
- [Aggregates](aggregates.md) - Workflow aggregate pattern
- [Diagrams](diagrams.md) - Architecture diagrams

