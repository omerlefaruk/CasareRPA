# Canvas Controllers Index

Quick reference for Canvas UI controllers. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | MVC controllers for Canvas UI interactions |
| Files | 18 files |
| Exports | 16 total exports |

## Architecture

Controllers follow MVC pattern:
- Handle user input
- Update models
- Coordinate UI updates
- Route events between components

## Base Class

| Export | Source | Description |
|--------|--------|-------------|
| `BaseController` | `base_controller.py` | Abstract base for all controllers |

## Core Controllers

| Export | Source | Description |
|--------|--------|-------------|
| `WorkflowController` | `workflow_controller.py` | Workflow lifecycle (new, open, save, close) |
| `ExecutionController` | `execution_controller.py` | Workflow execution (run, pause, stop, debug) |
| `NodeController` | `node_controller.py` | Node operations (select, disable, navigate) |
| `ConnectionController` | `connection_controller.py` | Connection management (create, delete, validate) |
| `PanelController` | `panel_controller.py` | Panel visibility (properties, debug, minimap) |
| `MenuController` | `menu_controller.py` | Menu/action management (shortcuts, recent files) |
| `ViewportController` | `viewport_controller.py` | Canvas viewport, minimap, zoom, frame management |

## State Controllers

| Export | Source | Description |
|--------|--------|-------------|
| `UIStateController` | `ui_state_controller.py` | UI state persistence (geometry, panels, recent files) |
| `PreferencesController` | `preferences_controller.py` | Settings and preferences management |
| `AutosaveController` | `autosave_controller.py` | Automatic workflow saving |
| `ProjectAutosaveController` | `project_autosave_controller.py` | Project-level autosave |

## Specialized Controllers

| Export | Source | Description |
|--------|--------|-------------|
| `ProjectController` | `project_controller.py` | Project management |
| `SelectorController` | `selector_controller.py` | Element selector/picker (browser, desktop) |
| `RobotController` | `robot_controller.py` | Robot execution management |
| `EventBusController` | `event_bus_controller.py` | Centralized event routing |

## Event Utilities

| Export | Source | Description |
|--------|--------|-------------|
| `EventTypes` | `event_bus_controller.py` | Event type enumeration |
| `Event` | `event_bus_controller.py` | Event data structure |

## Controller Responsibilities

### WorkflowController
- New workflow creation
- Open/save workflow files
- Close with save prompts
- Recent files management

### ExecutionController
- Start/pause/stop execution
- Debug mode (step, breakpoints)
- Execution state tracking
- Progress updates

### NodeController
- Node selection
- Enable/disable nodes
- Node navigation
- Property editing

### ViewportController
- Zoom in/out/fit
- Pan and scroll
- Minimap sync
- Frame to selection

### UIStateController
- Window geometry persistence
- Panel states
- Recent files
- User preferences

## Usage Patterns

```python
from casare_rpa.presentation.canvas.controllers import (
    WorkflowController,
    ExecutionController,
    NodeController,
    ViewportController,
    UIStateController,
)

# Initialize controllers
workflow_ctrl = WorkflowController(main_window)
workflow_ctrl.initialize()

# Handle workflow operations
workflow_ctrl.new_workflow()
workflow_ctrl.open_workflow(path)
workflow_ctrl.save_workflow()

# Execution control
execution_ctrl = ExecutionController(main_window)
execution_ctrl.run_workflow()
execution_ctrl.pause()
execution_ctrl.stop()

# Viewport control
viewport_ctrl = ViewportController(main_window)
viewport_ctrl.zoom_to_fit()
viewport_ctrl.zoom_in()
```

## Related Modules

| Module | Relation |
|--------|----------|
| `canvas.events` | Event bus system |
| `canvas.ui` | UI components controlled |
| `canvas.graph` | Graph rendering |
