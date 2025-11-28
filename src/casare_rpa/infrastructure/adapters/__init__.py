"""
CasareRPA Infrastructure Adapters

Adapters for external libraries and services.
"""

from .port_type_system import (
    PortTypeRegistry,
    PortTypeInfo,
    PortShape,
    TypeCompatibilityRule,
    DefaultCompatibilityRule,
    get_port_type_registry,
    is_types_compatible,
    get_type_color,
)

__all__ = [
    "PortTypeRegistry",
    "PortTypeInfo",
    "PortShape",
    "TypeCompatibilityRule",
    "DefaultCompatibilityRule",
    "get_port_type_registry",
    "is_types_compatible",
    "get_type_color",
]
