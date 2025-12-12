# Production Scheduling

CasareRPA supports cron-based scheduling for automated workflow execution. This guide covers schedule configuration, time zone handling, and best practices for production deployments.

---

## Overview

Schedules are managed by the Orchestrator and trigger workflows on connected robots:

```
+----------------+     +---------------+     +------------+
| Cron Schedule  | --> | Orchestrator  | --> | Robot      |
| (Every hour)   |     | (Job Queue)   |     | (Execute)  |
+----------------+     +---------------+     +------------+
```

---

## Schedule Configuration

### Cron Expression Syntax

CasareRPA uses standard 5-field cron expressions:

```
 * * * * *
 | | | | |
 | | | | +---- Day of week (0-6, Sunday=0)
 | | | +------ Month (1-12)
 | | +-------- Day of month (1-31)
 | +---------- Hour (0-23)
 +------------ Minute (0-59)
```

### Common Examples

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Every minute | `* * * * *` | Testing only |
| Every hour | `0 * * * *` | On the hour |
| Daily at 9 AM | `0 9 * * *` | Morning job |
| Daily at 6 PM | `0 18 * * *` | End of day |
| Weekdays 9 AM | `0 9 * * 1-5` | Business days |
| Every Monday | `0 9 * * 1` | Weekly report |
| First of month | `0 9 1 * *` | Monthly job |
| Every 15 min | `*/15 * * * *` | Frequent check |
| Every 30 min business hours | `0,30 9-17 * * 1-5` | Work hours |

### Advanced Expressions

```bash
# Multiple specific hours
0 9,12,18 * * *      # 9 AM, 12 PM, 6 PM

# Range with step
*/10 9-17 * * *      # Every 10 min, 9 AM to 5 PM

# Last day of month (use day 28-31 carefully)
0 9 28-31 * *        # Runs 28th-31st (check month)

# Multiple days of week
0 9 * * 1,3,5        # Monday, Wednesday, Friday
```

---

## Creating Schedules

### Via Canvas Designer

1. Open workflow in Canvas
2. Add **ScheduleTriggerNode** as entry point
3. Configure properties:
   - **Cron Expression**: `0 9 * * *`
   - **Timezone**: `America/New_York`
   - **Description**: `Daily morning report`
4. Deploy to Orchestrator

### Via CLI

```bash
# Deploy workflow with schedule
casare-rpa orchestrator deploy workflow.json \
  --trigger schedule \
  --cron "0 9 * * *" \
  --timezone "America/New_York" \
  --name "Daily Report Schedule"

# List schedules
casare-rpa orchestrator list-schedules

# Disable schedule
casare-rpa orchestrator disable-schedule SCHED_123

# Enable schedule
casare-rpa orchestrator enable-schedule SCHED_123

# Delete schedule
casare-rpa orchestrator delete-schedule SCHED_123
```

### Via API

```python
import httpx

async def create_schedule():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/schedules",
            headers={"Authorization": "Bearer YOUR_API_KEY"},
            json={
                "workflow_id": "WF_123",
                "name": "Daily Report",
                "cron_expression": "0 9 * * *",
                "timezone": "America/New_York",
                "enabled": True,
                "description": "Generate daily sales report",
                "input_data": {
                    "report_type": "sales",
                    "format": "pdf"
                }
            }
        )
        return response.json()
```

---

## Time Zone Handling

### Supported Timezones

CasareRPA uses IANA timezone identifiers:

| Region | Examples |
|--------|----------|
| Americas | `America/New_York`, `America/Los_Angeles`, `America/Chicago` |
| Europe | `Europe/London`, `Europe/Paris`, `Europe/Berlin` |
| Asia | `Asia/Tokyo`, `Asia/Singapore`, `Asia/Dubai` |
| Other | `UTC`, `Australia/Sydney`, `Pacific/Auckland` |

### Timezone Configuration

```yaml
# Schedule with timezone
schedule:
  cron: "0 9 * * *"
  timezone: "America/New_York"
```

The cron expression is evaluated in the specified timezone. `0 9 * * *` with `America/New_York` runs at 9 AM Eastern Time, regardless of server timezone.

### Daylight Saving Time

Schedules automatically adjust for DST transitions:

- **Spring Forward**: Schedule may skip once (when clock jumps 2 AM -> 3 AM)
- **Fall Back**: Schedule may run twice (when clock repeats 1 AM - 2 AM)

For time-sensitive workflows, use UTC:

```yaml
schedule:
  cron: "0 14 * * *"  # 2 PM UTC = 9 AM EST / 10 AM EDT
  timezone: "UTC"
```

---

## Schedule Trigger Node

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `cron_expression` | string | Required | Cron expression |
| `timezone` | string | `UTC` | IANA timezone |
| `description` | string | Empty | Human-readable description |
| `enabled` | boolean | `true` | Whether schedule is active |
| `input_data` | dict | Empty | Data passed to workflow |
| `max_instances` | integer | `1` | Max concurrent runs |
| `misfire_action` | string | `run_once` | How to handle missed runs |

### Output Ports

When triggered, the ScheduleTriggerNode provides:

| Port | Type | Description |
|------|------|-------------|
| `trigger_time` | STRING | ISO timestamp of trigger |
| `run_number` | INTEGER | Sequential run counter |
| `schedule_id` | STRING | Schedule identifier |
| `cron_expression` | STRING | The cron expression |
| `timezone` | STRING | Configured timezone |
| `exec_out` | EXEC | Execution flow |

### Example Workflow

```
[Schedule Trigger]                    [Set Variable]
    |                                      |
    |-- trigger_time -------------------->  |
    |-- run_number ---------------------->  |
    |-- exec_out ----------------------->  |
                                          |
                                    [Generate Report]
                                          |
                                    [Send Email]
```

---

## Misfire Handling

When a scheduled run is missed (server downtime, overload):

### Options

| Action | Description |
|--------|-------------|
| `run_once` | Run once immediately, skip others (default) |
| `run_all` | Run all missed instances sequentially |
| `skip` | Skip all missed runs, wait for next |

### Configuration

```yaml
schedule:
  cron: "0 9 * * *"
  misfire_action: "run_once"  # Default
```

---

## Concurrency Control

### Max Instances

Prevent overlapping runs of long-running workflows:

```yaml
schedule:
  cron: "*/15 * * * *"  # Every 15 minutes
  max_instances: 1      # Only 1 concurrent run
```

If a run is still in progress when the next is scheduled:

| Strategy | Behavior |
|----------|----------|
| Queue | Queues new run (default) |
| Skip | Skips new run |
| Terminate | Stops current, starts new |

### Configuration

```python
{
    "max_instances": 1,
    "overlap_strategy": "skip"  # queue, skip, or terminate
}
```

---

## Monitoring Schedules

### Dashboard View

Access schedule monitoring at:

```
http://localhost:8000/dashboard/schedules
```

### API Queries

```bash
# List all schedules
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/v1/schedules

# Get schedule details
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/v1/schedules/SCHED_123

# Get schedule run history
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/v1/schedules/SCHED_123/runs
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Schedule-specific metrics
casare_schedules_total{status="active"} 15
casare_schedules_total{status="disabled"} 3
casare_schedule_runs_total{schedule="daily_report",status="success"} 120
casare_schedule_runs_total{schedule="daily_report",status="failed"} 2
casare_schedule_next_run_seconds{schedule="daily_report"} 3600
```

---

## Alerting

### Schedule Failure Alerts

Configure alerts for:

- Schedule failures
- Missed runs
- Long-running executions

```yaml
# Alert configuration
alerts:
  schedule_failure:
    enabled: true
    channels:
      - email
      - slack

  missed_run:
    enabled: true
    threshold_minutes: 60  # Alert if >1 hour late

  long_running:
    enabled: true
    threshold_minutes: 120  # Alert if running >2 hours
```

---

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
name: "Daily Sales Report - 9 AM EST"
description: "Generates sales summary, sends to finance team"

# Bad
name: "Schedule 1"
```

### 2. Stagger Schedules

Avoid resource contention by staggering start times:

```bash
# Instead of all at :00
0 9 * * *    # Report A
0 9 * * *    # Report B
0 9 * * *    # Report C

# Stagger by 5 minutes
0 9 * * *    # Report A
5 9 * * *    # Report B
10 9 * * *   # Report C
```

### 3. Set Appropriate Timeouts

```yaml
schedule:
  cron: "0 9 * * *"
  job_timeout: 1800  # 30 minutes max
```

### 4. Use Business-Appropriate Timezones

```yaml
# For US business reports
schedule:
  cron: "0 9 * * 1-5"
  timezone: "America/New_York"
  description: "Weekday report for East Coast team"
```

### 5. Monitor and Maintain

- Review schedule run history weekly
- Adjust cron expressions based on actual usage
- Disable unused schedules
- Set up alerts for failures

---

## Troubleshooting

### Schedule Not Running

1. Check schedule is enabled:
   ```bash
   casare-rpa orchestrator get-schedule SCHED_123
   ```

2. Verify cron expression:
   ```bash
   # Test expression (shows next 5 runs)
   casare-rpa orchestrator test-cron "0 9 * * *" --timezone "UTC"
   ```

3. Check orchestrator logs:
   ```bash
   tail -f /var/log/casare-rpa/orchestrator.log | grep schedule
   ```

### Wrong Execution Time

- Verify timezone is correct
- Check DST transitions
- Confirm server time is synchronized (NTP)

### Overlapping Runs

- Reduce schedule frequency
- Set `max_instances: 1`
- Configure `overlap_strategy: skip`

---

## Related Documentation

- [Robot Setup](robot-setup.md) - Execution agents
- [Orchestrator Setup](orchestrator-setup.md) - Server configuration
- [Schedule Trigger Reference](../../reference/triggers/schedule.md) - Trigger node details
- [Monitoring](monitoring.md) - Metrics and alerting
