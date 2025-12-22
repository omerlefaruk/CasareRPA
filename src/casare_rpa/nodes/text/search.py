"""
Text search and extraction nodes.

This module provides nodes for searching and extracting text:
- Substring
- Contains
- Starts With
- Ends With
- Regex Extract
"""

import re
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils import safe_int


@properties()
@node(category="text")
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

    # @category: data
    # @requires: none
    # @ports: text, start, end -> result, length

    def __init__(self, node_id: str, name: str = "Text Substring", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextSubstringNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        # start defaults to 0, end defaults to None (end of string)
        self.add_input_port("start", DataType.INTEGER, required=False)
        self.add_input_port("end", DataType.INTEGER, required=False)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("length", DataType.INTEGER)

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


@properties(
    PropertyDef(
        "case_sensitive",
        PropertyType.BOOLEAN,
        default=True,
        label="Case Sensitive",
        tooltip="Case-sensitive search",
    ),
)
@node(category="text")
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

    # @category: data
    # @requires: none
    # @ports: text, search -> contains, position, count

    def __init__(self, node_id: str, name: str = "Text Contains", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextContainsNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("search", DataType.STRING, required=False)
        self.add_output_port("contains", DataType.BOOLEAN)
        self.add_output_port("position", DataType.INTEGER)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            search = str(self.get_input_value("search", context) or "")

            # Resolve {{variable}} patterns in search

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
                "data": {"contains": contains, "position": position, "count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextContainsNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "case_sensitive",
        PropertyType.BOOLEAN,
        default=True,
        label="Case Sensitive",
        tooltip="Case-sensitive check",
    ),
)
@node(category="text")
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

    # @category: data
    # @requires: none
    # @ports: text, prefix -> result

    def __init__(self, node_id: str, name: str = "Text Starts With", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextStartsWithNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("prefix", DataType.STRING, required=False)
        self.add_output_port("result", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            prefix = str(self.get_input_value("prefix", context) or "")

            # Resolve {{variable}} patterns in prefix

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

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextStartsWithNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "case_sensitive",
        PropertyType.BOOLEAN,
        default=True,
        label="Case Sensitive",
        tooltip="Case-sensitive check",
    ),
)
@node(category="text")
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

    # @category: data
    # @requires: none
    # @ports: text, suffix -> result

    def __init__(self, node_id: str, name: str = "Text Ends With", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextEndsWithNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("suffix", DataType.STRING, required=False)
        self.add_output_port("result", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            suffix = str(self.get_input_value("suffix", context) or "")

            # Resolve {{variable}} patterns in suffix

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

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextEndsWithNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "pattern",
        PropertyType.STRING,
        required=True,
        label="Pattern",
        tooltip="Regex pattern with optional capture groups",
    ),
    PropertyDef(
        "all_matches",
        PropertyType.BOOLEAN,
        default=False,
        label="All Matches",
        tooltip="Return all matches instead of just first",
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
@node(category="text")
class TextExtractNode(BaseNode):
    """
    Extract text using regex with capture groups.

    Config:
        all_matches: Return all matches instead of just first (default: False)
        ignore_case: Case-insensitive matching (default: False)
        multiline: ^ and $ match line boundaries (default: False)
        dotall: . matches newlines (default: False)

    Inputs:
        text: The text to search
        pattern: Regex pattern with optional capture groups

    Outputs:
        match: The full match string (or list if all_matches)
        groups: List of capture groups (or list of lists if all_matches)
        found: Whether a match was found
    """

    # @category: data
    # @requires: none
    # @ports: text, pattern -> match, groups, found

    def __init__(self, node_id: str, name: str = "Text Extract", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextExtractNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("pattern", DataType.STRING, required=True)
        self.add_output_port("match", DataType.ANY)  # String or List[String]
        self.add_output_port("groups", DataType.LIST)  # List[String] or List[List[String]]
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")
            pattern = str(self.get_input_value("pattern", context) or "")

            # Resolve {{variable}} patterns

            all_matches = self.get_parameter("all_matches", False)

            # Build regex flags
            flags = 0
            if self.get_parameter("ignore_case", False):
                flags |= re.IGNORECASE
            if self.get_parameter("multiline", False):
                flags |= re.MULTILINE
            if self.get_parameter("dotall", False):
                flags |= re.DOTALL

            if not pattern:
                raise ValueError("Regex pattern is required")

            if all_matches:
                matches = list(re.finditer(pattern, text, flags))
                found = len(matches) > 0

                full_matches = [m.group(0) for m in matches]
                groups_list = [list(m.groups()) for m in matches]

                self.set_output_value("match", full_matches)
                self.set_output_value("groups", groups_list)
                self.set_output_value("found", found)

                result_data = {"found": found, "count": len(matches)}
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

                result_data = {"found": found, "match": full_match}

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": result_data,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"TextExtractNode failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        if not self.get_input_value("pattern") and not self.get_parameter("pattern"):
            # This check is weak because pattern comes from input usually
            pass
        return True, ""
