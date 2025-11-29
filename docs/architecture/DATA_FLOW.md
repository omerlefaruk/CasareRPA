# CasareRPA Data Flow Diagrams

This document describes the key data flows within the CasareRPA platform using sequence diagrams and flow charts.

## Table of Contents

1. [Job Submission Flow](#job-submission-flow)
2. [Robot Execution Flow](#robot-execution-flow)
3. [Failover and Recovery Flow](#failover-and-recovery-flow)
4. [Self-Healing Flow](#self-healing-flow)
5. [Trigger Event Flow](#trigger-event-flow)
6. [Workflow Persistence Flow](#workflow-persistence-flow)

---

## Job Submission Flow

This diagram shows the complete flow from job submission to execution start.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Canvas as Canvas (Designer)
    participant Orchestrator as Orchestrator
    participant JobQueue as Job Queue
    participant Dispatcher as Dispatcher
    participant Robot as Robot Agent
    participant Supabase as Supabase Backend

    User->>Canvas: Click "Run Workflow"
    Canvas->>Canvas: Validate workflow
    Canvas->>Canvas: Serialize to JSON

    alt Direct Execution
        Canvas->>Orchestrator: Submit job (WebSocket)
    else Scheduled Execution
        Canvas->>Supabase: Save schedule
        Supabase-->>Orchestrator: Sync schedule
    end

    Orchestrator->>Orchestrator: Create Job object
    Orchestrator->>JobQueue: Enqueue job

    Note over JobQueue: Priority Queue<br/>(Critical > High > Normal > Low)

    JobQueue->>JobQueue: Check duplicates
    JobQueue->>JobQueue: Set state: QUEUED

    loop Dispatch Loop (every 5s)
        Dispatcher->>JobQueue: Get next job
        Dispatcher->>Dispatcher: Select robot (load balancing)

        alt Round Robin
            Dispatcher->>Dispatcher: Next available robot
        else Least Loaded
            Dispatcher->>Dispatcher: Robot with fewest jobs
        else Affinity
            Dispatcher->>Dispatcher: Preferred robot for workflow
        end
    end

    Dispatcher->>Robot: Assign job (WebSocket)
    Robot->>Robot: Check capacity

    alt Robot Available
        Robot-->>Orchestrator: JOB_ACCEPT
        Robot->>Robot: Set state: RUNNING
        Orchestrator->>Supabase: Update job status
    else Robot Busy
        Robot-->>Orchestrator: JOB_REJECT
        Dispatcher->>Dispatcher: Try next robot
    end
```

---

## Robot Execution Flow

This diagram shows workflow execution within the Robot agent.

```mermaid
sequenceDiagram
    autonumber
    participant Orchestrator as Orchestrator
    participant Robot as Robot Agent
    participant Executor as Job Executor
    participant Workflow as Workflow Engine
    participant Checkpoint as Checkpoint Manager
    participant Browser as Playwright Browser
    participant Desktop as UIAutomation

    Orchestrator->>Robot: JOB_ASSIGN (workflow_json)
    Robot->>Executor: Submit job

    Executor->>Executor: Check concurrent limit
    Executor->>Workflow: Parse workflow JSON
    Workflow->>Workflow: Build execution graph

    Note over Workflow: Topological sort<br/>for node ordering

    loop For each node
        Workflow->>Workflow: Get next executable node
        Workflow->>Checkpoint: Save checkpoint

        alt Browser Node
            Workflow->>Browser: Execute action
            Browser-->>Workflow: Result
        else Desktop Node
            Workflow->>Desktop: Execute action
            Desktop-->>Workflow: Result
        else Control Flow Node
            Workflow->>Workflow: Evaluate condition
        else Data Node
            Workflow->>Workflow: Transform data
        end

        Workflow->>Workflow: Update context variables

        alt Success
            Workflow->>Robot: Progress update
            Robot->>Orchestrator: JOB_PROGRESS
        else Error
            alt Retry configured
                Workflow->>Workflow: Retry with backoff
            else No retry
                Workflow->>Robot: Error notification
            end
        end
    end

    alt Workflow Complete
        Workflow->>Robot: Execution complete
        Robot->>Orchestrator: JOB_COMPLETE (result)
        Orchestrator->>Orchestrator: Update metrics
    else Workflow Failed
        Workflow->>Robot: Execution failed
        Robot->>Orchestrator: JOB_FAILED (error)
        Orchestrator->>Orchestrator: Trigger recovery
    end
```

---

## Failover and Recovery Flow

This diagram shows how the system handles robot failures and job recovery.

```mermaid
sequenceDiagram
    autonumber
    participant Orchestrator as Orchestrator
    participant HealthMonitor as Health Monitor
    participant Recovery as Error Recovery Manager
    participant Robot1 as Robot 1 (Failed)
    participant Robot2 as Robot 2 (Healthy)
    participant JobQueue as Job Queue

    Note over Robot1: Robot stops responding

    loop Health Check (every 30s)
        Orchestrator->>Robot1: HEARTBEAT
        Robot1--xOrchestrator: No response
    end

    HealthMonitor->>HealthMonitor: Heartbeat timeout (60s)
    HealthMonitor->>Orchestrator: Robot UNHEALTHY

    Orchestrator->>Orchestrator: Get active jobs on Robot1
    Orchestrator->>Recovery: Handle robot crash

    Note over Recovery: Recovery Strategy Selection

    Recovery->>Recovery: Check retry policy

    alt Retry on Same Robot
        Recovery->>Robot1: Attempt reconnection
        Robot1--xRecovery: Connection failed
        Recovery->>Recovery: Exponential backoff
        Recovery->>Robot1: Retry connection
        Robot1--xRecovery: Max retries exceeded
    end

    Recovery->>Orchestrator: Initiate failover

    loop For each active job
        Orchestrator->>JobQueue: Re-queue job
        JobQueue->>JobQueue: State: QUEUED (preserve priority)
    end

    Note over Orchestrator: Dispatch to healthy robot

    Orchestrator->>Robot2: JOB_ASSIGN
    Robot2->>Robot2: Check for checkpoint

    alt Checkpoint exists
        Robot2->>Robot2: Resume from checkpoint
        Note over Robot2: Skip completed nodes
    else No checkpoint
        Robot2->>Robot2: Start from beginning
    end

    Robot2-->>Orchestrator: JOB_ACCEPT
    Robot2->>Orchestrator: JOB_PROGRESS

    Note over Robot2: Execution continues...

    Robot2->>Orchestrator: JOB_COMPLETE
    Recovery->>Recovery: Record success
```

---

## Self-Healing Flow

This diagram shows the automatic self-healing capabilities of the system.

```mermaid
flowchart TB
    subgraph Detection["Error Detection"]
        A[Error Occurs] --> B{Error Type?}
        B -->|Connection| C[Connection Error]
        B -->|Execution| D[Execution Error]
        B -->|Resource| E[Resource Error]
        B -->|Timeout| F[Timeout Error]
    end

    subgraph Classification["Error Classification"]
        C --> G{Retriable?}
        D --> G
        E --> G
        F --> G

        G -->|Yes| H[Transient Error]
        G -->|No| I[Permanent Error]
    end

    subgraph Recovery["Recovery Actions"]
        H --> J[Calculate Backoff]
        J --> K[Wait]
        K --> L[Retry Operation]

        L --> M{Success?}
        M -->|Yes| N[Resume Normal]
        M -->|No| O{Max Retries?}
        O -->|No| J
        O -->|Yes| P[Failover]

        P --> Q{Alternate Available?}
        Q -->|Yes| R[Switch to Alternate]
        Q -->|No| S[Escalate]

        I --> S
        R --> N

        S --> T[Alert Admin]
        S --> U[Mark Job Failed]
    end

    subgraph Monitoring["Continuous Monitoring"]
        V[Circuit Breaker] --> W{State?}
        W -->|Closed| X[Allow Operations]
        W -->|Open| Y[Block Operations]
        W -->|Half-Open| Z[Test Operations]

        X --> AA{Failure Rate?}
        AA -->|High| AB[Trip Breaker]
        AB --> Y

        Z --> AC{Test Success?}
        AC -->|Yes| X
        AC -->|No| Y
    end

    N --> V
```

### Recovery Strategy Details

| Error Type | Strategy | Max Retries | Backoff | Failover |
|------------|----------|-------------|---------|----------|
| ConnectionError | Retry + Failover | 3 | Exponential | Yes |
| TimeoutError | Retry | 3 | Exponential | Yes |
| NetworkError | Retry + Failover | 3 | Exponential | Yes |
| TemporaryError | Retry | 3 | Exponential | No |
| ResourceBusy | Retry | 3 | Linear | No |
| AuthenticationError | Escalate | 0 | N/A | No |
| ValidationError | Escalate | 0 | N/A | No |

---

## Trigger Event Flow

This diagram shows how triggers initiate workflow executions.

```mermaid
sequenceDiagram
    autonumber
    participant Source as Trigger Source
    participant Trigger as Trigger Instance
    participant Manager as Trigger Manager
    participant Orchestrator as Orchestrator Engine
    participant JobQueue as Job Queue

    alt Webhook Trigger
        Source->>Trigger: HTTP POST /webhook/{id}
    else File Watch Trigger
        Source->>Trigger: File system event
    else Email Trigger
        Source->>Trigger: New email received
    else Scheduled Trigger
        Source->>Trigger: Cron schedule fires
    end

    Trigger->>Trigger: Validate event

    Trigger->>Trigger: Check cooldown
    alt In cooldown
        Trigger-->>Source: Ignored (rate limited)
    else Cooldown passed
        Trigger->>Trigger: Create TriggerEvent
    end

    Note over Trigger: TriggerEvent contains:<br/>- trigger_id<br/>- payload<br/>- metadata<br/>- priority

    Trigger->>Manager: Emit event
    Manager->>Manager: Update trigger stats

    Manager->>Orchestrator: on_trigger_fired(event)

    Orchestrator->>Orchestrator: Load workflow definition
    Orchestrator->>Orchestrator: Create Job with trigger context

    Note over Orchestrator: Job includes:<br/>- trigger_id<br/>- trigger_type<br/>- trigger_payload

    Orchestrator->>JobQueue: Submit job

    JobQueue-->>Orchestrator: Job queued
    Orchestrator-->>Manager: Trigger processed
    Manager-->>Trigger: Success recorded
```

### Trigger Configuration Flow

```mermaid
flowchart LR
    subgraph Configuration["Trigger Configuration"]
        A[Select Trigger Type] --> B[Configure Parameters]
        B --> C[Set Priority]
        C --> D[Set Cooldown]
        D --> E[Associate Workflow]
        E --> F[Validate Config]
        F --> G[Register Trigger]
    end

    subgraph Lifecycle["Trigger Lifecycle"]
        G --> H[INACTIVE]
        H -->|start| I[STARTING]
        I -->|success| J[ACTIVE]
        I -->|failure| K[ERROR]
        J -->|pause| L[PAUSED]
        L -->|resume| J
        J -->|stop| M[STOPPING]
        M --> H
    end
```

---

## Workflow Persistence Flow

This diagram shows how workflows are saved and loaded.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Canvas as Canvas UI
    participant Controller as Workflow Controller
    participant Serializer as JSON Serializer
    participant Storage as Local Storage
    participant Supabase as Supabase Backend

    Note over User,Supabase: Save Workflow

    User->>Canvas: Ctrl+S / Save button
    Canvas->>Controller: save_workflow()

    Controller->>Controller: Collect graph state
    Controller->>Controller: Collect node properties
    Controller->>Controller: Collect connections

    Controller->>Serializer: Serialize to JSON
    Serializer->>Serializer: Use orjson for performance

    Note over Serializer: Workflow Schema:<br/>- metadata<br/>- nodes[]<br/>- connections[]<br/>- variables{}

    Serializer-->>Controller: JSON string

    Controller->>Storage: Write to file
    Storage-->>Controller: File saved

    alt Cloud sync enabled
        Controller->>Supabase: Upload workflow
        Supabase-->>Controller: Sync complete
    end

    Controller-->>Canvas: Save successful
    Canvas-->>User: Status notification

    Note over User,Supabase: Load Workflow

    User->>Canvas: Open workflow
    Canvas->>Controller: load_workflow(path)

    Controller->>Storage: Read file
    Storage-->>Controller: JSON content

    Controller->>Serializer: Deserialize JSON
    Serializer->>Serializer: Validate schema
    Serializer->>Serializer: Version migration

    alt Valid workflow
        Serializer-->>Controller: Workflow object
        Controller->>Canvas: Reconstruct graph
        Canvas->>Canvas: Create nodes
        Canvas->>Canvas: Create connections
        Canvas->>Canvas: Apply properties
        Canvas-->>User: Workflow loaded
    else Invalid workflow
        Serializer-->>Controller: Validation error
        Controller-->>Canvas: Error message
        Canvas-->>User: Load failed
    end
```

### Workflow JSON Schema

```json
{
  "version": "3.0",
  "metadata": {
    "id": "uuid",
    "name": "Workflow Name",
    "description": "Description",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "author": "user@example.com"
  },
  "nodes": [
    {
      "id": "node-uuid",
      "type": "browser.click",
      "name": "Click Login",
      "position": {"x": 100, "y": 200},
      "properties": {
        "selector": "#login-button",
        "timeout": 30000
      }
    }
  ],
  "connections": [
    {
      "source_node": "node-1-uuid",
      "source_port": "output",
      "target_node": "node-2-uuid",
      "target_port": "input"
    }
  ],
  "variables": {
    "url": {"type": "string", "value": "https://example.com"},
    "credentials": {"type": "credential", "ref": "cred-uuid"}
  },
  "triggers": [
    {
      "id": "trigger-uuid",
      "type": "scheduled",
      "config": {"cron": "0 9 * * MON-FRI"}
    }
  ]
}
```

---

## Data Flow Summary

```mermaid
flowchart TB
    subgraph Input["Input Sources"]
        User[User Actions]
        Triggers[Triggers]
        Schedules[Schedules]
        API[External API]
    end

    subgraph Processing["Processing Layer"]
        Canvas[Canvas Designer]
        Orchestrator[Orchestrator]
        Robot[Robot Agents]
    end

    subgraph Storage["Storage Layer"]
        Local[Local Files]
        SQLite[SQLite Queue]
        Supabase[Supabase Cloud]
    end

    subgraph Output["Output Targets"]
        Browser[Web Browsers]
        Desktop[Desktop Apps]
        Files[File Systems]
        DBs[Databases]
        APIs[External APIs]
    end

    User --> Canvas
    Triggers --> Orchestrator
    Schedules --> Orchestrator
    API --> Orchestrator

    Canvas --> Local
    Canvas --> Orchestrator
    Orchestrator --> Supabase
    Orchestrator --> Robot

    Robot --> SQLite
    Robot --> Browser
    Robot --> Desktop
    Robot --> Files
    Robot --> DBs
    Robot --> APIs

    Robot --> Orchestrator
```

## Related Documentation

- [System Overview](SYSTEM_OVERVIEW.md)
- [Component Diagram](COMPONENT_DIAGRAM.md)
- [API Reference](../api/REST_API_REFERENCE.md)
- [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
