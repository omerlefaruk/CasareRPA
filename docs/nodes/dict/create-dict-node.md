# CreateDictNode

Node that creates a dictionary from key-value pairs.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:357`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `key_1` | INPUT | No | DataType.STRING |
| `value_1` | INPUT | No | DataType.ANY |
| `key_2` | INPUT | No | DataType.STRING |
| `value_2` | INPUT | No | DataType.ANY |
| `key_3` | INPUT | No | DataType.STRING |
| `value_3` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `dict` | OUTPUT | DataType.DICT |

## Inheritance

Extends: `BaseNode`
