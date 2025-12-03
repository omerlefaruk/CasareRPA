"""
CasareRPA - Recovery Strategies Implementation

Provides concrete recovery strategy implementations for the error handling framework.

Key Strategies:
- RetryStrategy: Exponential backoff retry with jitter
- SkipStrategy: Skip and continue with logging
- FallbackStrategy: Use alternative workflow path
- CompensateStrategy: Run rollback/compensation operations
- AbortStrategy: Graceful workflow termination
- EscalateStrategy: Human-in-the-loop escalation

Additional Features:
- Circuit breaker pattern integration
- Automatic screenshot capture on UI errors
- Graceful degradation support
"""

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.errors import (
    ErrorCategory,
    ErrorContext,
    RecoveryAction,
    RecoveryDecision,
)
from casare_rpa.domain.value_objects.types import NodeId

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution.execution_context import ExecutionContext


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = auto()  # Normal operation, requests allowed
    OPEN = auto()  # Failures exceeded threshold, requests blocked
    HALF_OPEN = auto()  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    """Number of failures before opening circuit."""

    recovery_timeout_seconds: float = 30.0
    """Time to wait before trying again (half-open state)."""

    success_threshold: int = 2
    """Consecutive successes needed to close circuit."""

    tracked_errors: Optional[Set[str]] = None
    """Error types to track (None = all)."""


@dataclass
class CircuitBreakerState:
    """Runtime state for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.now)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by:
    - Opening circuit after threshold failures
    - Blocking requests while circuit is open
    - Testing recovery with half-open state
    """

    def __init__(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker.
            config: Configuration options.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self._state.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._state.last_failure_time:
                elapsed = datetime.now() - self._state.last_failure_time
                if elapsed.total_seconds() >= self.config.recovery_timeout_seconds:
                    self._transition_to_half_open()
                    return False
            return True
        return False

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is in half-open state (testing)."""
        return self._state.state == CircuitState.HALF_OPEN

    def record_success(self) -> None:
        """Record a successful operation."""
        if self._state.state == CircuitState.HALF_OPEN:
            self._state.success_count += 1
            if self._state.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        else:
            # Reset failure count on success
            self._state.failure_count = 0
            self._state.success_count += 1

    def record_failure(self, error_type: Optional[str] = None) -> None:
        """
        Record a failed operation.

        Args:
            error_type: Type of error (for selective tracking).
        """
        # Check if we should track this error type
        if self.config.tracked_errors and error_type:
            if error_type not in self.config.tracked_errors:
                return

        self._state.failure_count += 1
        self._state.last_failure_time = datetime.now()
        self._state.success_count = 0  # Reset success count

        if self._state.state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            self._transition_to_open()
        elif self._state.failure_count >= self.config.failure_threshold:
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to open state."""
        self._state.state = CircuitState.OPEN
        self._state.last_state_change = datetime.now()
        logger.warning(
            f"Circuit breaker '{self.name}' OPENED after {self._state.failure_count} failures"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        self._state.state = CircuitState.HALF_OPEN
        self._state.last_state_change = datetime.now()
        self._state.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN (testing recovery)")

    def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        self._state.state = CircuitState.CLOSED
        self._state.last_state_change = datetime.now()
        self._state.failure_count = 0
        self._state.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitBreakerState()
        logger.debug(f"Circuit breaker '{self.name}' reset")

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self._state.state.name,
            "failure_count": self._state.failure_count,
            "success_count": self._state.success_count,
            "last_failure": self._state.last_failure_time.isoformat()
            if self._state.last_failure_time
            else None,
            "last_state_change": self._state.last_state_change.isoformat(),
        }


class RecoveryStrategy(ABC):
    """
    Abstract base class for recovery strategies.

    Recovery strategies implement specific recovery behaviors
    that can be applied when errors occur during workflow execution.
    """

    @property
    @abstractmethod
    def action(self) -> RecoveryAction:
        """Get the recovery action this strategy implements."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute the recovery strategy.

        Args:
            context: Error context.
            decision: Recovery decision.
            execution_context: Current execution context.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        pass


@dataclass
class RetryConfig:
    """Configuration for retry strategy."""

    max_retries: int = 3
    """Maximum number of retry attempts."""

    base_delay_ms: int = 1000
    """Base delay between retries (milliseconds)."""

    max_delay_ms: int = 30000
    """Maximum delay between retries (milliseconds)."""

    exponential_base: float = 2.0
    """Base for exponential backoff calculation."""

    jitter_factor: float = 0.2
    """Jitter factor (0-1) to add randomness to delays."""

    retry_on_timeout: bool = True
    """Whether to retry on timeout errors."""


class RetryStrategy(RecoveryStrategy):
    """
    Exponential backoff retry strategy with jitter.

    Implements retry logic with:
    - Exponential backoff (1s, 2s, 4s, 8s...)
    - Random jitter to prevent thundering herd
    - Maximum delay cap
    - Circuit breaker integration
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        """
        Initialize retry strategy.

        Args:
            config: Retry configuration.
            circuit_breaker: Optional circuit breaker for this node/operation.
        """
        self.config = config or RetryConfig()
        self.circuit_breaker = circuit_breaker

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.RETRY

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute retry with backoff.

        Args:
            context: Error context.
            decision: Recovery decision (contains retry_delay_ms).
            execution_context: Current execution context.

        Returns:
            True if ready to retry, False if should not retry.
        """
        # Check circuit breaker
        if self.circuit_breaker and self.circuit_breaker.is_open:
            logger.warning(
                f"Circuit breaker '{self.circuit_breaker.name}' is open - "
                f"skipping retry for node {context.node_id}"
            )
            return False

        # Check retry count
        if context.retry_count >= self.config.max_retries:
            logger.warning(
                f"Max retries ({self.config.max_retries}) exceeded for node {context.node_id}"
            )
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(
                    context.error_code.name if context.error_code else None
                )
            return False

        # Calculate delay
        delay_ms = decision.retry_delay_ms
        if delay_ms <= 0:
            delay_ms = self._calculate_delay(context.retry_count)

        logger.info(
            f"Retrying node {context.node_id} in {delay_ms}ms "
            f"(attempt {context.retry_count + 1}/{self.config.max_retries})"
        )

        # Wait before retry
        await asyncio.sleep(delay_ms / 1000.0)

        return True

    def _calculate_delay(self, retry_count: int) -> int:
        """
        Calculate delay with exponential backoff and jitter.

        Args:
            retry_count: Current retry attempt (0-based).

        Returns:
            Delay in milliseconds.
        """
        # Exponential backoff
        delay = self.config.base_delay_ms * (self.config.exponential_base**retry_count)

        # Add jitter
        jitter_range = delay * self.config.jitter_factor
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = int(delay + jitter)

        # Cap at max delay
        return min(delay, self.config.max_delay_ms)


class SkipStrategy(RecoveryStrategy):
    """
    Skip strategy - skip failed node and continue workflow.

    Logs the skip and allows workflow to continue to next node.
    Useful for non-critical operations.
    """

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.SKIP

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute skip strategy.

        Args:
            context: Error context.
            decision: Recovery decision.
            execution_context: Current execution context.

        Returns:
            True (skip always succeeds).
        """
        logger.warning(
            f"Skipping node {context.node_id} ({context.node_type}) due to error: {context.message}"
        )

        # Record skip in execution context
        execution_context.set_variable(
            f"_skip_{context.node_id}",
            {
                "skipped": True,
                "reason": context.message,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return True


@dataclass
class FallbackConfig:
    """Configuration for fallback strategy."""

    fallback_node_id: Optional[NodeId] = None
    """Node ID to fall back to."""

    fallback_value: Any = None
    """Default value to use."""

    fallback_variable: Optional[str] = None
    """Variable to store fallback value in."""


class FallbackStrategy(RecoveryStrategy):
    """
    Fallback strategy - use alternative path or default value.

    Can:
    - Redirect to a fallback node
    - Use a default value
    - Set a variable for downstream nodes
    """

    def __init__(self, config: Optional[FallbackConfig] = None) -> None:
        """
        Initialize fallback strategy.

        Args:
            config: Fallback configuration.
        """
        self.config = config or FallbackConfig()

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.FALLBACK

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute fallback strategy.

        Args:
            context: Error context.
            decision: Recovery decision (may contain fallback_value).
            execution_context: Current execution context.

        Returns:
            True if fallback applied, False otherwise.
        """
        fallback_value = decision.fallback_value or self.config.fallback_value
        fallback_variable = self.config.fallback_variable

        if fallback_value is not None:
            if fallback_variable:
                execution_context.set_variable(fallback_variable, fallback_value)
                logger.info(
                    f"Fallback: set variable '{fallback_variable}' = {fallback_value}"
                )
            else:
                # Store as output of failed node
                execution_context.set_variable(
                    f"_fallback_{context.node_id}", fallback_value
                )
                logger.info(
                    f"Fallback: stored fallback value for node {context.node_id}"
                )
            return True

        if decision.continue_from_node or self.config.fallback_node_id:
            target = decision.continue_from_node or self.config.fallback_node_id
            logger.info(f"Fallback: redirecting to node {target}")
            # Set marker for orchestrator to pick up
            execution_context.set_variable("_fallback_redirect", target)
            return True

        logger.warning(
            f"Fallback strategy has no fallback value or node configured "
            f"for {context.node_id}"
        )
        return False


@dataclass
class CompensateConfig:
    """Configuration for compensate strategy."""

    compensation_nodes: List[NodeId] = field(default_factory=list)
    """Nodes to execute for compensation (in order)."""

    rollback_variables: List[str] = field(default_factory=list)
    """Variables to rollback/delete."""

    compensation_timeout_seconds: float = 60.0
    """Timeout for compensation operations."""


class CompensateStrategy(RecoveryStrategy):
    """
    Compensation strategy - run rollback operations.

    Executes compensation nodes to undo partial changes.
    Used for maintaining data consistency after failures.
    """

    def __init__(
        self,
        config: Optional[CompensateConfig] = None,
        compensator_func: Optional[Callable[..., Any]] = None,
    ) -> None:
        """
        Initialize compensate strategy.

        Args:
            config: Compensation configuration.
            compensator_func: Custom compensation function.
        """
        self.config = config or CompensateConfig()
        self.compensator_func = compensator_func

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.COMPENSATE

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute compensation strategy.

        Args:
            context: Error context.
            decision: Recovery decision (may contain compensate_nodes).
            execution_context: Current execution context.

        Returns:
            True if compensation succeeded, False otherwise.
        """
        nodes_to_compensate = (
            decision.compensate_nodes or self.config.compensation_nodes
        )

        logger.info(
            f"Starting compensation for node {context.node_id} - "
            f"{len(nodes_to_compensate)} compensation nodes"
        )

        # Rollback variables
        for var_name in self.config.rollback_variables:
            if execution_context.has_variable(var_name):
                execution_context.delete_variable(var_name)
                logger.debug(f"Compensation: deleted variable '{var_name}'")

        # Execute custom compensator if provided
        if self.compensator_func:
            try:
                if asyncio.iscoroutinefunction(self.compensator_func):
                    await self.compensator_func(context, execution_context)
                else:
                    self.compensator_func(context, execution_context)
                logger.info("Custom compensation function executed")
            except Exception as e:
                logger.error(f"Custom compensation function failed: {e}")
                return False

        # Set compensation nodes for orchestrator to execute
        if nodes_to_compensate:
            execution_context.set_variable(
                "_compensation_nodes",
                {
                    "nodes": nodes_to_compensate,
                    "triggered_by": context.node_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        logger.info(f"Compensation prepared for node {context.node_id}")
        return True


class AbortStrategy(RecoveryStrategy):
    """
    Abort strategy - gracefully terminate workflow.

    Stops workflow execution and triggers cleanup.
    Used for critical/unrecoverable errors.
    """

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.ABORT

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute abort strategy.

        Args:
            context: Error context.
            decision: Recovery decision.
            execution_context: Current execution context.

        Returns:
            True (abort always "succeeds" in the sense of being handled).
        """
        logger.error(
            f"ABORTING workflow due to error in node {context.node_id}: {context.message}"
        )

        # Signal stop to execution context
        execution_context.stop_execution()

        # Record abort reason
        execution_context.set_variable(
            "_abort_reason",
            {
                "node_id": context.node_id,
                "node_type": context.node_type,
                "error": context.message,
                "category": context.category.name,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return True


@dataclass
class EscalateConfig:
    """Configuration for escalate strategy."""

    notification_callback: Optional[Callable[[ErrorContext, str], None]] = None
    """Callback to notify human operators."""

    wait_for_response: bool = False
    """Whether to pause workflow waiting for response."""

    timeout_seconds: float = 300.0
    """Timeout waiting for human response."""

    default_action_on_timeout: RecoveryAction = RecoveryAction.SKIP
    """Action to take if timeout expires."""


class EscalateStrategy(RecoveryStrategy):
    """
    Escalation strategy - request human intervention.

    Notifies operators and optionally waits for response.
    Used when automated recovery cannot resolve the issue.
    """

    def __init__(self, config: Optional[EscalateConfig] = None) -> None:
        """
        Initialize escalate strategy.

        Args:
            config: Escalation configuration.
        """
        self.config = config or EscalateConfig()
        self._pending_escalations: Dict[str, asyncio.Event] = {}
        self._escalation_responses: Dict[str, RecoveryAction] = {}

    @property
    def action(self) -> RecoveryAction:
        """Get recovery action."""
        return RecoveryAction.ESCALATE

    async def execute(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute escalation strategy.

        Args:
            context: Error context.
            decision: Recovery decision (contains escalation_message).
            execution_context: Current execution context.

        Returns:
            True if escalation handled, False otherwise.
        """
        escalation_id = f"{context.node_id}_{datetime.now().timestamp()}"
        escalation_message = decision.escalation_message or (
            f"Manual intervention required for node {context.node_id} "
            f"({context.node_type}): {context.message}"
        )

        logger.warning(f"ESCALATION [{escalation_id}]: {escalation_message}")

        # Record escalation
        execution_context.set_variable(
            f"_escalation_{context.node_id}",
            {
                "id": escalation_id,
                "message": escalation_message,
                "node_id": context.node_id,
                "node_type": context.node_type,
                "error": context.message,
                "category": context.category.name,
                "severity": context.severity.name,
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
            },
        )

        # Notify via callback if configured
        if self.config.notification_callback:
            try:
                self.config.notification_callback(context, escalation_message)
            except Exception as e:
                logger.error(f"Escalation notification callback failed: {e}")

        # Wait for response if configured
        if self.config.wait_for_response:
            response_event = asyncio.Event()
            self._pending_escalations[escalation_id] = response_event

            try:
                await asyncio.wait_for(
                    response_event.wait(), timeout=self.config.timeout_seconds
                )

                # Check response
                if escalation_id in self._escalation_responses:
                    response_action = self._escalation_responses.pop(escalation_id)
                    logger.info(
                        f"Escalation {escalation_id} resolved with action: {response_action.name}"
                    )
                    # Update escalation status
                    execution_context.set_variable(
                        f"_escalation_{context.node_id}",
                        {
                            **execution_context.get_variable(
                                f"_escalation_{context.node_id}"
                            ),
                            "status": "resolved",
                            "resolution": response_action.name,
                        },
                    )
                    return True

            except asyncio.TimeoutError:
                logger.warning(
                    f"Escalation {escalation_id} timed out after "
                    f"{self.config.timeout_seconds}s - using default action: "
                    f"{self.config.default_action_on_timeout.name}"
                )
                execution_context.set_variable(
                    f"_escalation_{context.node_id}",
                    {
                        **execution_context.get_variable(
                            f"_escalation_{context.node_id}"
                        ),
                        "status": "timeout",
                        "default_action": self.config.default_action_on_timeout.name,
                    },
                )
            finally:
                self._pending_escalations.pop(escalation_id, None)

        return True

    def resolve_escalation(self, escalation_id: str, action: RecoveryAction) -> bool:
        """
        Resolve a pending escalation.

        Args:
            escalation_id: ID of the escalation to resolve.
            action: Action to take.

        Returns:
            True if escalation was pending and resolved.
        """
        if escalation_id in self._pending_escalations:
            self._escalation_responses[escalation_id] = action
            self._pending_escalations[escalation_id].set()
            return True
        return False


class ScreenshotCapture:
    """
    Utility for capturing screenshots on UI errors.

    Captures browser or desktop screenshots for debugging.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        max_screenshots: int = 100,
    ) -> None:
        """
        Initialize screenshot capture.

        Args:
            output_dir: Directory to save screenshots.
            max_screenshots: Maximum screenshots to retain.
        """
        self.output_dir = output_dir or Path("./error_screenshots")
        self.max_screenshots = max_screenshots
        self._screenshot_count = 0

    async def capture_browser_screenshot(
        self,
        context: ErrorContext,
        execution_context: "ExecutionContext",
    ) -> Optional[str]:
        """
        Capture browser screenshot on error.

        Args:
            context: Error context.
            execution_context: Execution context with browser page.

        Returns:
            Path to screenshot file, or None if capture failed.
        """
        try:
            page = execution_context.get_active_page()
            if not page:
                logger.debug("No active page for screenshot capture")
                return None

            self.output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{context.node_id}_{timestamp}.png"
            filepath = self.output_dir / filename

            await page.screenshot(path=str(filepath), full_page=True)

            self._cleanup_old_screenshots()

            logger.info(f"Error screenshot captured: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.warning(f"Failed to capture browser screenshot: {e}")
            return None

    def capture_desktop_screenshot(
        self,
        context: ErrorContext,
    ) -> Optional[str]:
        """
        Capture desktop screenshot on error.

        Args:
            context: Error context.

        Returns:
            Path to screenshot file, or None if capture failed.
        """
        try:
            import mss

            self.output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"desktop_error_{context.node_id}_{timestamp}.png"
            filepath = self.output_dir / filename

            with mss.mss() as sct:
                sct.shot(mon=-1, output=str(filepath))

            self._cleanup_old_screenshots()

            logger.info(f"Desktop error screenshot captured: {filepath}")
            return str(filepath)

        except ImportError:
            logger.debug("mss not available for desktop screenshot")
            return None
        except Exception as e:
            logger.warning(f"Failed to capture desktop screenshot: {e}")
            return None

    async def capture_for_context(
        self,
        context: ErrorContext,
        execution_context: "ExecutionContext",
    ) -> Optional[str]:
        """
        Capture appropriate screenshot based on error category.

        Args:
            context: Error context.
            execution_context: Execution context.

        Returns:
            Path to screenshot file, or None if capture failed.
        """
        if context.category == ErrorCategory.BROWSER:
            return await self.capture_browser_screenshot(context, execution_context)
        elif context.category == ErrorCategory.DESKTOP:
            return self.capture_desktop_screenshot(context)
        return None

    def _cleanup_old_screenshots(self) -> None:
        """Remove old screenshots if over limit."""
        try:
            screenshots = sorted(
                self.output_dir.glob("*.png"),
                key=lambda p: p.stat().st_mtime,
            )
            while len(screenshots) > self.max_screenshots:
                oldest = screenshots.pop(0)
                oldest.unlink()
                logger.debug(f"Removed old screenshot: {oldest}")
        except Exception as e:
            logger.warning(f"Screenshot cleanup failed: {e}")


class RecoveryStrategyRegistry:
    """
    Registry for recovery strategies.

    Provides access to strategy implementations by action type.
    """

    def __init__(self) -> None:
        """Initialize recovery strategy registry."""
        self._strategies: Dict[RecoveryAction, RecoveryStrategy] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._screenshot_capture = ScreenshotCapture()

        # Register default strategies
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default strategy implementations."""
        self._strategies[RecoveryAction.RETRY] = RetryStrategy()
        self._strategies[RecoveryAction.SKIP] = SkipStrategy()
        self._strategies[RecoveryAction.FALLBACK] = FallbackStrategy()
        self._strategies[RecoveryAction.COMPENSATE] = CompensateStrategy()
        self._strategies[RecoveryAction.ABORT] = AbortStrategy()
        self._strategies[RecoveryAction.ESCALATE] = EscalateStrategy()

    def register_strategy(
        self, action: RecoveryAction, strategy: RecoveryStrategy
    ) -> None:
        """
        Register or replace a recovery strategy.

        Args:
            action: Recovery action type.
            strategy: Strategy implementation.
        """
        self._strategies[action] = strategy
        logger.debug(f"Registered strategy for {action.name}")

    def get_strategy(self, action: RecoveryAction) -> Optional[RecoveryStrategy]:
        """
        Get strategy for a recovery action.

        Args:
            action: Recovery action type.

        Returns:
            Strategy instance, or None if not registered.
        """
        return self._strategies.get(action)

    def get_or_create_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker by name.

        Args:
            name: Circuit breaker identifier.
            config: Configuration (only used if creating new).

        Returns:
            Circuit breaker instance.
        """
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name, config)
        return self._circuit_breakers[name]

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get existing circuit breaker by name.

        Args:
            name: Circuit breaker identifier.

        Returns:
            Circuit breaker instance, or None if not found.
        """
        return self._circuit_breakers.get(name)

    @property
    def screenshot_capture(self) -> ScreenshotCapture:
        """Get screenshot capture utility."""
        return self._screenshot_capture

    async def execute_recovery(
        self,
        context: ErrorContext,
        decision: RecoveryDecision,
        execution_context: "ExecutionContext",
    ) -> bool:
        """
        Execute recovery strategy for a decision.

        Args:
            context: Error context.
            decision: Recovery decision.
            execution_context: Current execution context.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        strategy = self.get_strategy(decision.action)
        if not strategy:
            logger.error(f"No strategy registered for action: {decision.action.name}")
            return False

        # Capture screenshot for UI errors
        if context.is_ui_error and not context.screenshot_path:
            screenshot = await self._screenshot_capture.capture_for_context(
                context, execution_context
            )
            if screenshot:
                context.screenshot_path = screenshot

        return await strategy.execute(context, decision, execution_context)


# Thread-safe singleton holder
from casare_rpa.application.dependency_injection.singleton import Singleton


def _on_create_registry(instance: RecoveryStrategyRegistry) -> None:
    """Callback when registry is created."""
    logger.info("Global recovery strategy registry created")


_strategy_registry_holder = Singleton(
    RecoveryStrategyRegistry,
    name="RecoveryStrategyRegistry",
    on_create=_on_create_registry,
)


def get_recovery_strategy_registry() -> RecoveryStrategyRegistry:
    """
    Get the global recovery strategy registry (singleton).

    Returns:
        Global RecoveryStrategyRegistry instance.
    """
    return _strategy_registry_holder.get()


def reset_recovery_strategy_registry() -> None:
    """Reset the global recovery strategy registry (for testing)."""
    _strategy_registry_holder.reset()
    logger.debug("Global recovery strategy registry reset")
