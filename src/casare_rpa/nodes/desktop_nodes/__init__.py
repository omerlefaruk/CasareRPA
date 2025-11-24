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

from .window_nodes import (
    ResizeWindowNode,
    MoveWindowNode,
    MaximizeWindowNode,
    MinimizeWindowNode,
    RestoreWindowNode,
    GetWindowPropertiesNode,
    SetWindowStateNode,
)

from .interaction_nodes import (
    SelectFromDropdownNode,
    CheckCheckboxNode,
    SelectRadioButtonNode,
    SelectTabNode,
    ExpandTreeItemNode,
    ScrollElementNode,
)

__all__ = [
    # Application nodes
    'LaunchApplicationNode',
    'CloseApplicationNode',
    'ActivateWindowNode',
    'GetWindowListNode',
    # Element nodes
    'FindElementNode',
    'ClickElementNode',
    'TypeTextNode',
    'GetElementTextNode',
    'GetElementPropertyNode',
    # Window management nodes
    'ResizeWindowNode',
    'MoveWindowNode',
    'MaximizeWindowNode',
    'MinimizeWindowNode',
    'RestoreWindowNode',
    'GetWindowPropertiesNode',
    'SetWindowStateNode',
    # Advanced interaction nodes
    'SelectFromDropdownNode',
    'CheckCheckboxNode',
    'SelectRadioButtonNode',
    'SelectTabNode',
    'ExpandTreeItemNode',
    'ScrollElementNode',
]
