"""
DEPRECATED: Interaction nodes have been moved to src/casare_rpa/nodes/browser/interaction.py.
This module is kept for backward compatibility and re-exports the original classes.
"""

from casare_rpa.nodes.browser.interaction import (
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode,
    ImageClickNode,
    PressKeyNode,
)

__all__ = [
    "ClickElementNode",
    "TypeTextNode",
    "SelectDropdownNode",
    "ImageClickNode",
    "PressKeyNode",
]
