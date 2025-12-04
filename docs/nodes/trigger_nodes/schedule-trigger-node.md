# ScheduleTriggerNode

Schedule trigger node that fires on a time-based schedule.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.schedule_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\schedule_trigger_node.py:102`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `trigger_time` | STRING | Trigger Time |
| `run_number` | INTEGER | Run Number |
| `scheduled_time` | STRING | Scheduled Time |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `frequency` | CHOICE | `daily` | No | How often to trigger Choices: once, interval, hourly, daily, weekly, ... (7 total) |
| `time_hour` | INTEGER | `9` | No | Hour of day (for daily/weekly/monthly) |
| `time_minute` | INTEGER | `0` | No | Minute of hour |
| `interval_seconds` | INTEGER | `60` | No | Interval in seconds (for interval mode) |
| `day_of_week` | CHOICE | `mon` | No | Day of week (for weekly) Choices: mon, tue, wed, thu, fri, ... (7 total) |
| `day_of_month` | INTEGER | `1` | No | Day of month (for monthly) |
| `cron_expression` | STRING | `0 9 * * *` | No | Cron expression (minute hour day month weekday) |
| `timezone` | STRING | `UTC` | No | Timezone for schedule |
| `max_runs` | INTEGER | `0` | No | Maximum number of runs (0 = unlimited) |
| `start_time` | STRING | `` | No | When to start (for once mode) |

## Inheritance

Extends: `BaseTriggerNode`
