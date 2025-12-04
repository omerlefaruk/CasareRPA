# DictKeysNode

Node that gets all keys from a dictionary.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:248`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `dict` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `keys` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
