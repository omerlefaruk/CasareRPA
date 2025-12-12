# Scheduled Workflows Tutorial

Learn to automate time-based tasks: create cron schedules, run daily reports, and manage scheduled workflow executions.

**Time required:** 20 minutes

**What you will build:**
A daily report workflow that runs automatically at 9 AM, fetches data, generates a summary, and sends email notifications.

## Prerequisites

- CasareRPA installed and running
- Understanding of cron expressions
- Email configured for notifications

## Goals

By the end of this tutorial, you will:
- Create schedule triggers with various frequencies
- Use cron expressions for complex schedules
- Handle timezone considerations
- Implement daily, weekly, and monthly schedules
- Monitor scheduled workflow executions

---

## Understanding Schedule Triggers

Schedule triggers start workflows automatically based on time. CasareRPA supports:

| Frequency | Use Case |
|-----------|----------|
| `once` | One-time execution at specific time |
| `interval` | Every N seconds/minutes |
| `hourly` | Every hour at specific minute |
| `daily` | Every day at specific time |
| `weekly` | Specific day and time each week |
| `monthly` | Specific day of month |
| `cron` | Complex schedules using cron syntax |

---

## Part 1: Create a Daily Report Workflow

### Step 1: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `daily_report_workflow.json`

### Step 2: Add Schedule Trigger

Instead of a Start node, use a Schedule Trigger:

1. Drag **Schedule Trigger** from **Triggers** category
2. Position at (100, 300)

### Configure Schedule Trigger (Daily at 9 AM)

| Property | Value |
|----------|-------|
| frequency | `daily` |
| time_hour | `9` |
| time_minute | `0` |
| timezone | `America/New_York` |
| max_runs | `0` (unlimited) |

### Output Ports

- `trigger_time` (STRING) - When trigger fired (ISO format)
- `run_number` (INTEGER) - Execution count
- `scheduled_time` (STRING) - Originally scheduled time
- `exec_out` (EXEC) - Continue workflow

---

### Step 3: Log Trigger Information

1. Drag **Log** from **Basic**
2. Position at (400, 300)
3. Connect: Schedule Trigger `exec_out` -> Log

| Property | Value |
|----------|-------|
| message | `Daily report triggered at {{trigger_time}}, run #{{run_number}}` |
| level | `info` |

---

### Step 4: Fetch Report Data

1. Drag **Read Google Sheet** (or **Read CSV**) from data sources
2. Position at (700, 300)

Example configuration:

| Property | Value |
|----------|-------|
| spreadsheet_id | `{{env.REPORT_SHEET_ID}}` |
| range | `Sales!A:E` |

---

### Step 5: Process and Calculate Summary

1. Drag **List Reduce** to calculate totals
2. Drag **Format String** for report body

```
[List Reduce]
    operation: "sum"
    key_path: "revenue"
        |
        +---> total_revenue

[List Reduce]
    operation: "count"
        |
        +---> order_count

[Format String]
    template: |
        Daily Sales Report
        Date: {date}

        Summary:
        - Total Orders: {order_count}
        - Total Revenue: ${total_revenue}
        - Average Order: ${average}

        Generated at: {timestamp}
    variables: {{summary_dict}}
        |
        +---> report_body
```

---

### Step 6: Send Email Notification

1. Drag **Send Email** from **Email**
2. Position near the end

| Property | Value |
|----------|-------|
| to_email | `{{env.REPORT_RECIPIENTS}}` |
| subject | `Daily Sales Report - {{today}}` |
| body | `{{report_body}}` |
| is_html | `false` |

---

### Step 7: Add End Node

1. Drag **End** from **Basic**
2. Connect: Send Email -> End

---

## Complete Daily Report Workflow

```
[Schedule Trigger]
    frequency: "daily"
    time_hour: 9
    time_minute: 0
    timezone: "America/New_York"
        |
[Log: "Daily report triggered..."]
        |
[Read Google Sheet: Sales Data]
        |
[List Filter: Today's Data]
        |
[List Reduce: sum revenue] --> total_revenue
[List Reduce: count] --> order_count
        |
[Math Operation: average]
        |
[Format String: Report Body]
        |
[Send Email]
    to: "team@company.com"
    subject: "Daily Sales Report - {{today}}"
        |
[Log: "Report sent successfully"]
        |
[End]
```

---

## Part 2: Cron Expression Schedules

### Cron Syntax

```
 +---------------- minute (0-59)
 |  +------------- hour (0-23)
 |  |  +---------- day of month (1-31)
 |  |  |  +------- month (1-12)
 |  |  |  |  +---- day of week (0-6, Sunday=0)
 |  |  |  |  |
 *  *  *  *  *
```

### Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` (every minute) |
| `,` | List | `0,30 * * * *` (0 and 30 minutes) |
| `-` | Range | `0 9-17 * * *` (9 AM to 5 PM hourly) |
| `/` | Step | `*/15 * * * *` (every 15 minutes) |

### Common Cron Examples

| Schedule | Cron Expression |
|----------|-----------------|
| Every minute | `* * * * *` |
| Every 5 minutes | `*/5 * * * *` |
| Every hour | `0 * * * *` |
| Daily at midnight | `0 0 * * *` |
| Daily at 9 AM | `0 9 * * *` |
| Weekdays at 8:30 AM | `30 8 * * 1-5` |
| Every Monday at 9 AM | `0 9 * * 1` |
| First day of month at 6 AM | `0 6 1 * *` |
| Every quarter (Jan, Apr, Jul, Oct) | `0 9 1 1,4,7,10 *` |

---

## Part 3: Different Schedule Frequencies

### Interval Schedule (Every 5 Minutes)

```
[Schedule Trigger]
    frequency: "interval"
    interval_seconds: 300  # 5 minutes
```

Use for:
- Health checks
- Data polling
- Queue processing

### Hourly Schedule

```
[Schedule Trigger]
    frequency: "hourly"
    time_minute: 0  # On the hour
```

Use for:
- Hourly data syncs
- Regular API polling
- Log aggregation

### Weekly Schedule

```
[Schedule Trigger]
    frequency: "weekly"
    day_of_week: "mon"  # Monday
    time_hour: 9
    time_minute: 0
    timezone: "America/New_York"
```

Use for:
- Weekly reports
- Backup jobs
- Maintenance tasks

### Monthly Schedule

```
[Schedule Trigger]
    frequency: "monthly"
    day_of_month: 1  # First day
    time_hour: 6
    time_minute: 0
    timezone: "America/New_York"
```

Use for:
- Monthly reports
- Invoice generation
- Account reconciliation

### One-Time Schedule

```
[Schedule Trigger]
    frequency: "once"
    start_time: "2025-12-31T23:59:00"
    timezone: "America/New_York"
```

Use for:
- Migrations
- One-time data loads
- Scheduled deployments

---

## Part 4: Business Hours Monitoring

### Weekdays 9 AM to 5 PM, Every 15 Minutes

```
[Schedule Trigger]
    frequency: "cron"
    cron_expression: "*/15 9-17 * * 1-5"
    timezone: "America/New_York"
```

This runs:
- Every 15 minutes (0, 15, 30, 45)
- Between 9 AM and 5 PM
- Monday through Friday only

### Workflow: System Health Check

```
[Schedule Trigger]
    cron_expression: "*/15 9-17 * * 1-5"
        |
[HTTP Request: Health Endpoint]
    url: "https://api.company.com/health"
        |
[If: status_code != 200]
    |
  true
    |
[Send Email: Alert]
    to: "oncall@company.com"
    subject: "ALERT: System Health Check Failed"
    body: "Status: {{status_code}}\nResponse: {{response_body}}"
    priority: "high"
```

---

## Part 5: Timezone Handling

### Common Timezones

| Region | Timezone ID |
|--------|-------------|
| US Eastern | `America/New_York` |
| US Pacific | `America/Los_Angeles` |
| US Central | `America/Chicago` |
| UK | `Europe/London` |
| Central Europe | `Europe/Paris` |
| Japan | `Asia/Tokyo` |
| Australia | `Australia/Sydney` |
| UTC | `UTC` |

### Multi-Timezone Reports

For global teams, send reports at local times:

```
# US Report at 9 AM EST
[Schedule Trigger]
    cron_expression: "0 9 * * 1-5"
    timezone: "America/New_York"
    --> [US Report Workflow]

# EU Report at 9 AM CET
[Schedule Trigger]
    cron_expression: "0 9 * * 1-5"
    timezone: "Europe/Paris"
    --> [EU Report Workflow]
```

---

## Part 6: Managing Scheduled Workflows

### Limiting Executions

Set `max_runs` to limit total executions:

```
[Schedule Trigger]
    frequency: "daily"
    max_runs: 30  # Run for 30 days only
```

### Tracking Run Numbers

Use `run_number` in your workflow:

```
[Log]
    message: "Execution #{{run_number}} started at {{trigger_time}}"

[If: run_number == 1]
    |
  true
    |
[Log: "First execution - performing initial setup"]
```

---

## Part 7: Complete Examples

### Example 1: Daily Backup at 2 AM

```
[Schedule Trigger]
    frequency: "daily"
    time_hour: 2
    time_minute: 0
    timezone: "UTC"
        |
[Log: "Starting daily backup"]
        |
[Read Directory: Source Files]
    path: "C:\data"
        |
[For Loop: Each File]
        |
    [Copy File]
        destination: "D:\backups\{{today}}\{{filename}}"
        |
[List Reduce: count]
        |
[Send Email]
    subject: "Backup Complete - {{file_count}} files"
        |
[Log: "Backup completed"]
        |
[End]
```

### Example 2: Weekly Cleanup (Sunday 3 AM)

```
[Schedule Trigger]
    frequency: "weekly"
    day_of_week: "sun"
    time_hour: 3
    timezone: "America/New_York"
        |
[Log: "Starting weekly cleanup"]
        |
[List Directory]
    path: "C:\temp"
    pattern: "*.log"
        |
[For Loop: Each File]
        |
    [Get File Info]
            |
    [If: modified_date < 7_days_ago]
        |
      true
        |
    [Delete File]
            |
[Log: "Cleanup complete - deleted {{deleted_count}} files"]
        |
[End]
```

### Example 3: Monthly Invoice Generation

```
[Schedule Trigger]
    frequency: "monthly"
    day_of_month: 1
    time_hour: 6
    timezone: "America/New_York"
        |
[Log: "Generating monthly invoices for {{previous_month}}"]
        |
[Read Database: Unbilled Items]
    query: "SELECT * FROM orders WHERE billed = false AND month = {{previous_month}}"
        |
[For Loop: Each Customer]
        |
    [Generate Invoice PDF]
            |
    [Send Email: Invoice]
            |
    [Update Database: Mark as Billed]
            |
[Log: "Generated {{invoice_count}} invoices"]
        |
[End]
```

---

## Monitoring and Troubleshooting

### Execution History

CasareRPA logs all scheduled executions:

```
[INFO] 2025-01-15 09:00:00 - Schedule trigger fired: daily_report_workflow
[INFO] 2025-01-15 09:00:01 - Workflow started, run #45
[INFO] 2025-01-15 09:00:15 - Workflow completed successfully
```

### Handling Missed Executions

If the system is down during scheduled time:
- Execution is skipped (not queued)
- Next execution runs at normal time

For critical jobs, add monitoring:

```
[Schedule Trigger: Monitoring]
    cron_expression: "*/5 * * * *"  # Every 5 minutes
        |
[Check Last Execution Time]
        |
[If: last_run > 2_hours_ago]
    |
  true
    |
[Send Alert: "Scheduled job may have missed executions"]
```

### Debugging Schedules

1. Check timezone settings
2. Verify cron expression with online tools
3. Test with short intervals first
4. Review execution logs

---

## Best Practices

### 1. Always Set Timezone

```
# Always explicit:
timezone: "America/New_York"

# Avoid implicit UTC:
timezone: ""  # Don't do this
```

### 2. Use Appropriate Intervals

| Task Type | Recommended Interval |
|-----------|---------------------|
| Critical monitoring | 1-5 minutes |
| Data sync | 15-60 minutes |
| Reports | Daily/Weekly |
| Cleanup | Weekly |
| Archival | Monthly |

### 3. Stagger Multiple Schedules

Don't run all jobs at the same time:

```
# Bad: All at midnight
0 0 * * *  Job 1
0 0 * * *  Job 2
0 0 * * *  Job 3

# Good: Staggered
0 0 * * *   Job 1
15 0 * * *  Job 2
30 0 * * *  Job 3
```

### 4. Add Timeout Protection

Prevent runaway executions:

```
[Schedule Trigger]
        |
[Set Variable: start_time]
        |
[Main Workflow Logic]
        |
[If: elapsed > 30_minutes]
    |
  true
    |
[Log: "Execution timeout - aborting"]
[Throw Error: "Timeout"]
```

### 5. Send Failure Notifications

```
[Try]
    |
  try_body
    |
[Scheduled Job Logic]
    |
    +---(error)---> [Catch]
    |                   |
    |              [Send Email: Failure Alert]
    |                   to: "oncall@company.com"
    |                   subject: "FAILED: {{workflow_name}} - {{error_message}}"
```

---

## Node Reference

### ScheduleTriggerNode

| Property | Type | Description |
|----------|------|-------------|
| frequency | CHOICE | once/interval/hourly/daily/weekly/monthly/cron |
| time_hour | INTEGER | Hour (0-23) |
| time_minute | INTEGER | Minute (0-59) |
| interval_seconds | INTEGER | Interval in seconds |
| day_of_week | CHOICE | mon/tue/wed/thu/fri/sat/sun |
| day_of_month | INTEGER | Day of month (1-31) |
| cron_expression | STRING | Cron expression |
| timezone | STRING | IANA timezone ID |
| max_runs | INTEGER | Max executions (0=unlimited) |
| start_time | STRING | ISO datetime for `once` mode |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| trigger_time | STRING | When trigger fired |
| run_number | INTEGER | Execution count |
| scheduled_time | STRING | Originally scheduled time |
| exec_out | EXEC | Continue workflow |

---

## Next Steps

- [Error Handling](error-handling.md) - Handle failures in scheduled jobs
- [Email Processing](email-processing.md) - Send scheduled reports
- [Data Processing](data-processing.md) - Process data in scheduled pipelines
- [API Integration](api-integration.md) - Scheduled API polling

---

## Summary

You learned how to:
1. Create schedule triggers with various frequencies
2. Use cron expressions for complex schedules
3. Handle timezone considerations
4. Implement daily, weekly, and monthly automations
5. Monitor and troubleshoot scheduled executions

Scheduled workflows enable hands-off automation for reporting, monitoring, maintenance, and data processing tasks.
