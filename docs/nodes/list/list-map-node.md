# ListMapNode

Node that transforms each item in a list.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:555`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `transform` | INPUT | No | DataType.STRING |
| `key_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `transform` | CHOICE | `to_string` | No | Transformation to apply to each item Choices: get_property, to_string, to_int, to_float, to_upper, ... (8 total) |
| `key_path` | STRING | `` | No | Dot-separated path to extract (for dict items) |

## Inheritance

Extends: `BaseNode`
