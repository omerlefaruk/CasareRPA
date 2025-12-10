"""
CasareRPA - Application Layer

Use cases, orchestration services, and application-specific business rules.

Entry Points:
    - ExecuteWorkflowUseCase: Main workflow execution logic
    - WorkflowMigrationUseCase: Workflow version migration logic

Key Patterns:
    - Use Cases: Single-responsibility operations
    - Services: Cross-cutting concerns
"""

from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.application.use_cases.workflow_migration import WorkflowMigrationUseCase
from casare_rpa.application.use_cases.node_executor import NodeExecutor
from casare_rpa.application.use_cases.variable_resolver import VariableResolver

__all__ = [
    "ExecuteWorkflowUseCase",
    "WorkflowMigrationUseCase",
    "NodeExecutor",
    "VariableResolver",
]
