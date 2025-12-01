# CasareRPA - Clean Architecture Documentation

## Overview

CasareRPA follows **Clean Architecture** principles with clear separation of concerns across multiple layers. This document describes the architectural structure, layer responsibilities, dependency rules, and migration patterns.

**Version**: 3.1
**Last Updated**: 2025-12-01

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [Layer Structure](#layer-structure)
3. [Dependency Flow](#dependency-flow)
4. [Import Guidelines](#import-guidelines)
5. [Composition Patterns](#composition-patterns)
6. [Testing Strategy](#testing-strategy)
7. [Migration Timeline](#migration-timeline)
8. [Examples](#examples)

---

## Architecture Principles

CasareRPA architecture follows these core principles:

### 1. Separation of Concerns
- **Domain logic** is independent of infrastructure
- **Business rules** have no dependencies on frameworks or UI
- **External integrations** are isolated in the infrastructure layer

### 2. Dependency Rule
- Dependencies point **inward** only
- Inner layers know nothing about outer layers
- Domain layer has **zero external dependencies**

### 3. Testability
- Domain logic can be tested without infrastructure
- Infrastructure can be mocked/stubbed for testing
- UI components are thin wrappers over domain logic

### 4. Maintainability
- Changes to infrastructure don't affect domain
- Business rules are centralized and explicit
- Deprecation warnings guide migration

---

## Layer Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│                (Canvas UI, Visual Nodes)                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Application Layer                      │
│            (Use Cases, Orchestration)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Domain Layer                          │
│         (Entities, Value Objects, Services)              │
└─────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Infrastructure Layer                      │
│         (Resources, Persistence, External APIs)          │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
            External Systems
    (File System, Playwright, Database)
```

---

### Domain Layer (`domain/`)

**Purpose**: Core business logic, entities, and rules
**Dependencies**: None (pure Python)
**Location**: `src/casare_rpa/domain/`

#### Contents

**Entities** (`domain/entities/`):
- `workflow.py` - WorkflowSchema, VariableDefinition
- `workflow_metadata.py` - WorkflowMetadata
- `node_connection.py` - NodeConnection
- `execution_state.py` - ExecutionState
- `project.py` - Project, Scenario, ProjectVariable, etc.

**Value Objects** (`domain/value_objects/`):
- `types.py` - DataType enum
- `port.py` - Port, PortDirection, PortType
- `execution_result.py` - ExecutionResult, ExecutionStatus

**Domain Services** (`domain/services/`):
- `execution_orchestrator.py` - Workflow execution coordination
- `project_context.py` - Project-scoped variable resolution

#### Rules
- ✅ **DO**: Pure business logic only
- ✅ **DO**: Use only standard library + typing
- ❌ **DON'T**: Import from infrastructure, application, or UI layers
- ❌ **DON'T**: Use frameworks (PySide6, Playwright, etc.)

---

### Application Layer (`application/`)

**Purpose**: Use cases and application services
**Dependencies**: Domain layer only
**Location**: `src/casare_rpa/application/`

#### Contents

**Use Cases** (`application/use_cases/`):
- `execute_workflow.py` - ExecuteWorkflowUseCase

#### Rules
- ✅ **DO**: Orchestrate domain entities and services
- ✅ **DO**: Define application-specific workflows
- ❌ **DON'T**: Contain UI or infrastructure details
- ❌ **DON'T**: Directly interact with external systems

---

### Infrastructure Layer (`infrastructure/`)

**Purpose**: External integrations and technical concerns
**Dependencies**: Domain, Application
**Location**: `src/casare_rpa/infrastructure/`

#### Contents

**Resources** (`infrastructure/resources/`):
- `browser_resource_manager.py` - Playwright browser lifecycle

**Persistence** (`infrastructure/persistence/`):
- `project_storage.py` - File system I/O for projects

#### Rules
- ✅ **DO**: Handle all external system interactions
- ✅ **DO**: Implement repository patterns
- ✅ **DO**: Proper error handling with retries
- ❌ **DON'T**: Contain business logic

---

### Core Layer (`core/`) - **DEPRECATED**

**Purpose**: Legacy code being refactored
**Status**: Compatibility layer with deprecation warnings
**Timeline**: Remove in v3.0

**Migration Path**:
- `core/types.py` → `domain/value_objects/types.py` ✅
- `core/workflow_schema.py` → `domain/entities/workflow.py` ✅
- `core/execution_context.py` → Split into domain + infrastructure ✅
- `core/project_schema.py` → `domain/entities/project.py` ✅

All core imports now emit **DeprecationWarning** and redirect to the new locations.

---

## Dependency Flow

```
┌──────────────┐
│      UI      │────┐
└──────────────┘    │
                    ▼
┌──────────────┐  ┌─────────────┐
│ Application  │──│   Domain    │
└──────────────┘  └─────────────┘
       │                 ▲
       ▼                 │
┌──────────────┐         │
│Infrastructure│─────────┘
└──────────────┘
```

**Key Points**:
- UI depends on Application and Domain
- Application depends on Domain only
- Infrastructure depends on Domain (implements interfaces)
- **Domain depends on nothing** (core principle)

---

## Import Guidelines

### ✅ DO: Import from domain layer

```python
# Entities
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.project import Project, Scenario

# Value Objects
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.domain.value_objects.port import Port, PortDirection

# Services
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.services.project_context import ProjectContext
```

### ✅ DO: Import from infrastructure

```python
from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager
)
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage
```

### ✅ DO: Import from application

```python
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
```

### ❌ DON'T: Import from core layer (deprecated)

```python
# DEPRECATED - emits DeprecationWarning
from casare_rpa.core.workflow_schema import WorkflowSchema  # Use domain.entities
from casare_rpa.core.types import DataType  # Use domain.value_objects
from casare_rpa.core.project_schema import Project  # Use domain.entities
```

---

## Composition Patterns

### Example: ExecutionContext

ExecutionContext uses composition to separate domain state from infrastructure resources:

```python
from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager
)

class ExecutionContext:
    """
    Execution context using composition pattern.

    Separates:
    - Domain state (ExecutionState)
    - Infrastructure resources (BrowserResourceManager)
    """

    def __init__(self):
        # Domain: Pure state management
        self._state = ExecutionState()

        # Infrastructure: Browser lifecycle
        self._resources = BrowserResourceManager()

    @property
    def state(self) -> ExecutionState:
        """Access domain state."""
        return self._state

    async def get_browser_page(self):
        """Access infrastructure resources."""
        return await self._resources.get_page()
```

### Example: ProjectContext

ProjectContext is a domain service that manages variable scoping:

```python
from casare_rpa.domain.services.project_context import ProjectContext
from casare_rpa.domain.entities.project import Project, Scenario

# Create context with proper variable scoping
context = ProjectContext(
    project=my_project,
    scenario=my_scenario,
    project_variables=project_vars,
    global_variables=global_vars
)

# Variable resolution follows: scenario > project > global
value = context.get_variable("api_url")
```

---

## Testing Strategy

### Domain Layer Testing
- **Pure unit tests** - No mocks needed
- **Fast execution** - No I/O operations
- **High coverage** - Core business logic

```python
def test_execution_state_transitions():
    """Test domain logic without infrastructure."""
    state = ExecutionState()

    state.set_variable("count", 0)
    assert state.get_variable("count") == 0

    state.set_variable("count", 5)
    assert state.get_variable("count") == 5
```

### Application Layer Testing
- **Use case tests** - Mock infrastructure
- **Workflow validation** - Test orchestration logic

```python
@pytest.fixture
def mock_resources():
    return Mock(spec=BrowserResourceManager)

def test_execute_workflow_use_case(mock_resources):
    """Test use case with mocked infrastructure."""
    use_case = ExecuteWorkflowUseCase(resources=mock_resources)
    result = use_case.execute(workflow_schema)

    assert result.success
    mock_resources.cleanup.assert_called_once()
```

### Infrastructure Layer Testing
- **Integration tests** - Real dependencies when possible
- **Error handling** - Test retry logic, timeouts
- **Resource cleanup** - Verify proper lifecycle

```python
@pytest.mark.asyncio
async def test_browser_resource_manager():
    """Test infrastructure with real Playwright."""
    manager = BrowserResourceManager()

    try:
        page = await manager.get_page()
        assert page is not None
        await page.goto("https://example.com")
    finally:
        await manager.cleanup()
```

---

## Migration Status

### v3.0 Migration - COMPLETE ✅

All phases of the clean architecture migration have been completed:

- ✅ Domain layer with entities, value objects, and services
- ✅ Application layer with use cases and orchestration
- ✅ Infrastructure layer with API, persistence, and security
- ✅ Presentation layer with Canvas and Orchestrator UI
- ✅ Legacy compatibility layers removed
- ✅ All imports updated to clean architecture paths
- ✅ 3,480+ tests with comprehensive coverage
- ✅ Orchestrator refactored to clean architecture

---

## Examples

### Creating a Workflow (Domain)

```python
from casare_rpa.domain.entities.workflow import WorkflowSchema, VariableDefinition
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection

# Create workflow metadata
metadata = WorkflowMetadata(
    name="Data Extraction Workflow",
    description="Extract data from web page",
    version="1.0.0"
)

# Create workflow schema
workflow = WorkflowSchema(
    metadata=metadata,
    nodes={},
    connections=[],
    variables={}
)
```

### Saving a Workflow (Infrastructure)

```python
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage
from casare_rpa.domain.entities.project import Project

# Load project
project = ProjectStorage.load_project(Path("/path/to/project"))

# Save workflow (infrastructure handles file I/O)
workflow_path = project.path / "workflows" / "my_workflow.json"
workflow_path.write_bytes(orjson.dumps(workflow.to_dict()))
```

### Executing a Workflow (Application)

```python
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager
)

# Create use case with infrastructure
resources = BrowserResourceManager()
use_case = ExecuteWorkflowUseCase(resources=resources)

# Execute workflow
try:
    result = await use_case.execute(workflow_schema)
    if result.success:
        print(f"Workflow completed: {result.output}")
    else:
        print(f"Workflow failed: {result.error}")
finally:
    await resources.cleanup()
```

---

## Conclusion

CasareRPA's clean architecture provides:

1. **Maintainability** - Changes are isolated to specific layers
2. **Testability** - Domain logic can be tested in isolation
3. **Flexibility** - Infrastructure can be swapped without affecting domain
4. **Clarity** - Clear separation of concerns and dependencies

For the project roadmap, see [ROADMAP_COMPLETE.md](ROADMAP_COMPLETE.md).

---

**Last Updated**: 2025-11-30
