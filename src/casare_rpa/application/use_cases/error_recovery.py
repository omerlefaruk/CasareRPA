"""
CasareRPA - Error Recovery Orchestration Use Case

Coordinates error handling and recovery across domain and infrastructure layers.

This use case:
- Receives errors from node execution
- Uses ErrorHandlerRegistry (domain) for classification
- Uses RecoveryStrategyRegistry (infrastructure) for recovery execution
- Emits events for monitoring and logging
- Manages error aggregation and reporting

Architecture:
- Application layer: Orchestrates domain and infrastructure
- Domain: Error classification and handler decisions
- Infrastructure: Recovery strategy execution and screenshots
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.errors import (
    ErrorContext,
    ErrorHandlerRegistry,
    RecoveryAction,
    RecoveryDecision,
    get_error_handler_registry,
)
from casare_rpa.domain.events import EventBus, get_event_bus, NodeFailed
from casare_rpa.domain.value_objects.types import NodeId
from casare_rpa.infrastructure.execution.recovery_strategies import (
    CircuitBreaker,
    CircuitBreakerConfig,
    RecoveryStrategyRegistry,
    get_recovery_strategy_registry,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution.execution_context import ExecutionContext


@dataclass
class ErrorRecoveryConfig:
    """Configuration for error recovery orchestration."""

    enable_auto_retry: bool = True
    """Enable automatic retry for transient errors."""

    enable_circuit_breaker: bool = True
    """Enable circuit breaker pattern."""

    enable_screenshots: bool = True
    """Capture screenshots on UI errors."""

    enable_escalation: bool = True
    """Allow escalation to human operators."""

    max_consecutive_errors: int = 10
    """Stop workflow after this many consecutive errors."""

    error_aggregation_window_seconds: float = 60.0
    """Window for aggregating similar errors."""

    circuit_breaker_failure_threshold: int = 5
    """Failures before opening circuit breaker."""

    circuit_breaker_recovery_seconds: float = 30.0
    """Time before retrying after circuit opens."""


@dataclass
class ErrorAggregation:
    """Aggregates similar errors for reporting."""

    error_key: str
    """Unique key for this error type."""

    first_occurrence: datetime
    """When this error first occurred."""

    last_occurrence: datetime
    """When this error last occurred."""

    count: int = 1
    """Number of occurrences."""

    node_ids: Set[NodeId] = field(default_factory=set)
    """Nodes where this error occurred."""

    sample_context: Optional[ErrorContext] = None
    """Sample error context for details."""


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""

    success: bool
    """Whether recovery succeeded."""

    action_taken: RecoveryAction
    """Action that was executed."""

    should_retry: bool = False
    """Whether node should be retried."""

    should_skip: bool = False
    """Whether node should be skipped."""

    should_abort: bool = False
    """Whether workflow should abort."""

    next_node_id: Optional[NodeId] = None
    """Node to continue from (fallback/redirect)."""

    retry_delay_ms: int = 0
    """Delay before retry (if retrying)."""

    error_context: Optional[ErrorContext] = None
    """Full error context."""

    message: str = ""
    """Human-readable result message."""

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RecoveryResult(success={self.success}, action={self.action_taken.name}, "
            f"retry={self.should_retry}, skip={self.should_skip}, abort={self.should_abort})"
        )


class ErrorRecoveryUseCase:
    """
    Application use case for error recovery orchestration.

    Coordinates:
    - Domain: ErrorHandlerRegistry for classification and decisions
    - Infrastructure: RecoveryStrategyRegistry for recovery execution
    - Events: Progress and error notifications
    """

    def __init__(
        self,
        config: Optional[ErrorRecoveryConfig] = None,
        error_registry: Optional[ErrorHandlerRegistry] = None,
        strategy_registry: Optional[RecoveryStrategyRegistry] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """
        Initialize error recovery use case.

        Args:
            config: Recovery configuration.
            error_registry: Error handler registry (domain).
            strategy_registry: Recovery strategy registry (infrastructure).
            event_bus: Event bus for notifications.
        """
        self.config = config or ErrorRecoveryConfig()
        self.error_registry = error_registry or get_error_handler_registry()
        self.strategy_registry = strategy_registry or get_recovery_strategy_registry()
        self.event_bus = event_bus or get_event_bus()

        # Tracking
        self._consecutive_errors = 0
        self._error_aggregations: Dict[str, ErrorAggregation] = {}
        self._node_retry_counts: Dict[NodeId, int] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        logger.debug("Error recovery use case initialized")

    async def handle_error(
        self,
        exception: Exception,
        node_id: NodeId,
        node_type: str,
        execution_context: "ExecutionContext",
        node_config: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Handle an error during node execution.

        This is the main entry point for error handling.

        Args:
            exception: The exception that occurred.
            node_id: ID of the node where error occurred.
            node_type: Type/class name of the node.
            execution_context: Current execution context.
            node_config: Node configuration.
            execution_time_ms: How long the operation ran.
            additional_data: Extra context (URL, selector, etc.).

        Returns:
            RecoveryResult indicating what action was taken.
        """
        # Get retry count for this node
        retry_count = self._node_retry_counts.get(node_id, 0)
        max_retries = 3  # Default, can be overridden by config

        # Check circuit breaker
        if self.config.enable_circuit_breaker:
            cb_key = f"node_{node_type}"
            if cb_key in self._circuit_breakers:
                cb = self._circuit_breakers[cb_key]
                if cb.is_open:
                    return RecoveryResult(
                        success=False,
                        action_taken=RecoveryAction.SKIP,
                        should_skip=True,
                        message=f"Circuit breaker open for {node_type} - skipping",
                    )

        # Use error registry to classify and decide
        error_context, decision = self.error_registry.handle_error(
            exception=exception,
            node_id=node_id,
            node_type=node_type,
            retry_count=retry_count,
            max_retries=max_retries,
            execution_time_ms=execution_time_ms,
            node_config=node_config,
            variables=dict(execution_context.variables) if execution_context else {},
            additional_data=additional_data,
        )

        # Track consecutive errors
        self._consecutive_errors += 1
        if self._consecutive_errors >= self.config.max_consecutive_errors:
            logger.error(
                f"Max consecutive errors ({self.config.max_consecutive_errors}) reached - aborting"
            )
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ABORT,
                should_abort=True,
                error_context=error_context,
                message=f"Max consecutive errors exceeded ({self._consecutive_errors})",
            )

        # Aggregate similar errors
        self._aggregate_error(error_context)

        # Emit error event
        self._emit_error_event(error_context, decision)

        # Execute recovery strategy
        return await self._execute_recovery(error_context, decision, execution_context)

    async def _execute_recovery(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> RecoveryResult:
        """
        Execute recovery strategy and return result.

        Args:
            context: Error context.
            decision: Recovery decision from handler.
            execution_context: Current execution context.

        Returns:
            RecoveryResult with outcome.
        """
        logger.info(
            f"Executing recovery: {decision.action.name} for node {context.node_id} - "
            f"{decision.reason}"
        )

        # Override certain actions based on config
        if decision.action == RecoveryAction.RETRY and not self.config.enable_auto_retry:
            logger.debug("Auto-retry disabled - converting to SKIP")
            decision = RecoveryDecision(
                action=RecoveryAction.SKIP,
                reason="Auto-retry disabled by configuration",
            )

        if decision.action == RecoveryAction.ESCALATE and not self.config.enable_escalation:
            logger.debug("Escalation disabled - converting to ABORT")
            decision = RecoveryDecision(
                action=RecoveryAction.ABORT,
                reason="Escalation disabled by configuration - aborting",
            )

        # Execute strategy
        strategy_success = await self.strategy_registry.execute_recovery(
            context, decision, execution_context
        )

        # Build result based on action
        result = self._build_recovery_result(context, decision, strategy_success)

        # Update circuit breaker
        if self.config.enable_circuit_breaker:
            self._update_circuit_breaker(context, strategy_success)

        # Update retry count if retrying
        if result.should_retry:
            self._node_retry_counts[context.node_id] = context.retry_count + 1

        return result

    def _build_recovery_result(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        strategy_success: bool,
    ) -> RecoveryResult:
        """
        Build RecoveryResult from decision and strategy execution.

        Args:
            context: Error context.
            decision: Recovery decision.
            strategy_success: Whether strategy execution succeeded.

        Returns:
            RecoveryResult.
        """
        if decision.action == RecoveryAction.RETRY:
            return RecoveryResult(
                success=strategy_success,
                action_taken=RecoveryAction.RETRY,
                should_retry=strategy_success,
                retry_delay_ms=decision.retry_delay_ms,
                error_context=context,
                message=decision.reason,
            )

        elif decision.action == RecoveryAction.SKIP:
            return RecoveryResult(
                success=True,  # Skip is always "successful"
                action_taken=RecoveryAction.SKIP,
                should_skip=True,
                error_context=context,
                message=decision.reason,
            )

        elif decision.action == RecoveryAction.FALLBACK:
            return RecoveryResult(
                success=strategy_success,
                action_taken=RecoveryAction.FALLBACK,
                should_skip=not decision.continue_from_node,
                next_node_id=decision.continue_from_node,
                error_context=context,
                message=decision.reason,
            )

        elif decision.action == RecoveryAction.COMPENSATE:
            return RecoveryResult(
                success=strategy_success,
                action_taken=RecoveryAction.COMPENSATE,
                should_abort=not strategy_success,  # Abort if compensation failed
                error_context=context,
                message=decision.reason,
            )

        elif decision.action == RecoveryAction.ABORT:
            return RecoveryResult(
                success=True,  # Abort is intentional
                action_taken=RecoveryAction.ABORT,
                should_abort=True,
                error_context=context,
                message=decision.reason,
            )

        elif decision.action == RecoveryAction.ESCALATE:
            return RecoveryResult(
                success=strategy_success,
                action_taken=RecoveryAction.ESCALATE,
                should_skip=True,  # Continue after escalation
                error_context=context,
                message=decision.reason,
            )

        # Unknown action - default to skip
        return RecoveryResult(
            success=False,
            action_taken=decision.action,
            should_skip=True,
            error_context=context,
            message=f"Unknown recovery action: {decision.action.name}",
        )

    def _aggregate_error(self, context: ErrorContext) -> None:
        """
        Aggregate similar errors for reporting.

        Args:
            context: Error context.
        """
        # Create error key from type + code
        error_key = (
            f"{context.node_type}:{context.error_code.name if context.error_code else 'UNKNOWN'}"
        )

        now = datetime.now()

        if error_key in self._error_aggregations:
            agg = self._error_aggregations[error_key]
            # Check if within aggregation window
            if (
                now - agg.last_occurrence
            ).total_seconds() <= self.config.error_aggregation_window_seconds:
                agg.count += 1
                agg.last_occurrence = now
                agg.node_ids.add(context.node_id)
            else:
                # Start new aggregation
                self._error_aggregations[error_key] = ErrorAggregation(
                    error_key=error_key,
                    first_occurrence=now,
                    last_occurrence=now,
                    count=1,
                    node_ids={context.node_id},
                    sample_context=context,
                )
        else:
            self._error_aggregations[error_key] = ErrorAggregation(
                error_key=error_key,
                first_occurrence=now,
                last_occurrence=now,
                count=1,
                node_ids={context.node_id},
                sample_context=context,
            )

    def _update_circuit_breaker(self, context: ErrorContext, success: bool) -> None:
        """
        Update circuit breaker for node type.

        Args:
            context: Error context.
            success: Whether recovery succeeded.
        """
        cb_key = f"node_{context.node_type}"

        if cb_key not in self._circuit_breakers:
            self._circuit_breakers[cb_key] = CircuitBreaker(
                cb_key,
                CircuitBreakerConfig(
                    failure_threshold=self.config.circuit_breaker_failure_threshold,
                    recovery_timeout_seconds=self.config.circuit_breaker_recovery_seconds,
                ),
            )

        cb = self._circuit_breakers[cb_key]
        if success:
            cb.record_success()
        else:
            cb.record_failure(context.error_code.name if context.error_code else None)

    def _emit_error_event(self, context: ErrorContext, decision: RecoveryDecision) -> None:
        """
        Emit error event to event bus.

        Args:
            context: Error context.
            decision: Recovery decision.
        """
        if self.event_bus:
            self.event_bus.publish(
                NodeFailed(
                    node_id=context.node_id,
                    node_type=context.node_type,
                    workflow_id="",
                    error_message=context.message,
                    error_code=context.error_code,  # Pass enum directly, not .name
                    is_retryable=decision.action == RecoveryAction.RETRY,
                )
            )

    def record_success(self, node_id: NodeId, node_type: str) -> None:
        """
        Record successful node execution.

        Call this after a node succeeds to:
        - Reset consecutive error counter
        - Clear retry count for the node
        - Update circuit breaker

        Args:
            node_id: Node that succeeded.
            node_type: Type of the node.
        """
        self._consecutive_errors = 0

        if node_id in self._node_retry_counts:
            del self._node_retry_counts[node_id]

        # Update circuit breaker
        if self.config.enable_circuit_breaker:
            cb_key = f"node_{node_type}"
            if cb_key in self._circuit_breakers:
                self._circuit_breakers[cb_key].record_success()

    def get_error_report(self) -> Dict[str, Any]:
        """
        Get comprehensive error report.

        Returns:
            Dictionary with error statistics and aggregations.
        """
        # Get aggregations
        aggregations = []
        for key, agg in self._error_aggregations.items():
            aggregations.append(
                {
                    "error_key": key,
                    "count": agg.count,
                    "first_occurrence": agg.first_occurrence.isoformat(),
                    "last_occurrence": agg.last_occurrence.isoformat(),
                    "affected_nodes": list(agg.node_ids),
                    "sample_message": agg.sample_context.message if agg.sample_context else None,
                }
            )

        # Get circuit breaker states
        circuit_states = {name: cb.get_state() for name, cb in self._circuit_breakers.items()}

        # Get error history summary from registry
        history_summary = self.error_registry.get_error_summary()

        return {
            "consecutive_errors": self._consecutive_errors,
            "nodes_with_retries": dict(self._node_retry_counts),
            "error_aggregations": sorted(aggregations, key=lambda x: x["count"], reverse=True),
            "circuit_breakers": circuit_states,
            "history_summary": history_summary,
        }

    def get_node_error_history(self, node_id: NodeId, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get error history for a specific node.

        Args:
            node_id: Node ID to query.
            limit: Maximum results.

        Returns:
            List of error contexts as dictionaries.
        """
        history = self.error_registry.get_error_history(node_id=node_id, limit=limit)
        return [ctx.to_dict() for ctx in history]

    def reset(self) -> None:
        """Reset all error tracking state."""
        self._consecutive_errors = 0
        self._error_aggregations.clear()
        self._node_retry_counts.clear()
        for cb in self._circuit_breakers.values():
            cb.reset()
        logger.info("Error recovery state reset")


class ErrorRecoveryIntegration:
    """
    Integration helper for connecting error recovery to workflow execution.

    Provides convenience methods for common integration patterns.
    """

    def __init__(
        self,
        config: Optional[ErrorRecoveryConfig] = None,
    ) -> None:
        """
        Initialize integration.

        Args:
            config: Recovery configuration.
        """
        self.use_case = ErrorRecoveryUseCase(config=config)
        self._execution_context: Optional["ExecutionContext"] = None

    def set_execution_context(self, context: "ExecutionContext") -> None:
        """
        Set the execution context for recovery operations.

        Args:
            context: Current execution context.
        """
        self._execution_context = context

    async def wrap_node_execution(
        self,
        node_id: NodeId,
        node_type: str,
        execute_func: Callable[..., Any],
        node_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> tuple[bool, Any]:
        """
        Wrap node execution with automatic error handling.

        Args:
            node_id: Node ID.
            node_type: Node type name.
            execute_func: Async function to execute.
            node_config: Node configuration.
            max_retries: Maximum retry attempts.

        Returns:
            Tuple of (success, result_or_error).
        """
        import time

        retry_count = 0
        last_error: Optional[Exception] = None

        while retry_count <= max_retries:
            start_time = time.time()

            try:
                result = await execute_func()
                # Success - record it
                self.use_case.record_success(node_id, node_type)
                return True, result

            except Exception as e:
                last_error = e
                execution_time_ms = (time.time() - start_time) * 1000

                # Handle error
                recovery_result = await self.use_case.handle_error(
                    exception=e,
                    node_id=node_id,
                    node_type=node_type,
                    execution_context=self._execution_context,
                    node_config=node_config,
                    execution_time_ms=execution_time_ms,
                )

                if recovery_result.should_abort:
                    return False, e

                if recovery_result.should_retry:
                    retry_count += 1
                    if recovery_result.retry_delay_ms > 0:
                        await asyncio.sleep(recovery_result.retry_delay_ms / 1000.0)
                    continue

                if recovery_result.should_skip:
                    return False, e

                # Fallback or other action - return failure
                return False, e

        return False, last_error

    def create_custom_handler(
        self,
        name: str,
        handler_func: Callable[[ErrorContext], Optional[RecoveryDecision]],
    ) -> None:
        """
        Register a custom error handler.

        Args:
            name: Handler name.
            handler_func: Function that takes ErrorContext and returns RecoveryDecision.
        """
        self.use_case.error_registry.register_custom_handler(name, handler_func)

    def get_report(self) -> Dict[str, Any]:
        """Get error report."""
        return self.use_case.get_error_report()


# Convenience function for one-off error handling
async def handle_node_error(
    exception: Exception,
    node_id: NodeId,
    node_type: str,
    execution_context: "ExecutionContext",
    **kwargs: Any,
) -> RecoveryResult:
    """
    Handle a node error using the global error recovery system.

    Convenience function for simple error handling without explicit use case creation.

    Args:
        exception: The exception that occurred.
        node_id: ID of the node where error occurred.
        node_type: Type/class name of the node.
        execution_context: Current execution context.
        **kwargs: Additional arguments passed to handle_error.

    Returns:
        RecoveryResult indicating what action was taken.
    """
    use_case = ErrorRecoveryUseCase()
    return await use_case.handle_error(
        exception=exception,
        node_id=node_id,
        node_type=node_type,
        execution_context=execution_context,
        **kwargs,
    )
