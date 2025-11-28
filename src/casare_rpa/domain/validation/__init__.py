"""
CasareRPA - Domain Workflow Validation Package

Provides comprehensive validation for workflow JSON files including:
- Schema validation for structure integrity
- Node validation for required fields and types
- Connection validation for port compatibility
- Semantic validation for workflow logic

This is the canonical location for validation components (v3.0).

Package Structure:
- types.py: ValidationResult, ValidationIssue, ValidationSeverity
- schemas.py: Schema definitions and constants (NODE_REQUIRED_FIELDS, etc.)
- validators.py: Main validation functions (validate_workflow, etc.)
- rules.py: Graph analysis and connection parsing helpers
"""

# Types (enums and dataclasses)
from .types import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
)

# Schemas (constants and type mappings)
from .schemas import (
    NODE_REQUIRED_FIELDS,
    CONNECTION_REQUIRED_FIELDS,
    DATA_TYPE_COMPATIBILITY,
    VALID_NODE_TYPES,
    get_valid_node_types,
)

# Validators (main validation functions)
from .validators import (
    validate_workflow,
    validate_node,
    validate_connections,
    quick_validate,
)

# Rules (helper functions for graph analysis)
from .rules import (
    # Public API
    parse_connection,
    is_exec_port,
    is_exec_input_port,
    has_circular_dependency,
    find_entry_points_and_reachable,
    find_reachable_nodes,
    # Legacy aliases (with underscore) for backwards compatibility
    _parse_connection,
    _is_exec_port,
    _is_exec_input_port,
    _has_circular_dependency,
    _find_entry_points_and_reachable,
    _find_reachable_nodes,
    _is_exec_port_name,
)


__all__ = [
    # Types
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    # Schemas
    "NODE_REQUIRED_FIELDS",
    "CONNECTION_REQUIRED_FIELDS",
    "DATA_TYPE_COMPATIBILITY",
    "VALID_NODE_TYPES",
    "get_valid_node_types",
    # Validators
    "validate_workflow",
    "validate_node",
    "validate_connections",
    "quick_validate",
    # Rules (public API)
    "parse_connection",
    "is_exec_port",
    "is_exec_input_port",
    "has_circular_dependency",
    "find_entry_points_and_reachable",
    "find_reachable_nodes",
    # Legacy aliases
    "_parse_connection",
    "_is_exec_port",
    "_is_exec_input_port",
    "_has_circular_dependency",
    "_find_entry_points_and_reachable",
    "_find_reachable_nodes",
    "_is_exec_port_name",
]
