# Architecture Diagrams

This document contains Mermaid diagrams illustrating CasareRPA's architecture.

## Layer Dependency Diagram

Shows the dependency direction between architectural layers.

```mermaid
graph TB
    subgraph Presentation ["Presentation Layer"]
        Canvas["Canvas (PySide6)"]
        VisualNodes["Visual Nodes (405)"]
        Controllers["Controllers"]
        Coordinators["Coordinators"]
    end

    subgraph Application ["Application Layer"]
        UseCases["Use Cases"]
        Queries["CQRS Queries"]
        Services["App Services"]
    end

    subgraph Domain ["Domain Layer"]
        Aggregates["Aggregates"]
        Entities["Entities"]
        Events["Domain Events"]
        ValueObjects["Value Objects"]
        Interfaces["Interfaces"]
    end

    subgraph Infrastructure ["Infrastructure Layer"]
        Persistence["Persistence"]
        Browser["Browser (Playwright)"]
        HTTP["HTTP Client"]
        Agent["Robot Agent"]
    end

    Presentation --> Application
    Presentation --> Domain
    Application --> Domain
    Infrastructure --> Domain
    Infrastructure --> Application

    classDef domainStyle fill:#2d5016,stroke:#4a7c23,color:#fff
    classDef appStyle fill:#1a365d,stroke:#2c5282,color:#fff
    classDef infraStyle fill:#744210,stroke:#c05621,color:#fff
    classDef presStyle fill:#553c9a,stroke:#805ad5,color:#fff

    class Domain,Aggregates,Entities,Events,ValueObjects,Interfaces domainStyle
    class Application,UseCases,Queries,Services appStyle
    class Infrastructure,Persistence,Browser,HTTP,Agent infraStyle
    class Presentation,Canvas,VisualNodes,Controllers,Coordinators presStyle
```

## Component Diagram

Shows the three main applications and their relationships.

```mermaid
graph LR
    subgraph Designer ["Canvas (Designer)"]
        MainWindow["Main Window"]
        NodeEditor["Node Editor"]
        PropertyPanel["Property Panel"]
        DebugPanel["Debug Panel"]
    end

    subgraph Executor ["Robot (Executor)"]
        RobotAgent["Robot Agent"]
        JobExecutor["Job Executor"]
        Heartbeat["Heartbeat Service"]
    end

    subgraph Manager ["Orchestrator (Manager)"]
        API["FastAPI Server"]
        JobQueue["Job Queue"]
        RobotRegistry["Robot Registry"]
        Scheduler["Scheduler"]
    end

    subgraph Shared ["Shared Domain"]
        Workflows["Workflows"]
        Nodes["Nodes (413+)"]
        Events["Domain Events"]
    end

    Designer --> Shared
    Executor --> Shared
    Manager --> Shared

    Designer -.->|"Submit Job"| Manager
    Manager -.->|"Assign Job"| Executor
    Executor -.->|"Report Status"| Manager

    classDef canvasStyle fill:#553c9a,stroke:#805ad5,color:#fff
    classDef robotStyle fill:#2d5016,stroke:#4a7c23,color:#fff
    classDef orchStyle fill:#744210,stroke:#c05621,color:#fff
    classDef sharedStyle fill:#1a365d,stroke:#2c5282,color:#fff

    class Designer,MainWindow,NodeEditor,PropertyPanel,DebugPanel canvasStyle
    class Executor,RobotAgent,JobExecutor,Heartbeat robotStyle
    class Manager,API,JobQueue,RobotRegistry,Scheduler orchStyle
    class Shared,Workflows,Nodes,Events sharedStyle
```

## Event Flow Sequence Diagram

Shows how domain events flow through the system.

```mermaid
sequenceDiagram
    participant UC as Use Case
    participant WF as Workflow Aggregate
    participant UoW as Unit of Work
    participant Bus as EventBus
    participant Bridge as Qt Event Bridge
    participant UI as Canvas UI

    UC->>WF: add_node()
    WF->>WF: Create node
    WF->>WF: Collect NodeAdded event

    UC->>UoW: track(workflow)
    UC->>UoW: commit()

    UoW->>WF: collect_events()
    WF-->>UoW: [NodeAdded]

    UoW->>UoW: Persist workflow

    loop For each event
        UoW->>Bus: publish(event)
        Bus->>Bridge: handle_event(event)
        Bridge->>UI: emit Qt signal
        UI->>UI: Update visual node
    end
```

## Workflow Execution Flow

Shows the execution of a workflow from start to finish.

```mermaid
flowchart TD
    Start([Start Workflow]) --> Publish1[Publish WorkflowStarted]

    Publish1 --> GetNext{Get Next Node}

    GetNext --> |Node Found| StartNode[Publish NodeStarted]
    StartNode --> Execute[Execute Node]

    Execute --> |Success| Complete[Publish NodeCompleted]
    Execute --> |Failure| Failed[Publish NodeFailed]

    Complete --> Progress[Publish WorkflowProgress]
    Progress --> GetNext

    Failed --> |Retryable| Retry{Retry?}
    Retry --> |Yes| Execute
    Retry --> |No| WorkflowFailed[Publish WorkflowFailed]

    GetNext --> |No More Nodes| WorkflowComplete[Publish WorkflowCompleted]

    WorkflowFailed --> End([End])
    WorkflowComplete --> End

    style Start fill:#2d5016,stroke:#4a7c23,color:#fff
    style End fill:#553c9a,stroke:#805ad5,color:#fff
    style Complete fill:#1a365d,stroke:#2c5282,color:#fff
    style Failed fill:#744210,stroke:#c05621,color:#fff
```

## Node Execution Sequence

Detailed sequence for executing a single node.

```mermaid
sequenceDiagram
    participant Exec as ExecuteWorkflowUseCase
    participant NE as NodeExecutor
    participant Ctx as ExecutionContext
    participant Node as BaseNode
    participant Bus as EventBus

    Exec->>NE: execute_node(node_id)

    NE->>Bus: publish(NodeStarted)

    NE->>Ctx: get_variables()
    Ctx-->>NE: {variables}

    NE->>NE: resolve_properties(variables)

    NE->>Node: execute(context)

    alt Success
        Node-->>NE: ExecutionResult(success=True)
        NE->>Ctx: set_output(result.data)
        NE->>Bus: publish(NodeCompleted)
    else Failure
        Node-->>NE: ExecutionResult(success=False, error)
        NE->>Bus: publish(NodeFailed)
    end

    NE-->>Exec: result
```

## Aggregate Structure

Shows the internal structure of the Workflow aggregate.

```mermaid
classDiagram
    class Workflow {
        -WorkflowId _id
        -String _name
        -String _description
        -Dict~str,WorkflowNode~ _nodes
        -List~Connection~ _connections
        -List~DomainEvent~ _events
        +add_node(type, position, config) String
        +remove_node(node_id) void
        +connect(src, src_port, tgt, tgt_port) void
        +disconnect(src, src_port, tgt, tgt_port) void
        +collect_events() List~DomainEvent~
        +to_dict() Dict
        +from_dict(data) Workflow
    }

    class WorkflowId {
        +String value
        +generate() WorkflowId
        +from_string(value) WorkflowId
    }

    class WorkflowNode {
        +NodeIdValue id
        +String node_type
        +Position position
        +Dict config
        +move_to(position) void
        +update_config(key, value) void
    }

    class Position {
        +Float x
        +Float y
        +to_dict() Dict
        +from_dict(data) Position
    }

    class Connection {
        +PortReference source
        +PortReference target
        +to_dict() Dict
    }

    class PortReference {
        +String node_id
        +String port_name
        +full_id() String
    }

    Workflow "1" *-- "0..*" WorkflowNode : contains
    Workflow "1" *-- "0..*" Connection : contains
    Workflow "1" --> "1" WorkflowId : identified by
    WorkflowNode "1" --> "1" Position : positioned at
    Connection "1" --> "2" PortReference : connects
```

## Domain Events Hierarchy

Shows the event class hierarchy.

```mermaid
classDiagram
    class DomainEvent {
        <<abstract>>
        +UUID event_id
        +DateTime occurred_on
        +to_dict() Dict
        +event_type_name() String
    }

    class AggregateEvent {
        +String aggregate_id
    }

    class NodeStarted {
        +String node_id
        +String node_type
        +String workflow_id
    }

    class NodeCompleted {
        +String node_id
        +String node_type
        +String workflow_id
        +Float execution_time_ms
        +Dict output_data
    }

    class NodeFailed {
        +String node_id
        +String node_type
        +ErrorCode error_code
        +String error_message
        +Boolean is_retryable
    }

    class WorkflowStarted {
        +String workflow_id
        +String workflow_name
        +ExecutionMode execution_mode
        +Int total_nodes
    }

    class WorkflowCompleted {
        +String workflow_id
        +Float execution_time_ms
        +Int nodes_executed
    }

    class NodeAdded {
        +String workflow_id
        +String node_id
        +String node_type
        +Float position_x
        +Float position_y
    }

    DomainEvent <|-- AggregateEvent
    DomainEvent <|-- NodeStarted
    DomainEvent <|-- NodeCompleted
    DomainEvent <|-- NodeFailed
    DomainEvent <|-- WorkflowStarted
    DomainEvent <|-- WorkflowCompleted
    DomainEvent <|-- NodeAdded
```

## Unit of Work Flow

Shows how Unit of Work manages transactions and event publishing.

```mermaid
flowchart TD
    subgraph UoW ["Unit of Work Context"]
        Enter["__aenter__"]
        Track["track(aggregate)"]
        Commit["commit()"]
        Exit["__aexit__"]
    end

    subgraph CommitProcess ["Commit Process"]
        Collect["Collect events from aggregates"]
        Persist["Persist to storage"]
        Publish["Publish events to EventBus"]
    end

    Start([Start]) --> Enter
    Enter --> Track
    Track --> Track
    Track --> Commit

    Commit --> Collect
    Collect --> Persist

    Persist --> |Success| Publish
    Persist --> |Failure| Rollback["Rollback - discard events"]

    Publish --> Exit
    Rollback --> Exit
    Exit --> End([End])

    style Commit fill:#2d5016,stroke:#4a7c23,color:#fff
    style Rollback fill:#744210,stroke:#c05621,color:#fff
    style Publish fill:#1a365d,stroke:#2c5282,color:#fff
```

## Qt Event Bridge

Shows how domain events are bridged to Qt signals.

```mermaid
flowchart LR
    subgraph Domain ["Domain Layer"]
        NodeExecutor["Node Executor"]
        EventBus["EventBus"]
    end

    subgraph Bridge ["Qt Bridge"]
        QtBridge["QtDomainEventBridge"]
    end

    subgraph Qt ["Qt UI"]
        Signal1["node_started Signal"]
        Signal2["node_completed Signal"]
        Signal3["workflow_progress Signal"]
        Panel["Execution Panel"]
        Highlighter["Node Highlighter"]
    end

    NodeExecutor -->|publish| EventBus
    EventBus -->|subscribe| QtBridge
    QtBridge -->|emit| Signal1
    QtBridge -->|emit| Signal2
    QtBridge -->|emit| Signal3
    Signal1 -->|connect| Panel
    Signal2 -->|connect| Panel
    Signal2 -->|connect| Highlighter
    Signal3 -->|connect| Panel

    style Domain fill:#2d5016,stroke:#4a7c23,color:#fff
    style Bridge fill:#744210,stroke:#c05621,color:#fff
    style Qt fill:#553c9a,stroke:#805ad5,color:#fff
```

## Visual Node Architecture

Shows the relationship between domain nodes and visual nodes.

```mermaid
classDiagram
    class BaseNode {
        <<abstract>>
        +String NODE_NAME
        +List~Port~ inputs
        +List~Port~ outputs
        +Dict config
        +execute(context) ExecutionResult
    }

    class ClickElementNode {
        +execute(context) ExecutionResult
    }

    class VisualNode {
        <<abstract>>
        +String __identifier__
        +String NODE_NAME
        +BaseNode _casare_node
        +setup_ports() void
        +setup_widgets() void
        +update_status(status) void
    }

    class VisualClickElementNode {
        +setup_ports() void
        +setup_widgets() void
    }

    class NodeGraphQt_BaseNode {
        <<external>>
    }

    BaseNode <|-- ClickElementNode
    NodeGraphQt_BaseNode <|-- VisualNode
    VisualNode <|-- VisualClickElementNode
    VisualClickElementNode --> ClickElementNode : wraps

    note for VisualNode "Bridges CasareRPA\nBaseNode with\nNodeGraphQt"
```

## Data Flow: Canvas to Robot

Shows how a workflow flows from design to execution.

```mermaid
sequenceDiagram
    participant Canvas as Canvas (Designer)
    participant Orch as Orchestrator
    participant Queue as Job Queue
    participant Robot as Robot Agent
    participant Exec as Node Executor

    Canvas->>Canvas: Design workflow
    Canvas->>Canvas: Save workflow.json

    Canvas->>Orch: Submit job
    Orch->>Queue: Enqueue job

    Robot->>Queue: Poll for jobs
    Queue-->>Robot: Job assigned

    Robot->>Robot: Load workflow.json

    loop For each node
        Robot->>Exec: Execute node
        Exec-->>Robot: Result
        Robot->>Orch: Report progress
    end

    Robot->>Orch: Job completed
    Orch->>Canvas: Notify completion
```

## Viewing These Diagrams

These Mermaid diagrams can be rendered in:

1. **GitHub/GitLab**: Markdown files with Mermaid blocks render automatically
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Online**: Use [Mermaid Live Editor](https://mermaid.live)
4. **Documentation**: Most static site generators support Mermaid

## Related Documentation

- [Overview](overview.md) - Architecture overview
- [Layers](layers.md) - Layer documentation
- [Events](events.md) - Typed domain events reference
- [Aggregates](aggregates.md) - Workflow aggregate pattern
