# Google Workspace Integration Tutorial

Learn to automate Google Workspace: read and write Google Sheets, manage Google Drive files, and send Gmail emails.

**Time required:** 30 minutes

**What you will build:**
A workflow that reads data from Google Sheets, processes it, writes results back, and sends an email notification via Gmail.

## Prerequisites

- CasareRPA installed and running
- Google account with Workspace or personal Gmail
- Google Cloud project with APIs enabled
- Service account or OAuth credentials

## Goals

By the end of this tutorial, you will:
- Set up Google API authentication
- Read data from Google Sheets
- Write data back to sheets
- Upload files to Google Drive
- Send emails via Gmail API
- Handle Google API quotas

---

## Part 1: Setting Up Google API Access

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select Project** > **New Project**
3. Name it: `CasareRPA Automation`
4. Click **Create**

### Step 2: Enable APIs

Enable the following APIs:

1. Go to **APIs & Services** > **Library**
2. Search and enable:
   - Google Sheets API
   - Google Drive API
   - Gmail API

### Step 3: Create Service Account

For server-side automation (recommended):

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Name: `casare-rpa-service`
4. Click **Create and Continue**
5. Grant role: **Editor** (or specific roles)
6. Click **Done**

### Step 4: Create Service Account Key

1. Click on the service account you created
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON**
5. Save the downloaded file securely

### Step 5: Share Resources with Service Account

For Google Sheets:
1. Open your Google Sheet
2. Click **Share**
3. Add the service account email: `casare-rpa-service@your-project.iam.gserviceaccount.com`
4. Grant **Editor** access

---

## Part 2: Reading from Google Sheets

### Step 6: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `google_sheets_tutorial.json`

### Step 7: Configure Credentials

1. Drag **Set Variable** from **Variable**
2. Create variables:

| Variable | Value |
|----------|-------|
| credentials_path | `C:\credentials\google-service-account.json` |
| spreadsheet_id | `1ABC123...` (from sheet URL) |
| sheet_name | `Sales Data` |

> **Tip:** The spreadsheet ID is in the URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### Step 8: Read Sheet Data

1. Drag **Read Google Sheet** from **Google** > **Sheets**
2. Position at (400, 300)

### Configure Read Google Sheet

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| spreadsheet_id | `{{spreadsheet_id}}` |
| range | `{{sheet_name}}!A1:E100` |
| value_render_option | `FORMATTED_VALUE` |

### Range Syntax

| Example | Description |
|---------|-------------|
| `Sheet1!A1:E10` | Specific range |
| `Sheet1!A:E` | Entire columns A-E |
| `Sheet1` | Entire sheet |
| `A1:E10` | Default sheet, specific range |

### Output Ports

- `data` (LIST) - Rows as list of lists
- `row_count` (INTEGER) - Number of rows
- `headers` (LIST) - First row if present

---

## Step 9: Process Data

Convert the raw data to dictionaries:

```
[Read Google Sheet]
    |
    +---> data (list of lists)
    |
[List Get Item]  # Get header row
    index: 0
    |
    +---> headers
    |
[List Slice]  # Get data rows (skip header)
    start: 1
    |
    +---> data_rows
    |
[For Loop Start]
    items: data_rows
    item_var: row
        |
      body
        |
    [Create Dict from Lists]  # Zip headers with row values
        keys: {{headers}}
        values: {{row}}
            |
    [List Append: to processed_data]
            |
    [For Loop End]
```

---

## Part 3: Writing to Google Sheets

### Step 10: Prepare Data to Write

After processing, write results back:

```
[Set Variable: output_data]
    value: [
        ["Order ID", "Status", "Processed At"],
        ["1001", "Complete", "2025-01-15 10:30:00"],
        ["1002", "Complete", "2025-01-15 10:30:05"]
    ]
```

### Step 11: Write to Sheet

1. Drag **Write Google Sheet** from **Google** > **Sheets**
2. Position after processing nodes

### Configure Write Google Sheet

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| spreadsheet_id | `{{spreadsheet_id}}` |
| range | `Results!A1` |
| data | `{{output_data}}` |
| value_input_option | `USER_ENTERED` |

### Value Input Options

| Option | Description |
|--------|-------------|
| `RAW` | Values stored as-is (strings) |
| `USER_ENTERED` | Parsed as if typed (dates, numbers) |

---

## Step 12: Append Data (Instead of Overwrite)

To add rows without overwriting:

1. Drag **Append Google Sheet** from **Google** > **Sheets**

### Configure Append

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| spreadsheet_id | `{{spreadsheet_id}}` |
| range | `Log!A:D` |
| data | `{{new_rows}}` |
| value_input_option | `USER_ENTERED` |

---

## Part 4: Google Drive Integration

### Step 13: List Files in Folder

1. Drag **List Drive Files** from **Google** > **Drive**

### Configure List Files

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| folder_id | `1ABC123...` |
| query | `mimeType='application/pdf'` |
| page_size | `100` |

### Query Examples

| Query | Description |
|-------|-------------|
| `name contains 'Invoice'` | Name contains text |
| `mimeType='application/pdf'` | PDF files only |
| `modifiedTime > '2025-01-01'` | Modified after date |
| `'folder_id' in parents` | Files in specific folder |

### Output

- `files` (LIST) - List of file metadata
- `count` (INTEGER) - Number of files

---

### Step 14: Upload File to Drive

1. Drag **Upload to Drive** from **Google** > **Drive**

### Configure Upload

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| file_path | `C:\reports\monthly_report.pdf` |
| folder_id | `{{target_folder_id}}` |
| file_name | `Report_{{today}}.pdf` |
| mime_type | `application/pdf` |

### Output

- `file_id` (STRING) - ID of uploaded file
- `web_link` (STRING) - Shareable link

---

### Step 15: Download File from Drive

1. Drag **Download from Drive** from **Google** > **Drive**

### Configure Download

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| file_id | `{{file_id}}` |
| save_path | `C:\downloads\{{file_name}}` |

---

### Step 16: Share File

1. Drag **Share Drive File** from **Google** > **Drive**

### Configure Share

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| file_id | `{{file_id}}` |
| email | `recipient@example.com` |
| role | `reader` |
| send_notification | `true` |

### Role Options

| Role | Permissions |
|------|-------------|
| `reader` | View only |
| `commenter` | View and comment |
| `writer` | Edit |
| `owner` | Full control (transfer ownership) |

---

## Part 5: Gmail Integration

### Step 17: Send Email via Gmail API

1. Drag **Send Gmail** from **Google** > **Gmail**

### Configure Send Gmail

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| to | `recipient@example.com` |
| subject | `Monthly Report - {{month}}` |
| body | `Please find the attached report.` |
| is_html | `false` |
| cc | `manager@example.com` |
| attachments | `["C:\\reports\\report.pdf"]` |

### HTML Email Body

```
[Set Variable: email_body]
    value: "<h1>Monthly Report</h1><p>The report for <b>{{month}}</b> is ready.</p><ul><li>Total Orders: {{total_orders}}</li><li>Revenue: ${{revenue}}</li></ul>"

[Send Gmail]
    body: {{email_body}}
    is_html: true
```

---

### Step 18: Read Gmail Messages

1. Drag **Read Gmail** from **Google** > **Gmail**

### Configure Read Gmail

| Property | Value |
|----------|-------|
| credentials_file | `{{credentials_path}}` |
| query | `from:vendor@example.com is:unread` |
| max_results | `10` |
| include_body | `true` |

### Query Examples

| Query | Description |
|-------|-------------|
| `is:unread` | Unread emails |
| `from:email@example.com` | From specific sender |
| `subject:Invoice` | Subject contains text |
| `has:attachment` | Has attachments |
| `after:2025/01/01` | After date |
| `label:Important` | Has label |

---

## Complete Workflow: Daily Sales Report

### Workflow Overview

```
[Start]
    |
[Set Credentials]
    |
[Read Google Sheet: Sales Data]
    |
[Filter: Today's Sales]
    |
[List Reduce: Calculate Total]
    |
[Create Report Dict]
    |
[Append Google Sheet: Daily Log]
    |
[Upload PDF to Drive]
    |
[Send Gmail: Report Notification]
    |
[End]
```

### Detailed Implementation

```
[Start]
    |
[Set Variable: spreadsheet_id]
    value: "1ABC..."
    |
[Set Variable: today]
    value: "{{now|date:'YYYY-MM-DD'}}"
    |
[Read Google Sheet]
    range: "Sales!A:F"
        |
        +---> sales_data
        |
[List Filter]
    condition: "equals"
    key_path: "date"
    value: {{today}}
        |
        +---> today_sales
        |
[List Reduce]
    operation: "sum"
    key_path: "amount"
        |
        +---> total_revenue
        |
[List Reduce]
    operation: "count"
        |
        +---> order_count
        |
[Create Dict]
    |
[Dict Set: date, total_revenue, order_count, processed_at]
        |
        +---> report_summary
        |
[Append Google Sheet]
    range: "Daily Reports!A:D"
    data: [[{{today}}, {{total_revenue}}, {{order_count}}, {{timestamp}}]]
        |
[Format String]
    template: "Daily Sales Report\n\nDate: {date}\nOrders: {order_count}\nRevenue: ${total_revenue}"
    variables: {{report_summary}}
        |
        +---> email_body
        |
[Send Gmail]
    to: "manager@company.com"
    subject: "Sales Report - {{today}}"
    body: {{email_body}}
        |
[Log: "Report sent successfully"]
        |
[End]
```

---

## Handling API Quotas

### Google Sheets Quotas

| Quota | Limit |
|-------|-------|
| Read requests | 300/minute per project |
| Write requests | 300/minute per project |
| Cells per request | 100,000 |

### Rate Limiting Strategy

```
[For Loop Start]
    items: {{batches}}
        |
      body
        |
    [Write Google Sheet]
        data: {{batch}}
            |
    [Wait]
        seconds: 0.5  # Max 120 writes/minute
            |
    [For Loop End]
```

---

## Error Handling

### Common Google API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | No access to resource | Share resource with service account |
| 404 Not Found | Wrong ID | Verify spreadsheet/file ID |
| 429 Too Many Requests | Rate limited | Add delays, implement backoff |
| 400 Bad Request | Invalid range/data | Check range syntax, data format |

### Error Handling Pattern

```
[Try]
    |
  try_body
    |
[Read Google Sheet]
    |
[Write Google Sheet]
    |
    +---(error)---> [Catch]
    |                   |
    |              catch_body
    |                   |
    |              [If: error_type == "RATE_LIMIT_EXCEEDED"]
    |                   |
    |                 true
    |                   |
    |              [Wait: 60]  # Wait and retry
    |                   |
    |              [Read Google Sheet]  # Retry
    |                   |
    +--------+---------+
             |
         [Finally]
             |
        [Log: "Google Sheets operation complete"]
```

---

## OAuth 2.0 for User Authorization

For accessing user data (not service account):

### Step 1: Create OAuth Client

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Desktop app**
4. Download the credentials file

### Step 2: Authorize in Workflow

```
[Google OAuth Authorize]
    credentials_file: "C:\credentials\oauth_client.json"
    scopes: ["https://www.googleapis.com/auth/spreadsheets"]
    token_file: "C:\credentials\token.json"
        |
        +---> access_token
```

The first run opens a browser for authorization.

---

## Best Practices

### 1. Use Service Accounts for Automation

Service accounts don't require user interaction.

### 2. Batch Operations

```
# Instead of:
[Write Row 1]
[Write Row 2]
[Write Row 3]

# Do:
[Write All Rows at Once]
    data: [[row1], [row2], [row3]]
```

### 3. Handle Credentials Securely

- Store credentials in CasareRPA Vault
- Never commit credentials to version control
- Use environment variables for paths

### 4. Use Named Ranges

```
# Instead of: A1:E100
# Use named range: SalesData

[Read Google Sheet]
    range: "SalesData"
```

### 5. Log API Calls

Track quota usage:

```
[Log]
    message: "Google Sheets API call: READ {{range}}"
    level: "debug"
```

---

## Node Reference

### ReadGoogleSheetNode

| Property | Type | Description |
|----------|------|-------------|
| credentials_file | FILE_PATH | Service account JSON |
| spreadsheet_id | STRING | Sheet ID from URL |
| range | STRING | A1 notation range |
| value_render_option | CHOICE | FORMATTED_VALUE/UNFORMATTED_VALUE |

### WriteGoogleSheetNode

| Property | Type | Description |
|----------|------|-------------|
| credentials_file | FILE_PATH | Service account JSON |
| spreadsheet_id | STRING | Sheet ID |
| range | STRING | Starting cell |
| data | LIST | Data to write |
| value_input_option | CHOICE | RAW/USER_ENTERED |

### SendGmailNode

| Property | Type | Description |
|----------|------|-------------|
| credentials_file | FILE_PATH | Service account JSON |
| to | STRING | Recipient email |
| subject | STRING | Email subject |
| body | STRING | Email body |
| is_html | BOOLEAN | HTML content |
| attachments | LIST | File paths |

---

## Next Steps

- [API Integration](api-integration.md) - Connect to other APIs
- [Scheduled Workflows](scheduled-workflows.md) - Automate daily reports
- [Error Handling](error-handling.md) - Handle API failures
- [Data Processing](data-processing.md) - Process sheet data

---

## Summary

You learned how to:
1. Set up Google API authentication
2. Read and write Google Sheets data
3. Upload and download Google Drive files
4. Send emails via Gmail API
5. Handle API quotas and errors

Google Workspace integration enables powerful automation for spreadsheet processing, document management, and email workflows.
