# GmailBatchDeleteNode

Delete multiple Gmail messages in batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:1079`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_ids` | ARRAY | No | Array of message IDs |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `deleted_count` | INTEGER | Number deleted |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
