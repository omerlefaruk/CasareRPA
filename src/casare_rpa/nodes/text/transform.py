"""
Text transformation nodes.

This module provides nodes for transforming multiple texts:
- Joining list of strings
- Formatting (future)
- Templating (future)
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "items",
        PropertyType.LIST,
        required=True,
        label="Items",
        tooltip="List of items to join",
    ),
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default="",
        label="Separator",
        tooltip="Separator to use (default: empty string)",
    ),
)
@node(category="text")
class TextJoinNode(BaseNode):
    """
    Join a list of strings with a separator.

    Config:
        separator: Separator to use (default: empty string)

    Inputs:
        items: List of items to join

    Outputs:
        result: Joined string
    """

    # @category: data
    # @requires: none
    # @ports: items -> result

    def __init__(self, node_id: str, name: str = "Text Join", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextJoinNode"

    def _define_ports(self) -> None:
        self.add_input_port("items", DataType.LIST, required=True)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_input_value("items", context)
            if not isinstance(items, list):
                # Try to handle single value or None
                if items is None:
                    items = []
                else:
                    items = [items]

            separator = self.get_parameter("separator", "")

            # Resolve {{variable}} patterns in separator

            result = separator.join(str(item) for item in items)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result, "count": len(items)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextJoinNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
