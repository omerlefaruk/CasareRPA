# EmailTriggerNode

Email trigger node that fires when new emails arrive.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.email_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\email_trigger_node.py:126`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `email` | DICT | Email Object |
| `subject` | STRING | Subject |
| `sender` | STRING | Sender |
| `body` | STRING | Body (Text) |
| `html_body` | STRING | Body (HTML) |
| `attachments` | LIST | Attachments |
| `received_at` | STRING | Received At |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `provider` | CHOICE | `imap` | No | Email service provider Choices: imap, gmail, outlook |
| `server` | STRING | `` | No | IMAP server address |
| `port` | INTEGER | `993` | No | IMAP port (993 for SSL) |
| `username` | STRING | `` | No | Username/Email |
| `password` | STRING | `` | No | Password or app-specific password |
| `use_ssl` | BOOLEAN | `True` | No | Use SSL |
| `folder` | STRING | `INBOX` | No | Email folder to monitor |
| `filter_subject` | STRING | `` | No | Regex pattern for subject |
| `filter_from` | STRING | `` | No | Regex pattern for sender |
| `unread_only` | BOOLEAN | `True` | No | Only trigger on unread emails |
| `mark_as_read` | BOOLEAN | `True` | No | Mark email as read after triggering |
| `poll_interval_seconds` | INTEGER | `60` | No | How often to check for new emails |
| `download_attachments` | BOOLEAN | `False` | No | Download email attachments |
| `attachment_dir` | DIRECTORY_PATH | `` | No | Attachment Directory |

## Inheritance

Extends: `BaseTriggerNode`
