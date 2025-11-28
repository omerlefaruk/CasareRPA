"""
Port Type System Infrastructure Adapter (Backward Compatibility).

This module provides backward compatibility for code that imports from
the infrastructure layer. The canonical implementation is now in the
application layer.

DEPRECATED: Import from application layer instead:
    from casare_rpa.application.services.port_type_service import PortTypeRegistry

Or via domain re-export:
    from casare_rpa.domain.port_type_system import PortTypeRegistry

This module will be removed in v4.0.
"""

import warnings

# Re-export from canonical location (application layer)
from casare_rpa.application.services.port_type_service import (
    PortTypeRegistry,
    get_port_type_registry,
    get_type_color,
    is_types_compatible,
)

# Re-export domain abstractions for backward compat
from casare_rpa.domain.ports.port_type_interfaces import (
    DefaultCompatibilityRule,
    PortShape,
    PortTypeInfo,
    PortTypeRegistryProtocol,
    TypeCompatibilityRule,
)


def __getattr__(name: str):
    """Emit deprecation warning on first access to module attributes."""
    if name in __all__:
        warnings.warn(
            f"Importing {name} from casare_rpa.infrastructure.adapters.port_type_system "
            "is deprecated. Use casare_rpa.application.services.port_type_service or "
            "casare_rpa.domain.port_type_system instead. Will be removed in v4.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[f"_{name}"] if f"_{name}" in globals() else globals().get(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Domain abstractions
    "PortTypeInfo",
    "PortShape",
    "TypeCompatibilityRule",
    "DefaultCompatibilityRule",
    "PortTypeRegistryProtocol",
    # Application implementations
    "PortTypeRegistry",
    "get_port_type_registry",
    "is_types_compatible",
    "get_type_color",
]
