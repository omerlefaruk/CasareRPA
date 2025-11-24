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
    
    def __init__(self):
        super().__init__()
        self.add_input('string_1', label='String 1')
        self.add_input('string_2', label='String 2')
        self.add_output('result', label='Result')
        self.create_property('separator', '', widget_type='text_input')

    def get_node_class(self):
        return ConcatenateNode

class VisualFormatStringNode(VisualNode):
    """Visual representation of FormatStringNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Format String'
    
    def __init__(self):
        super().__init__()
        self.add_input('template', label='Template')
        self.add_input('variables', label='Variables (Dict)')
        self.add_output('result', label='Result')

    def get_node_class(self):
        return FormatStringNode

class VisualRegexMatchNode(VisualNode):
    """Visual representation of RegexMatchNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Regex Match'
    
    def __init__(self):
        super().__init__()
        self.add_input('text', label='Text')
        self.add_input('pattern', label='Pattern')
        self.add_output('match_found', label='Match Found')
        self.add_output('first_match', label='First Match')
        self.add_output('all_matches', label='All Matches')
        self.add_output('groups', label='Groups')

    def get_node_class(self):
        return RegexMatchNode

class VisualRegexReplaceNode(VisualNode):
    """Visual representation of RegexReplaceNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Regex Replace'
    
    def __init__(self):
        super().__init__()
        self.add_input('text', label='Text')
        self.add_input('pattern', label='Pattern')
        self.add_input('replacement', label='Replacement')
        self.add_output('result', label='Result')
        self.add_output('count', label='Count')

    def get_node_class(self):
        return RegexReplaceNode

class VisualMathOperationNode(VisualNode):
    """Visual representation of MathOperationNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Math Operation'
    
    def __init__(self):
        super().__init__()
        self.add_input('a', label='A')
        self.add_input('b', label='B')
        self.add_output('result', label='Result')
        
        items = ['add', 'subtract', 'multiply', 'divide', 'power', 'modulo']
        self.create_property('operation', 'add', items=items, widget_type='combo')

    def get_node_class(self):
        return MathOperationNode

class VisualComparisonNode(VisualNode):
    """Visual representation of ComparisonNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Compare Values'
    
    def __init__(self):
        super().__init__()
        self.add_input('a', label='A')
        self.add_input('b', label='B')
        self.add_output('result', label='Result')
        
        items = ['==', '!=', '>', '<', '>=', '<=']
        self.create_property('operator', '==', items=items, widget_type='combo')

    def get_node_class(self):
        return ComparisonNode

class VisualCreateListNode(VisualNode):
    """Visual representation of CreateListNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Create List'
    
    def __init__(self):
        super().__init__()
        self.add_input('item_1', label='Item 1')
        self.add_input('item_2', label='Item 2')
        self.add_input('item_3', label='Item 3')
        self.add_output('list', label='List')

    def get_node_class(self):
        return CreateListNode

class VisualListGetItemNode(VisualNode):
    """Visual representation of ListGetItemNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Get List Item'
    
    def __init__(self):
        super().__init__()
        self.add_input('list', label='List')
        self.add_input('index', label='Index')
        self.add_output('item', label='Item')

    def get_node_class(self):
        return ListGetItemNode

class VisualJsonParseNode(VisualNode):
    """Visual representation of JsonParseNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Parse JSON'
    
    def __init__(self):
        super().__init__()
        self.add_input('json_string', label='JSON String')
        self.add_output('data', label='Data')

    def get_node_class(self):
        return JsonParseNode

class VisualGetPropertyNode(VisualNode):
    """Visual representation of GetPropertyNode."""
    
    __identifier__ = 'casare_rpa.data'
    NODE_NAME = 'Get Property'
    
    def __init__(self):
        super().__init__()
        self.add_input('object', label='Object/Dict')
        self.add_input('property_path', label='Property Path')
        self.add_output('value', label='Value')

    def get_node_class(self):
        return GetPropertyNode
