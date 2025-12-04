# ActivateWindowNode

Activate (bring to foreground) a Windows desktop window.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.application_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\application_nodes.py:257`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `window` | INPUT | No | DataType.ANY |
| `window_title` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `window` | OUTPUT | DataType.ANY |

## Inheritance

Extends: `DesktopNodeBase`
