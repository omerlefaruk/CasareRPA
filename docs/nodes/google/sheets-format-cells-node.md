# SheetsFormatCellsNode

Format cells in a range.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1085`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `sheet_id` | INTEGER | No | Sheet ID |
| `start_row` | INTEGER | No | Start row index |
| `end_row` | INTEGER | No | End row index |
| `start_column` | INTEGER | No | Start column index |
| `end_column` | INTEGER | No | End column index |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
