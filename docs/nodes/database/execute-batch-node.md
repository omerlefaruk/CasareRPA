# ExecuteBatchNode

Execute multiple SQL statements as a batch.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.sql_nodes`
**File:** `src\casare_rpa\nodes\database\sql_nodes.py:1341`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `connection` | INPUT | No | DataType.ANY |
| `statements` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `results` | OUTPUT | DataType.LIST |
| `total_rows_affected` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `statements` | LIST | `[]` | No | List of SQL statements to execute as a batch |
| `stop_on_error` | BOOLEAN | `True` | No | Stop batch execution on first error |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts per statement on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retry attempts in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
