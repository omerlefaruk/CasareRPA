"""
Text manipulation nodes.

This module provides nodes for modifying text content:
- Splitting
- Replacing
- Trimming
- Changing case
- Padding
- Reversing
- Handling lines
"""

import re
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
from casare_rpa.utils import safe_int


def _strip_var_wrapper(value: str) -> str:
    """Strip {{}} wrapper from variable reference if present."""
    value = value.strip()
    if value.startswith("{{") and value.endswith("}}"):
        return value[2:-2].strip()
    return value


def _resolve_string_param(
    node: BaseNode, context: ExecutionContext, param_name: str, default: str = ""
) -> str:
    """Resolve a string parameter from input port, parameter, or variable reference."""
    # Try input port first
    value = node.get_input_value(param_name)
    if value is not None:
        return str(value)

    # Try parameter
    param = node.get_parameter(param_name, default)

    # If it's a string that looks like a variable reference
    if isinstance(param, str) and param:
        var_name = _strip_var_wrapper(param)
        if var_name != param:  # Had wrapper, resolve as variable
            resolved = context.get_variable(var_name)
            if resolved is not None:
                return str(resolved)
        return param

    return str(param) if param is not None else default


@node_schema(
    PropertyDef(
        "max_split",
        PropertyType.INTEGER,
        default=-1,
        label="Max Split",
        tooltip="Maximum number of splits (-1 for unlimited)",
    ),
)
@executable_node
class TextSplitNode(BaseNode):
    """
    Split a string into a list.

    Config:
        max_split: Maximum number of splits (default: -1 for unlimited)

    Inputs:
        text: The text to split
        separator: The separator to split on (default: whitespace)

    Outputs:
        result: List of split parts
        count: Number of parts
    """

    # @category: data
    # @requires: none
    # @ports: text, separator -> result, count

    def __init__(self, node_id: str, name: str = "Text Split", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextSplitNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        # separator is optional - defaults to whitespace splitting
        self.add_input_port("separator", DataType.STRING, required=False)
        self.add_output_port("result", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            separator = self.get_input_value("separator", context)
            max_split = safe_int(self.get_parameter("max_split", -1), -1)

            # Resolve {{variable}} patterns in separator
            if separator is not None:
                separator = context.resolve_value(separator)

            if separator is None or separator == "":
                result = (
                    text.split(maxsplit=max_split) if max_split >= 0 else text.split()
                )
            else:
                result = (
                    text.split(separator, maxsplit=max_split)
                    if max_split >= 0
                    else text.split(separator)
                )

            self.set_output_value("result", result)
            self.set_output_value("count", len(result))
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(result)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextSplitNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "count",
        PropertyType.INTEGER,
        default=-1,
        label="Max Replacements",
        tooltip="Maximum number of replacements (-1 for all)",
    ),
    PropertyDef(
        "use_regex",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Regex",
        tooltip="Use regex for matching",
    ),
    PropertyDef(
        "ignore_case",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Case",
        tooltip="Case-insensitive matching",
    ),
    PropertyDef(
        "multiline",
        PropertyType.BOOLEAN,
        default=False,
        label="Multiline",
        tooltip="^ and $ match line boundaries",
    ),
    PropertyDef(
        "dotall",
        PropertyType.BOOLEAN,
        default=False,
        label="Dot All",
        tooltip=". matches newlines",
    ),
)
@executable_node
class TextReplaceNode(BaseNode):
    """
    Replace occurrences in a string.

    Config:
        count: Maximum replacements (default: -1 for all)
        use_regex: Use regex for matching (default: False)
        ignore_case: Case-insensitive matching (default: False)
        multiline: ^ and $ match line boundaries (default: False)
        dotall: . matches newlines (default: False)

    Inputs:
        text: The text to modify
        old_value: Value to replace (or regex pattern)
        new_value: Replacement value

    Outputs:
        result: Modified text
        replacements: Number of replacements made
    """

    # @category: data
    # @requires: none
    # @ports: text, old_value, new_value -> result, replacements

    def __init__(self, node_id: str, name: str = "Text Replace", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextReplaceNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("old_value", DataType.STRING, required=False)
        self.add_input_port("new_value", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("replacements", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            old_value = str(self.get_input_value("old_value", context) or "")
            new_value = str(self.get_input_value("new_value", context) or "")

            # Resolve {{variable}} patterns
            old_value = context.resolve_value(old_value)
            new_value = context.resolve_value(new_value)

            count = safe_int(self.get_parameter("count", -1), -1)
            use_regex = self.get_parameter("use_regex", False)

            if use_regex:
                # Build regex flags
                flags = 0
                if self.get_parameter("ignore_case", False):
                    flags |= re.IGNORECASE
                if self.get_parameter("multiline", False):
                    flags |= re.MULTILINE
                if self.get_parameter("dotall", False):
                    flags |= re.DOTALL

                if count >= 0:
                    result, replacements = re.subn(
                        old_value, new_value, text, count=count, flags=flags
                    )
                else:
                    result, replacements = re.subn(
                        old_value, new_value, text, flags=flags
                    )
            else:
                original_count = text.count(old_value)
                if count >= 0:
                    result = text.replace(old_value, new_value, count)
                    replacements = min(count, original_count)
                else:
                    result = text.replace(old_value, new_value)
                    replacements = original_count

            self.set_output_value("result", result)
            self.set_output_value("replacements", replacements)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"replacements": replacements},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="both",
        choices=["both", "left", "right"],
        label="Trim Mode",
        tooltip="Trim from both sides, left only, or right only",
    ),
    PropertyDef(
        "characters",
        PropertyType.STRING,
        default="",
        label="Characters to Trim",
        tooltip="Characters to trim (default: whitespace)",
    ),
)
@executable_node
class TextTrimNode(BaseNode):
    """
    Trim whitespace from a string.

    Config:
        mode: 'both', 'left', 'right' (default: both)
        characters: Characters to trim (default: whitespace)

    Inputs:
        text: The text to trim

    Outputs:
        result: Trimmed text
    """

    # @category: data
    # @requires: none
    # @ports: text -> result

    def __init__(self, node_id: str, name: str = "Text Trim", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextTrimNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            mode = self.get_parameter("mode", "both")
            chars = self.get_parameter("characters", "")

            # Resolve {{variable}} patterns in characters
            if chars:
                chars = context.resolve_value(chars)
                chars_arg = chars
            else:
                chars_arg = None

            if mode == "left":
                result = text.lstrip(chars_arg)
            elif mode == "right":
                result = text.rstrip(chars_arg)
            else:
                result = text.strip(chars_arg)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextTrimNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "case",
        PropertyType.CHOICE,
        default="lower",
        choices=["upper", "lower", "title", "capitalize", "swapcase"],
        label="Case Transform",
        tooltip="Case transformation to apply",
    ),
)
@executable_node
class TextCaseNode(BaseNode):
    """
    Change the case of a string.

    Config:
        case: 'upper', 'lower', 'title', 'capitalize', 'swapcase' (default: lower)

    Inputs:
        text: The text to transform

    Outputs:
        result: Transformed text
    """

    # @category: data
    # @requires: none
    # @ports: text -> result

    def __init__(self, node_id: str, name: str = "Text Case", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextCaseNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            case = self.get_parameter("case", "lower")

            if case == "upper":
                result = text.upper()
            elif case == "lower":
                result = text.lower()
            elif case == "title":
                result = text.title()
            elif case == "capitalize":
                result = text.capitalize()
            elif case == "swapcase":
                result = text.swapcase()
            else:
                result = text

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="left",
        choices=["left", "right", "center"],
        label="Pad Mode",
        tooltip="Pad left, right, or center",
    ),
    PropertyDef(
        "fill_char",
        PropertyType.STRING,
        default=" ",
        label="Fill Character",
        tooltip="Character to use for padding",
    ),
)
@executable_node
class TextPadNode(BaseNode):
    """
    Pad a string to a certain length.

    Config:
        mode: 'left', 'right', 'center' (default: left)
        fill_char: Character to use for padding (default: space)

    Inputs:
        text: The text to pad
        length: Target length

    Outputs:
        result: Padded text
    """

    # @category: data
    # @requires: none
    # @ports: text, length -> result

    def __init__(self, node_id: str, name: str = "Text Pad", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextPadNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("length", DataType.INTEGER, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            length = safe_int(self.get_input_value("length", context), 0)
            mode = self.get_parameter("mode", "left")
            fill_char = self.get_parameter("fill_char", " ")

            # Resolve {{variable}} patterns in fill_char
            fill_char = context.resolve_value(fill_char)

            if len(fill_char) != 1:
                fill_char = " "

            if mode == "right":
                result = text.ljust(length, fill_char)
            elif mode == "center":
                result = text.center(length, fill_char)
            else:  # left
                result = text.rjust(length, fill_char)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextPadNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class TextReverseNode(BaseNode):
    """
    Reverse a string.

    Inputs:
        text: The text to reverse

    Outputs:
        result: Reversed text
    """

    # @category: data
    # @requires: none
    # @ports: text -> result

    def __init__(self, node_id: str, name: str = "Text Reverse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextReverseNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            result = text[::-1]

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextReverseNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="split",
        choices=["split", "join"],
        label="Mode",
        tooltip="Split text into lines or join lines into text",
    ),
    PropertyDef(
        "line_separator",
        PropertyType.CHOICE,
        default="newline",
        choices=["newline", "crlf", "comma"],
        label="Line Separator",
        tooltip="Separator for join mode (newline=\n, crlf=\r\n)",
    ),
    PropertyDef(
        "remove_empty",
        PropertyType.BOOLEAN,
        default=False,
        label="Remove Empty Lines",
        tooltip="Remove empty lines when splitting",
    ),
)
@executable_node
class TextLinesNode(BaseNode):
    """
    Split text into lines or join lines into text.

    Config:
        mode: 'split' or 'join' (default: split)
        line_separator: Line separator for join (default: newline)
        remove_empty: Remove empty lines when splitting (default: False)

    Inputs:
        text: Text to split (split mode)
        lines: List of strings to join (join mode)

    Outputs:
        lines: List of strings (split mode)
        text: Joined text (join mode)
        count: Number of lines
    """

    # @category: data
    # @requires: none
    # @ports: text/lines -> lines/text, count

    def __init__(self, node_id: str, name: str = "Text Lines", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextLinesNode"

    def _define_ports(self) -> None:
        # Dynamic ports based on mode? No, just add all, but document usage
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("lines", DataType.LIST, required=False)
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("lines", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            mode = self.get_parameter("mode", "split")
            separator_key = self.get_parameter("line_separator", "newline")
            remove_empty = self.get_parameter("remove_empty", False)

            separators = {
                "newline": "\n",
                "crlf": "\r\n",
                "comma": ",",
            }
            separator = separators.get(separator_key, "\n")

            if mode == "split":
                text = str(self.get_input_value("text", context) or "")

                # Split by newline handles various line endings better usually
                lines = text.splitlines()

                if remove_empty:
                    lines = [line for line in lines if line]

                self.set_output_value("lines", lines)
                self.set_output_value("count", len(lines))

                return {
                    "success": True,
                    "data": {"count": len(lines), "mode": "split"},
                    "next_nodes": ["exec_out"],
                }

            else:  # join
                lines_input = self.get_input_value("lines", context)
                if not isinstance(lines_input, list):
                    lines_input = []

                text_result = separator.join(str(x) for x in lines_input)

                self.set_output_value("text", text_result)
                self.set_output_value("count", len(lines_input))

                return {
                    "success": True,
                    "data": {"count": len(lines_input), "mode": "join"},
                    "next_nodes": ["exec_out"],
                }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextLinesNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
