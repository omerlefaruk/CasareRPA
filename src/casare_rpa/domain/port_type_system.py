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

# Backwards-compatibility: some callers import the concrete `PortTypeRegistry`
# from this module. The concrete implementation lives in the application layer
# (`application.services.port_type_service`). Provide a lazy runtime alias
# when that implementation is available to avoid import errors in presentation
# code while keeping the domain-focused exports primary.
try:
    # Import lazily to avoid import-time dependency issues when application
    # layer isn't fully initialised (or when using strict domain-only tests).
    from casare_rpa.application.services.port_type_service import (
        PortTypeRegistry,
        get_port_type_registry,
        get_type_color,
        is_types_compatible,
    )

    # Expose compatibility names for older imports
    globals()["PortTypeRegistry"] = PortTypeRegistry
    globals()["get_port_type_registry"] = get_port_type_registry
    globals()["is_types_compatible"] = is_types_compatible
    globals()["get_type_color"] = get_type_color

    __all__.extend(
        [
            "PortTypeRegistry",
            "get_port_type_registry",
            "is_types_compatible",
            "get_type_color",
        ]
    )
except Exception:
    # If application layer isn't importable (e.g., domain-only tests), just
    # keep the protocol-only exports. Import errors are swallowed so that
    # domain tests remain isolated.
    pass
