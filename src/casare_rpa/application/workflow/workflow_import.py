"""
Workflow Import Module for CasareRPA.

Handles importing/merging nodes from external workflows into the current canvas.
Supports:
- File import via menu
- JSON text paste
- Drag-and-drop JSON files
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    imported_nodes: list[str] = field(default_factory=list)
    imported_frames: list[Any] = field(default_factory=list)
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)


class WorkflowImporter:
    """
    Imports nodes from workflow JSON data into an existing graph.

    Handles:
    - ID remapping to prevent conflicts
    - Position offsetting to avoid overlapping existing nodes
    - Connection remapping to use new IDs
    - Frame import with node reference updates
    """

    def __init__(self, graph, node_factory):
        """
        Initialize importer.

        Args:
            graph: NodeGraphQt NodeGraph instance
            node_factory: NodeFactory for creating nodes
        """
        self._graph = graph
        self._node_factory = node_factory

    def get_existing_node_ids(self) -> set[str]:
        """Get set of all existing node IDs in the graph."""
        existing_ids = set()
        for visual_node in self._graph.all_nodes():
            node_id = visual_node.get_property("node_id")
            if node_id:
                existing_ids.add(node_id)
        return existing_ids

    def remap_node_ids(self, workflow_data: dict) -> tuple[dict, dict[str, str]]:
        """
        Remap node IDs to avoid conflicts with existing nodes.

        Args:
            workflow_data: Raw workflow JSON data

        Returns:
            Tuple of (modified workflow data, id_mapping dict)
        """
        from ...utils.id_generator import generate_node_id

        data = copy.deepcopy(workflow_data)
        existing_ids = self.get_existing_node_ids()
        id_mapping: dict[str, str] = {}  # old_id -> new_id

        # Generate new IDs for all nodes that conflict
        for old_id, node_data in list(data.get("nodes", {}).items()):
            if old_id in existing_ids or old_id in id_mapping.values():
                # Conflict - generate new unique ID
                node_type = node_data.get("node_type", "Node")
                new_id = generate_node_id(node_type)
                id_mapping[old_id] = new_id
                logger.debug(f"Remapped conflicting ID: {old_id} -> {new_id}")
            else:
                # No conflict - keep original ID
                id_mapping[old_id] = old_id

        # Apply ID remapping to nodes dict
        new_nodes = {}
        for old_id, node_data in data.get("nodes", {}).items():
            new_id = id_mapping[old_id]
            node_data["node_id"] = new_id
            new_nodes[new_id] = node_data
        data["nodes"] = new_nodes

        # Remap connections
        new_connections = []
        for conn in data.get("connections", []):
            new_conn = {
                "source_node": id_mapping.get(
                    conn.get("source_node", ""), conn.get("source_node", "")
                ),
                "source_port": conn.get("source_port", ""),
                "target_node": id_mapping.get(
                    conn.get("target_node", ""), conn.get("target_node", "")
                ),
                "target_port": conn.get("target_port", ""),
            }
            new_connections.append(new_conn)
        data["connections"] = new_connections

        # Remap frame contained_nodes
        new_frames = []
        for frame in data.get("frames", []):
            new_frame = dict(frame)

            # Handle both possible key names
            if "contained_nodes" in frame:
                new_frame["contained_nodes"] = [
                    id_mapping.get(nid, nid) for nid in frame["contained_nodes"]
                ]
            elif "node_ids" in frame:
                new_frame["node_ids"] = [id_mapping.get(nid, nid) for nid in frame["node_ids"]]

            new_frames.append(new_frame)
        data["frames"] = new_frames

        return data, id_mapping

    def calculate_import_position(
        self, workflow_data: dict, drop_position: tuple[float, float] | None = None
    ) -> tuple[float, float]:
        """
        Calculate position offset for imported nodes.

        Args:
            workflow_data: Workflow data with node positions
            drop_position: Optional drop location (for drag-and-drop)

        Returns:
            (offset_x, offset_y) to add to all imported node positions
        """
        # Get bounds of existing nodes
        existing_nodes = self._graph.all_nodes()
        if existing_nodes:
            max_x = max(n.pos()[0] for n in existing_nodes)
            min_y = min(n.pos()[1] for n in existing_nodes)
        else:
            max_x, min_y = 0, 0

        # Get bounds of imported nodes
        import_nodes = workflow_data.get("nodes", {})
        if not import_nodes:
            return (0, 0)

        min_import_x = float("inf")
        min_import_y = float("inf")

        for node_data in import_nodes.values():
            pos = node_data.get("position", [0, 0])
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                min_import_x = min(min_import_x, float(pos[0]))
                min_import_y = min(min_import_y, float(pos[1]))

        if min_import_x == float("inf"):
            min_import_x = 0
        if min_import_y == float("inf"):
            min_import_y = 0

        if drop_position:
            # Place at drop location
            offset_x = drop_position[0] - min_import_x
            offset_y = drop_position[1] - min_import_y
        else:
            # Place to the right of existing nodes with spacing
            spacing = 300
            offset_x = max_x + spacing - min_import_x
            offset_y = min_y - min_import_y

        return (offset_x, offset_y)

    def apply_position_offset(self, workflow_data: dict, offset: tuple[float, float]) -> dict:
        """
        Apply position offset to all nodes and frames in workflow data.

        Args:
            workflow_data: Workflow data (will be modified in place)
            offset: (offset_x, offset_y) tuple

        Returns:
            Modified workflow data
        """
        offset_x, offset_y = offset

        # Offset node positions
        for node_data in workflow_data.get("nodes", {}).values():
            if "position" in node_data:
                pos = node_data["position"]
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    node_data["position"] = [
                        float(pos[0]) + offset_x,
                        float(pos[1]) + offset_y,
                    ]

        # Offset frame positions (canonical: [x, y])
        for frame in workflow_data.get("frames", []):
            position = frame.get("position", [0, 0])
            if not isinstance(position, (list, tuple)) or len(position) < 2:
                raise ValueError("Frame position must be a [x, y] list")
            frame["position"] = [
                float(position[0]) + offset_x,
                float(position[1]) + offset_y,
            ]

        return workflow_data


def import_workflow_data(
    graph,
    node_factory,
    workflow_data: dict,
    drop_position: tuple[float, float] | None = None,
) -> tuple[dict, dict[str, str]]:
    """
    Prepare workflow data for import.

    Convenience function that handles ID remapping and position calculation.

    Args:
        graph: NodeGraphQt NodeGraph instance
        node_factory: NodeFactory instance
        workflow_data: Raw workflow JSON data
        drop_position: Optional drop location

    Returns:
        Tuple of (prepared workflow data, id_mapping)
    """
    importer = WorkflowImporter(graph, node_factory)

    # Remap IDs to avoid conflicts
    data, id_mapping = importer.remap_node_ids(workflow_data)

    # Calculate and apply position offset
    offset = importer.calculate_import_position(data, drop_position)
    data = importer.apply_position_offset(data, offset)

    return data, id_mapping
