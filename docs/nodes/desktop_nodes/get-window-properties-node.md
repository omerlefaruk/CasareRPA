# GetWindowPropertiesNode

Get properties of a Windows desktop window.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.window_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\window_nodes.py:402`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `window` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `properties` | OUTPUT | DataType.DICT |
| `title` | OUTPUT | DataType.STRING |
| `x` | OUTPUT | DataType.INTEGER |
| `y` | OUTPUT | DataType.INTEGER |
| `width` | OUTPUT | DataType.INTEGER |
| `height` | OUTPUT | DataType.INTEGER |
| `state` | OUTPUT | DataType.STRING |
| `is_maximized` | OUTPUT | DataType.BOOLEAN |
| `is_minimized` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `WindowNodeBase`
