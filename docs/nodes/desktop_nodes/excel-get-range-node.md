# ExcelGetRangeNode

Node to read a range of cells from Excel.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:269`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `workbook` | ANY | No | Workbook object |
| `sheet` | ANY | No | Sheet name or index |
| `range` | STRING | No | Range reference (e.g., A1:C10) |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `data` | ANY | 2D list of values |
| `rows` | INTEGER | Number of rows |
| `columns` | INTEGER | Number of columns |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
