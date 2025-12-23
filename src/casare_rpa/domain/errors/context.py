"""
CasareRPA - Error Context and Recovery Decision.

Data classes for capturing error context and recovery decisions.
"""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from casare_rpa.domain.errors.types import (
    ErrorCategory,
    ErrorClassification,
    ErrorSeverity,
    RecoveryAction,
)
from casare_rpa.domain.value_objects.types import ErrorCode, NodeId


@dataclass
class ErrorContext:
    """
    Captures full context of an error occurrence.

    Used for:
    - Error analysis and classification
    - Recovery decision making
    - Logging and reporting
    - Screenshot capture triggers (UI errors)
    """

    exception: Exception
    """The original exception that occurred."""

    node_id: NodeId
    """ID of the node where error occurred."""

    node_type: str
    """Type/class name of the node."""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the error occurred."""

    error_code: ErrorCode | None = None
    """Standardized error code (if classified)."""

    classification: ErrorClassification = ErrorClassification.UNKNOWN
    """Whether error is transient, permanent, or unknown."""

    category: ErrorCategory = ErrorCategory.UNKNOWN
    """High-level error category."""

    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    """Error severity level."""

    message: str = ""
    """Human-readable error message."""

    stack_trace: str = ""
    """Full stack trace."""

    retry_count: int = 0
    """Number of retries already attempted."""

    max_retries: int = 3
    """Maximum retry attempts configured."""

    execution_time_ms: float = 0.0
    """How long the operation ran before failing."""

    node_config: dict[str, Any] = field(default_factory=dict)
    """Node configuration at time of error."""

    variables: dict[str, Any] = field(default_factory=dict)
    """Execution context variables (sanitized)."""

    additional_data: dict[str, Any] = field(default_factory=dict)
    """Extra context data (page URL, element selector, etc.)."""

    screenshot_path: str | None = None
    """Path to error screenshot (if captured)."""

    def __post_init__(self) -> None:
        """Post-initialization to set derived fields."""
        if not self.message:
            self.message = str(self.exception)
        if not self.stack_trace:
            self.stack_trace = traceback.format_exc()
        if self.error_code is None:
            self.error_code = ErrorCode.from_exception(self.exception)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize error context to dictionary.

        Returns:
            Dictionary representation for logging/storage.
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "timestamp": self.timestamp.isoformat(),
            "error_code": self.error_code.name if self.error_code else None,
            "error_code_value": self.error_code.value if self.error_code else None,
            "classification": self.classification.name,
            "category": self.category.name,
            "severity": self.severity.name,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "execution_time_ms": self.execution_time_ms,
            "screenshot_path": self.screenshot_path,
            "additional_data": self.additional_data,
        }

    @property
    def is_retryable(self) -> bool:
        """Check if error is potentially retryable."""
        if self.classification == ErrorClassification.PERMANENT:
            return False
        if self.retry_count >= self.max_retries:
            return False
        if self.error_code and self.error_code.is_retryable:
            return True
        return self.classification == ErrorClassification.TRANSIENT

    @property
    def is_ui_error(self) -> bool:
        """Check if this is a UI-related error (screenshot useful)."""
        return self.category in (ErrorCategory.BROWSER, ErrorCategory.DESKTOP)


@dataclass
class RecoveryDecision:
    """
    Decision from error handler on how to recover.

    Contains the recommended action and parameters for recovery.
    """

    action: RecoveryAction
    """Recommended recovery action."""

    reason: str
    """Human-readable reason for this decision."""

    retry_delay_ms: int = 0
    """Delay before retry (if action is RETRY)."""

    fallback_value: Any = None
    """Value to use (if action is FALLBACK)."""

    compensate_nodes: list[NodeId] = field(default_factory=list)
    """Nodes to run for compensation (if action is COMPENSATE)."""

    escalation_message: str = ""
    """Message for human escalation (if action is ESCALATE)."""

    continue_from_node: NodeId | None = None
    """Node to resume from (if action is SKIP)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional decision metadata."""

    def __repr__(self) -> str:
        """String representation."""
        return f"RecoveryDecision({self.action.name}: {self.reason})"


__all__ = [
    "ErrorContext",
    "RecoveryDecision",
]
