"""
CasareRPA - Domain Error Handling Module

Provides error classification, handler registry, recovery interfaces,
and Result<T,E> pattern for explicit error handling.

Entry Points:
    - Result, Ok, Err: Rust-style result types for explicit error handling
    - DomainError, NodeExecutionError, etc.: Structured exception hierarchy
    - ErrorHandlerRegistry: Error handler registration and dispatch

Module Structure:
    - result: Result<T,E> type system (Ok, Err, Result)
    - exceptions: Domain exception hierarchy (DomainError, NodeExecutionError, etc.)
    - types: Error enumerations (ErrorCategory, ErrorSeverity, etc.)
    - context: ErrorContext, RecoveryDecision dataclasses
    - handlers/: Error handler base and implementations
    - registry: ErrorHandlerRegistry and global functions

Usage:
    from casare_rpa.domain.errors import Result, Ok, Err, NodeExecutionError

    def get_element(selector: str) -> Result[Element, NodeExecutionError]:
        try:
            element = page.query_selector(selector)
            if element is None:
                return Err(NodeExecutionError("Not found", node_id=self.node_id))
            return Ok(element)
        except Exception as e:
            return Err(NodeExecutionError(str(e), original_error=e))

Related:
    - See domain/errors/result.py for Result type documentation
    - See domain/errors/exceptions.py for exception hierarchy
"""

# Result type system (Rust-style)
from casare_rpa.domain.errors.context import (
    ErrorContext,
    RecoveryDecision,
)
from casare_rpa.domain.errors.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    DomainError,
    FileSystemError,
    NetworkError,
    NodeExecutionError,
    NodeTimeoutError,
    NodeValidationError,
    ResourceError,
    SchemaError,
    ValidationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowValidationError,
    wrap_exception,
)

# Exception hierarchy
from casare_rpa.domain.errors.exceptions import (
    ErrorContext as StructuredErrorContext,
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
from casare_rpa.domain.errors.result import (
    Err,
    Ok,
    Result,
    collect_results,
    is_err,
    is_ok,
    unwrap_or_default,
)

# Import from existing modular structure
from casare_rpa.domain.errors.types import (
    ErrorCategory,
    ErrorClassification,
    ErrorSeverity,
    RecoveryAction,
)

__all__ = [
    # Result types (NEW)
    "Result",
    "Ok",
    "Err",
    "is_ok",
    "is_err",
    "unwrap_or_default",
    "collect_results",
    # Exception hierarchy (NEW)
    "StructuredErrorContext",
    "DomainError",
    "NodeExecutionError",
    "NodeTimeoutError",
    "NodeValidationError",
    "ValidationError",
    "ConfigurationError",
    "SchemaError",
    "ResourceError",
    "FileSystemError",
    "NetworkError",
    "DatabaseError",
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "wrap_exception",
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
