"""
CasareRPA - Application Use Cases

Use cases coordinate domain logic and infrastructure to implement application features.
"""

from .execute_workflow import ExecuteWorkflowUseCase, ExecutionSettings
from .validate_workflow import (
    ValidateWorkflowUseCase,
    ValidationResult,
    ValidationIssue,
)
from .project_management import (
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

__all__ = [
    # Workflow use cases
    "ExecuteWorkflowUseCase",
    "ExecutionSettings",
    "ValidateWorkflowUseCase",
    "ValidationResult",
    "ValidationIssue",
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
]
