"""
CasareRPA - Control Flow Nodes (Compatibility Module)

This module re-exports control flow nodes from their new locations
for backward compatibility.

Node classes have been split into:
- control_flow/conditionals.py: IfNode, SwitchNode, MergeNode
- control_flow/loops.py: ForLoopStartNode, ForLoopEndNode, WhileLoopStartNode,
                         WhileLoopEndNode, BreakNode, ContinueNode
- control_flow/error_handling.py: TryNode, CatchNode, FinallyNode

For new code, prefer importing from:
    from casare_rpa.nodes.control_flow import IfNode, ForLoopStartNode
    # or
    from casare_rpa.nodes import IfNode  # via lazy loading
"""

# Re-export all nodes for backward compatibility
# Conditionals
from casare_rpa.nodes.control_flow.conditionals import (
    IfNode,
    SwitchNode,
    MergeNode,
)

# Loops
from casare_rpa.nodes.control_flow.loops import (
    ForLoopStartNode,
    ForLoopEndNode,
    WhileLoopStartNode,
    WhileLoopEndNode,
    BreakNode,
    ContinueNode,
)

# Error Handling (Try/Catch/Finally)
from casare_rpa.nodes.control_flow.error_handling import (
    TryNode,
    CatchNode,
    FinallyNode,
)

__all__ = [
    # Conditionals
    "IfNode",
    "SwitchNode",
    "MergeNode",
    # Loops
    "ForLoopStartNode",
    "ForLoopEndNode",
    "WhileLoopStartNode",
    "WhileLoopEndNode",
    "BreakNode",
    "ContinueNode",
    # Error Handling
    "TryNode",
    "CatchNode",
    "FinallyNode",
]
