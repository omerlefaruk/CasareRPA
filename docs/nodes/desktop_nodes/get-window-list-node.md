# GetWindowListNode

Get a list of all open Windows desktop windows.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.application_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\application_nodes.py:342`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `window_list` | OUTPUT | DataType.LIST |
| `window_count` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `DesktopNodeBase`
