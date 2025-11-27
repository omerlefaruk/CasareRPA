"""
COMPATIBILITY LAYER - Visual Nodes

This module provides backward compatibility for old import paths.
All visual nodes have been reorganized into:
    src/casare_rpa/presentation/canvas/visual_nodes/

Old code will continue to work:
    from casare_rpa.canvas.visual_nodes import VisualStartNode

But new code should use:
    from casare_rpa.presentation.canvas.visual_nodes import VisualStartNode

This compatibility layer will be removed in v3.0.
"""

# Re-export all visual nodes from new location
from casare_rpa.presentation.canvas.visual_nodes import *  # noqa: F401, F403

__all__ = [
    # All nodes are re-exported from presentation.canvas.visual_nodes
    # See: src/casare_rpa/presentation/canvas/visual_nodes/__init__.py
]
