# EvalExpressionNode

Evaluate a Python expression and return the result.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.script_nodes`
**File:** `src\casare_rpa\nodes\script_nodes.py:429`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `expression` | INPUT | No | DataType.STRING |
| `variables` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |
| `type` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
