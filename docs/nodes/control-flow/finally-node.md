# FinallyNode

Finally block - always executes after Try/Catch regardless of errors.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:991`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `finally_body` | EXEC_OUTPUT |  |
| `had_error` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
