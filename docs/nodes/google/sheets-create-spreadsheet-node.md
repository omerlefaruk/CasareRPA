# SheetsCreateSpreadsheetNode

Create a new Google Spreadsheet.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:382`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `title` | STRING | No | Spreadsheet title |
| `sheet_names` | ARRAY | No | Initial sheet names |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `spreadsheet_id` | STRING | New spreadsheet ID |
| `spreadsheet_url` | STRING | Spreadsheet URL |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
