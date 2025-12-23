"""
Workflow Loader Utility
Deserializes workflow JSON into executable WorkflowSchema with node instances.

SECURITY: All workflows are validated against a strict schema before execution.

This module delegates to casare_rpa.nodes for node class resolution, which uses
lazy loading from the central node registry. This eliminates duplicate
registration and improves startup performance.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from loguru import logger

# Import the nodes module for lazy loading node classes
import casare_rpa.nodes as nodes_module
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.validation import (
    validate_workflow_json,
)
from casare_rpa.infrastructure.caching.workflow_cache import get_workflow_cache


def get_node_class(node_type: str) -> type[BaseNode] | None:
    """
    Get a node class by type name using lazy loading from nodes module.

    This delegates to casare_rpa.nodes.get_node_class which is the single
    source of truth for node class registration.

    Args:
        node_type: The node type name (e.g., "ClickElementNode")

    Returns:
        The node class, or None if not found
    """
    try:
        return nodes_module.get_node_class(node_type)
    except AttributeError:
        return None


def is_valid_node_type(node_type: str) -> bool:
    """Check if a node type is registered."""
    return node_type in nodes_module.NODE_REGISTRY


def get_all_node_types() -> list:
    """Get all registered node type names."""
    return list(nodes_module.NODE_REGISTRY.keys())


# =============================================================================
# PARALLEL NODE INSTANTIATION (Phase C3 Optimization)
# =============================================================================

# Threshold for switching to parallel instantiation
PARALLEL_NODE_THRESHOLD = 20
PARALLEL_MAX_WORKERS = 4


def _batch_resolve_node_types(
    nodes_data: dict[str, dict],
) -> dict[str, tuple[str, dict[str, Any]]]:
    """
    Batch extract node types/configs for performance.

    Args:
        nodes_data: Dict mapping node_id to node data

    Returns:
        Dict mapping node_id to (node_type, config)
    """
    resolved = {}
    for node_id, node_data in nodes_data.items():
        node_type = node_data.get("node_type")
        config = node_data.get("config", {})
        if node_type:
            resolved[node_id] = (node_type, config)
    return resolved


def _preload_workflow_node_types(node_types: set) -> None:
    """
    Preload all unique node types used in a workflow.

    PERFORMANCE: Triggers lazy loading of all needed node classes
    before the instantiation loop, improving cache hit rates.

    Args:
        node_types: Set of node type names
    """
    for node_type in node_types:
        try:
            get_node_class(node_type)
        except Exception:
            pass  # Ignore errors, handled during instantiation


def _create_single_node(
    node_id: str,
    node_type: str,
    config: dict[str, Any],
    use_pooling: bool = False,
) -> tuple[str, Any | None]:
    """
    Create a single node instance.

    Used by both sequential and parallel instantiation.

    Args:
        node_id: Node identifier
        node_type: Node type name
        config: Node configuration
        use_pooling: Whether to use node instance pooling

    Returns:
        Tuple of (node_id, node_instance or None)
    """
    try:
        node_class = get_node_class(node_type)
        if node_class is None:
            logger.warning(f"Unknown node type: {node_type}")
            return node_id, None

        if use_pooling:
            try:
                from casare_rpa.utils.performance.object_pool import (
                    get_node_instance_pool,
                )

                pool = get_node_instance_pool()
                node_instance = pool.acquire(node_type, node_class, node_id, config)
            except Exception as e:
                # Fallback to direct instantiation
                logger.debug(
                    f"Pool acquire failed for {node_type}, using direct instantiation: {e}"
                )
                node_instance = node_class(node_id, config=config)
        else:
            node_instance = node_class(node_id, config=config)

        return node_id, node_instance

    except Exception as e:
        logger.warning(f"Failed to create node {node_id} ({node_type}): {e}")
        return node_id, None


def _instantiate_nodes_parallel(
    nodes_data: dict[str, dict],
    resolved_types: dict[str, tuple[str, dict[str, Any]]],
    max_workers: int = PARALLEL_MAX_WORKERS,
    use_pooling: bool = False,
) -> dict[str, Any]:
    """
    Instantiate nodes in parallel for large workflows.

    PERFORMANCE: Uses ThreadPoolExecutor for concurrent node creation.
    Provides 50-100ms improvement for workflows with 50+ nodes.

    THREAD SAFETY NOTE: Node instantiation is assumed to be thread-safe.
    If a node's __init__ has non-thread-safe side effects (e.g., modifying
    global state), parallel instantiation may cause issues. In such cases,
    use use_parallel=False in load_workflow_from_dict().

    Args:
        nodes_data: Dict mapping node_id to node data
        resolved_types: Pre-resolved node types from _batch_resolve_node_types
        max_workers: Max concurrent workers
        use_pooling: Whether to use node instance pooling

    Returns:
        Dict mapping node_id to node instance
    """
    nodes_dict = {}
    node_count = len(nodes_data)

    # For small workflows, sequential is faster (no thread overhead)
    if node_count < PARALLEL_NODE_THRESHOLD:
        for node_id in nodes_data:
            if node_id not in resolved_types:
                continue
            node_type, config = resolved_types[node_id]
            _, node = _create_single_node(node_id, node_type, config, use_pooling)
            if node:
                nodes_dict[node_id] = node
                logger.debug(f"Loaded node {node_id}: {node_type}")
        return nodes_dict

    # Parallel instantiation for large workflows
    logger.debug(f"Using parallel instantiation for {node_count} nodes")
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for node_id in nodes_data:
            if node_id not in resolved_types:
                continue
            node_type, config = resolved_types[node_id]
            future = executor.submit(_create_single_node, node_id, node_type, config, use_pooling)
            futures[future] = node_id

        for future in as_completed(futures):
            node_id, node = future.result()
            if node:
                nodes_dict[node_id] = node

    elapsed = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Parallel instantiation complete: {len(nodes_dict)} nodes in {elapsed:.1f}ms")

    return nodes_dict


def load_workflow_from_dict(
    workflow_data: dict,
    skip_validation: bool = False,
    use_parallel: bool = True,
    use_pooling: bool = False,
    use_cache: bool = True,
) -> WorkflowSchema:
    """
    Load a workflow from serialized dictionary data.

    SECURITY: Validates workflow structure before loading unless skip_validation=True.

    PERFORMANCE: Uses parallel instantiation for large workflows (>20 nodes)
    and optional node instance pooling for repeated loads. Caches parsed
    workflows using content fingerprinting for repeated loads.

    Args:
        workflow_data: Serialized workflow data
        skip_validation: Skip security validation (NOT RECOMMENDED)
        use_parallel: Use parallel node instantiation for large workflows
        use_pooling: Use node instance pooling for repeated loads
        use_cache: Use workflow cache for repeated loads (default True)

    Returns:
        WorkflowSchema with actual node instances

    Raises:
        WorkflowValidationError: If validation fails
    """
    load_start = time.perf_counter()

    # PERFORMANCE: Check workflow cache first
    cache_fingerprint = None
    if use_cache:
        cache = get_workflow_cache()
        fingerprint_data = dict(workflow_data)
        cache_fingerprint = cache.compute_fingerprint(fingerprint_data)
        cached_workflow = cache.get(cache_fingerprint)
        if cached_workflow is not None:
            load_elapsed = (time.perf_counter() - load_start) * 1000
            logger.info(f"Loaded workflow from cache in {load_elapsed:.1f}ms")
            return cached_workflow

    # SECURITY: Validate workflow structure before processing
    if not skip_validation:
        validate_workflow_json(workflow_data)
        logger.debug("Workflow validation passed")
    else:
        logger.warning(
            "Workflow validation SKIPPED - this is not recommended for untrusted workflows"
        )

    # Create metadata
    metadata = WorkflowMetadata.from_dict(workflow_data.get("metadata", {}))
    workflow = WorkflowSchema(metadata)

    # Get nodes data
    nodes_data = workflow_data.get("nodes", {})

    # PERFORMANCE: Batch resolve all node types first
    resolved_types = _batch_resolve_node_types(nodes_data)

    # PERFORMANCE: Preload all unique node types
    unique_types = {t for t, _ in resolved_types.values()}
    _preload_workflow_node_types(unique_types)

    # PERFORMANCE: Use parallel instantiation for large workflows
    if use_parallel:
        nodes_dict = _instantiate_nodes_parallel(
            nodes_data, resolved_types, use_pooling=use_pooling
        )
    else:
        # Sequential instantiation
        nodes_dict: dict[str, BaseNode] = {}
        for node_id in nodes_data:
            if node_id not in resolved_types:
                continue
            node_type, config = resolved_types[node_id]
            _, node = _create_single_node(node_id, node_type, config, use_pooling)
            if node:
                nodes_dict[node_id] = node
                logger.debug(f"Loaded node {node_id}: {node_type}")

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

    # PERFORMANCE: Log total load time
    load_elapsed = (time.perf_counter() - load_start) * 1000
    logger.info(
        f"Loaded workflow '{metadata.name}' with {len(nodes_dict)} nodes "
        f"and {len(workflow.connections)} connections in {load_elapsed:.1f}ms"
    )

    # PERFORMANCE: Cache the parsed workflow for future loads
    if use_cache and cache_fingerprint:
        cache.put(cache_fingerprint, workflow)

    return workflow
