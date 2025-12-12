# Workflow Triggers

CasareRPA supports multiple trigger types for workflow execution.

## Trigger Types

| Type | Description | Implementation |
|------|-------------|----------------|
| `manual` | User-initiated | Canvas "Run" button |
| `scheduled` | Time-based | APScheduler + cron |
| `webhook` | HTTP callback | FastAPI endpoint |
| `file_watch` | File system events | watchdog library |
| `email` | Email arrival | IMAP polling |
| `hotkey` | Keyboard shortcut | keyboard library |

## Trigger Configuration
Triggers are defined in `domain/entities/trigger_config.py`.

## Trigger Nodes
Located in `nodes/trigger_nodes/`:
- `ManualTriggerNode`
- `ScheduleTriggerNode`
- `WebhookTriggerNode`
- `FileWatchTriggerNode`

## Adding New Triggers
1. Define trigger type in `TriggerType` enum
2. Create trigger node in `nodes/trigger_nodes/`
3. Register in trigger registry
4. Add tests in `tests/triggers/`
