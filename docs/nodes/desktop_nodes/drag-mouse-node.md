# DragMouseNode

Drag the mouse from one position to another.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py:515`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `start_x` | INPUT | No | DataType.INTEGER |
| `start_y` | INPUT | No | DataType.INTEGER |
| `end_x` | INPUT | No | DataType.INTEGER |
| `end_y` | INPUT | No | DataType.INTEGER |
| `duration` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`
