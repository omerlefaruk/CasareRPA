# GetServiceStatusNode

Get the status of a Windows service.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.service_nodes`
**File:** `src\casare_rpa\nodes\system\service_nodes.py:27`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `service_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `status` | OUTPUT | DataType.STRING |
| `display_name` | OUTPUT | DataType.STRING |
| `exists` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
