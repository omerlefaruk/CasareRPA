# Domain Layer Index

Quick reference for domain layer components. Use for fast discovery.

Pure business logic with zero external dependencies. Framework-agnostic and testable in isolation.

## Directory Structure

| Directory | Purpose | Key Exports |
|-----------|---------|-------------|
| `aggregates/` | DDD Aggregate Roots | Workflow, WorkflowId, WorkflowNode, Position |
| `entities/` | Domain entities with identity | BaseNode, WorkflowSchema, Variable, Subflow, Project, Scenario |
| `events/` | Typed domain events | DomainEvent, NodeAdded, WorkflowStarted, etc. |
| `value_objects/` | Immutable types | DataType, NodeStatus, PortType, Port, LogEntry, Connection, Position |
| `services/` | Domain services | ExecutionOrchestrator, ProjectContext, resolve_variables, WorkflowValidator |
| `schemas/` | Property/validation schemas | PropertyDef, NodeSchema, PropertyType, WorkflowAISchema |
| `protocols/` | Interface contracts | CredentialProviderProtocol, ExecutionContextProtocol |
| `interfaces/` | Core protocols | INode, IExecutionContext, IFolderStorage, AbstractUnitOfWork |
| `ai/` | AI/LLM domain config | Prompt templates, AI configuration |
| `validation/` | Workflow validation | ValidationResult, ValidationIssue, validate_workflow |
| `errors/` | Error handling | ErrorCode, custom exceptions, error handlers |
| `orchestrator/` | Orchestrator domain | Robot, Job, Schedule entities and repositories |
| `ports/` | Port type interfaces | PortTypeInterfaces |
| `repositories/` | Repository interfaces | ProjectRepository interface |
| `workflow/` | Workflow utilities | Versioning utilities |

## Key Files

| File | Contains | Lines |
|------|----------|-------|
| `__init__.py` | Domain exports: node, CredentialAwareMixin, protocols | ~64 |
| `decorators.py` | `@node`, `@properties` decorators | ~145 |
| `credentials.py` | CredentialAwareMixin, credential property helpers | Variable |
| `port_type_system.py` | Port type compatibility and validation | Variable |
| `variable_resolver.py` | Variable pattern resolution utilities | Variable |
| `entities/__init__.py` | Entity exports: BaseNode, Variable, Project, Subflow | ~101 |
| `entities/base_node.py` | BaseNode abstract class - all nodes inherit from this | ~371 |
| `entities/workflow.py` | WorkflowSchema - workflow definition | Variable |
| `entities/subflow.py` | Subflow entity for reusable workflows | Variable |
| `entities/project/` | Project domain model (6 files) | Variable |
| `value_objects/__init__.py` | Type exports: DataType, NodeStatus, Port, LogEntry | ~87 |
| `value_objects/types.py` | Core type definitions and enums | Variable |
| `services/__init__.py` | Service exports: ExecutionOrchestrator, validators | ~78 |
| `schemas/__init__.py` | Schema exports: PropertyDef, NodeSchema, AI schemas | ~50 |
| `schemas/property_schema.py` | PropertyDef, NodeSchema for declarative config | ~295 |
| `schemas/property_types.py` | PropertyType enum | Variable |
| `protocols/__init__.py` | Protocol exports for dependency inversion | ~25 |
| `interfaces/__init__.py` | INode, IExecutionContext, AbstractUnitOfWork interfaces | ~55 |
| `interfaces/unit_of_work.py` | AbstractUnitOfWork - Unit of Work pattern interface | ~105 |

## Entry Points

```python
# Node decorators - auto-add exec ports and schema
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("url", PropertyType.STRING, default="", essential=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node
class MyNode(BaseNode):
    pass

# Base node class
from casare_rpa.domain.entities import BaseNode

# Value objects and types
from casare_rpa.domain.value_objects import (
    DataType,
    NodeStatus,
    PortType,
    Port,
    ExecutionResult,
)

# Credential-aware nodes
from casare_rpa.domain import (
    CredentialAwareMixin,
    resolve_node_credential,
    API_KEY_PROP,
    USERNAME_PROP,
    PASSWORD_PROP,
)

# Interfaces for dependency inversion
from casare_rpa.domain.interfaces import INode, IExecutionContext, AbstractUnitOfWork

# Domain services
from casare_rpa.domain.services import (
    resolve_variables,
    validate_workflow,
    ValidationResult,
)

# Project entities
from casare_rpa.domain.entities import (
    Project,
    Scenario,
    Variable,
    Subflow,
)

# Workflow Aggregate (DDD 2025 pattern)
from casare_rpa.domain.aggregates import (
    Workflow,
    WorkflowId,
    WorkflowNode,
    Position,
    NodeAdded,
    NodeRemoved,
    NodeConnected,
)
```

## Aggregate Pattern (DDD 2025)

The `Workflow` aggregate root enforces consistency boundaries:

```python
from casare_rpa.domain.aggregates import Workflow, WorkflowId, Position

# Create workflow through aggregate root
workflow = Workflow(id=WorkflowId.generate(), name="My Automation")

# All modifications go through aggregate
node_id = workflow.add_node(
    node_type="ClickElementNode",
    position=Position(x=100, y=200),
    config={"selector": "#button"},
)

# Connect nodes within aggregate boundary
workflow.connect(
    source_node=start_node,
    source_port="exec_out",
    target_node=node_id,
    target_port="exec_in",
)

# Collect domain events after transaction
events = workflow.collect_events()
for event in events:
    event_bus.publish(event)  # NodeAdded, NodeConnected events
```

Key principles:
- **Aggregate Root**: Only `Workflow` is accessed from outside
- **Consistency Boundary**: All modifications validated within aggregate
- **Event Collection**: Domain events raised but not published until transaction complete
- **Reference by ID**: Other aggregates referenced by ID only, never by object

## Entity Hierarchy

```
entities/
    +-- base_node.py      # BaseNode - abstract base for all nodes
    +-- workflow.py       # WorkflowSchema - workflow definition
    +-- variable.py       # Variable, VariableDefinition
    +-- subflow.py        # Subflow - reusable workflow blocks
    +-- execution_state.py # ExecutionState, ExecutionContext
    +-- node_connection.py # NodeConnection
    +-- workflow_metadata.py # WorkflowMetadata
    +-- tenant.py         # Tenant, TenantSettings
    +-- trigger_config.py # TriggerConfig
    +-- project/          # Project subdomain
        +-- project.py    # Project entity
        +-- scenario.py   # Scenario entity
        +-- variables.py  # VariablesFile
        +-- credentials.py # CredentialBinding
        +-- settings.py   # ProjectSettings
        +-- environment.py # Environment config
```

## Value Object Types

| Type | Purpose | Values |
|------|---------|--------|
| `DataType` | Port data typing | STRING, INTEGER, FLOAT, BOOLEAN, LIST, DICT, ANY, EXEC, PAGE, ELEMENT |
| `NodeStatus` | Execution state | IDLE, RUNNING, SUCCESS, ERROR, SKIPPED |
| `PortType` | Port direction | INPUT, OUTPUT, EXEC_INPUT, EXEC_OUTPUT |
| `PropertyType` | Schema property types | STRING, INTEGER, FLOAT, BOOLEAN, CHOICE, FILE_PATH, SELECTOR, etc. |
| `TriggerType` | Trigger categories | SCHEDULE, WEBHOOK, FILE_WATCH, EMAIL, etc. |
| `ErrorCode` | Error classification | VALIDATION_ERROR, EXECUTION_ERROR, TIMEOUT, etc. |

## Schema System

The `@properties` decorator enables declarative property definitions:

```python
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@properties(
    PropertyDef("selector", PropertyType.SELECTOR, essential=True,
                placeholder="Pick element..."),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000,
                min_value=0, max_value=300000),
    PropertyDef("click_type", PropertyType.CHOICE, default="single",
                choices=["single", "double", "right"]),
)
```

Benefits:
- Auto-generates default config
- Validates config on initialization
- Enables auto-widget generation in visual nodes
- `essential=True` keeps widget visible when node is collapsed

## Design Principles

1. **Pure Domain Logic**: No external dependencies (DB, UI, network)
2. **Framework Agnostic**: No PySide6, Playwright, etc. in domain layer
3. **Testable in Isolation**: All logic can be unit tested without infrastructure
4. **Dependency Inversion**: Infrastructure implements domain protocols

## Related Indexes

- [nodes/_index.md](../../nodes/_index.md) - Node implementations (uses domain BaseNode)
- [visual_nodes/_index.md](../../presentation/canvas/visual_nodes/_index.md) - Visual node layer
- [infrastructure/_index.md](../../infrastructure/_index.md) - Infrastructure implementations
- [application/_index.md](../../application/_index.md) - Application use cases
