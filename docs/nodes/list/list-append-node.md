# ListAppendNode

Node that appends an item to a list.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:123`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `item` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.LIST |

## Inheritance

Extends: `BaseNode`
