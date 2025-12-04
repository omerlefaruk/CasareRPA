# ExcelReadCellNode

Node to read a cell value from Excel.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:117`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `workbook` | ANY | No | Workbook object |
| `sheet` | ANY | No | Sheet name or index |
| `cell` | STRING | No | Cell reference (e.g., A1) |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | ANY | Cell value |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
