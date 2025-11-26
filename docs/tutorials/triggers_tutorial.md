# CasareRPA Triggers Tutorial

This tutorial explains how to use the trigger system to automatically start workflows based on various events.

## Overview

Triggers allow your workflows to run automatically when specific events occur:

| Trigger Type | Description | Use Case |
|-------------|-------------|----------|
| **Manual** | Run from UI or API | Testing, on-demand tasks |
| **Scheduled** | Run on a schedule (cron/interval) | Daily reports, periodic cleanup |
| **Webhook** | HTTP POST request | External system integration |
| **File Watch** | File system changes | Process new files automatically |
| **Email** | Incoming emails | Invoice processing, support tickets |
| **App Event** | Windows/browser events | React to application changes |
| **Error** | Workflow failures | Error notifications, retry logic |
| **Workflow Call** | Called by other workflows | Modular sub-workflows |
| **Form** | Form submissions | User input collection |
| **Chat** | Chat messages | Slack/Teams bot commands |

---

## Accessing the Triggers Tab

1. Open CasareRPA Canvas
2. Look at the **Bottom Panel** (below the canvas)
3. Click the **"Triggers"** tab

The Triggers tab shows:
- List of configured triggers
- Status (ON/OFF)
- Type
- Last triggered time
- Run count
- Action buttons (Run, Edit)

---

## Tutorial 1: Create a Scheduled Trigger

**Goal:** Run a workflow every day at 9:00 AM

### Step 1: Create a Simple Workflow

First, create a workflow that logs a message:

1. Drag a **Log Message** node onto the canvas
2. Set the message to: `"Daily report started at {datetime.now()}"`
3. Save the workflow as `daily_report.json`

### Step 2: Add the Trigger

1. Go to the **Triggers** tab in the bottom panel
2. Click **"+ Add Trigger"**
3. In the type selector, click **"Scheduled"**
4. Click **"Continue"**

### Step 3: Configure the Trigger

**General Tab:**
- Name: `Daily Morning Report`
- Description: `Runs the daily report workflow at 9 AM`
- Enabled: checked

**Settings Tab:**
- Schedule Type: `cron`
- Cron Expression: `0 9 * * *` (every day at 9:00 AM)
- Timezone: `America/New_York` (or your timezone)

**Advanced Tab:**
- Priority: `1` (Normal)
- Cooldown: `0` seconds

5. Click **"Create"**

### Step 4: Verify

The trigger should appear in the Triggers tab with status "ON".

---

## Tutorial 2: Create a Webhook Trigger

**Goal:** Trigger a workflow via HTTP POST from an external system

### Step 1: Create the Workflow

Create a workflow that processes incoming data:

1. Add a **Log Message** node
2. Set message to: `"Webhook received: {trigger_payload}"`
3. Save as `webhook_processor.json`

### Step 2: Add the Webhook Trigger

1. Click **"+ Add Trigger"** in the Triggers tab
2. Select **"Webhook"**
3. Click **"Continue"**

### Step 3: Configure

**General Tab:**
- Name: `External System Webhook`
- Enabled: checked

**Settings Tab:**
- Authentication: `api_key`
- Secret Key: `my-secret-key-123`
- Allowed IPs: (leave empty for any IP, or add specific IPs)

4. Click **"Create"**

### Step 4: Test the Webhook

The webhook URL will be:
```
POST http://localhost:8766/webhook/{trigger_id}
```

Test with curl:
```bash
curl -X POST http://localhost:8766/webhook/YOUR_TRIGGER_ID \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret-key-123" \
  -d '{"order_id": "12345", "customer": "John Doe"}'
```

The workflow will receive the JSON payload in the `trigger_payload` variable.

---

## Tutorial 3: Create a File Watch Trigger

**Goal:** Automatically process CSV files dropped into a folder

### Step 1: Create the Workflow

1. Add a **Log Message** node: `"New file detected: {file_path}"`
2. Add a **Read CSV** node to process the file
3. Save as `csv_processor.json`

### Step 2: Add the File Watch Trigger

1. Click **"+ Add Trigger"**
2. Select **"File Watch"**
3. Click **"Continue"**

### Step 3: Configure

**General Tab:**
- Name: `CSV File Processor`
- Enabled: checked

**Settings Tab:**
- Watch Paths: `C:\Users\YourName\Documents\Incoming`
- Patterns: `*.csv`
- Ignore Patterns: `*.tmp`, `~*`
- Events: `created` (or `created`, `modified`)
- Recursive: unchecked

4. Click **"Create"**

### Step 4: Test

1. Drop a `.csv` file into the watched folder
2. The workflow should trigger automatically
3. Check the Log tab for execution details

---

## Tutorial 4: Create an Error Handler Trigger

**Goal:** Send a notification when any workflow fails

### Step 1: Create the Error Handler Workflow

1. Add a **Log Message** node: `"ERROR: Workflow {failed_workflow_id} failed with: {error_message}"`
2. Add a **Send Email** node (optional) to notify admins
3. Save as `error_notifier.json`

### Step 2: Add the Error Trigger

1. Click **"+ Add Trigger"**
2. Select **"Error Handler"**
3. Click **"Continue"**

### Step 3: Configure

**General Tab:**
- Name: `Global Error Handler`
- Enabled: checked

**Settings Tab:**
- Source Scenarios: (leave empty to monitor all)
- Error Types: (leave empty for all types)
- Error Pattern: (optional regex, e.g., `timeout|connection`)
- Min Severity: `error`
- Exclude Self: checked (prevents infinite loops)

4. Click **"Create"**

Now when any workflow fails, this error handler workflow will run.

---

## Tutorial 5: Create a Workflow Call Trigger

**Goal:** Create a reusable sub-workflow that other workflows can call

### Step 1: Create the Sub-Workflow

Create a workflow that validates an email address:

1. Add a **Set Variable** node: `is_valid = regex_match(email, r'^[^@]+@[^@]+\.[^@]+$')`
2. Add a **Return** node with `is_valid`
3. Save as `validate_email.json`

### Step 2: Add the Workflow Call Trigger

1. Click **"+ Add Trigger"**
2. Select **"Workflow Call"**
3. Click **"Continue"**

### Step 3: Configure

**General Tab:**
- Name: `Email Validator`
- Enabled: checked

**Settings Tab:**
- Call Alias: `validate_email`
- Synchronous: checked (wait for result)
- Allowed Callers: (leave empty to allow all)

4. Click **"Create"**

### Step 4: Call from Another Workflow

In your main workflow, use a **Call Workflow** node:
- Alias: `validate_email`
- Input: `{"email": "test@example.com"}`

The result will be available in the workflow variables.

---

## Accessing Trigger Data in Workflows

When a trigger fires, it provides data to the workflow through special variables:

### Common Variables (All Triggers)

```python
trigger_id        # Unique ID of the trigger
trigger_type      # Type (webhook, scheduled, file_watch, etc.)
trigger_payload   # Data from the trigger event
trigger_metadata  # Additional metadata
```

### Webhook Trigger Variables

```python
trigger_payload.body      # POST body (parsed JSON)
trigger_payload.headers   # Request headers
trigger_payload.query     # Query parameters
```

### File Watch Trigger Variables

```python
trigger_payload.file_path    # Full path to the file
trigger_payload.file_name    # Just the filename
trigger_payload.event_type   # created, modified, deleted, moved
trigger_payload.is_directory # True if it's a directory
```

### Email Trigger Variables

```python
trigger_payload.subject      # Email subject
trigger_payload.sender       # Sender email address
trigger_payload.body_text    # Plain text body
trigger_payload.body_html    # HTML body
trigger_payload.attachments  # List of attachments
```

### Error Trigger Variables

```python
trigger_payload.error_message      # The error message
trigger_payload.error_type         # Type of error
trigger_payload.failed_workflow_id # Workflow that failed
trigger_payload.failed_node_id     # Node that failed
trigger_payload.stack_trace        # Full stack trace
```

---

## Managing Triggers

### Enable/Disable a Trigger

1. Right-click the trigger in the list
2. Select **"Enable"** or **"Disable"**

Or click the status indicator to toggle.

### Edit a Trigger

1. Click the **"Edit"** button in the Actions column
2. Or double-click the trigger row
3. Modify settings and click **"Save"**

### Delete a Trigger

1. Right-click the trigger
2. Select **"Delete"**
3. Confirm the deletion

### Run a Trigger Manually

1. Click the **"Run"** button in the Actions column
2. The workflow will execute immediately with an empty payload

---

## Best Practices

1. **Name triggers descriptively** - Include what triggers it and what it does
2. **Use cooldowns** - Prevent rapid-fire triggers (especially for file watch)
3. **Set appropriate priorities** - Critical triggers should have higher priority
4. **Test thoroughly** - Use manual run to test before enabling
5. **Monitor the Log tab** - Check for trigger execution and errors
6. **Use error triggers** - Always have an error handler for production workflows

---

## Troubleshooting

### Trigger Not Firing

1. Check that the trigger is **enabled** (status = ON)
2. Verify the trigger configuration is correct
3. Check the Log tab for errors
4. For webhooks, verify the URL and authentication

### Webhook Returns 401 Unauthorized

1. Check the API key or JWT token
2. Verify the header name (default: `X-API-Key`)
3. Check IP allowlist if configured

### File Watch Not Detecting Files

1. Verify the watch path exists
2. Check file patterns (case-sensitive on Linux)
3. Ensure the file isn't being written when detected (use cooldown)

### Scheduled Trigger Not Running

1. Verify cron expression syntax
2. Check timezone setting
3. Ensure the orchestrator engine is running

---

## Example: Complete Invoice Processing System

Here's a complete example combining multiple triggers:

### Workflows

1. **invoice_processor.json** - Processes invoice PDFs
2. **error_notifier.json** - Sends error notifications
3. **daily_summary.json** - Generates daily summary report

### Triggers

1. **File Watch** - Monitors `C:\Invoices\Incoming` for new PDFs
2. **Error Trigger** - Catches processing failures
3. **Scheduled** - Runs daily summary at 6 PM

### Setup

```
Trigger 1: "Invoice File Watcher"
- Type: File Watch
- Path: C:\Invoices\Incoming
- Pattern: *.pdf
- Workflow: invoice_processor.json

Trigger 2: "Invoice Error Handler"
- Type: Error
- Source: invoice_processor scenario
- Workflow: error_notifier.json

Trigger 3: "Daily Invoice Summary"
- Type: Scheduled
- Cron: 0 18 * * *
- Workflow: daily_summary.json
```

This creates a complete automated invoice processing pipeline!
