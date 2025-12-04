# GmailGetAttachmentNode

Download an email attachment.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_read`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_read.py:562`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message_id` | INPUT | No | DataType.STRING |
| `attachment_id` | INPUT | No | DataType.STRING |
| `save_path` | INPUT | No | DataType.STRING |
| `filename` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `attachment_data` | OUTPUT | DataType.STRING |
| `save_path` | OUTPUT | DataType.STRING |
| `filename` | OUTPUT | DataType.STRING |
| `size` | OUTPUT | DataType.INTEGER |
| `saved` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `attachment_id` | STRING | `` | Yes | Attachment ID from message payload |
| `save_path` | FILE_PATH | `` | No | File path to save the attachment (optional) |
| `filename` | STRING | `` | No | Filename for the attachment (used if no save path specified) |

## Inheritance

Extends: `GmailBaseNode`
