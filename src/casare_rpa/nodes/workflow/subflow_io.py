"""
Subflow I/O Nodes for CasareRPA.

These nodes define the boundary interface for a subflow.
- SubflowInputNode: Receives data from the caller into the subflow.
- SubflowOutputNode: Sends data from the subflow back to the caller.
"""

from typing import Any

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef(
        "port_name",
        PropertyType.STRING,
        default="input",
        label="Port Name",
        description="Name of the input port on the parent Subflow node",
    )
)
@node(
    category="workflow",
    exec_inputs=[],  # Data only
    exec_outputs=[],
)
class SubflowInputNode(BaseNode):
    """
    Defines an input port for the subflow.
    Data flowing out of this node's 'value' port comes from the subflow caller.
    """

    def __init__(self, node_id: str = "", config: dict[str, Any] | None = None):
        super().__init__(node_id, config)
        self.node_type = "SubflowInputNode"
        self.name = "Subflow Input"

    def _define_ports(self) -> None:
        # One output port to pass data into the subflow internal graph
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context) -> dict:
        # The value is expected to be in the context under the port name
        # set by the SubflowExecutor
        port_name = self.get_parameter("port_name", "input")
        val = context.get_variable(port_name)
        return {"value": val}


@properties(
    PropertyDef(
        "port_name",
        PropertyType.STRING,
        default="output",
        label="Port Name",
        description="Name of the output port on the parent Subflow node",
    ),
    PropertyDef(
        "value",
        PropertyType.ANY,
        label="Value",
        description="Data to return from subflow",
    ),
)
@node(
    category="workflow",
    exec_inputs=[],  # Data only
    exec_outputs=[],
)
class SubflowOutputNode(BaseNode):
    """
    Defines an output port for the subflow.
    Data connected to this node's 'value' port is returned to the subflow caller.
    """

    def __init__(self, node_id: str = "", config: dict[str, Any] | None = None):
        super().__init__(node_id, config)
        self.node_type = "SubflowOutputNode"
        self.name = "Subflow Output"

    def _define_ports(self) -> None:
        # One input port to receive data from the subflow internal graph
        self.add_input_port("value", DataType.ANY)

    async def execute(self, context) -> dict:
        # The value received here will be collected by the SubflowExecutor
        val = self.get_parameter("value")
        port_name = self.get_parameter("port_name", "output")
        # SubflowExecutor typically looks at context variables or node results
        context.set_variable(port_name, val)
        return {"result": val}
