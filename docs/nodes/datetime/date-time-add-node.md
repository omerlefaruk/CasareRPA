# DateTimeAddNode

Add or subtract time from a datetime.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:343`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `datetime` | INPUT | No | DataType.ANY |
| `years` | INPUT | No | DataType.INTEGER |
| `months` | INPUT | No | DataType.INTEGER |
| `weeks` | INPUT | No | DataType.INTEGER |
| `days` | INPUT | No | DataType.INTEGER |
| `hours` | INPUT | No | DataType.INTEGER |
| `minutes` | INPUT | No | DataType.INTEGER |
| `seconds` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |
| `timestamp` | OUTPUT | DataType.FLOAT |

## Inheritance

Extends: `BaseNode`
