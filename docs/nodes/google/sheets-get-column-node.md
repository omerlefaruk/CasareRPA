# SheetsGetColumnNode

Read an entire column from Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:483`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `column` | INPUT | No | DataType.STRING |
| `start_row` | INPUT | No | DataType.INTEGER |
| `end_row` | INPUT | No | DataType.INTEGER |
| `value_render_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `values` | OUTPUT | DataType.ARRAY |
| `cell_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `column` | STRING | `A` | Yes | Column letter (e.g., 'A', 'B', 'AA') |
| `start_row` | INTEGER | `1` | No | 1-based starting row number (min: 1) |
| `end_row` | INTEGER | `1000` | No | 1-based ending row number (min: 1) |

## Inheritance

Extends: `SheetsBaseNode`
