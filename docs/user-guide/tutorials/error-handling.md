# Error Handling Tutorial

Learn to build resilient workflows: use Try/Catch blocks, implement retries with backoff, and create recovery strategies for common failures.

**Time required:** 25 minutes

**What you will build:**
A robust workflow that handles API failures, browser timeouts, and data validation errors with proper logging and recovery.

## Prerequisites

- CasareRPA installed and running
- Basic workflow building experience
- Understanding of control flow nodes

## Goals

By the end of this tutorial, you will:
- Use Try/Catch/Finally blocks
- Implement retry logic with exponential backoff
- Handle specific error types differently
- Create fallback strategies
- Log errors for debugging
- Send failure notifications

---

## Understanding Error Types

### Transient Errors (Recoverable)

| Error | Cause | Recovery |
|-------|-------|----------|
| Network timeout | Slow server | Retry with backoff |
| 429 Rate Limited | Too many requests | Wait and retry |
| 500 Server Error | Server issue | Retry with backoff |
| Element not found | Timing issue | Wait and retry |
| File locked | Another process | Wait and retry |

### Permanent Errors (Non-Recoverable)

| Error | Cause | Action |
|-------|-------|--------|
| 401 Unauthorized | Bad credentials | Fail immediately |
| 404 Not Found | Resource doesn't exist | Skip or fail |
| Validation error | Bad input data | Log and skip |
| Permission denied | Access issue | Fail with alert |

---

## Part 1: Basic Try/Catch/Finally

### Step 1: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `error_handling_tutorial.json`

### Step 2: Add Start and Try Nodes

1. Drag **Start** from **Basic** to position (100, 300)
2. Drag **Try** from **Control Flow** to position (400, 300)
3. Connect: Start -> Try

### Step 3: Add Protected Code (Try Body)

Add nodes that might fail inside the try_body:

1. Drag **HTTP Request** from **HTTP**
2. Position at (700, 300)
3. Connect: Try `try_body` -> HTTP Request

| Property | Value |
|----------|-------|
| method | `GET` |
| url | `https://api.example.com/data` |
| timeout | `10000` |

### Step 4: Add Catch Block

1. Drag **Catch** from **Control Flow**
2. Position at (700, 500)

The Catch node automatically links to the Try node. When an error occurs in the try_body, execution jumps to the Catch.

### Configure Catch

| Property | Value |
|----------|-------|
| error_types | `""` (catch all errors) |

### Catch Output Ports

- `error_message` (STRING) - Error description
- `error_type` (STRING) - Error class name
- `stack_trace` (STRING) - Full stack trace

### Step 5: Handle the Error

1. Drag **Log** from **Basic**
2. Connect: Catch `catch_body` -> Log

| Property | Value |
|----------|-------|
| message | `Error occurred: {{error_type}} - {{error_message}}` |
| level | `error` |

### Step 6: Add Finally Block

The Finally block ALWAYS executes, whether or not an error occurred:

1. Drag **Finally** from **Control Flow**
2. Position at (1000, 400)

### Finally Output Ports

- `had_error` (BOOLEAN) - True if error occurred

### Step 7: Cleanup in Finally

1. Drag **Log** from **Basic**
2. Connect: Finally `finally_body` -> Log

| Property | Value |
|----------|-------|
| message | `Cleanup complete. Had error: {{had_error}}` |
| level | `info` |

### Step 8: Continue After Try/Catch

1. Drag **End** from **Basic**
2. Connect after Finally

---

## Complete Try/Catch/Finally Structure

```
[Start]
    |
[Try]
    |
  try_body
    |
[HTTP Request]  -----(error)-----> [Catch]
    |                                  |
    |                             catch_body
    |                                  |
    |                             [Log Error]
    |                                  |
    +----------------+-----------------+
                     |
                 [Finally]
                     |
                finally_body
                     |
                [Cleanup / Log]
                     |
                 [End]
```

---

## Part 2: Retry with Exponential Backoff

### Step 9: Using RetryNode

The Retry node automatically retries failed operations:

1. Drag **Retry** from **Control Flow**
2. Position at (400, 300)
3. Connect: Start -> Retry

### Configure Retry

| Property | Value | Description |
|----------|-------|-------------|
| max_attempts | `3` | Try up to 3 times |
| delay_ms | `1000` | Initial delay: 1 second |
| backoff_multiplier | `2.0` | Double delay each retry |
| max_delay_ms | `30000` | Cap at 30 seconds |

### Retry Timing Example

| Attempt | Delay Before |
|---------|--------------|
| 1 | None (immediate) |
| 2 | 1000ms (1 second) |
| 3 | 2000ms (2 seconds) |

### Step 10: Add Code to Retry

1. Drag **HTTP Request** inside the retry_body
2. Connect: Retry `retry_body` -> HTTP Request

### Step 11: Handle Success and Failure

Retry node has two exit paths:

```
[Retry]
    |
  retry_body --> [HTTP Request]
    |
+---+---+
|       |
success failure
|       |
[Process] [Alert]
```

1. Drag nodes for success path
2. Drag nodes for failure path (all retries exhausted)

### Complete Retry Pattern

```
[Start]
    |
[Retry]
    max_attempts: 3
    delay_ms: 1000
    backoff_multiplier: 2.0
        |
    retry_body
        |
    [HTTP Request]
        url: "https://api.example.com/data"
            |
    [If: status_code >= 500]  # Server error - should retry
        |
      true --> [Throw Error: "Server error"]  # Triggers retry
      false --> (continue normally)
        |
    +---+---+
    |       |
success   failure
    |       |
[Process] [Send Alert Email]
    |       subject: "API Failed after 3 attempts"
    |       |
    +---+---+
        |
    [End]
```

---

## Part 3: Handling Specific Error Types

### Catch Specific Errors

You can have multiple Catch blocks for different error types:

```
[Try]
    |
  try_body
    |
[Complex Operation]
    |
    +---(ValidationError)---> [Catch: ValidationError]
    |                              |
    |                         [Log: "Invalid data: {{error_message}}"]
    |                              |
    +---(NetworkError)------> [Catch: NetworkError]
    |                              |
    |                         [Retry Logic]
    |                              |
    +---(catch all)---------> [Catch]
                                   |
                              [Log: "Unexpected error"]
```

### Step 12: Multiple Error Handlers

Configure Catch nodes with specific error types:

**Catch 1: Validation Errors**
| Property | Value |
|----------|-------|
| error_types | `ValidationError,ValueError` |

**Catch 2: Network Errors**
| Property | Value |
|----------|-------|
| error_types | `NetworkError,TimeoutError,ConnectionError` |

**Catch 3: All Others**
| Property | Value |
|----------|-------|
| error_types | `""` |

---

## Part 4: Error Handling Patterns

### Pattern 1: Fail Fast

For critical errors, stop immediately:

```
[If: credentials_invalid]
    |
  true
    |
[Throw Error]
    error_type: "AuthenticationError"
    message: "Invalid API credentials - check configuration"
    |
# Workflow stops, error logged
```

### Pattern 2: Skip and Continue

For non-critical errors, log and continue:

```
[For Loop Start]
    items: {{records}}
        |
      body
        |
    [Try]
        |
      try_body
        |
    [Process Record]
        |
        +---(error)---> [Catch]
        |                   |
        |              [Log: "Skipping record {{id}}: {{error_message}}"]
        |              [List Append: to failed_records]
        |                   |
        +--------+---------+
                 |
    [For Loop End]
        |
    completed
        |
[Log: "Processed {{success_count}}, Failed {{failed_count}}"]
```

### Pattern 3: Fallback Strategy

Try primary method, fall back to secondary:

```
[Try]
    |
  try_body
    |
[HTTP Request: Primary API]
    url: "https://primary-api.com/data"
        |
        +---(error)---> [Catch]
        |                   |
        |              [Log: "Primary API failed, trying backup"]
        |                   |
        |              [HTTP Request: Backup API]
        |                   url: "https://backup-api.com/data"
        |                   |
        +--------+---------+
                 |
[Process Response]
```

### Pattern 4: Circuit Breaker

Prevent repeated failures from overwhelming the system:

```
[Get Variable: failure_count]
        |
[If: failure_count >= 5]
    |
  true
    |
[Get Variable: last_failure_time]
        |
[If: time_since_failure < 5_minutes]
    |
  true --> [Log: "Circuit breaker open - skipping"]
           [Return: cached_response]
    |
  false --> [Set Variable: failure_count = 0]  # Reset
            [Continue with request]
```

---

## Part 5: Browser Automation Error Handling

### Step 13: Handle Element Not Found

```
[Try]
    |
  try_body
    |
[Wait For Element]
    selector: "#submit-button"
    timeout: 10000
        |
[Click Element]
        |
        +---(TimeoutError)---> [Catch]
        |                          |
        |                     [Screenshot]
        |                          path: "C:\errors\element_not_found_{{timestamp}}.png"
        |                          |
        |                     [Log: "Element not found: #submit-button"]
        |                          |
        |                     [Try Alternative Selector]
        |                          |
        +------------+-------------+
                     |
                 [Finally]
                     |
                [Close Browser]
```

### Step 14: Handle Page Load Failures

```
[Retry]
    max_attempts: 3
        |
    retry_body
        |
    [Go To URL]
        url: "https://example.com"
        timeout: 30000
            |
    [If: page_title == ""]
        |
      true --> [Throw Error: "Page failed to load"]
        |
    success --> [Continue]
    failure --> [Log: "Site unreachable after 3 attempts"]
```

---

## Part 6: Data Validation Errors

### Step 15: Validate Before Processing

```
[Read CSV]
    file_path: "C:\data\input.csv"
        |
[Validate Data]
        |
[If: validation_errors.length > 0]
    |
  true
    |
[For Each: validation_errors]
        |
    [Log: "Validation error: {{error}}"]
        |
[Throw Error]
    error_type: "ValidationError"
    message: "Data validation failed - {{error_count}} errors"
```

### Validation Examples

```
# Check required fields
[If: record.email == "" or record.email is None]
    |
  true --> [List Append: "Missing email for record {{record.id}}"]

# Check data types
[If: typeof(record.amount) != "number"]
    |
  true --> [List Append: "Invalid amount for record {{record.id}}"]

# Check value ranges
[If: record.quantity < 0]
    |
  true --> [List Append: "Negative quantity for record {{record.id}}"]
```

---

## Part 7: Logging and Alerting

### Step 16: Structured Error Logging

```
[Create Dict]
    |
[Dict Set: timestamp]
    value: {{now}}
[Dict Set: workflow]
    value: "daily_report"
[Dict Set: error_type]
    value: {{error_type}}
[Dict Set: error_message]
    value: {{error_message}}
[Dict Set: node_id]
    value: {{current_node}}
[Dict Set: context]
    value: {{execution_context}}
        |
[Write JSON]
    file_path: "C:\logs\errors\{{today}}.json"
    append: true
```

### Step 17: Send Alert Emails

```
[If: error_severity == "critical"]
    |
  true
    |
[Send Email]
    to: "oncall@company.com"
    subject: "CRITICAL: {{workflow_name}} Failed"
    body: |
        Workflow: {{workflow_name}}
        Error: {{error_type}}
        Message: {{error_message}}
        Time: {{timestamp}}

        Stack Trace:
        {{stack_trace}}
    priority: "high"
```

### Step 18: Slack/Teams Notification

```
[HTTP Request]
    method: "POST"
    url: "{{slack_webhook_url}}"
    headers: {"Content-Type": "application/json"}
    body: {
        "text": ":red_circle: Workflow Failed",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Workflow", "value": "{{workflow_name}}"},
                {"title": "Error", "value": "{{error_message}}"},
                {"title": "Time", "value": "{{timestamp}}"}
            ]
        }]
    }
```

---

## Complete Error Handling Workflow

```
[Start]
    |
[Set Variable: start_time]
    |
[Try]
    |
  try_body
    |
[Retry]
    max_attempts: 3
        |
    retry_body
        |
    [Launch Browser]
            |
    [Go To URL]
            |
    [Wait For Element: data-table]
            |
    [Table Scraper]
            |
    [Retry End]
        |
    success
        |
    [Validate Data]
            |
    [If: valid]
        |
      true --> [Write CSV]
      false --> [Throw Error: "Validation failed"]
        |
        +---(error)---> [Catch]
        |                   |
        |              catch_body
        |                   |
        |              [Screenshot: error_{{timestamp}}.png]
        |                   |
        |              [Log Error: {{error_message}}]
        |                   |
        |              [If: is_critical]
        |                   |
        |                 true --> [Send Alert Email]
        |                   |
        +--------+---------+
                 |
             [Finally]
                 |
            finally_body
                 |
            [Close Browser]
                 |
            [Calculate Duration]
                 |
            [Log: "Workflow complete. Duration: {{duration}}s, Had error: {{had_error}}"]
                 |
            [Write Execution Log]
                 |
             [End]
```

---

## Best Practices

### 1. Always Use Finally for Cleanup

```
[Finally]
    |
[Close Browser]
[Close Database Connection]
[Release File Locks]
```

### 2. Log Context, Not Just Errors

```
# Bad
[Log: "Error occurred"]

# Good
[Log: "Failed to process order {{order_id}} for customer {{customer_id}}: {{error_message}}"]
```

### 3. Use Appropriate Retry Limits

| Operation | Max Attempts | Initial Delay |
|-----------|--------------|---------------|
| API call | 3-5 | 1-2 seconds |
| File operation | 2-3 | 500ms |
| Browser action | 2-3 | 1 second |
| Email send | 3 | 5 seconds |

### 4. Don't Retry Non-Recoverable Errors

```
[If: status_code == 401 or status_code == 403]
    |
  true --> [Throw Error: "Authentication failed - do not retry"]
```

### 5. Include Recovery Steps in Documentation

Document what to do when errors occur:

```
# Error: RATE_LIMIT_EXCEEDED
# Action: Wait 60 seconds and retry
# Escalation: If persists, contact API provider
```

---

## Node Reference

### TryNode

| Property | Type | Description |
|----------|------|-------------|
| (no properties) | - | Begins protected block |

### CatchNode

| Property | Type | Description |
|----------|------|-------------|
| error_types | STRING | Comma-separated error types to catch |

### FinallyNode

| Property | Type | Description |
|----------|------|-------------|
| (no properties) | - | Always executes |

### RetryNode

| Property | Type | Description |
|----------|------|-------------|
| max_attempts | INTEGER | Maximum retry attempts |
| delay_ms | INTEGER | Initial delay (ms) |
| backoff_multiplier | FLOAT | Delay multiplier |
| max_delay_ms | INTEGER | Maximum delay cap |

### ThrowErrorNode

| Property | Type | Description |
|----------|------|-------------|
| error_type | STRING | Error class name |
| message | STRING | Error message |

---

## Next Steps

- [Browser Automation](browser-automation.md) - Handle web automation errors
- [API Integration](api-integration.md) - Handle API failures
- [Scheduled Workflows](scheduled-workflows.md) - Error handling in scheduled jobs
- [Email Processing](email-processing.md) - Handle email errors

---

## Summary

You learned how to:
1. Use Try/Catch/Finally blocks for error handling
2. Implement retry logic with exponential backoff
3. Handle specific error types differently
4. Create fallback strategies
5. Log errors for debugging
6. Send failure notifications

Robust error handling is essential for production workflows that must handle failures gracefully and provide visibility into issues.
