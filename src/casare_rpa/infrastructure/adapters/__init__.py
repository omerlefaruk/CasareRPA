"""
CasareRPA Infrastructure Adapters

Adapters for external libraries and services.

Note: port_type_system is deprecated. Import from:
    casare_rpa.application.services.port_type_service
    casare_rpa.domain.port_type_system
"""

from .port_type_system import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistry,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
    get_port_type_registry,
    get_type_color,
    is_types_compatible,
)

__all__ = [
    "DefaultCompatibilityRule",
    "PortShape",
    "PortTypeInfo",
    "PortTypeRegistry",
    "PortTypeRegistryProtocol",
    "TypeCompatibilityRule",
    "get_port_type_registry",
    "get_type_color",
    "is_types_compatible",
]
