# GmailSendEmailNode

Send a plain text or HTML email via Gmail.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_send`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py:131`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `to` | INPUT | No | DataType.STRING |
| `cc` | INPUT | No | DataType.STRING |
| `bcc` | INPUT | No | DataType.STRING |
| `subject` | INPUT | No | DataType.STRING |
| `body` | INPUT | No | DataType.STRING |
| `body_type` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_id` | OUTPUT | DataType.STRING |
| `thread_id` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `GmailBaseNode`
