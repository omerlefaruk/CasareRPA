# SheetsGetSheetInfoNode

Get spreadsheet metadata and sheet information.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:791`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `title` | OUTPUT | DataType.STRING |
| `sheets` | OUTPUT | DataType.ARRAY |
| `sheet_count` | OUTPUT | DataType.INTEGER |
| `locale` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `SheetsBaseNode`
