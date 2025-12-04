# RunPowerShellNode

Run a PowerShell script or command.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.command_nodes`
**File:** `src\casare_rpa\nodes\system\command_nodes.py:311`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `script` | INPUT | No | DataType.STRING |

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
| `timeout` | INTEGER | `60` | No | Command timeout in seconds (min: 1) |
| `execution_policy` | CHOICE | `RemoteSigned` | No | PowerShell execution policy Choices: RemoteSigned, Bypass, Unrestricted, AllSigned, Restricted |
| `allow_dangerous` | BOOLEAN | `False` | No | Allow dangerous PowerShell patterns (NOT RECOMMENDED) |
| `constrained_mode` | BOOLEAN | `False` | No | Use PowerShell Constrained Language Mode for additional security |

## Inheritance

Extends: `BaseNode`
