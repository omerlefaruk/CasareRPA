# SheetsGetRowNode

Read an entire row from Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:345`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `row_num` | INPUT | No | DataType.INTEGER |
| `start_col` | INPUT | No | DataType.STRING |
| `end_col` | INPUT | No | DataType.STRING |
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
| `row_num` | INTEGER | `1` | Yes | 1-based row number to read (min: 1) |
| `start_col` | STRING | `A` | No | Starting column letter |
| `end_col` | STRING | `Z` | No | Ending column letter |

## Inheritance

Extends: `SheetsBaseNode`
