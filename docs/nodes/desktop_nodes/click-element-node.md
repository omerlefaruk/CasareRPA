# ClickElementNode

Click a desktop UI element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.element_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\element_nodes.py:141`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `element` | INPUT | No | DataType.ANY |
| `window` | INPUT | No | DataType.ANY |
| `selector` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`, `ElementInteractionMixin`
