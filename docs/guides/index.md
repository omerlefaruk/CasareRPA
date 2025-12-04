# User Guides

Step-by-step tutorials for common automation tasks with CasareRPA v3.1.

## Automation Guides

| Guide | Description | Key Nodes |
|-------|-------------|-----------|
| [Browser Automation](browser-automation.md) | Web automation with Playwright | 6 nodes |
| [Desktop Automation](desktop-automation.md) | Windows desktop automation | 48 nodes |
| [Data Processing](data-processing.md) | CSV, JSON, Excel operations | 44+ nodes |
| [Google Integration](google-integration.md) | Google Workspace APIs | 116 nodes |
| [Error Handling](error-handling.md) | Resilient workflow patterns | 37 nodes |
| [Scheduling](scheduling.md) | Cron-based execution | APScheduler |
| [Deployment](deployment.md) | Enterprise deployment | PostgreSQL, Docker |

## Platform Architecture

```
Canvas → POST /api/v1/workflows → Orchestrator → PgQueuer → Robot
                                       ↓
                              Monitoring Dashboard
```

## Quick Tips

### Browser Automation
- Use headless mode for production (`headless=true`)
- Set appropriate timeouts (default: 30s)
- Handle dynamic content with `WaitForSelector`
- Use Playwright's auto-wait features

### Desktop Automation
- Use unique UIAutomation selectors
- Handle window focus with `FocusWindow`
- Test on target machine configuration
- Use `FindControl` with multiple strategies

### Error Handling
- Wrap risky operations with `Try/Catch`
- Use `Retry` nodes for transient failures
- Log errors with `LogError` for debugging
- Implement `WebhookNotify` for alerts

### Distributed Execution
- **Local (F8)**: Quick testing in Canvas
- **Robot (Ctrl+F5)**: LAN robot execution
- **Submit (Ctrl+Shift+F5)**: Queue for remote robots

## Execution Monitoring

Monitor workflows in real-time:

1. **Dashboard**: http://localhost:5173
2. **API Docs**: http://localhost:8000/docs
3. **Analytics**: Bottleneck detection, execution timeline

## Related Resources

- [Node Reference](../nodes/index.md) - 405 automation nodes
- [API Reference](../api/index.md) - Architecture layers
- [Orchestrator API](../api/infrastructure/orchestrator-api.md) - REST endpoints
- [Deployment Guide](../DEPLOY.md) - Enterprise setup
