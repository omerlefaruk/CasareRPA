# DocsDeleteContentNode

Delete content from a Google Document.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.docs_nodes`
**File:** `src\casare_rpa\nodes\google\docs_nodes.py:248`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | STRING | No | Document ID |
| `start_index` | INTEGER | No | Start index |
| `end_index` | INTEGER | No | End index |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
