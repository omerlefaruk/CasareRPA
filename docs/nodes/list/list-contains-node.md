# ListContainsNode

Node that checks if a list contains an item.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:157`


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
| `contains` | OUTPUT | DataType.BOOLEAN |
| `index` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
