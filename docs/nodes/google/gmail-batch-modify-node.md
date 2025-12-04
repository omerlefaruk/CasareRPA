# GmailBatchModifyNode

Modify multiple Gmail messages in batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:1029`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_ids` | ARRAY | No | Array of message IDs |
| `add_labels` | ARRAY | No | Labels to add |
| `remove_labels` | ARRAY | No | Labels to remove |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `modified_count` | INTEGER | Number modified |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
