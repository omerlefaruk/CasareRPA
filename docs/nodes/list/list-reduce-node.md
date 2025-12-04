# ListReduceNode

Node that reduces a list to a single value.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:646`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `operation` | INPUT | No | DataType.STRING |
| `key_path` | INPUT | No | DataType.STRING |
| `initial` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `operation` | CHOICE | `sum` | No | Reduction operation to perform Choices: sum, product, min, max, avg, ... (9 total) |
| `key_path` | STRING | `` | No | Dot-separated path to values (for dict items) |

## Inheritance

Extends: `BaseNode`
