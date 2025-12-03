"""
CasareRPA - String Operation Nodes

Provides nodes for string manipulation including:
- Concatenation
- String formatting
- Regular expression matching and replacement
"""

import re
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, PortType
from casare_rpa.infrastructure.execution import ExecutionContext


@node_schema(
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default="",
        label="Separator",
        tooltip="Separator to insert between strings",
    ),
)
@executable_node
class ConcatenateNode(BaseNode):
    """Node that concatenates multiple strings."""

    def __init__(self, node_id: str, name: str = "Concatenate", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ConcatenateNode"

    def _define_ports(self) -> None:
        self.add_input_port("string_1", PortType.INPUT, DataType.STRING)
        self.add_input_port("string_2", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            s1 = str(self.get_parameter("string_1", ""))
            s2 = str(self.get_parameter("string_2", ""))
            separator = self.get_parameter("separator", "")

            result = f"{s1}{separator}{s2}"

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""

    def __init__(self, node_id: str, name: str = "Format String", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FormatStringNode"

    def _define_ports(self) -> None:
        self.add_input_port("template", PortType.INPUT, DataType.STRING)
        self.add_input_port("variables", PortType.INPUT, DataType.DICT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            template = self.get_parameter("template", "")
            variables = self.get_parameter("variables", {})

            if not isinstance(variables, dict):
                raise ValueError("Variables input must be a dictionary")

            result = template.format(**variables)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "ignore_case",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Case",
        tooltip="Perform case-insensitive matching",
    ),
    PropertyDef(
        "multiline",
        PropertyType.BOOLEAN,
        default=False,
        label="Multiline",
        tooltip="^ and $ match start/end of lines",
    ),
    PropertyDef(
        "dotall",
        PropertyType.BOOLEAN,
        default=False,
        label="Dot All",
        tooltip=". matches newline characters",
    ),
)
@executable_node
class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""

    def __init__(self, node_id: str, name: str = "Regex Match", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RegexMatchNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("pattern", PortType.INPUT, DataType.STRING)
        self.add_output_port("match_found", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("first_match", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("all_matches", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("groups", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("match_count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_parameter("text", "")
            pattern = self.get_parameter("pattern", "")

            flags = 0
            if self.get_parameter("ignore_case", False):
                flags |= re.IGNORECASE
            if self.get_parameter("multiline", False):
                flags |= re.MULTILINE
            if self.get_parameter("dotall", False):
                flags |= re.DOTALL

            matches = list(re.finditer(pattern, text, flags=flags))

            match_found = len(matches) > 0
            first_match = matches[0].group(0) if match_found else ""
            all_matches = [m.group(0) for m in matches]
            groups = list(matches[0].groups()) if match_found else []

            self.set_output_value("match_found", match_found)
            self.set_output_value("first_match", first_match)
            self.set_output_value("all_matches", all_matches)
            self.set_output_value("groups", groups)
            self.set_output_value("match_count", len(matches))

            return {
                "success": True,
                "data": {
                    "match_found": match_found,
                    "first_match": first_match,
                    "all_matches": all_matches,
                    "groups": groups,
                    "match_count": len(matches),
                },
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Regex match failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "ignore_case",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Case",
        tooltip="Perform case-insensitive replacement",
    ),
    PropertyDef(
        "multiline",
        PropertyType.BOOLEAN,
        default=False,
        label="Multiline",
        tooltip="^ and $ match start/end of lines",
    ),
    PropertyDef(
        "dotall",
        PropertyType.BOOLEAN,
        default=False,
        label="Dot All",
        tooltip=". matches newline characters",
    ),
    PropertyDef(
        "max_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Count",
        tooltip="Maximum number of replacements (0 = unlimited)",
    ),
)
@executable_node
class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""

    def __init__(self, node_id: str, name: str = "Regex Replace", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RegexReplaceNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("pattern", PortType.INPUT, DataType.STRING)
        self.add_input_port("replacement", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_parameter("text", "")
            pattern = self.get_parameter("pattern", "")
            replacement = self.get_parameter("replacement", "")

            flags = 0
            if self.get_parameter("ignore_case", False):
                flags |= re.IGNORECASE
            if self.get_parameter("multiline", False):
                flags |= re.MULTILINE
            if self.get_parameter("dotall", False):
                flags |= re.DOTALL

            max_count = int(self.get_parameter("max_count", 0))
            if max_count > 0:
                result, count = re.subn(
                    pattern, replacement, text, count=max_count, flags=flags
                )
            else:
                result, count = re.subn(pattern, replacement, text, flags=flags)

            self.set_output_value("result", result)
            self.set_output_value("count", count)
            return {
                "success": True,
                "data": {"result": result, "count": count},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Regex replace failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
]
