<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# CasareRPA Robot Fleet Management System - Comprehensive Analysis

**Date:** 2025-12-14
**Status:** Complete System Architecture Review
**Scope:** Presentation, Application, Infrastructure, and Domain Layers

---

## Executive Summary

CasareRPA implements a **multi-layered robot fleet management system** with:
- **Canvas UI Integration** - RobotPickerPanel for selecting execution mode and robots
- **REST API** - Comprehensive orchestrator APIs for CRUD, metrics, and job management
- **WebSocket Real-time Updates** - Live status and job progress streaming
- **PostgreSQL Persistence** - Optional persistent robot registry and state
- **Domain Events** - Typed event system for audit and real-time UI updates
- **Cloud Execution** - Job submission to remote robots with automatic routing

The system supports both **local execution** (single machine) and **cloud execution** (distributed robots).

---

## Architecture Overview

### Layer Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│ PRESENTATION (Canvas + UI Dialogs)                          │
│ - RobotPickerPanel: UI for mode & robot selection           │
│ - FleetDashboardDialog: Admin dashboard for fleet management│
│ - RobotTabWidget, JobsTabWidget, etc.: Detailed views       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION (Controllers + Coordinators)                    │
│ - RobotController: Bridge between UI and APIs               │
│ - Handles connection, job submission, status updates        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ DOMAIN (Entities, Events, Repositories)                     │
│ - Robot entity: Status, capabilities, job management        │
│ - RobotStatus enum: offline/online/busy/error/maintenance   │
│ - RobotCapability enum: browser/desktop/gpu/secure/etc.     │
│ - Domain events: RobotRegistered, JobSubmitted, etc.        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE                                              │
│ ├─ OrchestratorClient: HTTP + WebSocket client (REST API)  │
│ ├─ RobotManager: In-memory + optional PostgreSQL state      │
│ ├─ REST Routers: /api/v1/robots, /api/v1/jobs, metrics     │
│ └─ Persistence: PgRobotRepository, LocalRobotRepository     │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Presentation Layer (UI)

### 1.1 RobotPickerPanel
**File:** `presentation/canvas/ui/panels/robot_picker_panel.py` (759 lines)

**Purpose:** Dockable panel for execution mode selection and robot picking

**Key Features:**
- **Execution Mode Toggle**
  - Local: Run workflow on current machine
  - Cloud: Submit to orchestrator for remote execution
  - State: Initially set to "Local", can switch dynamically

- **Robot List Display**
  - Tree widget showing: Name, Status, Jobs (current/max), Capabilities
  - Color-coded status indicators:
    - Green (#5a9): Online
    - Yellow (#F4A): Busy
    - Red (#F44): Offline/Error
    - Gray (#aaa): Maintenance
  - Supports alternating row colors, single-selection

- **Filtering System**
  - Dropdown filters by capability:
    - All Robots, Browser Capable, Desktop Capable, GPU Available
    - High Memory, Secure Zone, Cloud Hosted, On-Premise
  - Applies visibility filtering in real-time
  - Shows count of visible robots

- **Robot Selection & Submission**
  - Single-click to select, double-click for quick submit
  - "Submit to Cloud" button (disabled until valid state)
  - Shows submission result in status label (5s timeout)

- **State Management**
  - `_selected_robot_id`: Currently selected robot (or None)
  - `_execution_mode`: "local" or "cloud"
  - `_connected_to_orchestrator`: Connection flag
  - `_robots`: List of Robot entities
  - `_robot_items`: Dict mapping robot_id to QTreeWidgetItem

- **Signals**
  ```python
  robot_selected = Signal(str)                    # robot_id
  execution_mode_changed = Signal(str)            # "local" or "cloud"
  refresh_requested = Signal()                    # User clicked refresh
  submit_to_cloud_requested = Signal()            # Submit button clicked
  ```

- **Styling**
  - Dark theme with THEME constants (mostly hardcoded hex fallback)
  - Dock widget with float/close/move options
  - 280px min width, 300px min height

---

### 1.2 FleetDashboardDialog
**File:** `presentation/canvas/ui/dialogs/fleet_dashboard.py` (250+ lines)

**Purpose:** Comprehensive admin dashboard for fleet operations

**Features:**
- **Multi-Tab Interface**
  1. **Robots Tab** - Robot CRUD, status, metrics, actions (start/stop/restart)
  2. **Jobs Tab** - Job history, current queue, cancel/retry operations
  3. **Schedules Tab** - Workflow schedule management
  4. **Queues Tab** - Transaction queue (UiPath-style) management
  5. **Analytics Tab** - Fleet statistics and charts
  6. **API Keys Tab** - Robot API key management

- **Tenant Filtering** (super admin only)
  - TenantSelectorWidget for filtering by tenant
  - Hidden by default, shown for super admin users

- **Connection Status**
  - Live indicator (green/red)
  - Updates on orchestrator connect/disconnect

- **Signals** (delegates to tabs)
  - `robot_selected`, `robot_edited`, `robot_deleted`
  - `job_cancelled`, `job_retried`
  - `schedule_enabled_changed`, `schedule_edited`, etc.
  - `queue_selected`, `queue_created`, `queue_deleted`
  - `api_key_generated`, `api_key_revoked`, `api_key_rotated`
  - `tenant_changed`, `refresh_requested`

---

## 2. Application Layer

### 2.1 RobotController
**File:** `presentation/canvas/controllers/robot_controller.py` (1163 lines)

**Responsibility:** Bridge between UI (RobotPickerPanel/Dashboard) and Orchestrator APIs

**Core Responsibilities:**
1. **Orchestrator Connection**
   - Initialize OrchestratorClient with URL/API key from:
     - ClientConfigManager (config.yaml)
     - Environment variables (ORCHESTRATOR_URL, ORCHESTRATOR_API_KEY)
     - Fallback: CASARE_API_URL (Cloudflare tunnel), then localhost
   - Automatic reconnection with fallback URL list
   - WebSocket subscriptions for real-time updates

2. **Robot Listing & Filtering**
   - Fetch robots from orchestrator API (`GET /api/v1/metrics/robots`)
   - Support status filters: idle, busy, offline
   - Support capability filtering in UI
   - Convert RobotData DTO → Robot domain entities

3. **Execution Mode Management**
   - Track current mode: "local" vs "cloud"
   - Disable robot selection in local mode
   - Clear selection when switching to local

4. **Job Submission**
   - Extract workflow data from main window
   - Get workflow variables (if available)
   - Submit via `POST /api/v1/workflows`
   - Handle auth errors (401) with helpful messages
   - Return job_id on success or None on failure

5. **Remote Robot Management Commands**
   - `start_robot()`, `stop_robot()`, `pause_robot()`, `resume_robot()`, `restart_robot()`
   - Batch operations: `stop_all_robots()`, `restart_all_robots()`
   - Log retrieval: `get_robot_logs()`
   - Metrics retrieval: `get_robot_metrics()`

6. **Real-time Updates**
   - WebSocket callbacks from OrchestratorClient:
     - `robot_status`: Updates robot status
     - `connected`/`disconnected`: Connection state
     - `error`: Error handling

**Signals:**
```python
# State signals
robots_updated = Signal(list)                   # List[Robot]
robot_selected = Signal(str)                    # robot_id
execution_mode_changed = Signal(str)            # "local" or "cloud"
connection_status_changed = Signal(bool)        # connected

# Job signals
job_submitted = Signal(str)                     # job_id
job_submission_failed = Signal(str)             # error message

# UI state signals
refreshing_changed = Signal(bool)               # True when fetching
submission_state_changed = Signal(str, str)     # (state, message)
                                               # state: idle/submitting/success/error
```

**Configuration Sources (Priority):**
```
1. config.yaml via ClientConfigManager
   └── orchestrator.url
   └── orchestrator.api_key

2. Environment Variables
   └── ORCHESTRATOR_URL
   └── ORCHESTRATOR_API_KEY
   └── CASARE_API_URL (Cloudflare tunnel)

3. Defaults
   └── https://api.casare.net (production tunnel)
   └── http://localhost:8000 (fallback)
```

**Key Methods:**
- `connect_to_orchestrator(url)` - Connect with auto-fallback
- `refresh_robots()` - Fetch latest robot list
- `submit_job(workflow_data, variables, robot_id)` - Submit workflow
- `get_statistics()` - Fleet statistics
- `get_robot_logs(robot_id, limit, since)` - Robot logs
- `get_robot_metrics(robot_id)` - CPU, memory, job stats

---

## 3. Infrastructure Layer

### 3.1 OrchestratorClient
**File:** `infrastructure/orchestrator/client.py` (580 lines)

**Type:** HTTP + WebSocket client for remote orchestrator

**Configuration:**
```python
@dataclass
class OrchestratorConfig:
    base_url: str = "http://localhost:8000"
    ws_url: str = "ws://localhost:8000"
    api_key: Optional[str] = None
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
```

**REST Endpoints Implemented:**

| Category | Method | Endpoint | Purpose |
|----------|--------|----------|---------|
| **Robots** | GET | `/api/v1/metrics/robots[?status]` | List all robots |
| | GET | `/api/v1/metrics/robots/{id}` | Get robot details |
| | POST | `/api/v1/robots/register` | Register new robot |
| | PUT | `/api/v1/robots/{id}/status` | Update robot status |
| | DELETE | `/api/v1/robots/{id}` | Deregister robot |
| **Jobs** | GET | `/api/v1/metrics/jobs[?limit,status,workflow_id,robot_id]` | List jobs |
| | GET | `/api/v1/metrics/jobs/{id}` | Get job details |
| | POST | `/api/v1/jobs/{id}/cancel` | Cancel job |
| | POST | `/api/v1/jobs/{id}/retry` | Retry job |
| **Fleet** | GET | `/api/v1/metrics/fleet` | Fleet summary (total, online, busy, offline, queue depth) |
| **Analytics** | GET | `/api/v1/metrics/analytics[?days]` | Aggregated analytics |
| | GET | `/api/v1/metrics/activity[?limit,since,event_type]` | Activity feed |
| **Schedules** | GET | `/api/v1/schedules` | List all schedules |
| | POST | `/api/v1/schedules/{id}/run-now` | Trigger schedule immediately |

**WebSocket Events:**
```python
# Callback registration
client.on("robot_status", callback)      # Robot status changed
client.on("job_update", callback)        # Job progress/status
client.on("queue_metrics", callback)     # Queue depth changed
client.on("connected", callback)         # WebSocket connected
client.on("disconnected", callback)      # WebSocket disconnected
client.on("error", callback)             # Error occurred
```

**DTOs:**
```python
@dataclass
class RobotData:
    id, name, hostname, status, environment
    cpu_percent, memory_mb
    current_job, current_jobs, max_concurrent_jobs
    last_seen, capabilities, tags

@dataclass
class JobData:
    id, workflow_id, workflow_name, robot_id, robot_name, status
    progress, current_node
    created_at, started_at, completed_at, duration_ms, error_message
```

**Error Handling:**
- Automatic retry with exponential backoff (3 attempts, 1s base delay)
- Connection pooling via aiohttp
- Graceful degradation on API failure
- WebSocket auto-reconnect on disconnect

---

### 3.2 RobotManager
**File:** `infrastructure/orchestrator/robot_manager.py` (764 lines)

**Type:** In-memory robot registry with optional PostgreSQL persistence

**Dual-Mode Architecture:**
```
┌─ In-Memory (Always) ──────────────────────┐
│ - WebSocket connections (not serializable)│
│ - Active job assignments                  │
│ - Real-time state                         │
└───────────────────────────────────────────┘
        ↓ (sync via)
┌─ PostgreSQL (Optional) ────────────────────┐
│ - Persistent robot registry                │
│ - Heartbeat history                        │
│ - Job history                              │
│ - Survives orchestrator restart            │
└────────────────────────────────────────────┘
```

**Key Data Structures:**

```python
@dataclass
class ConnectedRobot:
    robot_id: str
    robot_name: str
    websocket: WebSocket               # Sent job assignments here
    capabilities: List[str]            # ["browser", "desktop", "gpu"]
    max_concurrent_jobs: int           # e.g., 3
    current_job_ids: Set[str]          # Active jobs
    connected_at: datetime
    last_heartbeat: datetime
    environment: str
    tenant_id: Optional[str]           # For multi-tenancy
    hostname: str

    @property
    def status(self) -> str:
        # "idle", "working", or "busy" (at capacity)

    @property
    def available_slots(self) -> int:
        # max_concurrent_jobs - len(current_job_ids)

@dataclass
class PendingJob:
    job_id: str
    workflow_id: str
    workflow_data: Dict[str, Any]      # Full workflow JSON
    variables: Dict[str, Any]
    priority: int
    target_robot_id: Optional[str]     # Specific robot or None for auto-select
    required_capabilities: List[str]
    timeout: int                       # seconds
    created_at: datetime
    status: str                        # "pending", "assigned", "completed", "failed"
    assigned_robot_id: Optional[str]
    tenant_id: Optional[str]
    rejected_by: Set[str]              # Robots that rejected this job
```

**Job Lifecycle:**
```
1. submit_job() → Creates PendingJob, emits JobSubmitted event
2. _try_assign_job() → Finds available robot, sends job assignment
3. WebSocket sends job_assign message to robot
4. Robot processes job
5. job_completed() → Marks complete/failed, publishes JobCompletedOnOrchestrator
6. Robot capacity freed for next job
```

**Job Routing Algorithm:**
```python
async def _try_assign_job(self, job):
    if job.target_robot_id:
        # 1. Try specific robot if requested
        robot = get_robot(job.target_robot_id)
        if robot and has_available_slots and matches_tenant:
            assign_job(robot, job)
    else:
        # 2. Auto-select: find available robot matching capabilities
        candidates = [
            r for r in all_robots
            if r.available_slots > 0
            and all(cap in r.capabilities for cap in job.required_capabilities)
            and (not job.tenant_id or r.tenant_id == job.tenant_id)
        ]
        # 3. Load balance: pick robot with fewest current jobs
        if candidates:
            candidates.sort(key=lambda r: len(r.current_job_ids))
            assign_job(candidates[0], job)
```

**Requeue Logic:**
```python
async def requeue_job(robot_id, job_id, reason):
    robot.current_job_ids.discard(job_id)
    job.rejected_by.add(robot_id)           # Track which robots rejected
    job.status = "pending"
    # Try assigning to different robot (exclude previous rejections)
    _try_assign_job_excluding(job, job.rejected_by)
```

**Public Interface:**
```python
# Registration
register_robot(websocket, robot_id, robot_name, capabilities, ...)
unregister_robot(robot_id, reason="")
update_heartbeat(robot_id, metrics)

# Job Management
submit_job(workflow_id, workflow_data, variables, priority, target_robot_id, ...)
requeue_job(robot_id, job_id, reason)
job_completed(robot_id, job_id, success, result)

# Querying
get_robot(robot_id) → Optional[ConnectedRobot]
get_all_robots(tenant_id) → List[ConnectedRobot]
get_available_robots(required_capabilities, tenant_id) → List[ConnectedRobot]
get_job(job_id) → Optional[PendingJob]
get_pending_jobs() → List[PendingJob]
get_fleet_stats() → Dict with summary stats

# Admin Connections
add_admin_connection(websocket)              # For dashboard subscribers
_broadcast_admin(message)                    # Send to all dashboards
```

**Domain Events Published:**
```python
RobotRegistered(robot_id, robot_name, hostname, environment,
                capabilities, max_concurrent_jobs, tenant_id)
RobotDisconnected(robot_id, robot_name, orphaned_job_ids, reason)
RobotHeartbeat(robot_id, cpu_percent, memory_mb, current_job_count)

JobSubmitted(job_id, workflow_id, workflow_name, priority,
             target_robot_id, tenant_id)
JobAssigned(job_id, robot_id, robot_name, workflow_id)
JobCompletedOnOrchestrator(job_id, robot_id, success, execution_time_ms)
JobRequeued(job_id, previous_robot_id, reason, rejected_by_count)
```

---

### 3.3 REST API Routers

#### 3.3.1 Metrics Router (`routers/metrics.py`)
**Provides:** Fleet monitoring data for dashboards

| Endpoint | Method | Rate Limit | Purpose |
|----------|--------|-----------|---------|
| `/metrics/fleet` | GET | 100/min | Total/active/idle/offline counts, queue depth |
| `/metrics/robots` | GET | 100/min | List all robots with status filter |
| `/metrics/robots/{id}` | GET | 200/min | Detailed metrics (CPU, memory, jobs, performance) |
| `/metrics/jobs` | GET | 100/min | Job history with filters (limit, status, workflow_id, robot_id) |
| `/metrics/jobs/{id}` | GET | 200/min | Job details and progress |
| `/metrics/analytics[?days]` | GET | 100/min | 7-day analytics: success rates, performance, top workflows |
| `/metrics/activity[?limit,since,event_type]` | GET | 100/min | Activity feed (registrations, submissions, completions) |

**Rate Limiting:** Uses slowapi with IP-based limiting

#### 3.3.2 Robots Router (`routers/robots.py`)
**Provides:** Robot CRUD operations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/robots/register` | POST | Register/upsert robot (UPSERT semantics) |
| `/robots/{id}` | GET | Get robot details |
| `/robots/{id}` | PUT | Update robot (name, capabilities, etc.) |
| `/robots/{id}` | DELETE | Deregister robot |
| `/robots/{id}/status` | PUT | Update status (idle/busy/offline/error/maintenance) |

**Database:** PostgreSQL with UPSERT on `robot_id` (handles reconnections)

#### 3.3.3 Jobs Router (`routers/jobs.py`)
**Provides:** Job operations and history

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/jobs` | POST | Submit workflow job |
| `/jobs/{id}` | GET | Get job details |
| `/jobs/{id}/cancel` | POST | Cancel pending/running job |
| `/jobs/{id}/retry` | POST | Retry failed job |

---

### 3.4 PostgreSQL Persistence

#### 3.4.1 PgRobotRepository
**File:** `infrastructure/orchestrator/persistence/pg_robot_repository.py` (300+ lines)

**Purpose:** Persistent robot registry with async database access

**Schema (robots table):**
```sql
CREATE TABLE robots (
    robot_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    hostname VARCHAR(256),
    status VARCHAR(32),                    -- offline/online/busy/error/maintenance
    environment VARCHAR(64),
    capabilities JSONB,                    -- ["browser", "desktop", "gpu"]
    max_concurrent_jobs INT,
    current_job_ids JSONB,                 -- ["job-1", "job-2"]
    tags JSONB,                            -- ["region-us", "prod"]
    metrics JSONB,                         -- {cpu_percent, memory_mb, ...}
    tenant_id VARCHAR(64),
    last_heartbeat TIMESTAMP,
    last_seen TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,

    INDEX (status),
    INDEX (environment),
    INDEX (tenant_id),
    INDEX (last_heartbeat)
);
```

**Key Methods:**
```python
async def get_by_id(robot_id: str) → Optional[Robot]
async def get_all() → List[Robot]
async def get_all_online() → List[Robot]       # status != offline AND last_heartbeat > timeout
async def get_by_environment(env: str) → List[Robot]
async def get_by_tenant(tenant_id: str) → List[Robot]
async def save(robot: Robot)                   # INSERT OR UPDATE
async def update_status(robot_id: str, status: RobotStatus)
async def update_heartbeat(robot_id: str, metrics: Dict)
async def add_job_to_robot(robot_id: str, job_id: str)
async def remove_job_from_robot(robot_id: str, job_id: str)
async def mark_offline(robot_id: str) → List[str]   # Returns orphaned job IDs
async def delete(robot_id: str)
```

**UPSERT Pattern (Handles Reconnections):**
```sql
INSERT INTO robots (...) VALUES (...)
ON CONFLICT (robot_id) DO UPDATE SET
    name = EXCLUDED.name,
    last_heartbeat = EXCLUDED.last_heartbeat,
    status = EXCLUDED.status,
    ...
```

**Heartbeat-Based Online Detection:**
```python
def __init__(self, db_pool, heartbeat_timeout_seconds=90):
    # Robot considered offline if last_heartbeat > 90 seconds ago
    # Checked via: last_heartbeat > NOW() - INTERVAL '90 seconds'
```

---

## 4. Domain Layer

### 4.1 Robot Entity
**File:** `domain/orchestrator/entities/robot.py` (296 lines)

**Invariants:**
```python
@dataclass
class Robot:
    id: str                                          # Cannot be empty
    name: str                                        # Cannot be empty
    status: RobotStatus = OFFLINE
    environment: str = "default"
    max_concurrent_jobs: int = 1                    # >= 0
    capabilities: Set[RobotCapability] = field(...)
    assigned_workflows: List[str] = field(...)      # Default robot for workflows
    current_job_ids: List[str] = field(...)         # count <= max_concurrent_jobs

    # Additional fields
    last_seen: Optional[datetime]
    last_heartbeat: Optional[datetime]
    created_at: Optional[datetime]
    tags: List[str]
    metrics: Dict[str, Any]
```

**Status Enum:**
```python
class RobotStatus(Enum):
    OFFLINE = "offline"              # Not connected
    ONLINE = "online"                # Connected, idle
    BUSY = "busy"                    # At capacity (current_jobs >= max_concurrent_jobs)
    ERROR = "error"                  # Error state
    MAINTENANCE = "maintenance"      # Under maintenance
```

**Capability Enum:**
```python
class RobotCapability(Enum):
    BROWSER = "browser"              # Can run Playwright automation
    DESKTOP = "desktop"              # Can run UIAutomation
    GPU = "gpu"                       # Has GPU for ML workloads
    HIGH_MEMORY = "high_memory"       # Optimized for large data processing
    SECURE = "secure"                 # In secure network zone
    CLOUD = "cloud"                   # Cloud-hosted
    ON_PREMISE = "on_premise"         # On-premise/self-hosted
```

**Key Methods:**
```python
# Job Management
assign_job(job_id: str) → None
    # Raises: RobotUnavailableError, RobotAtCapacityError, DuplicateJobAssignmentError
complete_job(job_id: str) → None

# Workflow Assignment (default robot for workflow)
assign_workflow(workflow_id: str) → None
unassign_workflow(workflow_id: str) → None
is_assigned_to_workflow(workflow_id: str) → bool

# Capability Checking
has_capability(capability: RobotCapability) → bool
has_all_capabilities(capabilities: Set[RobotCapability]) → bool

# Properties
@property
current_jobs() → int                              # len(current_job_ids)

@property
is_available() → bool
    # status == ONLINE AND current_jobs < max_concurrent_jobs

@property
can_accept_job() → bool                           # Same as is_available

@property
utilization() → float                             # (current_jobs / max_concurrent_jobs) * 100

# Serialization
@classmethod
from_dict(cls, data: Dict) → Robot
to_dict() → Dict
```

**Domain Validation:**
```python
def __post_init__(self):
    if not self.id or not self.id.strip():
        raise ValueError("Robot ID cannot be empty")
    if not self.name or not self.name.strip():
        raise ValueError("Robot name cannot be empty")
    if self.max_concurrent_jobs < 0:
        raise ValueError("max_concurrent_jobs must be >= 0")
    if len(self.current_job_ids) > self.max_concurrent_jobs:
        raise ValueError("current_job_ids count cannot exceed max_concurrent_jobs")
```

---

### 4.2 Orchestrator Domain Events
**File:** `domain/orchestrator/events.py` (200+ lines)

**Robot Events:**
```python
@dataclass(frozen=True)
class RobotRegistered(DomainEvent):
    robot_id: str
    robot_name: str
    hostname: str
    environment: str = "production"
    capabilities: Tuple[str, ...] = ()
    max_concurrent_jobs: int = 1
    tenant_id: str = ""

@dataclass(frozen=True)
class RobotDisconnected(DomainEvent):
    robot_id: str
    robot_name: str
    orphaned_job_ids: Tuple[str, ...] = ()
    reason: str = ""

@dataclass(frozen=True)
class RobotHeartbeat(DomainEvent):
    robot_id: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    current_job_count: int = 0
```

**Job Events:**
```python
@dataclass(frozen=True)
class JobSubmitted(DomainEvent):
    job_id: str
    workflow_id: str
    workflow_name: str
    priority: int
    target_robot_id: str = ""
    tenant_id: str = ""

@dataclass(frozen=True)
class JobAssigned(DomainEvent):
    job_id: str
    robot_id: str
    robot_name: str
    workflow_id: str

@dataclass(frozen=True)
class JobCompletedOnOrchestrator(DomainEvent):
    job_id: str
    robot_id: str
    success: bool
    execution_time_ms: int

@dataclass(frozen=True)
class JobRequeued(DomainEvent):
    job_id: str
    previous_robot_id: str
    reason: str
    rejected_by_count: int
```

**Usage:**
```python
from casare_rpa.domain.orchestrator.events import RobotRegistered, get_event_bus

bus = get_event_bus()
bus.subscribe(RobotRegistered, on_robot_registered)
bus.publish(RobotRegistered(robot_id="bot-1", robot_name="Bot-1", ...))
```

---

## 5. Current Features & Capabilities

### 5.1 Robot Selection & Execution Mode

| Feature | Capability | Status |
|---------|-----------|--------|
| Local Execution | Run on current machine | ✓ Implemented |
| Cloud Submission | Send to remote robot | ✓ Implemented |
| Mode Toggle | Switch local ↔ cloud | ✓ Implemented |
| Robot Filtering | Filter by capability | ✓ Implemented |
| Robot Selection | Single robot select | ✓ Implemented |
| Connection Status | Show orchestrator state | ✓ Implemented |

### 5.2 Robot Management

| Feature | Capability | Status |
|---------|-----------|--------|
| Robot Registration | Add new robots | ✓ Via API |
| Robot Listing | View all robots | ✓ Implemented |
| Status Monitoring | Online/busy/offline/error/maintenance | ✓ Implemented |
| Capability Tracking | Track robot capabilities (browser/desktop/gpu/etc.) | ✓ Implemented |
| Load Balancing | Auto-route to least-busy robot | ✓ Implemented |
| Job Routing | Route to specific robot or by capability | ✓ Implemented |
| Job Requeue | Auto-retry on robot rejection | ✓ Implemented |

### 5.3 Job Management

| Feature | Capability | Status |
|---------|-----------|--------|
| Job Submission | Submit workflow to robot | ✓ Implemented |
| Job Tracking | Monitor job progress | ✓ Implemented |
| Job Cancellation | Cancel pending/running jobs | ✓ Via API |
| Job Retry | Retry failed jobs | ✓ Via API |
| Job History | Store job execution records | ✓ PostgreSQL |
| Priority Queue | Support priority-based routing | ✓ Implemented |
| Multi-Tenancy | Isolate robots/jobs by tenant | ✓ PostgreSQL |

### 5.4 Fleet Monitoring

| Feature | Capability | Status |
|---------|-----------|--------|
| Fleet Metrics | Total/online/busy/offline counts | ✓ Implemented |
| Robot Metrics | CPU, memory, job count per robot | ✓ Via API |
| Queue Depth | Monitor pending job queue | ✓ Implemented |
| Activity Feed | Track registration/submission/completion events | ✓ Via API |
| Analytics | Success rates, performance stats, trends | ✓ Via API |
| Real-time Updates | WebSocket for live status changes | ✓ Implemented |

### 5.5 Configuration & Authentication

| Feature | Capability | Status |
|---------|-----------|--------|
| Orchestrator Discovery | Multiple URL fallbacks | ✓ Implemented |
| API Key Auth | Bearer token authentication | ✓ Implemented |
| Config File Support | Load from config.yaml | ✓ Implemented |
| Environment Variables | ORCHESTRATOR_URL, API_KEY | ✓ Implemented |
| Cloudflare Tunnel | Support for tunnel URLs | ✓ Implemented |
| Dev Mode | JWT_DEV_MODE for development | ✓ Supported |

### 5.6 Data Persistence

| Feature | Capability | Status |
|---------|-----------|--------|
| Robot Registry | PostgreSQL persistent storage | ✓ Implemented |
| Job History | Store execution records | ✓ PostgreSQL |
| Metrics History | Track performance over time | ✓ PostgreSQL |
| Local Fallback | In-memory cache for offline mode | ✓ Implemented |

---

## 6. Architecture Limitations & Gaps

### 6.1 Critical Gaps

| Gap | Impact | Severity |
|-----|--------|----------|
| No Workflow Constraints | Can't enforce "only on GPU robots" in workflow definition | Medium |
| Limited Job Prioritization | Priority exists but no priority queue enforcement | Medium |
| No Resource Reservations | Can't pre-allocate capacity for critical jobs | Medium |
| No Job Dependencies | Can't define job chains (job A → job B) | Low |
| No Scaling Policies | Manual robot management only, no auto-scale | Low |
| No Audit Trail | Limited event history, no compliance logging | Medium |

### 6.2 UI/UX Limitations

| Limitation | Impact |
|-----------|--------|
| RobotPickerPanel only in one location | Can't select robot for specific nodes in workflow |
| No robot health dashboard | Hard to diagnose robot issues |
| No bulk robot operations UI | Can't restart all robots at once from UI |
| Limited job monitoring | Can't track job progress in detail from Canvas |
| No robot status details popup | Takes extra click to see full robot info |

### 6.3 Infrastructure Limitations

| Limitation | Impact |
|-----------|--------|
| Single orchestrator instance | No high availability |
| WebSocket reconnection is basic | May lose updates on brief network loss |
| No circuit breaker | API failures can cascade |
| Rate limiting too generous (100/min) | Potential DOS risk |
| Heartbeat timeout is fixed (90s) | Can't tune per-environment |

### 6.4 Code Organization

| Issue | Impact |
|-------|--------|
| RobotController handles too much | Hard to test, violates SRP |
| Conversion logic scattered | RobotData ↔ Robot conversion in multiple places |
| Mixed concerns in RobotManager | Job routing + state management + events |

---

## 7. Integration Points

### 7.1 With Canvas Execution
```
Canvas Main Window
    ↓
RobotController.refresh_robots()
    ↓
OrchestratorClient.get_robots()
    ↓
RobotPickerPanel.update_robots()
    ↓ (User selects mode & robot)
RobotPickerPanel.submit_to_cloud_requested
    ↓
RobotController._submit_current_workflow()
    ↓
RobotController.submit_job(workflow_data, variables, robot_id)
    ↓
OrchestratorClient.POST /api/v1/workflows
    ↓
RobotManager.submit_job() [on orchestrator]
    ↓
Automatic routing to selected robot
    ↓
WebSocket: job_assign message
    ↓
Robot receives & executes
```

### 7.2 With Credentials System
- Robot credentials stored separately in domain/credentials.py
- API keys managed via FleetDashboardDialog > API Keys Tab
- Support for robot-specific authentication

### 7.3 With Event System
```
RobotRegistered ──→ Observable by:
                    - Analytics dashboards
                    - Audit logs
                    - WebSocket subscribers

JobSubmitted ──────→ Observable by:
                    - Job monitor UIs
                    - Activity feeds
                    - Statistics aggregators

JobCompletedOnOrchestrator ──→ Observable by:
                               - Execution monitors
                               - Analytics
                               - Workflow completion handlers
```

---

## 8. Configuration & Deployment

### 8.1 Client-Side Configuration
**File:** `config.yaml` (via ClientConfigManager)
```yaml
orchestrator:
  url: "http://localhost:8000"        # or https://api.casare.net
  api_key: "secret_key_here"          # Optional
```

### 8.2 Environment Variables
```bash
# Primary orchestrator location
export ORCHESTRATOR_URL="http://orchestrator-host:8000"
export ORCHESTRATOR_API_KEY="secret_key"

# Or use cloud tunnel
export CASARE_API_URL="https://api.casare.net"

# Developer mode (no auth required)
export JWT_DEV_MODE=true
```

### 8.3 Orchestrator Setup
```bash
# Start with dev mode (no auth)
JWT_DEV_MODE=true python manage.py orchestrator start

# Or with proper auth (requires API key)
python manage.py orchestrator start
```

---

## 9. Data Flow Diagrams

### 9.1 Job Submission Flow
```
┌─ Canvas UI ─────────────────────┐
│ 1. Select robot from picker     │
│ 2. Click "Submit to Cloud"      │
└─────────┬───────────────────────┘
          │
          ↓
┌─ RobotController ───────────────┐
│ 3. Get workflow data from main  │
│ 4. Extract variables            │
│ 5. Submit via API               │
└─────────┬───────────────────────┘
          │
          ↓ HTTP POST
┌─ Orchestrator (REST API) ───────┐
│ 6. Validate workflow            │
│ 7. Create Job record            │
│ 8. Publish JobSubmitted event   │
└─────────┬───────────────────────┘
          │
          ↓
┌─ RobotManager ──────────────────┐
│ 9. Route to robot (auto or      │
│    specific)                    │
│ 10. Update job status           │
│ 11. Send job_assign via WS      │
└─────────┬───────────────────────┘
          │
          ↓ WebSocket
┌─ Robot ─────────────────────────┐
│ 12. Receive job_assign          │
│ 13. Execute workflow            │
│ 14. Send periodic heartbeat     │
│ 15. Send job_complete           │
└─────────┬───────────────────────┘
          │
          ↓ WebSocket
┌─ RobotManager ──────────────────┐
│ 16. Mark job complete           │
│ 17. Free robot capacity         │
│ 18. Process next job in queue   │
└───────────────────────────────────┘
```

### 9.2 Robot Status Update Flow
```
┌─ Robot ─────────────────────┐
│ 1. Send heartbeat via WS    │
│    {cpu, memory, job_count} │
└──────────┬──────────────────┘
           │
           ↓ WebSocket
┌─ RobotManager ──────────────┐
│ 2. Update last_heartbeat    │
│ 3. Publish RobotHeartbeat   │
│    event                    │
└──────────┬──────────────────┘
           │
           ├─→ Broadcast to admin
           │   connections
           │
           ├─→ Domain event bus
           │
           └─→ Update PgRobotRepository
               (if enabled)
               │
               ↓
┌─ PostgreSQL ────────────────┐
│ 4. Update robots table      │
│    - metrics                │
│    - last_heartbeat         │
│    - status (if changed)    │
└─────────────────────────────┘
```

---

## 10. Best Practices for Extension

### 10.1 Adding a New Robot Command
```python
# 1. Add to RobotController
async def my_robot_command(self, robot_id: str) -> bool:
    if not self._connected:
        return False
    return await self._orchestrator_client._request(
        "POST", f"/api/v1/robots/{robot_id}/my-command"
    ) is not None

# 2. Expose in REST API
@router.post("/robots/{robot_id}/my-command")
async def my_robot_command_endpoint(robot_id: str):
    # Validation, authorization, execution
    pass

# 3. Add domain event if state-changing
@dataclass(frozen=True)
class MyRobotEventHappened(DomainEvent):
    robot_id: str
    # ... other fields
```

### 10.2 Adding Robot Filtering
```python
# RobotPickerPanel._capability_filter.addItems([...])
# Add new filter option:
capability_map = {
    # ... existing
    "New Filter": "new_capability_enum_value",
}

# Make sure Robot.capabilities includes the new RobotCapability enum value
```

### 10.3 Custom Job Routing
```python
# In RobotManager._try_assign_job():
# Instead of just checking availability, add:

available = [
    r for r in self.get_available_robots(...)
    if r.matches_custom_criteria(job)  # Custom predicate
]
```

---

## 11. Testing Recommendations

### 11.1 Unit Tests
```
tests/
├── presentation/
│   └── robot_picker_panel_test.py
│       ├── test_execution_mode_toggle
│       ├── test_robot_filtering
│       └── test_submit_button_state
├── controllers/
│   └── robot_controller_test.py
│       ├── test_orchestrator_connection_fallback
│       ├── test_refresh_robots
│       └── test_submit_job_validation
└── infrastructure/
    └── orchestrator/
        ├── client_test.py
        │   ├── test_robot_listing
        │   └── test_websocket_reconnect
        └── robot_manager_test.py
            ├── test_job_routing
            ├── test_job_requeue
            └── test_robot_heartbeat
```

### 11.2 Integration Tests
```
- Start mock orchestrator
- Register test robots
- Submit jobs
- Verify assignment
- Monitor heartbeats
- Test failover scenarios
```

### 11.3 Load Tests
```
- Submit 100 jobs rapidly
- Verify queue handling
- Monitor memory usage
- Check database performance
```

---

## 12. Migration Path (Local → Cloud)

### Scenario: User switches from local to cloud execution

```
1. Local Mode (Default)
   - Workflow runs on Canvas machine
   - No robot selection available
   - No orchestrator connection needed

2. User clicks "Submit to Cloud"
   ↓

3. RobotPickerPanel enables
   - Prompts to configure orchestrator
   - Attempts connection with fallback URLs
   - Shows available robots

4. User selects robot
   ↓

5. RobotController stores selection
   - Execution mode → "cloud"
   - Selected robot ID → stored

6. Next execution
   - RobotController.submit_job() called
   - Workflow serialized and sent to API
   - Job routes to selected robot

7. Execution completes
   - Event published
   - UI updated
   - Job history recorded
```

---

## 13. Summary Table

### System Components

| Component | Type | Location | Responsibility |
|-----------|------|----------|-----------------|
| RobotPickerPanel | UI | presentation/ui/panels | Execution mode selection, robot picking |
| FleetDashboardDialog | UI | presentation/ui/dialogs | Admin dashboard for fleet management |
| RobotController | Controller | presentation/controllers | Bridge between UI and APIs |
| OrchestratorClient | Client | infrastructure/orchestrator | HTTP + WebSocket communication |
| RobotManager | Manager | infrastructure/orchestrator | In-memory robot + job state |
| PgRobotRepository | Repository | infrastructure/orchestrator/persistence | PostgreSQL persistence |
| Robot | Entity | domain/orchestrator/entities | Domain model for robot |
| RobotStatus/Capability | Enum | domain/orchestrator/entities | Robot state and capabilities |
| Orchestrator Events | Events | domain/orchestrator | DDD event system |

### Feature Coverage Matrix

| Feature | Panel | Controller | Client | Manager | Repository | Domain |
|---------|-------|-----------|--------|---------|------------|--------|
| Robot Selection | ✓ | ✓ |  |  |  | ✓ |
| Execution Mode | ✓ | ✓ |  |  |  |  |
| Job Submission | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Job Routing |  | ✓ |  | ✓ |  |  |
| Heartbeat |  |  | ✓ | ✓ | ✓ |  |
| Persistence |  |  |  | ✓ | ✓ |  |
| Real-time Updates |  | ✓ | ✓ | ✓ |  |  |

---

## Conclusion

CasareRPA's robot fleet management system provides:

1. **Tight Canvas Integration** - Seamless local ↔ cloud switching
2. **Distributed Architecture** - Orchestrator as central hub, robots as agents
3. **DDD Foundation** - Typed events, domain entities, repository pattern
4. **Production-Ready** - PostgreSQL persistence, error handling, multi-tenancy
5. **Extensible Design** - Clear integration points for new features

**Recommended Next Steps:**
1. Add workflow-level robot constraints (capability requirements in workflow definition)
2. Implement job dependency chains (Job A → Job B)
3. Add robot health dashboard with detailed metrics
4. Implement scaling policies (auto-scale based on queue depth)
5. Add audit trail for compliance requirements
