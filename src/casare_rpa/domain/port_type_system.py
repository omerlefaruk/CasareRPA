"""
Domain Port Type System Re-export Module.

Re-exports port type system components from infrastructure.adapters.port_type_system.
"""

from casare_rpa.infrastructure.adapters.port_type_system import (
    PortTypeInfo,
    PortShape,
    TypeCompatibilityRule,
    DefaultCompatibilityRule,
    PortTypeRegistry,
    get_port_type_registry,
    is_types_compatible,
    get_type_color,
)

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
