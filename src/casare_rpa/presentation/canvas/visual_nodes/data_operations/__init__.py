"""
Visual Nodes - Data Operations
"""

from .nodes import (
    # Data operations
    VisualConcatenateNode,
    VisualFormatStringNode,
    VisualRegexMatchNode,
    VisualRegexReplaceNode,
    VisualMathOperationNode,
    VisualComparisonNode,
    VisualCreateListNode,
    VisualListGetItemNode,
    VisualJsonParseNode,
    VisualGetPropertyNode,
    # List operations
    VisualListLengthNode,
    VisualListAppendNode,
    VisualListContainsNode,
    VisualListSliceNode,
    VisualListJoinNode,
    VisualListSortNode,
    VisualListReverseNode,
    VisualListUniqueNode,
    VisualListFilterNode,
    VisualListMapNode,
    VisualListReduceNode,
    VisualListFlattenNode,
    # Dict operations
    VisualDictGetNode,
    VisualDictSetNode,
    VisualDictRemoveNode,
    VisualDictMergeNode,
    VisualDictKeysNode,
    VisualDictValuesNode,
    VisualDictHasKeyNode,
    VisualCreateDictNode,
    VisualDictToJsonNode,
    VisualDictItemsNode,
)

__all__ = [
    # Data operations
    "VisualConcatenateNode",
    "VisualFormatStringNode",
    "VisualRegexMatchNode",
    "VisualRegexReplaceNode",
    "VisualMathOperationNode",
    "VisualComparisonNode",
    "VisualCreateListNode",
    "VisualListGetItemNode",
    "VisualJsonParseNode",
    "VisualGetPropertyNode",
    # List operations
    "VisualListLengthNode",
    "VisualListAppendNode",
    "VisualListContainsNode",
    "VisualListSliceNode",
    "VisualListJoinNode",
    "VisualListSortNode",
    "VisualListReverseNode",
    "VisualListUniqueNode",
    "VisualListFilterNode",
    "VisualListMapNode",
    "VisualListReduceNode",
    "VisualListFlattenNode",
    # Dict operations
    "VisualDictGetNode",
    "VisualDictSetNode",
    "VisualDictRemoveNode",
    "VisualDictMergeNode",
    "VisualDictKeysNode",
    "VisualDictValuesNode",
    "VisualDictHasKeyNode",
    "VisualCreateDictNode",
    "VisualDictToJsonNode",
    "VisualDictItemsNode",
]
