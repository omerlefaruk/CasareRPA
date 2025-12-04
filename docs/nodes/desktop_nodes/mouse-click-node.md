# MouseClickNode

Perform mouse clicks at a position.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py:196`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `x` | INPUT | No | DataType.INTEGER |
| `y` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `click_x` | OUTPUT | DataType.INTEGER |
| `click_y` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `DesktopNodeBase`
