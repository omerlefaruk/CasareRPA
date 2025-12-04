# OnErrorNode

Global error handler node.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:646`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `protected_body` | EXEC_OUTPUT |  |
| `on_error` | EXEC_OUTPUT |  |
| `finally` | EXEC_OUTPUT |  |
| `error_message` | OUTPUT | DataType.STRING |
| `error_type` | OUTPUT | DataType.STRING |
| `error_node` | OUTPUT | DataType.STRING |
| `stack_trace` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
