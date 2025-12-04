# GetCurrentDateTimeNode

Get the current date and time.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:54`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `datetime` | OUTPUT | DataType.STRING |
| `timestamp` | OUTPUT | DataType.FLOAT |
| `year` | OUTPUT | DataType.INTEGER |
| `month` | OUTPUT | DataType.INTEGER |
| `day` | OUTPUT | DataType.INTEGER |
| `hour` | OUTPUT | DataType.INTEGER |
| `minute` | OUTPUT | DataType.INTEGER |
| `second` | OUTPUT | DataType.INTEGER |
| `day_of_week` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timezone` | STRING | `` | No | Timezone name (default: local) |
| `format` | STRING | `` | No | Output format string (default: ISO format) |

## Inheritance

Extends: `BaseNode`
