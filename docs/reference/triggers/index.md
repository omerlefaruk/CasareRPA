# Triggers Reference

Triggers are workflow entry points that start automation when specific events occur. Unlike executable nodes that process data within a workflow, triggers listen for external events and initiate workflow execution.

## What Are Triggers?

Triggers are special nodes that:

- **Have no exec_in port** - They START workflows, they don't receive execution flow
- **Have exec_out port** - To continue flow after the trigger fires
- **Output payload data** - Each trigger type provides event-specific data via output ports
- **Run in the background** - They listen for events while the Orchestrator or Robot is running

## Trigger vs Executable Nodes

| Aspect | Trigger Node | Executable Node |
|--------|-------------|-----------------|
| Purpose | Starts workflow | Processes data |
| exec_in port | None | Yes |
| exec_out port | Yes | Yes |
| Placement | Beginning of workflow | Anywhere in workflow |
| Execution | Event-driven | Sequential |

## How Triggers Start Workflows

1. **Trigger Registration**: When a workflow with a trigger is deployed, the trigger registers with the system
2. **Event Listening**: The trigger monitors for its specific event type (HTTP request, file change, schedule, etc.)
3. **Event Detection**: When an event occurs that matches the trigger's filters, it fires
4. **Payload Population**: The trigger populates its output ports with event data
5. **Workflow Execution**: The workflow begins executing from the trigger node

## Trigger Payload Ports

Every trigger has output ports that provide event-specific data. These ports are automatically populated when the trigger fires:

```
[Webhook Trigger]
    |-- payload (dict)      -> Request body
    |-- headers (dict)      -> HTTP headers
    |-- method (string)     -> HTTP method
    |-- path (string)       -> Request path
    |-- exec_out            -> Flow continues
```

Access payload data by connecting these ports to subsequent nodes:

```python
# In a subsequent node
request_body = inputs["payload"]  # Data from webhook trigger
sender_email = inputs["sender"]   # Data from email trigger
```

## Trigger Categories

### Time-Based Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [ScheduleTriggerNode](schedule.md) | Cron/interval schedules | Daily reports, periodic cleanup |

### HTTP Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [WebhookTriggerNode](webhook.md) | HTTP webhook endpoint | API integrations, external notifications |
| [FormTriggerNode](other-triggers.md#form-trigger) | Web form submission | User data collection |

### File System Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [FileWatchTriggerNode](file-watch.md) | File/folder changes | Invoice processing, document workflows |

### Email Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [EmailTriggerNode](email-triggers.md) | IMAP email polling | Generic email automation |
| [GmailTriggerNode](email-triggers.md#gmail-trigger) | Gmail API integration | Gmail-specific workflows |

### Messaging Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [TelegramTriggerNode](messaging-triggers.md#telegram-trigger) | Telegram bot messages | Bot commands, chat automation |
| [WhatsAppTriggerNode](messaging-triggers.md#whatsapp-trigger) | WhatsApp Cloud API | Customer communication |

### Google Workspace Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [DriveTriggerNode](google-triggers.md#drive-trigger) | Google Drive file changes | Document workflows |
| [SheetsTriggerNode](google-triggers.md#sheets-trigger) | Google Sheets changes | Data entry automation |
| [CalendarTriggerNode](google-triggers.md#calendar-trigger) | Calendar events | Meeting reminders, scheduling |

### Other Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| [WorkflowCallTriggerNode](other-triggers.md#workflow-call-trigger) | Sub-workflow invocation | Modular workflow design |
| [RSSFeedTriggerNode](other-triggers.md#rss-feed-trigger) | RSS/Atom feed updates | Content monitoring |
| [AppEventTriggerNode](other-triggers.md#app-event-trigger) | Application events | Internal event handling |
| [ErrorTriggerNode](other-triggers.md#error-trigger) | Error handling | Global error recovery |
| [FormTriggerNode](other-triggers.md#form-trigger) | Web form submission | User data collection |
| [SSETriggerNode](other-triggers.md#sse-trigger) | Server-Sent Events | Real-time integrations |

## Common Properties

All triggers share these base properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| enabled | boolean | true | Whether trigger is active |
| priority | integer | 1 | Execution priority (higher = first) |
| cooldown_seconds | integer | 0 | Minimum time between triggers |
| description | string | "" | Human-readable description |

## Example: Basic Trigger Workflow

```
[Schedule Trigger]                    [Send Email Node]
    |-- trigger_time (string)  -->        |
    |-- run_number (int)                  |
    |-- exec_out -----------------------> |
```

This workflow sends an email every time the schedule trigger fires, with access to when it was triggered and how many times it has run.

## Trigger Deployment

Triggers can be deployed in multiple modes:

### 1. Canvas (Development)
Manual testing by clicking "Run" in the designer. Webhook triggers get temporary URLs.

### 2. Robot (Single Machine)
Triggers are active while the Robot process is running:
```bash
casare-rpa robot start --workflow my_workflow.json
```

### 3. Orchestrator (Production)
Centralized trigger management with high availability:
```bash
casare-rpa orchestrator deploy my_workflow.json
```

## Best Practices

1. **Filter Early**: Use trigger-level filters to avoid unnecessary workflow executions
2. **Use Cooldowns**: Prevent trigger storms with appropriate cooldown settings
3. **Handle Payloads**: Always validate trigger payload data before processing
4. **Monitor Triggers**: Enable logging to track trigger activity
5. **Test Thoroughly**: Use Canvas mode to test triggers before deployment

## Related Documentation

- [Node Development](../nodes/index.md) - Creating custom nodes
- [Workflow Execution](../../guides/execution.md) - Understanding execution flow
- [Orchestrator API](../../api/orchestrator.md) - Deploying workflows
