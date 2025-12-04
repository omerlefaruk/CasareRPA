# DictItemsNode

Node that gets key-value pairs from a dictionary as a list of dicts.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:464`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `dict` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `items` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
