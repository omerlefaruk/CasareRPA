# ReadEmailsNode

Read emails from an IMAP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.receive_nodes`
**File:** `src\casare_rpa\nodes\email\receive_nodes.py:115`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `imap_server` | INPUT | No | DataType.STRING |
| `imap_port` | INPUT | No | DataType.INTEGER |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `folder` | INPUT | No | DataType.STRING |
| `limit` | INPUT | No | DataType.INTEGER |
| `search_criteria` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `emails` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `folder` | STRING | `INBOX` | No | Mailbox folder to read from |
| `limit` | INTEGER | `10` | No | Maximum number of emails to retrieve (min: 0) |
| `search_criteria` | STRING | `ALL` | No | IMAP search criteria (e.g., ALL, UNSEEN, FROM 'sender@example.com') |
| `use_ssl` | BOOLEAN | `True` | No | Use SSL encryption |
| `timeout` | INTEGER | `30` | No | IMAP connection timeout |
| `mark_as_read` | BOOLEAN | `False` | No | Mark emails as read after fetching |
| `include_body` | BOOLEAN | `True` | No | Include email body content |
| `newest_first` | BOOLEAN | `True` | No | Return newest emails first |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retry attempts in milliseconds (min: 0) |

## Inheritance

Extends: `CredentialAwareMixin`, `BaseNode`
