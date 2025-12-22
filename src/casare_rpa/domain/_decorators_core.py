"""
CasareRPA - Node Decorators

AI-HINT: Core decorators for node development. Use @node and @properties on all nodes.
AI-CONTEXT: These decorators auto-register nodes and define their configuration schema.

Provides decorators for common node patterns:
- @node: Unified decorator combining metadata, retry, and hooks
- @properties: Enhanced property schema decorator
- @error_handler: Standardized error handling for execute methods (simple, no retry)
- @handle_errors: Error handling with retry support (legacy)
- @validate_required: Parameter validation decorator
- @with_timeout: Timeout handling decorator

Usage:
    @properties(
        PropertyDef("selector", PropertyType.SELECTOR, essential=True),
    )
    @node(category="browser")
    class MyNode(BaseNode):
        @error_handler()  # Simple error handling
        @validate_required("selector")
        async def execute(self, ctx):
            ...

    # Or with retry support (legacy):
    @node(category="browser")
    class MyRetryNode(BaseNode):
        @handle_errors(retries=3)
        async def execute(self, ctx):
            ...
"""

import asyncio
import functools
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar
import logging

from casare_rpa.domain.value_objects.node_metadata import NodeMetadata
from casare_rpa.domain.schemas import PropertyDef, NodeSchema

logger = logging.getLogger(__name__)
T = TypeVar("T")


def node(
    name: Optional[str] = None,
    category: str = "General",
    icon: str = "",
    description: str = "",
    # Execution port configuration (non-standard nodes)
    # - Normal nodes default to exec_in + exec_out
    # - Control-flow/trigger/super nodes can override to explicit branch outputs
    exec_inputs: Optional[List[str]] = None,
    exec_outputs: Optional[List[str]] = None,
    # Retry configuration
    retries: int = 0,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_jitter: float = 0.1,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    # Lifecycle hooks
    on_start: Optional[List[Callable]] = None,
    on_success: Optional[List[Callable]] = None,
    on_failure: Optional[List[Callable]] = None,
    on_complete: Optional[List[Callable]] = None,
    # Timeout
    timeout_seconds: Optional[float] = None,
    # Tags
    tags: Optional[List[str]] = None,
) -> Callable[[Type[T]], Type[T]]:
    """
    Unified node decorator with rich metadata and automatic exec ports.

    This decorator:
    - Automatically adds execution ports (configurable for non-standard nodes)
    - Attaches NodeMetadata for runtime behavior (retries, hooks)
    - Sets node identity (name, category, icon)

    Example:
        @node(
            name="Click Element",
            category="browser",
            retries=3,
            retry_delay=1.0,
            on_failure=[take_screenshot],
            tags=["browser", "interaction"],
        )
        @properties(
            PropertyDef("selector", SELECTOR, required=True),
        )
        class ClickElementNode(BrowserNode):
            async def execute(self, ctx: NodeContext) -> NodeResult:
                ...

    Args:
        name: Display name (defaults to class name without "Node" suffix)
        category: Node category for grouping
        icon: Icon identifier for UI
        description: Human-readable description
        exec_inputs: List of execution input port names to enforce.
            Default: ["exec_in"]. Use [] for trigger-like entry nodes.
        exec_outputs: List of execution output port names to enforce.
            Default: ["exec_out"]. Use ["true", "false"] etc. for branching nodes.
        retries: Number of retry attempts on failure
        retry_delay: Initial delay between retries (seconds)
        retry_backoff: Multiplier for exponential backoff
        retry_jitter: Random jitter factor (0.0-1.0)
        retry_on: Tuple of exception types that trigger retry
        on_start: Callbacks invoked before execution
        on_success: Callbacks invoked after successful execution
        on_failure: Callbacks invoked after failed execution
        on_complete: Callbacks invoked after execution (success or failure)
        timeout_seconds: Maximum execution time before timeout
        tags: Tags for filtering and grouping

    Returns:
        Decorator function that attaches metadata and exec ports to class
    """

    def decorator(cls: Type[T]) -> Type[T]:
        # Derive name from class if not provided
        derived_name = name
        if derived_name is None:
            derived_name = cls.__name__.replace("Node", "").replace("_", " ")

        # Create metadata
        metadata = NodeMetadata(
            name=derived_name,
            category=category,
            icon=icon,
            description=description or cls.__doc__ or "",
            retries=retries,
            retry_delay=retry_delay,
            retry_backoff=retry_backoff,
            retry_jitter=retry_jitter,
            retry_on=tuple(retry_on) if retry_on else (),
            on_start=tuple(on_start) if on_start else (),
            on_success=tuple(on_success) if on_success else (),
            on_failure=tuple(on_failure) if on_failure else (),
            on_complete=tuple(on_complete) if on_complete else (),
            timeout_seconds=timeout_seconds,
            tags=tuple(tags) if tags else (),
        )
        cls.__node_meta__ = metadata

        # Also set category on class for compatibility with existing code
        cls.category = category

        # Wrap _define_ports to enforce exec ports
        if hasattr(cls, "_define_ports"):
            original_define = cls._define_ports

            def wrapped_define(self) -> None:
                """Wrapped _define_ports that enforces configured execution ports."""
                from casare_rpa.domain.value_objects.types import DataType

                desired_exec_inputs = exec_inputs if exec_inputs is not None else ["exec_in"]
                desired_exec_outputs = exec_outputs if exec_outputs is not None else ["exec_out"]

                # Let the node define its data ports first.
                original_define(self)

                # Remove any legacy/incorrect exec ports not in the desired set.
                # (Legacy nodes often add DataType.EXEC via add_input_port/add_output_port)
                for port_name, port in list(self.input_ports.items()):
                    if port.data_type == DataType.EXEC and port_name not in desired_exec_inputs:
                        logger.warning(
                            f"[{self.node_type}] Removing unconfigured execution input port '{port_name}'. "
                            f"Add '{port_name}' to @node(exec_inputs=[...]) to preserve it."
                        )
                        self.input_ports.pop(port_name, None)
                for port_name, port in list(self.output_ports.items()):
                    if port.data_type == DataType.EXEC and port_name not in desired_exec_outputs:
                        logger.warning(
                            f"[{self.node_type}] Removing unconfigured execution output port '{port_name}'. "
                            f"Add '{port_name}' to @node(exec_outputs=[...]) to preserve it."
                        )
                        self.output_ports.pop(port_name, None)

                # Ensure desired exec ports exist with correct PortType/typing.
                for port_name in desired_exec_inputs:
                    self.add_exec_input(port_name)
                for port_name in desired_exec_outputs:
                    self.add_exec_output(port_name)

            cls._define_ports = wrapped_define

        return cls

    return decorator


def properties(*property_defs: PropertyDef, strict: bool = False) -> Callable[[Type[T]], Type[T]]:
    """
    Property schema decorator for nodes.

    Features:
    - Sorts properties by order field
    - Supports dynamic defaults
    - Auto-validates config on initialization

    Example:
        @properties(
            PropertyDef("selector", SELECTOR, required=True, order=1),
            PropertyDef("timeout", INTEGER, default=30000, order=10),
        )
        class MyNode(BaseNode):
            ...

    Args:
        *property_defs: Variable number of PropertyDef instances
        strict: If True, raise ValueError on validation failure.
                If False (default), log warning and continue.

    Returns:
        Decorator function that attaches schema to class
    """

    def decorator(cls: Type[T]) -> Type[T]:
        # Sort by order field
        sorted_props = sorted(property_defs, key=lambda p: p.order)
        schema = NodeSchema(list(sorted_props))
        cls.__node_schema__ = schema

        # Wrap __init__ for config handling
        original_init = cls.__init__

        def wrapped_init(self, node_id: str, *args, **kwargs) -> None:
            """Wrapped __init__ that handles config, defaults, and validation."""
            # Handle config passed positionally (legacy pattern from child nodes)
            # If args[0] is a dict and there's also config in kwargs, skip args[0]
            # to prevent "multiple values for argument 'config'" error
            filtered_args = args
            if args and isinstance(args[0], dict) and "config" in kwargs:
                # Config passed both positionally AND via kwargs - skip positional
                filtered_args = args[1:]
            elif args and isinstance(args[0], dict) and "config" not in kwargs:
                # Config passed positionally only - move to kwargs
                kwargs["config"] = args[0]
                filtered_args = args[1:]

            config = kwargs.get("config") or {}

            # Extract property values from kwargs
            property_names = {p.name for p in property_defs}
            for prop_name in property_names:
                if prop_name in kwargs and prop_name not in config:
                    config[prop_name] = kwargs[prop_name]

            # Apply defaults (including dynamic defaults)
            for prop in sorted_props:
                if prop.name not in config or config[prop.name] is None:
                    if prop.dynamic_default:
                        try:
                            config[prop.name] = prop.dynamic_default(config)
                        except Exception as e:
                            logger.debug(
                                f"Dynamic default for {prop.name} failed: {e}, using static default"
                            )
                            config[prop.name] = prop.default
                    else:
                        config[prop.name] = prop.default

            # Validate config against schema
            valid, error = schema.validate_config(config)
            if not valid:
                if strict:
                    raise ValueError(f"Invalid config for {cls.__name__}: {error}")
                else:
                    logger.debug(f"Config validation skipped for {cls.__name__}: {error}")

            kwargs["config"] = config
            original_init(self, node_id, *filtered_args, **kwargs)

        cls.__init__ = wrapped_init
        return cls

    return decorator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_node_metadata(cls: Type) -> Optional[NodeMetadata]:
    """
    Get NodeMetadata from a decorated class.

    Args:
        cls: A class potentially decorated with @node

    Returns:
        NodeMetadata if present, None otherwise
    """
    return getattr(cls, "__node_meta__", None)


def get_node_schema(cls: Type) -> Optional[NodeSchema]:
    """
    Get NodeSchema from a decorated class.

    Args:
        cls: A class potentially decorated with @properties

    Returns:
        NodeSchema if present, None otherwise
    """
    return getattr(cls, "__node_schema__", None)


def has_exec_ports(cls: Type) -> bool:
    """
    Check if a class is decorated with @node.

    Args:
        cls: A node class

    Returns:
        True if class has exec port decoration, False otherwise
    """
    return hasattr(cls, "__node_meta__")


# =============================================================================
# ERROR HANDLING DECORATORS
# =============================================================================


def handle_errors(
    *,
    log_errors: bool = True,
    include_traceback: bool = False,
    retries: int = 0,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for standardized error handling in node execute methods.

    Wraps execute methods with try/except, handles status updates,
    logging, and optional retry logic.

    Args:
        log_errors: Whether to log errors with loguru (default True)
        include_traceback: Include full traceback in error message (default False)
        retries: Number of retry attempts on failure (default 0)
        retry_delay: Initial delay between retries in seconds (default 1.0)
        retry_backoff: Multiplier for exponential backoff (default 2.0)
        retry_on: Tuple of exception types that trigger retry (default all)

    Returns:
        Decorated function with standardized error handling

    Example:
        @handle_errors(retries=3, retry_delay=1.0)
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            result = await risky_operation()
            return {"success": True, "data": result, "next_nodes": ["exec_out"]}
    """
    # Import here to avoid circular imports
    from casare_rpa.domain.value_objects.types import NodeStatus

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, context, *args, **kwargs) -> Dict[str, Any]:
            node_id = getattr(self, "node_id", "unknown")
            node_type = getattr(self, "node_type", self.__class__.__name__)

            last_error: Optional[Exception] = None
            attempt = 0
            current_delay = retry_delay

            while attempt <= retries:
                try:
                    return await func(self, context, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    attempt += 1

                    should_retry = (
                        retry_on is None or isinstance(e, retry_on)
                    ) and attempt <= retries

                    if should_retry:
                        if log_errors:
                            logger.warning(
                                f"[{node_type}:{node_id}] Attempt {attempt}/{retries + 1} "
                                f"failed: {e}. Retrying in {current_delay:.1f}s..."
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= retry_backoff
                    else:
                        break

            self.status = NodeStatus.ERROR
            error_msg = str(last_error)
            if include_traceback:
                error_msg = f"{error_msg}\n{traceback.format_exc()}"

            if log_errors:
                if retries > 0:
                    logger.error(
                        f"[{node_type}:{node_id}] Failed after {attempt} attempts: {last_error}"
                    )
                else:
                    logger.error(f"[{node_type}:{node_id}] Error: {last_error}")

            return {
                "success": False,
                "error": error_msg,
                "error_type": type(last_error).__name__,
                "next_nodes": [],
            }

        return wrapper

    return decorator


def validate_required(
    *param_names: str,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to validate required parameters before execution.

    Checks that specified parameters are not None or empty before
    executing the wrapped function.

    Args:
        *param_names: Names of parameters to validate

    Example:
        @validate_required("file_path", "encoding")
        @handle_errors()
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            file_path = self.get_parameter("file_path")  # Guaranteed not None
            ...
    """
    from casare_rpa.domain.value_objects.types import NodeStatus

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, context, *args, **kwargs) -> Dict[str, Any]:
            missing = []
            for param in param_names:
                value = self.get_parameter(param)
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing.append(param)

            if missing:
                self.status = NodeStatus.ERROR
                error_msg = f"Missing required parameter(s): {', '.join(missing)}"
                logger.error(f"[{self.node_type}:{self.node_id}] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "ValidationError",
                    "next_nodes": [],
                }

            return await func(self, context, *args, **kwargs)

        return wrapper

    return decorator


def with_timeout(
    timeout_param: str = "timeout",
    default_timeout: float = 30.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add timeout handling to execute methods.

    Reads timeout from node config and wraps execution with asyncio.timeout.

    Args:
        timeout_param: Config key for timeout value (default "timeout")
        default_timeout: Default timeout in seconds if not in config

    Example:
        @with_timeout(timeout_param="timeout", default_timeout=60.0)
        @handle_errors()
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            # Will timeout after config["timeout"] seconds
            ...
    """
    from casare_rpa.domain.value_objects.types import NodeStatus

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, context, *args, **kwargs) -> Dict[str, Any]:
            timeout_value = self.config.get(timeout_param, default_timeout)

            # If timeout > 1000, assume it's in milliseconds
            if timeout_value > 1000:
                timeout_seconds = timeout_value / 1000
            else:
                timeout_seconds = timeout_value

            try:
                async with asyncio.timeout(timeout_seconds):
                    return await func(self, context, *args, **kwargs)
            except asyncio.TimeoutError:
                self.status = NodeStatus.ERROR
                error_msg = f"Operation timed out after {timeout_seconds:.1f}s"
                logger.error(f"[{self.node_type}:{self.node_id}] Timeout: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "TimeoutError",
                    "next_nodes": [],
                }

        return wrapper

    return decorator


# NOTE: error_handler decorator is now in casare_rpa.domain.decorators.error_handler
# All exports are managed by the decorators package __init__.py
