# Google Workspace Triggers

CasareRPA integrates with Google Workspace to trigger workflows based on events in Google Drive, Sheets, and Calendar. All Google triggers require OAuth credentials with appropriate scopes.

---

## Prerequisites

### OAuth Setup

1. Create a Google Cloud project
2. Enable the required APIs:
   - Google Drive API
   - Google Sheets API
   - Google Calendar API
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials
5. Store credentials in CasareRPA:

```bash
# Add Google credential via CLI
casare-rpa credentials add google \
  --type oauth \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET"
```

Or via Canvas: **Settings > Credentials > Add Google Credential**

---

## Drive Trigger

Monitor Google Drive for file changes and trigger workflows when files are created, modified, or deleted.

### Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `credential_name` | STRING | `google` | Name of stored OAuth credential |
| `polling_interval` | INTEGER | `60` | Seconds between checks |
| `folder_id` | STRING | (empty) | Folder ID to monitor (empty = entire drive) |
| `include_subfolders` | BOOLEAN | `true` | Monitor subfolders recursively |
| `event_types` | STRING | `created,modified` | Comma-separated events |
| `file_types` | STRING | (empty) | File extensions to filter |
| `mime_types` | STRING | (empty) | MIME types to filter |
| `name_pattern` | STRING | (empty) | Glob pattern for file names |
| `ignore_own_changes` | BOOLEAN | `true` | Ignore changes made by automation |

### Event Types

| Event | Description |
|-------|-------------|
| `created` | New file uploaded or created |
| `modified` | Existing file content changed |
| `deleted` | File moved to trash |
| `moved` | File moved to different folder |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| `file_id` | STRING | Google Drive file ID |
| `file_name` | STRING | Name of the file |
| `mime_type` | STRING | MIME type of the file |
| `event_type` | STRING | Type of change (created, modified, etc.) |
| `modified_time` | STRING | Last modification timestamp (ISO format) |
| `size` | INTEGER | File size in bytes |
| `parent_id` | STRING | Parent folder ID |
| `parent_name` | STRING | Parent folder name |
| `web_view_link` | STRING | URL to view file in browser |
| `download_url` | STRING | Direct download URL |
| `changed_by` | STRING | Email of user who made change |
| `raw_change` | DICT | Full change object from API |
| `exec_out` | EXEC | Execution flow |

### Example: Process New PDFs

```
Trigger: New PDF in "Invoices" folder
+-------------------------------------------+
| Drive Trigger                              |
| folder_id: "1ABC123..."                    |
| event_types: "created"                     |
| file_types: "pdf"                          |
+-------------------------------------------+
        |
        |-- file_id --->  [Download File]
        |-- file_name ->  [Extract Text]
        |-- exec_out --->  |
                          |
                    [Process Invoice]
                          |
                    [Update Spreadsheet]
```

### Example: Sync Modified Documents

```python
# Workflow configuration
{
    "trigger": {
        "type": "DriveTriggerNode",
        "config": {
            "credential_name": "google",
            "folder_id": "1ABC123xyz",
            "event_types": "modified",
            "file_types": "docx,pdf",
            "polling_interval": 120
        }
    }
}
```

---

## Sheets Trigger

Monitor Google Sheets for data changes and trigger workflows when cells are modified or rows are added.

### Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `credential_name` | STRING | `google` | Name of stored OAuth credential |
| `spreadsheet_id` | STRING | (required) | Google Sheets spreadsheet ID |
| `sheet_name` | STRING | `Sheet1` | Name of sheet to monitor |
| `range` | STRING | (empty) | Cell range to monitor (empty = entire sheet) |
| `polling_interval` | INTEGER | `30` | Seconds between checks |
| `trigger_on_new_row` | BOOLEAN | `true` | Trigger on new row added |
| `trigger_on_cell_change` | BOOLEAN | `true` | Trigger on cell value change |
| `trigger_on_delete` | BOOLEAN | `false` | Trigger on row deletion |
| `watch_columns` | STRING | (empty) | Comma-separated columns to watch |
| `ignore_empty_rows` | BOOLEAN | `true` | Skip empty rows |

### Event Types

| Event | Description |
|-------|-------------|
| `new_row` | New row added to sheet |
| `cell_change` | Cell value modified |
| `delete` | Row deleted |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| `spreadsheet_id` | STRING | ID of the spreadsheet |
| `sheet_name` | STRING | Name of the modified sheet |
| `event_type` | STRING | Type of change |
| `row_number` | INTEGER | Row number of the change |
| `column` | STRING | Column letter of the change |
| `old_value` | ANY | Previous cell value |
| `new_value` | ANY | New cell value |
| `row_data` | LIST | Full row data as list |
| `row_dict` | DICT | Row data as dict (using header row) |
| `changed_cells` | LIST | List of changed cell references |
| `timestamp` | STRING | When the change was detected |
| `raw_data` | DICT | Full change data |
| `exec_out` | EXEC | Execution flow |

### Example: Process Form Submissions

```
Trigger: New row in "Form Responses" sheet
+-------------------------------------------+
| Sheets Trigger                             |
| spreadsheet_id: "1ABC123..."               |
| sheet_name: "Form Responses 1"             |
| trigger_on_new_row: true                   |
| trigger_on_cell_change: false              |
+-------------------------------------------+
        |
        |-- row_dict --->  [Process Data]
        |                       |
        |-- exec_out --->  [Validate Input]
                               |
                         [Send Email]
                               |
                         [Update CRM]
```

### Example: Monitor Inventory Changes

```python
# Workflow configuration
{
    "trigger": {
        "type": "SheetsTriggerNode",
        "config": {
            "credential_name": "google",
            "spreadsheet_id": "1ABC123xyz",
            "sheet_name": "Inventory",
            "range": "A:E",
            "watch_columns": "D,E",  # Only watch quantity columns
            "trigger_on_cell_change": true,
            "trigger_on_new_row": false,
            "polling_interval": 60
        }
    }
}
```

### Using Row Data

```python
# Access row data as dictionary (headers as keys)
row_dict = inputs.get("row_dict")
# {"Name": "John", "Email": "john@example.com", "Status": "New"}

customer_name = row_dict.get("Name")
customer_email = row_dict.get("Email")

# Or as list
row_data = inputs.get("row_data")
# ["John", "john@example.com", "New"]
```

---

## Calendar Trigger

Listen for Google Calendar events and trigger workflows based on upcoming meetings, new events, or event changes.

### Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `credential_name` | STRING | `google` | Name of stored OAuth credential |
| `calendar_id` | STRING | `primary` | Calendar ID to watch |
| `trigger_on` | CHOICE | `upcoming` | When to trigger |
| `minutes_before` | INTEGER | `15` | Minutes before event (for upcoming) |
| `polling_interval` | INTEGER | `60` | Seconds between checks (min 30) |
| `filter_summary` | STRING | (empty) | Keywords in event summary |
| `filter_attendees` | STRING | (empty) | Required attendee emails |
| `include_all_day` | BOOLEAN | `true` | Include all-day events |

### Trigger Modes

| Mode | Description |
|------|-------------|
| `upcoming` | Trigger N minutes before event starts |
| `created` | Trigger when new event is created |
| `updated` | Trigger when event is modified |
| `cancelled` | Trigger when event is cancelled |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| `event_id` | STRING | Calendar event ID |
| `calendar_id` | STRING | Calendar ID |
| `summary` | STRING | Event title |
| `description` | STRING | Event description |
| `start` | STRING | Start time (ISO format) |
| `end` | STRING | End time (ISO format) |
| `location` | STRING | Event location |
| `attendees` | LIST | List of attendee emails |
| `event_type` | STRING | Trigger type (upcoming, created, etc.) |
| `minutes_until_start` | INTEGER | Minutes until event starts |
| `organizer` | STRING | Event organizer email |
| `html_link` | STRING | Link to event in Google Calendar |
| `status` | STRING | Event status (confirmed, tentative, cancelled) |
| `created` | STRING | When event was created |
| `updated` | STRING | When event was last updated |
| `exec_out` | EXEC | Execution flow |

### Example: Meeting Reminders

```
Trigger: 15 minutes before meetings
+-------------------------------------------+
| Calendar Trigger                           |
| calendar_id: "primary"                     |
| trigger_on: "upcoming"                     |
| minutes_before: 15                         |
| filter_summary: "Team Meeting"             |
+-------------------------------------------+
        |
        |-- summary ------->  [Send Webhook]
        |-- attendees ----->  [Notify]
        |-- html_link ----->  |
        |-- exec_out ------>  |
                              |
                        [Prepare Agenda]
```

### Example: New Meeting Handler

```python
# Workflow configuration
{
    "trigger": {
        "type": "CalendarTriggerNode",
        "config": {
            "credential_name": "google",
            "calendar_id": "primary",
            "trigger_on": "created",
            "filter_attendees": "external@partner.com",
            "include_all_day": false,
            "polling_interval": 60
        }
    }
}
```

### Calendar ID Options

| ID | Description |
|----|-------------|
| `primary` | User's primary calendar |
| `email@example.com` | Specific user's calendar |
| `calendar_id` | Shared/team calendar ID |

Find calendar IDs in Google Calendar settings or via API.

---

## Authentication Flow

### Initial Setup

1. User adds Google credential in Canvas
2. OAuth consent screen opens in browser
3. User grants requested permissions
4. Refresh token stored securely

### Required Scopes

| Trigger | Required Scopes |
|---------|----------------|
| Drive | `https://www.googleapis.com/auth/drive.readonly` |
| Sheets | `https://www.googleapis.com/auth/spreadsheets.readonly` |
| Calendar | `https://www.googleapis.com/auth/calendar.readonly` |

### Token Refresh

Tokens are automatically refreshed before expiration. If refresh fails:

1. Re-authenticate via Credentials panel
2. Verify API quotas not exceeded
3. Check Google Cloud Console for errors

---

## Best Practices

### 1. Use Appropriate Polling Intervals

```yaml
# High-frequency data (forms, chats)
polling_interval: 30

# Standard updates (files, emails)
polling_interval: 60

# Low-frequency data (reports, logs)
polling_interval: 300
```

### 2. Filter at Trigger Level

```yaml
# Good - filter at trigger
file_types: "pdf,xlsx"
name_pattern: "Invoice_*.pdf"

# Avoid - process everything then filter
# (wastes API quota)
```

### 3. Handle Duplicates

Triggers use change tokens to avoid duplicates, but implement idempotency:

```python
# Check if already processed
if context.get_variable(f"processed_{file_id}"):
    return  # Skip duplicate

# Mark as processed
context.set_variable(f"processed_{file_id}", True)
```

### 4. Monitor API Quotas

Google APIs have daily quotas:

| API | Free Tier Quota |
|-----|-----------------|
| Drive | 10,000 requests/day |
| Sheets | 500 requests/100 sec |
| Calendar | 1,000,000 requests/day |

---

## Troubleshooting

### Trigger Not Firing

1. **Check credentials**: Verify OAuth token is valid
2. **Check filters**: Ensure events match filter criteria
3. **Check polling**: Verify polling interval is appropriate
4. **Check permissions**: Ensure API scopes are granted

### Permission Errors

```
Error: Insufficient permission to access resource
```

1. Re-authenticate with correct scopes
2. Verify resource sharing settings
3. Check API enabled in Google Cloud Console

### Rate Limit Errors

```
Error: Rate Limit Exceeded
```

1. Increase polling interval
2. Reduce number of monitored resources
3. Request quota increase from Google

### Missing Events

1. Check polling interval (events may occur between polls)
2. Verify filter criteria
3. Check `ignore_own_changes` setting

---

## Related Documentation

- [Schedule Trigger](schedule.md) - Time-based triggers
- [Webhook Trigger](webhook.md) - HTTP webhook triggers
- [File Watch Trigger](file-watch.md) - Local file system triggers
- [Credentials Management](../../security/credentials.md) - OAuth setup
