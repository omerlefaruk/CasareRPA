# CasareRPA Architecture

## System Overview

CasareRPA is a Windows Desktop RPA platform consisting of three interconnected applications:

```
+------------------+      +------------------+      +------------------+
|     CANVAS       |      |   ORCHESTRATOR   |      |      ROBOT       |
|  (Visual Editor) |----->| (Job Management) |----->| (Executor Agent) |
+------------------+      +------------------+      +------------------+
        |                         |                         |
        v                         v                         v
   +----------+            +----------+              +----------+
   | Workflow |            |  Supabase |             | Workflow |
   |   JSON   |            |   Cloud   |             | Execution|
   +----------+            +----------+              +----------+
```

## Application Architecture

### 1. Canvas (Visual Workflow Editor)

**Entry Point:** `run.py` → `casare_rpa.canvas.app:CasareRPAApp`

The Canvas is the primary development environment where users design automation workflows using a node-based visual interface.

```
canvas/
├── app.py                  # CasareRPAApp - Main application class
├── main_window.py          # MainWindow - Primary UI container
├── node_search_dialog.py   # Node palette with fuzzy search
├── searchable_menu.py      # Right-click node creation menu
├── visual_nodes/           # Visual wrappers for node logic
│   └── desktop_visual.py   # Desktop automation visual nodes
├── node_frame.py           # Node grouping/framing system
├── node_icons.py           # SVG icons for node types
├── minimap.py              # Workflow overview navigation
├── viewport_culling.py     # Performance optimization
├── custom_pipe.py          # Connection line rendering
├── debug_toolbar.py        # Execution debugging controls
├── log_viewer.py           # Real-time log display
├── variable_inspector.py   # Runtime variable viewer
├── execution_history_viewer.py  # Execution trace viewer
├── template_browser.py     # Workflow template manager
├── selector_dialog.py      # Web element selector builder
├── desktop_selector_builder.py  # Desktop element selector
├── element_picker.py       # Live element selection
├── element_tree_widget.py  # UI Automation tree view
├── selector_strategy.py    # Selector generation strategies
├── selector_validator.py   # Selector validation
├── selector_integration.py # Node integration for selectors
├── recording_dialog.py     # Web recording interface
├── desktop_recording_panel.py   # Desktop recording interface
├── hotkey_manager.py       # Keyboard shortcuts
└── rich_comment_node.py    # Annotation nodes
```

### 2. Robot (Executor Agent)

**Entry Point:** `robot/tray_icon.py`

The Robot runs as a background service (system tray application) that executes workflows assigned by the Orchestrator.

```
robot/
├── tray_icon.py        # System tray interface & entry point
├── agent.py            # RobotAgent - Main execution coordinator
├── executor.py         # Job execution engine
├── connection.py       # Orchestrator connection manager
├── checkpoint.py       # Workflow checkpoint/resume system
├── circuit_breaker.py  # Fault tolerance pattern
├── job_manager.py      # Job lifecycle management
├── offline_queue.py    # Offline job queuing
├── heartbeat.py        # Health monitoring
├── metrics.py          # Performance metrics collection
├── config.py           # Robot configuration
└── audit.py            # Execution audit logging
```

### 3. Orchestrator (Workflow Manager)

**Entry Point:** `orchestrator/main_window.py`

The Orchestrator provides centralized management of robots, job scheduling, and workflow distribution.

```
orchestrator/
├── main_window.py      # Main UI window
├── engine.py           # OrchestratorEngine - Core coordination
├── scheduler.py        # Job scheduling system
├── dispatcher.py       # Job dispatch to robots
├── job_queue.py        # Job queue management
├── cloud_service.py    # Supabase cloud integration
├── realtime_service.py # Real-time event streaming
├── client.py           # Robot client management
├── server.py           # WebSocket server
├── models.py           # Data models
├── protocol.py         # Communication protocol
├── resilience.py       # Error recovery patterns
├── services.py         # Business logic services
├── distribution.py     # Workflow distribution
├── results.py          # Execution results handling
├── delegates.py        # Qt item delegates
├── panels/             # UI panels
│   ├── dashboard_panel.py
│   ├── robots_panel.py
│   ├── jobs_panel.py
│   ├── metrics_panel.py
│   ├── detail_panel.py
│   └── tree_panel.py
└── views/              # Specialized views
    ├── metrics_view.py
    └── schedules_view.py
```

## Core Modules

### Core (`core/`)

Foundation classes shared across all applications:

```
core/
├── base_node.py           # BaseNode - Abstract node interface
├── types.py               # Type definitions (DataType, NodeStatus, etc.)
├── events.py              # Event system (EventEmitter, EventType)
├── execution_context.py   # ExecutionContext - Runtime state
└── workflow_schema.py     # WorkflowSchema - JSON serialization
```

### Nodes (`nodes/`)

Automation node implementations (logic only, no UI):

```
nodes/
├── basic_nodes.py         # Start, End, Comment
├── browser_nodes.py       # LaunchBrowser, CloseBrowser
├── navigation_nodes.py    # GoToURL, GoBack, Refresh
├── interaction_nodes.py   # Click, Type, Select, Hover
├── control_flow_nodes.py  # If, ForLoop, WhileLoop, Switch
├── error_handling_nodes.py # Try, Retry, ThrowError
├── data_nodes.py          # Concatenate, Regex, Math, JSON
├── variable_nodes.py      # SetVariable, GetVariable
├── utility_nodes.py       # Delay, Log, Screenshot
├── wait_nodes.py          # WaitForElement, WaitForCondition
├── file_nodes.py          # ReadFile, WriteFile, FileExists
└── desktop_nodes/         # Desktop automation nodes
    ├── application_nodes.py
    ├── window_nodes.py
    ├── element_nodes.py
    ├── interaction_nodes.py
    ├── mouse_keyboard_nodes.py
    ├── wait_verification_nodes.py
    ├── screenshot_ocr_nodes.py
    └── office_nodes.py
```

### Desktop (`desktop/`)

Windows desktop automation infrastructure:

```
desktop/
├── selector.py            # Desktop selector system
├── element.py             # DesktopElement wrapper
├── context.py             # DesktopContext - Automation state
└── desktop_recorder.py    # Action recording
```

### Runner (`runner/`)

Workflow execution engine:

```
runner/
├── workflow_runner.py     # WorkflowRunner - Main executor
├── graph_traversal.py     # DAG traversal algorithms
└── debug_manager.py       # Debug mode support
```

### Recorder (`recorder/`)

Action recording functionality:

```
recorder/
├── recording_session.py   # RecordingSession - Capture manager
└── workflow_generator.py  # Convert recordings to workflows
```

### Utils (`utils/`)

Shared utilities:

```
utils/
├── config.py              # Application configuration
├── fuzzy_search.py        # Fuzzy string matching
├── workflow_loader.py     # Workflow file loading
├── playwright_setup.py    # Browser initialization
├── selector_generator.py  # Web selector generation
└── selector_normalizer.py # Selector normalization
```

## Data Flow

### 1. Workflow Creation (Canvas)

```
User Action → Visual Node → BaseNode → Serialization → JSON File
     │            │            │             │
     │            │            │             └── workflows/*.json
     │            │            └── Node logic + ports
     │            └── Visual wrapper + Qt widgets
     └── Drag/drop, connect, configure
```

### 2. Workflow Distribution (Orchestrator → Robot)

```
Orchestrator                    Robot
     │                            │
     ├── Load workflow JSON       │
     ├── Create Job               │
     ├── Schedule                 │
     ├── Dispatch via WS ─────────┼──> Receive Job
     │                            ├── Download workflow
     │                            ├── Execute nodes
     ├── <── Status updates ──────┤
     │                            └── Report results
     └── Store results
```

### 3. Workflow Execution (Robot)

```
WorkflowRunner
     │
     ├── Parse workflow JSON
     ├── Build execution graph
     ├── TopologicalSort for order
     │
     └── For each node:
         ├── Create ExecutionContext
         ├── Execute node.execute(context)
         ├── Handle outputs/errors
         └── Follow connections to next node
```

## Key Patterns

### 1. Node Architecture

Every node has two components:
- **Logic Class** (`nodes/`): Business logic, ports, execution
- **Visual Wrapper** (`canvas/visual_nodes/`): Qt widget, property editors

```python
# Logic (nodes/browser_nodes.py)
class LaunchBrowserNode(BaseNode):
    def setup(self):
        self.add_output("browser", DataType.BROWSER)

    async def execute(self, context):
        browser = await context.launch_browser()
        return {"browser": browser}

# Visual (canvas/visual_nodes/)
class LaunchBrowserVisualNode(VisualNodeBase):
    NODE_CLASS = LaunchBrowserNode
    # Qt property widgets
```

### 2. Async Execution

All Playwright operations are async, integrated with Qt via `qasync`:

```python
async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
    page = await context.get_page()
    await page.goto(self.get_property("url"))
    return {"page": page}
```

### 3. Event System

Components communicate via events:

```python
# Emit
context.emit(EventType.NODE_COMPLETED, {"node_id": self.id})

# Subscribe
context.on(EventType.NODE_ERROR, self.handle_error)
```

### 4. Circuit Breaker (Robot)

Fault tolerance for network operations:

```python
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60
)

@breaker.call
async def poll_orchestrator():
    ...
```

### 5. Checkpoint/Resume (Robot)

Long-running workflows can checkpoint and resume:

```python
checkpoint = Checkpoint(workflow_id)
checkpoint.save_state(current_node, context)
# Later...
context = checkpoint.restore_state()
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| GUI Framework | PySide6 (Qt6) | Cross-platform desktop UI |
| Node Editor | NodeGraphQt | Visual node-based editor |
| Web Automation | Playwright | Browser control |
| Desktop Automation | uiautomation | Windows UI Automation |
| Async Bridge | qasync | Qt + asyncio integration |
| JSON Handling | orjson | High-performance serialization |
| Logging | loguru | Structured logging |
| Cloud Backend | Supabase | Real-time database |
| Process Management | psutil | System monitoring |

## Module Dependencies

```
                    ┌─────────────┐
                    │    core/    │
                    │ (base_node, │
                    │   types,    │
                    │  events)    │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            v              v              v
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │  nodes/  │  │ desktop/ │  │ runner/  │
      │(logic)   │  │(uiauto)  │  │(executor)│
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │              │              │
           │         ┌────┴────┐         │
           │         │ utils/  │         │
           └────────>│(shared) │<────────┘
                     └────┬────┘
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
      v                   v                   v
┌──────────┐       ┌──────────┐       ┌──────────┐
│ canvas/  │       │orchestr- │       │  robot/  │
│(editor)  │       │  ator/   │       │(executor)│
└──────────┘       └──────────┘       └──────────┘
```

## File Formats

### Workflow JSON Schema

```json
{
  "metadata": {
    "name": "Example Workflow",
    "version": "1.0.0",
    "schema_version": "1.0.0",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "nodes": {
    "node_1": {
      "node_id": "node_1",
      "node_type": "LaunchBrowser",
      "position": [100, 100],
      "properties": {
        "browser_type": "chromium",
        "headless": false
      }
    }
  },
  "connections": [
    {
      "source_node": "node_1",
      "source_port": "exec_out",
      "target_node": "node_2",
      "target_port": "exec_in"
    }
  ],
  "frames": [],
  "variables": {},
  "settings": {
    "stop_on_error": true,
    "timeout": 30
  }
}
```

## Security Considerations

1. **Credential Storage**: Sensitive data should use OS credential manager
2. **Selector Injection**: Sanitize user-provided selectors
3. **Code Execution**: No eval() or exec() on user input
4. **Network Security**: WebSocket connections use TLS in production
5. **File Access**: Validate file paths, prevent directory traversal

## Performance Optimizations

1. **Viewport Culling**: Only render visible nodes on large canvases
2. **Lazy Loading**: Load node icons and resources on demand
3. **Connection Batching**: Batch database operations in Orchestrator
4. **Checkpoint Compression**: Compress large checkpoint states
5. **Event Debouncing**: Debounce frequent UI updates
