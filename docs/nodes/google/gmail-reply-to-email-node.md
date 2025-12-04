# GmailReplyToEmailNode

Reply to an existing email thread.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_send`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py:482`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `thread_id` | INPUT | No | DataType.STRING |
| `message_id` | INPUT | No | DataType.STRING |
| `body` | INPUT | No | DataType.STRING |
| `body_type` | INPUT | No | DataType.STRING |
| `cc` | INPUT | No | DataType.STRING |
| `bcc` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_id` | OUTPUT | DataType.STRING |
| `thread_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `thread_id` | STRING | `` | Yes | Thread ID of the conversation to reply to |
| `message_id` | STRING | `` | Yes | Message ID to reply to |
| `body` | TEXT | `` | Yes | Reply body content |

## Inheritance

Extends: `GmailBaseNode`
