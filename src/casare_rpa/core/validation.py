"""
CasareRPA - Workflow Validation Module

Provides comprehensive validation for workflow JSON files including:
- Schema validation for structure integrity
- Node validation for required fields and types
- Connection validation for port compatibility
- Semantic validation for workflow logic
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from loguru import logger

from .types import DataType, ErrorCode, SCHEMA_VERSION


class ValidationSeverity(Enum):
    """Severity level of validation issues."""

    ERROR = auto()    # Prevents workflow execution
    WARNING = auto()  # May cause issues, but execution can proceed
    INFO = auto()     # Informational message


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: ValidationSeverity
    code: str
    message: str
    location: Optional[str] = None  # e.g., "node:abc123", "connection:0"
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "severity": self.severity.name,
            "code": self.code,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return len(self.warnings)

    def add_error(
        self,
        code: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add an error-level issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
        ))
        self.is_valid = False

    def add_warning(
        self,
        code: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a warning-level issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code=code,
            message=message,
            location=location,
            suggestion=suggestion,
        ))

    def add_info(
        self,
        code: str,
        message: str,
        location: Optional[str] = None,
    ) -> None:
        """Add an info-level issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            code=code,
            message=message,
            location=location,
        ))

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        if not other.is_valid:
            self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        if self.is_valid and not self.issues:
            return "Validation passed with no issues."

        lines = []
        if not self.is_valid:
            lines.append(f"Validation FAILED: {self.error_count} error(s), {self.warning_count} warning(s)")
        else:
            lines.append(f"Validation passed with {self.warning_count} warning(s)")

        for issue in self.issues:
            prefix = {"ERROR": "E", "WARNING": "W", "INFO": "I"}[issue.severity.name]
            loc = f" [{issue.location}]" if issue.location else ""
            lines.append(f"  [{prefix}] {issue.code}{loc}: {issue.message}")
            if issue.suggestion:
                lines.append(f"       Suggestion: {issue.suggestion}")

        return "\n".join(lines)


# ============================================================================
# Schema Definitions
# ============================================================================

# Valid node types (matches NODE_TYPE_MAP in workflow_loader.py)
# VALID_NODE_TYPES is dynamically generated from NODE_TYPE_MAP to stay in sync
# This avoids manual maintenance of a hardcoded list
def _get_valid_node_types() -> Set[str]:
    """
    Dynamically get valid node types from NODE_TYPE_MAP.

    This ensures VALID_NODE_TYPES always stays in sync with the actual
    available node types in the system.
    """
    try:
        from ..utils.workflow_loader import NODE_TYPE_MAP
        return set(NODE_TYPE_MAP.keys())
    except ImportError:
        # Fallback to a minimal set if workflow_loader isn't available
        logger.warning("Could not import NODE_TYPE_MAP, using minimal node set")
        return {
            "StartNode", "EndNode", "IfNode", "ForLoopNode", "WhileLoopNode",
            "SetVariableNode", "GetVariableNode", "LogNode", "CommentNode",
        }

# Lazily evaluated to avoid circular imports
_valid_node_types_cache: Optional[Set[str]] = None

def get_valid_node_types() -> Set[str]:
    """Get the set of valid node types."""
    global _valid_node_types_cache
    if _valid_node_types_cache is None:
        _valid_node_types_cache = _get_valid_node_types()
    return _valid_node_types_cache

# Legacy alias for backwards compatibility (will be evaluated lazily when accessed)
VALID_NODE_TYPES: Set[str] = set()  # Placeholder, use get_valid_node_types() instead

# Required fields for node data
NODE_REQUIRED_FIELDS: Set[str] = {"node_id", "node_type"}

# Required fields for connection data
CONNECTION_REQUIRED_FIELDS: Set[str] = {
    "source_node", "source_port", "target_node", "target_port"
}

# Data type compatibility matrix (source -> compatible targets)
DATA_TYPE_COMPATIBILITY: Dict[str, Set[str]] = {
    "ANY": {"STRING", "INTEGER", "FLOAT", "BOOLEAN", "LIST", "DICT", "ANY",
            "ELEMENT", "PAGE", "BROWSER"},
    "STRING": {"STRING", "ANY"},
    "INTEGER": {"INTEGER", "FLOAT", "STRING", "ANY"},
    "FLOAT": {"FLOAT", "STRING", "ANY"},
    "BOOLEAN": {"BOOLEAN", "STRING", "ANY"},
    "LIST": {"LIST", "ANY"},
    "DICT": {"DICT", "ANY"},
    "ELEMENT": {"ELEMENT", "ANY"},
    "PAGE": {"PAGE", "ANY"},
    "BROWSER": {"BROWSER", "ANY"},
}


# ============================================================================
# Validation Functions
# ============================================================================

def validate_workflow(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a complete workflow data structure.

    Args:
        data: Serialized workflow dictionary

    Returns:
        ValidationResult with all issues found
    """
    result = ValidationResult()

    # Check top-level structure
    _validate_structure(data, result)
    if not result.is_valid:
        return result  # Can't proceed without basic structure

    # Validate metadata
    _validate_metadata(data.get("metadata", {}), result)

    # Validate nodes
    nodes = data.get("nodes", {})
    node_ids = set(nodes.keys())
    for node_id, node_data in nodes.items():
        _validate_node(node_id, node_data, result)

    # Validate connections
    connections = data.get("connections", [])
    _validate_connections(connections, node_ids, result)

    # Validate workflow-level semantics
    _validate_workflow_semantics(data, result)

    return result


def validate_node(node_id: str, node_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a single node's data structure.

    Args:
        node_id: Node identifier
        node_data: Node data dictionary

    Returns:
        ValidationResult for this node
    """
    result = ValidationResult()
    _validate_node(node_id, node_data, result)
    return result


def validate_connections(
    connections: List[Dict[str, str]],
    node_ids: Set[str],
) -> ValidationResult:
    """
    Validate workflow connections.

    Args:
        connections: List of connection dictionaries
        node_ids: Set of valid node IDs

    Returns:
        ValidationResult for connections
    """
    result = ValidationResult()
    _validate_connections(connections, node_ids, result)
    return result


# ============================================================================
# Internal Validation Helpers
# ============================================================================

def _validate_structure(data: Dict[str, Any], result: ValidationResult) -> None:
    """Validate top-level workflow structure."""

    # Must be a dictionary
    if not isinstance(data, dict):
        result.add_error(
            "INVALID_TYPE",
            "Workflow data must be a dictionary",
            suggestion="Ensure the workflow file contains valid JSON object",
        )
        return

    # Check for required top-level keys
    required_keys = {"nodes"}
    missing_keys = required_keys - set(data.keys())

    if missing_keys:
        result.add_error(
            "MISSING_REQUIRED_KEY",
            f"Missing required keys: {', '.join(missing_keys)}",
            suggestion="Add the missing keys to the workflow file",
        )

    # Validate types of top-level values
    if "nodes" in data and not isinstance(data["nodes"], dict):
        result.add_error(
            "INVALID_TYPE",
            "'nodes' must be a dictionary",
            location="nodes",
        )

    if "connections" in data and not isinstance(data["connections"], list):
        result.add_error(
            "INVALID_TYPE",
            "'connections' must be a list",
            location="connections",
        )

    if "metadata" in data and not isinstance(data["metadata"], dict):
        result.add_error(
            "INVALID_TYPE",
            "'metadata' must be a dictionary",
            location="metadata",
        )


def _validate_metadata(metadata: Dict[str, Any], result: ValidationResult) -> None:
    """Validate workflow metadata."""

    # Check schema version compatibility
    schema_version = metadata.get("schema_version", SCHEMA_VERSION)
    if schema_version != SCHEMA_VERSION:
        result.add_warning(
            "SCHEMA_VERSION_MISMATCH",
            f"Workflow schema version {schema_version} differs from current {SCHEMA_VERSION}",
            location="metadata.schema_version",
            suggestion="Consider re-saving the workflow to update schema version",
        )

    # Validate name
    name = metadata.get("name", "")
    if not name:
        result.add_warning(
            "MISSING_NAME",
            "Workflow has no name",
            location="metadata.name",
            suggestion="Add a descriptive name to the workflow",
        )
    elif len(name) > 100:
        result.add_warning(
            "NAME_TOO_LONG",
            f"Workflow name is too long ({len(name)} chars, max 100)",
            location="metadata.name",
        )


def _validate_node(
    node_id: str,
    node_data: Dict[str, Any],
    result: ValidationResult,
) -> None:
    """Validate a single node."""

    location = f"node:{node_id}"

    # Check required fields
    missing_fields = NODE_REQUIRED_FIELDS - set(node_data.keys())
    if missing_fields:
        result.add_error(
            "MISSING_REQUIRED_FIELD",
            f"Node missing required fields: {', '.join(missing_fields)}",
            location=location,
        )
        return

    # Validate node_id matches key
    if node_data.get("node_id") != node_id:
        result.add_error(
            "NODE_ID_MISMATCH",
            f"Node ID in data '{node_data.get('node_id')}' doesn't match key '{node_id}'",
            location=location,
            suggestion="Ensure node_id field matches the dictionary key",
        )

    # Validate node type
    node_type = node_data.get("node_type")
    if node_type not in get_valid_node_types():
        result.add_error(
            "UNKNOWN_NODE_TYPE",
            f"Unknown node type: {node_type}",
            location=location,
            suggestion="Check spelling or use a supported node type",
        )

    # Validate position if present
    position = node_data.get("position")
    if position is not None:
        if not isinstance(position, (list, tuple)) or len(position) != 2:
            result.add_warning(
                "INVALID_POSITION",
                "Node position should be [x, y] array",
                location=f"{location}.position",
            )
        elif not all(isinstance(p, (int, float)) for p in position):
            result.add_warning(
                "INVALID_POSITION",
                "Node position values must be numbers",
                location=f"{location}.position",
            )

    # Validate config if present
    config = node_data.get("config")
    if config is not None and not isinstance(config, dict):
        result.add_error(
            "INVALID_CONFIG",
            "Node config must be a dictionary",
            location=f"{location}.config",
        )


def _validate_connections(
    connections: List[Dict[str, str]],
    node_ids: Set[str],
    result: ValidationResult,
) -> None:
    """Validate all connections."""

    seen_connections: Set[Tuple[str, str, str, str]] = set()

    for idx, conn in enumerate(connections):
        location = f"connection:{idx}"

        # Check required fields
        missing_fields = CONNECTION_REQUIRED_FIELDS - set(conn.keys())
        if missing_fields:
            result.add_error(
                "MISSING_REQUIRED_FIELD",
                f"Connection missing required fields: {', '.join(missing_fields)}",
                location=location,
            )
            continue

        source_node = conn.get("source_node", "")
        source_port = conn.get("source_port", "")
        target_node = conn.get("target_node", "")
        target_port = conn.get("target_port", "")

        # Check for orphaned connections
        if source_node not in node_ids:
            result.add_error(
                "ORPHANED_CONNECTION",
                f"Connection references non-existent source node: {source_node}",
                location=location,
                suggestion="Remove the connection or add the missing node",
            )

        if target_node not in node_ids:
            result.add_error(
                "ORPHANED_CONNECTION",
                f"Connection references non-existent target node: {target_node}",
                location=location,
                suggestion="Remove the connection or add the missing node",
            )

        # Check for self-connections
        if source_node == target_node:
            result.add_error(
                "SELF_CONNECTION",
                f"Node cannot connect to itself: {source_node}",
                location=location,
            )

        # Check for duplicate connections
        conn_tuple = (source_node, source_port, target_node, target_port)
        if conn_tuple in seen_connections:
            result.add_warning(
                "DUPLICATE_CONNECTION",
                f"Duplicate connection: {source_node}.{source_port} -> {target_node}.{target_port}",
                location=location,
                suggestion="Remove the duplicate connection",
            )
        seen_connections.add(conn_tuple)


def _validate_workflow_semantics(
    data: Dict[str, Any],
    result: ValidationResult,
) -> None:
    """Validate workflow-level semantics."""

    nodes = data.get("nodes", {})
    connections = data.get("connections", [])

    # Check for empty workflow
    if not nodes:
        result.add_error(
            "EMPTY_WORKFLOW",
            "Workflow has no nodes",
            suggestion="Add at least a Start and End node",
        )
        return

    # Check for Start node
    start_nodes = [
        nid for nid, n in nodes.items()
        if n.get("node_type") == "StartNode"
    ]

    if not start_nodes:
        result.add_warning(
            "NO_START_NODE",
            "Workflow has no StartNode (one will be auto-created)",
            suggestion="Add a StartNode for explicit workflow entry point",
        )
    elif len(start_nodes) > 1:
        result.add_error(
            "MULTIPLE_START_NODES",
            f"Workflow has multiple StartNodes: {', '.join(start_nodes)}",
            suggestion="Remove extra StartNodes, only one is allowed",
        )

    # Check for End node
    end_nodes = [
        nid for nid, n in nodes.items()
        if n.get("node_type") == "EndNode"
    ]

    if not end_nodes:
        result.add_warning(
            "NO_END_NODE",
            "Workflow has no EndNode",
            suggestion="Add an EndNode to mark workflow completion",
        )

    # Check for circular dependencies
    if _has_circular_dependency(nodes, connections):
        result.add_error(
            "CIRCULAR_DEPENDENCY",
            "Workflow contains circular execution flow",
            suggestion="Review and break the circular connection chain",
        )

    # Check for unreachable nodes
    reachable = _find_reachable_nodes(nodes, connections)
    all_nodes = set(nodes.keys())
    unreachable = all_nodes - reachable

    if unreachable:
        result.add_warning(
            "UNREACHABLE_NODES",
            f"Some nodes are not reachable from Start: {', '.join(list(unreachable)[:5])}{'...' if len(unreachable) > 5 else ''}",
            suggestion="Connect these nodes to the workflow or remove them",
        )


def _has_circular_dependency(
    nodes: Dict[str, Any],
    connections: List[Dict[str, str]],
) -> bool:
    """Check for circular dependencies using DFS."""

    # Build adjacency list (only exec connections for flow)
    graph: Dict[str, List[str]] = {node_id: [] for node_id in nodes}

    for conn in connections:
        source = conn.get("source_node", "")
        target = conn.get("target_node", "")
        source_port = conn.get("source_port", "")

        # Only consider execution flow connections
        if source in graph and "exec" in source_port:
            graph[source].append(target)

    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.discard(node)
        return False

    for node_id in nodes:
        if node_id not in visited:
            if has_cycle(node_id):
                return True

    return False


def _find_reachable_nodes(
    nodes: Dict[str, Any],
    connections: List[Dict[str, str]],
) -> Set[str]:
    """Find all nodes reachable from Start nodes."""

    # Build adjacency list
    graph: Dict[str, List[str]] = {node_id: [] for node_id in nodes}

    for conn in connections:
        source = conn.get("source_node", "")
        target = conn.get("target_node", "")
        if source in graph:
            graph[source].append(target)

    # Find start nodes
    start_nodes = [
        nid for nid, n in nodes.items()
        if n.get("node_type") == "StartNode"
    ]

    # If no start node, consider all nodes with no incoming exec connections as entry points
    if not start_nodes:
        nodes_with_incoming: Set[str] = set()
        for conn in connections:
            if conn.get("target_port") == "exec_in":
                nodes_with_incoming.add(conn.get("target_node", ""))

        start_nodes = [nid for nid in nodes if nid not in nodes_with_incoming]

    # BFS from start nodes
    reachable: Set[str] = set()
    queue = list(start_nodes)

    while queue:
        current = queue.pop(0)
        if current in reachable:
            continue
        reachable.add(current)

        for neighbor in graph.get(current, []):
            if neighbor not in reachable:
                queue.append(neighbor)

    return reachable


# ============================================================================
# Quick Validation Helper
# ============================================================================

def quick_validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Quick validation returning simple tuple for backward compatibility.

    Args:
        data: Workflow data to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    result = validate_workflow(data)
    error_messages = [
        f"{issue.code}: {issue.message}"
        for issue in result.errors
    ]
    return result.is_valid, error_messages
