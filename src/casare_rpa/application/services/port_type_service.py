"""
Port Type Service for CasareRPA.

Application layer service providing port type information, compatibility checking,
and visual metadata to the presentation layer. This follows Clean Architecture
by depending only on domain abstractions.
"""

from typing import Dict, Optional, Set, Tuple

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)


class PortTypeRegistry(PortTypeRegistryProtocol):
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
        compatible: Set[DataType] = set()
        for dt in DataType:
            if self.is_compatible(source, dt):
                compatible.add(dt)
        return compatible


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


__all__ = [
    "PortTypeRegistry",
    "get_port_type_registry",
    "is_types_compatible",
    "get_type_color",
]
