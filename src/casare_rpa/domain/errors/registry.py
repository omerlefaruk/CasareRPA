"""
CasareRPA - Error Handler Registry.

Registry for error handlers with global singleton access.
"""

import logging
from collections.abc import Callable
from typing import Any, Optional

logger = logging.getLogger(__name__)

from casare_rpa.domain.errors.context import ErrorContext, RecoveryDecision
from casare_rpa.domain.errors.handlers import ErrorHandler, NodeErrorHandler
from casare_rpa.domain.errors.types import ErrorCategory
from casare_rpa.domain.value_objects.types import NodeId

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
        self._node_handlers: dict[str, list[ErrorHandler]] = {}
        self._category_handlers: dict[ErrorCategory, list[ErrorHandler]] = {}
        self._global_handlers: list[ErrorHandler] = []
        self._custom_handlers: dict[str, CustomErrorHandlerFunc] = {}
        self._error_history: list[ErrorContext] = []
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

    def register_category_handler(self, category: ErrorCategory, handler: ErrorHandler) -> None:
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

    def register_custom_handler(self, name: str, handler_func: CustomErrorHandlerFunc) -> None:
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
        node_config: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        additional_data: dict[str, Any] | None = None,
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

    def _sanitize_config(self, config: dict[str, Any]) -> dict[str, Any]:
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

    def _sanitize_variables(self, variables: dict[str, Any]) -> dict[str, Any]:
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
            elif isinstance(value, list | dict) and len(str(value)) > 1000:
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
        node_id: NodeId | None = None,
        category: ErrorCategory | None = None,
        limit: int = 100,
    ) -> list[ErrorContext]:
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

    def get_error_summary(self) -> dict[str, Any]:
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

        by_category: dict[str, int] = {}
        by_classification: dict[str, int] = {}
        by_node_type: dict[str, int] = {}

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


# Thread-safe singleton implementation (pure domain, no application dependency)
import threading

_registry_instance: Optional["ErrorHandlerRegistry"] = None
_registry_lock = threading.Lock()


def get_error_handler_registry() -> ErrorHandlerRegistry:
    """
    Get the global error handler registry (singleton).

    Thread-safe lazy initialization.

    Returns:
        Global ErrorHandlerRegistry instance.
    """
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ErrorHandlerRegistry()
                logger.info("Global error handler registry created")
    return _registry_instance


def reset_error_handler_registry() -> None:
    """Reset the global error handler registry (for testing)."""
    global _registry_instance
    with _registry_lock:
        _registry_instance = None
    logger.debug("Global error handler registry reset")


__all__ = [
    "ErrorHandlerRegistry",
    "CustomErrorHandlerFunc",
    "get_error_handler_registry",
    "reset_error_handler_registry",
]
