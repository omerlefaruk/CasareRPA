# GmailSendWithAttachmentNode

Send an email with file attachments via Gmail.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_send`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py:277`


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
| `attachments` | INPUT | No | DataType.STRING |
| `attachment_list` | INPUT | No | DataType.ARRAY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_id` | OUTPUT | DataType.STRING |
| `thread_id` | OUTPUT | DataType.STRING |
| `attachment_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `attachments` | STRING | `` | No | File paths to attach (comma-separated) |

## Inheritance

Extends: `GmailBaseNode`
