# Control Flow Package Index

Conditionals, loops, and error handling nodes.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Package exports | IfNode, ForLoopStartNode |
| `conditionals.py` | If/Switch/Merge | IfNode, SwitchNode, MergeNode |
| `loops.py` | Loop constructs | ForLoopStartNode, ForLoopEndNode, BreakNode |
| `error_handling.py` | Error recovery | TryCatchNode, ThrowNode |

## Entry Points

```python
from casare_rpa.nodes.control_flow import (
    # Conditionals
    IfNode,
    SwitchNode,
    MergeNode,
    # Loops
    ForLoopStartNode,
    ForLoopEndNode,
    ForEachLoopStartNode,
    ForEachLoopEndNode,
    WhileLoopStartNode,
    WhileLoopEndNode,
    BreakNode,
    ContinueNode,
)
```

## Loop Patterns

```
ForLoopStartNode → (loop body) → ForLoopEndNode
                         ↓
                     BreakNode (early exit)
```
