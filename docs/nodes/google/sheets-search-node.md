# SheetsSearchNode

Search for values in Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:627`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `search_value` | INPUT | No | DataType.STRING |
| `sheet_name` | INPUT | No | DataType.STRING |
| `search_range` | INPUT | No | DataType.STRING |
| `match_case` | INPUT | No | DataType.BOOLEAN |
| `match_entire_cell` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `results` | OUTPUT | DataType.ARRAY |
| `match_count` | OUTPUT | DataType.INTEGER |
| `first_match` | OUTPUT | DataType.OBJECT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `search_value` | STRING | `` | Yes | Value to search for in the spreadsheet |
| `search_range` | STRING | `` | No | Optional range to limit search (empty = entire sheet) |
| `match_case` | BOOLEAN | `False` | No | Case-sensitive search |
| `match_entire_cell` | BOOLEAN | `False` | No | Only match if entire cell content equals search value |

## Inheritance

Extends: `SheetsBaseNode`
