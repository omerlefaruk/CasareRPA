# TypeTextNode

Type text into a desktop UI element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.element_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\element_nodes.py:222`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `element` | INPUT | No | DataType.ANY |
| `window` | INPUT | No | DataType.ANY |
| `selector` | INPUT | No | DataType.ANY |
| `text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`, `ElementInteractionMixin`
