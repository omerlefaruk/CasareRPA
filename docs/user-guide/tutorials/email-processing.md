# Email Processing Automation Tutorial

Learn to automate email workflows: read messages from an inbox, filter by criteria, download attachments, and archive processed emails.

**Time required:** 20 minutes

**What you will build:**
A workflow that reads unread emails from a vendor, downloads invoice attachments, and moves processed emails to an archive folder.

## Prerequisites

- CasareRPA installed and running
- IMAP-enabled email account (Gmail, Outlook, etc.)
- App password for your email (if using 2FA)

## Goals

By the end of this tutorial, you will:
- Connect to an IMAP email server
- Read and filter emails
- Download attachments to disk
- Mark emails as read
- Move emails between folders
- Handle email processing errors

---

## Step 1: Create a New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `email_processor_tutorial.json`

---

## Step 2: Set Up Variables

First, define variables for email credentials. In production, use the Vault for secure storage.

1. Drag **Set Variable** from **Variable** category
2. Position at (100, 300)

Create these variables:

| Variable Name | Value |
|--------------|-------|
| imap_server | `imap.gmail.com` |
| imap_port | `993` |
| email_user | `your-email@gmail.com` |
| email_pass | `your-app-password` |
| save_path | `C:\downloads\invoices` |

> **Important:** Never hardcode passwords in production workflows. Use the CasareRPA Vault or environment variables.

---

## Step 3: Add Start Node and Connect Variables

```
[Start] --> [Set Variable: imap_server] --> [Set Variable: email_user] --> ...
```

Connect all variable nodes in sequence, then proceed to the email reading step.

---

## Step 4: Read Emails from Inbox

1. Drag **Read Emails** from **Email** category
2. Position after the last Set Variable node

### Configure Read Emails

| Property | Value |
|----------|-------|
| imap_server | `{{imap_server}}` |
| imap_port | `{{imap_port}}` |
| username | `{{email_user}}` |
| password | `{{email_pass}}` |
| folder | `INBOX` |
| search_criteria | `FROM "invoices@vendor.com" UNSEEN` |
| limit | `20` |
| newest_first | `true` |
| include_body | `true` |
| mark_as_read | `false` |

### Search Criteria Examples

| Criteria | Description |
|----------|-------------|
| `ALL` | All messages |
| `UNSEEN` | Unread messages |
| `FROM "email@example.com"` | From specific sender |
| `SUBJECT "Invoice"` | Subject contains text |
| `SINCE "01-Jan-2025"` | Messages after date |
| `BEFORE "31-Dec-2025"` | Messages before date |
| `FROM "vendor.com" UNSEEN` | Combined criteria |

### Output Ports

- `emails` (LIST) - List of email dictionaries
- `count` (INTEGER) - Number of emails retrieved

---

## Step 5: Check if Emails Were Found

1. Drag **If** from **Control Flow** category
2. Position after Read Emails
3. Connect: Read Emails `exec_out` -> If `exec_in`

### Configure If Node

| Property | Value |
|----------|-------|
| expression | `{{count}} > 0` |

Connect the `count` output from Read Emails to use in the condition.

---

## Step 6: Log "No Emails" Case

For the `false` branch (no emails):

1. Drag **Log** from **Basic**
2. Connect: If `false` -> Log

| Property | Value |
|----------|-------|
| message | `No new emails to process` |
| level | `info` |

3. Connect Log to End node

---

## Step 7: Loop Through Emails

For the `true` branch (emails found):

1. Drag **For Loop Start** from **Control Flow**
2. Connect: If `true` -> For Loop Start
3. Connect: Read Emails `emails` -> For Loop Start `items`

### Configure For Loop Start

| Property | Value |
|----------|-------|
| mode | `items` |
| item_var | `email` |

---

## Step 8: Extract Email Content

Inside the loop, extract fields from the current email:

1. Drag **Get Email Content** from **Email**
2. Connect: For Loop Start `body` -> Get Email Content

### Configure Get Email Content

Connect the `current_item` output from For Loop Start to the `email` input.

### Output Ports

- `subject` (STRING)
- `from` (STRING)
- `to` (STRING)
- `date` (STRING)
- `body_text` (STRING)
- `body_html` (STRING)
- `attachments` (LIST)

---

## Step 9: Log Email Being Processed

1. Drag **Log** from **Basic**
2. Connect after Get Email Content

| Property | Value |
|----------|-------|
| message | `Processing email: {{subject}} from {{from}}` |
| level | `info` |

---

## Step 10: Check for Attachments

1. Drag **If** from **Control Flow**
2. Connect after Log

| Property | Value |
|----------|-------|
| expression | `{{email.has_attachments}} == true` |

---

## Step 11: Save Attachments

For the `true` branch (has attachments):

1. Drag **Save Attachment** from **Email**
2. Connect: If `true` -> Save Attachment

### Configure Save Attachment

| Property | Value |
|----------|-------|
| imap_server | `{{imap_server}}` |
| imap_port | `{{imap_port}}` |
| username | `{{email_user}}` |
| password | `{{email_pass}}` |
| folder | `INBOX` |
| save_path | `{{save_path}}\{{email.date}}` |

Connect the `email_uid` port from the loop's current item.

### Output Ports

- `saved_files` (LIST) - Paths to saved files
- `count` (INTEGER) - Number of attachments saved

---

## Step 12: Log Saved Attachments

1. Drag **Log** from **Basic**
2. Connect after Save Attachment

| Property | Value |
|----------|-------|
| message | `Saved {{count}} attachments: {{saved_files}}` |
| level | `info` |

---

## Step 13: Mark Email as Read

1. Drag **Mark Email** from **Email**
2. Position after the attachment If branches merge

### Configure Mark Email

| Property | Value |
|----------|-------|
| imap_server | `{{imap_server}}` |
| imap_port | `{{imap_port}}` |
| username | `{{email_user}}` |
| password | `{{email_pass}}` |
| folder | `INBOX` |
| mark_as | `read` |

Connect `email_uid` from current loop item.

---

## Step 14: Move Email to Archive

1. Drag **Move Email** from **Email**
2. Connect after Mark Email

### Configure Move Email

| Property | Value |
|----------|-------|
| imap_server | `{{imap_server}}` |
| imap_port | `{{imap_port}}` |
| username | `{{email_user}}` |
| password | `{{email_pass}}` |
| source_folder | `INBOX` |
| target_folder | `[Gmail]/All Mail` |

> **Note:** Gmail folder names use the `[Gmail]/` prefix. For other providers, folder names vary.

### Common Folder Names

| Provider | Archive Folder |
|----------|----------------|
| Gmail | `[Gmail]/All Mail` or `Archive` |
| Outlook | `Archive` |
| Yahoo | `Archive` |
| Custom IMAP | Check with provider |

---

## Step 15: Complete the Loop

1. Drag **For Loop End** from **Control Flow**
2. Connect: Move Email -> For Loop End
3. The loop automatically returns to For Loop Start

---

## Step 16: Add Summary Log

After the loop completes:

1. Drag **Log** from **Basic**
2. Connect: For Loop Start `completed` -> Log

| Property | Value |
|----------|-------|
| message | `Email processing complete. Processed {{count}} emails.` |
| level | `info` |

---

## Step 17: Add Merge and End

1. Drag **Merge** from **Control Flow**
2. Connect both the "no emails" Log and the "processing complete" Log to Merge
3. Drag **End** from **Basic**
4. Connect: Merge -> End

---

## Complete Workflow Diagram

```
[Start]
    |
[Set Variables: imap_server, email_user, email_pass, save_path]
    |
[Read Emails]
    search_criteria: 'FROM "invoices@vendor.com" UNSEEN'
    |
[If: count > 0]
    |
+---+---+
|       |
true    false
|       |
|   [Log: "No emails"]
|       |
|       +------------+
|                    |
[For Loop Start]     |
    item_var: email  |
    |                |
  body               |
    |                |
[Get Email Content]  |
    |                |
[Log: "Processing..."]
    |                |
[If: has_attachments]|
    |                |
+---+---+            |
|       |            |
true    false        |
|       |            |
[Save   |            |
 Attachment]         |
|       |            |
+---+---+            |
    |                |
[Mark Email: read]   |
    |                |
[Move Email: Archive]|
    |                |
[For Loop End]       |
    |                |
completed            |
    |                |
[Log: "Complete"]    |
    |                |
+---+----------------+
    |
[Merge]
    |
[End]
```

---

## Step 18: Run the Workflow

1. Click **Run** (or `F5`)
2. Monitor the log panel for progress
3. Check your archive folder and download directory

### Expected Log Output

```
[INFO] Workflow started
[INFO] Connecting to imap.gmail.com:993
[INFO] Found 3 emails matching criteria
[INFO] Processing email: Invoice #12345 from invoices@vendor.com
[INFO] Saved 1 attachments: ['C:\downloads\invoices\2025-01-15\invoice_12345.pdf']
[INFO] Processing email: Invoice #12346 from invoices@vendor.com
[INFO] Saved 1 attachments: ['C:\downloads\invoices\2025-01-15\invoice_12346.pdf']
[INFO] Processing email: Statement January from invoices@vendor.com
[INFO] No attachments in this email
[INFO] Email processing complete. Processed 3 emails.
[INFO] Workflow completed successfully
```

---

## Gmail-Specific Configuration

### Enable IMAP

1. Open Gmail Settings
2. Go to **Forwarding and POP/IMAP**
3. Enable IMAP
4. Save changes

### Create App Password

If you have 2-factor authentication enabled:

1. Go to Google Account > Security
2. Select **App passwords**
3. Generate a new app password for "Mail"
4. Use this password in CasareRPA (not your regular password)

### Gmail Folder Names

| Folder | IMAP Name |
|--------|-----------|
| Inbox | `INBOX` |
| Sent | `[Gmail]/Sent Mail` |
| Drafts | `[Gmail]/Drafts` |
| Spam | `[Gmail]/Spam` |
| Trash | `[Gmail]/Trash` |
| All Mail | `[Gmail]/All Mail` |
| Starred | `[Gmail]/Starred` |

---

## Outlook/Office 365 Configuration

### IMAP Settings

| Property | Value |
|----------|-------|
| imap_server | `outlook.office365.com` |
| imap_port | `993` |
| use_ssl | `true` |

### Common Folder Names

| Folder | IMAP Name |
|--------|-----------|
| Inbox | `INBOX` |
| Sent | `Sent Items` |
| Drafts | `Drafts` |
| Archive | `Archive` |
| Deleted | `Deleted Items` |

---

## Adding Error Handling

Wrap email operations in Try/Catch:

```
[Try]
    |
  try_body
    |
[Read Emails]
    |
[For Loop Start]
    |
[Save Attachment]  --error--> [Catch]
    |                             |
[Mark Email]                 catch_body
    |                             |
[Move Email]                 [Log: "Error processing email: {{error_message}}"]
    |                             |
[For Loop End]                    |
    |                             |
    +--------------+--------------+
                   |
               [Finally]
                   |
              finally_body
                   |
              [Log: "Email processing finished"]
```

---

## Filtering Emails

### Filter by Subject

```
[Filter Emails]
    subject_contains: "Invoice"
```

### Filter by Sender

```
[Filter Emails]
    from_contains: "accounting@"
```

### Filter by Attachment Presence

```
[Filter Emails]
    has_attachments: true
```

### Chained Filters

```
[Read Emails]
    |
    +---> emails
    |
[Filter Emails]
    subject_contains: "Invoice"
    |
    +---> filtered
    |
[Filter Emails]
    has_attachments: true
    |
    +---> (final list)
```

---

## Sending Confirmation Emails

After processing, send a summary email:

```
[Send Email]
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "{{email_user}}"
    password: "{{email_pass}}"
    from_email: "{{email_user}}"
    to_email: "manager@company.com"
    subject: "Invoice Processing Report - {{date}}"
    body: "Processed {{processed_count}} invoices.\n\nAttachments saved to: {{save_path}}"
    use_tls: true
```

---

## Best Practices

### 1. Use App Passwords

Never use your main email password. Generate app-specific passwords.

### 2. Store Credentials Securely

Use CasareRPA Vault or environment variables:

```python
credential_name: "email_creds"  # Vault lookup
# or
username: "{{env.EMAIL_USER}}"  # Environment variable
```

### 3. Handle Connection Failures

Add retries for network issues:

```
[Read Emails]
    retry_count: 3
    retry_interval: 5000
```

### 4. Create Output Directories

Ensure save paths exist:

```
[Create Directory]
    path: "{{save_path}}\{{today}}"
    create_parents: true
```

### 5. Log Everything

Maintain audit trail of processed emails.

### 6. Test with Mark as Read Disabled

During development, set `mark_as_read: false` to avoid losing test data.

---

## Troubleshooting

### Authentication Failed

**Causes:**
- Wrong username/password
- Need app password (2FA accounts)
- IMAP not enabled

**Solutions:**
- Verify credentials
- Generate app password
- Enable IMAP in settings

### Folder Not Found

**Cause:** Wrong folder name
**Solution:** Use exact IMAP folder name (case-sensitive)

### No Emails Returned

**Causes:**
- Search criteria too restrictive
- No matching emails
- Wrong folder

**Solutions:**
- Test with `ALL` criteria first
- Check folder name
- Verify emails exist matching criteria

### SSL Certificate Error

**Cause:** Server certificate issues
**Solution:** In advanced cases, set `use_ssl: false` with `use_tls: true`

---

## Node Reference

### ReadEmailsNode

| Property | Type | Description |
|----------|------|-------------|
| imap_server | STRING | IMAP server hostname |
| imap_port | INTEGER | IMAP port (993) |
| username | STRING | Email username |
| password | STRING | Email password |
| folder | STRING | Mailbox folder |
| search_criteria | STRING | IMAP search query |
| limit | INTEGER | Max emails to retrieve |
| mark_as_read | BOOLEAN | Mark as read on retrieve |

### SaveAttachmentNode

| Property | Type | Description |
|----------|------|-------------|
| save_path | STRING | Directory to save files |
| email_uid | STRING | Email UID |
| folder | STRING | Source folder |

### MoveEmailNode

| Property | Type | Description |
|----------|------|-------------|
| source_folder | STRING | Origin folder |
| target_folder | STRING | Destination folder |
| email_uid | STRING | Email UID |

---

## Next Steps

- [API Integration](api-integration.md) - Send processed data to APIs
- [Data Processing](data-processing.md) - Parse invoice content
- [Scheduled Workflows](scheduled-workflows.md) - Run email processing daily
- [Error Handling](error-handling.md) - Handle failures gracefully

---

## Summary

You learned how to:
1. Connect to IMAP email servers
2. Search and filter emails
3. Download attachments
4. Mark emails as read
5. Move emails between folders
6. Handle errors in email workflows

Email automation is essential for invoice processing, notification handling, and communication workflows.
