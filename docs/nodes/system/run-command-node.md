# RunCommandNode

Run a terminal/CMD command.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.command_nodes`
**File:** `src\casare_rpa\nodes\system\command_nodes.py:70`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `command` | INPUT | No | DataType.STRING |
| `args` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `stdout` | OUTPUT | DataType.STRING |
| `stderr` | OUTPUT | DataType.STRING |
| `return_code` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `shell` | BOOLEAN | `False` | No | Use shell execution (less secure) |
| `timeout` | INTEGER | `60` | No | Command timeout in seconds (min: 1) |
| `working_dir` | STRING | `` | No | Working directory for command execution |
| `capture_output` | BOOLEAN | `True` | No | Capture stdout and stderr |
| `allow_dangerous` | BOOLEAN | `False` | No | Allow blocked commands and dangerous characters (NOT RECOMMENDED) |

## Inheritance

Extends: `BaseNode`
