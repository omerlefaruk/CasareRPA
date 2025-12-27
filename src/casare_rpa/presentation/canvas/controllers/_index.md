# Canvas Controllers Index

```xml<controllers_index>
  <!-- Quick reference for Canvas UI controllers. Use for fast discovery. -->

  <overview>
    <p>MVC controllers for Canvas UI interactions</p>
    <files>18 files</files>
    <exports>16 total</exports>
  </overview>

  <architecture>
    <p>Handle user input</p>
    <p>Update models</p>
    <p>Coordinate UI updates</p>
    <p>Route events between components</p>
  </architecture>

  <base>
    <e>BaseController</e> <s>base_controller.py</s> <d>Abstract base for all controllers</d>
  </base>

  <core>
    <e>WorkflowController</e>      <s>workflow_controller.py</s> <d>Workflow lifecycle (new, open, save, close)</d>
    <e>ExecutionController</e>     <s>execution_controller.py</s> <d>Workflow execution (run, pause, stop, debug)</d>
    <e>NodeController</e>          <s>node_controller.py</s> <d>Node operations (select, disable, navigate)</d>
    <e>ConnectionController</e>    <s>connection_controller.py</s> <d>Connection management (create, delete, validate)</d>
    <e>PanelController</e>         <s>panel_controller.py</s> <d>Panel visibility (properties, debug, minimap)</d>
    <e>MenuController</e>          <s>menu_controller.py</s> <d>Menu/action management (shortcuts, recent files)</d>
    <e>ViewportController</e>      <s>viewport_controller.py</s> <d>Canvas viewport, minimap, zoom, frame management</d>
  </core>

  <state>
    <e>UIStateController</e>       <s>ui_state_controller.py</s> <d>UI state persistence (geometry, panels, recent files)</d>
    <e>PreferencesController</e>   <s>preferences_controller.py</s> <d>Settings and preferences management</d>
    <e>AutosaveController</e>      <s>autosave_controller.py</s> <d>Automatic workflow saving</d>
    <e>ProjectAutosaveController</e> <s>project_autosave_controller.py</s> <d>Project-level autosave</d>
  </state>

  <specialized>
    <e>ProjectController</e>       <s>project_controller.py</s> <d>Project management</d>
    <e>SelectorController</e>      <s>selector_controller.py</s> <d>Element selector/picker (browser, desktop)</d>
    <e>RobotController</e>         <s>robot_controller.py</s> <d>Robot execution management</d>
    <e>EventBusController</e>      <s>event_bus_controller.py</s> <d>Centralized event routing</d>
  </specialized>

  <event_utils>
    <e>EventTypes</e>              <s>event_bus_controller.py</s> <d>Event type enumeration</d>
    <e>Event</e>                   <s>event_bus_controller.py</s> <d>Event data structure</d>
  </event_utils>

  <responsibilities>
    <r name="WorkflowController">
      <i>New workflow creation</i>
      <i>Open/save workflow files</i>
      <i>Close with save prompts</i>
      <i>Recent files management</i>
    </r>
    <r name="ExecutionController">
      <i>Start/pause/stop execution</i>
      <i>Debug mode (step, breakpoints)</i>
      <i>Execution state tracking</i>
      <i>Progress updates</i>
    </r>
    <r name="NodeController">
      <i>Node selection</i>
      <i>Enable/disable nodes</i>
      <i>Node navigation</i>
      <i>Property editing</i>
    </r>
    <r name="ViewportController">
      <i>Zoom in/out/fit</i>
      <i>Pan and scroll</i>
      <i>Minimap sync</i>
      <i>Frame to selection</i>
    </r>
    <r name="UIStateController">
      <i>Window geometry persistence</i>
      <i>Panel states</i>
      <i>Recent files</i>
      <i>User preferences</i>
    </r>
  </responsibilities>

  <usage>
    <code>
from casare_rpa.presentation.canvas.controllers import (
    WorkflowController, ExecutionController, NodeController,
    ViewportController, UIStateController
)

# Initialize controllers
workflow_ctrl = WorkflowController(main_window)
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
    </code>
  </usage>

  <related>
    <r>canvas.events</r>  <d>Event bus system</d>
    <r>canvas.ui</r>      <d>UI components controlled</d>
    <r>canvas.graph</r>   <d>Graph rendering</d>
  </related>
</controllers_index>
```
