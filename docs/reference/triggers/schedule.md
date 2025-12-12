# Schedule Trigger

The **ScheduleTriggerNode** fires workflows on a time-based schedule. Use it for periodic tasks like daily reports, hourly data syncs, or weekly maintenance jobs.

## Overview

| Property | Value |
|----------|-------|
| Node Type | `ScheduleTriggerNode` |
| Trigger Type | `SCHEDULED` |
| Icon | schedule |
| Category | triggers |

## Configuration Properties

### Frequency Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| frequency | choice | `daily` | Schedule type: `once`, `interval`, `hourly`, `daily`, `weekly`, `monthly`, `cron` |

### Time Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| time_hour | integer | 9 | Hour of day (0-23) for daily/weekly/monthly |
| time_minute | integer | 0 | Minute of hour (0-59) |
| interval_seconds | integer | 60 | Interval in seconds (for interval mode) |

### Weekly/Monthly Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| day_of_week | choice | `mon` | Day for weekly schedules: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun` |
| day_of_month | integer | 1 | Day of month (1-31) for monthly schedules |

### Cron Expression

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| cron_expression | string | `0 9 * * *` | Cron expression (minute hour day month weekday) |

### Advanced Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| timezone | string | `UTC` | Timezone for schedule (e.g., `America/New_York`) |
| max_runs | integer | 0 | Maximum executions (0 = unlimited) |
| start_time | string | `""` | Start time for `once` mode (ISO format) |

## Output Ports (Payload)

| Port | Type | Description |
|------|------|-------------|
| trigger_time | string | When the trigger fired (ISO format) |
| run_number | integer | How many times this trigger has fired |
| scheduled_time | string | The originally scheduled time |
| exec_out | exec | Execution flow continues |

## Cron Expression Syntax

The cron expression follows standard 5-field format:

```
 +---------------- minute (0-59)
 | +------------- hour (0-23)
 | | +---------- day of month (1-31)
 | | | +------- month (1-12)
 | | | | +---- day of week (0-6, Sunday=0)
 | | | | |
 * * * * *
```

### Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` (every minute) |
| `,` | List | `0,30 * * * *` (0 and 30 minutes) |
| `-` | Range | `0 9-17 * * *` (9am to 5pm hourly) |
| `/` | Step | `*/15 * * * *` (every 15 minutes) |

## Examples

### Every Hour

**Using frequency setting:**
```json
{
  "frequency": "hourly",
  "time_minute": 0
}
```

**Using cron:**
```json
{
  "frequency": "cron",
  "cron_expression": "0 * * * *"
}
```

### Daily at 9 AM

**Using frequency setting:**
```json
{
  "frequency": "daily",
  "time_hour": 9,
  "time_minute": 0,
  "timezone": "America/New_York"
}
```

**Using cron:**
```json
{
  "frequency": "cron",
  "cron_expression": "0 9 * * *",
  "timezone": "America/New_York"
}
```

### Weekdays Only at 8:30 AM

```json
{
  "frequency": "cron",
  "cron_expression": "30 8 * * 1-5",
  "timezone": "America/New_York"
}
```

### Every 5 Minutes

```json
{
  "frequency": "interval",
  "interval_seconds": 300
}
```

Or with cron:
```json
{
  "frequency": "cron",
  "cron_expression": "*/5 * * * *"
}
```

### First Monday of Every Month at 9 AM

```json
{
  "frequency": "cron",
  "cron_expression": "0 9 1-7 * 1",
  "timezone": "UTC"
}
```

### Once at a Specific Time

```json
{
  "frequency": "once",
  "start_time": "2024-12-25T09:00:00",
  "timezone": "America/New_York"
}
```

## Timezone Handling

The `timezone` property accepts IANA timezone identifiers:

| Region | Examples |
|--------|----------|
| Americas | `America/New_York`, `America/Los_Angeles`, `America/Chicago` |
| Europe | `Europe/London`, `Europe/Paris`, `Europe/Berlin` |
| Asia | `Asia/Tokyo`, `Asia/Singapore`, `Asia/Dubai` |
| Other | `UTC`, `Pacific/Auckland`, `Australia/Sydney` |

> **Warning:** Always specify timezone explicitly for production workflows. Default `UTC` may cause unexpected behavior during daylight saving time transitions.

## Complete Workflow Example

```python
from casare_rpa.nodes.trigger_nodes import ScheduleTriggerNode
from casare_rpa.nodes import SendEmailNode, LogNode

# Create schedule trigger for daily report at 9 AM EST
trigger = ScheduleTriggerNode(
    node_id="daily_report_trigger",
    config={
        "frequency": "daily",
        "time_hour": 9,
        "time_minute": 0,
        "timezone": "America/New_York",
        "max_runs": 0,  # Unlimited
    }
)

# Workflow structure:
# [Schedule Trigger] -> [Generate Report] -> [Send Email] -> [Log]
#       |
#       +-- trigger_time -> Used in email body
#       +-- run_number   -> Included in report title
```

## Workflow JSON Example

```json
{
  "nodes": [
    {
      "id": "trigger_1",
      "type": "ScheduleTriggerNode",
      "config": {
        "frequency": "cron",
        "cron_expression": "0 9 * * 1-5",
        "timezone": "America/New_York"
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "log_1",
      "type": "LogNode",
      "config": {
        "message": "Daily report triggered at {{trigger_time}}, run #{{run_number}}"
      },
      "position": {"x": 400, "y": 200}
    }
  ],
  "connections": [
    {
      "source_node": "trigger_1",
      "source_port": "exec_out",
      "target_node": "log_1",
      "target_port": "exec_in"
    }
  ]
}
```

## Common Use Cases

### Daily Report Generation
- **Frequency:** `daily` at 6 AM
- **Use Case:** Generate and email overnight processing summary

### Hourly Data Sync
- **Frequency:** `hourly` at minute 0
- **Use Case:** Sync data between systems every hour

### Weekly Cleanup
- **Frequency:** `weekly` on Sunday at 2 AM
- **Use Case:** Archive old files, clean temp directories

### Business Hours Monitoring
- **Cron:** `*/15 9-17 * * 1-5`
- **Use Case:** Check system health every 15 minutes during business hours

## Best Practices

1. **Use Timezones:** Always specify timezone for predictable behavior
2. **Test First:** Use `once` mode to test before deploying recurring schedules
3. **Set Max Runs:** For migrations or one-time tasks, set `max_runs` to prevent infinite loops
4. **Log Run Numbers:** Track `run_number` to identify issues with specific executions
5. **Avoid Second-Level Precision:** Cron doesn't support seconds; use `interval` mode for sub-minute schedules

## Related

- [Webhook Trigger](webhook.md) - HTTP-based workflow triggering
- [File Watch Trigger](file-watch.md) - File system event triggering
- [Trigger Overview](index.md) - All available triggers
