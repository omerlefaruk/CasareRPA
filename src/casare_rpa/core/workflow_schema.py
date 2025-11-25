"""
CasareRPA - Workflow Schema
Defines the JSON structure for saving and loading workflows.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import orjson
from loguru import logger

from .types import (
    Connection,
    NodeId,
    PortId,
    SerializedFrame,
    SerializedNode,
    SerializedWorkflow,
    SCHEMA_VERSION,
)


class WorkflowMetadata:
    """Metadata about a workflow."""

    def __init__(
        self,
        name: str,
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize workflow metadata.

        Args:
            name: Workflow name
            description: Workflow description
            author: Workflow creator
            version: Workflow version
            tags: List of tags for categorization
        """
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.schema_version = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowMetadata":
        """Create metadata from dictionary."""
        metadata = cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
        )
        metadata.created_at = data.get("created_at", metadata.created_at)
        metadata.modified_at = data.get("modified_at", metadata.modified_at)
        metadata.schema_version = data.get("schema_version", SCHEMA_VERSION)
        return metadata


class NodeConnection:
    """Represents a connection between two node ports."""

    def __init__(
        self,
        source_node: NodeId,
        source_port: str,
        target_node: NodeId,
        target_port: str,
    ) -> None:
        """
        Initialize a connection.

        Args:
            source_node: ID of source node
            source_port: Name of source port
            target_node: ID of target node
            target_port: Name of target port
        """
        self.source_node = source_node
        self.source_port = source_port
        self.target_node = target_node
        self.target_port = target_port

    @property
    def source_id(self) -> PortId:
        """Get full source port ID."""
        return f"{self.source_node}.{self.source_port}"

    @property
    def target_id(self) -> PortId:
        """Get full target port ID."""
        return f"{self.target_node}.{self.target_port}"

    def to_dict(self) -> Dict[str, str]:
        """Serialize connection to dictionary."""
        return {
            "source_node": self.source_node,
            "source_port": self.source_port,
            "target_node": self.target_node,
            "target_port": self.target_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "NodeConnection":
        """Create connection from dictionary."""
        return cls(
            source_node=data["source_node"],
            source_port=data["source_port"],
            target_node=data["target_node"],
            target_port=data["target_port"],
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.source_id} -> {self.target_id}"


class WorkflowSchema:
    """
    Represents a complete workflow with nodes and connections.
    Handles serialization and deserialization.
    """

    def __init__(self, metadata: Optional[WorkflowMetadata] = None) -> None:
        """
        Initialize workflow schema.

        Args:
            metadata: Workflow metadata (creates default if None)
        """
        self.metadata = metadata or WorkflowMetadata(name="Untitled Workflow")
        self.nodes: Dict[NodeId, SerializedNode] = {}
        self.connections: List[NodeConnection] = []
        self.frames: List[SerializedFrame] = []  # Node frames/groups
        self.variables: Dict[str, Any] = {}  # Global workflow variables
        self.settings: Dict[str, Any] = {
            "stop_on_error": True,
            "timeout": 30,
            "retry_count": 0,
        }

    def add_node(self, node_data: SerializedNode) -> None:
        """Add a node to the workflow."""
        node_id = node_data["node_id"]
        self.nodes[node_id] = node_data
        logger.debug(f"Added node {node_id} to workflow")

    def remove_node(self, node_id: NodeId) -> None:
        """Remove a node and its connections from the workflow."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Remove connections involving this node
            self.connections = [
                conn
                for conn in self.connections
                if conn.source_node != node_id and conn.target_node != node_id
            ]
            logger.debug(f"Removed node {node_id} from workflow")

    def add_connection(self, connection: NodeConnection) -> None:
        """Add a connection between nodes."""
        # Validate nodes exist
        if connection.source_node not in self.nodes:
            raise ValueError(f"Source node {connection.source_node} not found")
        if connection.target_node not in self.nodes:
            raise ValueError(f"Target node {connection.target_node} not found")

        self.connections.append(connection)
        logger.debug(f"Added connection: {connection}")

    def remove_connection(
        self, source_node: NodeId, source_port: str, target_node: NodeId, target_port: str
    ) -> None:
        """Remove a connection between nodes."""
        self.connections = [
            conn
            for conn in self.connections
            if not (
                conn.source_node == source_node
                and conn.source_port == source_port
                and conn.target_node == target_node
                and conn.target_port == target_port
            )
        ]

    def get_node(self, node_id: NodeId) -> Optional[SerializedNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_connections_from(self, node_id: NodeId) -> List[NodeConnection]:
        """Get all connections originating from a node."""
        return [conn for conn in self.connections if conn.source_node == node_id]

    def get_connections_to(self, node_id: NodeId) -> List[NodeConnection]:
        """Get all connections targeting a node."""
        return [conn for conn in self.connections if conn.target_node == node_id]

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the workflow structure.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        # Check for orphaned connections
        for conn in self.connections:
            if conn.source_node not in self.nodes:
                errors.append(f"Connection references missing source node: {conn.source_node}")
            if conn.target_node not in self.nodes:
                errors.append(f"Connection references missing target node: {conn.target_node}")

        # Check for circular dependencies (simple check)
        if self._has_circular_dependency():
            errors.append("Workflow contains circular dependencies")

        # Check if workflow has at least one node
        if not self.nodes:
            errors.append("Workflow has no nodes")

        return len(errors) == 0, errors

    def _has_circular_dependency(self) -> bool:
        """Check if workflow has circular dependencies using DFS."""
        # Build adjacency list
        graph: Dict[NodeId, List[NodeId]] = {node_id: [] for node_id in self.nodes}
        for conn in self.connections:
            graph[conn.source_node].append(conn.target_node)

        visited: set[NodeId] = set()
        rec_stack: set[NodeId] = set()

        def has_cycle(node: NodeId) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return True

        return False

    def to_dict(self) -> SerializedWorkflow:
        """
        Serialize workflow to dictionary.

        Returns:
            Complete workflow data structure
        """
        return {
            "metadata": self.metadata.to_dict(),
            "nodes": self.nodes,
            "connections": [conn.to_dict() for conn in self.connections],
            "frames": self.frames,
            "variables": self.variables,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: SerializedWorkflow) -> "WorkflowSchema":
        """
        Create workflow from dictionary.

        Args:
            data: Serialized workflow data

        Returns:
            WorkflowSchema instance
        """
        metadata = WorkflowMetadata.from_dict(data.get("metadata", {}))
        workflow = cls(metadata)

        # Load nodes
        workflow.nodes = data.get("nodes", {})

        # Load connections
        for conn_data in data.get("connections", []):
            workflow.connections.append(NodeConnection.from_dict(conn_data))

        # Load frames
        workflow.frames = data.get("frames", [])

        # Load variables and settings
        workflow.variables = data.get("variables", {})
        workflow.settings = data.get("settings", workflow.settings)

        return workflow

    def save_to_file(self, file_path: Path) -> None:
        """
        Save workflow to JSON file using orjson.

        Args:
            file_path: Path to save file
        """
        try:
            # Update modified timestamp
            self.metadata.modified_at = datetime.now().isoformat()

            # Serialize to JSON using orjson for performance
            json_data = orjson.dumps(
                self.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )

            # Write to file
            file_path.write_bytes(json_data)
            logger.info(f"Workflow saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            raise

    @classmethod
    def load_from_file(cls, file_path: Path) -> "WorkflowSchema":
        """
        Load workflow from JSON file.

        Args:
            file_path: Path to workflow file

        Returns:
            WorkflowSchema instance
        """
        try:
            # Read file
            json_data = file_path.read_bytes()

            # Parse JSON using orjson
            data = orjson.loads(json_data)

            # Create workflow
            workflow = cls.from_dict(data)
            logger.info(f"Workflow loaded from {file_path}")

            return workflow

        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Workflow(name='{self.metadata.name}', "
            f"nodes={len(self.nodes)}, "
            f"connections={len(self.connections)})"
        )
