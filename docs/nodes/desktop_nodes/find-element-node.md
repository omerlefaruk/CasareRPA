# FindElementNode

Find a desktop UI element within a window.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.element_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\element_nodes.py:51`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `window` | INPUT | No | DataType.ANY |
| `selector` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `element` | OUTPUT | DataType.ANY |
| `found` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`
