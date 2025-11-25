# Orchestrator Reference

The Orchestrator is CasareRPA's centralized management system for robots, job scheduling, and workflow distribution.

## Entry Point

```
orchestrator/main_window.py
```

## Main Components

### OrchestratorEngine (`engine.py`)

The main orchestration coordinator integrating all components.

```python
class OrchestratorEngine:
    """
    Main orchestrator engine that coordinates all components.

    Components:
    - JobQueue: Priority queue with state machine
    - JobScheduler: Cron-based scheduling
    - JobDispatcher: Robot selection and load balancing
    - OrchestratorService: Data persistence
    """

    def __init__(
        self,
        service: OrchestratorService,
        load_balancing: str = "least_loaded",
        dispatch_interval: int = 5,
        timeout_check_interval: int = 30,
        default_job_timeout: int = 3600
    ):
        ...
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `start()` | Start the orchestrator engine |
| `stop()` | Stop the orchestrator engine |
| `submit_job(workflow, variables, priority)` | Submit a new job |
| `cancel_job(job_id)` | Cancel a running job |
| `get_job_status(job_id)` | Get job status |
| `register_robot(robot)` | Register a robot |
| `unregister_robot(robot_id)` | Unregister a robot |
| `get_dashboard_metrics()` | Get dashboard metrics |

### JobScheduler (`scheduler.py`)

Cron-based job scheduling using APScheduler.

```python
class JobScheduler:
    """Schedules jobs based on cron expressions."""

    # Supported frequencies
    class ScheduleFrequency(Enum):
        ONCE = "once"
        HOURLY = "hourly"
        DAILY = "daily"
        WEEKLY = "weekly"
        MONTHLY = "monthly"
        CRON = "cron"  # Custom cron expression
```

**Cron Expression Support:**
```python
# Standard 5-field: minute hour day month weekday
"0 9 * * 1-5"  # 9 AM weekdays

# Extended 6-field: second minute hour day month weekday
"0 0 9 * * 1-5"  # 9:00:00 AM weekdays
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `add_schedule(schedule)` | Add a schedule |
| `remove_schedule(schedule_id)` | Remove a schedule |
| `update_schedule(schedule)` | Update a schedule |
| `pause_schedule(schedule_id)` | Pause a schedule |
| `resume_schedule(schedule_id)` | Resume a schedule |
| `get_next_run(schedule_id)` | Get next run time |

### JobDispatcher (`dispatcher.py`)

Dispatches jobs to robots with load balancing.

```python
class JobDispatcher:
    """Dispatches jobs to available robots."""

    # Load balancing strategies
    class LoadBalancingStrategy(Enum):
        ROUND_ROBIN = "round_robin"
        LEAST_LOADED = "least_loaded"
        RANDOM = "random"
        AFFINITY = "affinity"  # Prefer same robot for workflow
```

**RobotPool:**
```python
class RobotPool:
    """Manages pool of available robots."""

    def get_available_robot(strategy) -> Optional[Robot]
    def add_robot(robot)
    def remove_robot(robot_id)
    def update_robot_load(robot_id, load)
```

### JobQueue (`job_queue.py`)

Priority queue with job state machine.

```python
class JobQueue:
    """Priority queue for jobs with state machine."""

    # Job states
    class JobStatus(Enum):
        PENDING = "pending"
        QUEUED = "queued"
        DISPATCHED = "dispatched"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
        TIMEOUT = "timeout"
```

**JobStateMachine:**
Valid state transitions:
```
PENDING → QUEUED → DISPATCHED → RUNNING → COMPLETED
                                       → FAILED
                                       → CANCELLED
                                       → TIMEOUT
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `enqueue(job)` | Add job to queue |
| `dequeue()` | Get next job by priority |
| `peek()` | View next job |
| `update_status(job_id, status)` | Update job status |
| `get_by_status(status)` | Get jobs by status |

### OrchestratorService (`services.py`)

Business logic and data persistence.

```python
class OrchestratorService:
    """Core business logic for orchestrator."""

    # CRUD operations for:
    - Workflows
    - Jobs
    - Robots
    - Schedules
    - Results
```

### CloudService (`cloud_service.py`)

Supabase cloud integration.

```python
class CloudService:
    """Supabase cloud backend integration."""

    # Features
    - Workflow storage
    - Job persistence
    - Robot registry
    - Execution results
    - Audit logs
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `save_workflow(workflow)` | Save workflow to cloud |
| `load_workflow(workflow_id)` | Load workflow from cloud |
| `save_job_result(result)` | Save execution result |
| `get_robot_status(robot_id)` | Get robot status |

### RealtimeService (`realtime_service.py`)

Supabase Realtime event streaming.

```python
class RealtimeService:
    """Real-time event streaming via Supabase."""

    # Channels
    - robots:{org_id}      # Robot status updates
    - jobs:{org_id}        # Job status updates
    - progress:{job_id}    # Execution progress
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `subscribe(channel, callback)` | Subscribe to channel |
| `unsubscribe(channel)` | Unsubscribe from channel |
| `broadcast(channel, event, data)` | Broadcast event |

### Client (`client.py`)

Robot client management.

```python
class RobotClient:
    """Represents a connected robot."""

    robot_id: str
    name: str
    status: RobotStatus
    websocket: WebSocket
    last_heartbeat: datetime
    current_job: Optional[str]
    capabilities: List[str]
    load: float
```

### Server (`server.py`)

WebSocket server for robot connections.

```python
class OrchestratorServer:
    """WebSocket server for robot communication."""

    async def start(host, port)
    async def stop()
    async def send_job(robot_id, job)
    async def broadcast(message)
```

## Data Models (`models.py`)

### Job

```python
class Job:
    job_id: str
    workflow_id: str
    workflow: Workflow
    status: JobStatus
    priority: JobPriority
    variables: Dict[str, Any]
    robot_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[JobResult]
    error: Optional[str]
    timeout: int
```

### Robot

```python
class Robot:
    robot_id: str
    name: str
    status: RobotStatus
    last_seen: datetime
    current_job: Optional[str]
    capabilities: List[str]
    tags: List[str]
    max_concurrent_jobs: int
    metrics: RobotMetrics
```

### Schedule

```python
class Schedule:
    schedule_id: str
    workflow_id: str
    frequency: ScheduleFrequency
    cron_expression: Optional[str]
    timezone: str
    enabled: bool
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    variables: Dict[str, Any]
    robot_id: Optional[str]  # Affinity
```

### Workflow

```python
class Workflow:
    workflow_id: str
    name: str
    description: str
    version: str
    status: WorkflowStatus
    content: Dict  # Workflow JSON
    created_at: datetime
    updated_at: datetime
    tags: List[str]
```

### DashboardMetrics

```python
class DashboardMetrics:
    total_robots: int
    online_robots: int
    offline_robots: int
    total_jobs_today: int
    completed_jobs_today: int
    failed_jobs_today: int
    pending_jobs: int
    running_jobs: int
    average_execution_time: float
    success_rate: float
```

## UI Panels

### MainWindow (`main_window.py`)

Primary orchestrator UI window with panels.

### DashboardPanel (`panels/dashboard_panel.py`)

Overview dashboard with metrics and charts.

```python
class DashboardPanel(QWidget):
    """Main dashboard with KPIs and charts."""

    # Widgets
    - Robot count card
    - Job statistics card
    - Success rate chart
    - Recent activity list
```

### RobotsPanel (`panels/robots_panel.py`)

Robot management panel.

```python
class RobotsPanel(QWidget):
    """Robot fleet management."""

    # Features
    - Robot list with status indicators
    - Robot details view
    - Send job to robot
    - View robot logs
```

### JobsPanel (`panels/jobs_panel.py`)

Job management panel.

```python
class JobsPanel(QWidget):
    """Job queue management."""

    # Features
    - Job queue table
    - Job details view
    - Cancel/retry jobs
    - Filter by status
```

### MetricsPanel (`panels/metrics_panel.py`)

Performance metrics panel.

```python
class MetricsPanel(QWidget):
    """Performance metrics and analytics."""

    # Charts
    - Execution time trends
    - Success/failure rates
    - Robot utilization
    - Queue depth over time
```

### TreePanel (`panels/tree_panel.py`)

Workflow/folder tree navigation.

### DetailPanel (`panels/detail_panel.py`)

Detail view for selected items.

## Resilience (`resilience.py`)

Error recovery patterns.

```python
class RetryPolicy:
    """Configurable retry policy."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retryable_errors: List[Type[Exception]]
```

## Results (`results.py`)

Execution result handling.

```python
class JobResult:
    job_id: str
    status: JobStatus
    outputs: Dict[str, Any]
    logs: List[LogEntry]
    execution_time: float
    node_results: Dict[str, NodeResult]
    error: Optional[ErrorInfo]
```

## Communication Protocol (`protocol.py`)

WebSocket message protocol.

```python
# Message types
class MessageType(Enum):
    HEARTBEAT = "heartbeat"
    JOB_ASSIGNMENT = "job_assignment"
    JOB_RESULT = "job_result"
    STATUS_UPDATE = "status_update"
    CANCEL_JOB = "cancel_job"
    ROBOT_REGISTERED = "robot_registered"
    ERROR = "error"
```

**Message Format:**
```json
{
    "type": "job_assignment",
    "id": "msg-uuid",
    "timestamp": "2025-01-01T00:00:00Z",
    "payload": {
        "job_id": "job-uuid",
        "workflow": { /* ... */ },
        "variables": { /* ... */ }
    }
}
```

## Workflow Distribution (`distribution.py`)

Workflow deployment to robots.

```python
class WorkflowDistributor:
    """Distributes workflows to robot fleet."""

    async def deploy(workflow_id, robot_ids)
    async def undeploy(workflow_id, robot_ids)
    async def get_deployment_status(workflow_id)
```

## Configuration

**Environment Variables:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8765
DEFAULT_JOB_TIMEOUT=3600
DISPATCH_INTERVAL=5
```

## Lifecycle

```
1. Startup
   ├── Initialize engine
   ├── Connect to Supabase
   ├── Start WebSocket server
   ├── Load schedules
   └── Start scheduler

2. Operation
   ├── Accept robot connections
   ├── Process job submissions
   ├── Execute schedules
   ├── Dispatch jobs
   ├── Monitor robot health
   └── Collect metrics

3. Job Flow
   ├── Submit job (API/Schedule)
   ├── Enqueue with priority
   ├── Select robot (load balancing)
   ├── Dispatch job
   ├── Monitor progress
   ├── Receive result
   └── Store result

4. Shutdown
   ├── Stop scheduler
   ├── Complete/cancel pending jobs
   ├── Disconnect robots gracefully
   └── Save state
```

## Load Balancing Strategies

### Round Robin
Sequential distribution across robots.

### Least Loaded
Assign to robot with lowest current load.

### Random
Random robot selection (useful for homogeneous fleets).

### Affinity
Prefer same robot for repeated workflow executions (cache benefits).

## Monitoring

### Health Checks
- Robot heartbeat monitoring
- Connection state tracking
- Job timeout detection

### Metrics
- Job throughput
- Average execution time
- Queue depth
- Robot utilization
- Error rates

### Alerts (Future)
- Robot disconnected
- Job timeout
- High error rate
- Queue backlog
