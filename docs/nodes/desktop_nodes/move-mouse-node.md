# MoveMouseNode

Move the mouse cursor to a specific position.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py:110`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `x` | INPUT | No | DataType.INTEGER |
| `y` | INPUT | No | DataType.INTEGER |
| `duration` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `final_x` | OUTPUT | DataType.INTEGER |
| `final_y` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `DesktopNodeBase`
