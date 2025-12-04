# SheetsBatchUpdateNode

Execute multiple updates in a single batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1254`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `data` | ARRAY | No | Array of {range, values} objects |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `total_updated_rows` | INTEGER | Total rows updated |
| `total_updated_columns` | INTEGER | Total columns updated |
| `total_updated_cells` | INTEGER | Total cells updated |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
