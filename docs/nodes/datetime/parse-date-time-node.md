# ParseDateTimeNode

Parse a datetime string into components.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:244`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `datetime_string` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `timestamp` | OUTPUT | DataType.FLOAT |
| `year` | OUTPUT | DataType.INTEGER |
| `month` | OUTPUT | DataType.INTEGER |
| `day` | OUTPUT | DataType.INTEGER |
| `hour` | OUTPUT | DataType.INTEGER |
| `minute` | OUTPUT | DataType.INTEGER |
| `second` | OUTPUT | DataType.INTEGER |
| `iso_format` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `format` | STRING | `` | No | Expected format string (optional, will try auto-detect) |

## Inheritance

Extends: `BaseNode`
