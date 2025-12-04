# SaveAttachmentNode

Save email attachments to disk.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.imap_nodes`
**File:** `src\casare_rpa\nodes\email\imap_nodes.py:79`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `imap_server` | INPUT | No | DataType.STRING |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `email_uid` | INPUT | No | DataType.STRING |
| `save_path` | INPUT | No | DataType.STRING |
| `folder` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `saved_files` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `imap_server` | STRING | `imap.gmail.com` | No | IMAP server hostname |
| `imap_port` | INTEGER | `993` | No | IMAP server port |
| `username` | STRING | `` | No | Email account username |
| `password` | STRING | `` | No | Email account password |
| `folder` | STRING | `INBOX` | No | Mailbox folder |
| `save_path` | STRING | `.` | No | Directory path to save attachments |

## Inheritance

Extends: `BaseNode`
