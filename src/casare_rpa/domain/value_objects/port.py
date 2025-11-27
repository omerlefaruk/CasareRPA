"""
CasareRPA - Port Value Object

Port is an immutable value object representing a connection point on a node.
"""

from typing import Any, Optional

from .types import DataType, PortDefinition, PortType


class Port:
    """
    Represents a single input or output port on a node.

    This is a value object - once created, its core properties are immutable.
    Only the value can be changed during workflow execution.
    """

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
        # Immutable properties (use private attributes with @property)
        self._name = name
        self._port_type = port_type
        self._data_type = data_type
        self._label = label or name
        self._required = required

        # Mutable state (value can change during execution)
        self.value: Any = None

    @property
    def name(self) -> str:
        """Get port name (immutable)."""
        return self._name

    @property
    def port_type(self) -> PortType:
        """Get port type (immutable)."""
        return self._port_type

    @property
    def data_type(self) -> DataType:
        """Get data type (immutable)."""
        return self._data_type

    @property
    def label(self) -> str:
        """Get display label (immutable)."""
        return self._label

    @property
    def required(self) -> bool:
        """Check if port is required (immutable)."""
        return self._required

    def set_value(self, value: Any) -> None:
        """Set the port's value."""
        self.value = value

    def get_value(self) -> Any:
        """Get the port's value."""
        return self.value

    def to_dict(self) -> PortDefinition:
        """
        Serialize port to dictionary.

        Returns:
            Dictionary representation of the port
        """
        return {
            "name": self.name,
            "port_type": self.port_type.name,
            "data_type": self.data_type.name,
            "label": self.label,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: PortDefinition) -> "Port":
        """
        Create a Port from dictionary representation.

        Args:
            data: Dictionary containing port definition

        Returns:
            Port instance
        """
        return cls(
            name=data["name"],
            port_type=PortType[data["port_type"]],
            data_type=DataType[data["data_type"]],
            label=data.get("label"),
            required=data.get("required", True),
        )

    def __repr__(self) -> str:
        """String representation of port."""
        return (
            f"Port(name={self.name}, type={self.port_type.name}, "
            f"data_type={self.data_type.name}, required={self.required})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Check equality based on immutable properties.

        Args:
            other: Other object to compare

        Returns:
            True if ports have same immutable properties
        """
        if not isinstance(other, Port):
            return False
        return (
            self.name == other.name
            and self.port_type == other.port_type
            and self.data_type == other.data_type
            and self.label == other.label
            and self.required == other.required
        )

    def __hash__(self) -> int:
        """Hash based on immutable properties."""
        return hash((self.name, self.port_type, self.data_type, self.label, self.required))
