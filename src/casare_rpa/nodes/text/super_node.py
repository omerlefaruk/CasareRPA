"""
Super Node for CasareRPA Text Operations.

This module provides a consolidated "Text Super Node" that replaces 14
atomic text nodes with action-based dynamic ports and properties.

TextSuperNode (14 operations):
    Search:
        - Substring: Extract substring by index
        - Contains: Check if text contains substring
        - Starts With: Check if text starts with prefix
        - Ends With: Check if text ends with suffix
        - Extract (Regex): Extract text using regex pattern

    Transform:
        - Split: Split text into list
        - Replace: Replace occurrences
        - Trim: Trim whitespace/characters
        - Case: Change case (upper/lower/title/etc.)
        - Pad: Pad text to length
        - Reverse: Reverse text
        - Lines: Split/join lines

    Analyze:
        - Count: Count characters/words/lines
        - Join: Join list with separator
"""

import re
from enum import Enum
from typing import TYPE_CHECKING, Dict, Callable, Awaitable

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef,
    ActionPortConfig,
    DynamicPortSchema,
)
from casare_rpa.utils import safe_int

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class TextAction(str, Enum):
    """Actions available in TextSuperNode."""

    # Search operations
    SUBSTRING = "Substring"
    CONTAINS = "Contains"
    STARTS_WITH = "Starts With"
    ENDS_WITH = "Ends With"
    EXTRACT = "Extract (Regex)"

    # Transform operations
    SPLIT = "Split"
    REPLACE = "Replace"
    TRIM = "Trim"
    CASE = "Case"
    PAD = "Pad"
    REVERSE = "Reverse"
    LINES = "Lines"

    # Analyze operations
    COUNT = "Count"
    JOIN = "Join"


# Port schema for dynamic port visibility
TEXT_PORT_SCHEMA = DynamicPortSchema()

# Substring ports
TEXT_PORT_SCHEMA.register(
    TextAction.SUBSTRING.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("start", DataType.INTEGER),
            PortDef("end", DataType.INTEGER),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Contains ports
TEXT_PORT_SCHEMA.register(
    TextAction.CONTAINS.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("search", DataType.STRING),
        ],
        outputs=[
            PortDef("contains", DataType.BOOLEAN),
            PortDef("position", DataType.INTEGER),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Starts With ports
TEXT_PORT_SCHEMA.register(
    TextAction.STARTS_WITH.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("prefix", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.BOOLEAN),
        ],
    ),
)

# Ends With ports
TEXT_PORT_SCHEMA.register(
    TextAction.ENDS_WITH.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("suffix", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.BOOLEAN),
        ],
    ),
)

# Extract (Regex) ports
TEXT_PORT_SCHEMA.register(
    TextAction.EXTRACT.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("pattern", DataType.STRING),
        ],
        outputs=[
            PortDef("match", DataType.ANY),
            PortDef("groups", DataType.LIST),
            PortDef("found", DataType.BOOLEAN),
        ],
    ),
)

# Split ports
TEXT_PORT_SCHEMA.register(
    TextAction.SPLIT.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("separator", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.LIST),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Replace ports
TEXT_PORT_SCHEMA.register(
    TextAction.REPLACE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("old_value", DataType.STRING),
            PortDef("new_value", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
            PortDef("replacements", DataType.INTEGER),
        ],
    ),
)

# Trim ports
TEXT_PORT_SCHEMA.register(
    TextAction.TRIM.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)

# Case ports
TEXT_PORT_SCHEMA.register(
    TextAction.CASE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)

# Pad ports
TEXT_PORT_SCHEMA.register(
    TextAction.PAD.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("length", DataType.INTEGER),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)

# Reverse ports
TEXT_PORT_SCHEMA.register(
    TextAction.REVERSE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)

# Lines ports
TEXT_PORT_SCHEMA.register(
    TextAction.LINES.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
            PortDef("lines", DataType.LIST),
        ],
        outputs=[
            PortDef("text", DataType.STRING),
            PortDef("lines", DataType.LIST),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Count ports
TEXT_PORT_SCHEMA.register(
    TextAction.COUNT.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("text", DataType.STRING),
        ],
        outputs=[
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Join ports
TEXT_PORT_SCHEMA.register(
    TextAction.JOIN.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("items", DataType.LIST),
        ],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)


# Action groups for display_when
SEARCH_ACTIONS = [
    TextAction.SUBSTRING.value,
    TextAction.CONTAINS.value,
    TextAction.STARTS_WITH.value,
    TextAction.ENDS_WITH.value,
    TextAction.EXTRACT.value,
]

CASE_SENSITIVE_ACTIONS = [
    TextAction.CONTAINS.value,
    TextAction.STARTS_WITH.value,
    TextAction.ENDS_WITH.value,
]

REGEX_ACTIONS = [
    TextAction.REPLACE.value,
    TextAction.EXTRACT.value,
]


@node(category="text")
@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=TextAction.CONTAINS.value,
        label="Action",
        tooltip="Text operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in TextAction],
    ),
    # === CASE SENSITIVITY (for search actions) ===
    PropertyDef(
        "case_sensitive",
        PropertyType.BOOLEAN,
        default=True,
        label="Case Sensitive",
        tooltip="Case-sensitive search/check",
        order=10,
        display_when={"action": CASE_SENSITIVE_ACTIONS},
    ),
    # === SPLIT OPTIONS ===
    PropertyDef(
        "max_split",
        PropertyType.INTEGER,
        default=-1,
        label="Max Split",
        tooltip="Maximum number of splits (-1 for unlimited)",
        order=20,
        display_when={"action": [TextAction.SPLIT.value]},
    ),
    # === REPLACE OPTIONS ===
    PropertyDef(
        "replace_count",
        PropertyType.INTEGER,
        default=-1,
        label="Max Replacements",
        tooltip="Maximum number of replacements (-1 for all)",
        order=20,
        display_when={"action": [TextAction.REPLACE.value]},
    ),
    PropertyDef(
        "use_regex",
        PropertyType.BOOLEAN,
        default=False,
        label="Use Regex",
        tooltip="Use regex for matching",
        order=21,
        display_when={"action": [TextAction.REPLACE.value]},
    ),
    # === REGEX OPTIONS (for replace and extract) ===
    PropertyDef(
        "ignore_case",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Case",
        tooltip="Case-insensitive matching",
        order=30,
        display_when={"action": REGEX_ACTIONS},
    ),
    PropertyDef(
        "multiline",
        PropertyType.BOOLEAN,
        default=False,
        label="Multiline",
        tooltip="^ and $ match line boundaries",
        order=31,
        display_when={"action": REGEX_ACTIONS},
    ),
    PropertyDef(
        "dotall",
        PropertyType.BOOLEAN,
        default=False,
        label="Dot All",
        tooltip=". matches newlines",
        order=32,
        display_when={"action": REGEX_ACTIONS},
    ),
    # === EXTRACT OPTIONS ===
    PropertyDef(
        "all_matches",
        PropertyType.BOOLEAN,
        default=False,
        label="All Matches",
        tooltip="Return all matches instead of just first",
        order=33,
        display_when={"action": [TextAction.EXTRACT.value]},
    ),
    # === TRIM OPTIONS ===
    PropertyDef(
        "trim_mode",
        PropertyType.CHOICE,
        default="both",
        choices=["both", "left", "right"],
        label="Trim Mode",
        tooltip="Trim from both sides, left only, or right only",
        order=20,
        display_when={"action": [TextAction.TRIM.value]},
    ),
    PropertyDef(
        "trim_characters",
        PropertyType.STRING,
        default="",
        label="Characters to Trim",
        tooltip="Characters to trim (default: whitespace)",
        order=21,
        display_when={"action": [TextAction.TRIM.value]},
    ),
    # === CASE OPTIONS ===
    PropertyDef(
        "case_transform",
        PropertyType.CHOICE,
        default="lower",
        choices=["upper", "lower", "title", "capitalize", "swapcase"],
        label="Case Transform",
        tooltip="Case transformation to apply",
        order=20,
        display_when={"action": [TextAction.CASE.value]},
    ),
    # === PAD OPTIONS ===
    PropertyDef(
        "pad_mode",
        PropertyType.CHOICE,
        default="left",
        choices=["left", "right", "center"],
        label="Pad Mode",
        tooltip="Pad left, right, or center",
        order=20,
        display_when={"action": [TextAction.PAD.value]},
    ),
    PropertyDef(
        "fill_char",
        PropertyType.STRING,
        default=" ",
        label="Fill Character",
        tooltip="Character to use for padding",
        order=21,
        display_when={"action": [TextAction.PAD.value]},
    ),
    # === LINES OPTIONS ===
    PropertyDef(
        "lines_mode",
        PropertyType.CHOICE,
        default="split",
        choices=["split", "join"],
        label="Mode",
        tooltip="Split text into lines or join lines into text",
        order=20,
        display_when={"action": [TextAction.LINES.value]},
    ),
    PropertyDef(
        "line_separator",
        PropertyType.CHOICE,
        default="newline",
        choices=["newline", "crlf", "comma"],
        label="Line Separator",
        tooltip="Separator for join mode",
        order=21,
        display_when={"action": [TextAction.LINES.value]},
    ),
    PropertyDef(
        "remove_empty",
        PropertyType.BOOLEAN,
        default=False,
        label="Remove Empty Lines",
        tooltip="Remove empty lines when splitting",
        order=22,
        display_when={"action": [TextAction.LINES.value]},
    ),
    # === COUNT OPTIONS ===
    PropertyDef(
        "count_mode",
        PropertyType.CHOICE,
        default="characters",
        choices=["characters", "words", "lines"],
        label="Count Mode",
        tooltip="What to count",
        order=20,
        display_when={"action": [TextAction.COUNT.value]},
    ),
    PropertyDef(
        "exclude_whitespace",
        PropertyType.BOOLEAN,
        default=False,
        label="Exclude Whitespace",
        tooltip="Exclude whitespace from character count",
        order=21,
        display_when={"action": [TextAction.COUNT.value]},
    ),
    # === JOIN OPTIONS ===
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default="",
        label="Separator",
        tooltip="Separator to use between items",
        order=20,
        display_when={"action": [TextAction.JOIN.value]},
    ),
)
class TextSuperNode(BaseNode):
    """
    Unified text operations node.

    Consolidates 14 atomic text operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        Search:
        - Substring: Extract substring by index
        - Contains: Check if text contains substring
        - Starts With: Check if text starts with prefix
        - Ends With: Check if text ends with suffix
        - Extract (Regex): Extract text using regex pattern

        Transform:
        - Split: Split text into list
        - Replace: Replace occurrences in text
        - Trim: Trim whitespace or specified characters
        - Case: Change case (upper/lower/title/etc.)
        - Pad: Pad text to target length
        - Reverse: Reverse text
        - Lines: Split text into lines or join lines

        Analyze:
        - Count: Count characters, words, or lines
        - Join: Join list of items with separator
    """

    def __init__(self, node_id: str, name: str = "Text", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Default to Contains ports
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("search", DataType.STRING)
        self.add_output_port("contains", DataType.BOOLEAN)
        self.add_output_port("position", DataType.INTEGER)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected text action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", TextAction.CONTAINS.value)

        # Map actions to handlers
        handlers: Dict[
            str, Callable[["IExecutionContext"], Awaitable[ExecutionResult]]
        ] = {
            TextAction.SUBSTRING.value: self._execute_substring,
            TextAction.CONTAINS.value: self._execute_contains,
            TextAction.STARTS_WITH.value: self._execute_starts_with,
            TextAction.ENDS_WITH.value: self._execute_ends_with,
            TextAction.EXTRACT.value: self._execute_extract,
            TextAction.SPLIT.value: self._execute_split,
            TextAction.REPLACE.value: self._execute_replace,
            TextAction.TRIM.value: self._execute_trim,
            TextAction.CASE.value: self._execute_case,
            TextAction.PAD.value: self._execute_pad,
            TextAction.REVERSE.value: self._execute_reverse,
            TextAction.LINES.value: self._execute_lines,
            TextAction.COUNT.value: self._execute_count,
            TextAction.JOIN.value: self._execute_join,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Error in TextSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    # === SEARCH ACTION HANDLERS ===

    async def _execute_substring(self, context: "IExecutionContext") -> ExecutionResult:
        """Extract substring."""
        text = str(self.get_input_value("text", context) or "")
        start = self.get_input_value("start", context)
        end = self.get_input_value("end", context)

        start = safe_int(start, 0) if start is not None else 0
        end = safe_int(end, 0) if end is not None else None

        result = text[start:end]

        self.set_output_value("result", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_contains(self, context: "IExecutionContext") -> ExecutionResult:
        """Check if text contains substring."""
        text = str(self.get_input_value("text", context) or "")
        search = str(self.get_input_value("search", context) or "")
        search = context.resolve_value(search)
        case_sensitive = self.get_parameter("case_sensitive", True)

        if not case_sensitive:
            text_search = text.lower()
            search_lower = search.lower()
        else:
            text_search = text
            search_lower = search

        position = text_search.find(search_lower)
        contains = position >= 0
        count = text_search.count(search_lower)

        self.set_output_value("contains", contains)
        self.set_output_value("position", position)
        self.set_output_value("count", count)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"contains": contains, "count": count},
            "next_nodes": ["exec_out"],
        }

    async def _execute_starts_with(
        self, context: "IExecutionContext"
    ) -> ExecutionResult:
        """Check if text starts with prefix."""
        text = str(self.get_input_value("text", context) or "")
        prefix = str(self.get_input_value("prefix", context) or "")
        prefix = context.resolve_value(prefix)
        case_sensitive = self.get_parameter("case_sensitive", True)

        if not case_sensitive:
            result = text.lower().startswith(prefix.lower())
        else:
            result = text.startswith(prefix)

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result},
            "next_nodes": ["exec_out"],
        }

    async def _execute_ends_with(self, context: "IExecutionContext") -> ExecutionResult:
        """Check if text ends with suffix."""
        text = str(self.get_input_value("text", context) or "")
        suffix = str(self.get_input_value("suffix", context) or "")
        suffix = context.resolve_value(suffix)
        case_sensitive = self.get_parameter("case_sensitive", True)

        if not case_sensitive:
            result = text.lower().endswith(suffix.lower())
        else:
            result = text.endswith(suffix)

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result},
            "next_nodes": ["exec_out"],
        }

    async def _execute_extract(self, context: "IExecutionContext") -> ExecutionResult:
        """Extract text using regex."""
        text = str(self.get_input_value("text", context) or "")
        pattern = str(self.get_input_value("pattern", context) or "")
        pattern = context.resolve_value(pattern)

        if not pattern:
            raise ValueError("Regex pattern is required")

        all_matches = self.get_parameter("all_matches", False)

        # Build regex flags
        flags = 0
        if self.get_parameter("ignore_case", False):
            flags |= re.IGNORECASE
        if self.get_parameter("multiline", False):
            flags |= re.MULTILINE
        if self.get_parameter("dotall", False):
            flags |= re.DOTALL

        if all_matches:
            matches = list(re.finditer(pattern, text, flags))
            found = len(matches) > 0
            full_matches = [m.group(0) for m in matches]
            groups_list = [list(m.groups()) for m in matches]

            self.set_output_value("match", full_matches)
            self.set_output_value("groups", groups_list)
            self.set_output_value("found", found)
        else:
            match = re.search(pattern, text, flags)
            found = match is not None

            if found:
                full_match = match.group(0)
                groups = list(match.groups())
            else:
                full_match = ""
                groups = []

            self.set_output_value("match", full_match)
            self.set_output_value("groups", groups)
            self.set_output_value("found", found)

        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"found": found},
            "next_nodes": ["exec_out"],
        }

    # === TRANSFORM ACTION HANDLERS ===

    async def _execute_split(self, context: "IExecutionContext") -> ExecutionResult:
        """Split text into list."""
        text = str(self.get_input_value("text", context) or "")
        separator = self.get_input_value("separator", context)
        max_split = safe_int(self.get_parameter("max_split", -1), -1)

        if separator is not None:
            separator = context.resolve_value(separator)

        if separator is None or separator == "":
            result = text.split(maxsplit=max_split) if max_split >= 0 else text.split()
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

    async def _execute_replace(self, context: "IExecutionContext") -> ExecutionResult:
        """Replace occurrences in text."""
        text = str(self.get_input_value("text", context) or "")
        old_value = str(self.get_input_value("old_value", context) or "")
        new_value = str(self.get_input_value("new_value", context) or "")

        old_value = context.resolve_value(old_value)
        new_value = context.resolve_value(new_value)

        count = safe_int(self.get_parameter("replace_count", -1), -1)
        use_regex = self.get_parameter("use_regex", False)

        if use_regex:
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
                result, replacements = re.subn(old_value, new_value, text, flags=flags)
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

    async def _execute_trim(self, context: "IExecutionContext") -> ExecutionResult:
        """Trim whitespace from text."""
        text = str(self.get_input_value("text", context) or "")
        mode = self.get_parameter("trim_mode", "both")
        chars = self.get_parameter("trim_characters", "")

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

    async def _execute_case(self, context: "IExecutionContext") -> ExecutionResult:
        """Change case of text."""
        text = str(self.get_input_value("text", context) or "")
        case = self.get_parameter("case_transform", "lower")

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

    async def _execute_pad(self, context: "IExecutionContext") -> ExecutionResult:
        """Pad text to length."""
        text = str(self.get_input_value("text", context) or "")
        length = safe_int(self.get_input_value("length", context), 0)
        mode = self.get_parameter("pad_mode", "left")
        fill_char = self.get_parameter("fill_char", " ")

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

    async def _execute_reverse(self, context: "IExecutionContext") -> ExecutionResult:
        """Reverse text."""
        text = str(self.get_input_value("text", context) or "")
        result = text[::-1]

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result},
            "next_nodes": ["exec_out"],
        }

    async def _execute_lines(self, context: "IExecutionContext") -> ExecutionResult:
        """Split/join lines."""
        mode = self.get_parameter("lines_mode", "split")
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
            lines = text.splitlines()

            if remove_empty:
                lines = [line for line in lines if line]

            self.set_output_value("lines", lines)
            self.set_output_value("count", len(lines))
            result_data = {"count": len(lines), "mode": "split"}
        else:  # join
            lines_input = self.get_input_value("lines", context)
            if not isinstance(lines_input, list):
                lines_input = []

            text_result = separator.join(str(x) for x in lines_input)

            self.set_output_value("text", text_result)
            self.set_output_value("count", len(lines_input))
            result_data = {"count": len(lines_input), "mode": "join"}

        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": result_data,
            "next_nodes": ["exec_out"],
        }

    # === ANALYZE ACTION HANDLERS ===

    async def _execute_count(self, context: "IExecutionContext") -> ExecutionResult:
        """Count characters/words/lines."""
        text = str(self.get_input_value("text", context) or "")
        mode = self.get_parameter("count_mode", "characters")
        exclude_whitespace = self.get_parameter("exclude_whitespace", False)

        if mode == "words":
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

    async def _execute_join(self, context: "IExecutionContext") -> ExecutionResult:
        """Join list with separator."""
        items = self.get_input_value("items", context)
        if not isinstance(items, list):
            if items is None:
                items = []
            else:
                items = [items]

        separator = self.get_parameter("separator", "")
        separator = context.resolve_value(separator)

        result = separator.join(str(item) for item in items)

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result, "count": len(items)},
            "next_nodes": ["exec_out"],
        }

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


__all__ = [
    "TextSuperNode",
    "TextAction",
    "TEXT_PORT_SCHEMA",
]
