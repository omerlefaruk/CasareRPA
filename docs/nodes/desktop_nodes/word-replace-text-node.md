# WordReplaceTextNode

Node to find and replace text in a Word document.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:566`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `document` | ANY | No | Document object |
| `find_text` | STRING | No | Text to find |
| `replace_text` | STRING | No | Replacement text |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `replacements` | INTEGER | Number of replacements |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
