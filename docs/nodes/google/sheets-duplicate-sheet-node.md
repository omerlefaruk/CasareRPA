# SheetsDuplicateSheetNode

Duplicate a sheet within a spreadsheet.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:599`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `sheet_id` | INTEGER | No | Source sheet ID |
| `new_sheet_name` | STRING | No | New sheet name |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `new_sheet_id` | INTEGER | New sheet ID |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
