# Scheduling Guide

Schedule workflows to run automatically.

## Trigger Types

| Trigger | Description |
|---------|-------------|
| ScheduleTriggerNode | Run on schedule (cron) |
| WebhookTriggerNode | Run on HTTP request |
| FileWatchTriggerNode | Run on file change |
| EmailTriggerNode | Run on email received |

## Cron Expressions

Format: `minute hour day month weekday`

| Expression | Schedule |
|------------|----------|
| `0 9 * * *` | Daily at 9 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * 1-5` | Weekdays at 9 AM |
| `0 0 1 * *` | Monthly on 1st |

## Schedule Trigger

Configure ScheduleTriggerNode:

| Property | Description |
|----------|-------------|
| cron_expression | Cron schedule |
| timezone | Timezone (e.g., America/New_York) |
| enabled | Active/inactive |

## Orchestrator Integration

For distributed scheduling:

1. Deploy Robot agents
2. Configure Orchestrator
3. Assign workflows to robots
4. Monitor from dashboard

## Related Nodes

- [Trigger Nodes](../nodes/trigger_nodes/index.md)
