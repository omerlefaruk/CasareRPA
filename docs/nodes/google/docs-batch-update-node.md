# DocsBatchUpdateNode

Execute multiple document updates in a single batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.docs_nodes`
**File:** `src\casare_rpa\nodes\google\docs_nodes.py:607`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | STRING | No | Document ID |
| `requests` | ARRAY | No | Array of request objects |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `replies` | ARRAY | Response replies |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
