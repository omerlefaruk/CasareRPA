# SendEmailNode

Send an email via SMTP.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.send_nodes`
**File:** `src\casare_rpa\nodes\email\send_nodes.py:161`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `smtp_server` | INPUT | No | DataType.STRING |
| `smtp_port` | INPUT | No | DataType.INTEGER |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `from_email` | INPUT | No | DataType.STRING |
| `to_email` | INPUT | No | DataType.STRING |
| `subject` | INPUT | No | DataType.STRING |
| `body` | INPUT | No | DataType.STRING |
| `cc` | INPUT | No | DataType.STRING |
| `bcc` | INPUT | No | DataType.STRING |
| `attachments` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `message_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `from_email` | STRING | `` | No | Sender email address |
| `to_email` | STRING | `` | No | Recipient email address(es), comma-separated |
| `subject` | STRING | `` | No | Email subject line |
| `body` | STRING | `` | No | Email message body |
| `cc` | STRING | `` | No | CC recipients, comma-separated |
| `bcc` | STRING | `` | No | BCC recipients, comma-separated |
| `use_tls` | BOOLEAN | `True` | No | Use TLS encryption |
| `use_ssl` | BOOLEAN | `False` | No | Use SSL encryption |
| `is_html` | BOOLEAN | `False` | No | Body contains HTML content |
| `timeout` | INTEGER | `30` | No | SMTP connection timeout |
| `reply_to` | STRING | `` | No | Reply-To email address |
| `priority` | CHOICE | `normal` | No | Email priority level Choices: high, normal, low |
| `read_receipt` | BOOLEAN | `False` | No | Request read receipt notification |
| `sender_name` | STRING | `` | No | Display name for sender |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retry attempts in milliseconds (min: 0) |

## Inheritance

Extends: `CredentialAwareMixin`, `BaseNode`
