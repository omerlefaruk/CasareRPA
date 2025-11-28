"""
Text operation nodes for CasareRPA.

This module provides extended text manipulation nodes:
- TextSplitNode: Split text into list
- TextReplaceNode: Replace text occurrences
- TextTrimNode: Trim whitespace
- TextCaseNode: Change text case
- TextPadNode: Pad text to length
- TextSubstringNode: Extract substring
- TextContainsNode: Check if contains
- TextStartsWithNode, TextEndsWithNode: Check prefix/suffix
- TextLinesNode: Split/join lines
- TextReverseNode: Reverse text
- TextCountNode: Count characters/words
"""

import re

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


def safe_int(value, default: int) -> int:
    """Safely parse int values with defaults."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


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

    def __init__(self, node_id: str, name: str = "Text Split", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextSplitNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("separator", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            separator = self.get_input_value("separator", context)
            max_split = safe_int(self.config.get("max_split"), -1)

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

    def __init__(self, node_id: str, name: str = "Text Replace", **kwargs) -> None:
        default_config = {
            "count": -1,
            "use_regex": False,
            "ignore_case": False,
            "multiline": False,
            "dotall": False,
        }
        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextReplaceNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("old_value", PortType.INPUT, DataType.STRING)
        self.add_input_port("new_value", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("replacements", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            old_value = str(self.get_input_value("old_value", context) or "")
            new_value = str(self.get_input_value("new_value", context) or "")

            # Resolve {{variable}} patterns
            old_value = context.resolve_value(old_value)
            new_value = context.resolve_value(new_value)

            count = safe_int(self.config.get("count"), -1)
            use_regex = self.config.get("use_regex", False)

            if use_regex:
                # Build regex flags
                flags = 0
                if self.config.get("ignore_case", False):
                    flags |= re.IGNORECASE
                if self.config.get("multiline", False):
                    flags |= re.MULTILINE
                if self.config.get("dotall", False):
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

    def __init__(self, node_id: str, name: str = "Text Trim", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextTrimNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            mode = self.config.get("mode", "both")
            chars = self.config.get("characters")

            # Resolve {{variable}} patterns in characters
            if chars is not None:
                chars = context.resolve_value(chars)

            if mode == "left":
                result = text.lstrip(chars)
            elif mode == "right":
                result = text.rstrip(chars)
            else:
                result = text.strip(chars)

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

    def __init__(self, node_id: str, name: str = "Text Case", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextCaseNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            case = self.config.get("case", "lower")

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

    def __init__(self, node_id: str, name: str = "Text Pad", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextPadNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("length", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            length = safe_int(self.get_input_value("length", context), 0)
            mode = self.config.get("mode", "left")
            fill_char = self.config.get("fill_char", " ")

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


class TextSubstringNode(BaseNode):
    """
    Extract a substring from a string.

    Inputs:
        text: The source text
        start: Start index (inclusive)
        end: End index (exclusive, optional)

    Outputs:
        result: Extracted substring
        length: Length of substring
    """

    def __init__(self, node_id: str, name: str = "Text Substring", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextSubstringNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("start", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("length", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
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
                "data": {"result": result, "length": len(result)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextSubstringNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextContainsNode(BaseNode):
    """
    Check if a string contains a substring.

    Config:
        case_sensitive: Case-sensitive search (default: True)

    Inputs:
        text: The text to search in
        search: The substring to find

    Outputs:
        contains: Whether the substring was found
        position: Position of first occurrence (-1 if not found)
        count: Number of occurrences
    """

    def __init__(self, node_id: str, name: str = "Text Contains", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextContainsNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("search", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("contains", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("position", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            search = str(self.get_input_value("search", context) or "")

            # Resolve {{variable}} patterns in search
            search = context.resolve_value(search)

            case_sensitive = self.config.get("case_sensitive", True)

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
                "data": {"contains": contains, "position": position, "count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextContainsNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextStartsWithNode(BaseNode):
    """
    Check if a string starts with a prefix.

    Config:
        case_sensitive: Case-sensitive check (default: True)

    Inputs:
        text: The text to check
        prefix: The prefix to look for

    Outputs:
        result: Whether text starts with prefix
    """

    def __init__(self, node_id: str, name: str = "Text Starts With", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextStartsWithNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("prefix", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            prefix = str(self.get_input_value("prefix", context) or "")

            # Resolve {{variable}} patterns in prefix
            prefix = context.resolve_value(prefix)

            case_sensitive = self.config.get("case_sensitive", True)

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

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextStartsWithNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextEndsWithNode(BaseNode):
    """
    Check if a string ends with a suffix.

    Config:
        case_sensitive: Case-sensitive check (default: True)

    Inputs:
        text: The text to check
        suffix: The suffix to look for

    Outputs:
        result: Whether text ends with suffix
    """

    def __init__(self, node_id: str, name: str = "Text Ends With", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextEndsWithNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("suffix", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            suffix = str(self.get_input_value("suffix", context) or "")

            # Resolve {{variable}} patterns in suffix
            suffix = context.resolve_value(suffix)

            case_sensitive = self.config.get("case_sensitive", True)

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

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextEndsWithNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextLinesNode(BaseNode):
    """
    Split text into lines or join lines into text.

    Config:
        mode: 'split' or 'join' (default: split)
        line_separator: Line separator for join (default: newline)
        keep_ends: Keep line endings when splitting (default: False)

    Inputs:
        input: Text to split or list to join

    Outputs:
        result: Split lines (list) or joined text (string)
        count: Number of lines
    """

    def __init__(self, node_id: str, name: str = "Text Lines", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextLinesNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("input", PortType.INPUT, DataType.ANY)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            input_val = self.get_input_value("input", context)
            mode = self.config.get("mode", "split")
            separator = self.config.get("line_separator", "\n")
            keep_ends = self.config.get("keep_ends", False)

            # Resolve {{variable}} patterns in separator
            separator = context.resolve_value(separator)

            if mode == "split":
                text = str(input_val or "")
                if keep_ends:
                    result = text.splitlines(keepends=True)
                else:
                    result = text.splitlines()
                count = len(result)
            else:  # join
                if isinstance(input_val, (list, tuple)):
                    result = separator.join(str(item) for item in input_val)
                    count = len(input_val)
                else:
                    result = str(input_val or "")
                    count = 1

            self.set_output_value("result", result)
            self.set_output_value("count", count)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextLinesNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextReverseNode(BaseNode):
    """
    Reverse a string.

    Inputs:
        text: The text to reverse

    Outputs:
        result: Reversed text
    """

    def __init__(self, node_id: str, name: str = "Text Reverse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextReverseNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

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
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextCountNode(BaseNode):
    """
    Count characters, words, or lines in text.

    Config:
        mode: 'characters', 'words', 'lines' (default: characters)
        exclude_whitespace: Exclude whitespace from character count (default: False)

    Inputs:
        text: The text to count

    Outputs:
        count: The count
        characters: Character count
        words: Word count
        lines: Line count
    """

    def __init__(self, node_id: str, name: str = "Text Count", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextCountNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("characters", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("words", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("lines", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            mode = self.config.get("mode", "characters")
            exclude_whitespace = self.config.get("exclude_whitespace", False)

            # Calculate all counts
            if exclude_whitespace:
                characters = len(
                    text.replace(" ", "").replace("\n", "").replace("\t", "")
                )
            else:
                characters = len(text)

            words = len(text.split())
            lines = len(text.splitlines()) if text else 0

            # Set primary count based on mode
            if mode == "words":
                count = words
            elif mode == "lines":
                count = lines
            else:
                count = characters

            self.set_output_value("count", count)
            self.set_output_value("characters", characters)
            self.set_output_value("words", words)
            self.set_output_value("lines", lines)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "count": count,
                    "characters": characters,
                    "words": words,
                    "lines": lines,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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

    def __init__(self, node_id: str, name: str = "Text Join", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextJoinNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.LIST)
        self.add_input_port("separator", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_input_value("items", context) or []
            separator = self.get_input_value("separator", context)

            if separator is None:
                separator = self.config.get("separator", "")

            # Resolve {{variable}} patterns in separator
            separator = context.resolve_value(separator)

            if not isinstance(items, (list, tuple)):
                items = [items]

            result = separator.join(str(item) for item in items)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextJoinNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class TextExtractNode(BaseNode):
    """
    Extract text using regex with capture groups.

    Config:
        all_matches: Return all matches instead of just first (default: False)
        ignore_case: Case-insensitive matching (default: False)
        multiline: ^ and $ match line boundaries (default: False)
        dotall: . matches newlines (default: False)

    Inputs:
        text: The source text
        pattern: Regex pattern with capture groups

    Outputs:
        match: First match (or all matches if all_matches=True)
        groups: Captured groups from first match
        found: Whether any match was found
        match_count: Number of matches found
    """

    def __init__(self, node_id: str, name: str = "Text Extract", **kwargs) -> None:
        default_config = {
            "all_matches": False,
            "ignore_case": False,
            "multiline": False,
            "dotall": False,
        }
        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextExtractNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("pattern", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("match", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("groups", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("found", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("match_count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            pattern = str(self.get_input_value("pattern", context) or "")

            # Resolve {{variable}} patterns in pattern
            pattern = context.resolve_value(pattern)

            all_matches = self.config.get("all_matches", False)

            if not pattern:
                raise ValueError("pattern is required")

            # Build regex flags
            flags = 0
            if self.config.get("ignore_case", False):
                flags |= re.IGNORECASE
            if self.config.get("multiline", False):
                flags |= re.MULTILINE
            if self.config.get("dotall", False):
                flags |= re.DOTALL

            if all_matches:
                matches = re.findall(pattern, text, flags=flags)
                found = len(matches) > 0
                match = matches if found else []
                groups = []
                match_count = len(matches)
            else:
                result = re.search(pattern, text, flags=flags)
                found = result is not None
                match = result.group(0) if found else ""
                groups = list(result.groups()) if found and result.groups() else []
                match_count = 1 if found else 0

            self.set_output_value("match", match)
            self.set_output_value("groups", groups)
            self.set_output_value("found", found)
            self.set_output_value("match_count", match_count)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"found": found, "match_count": match_count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
