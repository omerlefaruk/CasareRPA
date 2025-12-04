# FormatStringNode

Node that formats a string using python's format() method.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.string_nodes`
**File:** `src\casare_rpa\nodes\string_nodes.py:61`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `template` | INPUT | No | DataType.STRING |
| `variables` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
