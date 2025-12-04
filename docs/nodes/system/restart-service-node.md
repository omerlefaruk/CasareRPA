# RestartServiceNode

Restart a Windows service.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.service_nodes`
**File:** `src\casare_rpa\nodes\system\service_nodes.py:264`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `service_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `message` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `wait_time` | INTEGER | `2` | No | Seconds to wait between stop and start (min: 0) |

## Inheritance

Extends: `BaseNode`
