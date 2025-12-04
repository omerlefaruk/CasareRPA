# ExcelWriteCellNode

Node to write a value to an Excel cell.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:193`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `workbook` | ANY | No | Workbook object |
| `sheet` | ANY | No | Sheet name or index |
| `cell` | STRING | No | Cell reference (e.g., A1) |
| `value` | ANY | No | Value to write |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
