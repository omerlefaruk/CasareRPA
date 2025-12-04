# MoveWindowNode

Move a Windows desktop window.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.window_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\window_nodes.py:170`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `window` | INPUT | No | DataType.ANY |
| `x` | INPUT | No | DataType.INTEGER |
| `y` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `WindowNodeBase`
