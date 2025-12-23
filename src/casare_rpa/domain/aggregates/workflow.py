"""
CasareRPA - Workflow Aggregate

Aggregate root for workflow operations with consistency boundaries.
Follows DDD 2025 patterns: aggregates reference other aggregates by ID only.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.events.workflow_events import (
    NodeAdded,
    NodeConnected,
    NodeDisconnected,
    NodeRemoved,
)
from casare_rpa.domain.value_objects.position import Position
from casare_rpa.domain.value_objects.types import NodeConfig, PortId

# =============================================================================
# VALUE OBJECTS (Workflow-specific)
# =============================================================================


@dataclass(frozen=True)
class WorkflowId:
    """
    Strongly-typed identifier for Workflow aggregate.

    Using a value object instead of raw string prevents ID confusion
    between different entity types.
    """

    value: str

    @classmethod
    def generate(cls) -> "WorkflowId":
        """Generate a new unique workflow ID."""
        return cls(value=f"wf_{uuid4().hex[:12]}")

    @classmethod
    def from_string(cls, value: str) -> "WorkflowId":
        """Create WorkflowId from existing string."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class NodeIdValue:
    """
    Strongly-typed identifier for nodes within a workflow.

    Distinct from NodeId type alias for clarity within aggregate.
    """

    value: str

    @classmethod
    def generate(cls) -> "NodeIdValue":
        """Generate a new unique node ID."""
        return cls(value=f"node_{uuid4().hex[:12]}")

    @classmethod
    def from_string(cls, value: str) -> "NodeIdValue":
        """Create NodeIdValue from existing string."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PortReference:
    """
    Reference to a specific port on a node.

    Value object representing a connection endpoint.
    """

    node_id: str
    port_name: str

    @property
    def full_id(self) -> PortId:
        """Get full port identifier (node_id.port_name)."""
        return f"{self.node_id}.{self.port_name}"


@dataclass(frozen=True)
class Connection:
    """
    Immutable connection between two ports.

    Value object representing data or execution flow between nodes.
    """

    source: PortReference
    target: PortReference

    def to_dict(self) -> dict[str, str]:
        """Serialize connection to dictionary."""
        return {
            "source_node": self.source.node_id,
            "source_port": self.source.port_name,
            "target_node": self.target.node_id,
            "target_port": self.target.port_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Connection":
        """Create Connection from dictionary."""
        return cls(
            source=PortReference(
                node_id=data["source_node"],
                port_name=data["source_port"],
            ),
            target=PortReference(
                node_id=data["target_node"],
                port_name=data["target_port"],
            ),
        )


# =============================================================================
# ENTITIES (Internal to Workflow Aggregate)
# =============================================================================


@dataclass
class WorkflowNode:
    """
    Entity within Workflow aggregate.

    Represents a node instance in a workflow. Not directly accessible
    from outside the aggregate - all access goes through Workflow.

    Note: This is a mutable entity (not frozen) because nodes can be
    configured and moved within the aggregate boundary.
    """

    id: NodeIdValue
    node_type: str
    position: Position
    config: NodeConfig = field(default_factory=dict)

    def move_to(self, new_position: Position) -> None:
        """Move node to a new position."""
        self.position = new_position

    def update_config(self, key: str, value: Any) -> None:
        """Update a configuration value."""
        self.config[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "node_id": str(self.id),
            "node_type": self.node_type,
            "position": self.position.to_dict(),
            "config": self.config,
        }


# =============================================================================
# AGGREGATE ROOT
# =============================================================================


class Workflow:
    """
    Aggregate Root - entry point for all workflow operations.

    All modifications to workflow structure (nodes, connections) must go
    through this aggregate root. This ensures:
    - Consistency within the aggregate boundary
    - Domain events are properly raised
    - Invariants are maintained

    Principles:
    - Reference other aggregates by ID only (not object reference)
    - Raise domain events for cross-aggregate communication
    - Encapsulate all business rules within aggregate
    """

    def __init__(
        self,
        id: WorkflowId,
        name: str,
        description: str = "",
    ) -> None:
        """
        Initialize workflow aggregate.

        Args:
            id: Unique workflow identifier
            name: Workflow display name
            description: Optional description
        """
        self._id = id
        self._name = name
        self._description = description
        self._nodes: dict[str, WorkflowNode] = {}
        self._connections: list[Connection] = []
        self._events: list[DomainEvent] = []
        self._settings: dict[str, Any] = {
            "stop_on_error": True,
            "timeout": 30,
            "retry_count": 0,
        }

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def id(self) -> WorkflowId:
        """Get workflow ID."""
        return self._id

    @property
    def name(self) -> str:
        """Get workflow name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set workflow name."""
        if not value or not value.strip():
            raise ValueError("Workflow name cannot be empty")
        self._name = value.strip()

    @property
    def description(self) -> str:
        """Get workflow description."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """Set workflow description."""
        self._description = value

    @property
    def node_count(self) -> int:
        """Get number of nodes in workflow."""
        return len(self._nodes)

    @property
    def connection_count(self) -> int:
        """Get number of connections in workflow."""
        return len(self._connections)

    @property
    def settings(self) -> dict[str, Any]:
        """Get workflow settings (copy to prevent mutation)."""
        return self._settings.copy()

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(
        self,
        node_type: str,
        position: Position,
        config: NodeConfig | None = None,
        node_id: str | None = None,
    ) -> str:
        """
        Add a node to the workflow.

        Args:
            node_type: Type of node (e.g., "ClickElementNode")
            position: Position to place the node
            config: Optional initial configuration

        Returns:
            ID of the created node

        Raises:
            ValueError: If node_type is empty
        """
        if not node_type:
            raise ValueError("Node type cannot be empty")

        # Generate or use provided ID
        if node_id:
            nid = NodeIdValue.from_string(node_id)
        else:
            nid = NodeIdValue.generate()

        node = WorkflowNode(
            id=nid,
            node_type=node_type,
            position=position,
            config=config or {},
        )

        self._nodes[str(nid)] = node

        # Raise domain event
        self._events.append(
            NodeAdded(
                workflow_id=str(self._id),
                node_id=str(nid),
                node_type=node_type,
                position_x=position.x,
                position_y=position.y,
            )
        )

        return str(nid)

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node and all its connections.

        Args:
            node_id: ID of node to remove

        Raises:
            KeyError: If node doesn't exist
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found in workflow")

        # Remove all connections involving this node
        self._connections = [
            conn
            for conn in self._connections
            if conn.source.node_id != node_id and conn.target.node_id != node_id
        ]

        del self._nodes[node_id]

        self._events.append(
            NodeRemoved(
                workflow_id=str(self._id),
                node_id=node_id,
            )
        )

    def get_node(self, node_id: str) -> WorkflowNode | None:
        """
        Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            WorkflowNode or None if not found
        """
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if node exists in workflow."""
        return node_id in self._nodes

    def get_all_nodes(self) -> list[WorkflowNode]:
        """Get all nodes in the workflow."""
        return list(self._nodes.values())

    def move_node(self, node_id: str, new_position: Position) -> None:
        """
        Move a node to a new position.

        Args:
            node_id: ID of node to move
            new_position: New position

        Raises:
            KeyError: If node doesn't exist
        """
        node = self._nodes.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not found in workflow")
        node.move_to(new_position)

    def update_node_config(self, node_id: str, config: NodeConfig) -> None:
        """
        Update a node's configuration.

        Args:
            node_id: ID of node to update
            config: New configuration values (merged with existing)

        Raises:
            KeyError: If node doesn't exist
        """
        node = self._nodes.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not found in workflow")

        for key, value in config.items():
            node.update_config(key, value)

    # -------------------------------------------------------------------------
    # Connection Operations
    # -------------------------------------------------------------------------

    def connect(
        self,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
    ) -> None:
        """
        Create a connection between two node ports.

        Args:
            source_node: Source node ID
            source_port: Source port name
            target_node: Target node ID
            target_port: Target port name

        Raises:
            ValueError: If validation fails (nodes don't exist, etc.)
        """
        source = PortReference(node_id=source_node, port_name=source_port)
        target = PortReference(node_id=target_node, port_name=target_port)

        self._validate_connection(source, target)

        connection = Connection(source=source, target=target)

        # Check for duplicate
        if connection in self._connections:
            return  # Already exists, no-op

        self._connections.append(connection)

        self._events.append(
            NodeConnected(
                workflow_id=str(self._id),
                source_node=source_node,
                source_port=source_port,
                target_node=target_node,
                target_port=target_port,
            )
        )

    def disconnect(
        self,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
    ) -> None:
        """
        Remove a connection between two node ports.

        Args:
            source_node: Source node ID
            source_port: Source port name
            target_node: Target node ID
            target_port: Target port name
        """
        source = PortReference(node_id=source_node, port_name=source_port)
        target = PortReference(node_id=target_node, port_name=target_port)
        connection = Connection(source=source, target=target)

        if connection in self._connections:
            self._connections.remove(connection)
            self._events.append(
                NodeDisconnected(
                    workflow_id=str(self._id),
                    source_node=source_node,
                    source_port=source_port,
                    target_node=target_node,
                    target_port=target_port,
                )
            )

    def get_connections_from(self, node_id: str) -> list[Connection]:
        """Get all connections originating from a node."""
        return [c for c in self._connections if c.source.node_id == node_id]

    def get_connections_to(self, node_id: str) -> list[Connection]:
        """Get all connections targeting a node."""
        return [c for c in self._connections if c.target.node_id == node_id]

    def get_all_connections(self) -> list[Connection]:
        """Get all connections in the workflow."""
        return self._connections.copy()

    def _validate_connection(self, source: PortReference, target: PortReference) -> None:
        """
        Validate a connection before creating it.

        Args:
            source: Source port reference
            target: Target port reference

        Raises:
            ValueError: If validation fails
        """
        # Check source node exists
        if source.node_id not in self._nodes:
            raise ValueError(f"Source node {source.node_id} not found")

        # Check target node exists
        if target.node_id not in self._nodes:
            raise ValueError(f"Target node {target.node_id} not found")

        # Prevent self-connections
        if source.node_id == target.node_id:
            raise ValueError("Cannot connect node to itself")

    # -------------------------------------------------------------------------
    # Event Collection
    # -------------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """
        Collect and clear pending domain events.

        Call this after persisting the aggregate to publish events.

        Returns:
            List of domain events that were raised
        """
        events = self._events[:]
        self._events.clear()
        return events

    def has_pending_events(self) -> bool:
        """Check if there are pending domain events."""
        return len(self._events) > 0

    # -------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------

    def update_settings(self, settings: dict[str, Any]) -> None:
        """Update workflow settings."""
        self._settings.update(settings)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize workflow to dictionary.

        Returns:
            Complete workflow data structure
        """
        return {
            "id": str(self._id),
            "name": self._name,
            "description": self._description,
            "nodes": {node_id: node.to_dict() for node_id, node in self._nodes.items()},
            "connections": [conn.to_dict() for conn in self._connections],
            "settings": self._settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        """
        Create Workflow from dictionary.

        Args:
            data: Serialized workflow data

        Returns:
            Workflow instance
        """
        workflow = cls(
            id=WorkflowId.from_string(data.get("id", f"wf_{uuid4().hex[:12]}")),
            name=data.get("name", "Untitled Workflow"),
            description=data.get("description", ""),
        )

        # Load settings
        if "settings" in data:
            workflow._settings.update(data["settings"])

        # Load nodes
        for node_id, node_data in data.get("nodes", {}).items():
            position = Position.from_dict(node_data.get("position", [0, 0]))
            workflow.add_node(
                node_type=node_data.get("node_type", ""),
                position=position,
                config=node_data.get("config", {}),
                node_id=node_id,
            )

        # Clear events from loading (we don't want to replay load events)
        workflow._events.clear()

        # Load connections
        for conn_data in data.get("connections", []):
            workflow.connect(
                source_node=conn_data["source_node"],
                source_port=conn_data["source_port"],
                target_node=conn_data["target_node"],
                target_port=conn_data["target_port"],
            )

        # Clear events again after connections
        workflow._events.clear()

        return workflow

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Workflow(id={self._id}, name='{self._name}', "
            f"nodes={self.node_count}, connections={self.connection_count})"
        )


__all__ = [
    # Value Objects
    "WorkflowId",
    "NodeIdValue",
    "PortReference",
    "Connection",
    # Events
    "NodeAdded",
    "NodeRemoved",
    "NodeConnected",
    "NodeDisconnected",
    # Entities
    "WorkflowNode",
    # Aggregate Root
    "Workflow",
]
