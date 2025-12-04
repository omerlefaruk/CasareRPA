# RetryNode

Retry node for automatic retry with backoff.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:143`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `retry_body` | EXEC_OUTPUT |  |
| `success` | EXEC_OUTPUT |  |
| `failed` | EXEC_OUTPUT |  |
| `attempt` | OUTPUT | DataType.INTEGER |
| `last_error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `max_attempts` | INTEGER | `3` | No | Maximum number of retry attempts (min: 1) |
| `initial_delay` | FLOAT | `1.0` | No | Initial delay before first retry (min: 0.0) |
| `backoff_multiplier` | FLOAT | `2.0` | No | Exponential backoff multiplier for retry delays (min: 1.0) |

## Inheritance

Extends: `BaseNode`
