"""
Text operation nodes package.

This package provides nodes for text manipulation, search, and analysis.
"""

from casare_rpa.nodes.text.manipulation import (
    TextSplitNode,
    TextReplaceNode,
    TextTrimNode,
    TextCaseNode,
    TextPadNode,
    TextReverseNode,
    TextLinesNode,
)
from casare_rpa.nodes.text.search import (
    TextSubstringNode,
    TextContainsNode,
    TextStartsWithNode,
    TextEndsWithNode,
    TextExtractNode,
)
from casare_rpa.nodes.text.analysis import (
    TextCountNode,
)
from casare_rpa.nodes.text.transform import (
    TextJoinNode,
)

__all__ = [
    # Manipulation
    "TextSplitNode",
    "TextReplaceNode",
    "TextTrimNode",
    "TextCaseNode",
    "TextPadNode",
    "TextReverseNode",
    "TextLinesNode",
    # Search
    "TextSubstringNode",
    "TextContainsNode",
    "TextStartsWithNode",
    "TextEndsWithNode",
    "TextExtractNode",
    # Analysis
    "TextCountNode",
    # Transform
    "TextJoinNode",
]
