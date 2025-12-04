# SheetsBatchClearNode

Clear multiple ranges in a single batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1391`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `ranges` | ARRAY | No | Array of range strings |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `cleared_ranges` | ARRAY | Cleared ranges |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
