"""
Visual Nodes - Utility
"""

from casare_rpa.presentation.canvas.visual_nodes.utility.nodes import (
    VisualDateTimeAddNode,
    VisualDateTimeCompareNode,
    VisualDateTimeDiffNode,
    VisualFormatDateTimeNode,
    # DateTime operations
    VisualGetCurrentDateTimeNode,
    VisualGetTimestampNode,
    VisualParseDateTimeNode,
    VisualRandomChoiceNode,
    # Random operations
    VisualRandomNumberNode,
    VisualRandomStringNode,
    VisualRandomUUIDNode,
    VisualShuffleListNode,
    VisualTextCaseNode,
    VisualTextContainsNode,
    VisualTextCountNode,
    VisualTextEndsWithNode,
    VisualTextExtractNode,
    VisualTextJoinNode,
    VisualTextLinesNode,
    VisualTextPadNode,
    VisualTextReplaceNode,
    VisualTextReverseNode,
    # Text operations
    VisualTextSplitNode,
    VisualTextStartsWithNode,
    VisualTextSubstringNode,
    VisualTextTrimNode,
    VisualLogNode,
)
from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
    VisualRerouteNode,
)

__all__ = [
    # Random operations
    "VisualRandomNumberNode",
    "VisualRandomChoiceNode",
    "VisualRandomStringNode",
    "VisualRandomUUIDNode",
    "VisualShuffleListNode",
    # DateTime operations
    "VisualGetCurrentDateTimeNode",
    "VisualFormatDateTimeNode",
    "VisualParseDateTimeNode",
    "VisualDateTimeAddNode",
    "VisualDateTimeDiffNode",
    "VisualDateTimeCompareNode",
    "VisualGetTimestampNode",
    # Text operations
    "VisualTextSplitNode",
    "VisualTextReplaceNode",
    "VisualTextTrimNode",
    "VisualTextCaseNode",
    "VisualTextPadNode",
    "VisualTextSubstringNode",
    "VisualTextContainsNode",
    "VisualTextStartsWithNode",
    "VisualTextEndsWithNode",
    "VisualTextLinesNode",
    "VisualTextReverseNode",
    "VisualTextCountNode",
    "VisualTextJoinNode",
    "VisualTextExtractNode",
    # Logging operations
    "VisualLogNode",
    # Reroute node
    "VisualRerouteNode",
]
