"""
Domain Port Type System Module.

Re-exports port type system components following Clean Architecture:
- Domain abstractions from domain.ports.port_type_interfaces
- Service implementation from application.services.port_type_service

This module provides a unified import point for port type functionality.
"""

from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)

# Import service implementation from application layer
from casare_rpa.application.services.port_type_service import (
    PortTypeRegistry,
    get_port_type_registry,
    get_type_color,
    is_types_compatible,
)

__all__ = [
    # Domain layer abstractions
    "PortTypeInfo",
    "PortShape",
    "TypeCompatibilityRule",
    "DefaultCompatibilityRule",
    "PortTypeRegistryProtocol",
    # Application layer implementations
    "PortTypeRegistry",
    "get_port_type_registry",
    "is_types_compatible",
    "get_type_color",
]
