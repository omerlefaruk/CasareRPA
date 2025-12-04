# GmailForwardEmailNode

Forward an existing email to new recipients.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_send`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py:643`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message_id` | INPUT | No | DataType.STRING |
| `to` | INPUT | No | DataType.STRING |
| `cc` | INPUT | No | DataType.STRING |
| `bcc` | INPUT | No | DataType.STRING |
| `additional_body` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_id` | OUTPUT | DataType.STRING |
| `thread_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `message_id` | STRING | `` | Yes | Message ID to forward |
| `additional_body` | TEXT | `` | No | Optional text to add before the forwarded message |

## Inheritance

Extends: `GmailBaseNode`
