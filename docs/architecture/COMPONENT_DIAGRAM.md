# CasareRPA Component Diagram

This document provides detailed component diagrams showing the internal structure and interactions within each major application of the CasareRPA platform.

## Table of Contents

1. [Canvas (Designer) Components](#canvas-designer-components)
2. [Robot (Executor) Components](#robot-executor-components)
3. [Orchestrator (Manager) Components](#orchestrator-manager-components)
4. [Shared Infrastructure Components](#shared-infrastructure-components)
5. [Component Dependencies](#component-dependencies)

---

## Canvas (Designer) Components

```mermaid
C4Component
    title Canvas Application - Component Diagram

    Container_Boundary(canvas, "Canvas Application") {
        Component(main_window, "Main Window", "PySide6", "Primary application window and layout manager")
        Component(node_graph, "Node Graph Widget", "NodeGraphQt", "Visual node editor canvas")
        Component(properties_panel, "Properties Panel", "PySide6", "Node property editor")
        Component(output_console, "Output Console", "PySide6", "Execution logs and debug output")
        Component(minimap, "Minimap", "PySide6", "Canvas overview navigation")

        Component(event_bus, "Event Bus", "Python", "Pub/sub event system")

        Component(workflow_ctrl, "Workflow Controller", "Python", "Workflow operations")
        Component(node_ctrl, "Node Controller", "Python", "Node lifecycle management")
        Component(conn_ctrl, "Connection Controller", "Python", "Port connection handling")
        Component(trigger_ctrl, "Trigger Controller", "Python", "Trigger configuration")
        Component(schedule_ctrl, "Scheduling Controller", "Python", "Schedule management")

        Component(node_registry, "Node Registry", "Python", "Visual node type registration")
        Component(serializer, "Workflow Serializer", "orjson", "JSON serialization")
        Component(validator, "Workflow Validator", "Python", "Schema validation")
    }

    Rel(main_window, node_graph, "Contains")
    Rel(main_window, properties_panel, "Contains")
    Rel(main_window, output_console, "Contains")
    Rel(node_graph, minimap, "Updates")

    Rel(node_graph, event_bus, "Emits events")
    Rel(properties_panel, event_bus, "Emits events")

    Rel(workflow_ctrl, event_bus, "Subscribes")
    Rel(node_ctrl, event_bus, "Subscribes")
    Rel(conn_ctrl, event_bus, "Subscribes")

    Rel(workflow_ctrl, serializer, "Uses")
    Rel(workflow_ctrl, validator, "Uses")
    Rel(node_ctrl, node_registry, "Uses")
```

### Canvas Component Details

| Component | Responsibility | Key Classes |
|-----------|---------------|-------------|
| Main Window | Application shell, menu bar, toolbar | `MainWindow` |
| Node Graph Widget | Visual editing canvas | `NodeGraphWidget`, `CustomNodeItem` |
| Properties Panel | Node configuration UI | `PropertiesPanel`, `PropertyWidgets` |
| Output Console | Log display | `OutputConsoleWidget` |
| Event Bus | Decoupled communication | `EventBus`, `EventBatcher` |
| Workflow Controller | Save/load/execute workflows | `WorkflowController` |
| Node Controller | Create/delete/configure nodes | `NodeController` |
| Connection Controller | Validate and manage connections | `ConnectionController` |
| Node Registry | Node type catalog | `NodeRegistry` |

### Controller Interactions

```mermaid
flowchart TB
    subgraph Controllers["Controllers"]
        WC[Workflow Controller]
        NC[Node Controller]
        CC[Connection Controller]
        TC[Trigger Controller]
        SC[Scheduling Controller]
        PC[Project Controller]
        VC[Viewport Controller]
    end

    subgraph EventBus["Event Bus"]
        EB[Event Bus]
    end

    subgraph UI["UI Components"]
        MW[Main Window]
        NG[Node Graph]
        PP[Properties Panel]
    end

    MW -->|user action| EB
    NG -->|node events| EB
    PP -->|property change| EB

    EB -->|workflow.save| WC
    EB -->|node.created| NC
    EB -->|connection.made| CC
    EB -->|trigger.config| TC
    EB -->|schedule.create| SC
    EB -->|project.open| PC
    EB -->|viewport.zoom| VC

    WC -->|update| MW
    NC -->|update| NG
    CC -->|validate| NG
```

---

## Robot (Executor) Components

```mermaid
C4Component
    title Robot Agent - Component Diagram

    Container_Boundary(robot, "Robot Application") {
        Component(agent, "Robot Agent", "Python", "Main agent controller")

        Component(conn_mgr, "Connection Manager", "Python", "Supabase connection with resilience")
        Component(ws_client, "WebSocket Client", "websockets", "Orchestrator communication")
        Component(circuit_breaker, "Circuit Breaker", "Python", "Fault isolation")

        Component(job_executor, "Job Executor", "Python", "Concurrent job execution")
        Component(workflow_engine, "Workflow Engine", "Python", "Graph traversal and node execution")

        Component(checkpoint_mgr, "Checkpoint Manager", "Python", "Execution state persistence")
        Component(offline_queue, "Offline Queue", "SQLite", "Job queue for disconnected operation")

        Component(progress_reporter, "Progress Reporter", "Python", "Real-time progress updates")
        Component(job_locker, "Job Locker", "Python", "Distributed job locking")

        Component(metrics, "Metrics Collector", "Python", "Performance metrics")
        Component(audit, "Audit Logger", "Python", "Security audit trail")

        Component(playwright_mgr, "Playwright Manager", "Playwright", "Browser automation")
        Component(uiautomation, "UIAutomation", "uiautomation", "Desktop automation")
    }

    Rel(agent, conn_mgr, "Uses")
    Rel(agent, ws_client, "Uses")
    Rel(agent, job_executor, "Manages")

    Rel(conn_mgr, circuit_breaker, "Protected by")

    Rel(job_executor, workflow_engine, "Runs")
    Rel(job_executor, checkpoint_mgr, "Checkpoints to")
    Rel(job_executor, progress_reporter, "Reports via")

    Rel(workflow_engine, playwright_mgr, "Browser ops")
    Rel(workflow_engine, uiautomation, "Desktop ops")

    Rel(agent, offline_queue, "Queues to")
    Rel(agent, metrics, "Records to")
    Rel(agent, audit, "Logs to")
```

### Robot Component Details

| Component | Responsibility | Key Classes |
|-----------|---------------|-------------|
| Robot Agent | Main lifecycle controller | `RobotAgent` |
| Connection Manager | Supabase connection with backoff | `ConnectionManager`, `ConnectionConfig` |
| WebSocket Client | Bidirectional Orchestrator communication | `RobotWebSocketClient` |
| Circuit Breaker | Prevent cascade failures | `CircuitBreaker`, `CircuitBreakerConfig` |
| Job Executor | Concurrent job execution | `JobExecutor` |
| Workflow Engine | Node-by-node execution | `WorkflowEngine` |
| Checkpoint Manager | Crash recovery | `CheckpointManager` |
| Offline Queue | Disconnected operation | `OfflineQueue` |
| Progress Reporter | Real-time updates | `ProgressReporter` |
| Playwright Manager | Browser automation | `PlaywrightManager` |

### Execution Flow

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Connecting: start()
    Connecting --> Connected: connection success
    Connecting --> Reconnecting: connection failed

    Reconnecting --> Connecting: retry
    Reconnecting --> Offline: max retries

    Offline --> Connecting: network restored

    Connected --> Executing: job received
    Connected --> Idle: shutdown

    Executing --> Checkpointing: node complete
    Checkpointing --> Executing: next node
    Executing --> Reporting: progress update
    Reporting --> Executing: continue
    Executing --> Connected: job complete
    Executing --> Recovering: error occurred

    Recovering --> Executing: retry success
    Recovering --> Connected: failover/give up

    Connected --> [*]: stop()
```

---

## Orchestrator (Manager) Components

```mermaid
C4Component
    title Orchestrator - Component Diagram

    Container_Boundary(orchestrator, "Orchestrator Application") {
        Component(engine, "Orchestrator Engine", "Python", "Central coordination")

        Component(job_queue, "Job Queue", "Python", "Priority queue with state machine")
        Component(deduplicator, "Deduplicator", "Python", "Prevent duplicate jobs")
        Component(timeout_mgr, "Timeout Manager", "Python", "Job timeout tracking")

        Component(scheduler, "Job Scheduler", "APScheduler", "Cron-based scheduling")
        Component(dispatcher, "Job Dispatcher", "Python", "Robot selection and load balancing")
        Component(robot_pool, "Robot Pool", "Python", "Robot connection management")

        Component(ws_server, "WebSocket Server", "websockets", "Robot communication")
        Component(trigger_mgr, "Trigger Manager", "Python", "Trigger lifecycle management")

        Component(recovery_mgr, "Error Recovery Manager", "Python", "Failover and retry")
        Component(health_monitor, "Health Monitor", "Python", "Robot health tracking")
        Component(security_mgr, "Security Manager", "Python", "Token auth, rate limiting")

        Component(service, "Orchestrator Service", "Python", "Data persistence")
        Component(local_storage, "Local Storage", "JSON", "Job and workflow storage")
    }

    Rel(engine, job_queue, "Manages")
    Rel(engine, scheduler, "Schedules via")
    Rel(engine, dispatcher, "Dispatches via")
    Rel(engine, ws_server, "Communicates via")
    Rel(engine, trigger_mgr, "Triggers via")

    Rel(job_queue, deduplicator, "Checks")
    Rel(job_queue, timeout_mgr, "Tracks")

    Rel(dispatcher, robot_pool, "Selects from")
    Rel(dispatcher, job_queue, "Dequeues from")

    Rel(ws_server, robot_pool, "Updates")
    Rel(ws_server, health_monitor, "Feeds")

    Rel(engine, recovery_mgr, "Recovers via")
    Rel(engine, security_mgr, "Secures via")

    Rel(engine, service, "Persists via")
    Rel(service, local_storage, "Stores in")
```

### Orchestrator Component Details

| Component | Responsibility | Key Classes |
|-----------|---------------|-------------|
| Orchestrator Engine | Central coordination | `OrchestratorEngine` |
| Job Queue | Priority-based job management | `JobQueue`, `JobStateMachine` |
| Job Scheduler | Time-based execution | `JobScheduler` |
| Job Dispatcher | Robot selection | `JobDispatcher`, `LoadBalancingStrategy` |
| WebSocket Server | Robot communication | `OrchestratorServer`, `RobotConnection` |
| Trigger Manager | Trigger lifecycle | `TriggerManager` |
| Error Recovery Manager | Failover handling | `ErrorRecoveryManager`, `RetryPolicy` |
| Health Monitor | Robot health | `HealthMonitor`, `HealthMetrics` |
| Security Manager | Authentication | `SecurityManager`, `AuthToken` |

### Load Balancing Strategies

```mermaid
flowchart TB
    subgraph Strategies["Load Balancing Strategies"]
        RR[Round Robin]
        LL[Least Loaded]
        RN[Random]
        AF[Affinity]
    end

    subgraph Selection["Robot Selection"]
        Queue[Job Queue] --> Dispatcher
        Dispatcher --> |strategy| Strategies
        Strategies --> RobotPool[Robot Pool]
        RobotPool --> |available robots| Filter
        Filter --> |environment match| Selected[Selected Robot]
    end

    subgraph Metrics["Selection Metrics"]
        LL --> CurrentJobs[Current Jobs]
        LL --> MaxConcurrent[Max Concurrent]
        AF --> History[Execution History]
        AF --> SuccessRate[Success Rate]
    end
```

---

## Shared Infrastructure Components

```mermaid
C4Component
    title Shared Infrastructure - Component Diagram

    Container_Boundary(shared, "Shared Components") {
        Component(domain, "Domain Layer", "Python", "Business entities and logic")
        Component(app_layer, "Application Layer", "Python", "Use cases and services")
        Component(infra, "Infrastructure Layer", "Python", "External integrations")

        Component(nodes, "Node Library", "Python", "Automation node implementations")
        Component(triggers, "Trigger Library", "Python", "Trigger implementations")

        Component(utils, "Utilities", "Python", "Shared utilities")
        Component(security, "Security Utils", "Python", "Encryption, credentials")
        Component(pooling, "Connection Pooling", "Python", "Resource management")
        Component(resilience, "Resilience Utils", "Python", "Retry, circuit breaker")
    }

    Rel(app_layer, domain, "Uses")
    Rel(infra, domain, "Implements")

    Rel(nodes, domain, "Uses")
    Rel(triggers, domain, "Uses")

    Rel(utils, security, "Contains")
    Rel(utils, pooling, "Contains")
    Rel(utils, resilience, "Contains")
```

### Node Architecture

```mermaid
classDiagram
    class BaseNode {
        <<abstract>>
        +id: str
        +name: str
        +execute(context) NodeResult
        +validate() ValidationResult
    }

    class BrowserNode {
        <<abstract>>
        #browser: Browser
        #page: Page
    }

    class DesktopNode {
        <<abstract>>
        #element: UIElement
    }

    class ControlFlowNode {
        <<abstract>>
        +evaluate(context) bool
    }

    class DataNode {
        <<abstract>>
        +transform(data) Any
    }

    BaseNode <|-- BrowserNode
    BaseNode <|-- DesktopNode
    BaseNode <|-- ControlFlowNode
    BaseNode <|-- DataNode

    BrowserNode <|-- ClickNode
    BrowserNode <|-- TypeNode
    BrowserNode <|-- NavigateNode

    DesktopNode <|-- DesktopClickNode
    DesktopNode <|-- DesktopTypeNode

    ControlFlowNode <|-- IfNode
    ControlFlowNode <|-- ForEachNode
    ControlFlowNode <|-- WhileNode

    DataNode <|-- SetVariableNode
    DataNode <|-- TransformNode
```

---

## Component Dependencies

### Dependency Matrix

| Component | Canvas | Robot | Orchestrator | Domain | Infrastructure |
|-----------|--------|-------|--------------|--------|----------------|
| Canvas | - | No | WebSocket | Yes | Yes |
| Robot | No | - | WebSocket | Yes | Yes |
| Orchestrator | WebSocket | WebSocket | - | Yes | Yes |
| Domain | No | No | No | - | No |
| Infrastructure | No | No | No | Yes | - |

### External Dependencies

```mermaid
flowchart LR
    subgraph CasareRPA["CasareRPA"]
        Canvas
        Robot
        Orchestrator
    end

    subgraph Python["Python Ecosystem"]
        PySide6[PySide6]
        NodeGraphQt
        Playwright
        UIAutomation[uiautomation]
        APScheduler
        websockets
        orjson
        loguru
        pydantic
    end

    subgraph External["External Services"]
        Supabase
        Browsers[Browser Engines]
        WindowsAPI[Windows API]
    end

    Canvas --> PySide6
    Canvas --> NodeGraphQt
    Canvas --> orjson

    Robot --> Playwright
    Robot --> UIAutomation
    Robot --> websockets

    Orchestrator --> PySide6
    Orchestrator --> APScheduler
    Orchestrator --> websockets

    Playwright --> Browsers
    UIAutomation --> WindowsAPI
    Robot --> Supabase
    Orchestrator --> Supabase
```

### Package Structure

```
src/casare_rpa/
    domain/
        entities/          # Business entities
        value_objects/     # Immutable value types
        services/          # Domain services
        repositories/      # Repository interfaces

    application/
        use_cases/         # Application use cases
        services/          # Application services
        execution/         # Workflow execution
        scheduling/        # Schedule management
        workflow/          # Workflow operations

    infrastructure/
        persistence/       # Storage implementations
        events/            # Event infrastructure

    presentation/
        canvas/            # Designer application
            controllers/   # Controller classes
            graph/         # Node graph components
            visual_nodes/  # Visual node wrappers
            ui/            # UI widgets and dialogs

    orchestrator/          # Orchestrator application
        panels/            # UI panels
        views/             # Dashboard views

    robot/                 # Robot application

    nodes/                 # Node implementations
        browser/           # Browser automation nodes
        desktop/           # Desktop automation nodes
        control_flow/      # Control flow nodes
        data/              # Data operation nodes

    triggers/              # Trigger implementations
        implementations/   # Concrete triggers

    utils/                 # Shared utilities
        security/          # Security utilities
        pooling/           # Connection pooling
        resilience/        # Resilience patterns
```

---

## Deployment Topologies

### Single-Node Deployment

```mermaid
flowchart TB
    subgraph SingleMachine["Single Machine"]
        Canvas[Canvas Designer]
        Robot[Robot Agent]
        LocalFiles[Local Storage]
    end

    User[User] --> Canvas
    Canvas --> LocalFiles
    Canvas --> Robot
    Robot --> LocalFiles

    Robot --> TargetApps[Target Applications]
```

### Multi-Robot Deployment

```mermaid
flowchart TB
    subgraph DesignerMachine["Designer Machine"]
        Canvas[Canvas Designer]
    end

    subgraph OrchestratorMachine["Orchestrator Server"]
        Orchestrator[Orchestrator]
        DB[(Database)]
    end

    subgraph RobotMachine1["Robot Machine 1"]
        Robot1[Robot Agent 1]
    end

    subgraph RobotMachine2["Robot Machine 2"]
        Robot2[Robot Agent 2]
    end

    subgraph RobotMachine3["Robot Machine 3"]
        Robot3[Robot Agent 3]
    end

    Canvas -->|submit jobs| Orchestrator
    Orchestrator --> DB

    Orchestrator <-->|WebSocket| Robot1
    Orchestrator <-->|WebSocket| Robot2
    Orchestrator <-->|WebSocket| Robot3

    Robot1 --> Apps1[Target Apps]
    Robot2 --> Apps2[Target Apps]
    Robot3 --> Apps3[Target Apps]
```

### Cloud-Hybrid Deployment

```mermaid
flowchart TB
    subgraph OnPremise["On-Premise"]
        Canvas[Canvas Designer]
        Robot1[Robot Agent 1]
        Robot2[Robot Agent 2]
    end

    subgraph Cloud["Cloud (Supabase)"]
        Supabase[(Supabase)]
        Realtime[Realtime Service]
    end

    subgraph Orchestrator["Orchestrator (Cloud/On-Prem)"]
        OrchestratorApp[Orchestrator]
    end

    Canvas -->|save workflows| Supabase
    Canvas -->|submit jobs| OrchestratorApp

    OrchestratorApp --> Supabase
    OrchestratorApp --> Realtime

    Robot1 <-->|WebSocket| OrchestratorApp
    Robot2 <-->|WebSocket| OrchestratorApp

    Robot1 -->|progress| Realtime
    Robot2 -->|progress| Realtime

    Robot1 -->|offline sync| Supabase
    Robot2 -->|offline sync| Supabase
```

---

## Related Documentation

- [System Overview](SYSTEM_OVERVIEW.md)
- [Data Flow Diagrams](DATA_FLOW.md)
- [API Reference](../api/REST_API_REFERENCE.md)
- [Security Architecture](../security/SECURITY_ARCHITECTURE.md)
