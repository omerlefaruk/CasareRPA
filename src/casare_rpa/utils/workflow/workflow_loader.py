"""
Workflow Loader Utility
Deserializes workflow JSON into executable WorkflowSchema with node instances.

SECURITY: All workflows are validated against a strict schema before execution.

This module delegates to casare_rpa.nodes for node class resolution, which uses
lazy loading from _NODE_REGISTRY. This eliminates duplicate registration and
improves startup performance.
"""

from typing import Any, Dict, Type, Optional
from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.base_node import BaseNode

# Import the nodes module for lazy loading node classes
import casare_rpa.nodes as nodes_module


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""

    pass


# SECURITY: Maximum limits to prevent resource exhaustion
MAX_NODES = 1000
MAX_CONNECTIONS = 5000
MAX_NODE_ID_LENGTH = 256
MAX_CONFIG_DEPTH = 10
MAX_STRING_LENGTH = 10000


def _validate_string(
    value: Any, field_name: str, max_length: int = MAX_STRING_LENGTH
) -> str:
    """Validate a string field."""
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


def _validate_config_value(value: Any, path: str, depth: int = 0) -> Any:
    """Recursively validate config values to prevent malicious payloads."""
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
        # SECURITY: Check for potential code injection patterns - BLOCK, don't just log
        dangerous_patterns = [
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
        ]
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                logger.error(
                    f"SECURITY: Blocked dangerous pattern '{pattern}' in config at '{path}'"
                )
                raise WorkflowValidationError(
                    f"Security error: Potentially dangerous pattern '{pattern}' found in "
                    f"config value at '{path}'. This workflow cannot be loaded for security reasons."
                )
        return value

    if isinstance(value, list):
        return [
            _validate_config_value(item, f"{path}[{i}]", depth + 1)
            for i, item in enumerate(value)
        ]

    if isinstance(value, dict):
        return {
            _validate_string(
                k, f"{path}.key", MAX_NODE_ID_LENGTH
            ): _validate_config_value(v, f"{path}.{k}", depth + 1)
            for k, v in value.items()
        }

    raise WorkflowValidationError(
        f"Unsupported config value type at '{path}': {type(value).__name__}"
    )


def validate_workflow_structure(workflow_data: Dict) -> None:
    """
    SECURITY: Validate workflow structure before loading.

    Checks:
    - Required fields present
    - Field types correct
    - No malicious payloads
    - Size limits respected

    Args:
        workflow_data: Raw workflow dictionary from JSON

    Raises:
        WorkflowValidationError: If validation fails
    """
    if not isinstance(workflow_data, dict):
        raise WorkflowValidationError(
            f"Workflow must be a dictionary, got {type(workflow_data).__name__}"
        )

    # Validate metadata
    metadata = workflow_data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise WorkflowValidationError("'metadata' must be a dictionary")

    _validate_string(metadata.get("name"), "metadata.name", 256)
    _validate_string(metadata.get("description"), "metadata.description", 10000)
    _validate_string(metadata.get("version"), "metadata.version", 50)

    # Validate nodes
    nodes = workflow_data.get("nodes", {})
    if not isinstance(nodes, dict):
        raise WorkflowValidationError("'nodes' must be a dictionary")

    if len(nodes) > MAX_NODES:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum of {MAX_NODES} nodes (has {len(nodes)})"
        )

    for node_id, node_data in nodes.items():
        # Validate node_id
        _validate_string(node_id, "node_id", MAX_NODE_ID_LENGTH)

        if not isinstance(node_data, dict):
            raise WorkflowValidationError(f"Node '{node_id}' must be a dictionary")

        # Validate node_type
        node_type = node_data.get("node_type")
        _validate_string(node_type, f"nodes.{node_id}.node_type", 128)

        if not node_type:
            raise WorkflowValidationError(f"Node '{node_id}' is missing 'node_type'")

        # Validate config
        config = node_data.get("config", {})
        if not isinstance(config, dict):
            raise WorkflowValidationError(
                f"Node '{node_id}' config must be a dictionary"
            )

        _validate_config_value(config, f"nodes.{node_id}.config")

    # Validate connections
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
        _validate_string(
            conn.get("source_port", ""), f"connections[{i}].source_port", 128
        )
        _validate_string(
            conn.get("target_port", ""), f"connections[{i}].target_port", 128
        )

    logger.debug(
        f"Workflow validation passed: {len(nodes)} nodes, {len(connections)} connections"
    )


def get_node_class(node_type: str) -> Optional[Type[BaseNode]]:
    """
    Get a node class by type name using lazy loading from nodes module.

    This delegates to casare_rpa.nodes._NODE_REGISTRY which is the single
    source of truth for node class registration.

    Args:
        node_type: The node type name (e.g., "ClickElementNode")

    Returns:
        The node class, or None if not found
    """
    try:
        return getattr(nodes_module, node_type)
    except AttributeError:
        return None


def is_valid_node_type(node_type: str) -> bool:
    """Check if a node type is registered."""
    return node_type in nodes_module._NODE_REGISTRY


def get_all_node_types() -> list:
    """Get all registered node type names."""
    return list(nodes_module._NODE_REGISTRY.keys())


# Legacy compatibility - NODE_TYPE_MAP is now generated from _NODE_REGISTRY
# This allows existing code that imports NODE_TYPE_MAP to continue working
def _build_node_type_map() -> Dict[str, Type]:
    """Build NODE_TYPE_MAP from nodes module (lazy, on first access)."""
    return nodes_module.get_all_node_classes()


# Lazy-loaded NODE_TYPE_MAP for backward compatibility
_node_type_map_cache: Optional[Dict[str, Type]] = None


def _get_node_type_map() -> Dict[str, Type]:
    """Get NODE_TYPE_MAP, building it lazily if needed."""
    global _node_type_map_cache
    if _node_type_map_cache is None:
        _node_type_map_cache = _build_node_type_map()
    return _node_type_map_cache


# Backward compatibility: NODE_TYPE_MAP is now a lazy property
# Code that accesses NODE_TYPE_MAP directly will trigger building the full map
class _NodeTypeMapProxy:
    """Proxy class that builds NODE_TYPE_MAP on first access."""

    def __contains__(self, key):
        return is_valid_node_type(key)

    def __getitem__(self, key):
        node_class = get_node_class(key)
        if node_class is None:
            raise KeyError(key)
        return node_class

    def get(self, key, default=None):
        return get_node_class(key) or default

    def keys(self):
        return get_all_node_types()

    def __len__(self):
        return len(nodes_module._NODE_REGISTRY)

    def items(self):
        return _get_node_type_map().items()

    def values(self):
        return _get_node_type_map().values()


# Export NODE_TYPE_MAP as the proxy for backward compatibility
NODE_TYPE_MAP = _NodeTypeMapProxy()


def load_workflow_from_dict(
    workflow_data: Dict, skip_validation: bool = False
) -> WorkflowSchema:
    """
    Load a workflow from serialized dictionary data.

    SECURITY: Validates workflow structure before loading unless skip_validation=True.

    Args:
        workflow_data: Serialized workflow data
        skip_validation: Skip security validation (NOT RECOMMENDED)

    Returns:
        WorkflowSchema with actual node instances

    Raises:
        WorkflowValidationError: If validation fails
    """
    # SECURITY: Validate workflow structure before processing
    if not skip_validation:
        validate_workflow_structure(workflow_data)
        logger.info("Workflow validation passed")
    else:
        logger.warning(
            "Workflow validation SKIPPED - this is not recommended for untrusted workflows"
        )

    # Create metadata
    metadata = WorkflowMetadata.from_dict(workflow_data.get("metadata", {}))
    workflow = WorkflowSchema(metadata)

    # Deserialize nodes into instances
    nodes_dict: Dict[str, BaseNode] = {}

    for node_id, node_data in workflow_data.get("nodes", {}).items():
        node_type = node_data.get("node_type")
        config = node_data.get("config", {})

        # Use lazy loading from nodes module
        node_class = get_node_class(node_type)
        if node_class is not None:
            # Pass config as keyword argument
            node_instance = node_class(node_id, config=config)
            nodes_dict[node_id] = node_instance
            logger.debug(f"Loaded node {node_id}: {node_type} with config: {config}")
        else:
            logger.warning(f"Unknown node type: {node_type}")

    # Check if workflow already has a StartNode (from Canvas)
    has_start_node = any(node.node_type == "StartNode" for node in nodes_dict.values())

    # Auto-create hidden Start node ONLY if workflow doesn't have one (like Canvas does)
    if not has_start_node:
        StartNode = get_node_class("StartNode")
        if StartNode:
            start_node = StartNode("__auto_start__")
            nodes_dict["__auto_start__"] = start_node
            logger.info("Added auto-start node (no StartNode found in workflow)")
    else:
        logger.info("Workflow already has a StartNode, skipping auto-start creation")

    # Set nodes as instances (WorkflowRunner needs this)
    workflow.nodes = nodes_dict

    # Load connections
    for conn_data in workflow_data.get("connections", []):
        workflow.connections.append(NodeConnection.from_dict(conn_data))

    # Find entry points (nodes without exec_in connections) and auto-connect Start node
    # Only do this if we created __auto_start__
    if not has_start_node:
        connected_exec_ins = set()
        trigger_output_targets = set()  # Nodes connected to trigger exec_out

        for conn in workflow.connections:
            if conn.target_port == "exec_in":
                connected_exec_ins.add(conn.target_node)
            # Track what trigger nodes connect to
            source_node = nodes_dict.get(conn.source_node)
            if (
                source_node
                and "Trigger" in source_node.node_type
                and conn.source_port == "exec_out"
            ):
                trigger_output_targets.add(conn.target_node)

        # Auto-connect Start to entry points
        for node_id, node in nodes_dict.items():
            if node_id == "__auto_start__":
                continue

            # Skip trigger nodes - they're entry points themselves, not execution targets
            if "Trigger" in node.node_type:
                continue

            # Connect Start to:
            # 1. Nodes with unconnected exec_in, OR
            # 2. Nodes that are targets of trigger exec_out (so workflow runs from trigger's target)
            should_connect = (
                "exec_in" in node.input_ports and node_id not in connected_exec_ins
            ) or node_id in trigger_output_targets

            if should_connect:
                connection = NodeConnection(
                    source_node="__auto_start__",
                    source_port="exec_out",
                    target_node=node_id,
                    target_port="exec_in",
                )
                workflow.connections.append(connection)
                logger.info(f"Auto-connected Start → {node_id}")

    # Load variables and settings
    workflow.variables = workflow_data.get("variables", {})
    workflow.settings = workflow_data.get("settings", workflow.settings)

    logger.info(
        f"Loaded workflow '{metadata.name}' with {len(nodes_dict)} nodes and {len(workflow.connections)} connections"
    )
    return workflow
