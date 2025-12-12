# Email Triggers

CasareRPA provides two email trigger nodes for different use cases:

- **EmailTriggerNode** - Generic IMAP-based polling for any email provider
- **GmailTriggerNode** - Native Gmail API integration with push support

## EmailTriggerNode (IMAP)

The generic email trigger uses IMAP polling to check for new emails from any provider.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `EmailTriggerNode` |
| Trigger Type | `EMAIL` |
| Icon | email |
| Category | triggers |

### Configuration Properties

#### Provider Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| provider | choice | `imap` | Email provider: `imap`, `gmail`, `outlook` |
| server | string | `""` | IMAP server address |
| port | integer | `993` | IMAP port (993 for SSL) |
| username | string | `""` | Username/email address |
| password | string | `""` | Password or app-specific password |
| use_ssl | boolean | `true` | Use SSL connection |

#### Folder and Filters

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| folder | string | `INBOX` | Email folder to monitor |
| filter_subject | string | `""` | Regex pattern for subject |
| filter_from | string | `""` | Regex pattern for sender |
| unread_only | boolean | `true` | Only trigger on unread emails |
| mark_as_read | boolean | `true` | Mark email as read after triggering |

#### Polling and Attachments

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| poll_interval_seconds | integer | `60` | How often to check for new emails |
| download_attachments | boolean | `false` | Download email attachments |
| attachment_dir | directory | `""` | Directory for downloaded attachments |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| email | dict | Full email object |
| subject | string | Email subject |
| sender | string | Sender email address |
| body | string | Email body (plain text) |
| html_body | string | Email body (HTML) |
| attachments | list | List of attachment file paths |
| received_at | string | When the email was received |
| exec_out | exec | Execution flow continues |

### IMAP Server Settings

| Provider | Server | Port |
|----------|--------|------|
| Gmail | `imap.gmail.com` | 993 |
| Outlook/Hotmail | `outlook.office365.com` | 993 |
| Yahoo | `imap.mail.yahoo.com` | 993 |
| Custom | Your IMAP server | Usually 993 |

### Example: Gmail via IMAP

```json
{
  "provider": "gmail",
  "server": "imap.gmail.com",
  "port": 993,
  "username": "myemail@gmail.com",
  "password": "app-specific-password",
  "use_ssl": true,
  "folder": "INBOX",
  "filter_subject": ".*Invoice.*",
  "filter_from": ".*@vendor.com",
  "unread_only": true,
  "mark_as_read": true,
  "poll_interval_seconds": 60
}
```

> **Note:** For Gmail, you must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### Example: Outlook/Office 365

```json
{
  "provider": "outlook",
  "server": "outlook.office365.com",
  "port": 993,
  "username": "user@company.com",
  "password": "your-password",
  "use_ssl": true,
  "folder": "INBOX",
  "filter_subject": ".*Order Confirmation.*",
  "unread_only": true,
  "poll_interval_seconds": 120
}
```

### Filter Examples

#### Subject Contains "Invoice"

```json
{
  "filter_subject": ".*Invoice.*"
}
```

#### From Specific Domain

```json
{
  "filter_from": ".*@vendor\\.com"
}
```

#### Subject Starts With

```json
{
  "filter_subject": "^\\[URGENT\\].*"
}
```

#### Combined Filters

Both filters must match (AND logic):

```json
{
  "filter_subject": ".*Order.*",
  "filter_from": ".*@shop\\.com"
}
```

---

## GmailTriggerNode {#gmail-trigger}

The Gmail trigger uses the native Gmail API for better performance and push notification support.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `GmailTriggerNode` |
| Trigger Type | `GMAIL` |
| Icon | gmail |
| Category | triggers |

### Configuration Properties

#### Connection Settings

| Property | Type | Default | Tab | Description |
|----------|------|---------|-----|-------------|
| credential_name | string | `google` | connection | Name of stored Google OAuth credential |

#### Polling Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| polling_interval | integer | `60` | Seconds between checks |

#### Filters

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| label_ids | string | `INBOX` | Comma-separated Gmail label IDs |
| query | string | `is:unread` | Gmail search query |
| from_filter | string | `""` | Only trigger for emails from this address |
| subject_contains | string | `""` | Only trigger if subject contains this text |

#### Advanced Settings

| Property | Type | Default | Tab | Description |
|----------|------|---------|-----|-------------|
| mark_as_read | boolean | `true` | advanced | Mark email as read after triggering |
| include_attachments | boolean | `true` | advanced | Include attachment metadata |
| max_results | integer | `10` | advanced | Maximum emails to process per poll |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| message_id | string | Gmail message ID |
| thread_id | string | Gmail thread ID |
| subject | string | Email subject |
| from_email | string | Sender email address |
| from_name | string | Sender display name |
| to_email | string | Recipient email address |
| date | string | Email date/time |
| snippet | string | Email preview snippet |
| body_text | string | Plain text body |
| body_html | string | HTML body |
| labels | list | List of Gmail labels |
| has_attachments | boolean | Whether email has attachments |
| attachments | list | List of attachment metadata |
| raw_message | dict | Full message object |
| exec_out | exec | Execution flow continues |

### Gmail Search Query Syntax

Gmail triggers support the full Gmail search syntax:

| Query | Description |
|-------|-------------|
| `is:unread` | Unread messages |
| `is:starred` | Starred messages |
| `from:user@example.com` | From specific sender |
| `to:me` | Addressed to you |
| `subject:invoice` | Subject contains "invoice" |
| `has:attachment` | Has attachments |
| `filename:pdf` | Has PDF attachment |
| `label:important` | Has "important" label |
| `after:2024/01/01` | After date |
| `before:2024/12/31` | Before date |
| `newer_than:7d` | Newer than 7 days |
| `older_than:1m` | Older than 1 month |

Combine with spaces (AND) or OR:

```
is:unread from:vendor@example.com has:attachment
is:unread (from:alice OR from:bob)
```

### Example Configurations

#### Unread Emails from Specific Sender

```json
{
  "credential_name": "google",
  "polling_interval": 60,
  "label_ids": "INBOX",
  "query": "is:unread",
  "from_filter": "notifications@github.com",
  "mark_as_read": true
}
```

#### Invoices with PDF Attachments

```json
{
  "credential_name": "google",
  "polling_interval": 120,
  "query": "is:unread has:attachment filename:pdf",
  "subject_contains": "Invoice",
  "include_attachments": true,
  "max_results": 5
}
```

#### Starred Important Emails

```json
{
  "credential_name": "google",
  "polling_interval": 30,
  "label_ids": "INBOX,STARRED",
  "query": "is:starred is:unread",
  "mark_as_read": false
}
```

### OAuth Setup Requirements

The Gmail trigger requires Google OAuth credentials:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing

2. **Enable Gmail API**
   - Navigate to APIs & Services > Library
   - Search for "Gmail API" and enable it

3. **Create OAuth Credentials**
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download credentials JSON

4. **Configure in CasareRPA**
   - Store credentials with name (e.g., `google`)
   - Grant required scopes: `gmail.readonly`, `gmail.modify`

---

## Comparison: IMAP vs Gmail API

| Feature | EmailTriggerNode (IMAP) | GmailTriggerNode |
|---------|------------------------|------------------|
| Works with | Any IMAP provider | Gmail only |
| Setup | Server/password | OAuth credentials |
| Performance | Polling only | API-native |
| Filtering | Regex patterns | Gmail search syntax |
| Attachments | Download to disk | Metadata by default |
| Rate limits | Provider-dependent | Gmail API quotas |
| Best for | Multi-provider support | Gmail-specific features |

---

## Complete Workflow Example

```python
from casare_rpa.nodes.trigger_nodes import GmailTriggerNode
from casare_rpa.nodes.file import WriteFileNode
from casare_rpa.nodes import SendEmailNode

# Gmail trigger for invoice processing
trigger = GmailTriggerNode(
    node_id="invoice_email_trigger",
    config={
        "credential_name": "google",
        "polling_interval": 60,
        "query": "is:unread has:attachment filename:pdf",
        "subject_contains": "Invoice",
        "from_filter": "billing@vendor.com",
        "mark_as_read": True,
        "include_attachments": True,
    }
)

# Workflow:
# [Gmail Trigger] -> [Download Attachment] -> [Process PDF] -> [Archive Email]
#       |
#       +-- subject      -> "Invoice #12345"
#       +-- from_email   -> "billing@vendor.com"
#       +-- attachments  -> [{name: "invoice.pdf", id: "..."}]
```

## Workflow JSON Example

```json
{
  "nodes": [
    {
      "id": "gmail_trigger_1",
      "type": "GmailTriggerNode",
      "config": {
        "credential_name": "google",
        "polling_interval": 60,
        "query": "is:unread from:orders@shop.com",
        "mark_as_read": true
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "log_1",
      "type": "LogNode",
      "config": {
        "message": "New order email: {{subject}} from {{from_email}}"
      },
      "position": {"x": 400, "y": 200}
    }
  ],
  "connections": [
    {
      "source_node": "gmail_trigger_1",
      "source_port": "exec_out",
      "target_node": "log_1",
      "target_port": "exec_in"
    }
  ]
}
```

## Common Use Cases

### Invoice Processing
1. Trigger on emails with PDF attachments
2. Download and parse invoice
3. Create accounting entry
4. Archive email with label

### Order Notifications
1. Trigger on order confirmation emails
2. Extract order details from body
3. Update inventory system
4. Send internal notification

### Support Ticket Creation
1. Trigger on emails to support address
2. Parse email content
3. Create ticket in helpdesk
4. Send acknowledgment reply

### Lead Capture
1. Trigger on emails from web forms
2. Extract contact information
3. Add to CRM
4. Assign to sales rep

## Best Practices

1. **Use App Passwords**: For IMAP with Gmail, always use app-specific passwords
2. **Set Appropriate Polling**: Balance responsiveness with API quota usage
3. **Filter Server-Side**: Use Gmail queries or IMAP folders to reduce polling load
4. **Handle Duplicates**: Design workflows to handle emails being processed twice
5. **Mark as Read**: Prevent re-processing by marking emails as read
6. **Monitor Quotas**: Gmail API has daily limits; design accordingly
7. **Secure Credentials**: Store email passwords in credential manager

## Related

- [Messaging Triggers](messaging-triggers.md) - Telegram and WhatsApp triggers
- [Google Triggers](google-triggers.md) - Drive, Sheets, Calendar triggers
- [Webhook Trigger](webhook.md) - HTTP-based triggering
- [Trigger Overview](index.md) - All available triggers
