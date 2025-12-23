"""
CasareRPA - Node Error Handler.

Default error handler for node execution errors.
"""

import random
from typing import List, Optional

from casare_rpa.domain.value_objects.types import ErrorCode

from casare_rpa.domain.errors.context import ErrorContext, RecoveryDecision
from casare_rpa.domain.errors.types import (
    ErrorCategory,
    ErrorClassification,
    ErrorSeverity,
    RecoveryAction,
)
from casare_rpa.domain.errors.handlers.base import ErrorHandler


class NodeErrorHandler(ErrorHandler):
    """
    Default error handler for node execution errors.

    Provides baseline error classification and recovery for all nodes.
    Can be extended for node-type-specific handling.
    """

    def __init__(
        self,
        node_types: Optional[List[str]] = None,
        default_max_retries: int = 3,
        retry_on_transient: bool = True,
    ) -> None:
        """
        Initialize node error handler.

        Args:
            node_types: List of node type names this handler applies to.
                       None means all node types.
            default_max_retries: Default max retry attempts.
            retry_on_transient: Whether to recommend retry for transient errors.
        """
        self.node_types = node_types
        self.default_max_retries = default_max_retries
        self.retry_on_transient = retry_on_transient

    def can_handle(self, context: ErrorContext) -> bool:
        """
        Check if this handler applies to the error's node type.

        Args:
            context: Error context.

        Returns:
            True if handler should process this error.
        """
        if self.node_types is None:
            return True
        return context.node_type in self.node_types

    def classify(self, context: ErrorContext) -> ErrorContext:
        """
        Classify error based on error code and exception type.

        Args:
            context: Error context to classify.

        Returns:
            Updated context with classification, category, severity.
        """
        # Determine category from error code
        if context.error_code:
            context.category = self._category_from_code(context.error_code)
            context.classification = self._classification_from_code(context.error_code)
            context.severity = self._severity_from_code(context.error_code)
        else:
            # Fallback classification based on exception type
            context.category = self._category_from_exception(context.exception)
            context.classification = self._classification_from_exception(context.exception)
            context.severity = ErrorSeverity.MEDIUM

        return context

    def decide_recovery(self, context: ErrorContext) -> RecoveryDecision:
        """
        Decide recovery action based on classification.

        Args:
            context: Classified error context.

        Returns:
            Recovery decision.
        """
        # Critical errors always abort
        if context.severity == ErrorSeverity.CRITICAL:
            return RecoveryDecision(
                action=RecoveryAction.ABORT,
                reason=f"Critical error: {context.message}",
            )

        # Permanent errors cannot be retried
        if context.classification == ErrorClassification.PERMANENT:
            return RecoveryDecision(
                action=RecoveryAction.SKIP,
                reason=f"Permanent error (not retryable): {context.message}",
            )

        # Transient errors - retry if enabled and under limit
        if context.classification == ErrorClassification.TRANSIENT:
            if self.retry_on_transient and context.retry_count < context.max_retries:
                delay = self._calculate_retry_delay(context.retry_count)
                return RecoveryDecision(
                    action=RecoveryAction.RETRY,
                    reason=f"Transient error, retry {context.retry_count + 1}/{context.max_retries}",
                    retry_delay_ms=delay,
                )
            elif context.retry_count >= context.max_retries:
                return RecoveryDecision(
                    action=RecoveryAction.ESCALATE,
                    reason=f"Max retries ({context.max_retries}) exceeded",
                    escalation_message=f"Node {context.node_id} failed after {context.max_retries} retries: {context.message}",
                )

        # Unknown errors - try once, then escalate
        if context.classification == ErrorClassification.UNKNOWN:
            if context.retry_count == 0:
                return RecoveryDecision(
                    action=RecoveryAction.RETRY,
                    reason="Unknown error - attempting single retry",
                    retry_delay_ms=1000,
                )
            return RecoveryDecision(
                action=RecoveryAction.ESCALATE,
                reason=f"Unknown error persists after retry: {context.message}",
                escalation_message=f"Unclassified error in {context.node_type}: {context.message}",
            )

        # Default fallback
        return RecoveryDecision(
            action=RecoveryAction.SKIP,
            reason="No specific recovery strategy available",
        )

    def _category_from_code(self, code: ErrorCode) -> ErrorCategory:
        """Map error code to category."""
        code_value = code.value
        if 2000 <= code_value < 3000:
            return ErrorCategory.BROWSER
        elif 3000 <= code_value < 4000:
            return ErrorCategory.DESKTOP
        elif 4000 <= code_value < 5000:
            return ErrorCategory.DATA
        elif 5000 <= code_value < 6000:
            return ErrorCategory.CONFIGURATION
        elif 6000 <= code_value < 7000:
            return ErrorCategory.NETWORK
        elif 7000 <= code_value < 8000:
            return ErrorCategory.RESOURCE
        return ErrorCategory.EXECUTION

    def _classification_from_code(self, code: ErrorCode) -> ErrorClassification:
        """Map error code to classification."""
        transient_codes = {
            ErrorCode.TIMEOUT,
            ErrorCode.NETWORK_ERROR,
            ErrorCode.CONNECTION_TIMEOUT,
            ErrorCode.CONNECTION_REFUSED,
            ErrorCode.ELEMENT_STALE,
            ErrorCode.DESKTOP_ELEMENT_STALE,
            ErrorCode.APPLICATION_NOT_RESPONDING,
            ErrorCode.RESOURCE_LOCKED,
        }
        permanent_codes = {
            ErrorCode.SELECTOR_INVALID,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.CONFIG_INVALID,
            ErrorCode.CONFIG_NOT_FOUND,
            ErrorCode.WORKFLOW_INVALID,
            ErrorCode.NODE_CONFIG_ERROR,
            ErrorCode.FILE_NOT_FOUND,
            ErrorCode.FILE_ACCESS_DENIED,
        }

        if code in transient_codes:
            return ErrorClassification.TRANSIENT
        elif code in permanent_codes:
            return ErrorClassification.PERMANENT
        return ErrorClassification.UNKNOWN

    def _severity_from_code(self, code: ErrorCode) -> ErrorSeverity:
        """Map error code to severity."""
        critical_codes = {
            ErrorCode.MEMORY_ERROR,
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.BROWSER_CLOSED,
        }
        high_codes = {
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.CONFIG_INVALID,
            ErrorCode.WORKFLOW_INVALID,
        }
        low_codes = {
            ErrorCode.ELEMENT_STALE,
            ErrorCode.TIMEOUT,
        }

        if code in critical_codes:
            return ErrorSeverity.CRITICAL
        elif code in high_codes:
            return ErrorSeverity.HIGH
        elif code in low_codes:
            return ErrorSeverity.LOW
        return ErrorSeverity.MEDIUM

    def _category_from_exception(self, exc: Exception) -> ErrorCategory:
        """Infer category from exception type."""
        exc_type = type(exc).__name__.lower()
        exc_module = type(exc).__module__.lower() if type(exc).__module__ else ""

        if "playwright" in exc_module or "browser" in exc_type:
            return ErrorCategory.BROWSER
        elif "uiautomation" in exc_module or "desktop" in exc_type:
            return ErrorCategory.DESKTOP
        elif any(x in exc_type for x in ["connection", "socket", "http", "timeout", "ssl"]):
            return ErrorCategory.NETWORK
        elif any(x in exc_type for x in ["value", "type", "parse", "validation"]):
            return ErrorCategory.DATA
        elif any(x in exc_type for x in ["file", "permission", "io", "os"]):
            return ErrorCategory.RESOURCE
        return ErrorCategory.EXECUTION

    def _classification_from_exception(self, exc: Exception) -> ErrorClassification:
        """Infer classification from exception type."""
        exc_type = type(exc).__name__.lower()
        exc_msg = str(exc).lower()

        # Transient patterns
        transient_patterns = [
            "timeout",
            "connection",
            "stale",
            "not responding",
            "temporary",
            "busy",
            "retry",
        ]
        if any(p in exc_type or p in exc_msg for p in transient_patterns):
            return ErrorClassification.TRANSIENT

        # Permanent patterns
        permanent_patterns = [
            "invalid",
            "not found",
            "permission",
            "denied",
            "does not exist",
            "malformed",
        ]
        if any(p in exc_type or p in exc_msg for p in permanent_patterns):
            return ErrorClassification.PERMANENT

        return ErrorClassification.UNKNOWN

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate retry delay with exponential backoff and jitter.

        Args:
            retry_count: Current retry attempt (0-based).

        Returns:
            Delay in milliseconds.
        """
        base_delay = 1000  # 1 second
        max_delay = 30000  # 30 seconds

        # Exponential backoff: 1s, 2s, 4s, 8s...
        delay = base_delay * (2**retry_count)

        # Add jitter (10-30% of delay)
        jitter = random.uniform(0.1, 0.3) * delay
        delay = int(delay + jitter)

        return min(delay, max_delay)


__all__ = ["NodeErrorHandler"]
