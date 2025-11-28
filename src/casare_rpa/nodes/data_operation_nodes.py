"""
CasareRPA - Data Operation Nodes (Compatibility Module)

This module re-exports data operation nodes from their new locations
for backward compatibility.

Node classes have been split into:
- string_nodes.py: String manipulation (Concatenate, Format, Regex)
- math_nodes.py: Math operations (MathOperation, Comparison)
- list_nodes.py: List operations (Create, Get, Filter, Map, etc.)
- dict_nodes.py: Dictionary operations (Get, Set, Merge, JSON, etc.)
"""

# Re-export all nodes for backward compatibility
from casare_rpa.nodes.string_nodes import (
    ConcatenateNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
)

from casare_rpa.nodes.math_nodes import (
    MathOperationNode,
    ComparisonNode,
)

from casare_rpa.nodes.list_nodes import (
    CreateListNode,
    ListGetItemNode,
    ListLengthNode,
    ListAppendNode,
    ListContainsNode,
    ListSliceNode,
    ListJoinNode,
    ListSortNode,
    ListReverseNode,
    ListUniqueNode,
    ListFilterNode,
    ListMapNode,
    ListReduceNode,
    ListFlattenNode,
)

from casare_rpa.nodes.dict_nodes import (
    JsonParseNode,
    GetPropertyNode,
    DictGetNode,
    DictSetNode,
    DictRemoveNode,
    DictMergeNode,
    DictKeysNode,
    DictValuesNode,
    DictHasKeyNode,
    CreateDictNode,
    DictToJsonNode,
    DictItemsNode,
)

__all__ = [
    # String operations
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
    # Math operations
    "MathOperationNode",
    "ComparisonNode",
    # List operations
    "CreateListNode",
    "ListGetItemNode",
    "ListLengthNode",
    "ListAppendNode",
    "ListContainsNode",
    "ListSliceNode",
    "ListJoinNode",
    "ListSortNode",
    "ListReverseNode",
    "ListUniqueNode",
    "ListFilterNode",
    "ListMapNode",
    "ListReduceNode",
    "ListFlattenNode",
    # Dict operations
    "JsonParseNode",
    "GetPropertyNode",
    "DictGetNode",
    "DictSetNode",
    "DictRemoveNode",
    "DictMergeNode",
    "DictKeysNode",
    "DictValuesNode",
    "DictHasKeyNode",
    "CreateDictNode",
    "DictToJsonNode",
    "DictItemsNode",
]
