# SendKeysNode

Send keyboard input.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py:309`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `keys` | INPUT | No | DataType.STRING |
| `interval` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `keys_sent` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `DesktopNodeBase`
