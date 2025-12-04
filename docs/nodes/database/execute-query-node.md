# ExecuteQueryNode

Execute a SELECT query and return results.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.sql_nodes`
**File:** `src\casare_rpa\nodes\database\sql_nodes.py:574`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `connection` | INPUT | No | DataType.ANY |
| `query` | INPUT | No | DataType.STRING |
| `parameters` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `results` | OUTPUT | DataType.LIST |
| `row_count` | OUTPUT | DataType.INTEGER |
| `columns` | OUTPUT | DataType.LIST |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `query` | STRING | `` | No | SELECT query to execute |
| `parameters` | LIST | `[]` | No | Parameterized query values (for safe queries) |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retry attempts in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
