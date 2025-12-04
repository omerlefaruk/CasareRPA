# ExcelOpenNode

Node to open an Excel workbook.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:34`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | STRING | No | Excel file path |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `workbook` | ANY | Workbook object |
| `app` | ANY | Excel application |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
