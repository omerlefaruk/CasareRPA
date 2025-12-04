# DateTimeCompareNode

Compare two datetimes.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:532`


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
| `is_before` | OUTPUT | DataType.BOOLEAN |
| `is_after` | OUTPUT | DataType.BOOLEAN |
| `is_equal` | OUTPUT | DataType.BOOLEAN |
| `comparison` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
