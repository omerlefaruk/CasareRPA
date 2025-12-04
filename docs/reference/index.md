# Reference

Quick lookup tables and reference materials for CasareRPA v3.1.

## Contents

| Reference | Description |
|-----------|-------------|
| [Data Types](data-types.md) | Port data types (STRING, INTEGER, BOOLEAN, etc.) |
| [Port Types](port-types.md) | Port connection types (INPUT, OUTPUT, EXEC) |
| [Error Codes](error-codes.md) | Error code reference |
| [Keyboard Shortcuts](keyboard-shortcuts.md) | Application shortcuts |

## Quick Reference

### Execution Modes

| Mode | Shortcut | Description |
|------|----------|-------------|
| **Run Local** | F8 | Execute workflow in Canvas process |
| **Run on Robot** | Ctrl+F5 | Submit to LAN robot via Orchestrator |
| **Submit** | Ctrl+Shift+F5 | Queue for internet robots |

### Debugging

| Shortcut | Action |
|----------|--------|
| F9 | Toggle breakpoint |
| F10 | Step over |
| F11 | Step into |
| Shift+F5 | Stop execution |

### Platform URLs

| Component | URL |
|-----------|-----|
| Orchestrator API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Monitoring Dashboard | http://localhost:5173 |
| Health Check | http://localhost:8000/health |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCHESTRATOR_URL` | API base URL | http://localhost:8000 |
| `DB_ENABLED` | Enable PostgreSQL | false |
| `USE_MEMORY_QUEUE` | Use in-memory queue | true |
| `WORKFLOWS_DIR` | Workflow storage | ./workflows |

## Related Resources

- [API Reference](../api/index.md) - Architecture layers
- [Node Reference](../nodes/index.md) - 405 automation nodes
- [User Guides](../guides/index.md) - Step-by-step tutorials
- [Deployment Guide](../DEPLOY.md) - Enterprise setup
