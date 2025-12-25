# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Robot Fleet Management System - Executive Summary

## Overview

CasareRPA implements a **production-ready distributed robot fleet management system** with cloud execution capabilities. Users can switch from local workflow execution to submitting jobs to remote robots with automatic routing, load balancing, and real-time monitoring.

## Core Components

### 1. User Interface (Presentation Layer)
- **RobotPickerPanel** - Dockable panel for mode selection (local/cloud) and robot picking
- **FleetDashboardDialog** - Comprehensive admin dashboard with 6 tabs (Robots, Jobs, Schedules, Queues, Analytics, API Keys)
- **Status indicators** - Real-time color-coded robot status (green=online, yellow=busy, red=offline, gray=maintenance)
- **Filtering system** - Filter robots by capability (browser, desktop, GPU, secure zone, etc.)

### 2. Controller (Application Layer)
- **RobotController** - 1163-line bridge between UI and orchestrator APIs
- **Orchestrator connection management** - Automatic fallback through multiple URLs (config, env, tunnel, localhost)
- **Job submission** - Extracts workflow data and variables, submits to API
- **Robot management commands** - Start, stop, pause, restart individual or all robots
- **Real-time updates** - WebSocket subscriptions for status changes

### 3. Client Library (Infrastructure)
- **OrchestratorClient** - HTTP + WebSocket async client for orchestrator APIs
- **REST endpoints** - Robots, jobs, fleet metrics, analytics, schedules
- **DTOs** - RobotData and JobData for API communication
- **Error handling** - Automatic retry with exponential backoff, graceful degradation

### 4. Server Manager (Infrastructure)
- **RobotManager** - In-memory robot registry with optional PostgreSQL persistence
- **ConnectedRobot** - Runtime robot state with WebSocket connection
- **PendingJob** - Job state tracking with routing information
- **Job routing algorithm** - Auto-select best available robot matching capabilities
- **Requeue logic** - Handle robot rejections and reassign to different robot
- **Load balancing** - Route to robot with fewest current jobs

### 5. Data Persistence (Infrastructure)
- **PgRobotRepository** - PostgreSQL backend with UPSERT semantics
- **Robot state persistence** - Survives orchestrator restart
- **Heartbeat-based online detection** - Mark offline if no heartbeat in 90s
- **Multi-tenant support** - Isolate robots and jobs by tenant
- **Job history** - Store execution records for analytics

### 6. Domain Models (Domain Layer)
- **Robot entity** - Status, capabilities, job assignments
- **RobotStatus enum** - OFFLINE, ONLINE, BUSY, ERROR, MAINTENANCE
- **RobotCapability enum** - BROWSER, DESKTOP, GPU, HIGH_MEMORY, SECURE, CLOUD, ON_PREMISE
- **Domain events** - Typed, immutable events (RobotRegistered, JobSubmitted, JobCompleted, etc.)

## Key Features

### Execution Mode Selection
```
Local Mode (Default)
└─ Run workflow on Canvas machine
└─ Fast, no network latency
└─ Robot selection disabled

Cloud Mode
└─ Submit to orchestrator
└─ Enable robot selection
└─ Auto-route with load balancing
└─ Real-time monitoring
```

### Job Routing Algorithm
```
1. If target_robot_id specified
   └─ Use that robot if available and matches tenant

2. Else find available robots matching:
   └─ Capability requirements (browser, desktop, GPU, etc.)
   └─ Tenant isolation
   └─ Available job slots

3. Load balance: pick robot with fewest jobs
```

### Job Lifecycle
```
Pending → Assigned → Executing → Completed/Failed

If robot rejects:
└─ Mark as pending
└─ Add robot to rejected_by set
└─ Try different robot
└─ Repeat until max rejections or success
```

### Real-time Monitoring
```
Robot Heartbeat (every 10s)
└─ CPU, memory, job count
└─ Update last_heartbeat timestamp
└─ Publish RobotHeartbeat event
└─ Broadcast to admin dashboards

Job Status Update
└─ Job progress from robot
└─ Update job status in RobotManager
└─ Publish JobAssigned/JobCompleted event
└─ Notify subscribers via WebSocket
```

## Configuration

### Client (Canvas)
```bash
# Via config.yaml
orchestrator.url = "http://localhost:8000"
orchestrator.api_key = "secret_key"

# Via environment
ORCHESTRATOR_URL=...
ORCHESTRATOR_API_KEY=...
CASARE_API_URL=...  # Cloudflare tunnel
JWT_DEV_MODE=true   # Dev mode (no auth)
```

### Server (Orchestrator)
```bash
# Start with dev mode
JWT_DEV_MODE=true python manage.py orchestrator start

# Or with auth
python manage.py orchestrator start
```

## API Endpoints

### Robots
```
POST   /api/v1/robots/register
GET    /api/v1/metrics/robots[?status]
GET    /api/v1/metrics/robots/{robot_id}
PUT    /api/v1/robots/{robot_id}/status
DELETE /api/v1/robots/{robot_id}
```

### Jobs
```
POST   /api/v1/workflows  (submit job)
GET    /api/v1/metrics/jobs[?limit,status,workflow_id,robot_id]
GET    /api/v1/metrics/jobs/{job_id}
POST   /api/v1/jobs/{job_id}/cancel
POST   /api/v1/jobs/{job_id}/retry
```

### Fleet Monitoring
```
GET    /api/v1/metrics/fleet      (total/online/busy/offline counts)
GET    /api/v1/metrics/analytics  (success rates, performance trends)
GET    /api/v1/metrics/activity   (event feed)
```

## Domain Events

```
RobotRegistered(robot_id, robot_name, capabilities, max_concurrent_jobs)
RobotDisconnected(robot_id, orphaned_job_ids, reason)
RobotHeartbeat(robot_id, cpu_percent, memory_mb, current_job_count)

JobSubmitted(job_id, workflow_id, priority, target_robot_id)
JobAssigned(job_id, robot_id, robot_name)
JobCompletedOnOrchestrator(job_id, robot_id, success, execution_time_ms)
JobRequeued(job_id, previous_robot_id, reason, rejected_by_count)
```

## Current Capabilities

| Feature | Status |
|---------|--------|
| Robot selection & execution mode toggle | ✓ Implemented |
| Job submission to remote robots | ✓ Implemented |
| Automatic job routing by capability | ✓ Implemented |
| Load balancing (least-busy robot) | ✓ Implemented |
| Job requeue on robot rejection | ✓ Implemented |
| Real-time robot status monitoring | ✓ Implemented |
| Fleet metrics & analytics | ✓ Implemented |
| PostgreSQL persistence | ✓ Implemented |
| Multi-tenant support | ✓ Implemented |
| WebSocket real-time updates | ✓ Implemented |
| Admin fleet management dashboard | ✓ Implemented |
| API key management | ✓ Implemented |
| Robot health checks | ✓ Implemented |
| Heartbeat-based offline detection | ✓ Implemented |

## Limitations & Gaps

### Critical Gaps
- **Workflow-level constraints** - Can't define "this workflow only runs on GPU robots" in workflow definition
- **Job dependencies** - No support for job chains (Job A → Job B)
- **Resource reservations** - Can't pre-allocate capacity for critical jobs
- **Audit trail** - Limited event history and compliance logging

### Infrastructure Gaps
- **Single orchestrator** - No high availability or failover
- **Basic reconnection** - May lose updates on network blip
- **No circuit breaker** - API failures can cascade
- **Fixed heartbeat timeout** - Can't tune per-environment

### UI/UX Gaps
- **Limited robot info** - Need more detailed health dashboard
- **Single selection point** - Can't select robot for specific nodes in workflow
- **Bulk operations** - No UI for batch robot restart/shutdown
- **Job monitoring** - Limited progress tracking from Canvas

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| List robots | ~100ms | Cached, 100 req/min limit |
| Submit job | ~500ms | HTTP POST, includes routing |
| Robot assignment | <100ms | In-memory lookup |
| Heartbeat update | <50ms | Database update |
| WebSocket message | ~50ms | Broadcast to subscribers |

## Database Schema (PostgreSQL)

```sql
robots (
  robot_id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128),
  hostname VARCHAR(256),
  status VARCHAR(32),
  environment VARCHAR(64),
  capabilities JSONB,          -- ["browser", "desktop"]
  max_concurrent_jobs INT,
  current_job_ids JSONB,       -- ["job-1", "job-2"]
  tags JSONB,
  metrics JSONB,               -- {cpu_percent, memory_mb}
  tenant_id VARCHAR(64),
  last_heartbeat TIMESTAMP,
  last_seen TIMESTAMP,
  created_at TIMESTAMP
)
```

## Integration Points

### With Canvas Execution
```
1. User switches execution mode to "Cloud"
2. RobotPickerPanel connects to orchestrator
3. Shows available robots
4. User selects robot
5. User submits workflow
6. RobotController extracts workflow data
7. Submits via OrchestratorClient.submit_job()
8. RobotManager routes to robot
9. Robot receives job_assign via WebSocket
10. Robot executes and reports back
11. Event published to event bus
12. UI updates with completion status
```

### With Credentials System
- Robot API keys managed separately
- Support robot-specific authentication
- FleetDashboardDialog > API Keys tab for management

### With Event Bus
- RobotRegistered → dashboards, audit logs, statistics
- JobSubmitted → job monitors, activity feeds
- JobCompleted → execution monitors, analytics
- All events published to event bus for subscribers

## Security

- **API Key Auth** - Bearer token for all requests
- **Tenant Isolation** - Robots and jobs isolated by tenant_id
- **Development Mode** - JWT_DEV_MODE for dev/testing
- **Rate Limiting** - 100 req/min per IP for most endpoints
- **Connection Security** - WebSocket over WSS (if using HTTPS base URL)

## Future Enhancements (Recommended)

1. **Priority queue enforcement** - Currently priority exists but not enforced
2. **Resource constraints in workflow** - Define required capabilities at workflow level
3. **Job dependency chains** - Support sequential job execution
4. **Auto-scaling policies** - Provision robots based on queue depth
5. **High availability** - Multiple orchestrator instances with failover
6. **Audit trail** - Compliance-grade event logging
7. **Custom metrics** - Allow robots to report custom metrics
8. **Robot health dashboard** - Detailed health status, error history
9. **Bulk operations UI** - Restart/stop all robots from dashboard
10. **Job progress streaming** - Real-time job output to Canvas

## Conclusion

CasareRPA's robot fleet management system provides:
- **Seamless integration** with Canvas workflow execution
- **Production-ready architecture** with DDD patterns, persistence, and events
- **Extensible design** for custom routing and monitoring
- **Multi-tenant support** for SaaS deployments
- **Real-time coordination** via WebSocket for live updates

The system is ready for deployment but has clear extension points for advanced features like auto-scaling, resource constraints, and job dependencies.

## Files to Review (in order)

1. `ROBOT_FLEET_MANAGEMENT_ANALYSIS.md` - Comprehensive 400+ line analysis
2. `FLEET_MANAGEMENT_QUICK_REFERENCE.md` - Quick lookup guide with code examples
3. Source files:
   - `presentation/canvas/ui/panels/robot_picker_panel.py` (759 lines)
   - `presentation/canvas/controllers/robot_controller.py` (1163 lines)
   - `infrastructure/orchestrator/client.py` (580 lines)
   - `infrastructure/orchestrator/robot_manager.py` (764 lines)
   - `infrastructure/orchestrator/persistence/pg_robot_repository.py` (300+ lines)
   - `domain/orchestrator/entities/robot.py` (296 lines)
   - `domain/orchestrator/events.py` (200+ lines)
