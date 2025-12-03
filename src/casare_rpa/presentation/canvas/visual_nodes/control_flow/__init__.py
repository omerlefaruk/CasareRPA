"""
Visual Nodes - Control Flow
"""

from casare_rpa.presentation.canvas.visual_nodes.control_flow.nodes import (
    VisualIfNode,
    VisualForLoopNode,
    VisualForLoopStartNode,
    VisualForLoopEndNode,
    VisualWhileLoopNode,
    VisualWhileLoopStartNode,
    VisualWhileLoopEndNode,
    VisualBreakNode,
    VisualContinueNode,
    VisualMergeNode,
    VisualSwitchNode,
    # Try/Catch/Finally nodes
    VisualTryCatchFinallyNode,
    VisualTryNode,
    VisualCatchNode,
    VisualFinallyNode,
    # Parallel execution nodes
    VisualForkJoinNode,
    VisualForkNode,
    VisualJoinNode,
    VisualParallelForEachNode,
)

__all__ = [
    "VisualIfNode",
    "VisualForLoopNode",
    "VisualForLoopStartNode",
    "VisualForLoopEndNode",
    "VisualWhileLoopNode",
    "VisualWhileLoopStartNode",
    "VisualWhileLoopEndNode",
    "VisualBreakNode",
    "VisualContinueNode",
    "VisualMergeNode",
    "VisualSwitchNode",
    # Try/Catch/Finally nodes
    "VisualTryCatchFinallyNode",
    "VisualTryNode",
    "VisualCatchNode",
    "VisualFinallyNode",
    # Parallel execution nodes
    "VisualForkJoinNode",
    "VisualForkNode",
    "VisualJoinNode",
    "VisualParallelForEachNode",
]
