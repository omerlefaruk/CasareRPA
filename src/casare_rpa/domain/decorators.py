"""
CasareRPA - Node Decorators

Provides decorators for common node patterns:
- @executable_node: Auto-adds exec_in/exec_out ports
- @node_schema: Declarative property schema for nodes
"""

from typing import Type, TypeVar
import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.value_objects.types import PortType
from casare_rpa.domain.schemas import PropertyDef, NodeSchema

T = TypeVar("T")


def executable_node(cls: Type[T]) -> Type[T]:
    """
    Decorator to automatically add exec_in/exec_out ports to a node class.

    This decorator wraps the node's _define_ports method to prepend
    the standard execution flow ports before defining node-specific ports.

    Usage:
        @executable_node
        class MyNode(BaseNode):
            def _define_ports(self) -> None:
                # Only define data ports here
                self.add_input_port("data", DataType.STRING)
                self.add_output_port("result", DataType.STRING)

    The decorator will automatically add:
        - Input port: exec_in (PortType.EXEC_INPUT)
        - Output port: exec_out (PortType.EXEC_OUTPUT)

    Args:
        cls: The node class to decorate

    Returns:
        The decorated class with modified _define_ports method
    """
    original_define = cls._define_ports

    def wrapped_define(self) -> None:
        """Wrapped _define_ports that adds exec ports first."""
        # Using the existing pattern in the codebase for consistency
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        original_define(self)

    cls._define_ports = wrapped_define
    return cls


def node_schema(*property_defs: PropertyDef, strict: bool = False):
    """
    Decorator to attach property schema to node class.

    Enables declarative property definitions that automatically:
    - Generate default config
    - Validate config on initialization
    - Enable auto-widget generation in visual nodes

    Usage:
        from casare_rpa.domain.schemas import PropertyType, PropertyDef
        from casare_rpa.domain.decorators import node_schema, executable_node

        @node_schema(
            PropertyDef("url", PropertyType.STRING, default="",
                       placeholder="https://example.com"),
            PropertyDef("timeout", PropertyType.INTEGER, default=30000),
            PropertyDef("browser_type", PropertyType.CHOICE, default="chromium",
                       choices=["chromium", "firefox", "webkit"]),
        )
        @executable_node
        class LaunchBrowserNode(BaseNode):
            def __init__(self, node_id: str, name: str = "Launch Browser", **kwargs):
                # Schema decorator automatically merges default_config
                config = kwargs.get("config", {})
                super().__init__(node_id, config)
                self.name = name

    Args:
        *property_defs: Variable number of PropertyDef instances
        strict: If True, raise ValueError on validation failure.
                If False (default), log warning and continue (backward compatible).

    Returns:
        Decorator function that attaches schema to class
    """

    def decorator(cls: Type[T]) -> Type[T]:
        """Inner decorator that modifies the class."""
        # Attach schema to class
        schema = NodeSchema(list(property_defs))
        cls.__node_schema__ = schema

        # Wrap __init__ to inject default config and validate
        original_init = cls.__init__

        def wrapped_init(self, node_id: str, *args, **kwargs):
            """Wrapped __init__ that merges defaults and validates config."""
            config = kwargs.get("config") or {}

            # Extract property values from kwargs (e.g., comment="text" -> config["comment"]="text")
            property_names = {p.name for p in property_defs}
            for prop_name in property_names:
                if prop_name in kwargs and prop_name not in config:
                    config[prop_name] = kwargs[prop_name]

            # Merge with defaults from schema
            default_config = schema.get_default_config()
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value

            # Validate config against schema
            valid, error = schema.validate_config(config)
            if not valid:
                if strict:
                    # Strict mode: Raise exception on validation failure
                    raise ValueError(
                        f"Invalid configuration for {cls.__name__}: {error}"
                    )
                else:
                    # Lenient mode: Log debug and continue (validation at runtime)
                    # This is expected when nodes are created for palette display
                    logger.debug(
                        f"Config validation skipped for {cls.__name__}: {error}"
                    )

            # Update kwargs with merged config
            kwargs["config"] = config

            # Call original __init__
            original_init(self, node_id, *args, **kwargs)

        cls.__init__ = wrapped_init
        return cls

    return decorator
