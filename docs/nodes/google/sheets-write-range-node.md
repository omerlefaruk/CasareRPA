# SheetsWriteRangeNode

Write a range of values to Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:244`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `range` | INPUT | No | DataType.STRING |
| `values` | INPUT | No | DataType.ARRAY |
| `value_input_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `updated_cells` | OUTPUT | DataType.INTEGER |
| `updated_rows` | OUTPUT | DataType.INTEGER |
| `updated_columns` | OUTPUT | DataType.INTEGER |
| `updated_range` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `range` | STRING | `Sheet1!A1:B10` | Yes | Range in A1 notation (e.g., 'Sheet1!A1:B10') |
| `values` | JSON | `[]` | Yes | 2D array of values to write |

## Inheritance

Extends: `SheetsBaseNode`
