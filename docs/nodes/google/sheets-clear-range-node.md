# SheetsClearRangeNode

Clear values from a range in Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_write`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py:963`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `range` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `cleared_range` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `range` | STRING | `Sheet1!A1:Z1000` | Yes | Range in A1 notation to clear (e.g., 'Sheet1!A1:Z1000') |

## Inheritance

Extends: `SheetsBaseNode`
