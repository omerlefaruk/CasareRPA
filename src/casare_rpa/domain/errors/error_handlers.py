"""
CasareRPA - Error Handler Registry

Provides error classification, handler registration, and recovery decision framework.

Key Features:
- Error classification (Transient, Permanent, Unknown)
- Error handler registry per node type
- Custom error handlers via user-defined logic
- Error aggregation and context capture
- Recovery action recommendations

Architecture:
- Domain layer: Pure error handling logic
- No infrastructure dependencies (async I/O, screenshots done at infrastructure layer)
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, Union

from loguru import logger

from casare_rpa.domain.value_objects.types import ErrorCode, NodeId


class ErrorCategory(Enum):
    """
    High-level error categories for classification.

    Categories help determine recovery strategy:
    - BROWSER: Web automation errors (Playwright)
    - DESKTOP: Windows UI automation errors
    - NETWORK: Connection, timeout, SSL errors
    - DATA: Validation, parsing, type errors
    - RESOURCE: File, memory, permission errors
    - CONFIGURATION: Node/workflow config errors
    - EXECUTION: Runtime execution errors
    - UNKNOWN: Unclassified errors
    """

    BROWSER = auto()
    DESKTOP = auto()
    NETWORK = auto()
    DATA = auto()
    RESOURCE = auto()
    CONFIGURATION = auto()
    EXECUTION = auto()
    UNKNOWN = auto()


class ErrorSeverity(Enum):
    """
    Error severity levels.

    Severity affects:
    - Logging level
    - Recovery strategy aggressiveness
    - Human escalation threshold
    """

    LOW = 1  # Minor, easily recoverable
    MEDIUM = 2  # Significant, may need retry
    HIGH = 3  # Severe, may need human intervention
    CRITICAL = 4  # Fatal, workflow should abort


class ErrorClassification(Enum):
    """
    Error classification for recovery decisions.

    TRANSIENT: Temporary errors that may succeed on retry
        - Network timeouts
        - Element temporarily not visible
        - Application busy/not responding

    PERMANENT: Errors that will not resolve with retry
        - Invalid selector (element doesn't exist)
        - Permission denied
        - Configuration errors

    UNKNOWN: Cannot determine if transient or permanent
        - First occurrence of new error
        - Generic exceptions
    """

    TRANSIENT = auto()
    PERMANENT = auto()
    UNKNOWN = auto()


class RecoveryAction(Enum):
    """
    Recommended recovery actions.

    Actions the recovery system can take:
    - RETRY: Attempt the operation again
    - SKIP: Skip this node and continue
    - FALLBACK: Use alternative path/value
    - COMPENSATE: Run rollback operations
    - ABORT: Stop workflow execution
    - ESCALATE: Request human intervention
    """

    RETRY = auto()
    SKIP = auto()
    FALLBACK = auto()
    COMPENSATE = auto()
    ABORT = auto()
    ESCALATE = auto()


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

    error_code: Optional[ErrorCode] = None
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

    node_config: Dict[str, Any] = field(default_factory=dict)
    """Node configuration at time of error."""

    variables: Dict[str, Any] = field(default_factory=dict)
    """Execution context variables (sanitized)."""

    additional_data: Dict[str, Any] = field(default_factory=dict)
    """Extra context data (page URL, element selector, etc.)."""

    screenshot_path: Optional[str] = None
    """Path to error screenshot (if captured)."""

    def __post_init__(self) -> None:
        """Post-initialization to set derived fields."""
        if not self.message:
            self.message = str(self.exception)
        if not self.stack_trace:
            self.stack_trace = traceback.format_exc()
        if self.error_code is None:
            self.error_code = ErrorCode.from_exception(self.exception)

    def to_dict(self) -> Dict[str, Any]:
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

    compensate_nodes: List[NodeId] = field(default_factory=list)
    """Nodes to run for compensation (if action is COMPENSATE)."""

    escalation_message: str = ""
    """Message for human escalation (if action is ESCALATE)."""

    continue_from_node: Optional[NodeId] = None
    """Node to resume from (if action is SKIP)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional decision metadata."""

    def __repr__(self) -> str:
        """String representation."""
        return f"RecoveryDecision({self.action.name}: {self.reason})"


class ErrorHandler(ABC):
    """
    Abstract base class for error handlers.

    Error handlers analyze errors and recommend recovery actions.
    Subclasses implement domain-specific error handling logic.
    """

    @abstractmethod
    def can_handle(self, context: ErrorContext) -> bool:
        """
        Check if this handler can handle the given error.

        Args:
            context: Error context to evaluate.

        Returns:
            True if this handler should process the error.
        """
        pass

    @abstractmethod
    def classify(self, context: ErrorContext) -> ErrorContext:
        """
        Classify the error (set classification, category, severity).

        Args:
            context: Error context to classify.

        Returns:
            Updated error context with classification.
        """
        pass

    @abstractmethod
    def decide_recovery(self, context: ErrorContext) -> RecoveryDecision:
        """
        Decide recovery action for the error.

        Args:
            context: Classified error context.

        Returns:
            Recovery decision with recommended action.
        """
        pass


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
            context.classification = self._classification_from_exception(
                context.exception
            )
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
        elif any(
            x in exc_type for x in ["connection", "socket", "http", "timeout", "ssl"]
        ):
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
        import random

        base_delay = 1000  # 1 second
        max_delay = 30000  # 30 seconds

        # Exponential backoff: 1s, 2s, 4s, 8s...
        delay = base_delay * (2**retry_count)

        # Add jitter (10-30% of delay)
        jitter = random.uniform(0.1, 0.3) * delay
        delay = int(delay + jitter)

        return min(delay, max_delay)


# Type alias for custom handler functions
CustomErrorHandlerFunc = Callable[[ErrorContext], RecoveryDecision]


class ErrorHandlerRegistry:
    """
    Registry for error handlers.

    Maintains a collection of error handlers organized by:
    - Node type (specific handlers for specific nodes)
    - Error category (handlers for error types)
    - Global (fallback handlers)

    Handlers are tried in order of specificity:
    1. Node-type specific handlers
    2. Error-category handlers
    3. Global handlers
    """

    def __init__(self) -> None:
        """Initialize error handler registry."""
        self._node_handlers: Dict[str, List[ErrorHandler]] = {}
        self._category_handlers: Dict[ErrorCategory, List[ErrorHandler]] = {}
        self._global_handlers: List[ErrorHandler] = []
        self._custom_handlers: Dict[str, CustomErrorHandlerFunc] = {}
        self._error_history: List[ErrorContext] = []
        self._max_history = 1000

        # Register default handler as fallback
        self._default_handler = NodeErrorHandler()
        self._global_handlers.append(self._default_handler)

        logger.debug("Error handler registry initialized")

    def register_node_handler(self, node_type: str, handler: ErrorHandler) -> None:
        """
        Register handler for specific node type.

        Args:
            node_type: Node class name (e.g., "NavigateNode").
            handler: Error handler instance.
        """
        if node_type not in self._node_handlers:
            self._node_handlers[node_type] = []
        self._node_handlers[node_type].append(handler)
        logger.debug(f"Registered node handler for {node_type}")

    def register_category_handler(
        self, category: ErrorCategory, handler: ErrorHandler
    ) -> None:
        """
        Register handler for error category.

        Args:
            category: Error category.
            handler: Error handler instance.
        """
        if category not in self._category_handlers:
            self._category_handlers[category] = []
        self._category_handlers[category].append(handler)
        logger.debug(f"Registered category handler for {category.name}")

    def register_global_handler(self, handler: ErrorHandler) -> None:
        """
        Register global handler (fallback).

        Args:
            handler: Error handler instance.
        """
        # Insert before default handler
        self._global_handlers.insert(-1, handler)
        logger.debug("Registered global error handler")

    def register_custom_handler(
        self, name: str, handler_func: CustomErrorHandlerFunc
    ) -> None:
        """
        Register custom handler function (user-defined).

        Args:
            name: Unique handler name.
            handler_func: Function that takes ErrorContext and returns RecoveryDecision.
        """
        self._custom_handlers[name] = handler_func
        logger.debug(f"Registered custom error handler: {name}")

    def unregister_custom_handler(self, name: str) -> bool:
        """
        Unregister custom handler.

        Args:
            name: Handler name to remove.

        Returns:
            True if handler was removed, False if not found.
        """
        if name in self._custom_handlers:
            del self._custom_handlers[name]
            logger.debug(f"Unregistered custom error handler: {name}")
            return True
        return False

    def handle_error(
        self,
        exception: Exception,
        node_id: NodeId,
        node_type: str,
        retry_count: int = 0,
        max_retries: int = 3,
        execution_time_ms: float = 0.0,
        node_config: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> tuple[ErrorContext, RecoveryDecision]:
        """
        Handle an error and get recovery decision.

        Args:
            exception: The exception that occurred.
            node_id: ID of the node where error occurred.
            node_type: Type/class name of the node.
            retry_count: Number of retries already attempted.
            max_retries: Maximum retry attempts.
            execution_time_ms: How long the operation ran.
            node_config: Node configuration.
            variables: Execution context variables.
            additional_data: Extra context (URL, selector, etc.).

        Returns:
            Tuple of (ErrorContext, RecoveryDecision).
        """
        # Create error context
        context = ErrorContext(
            exception=exception,
            node_id=node_id,
            node_type=node_type,
            retry_count=retry_count,
            max_retries=max_retries,
            execution_time_ms=execution_time_ms,
            node_config=self._sanitize_config(node_config or {}),
            variables=self._sanitize_variables(variables or {}),
            additional_data=additional_data or {},
        )

        # Try custom handlers first (user-defined)
        for handler_name, handler_func in self._custom_handlers.items():
            try:
                decision = handler_func(context)
                if decision is not None:
                    logger.debug(f"Custom handler '{handler_name}' handled error")
                    self._record_error(context)
                    return context, decision
            except Exception as e:
                logger.error(f"Custom handler '{handler_name}' failed: {e}")

        # Find appropriate handler
        handler = self._find_handler(context)

        # Classify error
        context = handler.classify(context)

        # Get recovery decision
        decision = handler.decide_recovery(context)

        # Record error in history
        self._record_error(context)

        logger.info(
            f"Error handled: {context.node_type}[{context.node_id}] - "
            f"{context.classification.name} -> {decision.action.name}"
        )

        return context, decision

    def _find_handler(self, context: ErrorContext) -> ErrorHandler:
        """
        Find the most appropriate handler for the error.

        Args:
            context: Error context.

        Returns:
            Most appropriate error handler.
        """
        # Try node-specific handlers first
        if context.node_type in self._node_handlers:
            for handler in self._node_handlers[context.node_type]:
                if handler.can_handle(context):
                    return handler

        # Try category handlers
        if context.category in self._category_handlers:
            for handler in self._category_handlers[context.category]:
                if handler.can_handle(context):
                    return handler

        # Try global handlers
        for handler in self._global_handlers:
            if handler.can_handle(context):
                return handler

        # Fallback to default
        return self._default_handler

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize node config for storage (remove sensitive data).

        Args:
            config: Raw node configuration.

        Returns:
            Sanitized configuration.
        """
        sensitive_keys = {"password", "secret", "token", "api_key", "credential"}
        sanitized = {}
        for key, value in config.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize variables for storage (remove sensitive data, truncate large values).

        Args:
            variables: Raw variables dict.

        Returns:
            Sanitized variables.
        """
        sensitive_patterns = {"password", "secret", "token", "api_key", "credential"}
        sanitized = {}
        for key, value in variables.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_patterns):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "...[truncated]"
            elif isinstance(value, (list, dict)) and len(str(value)) > 1000:
                sanitized[key] = "[large value truncated]"
            else:
                sanitized[key] = value
        return sanitized

    def _record_error(self, context: ErrorContext) -> None:
        """
        Record error in history.

        Args:
            context: Error context to record.
        """
        self._error_history.append(context)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

    def get_error_history(
        self,
        node_id: Optional[NodeId] = None,
        category: Optional[ErrorCategory] = None,
        limit: int = 100,
    ) -> List[ErrorContext]:
        """
        Get error history with optional filtering.

        Args:
            node_id: Filter by node ID.
            category: Filter by error category.
            limit: Maximum results.

        Returns:
            List of error contexts (most recent first).
        """
        history = self._error_history[::-1]

        if node_id:
            history = [e for e in history if e.node_id == node_id]
        if category:
            history = [e for e in history if e.category == category]

        return history[:limit]

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of error history.

        Returns:
            Dictionary with error statistics.
        """
        if not self._error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_classification": {},
                "by_node_type": {},
            }

        by_category: Dict[str, int] = {}
        by_classification: Dict[str, int] = {}
        by_node_type: Dict[str, int] = {}

        for ctx in self._error_history:
            cat = ctx.category.name
            by_category[cat] = by_category.get(cat, 0) + 1

            cls = ctx.classification.name
            by_classification[cls] = by_classification.get(cls, 0) + 1

            nt = ctx.node_type
            by_node_type[nt] = by_node_type.get(nt, 0) + 1

        return {
            "total_errors": len(self._error_history),
            "by_category": by_category,
            "by_classification": by_classification,
            "by_node_type": by_node_type,
        }

    def clear_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
        logger.debug("Error history cleared")


# Global registry instance (singleton)
_global_registry: Optional[ErrorHandlerRegistry] = None


def get_error_handler_registry() -> ErrorHandlerRegistry:
    """
    Get the global error handler registry (singleton).

    Returns:
        Global ErrorHandlerRegistry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ErrorHandlerRegistry()
        logger.info("Global error handler registry created")
    return _global_registry


def reset_error_handler_registry() -> None:
    """Reset the global error handler registry (for testing)."""
    global _global_registry
    _global_registry = None
    logger.debug("Global error handler registry reset")
