# FormatDateTimeNode

Format a datetime to a string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.datetime_nodes`
**File:** `src\casare_rpa\nodes\datetime_nodes.py:154`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `datetime` | INPUT | No | DataType.ANY |
| `input_format` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `format` | STRING | `%Y-%m-%d %H:%M:%S` | No | strftime format string |

## Inheritance

Extends: `BaseNode`
