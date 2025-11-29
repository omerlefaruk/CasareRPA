# CasareRPA Monitoring API

FastAPI backend for multi-robot fleet monitoring dashboard.

## Overview

Provides REST and WebSocket endpoints for:
- Fleet-wide metrics (robot counts, active jobs, queue depth)
- Per-robot metrics (resource usage, performance stats)
- Job execution history and details
- Analytics and trends
- Real-time updates via WebSocket

## Running the API

### Development

```bash
# Install dependencies
pip install -e .

# Run with auto-reload
uvicorn casare_rpa.orchestrator.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Run with multiple workers
uvicorn casare_rpa.orchestrator.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### REST Endpoints

#### Fleet Metrics
```http
GET /api/v1/metrics/fleet
```

Returns fleet summary:
```json
{
  "total_robots": 10,
  "active_robots": 3,
  "idle_robots": 5,
  "offline_robots": 2,
  "active_jobs": 7,
  "queue_depth": 42
}
```

#### Robots List
```http
GET /api/v1/metrics/robots?status=busy
```

Query Parameters:
- `status` (optional): Filter by robot status (idle/busy/offline)

Returns array of robot summaries.

#### Robot Details
```http
GET /api/v1/metrics/robots/{robot_id}
```

Returns detailed robot metrics including performance stats.

#### Job History
```http
GET /api/v1/metrics/jobs?limit=50&status=completed&workflow_id=abc123
```

Query Parameters:
- `limit` (default: 50, max: 500): Number of jobs to return
- `status` (optional): Filter by job status (pending/claimed/completed/failed)
- `workflow_id` (optional): Filter by workflow
- `robot_id` (optional): Filter by robot

Returns paginated job history.

#### Job Details
```http
GET /api/v1/metrics/jobs/{job_id}
```

Returns detailed job execution info including node-by-node breakdown.

#### Analytics
```http
GET /api/v1/metrics/analytics
```

Returns aggregated statistics:
```json
{
  "total_jobs": 1523,
  "success_rate": 94.2,
  "failure_rate": 5.8,
  "average_duration_ms": 3245.6,
  "p50_duration_ms": 2100.0,
  "p90_duration_ms": 5200.0,
  "p99_duration_ms": 12000.0,
  "slowest_workflows": [...],
  "error_distribution": [...],
  "self_healing_success_rate": 78.5
}
```

### WebSocket Endpoints

#### Live Job Updates
```
WS /ws/live-jobs
```

Receives real-time job status updates:
```json
{
  "job_id": "job-123",
  "status": "completed",
  "timestamp": "2025-11-29T10:30:00Z"
}
```

#### Robot Status Stream
```
WS /ws/robot-status
```

Receives robot heartbeat updates:
```json
{
  "robot_id": "robot-001",
  "status": "busy",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "timestamp": "2025-11-29T10:30:00Z"
}
```

#### Queue Metrics
```
WS /ws/queue-metrics
```

Receives queue depth updates every 5 seconds:
```json
{
  "depth": 42,
  "timestamp": "2025-11-29T10:30:00Z"
}
```

## Integration

### Connect to EventBus

To broadcast real-time updates, integrate with the EventBus:

```python
from casare_rpa.orchestrator.api.routers.websockets import (
    broadcast_job_update,
    broadcast_robot_status,
    broadcast_queue_metrics,
)

# When job status changes
await broadcast_job_update(job_id="job-123", status="completed")

# When robot heartbeat received
await broadcast_robot_status(
    robot_id="robot-001",
    status="busy",
    cpu_percent=45.2,
    memory_mb=1024.5
)

# When queue depth changes
await broadcast_queue_metrics(depth=42)
```

### Connect to RPAMetricsCollector

Replace mock implementation in `dependencies.py`:

```python
from casare_rpa.infrastructure.observability.metrics import RPAMetricsCollector

@lru_cache
def get_metrics_collector():
    return RPAMetricsCollector.get_instance()
```

## Documentation

- **OpenAPI docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health check**: `http://localhost:8000/health`

## CORS Configuration

The API allows cross-origin requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8000` (Production)

Modify `main.py` to add additional origins if needed.

## TODO

- [ ] Implement actual RPAMetricsCollector integration
- [ ] Implement database queries for job/robot data
- [ ] Connect WebSocket broadcasts to EventBus
- [ ] Add authentication/authorization
- [ ] Add rate limiting
- [ ] Add request validation
- [ ] Add monitoring/observability (Prometheus metrics)
