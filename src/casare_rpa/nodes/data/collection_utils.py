"""
Collection Node Utilities

Shared utilities for list and dictionary operation nodes including:
- Variable resolution helpers
- Error handling decorators
- Common validation functions

This module reduces duplication across list_nodes.py and dict_nodes.py.
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionResult

T = TypeVar("T")


def strip_var_wrapper(value: str) -> str:
    """Strip {{}} wrapper from variable reference if present.

    Args:
        value: String that may contain {{variable}} wrapper

    Returns:
        The inner variable name or original value
    """
    value = value.strip()
    if value.startswith("{{") and value.endswith("}}"):
        return value[2:-2].strip()
    return value


def resolve_param(
    node_instance: BaseNode,
    context: ExecutionContext,
    port_name: str,
    param_name: Optional[str] = None,
    default: Any = None,
    type_cast: Optional[Callable[[Any], T]] = None,
) -> Union[Any, T]:
    """Resolve a parameter from input port, parameter, or variable reference.

    Priority order:
    1. Input port value (from connection)
    2. Parameter value (direct value)
    3. Variable reference (string -> context.get_variable)

    Args:
        node_instance: The node instance
        context: Execution context
        port_name: Name of the input port
        param_name: Name of the parameter (defaults to port_name)
        default: Default value if not found
        type_cast: Optional function to cast the result type

    Returns:
        Resolved value, optionally cast to specified type
    """
    if param_name is None:
        param_name = port_name

    # Try input port first
    value = node_instance.get_input_value(port_name)
    if value is not None:
        if type_cast:
            return type_cast(value)
        return value

    # Try parameter
    param = node_instance.get_parameter(param_name, default)

    # If string, resolve as variable reference
    if isinstance(param, str) and param:
        var_name = strip_var_wrapper(param)
        resolved = context.get_variable(var_name)
        if resolved is not None:
            if type_cast:
                return type_cast(resolved)
            return resolved
        # If no variable found, use the param itself (could be literal)
        if var_name != param:  # Had wrapper but variable not found
            return default
        # No wrapper, treat as literal
        if type_cast:
            try:
                return type_cast(param)
            except (ValueError, TypeError):
                return default
        return param

    if type_cast and param is not None:
        try:
            return type_cast(param)
        except (ValueError, TypeError):
            return default

    return param if param is not None else default


def resolve_list(
    node_instance: BaseNode,
    context: ExecutionContext,
    port_name: str = "list",
    param_name: str = "list",
) -> Any:
    """Resolve a list parameter.

    Args:
        node_instance: The node instance
        context: Execution context
        port_name: Name of the input port
        param_name: Name of the parameter

    Returns:
        Resolved list value (or empty list)
    """
    return resolve_param(node_instance, context, port_name, param_name, default=[])


def resolve_dict(
    node_instance: BaseNode,
    context: ExecutionContext,
    port_name: str = "dict",
    param_name: str = "dict",
) -> Any:
    """Resolve a dict parameter.

    Args:
        node_instance: The node instance
        context: Execution context
        port_name: Name of the input port
        param_name: Name of the parameter

    Returns:
        Resolved dict value (or empty dict)
    """
    return resolve_param(node_instance, context, port_name, param_name, default={})


def validate_list(value: Any) -> list:
    """Validate that a value is a list/tuple and convert to list.

    Args:
        value: Value to validate

    Returns:
        The value as a list

    Raises:
        ValueError: If value is not list-like
    """
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    raise ValueError(f"Expected list, got {type(value).__name__}")


def validate_dict(value: Any) -> dict:
    """Validate that a value is a dict.

    Args:
        value: Value to validate

    Returns:
        The value as a dict

    Raises:
        ValueError: If value is not a dict
    """
    if isinstance(value, dict):
        return value
    raise ValueError(f"Expected dict, got {type(value).__name__}")


def get_nested_value(obj: Any, key_path: str, default: Any = None) -> Any:
    """Get a nested value from a dict using dot-separated path.

    Args:
        obj: The object to traverse
        key_path: Dot-separated path (e.g., "user.profile.name")
        default: Value to return if path not found

    Returns:
        The nested value or default
    """
    if not key_path:
        return obj

    current = obj
    for part in key_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def node_execute_wrapper(operation_name: str):
    """Decorator for node execute methods with standard error handling.

    Args:
        operation_name: Name of the operation for logging

    Returns:
        Decorator function

    Usage:
        @node_execute_wrapper("list_append")
        async def execute(self, context):
            # ... implementation
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, context: ExecutionContext) -> ExecutionResult:
            try:
                return await func(self, context)
            except Exception as e:
                logger.error(f"{operation_name} failed: {e}")
                self.error_message = str(e)
                return {"success": False, "error": str(e), "next_nodes": []}

        return wrapper

    return decorator


def success_result(data: dict) -> ExecutionResult:
    """Create a standard success result.

    Args:
        data: Data to include in result

    Returns:
        ExecutionResult dict
    """
    return {"success": True, "data": data, "next_nodes": []}


def error_result(error: str) -> ExecutionResult:
    """Create a standard error result.

    Args:
        error: Error message

    Returns:
        ExecutionResult dict
    """
    return {"success": False, "error": error, "next_nodes": []}


__all__ = [
    "strip_var_wrapper",
    "resolve_param",
    "resolve_list",
    "resolve_dict",
    "validate_list",
    "validate_dict",
    "get_nested_value",
    "node_execute_wrapper",
    "success_result",
    "error_result",
]
