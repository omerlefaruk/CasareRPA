# GmailCreateDraftNode

Create a draft email (save without sending).

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_send`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py:786`


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

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `draft_id` | OUTPUT | DataType.STRING |
| `message_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `attachments` | STRING | `` | No | File paths to attach (comma-separated) |

## Inheritance

Extends: `GmailBaseNode`
