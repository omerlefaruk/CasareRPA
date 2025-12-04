# GetPropertyNode

Node that gets a property from a dictionary/object.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:51`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `object` | INPUT | No | DataType.DICT |
| `property_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |

## Inheritance

Extends: `BaseNode`
