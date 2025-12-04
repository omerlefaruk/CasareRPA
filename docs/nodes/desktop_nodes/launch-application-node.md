# LaunchApplicationNode

Launch a Windows desktop application.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.application_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\application_nodes.py:39`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `application_path` | INPUT | No | DataType.STRING |
| `arguments` | INPUT | No | DataType.STRING |
| `working_directory` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `window` | OUTPUT | DataType.ANY |
| `process_id` | OUTPUT | DataType.INTEGER |
| `window_title` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `DesktopNodeBase`
