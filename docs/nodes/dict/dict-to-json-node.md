# DictToJsonNode

Node that converts a dictionary to a JSON string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.dict_nodes`
**File:** `src\casare_rpa\nodes\dict_nodes.py:418`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `dict` | INPUT | No | DataType.DICT |
| `indent` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `json_string` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `indent` | INTEGER | `-` | No | Number of spaces for indentation (None = compact) (min: 0) |
| `sort_keys` | BOOLEAN | `False` | No | Sort dictionary keys alphabetically |
| `ensure_ascii` | BOOLEAN | `True` | No | Escape non-ASCII characters |

## Inheritance

Extends: `BaseNode`
