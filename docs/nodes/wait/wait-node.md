# WaitNode

Wait node - pauses execution for a specified duration.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.wait_nodes`
**File:** `src\casare_rpa\nodes\wait_nodes.py:58`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `duration` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `duration` | FLOAT | `1.0` | No | Wait duration in seconds |

## Inheritance

Extends: `BaseNode`
