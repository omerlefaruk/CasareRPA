# SheetsUpdateRowNode

Update an existing row in Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:524`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `row_num` | INPUT | No | DataType.INTEGER |
| `values` | INPUT | No | DataType.ARRAY |
| `start_col` | INPUT | No | DataType.STRING |
| `value_input_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `updated_cells` | OUTPUT | DataType.INTEGER |
| `updated_range` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `row_num` | INTEGER | `1` | Yes | 1-based row number to update (min: 1) |
| `values` | JSON | `[]` | Yes | Array of values to write to the row |
| `start_col` | STRING | `A` | No | Starting column letter |

## Inheritance

Extends: `SheetsBaseNode`
