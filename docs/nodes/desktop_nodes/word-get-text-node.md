# WordGetTextNode

Node to get text content from a Word document.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:509`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `document` | ANY | No | Document object |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `text` | STRING | Document text |
| `word_count` | INTEGER | Word count |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
