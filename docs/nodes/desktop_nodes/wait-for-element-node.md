# WaitForElementNode

Wait for an element to reach a specific state.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.wait_verification_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\wait_verification_nodes.py:34`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `selector` | INPUT | No | DataType.ANY |
| `timeout` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `element` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DesktopNodeBase`
