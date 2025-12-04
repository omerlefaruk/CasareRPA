# WordOpenNode

Node to open a Word document.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:426`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | STRING | No | Word file path |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `document` | ANY | Document object |
| `app` | ANY | Word application |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
