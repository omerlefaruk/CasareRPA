# SheetsSetCellNode

Set value in a single cell.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:108`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `cell` | STRING | No | Cell address (e.g., A1) |
| `value` | ANY | No | Value to set |
| `sheet_name` | STRING | No | Sheet name |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `updated_range` | STRING | Updated range |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
