# DateTimeDiffNode

Calculate the difference between two datetimes.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:432`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `datetime_1` | INPUT | No | DataType.ANY |
| `datetime_2` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `total_seconds` | OUTPUT | DataType.FLOAT |
| `total_minutes` | OUTPUT | DataType.FLOAT |
| `total_hours` | OUTPUT | DataType.FLOAT |
| `total_days` | OUTPUT | DataType.FLOAT |
| `days` | OUTPUT | DataType.INTEGER |
| `hours` | OUTPUT | DataType.INTEGER |
| `minutes` | OUTPUT | DataType.INTEGER |
| `seconds` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
