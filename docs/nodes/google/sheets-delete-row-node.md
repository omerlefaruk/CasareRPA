# SheetsDeleteRowNode

Delete one or more rows from Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:832`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `row_num` | INPUT | No | DataType.INTEGER |
| `num_rows` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `deleted_rows` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `row_num` | INTEGER | `1` | Yes | 1-based row number to delete (min: 1) |
| `num_rows` | INTEGER | `1` | No | Number of rows to delete (default: 1) (min: 1) |

## Inheritance

Extends: `SheetsBaseNode`
