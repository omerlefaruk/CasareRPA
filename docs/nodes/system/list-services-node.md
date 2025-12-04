# ListServicesNode

List all Windows services.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.service_nodes`
**File:** `src\casare_rpa\nodes\system\service_nodes.py:350`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `services` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `state_filter` | CHOICE | `all` | No | Filter services by state Choices: all, running, stopped |

## Inheritance

Extends: `BaseNode`
