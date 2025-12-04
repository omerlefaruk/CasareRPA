# GmailSendDraftNode

Send an existing draft from Gmail.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:297`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `draft_id` | STRING | No | Draft ID to send |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `message_id` | STRING | Sent message ID |
| `thread_id` | STRING | Thread ID |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
