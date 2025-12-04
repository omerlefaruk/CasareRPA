# SetWindowStateNode

Set the state of a Windows desktop window.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.window_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\window_nodes.py:485`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `window` | INPUT | No | DataType.ANY |
| `state` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `WindowNodeBase`
