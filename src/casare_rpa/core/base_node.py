"""
CasareRPA - Base Node Abstract Class
All automation nodes must inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from loguru import logger

from .types import (
    DataType,
    ExecutionResult,
    NodeConfig,
    NodeId,
    NodeStatus,
    PortDefinition,
    PortType,
    SerializedNode,
)


class Port:
    """Represents a single input or output port on a node."""

    def __init__(
        self,
        name: str,
        port_type: PortType,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = True,
    ) -> None:
        """
        Initialize a port.

        Args:
            name: Unique port identifier within the node
            port_type: Type of port (INPUT, OUTPUT, etc.)
            data_type: Data type this port accepts/provides
            label: Display label (defaults to name)
            required: Whether this port must be connected
        """
        self.name = name
        self.port_type = port_type
        self.data_type = data_type
        self.label = label or name
        self.required = required
        self.value: Any = None

    def set_value(self, value: Any) -> None:
        """Set the port's value."""
        self.value = value

    def get_value(self) -> Any:
        """Get the port's value."""
        return self.value

    def to_dict(self) -> PortDefinition:
        """Serialize port to dictionary."""
        return {
            "name": self.name,
            "port_type": self.port_type.name,
            "data_type": self.data_type.name,
            "label": self.label,
            "required": self.required,
        }


class BaseNode(ABC):
    """
    Abstract base class for all automation nodes.
    
    All nodes must implement:
    - execute(): Core execution logic
    - validate(): Input validation
    - _define_ports(): Port definitions
    """

    def __init__(self, node_id: NodeId, config: Optional[NodeConfig] = None) -> None:
        """
        Initialize base node.

        Args:
            node_id: Unique identifier for this node instance
            config: Node configuration dictionary
        """
        self.node_id = node_id
        self.config = config or {}
        self.status = NodeStatus.IDLE
        self.error_message: Optional[str] = None

        # Ports
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, Port] = {}

        # Metadata
        self.node_type = self.__class__.__name__
        self.category = "General"
        self.description = self.__class__.__doc__ or "No description"

        # Initialize ports
        self._define_ports()

    @abstractmethod
    def _define_ports(self) -> None:
        """
        Define the input and output ports for this node.
        Must be implemented by subclasses.
        
        Example:
            self.add_input_port("url", DataType.STRING, "URL to navigate")
            self.add_output_port("page", DataType.PAGE, "Loaded page")
        """
        pass

    @abstractmethod
    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute the node's main logic.

        Args:
            context: Execution context containing runtime state

        Returns:
            Dictionary of output port values, or None

        Raises:
            Exception: If execution fails
        """
        pass

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate node configuration and inputs.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required input ports have values
        for port in self.input_ports.values():
            if port.required and port.value is None:
                return False, f"Required input port '{port.name}' has no value"

        # Validate configuration
        validation_result = self._validate_config()
        if not validation_result[0]:
            return validation_result

        return True, None

    def _validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate node-specific configuration.
        Override in subclasses for custom validation.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def add_input_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = True,
    ) -> None:
        """Add an input port to the node."""
        port = Port(name, PortType.INPUT, data_type, label, required)
        self.input_ports[name] = port

    def add_output_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = False,
    ) -> None:
        """Add an output port to the node."""
        port = Port(name, PortType.OUTPUT, data_type, label, required)
        self.output_ports[name] = port

    def set_input_value(self, port_name: str, value: Any) -> None:
        """Set the value of an input port."""
        if port_name not in self.input_ports:
            raise ValueError(f"Input port '{port_name}' does not exist on {self.node_type}")
        self.input_ports[port_name].set_value(value)

    def get_input_value(self, port_name: str, default: Any = None) -> Any:
        """Get the value of an input port."""
        if port_name not in self.input_ports:
            return default
        return self.input_ports[port_name].get_value()

    def set_output_value(self, port_name: str, value: Any) -> None:
        """Set the value of an output port."""
        if port_name not in self.output_ports:
            raise ValueError(f"Output port '{port_name}' does not exist on {self.node_type}")
        self.output_ports[port_name].set_value(value)

    def get_output_value(self, port_name: str, default: Any = None) -> Any:
        """Get the value of an output port."""
        if port_name not in self.output_ports:
            return default
        return self.output_ports[port_name].get_value()

    def serialize(self) -> SerializedNode:
        """
        Serialize node to dictionary for saving workflows.

        Returns:
            Dictionary containing node data
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "category": self.category,
            "config": self.config,
            "input_ports": {name: port.to_dict() for name, port in self.input_ports.items()},
            "output_ports": {name: port.to_dict() for name, port in self.output_ports.items()},
        }

    @classmethod
    def deserialize(cls, data: SerializedNode) -> "BaseNode":
        """
        Create a node instance from serialized data.

        Args:
            data: Serialized node dictionary

        Returns:
            Node instance
        """
        node_id = data["node_id"]
        config = data.get("config", {})
        return cls(node_id, config)

    def set_status(self, status: NodeStatus, error_message: Optional[str] = None) -> None:
        """Update node status."""
        self.status = status
        self.error_message = error_message
        logger.debug(f"Node {self.node_id} ({self.node_type}) status: {status.name}")

    def get_status(self) -> NodeStatus:
        """Get current node status."""
        return self.status

    def reset(self) -> None:
        """Reset node to initial state."""
        self.status = NodeStatus.IDLE
        self.error_message = None
        for port in self.input_ports.values():
            port.value = None
        for port in self.output_ports.values():
            port.value = None

    def __repr__(self) -> str:
        """String representation of node."""
        return f"{self.node_type}(id={self.node_id}, status={self.status.name})"
