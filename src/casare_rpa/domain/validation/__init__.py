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
# Rules (helper functions for graph analysis)
from casare_rpa.domain.validation.rules import (
    find_entry_points_and_reachable,
    has_circular_dependency,
    is_exec_input_port,
    is_exec_port,
    # Public API
    parse_connection,
)

# Schemas (constants and type mappings)
from casare_rpa.domain.validation.schemas import (
    CONNECTION_REQUIRED_FIELDS,
    DATA_TYPE_COMPATIBILITY,
    NODE_REQUIRED_FIELDS,
    VALID_NODE_TYPES,
    get_valid_node_types,
)
from casare_rpa.domain.validation.types import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)

# Validators (main validation functions)
from casare_rpa.domain.validation.validators import (
    quick_validate,
    validate_connections,
    validate_node,
    validate_workflow,
)
from casare_rpa.domain.validation.workflow_json import (
    WorkflowValidationError,
    validate_workflow_json,
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
    "validate_workflow_json",
    "WorkflowValidationError",
    # Rules (public API)
    "parse_connection",
    "is_exec_port",
    "is_exec_input_port",
    "has_circular_dependency",
    "find_entry_points_and_reachable",
]
