# VerifyElementPropertyNode

Verify an element property has an expected value.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.wait_verification_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\wait_verification_nodes.py:266`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `element` | INPUT | No | DataType.ANY |
| `property_name` | INPUT | No | DataType.STRING |
| `expected_value` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.BOOLEAN |
| `actual_value` | OUTPUT | DataType.ANY |

## Inheritance

Extends: `DesktopNodeBase`
