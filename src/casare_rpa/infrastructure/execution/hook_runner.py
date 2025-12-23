"""
CasareRPA - Lifecycle Hook Runner for Node Execution

Runs lifecycle hooks defined in NodeMetadata from @node decorator.
Supports sync and async hook functions with proper error isolation.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.entities.base_node import BaseNode
    from casare_rpa.domain.interfaces import IExecutionContext
    from casare_rpa.domain.value_objects.types import NodeResult


@dataclass
class HookContext:
    """Context passed to lifecycle hooks.

    Provides hooks with information about the current execution state
    and access to the execution context for variable manipulation.

    Attributes:
        node_id: Unique identifier of the executing node.
        node_type: Type name of the node (e.g., "ClickElementNode").
        attempt: Current execution attempt (1-based).
        max_attempts: Maximum retry attempts configured.
        config: Node configuration dictionary.
        result: Execution result (available in on_success, on_complete).
        error: Exception that occurred (available in on_failure).
        execution_context: Reference to execution context for variable access.
    """

    node_id: str
    node_type: str
    attempt: int
    max_attempts: int
    config: dict[str, Any] = field(default_factory=dict)
    result: Optional["NodeResult"] = None
    error: Exception | None = None
    execution_context: Optional["IExecutionContext"] = None

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get variable from execution context.

        Args:
            name: Variable name.
            default: Default value if variable not found.

        Returns:
            Variable value or default.
        """
        if self.execution_context:
            return self.execution_context.get_variable(name, default)
        return default

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in execution context.

        Args:
            name: Variable name.
            value: Variable value.
        """
        if self.execution_context:
            self.execution_context.set_variable(name, value)

    @property
    def is_final_attempt(self) -> bool:
        """Check if this is the final retry attempt."""
        return self.attempt >= self.max_attempts

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.result is not None and self.result.success

    @property
    def is_failure(self) -> bool:
        """Check if execution failed."""
        return self.error is not None or (self.result is not None and not self.result.success)


class HookRunner:
    """
    Runs lifecycle hooks for node execution.

    Hook types:
    - on_start: Called before node execution begins
    - on_success: Called when node completes successfully
    - on_failure: Called when node fails (before retry)
    - on_complete: Called after all execution (success or final failure)

    Hooks can be sync or async functions. They receive HookContext
    with execution information and access to the execution context.

    Hook failures are logged but do not interrupt workflow execution.

    Example:
        runner = HookRunner()
        await runner.run_on_start(node, context)
        # ... execute node ...
        await runner.run_on_success(node, context, result, attempt)
    """

    async def run_hooks(
        self,
        hooks: tuple[Callable[..., Any], ...],
        context: HookContext,
    ) -> None:
        """
        Run a tuple of hooks with the given context.

        Hooks are executed sequentially in order. Each hook receives
        the HookContext. Failures in one hook do not prevent subsequent
        hooks from running.

        Args:
            hooks: Tuple of hook callables.
            context: HookContext with execution information.
        """
        for hook in hooks:
            try:
                hook_name = getattr(hook, "__name__", str(hook))
                logger.trace(f"Running hook {hook_name} for {context.node_type}")

                if asyncio.iscoroutinefunction(hook):
                    await hook(context)
                else:
                    result = hook(context)
                    # Handle case where sync function returns coroutine
                    if asyncio.iscoroutine(result):
                        await result

            except Exception as e:
                hook_name = getattr(hook, "__name__", str(hook))
                logger.error(f"Hook {hook_name} failed for {context.node_type}: {e}")
                # Continue with other hooks - don't let hook failures break execution

    async def run_on_start(
        self,
        node: "BaseNode",
        context: "IExecutionContext",
    ) -> None:
        """Run on_start hooks before node execution begins.

        Args:
            node: The node about to execute.
            context: Execution context.
        """
        metadata = getattr(node, "__node_meta__", None)
        if not metadata or not metadata.on_start:
            return

        hook_ctx = HookContext(
            node_id=node.node_id,
            node_type=node.node_type,
            attempt=1,
            max_attempts=metadata.retries + 1,
            config=node.config,
            execution_context=context,
        )
        await self.run_hooks(metadata.on_start, hook_ctx)

    async def run_on_success(
        self,
        node: "BaseNode",
        context: "IExecutionContext",
        result: "NodeResult",
        attempt: int,
    ) -> None:
        """Run on_success hooks after successful execution.

        Args:
            node: The node that executed successfully.
            context: Execution context.
            result: The successful NodeResult.
            attempt: Which attempt succeeded (1-based).
        """
        metadata = getattr(node, "__node_meta__", None)
        if not metadata or not metadata.on_success:
            return

        hook_ctx = HookContext(
            node_id=node.node_id,
            node_type=node.node_type,
            attempt=attempt,
            max_attempts=metadata.retries + 1,
            config=node.config,
            result=result,
            execution_context=context,
        )
        await self.run_hooks(metadata.on_success, hook_ctx)

    async def run_on_failure(
        self,
        node: "BaseNode",
        context: "IExecutionContext",
        error: Exception,
        attempt: int,
    ) -> None:
        """Run on_failure hooks after a failed attempt.

        Called after each failed attempt, before retry (if retry is configured).

        Args:
            node: The node that failed.
            context: Execution context.
            error: The exception that caused failure.
            attempt: Which attempt failed (1-based).
        """
        metadata = getattr(node, "__node_meta__", None)
        if not metadata or not metadata.on_failure:
            return

        hook_ctx = HookContext(
            node_id=node.node_id,
            node_type=node.node_type,
            attempt=attempt,
            max_attempts=metadata.retries + 1,
            config=node.config,
            error=error,
            execution_context=context,
        )
        await self.run_hooks(metadata.on_failure, hook_ctx)

    async def run_on_complete(
        self,
        node: "BaseNode",
        context: "IExecutionContext",
        result: "NodeResult",
        attempt: int,
    ) -> None:
        """Run on_complete hooks after all execution attempts.

        Called once after final success or final failure (all retries exhausted).

        Args:
            node: The node that completed execution.
            context: Execution context.
            result: The final NodeResult (success or failure).
            attempt: Final attempt number (1-based).
        """
        metadata = getattr(node, "__node_meta__", None)
        if not metadata or not metadata.on_complete:
            return

        hook_ctx = HookContext(
            node_id=node.node_id,
            node_type=node.node_type,
            attempt=attempt,
            max_attempts=metadata.retries + 1,
            config=node.config,
            result=result,
            execution_context=context,
        )
        await self.run_hooks(metadata.on_complete, hook_ctx)


# Module-level singleton
_hook_runner: HookRunner | None = None


def get_hook_runner() -> HookRunner:
    """Get the default hook runner instance (singleton).

    Returns:
        Global HookRunner instance.
    """
    global _hook_runner
    if _hook_runner is None:
        _hook_runner = HookRunner()
    return _hook_runner


def reset_hook_runner() -> None:
    """Reset the hook runner singleton (for testing)."""
    global _hook_runner
    _hook_runner = None


__all__ = [
    "HookContext",
    "HookRunner",
    "get_hook_runner",
    "reset_hook_runner",
]
