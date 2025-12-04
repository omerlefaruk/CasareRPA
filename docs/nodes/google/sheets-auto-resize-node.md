# SheetsAutoResizeNode

Auto-resize columns to fit content.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1184`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `sheet_id` | INTEGER | No | Sheet ID |
| `start_index` | INTEGER | No | Start column index |
| `end_index` | INTEGER | No | End column index |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
