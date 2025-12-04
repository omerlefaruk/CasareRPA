# GmailTriggerNode

Gmail trigger node that monitors for new emails.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.gmail_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\gmail_trigger_node.py:98`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `message_id` | STRING | Message ID |
| `thread_id` | STRING | Thread ID |
| `subject` | STRING | Subject |
| `from_email` | STRING | From Email |
| `from_name` | STRING | From Name |
| `to_email` | STRING | To Email |
| `date` | STRING | Date |
| `snippet` | STRING | Snippet |
| `body_text` | STRING | Body (Text) |
| `body_html` | STRING | Body (HTML) |
| `labels` | LIST | Labels |
| `has_attachments` | BOOLEAN | Has Attachments |
| `attachments` | LIST | Attachments |
| `raw_message` | DICT | Raw Message |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mark_as_read` | BOOLEAN | `True` | No | Mark email as read after triggering |
| `include_attachments` | BOOLEAN | `True` | No | Include attachment metadata in payload |
| `max_results` | INTEGER | `10` | No | Maximum emails to process per poll |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `credential_name` | STRING | `google` | No | Name of stored Google OAuth credential |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `polling_interval` | INTEGER | `60` | No | Seconds between checks for new emails |
| `label_ids` | STRING | `INBOX` | No | Comma-separated Gmail label IDs to monitor |
| `query` | STRING | `is:unread` | No | Gmail search query to filter emails |
| `from_filter` | STRING | `` | No | Only trigger for emails from this address |
| `subject_contains` | STRING | `` | No | Only trigger if subject contains this text |

## Inheritance

Extends: `BaseTriggerNode`
