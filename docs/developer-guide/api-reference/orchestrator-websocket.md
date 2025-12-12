# Orchestrator WebSocket API Reference

Real-time event streaming via WebSocket for live monitoring of jobs, robots, and queue metrics.

## Connection

### Base URL

```
ws://localhost:8000/api/v1/ws
```

For production with TLS:
```
wss://orchestrator.your-domain.com/api/v1/ws
```

### Authentication

WebSocket connections require authentication via query parameter (cannot use HTTP headers for WebSocket upgrades):

**JWT Token:**
```
ws://localhost:8000/api/v1/ws/live-jobs?token=eyJhbGciOiJIUzI1NiIs...
```

**Robot API Key:**
```
ws://localhost:8000/api/v1/ws/robot-status?token=crpa_your_api_key_here
```

> **Note:** In development mode (`JWT_DEV_MODE=true`), unauthenticated connections are allowed.

### Connection Lifecycle

1. Client sends WebSocket upgrade request with token
2. Server validates token (JWT or API key)
3. On success: connection accepted, client added to broadcast group
4. On failure: connection closed with code 4001

**Close Codes:**
- `4001` - Authentication required or failed
- `1000` - Normal closure
- `1001` - Going away (server shutdown)

---

## Available Endpoints

### /ws/live-jobs

Real-time job status updates as jobs transition through states.

**URL:** `ws://host:8000/api/v1/ws/live-jobs?token=<token>`

**Events Received:**

```json
{
  "job_id": "job-12345",
  "status": "completed",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Status Values:**
- `pending` - Job queued, waiting for robot
- `claimed` - Robot picked up the job
- `running` - Job executing
- `completed` - Job finished successfully
- `failed` - Job encountered error
- `cancelled` - Job was cancelled

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/live-jobs?token=' + accessToken);

ws.onopen = () => {
  console.log('Connected to live jobs stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Job ${data.job_id}: ${data.status}`);
  updateJobStatus(data.job_id, data.status);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log(`Connection closed: ${event.code} - ${event.reason}`);
  // Implement reconnection logic
};

// Keep-alive ping (optional, server sends pings)
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

**Python Example:**
```python
import asyncio
import websockets
import json

async def listen_to_jobs(token: str) -> None:
    """Listen to real-time job status updates."""
    uri = f"ws://localhost:8000/api/v1/ws/live-jobs?token={token}"

    async with websockets.connect(uri) as websocket:
        print("Connected to live jobs stream")

        # Start ping task
        async def ping():
            while True:
                await asyncio.sleep(30)
                await websocket.send("ping")

        ping_task = asyncio.create_task(ping())

        try:
            async for message in websocket:
                if message == "pong":
                    continue

                data = json.loads(message)
                print(f"Job {data['job_id']}: {data['status']}")

                if data["status"] == "completed":
                    # Handle job completion
                    pass
                elif data["status"] == "failed":
                    # Handle job failure
                    pass
        finally:
            ping_task.cancel()

# Run the listener
asyncio.run(listen_to_jobs(access_token))
```

---

### /ws/robot-status

Real-time robot heartbeat and status stream.

**URL:** `ws://host:8000/api/v1/ws/robot-status?token=<token>`

**Events Received:**

```json
{
  "robot_id": "robot-prod-001",
  "status": "busy",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Status Values:**
- `idle` - Robot available for jobs
- `busy` - Robot executing job(s)
- `offline` - Robot disconnected
- `error` - Robot in error state
- `maintenance` - Robot in maintenance mode

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/robot-status?token=' + accessToken);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Update robot status indicator
  updateRobotCard(data.robot_id, {
    status: data.status,
    cpu: data.cpu_percent,
    memory: data.memory_mb,
    lastSeen: data.timestamp
  });

  // Alert if robot goes offline
  if (data.status === 'offline') {
    showAlert(`Robot ${data.robot_id} went offline`);
  }
};
```

---

### /ws/queue-metrics

Real-time queue depth updates.

**URL:** `ws://host:8000/api/v1/ws/queue-metrics?token=<token>`

**Events Received:**

```json
{
  "depth": 42,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Initial Message:** Upon connection, the current queue depth is sent immediately.

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/queue-metrics?token=' + accessToken);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateQueueDepthChart(data.depth, data.timestamp);

  // Alert if queue is backing up
  if (data.depth > 100) {
    showWarning(`High queue depth: ${data.depth} jobs pending`);
  }
};
```

---

### /ws/metrics/stream

Comprehensive metrics streaming with configurable interval.

**URL:** `ws://host:8000/api/v1/ws/metrics/stream?token=<token>&interval=5&environment=production`

**Query Parameters:**
- `interval`: Update frequency in seconds (1-60, default: 5)
- `environment`: Environment name for metrics labels (default: `development`)

**Events Received:**

```json
{
  "type": "metrics",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "robots": {
      "total": 10,
      "active": 8,
      "idle": 5,
      "busy": 3,
      "offline": 2
    },
    "jobs": {
      "pending": 15,
      "running": 3,
      "completed_today": 125,
      "failed_today": 5
    },
    "queue": {
      "depth": 15,
      "avg_wait_time_ms": 5000
    },
    "system": {
      "uptime_seconds": 86400,
      "version": "1.0.0"
    }
  }
}
```

**JavaScript Example:**
```javascript
class MetricsStreamClient {
  constructor(token, interval = 5, environment = 'development') {
    this.token = token;
    this.interval = interval;
    this.environment = environment;
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    const url = `ws://localhost:8000/api/v1/ws/metrics/stream?` +
      `token=${this.token}&interval=${this.interval}&environment=${this.environment}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('Metrics stream connected');
      this.reconnectDelay = 1000; // Reset on successful connect
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'metrics') {
        this.handleMetrics(message.data, message.timestamp);
      }
    };

    this.ws.onclose = () => {
      console.log('Metrics stream disconnected, reconnecting...');
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    };
  }

  handleMetrics(data, timestamp) {
    // Update dashboard
    document.getElementById('robot-count').textContent = data.robots.total;
    document.getElementById('active-robots').textContent = data.robots.active;
    document.getElementById('queue-depth').textContent = data.queue.depth;
    document.getElementById('jobs-today').textContent = data.jobs.completed_today;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const metricsClient = new MetricsStreamClient(accessToken, 5, 'production');
metricsClient.connect();
```

**Python Example:**
```python
import asyncio
import websockets
import json
from datetime import datetime

async def stream_metrics(
    token: str,
    interval: int = 5,
    environment: str = "production",
) -> None:
    """Stream metrics from orchestrator."""
    uri = (
        f"ws://localhost:8000/api/v1/ws/metrics/stream"
        f"?token={token}&interval={interval}&environment={environment}"
    )

    async with websockets.connect(uri) as websocket:
        print(f"Connected to metrics stream (interval={interval}s)")

        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "metrics":
                metrics = data["data"]
                timestamp = data["timestamp"]

                print(f"\n[{timestamp}] Metrics Update:")
                print(f"  Robots: {metrics['robots']['total']} total, "
                      f"{metrics['robots']['busy']} busy")
                print(f"  Queue:  {metrics['queue']['depth']} pending jobs")
                print(f"  Jobs:   {metrics['jobs']['completed_today']} completed today")

# Run
asyncio.run(stream_metrics(access_token, interval=10))
```

---

## Keep-Alive Protocol

All WebSocket endpoints support a simple ping/pong keep-alive:

**Client sends:**
```
ping
```

**Server responds:**
```
pong
```

Recommended ping interval: 20-30 seconds.

> **Note:** The server also sends WebSocket-level pings (ping_interval=20s, ping_timeout=10s).

---

## Connection Management

### Broadcast Architecture

The orchestrator uses connection managers to broadcast events to all connected clients:

```
                    +----------------+
                    |  Event Source  |
                    | (Job Status,   |
                    |  Heartbeat,    |
                    |  Queue Depth)  |
                    +-------+--------+
                            |
                            v
                  +-------------------+
                  | Connection Manager|
                  |  (per endpoint)   |
                  +-------------------+
                   /    |    |    \
                  /     |    |     \
                 v      v    v      v
              Client  Client Client Client
              (WS)    (WS)  (WS)   (WS)
```

### Timeout Handling

- Send timeout: 1 second per client
- Slow clients are automatically disconnected
- Connection count is tracked per endpoint

### Reconnection Best Practices

```javascript
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.minDelay = options.minDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.currentDelay = this.minDelay;
    this.handlers = {};
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.currentDelay = this.minDelay; // Reset on success
      if (this.handlers.open) this.handlers.open();
    };

    this.ws.onmessage = (event) => {
      if (this.handlers.message) this.handlers.message(event);
    };

    this.ws.onclose = (event) => {
      if (this.handlers.close) this.handlers.close(event);

      // Don't reconnect on auth failure
      if (event.code === 4001) {
        console.error('Authentication failed');
        return;
      }

      // Exponential backoff
      setTimeout(() => this.connect(), this.currentDelay);
      this.currentDelay = Math.min(this.currentDelay * 2, this.maxDelay);
    };

    this.ws.onerror = (error) => {
      if (this.handlers.error) this.handlers.error(error);
    };
  }

  on(event, handler) {
    this.handlers[event] = handler;
    return this;
  }

  send(data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  close() {
    this.shouldReconnect = false;
    this.ws.close();
  }
}

// Usage
const ws = new ReconnectingWebSocket(
  `ws://localhost:8000/api/v1/ws/live-jobs?token=${token}`,
  { minDelay: 1000, maxDelay: 30000 }
);

ws.on('message', (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
});
```

---

## Event Bus Integration

WebSocket events are published by the internal event bus handlers:

```python
# These handlers are registered during server startup
from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
    on_job_status_changed,
    on_robot_heartbeat,
    on_queue_depth_changed,
)

# Event bus subscribes these handlers
event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
event_bus.subscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed)
```

### Publishing Custom Events

To broadcast to WebSocket clients from your code:

```python
from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
    broadcast_job_update,
    broadcast_robot_status,
    broadcast_queue_metrics,
)

# Broadcast job status change
await broadcast_job_update(job_id="job-12345", status="completed")

# Broadcast robot status
await broadcast_robot_status(
    robot_id="robot-001",
    status="busy",
    cpu_percent=45.2,
    memory_mb=1024.5,
)

# Broadcast queue depth
await broadcast_queue_metrics(depth=42)
```

---

## Error Handling

### Connection Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Code 4001 | Missing or invalid token | Check authentication |
| Connection refused | Server not running | Verify server is up |
| Timeout | Network issues | Implement retry logic |

### Message Errors

```javascript
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    // Process data
  } catch (error) {
    console.error('Invalid JSON message:', event.data);
    // Handle gracefully - don't close connection
  }
};
```

---

## Security Considerations

1. **Always use WSS in production** - Encrypt WebSocket traffic
2. **Token refresh** - Reconnect with new token before expiry
3. **Validate all messages** - Don't trust client-side data
4. **Rate limit connections** - Prevent connection flooding
5. **Monitor connection counts** - Alert on unusual spikes

---

## Related Documentation

- [REST API Reference](orchestrator-rest.md) - HTTP endpoints
- [Event Bus Reference](event-bus.md) - Domain events
- [Monitoring Guide](../../../user-guide/deployment/monitoring.md) - Dashboard setup
