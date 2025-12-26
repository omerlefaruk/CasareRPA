"""
Standardized error handling decorator for node execute methods.

This decorator eliminates the repetitive try/except/log/status pattern found
in 446+ node execute() methods across the codebase.

Usage:
    @error_handler()
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # Just the happy path - errors handled automatically
        result = await self.do_work()
        return {"success": True, "data": result, "next_nodes": ["exec_out"]}

    # With custom options:
    @error_handler(
        log_format="{class_name} failed on selector: {error}",
        include_traceback=True,
    )
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from casare_rpa.domain.interfaces.logger import LoggerService

P = ParamSpec("P")
T = TypeVar("T")


def _get_logger():
    """Lazy getter for logger - handles unconfigured state gracefully."""
    try:
        return LoggerService.get()
    except RuntimeError:
        # Logger not configured yet - use a fallback
        import logging

        return logging.getLogger(__name__)


def error_handler(
    *,
    log_format: str = "{class_name}: {error}",
    set_status: bool = True,
    include_traceback: bool = False,
    reraise: bool = False,
    error_outputs: dict[str, Any] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for standardized error handling in node execute methods.

    Wraps execute methods with try/except, handles status updates, logging,
    and returns a standardized error result. Supports both async and sync methods.

    Eliminates the repetitive pattern:
        try:
            # do work
            self.status = NodeStatus.SUCCESS
            return {"success": True, "data": result, "next_nodes": ["exec_out"]}
        except Exception as e:
            self.status = NodeStatus.ERROR
            _get_logger().error(f"NodeName: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    Args:
        log_format: Log message format string.
            Supports placeholders: {class_name}, {error}, {node_id}, {node_type}
        set_status: Whether to set self.status on success/failure.
            Default True - sets NodeStatus.SUCCESS on success, NodeStatus.ERROR on failure.
        include_traceback: Whether to include full traceback in error logs.
            Default False - only logs the exception message.
        reraise: Whether to re-raise the exception after handling.
            Default False - returns error result instead of raising.
        error_outputs: Additional outputs to set on error (e.g., {"success": False}).
            These are set via self.set_output_value() if the method exists.

    Returns:
        Decorated function with standardized error handling.

    Example:
        @error_handler()
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            result = await self.do_work()
            self.set_output_value("data", result)
            return {"success": True, "data": result, "next_nodes": ["exec_out"]}

        # With custom log format and traceback:
        @error_handler(
            log_format="{class_name}[{node_id}] failed: {error}",
            include_traceback=True,
            error_outputs={"success": False},
        )
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> dict[str, Any]:
            # Import here to avoid circular imports
            from casare_rpa.domain.value_objects.types import NodeStatus

            try:
                result = await func(self, *args, **kwargs)

                # Set success status if result indicates success
                if set_status and hasattr(self, "status"):
                    # Check if result is a dict with success key
                    if isinstance(result, dict) and result.get("success", True):
                        self.status = NodeStatus.SUCCESS

                return result

            except Exception as e:
                return _handle_error(
                    self,
                    e,
                    log_format=log_format,
                    set_status=set_status,
                    include_traceback=include_traceback,
                    reraise=reraise,
                    error_outputs=error_outputs,
                )

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> dict[str, Any]:
            # Import here to avoid circular imports
            from casare_rpa.domain.value_objects.types import NodeStatus

            try:
                result = func(self, *args, **kwargs)

                # Set success status if result indicates success
                if set_status and hasattr(self, "status"):
                    if isinstance(result, dict) and result.get("success", True):
                        self.status = NodeStatus.SUCCESS

                return result

            except Exception as e:
                return _handle_error(
                    self,
                    e,
                    log_format=log_format,
                    set_status=set_status,
                    include_traceback=include_traceback,
                    reraise=reraise,
                    error_outputs=error_outputs,
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _handle_error(
    node_instance: Any,
    error: Exception,
    *,
    log_format: str,
    set_status: bool,
    include_traceback: bool,
    reraise: bool,
    error_outputs: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Internal helper to handle errors consistently.

    Extracted to avoid code duplication between async and sync wrappers.

    Args:
        node_instance: The node instance (self)
        error: The caught exception
        log_format: Format string for log message
        set_status: Whether to set NodeStatus.ERROR
        include_traceback: Whether to log full traceback
        reraise: Whether to re-raise after handling
        error_outputs: Additional outputs to set on error

    Returns:
        Standardized error result dict
    """
    # Import here to avoid circular imports
    from casare_rpa.domain.value_objects.types import NodeStatus

    # Set error status
    if set_status and hasattr(node_instance, "status"):
        node_instance.status = NodeStatus.ERROR

    # Gather node information for log message
    class_name = node_instance.__class__.__name__
    node_id = getattr(node_instance, "node_id", getattr(node_instance, "id", "unknown"))
    node_type = getattr(node_instance, "node_type", class_name)

    # Format and log error message
    error_msg = log_format.format(
        class_name=class_name,
        error=str(error),
        node_id=node_id,
        node_type=node_type,
    )

    if include_traceback:
        _get_logger().exception(error_msg)
    else:
        _get_logger().error(error_msg)

    # Set error outputs if specified
    if error_outputs and hasattr(node_instance, "set_output_value"):
        for key, value in error_outputs.items():
            try:
                node_instance.set_output_value(key, value)
            except Exception as output_err:
                _get_logger().debug(f"Failed to set error output '{key}': {output_err}")

    # Re-raise if requested
    if reraise:
        raise error

    # Return standardized error result
    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
        "next_nodes": [],
    }
