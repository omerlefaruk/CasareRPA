"""
Domain Port Type System Module.

Exports ONLY domain abstractions following Clean Architecture.
Domain layer must have ZERO dependencies on application/infrastructure.

For implementation (PortTypeRegistry, get_port_type_registry, etc.),
import from: casare_rpa.application.services.port_type_service
"""

from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)

__all__ = [
    # Domain layer abstractions ONLY
    "PortTypeInfo",
    "PortShape",
    "TypeCompatibilityRule",
    "DefaultCompatibilityRule",
    "PortTypeRegistryProtocol",
]
