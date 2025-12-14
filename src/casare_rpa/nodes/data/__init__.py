"""
CasareRPA - Data Operations Nodes Package

Provides data manipulation nodes organized by type:

- string_ops.py: String manipulation (concatenate, format, regex)
- list_ops.py: List operations (create, get, filter, map, reduce)
- dict_ops.py: Dictionary operations (get, set, merge, JSON)
- math_ops.py: Mathematical operations (arithmetic, comparison)
- json_ops.py: JSON parsing and serialization

Note: The actual implementations are in separate files at the nodes/ level.
This package serves as a facade for organized imports.

Node Registry Entries:
    All nodes in this package are registered in the _NODE_REGISTRY at:
    src/casare_rpa/nodes/__init__.py

Usage:
    from casare_rpa.nodes.data import ConcatenateNode, CreateListNode
    # or
    from casare_rpa.nodes import ConcatenateNode  # via lazy loading
"""

# String Operations (from string_nodes.py)
from casare_rpa.nodes.string_nodes import (
    ConcatenateNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
)

# Math Operations (from math_nodes.py)
from casare_rpa.nodes.math_nodes import (
    MathOperationNode,
    ComparisonNode,
)

# List Operations (from list_nodes.py)
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

# Dictionary Operations (from dict_nodes.py)
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

# Collection Utilities (shared helpers for list/dict nodes)
from casare_rpa.nodes.data.collection_utils import (
    strip_var_wrapper,
    resolve_param,
    resolve_list,
    resolve_dict,
    validate_list,
    validate_dict,
    get_nested_value,
    node_execute_wrapper,
    success_result,
    error_result,
)

__all__ = [
    # String Operations
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
    # Math Operations
    "MathOperationNode",
    "ComparisonNode",
    # List Operations
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
    # Dictionary Operations
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

# Node Registry entries for lazy loading
# These map node class names to their module paths
_NODE_REGISTRY = {
    # String Operations
    "ConcatenateNode": "string_nodes",
    "FormatStringNode": "string_nodes",
    "RegexMatchNode": "string_nodes",
    "RegexReplaceNode": "string_nodes",
    # Math Operations
    "MathOperationNode": "math_nodes",
    "ComparisonNode": "math_nodes",
    # List Operations
    "CreateListNode": "list_nodes",
    "ListGetItemNode": "list_nodes",
    "ListLengthNode": "list_nodes",
    "ListAppendNode": "list_nodes",
    "ListContainsNode": "list_nodes",
    "ListSliceNode": "list_nodes",
    "ListJoinNode": "list_nodes",
    "ListSortNode": "list_nodes",
    "ListReverseNode": "list_nodes",
    "ListUniqueNode": "list_nodes",
    "ListFilterNode": "list_nodes",
    "ListMapNode": "list_nodes",
    "ListReduceNode": "list_nodes",
    "ListFlattenNode": "list_nodes",
    # Dictionary Operations
    "JsonParseNode": "dict_nodes",
    "GetPropertyNode": "dict_nodes",
    "DictGetNode": "dict_nodes",
    "DictSetNode": "dict_nodes",
    "DictRemoveNode": "dict_nodes",
    "DictMergeNode": "dict_nodes",
    "DictKeysNode": "dict_nodes",
    "DictValuesNode": "dict_nodes",
    "DictHasKeyNode": "dict_nodes",
    "CreateDictNode": "dict_nodes",
    "DictToJsonNode": "dict_nodes",
    "DictItemsNode": "dict_nodes",
}
