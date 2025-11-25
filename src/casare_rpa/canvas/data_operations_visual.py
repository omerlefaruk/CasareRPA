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
    GetPropertyNode
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
