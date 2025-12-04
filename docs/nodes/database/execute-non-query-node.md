# ExecuteNonQueryNode

Execute INSERT, UPDATE, DELETE, or DDL statements.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.sql_nodes`
**File:** `src\casare_rpa\nodes\database\sql_nodes.py:807`


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
| `rows_affected` | OUTPUT | DataType.INTEGER |
| `last_insert_id` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `query` | STRING | `` | No | INSERT, UPDATE, DELETE, or DDL statement |
| `parameters` | LIST | `[]` | No | Parameterized query values (for safe queries) |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retry attempts in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
