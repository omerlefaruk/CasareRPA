# CatchNode

Catch block for handling errors from the Try block.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:892`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `catch_body` | EXEC_OUTPUT |  |
| `error_message` | OUTPUT | DataType.STRING |
| `error_type` | OUTPUT | DataType.STRING |
| `stack_trace` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `error_types` | STRING | `` | No | Comma-separated error types to catch (empty = catch all). E.g., 'ValueError,KeyError' |

## Inheritance

Extends: `BaseNode`
