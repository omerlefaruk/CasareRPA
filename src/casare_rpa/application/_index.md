# Application Index

Quick reference for application layer. Use cases, services, and orchestration.

## Directory Structure

| Directory | Description | Key Exports |
|-----------|-------------|-------------|
| `use_cases/` | Core business use cases | ExecuteWorkflowUseCase, NodeExecutor |
| `services/` | Cross-cutting services | ExecutionLifecycleManager, BrowserRecordingService |
| `dependency_injection/` | DI container | DIContainer, Singleton |
| `orchestrator/` | Job execution use cases | SubmitJobUseCase, ExecuteLocalUseCase |
| `execution/` | Trigger execution | CanvasTriggerRunner |
| `workflow/` | Import/export, recent files | WorkflowImporter, RecentFilesManager |
| `scheduling/` | (Deprecated - use trigger nodes) | - |

## Key Files

| File | Contains |
|------|----------|
| `__init__.py` | Top-level exports (4 items) |
| `use_cases/__init__.py` | 32 exports |
| `use_cases/execute_workflow.py` | Main workflow executor |
| `use_cases/node_executor.py` | Node execution engine |
| `use_cases/variable_resolver.py` | Variable interpolation |
| `use_cases/generate_workflow.py` | AI workflow generation |
| `use_cases/subflow_executor.py` | Subflow execution |
| `services/__init__.py` | 9 exports |
| `dependency_injection/__init__.py` | 9 exports |

## Entry Points

```python
# Workflow Execution
from casare_rpa.application import (
    ExecuteWorkflowUseCase,
    NodeExecutor,
    VariableResolver,
)

# Or from use_cases directly
from casare_rpa.application.use_cases import (
    ExecuteWorkflowUseCase,
    ExecutionStateManager,
    ExecutionSettings,
    NodeExecutor,
    NodeExecutorWithTryCatch,
    NodeExecutionResult,
    VariableResolver,
    TryCatchErrorHandler,
)

# Workflow Validation
from casare_rpa.application.use_cases import (
    ValidateWorkflowUseCase,
    ValidationResult,
    ValidationIssue,
)

# Project Management
from casare_rpa.application.use_cases import (
    CreateProjectUseCase,
    LoadProjectUseCase,
    SaveProjectUseCase,
    ListProjectsUseCase,
    DeleteProjectUseCase,
    ProjectResult,
)

# Scenario Management
from casare_rpa.application.use_cases import (
    CreateScenarioUseCase,
    LoadScenarioUseCase,
    SaveScenarioUseCase,
    DeleteScenarioUseCase,
    ListScenariosUseCase,
    ScenarioResult,
)

# Subflow Execution
from casare_rpa.application.use_cases import (
    Subflow,
    SubflowExecutor,
    SubflowInputDefinition,
    SubflowOutputDefinition,
    SubflowExecutionResult,
)

# AI Workflow Generation
from casare_rpa.application.use_cases import (
    GenerateWorkflowUseCase,
    WorkflowGenerationError,
    generate_workflow_from_text,
)

# Services
from casare_rpa.application.services import (
    ExecutionLifecycleManager,
    ExecutionState,
    ExecutionSession,
    OrchestratorClient,
    WorkflowSubmissionResult,
    BrowserRecordingService,
    get_browser_recording_service,
)

# Dependency Injection
from casare_rpa.application.dependency_injection import (
    DIContainer,
    Lifecycle,
    Singleton,
    LazySingleton,
    create_singleton_accessor,
)

# Orchestrator Use Cases
from casare_rpa.application.orchestrator import (
    ExecuteJobUseCase,
    SubmitJobUseCase,
    ExecuteLocalUseCase,
    ExecutionResult,
    AssignRobotUseCase,
    ListRobotsUseCase,
)

# Trigger Execution
from casare_rpa.application.execution import (
    CanvasTriggerRunner,
    TriggerEventHandler,
)

# Workflow Import/Export
from casare_rpa.application.workflow import (
    WorkflowImporter,
    RecentFilesManager,
)
```

## Use Cases Summary

### Workflow Execution

| Use Case | Description |
|----------|-------------|
| `ExecuteWorkflowUseCase` | Main workflow execution orchestrator |
| `ExecutionStateManager` | Manage execution state and pause/resume |
| `NodeExecutor` | Execute individual nodes |
| `NodeExecutorWithTryCatch` | Node execution with error recovery |
| `VariableResolver` | Resolve variables in node properties |
| `SubflowExecutor` | Execute subflow nodes |

### Project Management

| Use Case | Description |
|----------|-------------|
| `CreateProjectUseCase` | Create new RPA project |
| `LoadProjectUseCase` | Load existing project |
| `SaveProjectUseCase` | Save project to disk |
| `DeleteProjectUseCase` | Delete project |
| `ListProjectsUseCase` | List all projects |

### Scenario Management

| Use Case | Description |
|----------|-------------|
| `CreateScenarioUseCase` | Create workflow scenario |
| `LoadScenarioUseCase` | Load scenario JSON |
| `SaveScenarioUseCase` | Save scenario to disk |
| `DeleteScenarioUseCase` | Delete scenario |
| `ListScenariosUseCase` | List project scenarios |

### Orchestrator

| Use Case | Description |
|----------|-------------|
| `SubmitJobUseCase` | Submit job to queue |
| `ExecuteJobUseCase` | Execute job from queue |
| `ExecuteLocalUseCase` | Local execution (no orchestrator) |
| `AssignRobotUseCase` | Assign robot to workflow |
| `ListRobotsUseCase` | List available robots |

## Export Counts

| Module | Exports |
|--------|---------|
| `__init__.py` | 4 |
| `use_cases/__init__.py` | 29 |
| `services/__init__.py` | 9 |
| `dependency_injection/__init__.py` | 9 |
| `orchestrator/__init__.py` | 6 |
| `execution/__init__.py` | 4 |
| `workflow/__init__.py` | 2 |

## Key Patterns

- **Use Cases**: Single-responsibility operations
- **Services**: Cross-cutting concerns (lifecycle, recording)
- **DI Container**: Thread-safe dependency management
- **Result Types**: Explicit success/failure returns

## Related Indexes

- `infrastructure/_index.md` - External adapters
- `domain/_index.md` - Domain entities
- `nodes/_index.md` - Node implementations
- `presentation/canvas/_index.md` - UI layer
