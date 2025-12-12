"""
Text analysis nodes.

This module provides nodes for analyzing text:
- Counting words/characters/lines
"""

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@node_schema(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="characters",
        choices=["characters", "words", "lines"],
        label="Count Mode",
        tooltip="What to count",
    ),
    PropertyDef(
        "exclude_whitespace",
        PropertyType.BOOLEAN,
        default=False,
        label="Exclude Whitespace",
        tooltip="Exclude whitespace from character count",
    ),
)
@executable_node
class TextCountNode(BaseNode):
    """
    Count characters, words, or lines in text.

    Config:
        mode: 'characters', 'words', 'lines' (default: characters)
        exclude_whitespace: Exclude whitespace from character count (default: False)

    Inputs:
        text: The text to analyze

    Outputs:
        count: The resulting count
    """

    # @category: data
    # @requires: none
    # @ports: text -> count

    def __init__(self, node_id: str, name: str = "Text Count", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextCountNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            mode = self.get_parameter("mode", "characters")
            exclude_whitespace = self.get_parameter("exclude_whitespace", False)

            if mode == "words":
                # Split by whitespace to mock words
                count = len(text.split())
            elif mode == "lines":
                count = len(text.splitlines())
            else:  # characters
                if exclude_whitespace:
                    text = "".join(text.split())
                count = len(text)

            self.set_output_value("count", count)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextCountNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
