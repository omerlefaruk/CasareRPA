# Robot Reference

The Robot is CasareRPA's headless workflow executor, running as a background service that executes workflows assigned by the Orchestrator.

## Entry Point

```
robot/tray_icon.py
```

The Robot runs as a system tray application on Windows.

## Main Components

### RobotAgent (`agent.py`)

The main execution coordinator with built-in resilience patterns.

```python
class RobotAgent:
    """
    Hardened Robot Agent for CasareRPA.

    Features:
    - Resilient connection with exponential backoff
    - Circuit breaker for failing operations
    - Offline job queue for disconnected operation
    - Job locking to prevent race conditions
    - Progress reporting to Orchestrator
    - Per-node checkpointing for crash recovery
    - Configurable concurrent job execution
    """

    # Key attributes
    robot_id: str               # Unique robot identifier
    name: str                   # Human-readable name
    config: RobotConfig         # Configuration
    connection: ConnectionManager
    circuit_breaker: CircuitBreaker
    offline_queue: OfflineQueue
    checkpoint_manager: CheckpointManager
    metrics: MetricsCollector
    audit: AuditLogger
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `start()` | Start the robot agent |
| `stop()` | Stop the robot agent |
| `execute_job(job)` | Execute a single job |
| `poll_for_jobs()` | Poll orchestrator for new jobs |
| `report_status()` | Report current status to orchestrator |

### JobExecutor (`job_executor.py`)

Executes individual workflow jobs with progress tracking.

```python
class JobExecutor:
    """Executes workflow jobs with checkpointing and progress."""

    async def execute(self, job: Job) -> JobResult:
        # Load workflow
        # Setup execution context
        # Execute nodes with checkpointing
        # Report progress
        # Return result
```

### ConnectionManager (`connection.py`)

Manages WebSocket connection to the Orchestrator with automatic reconnection.

```python
class ConnectionManager:
    """Resilient connection to Orchestrator."""

    # Connection states
    class ConnectionState(Enum):
        DISCONNECTED = "disconnected"
        CONNECTING = "connecting"
        CONNECTED = "connected"
        RECONNECTING = "reconnecting"

    # Features
    - Automatic reconnection with exponential backoff
    - Connection health monitoring
    - Message queuing during disconnection
```

**ConnectionConfig:**
```python
class ConnectionConfig:
    orchestrator_url: str
    heartbeat_interval: float = 30.0
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    reconnect_backoff_factor: float = 2.0
```

### CircuitBreaker (`circuit_breaker.py`)

Fault tolerance pattern preventing cascading failures.

```python
class CircuitBreaker:
    """
    Circuit breaker implementation.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked
    - HALF_OPEN: Testing if service recovered
    """

# Configuration
class CircuitBreakerConfig:
    failure_threshold: int = 5       # Failures before opening
    success_threshold: int = 2       # Successes to close
    timeout: float = 60.0            # Seconds in open state
    half_open_max_calls: int = 3     # Concurrent calls in half-open
```

**Usage:**
```python
breaker = CircuitBreaker("api_calls", config)

@breaker.call
async def api_request():
    # Protected operation
    pass
```

### CheckpointManager (`checkpoint.py`)

Per-node checkpointing for crash recovery.

```python
class CheckpointManager:
    """Manages workflow checkpoints for crash recovery."""

    # Features
    - Save state after each node execution
    - Resume from last checkpoint on restart
    - Compress large state data
    - Automatic cleanup of old checkpoints
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `save_checkpoint(job_id, node_id, context)` | Save execution state |
| `load_checkpoint(job_id)` | Load last checkpoint |
| `has_checkpoint(job_id)` | Check if checkpoint exists |
| `clear_checkpoint(job_id)` | Remove checkpoint after completion |

### OfflineQueue (`offline_queue.py`)

Stores jobs when disconnected from Orchestrator.

```python
class OfflineQueue:
    """Queue for jobs received while offline."""

    # Features
    - Persistent storage (survives restart)
    - FIFO ordering
    - Automatic sync when reconnected
    - Deduplication
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `enqueue(job)` | Add job to queue |
| `dequeue()` | Get next job |
| `peek()` | View next job without removing |
| `sync_with_orchestrator()` | Sync queue state |

### ProgressReporter (`progress_reporter.py`)

Reports execution progress to Orchestrator via Supabase Realtime.

```python
class ProgressReporter:
    """Reports job progress to Orchestrator."""

    async def report_node_started(node_id: str)
    async def report_node_completed(node_id: str, outputs: dict)
    async def report_node_error(node_id: str, error: str)
    async def report_job_completed(result: JobResult)
```

### JobLocker

Prevents concurrent execution of the same job:

```python
class JobLocker:
    """Distributed job locking."""

    async def acquire_lock(job_id: str) -> bool
    async def release_lock(job_id: str)
    async def is_locked(job_id: str) -> bool
```

### CancellationChecker

Checks for job cancellation requests:

```python
class CancellationChecker:
    """Polls for job cancellation."""

    async def is_cancelled(job_id: str) -> bool
    async def acknowledge_cancellation(job_id: str)
```

### MetricsCollector (`metrics.py`)

Collects performance metrics.

```python
class MetricsCollector:
    """Collects robot performance metrics."""

    # Metrics collected
    - Job execution time
    - Node execution time
    - Success/failure rates
    - Queue depths
    - Memory usage
    - CPU usage
```

**Key Methods:**
| Method | Description |
|--------|-------------|
| `record_job_start(job_id)` | Record job start time |
| `record_job_end(job_id, success)` | Record job completion |
| `record_node_execution(node_id, duration)` | Record node timing |
| `get_summary()` | Get metrics summary |

### AuditLogger (`audit.py`)

Comprehensive audit logging.

```python
class AuditLogger:
    """Audit logging for compliance and debugging."""

    # Event types
    class AuditEventType(Enum):
        JOB_RECEIVED = "job_received"
        JOB_STARTED = "job_started"
        JOB_COMPLETED = "job_completed"
        JOB_FAILED = "job_failed"
        NODE_EXECUTED = "node_executed"
        CONNECTION_CHANGED = "connection_changed"
        ERROR = "error"

    # Severity levels
    class AuditSeverity(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
```

### RobotConfig (`config.py`)

Robot configuration management.

```python
class RobotConfig:
    """Robot configuration."""

    robot_id: str                    # Unique identifier
    robot_name: str                  # Display name
    orchestrator_url: str            # Orchestrator WebSocket URL
    supabase_url: str                # Supabase project URL
    supabase_key: str                # Supabase anon key
    max_concurrent_jobs: int = 1     # Concurrent job limit
    heartbeat_interval: float = 30.0 # Heartbeat frequency
    checkpoint_enabled: bool = True  # Enable checkpointing
    checkpoint_dir: Path             # Checkpoint storage location
```

**Loading Config:**
```python
# From environment variables
config = get_config()

# Validate credentials
is_valid = validate_credentials(config)
```

## System Tray (`tray_icon.py`)

System tray interface for the Robot.

**Menu Items:**
- Status indicator (Connected/Disconnected)
- Current job info
- View logs
- Settings
- Exit

**Icons:**
- Green: Connected, idle
- Blue: Connected, executing
- Yellow: Reconnecting
- Red: Disconnected/Error

## Communication Protocol

### With Orchestrator (WebSocket)

```json
// Job assignment
{
    "type": "job_assignment",
    "job_id": "uuid",
    "workflow": { /* workflow JSON */ },
    "variables": { /* input variables */ }
}

// Status update
{
    "type": "status_update",
    "robot_id": "uuid",
    "status": "executing",
    "current_job": "uuid",
    "metrics": { /* metrics data */ }
}

// Job result
{
    "type": "job_result",
    "job_id": "uuid",
    "status": "completed",
    "outputs": { /* result data */ },
    "execution_time": 123.45
}
```

### With Supabase (Realtime)

Progress updates are broadcast via Supabase Realtime:

```python
# Channel: robot:{robot_id}
# Events: node_started, node_completed, job_completed
```

## Lifecycle

```
1. Startup
   ├── Load configuration
   ├── Initialize components
   ├── Connect to Orchestrator
   └── Start polling loop

2. Job Execution
   ├── Receive job assignment
   ├── Acquire job lock
   ├── Load workflow
   ├── Check for checkpoint (resume if exists)
   ├── Execute nodes (with checkpointing)
   ├── Report progress
   ├── Complete/fail job
   └── Release lock

3. Error Handling
   ├── Node error → Retry (if configured)
   ├── Connection lost → Queue locally
   ├── Circuit open → Back off
   └── Crash → Resume from checkpoint

4. Shutdown
   ├── Stop accepting jobs
   ├── Complete current job
   ├── Save checkpoint
   ├── Disconnect gracefully
   └── Exit
```

## Resilience Patterns

### Exponential Backoff

```python
delay = min(
    base_delay * (backoff_factor ** attempt),
    max_delay
)
# With jitter to prevent thundering herd
delay = delay * (0.5 + random.random())
```

### Circuit Breaker States

```
CLOSED ──[failures >= threshold]──> OPEN
   ↑                                  │
   │                                  │
   │                              [timeout]
   │                                  │
   │                                  ↓
   └──[successes >= threshold]── HALF_OPEN
```

### Offline Queue Flow

```
Online Mode:
  Orchestrator → Robot → Execute → Report

Offline Mode:
  Local Queue ← Robot (stores jobs)
                  │
             [reconnect]
                  │
                  ↓
  Local Queue → Robot → Execute → Sync Results
```

## Configuration Files

**Environment Variables:**
```bash
ROBOT_ID=robot-001
ROBOT_NAME="Production Robot 1"
ORCHESTRATOR_URL=wss://orchestrator.example.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

**Config File (robot_config.json):**
```json
{
    "robot_id": "robot-001",
    "robot_name": "Production Robot 1",
    "max_concurrent_jobs": 1,
    "heartbeat_interval": 30,
    "checkpoint_enabled": true,
    "log_level": "INFO"
}
```
