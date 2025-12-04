# GmailRemoveLabelNode

Remove label(s) from a Gmail message.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:1188`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | STRING | No | Message ID |
| `label_ids` | ARRAY | No | Label IDs to remove |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `labels` | ARRAY | Updated labels |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
