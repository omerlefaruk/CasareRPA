# SheetsGetCellNode

Read a single cell value from Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:107`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `sheet_name` | INPUT | No | DataType.STRING |
| `cell` | INPUT | No | DataType.STRING |
| `value_render_option` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `cell` | STRING | `A1` | Yes | Cell reference in A1 notation |

## Inheritance

Extends: `SheetsBaseNode`
