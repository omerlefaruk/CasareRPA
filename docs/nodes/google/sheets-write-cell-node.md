# SheetsWriteCellNode

Write a single cell value to Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:116`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `cell` | INPUT | No | DataType.STRING |
| `value` | INPUT | No | DataType.ANY |
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
| `cell` | STRING | `A1` | Yes | Cell reference in A1 notation |
| `value` | ANY | `` | Yes | Value to write to the cell |

## Inheritance

Extends: `SheetsBaseNode`
