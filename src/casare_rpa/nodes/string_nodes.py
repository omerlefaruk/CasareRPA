"""
CasareRPA - String Operation Nodes

Provides nodes for string manipulation including:
- Concatenation
- String formatting
- Regular expression matching and replacement
"""

from typing import Any, Dict, Optional
import re
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


class ConcatenateNode(BaseNode):
    """Node that concatenates multiple strings."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.separator = self.config.get("separator", "")

    def _define_ports(self) -> None:
        self.add_input_port("string_1", DataType.STRING)
        self.add_input_port("string_2", DataType.STRING)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            s1 = str(self.get_input_value("string_1", ""))
            s2 = str(self.get_input_value("string_2", ""))

            result = f"{s1}{self.separator}{s2}"

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""

    def _define_ports(self) -> None:
        self.add_input_port("template", DataType.STRING)
        self.add_input_port("variables", DataType.DICT)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            template = self.get_input_value("template", "")
            variables = self.get_input_value("variables", {})

            if not isinstance(variables, dict):
                raise ValueError("Variables input must be a dictionary")

            result = template.format(**variables)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "ignore_case": False,
            "multiline": False,
            "dotall": False,
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_output_port("match_found", DataType.BOOLEAN)
        self.add_output_port("first_match", DataType.STRING)
        self.add_output_port("all_matches", DataType.LIST)
        self.add_output_port("groups", DataType.LIST)
        self.add_output_port("match_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")

            flags = 0
            if self.config.get("ignore_case", False):
                flags |= re.IGNORECASE
            if self.config.get("multiline", False):
                flags |= re.MULTILINE
            if self.config.get("dotall", False):
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


class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "ignore_case": False,
            "multiline": False,
            "dotall": False,
            "max_count": 0,
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_input_port("replacement", DataType.STRING)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")
            replacement = self.get_input_value("replacement", "")

            flags = 0
            if self.config.get("ignore_case", False):
                flags |= re.IGNORECASE
            if self.config.get("multiline", False):
                flags |= re.MULTILINE
            if self.config.get("dotall", False):
                flags |= re.DOTALL

            max_count = int(self.config.get("max_count", 0))
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
