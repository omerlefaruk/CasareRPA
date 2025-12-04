# MoveEmailNode

Move an email to a different folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.imap_nodes`
**File:** `src\casare_rpa\nodes\email\imap_nodes.py:528`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `imap_server` | INPUT | No | DataType.STRING |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `email_uid` | INPUT | No | DataType.STRING |
| `source_folder` | INPUT | No | DataType.STRING |
| `target_folder` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `imap_server` | STRING | `imap.gmail.com` | No | IMAP server hostname |
| `imap_port` | INTEGER | `993` | No | IMAP server port |
| `username` | STRING | `` | No | Email account username |
| `password` | STRING | `` | No | Email account password |
| `source_folder` | STRING | `INBOX` | No | Source mailbox folder |
| `target_folder` | STRING | `` | No | Target mailbox folder |

## Inheritance

Extends: `BaseNode`
