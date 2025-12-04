# RollbackTransactionNode

Rollback the current database transaction.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.sql_nodes`
**File:** `src\casare_rpa\nodes\database\sql_nodes.py:1167`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `connection` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `connection` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
