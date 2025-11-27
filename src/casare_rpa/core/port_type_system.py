"""
Port Type System for CasareRPA.

Provides centralized type registry, compatibility rules, and visual metadata
for port types. Follows Clean Architecture principles with dependency inversion.

References:
- "Clean Architecture" by Robert C. Martin - Dependency Inversion Principle
- "Designing Data-Intensive Applications" - Type safety for data flow
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Set, Optional, Tuple, Protocol

from .types import DataType


# ============================================================================
# PORT TYPE METADATA
# ============================================================================


@dataclass(frozen=True)
class PortTypeInfo:
    """
    Immutable metadata for a port data type.

    Attributes:
        data_type: The DataType enum value
        display_name: Human-readable name for UI
        color: RGBA tuple for port visual color
        shape: Shape identifier for accessibility
        description: Tooltip description
    """

    data_type: DataType
    display_name: str
    color: Tuple[int, int, int, int]  # RGBA
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


# ============================================================================
# TYPE COMPATIBILITY RULES
# ============================================================================


class TypeCompatibilityRule(Protocol):
    """Protocol for type compatibility checking (Open/Closed Principle)."""

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        """Check if source type can connect to target type."""
        ...

    def get_incompatibility_reason(
        self, source: DataType, target: DataType
    ) -> Optional[str]:
        """Get human-readable reason why types are incompatible."""
        ...


class DefaultCompatibilityRule:
    """
    Default type compatibility rules.

    Rules:
    1. ANY accepts/provides all types (universal wildcard)
    2. Same types are always compatible
    3. Numeric types (INTEGER, FLOAT) are cross-compatible
    4. All types can connect to STRING (implicit conversion)
    5. LIST/DICT require exact type match
    6. PAGE, BROWSER, ELEMENT require exact type match
    """

    # Types that INTEGER can implicitly convert to
    INTEGER_COMPATIBLE: Set[DataType] = {
        DataType.INTEGER,
        DataType.FLOAT,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that FLOAT can implicitly convert to
    FLOAT_COMPATIBLE: Set[DataType] = {
        DataType.FLOAT,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that BOOLEAN can implicitly convert to
    BOOLEAN_COMPATIBLE: Set[DataType] = {
        DataType.BOOLEAN,
        DataType.STRING,
        DataType.ANY,
    }

    # Types that STRING can implicitly convert to
    STRING_COMPATIBLE: Set[DataType] = {
        DataType.STRING,
        DataType.ANY,
    }

    # Strict types (require exact match or ANY)
    STRICT_TYPES: Set[DataType] = {
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

    def get_incompatibility_reason(
        self, source: DataType, target: DataType
    ) -> Optional[str]:
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
            return (
                f"'{source.name}' requires exact type match. "
                f"Cannot convert to '{target.name}'."
            )

        if target in self.STRICT_TYPES:
            return (
                f"'{target.name}' only accepts '{target.name}' or ANY type. "
                f"Got '{source.name}'."
            )

        return f"Type mismatch: '{source.name}' is not compatible with '{target.name}'."


# ============================================================================
# PORT TYPE REGISTRY (Singleton)
# ============================================================================


class PortTypeRegistry:
    """
    Singleton registry for port types with colors, shapes, and compatibility.

    Provides centralized access to:
    - Type visual metadata (colors, shapes)
    - Type compatibility checking
    - Type information lookup

    Usage:
        registry = PortTypeRegistry()
        color = registry.get_type_color(DataType.STRING)
        is_valid = registry.is_compatible(DataType.INTEGER, DataType.FLOAT)
    """

    _instance: Optional["PortTypeRegistry"] = None

    # Type colors - carefully chosen for visibility on dark background
    # and distinctiveness between types
    TYPE_COLORS: Dict[DataType, Tuple[int, int, int, int]] = {
        DataType.STRING: (255, 193, 7, 255),  # Amber - common type
        DataType.INTEGER: (76, 175, 80, 255),  # Green - numeric
        DataType.FLOAT: (139, 195, 74, 255),  # Light Green - numeric variant
        DataType.BOOLEAN: (156, 39, 176, 255),  # Purple - binary decision
        DataType.LIST: (255, 152, 0, 255),  # Orange - container
        DataType.DICT: (255, 87, 34, 255),  # Deep Orange - complex container
        DataType.ANY: (150, 150, 150, 255),  # Gray - wildcard
        DataType.PAGE: (33, 150, 243, 255),  # Blue - browser page
        DataType.BROWSER: (3, 169, 244, 255),  # Light Blue - browser instance
        DataType.ELEMENT: (0, 188, 212, 255),  # Cyan - web element
    }

    # Execution port color (special case)
    EXEC_COLOR: Tuple[int, int, int, int] = (255, 255, 255, 255)  # White

    # Type shapes for accessibility (color-blind friendly)
    TYPE_SHAPES: Dict[DataType, PortShape] = {
        DataType.STRING: PortShape.CIRCLE,
        DataType.INTEGER: PortShape.CIRCLE,
        DataType.FLOAT: PortShape.CIRCLE,
        DataType.BOOLEAN: PortShape.DIAMOND,
        DataType.LIST: PortShape.SQUARE,
        DataType.DICT: PortShape.HEXAGON,
        DataType.ANY: PortShape.HOLLOW_CIRCLE,
        DataType.PAGE: PortShape.ROUNDED_SQUARE,
        DataType.BROWSER: PortShape.CIRCLE_DOT,
        DataType.ELEMENT: PortShape.PENTAGON,
    }

    def __new__(cls) -> "PortTypeRegistry":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize registry with type info and compatibility rules."""
        self._type_info: Dict[DataType, PortTypeInfo] = {}
        self._compatibility_rule: TypeCompatibilityRule = DefaultCompatibilityRule()
        self._register_default_types()

    def _register_default_types(self) -> None:
        """Register all default data types with their metadata."""
        type_descriptions = {
            DataType.STRING: "Text data (strings)",
            DataType.INTEGER: "Whole numbers",
            DataType.FLOAT: "Decimal numbers",
            DataType.BOOLEAN: "True/False values",
            DataType.LIST: "Array/list of values",
            DataType.DICT: "Dictionary/object",
            DataType.ANY: "Any type (wildcard)",
            DataType.PAGE: "Playwright page object",
            DataType.BROWSER: "Playwright browser instance",
            DataType.ELEMENT: "Web/desktop element reference",
        }

        for dt in DataType:
            self._type_info[dt] = PortTypeInfo(
                data_type=dt,
                display_name=dt.name.capitalize(),
                color=self.TYPE_COLORS.get(dt, (150, 150, 150, 255)),
                shape=self.TYPE_SHAPES.get(dt, PortShape.CIRCLE).name.lower(),
                description=type_descriptions.get(dt, ""),
            )

    def get_type_info(self, data_type: DataType) -> PortTypeInfo:
        """
        Get metadata for a data type.

        Args:
            data_type: The DataType to look up

        Returns:
            PortTypeInfo with color, shape, and description
        """
        return self._type_info.get(
            data_type,
            PortTypeInfo(data_type, "Unknown", (150, 150, 150, 255), "circle"),
        )

    def get_type_color(self, data_type: DataType) -> Tuple[int, int, int, int]:
        """
        Get the RGBA color for a data type.

        Args:
            data_type: The DataType to get color for

        Returns:
            RGBA tuple (r, g, b, a) where each component is 0-255
        """
        return self.TYPE_COLORS.get(data_type, (150, 150, 150, 255))

    def get_exec_color(self) -> Tuple[int, int, int, int]:
        """Get the color for execution ports."""
        return self.EXEC_COLOR

    def get_type_shape(self, data_type: DataType) -> PortShape:
        """
        Get the shape for a data type (for accessibility).

        Args:
            data_type: The DataType to get shape for

        Returns:
            PortShape enum value
        """
        return self.TYPE_SHAPES.get(data_type, PortShape.CIRCLE)

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        """
        Check if source type can connect to target type.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            True if connection is allowed, False otherwise
        """
        return self._compatibility_rule.is_compatible(source, target)

    def get_incompatibility_reason(
        self, source: DataType, target: DataType
    ) -> Optional[str]:
        """
        Get human-readable reason why types are incompatible.

        Args:
            source: The output port's data type
            target: The input port's data type

        Returns:
            Reason string if incompatible, None if compatible
        """
        return self._compatibility_rule.get_incompatibility_reason(source, target)

    def set_compatibility_rule(self, rule: TypeCompatibilityRule) -> None:
        """
        Set a custom compatibility rule (Open/Closed Principle).

        Allows extending type checking without modifying this class.

        Args:
            rule: Object implementing TypeCompatibilityRule protocol
        """
        self._compatibility_rule = rule

    def get_compatible_types(self, source: DataType) -> Set[DataType]:
        """
        Get all types that are compatible with the source type.

        Args:
            source: The source data type

        Returns:
            Set of DataTypes that can receive data from source
        """
        compatible = set()
        for dt in DataType:
            if self.is_compatible(source, dt):
                compatible.add(dt)
        return compatible


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================


def get_port_type_registry() -> PortTypeRegistry:
    """Get the singleton PortTypeRegistry instance."""
    return PortTypeRegistry()


def is_types_compatible(source: DataType, target: DataType) -> bool:
    """
    Check if source type can connect to target type.

    Convenience function for quick type checking.

    Args:
        source: The output port's data type
        target: The input port's data type

    Returns:
        True if connection is allowed, False otherwise
    """
    return PortTypeRegistry().is_compatible(source, target)


def get_type_color(data_type: DataType) -> Tuple[int, int, int, int]:
    """
    Get the RGBA color for a data type.

    Convenience function for quick color lookup.

    Args:
        data_type: The DataType to get color for

    Returns:
        RGBA tuple (r, g, b, a)
    """
    return PortTypeRegistry().get_type_color(data_type)
