"""
CasareRPA - Validators Module

Contains validation functions for workflows, nodes, and connections.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from casare_rpa.domain.value_objects.types import SCHEMA_VERSION

# PERFORMANCE: Incremental validation cache
# Stores validation results for unchanged nodes to avoid re-validation
_validation_cache: Dict[str, Tuple[str, "ValidationResult"]] = {}  # node_id -> (hash, result)

from casare_rpa.domain.validation.rules import (
    find_entry_points_and_reachable,
    has_circular_dependency,
)
from casare_rpa.domain.validation.schemas import (
    CONNECTION_REQUIRED_FIELDS,
    NODE_REQUIRED_FIELDS,
    get_valid_node_types,
)
from casare_rpa.domain.validation.types import ValidationResult


# ============================================================================
# Public Validation Functions
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


def quick_validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Quick validation returning simple tuple for backward compatibility.

    Args:
        data: Workflow data to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    result = validate_workflow(data)
    error_messages = [f"{issue.code}: {issue.message}" for issue in result.errors]
    return result.is_valid, error_messages


def validate_incremental(
    data: Dict[str, Any],
    changed_node_ids: Optional[Set[str]] = None,
) -> ValidationResult:
    """
    Incrementally validate a workflow, only re-validating changed nodes.

    PERFORMANCE: For large workflows, this can be 10-100x faster than
    full validation when only a few nodes have changed.

    Args:
        data: Serialized workflow dictionary
        changed_node_ids: Set of node IDs that have changed since last validation.
                         If None, validates all nodes (same as validate_workflow).

    Returns:
        ValidationResult with all issues found
    """
    import hashlib
    import orjson

    result = ValidationResult()

    # Check top-level structure (always required)
    _validate_structure(data, result)
    if not result.is_valid:
        return result

    # Validate metadata (always)
    _validate_metadata(data.get("metadata", {}), result)

    # Validate nodes with caching
    nodes = data.get("nodes", {})
    node_ids = set(nodes.keys())

    for node_id, node_data in nodes.items():
        # If no changed_node_ids specified, validate all
        if changed_node_ids is None or node_id in changed_node_ids:
            # Validate and cache
            node_result = ValidationResult()
            _validate_node(node_id, node_data, node_result)

            # Store in cache with hash
            try:
                node_hash = hashlib.md5(orjson.dumps(node_data)).hexdigest()
                _validation_cache[node_id] = (node_hash, node_result)
            except Exception:
                pass  # Skip caching if serialization fails

            # Merge into main result
            for error in node_result.errors:
                result.errors.append(error)
            for warning in node_result.warnings:
                result.warnings.append(warning)
        else:
            # Check cache for unchanged node
            try:
                node_hash = hashlib.md5(orjson.dumps(node_data)).hexdigest()
                if node_id in _validation_cache:
                    cached_hash, cached_result = _validation_cache[node_id]
                    if cached_hash == node_hash:
                        # Use cached result
                        for error in cached_result.errors:
                            result.errors.append(error)
                        for warning in cached_result.warnings:
                            result.warnings.append(warning)
                        continue
            except Exception:
                pass

            # Cache miss or hash mismatch - validate fully
            node_result = ValidationResult()
            _validate_node(node_id, node_data, node_result)
            for error in node_result.errors:
                result.errors.append(error)
            for warning in node_result.warnings:
                result.warnings.append(warning)

    # Connections must be validated fully (they depend on all nodes)
    connections = data.get("connections", [])
    _validate_connections(connections, node_ids, result)

    # Workflow-level semantics must be validated fully
    _validate_workflow_semantics(data, result)

    return result


def clear_validation_cache() -> None:
    """Clear the incremental validation cache."""
    global _validation_cache
    _validation_cache.clear()


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
            suggestion="Add at least one node to the workflow",
        )
        return

    # Check for duplicate node_ids (critical for execution)
    _check_duplicate_node_ids(nodes, result)

    # Check for circular dependencies
    if has_circular_dependency(nodes, connections):
        result.add_error(
            "CIRCULAR_DEPENDENCY",
            "Workflow contains circular execution flow",
            suggestion="Review and break the circular connection chain",
        )

    # Find entry points and check reachability
    entry_points, reachable = find_entry_points_and_reachable(nodes, connections)

    # Warn if no explicit entry points (unusual but not an error)
    if not entry_points:
        result.add_warning(
            "NO_ENTRY_POINT",
            "Could not determine workflow entry point",
            suggestion="Add a node without incoming exec connections as the start",
        )

    # Check for unreachable nodes
    all_nodes = set(nodes.keys())
    unreachable = all_nodes - reachable

    # Filter out hidden/auto nodes from unreachable warning
    visible_unreachable = [n for n in unreachable if not n.startswith("__")]

    if visible_unreachable:
        result.add_warning(
            "UNREACHABLE_NODES",
            f"Some nodes are not reachable: {', '.join(list(visible_unreachable)[:5])}{'...' if len(visible_unreachable) > 5 else ''}",
            suggestion="Connect these nodes to the workflow or remove them",
        )


def _check_duplicate_node_ids(
    nodes: Dict[str, Dict[str, Any]],
    result: ValidationResult,
) -> None:
    """
    Check for duplicate node_id values across all nodes.

    This is a critical error because duplicate node_ids cause execution failures -
    the engine cannot distinguish which node to run.

    Args:
        nodes: Dictionary of node data (graph_id -> node_data)
        result: ValidationResult to add issues to
    """
    # Build mapping of node_id -> list of graph_ids that have it
    node_id_to_graph_ids: Dict[str, List[str]] = {}

    for graph_id, node_data in nodes.items():
        node_id = node_data.get("node_id", "")

        if not node_id:
            continue  # Skip nodes without node_id

        if node_id not in node_id_to_graph_ids:
            node_id_to_graph_ids[node_id] = []
        node_id_to_graph_ids[node_id].append(graph_id)

    # Find duplicates
    for node_id, graph_ids in node_id_to_graph_ids.items():
        if len(graph_ids) > 1:
            # Get node names for better error message
            node_names = []
            for gid in graph_ids[:5]:  # Limit to first 5
                node_data = nodes[gid]
                # Check multiple locations for name
                name = node_data.get("name") or node_data.get("display_name") or gid
                node_names.append(name)

            names_str = ", ".join(node_names)
            if len(graph_ids) > 5:
                names_str += f" (+{len(graph_ids) - 5} more)"

            result.add_error(
                "DUPLICATE_NODE_ID",
                f"Duplicate node_id '{node_id}' found in {len(graph_ids)} nodes: {names_str}",
                location=f"node:{graph_ids[0]}",  # Link to first duplicate
                suggestion="Use 'Repair' button to auto-fix duplicate IDs",
            )


__all__ = [
    "validate_workflow",
    "validate_node",
    "validate_connections",
    "quick_validate",
    "validate_incremental",
    "clear_validation_cache",
]
