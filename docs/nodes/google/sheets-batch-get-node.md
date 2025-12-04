# SheetsBatchGetNode

Get values from multiple ranges in a single batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.sheets_nodes`
**File:** `src\casare_rpa\nodes\google\sheets_nodes.py:1331`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `spreadsheet_id` | STRING | No | Spreadsheet ID |
| `ranges` | ARRAY | No | Array of range strings |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `value_ranges` | ARRAY | Array of value ranges |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
