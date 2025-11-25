from typing import Any, Dict, List
from NodeGraphQt import BaseNode

from .base_visual_node import VisualNode
from ..nodes.data_operation_nodes import (
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
)

class VisualConcatenateNode(VisualNode):
    """Visual representation of ConcatenateNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Concatenate Strings'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('string_1')
        self.add_input('string_2')
        self.add_output('result')
        self.create_property('separator', '', widget_type='text_input')

    def get_node_class(self):
        return ConcatenateNode

class VisualFormatStringNode(VisualNode):
    """Visual representation of FormatStringNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Format String'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('template')
        self.add_input('variables')
        self.add_output('result')

    def get_node_class(self):
        return FormatStringNode

class VisualRegexMatchNode(VisualNode):
    """Visual representation of RegexMatchNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Regex Match'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('text')
        self.add_input('pattern')
        self.add_output('match_found')
        self.add_output('first_match')
        self.add_output('all_matches')
        self.add_output('groups')

    def get_node_class(self):
        return RegexMatchNode

class VisualRegexReplaceNode(VisualNode):
    """Visual representation of RegexReplaceNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Regex Replace'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('text')
        self.add_input('pattern')
        self.add_input('replacement')
        self.add_output('result')
        self.add_output('count')

    def get_node_class(self):
        return RegexReplaceNode

class VisualMathOperationNode(VisualNode):
    """Visual representation of MathOperationNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Math Operation'
    NODE_CATEGORY = 'Data Operations'

    def __init__(self):
        super().__init__()
        self.add_combo_menu('operation', 'Operation', items=[
            'add', 'subtract', 'multiply', 'divide', 'power', 'modulo'
        ], tab='inputs')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('a')
        self.add_input('b')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return MathOperationNode

class VisualComparisonNode(VisualNode):
    """Visual representation of ComparisonNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Compare Values'
    NODE_CATEGORY = 'Data Operations'

    def __init__(self):
        super().__init__()
        self.add_combo_menu('operator', 'Operator', items=[
            'equals (==)',
            'not equals (!=)',
            'greater than (>)',
            'less than (<)',
            'greater or equal (>=)',
            'less or equal (<=)'
        ], tab='inputs')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('a')
        self.add_input('b')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ComparisonNode

class VisualCreateListNode(VisualNode):
    """Visual representation of CreateListNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Create List'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('item_1')
        self.add_input('item_2')
        self.add_input('item_3')
        self.add_output('list')

    def get_node_class(self):
        return CreateListNode

class VisualListGetItemNode(VisualNode):
    """Visual representation of ListGetItemNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Get List Item'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('list')
        self.add_input('index')
        self.add_output('item')

    def get_node_class(self):
        return ListGetItemNode

class VisualJsonParseNode(VisualNode):
    """Visual representation of JsonParseNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Parse JSON'
    NODE_CATEGORY = 'Data Operations'
    
    def __init__(self):
        super().__init__()
        self.add_input('json_string')
        self.add_output('data')

    def get_node_class(self):
        return JsonParseNode

class VisualGetPropertyNode(VisualNode):
    """Visual representation of GetPropertyNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Get Property'
    NODE_CATEGORY = 'Data Operations'

    def __init__(self):
        super().__init__()
        self.add_input('object')
        self.add_input('property_path')
        self.add_output('value')

    def get_node_class(self):
        return GetPropertyNode


# =============================================================================
# List Operation Nodes
# =============================================================================

class VisualListLengthNode(VisualNode):
    """Visual representation of ListLengthNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Length'
    NODE_CATEGORY = 'List Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_output('exec_out')
        self.add_output('length')

    def get_node_class(self):
        return ListLengthNode


class VisualListAppendNode(VisualNode):
    """Visual representation of ListAppendNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Append'
    NODE_CATEGORY = 'List Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('item')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListAppendNode


class VisualListContainsNode(VisualNode):
    """Visual representation of ListContainsNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Contains'
    NODE_CATEGORY = 'List Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('item')
        self.add_output('exec_out')
        self.add_output('contains')
        self.add_output('index')

    def get_node_class(self):
        return ListContainsNode


class VisualListSliceNode(VisualNode):
    """Visual representation of ListSliceNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Slice'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('start', 'Start Index', text='0', tab='config')
        self.add_text_input('end', 'End Index', text='', tab='config')
        self.add_text_input('step', 'Step', text='1', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('start')
        self.add_input('end')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListSliceNode


class VisualListJoinNode(VisualNode):
    """Visual representation of ListJoinNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Join'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('separator', 'Separator', text='', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('separator')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListJoinNode


class VisualListSortNode(VisualNode):
    """Visual representation of ListSortNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Sort'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.create_property('reverse', False, widget_type=1, tab='config')
        self.add_text_input('key_path', 'Key Path', text='', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListSortNode


class VisualListReverseNode(VisualNode):
    """Visual representation of ListReverseNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Reverse'
    NODE_CATEGORY = 'List Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListReverseNode


class VisualListUniqueNode(VisualNode):
    """Visual representation of ListUniqueNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Unique'
    NODE_CATEGORY = 'List Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_output('exec_out')
        self.add_output('result')
        self.add_output('removed_count')

    def get_node_class(self):
        return ListUniqueNode


class VisualListFilterNode(VisualNode):
    """Visual representation of ListFilterNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Filter'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.add_combo_menu('condition', 'Condition', items=[
            'equals', 'not_equals', 'contains', 'starts_with', 'ends_with',
            'greater_than', 'less_than', 'is_not_none', 'is_none',
            'is_truthy', 'is_falsy'
        ], tab='config')
        self.add_text_input('key_path', 'Key Path', text='', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('condition')
        self.add_input('value')
        self.add_input('key_path')
        self.add_output('exec_out')
        self.add_output('result')
        self.add_output('removed')

    def get_node_class(self):
        return ListFilterNode


class VisualListMapNode(VisualNode):
    """Visual representation of ListMapNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Map'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.add_combo_menu('transform', 'Transform', items=[
            'get_property', 'to_string', 'to_int', 'to_float',
            'to_upper', 'to_lower', 'trim', 'length'
        ], tab='config')
        self.add_text_input('key_path', 'Key Path', text='', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('transform')
        self.add_input('key_path')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListMapNode


class VisualListReduceNode(VisualNode):
    """Visual representation of ListReduceNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Reduce'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.add_combo_menu('operation', 'Operation', items=[
            'sum', 'product', 'min', 'max', 'avg', 'count', 'first', 'last', 'join'
        ], tab='config')
        self.add_text_input('key_path', 'Key Path', text='', tab='config')
        self.add_text_input('separator', 'Separator (join)', text=',', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('operation')
        self.add_input('key_path')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListReduceNode


class VisualListFlattenNode(VisualNode):
    """Visual representation of ListFlattenNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'List Flatten'
    NODE_CATEGORY = 'List Operations'

    def __init__(self):
        super().__init__()
        self.create_property('depth', 1, widget_type=2, tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('list')
        self.add_input('depth')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return ListFlattenNode


# =============================================================================
# Dict Operation Nodes
# =============================================================================

class VisualDictGetNode(VisualNode):
    """Visual representation of DictGetNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Get'
    NODE_CATEGORY = 'Dict Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('key', 'Key', text='', tab='inputs')
        self.add_text_input('default', 'Default Value', text='', tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_input('key')
        self.add_input('default')
        self.add_output('exec_out')
        self.add_output('value')
        self.add_output('found')

    def get_node_class(self):
        return DictGetNode


class VisualDictSetNode(VisualNode):
    """Visual representation of DictSetNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Set'
    NODE_CATEGORY = 'Dict Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('key', 'Key', text='', tab='inputs')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_input('key')
        self.add_input('value')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return DictSetNode


class VisualDictRemoveNode(VisualNode):
    """Visual representation of DictRemoveNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Remove'
    NODE_CATEGORY = 'Dict Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('key', 'Key', text='', tab='inputs')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_input('key')
        self.add_output('exec_out')
        self.add_output('result')
        self.add_output('removed_value')

    def get_node_class(self):
        return DictRemoveNode


class VisualDictMergeNode(VisualNode):
    """Visual representation of DictMergeNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Merge'
    NODE_CATEGORY = 'Dict Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict1')
        self.add_input('dict2')
        self.add_output('exec_out')
        self.add_output('result')

    def get_node_class(self):
        return DictMergeNode


class VisualDictKeysNode(VisualNode):
    """Visual representation of DictKeysNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Keys'
    NODE_CATEGORY = 'Dict Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_output('exec_out')
        self.add_output('keys')

    def get_node_class(self):
        return DictKeysNode


class VisualDictValuesNode(VisualNode):
    """Visual representation of DictValuesNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Values'
    NODE_CATEGORY = 'Dict Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_output('exec_out')
        self.add_output('values')

    def get_node_class(self):
        return DictValuesNode


class VisualDictHasKeyNode(VisualNode):
    """Visual representation of DictHasKeyNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Has Key'
    NODE_CATEGORY = 'Dict Operations'

    def __init__(self):
        super().__init__()
        self.add_text_input('key', 'Key', text='', tab='inputs')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_input('key')
        self.add_output('exec_out')
        self.add_output('exists')

    def get_node_class(self):
        return DictHasKeyNode


class VisualCreateDictNode(VisualNode):
    """Visual representation of CreateDictNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Create Dict'
    NODE_CATEGORY = 'Dict Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('key1')
        self.add_input('value1')
        self.add_input('key2')
        self.add_input('value2')
        self.add_input('key3')
        self.add_input('value3')
        self.add_output('exec_out')
        self.add_output('dict')

    def get_node_class(self):
        return CreateDictNode


class VisualDictToJsonNode(VisualNode):
    """Visual representation of DictToJsonNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict to JSON'
    NODE_CATEGORY = 'Dict Operations'

    def __init__(self):
        super().__init__()
        self.create_property('indent', 2, widget_type=2, tab='config')

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_input('indent')
        self.add_output('exec_out')
        self.add_output('json')

    def get_node_class(self):
        return DictToJsonNode


class VisualDictItemsNode(VisualNode):
    """Visual representation of DictItemsNode."""

    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Dict Items'
    NODE_CATEGORY = 'Dict Operations'

    def setup_ports(self):
        """Setup ports."""
        self.add_input('exec_in')
        self.add_input('dict')
        self.add_output('exec_out')
        self.add_output('items')

    def get_node_class(self):
        return DictItemsNode
