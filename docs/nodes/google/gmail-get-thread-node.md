# GmailGetThreadNode

Get a conversation thread with all messages.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_read`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_read.py:402`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `thread_id` | INPUT | No | DataType.STRING |
| `format` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `thread_id` | OUTPUT | DataType.STRING |
| `snippet` | OUTPUT | DataType.STRING |
| `messages` | OUTPUT | DataType.ARRAY |
| `message_count` | OUTPUT | DataType.INTEGER |
| `first_message` | OUTPUT | DataType.OBJECT |
| `last_message` | OUTPUT | DataType.OBJECT |
| `participants` | OUTPUT | DataType.ARRAY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `thread_id` | STRING | `` | Yes | Gmail thread ID |

## Inheritance

Extends: `GmailBaseNode`
