# LogNode

Log node - explicit logging within workflows.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.utility_nodes`
**File:** `src\casare_rpa\nodes\utility_nodes.py:765`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message` | INPUT | No | DataType.STRING |
| `data` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `message` | STRING | `` | No | Message to log (can include {variable} placeholders) |
| `level` | CHOICE | `critical` | No | Log level (debug, info, warning, error, critical) Choices: debug, info, warning, error, critical |
| `include_timestamp` | BOOLEAN | `True` | No | Include timestamp in log message |
| `include_node_id` | BOOLEAN | `True` | No | Include node ID in log message |

## Inheritance

Extends: `BaseNode`
