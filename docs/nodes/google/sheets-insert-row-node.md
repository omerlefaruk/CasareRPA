# SheetsInsertRowNode

Insert a new row at a specific position in Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:675`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `row_num` | INPUT | No | DataType.INTEGER |
| `values` | INPUT | No | DataType.ARRAY |
| `value_input_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `inserted_row` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `row_num` | INTEGER | `1` | Yes | 1-based row number where to insert (min: 1) |
| `values` | JSON | `[]` | No | Optional values to write to the new row |

## Inheritance

Extends: `SheetsBaseNode`
