"""
Workflow migration utility for upgrading legacy node IDs to UUID format.

Handles:
- Migrating old incremental IDs (NodeType_1) to UUID format (NodeType_a1b2c3d4)
- Remapping connections to use new IDs
- Updating frame node references
"""

from typing import Dict, Any, Tuple
import copy
from loguru import logger

from .id_generator import generate_node_id, is_uuid_based_id


def migrate_workflow_ids(workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Migrate legacy numeric IDs to UUID-based IDs in a workflow.

    This function is idempotent - it won't re-migrate already migrated IDs.

    Args:
        workflow_data: Deserialized workflow dictionary

    Returns:
        Tuple of (migrated_workflow_data, old_to_new_id_mapping)
    """
    # Work on a deep copy to avoid mutating input
    data = copy.deepcopy(workflow_data)
    id_mapping: Dict[str, str] = {}  # old_id -> new_id

    nodes = data.get("nodes", {})
    connections = data.get("connections", [])
    frames = data.get("frames", [])

    # Pass 1: Generate new IDs for nodes with legacy format
    new_nodes = {}
    migrated_count = 0

    for old_id, node_data in nodes.items():
        if is_uuid_based_id(old_id):
            # Already using new format - keep as-is
            new_nodes[old_id] = node_data
            id_mapping[old_id] = old_id
        else:
            # Generate new UUID-based ID
            node_type = node_data.get("node_type", "Node")
            new_id = generate_node_id(node_type)
            id_mapping[old_id] = new_id

            # Update node_id in node data
            node_data["node_id"] = new_id
            new_nodes[new_id] = node_data

            migrated_count += 1
            logger.debug(f"Migrated node ID: {old_id} -> {new_id}")

    data["nodes"] = new_nodes

    # Pass 2: Update connection references
    for conn in connections:
        source = conn.get("source_node", "")
        target = conn.get("target_node", "")

        if source in id_mapping:
            conn["source_node"] = id_mapping[source]
        if target in id_mapping:
            conn["target_node"] = id_mapping[target]

    # Pass 3: Update frame node references
    for frame in frames:
        # Handle both possible key names
        contained_key = None
        if "contained_nodes" in frame:
            contained_key = "contained_nodes"
        elif "node_ids" in frame:
            contained_key = "node_ids"

        if contained_key and frame[contained_key]:
            frame[contained_key] = [
                id_mapping.get(nid, nid) for nid in frame[contained_key]
            ]

    # Update schema version to indicate migration
    if "metadata" in data:
        data["metadata"]["schema_version"] = "1.1.0"

    if migrated_count > 0:
        logger.info(f"Migrated {migrated_count} node IDs to UUID format")

    return data, id_mapping


def needs_migration(workflow_data: Dict[str, Any]) -> bool:
    """
    Check if a workflow needs ID migration.

    Args:
        workflow_data: Deserialized workflow dictionary

    Returns:
        True if any nodes use legacy numeric IDs
    """
    nodes = workflow_data.get("nodes", {})
    return any(not is_uuid_based_id(nid) for nid in nodes.keys())


def remap_ids_for_import(
    workflow_data: Dict[str, Any],
    existing_ids: set
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Remap node IDs in a workflow to avoid conflicts with existing nodes.

    Used when importing/merging a workflow into an existing one.

    Args:
        workflow_data: Deserialized workflow dictionary to import
        existing_ids: Set of node IDs that already exist in the target workflow

    Returns:
        Tuple of (remapped_workflow_data, old_to_new_id_mapping)
    """
    data = copy.deepcopy(workflow_data)
    id_mapping: Dict[str, str] = {}

    nodes = data.get("nodes", {})
    connections = data.get("connections", [])
    frames = data.get("frames", [])

    # Remap nodes that conflict with existing IDs
    new_nodes = {}
    remapped_count = 0

    for old_id, node_data in nodes.items():
        if old_id in existing_ids or old_id in id_mapping.values():
            # Conflict - generate new ID
            node_type = node_data.get("node_type", "Node")
            new_id = generate_node_id(node_type)
            id_mapping[old_id] = new_id

            node_data["node_id"] = new_id
            new_nodes[new_id] = node_data

            remapped_count += 1
            logger.debug(f"Remapped conflicting ID: {old_id} -> {new_id}")
        else:
            # No conflict - keep original
            id_mapping[old_id] = old_id
            new_nodes[old_id] = node_data

    data["nodes"] = new_nodes

    # Update connection references
    for conn in connections:
        source = conn.get("source_node", "")
        target = conn.get("target_node", "")

        if source in id_mapping:
            conn["source_node"] = id_mapping[source]
        if target in id_mapping:
            conn["target_node"] = id_mapping[target]

    # Update frame node references
    for frame in frames:
        contained_key = None
        if "contained_nodes" in frame:
            contained_key = "contained_nodes"
        elif "node_ids" in frame:
            contained_key = "node_ids"

        if contained_key and frame[contained_key]:
            frame[contained_key] = [
                id_mapping.get(nid, nid) for nid in frame[contained_key]
            ]

    if remapped_count > 0:
        logger.info(f"Remapped {remapped_count} conflicting node IDs for import")

    return data, id_mapping
