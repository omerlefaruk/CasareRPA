# SheetsAddSheetNode

Add a new sheet to a spreadsheet.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:493`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `sheet_name` | STRING | No | New sheet name |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `sheet_id` | INTEGER | New sheet ID |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
