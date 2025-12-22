"""
Workflow JSON validation (canonical).

Enforces structural and security constraints for persisted workflows.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from casare_rpa.domain.errors.exceptions import (
    WorkflowValidationError as BaseWorkflowValidationError,
)
from casare_rpa.domain.validation.validators import validate_workflow


MAX_NODES = 1000
MAX_CONNECTIONS = 5000
MAX_NODE_ID_LENGTH = 256
MAX_CONFIG_DEPTH = 10
MAX_STRING_LENGTH = 10000

_DANGEROUS_PATTERNS = (
    "__import__",
    "eval(",
    "exec(",
    "compile(",
    "os.system",
    "subprocess.",
    "open(",
    "pickle.",
    "marshal.",
    "__builtins__",
    "__globals__",
)


class WorkflowValidationError(BaseWorkflowValidationError):
    """Raised when workflow JSON fails validation."""

    def __init__(self, message: str, errors: Iterable[str] | None = None) -> None:
        super().__init__(message)
        self.errors = list(errors or [])


def _validate_string(value: Any, field_name: str, max_length: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise WorkflowValidationError(
            f"Field '{field_name}' must be a string, got {type(value).__name__}"
        )
    if len(value) > max_length:
        raise WorkflowValidationError(
            f"Field '{field_name}' exceeds maximum length of {max_length}"
        )
    return value


def _check_dangerous_patterns(value: str, path: str) -> None:
    value_lower = value.lower()
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in value_lower:
            raise WorkflowValidationError(
                f"Security error: dangerous pattern '{pattern}' found in {path}"
            )


def _validate_config_value(value: Any, path: str, depth: int = 0) -> Any:
    if depth > MAX_CONFIG_DEPTH:
        raise WorkflowValidationError(
            f"Config at '{path}' exceeds maximum nesting depth of {MAX_CONFIG_DEPTH}"
        )

    if value is None:
        return value

    if isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise WorkflowValidationError(
                f"Config value at '{path}' exceeds maximum length of {MAX_STRING_LENGTH}"
            )
        _check_dangerous_patterns(value, path)
        return value

    if isinstance(value, list):
        return [
            _validate_config_value(item, f"{path}[{i}]", depth + 1) for i, item in enumerate(value)
        ]

    if isinstance(value, dict):
        validated: Dict[str, Any] = {}
        for k, v in value.items():
            key = _validate_string(k, f"{path}.key", MAX_NODE_ID_LENGTH)
            validated[key] = _validate_config_value(v, f"{path}.{key}", depth + 1)
        return validated

    raise WorkflowValidationError(
        f"Unsupported config value type at '{path}': {type(value).__name__}"
    )


def validate_workflow_json(workflow_data: Dict[str, Any]) -> None:
    """
    Validate workflow JSON structure and security constraints.

    Raises WorkflowValidationError on failure.
    """
    if not isinstance(workflow_data, dict):
        raise WorkflowValidationError(
            f"Workflow must be a dictionary, got {type(workflow_data).__name__}"
        )

    metadata = workflow_data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise WorkflowValidationError("'metadata' must be a dictionary")

    _validate_string(metadata.get("name"), "metadata.name", 256)
    _validate_string(metadata.get("description"), "metadata.description", 10000)
    _validate_string(metadata.get("version"), "metadata.version", 50)

    nodes = workflow_data.get("nodes", {})
    if not isinstance(nodes, dict):
        raise WorkflowValidationError("'nodes' must be a dictionary")

    if len(nodes) > MAX_NODES:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum of {MAX_NODES} nodes (has {len(nodes)})"
        )

    for node_id, node_data in nodes.items():
        _validate_string(node_id, "node_id", MAX_NODE_ID_LENGTH)
        if not isinstance(node_data, dict):
            raise WorkflowValidationError(f"Node '{node_id}' must be a dictionary")

        node_type = node_data.get("node_type")
        _validate_string(node_type, f"nodes.{node_id}.node_type", 128)
        if not node_type:
            raise WorkflowValidationError(f"Node '{node_id}' is missing 'node_type'")

        config = node_data.get("config", {})
        if not isinstance(config, dict):
            raise WorkflowValidationError(f"Node '{node_id}' config must be a dictionary")
        _validate_config_value(config, f"nodes.{node_id}.config")

    connections = workflow_data.get("connections", [])
    if not isinstance(connections, list):
        raise WorkflowValidationError("'connections' must be a list")

    if len(connections) > MAX_CONNECTIONS:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum of {MAX_CONNECTIONS} connections (has {len(connections)})"
        )

    for i, conn in enumerate(connections):
        if not isinstance(conn, dict):
            raise WorkflowValidationError(f"Connection {i} must be a dictionary")

        _validate_string(
            conn.get("source_node"), f"connections[{i}].source_node", MAX_NODE_ID_LENGTH
        )
        _validate_string(
            conn.get("target_node"), f"connections[{i}].target_node", MAX_NODE_ID_LENGTH
        )
        _validate_string(conn.get("source_port", ""), f"connections[{i}].source_port", 128)
        _validate_string(conn.get("target_port", ""), f"connections[{i}].target_port", 128)

    validation_result = validate_workflow(workflow_data)
    if not validation_result.is_valid:
        errors: List[str] = [f"{issue.code}: {issue.message}" for issue in validation_result.errors]
        raise WorkflowValidationError("Workflow semantic validation failed", errors)

    workflow_data["__validated__"] = True
