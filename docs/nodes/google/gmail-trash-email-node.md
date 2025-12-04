# GmailTrashEmailNode

Move a Gmail message to trash (alias for MoveToTrash with clearer name).

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:1307`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | STRING | No | Message ID to trash |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
