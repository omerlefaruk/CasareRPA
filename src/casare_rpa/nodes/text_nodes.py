"""
DEPRECATED: Text nodes have been moved to src/casare_rpa/nodes/text/ package.
This module is kept for backward compatibility and re-exports the original classes.
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
    "TextSplitNode",
    "TextReplaceNode",
    "TextTrimNode",
    "TextCaseNode",
    "TextPadNode",
    "TextReverseNode",
    "TextLinesNode",
    "TextSubstringNode",
    "TextContainsNode",
    "TextStartsWithNode",
    "TextEndsWithNode",
    "TextExtractNode",
    "TextCountNode",
    "TextJoinNode",
]
