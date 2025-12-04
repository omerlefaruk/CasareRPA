# SheetsAppendRowNode

Append a row to the end of data in a Google Sheet.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:377`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `values` | INPUT | No | DataType.ARRAY |
| `value_input_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `updated_cells` | OUTPUT | DataType.INTEGER |
| `updated_range` | OUTPUT | DataType.STRING |
| `table_range` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `values` | JSON | `[]` | Yes | Array of values for the new row |

## Inheritance

Extends: `SheetsBaseNode`
