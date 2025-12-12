# Other Triggers

Additional trigger types for specialized use cases: RSS feeds, application events, workflow calls, error handling, forms, and server-sent events.

---

## RSS Feed Trigger {#rss-feed-trigger}

The **RSSFeedTriggerNode** monitors RSS/Atom feeds and fires when new items are published.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `RSSFeedTriggerNode` |
| Category | triggers |
| Use Case | News monitoring, content aggregation |

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| feed_url | string | `""` | URL of the RSS/Atom feed (required) |
| poll_interval_minutes | integer | `15` | How often to check for new items |
| filter_keywords | string | `""` | Comma-separated keywords to filter items |
| filter_mode | choice | `any` | Match mode: `any`, `all`, `none` |
| max_items_per_check | integer | `10` | Maximum items to process per poll |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| title | string | Item title |
| link | string | Item URL |
| description | string | Item summary/description |
| published | string | Publication date |
| author | string | Item author |
| categories | array | Item categories/tags |

### Example Use Case

Monitor a tech news feed for specific topics:

```
Feed URL: https://news.ycombinator.com/rss
Keywords: python, automation
Filter Mode: any
Poll Interval: 30 minutes
```

---

## App Event Trigger {#app-event-trigger}

The **AppEventTriggerNode** fires on application and system events like window focus, process launch, or browser events.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `AppEventTriggerNode` |
| Category | triggers |
| Use Case | Reactive automation, application monitoring |

### Configuration Properties

#### Event Source

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| event_source | choice | `windows` | Source: `windows`, `browser`, `rpa` |

#### Windows Events

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| window_event | choice | `focus` | Event: `focus`, `open`, `close`, `minimize`, `maximize` |
| window_title_pattern | string | `""` | Regex pattern for window title |
| process_name | string | `""` | Process name to match (e.g., `notepad.exe`) |

#### Browser Events

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| browser_event | choice | `tab_open` | Event: `tab_open`, `tab_close`, `url_change`, `page_load` |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| event_type | string | Type of event that fired |
| window_title | string | Window title (Windows events) |
| process_name | string | Process name |
| timestamp | string | Event timestamp |

### Example Use Case

Trigger when Excel opens:

```
Event Source: windows
Window Event: open
Process Name: EXCEL.EXE
```

---

## Workflow Call Trigger {#workflow-call-trigger}

The **WorkflowCallTriggerNode** creates a callable workflow that can be invoked from other workflows, enabling subflow patterns.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `WorkflowCallTriggerNode` |
| Category | triggers |
| Use Case | Reusable workflows, subflow patterns |

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| call_alias | string | `""` | Unique alias to call this workflow (required) |
| input_schema | json | `{}` | JSON schema for input parameters |
| output_schema | json | `{}` | JSON schema for output parameters |
| wait_for_completion | boolean | `true` | Caller waits for completion |
| timeout_seconds | integer | `300` | Maximum wait time |

### Input/Output Schema Format

Define expected parameters:

```json
{
  "invoice_id": "string",
  "amount": "number",
  "date": "string"
}
```

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| inputs | object | Input parameters passed by caller |
| caller_workflow_id | string | ID of calling workflow |
| call_id | string | Unique call identifier |

### Example Use Case

Create a reusable "Process Invoice" subflow:

```
Call Alias: process_invoice
Input Schema: {"invoice_id": "string", "vendor": "string"}
Output Schema: {"success": "boolean", "processed_amount": "number"}
```

Call from another workflow using **CallSubworkflowNode**.

---

## Error Trigger {#error-trigger}

The **ErrorTriggerNode** fires when errors occur in other workflows, enabling centralized error handling and alerting.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `ErrorTriggerNode` |
| Category | triggers |
| Use Case | Error monitoring, alerting, recovery |

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| error_types | string | `*` | Comma-separated error types (`*` for all) |
| workflow_filter | string | `""` | Workflow IDs to monitor (empty = all) |
| severity | choice | `all` | Minimum severity: `all`, `critical`, `error`, `warning` |
| error_pattern | string | `""` | Regex to match error messages |
| include_warnings | boolean | `false` | Also trigger on warnings |

### Error Types

Common error types to filter:

- `NodeExecutionError` - Node execution failures
- `TimeoutError` - Operation timeouts
- `ValidationError` - Data validation failures
- `ConnectionError` - Network/connection issues
- `BrowserError` - Browser automation errors

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| error_type | string | Type of error |
| error_message | string | Full error message |
| workflow_id | string | ID of workflow that failed |
| node_id | string | ID of node that failed |
| severity | string | Error severity level |
| stack_trace | string | Full stack trace |
| timestamp | string | Error timestamp |

### Example Use Case

Alert on critical errors:

```
Error Types: NodeExecutionError,TimeoutError
Severity: critical
Workflow Filter: production_*
```

---

## Form Trigger {#form-trigger}

The **FormTriggerNode** creates a web form that triggers the workflow when submitted.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `FormTriggerNode` |
| Category | triggers |
| Use Case | User input collection, manual triggers |

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| form_title | string | `Submit Data` | Form title displayed to users |
| form_description | string | `""` | Form description/instructions |
| form_fields | json | `[...]` | JSON array of field definitions |
| submit_button_text | string | `Submit` | Submit button label |
| success_message | string | `""` | Message shown after submission |

### Form Field Definition

Define fields in JSON:

```json
[
  {
    "name": "invoice_number",
    "type": "text",
    "label": "Invoice Number",
    "required": true
  },
  {
    "name": "amount",
    "type": "number",
    "label": "Amount",
    "required": true
  },
  {
    "name": "category",
    "type": "select",
    "label": "Category",
    "options": ["Sales", "Expenses", "Refund"]
  }
]
```

**Field Types:** `text`, `number`, `email`, `textarea`, `select`, `checkbox`, `date`, `file`

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| form_data | object | All submitted field values |
| submitter_ip | string | IP address of submitter |
| submission_time | string | Timestamp of submission |

---

## SSE Trigger {#sse-trigger}

The **SSETriggerNode** listens to Server-Sent Events streams for real-time event-driven triggers.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `SSETriggerNode` |
| Category | triggers |
| Use Case | Real-time integrations, push notifications |

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| sse_url | string | `""` | SSE endpoint URL (required) |
| event_types | string | `""` | Event types to listen for (empty = all) |
| headers | json | `{}` | Request headers (e.g., auth tokens) |
| reconnect_delay_seconds | integer | `5` | Delay before reconnecting |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| event | string | Event type name |
| data | any | Event data payload |
| id | string | Event ID (if provided) |
| timestamp | string | Received timestamp |

### Example Use Case

Listen to a real-time notification stream:

```
SSE URL: https://api.example.com/events
Event Types: notification,alert
Headers: {"Authorization": "Bearer sk_xxxx"}
```

---

## Related Documentation

- [Schedule Trigger](schedule.md)
- [Webhook Trigger](webhook.md)
- [File Watch Trigger](file-watch.md)
- [Email Triggers](email-triggers.md)
