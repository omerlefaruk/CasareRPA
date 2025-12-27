# Control Flow Package Index

```xml<control_flow_index>
  <!-- Conditionals, loops, and error handling nodes. -->

  <files>
    <f>__init__.py</f>        <e>IfNode, ForLoopStartNode</e>
    <f>conditionals.py</f>    <e>IfNode, SwitchNode, MergeNode</e>
    <f>loops.py</f>           <e>ForLoopStartNode, ForLoopEndNode, BreakNode</e>
    <f>error_handling.py</f>   <e>TryCatchNode, ThrowNode</e>
  </files>

  <entry_points>
    <code>
from casare_rpa.nodes.control_flow import (
    # Conditionals
    IfNode, SwitchNode, MergeNode,
    # Loops
    ForLoopStartNode, ForLoopEndNode,
    ForEachLoopStartNode, ForEachLoopEndNode,
    WhileLoopStartNode, WhileLoopEndNode,
    BreakNode, ContinueNode,
)
    </code>
  </entry_points>

  <loop_pattern>
    <p>ForLoopStartNode → (loop body) → ForLoopEndNode</p>
    <p>                         ↓</p>
    <p>                     BreakNode (early exit)</p>
  </loop_pattern>
</control_flow_index>
```
