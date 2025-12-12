# Triggers

Triggers are special nodes that start workflows automatically when specific events occur. Instead of manually running a workflow, triggers allow automations to execute in response to schedules, incoming data, or external events.

## What is a Trigger?

A trigger is a workflow entry point that:

- **Listens** for specific events or conditions
- **Activates** when the condition is met
- **Starts** the workflow execution
- **Provides** event data through output ports

Think of triggers as the "when" of your automation: "When an email arrives," "When a file is created," or "When it's 9 AM every Monday."

## Trigger vs Executable Nodes

Triggers differ from regular nodes in important ways:

| Aspect | Regular Nodes | Trigger Nodes |
|--------|---------------|---------------|
| exec_in port | Has exec_in | **No** exec_in |
| Position | Middle of workflow | **Start** of workflow |
| Activation | When previous node completes | When event occurs |
| Data | Receives from connections | Produces from event |
| Purpose | Process data | Start workflow |

A trigger node replaces the Start node as the workflow entry point.

## Trigger Types

CasareRPA includes triggers for various event sources:

### Schedule Trigger

Runs workflows on a time-based schedule.

| Property | Description |
|----------|-------------|
| `frequency` | once, interval, hourly, daily, weekly, monthly, cron |
| `time_hour` | Hour of day (0-23) |
| `time_minute` | Minute (0-59) |
| `interval_seconds` | Interval between runs (for interval mode) |
| `day_of_week` | Day for weekly schedules (mon-sun) |
| `day_of_month` | Day for monthly schedules (1-31) |
| `cron_expression` | Cron expression for complex schedules |
| `timezone` | Timezone for the schedule |

**Output Ports:**
- `trigger_time`: When the trigger fired (ISO format)
- `run_number`: How many times this trigger has fired
- `scheduled_time`: The originally scheduled time

**Example Use Cases:**
- Daily report generation at 8 AM
- Hourly data synchronization
- Monthly invoice processing on the 1st

**Cron Expression Examples:**
```
0 9 * * *        # 9:00 AM every day
0 9 * * 1        # 9:00 AM every Monday
0 */2 * * *      # Every 2 hours
0 9,17 * * 1-5   # 9 AM and 5 PM, Monday-Friday
```

### Webhook Trigger

Starts workflows when HTTP requests arrive at a custom endpoint.

| Property | Description |
|----------|-------------|
| `endpoint` | Custom URL path (e.g., `/my-webhook`) |
| `methods` | Accepted HTTP methods (GET, POST, PUT, etc.) |
| `auth_type` | Authentication: none, basic, header, jwt |
| `cors_enabled` | Allow cross-origin requests |
| `ip_whitelist` | Allowed IP addresses/ranges |
| `response_mode` | When to send response: immediate, wait_for_workflow |

**Output Ports:**
- `payload`: Request body (JSON parsed if applicable)
- `headers`: HTTP request headers
- `query_params`: URL query parameters
- `method`: HTTP method used
- `path`: Request path
- `client_ip`: Sender's IP address

**Example Use Cases:**
- Receive notifications from external systems
- Process form submissions
- Integrate with third-party services
- Build custom APIs

**Webhook URL Format:**
```
http://your-server:8766/webhooks/your-endpoint
http://your-server:8766/hooks/trigger_node_id
```

### File Watch Trigger

Activates when files change in a monitored directory.

| Property | Description |
|----------|-------------|
| `watch_path` | Directory to monitor |
| `patterns` | File patterns to match (e.g., `*.pdf`, `*.xlsx`) |
| `events` | Events to watch: created, modified, deleted, moved |
| `recursive` | Watch subdirectories |
| `ignore_patterns` | Patterns to ignore (e.g., `*.tmp`, `~*`) |
| `debounce_ms` | Minimum time between events for same file |

**Output Ports:**
- `file_path`: Full path to the changed file
- `file_name`: Name of the file
- `event_type`: Type of change (created/modified/deleted/moved)
- `directory`: Parent directory path
- `old_path`: Previous path (for moved events)

**Example Use Cases:**
- Process new files in an inbox folder
- Sync files when modified
- Archive files when deleted
- Log file activity

### Email Trigger

Fires when new emails arrive in a mailbox.

| Property | Description |
|----------|-------------|
| `provider` | Email service: imap, gmail, outlook |
| `server` | IMAP server address |
| `port` | Server port (993 for SSL) |
| `username` | Email account username |
| `password` | Account password or app password |
| `folder` | Mailbox folder to monitor (INBOX) |
| `filter_subject` | Regex pattern to match subjects |
| `filter_from` | Regex pattern to match senders |
| `unread_only` | Only trigger on unread emails |
| `mark_as_read` | Mark email as read after processing |
| `poll_interval_seconds` | How often to check for new emails |

**Output Ports:**
- `email`: Full email object
- `subject`: Email subject line
- `sender`: Sender's email address
- `body`: Email body (plain text)
- `html_body`: Email body (HTML)
- `attachments`: List of attachment file paths
- `received_at`: When the email was received

**Example Use Cases:**
- Process invoice emails automatically
- Route support requests
- Download and process attachments
- Send automated replies

### Messaging Triggers

#### Telegram Trigger

Responds to messages in Telegram chats or groups.

**Output Ports:**
- `message`: Message text
- `chat_id`: Chat identifier
- `user`: Sender information
- `message_type`: text, photo, document, etc.

#### WhatsApp Trigger

Responds to WhatsApp messages (via WhatsApp Business API).

**Output Ports:**
- `message`: Message text
- `phone_number`: Sender's phone number
- `message_type`: Message type
- `media_url`: URL for media messages

**Example Use Cases:**
- Build chat bots
- Process commands from users
- Automate customer support responses

### Google Triggers

#### Google Drive Trigger

Activates when files change in Google Drive.

**Output Ports:**
- `file_id`: Google Drive file ID
- `file_name`: File name
- `event_type`: created, modified, deleted
- `folder_id`: Parent folder ID

#### Google Sheets Trigger

Fires when spreadsheet data changes.

**Output Ports:**
- `spreadsheet_id`: Sheet identifier
- `sheet_name`: Name of the changed sheet
- `range`: Modified cell range
- `values`: New values

#### Google Calendar Trigger

Activates based on calendar events.

**Output Ports:**
- `event`: Calendar event details
- `event_id`: Event identifier
- `start_time`: Event start
- `end_time`: Event end

**Example Use Cases:**
- Process new files uploaded to Drive
- Sync spreadsheet changes
- Trigger actions before meetings

### Other Triggers

#### RSS Feed Trigger

Monitors RSS feeds for new items.

**Output Ports:**
- `title`: Article title
- `link`: Article URL
- `description`: Article summary
- `published_at`: Publication date

#### SSE Trigger (Server-Sent Events)

Listens to server-sent event streams.

**Output Ports:**
- `event`: Event name
- `data`: Event data
- `id`: Event ID

#### Workflow Call Trigger

Allows workflows to be called from other workflows.

**Output Ports:**
- `input_data`: Data passed from calling workflow

## Trigger Payload Output Ports

Every trigger provides event data through output ports. These ports connect to subsequent nodes:

```
[Trigger Node]
    [payload] ---------> [Process Data Node]
    [headers] ---------> [Log Headers Node]
    [exec_out] --------> [First Action Node]
```

### Accessing Trigger Data

Use the output ports directly or store in variables:

```
# Direct connection
[Email Trigger: subject] --> [If Node: condition]

# Via variable
[Email Trigger: subject] --> [Set Variable: email_subject]
```

## Configuring Triggers

### Adding a Trigger to a Workflow

1. Remove the Start node (or keep it for manual runs)
2. Drag a trigger node from the **Triggers** category
3. Configure the trigger properties
4. Connect the `exec_out` port to your first action node
5. Connect data output ports as needed

### Multiple Triggers

A workflow can have multiple triggers for different entry points:

```
[Schedule Trigger] ----+
                       +--> [Main Process] --> [End]
[Webhook Trigger]  ----+
```

Both triggers feed into the same processing logic.

### Trigger Properties Panel

Configure triggers in the Properties Panel:

1. Select the trigger node
2. Set required properties (server, path, schedule, etc.)
3. Configure optional settings (filters, authentication)
4. Test the trigger configuration

## Trigger Activation

### Manual Activation

While designing, you can test triggers:
1. Right-click the trigger node
2. Select **Test Trigger**
3. Provide sample input data
4. Workflow executes with test data

### Automatic Activation

When deployed to a Robot:
1. The Robot registers the trigger
2. Trigger listens for its specific event
3. When event occurs, trigger fires
4. Workflow executes with event data

### Enabling/Disabling Triggers

Each trigger has an `enabled` property:
- **Enabled (true)**: Trigger actively listens for events
- **Disabled (false)**: Trigger is ignored, workflow can still run manually

## Best Practices

### Trigger Design

1. **One trigger purpose per workflow**: Keep workflows focused
2. **Validate trigger data**: Check incoming data before processing
3. **Handle missing data**: Use default values for optional fields
4. **Log trigger events**: Record when and why triggers fire

### Security

1. **Use authentication**: Protect webhook endpoints
2. **Validate sources**: Check IP addresses, signatures
3. **Sanitize input**: Never trust trigger data blindly
4. **Limit permissions**: Use least-privilege credentials

### Performance

1. **Debounce file triggers**: Prevent rapid repeated fires
2. **Set appropriate polling intervals**: Balance responsiveness vs. resources
3. **Filter at the source**: Use trigger filters to reduce unnecessary executions
4. **Consider rate limits**: Some services limit API calls

### Error Handling

1. **Wrap trigger workflows in Try-Catch**: Handle processing errors
2. **Implement retry logic**: For transient failures
3. **Send notifications**: Alert on repeated failures
4. **Log extensively**: Track trigger behavior for debugging

## Example: Email Processing Workflow

```
[Email Trigger] --> [If: Subject contains "Invoice"]
     |                        |
     |                   [Yes] --> [Download Attachments]
     |                                    |
     |                              [Process Invoice]
     |                                    |
     |                              [Send Confirmation]
     |                        |
     |                   [No] --> [Archive Email]
     |
     +--> [Log: Email Received]
```

Trigger configuration:
- Provider: IMAP
- Server: imap.gmail.com
- Filter Subject: `.*Invoice.*`
- Unread Only: true
- Mark as Read: true

## Next Steps

- [Execution Modes](execution-modes.md): Understand how triggered workflows execute
- [Workflows](workflows.md): Learn about workflow structure
- [Variables](variables.md): Use trigger data in your workflow
