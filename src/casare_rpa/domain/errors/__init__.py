"""
CasareRPA - Domain Error Handling Module

Provides error classification, handler registry, and recovery interfaces.

Module Structure:
- types: Error enumerations (ErrorCategory, ErrorSeverity, etc.)
- context: ErrorContext, RecoveryDecision dataclasses
- handlers/: Error handler base and implementations
- registry: ErrorHandlerRegistry and global functions
- error_handlers: Legacy compatibility module (re-exports all)
"""

# Import from new modular structure
from casare_rpa.domain.errors.types import (
    ErrorCategory,
    ErrorSeverity,
    ErrorClassification,
    RecoveryAction,
)

from casare_rpa.domain.errors.context import (
    ErrorContext,
    RecoveryDecision,
)

from casare_rpa.domain.errors.handlers import (
    ErrorHandler,
    NodeErrorHandler,
)

from casare_rpa.domain.errors.registry import (
    ErrorHandlerRegistry,
    CustomErrorHandlerFunc,
    get_error_handler_registry,
    reset_error_handler_registry,
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
