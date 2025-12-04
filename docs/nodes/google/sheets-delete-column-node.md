# SheetsDeleteColumnNode

Delete columns from a sheet.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1008`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `sheet_id` | INTEGER | No | Sheet ID |
| `start_column` | INTEGER | No | Start column index (0-based) |
| `num_columns` | INTEGER | No | Number of columns to delete |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
