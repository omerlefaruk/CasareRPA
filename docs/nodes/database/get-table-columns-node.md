# GetTableColumnsNode

Get column information for a table.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.database.database_utils`
**File:** `src\casare_rpa\nodes\database\database_utils.py:230`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `connection` | INPUT | No | DataType.ANY |
| `table_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `columns` | OUTPUT | DataType.LIST |
| `column_names` | OUTPUT | DataType.LIST |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
