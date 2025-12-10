"""
Advanced Error Handling System for CasareRPA.

Provides:
- Global error handler with configurable strategies
- Error analytics and pattern tracking
- Error notifications via webhooks
- Recovery strategies (restart, fallback, ignore)
"""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import asyncio
import traceback

from loguru import logger

# Memory management constants
MAX_ERROR_PATTERNS = 500
MAX_ERROR_COUNTS = 1000
MAX_HOURLY_BUCKETS = 168  # 1 week of hours
MAX_AFFECTED_ITEMS = 100  # Per pattern


class RecoveryStrategy(Enum):
    """Error recovery strategies."""

    STOP = "stop"  # Stop workflow execution
    CONTINUE = "continue"  # Skip failed node and continue
    RETRY = "retry"  # Retry the failed node
    RESTART = "restart"  # Restart entire workflow
    FALLBACK = "fallback"  # Execute fallback workflow/node
    NOTIFY_AND_STOP = "notify_and_stop"  # Send notification then stop


class ErrorSeverity(Enum):
    """Error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Record of a single error occurrence."""

    timestamp: datetime
    workflow_id: str
    workflow_name: str
    node_id: str
    node_type: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    recovered: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "severity": self.severity.value,
            "context": self.context,
            "recovered": self.recovered,
            "recovery_strategy": self.recovery_strategy.value
            if self.recovery_strategy
            else None,
        }


@dataclass
class ErrorPattern:
    """Tracked error pattern for analytics."""

    error_type: str
    first_seen: datetime
    last_seen: datetime
    count: int = 0
    affected_nodes: set = field(default_factory=set)
    affected_workflows: set = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "count": self.count,
            "affected_nodes": list(self.affected_nodes),
            "affected_workflows": list(self.affected_workflows),
        }


class ErrorAnalytics:
    """
    Track and analyze error patterns.

    Provides insights into:
    - Most common errors
    - Error frequency over time
    - Affected nodes and workflows
    - Error trends
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize error analytics.

        Args:
            max_history: Maximum number of error records to keep
        """
        self._history: deque[ErrorRecord] = deque(maxlen=max_history)
        self._patterns: Dict[str, ErrorPattern] = {}
        self._max_history = max_history
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._hourly_counts: Dict[str, int] = defaultdict(int)

    def record_error(self, error: ErrorRecord) -> None:
        """
        Record an error occurrence.

        Args:
            error: The error record to track
        """
        # Add to history (deque handles size limit automatically)
        self._history.append(error)

        # Update patterns with eviction
        error_type = error.error_type
        if error_type not in self._patterns:
            # Evict oldest pattern if at capacity
            if len(self._patterns) >= MAX_ERROR_PATTERNS:
                oldest = next(iter(self._patterns))
                del self._patterns[oldest]
            self._patterns[error_type] = ErrorPattern(
                error_type=error_type,
                first_seen=error.timestamp,
                last_seen=error.timestamp,
            )

        pattern = self._patterns[error_type]
        pattern.count += 1
        pattern.last_seen = error.timestamp

        # Limit affected_nodes and affected_workflows sets
        if len(pattern.affected_nodes) < MAX_AFFECTED_ITEMS:
            pattern.affected_nodes.add(error.node_id)
        if len(pattern.affected_workflows) < MAX_AFFECTED_ITEMS:
            pattern.affected_workflows.add(error.workflow_name)

        # Update error counts with eviction
        if error_type not in self._error_counts:
            if len(self._error_counts) >= MAX_ERROR_COUNTS:
                oldest = next(iter(self._error_counts))
                del self._error_counts[oldest]
        self._error_counts[error_type] += 1

        # Update hourly counts with eviction
        hour_key = error.timestamp.strftime("%Y-%m-%d-%H")
        if hour_key not in self._hourly_counts:
            if len(self._hourly_counts) >= MAX_HOURLY_BUCKETS:
                oldest = next(iter(self._hourly_counts))
                del self._hourly_counts[oldest]
        self._hourly_counts[hour_key] += 1

        logger.debug(f"Error recorded: {error_type} (total: {pattern.count})")

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most common errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of error patterns sorted by frequency
        """
        sorted_patterns = sorted(
            self._patterns.values(), key=lambda p: p.count, reverse=True
        )
        return [p.to_dict() for p in sorted_patterns[:limit]]

    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get errors from the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent error records
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [e for e in self._history if e.timestamp >= cutoff]
        return [e.to_dict() for e in recent]

    def get_error_rate(self, hours: int = 1) -> float:
        """
        Get the error rate (errors per hour) for recent period.

        Args:
            hours: Number of hours to calculate rate for

        Returns:
            Errors per hour
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_count = sum(1 for e in self._history if e.timestamp >= cutoff)
        return recent_count / max(hours, 1)

    def get_error_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get hourly error counts for trend analysis.

        Args:
            hours: Number of hours of history

        Returns:
            List of {hour, count} dictionaries
        """
        trend = []
        now = datetime.now()
        for i in range(hours, 0, -1):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y-%m-%d-%H")
            trend.append(
                {
                    "hour": hour.strftime("%Y-%m-%d %H:00"),
                    "count": self._hourly_counts.get(hour_key, 0),
                }
            )
        return trend

    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall error analytics summary.

        Returns:
            Summary statistics
        """
        return {
            "total_errors": len(self._history),
            "unique_error_types": len(self._patterns),
            "error_rate_1h": self.get_error_rate(1),
            "error_rate_24h": self.get_error_rate(24),
            "top_errors": self.get_top_errors(5),
        }

    def clear(self) -> None:
        """Clear all error history and patterns."""
        self._history.clear()
        self._patterns.clear()
        self._error_counts.clear()
        self._hourly_counts.clear()

    def clear_old_data(self, max_age_hours: int = 168) -> None:
        """
        Clear data older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours (default 168 = 1 week)
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cutoff_hour = cutoff.replace(minute=0, second=0, microsecond=0)

        # Clear old patterns (keep only those seen after cutoff)
        self._patterns = {
            k: v for k, v in self._patterns.items() if v.last_seen >= cutoff
        }

        # Clear old hourly counts
        cutoff_hour_key = cutoff_hour.strftime("%Y-%m-%d-%H")
        self._hourly_counts = {
            k: v for k, v in self._hourly_counts.items() if k >= cutoff_hour_key
        }

        logger.debug(
            f"Cleared old error data (cutoff: {cutoff}). "
            f"Patterns: {len(self._patterns)}, Hourly buckets: {len(self._hourly_counts)}"
        )


class GlobalErrorHandler:
    """
    Global error handler for workflow execution.

    Features:
    - Configurable recovery strategies per error type
    - Default recovery behavior
    - Error notifications via callbacks
    - Integration with error analytics
    """

    def __init__(
        self,
        default_strategy: RecoveryStrategy = RecoveryStrategy.STOP,
        analytics: Optional[ErrorAnalytics] = None,
    ):
        """
        Initialize global error handler.

        Args:
            default_strategy: Default recovery strategy for unhandled errors
            analytics: Optional ErrorAnalytics instance for tracking
        """
        self._default_strategy = default_strategy
        self._analytics = analytics or ErrorAnalytics()
        self._strategy_map: Dict[str, RecoveryStrategy] = {}
        self._notification_handlers: List[Callable[[ErrorRecord], Awaitable[None]]] = []
        self._fallback_workflows: Dict[
            str, str
        ] = {}  # error_type -> fallback_workflow_id
        self._enabled = True

    @property
    def analytics(self) -> ErrorAnalytics:
        """Get the error analytics instance."""
        return self._analytics

    def set_default_strategy(self, strategy: RecoveryStrategy) -> None:
        """
        Set the default recovery strategy.

        Args:
            strategy: Default strategy for unhandled errors
        """
        self._default_strategy = strategy
        logger.info(f"Default error recovery strategy set to: {strategy.value}")

    def set_strategy_for_error(
        self, error_type: str, strategy: RecoveryStrategy
    ) -> None:
        """
        Set recovery strategy for a specific error type.

        Args:
            error_type: The error type (exception class name or custom type)
            strategy: Recovery strategy to use
        """
        self._strategy_map[error_type] = strategy
        logger.info(f"Recovery strategy for '{error_type}' set to: {strategy.value}")

    def set_fallback_workflow(self, error_type: str, workflow_id: str) -> None:
        """
        Set a fallback workflow to execute when specific error occurs.

        Args:
            error_type: The error type to trigger fallback
            workflow_id: ID of the fallback workflow to execute
        """
        self._fallback_workflows[error_type] = workflow_id
        self._strategy_map[error_type] = RecoveryStrategy.FALLBACK
        logger.info(
            f"Fallback workflow '{workflow_id}' set for error type: {error_type}"
        )

    def add_notification_handler(
        self, handler: Callable[[ErrorRecord], Awaitable[None]]
    ) -> None:
        """
        Add a notification handler for error events.

        Args:
            handler: Async function that receives ErrorRecord and sends notification
        """
        self._notification_handlers.append(handler)
        logger.info(
            f"Added error notification handler (total: {len(self._notification_handlers)})"
        )

    def remove_notification_handler(
        self, handler: Callable[[ErrorRecord], Awaitable[None]]
    ) -> None:
        """Remove a notification handler."""
        if handler in self._notification_handlers:
            self._notification_handlers.remove(handler)

    def enable(self, enabled: bool = True) -> None:
        """Enable or disable the global error handler."""
        self._enabled = enabled
        logger.info(f"Global error handler {'enabled' if enabled else 'disabled'}")

    def get_strategy(self, error_type: str) -> RecoveryStrategy:
        """
        Get the recovery strategy for an error type.

        Args:
            error_type: The error type

        Returns:
            Configured or default recovery strategy
        """
        return self._strategy_map.get(error_type, self._default_strategy)

    def get_fallback_workflow(self, error_type: str) -> Optional[str]:
        """
        Get the fallback workflow ID for an error type.

        Args:
            error_type: The error type

        Returns:
            Fallback workflow ID or None
        """
        return self._fallback_workflows.get(error_type)

    async def handle_error(
        self,
        exception: Exception,
        workflow_id: str,
        workflow_name: str,
        node_id: str,
        node_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryStrategy:
        """
        Handle an error occurrence.

        Args:
            exception: The exception that occurred
            workflow_id: ID of the workflow
            workflow_name: Name of the workflow
            node_id: ID of the node that failed
            node_type: Type of the node
            context: Additional context information

        Returns:
            The recovery strategy to apply
        """
        if not self._enabled:
            return self._default_strategy

        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()

        # Determine severity
        severity = self._classify_severity(exception)

        # Create error record
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            node_id=node_id,
            node_type=node_type,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            severity=severity,
            context=context or {},
        )

        # Get recovery strategy
        strategy = self.get_strategy(error_type)
        error_record.recovery_strategy = strategy

        # Track in analytics
        self._analytics.record_error(error_record)

        # Send notifications
        await self._send_notifications(error_record)

        logger.error(
            f"Error handled: {error_type} in {workflow_name}/{node_id} "
            f"-> Strategy: {strategy.value}"
        )

        return strategy

    def _classify_severity(self, exception: Exception) -> ErrorSeverity:
        """Classify error severity based on exception type."""
        critical_types = (SystemExit, KeyboardInterrupt, MemoryError)
        warning_types = (TimeoutError, asyncio.TimeoutError)

        if isinstance(exception, critical_types):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, warning_types):
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR

    async def _send_notifications(self, error_record: ErrorRecord) -> None:
        """Send error notifications to all registered handlers."""
        if not self._notification_handlers:
            return

        for handler in self._notification_handlers:
            try:
                await handler(error_record)
            except Exception as e:
                logger.error(f"Error notification handler failed: {e}")

    def get_config(self) -> Dict[str, Any]:
        """Get current error handler configuration."""
        return {
            "enabled": self._enabled,
            "default_strategy": self._default_strategy.value,
            "strategy_map": {k: v.value for k, v in self._strategy_map.items()},
            "fallback_workflows": self._fallback_workflows.copy(),
            "notification_handlers_count": len(self._notification_handlers),
        }


# Global singleton instance
_global_error_handler: Optional[GlobalErrorHandler] = None


def get_global_error_handler() -> GlobalErrorHandler:
    """Get or create the global error handler singleton."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = GlobalErrorHandler()
    return _global_error_handler


def reset_global_error_handler() -> None:
    """Reset the global error handler (mainly for testing)."""
    global _global_error_handler
    _global_error_handler = None
