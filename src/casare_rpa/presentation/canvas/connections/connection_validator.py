"""
Connection Validator for CasareRPA Canvas.

Provides validation services for port connections with strict type checking.
Follows Single Responsibility Principle - handles only connection validation.

References:
- "Clean Architecture" by Robert C. Martin - Single Responsibility Principle
- "The Design of Everyday Things" by Don Norman - Error Prevention
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional

from casare_rpa.application.services.port_type_service import (
    PortTypeRegistry,
    get_port_type_registry,
)
from casare_rpa.domain.value_objects.types import DataType

if TYPE_CHECKING:
    from ..visual_nodes.base_visual_node import VisualNode


# ============================================================================
# VALIDATION RESULT TYPES
# ============================================================================


class ValidationResult(Enum):
    """Result codes for connection validation."""

    VALID = auto()  # Connection is allowed
    INCOMPATIBLE_TYPES = auto()  # Data types don't match
    EXEC_DATA_MISMATCH = auto()  # Mixing exec and data ports
    SELF_CONNECTION = auto()  # Node connecting to itself
    ALREADY_CONNECTED = auto()  # Connection already exists
    PORT_NOT_FOUND = auto()  # Port doesn't exist on node
    DIRECTION_MISMATCH = auto()  # Input-to-input or output-to-output


@dataclass
class ConnectionValidation:
    """
    Result of a connection validation check.

    Attributes:
        result: The ValidationResult enum value
        is_valid: Quick boolean check for validity
        message: Human-readable description
        source_type: DataType of the source port (if applicable)
        target_type: DataType of the target port (if applicable)
    """

    result: ValidationResult
    is_valid: bool
    message: str
    source_type: DataType | None = None
    target_type: DataType | None = None

    @classmethod
    def valid(
        cls,
        message: str = "Connection valid",
        source_type: DataType | None = None,
        target_type: DataType | None = None,
    ) -> "ConnectionValidation":
        """Create a valid connection result."""
        return cls(
            result=ValidationResult.VALID,
            is_valid=True,
            message=message,
            source_type=source_type,
            target_type=target_type,
        )

    @classmethod
    def invalid(
        cls,
        result: ValidationResult,
        message: str,
        source_type: DataType | None = None,
        target_type: DataType | None = None,
    ) -> "ConnectionValidation":
        """Create an invalid connection result."""
        return cls(
            result=result,
            is_valid=False,
            message=message,
            source_type=source_type,
            target_type=target_type,
        )


# ============================================================================
# CONNECTION VALIDATOR
# ============================================================================


class ConnectionValidator:
    """
    Validates port connections between nodes.

    Implements strict type checking - invalid connections are blocked entirely.
    Uses PortTypeRegistry for type compatibility rules.

    Usage:
        validator = ConnectionValidator()
        result = validator.validate_connection(source_node, "output", target_node, "input")
        if not result.is_valid:
            show_error(result.message)
    """

    def __init__(self) -> None:
        """Initialize validator with type registry."""
        self._registry: PortTypeRegistry = get_port_type_registry()

    def validate_connection(
        self,
        source_node: "VisualNode",
        source_port_name: str,
        target_node: "VisualNode",
        target_port_name: str,
    ) -> ConnectionValidation:
        """
        Validate a proposed connection between two ports.

        Args:
            source_node: The node with the output port
            source_port_name: Name of the output port
            target_node: The node with the input port
            target_port_name: Name of the input port

        Returns:
            ConnectionValidation with result and message
        """
        # Check 1: Self-connection
        if source_node == target_node:
            return ConnectionValidation.invalid(
                ValidationResult.SELF_CONNECTION,
                "Cannot connect a node to itself",
            )

        # Check 2: Get port types
        source_type = self._get_port_type(source_node, source_port_name)
        target_type = self._get_port_type(target_node, target_port_name)

        source_is_exec = self._is_exec_port(source_port_name, source_type)
        target_is_exec = self._is_exec_port(target_port_name, target_type)

        # Check 3: Exec/data port mismatch
        if source_is_exec != target_is_exec:
            return ConnectionValidation.invalid(
                ValidationResult.EXEC_DATA_MISMATCH,
                "Cannot connect execution ports to data ports",
                source_type,
                target_type,
            )

        # Check 4: Exec-to-exec is always valid
        if source_is_exec and target_is_exec:
            return ConnectionValidation.valid(
                "Execution flow connection",
                source_type,
                target_type,
            )

        # Check 5: Data type compatibility
        if source_type is not None and target_type is not None:
            if self._registry.is_compatible(source_type, target_type):
                return ConnectionValidation.valid(
                    f"Compatible: {source_type.name} → {target_type.name}",
                    source_type,
                    target_type,
                )
            else:
                reason = self._registry.get_incompatibility_reason(source_type, target_type)
                return ConnectionValidation.invalid(
                    ValidationResult.INCOMPATIBLE_TYPES,
                    reason or f"Type mismatch: {source_type.name} → {target_type.name}",
                    source_type,
                    target_type,
                )

        # Default: Allow if types are unknown (backward compatibility)
        return ConnectionValidation.valid(
            "Connection allowed (types unknown)",
            source_type,
            target_type,
        )

    def get_compatible_ports(
        self,
        source_node: "VisualNode",
        source_port_name: str,
        target_node: "VisualNode",
    ) -> list[str]:
        """
        Get list of compatible input ports on target node.

        Args:
            source_node: The node with the output port
            source_port_name: Name of the output port
            target_node: The node to find compatible ports on

        Returns:
            List of port names that can accept the connection
        """
        if source_node == target_node:
            return []

        source_type = self._get_port_type(source_node, source_port_name)
        source_is_exec = self._is_exec_port(source_port_name, source_type)

        compatible = []

        for port in target_node.input_ports():
            port_name = port.name()
            target_type = self._get_port_type(target_node, port_name)
            target_is_exec = self._is_exec_port(port_name, target_type)

            # Must match exec/data category
            if source_is_exec != target_is_exec:
                continue

            # Exec ports are always compatible
            if source_is_exec and target_is_exec:
                compatible.append(port_name)
                continue

            # Check type compatibility
            if source_type is not None and target_type is not None:
                if self._registry.is_compatible(source_type, target_type):
                    compatible.append(port_name)
            else:
                # Unknown types default to compatible
                compatible.append(port_name)

        return compatible

    def get_incompatible_ports(
        self,
        source_node: "VisualNode",
        source_port_name: str,
        target_node: "VisualNode",
    ) -> list[str]:
        """
        Get list of incompatible input ports on target node.

        Useful for visual feedback - highlighting ports that can't receive.

        Args:
            source_node: The node with the output port
            source_port_name: Name of the output port
            target_node: The node to find incompatible ports on

        Returns:
            List of port names that cannot accept the connection
        """
        if source_node == target_node:
            return [p.name() for p in target_node.input_ports()]

        source_type = self._get_port_type(source_node, source_port_name)
        source_is_exec = self._is_exec_port(source_port_name, source_type)

        incompatible = []

        for port in target_node.input_ports():
            port_name = port.name()
            target_type = self._get_port_type(target_node, port_name)
            target_is_exec = self._is_exec_port(port_name, target_type)

            # Exec/data mismatch
            if source_is_exec != target_is_exec:
                incompatible.append(port_name)
                continue

            # Check type compatibility
            if source_type is not None and target_type is not None:
                if not self._registry.is_compatible(source_type, target_type):
                    incompatible.append(port_name)

        return incompatible

    def _get_port_type(self, node: "VisualNode", port_name: str) -> DataType | None:
        """
        Get the DataType for a port on a node.

        Args:
            node: The VisualNode to get port type from
            port_name: Name of the port

        Returns:
            DataType if known, None otherwise
        """
        # Check if node has typed port method
        if hasattr(node, "get_port_type"):
            return node.get_port_type(port_name)

        # Fall back to checking underlying CasareRPA node
        casare_node = node.get_casare_node()
        if casare_node:
            # Check input ports
            if port_name in getattr(casare_node, "input_ports", {}):
                port = casare_node.input_ports[port_name]
                return port.data_type if hasattr(port, "data_type") else None
            # Check output ports
            if port_name in getattr(casare_node, "output_ports", {}):
                port = casare_node.output_ports[port_name]
                return port.data_type if hasattr(port, "data_type") else None

        # Type unknown
        return None

    def _is_exec_port(self, port_name: str, data_type: DataType | None) -> bool:
        """
        Check if a port is an execution flow port.

        Args:
            port_name: Name of the port
            data_type: DataType if known (None indicates exec port)

        Returns:
            True if this is an execution port
        """
        # Check if data_type is None - this is how exec ports are marked
        # in the visual node's _port_types dictionary via add_exec_input/add_exec_output
        if data_type is None:
            return True

        # Also check name patterns for exec ports
        port_lower = port_name.lower()

        # Common exec port names
        exec_port_names = {
            "exec_in",
            "exec_out",
            "exec",
            "loop_body",
            "completed",  # Loop node exec outputs
            "true",
            "false",  # If/Branch node exec outputs
            "then",
            "else",  # Alternative if/branch names
            "on_success",
            "on_error",
            "on_finally",  # Error handling
            "body",
            "done",
            "finish",
            "next",  # Other common exec names
        }

        if port_lower in exec_port_names:
            return True

        # Fallback: check if "exec" is in the name
        return "exec" in port_lower


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================


_validator_instance: ConnectionValidator | None = None


def get_connection_validator() -> ConnectionValidator:
    """Get the singleton ConnectionValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ConnectionValidator()
    return _validator_instance


def validate_connection(
    source_node: "VisualNode",
    source_port: str,
    target_node: "VisualNode",
    target_port: str,
) -> ConnectionValidation:
    """
    Validate a connection between two ports.

    Convenience function for quick validation.

    Args:
        source_node: The node with the output port
        source_port: Name of the output port
        target_node: The node with the input port
        target_port: Name of the input port

    Returns:
        ConnectionValidation with result and message
    """
    return get_connection_validator().validate_connection(
        source_node, source_port, target_node, target_port
    )
