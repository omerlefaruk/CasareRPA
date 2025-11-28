"""
CasareRPA - Node Decorators

Provides decorators for common node patterns:
- @executable_node: Auto-adds exec_in/exec_out ports
"""

from typing import Type, TypeVar

from casare_rpa.domain.value_objects.types import DataType, PortType

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
