# ErrorRecoveryNode

Configure error recovery strategy for workflow.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:772`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `strategy` | INPUT | No | DataType.STRING |
| `max_retries` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC_OUTPUT |  |
| `fallback` | EXEC_OUTPUT |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `strategy` | CHOICE | `stop` | No | Error recovery strategy Choices: stop, continue, retry, restart, fallback |
| `max_retries` | INTEGER | `3` | No | Maximum retries for 'retry' strategy (min: 0) |

## Inheritance

Extends: `BaseNode`
