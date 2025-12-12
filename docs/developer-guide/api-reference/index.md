# API Reference

Complete reference documentation for CasareRPA's programmatic interfaces.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Orchestrator REST API](orchestrator-rest.md) | HTTP endpoints for workflow management |
| [Orchestrator WebSocket](orchestrator-websocket.md) | Real-time execution updates |
| [Event Bus API](event-bus.md) | Domain event subscription and publishing |

---

## API Overview

### Orchestrator REST API

The Orchestrator provides a REST API for managing workflows, jobs, and robots:

```
Base URL: http://localhost:8000/api/v1
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows` | GET | List all workflows |
| `/workflows/{id}` | GET | Get workflow details |
| `/workflows` | POST | Create workflow |
| `/jobs` | GET | List execution jobs |
| `/jobs` | POST | Submit new job |
| `/jobs/{id}` | GET | Get job status |
| `/robots` | GET | List registered robots |

**Example: Submit a Job**

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "workflow_id": "my-workflow",
    "input_data": {"param": "value"}
  }'
```

### WebSocket API

Real-time execution updates via WebSocket:

```
WebSocket URL: ws://localhost:8000/ws/jobs/{job_id}
```

**Message Types:**
- `job.started` - Job execution began
- `node.started` - Node execution started
- `node.completed` - Node execution completed
- `job.completed` - Job finished successfully
- `job.failed` - Job execution failed

### Event Bus API

Subscribe to typed domain events in code:

```python
from casare_rpa.domain.events import get_event_bus, NodeCompleted

bus = get_event_bus()

@bus.subscribe(NodeCompleted)
def on_node_completed(event: NodeCompleted):
    print(f"Node {event.node_id} completed in {event.execution_time_ms}ms")
```

---

## Authentication

### API Key Authentication

```python
headers = {
    "Authorization": "Bearer sk_live_xxxxxxxxxxxx"
}
```

### Robot Authentication

Robots authenticate using robot-specific API keys:

```bash
casare-rpa agent --api-key robot_xxxxxxxxxxxx
```

---

## Quick Navigation

| Need | Document |
|------|----------|
| Manage workflows via HTTP | [REST API](orchestrator-rest.md) |
| Get real-time updates | [WebSocket API](orchestrator-websocket.md) |
| Subscribe to events | [Event Bus](event-bus.md) |

---

## Related Documentation

- [Orchestrator Setup](../../user-guide/deployment/orchestrator-setup.md)
- [Security Architecture](../../security/architecture.md)
- [Authentication](../../security/authentication.md)
