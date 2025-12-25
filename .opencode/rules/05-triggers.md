---
description: Trigger definitions for automation
---

# Workflow Triggers

## Trigger Types

- **Manual**: User clicks run
- **Schedule**: Cron-based execution
- **Event**: File system or external event
- **API**: HTTP webhook trigger

## Implementation

- Triggers initiate a Workflow execution via the `ExecutionOrchestrator`.
- Triggers must handle their own error logging.
