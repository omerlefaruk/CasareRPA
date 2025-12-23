"""
CasareRPA - Error Handler Registry (Compatibility Module).

.. deprecated:: 3.0
    This module has been split into smaller, focused modules:
    - types.py: Error enumerations (ErrorCategory, ErrorSeverity, etc.)
    - context.py: ErrorContext, RecoveryDecision dataclasses
    - handlers/: Error handler base and implementations
    - registry.py: ErrorHandlerRegistry and global functions

    Import from the new locations for better organization.
    This module re-exports everything for backward compatibility.

Key Features:
- Error classification (Transient, Permanent, Unknown)
- Error handler registry per node type
- Custom error handlers via user-defined logic
- Error aggregation and context capture
- Recovery action recommendations

Architecture:
- Domain layer: Pure error handling logic
- No infrastructure dependencies
"""

# Re-export from new modules for backward compatibility
from casare_rpa.domain.errors.context import (
    ErrorContext,
    RecoveryDecision,
)
from casare_rpa.domain.errors.handlers import (
    ErrorHandler,
    NodeErrorHandler,
)
from casare_rpa.domain.errors.registry import (
    CustomErrorHandlerFunc,
    ErrorHandlerRegistry,
    get_error_handler_registry,
    reset_error_handler_registry,
)
from casare_rpa.domain.errors.types import (
    ErrorCategory,
    ErrorClassification,
    ErrorSeverity,
    RecoveryAction,
)

__all__ = [
    # Enums
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorClassification",
    "RecoveryAction",
    # Data classes
    "ErrorContext",
    "RecoveryDecision",
    # Handlers
    "ErrorHandler",
    "NodeErrorHandler",
    # Registry
    "ErrorHandlerRegistry",
    "CustomErrorHandlerFunc",
    "get_error_handler_registry",
    "reset_error_handler_registry",
]
