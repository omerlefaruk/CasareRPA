# WaitForWindowNode

Wait for a window to reach a specific state.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.wait_verification_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\wait_verification_nodes.py:111`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `title` | INPUT | No | DataType.STRING |
| `title_regex` | INPUT | No | DataType.STRING |
| `class_name` | INPUT | No | DataType.STRING |
| `timeout` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `window` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`
