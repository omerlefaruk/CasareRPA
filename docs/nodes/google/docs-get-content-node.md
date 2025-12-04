# DocsGetContentNode

Get the text content of a Google Document.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.docs_nodes`
**File:** `src\casare_rpa\nodes\google\docs_nodes.py:128`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | STRING | No | Document ID |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `text` | STRING | Plain text content |
| `word_count` | INTEGER | Word count |
| `character_count` | INTEGER | Character count |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
