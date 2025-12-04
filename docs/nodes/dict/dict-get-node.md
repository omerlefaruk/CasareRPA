# DictGetNode

Node that gets a value from a dictionary by key.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:92`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `dict` | INPUT | No | DataType.DICT |
| `key` | INPUT | No | DataType.STRING |
| `default` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |
| `found` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
