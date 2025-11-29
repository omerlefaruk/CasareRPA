"""
CasareRPA - Domain Error Handling Module

Provides error classification, handler registry, and recovery interfaces.
"""

from .error_handlers import (
    ErrorClassification,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorHandler,
    ErrorHandlerRegistry,
    NodeErrorHandler,
    RecoveryAction,
    RecoveryDecision,
    get_error_handler_registry,
)

__all__ = [
    "ErrorClassification",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "ErrorHandler",
    "ErrorHandlerRegistry",
    "NodeErrorHandler",
    "RecoveryAction",
    "RecoveryDecision",
    "get_error_handler_registry",
]
