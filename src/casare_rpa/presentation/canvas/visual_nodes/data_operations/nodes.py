"""Visual nodes for data operations category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# Import logic nodes
from casare_rpa.nodes.data_operation_nodes import (
    ConcatenateNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
    MathOperationNode,
    ComparisonNode,
    CreateListNode,
    ListGetItemNode,
    JsonParseNode,
    GetPropertyNode,
    # List operations
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
    # Dict operations
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
    # Dataset comparison
    DataCompareNode,
)


# =============================================================================
# Data Operation Nodes
# =============================================================================


class VisualConcatenateNode(VisualNode):
    """Visual representation of ConcatenateNode.

    Widgets are auto-generated from ConcatenateNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Concatenate Strings"
    NODE_CATEGORY = "data_operations/string"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("string_1", DataType.STRING)
        self.add_typed_input("string_2", DataType.STRING)
        self.add_typed_output("result", DataType.STRING)

    def get_node_class(self) -> type:
        return ConcatenateNode


class VisualFormatStringNode(VisualNode):
    """Visual representation of FormatStringNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Format String"
    NODE_CATEGORY = "data_operations/string"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("template", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_typed_output("result", DataType.STRING)

    def get_node_class(self) -> type:
        return FormatStringNode


class VisualRegexMatchNode(VisualNode):
    """Visual representation of RegexMatchNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Regex Match"
    NODE_CATEGORY = "data_operations/string"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("pattern", DataType.STRING)
        self.add_typed_output("match_found", DataType.BOOLEAN)
        self.add_typed_output("first_match", DataType.STRING)
        self.add_typed_output("all_matches", DataType.LIST)
        self.add_typed_output("groups", DataType.LIST)

    def get_node_class(self) -> type:
        return RegexMatchNode


class VisualRegexReplaceNode(VisualNode):
    """Visual representation of RegexReplaceNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Regex Replace"
    NODE_CATEGORY = "data_operations/string"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("pattern", DataType.STRING)
        self.add_typed_input("replacement", DataType.STRING)
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("count", DataType.INTEGER)

    def get_node_class(self):
        return RegexReplaceNode


class VisualMathOperationNode(VisualNode):
    """Visual representation of MathOperationNode.

    Widgets are auto-generated from MathOperationNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Math Operation"
    NODE_CATEGORY = "data_operations/math"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("a", DataType.FLOAT)
        self.add_typed_input("b", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.FLOAT)

    def get_node_class(self):
        return MathOperationNode


class VisualComparisonNode(VisualNode):
    """Visual representation of ComparisonNode.

    Widgets are auto-generated from ComparisonNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Compare Values"
    NODE_CATEGORY = "data_operations/math"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("a", DataType.ANY)
        self.add_typed_input("b", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.BOOLEAN)

    def get_node_class(self):
        return ComparisonNode


class VisualCreateListNode(VisualNode):
    """Visual representation of CreateListNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Create List"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("item_1", DataType.ANY)
        self.add_typed_input("item_2", DataType.ANY)
        self.add_typed_input("item_3", DataType.ANY)
        self.add_typed_output("list", DataType.LIST)

    def get_node_class(self) -> type:
        return CreateListNode


class VisualListGetItemNode(VisualNode):
    """Visual representation of ListGetItemNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Get List Item"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_typed_output("item", DataType.ANY)

    def get_node_class(self) -> type:
        return ListGetItemNode


class VisualJsonParseNode(VisualNode):
    """Visual representation of JsonParseNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Parse JSON"
    NODE_CATEGORY = "data_operations/json"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("json_string", DataType.STRING)
        self.add_typed_output("data", DataType.ANY)

    def get_node_class(self) -> type:
        return JsonParseNode


class VisualGetPropertyNode(VisualNode):
    """Visual representation of GetPropertyNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Get Property"
    NODE_CATEGORY = "data_operations/json"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_typed_input("object", DataType.ANY)
        self.add_typed_input("property_path", DataType.STRING)
        self.add_typed_output("value", DataType.ANY)

    def get_node_class(self) -> type:
        return GetPropertyNode


# =============================================================================
# List Operation Nodes
# =============================================================================


class VisualListLengthNode(VisualNode):
    """Visual representation of ListLengthNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Length"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("length", DataType.INTEGER)

    def get_node_class(self):
        return ListLengthNode


class VisualListAppendNode(VisualNode):
    """Visual representation of ListAppendNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Append"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("item", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListAppendNode


class VisualListContainsNode(VisualNode):
    """Visual representation of ListContainsNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Contains"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("item", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("contains", DataType.BOOLEAN)
        self.add_typed_output("index", DataType.INTEGER)

    def get_node_class(self):
        return ListContainsNode


class VisualListSliceNode(VisualNode):
    """Visual representation of ListSliceNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Slice"
    NODE_CATEGORY = "data_operations/list"

    def __init__(self):
        super().__init__()
        self.add_text_input("start", "Start Index", text="0", tab="config")
        self.add_text_input("end", "End Index", text="", tab="config")
        self.add_text_input("step", "Step", text="1", tab="config")

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("start", DataType.INTEGER)
        self.add_typed_input("end", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListSliceNode


class VisualListJoinNode(VisualNode):
    """Visual representation of ListJoinNode.

    Widgets are auto-generated from ListJoinNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Join"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("separator", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)

    def get_node_class(self):
        return ListJoinNode


class VisualListSortNode(VisualNode):
    """Visual representation of ListSortNode.

    Widgets are auto-generated from ListSortNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Sort"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListSortNode


class VisualListReverseNode(VisualNode):
    """Visual representation of ListReverseNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Reverse"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListReverseNode


class VisualListUniqueNode(VisualNode):
    """Visual representation of ListUniqueNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Unique"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)
        self.add_typed_output("removed_count", DataType.INTEGER)

    def get_node_class(self):
        return ListUniqueNode


class VisualListFilterNode(VisualNode):
    """Visual representation of ListFilterNode.

    Widgets are auto-generated from ListFilterNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Filter"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        # Note: "condition" port removed - use combo menu property instead
        self.add_typed_input("value", DataType.ANY)
        self.add_typed_input("key_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)
        self.add_typed_output("removed", DataType.LIST)

    def get_node_class(self):
        return ListFilterNode


class VisualListMapNode(VisualNode):
    """Visual representation of ListMapNode.

    Widgets are auto-generated from ListMapNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Map"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("transform", DataType.STRING)
        self.add_typed_input("key_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListMapNode


class VisualListReduceNode(VisualNode):
    """Visual representation of ListReduceNode.

    Widgets are auto-generated from ListReduceNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Reduce"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        # Note: "operation" port removed - use combo menu property instead
        self.add_typed_input("key_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)

    def get_node_class(self):
        return ListReduceNode


class VisualListFlattenNode(VisualNode):
    """Visual representation of ListFlattenNode.

    Widgets are auto-generated from ListFlattenNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "List Flatten"
    NODE_CATEGORY = "data_operations/list"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("list", DataType.LIST)
        self.add_typed_input("depth", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)

    def get_node_class(self):
        return ListFlattenNode


# =============================================================================
# Dict Operation Nodes
# =============================================================================


class VisualDictGetNode(VisualNode):
    """Visual representation of DictGetNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Get"
    NODE_CATEGORY = "data_operations/dict"

    def __init__(self):
        super().__init__()
        self.add_text_input("key", "Key", text="", tab="inputs")
        self.add_text_input("default", "Default Value", text="", tab="config")

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_typed_input("key", DataType.STRING)
        self.add_typed_input("default", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)
        self.add_typed_output("found", DataType.BOOLEAN)

    def get_node_class(self):
        return DictGetNode


class VisualDictSetNode(VisualNode):
    """Visual representation of DictSetNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Set"
    NODE_CATEGORY = "data_operations/dict"

    def __init__(self):
        super().__init__()
        self.add_text_input("key", "Key", text="", tab="inputs")

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_typed_input("key", DataType.STRING)
        self.add_typed_input("value", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.DICT)

    def get_node_class(self):
        return DictSetNode


class VisualDictRemoveNode(VisualNode):
    """Visual representation of DictRemoveNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Remove"
    NODE_CATEGORY = "data_operations/dict"

    def __init__(self):
        super().__init__()
        self.add_text_input("key", "Key", text="", tab="inputs")

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_typed_input("key", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.DICT)
        self.add_typed_output("removed_value", DataType.ANY)

    def get_node_class(self):
        return DictRemoveNode


class VisualDictMergeNode(VisualNode):
    """Visual representation of DictMergeNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Merge"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict1", DataType.DICT)
        self.add_typed_input("dict2", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.DICT)

    def get_node_class(self):
        return DictMergeNode


class VisualDictKeysNode(VisualNode):
    """Visual representation of DictKeysNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Keys"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("keys", DataType.LIST)

    def get_node_class(self):
        return DictKeysNode


class VisualDictValuesNode(VisualNode):
    """Visual representation of DictValuesNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Values"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("values", DataType.LIST)

    def get_node_class(self):
        return DictValuesNode


class VisualDictHasKeyNode(VisualNode):
    """Visual representation of DictHasKeyNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Has Key"
    NODE_CATEGORY = "data_operations/dict"

    def __init__(self):
        super().__init__()
        self.add_text_input("key", "Key", text="", tab="inputs")

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_typed_input("key", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("exists", DataType.BOOLEAN)

    def get_node_class(self):
        return DictHasKeyNode


class VisualCreateDictNode(VisualNode):
    """Visual representation of CreateDictNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Create Dict"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("key1", DataType.STRING)
        self.add_typed_input("value1", DataType.ANY)
        self.add_typed_input("key2", DataType.STRING)
        self.add_typed_input("value2", DataType.ANY)
        self.add_typed_input("key3", DataType.STRING)
        self.add_typed_input("value3", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("dict", DataType.DICT)

    def get_node_class(self):
        return CreateDictNode


class VisualDictToJsonNode(VisualNode):
    """Visual representation of DictToJsonNode.

    Widgets are auto-generated from DictToJsonNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict to JSON"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_typed_input("indent", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("json", DataType.STRING)

    def get_node_class(self):
        return DictToJsonNode


class VisualDictItemsNode(VisualNode):
    """Visual representation of DictItemsNode."""

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Dict Items"
    NODE_CATEGORY = "data_operations/dict"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("dict", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("items", DataType.LIST)

    def get_node_class(self):
        return DictItemsNode


# =============================================================================
# Dataset Comparison Nodes
# =============================================================================


class VisualDataCompareNode(VisualNode):
    """Visual representation of DataCompareNode.

    Compares two datasets (lists of dicts) and reports differences.
    Widgets are auto-generated from DataCompareNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.data_operations"
    NODE_NAME = "Data Compare"
    NODE_CATEGORY = "data_operations/comparison"

    def setup_ports(self):
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("data_a", DataType.LIST)
        self.add_typed_input("data_b", DataType.LIST)
        self.add_typed_input("key_columns", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("only_in_a", DataType.LIST)
        self.add_typed_output("only_in_b", DataType.LIST)
        self.add_typed_output("matched", DataType.LIST)
        self.add_typed_output("diff_summary", DataType.DICT)
        self.add_typed_output("has_differences", DataType.BOOLEAN)

    def get_node_class(self):
        return DataCompareNode
