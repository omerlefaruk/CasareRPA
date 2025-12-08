"""
Visual Nodes - Utility
"""

from casare_rpa.presentation.canvas.visual_nodes.utility.nodes import (
    # Random operations
    VisualRandomNumberNode,
    VisualRandomChoiceNode,
    VisualRandomStringNode,
    VisualRandomUUIDNode,
    VisualShuffleListNode,
    # DateTime operations
    VisualGetCurrentDateTimeNode,
    VisualFormatDateTimeNode,
    VisualParseDateTimeNode,
    VisualDateTimeAddNode,
    VisualDateTimeDiffNode,
    VisualDateTimeCompareNode,
    VisualGetTimestampNode,
    # Text operations
    VisualTextSplitNode,
    VisualTextReplaceNode,
    VisualTextTrimNode,
    VisualTextCaseNode,
    VisualTextPadNode,
    VisualTextSubstringNode,
    VisualTextContainsNode,
    VisualTextStartsWithNode,
    VisualTextEndsWithNode,
    VisualTextLinesNode,
    VisualTextReverseNode,
    VisualTextCountNode,
    VisualTextJoinNode,
    VisualTextExtractNode,
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
    # Reroute node
    "VisualRerouteNode",
]
