# SelectTabNode

Select a tab in a tab control.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.interaction_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\interaction_nodes.py:284`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `tab_control` | INPUT | No | DataType.ANY |
| `tab_name` | INPUT | No | DataType.STRING |
| `tab_index` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `InteractionNodeBase`
