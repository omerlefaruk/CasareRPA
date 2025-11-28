"""
Port Type System Infrastructure Adapter (Backward Compatibility).

This module provides backward compatibility for code that imports from
the infrastructure layer. The canonical implementation is now in the
application layer.

Preferred import:
    from casare_rpa.application.services.port_type_service import PortTypeRegistry

Or via domain re-export:
    from casare_rpa.domain.port_type_system import PortTypeRegistry
"""

from typing import Dict, Optional, Set, Tuple

from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)
from casare_rpa.domain.value_objects.types import DataType


class PortTypeRegistry(PortTypeRegistryProtocol):
    """
    Singleton registry for port types with colors, shapes, and compatibility.

    Note: This class is duplicated in application.services.port_type_service.
    Both implementations are kept for backward compatibility during migration.

    Provides centralized access to:
    - Type visual metadata (colors, shapes)
    - Type compatibility checking
    - Type information lookup
    """

    _instance: Optional["PortTypeRegistry"] = None

    TYPE_COLORS: Dict[DataType, Tuple[int, int, int, int]] = {
        DataType.STRING: (255, 193, 7, 255),
        DataType.INTEGER: (76, 175, 80, 255),
        DataType.FLOAT: (139, 195, 74, 255),
        DataType.BOOLEAN: (156, 39, 176, 255),
        DataType.LIST: (255, 152, 0, 255),
        DataType.DICT: (255, 87, 34, 255),
        DataType.ANY: (150, 150, 150, 255),
        DataType.PAGE: (33, 150, 243, 255),
        DataType.BROWSER: (3, 169, 244, 255),
        DataType.ELEMENT: (0, 188, 212, 255),
    }

    EXEC_COLOR: Tuple[int, int, int, int] = (255, 255, 255, 255)

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
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        self._type_info: Dict[DataType, PortTypeInfo] = {}
        self._compatibility_rule: TypeCompatibilityRule = DefaultCompatibilityRule()
        self._register_default_types()

    def _register_default_types(self) -> None:
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
        return self._type_info.get(
            data_type,
            PortTypeInfo(data_type, "Unknown", (150, 150, 150, 255), "circle"),
        )

    def get_type_color(self, data_type: DataType) -> Tuple[int, int, int, int]:
        return self.TYPE_COLORS.get(data_type, (150, 150, 150, 255))

    def get_exec_color(self) -> Tuple[int, int, int, int]:
        return self.EXEC_COLOR

    def get_type_shape(self, data_type: DataType) -> PortShape:
        return self.TYPE_SHAPES.get(data_type, PortShape.CIRCLE)

    def is_compatible(self, source: DataType, target: DataType) -> bool:
        return self._compatibility_rule.is_compatible(source, target)

    def get_incompatibility_reason(
        self, source: DataType, target: DataType
    ) -> Optional[str]:
        return self._compatibility_rule.get_incompatibility_reason(source, target)

    def set_compatibility_rule(self, rule: TypeCompatibilityRule) -> None:
        self._compatibility_rule = rule

    def get_compatible_types(self, source: DataType) -> Set[DataType]:
        compatible: Set[DataType] = set()
        for dt in DataType:
            if self.is_compatible(source, dt):
                compatible.add(dt)
        return compatible


def get_port_type_registry() -> PortTypeRegistry:
    """Get the singleton PortTypeRegistry instance."""
    return PortTypeRegistry()


def is_types_compatible(source: DataType, target: DataType) -> bool:
    """Check if source type can connect to target type."""
    return PortTypeRegistry().is_compatible(source, target)


def get_type_color(data_type: DataType) -> Tuple[int, int, int, int]:
    """Get the RGBA color for a data type."""
    return PortTypeRegistry().get_type_color(data_type)


__all__ = [
    "PortTypeInfo",
    "PortShape",
    "TypeCompatibilityRule",
    "DefaultCompatibilityRule",
    "PortTypeRegistry",
    "get_port_type_registry",
    "is_types_compatible",
    "get_type_color",
]
