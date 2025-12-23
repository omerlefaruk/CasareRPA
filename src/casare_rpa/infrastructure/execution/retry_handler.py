"""
CasareRPA - Retry Handler for Node Execution

Provides exponential backoff retry logic for node execution.
Uses NodeMetadata from @node decorator to configure retry behavior.
"""

import asyncio
from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.entities.base_node import BaseNode
    from casare_rpa.domain.interfaces import IExecutionContext
    from casare_rpa.domain.value_objects.node_metadata import NodeMetadata
    from casare_rpa.domain.value_objects.types import NodeResult


class RetryHandler:
    """
    Handles node execution retries with exponential backoff.

    Uses NodeMetadata from @node decorator to configure:
    - Max retry attempts (retries field)
    - Base delay between retries (retry_delay in seconds)
    - Backoff multiplier (retry_backoff)
    - Jitter for avoiding thundering herd (retry_jitter)
    - Exception types to retry on (retry_on tuple)

    Example:
        handler = RetryHandler()
        result = await handler.execute_with_retry(
            node=my_node,
            context=execution_context,
            execute_fn=actual_execute_function,
        )
    """

    async def execute_with_retry(
        self,
        node: "BaseNode",
        context: "IExecutionContext",
        execute_fn: Callable[["BaseNode", "IExecutionContext"], Coroutine[Any, Any, "NodeResult"]],
    ) -> "NodeResult":
        """
        Execute a node with retry logic based on NodeMetadata configuration.

        Args:
            node: The node to execute.
            context: Execution context providing runtime services.
            execute_fn: The actual execution function to call.

        Returns:
            NodeResult from successful execution or final failure.
        """
        from casare_rpa.domain.value_objects.execution_metadata import ExecutionMetadata
        from casare_rpa.domain.value_objects.types import NodeResult

        # Get metadata from node (if @node decorator was used)
        metadata: NodeMetadata | None = getattr(node, "__node_meta__", None)
        max_attempts = (metadata.retries + 1) if metadata and metadata.retries > 0 else 1

        last_error: str = ""

        for attempt in range(1, max_attempts + 1):
            # Create execution metadata for this attempt
            exec_meta = ExecutionMetadata(
                node_id=node.node_id,
                node_type=node.node_type,
                attempt=attempt,
                max_attempts=max_attempts,
                start_time=datetime.now(),
            )

            try:
                logger.debug(f"Executing {node.node_type} (attempt {attempt}/{max_attempts})")

                result = await execute_fn(node, context)

                # Handle NodeResult response
                if isinstance(result, NodeResult):
                    result = result.with_metadata(exec_meta.with_end_time())

                    # Check if result requests retry
                    if result.should_retry and attempt < max_attempts:
                        delay = result.retry_delay_ms / 1000.0
                        logger.info(
                            f"Node {node.node_type} requested retry, " f"waiting {delay:.2f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                    return result
                else:
                    # Legacy dict result - wrap in NodeResult
                    if isinstance(result, dict):
                        if result.get("success", False):
                            return NodeResult.ok(**result.get("data", {})).with_metadata(
                                exec_meta.with_end_time()
                            )
                        else:
                            return NodeResult.fail(
                                error=result.get("error", "Unknown error"),
                                code=result.get("error_code", "UNKNOWN_ERROR"),
                            ).with_metadata(exec_meta.with_end_time())
                    return result

            except Exception as e:
                last_error = str(e)

                # Check if we should retry this exception
                should_retry = attempt < max_attempts
                if metadata and metadata.retry_on:
                    should_retry = should_retry and metadata.should_retry_exception(e)

                if should_retry:
                    delay = metadata.get_retry_delay(attempt) if metadata else 1.0
                    logger.warning(
                        f"{node.node_type} failed (attempt {attempt}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{node.node_type} failed after {attempt} attempts: {e}")
                    break

        # All retries exhausted - return failure result
        final_meta = ExecutionMetadata(
            node_id=node.node_id,
            node_type=node.node_type,
            attempt=max_attempts,
            max_attempts=max_attempts,
            start_time=datetime.now(),
        ).with_end_time()

        return NodeResult.fail(
            error=last_error or "Max retries exceeded",
            code="MAX_RETRIES_EXCEEDED",
        ).with_metadata(final_meta)


# Module-level singleton
_retry_handler: RetryHandler | None = None


def get_retry_handler() -> RetryHandler:
    """Get the default retry handler instance (singleton).

    Returns:
        Global RetryHandler instance.
    """
    global _retry_handler
    if _retry_handler is None:
        _retry_handler = RetryHandler()
    return _retry_handler


def reset_retry_handler() -> None:
    """Reset the retry handler singleton (for testing)."""
    global _retry_handler
    _retry_handler = None


__all__ = ["RetryHandler", "get_retry_handler", "reset_retry_handler"]
