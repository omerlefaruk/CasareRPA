"""
CasareRPA - String Operation Nodes

Provides nodes for string manipulation including:
- Concatenation
- String formatting
- Regular expression matching and replacement
"""

import re

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext

# ReDoS protection limits
MAX_TEXT_LENGTH = 100000  # 100KB - prevents catastrophic backtracking on large inputs
MAX_PATTERN_LENGTH = 1000  # Reasonable limit for regex patterns


def _validate_regex_inputs(text: str, pattern: str) -> None:
    """Validate regex inputs to prevent ReDoS attacks.

    Args:
        text: The text to search/replace in
        pattern: The regex pattern

    Raises:
        ValueError: If inputs exceed safe limits
    """
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"Text length ({len(text):,} chars) exceeds maximum allowed "
            f"({MAX_TEXT_LENGTH:,} chars) for regex operations"
        )
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise ValueError(
            f"Pattern length ({len(pattern):,} chars) exceeds maximum allowed "
            f"({MAX_PATTERN_LENGTH:,} chars) for regex operations"
        )


@properties(
    PropertyDef(
        "string_1",
        DataType.STRING,
        default="",
        label="String 1",
        tooltip="First string to concatenate",
    ),
    PropertyDef(
        "string_2",
        DataType.STRING,
        default="",
        label="String 2",
        tooltip="Second string to concatenate",
    ),
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default="",
        label="Separator",
        tooltip="Separator to insert between strings",
    ),
)
@node(category="data")
class ConcatenateNode(BaseNode):
    """Node that concatenates multiple strings."""

    # @category: data
    # @requires: none
    # @ports: string_1, string_2 -> result

    def __init__(self, node_id: str, name: str = "Concatenate", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ConcatenateNode"
        self.cacheable = True
        self.cache_ttl = 3600  # 1 hour

    def _define_ports(self) -> None:
        self.add_input_port("string_1", DataType.STRING, required=False)
        self.add_input_port("string_2", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            s1 = self.get_parameter("string_1", "")
            s2 = self.get_parameter("string_2", "")
            separator = self.get_parameter("separator", "")

            result = f"{s1}{separator}{s2}"

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "template",
        DataType.STRING,
        default="",
        label="Template",
        tooltip="String template with {variables}",
    ),
    PropertyDef(
        "variables",
        DataType.DICT,
        default={},
        label="Variables",
        tooltip="Dictionary of variables for formatting",
    ),
)
@node(category="data")
class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""

    # @category: data
    # @requires: none
    # @ports: template, variables -> result

    def __init__(self, node_id: str, name: str = "Format String", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FormatStringNode"
        self.cacheable = True
        self.cache_ttl = 3600

    def _define_ports(self) -> None:
        self.add_input_port("template", DataType.STRING, required=False)
        self.add_input_port("variables", DataType.DICT, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            template = self.get_parameter("template", "")
            variables = self.get_parameter("variables", {})

            result = template.format(**variables)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
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
@node(category="data")
class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""

    # @category: data
    # @requires: none
    # @ports: text, pattern -> match_found, first_match, all_matches, groups, match_count

    def __init__(self, node_id: str, name: str = "Regex Match", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RegexMatchNode"
        self.cacheable = True
        self.cache_ttl = 3600

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("pattern", DataType.STRING, required=False)
        self.add_output_port("match_found", DataType.BOOLEAN)
        self.add_output_port("first_match", DataType.STRING)
        self.add_output_port("all_matches", DataType.LIST)
        self.add_output_port("groups", DataType.LIST)
        self.add_output_port("match_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            # get_parameter auto-resolves {{variables}} per Modern Node Standard
            text = self.get_parameter("text", "")
            pattern = self.get_parameter("pattern", "")

            # ReDoS protection - validate inputs before regex execution
            _validate_regex_inputs(text, pattern)

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


@properties(
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
@node(category="data")
class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""

    # @category: data
    # @requires: none
    # @ports: text, pattern, replacement -> result, count

    def __init__(self, node_id: str, name: str = "Regex Replace", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RegexReplaceNode"
        self.cacheable = True
        self.cache_ttl = 3600

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING, required=False)
        self.add_input_port("pattern", DataType.STRING, required=False)
        self.add_input_port("replacement", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            # get_parameter auto-resolves {{variables}} per Modern Node Standard
            text = self.get_parameter("text", "")
            pattern = self.get_parameter("pattern", "")
            replacement = self.get_parameter("replacement", "")

            # ReDoS protection - validate inputs before regex execution
            _validate_regex_inputs(text, pattern)

            flags = 0
            if self.get_parameter("ignore_case", False):
                flags |= re.IGNORECASE
            if self.get_parameter("multiline", False):
                flags |= re.MULTILINE
            if self.get_parameter("dotall", False):
                flags |= re.DOTALL

            max_count = int(self.get_parameter("max_count", 0))
            if max_count > 0:
                result, count = re.subn(pattern, replacement, text, count=max_count, flags=flags)
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


@properties(
    PropertyDef(
        "search_string",
        DataType.STRING,
        default="",
        label="Search String",
        tooltip="The string to search for",
    ),
    PropertyDef(
        "candidates",
        DataType.LIST,
        default=[],
        label="Candidates",
        tooltip="List of candidate strings to match against",
    ),
    PropertyDef(
        "threshold",
        DataType.FLOAT,
        default=0.6,
        label="Similarity Threshold",
        tooltip="Minimum similarity score (0-1) to consider a match",
    ),
)
@node(category="data")
class FuzzyStringMatchNode(BaseNode):
    """Node that performs fuzzy string matching using similarity algorithms."""

    def __init__(self, node_id: str, name: str = "Fuzzy String Match", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FuzzyStringMatchNode"
        self.cacheable = True
        self.cache_ttl = 3600

    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_input_port("search_string", DataType.STRING, required=False)
        self.add_input_port("candidates", DataType.LIST, required=False)
        self.add_input_port("threshold", DataType.FLOAT, required=False)
        self.add_exec_output("match_found")
        self.add_exec_output("no_match")
        self.add_output_port("matched_string", DataType.STRING)
        self.add_output_port("match_score", DataType.FLOAT)
        self.add_output_port("match_index", DataType.INTEGER)
        self.add_output_port("is_match", DataType.BOOLEAN)
        self.add_output_port("all_scores", DataType.DICT)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings using SequenceMatcher.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio between 0 and 1
        """
        from difflib import SequenceMatcher

        return SequenceMatcher(None, s1, s2).ratio()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            search_string = self.get_parameter("search_string", "")
            candidates = self.get_parameter("candidates", [])
            threshold = self.get_parameter("threshold", 0.6)

            if not search_string or not candidates:
                self.set_output_value("is_match", False)
                self.set_output_value("all_scores", {})
                return {
                    "success": True,
                    "data": {
                        "is_match": False,
                        "all_scores": {},
                    },
                    "next_nodes": ["no_match"],
                }

            # Calculate similarity scores for all candidates
            all_scores = {}
            best_match = None
            best_score = 0.0
            best_index = -1

            for i, candidate in enumerate(candidates):
                if not isinstance(candidate, str):
                    continue
                score = self._calculate_similarity(search_string, candidate)
                all_scores[candidate] = score
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    best_index = i

            is_match = best_score >= threshold
            self.set_output_value("matched_string", best_match if is_match else "")
            self.set_output_value("match_score", best_score)
            self.set_output_value("match_index", best_index)
            self.set_output_value("is_match", is_match)
            self.set_output_value("all_scores", all_scores)

            return {
                "success": True,
                "data": {
                    "matched_string": best_match if is_match else "",
                    "match_score": best_score,
                    "match_index": best_index,
                    "is_match": is_match,
                    "all_scores": all_scores,
                },
                "next_nodes": ["match_found" if is_match else "no_match"],
            }
        except Exception as e:
            logger.error(f"Fuzzy string match failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": ["no_match"]}


@properties(
    PropertyDef(
        "input_list",
        DataType.LIST,
        default=[],
        label="Input List",
        tooltip="List of strings to filter",
    ),
    PropertyDef(
        "filter_string",
        DataType.STRING,
        default="",
        label="Filter String",
        tooltip="String to compare against for similarity filtering",
    ),
    PropertyDef(
        "threshold",
        DataType.FLOAT,
        default=0.6,
        label="Similarity Threshold",
        tooltip="Minimum similarity score (0-1) to include in results",
    ),
)
@node(category="data")
class FilterBySimilarityNode(BaseNode):
    """Node that filters a list of strings by similarity to a target string."""

    def __init__(self, node_id: str, name: str = "Filter by Similarity", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FilterBySimilarityNode"
        self.cacheable = True
        self.cache_ttl = 3600

    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_input_port("input_list", DataType.LIST, required=False)
        self.add_input_port("filter_string", DataType.STRING, required=False)
        self.add_input_port("threshold", DataType.FLOAT, required=False)
        self.add_exec_output("exec_out")
        self.add_output_port("filtered_list", DataType.LIST)
        self.add_output_port("scores", DataType.DICT)
        self.add_output_port("count", DataType.INTEGER)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings using SequenceMatcher."""
        from difflib import SequenceMatcher

        return SequenceMatcher(None, s1, s2).ratio()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            input_list = self.get_parameter("input_list", [])
            filter_string = self.get_parameter("filter_string", "")
            threshold = self.get_parameter("threshold", 0.6)

            if not input_list or not filter_string:
                self.set_output_value("filtered_list", [])
                self.set_output_value("scores", {})
                self.set_output_value("count", 0)
                return {
                    "success": True,
                    "data": {
                        "filtered_list": [],
                        "scores": {},
                        "count": 0,
                    },
                    "next_nodes": ["exec_out"],
                }

            # Filter by similarity
            filtered_list = []
            scores = {}

            for item in input_list:
                if not isinstance(item, str):
                    # Keep non-string items as-is
                    filtered_list.append(item)
                    continue

                score = self._calculate_similarity(filter_string, item)
                scores[item] = score

                if score >= threshold:
                    filtered_list.append(item)

            self.set_output_value("filtered_list", filtered_list)
            self.set_output_value("scores", scores)
            self.set_output_value("count", len(filtered_list))

            return {
                "success": True,
                "data": {
                    "filtered_list": filtered_list,
                    "scores": scores,
                    "count": len(filtered_list),
                },
                "next_nodes": ["exec_out"],
            }
        except Exception as e:
            logger.error(f"Filter by similarity failed: {e}")
            self.error_message = str(e)
            return {
                "success": False,
                "error": str(e),
                "next_nodes": ["exec_out"],
            }


__all__ = [
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
    "FuzzyStringMatchNode",
    "FilterBySimilarityNode",
]
