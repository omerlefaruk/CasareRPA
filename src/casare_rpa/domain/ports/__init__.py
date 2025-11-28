"""
Domain Layer Port Interfaces.

This package defines protocols and interfaces for port-related functionality.
"""

from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)

__all__ = [
    "DefaultCompatibilityRule",
    "PortShape",
    "PortTypeInfo",
    "PortTypeRegistryProtocol",
    "TypeCompatibilityRule",
]
