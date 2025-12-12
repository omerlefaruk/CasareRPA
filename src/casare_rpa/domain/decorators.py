"""
CasareRPA - Node Decorators

Provides decorators for common node patterns:
- @node: Unified decorator combining metadata, retry, and hooks
- @properties: Enhanced property schema decorator
"""

from typing import Callable, List, Optional, Tuple, Type, TypeVar
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
    - Automatically adds exec_in/exec_out ports
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

        # Wrap _define_ports to add exec ports
        if hasattr(cls, "_define_ports"):
            original_define = cls._define_ports

            def wrapped_define(self) -> None:
                """Wrapped _define_ports that adds exec ports first."""
                self.add_exec_input("exec_in")
                self.add_exec_output("exec_out")
                original_define(self)

            cls._define_ports = wrapped_define

        return cls

    return decorator


def properties(
    *property_defs: PropertyDef, strict: bool = False
) -> Callable[[Type[T]], Type[T]]:
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
                    logger.debug(
                        f"Config validation skipped for {cls.__name__}: {error}"
                    )

            kwargs["config"] = config
            original_init(self, node_id, *args, **kwargs)

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
