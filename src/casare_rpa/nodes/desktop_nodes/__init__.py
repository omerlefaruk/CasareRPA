"""
Desktop Automation Nodes

Nodes for Windows desktop automation using UI Automation.
"""

from .application_nodes import (
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode,
)

from .element_nodes import (
    FindElementNode,
    ClickElementNode,
    TypeTextNode,
    GetElementTextNode,
    GetElementPropertyNode,
)

__all__ = [
    'LaunchApplicationNode',
    'CloseApplicationNode',
    'ActivateWindowNode',
    'GetWindowListNode',
    'FindElementNode',
    'ClickElementNode',
    'TypeTextNode',
    'GetElementTextNode',
    'GetElementPropertyNode',
]
