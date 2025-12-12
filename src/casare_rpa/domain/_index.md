# Domain Layer Index

Quick reference for domain layer components. Use for fast discovery.

Pure business logic with zero external dependencies. Framework-agnostic and testable in isolation.

## Directory Structure

| Directory | Purpose | Key Exports |
|-----------|---------|-------------|
| `entities/` | Domain entities with identity | BaseNode, WorkflowSchema, Variable, Subflow, Project, Scenario |
| `value_objects/` | Immutable types | DataType, NodeStatus, PortType, Port, LogEntry, Connection |
| `services/` | Domain services | ExecutionOrchestrator, ProjectContext, resolve_variables, WorkflowValidator |
| `schemas/` | Property/validation schemas | PropertyDef, NodeSchema, PropertyType, WorkflowAISchema |
| `protocols/` | Interface contracts | CredentialProviderProtocol, ExecutionContextProtocol |
| `interfaces/` | Core protocols | INode, IExecutionContext, IFolderStorage |
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
| `__init__.py` | Domain exports: executable_node, CredentialAwareMixin, protocols | ~64 |
| `decorators.py` | `@executable_node`, `@node_schema` decorators | ~145 |
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
| `interfaces/__init__.py` | INode, IExecutionContext interfaces | ~52 |

## Entry Points

```python
# Node decorators - auto-add exec ports and schema
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("url", PropertyType.STRING, default="", essential=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@executable_node
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
from casare_rpa.domain.interfaces import INode, IExecutionContext

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
```

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

The `@node_schema` decorator enables declarative property definitions:

```python
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
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
