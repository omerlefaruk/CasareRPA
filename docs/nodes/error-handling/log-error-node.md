# LogErrorNode

Log error details with structured information.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:858`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `error_message` | INPUT | No | DataType.STRING |
| `error_type` | INPUT | No | DataType.STRING |
| `context` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `log_entry` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `level` | CHOICE | `error` | No | Logging severity level Choices: debug, info, warning, error, critical |
| `include_stack_trace` | BOOLEAN | `False` | No | Include stack trace in log output |

## Inheritance

Extends: `BaseNode`
