"""
CasareRPA - Domain Exception Hierarchy

Structured exception classes with context for debugging and error recovery.
All exceptions extend DomainError which provides:
- Structured error context (component, operation, details)
- Original error preservation for stack traces
- Consistent message formatting

Usage:
    from casare_rpa.domain.errors.exceptions import (
        NodeExecutionError,
        ValidationError,
        ResourceError,
        ErrorContext,
    )

    # In node execution:
    raise NodeExecutionError(
        message="Element not found",
        node_id=self.node_id,
        node_type=self.node_type,
        context=ErrorContext(
            component="BrowserNode",
            operation="click_element",
            details={"selector": selector, "timeout_ms": 5000}
        )
    )

Design Pattern: Exception Hierarchy
- DomainError: Base for all domain exceptions
- Layer-specific errors: NodeExecutionError, ValidationError, etc.
- ErrorContext: Structured debugging information
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ErrorContext:
    """
    Structured context for debugging errors.

    Captures where and how an error occurred to aid in debugging
    and provide meaningful error messages to users.

    Attributes:
        component: The component/class where error occurred (e.g., "BrowserNode")
        operation: The operation being performed (e.g., "click_element")
        details: Additional context as key-value pairs

    Example:
        ErrorContext(
            component="GmailSendNode",
            operation="send_email",
            details={
                "recipient": "user@example.com",
                "subject": "Test",
                "credential_id": "gmail_oauth"
            }
        )
    """

    component: str
    operation: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "component": self.component,
            "operation": self.operation,
            "details": self.details,
        }

    def __str__(self) -> str:
        """Human-readable context string."""
        details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
        if details_str:
            return f"{self.component}.{self.operation}({details_str})"
        return f"{self.component}.{self.operation}()"


@dataclass
class DomainError(Exception):
    """
    Base exception for all domain-layer errors.

    Provides structured error information with context preservation.
    All domain exceptions should extend this class.

    Attributes:
        message: Human-readable error description
        context: Structured debugging context (optional)
        original_error: The underlying exception if wrapping another error

    Example:
        try:
            result = external_api.call()
        except APIError as e:
            raise DomainError(
                message="API call failed",
                original_error=e,
                context=ErrorContext(...)
            )
    """

    message: str
    context: ErrorContext | None = None
    original_error: Exception | None = None

    def __post_init__(self) -> None:
        """Initialize Exception base class with message."""
        super().__init__(self.message)

    def __str__(self) -> str:
        """Format error message with context."""
        parts = [self.message]
        if self.context:
            parts.append(f"[{self.context}]")
        if self.original_error:
            parts.append(f"(caused by: {type(self.original_error).__name__})")
        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dictionary for logging/API responses."""
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "context": self.context.to_dict() if self.context else None,
            "original_error": str(self.original_error) if self.original_error else None,
        }


# ============================================================================
# Node Execution Errors
# ============================================================================


@dataclass
class NodeExecutionError(DomainError):
    """
    Error during node execution.

    Raised when a node fails to execute its logic.
    Includes node identification for debugging.

    Attributes:
        node_id: The ID of the failed node
        node_type: The type/class of the failed node
        error_code: Optional error code for categorization

    Example:
        raise NodeExecutionError(
            message="Failed to click element",
            node_id="node_abc123",
            node_type="ClickElementNode",
            error_code="ELEMENT_NOT_FOUND",
            context=ErrorContext(...)
        )
    """

    node_id: str = ""
    node_type: str = ""
    error_code: str = ""

    def __str__(self) -> str:
        """Format with node info."""
        base = super().__str__()
        if self.node_id:
            return f"[{self.node_type}:{self.node_id}] {base}"
        return base

    def to_dict(self) -> dict[str, Any]:
        """Include node info in serialization."""
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "node_type": self.node_type,
                "error_code": self.error_code,
            }
        )
        return result


@dataclass
class NodeTimeoutError(NodeExecutionError):
    """
    Node execution timed out.

    Attributes:
        timeout_ms: The timeout that was exceeded
    """

    timeout_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["timeout_ms"] = self.timeout_ms
        return result


@dataclass
class NodeValidationError(NodeExecutionError):
    """
    Node validation failed before execution.

    Attributes:
        invalid_ports: List of port names that failed validation
    """

    invalid_ports: list = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["invalid_ports"] = self.invalid_ports
        return result


# ============================================================================
# Validation Errors
# ============================================================================


@dataclass
class ValidationError(DomainError):
    """
    General validation failure.

    Used for schema validation, type checking, constraint violations.

    Attributes:
        field: The field that failed validation
        constraint: The constraint that was violated
        received_value: The invalid value (optional, for debugging)
    """

    field: str = ""
    constraint: str = ""
    received_value: Any = None

    def __str__(self) -> str:
        base = super().__str__()
        if self.field:
            return f"Validation failed for '{self.field}': {base}"
        return base

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "field": self.field,
                "constraint": self.constraint,
                "received_value": repr(self.received_value) if self.received_value else None,
            }
        )
        return result


@dataclass
class ConfigurationError(ValidationError):
    """Invalid configuration detected."""

    config_key: str = ""


@dataclass
class SchemaError(ValidationError):
    """Schema validation failed (e.g., workflow JSON schema)."""

    schema_version: str = ""
    expected_version: str = ""


# ============================================================================
# Resource Errors
# ============================================================================


@dataclass
class ResourceError(DomainError):
    """
    External resource failure.

    For file system, network, database, API errors.

    Attributes:
        resource_type: Type of resource (file, network, database, api)
        resource_id: Identifier for the resource (path, URL, connection string)
        is_retryable: Whether the operation might succeed on retry
    """

    resource_type: str = ""
    resource_id: str = ""
    is_retryable: bool = False

    def __str__(self) -> str:
        base = super().__str__()
        if self.resource_type:
            return f"[{self.resource_type}] {base}"
        return base

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
                "is_retryable": self.is_retryable,
            }
        )
        return result


@dataclass
class FileSystemError(ResourceError):
    """File system operation failed."""

    path: str = ""

    def __post_init__(self) -> None:
        self.resource_type = "file"
        self.resource_id = self.path
        super().__post_init__()


@dataclass
class NetworkError(ResourceError):
    """Network operation failed."""

    url: str = ""
    status_code: int = 0

    def __post_init__(self) -> None:
        self.resource_type = "network"
        self.resource_id = self.url
        self.is_retryable = self.status_code >= 500  # Server errors are retryable
        super().__post_init__()


@dataclass
class DatabaseError(ResourceError):
    """Database operation failed."""

    query: str = ""

    def __post_init__(self) -> None:
        self.resource_type = "database"
        super().__post_init__()


@dataclass
class APIError(ResourceError):
    """External API call failed."""

    api_name: str = ""
    endpoint: str = ""
    response_body: str = ""

    def __post_init__(self) -> None:
        self.resource_type = "api"
        self.resource_id = f"{self.api_name}:{self.endpoint}"
        super().__post_init__()


# ============================================================================
# Authentication/Authorization Errors
# ============================================================================


@dataclass
class AuthenticationError(DomainError):
    """Authentication failed."""

    credential_id: str = ""
    auth_method: str = ""  # oauth, api_key, basic, etc.


@dataclass
class AuthorizationError(DomainError):
    """Authorization/permission denied."""

    required_permission: str = ""
    resource: str = ""


# ============================================================================
# Workflow Errors
# ============================================================================


@dataclass
class WorkflowError(DomainError):
    """Workflow-level error."""

    workflow_id: str = ""
    workflow_name: str = ""


@dataclass
class WorkflowValidationError(WorkflowError):
    """Workflow structure is invalid."""

    validation_errors: list = field(default_factory=list)


@dataclass
class WorkflowExecutionError(WorkflowError):
    """Workflow execution failed."""

    failed_node_id: str = ""
    execution_state: str = ""


# ============================================================================
# Utility Functions
# ============================================================================


def wrap_exception(
    error: Exception,
    error_class: type[DomainError] = DomainError,
    context: ErrorContext | None = None,
    **kwargs: Any,
) -> DomainError:
    """
    Wrap a generic exception in a domain error.

    Preserves the original exception for stack trace.

    Args:
        error: The exception to wrap
        error_class: The domain error class to use
        context: Optional error context
        **kwargs: Additional fields for the error class

    Returns:
        A domain error wrapping the original exception
    """
    return error_class(
        message=str(error),
        context=context,
        original_error=error,
        **kwargs,
    )
