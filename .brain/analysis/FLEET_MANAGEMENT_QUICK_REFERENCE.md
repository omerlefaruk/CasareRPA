# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Robot Fleet Management - Quick Reference Guide

## Files at a Glance

### Core UI Components
```
presentation/canvas/ui/panels/robot_picker_panel.py (759 lines)
├─ RobotPickerPanel - Dock panel for robot selection
├─ Execution mode toggle: "Run Local" vs "Submit to Cloud"
├─ Robot tree with status indicators
├─ Capability filtering (browser, desktop, GPU, etc.)
└─ Signals: robot_selected, execution_mode_changed, refresh_requested

presentation/canvas/ui/dialogs/fleet_dashboard.py (250+ lines)
├─ FleetDashboardDialog - Admin dashboard
├─ Tabs: Robots, Jobs, Schedules, Queues, Analytics, API Keys
└─ Tenant filtering (super admin only)
```

### Controllers
```
presentation/canvas/controllers/robot_controller.py (1163 lines)
├─ RobotController - UI ↔ Orchestrator bridge
├─ Orchestrator client management & connection
├─ Robot listing & filtering
├─ Job submission
├─ Remote robot commands (start/stop/pause/restart/etc.)
└─ Batch operations (stop_all_robots, restart_all_robots)
```

### Infrastructure - Client
```
infrastructure/orchestrator/client.py (580 lines)
├─ OrchestratorClient - HTTP + WebSocket client
├─ REST endpoints:
│   ├─ GET /api/v1/metrics/robots[?status]
│   ├─ GET /api/v1/metrics/jobs[?status,workflow_id,robot_id]
│   ├─ POST /api/v1/workflows (job submission)
│   ├─ POST /api/v1/robots/register
│   └─ GET /api/v1/metrics/fleet
├─ WebSocket events: robot_status, job_update, queue_metrics
├─ Automatic retry with exponential backoff
└─ Auto-reconnect on disconnect
```

### Infrastructure - Server
```
infrastructure/orchestrator/robot_manager.py (764 lines)
├─ RobotManager - In-memory robot + job state
├─ Data structures:
│   ├─ ConnectedRobot - WebSocket + capabilities + current_job_ids
│   └─ PendingJob - Job state + routing info
├─ Job routing algorithm:
│   1. If target_robot_id specified, try that robot
│   2. Else, find available robot matching capabilities
│   3. Load balance to robot with fewest current jobs
├─ Job requeue on robot rejection
└─ Domain event publishing (RobotRegistered, JobSubmitted, etc.)

infrastructure/orchestrator/persistence/pg_robot_repository.py (300+ lines)
├─ PgRobotRepository - PostgreSQL persistent storage
├─ Schema: robots table with JSONB for capabilities, metrics, tags
├─ Methods: get_by_id, get_all, save (UPSERT), update_status, update_heartbeat
├─ Tenant isolation support
└─ Heartbeat-based online detection (90s timeout)
```

### REST API Routers
```
infrastructure/orchestrator/api/routers/
├─ metrics.py - Fleet monitoring (fleet, robots, jobs, analytics, activity)
├─ robots.py - Robot CRUD (register, update, delete)
├─ jobs.py - Job operations (submit, cancel, retry)
├─ schedules.py - Workflow schedule management
└─ websockets.py - WebSocket connections & message handling
```

### Domain Models
```
domain/orchestrator/entities/robot.py (296 lines)
├─ Robot entity - status, capabilities, current_job_ids
├─ RobotStatus enum - OFFLINE, ONLINE, BUSY, ERROR, MAINTENANCE
├─ RobotCapability enum - BROWSER, DESKTOP, GPU, HIGH_MEMORY, SECURE, CLOUD, ON_PREMISE
├─ Methods: assign_job(), complete_job(), has_capability(), is_available
└─ Properties: current_jobs, utilization, can_accept_job

domain/orchestrator/events.py (200+ lines)
├─ RobotRegistered - Robot connected
├─ RobotDisconnected - Robot disconnected (includes orphaned_job_ids)
├─ RobotHeartbeat - Robot sent metrics (cpu, memory, job_count)
├─ JobSubmitted - Workflow submitted to orchestrator
├─ JobAssigned - Job routed to specific robot
├─ JobCompletedOnOrchestrator - Job finished (success/failure)
└─ JobRequeued - Job rejected by robot, being reassigned
```

---

## Key Workflows

### 1. Switching from Local to Cloud Execution

```python
# User selects "Submit to Cloud" in RobotPickerPanel
robot_picker.execution_mode_changed.emit("cloud")
                    ↓
robot_controller._on_panel_mode_changed("cloud")
                    ↓
robot_controller.set_execution_mode("cloud")
                    ↓
# RobotPickerPanel enables robot selection
robot_group.setEnabled(True)
                    ↓
# Controller connects to orchestrator (if not already)
await robot_controller.connect_to_orchestrator()
                    ↓
# Refresh robot list
await robot_controller.refresh_robots()
                    ↓
# User selects a robot
robot_picker.robot_selected.emit(robot_id)
                    ↓
robot_controller.select_robot(robot_id)
                    ↓
# User clicks "Submit to Cloud" button
robot_picker.submit_to_cloud_requested.emit()
                    ↓
await robot_controller._submit_current_workflow()
```

### 2. Job Submission Flow

```python
# Canvas: Get workflow data
workflow_data = main_window._get_workflow_data()  # From canvas graph
variables = project_controller.get_current_variables()

# Controller: Submit to API
job_id = await robot_controller.submit_job(
    workflow_data=workflow_data,
    variables=variables,
    robot_id=selected_robot_id
)

# API: Create job via POST /api/v1/workflows
async def submit_workflow_endpoint(payload):
    # payload = {workflow_json, variables, metadata: {robot_id}}
    # Create job in database
    job = Job(workflow_id, robot_id, ...)
    # Emit domain event
    bus.publish(JobSubmitted(...))

# RobotManager: Route job to robot
async def _try_assign_job(job):
    # Find robot: specific or auto-select
    robot = find_robot(job.target_robot_id or job.required_capabilities)

    if robot and robot.available_slots > 0:
        # Send job assignment via WebSocket
        await robot.websocket.send_text({
            "type": "job_assign",
            "job_id": job.job_id,
            "workflow_data": job.workflow_data,
            "variables": job.variables
        })
        # Publish event
        bus.publish(JobAssigned(job_id, robot_id, ...))
```

### 3. Robot Heartbeat & Status Update

```python
# Robot: Send heartbeat every 10 seconds
robot.send_heartbeat({
    "cpu_percent": 45.2,
    "memory_mb": 2048,
    "current_job_count": 2
})

# RobotManager: Receive heartbeat
async def handle_robot_heartbeat(robot_id, metrics):
    robot = _robots[robot_id]
    robot.last_heartbeat = now()

    # Publish domain event
    bus.publish(RobotHeartbeat(robot_id, metrics['cpu'], metrics['memory'], ...))

    # Persist to database (if repository available)
    await repository.update_heartbeat(robot_id, metrics)

    # Broadcast to admin dashboards
    await broadcast_admin({"type": "robot_heartbeat", "robot_id": ..., ...})
```

### 4. Job Completion & Requeue

```python
# Robot: Complete job (success or failure)
robot.send_job_complete({
    "job_id": "job-123",
    "success": true,  # or false
    "result": {...}
})

# RobotManager: Handle completion
async def job_completed(robot_id, job_id, success, result):
    robot = _robots[robot_id]
    robot.current_job_ids.discard(job_id)       # Free up slot

    job = _jobs[job_id]
    job.status = "completed" if success else "failed"

    # Publish event
    bus.publish(JobCompletedOnOrchestrator(job_id, robot_id, success, duration_ms))

    # Persist
    await repository.remove_job_from_robot(robot_id, job_id)

    # Try assigning next pending job to now-free robot
    await _try_assign_job(get_next_pending_job())
```

### 5. Robot Rejection & Requeue

```python
# Robot: Reject job (doesn't match capabilities, resource constraints, etc.)
robot.send_job_reject({
    "job_id": "job-123",
    "reason": "insufficient_memory"
})

# RobotManager: Handle rejection
async def requeue_job(robot_id, job_id, reason):
    robot = _robots[robot_id]
    robot.current_job_ids.discard(job_id)       # Free up slot

    job = _jobs[job_id]
    job.rejected_by.add(robot_id)               # Track rejection
    job.status = "pending"                      # Back to pending

    # Publish event
    bus.publish(JobRequeued(job_id, robot_id, reason, len(job.rejected_by)))

    # Try different robot (exclude rejected ones)
    await _try_assign_job_excluding(job, job.rejected_by)
```

---

## Configuration & Environment

### Client Configuration (config.yaml)
```yaml
orchestrator:
  url: "http://localhost:8000"        # or https://api.casare.net
  api_key: "secret_key_here"          # Optional
```

### Environment Variables (Priority Order)
```bash
# 1. Explicit URL
export ORCHESTRATOR_URL="http://orchestrator-host:8000"
export ORCHESTRATOR_API_KEY="secret_key"

# 2. Cloud tunnel (CASARE_API_URL)
export CASARE_API_URL="https://api.casare.net"

# 3. Development mode (no auth)
export JWT_DEV_MODE=true

# 4. Default fallback: localhost:8000
```

### Orchestrator Connection Fallback Order
```
1. Configured URL (from config.yaml)
2. ORCHESTRATOR_URL env var
3. CASARE_API_URL (Cloudflare tunnel)
4. http://localhost:8000 (fallback)
```

---

## API Endpoints Summary

### Robot Management
```
POST   /api/v1/robots/register
       {robot_id, name, hostname, capabilities, environment, max_concurrent_jobs}

GET    /api/v1/metrics/robots[?status=idle|busy|offline]
GET    /api/v1/metrics/robots/{robot_id}
PUT    /api/v1/robots/{robot_id}/status
       {status: "idle|busy|offline|error|maintenance"}
DELETE /api/v1/robots/{robot_id}
```

### Job Management
```
POST   /api/v1/workflows
       {workflow_name, workflow_json, metadata: {robot_id, variables}}

GET    /api/v1/metrics/jobs[?limit,status,workflow_id,robot_id]
GET    /api/v1/metrics/jobs/{job_id}
POST   /api/v1/jobs/{job_id}/cancel
POST   /api/v1/jobs/{job_id}/retry
```

### Fleet Monitoring
```
GET    /api/v1/metrics/fleet
       Returns: {robots: {total, online, busy, offline},
                jobs: {pending, assigned, completed, failed, total},
                queue_depth}

GET    /api/v1/metrics/analytics[?days=7]
       Returns: {success_rate, avg_duration, top_workflows, performance_trend}

GET    /api/v1/metrics/activity[?limit,since,event_type]
       Returns: {events: [{type, robot_id, timestamp, details}]}
```

### Rate Limits
```
Robots:    100 requests/minute
Details:   200 requests/minute
Metrics:   100 requests/minute
Analytics: 100 requests/minute
```

---

## Signal & Slot Connections

### RobotController → RobotPickerPanel
```python
controller.connection_status_changed.connect(panel.set_connected)
controller.robots_updated.connect(panel.update_robots)
controller.refreshing_changed.connect(panel.set_refreshing)
controller.submission_state_changed.connect(panel._on_submission_state_changed)
```

### RobotPickerPanel → RobotController
```python
panel.robot_selected.connect(controller._on_panel_robot_selected)
panel.execution_mode_changed.connect(controller._on_panel_mode_changed)
panel.refresh_requested.connect(controller._on_panel_refresh_requested)
panel.submit_to_cloud_requested.connect(controller._on_submit_to_cloud_requested)
```

---

## Domain Events Reference

### Publishing Events
```python
from casare_rpa.domain.orchestrator.events import RobotRegistered, get_event_bus

bus = get_event_bus()
bus.publish(RobotRegistered(
    robot_id="bot-1",
    robot_name="Bot-1",
    hostname="machine.local",
    environment="production",
    capabilities=("browser", "desktop"),
    max_concurrent_jobs=3,
    tenant_id="acme-corp"
))
```

### Subscribing to Events
```python
def on_robot_registered(event: RobotRegistered):
    print(f"Robot {event.robot_name} ({event.robot_id}) registered")
    # Update dashboard, statistics, etc.

bus.subscribe(RobotRegistered, on_robot_registered)
```

### Event List
```
RobotRegistered - Robot connected
RobotDisconnected - Robot disconnected (orphaned_job_ids list)
RobotHeartbeat - Robot sent metrics (cpu_percent, memory_mb, current_job_count)

JobSubmitted - Workflow submitted (job_id, workflow_id, priority, target_robot_id)
JobAssigned - Job routed to robot (job_id, robot_id, robot_name)
JobCompletedOnOrchestrator - Job finished (job_id, robot_id, success, execution_time_ms)
JobRequeued - Job rejected & reassigned (job_id, previous_robot_id, reason, rejected_by_count)
```

---

## Data Models

### ConnectedRobot (Runtime)
```python
@dataclass
class ConnectedRobot:
    robot_id: str
    robot_name: str
    websocket: WebSocket                      # For sending commands
    capabilities: List[str]                   # ["browser", "desktop", "gpu"]
    max_concurrent_jobs: int
    current_job_ids: Set[str]                 # {"job-1", "job-2"}
    connected_at: datetime
    last_heartbeat: datetime
    environment: str                          # "production", "development"
    tenant_id: Optional[str]
    hostname: str

    @property
    def status(self) -> str:  # "idle" | "working" | "busy"
    @property
    def available_slots(self) -> int:  # max_concurrent_jobs - len(current_job_ids)
```

### Robot (Domain Entity - Persistent)
```python
@dataclass
class Robot:
    id: str
    name: str
    status: RobotStatus                      # OFFLINE|ONLINE|BUSY|ERROR|MAINTENANCE
    environment: str = "default"
    max_concurrent_jobs: int = 1
    capabilities: Set[RobotCapability] = {...}  # BROWSER|DESKTOP|GPU|etc.
    assigned_workflows: List[str] = [...]   # Workflows this robot is default for
    current_job_ids: List[str] = [...]
    last_seen: Optional[datetime]
    last_heartbeat: Optional[datetime]
    created_at: Optional[datetime]
    tags: List[str]                          # ["region-us", "high-priority"]
    metrics: Dict[str, Any] = {}

    @property
    def is_available(self) -> bool:  # status == ONLINE and has capacity
    @property
    def current_jobs(self) -> int:  # len(current_job_ids)
    @property
    def utilization(self) -> float:  # (current_jobs / max_concurrent_jobs) * 100
```

### PendingJob
```python
@dataclass
class PendingJob:
    job_id: str
    workflow_id: str
    workflow_data: Dict[str, Any]           # Full workflow JSON
    variables: Dict[str, Any]               # Initial variables
    priority: int
    target_robot_id: Optional[str]          # Specific robot or None
    required_capabilities: List[str]        # ["browser", "high_memory"]
    timeout: int                            # seconds
    created_at: datetime
    status: str                             # "pending"|"assigned"|"completed"|"failed"
    assigned_robot_id: Optional[str]
    tenant_id: Optional[str]
    rejected_by: Set[str]                   # Robots that rejected this job
```

---

## Debugging Tips

### 1. Check Orchestrator Connection
```python
# In RobotController
print(f"Connected: {robot_controller.is_connected}")
print(f"Orchestrator URL: {robot_controller.orchestrator_url}")
print(f"Robots: {len(robot_controller.robots)}")
```

### 2. Monitor WebSocket Events
```python
# Attach to OrchestratorClient callbacks
client.on("robot_status", lambda data: print(f"Robot status: {data}"))
client.on("job_update", lambda data: print(f"Job update: {data}"))
client.on("error", lambda data: print(f"Error: {data}"))
```

### 3. Inspect Job Routing
```python
# In RobotManager
print(f"Available robots: {len(robot_manager.get_available_robots())}")
for robot in robot_manager.get_all_robots():
    print(f"{robot.robot_name}: status={robot.status}, jobs={len(robot.current_job_ids)}/{robot.max_concurrent_jobs}")
```

### 4. Check PostgreSQL State
```sql
-- Robots table
SELECT robot_id, name, status, current_job_ids, last_heartbeat
FROM robots
ORDER BY last_heartbeat DESC;

-- Job history
SELECT job_id, robot_id, workflow_id, status, duration_ms
FROM jobs
ORDER BY created_at DESC;
```

### 5. View Domain Events
```python
# Subscribe to all events
bus = get_event_bus()
bus.subscribe_all(lambda event: print(f"Event: {event}"))
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Disconnected" status in panel | Can't reach orchestrator | Check ORCHESTRATOR_URL, verify orchestrator is running |
| No robots showing | Orchestrator unreachable | Use fallback URL (localhost:8000) or verify API key |
| Job stuck in "pending" | No available robots | Check robot status, ensure capabilities match |
| Job requeued repeatedly | Robot rejects all assignments | Check job requirements vs. robot capabilities |
| WebSocket reconnection slow | Network latency | Reduce WebSocket reconnect delay in client config |
| PostgreSQL not persisting | Repository not configured | Verify PgRobotRepository is passed to RobotManager |
| Heartbeat timeout too strict | Robots marked offline prematurely | Increase heartbeat_timeout_seconds (default 90s) |

---

## Performance Tuning

| Parameter | Current | Recommendation | Notes |
|-----------|---------|-----------------|-------|
| Heartbeat timeout | 90s | 60-120s | Lower = faster offline detection, higher = more tolerant |
| Job assignment retry | Immediate | Implement backoff | Prevent cascade failures |
| Database pool size | Not specified | Min 5, Max 20 | Based on expected concurrent connections |
| WebSocket reconnect | 5s delay | Exponential backoff | Reduce server load on mass reconnect |
| Rate limiting | 100/min | Adjust per endpoint | Tighter on mutation (POST/DELETE), looser on GET |
| Queue depth | In-memory | Move to database | For persistence across restarts |

---

## Extension Points

### 1. Add Custom Robot Capability
```python
class RobotCapability(Enum):
    # ... existing
    CUSTOM_AI = "custom_ai"  # New capability
```

### 2. Implement Custom Job Router
```python
# In RobotManager._try_assign_job(), add custom predicate:
available = [
    r for r in candidates
    if r.matches_custom_criteria(job)  # Custom logic
]
```

### 3. Add Robot Health Checks
```python
# Custom RobotManager method:
async def check_robot_health(self, robot_id):
    robot = self.get_robot(robot_id)
    if not robot:
        return False

    # Send health check ping
    try:
        result = await asyncio.wait_for(
            robot.websocket.send_text({"type": "health_check"}),
            timeout=5.0
        )
        return True
    except asyncio.TimeoutError:
        return False
```

### 4. Custom Analytics
```python
# Subscribe to JobCompletedOnOrchestrator events:
def on_job_completed(event: JobCompletedOnOrchestrator):
    # Store in analytics database
    # Update dashboards
    # Alert on anomalies

bus.subscribe(JobCompletedOnOrchestrator, on_job_completed)
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **Robot** | A connected agent that executes workflows (can be local or cloud-hosted) |
| **RobotManager** | Orchestrator component managing connected robots and job assignments |
| **OrchestratorClient** | Canvas component for communicating with orchestrator |
| **Job** | A submitted workflow with associated variables and metadata |
| **Job Routing** | Process of assigning a job to an available robot (specific or auto-select) |
| **Job Requeue** | Re-assigning a rejected job to a different robot |
| **Heartbeat** | Periodic message from robot with CPU/memory/job metrics |
| **Capability** | Robot feature (browser, desktop, GPU, etc.) that affects job routing |
| **Tenant** | Isolated namespace for multi-tenant deployments |
| **WebSocket** | Persistent bidirectional connection for real-time updates |
