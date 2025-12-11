"""
CasareRPA - Application Use Cases

Use cases coordinate domain logic and infrastructure to implement application features.
"""

from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.application.use_cases.execution_state_manager import (
    ExecutionSettings,
    ExecutionStateManager,
)
from casare_rpa.application.use_cases.node_executor import (
    NodeExecutor,
    NodeExecutorWithTryCatch,
    NodeExecutionResult,
)
from casare_rpa.application.use_cases.variable_resolver import (
    VariableResolver,
    TryCatchErrorHandler,
)
from casare_rpa.application.use_cases.validate_workflow import (
    ValidateWorkflowUseCase,
    ValidationResult,
    ValidationIssue,
)
from casare_rpa.application.use_cases.project_management import (
    # Result types
    ProjectResult,
    ScenarioResult,
    ProjectListResult,
    # Project use cases
    CreateProjectUseCase,
    LoadProjectUseCase,
    SaveProjectUseCase,
    ListProjectsUseCase,
    DeleteProjectUseCase,
    # Scenario use cases
    CreateScenarioUseCase,
    LoadScenarioUseCase,
    SaveScenarioUseCase,
    DeleteScenarioUseCase,
    ListScenariosUseCase,
)
from casare_rpa.application.use_cases.subflow_executor import (
    Subflow,
    SubflowInputDefinition,
    SubflowOutputDefinition,
    SubflowExecutionResult,
    SubflowExecutor,
)
from casare_rpa.application.use_cases.generate_workflow import (
    GenerateWorkflowUseCase,
    WorkflowGenerationError,
    generate_workflow_from_text,
)

__all__ = [
    # Workflow use cases
    "ExecuteWorkflowUseCase",
    "ExecutionSettings",
    "ExecutionStateManager",
    "NodeExecutor",
    "NodeExecutorWithTryCatch",
    "NodeExecutionResult",
    "VariableResolver",
    "TryCatchErrorHandler",
    "ValidateWorkflowUseCase",
    "ValidationResult",
    "ValidationIssue",
    # Subflow use cases
    "Subflow",
    "SubflowInputDefinition",
    "SubflowOutputDefinition",
    "SubflowExecutionResult",
    "SubflowExecutor",
    # Project result types
    "ProjectResult",
    "ScenarioResult",
    "ProjectListResult",
    # Project use cases
    "CreateProjectUseCase",
    "LoadProjectUseCase",
    "SaveProjectUseCase",
    "ListProjectsUseCase",
    "DeleteProjectUseCase",
    # Scenario use cases
    "CreateScenarioUseCase",
    "LoadScenarioUseCase",
    "SaveScenarioUseCase",
    "DeleteScenarioUseCase",
    "ListScenariosUseCase",
    # AI workflow generation
    "GenerateWorkflowUseCase",
    "WorkflowGenerationError",
    "generate_workflow_from_text",
]
