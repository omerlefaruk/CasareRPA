"""
CasareRPA - Domain Services

Domain services contain business logic that doesn't naturally fit in entities or value objects.
"""

from .execution_orchestrator import ExecutionOrchestrator
from .project_context import ProjectContext
from .variable_resolver import (
    VARIABLE_PATTERN,
    resolve_variables,
    resolve_dict_variables,
    extract_variable_names,
    has_variables,
)
from ..validation import (
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
