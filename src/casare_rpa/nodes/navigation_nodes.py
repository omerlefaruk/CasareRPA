"""
DEPRECATED: Navigation nodes have been moved to src/casare_rpa/nodes/browser/navigation.py.
This module is kept for backward compatibility and re-exports the original classes.
"""

from casare_rpa.nodes.browser.navigation import (
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode,
)

__all__ = [
    "GoToURLNode",
    "GoBackNode",
    "GoForwardNode",
    "RefreshPageNode",
]
