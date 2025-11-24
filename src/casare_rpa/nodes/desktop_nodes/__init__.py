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

__all__ = [
    'LaunchApplicationNode',
    'CloseApplicationNode',
    'ActivateWindowNode',
    'GetWindowListNode',
]
