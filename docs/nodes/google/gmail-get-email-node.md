# GmailGetEmailNode

Get a single email by message ID.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_read`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_read.py:82`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message_id` | INPUT | No | DataType.STRING |
| `format` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_id` | OUTPUT | DataType.STRING |
| `thread_id` | OUTPUT | DataType.STRING |
| `subject` | OUTPUT | DataType.STRING |
| `from_address` | OUTPUT | DataType.STRING |
| `to_addresses` | OUTPUT | DataType.ARRAY |
| `cc_addresses` | OUTPUT | DataType.ARRAY |
| `date` | OUTPUT | DataType.STRING |
| `snippet` | OUTPUT | DataType.STRING |
| `body_plain` | OUTPUT | DataType.STRING |
| `body_html` | OUTPUT | DataType.STRING |
| `label_ids` | OUTPUT | DataType.ARRAY |
| `has_attachments` | OUTPUT | DataType.BOOLEAN |
| `attachment_count` | OUTPUT | DataType.INTEGER |
| `attachments` | OUTPUT | DataType.ARRAY |
| `raw_message` | OUTPUT | DataType.OBJECT |

## Inheritance

Extends: `GmailBaseNode`
