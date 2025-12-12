# Email Nodes

Email nodes provide SMTP and IMAP integration for sending and receiving emails. CasareRPA supports both traditional email protocols and modern credential management through vault integration.

## Overview

| Node | Purpose |
|------|---------|
| SendEmailNode | Send emails via SMTP |
| ReadEmailsNode | Read emails from IMAP server |
| GetEmailContentNode | Extract content from email object |
| FilterEmailsNode | Filter email list by criteria |
| MarkEmailNode | Mark emails as read/unread/flagged |
| DeleteEmailNode | Delete emails from mailbox |
| MoveEmailNode | Move emails between folders |
| SaveAttachmentNode | Save email attachments to disk |

---

## SendEmailNode

Send emails via SMTP with support for attachments, HTML content, and various delivery options.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| credential_name | STRING | "" | Vault credential alias for SMTP credentials |
| smtp_server | STRING | "smtp.gmail.com" | SMTP server hostname |
| smtp_port | INTEGER | 587 | SMTP server port |
| username | STRING | "" | SMTP username |
| password | STRING | "" | SMTP password |
| from_email | STRING | "" | Sender email address |
| to_email | STRING | "" | Recipient(s), comma-separated |
| subject | STRING | "" | Email subject line |
| body | STRING | "" | Email message body |
| cc | STRING | "" | CC recipients, comma-separated |
| bcc | STRING | "" | BCC recipients, comma-separated |
| use_tls | BOOLEAN | true | Use TLS encryption |
| use_ssl | BOOLEAN | false | Use SSL encryption |
| is_html | BOOLEAN | false | Body contains HTML content |
| timeout | INTEGER | 30 | Connection timeout in seconds |
| reply_to | STRING | "" | Reply-To address |
| priority | CHOICE | "normal" | Email priority (high/normal/low) |
| read_receipt | BOOLEAN | false | Request read receipt |
| sender_name | STRING | "" | Display name for sender |
| retry_count | INTEGER | 0 | Retry attempts on failure |
| retry_interval | INTEGER | 2000 | Delay between retries (ms) |

### Ports

**Inputs:**
- `smtp_server` (STRING)
- `smtp_port` (INTEGER)
- `username` (STRING)
- `password` (STRING)
- `from_email` (STRING)
- `to_email` (STRING)
- `subject` (STRING)
- `body` (STRING)
- `cc` (STRING)
- `bcc` (STRING)
- `attachments` (LIST) - Optional file paths

**Outputs:**
- `success` (BOOLEAN)
- `message_id` (STRING)

### Credential Resolution

Credentials are resolved in this order:
1. Vault lookup via `credential_name`
2. Direct parameters (`username`, `password`)
3. Environment variables (`SMTP_USERNAME`, `SMTP_PASSWORD`)

### Example: Send Plain Text Email

```python
from casare_rpa.nodes.email import SendEmailNode

node = SendEmailNode(
    node_id="send_email_1",
    config={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "{{env.SMTP_USERNAME}}",
        "password": "{{env.SMTP_PASSWORD}}",
        "from_email": "sender@example.com",
        "to_email": "recipient@example.com",
        "subject": "Automation Report",
        "body": "Your daily report is attached.",
        "use_tls": True,
    }
)
```

### Example: Send HTML Email with Attachments

```python
node = SendEmailNode(
    node_id="send_html_email",
    config={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "credential_name": "smtp_creds",  # Use vault credentials
        "from_email": "reports@company.com",
        "to_email": "team@company.com, manager@company.com",
        "cc": "archive@company.com",
        "subject": "Weekly Report - {{variables.week_number}}",
        "body": "<h1>Weekly Report</h1><p>See attached PDF.</p>",
        "is_html": True,
        "sender_name": "CasareRPA Reports",
        "priority": "high",
        "attachments": ["C:\\reports\\weekly_report.pdf"],
    }
)
```

### SMTP Configuration Examples

**Gmail:**
```python
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True
}
```

**Outlook/Office 365:**
```python
{
    "smtp_server": "smtp.office365.com",
    "smtp_port": 587,
    "use_tls": True
}
```

**Amazon SES:**
```python
{
    "smtp_server": "email-smtp.us-east-1.amazonaws.com",
    "smtp_port": 587,
    "use_tls": True
}
```

---

## ReadEmailsNode

Read emails from an IMAP server with filtering and search capabilities.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| credential_name | STRING | "" | Vault credential alias |
| imap_server | STRING | "imap.gmail.com" | IMAP server hostname |
| imap_port | INTEGER | 993 | IMAP server port |
| username | STRING | "" | Email account username |
| password | STRING | "" | Email account password |
| folder | STRING | "INBOX" | Mailbox folder to read |
| limit | INTEGER | 10 | Maximum emails to retrieve |
| search_criteria | STRING | "ALL" | IMAP search criteria |
| use_ssl | BOOLEAN | true | Use SSL encryption |
| timeout | INTEGER | 30 | Connection timeout |
| mark_as_read | BOOLEAN | false | Mark emails as read |
| include_body | BOOLEAN | true | Include email body |
| newest_first | BOOLEAN | true | Return newest first |
| retry_count | INTEGER | 0 | Retry attempts |
| retry_interval | INTEGER | 2000 | Retry delay (ms) |

### Ports

**Inputs:**
- `imap_server` (STRING)
- `imap_port` (INTEGER)
- `username` (STRING)
- `password` (STRING)
- `folder` (STRING)
- `limit` (INTEGER)
- `search_criteria` (STRING)

**Outputs:**
- `emails` (LIST) - List of email dictionaries
- `count` (INTEGER) - Number of emails retrieved

### Email Object Structure

Each email in the output list contains:

```python
{
    "uid": "12345",
    "subject": "Re: Meeting Tomorrow",
    "from": "sender@example.com",
    "to": "recipient@example.com",
    "date": "2025-01-15 10:30:00",
    "body_text": "Plain text content...",
    "body_html": "<html>...</html>",
    "has_attachments": True,
    "attachments": [
        {"filename": "document.pdf", "size": 1024}
    ]
}
```

### IMAP Search Criteria

| Criteria | Description |
|----------|-------------|
| ALL | All messages |
| UNSEEN | Unread messages |
| SEEN | Read messages |
| FLAGGED | Flagged messages |
| FROM "email" | Messages from sender |
| SUBJECT "text" | Messages with subject |
| SINCE "date" | Messages since date |
| BEFORE "date" | Messages before date |

### Example: Read Unread Emails

```python
from casare_rpa.nodes.email import ReadEmailsNode

node = ReadEmailsNode(
    node_id="read_inbox",
    config={
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "credential_name": "email_creds",
        "folder": "INBOX",
        "search_criteria": "UNSEEN",
        "limit": 20,
        "newest_first": True,
    }
)
```

### Example: Search Specific Emails

```python
node = ReadEmailsNode(
    node_id="search_invoices",
    config={
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "{{env.EMAIL_USER}}",
        "password": "{{env.EMAIL_PASS}}",
        "folder": "INBOX",
        "search_criteria": 'FROM "invoices@vendor.com" SINCE "01-Jan-2025"',
        "limit": 100,
    }
)
```

---

## MarkEmailNode

Mark emails as read, unread, or flagged.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| imap_server | STRING | "imap.gmail.com" | IMAP server |
| imap_port | INTEGER | 993 | IMAP port |
| username | STRING | "" | Username |
| password | STRING | "" | Password |
| folder | STRING | "INBOX" | Mailbox folder |
| mark_as | CHOICE | "read" | Flag type |

### Mark Options

- `read` - Mark as read (sets \Seen flag)
- `unread` - Mark as unread (removes \Seen flag)
- `flagged` - Add star/flag (\Flagged)
- `unflagged` - Remove star/flag

### Ports

**Inputs:**
- `imap_server`, `username`, `password` (STRING)
- `email_uid` (STRING) - Email UID to mark
- `folder` (STRING)
- `mark_as` (STRING)

**Outputs:**
- `success` (BOOLEAN)

### Example

```python
from casare_rpa.nodes.email import MarkEmailNode

node = MarkEmailNode(
    node_id="mark_read",
    config={
        "imap_server": "imap.gmail.com",
        "username": "{{env.EMAIL_USER}}",
        "password": "{{env.EMAIL_PASS}}",
        "folder": "INBOX",
        "mark_as": "read",
    }
)
# Pass email_uid from ReadEmailsNode output
```

---

## DeleteEmailNode

Delete emails from mailbox.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| imap_server | STRING | "imap.gmail.com" | IMAP server |
| imap_port | INTEGER | 993 | IMAP port |
| username | STRING | "" | Username |
| password | STRING | "" | Password |
| folder | STRING | "INBOX" | Source folder |
| permanent | BOOLEAN | false | Permanently delete (expunge) |

### Ports

**Inputs:**
- `email_uid` (STRING) - Email UID to delete
- Connection parameters

**Outputs:**
- `success` (BOOLEAN)

> **Warning:** Setting `permanent: true` will permanently delete the email. Without this flag, emails are marked as deleted but can be recovered.

---

## MoveEmailNode

Move emails between folders.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| imap_server | STRING | "imap.gmail.com" | IMAP server |
| imap_port | INTEGER | 993 | IMAP port |
| username | STRING | "" | Username |
| password | STRING | "" | Password |
| source_folder | STRING | "INBOX" | Source folder |
| target_folder | STRING | "" | Destination folder |

### Ports

**Inputs:**
- `email_uid` (STRING)
- `source_folder` (STRING)
- `target_folder` (STRING)

**Outputs:**
- `success` (BOOLEAN)

### Example: Move to Archive

```python
from casare_rpa.nodes.email import MoveEmailNode

node = MoveEmailNode(
    node_id="archive_email",
    config={
        "imap_server": "imap.gmail.com",
        "username": "{{env.EMAIL_USER}}",
        "password": "{{env.EMAIL_PASS}}",
        "source_folder": "INBOX",
        "target_folder": "[Gmail]/All Mail",
    }
)
```

---

## SaveAttachmentNode

Save email attachments to disk.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| imap_server | STRING | "imap.gmail.com" | IMAP server |
| imap_port | INTEGER | 993 | IMAP port |
| username | STRING | "" | Username |
| password | STRING | "" | Password |
| folder | STRING | "INBOX" | Email folder |
| save_path | STRING | "." | Directory to save attachments |

### Ports

**Inputs:**
- `email_uid` (STRING) - Email with attachments
- `save_path` (STRING) - Destination directory
- Connection parameters

**Outputs:**
- `saved_files` (LIST) - List of saved file paths
- `count` (INTEGER) - Number of files saved

### Example

```python
from casare_rpa.nodes.email import SaveAttachmentNode

node = SaveAttachmentNode(
    node_id="save_attachments",
    config={
        "imap_server": "imap.gmail.com",
        "username": "{{env.EMAIL_USER}}",
        "password": "{{env.EMAIL_PASS}}",
        "folder": "INBOX",
        "save_path": "C:\\downloads\\attachments",
    }
)
```

> **Note:** Filenames are sanitized to prevent path traversal attacks. Duplicate filenames get a numeric suffix.

---

## FilterEmailsNode

Filter a list of emails based on criteria.

### Ports

**Inputs:**
- `emails` (LIST) - Email list from ReadEmailsNode
- `subject_contains` (STRING) - Subject filter text
- `from_contains` (STRING) - Sender filter text
- `has_attachments` (BOOLEAN) - Filter by attachment presence

**Outputs:**
- `filtered` (LIST) - Filtered email list
- `count` (INTEGER) - Number of matches

### Example: Filter by Subject

```python
# Combine with ReadEmailsNode
# Read all emails, then filter for invoices

filter_node = FilterEmailsNode(
    node_id="filter_invoices",
    config={}
)
# Connect emails output from ReadEmailsNode to emails input
# Set subject_contains to "Invoice"
```

---

## GetEmailContentNode

Extract specific fields from an email object.

### Ports

**Inputs:**
- `email` (DICT) - Single email from list

**Outputs:**
- `subject` (STRING)
- `from` (STRING)
- `to` (STRING)
- `date` (STRING)
- `body_text` (STRING)
- `body_html` (STRING)
- `attachments` (LIST)

---

## Complete Workflow Example

```python
# Email Processing Workflow
#
# 1. Read unread emails from invoices
# 2. Filter for PDF attachments
# 3. Save attachments
# 4. Mark as read
# 5. Send confirmation

workflow = {
    "nodes": [
        {
            "id": "read_emails",
            "type": "ReadEmailsNode",
            "config": {
                "imap_server": "imap.gmail.com",
                "credential_name": "email_creds",
                "folder": "INBOX",
                "search_criteria": 'FROM "vendor@example.com" UNSEEN',
                "limit": 50
            }
        },
        {
            "id": "filter_with_attachments",
            "type": "FilterEmailsNode",
            "config": {
                "has_attachments": True
            }
        },
        {
            "id": "loop_emails",
            "type": "ForEachNode",
            "config": {}
        },
        {
            "id": "save_attachments",
            "type": "SaveAttachmentNode",
            "config": {
                "save_path": "C:\\invoices\\{{variables.today}}"
            }
        },
        {
            "id": "mark_read",
            "type": "MarkEmailNode",
            "config": {
                "mark_as": "read"
            }
        }
    ]
}
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid credentials | Verify username/password, check app passwords |
| Connection refused | Wrong server/port | Check SMTP/IMAP settings |
| SSL certificate error | Certificate issues | Try `use_ssl: false` with `use_tls: true` |
| Mailbox not found | Invalid folder name | Check folder name (case-sensitive) |

### Gmail-Specific Notes

1. **App Passwords**: Gmail requires app-specific passwords when 2FA is enabled
2. **Less Secure Apps**: Not recommended; use app passwords instead
3. **Folder Names**: Gmail uses `[Gmail]/Sent Mail`, `[Gmail]/All Mail`, etc.

---

## See Also

- [Gmail Nodes](google.md#gmail-nodes) - Gmail API integration
- [Control Flow Nodes](control-flow.md) - Loop through emails
- [File Nodes](file.md) - Process saved attachments
