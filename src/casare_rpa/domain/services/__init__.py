"""
CasareRPA - Domain Services

Domain services contain business logic that doesn't naturally fit in entities or value objects.
"""

from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.services.project_context import ProjectContext
from casare_rpa.domain.services.variable_resolver import (
    VARIABLE_PATTERN,
    resolve_variables,
    resolve_dict_variables,
    extract_variable_names,
    has_variables,
)
from casare_rpa.domain.services.expression_evaluator import (
    ExpressionEvaluator,
    ExpressionError,
    get_expression_evaluator,
    evaluate_expression,
    has_expressions,
)
from casare_rpa.domain.services.headless_validator import (
    HeadlessWorkflowSandbox,
    WorkflowValidationResult,
    WorkflowValidationError,
)
from casare_rpa.domain.services.workflow_validator import (
    WorkflowValidator,
    ValidationResult as QtValidationResult,
    ValidationIssue as QtValidationIssue,
    validate_workflow_with_qt,
    get_valid_ports_for_node,
)
from casare_rpa.domain.validation import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    validate_workflow,
    validate_node,
    validate_connections,
    quick_validate,
    get_valid_node_types,
    _has_circular_dependency,
    _find_entry_points_and_reachable,
    _parse_connection,
    _is_exec_port,
    _is_exec_input_port,
)

__all__ = [
    "ExecutionOrchestrator",
    "ProjectContext",
    # Variable resolver
    "VARIABLE_PATTERN",
    "resolve_variables",
    "resolve_dict_variables",
    "extract_variable_names",
    "has_variables",
    # Expression evaluator (Power Automate style)
    "ExpressionEvaluator",
    "ExpressionError",
    "get_expression_evaluator",
    "evaluate_expression",
    "has_expressions",
    # Headless workflow validation
    "HeadlessWorkflowSandbox",
    "WorkflowValidationResult",
    "WorkflowValidationError",
    # Qt-based workflow validation
    "WorkflowValidator",
    "QtValidationResult",
    "QtValidationIssue",
    "validate_workflow_with_qt",
    "get_valid_ports_for_node",
    # Validation
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "validate_workflow",
    "validate_node",
    "validate_connections",
    "quick_validate",
    "get_valid_node_types",
    "_has_circular_dependency",
    "_find_entry_points_and_reachable",
    "_parse_connection",
    "_is_exec_port",
    "_is_exec_input_port",
]
