"""
CasareRPA - Domain Entity: Workflow
Workflow aggregate root - manages nodes, connections, and workflow metadata.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger

from ..value_objects.types import NodeId, SerializedNode, SerializedFrame, SerializedWorkflow
from .workflow_metadata import WorkflowMetadata
from .node_connection import NodeConnection


@dataclass
class VariableDefinition:
    """
    Definition of a workflow variable.

    Attributes:
        name: Variable name (must be valid identifier)
        type: Variable type (String, Integer, Float, Boolean, List, Dict, DataTable)
        default_value: Default value for the variable
        description: Optional description
    """
    name: str
    type: str = "String"
    default_value: Any = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "default_value": self.default_value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableDefinition":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "String"),
            default_value=data.get("default_value", ""),
            description=data.get("description", ""),
        )


class WorkflowSchema:
    """
    Workflow aggregate root - manages nodes, connections, and workflow metadata.

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
        """
        Add a node to the workflow.

        Ensures consistency between node_id field and dict key
        to prevent NODE_ID_MISMATCH errors.

        Args:
            node_data: Serialized node data
        """
        node_id = node_data["node_id"]

        # Use node_id field as canonical source of truth
        self.nodes[node_id] = node_data
        logger.debug(f"Added node {node_id} to workflow")

    def remove_node(self, node_id: NodeId) -> None:
        """
        Remove a node and its connections from the workflow.

        Args:
            node_id: ID of node to remove
        """
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
        """
        Add a connection between nodes.

        Args:
            connection: NodeConnection to add

        Raises:
            ValueError: If source or target node doesn't exist
        """
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
        """
        Remove a connection between nodes.

        Args:
            source_node: Source node ID
            source_port: Source port name
            target_node: Target node ID
            target_port: Target port name
        """
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
        """
        Get a node by ID.

        Args:
            node_id: Node ID to look up

        Returns:
            Serialized node data or None if not found
        """
        return self.nodes.get(node_id)

    def get_connections_from(self, node_id: NodeId) -> List[NodeConnection]:
        """
        Get all connections originating from a node.

        Args:
            node_id: Source node ID

        Returns:
            List of connections from this node
        """
        return [conn for conn in self.connections if conn.source_node == node_id]

    def get_connections_to(self, node_id: NodeId) -> List[NodeConnection]:
        """
        Get all connections targeting a node.

        Args:
            node_id: Target node ID

        Returns:
            List of connections to this node
        """
        return [conn for conn in self.connections if conn.target_node == node_id]

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the workflow structure (simple interface).

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        # Import here to avoid circular dependency
        from ...core.validation import quick_validate
        return quick_validate(self.to_dict())

    def validate_full(self) -> "ValidationResult":
        """
        Perform comprehensive validation and return detailed result.

        Returns:
            ValidationResult with all issues and suggestions
        """
        # Import here to avoid circular dependency
        from ...core.validation import validate_workflow, ValidationResult
        return validate_workflow(self.to_dict())

    def to_dict(self) -> SerializedWorkflow:
        """
        Serialize workflow to dictionary.

        Returns:
            Complete workflow data structure
        """
        # Serialize variables - support both VariableDefinition objects and plain dicts
        serialized_vars = {}
        for name, var in self.variables.items():
            if isinstance(var, VariableDefinition):
                serialized_vars[name] = var.to_dict()
            elif isinstance(var, dict):
                serialized_vars[name] = var
            else:
                # Plain value - wrap in dict
                serialized_vars[name] = {
                    "type": self._infer_type(var),
                    "default_value": var,
                    "description": "",
                }

        return {
            "metadata": self.metadata.to_dict(),
            "nodes": self.nodes,
            "connections": [conn.to_dict() for conn in self.connections],
            "frames": self.frames,
            "variables": serialized_vars,
            "settings": self.settings,
        }

    def _infer_type(self, value: Any) -> str:
        """
        Infer variable type from value.

        Args:
            value: Value to infer type from

        Returns:
            Type name as string
        """
        if isinstance(value, bool):
            return "Boolean"
        if isinstance(value, int):
            return "Integer"
        if isinstance(value, float):
            return "Float"
        if isinstance(value, list):
            return "List"
        if isinstance(value, dict):
            return "Dict"
        return "String"

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

        # Load nodes with auto-correction for NODE_ID_MISMATCH
        nodes_data = data.get("nodes", {})
        repaired_count = 0

        for dict_key, node_data in nodes_data.items():
            node_id_field = node_data.get("node_id", dict_key)

            # Auto-repair mismatch (silent)
            if node_id_field != dict_key:
                logger.warning(
                    f"Auto-repaired NODE_ID_MISMATCH: "
                    f"dict_key='{dict_key}' -> node_id='{node_id_field}'"
                )
                # Use dict_key as authoritative (preserves workflow structure)
                node_data["node_id"] = dict_key
                repaired_count += 1

            workflow.nodes[dict_key] = node_data

        if repaired_count > 0:
            logger.info(f"Auto-repaired {repaired_count} node ID mismatches in workflow")

        # Load connections
        for conn_data in data.get("connections", []):
            workflow.connections.append(NodeConnection.from_dict(conn_data))

        # Load frames
        workflow.frames = data.get("frames", [])

        # Load variables and settings
        workflow.variables = data.get("variables", {})
        workflow.settings = data.get("settings", workflow.settings)

        return workflow

    def save_to_file(self, file_path: Path, validate_before_save: bool = False) -> None:
        """
        Save workflow to JSON file using orjson.

        Args:
            file_path: Path to save file
            validate_before_save: If True, validate workflow before saving

        Raises:
            ValueError: If validation fails and validate_before_save is True
        """
        try:
            # Optionally validate before saving
            if validate_before_save:
                result = self.validate_full()
                if not result.is_valid:
                    error_summary = result.format_summary()
                    logger.error(f"Validation failed before save:\n{error_summary}")
                    raise ValueError(f"Cannot save invalid workflow: {result.error_count} error(s)")

            # Update modified timestamp
            self.metadata.update_modified_timestamp()

            # Serialize to JSON using orjson for performance
            json_data = orjson.dumps(
                self.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )

            # Write to file
            file_path.write_bytes(json_data)
            logger.info(f"Workflow saved to {file_path}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            raise

    @classmethod
    def load_from_file(
        cls,
        file_path: Path,
        validate_on_load: bool = False,
        strict: bool = False,
    ) -> "WorkflowSchema":
        """
        Load workflow from JSON file.

        Args:
            file_path: Path to workflow file
            validate_on_load: If True, validate workflow after loading
            strict: If True and validate_on_load is True, raise on validation errors

        Returns:
            WorkflowSchema instance

        Raises:
            ValueError: If strict validation fails
        """
        try:
            # Read file
            json_data = file_path.read_bytes()

            # Parse JSON using orjson
            data = orjson.loads(json_data)

            # Auto-migrate legacy node IDs to UUID format if needed
            from ...utils.id_generator import is_uuid_based_id
            from ...utils.workflow_migration import migrate_workflow_ids, needs_migration

            if needs_migration(data):
                logger.info(f"Migrating legacy node IDs in {file_path}")
                data, _ = migrate_workflow_ids(data)

            # Optionally validate before creating workflow
            if validate_on_load:
                from ...core.validation import validate_workflow
                result = validate_workflow(data)

                if not result.is_valid:
                    error_summary = result.format_summary()
                    logger.warning(f"Workflow validation issues:\n{error_summary}")

                    if strict:
                        raise ValueError(f"Workflow validation failed: {result.error_count} error(s)")
                elif result.warnings:
                    logger.info(f"Workflow loaded with {result.warning_count} warning(s)")

            # Create workflow
            workflow = cls.from_dict(data)
            logger.info(f"Workflow loaded from {file_path}")

            return workflow

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WorkflowSchema(name='{self.metadata.name}', "
            f"nodes={len(self.nodes)}, "
            f"connections={len(self.connections)})"
        )
