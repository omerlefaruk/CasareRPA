"""
CasareRPA - Domain Entity: Node Connection
Represents a connection between two node ports in a workflow.
"""

from typing import Dict

from casare_rpa.domain.value_objects.types import NodeId, PortId


class NodeConnection:
    """
    Represents a connection between two node ports.

    A connection links the output of one node to the input of another,
    defining the flow of data or execution control in a workflow.
    """

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
        self._source_node = source_node
        self._source_port = source_port
        self._target_node = target_node
        self._target_port = target_port

    @property
    def source_node(self) -> NodeId:
        """Get the source node ID."""
        return self._source_node

    @property
    def source_port(self) -> str:
        """Get the source port name."""
        return self._source_port

    @property
    def target_node(self) -> NodeId:
        """Get the target node ID."""
        return self._target_node

    @property
    def target_port(self) -> str:
        """Get the target port name."""
        return self._target_port

    @property
    def source_id(self) -> PortId:
        """Get full source port ID (node_id.port_name)."""
        return f"{self._source_node}.{self._source_port}"

    @property
    def target_id(self) -> PortId:
        """Get full target port ID (node_id.port_name)."""
        return f"{self._target_node}.{self._target_port}"

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize connection to dictionary.

        Returns:
            Dictionary with connection data
        """
        return {
            "source_node": self._source_node,
            "source_port": self._source_port,
            "target_node": self._target_node,
            "target_port": self._target_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "NodeConnection":
        """
        Create connection from dictionary.

        Args:
            data: Dictionary containing connection data

        Returns:
            NodeConnection instance
        """
        return cls(
            source_node=data["source_node"],
            source_port=data["source_port"],
            target_node=data["target_node"],
            target_port=data["target_port"],
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"NodeConnection({self.source_id} -> {self.target_id})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on connection endpoints."""
        if not isinstance(other, NodeConnection):
            return False
        return (
            self._source_node == other._source_node
            and self._source_port == other._source_port
            and self._target_node == other._target_node
            and self._target_port == other._target_port
        )

    def __hash__(self) -> int:
        """Hash based on connection endpoints."""
        return hash((self._source_node, self._source_port, self._target_node, self._target_port))
