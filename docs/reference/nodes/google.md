# Google Workspace Nodes

Google Workspace nodes provide integration with Gmail, Google Sheets, and Google Drive. All nodes support OAuth 2.0 and service account authentication.

## Authentication

All Google nodes share common authentication properties:

| Property | Type | Description |
|----------|------|-------------|
| `service_account_file` | FILE_PATH | Path to service account JSON key |
| `access_token` | STRING | OAuth 2.0 access token |
| `credential_name` | STRING | Vault credential name |

### Authentication Methods

1. **Service Account** (recommended for automation): Use `service_account_file`
2. **OAuth Token**: Use `access_token` for user-delegated access
3. **Credential Vault**: Use `credential_name` for centralized credentials

---

## Gmail Nodes

### GmailSendEmailNode

Send emails via Gmail API.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `service_account_file` | FILE_PATH | `""` | Service account JSON path |
| `access_token` | STRING | `""` | OAuth access token |
| `credential_name` | STRING | `""` | Vault credential name |
| `sender_email` | STRING | (required) | From email address |
| `to` | STRING | (required) | Recipients (comma-separated) |
| `cc` | STRING | `""` | CC recipients |
| `bcc` | STRING | `""` | BCC recipients |
| `subject` | STRING | (required) | Email subject |
| `body` | TEXT | (required) | Email body |
| `body_type` | CHOICE | `text` | Body format: `text` or `html` |
| `attachments` | STRING | `""` | Attachment file paths (comma-separated) |

#### Ports

**Inputs:**
- `to` (STRING) - Recipients override
- `subject` (STRING) - Subject override
- `body` (STRING) - Body override
- `attachments` (LIST) - Attachments override

**Outputs:**
- `message_id` (STRING) - Sent message ID
- `thread_id` (STRING) - Gmail thread ID
- `success` (BOOLEAN) - Send success
- `error` (STRING) - Error message

#### Example

```python
send_email = GmailSendEmailNode(
    node_id="send_report",
    config={
        "service_account_file": "C:\\credentials\\service-account.json",
        "sender_email": "automation@company.com",
        "to": "{{recipient_email}}",
        "subject": "Daily Report - {{date}}",
        "body": "Please find attached the daily report.",
        "body_type": "text",
        "attachments": "{{report_file_path}}"
    }
)
```

### GmailReadEmailNode

Read emails from Gmail inbox.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `service_account_file` | FILE_PATH | `""` | Service account JSON |
| `query` | STRING | `""` | Gmail search query |
| `max_results` | INTEGER | `10` | Maximum emails to fetch |
| `include_body` | BOOLEAN | `true` | Include email body |
| `include_attachments` | BOOLEAN | `false` | Download attachments |

#### Ports

**Outputs:**
- `emails` (LIST) - List of email objects
- `count` (INTEGER) - Number of emails found
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Read unread emails from specific sender
read_emails = GmailReadEmailNode(
    node_id="read_inbox",
    config={
        "query": "is:unread from:reports@vendor.com",
        "max_results": 50,
        "include_body": True,
        "include_attachments": True
    }
)
```

---

## Google Sheets Nodes

### SheetsGetCellNode

Read a single cell or range from Google Sheets.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `service_account_file` | FILE_PATH | `""` | Service account JSON |
| `access_token` | STRING | `""` | OAuth token |
| `credential_name` | STRING | `""` | Vault credential |
| `spreadsheet_id` | STRING | (required) | Spreadsheet ID from URL |
| `sheet_name` | STRING | `Sheet1` | Sheet/tab name |
| `range` | STRING | (required) | Cell range (e.g., `A1`, `A1:D10`) |
| `value_render` | CHOICE | `FORMATTED_VALUE` | Value format |
| `date_time_render` | CHOICE | `FORMATTED_STRING` | Date format |

#### Ports

**Inputs:**
- `spreadsheet_id` (STRING) - Spreadsheet ID override
- `range` (STRING) - Range override

**Outputs:**
- `values` (LIST) - Cell values as 2D array
- `value` (ANY) - First cell value (single cell)
- `row_count` (INTEGER) - Number of rows
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Read data range from sheet
get_data = SheetsGetCellNode(
    node_id="read_sheet",
    config={
        "service_account_file": "{{google_credentials}}",
        "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        "sheet_name": "Sales",
        "range": "A2:E100"
    }
)
```

### SheetsWriteCellNode

Write data to Google Sheets.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `spreadsheet_id` | STRING | (required) | Spreadsheet ID |
| `sheet_name` | STRING | `Sheet1` | Sheet/tab name |
| `range` | STRING | (required) | Target range |
| `value` | STRING | `""` | Single value to write |
| `values` | JSON | `[]` | 2D array of values |
| `value_input` | CHOICE | `USER_ENTERED` | Input option |

#### Value Input Options

- `USER_ENTERED` - Parse values as if typed by user
- `RAW` - Store values exactly as provided

#### Ports

**Inputs:**
- `spreadsheet_id` (STRING) - Spreadsheet ID
- `range` (STRING) - Target range
- `value` (STRING) - Single value
- `values` (LIST) - 2D array of values

**Outputs:**
- `updated_cells` (INTEGER) - Number of cells updated
- `updated_range` (STRING) - Actual updated range
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Write data to sheet
write_data = SheetsWriteCellNode(
    node_id="write_results",
    config={
        "spreadsheet_id": "{{spreadsheet_id}}",
        "sheet_name": "Results",
        "range": "A1",
        "values": [
            ["Name", "Email", "Status"],
            ["{{name}}", "{{email}}", "Processed"]
        ],
        "value_input": "USER_ENTERED"
    }
)
```

### SheetsAppendRowNode

Append rows to a Google Sheet.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `spreadsheet_id` | STRING | (required) | Spreadsheet ID |
| `sheet_name` | STRING | `Sheet1` | Sheet name |
| `values` | JSON | (required) | Row data as 2D array |
| `insert_data_option` | CHOICE | `INSERT_ROWS` | Insert behavior |

#### Example

```python
# Append new row to tracking sheet
append_row = SheetsAppendRowNode(
    node_id="log_entry",
    config={
        "spreadsheet_id": "{{log_sheet_id}}",
        "sheet_name": "Log",
        "values": [["{{timestamp}}", "{{event}}", "{{details}}"]]
    }
)
```

---

## Google Drive Nodes

### DriveUploadFileNode

Upload files to Google Drive.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `service_account_file` | FILE_PATH | `""` | Service account JSON |
| `file_path` | FILE_PATH | (required) | Local file to upload |
| `folder_id` | STRING | `""` | Target folder ID (root if empty) |
| `file_name` | STRING | `""` | Custom filename (uses original if empty) |
| `mime_type` | STRING | `""` | Override MIME type |
| `convert_to_google` | BOOLEAN | `false` | Convert to Google Docs format |

#### Ports

**Inputs:**
- `file_path` (STRING) - Local file path
- `folder_id` (STRING) - Target folder ID
- `file_name` (STRING) - Custom filename

**Outputs:**
- `file_id` (STRING) - Uploaded file ID
- `web_view_link` (STRING) - View URL
- `web_content_link` (STRING) - Download URL
- `success` (BOOLEAN) - Upload success

#### Example

```python
upload_file = DriveUploadFileNode(
    node_id="upload_report",
    config={
        "service_account_file": "{{google_credentials}}",
        "file_path": "{{report_file}}",
        "folder_id": "{{reports_folder_id}}",
        "file_name": "Report_{{date}}.pdf"
    }
)
```

### DriveDownloadFileNode

Download files from Google Drive.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_id` | STRING | (required) | Drive file ID |
| `save_path` | FILE_PATH | (required) | Local save path |
| `export_format` | STRING | `""` | Export format for Google Docs |

#### Ports

**Outputs:**
- `file_path` (STRING) - Downloaded file path
- `file_size` (INTEGER) - File size in bytes
- `mime_type` (STRING) - File MIME type
- `success` (BOOLEAN) - Download success

### DriveListFilesNode

List files in Google Drive folder.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `folder_id` | STRING | `""` | Folder ID (root if empty) |
| `query` | STRING | `""` | Search query |
| `max_results` | INTEGER | `100` | Maximum files to list |
| `include_folders` | BOOLEAN | `true` | Include folders in results |

#### Ports

**Outputs:**
- `files` (LIST) - List of file metadata
- `count` (INTEGER) - Number of files
- `success` (BOOLEAN) - Operation success

### DriveCreateFolderNode

Create a new folder in Google Drive.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `folder_name` | STRING | (required) | New folder name |
| `parent_id` | STRING | `""` | Parent folder ID |

#### Ports

**Outputs:**
- `folder_id` (STRING) - Created folder ID
- `folder_link` (STRING) - Folder URL
- `success` (BOOLEAN) - Creation success

### DriveDeleteFileNode

Delete a file or folder from Google Drive.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_id` | STRING | (required) | File/folder ID to delete |
| `permanent` | BOOLEAN | `false` | Skip trash (permanent delete) |

### DriveMoveFileNode

Move a file to a different folder.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_id` | STRING | (required) | File ID to move |
| `new_folder_id` | STRING | (required) | Destination folder ID |

### DriveCopyFileNode

Create a copy of a file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_id` | STRING | (required) | File ID to copy |
| `new_name` | STRING | `""` | Name for copy |
| `target_folder_id` | STRING | `""` | Destination folder |

### DriveShareFileNode

Share a file or folder.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_id` | STRING | (required) | File/folder ID |
| `email` | STRING | (required) | Email to share with |
| `role` | CHOICE | `reader` | Permission: reader, writer, commenter |
| `send_notification` | BOOLEAN | `true` | Send email notification |

---

## Complete Example: Invoice Processing Workflow

```python
# 1. Read new invoices from Gmail
read_emails = GmailReadEmailNode(
    node_id="read_invoices",
    config={
        "query": "subject:invoice is:unread has:attachment",
        "include_attachments": True
    }
)

# 2. Save attachment to Drive
upload_attachment = DriveUploadFileNode(
    node_id="save_invoice",
    config={
        "folder_id": "{{invoices_folder_id}}",
        "file_path": "{{attachment_path}}"
    }
)

# 3. Log to spreadsheet
log_invoice = SheetsAppendRowNode(
    node_id="log_invoice",
    config={
        "spreadsheet_id": "{{tracking_sheet_id}}",
        "values": [["{{date}}", "{{sender}}", "{{amount}}", "{{file_id}}"]]
    }
)
```

---

## Best Practices

### Service Account Setup

1. Create service account in Google Cloud Console
2. Enable required APIs (Gmail, Sheets, Drive)
3. Download JSON key file
4. For Gmail: Enable domain-wide delegation

### Rate Limits

Google APIs have usage quotas. Implement appropriate delays:

| API | Default Quota |
|-----|---------------|
| Gmail | 250 quota units/second |
| Sheets | 500 requests/100 seconds |
| Drive | 1000 requests/100 seconds |

### Error Handling

> **Note:** All Google nodes output `success` (boolean) and `error` (string). Always check `success` before using other outputs.

## Related Documentation

- [HTTP Nodes](http.md) - OAuth token management
- [File Operations](file-operations.md) - Local file handling
- [Email Nodes](email.md) - SMTP/IMAP alternatives
