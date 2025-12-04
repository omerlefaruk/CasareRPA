# SheetsGetSpreadsheetNode

Get spreadsheet metadata.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:432`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `title` | STRING | Spreadsheet title |
| `sheets` | ARRAY | List of sheets |
| `locale` | STRING | Locale |
| `time_zone` | STRING | Time zone |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
