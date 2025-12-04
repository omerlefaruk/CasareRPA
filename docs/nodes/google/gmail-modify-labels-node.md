# GmailModifyLabelsNode

Modify labels on a Gmail message.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:626`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | STRING | No | Message ID |
| `add_labels` | ARRAY | No | Labels to add |
| `remove_labels` | ARRAY | No | Labels to remove |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `labels` | ARRAY | Updated labels |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
