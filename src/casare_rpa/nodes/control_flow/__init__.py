"""
CasareRPA - Control Flow Nodes Package

Provides workflow control flow nodes organized by responsibility:

- conditionals.py: IfNode, SwitchNode, MergeNode
- loops.py: ForLoopStartNode, ForLoopEndNode, WhileLoopStartNode, WhileLoopEndNode, BreakNode, ContinueNode
- error_handling.py: TryNode, CatchNode, FinallyNode

Node Registry Entries:
    All nodes in this package are registered in `NODE_REGISTRY` at:
    src/casare_rpa/nodes/registry_data.py

Usage:
    from casare_rpa.nodes.control_flow import IfNode, ForLoopStartNode
    # or
    from casare_rpa.nodes import IfNode  # via lazy loading
"""

# Conditionals
from casare_rpa.nodes.control_flow.conditionals import (
    IfNode,
    MergeNode,
    SwitchNode,
)

# Error Handling (Try/Catch/Finally)
from casare_rpa.nodes.control_flow.error_handling import (
    CatchNode,
    FinallyNode,
    TryNode,
)

# Loops
from casare_rpa.nodes.control_flow.loops import (
    BreakNode,
    ContinueNode,
    ForLoopEndNode,
    ForLoopStartNode,
    WhileLoopEndNode,
    WhileLoopStartNode,
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
