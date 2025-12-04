# TryNode

Try block node for error handling.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:27`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `try_body` | EXEC_OUTPUT |  |
| `success` | EXEC_OUTPUT |  |
| `catch` | EXEC_OUTPUT |  |
| `error_message` | OUTPUT | DataType.STRING |
| `error_type` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
