"""
Domain Layer Port Type Interfaces.

This module defines protocols and value objects for the port type system.
These are pure domain concepts with no external dependencies.

The actual implementation (colors, shapes, registry) lives in the
infrastructure layer (infrastructure.adapters.port_type_system).
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from casare_rpa.domain.value_objects.types import DataType


@dataclass(frozen=True)
class PortTypeInfo:
    """
    Immutable metadata for a port data type.

    This is a domain value object describing port visual characteristics.

    Attributes:
        data_type: The DataType enum value
        display_name: Human-readable name for UI
        color: RGBA tuple for port visual color
        shape: Shape identifier for accessibility
        description: Tooltip description
    """

    data_type: DataType
    display_name: str
    color: tuple[int, int, int, int]  # RGBA
    shape: str  # circle, diamond, square, hexagon, triangle, hollow_circle
    description: str = ""


class PortShape(Enum):
    """Shape types for port rendering (accessibility feature)."""

    CIRCLE = auto()  # Default for most types
    DIAMOND = auto()  # Boolean
    SQUARE = auto()  # List/Array
    HEXAGON = auto()  # Dict/Object
    TRIANGLE = auto()  # Execution flow
    HOLLOW_CIRCLE = auto()  # ANY/wildcard
    ROUNDED_SQUARE = auto()  # Page
    CIRCLE_DOT = auto()  # Browser
    PENTAGON = auto()  # Element


class TypeCompatibilityRule(Protocol):
    """
    Protocol for type compatibility checking.

    Implementations define rules for which port types can connect.
    This follows the Open/Closed Principle - new rules can be added
    without modifying existing code.
    """

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        """
        Check if source type can connect to target type.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            True if connection is allowed, False otherwise
        """
        ...

    def get_incompatibility_reason(self, source: DataType, target: DataType) -> str | None:
        """
        Get human-readable reason why types are incompatible.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            Reason string if incompatible, None if compatible
        """
        ...


class PortTypeRegistryProtocol(Protocol):
    """
    Protocol for port type registry.

    Defines the interface that infrastructure implementations must provide.
    Enables dependency inversion - domain code depends on this abstraction,
    not the concrete registry implementation.
    """

    def get_type_info(self, data_type: DataType) -> PortTypeInfo:
        """Get metadata for a data type."""
        ...

    def get_type_color(self, data_type: DataType) -> tuple[int, int, int, int]:
        """Get the RGBA color for a data type."""
        ...

    def get_exec_color(self) -> tuple[int, int, int, int]:
        """Get the color for execution ports."""
        ...

    def get_type_shape(self, data_type: DataType) -> PortShape:
        """Get the shape for a data type (for accessibility)."""
        ...

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        """Check if source type can connect to target type."""
        ...

    def get_incompatibility_reason(self, source: DataType, target: DataType) -> str | None:
        """Get reason why types are incompatible."""
        ...

    def get_compatible_types(self, source: DataType) -> set[DataType]:
        """Get all types that are compatible with the source type."""
        ...


class DefaultCompatibilityRule:
    """
    Default type compatibility rules.

    This is a domain service that defines the business rules for
    port type compatibility. It has no external dependencies.

    Rules:
    1. ANY accepts/provides all types (universal wildcard)
    2. Same types are always compatible
    3. Numeric types (INTEGER, FLOAT) are cross-compatible
    4. All types can connect to STRING (implicit conversion)
    5. LIST/DICT require exact type match
    6. PAGE, BROWSER, ELEMENT require exact type match
    """

    # Types that INTEGER can implicitly convert to
    INTEGER_COMPATIBLE: set[DataType] = {
        DataType.INTEGER,
        DataType.FLOAT,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that FLOAT can implicitly convert to
    FLOAT_COMPATIBLE: set[DataType] = {
        DataType.FLOAT,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that BOOLEAN can implicitly convert to
    BOOLEAN_COMPATIBLE: set[DataType] = {
        DataType.BOOLEAN,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that STRING can implicitly convert to
    STRING_COMPATIBLE: set[DataType] = {
        DataType.STRING,
        DataType.ANY,
    }

    # Strict types (require exact match or ANY)
    STRICT_TYPES: set[DataType] = {
        DataType.PAGE,
        DataType.BROWSER,
        DataType.ELEMENT,
        DataType.LIST,
        DataType.DICT,
    }

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        """
        Check if source type can connect to target type.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            True if connection is allowed, False otherwise
        """
        # Rule 1: ANY accepts/provides all types
        if source == DataType.ANY or target == DataType.ANY:
            return True

        # Rule 2: Same type always compatible
        if source == target:
            return True

        # Rule 3: Numeric cross-compatibility
        if source == DataType.INTEGER:
            return target in self.INTEGER_COMPATIBLE

        if source == DataType.FLOAT:
            return target in self.FLOAT_COMPATIBLE

        # Rule 4: Boolean to compatible types
        if source == DataType.BOOLEAN:
            return target in self.BOOLEAN_COMPATIBLE

        # Rule 5: String to compatible types
        if source == DataType.STRING:
            return target in self.STRING_COMPATIBLE

        # Rule 6: Strict types require exact match
        if source in self.STRICT_TYPES:
            return target == source or target == DataType.ANY

        # Default: incompatible
        return False

    def get_incompatibility_reason(self, source: DataType, target: DataType) -> str | None:
        """
        Get human-readable reason why types are incompatible.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            Reason string if incompatible, None if compatible
        """
        if self.is_compatible(source, target):
            return None

        # Provide helpful error messages
        if source in self.STRICT_TYPES:
            return f"'{source.name}' requires exact type match. Cannot convert to '{target.name}'."

        if target in self.STRICT_TYPES:
            return f"'{target.name}' only accepts '{target.name}' or ANY type. Got '{source.name}'."

        return f"Type mismatch: '{source.name}' is not compatible with '{target.name}'."
