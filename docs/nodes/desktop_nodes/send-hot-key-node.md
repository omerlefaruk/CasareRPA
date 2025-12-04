# SendHotKeyNode

Send hotkey combinations (e.g., Ctrl+C, Alt+Tab, Enter).

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py:401`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `keys` | INPUT | No | DataType.STRING |
| `wait_time` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`
