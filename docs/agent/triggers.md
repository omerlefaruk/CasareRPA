---
description: Trigger definitions for automation
paths:
  - src/casare_rpa/triggers/**
  - src/casare_rpa/application/execution/trigger_runner.py
  - src/casare_rpa/application/orchestrator/**
  - src/casare_rpa/application/scheduling/**
  - src/casare_rpa/utils/workflow/**
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
