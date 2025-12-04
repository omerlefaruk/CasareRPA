# Presentation Layer API

**Modules:** 162 | **Classes:** 631 | **Functions:** 94


## Modules

| Module | Classes | Functions | Description |
|--------|---------|-----------|-------------|
| `casare_rpa.presentation.canvas.app` | 1 | 1 | Main application class with qasync integration (Re... |
| `casare_rpa.presentation.canvas.component_factory` | 1 | 0 | Component factory for lazy component creation with... |
| `casare_rpa.presentation.canvas.components.action_manager` | 1 | 0 | Action manager for MainWindow QActions. |
| `casare_rpa.presentation.canvas.components.dock_creator` | 1 | 0 | Dock widget creator for MainWindow. |
| `casare_rpa.presentation.canvas.components.fleet_dashboard_manager` | 1 | 0 | Fleet dashboard manager for MainWindow. |
| `casare_rpa.presentation.canvas.components.menu_builder` | 1 | 0 | Menu builder for MainWindow menu bar. |
| `casare_rpa.presentation.canvas.components.status_bar_manager` | 1 | 0 | Status bar manager for MainWindow. |
| `casare_rpa.presentation.canvas.components.toolbar_builder` | 1 | 0 | Toolbar builder for MainWindow toolbar. |
| `casare_rpa.presentation.canvas.connections.auto_connect` | 1 | 0 | Auto-connect feature for node graph. |
| `casare_rpa.presentation.canvas.connections.connection_cutter` | 1 | 0 | Connection cutter for node graph. |
| `casare_rpa.presentation.canvas.connections.connection_validator` | 3 | 2 | Connection Validator for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.connections.node_insert` | 1 | 1 | Node insertion on connection drop. |
| `casare_rpa.presentation.canvas.controllers.autosave_controller` | 1 | 0 | Autosave controller for automatic workflow saving. |
| `casare_rpa.presentation.canvas.controllers.base_controller` | 2 | 0 | Base controller class for Canvas controllers. |
| `casare_rpa.presentation.canvas.controllers.connection_controller` | 1 | 0 | Connection management controller. |
| `casare_rpa.presentation.canvas.controllers.event_bus_controller` | 3 | 0 | Event bus controller for centralized event routing... |
| `casare_rpa.presentation.canvas.controllers.example_workflow_controller` | 1 | 0 | Example Workflow Controller demonstrating EventBus... |
| `casare_rpa.presentation.canvas.controllers.execution_controller` | 1 | 0 | Workflow execution controller. |
| `casare_rpa.presentation.canvas.controllers.menu_controller` | 1 | 0 | Menu and action management controller. |
| `casare_rpa.presentation.canvas.controllers.node_controller` | 1 | 0 | Node operations controller. |
| `casare_rpa.presentation.canvas.controllers.panel_controller` | 1 | 0 | Panel visibility and management controller. |
| `casare_rpa.presentation.canvas.controllers.preferences_controller` | 1 | 0 | Preferences controller for user settings and confi... |
| `casare_rpa.presentation.canvas.controllers.project_controller` | 1 | 0 | Project controller for managing projects in the Ca... |
| `casare_rpa.presentation.canvas.controllers.robot_controller` | 1 | 0 | Robot Controller for Canvas UI. |
| `casare_rpa.presentation.canvas.controllers.scheduling_controller` | 1 | 0 | Scheduling controller for workflow scheduling mana... |
| `casare_rpa.presentation.canvas.controllers.selector_controller` | 1 | 0 | Selector controller for element picker functionali... |
| `casare_rpa.presentation.canvas.controllers.ui_state_controller` | 1 | 0 | UI State Controller for Canvas. |
| `casare_rpa.presentation.canvas.controllers.viewport_controller` | 1 | 0 | Viewport controller for canvas view management. |
| `casare_rpa.presentation.canvas.controllers.workflow_controller` | 1 | 0 | Workflow lifecycle controller. |
| `casare_rpa.presentation.canvas.debugger.debug_controller` | 6 | 0 | Debug Controller for interactive workflow debuggin... |
| `casare_rpa.presentation.canvas.desktop.desktop_recording_panel` | 2 | 0 | Desktop Recording Panel for CasareRPA |
| `casare_rpa.presentation.canvas.desktop.rich_comment_node` | 3 | 2 | Rich Comment Node |
| `casare_rpa.presentation.canvas.events.domain_bridge` | 1 | 1 | Domain-to-Presentation Event Bridge. |
| `casare_rpa.presentation.canvas.events.event` | 3 | 1 | Event data structures for the Canvas event system. |
| `casare_rpa.presentation.canvas.events.event_batcher` | 1 | 0 | EventBatcher for high-frequency event batching. |
| `casare_rpa.presentation.canvas.events.event_bus` | 1 | 0 | Central event bus for Canvas UI component communic... |
| `casare_rpa.presentation.canvas.events.event_contracts` | 38 | 0 | Event Data Contracts for CasareRPA Event Bus Syste... |
| `casare_rpa.presentation.canvas.events.event_handler` | 1 | 1 | Event handler decorators and base class for Canvas... |
| `casare_rpa.presentation.canvas.events.event_types` | 2 | 0 | Event type definitions for the Canvas event system... |
| `casare_rpa.presentation.canvas.events.lazy_subscription` | 2 | 0 | Lazy event subscription for EventBus optimization. |
| `casare_rpa.presentation.canvas.events.qt_signal_bridge` | 3 | 0 | Qt Signal Bridge for EventBus integration. |
| `casare_rpa.presentation.canvas.execution.canvas_workflow_runner` | 1 | 0 | Canvas Workflow Runner. |
| `casare_rpa.presentation.canvas.graph.category_utils` | 2 | 9 | Category Utilities - Hierarchical category path su... |
| `casare_rpa.presentation.canvas.graph.collapse_components` | 3 | 0 | Collapse Components for NodeFrame |
| `casare_rpa.presentation.canvas.graph.composite_node_creator` | 1 | 0 | Composite Node Creator for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.graph.custom_node_item` | 2 | 0 | Custom node graphics item for CasareRPA. |
| `casare_rpa.presentation.canvas.graph.custom_pipe` | 1 | 2 | Custom pipe styling for node connections. |
| `casare_rpa.presentation.canvas.graph.event_filters` | 3 | 0 | Event filters for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.graph.frame_factory` | 1 | 3 | Frame Factory |
| `casare_rpa.presentation.canvas.graph.frame_managers` | 2 | 0 | Frame Managers |
| `casare_rpa.presentation.canvas.graph.frame_renderer` | 2 | 0 | Frame Renderer |
| `casare_rpa.presentation.canvas.graph.minimap` | 3 | 0 | Minimap widget for the node graph. |
| `casare_rpa.presentation.canvas.graph.node_creation_helper` | 1 | 0 | Node Creation Helper for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.graph.node_frame` | 1 | 0 | Node Frame/Group System |
| `casare_rpa.presentation.canvas.graph.node_graph_widget` | 1 | 0 | Node graph widget wrapper for NodeGraphQt integrat... |
| `casare_rpa.presentation.canvas.graph.node_icons` | 0 | 9 | Node Icon System |
| `casare_rpa.presentation.canvas.graph.node_quick_actions` | 1 | 1 | Node Quick Actions for CasareRPA. |
| `casare_rpa.presentation.canvas.graph.node_registry` | 2 | 14 | Node registry and factory for creating and managin... |
| `casare_rpa.presentation.canvas.graph.node_widgets` | 8 | 2 | Custom Node Widget Wrappers for NodeGraphQt. |
| `casare_rpa.presentation.canvas.graph.port_shapes` | 0 | 12 | Port Shape Drawing Functions for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.graph.selection_manager` | 1 | 0 | Selection Manager for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.graph.style_manager` | 3 | 0 | Frame Style Manager |
| `casare_rpa.presentation.canvas.graph.viewport_culling` | 2 | 3 | Viewport Culling Manager for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.initializers.controller_registrar` | 1 | 0 | Controller registration and wiring for MainWindow. |
| `casare_rpa.presentation.canvas.initializers.ui_component_initializer` | 1 | 0 | UI Component Initializer for MainWindow. |
| `casare_rpa.presentation.canvas.main_window` | 1 | 0 | Main application window for CasareRPA. |
| `casare_rpa.presentation.canvas.port_type_system` | 5 | 3 | Port Type System for CasareRPA (Presentation Layer... |
| `casare_rpa.presentation.canvas.resources` | 1 | 2 | CasareRPA - Resource Cache for Icons and Pixmaps |
| `casare_rpa.presentation.canvas.search.command_palette` | 2 | 0 | Command Palette for CasareRPA. |
| `casare_rpa.presentation.canvas.search.node_search` | 2 | 0 | Node Search Dialog for CasareRPA. |
| `casare_rpa.presentation.canvas.search.node_search_dialog` | 1 | 0 | Node search dialog for quick node creation. |
| `casare_rpa.presentation.canvas.search.searchable_menu` | 1 | 0 | Searchable context menu for node creation. |
| `casare_rpa.presentation.canvas.selectors.desktop_selector_builder` | 1 | 0 | Desktop Selector Builder Dialog |
| `casare_rpa.presentation.canvas.selectors.element_picker` | 1 | 1 | Element Picker Overlay |
| `casare_rpa.presentation.canvas.selectors.element_tree_widget` | 2 | 0 | Element Tree Widget |
| `casare_rpa.presentation.canvas.selectors.selector_dialog` | 1 | 0 | Selector Picker Dialog - PySide6 UI |
| `casare_rpa.presentation.canvas.selectors.selector_integration` | 1 | 0 | Selector Integration Module |
| `casare_rpa.presentation.canvas.selectors.selector_strategy` | 2 | 5 | Desktop Selector Strategy Generator |
| `casare_rpa.presentation.canvas.selectors.selector_validator` | 3 | 1 | Selector Validator |
| `casare_rpa.presentation.canvas.serialization.workflow_deserializer` | 1 | 0 | Workflow Deserializer for Canvas. |
| `casare_rpa.presentation.canvas.serialization.workflow_serializer` | 1 | 0 | Workflow Serializer for Canvas. |
| `casare_rpa.presentation.canvas.services.trigger_event_handler` | 1 | 1 | CasareRPA - Qt Trigger Event Handler |
| `casare_rpa.presentation.canvas.services.websocket_bridge` | 4 | 1 | WebSocket Bridge Service for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.theme` | 1 | 4 | Unified Theme System for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.ui.action_factory` | 1 | 0 | Action Factory for MainWindow. |
| `casare_rpa.presentation.canvas.ui.base_widget` | 4 | 0 | Base widget class for all UI components. |
| `casare_rpa.presentation.canvas.ui.debug_panel` | 1 | 0 | Enhanced Debug Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog` | 3 | 0 | Credential Manager Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_dashboard` | 1 | 0 | Fleet Dashboard Dialog for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.analytics_tab` | 4 | 0 | Analytics Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.api_keys_tab` | 1 | 0 | API Keys Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab` | 1 | 0 | Base Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab` | 1 | 0 | Jobs Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab` | 2 | 0 | Robots Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab` | 1 | 0 | Schedules Tab Widget for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.dialogs.node_properties_dialog` | 1 | 0 | Node Properties Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.preferences_dialog` | 1 | 0 | Preferences Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.project_manager_dialog` | 1 | 0 | Project Manager Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.recording_dialog` | 1 | 0 | Recording Preview Dialog |
| `casare_rpa.presentation.canvas.ui.dialogs.remote_robot_dialog` | 1 | 0 | Remote Robot Management Dialog. |
| `casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog` | 2 | 0 | Schedule Dialog for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.ui.dialogs.template_browser_dialog` | 1 | 1 | Template Browser Dialog |
| `casare_rpa.presentation.canvas.ui.dialogs.update_dialog` | 2 | 0 | Update Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.dialogs.workflow_settings_dialog` | 1 | 0 | Workflow Settings Dialog UI Component. |
| `casare_rpa.presentation.canvas.ui.icons` | 1 | 1 | CasareRPA - Icon Provider for Toolbar Actions. |
| `casare_rpa.presentation.canvas.ui.panels.analytics_panel` | 2 | 0 | Analytics Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.api_key_panel` | 2 | 0 | API Key Management Panel for Fleet Dashboard. |
| `casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock` | 1 | 0 | Bottom Panel Dock for CasareRPA. |
| `casare_rpa.presentation.canvas.ui.panels.history_tab` | 1 | 0 | History Tab for the Bottom Panel. |
| `casare_rpa.presentation.canvas.ui.panels.log_tab` | 1 | 0 | Log Tab for the Bottom Panel. |
| `casare_rpa.presentation.canvas.ui.panels.log_viewer_panel` | 2 | 0 | Log Viewer Panel for Robot Log Streaming. |
| `casare_rpa.presentation.canvas.ui.panels.minimap_panel` | 3 | 0 | Minimap Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.output_tab` | 1 | 0 | Output Tab for the Bottom Panel. |
| `casare_rpa.presentation.canvas.ui.panels.process_mining_panel` | 2 | 0 | Process Mining Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.properties_panel` | 2 | 0 | Properties Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.robot_picker_panel` | 1 | 0 | Robot Picker Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.terminal_tab` | 1 | 0 | Terminal Tab for the Bottom Panel. |
| `casare_rpa.presentation.canvas.ui.panels.validation_tab` | 1 | 0 | Validation Tab for the Bottom Panel. |
| `casare_rpa.presentation.canvas.ui.panels.variable_inspector_dock` | 1 | 0 | Variable Inspector Dock - Runtime variable value v... |
| `casare_rpa.presentation.canvas.ui.panels.variables_panel` | 2 | 0 | Variables Panel UI Component. |
| `casare_rpa.presentation.canvas.ui.panels.variables_tab` | 1 | 0 | Variables Tab - QWidget wrapper for VariablesPanel... |
| `casare_rpa.presentation.canvas.ui.signal_bridge` | 2 | 0 | Signal Bridge for MainWindow Controller Connection... |
| `casare_rpa.presentation.canvas.ui.toolbars.hotkey_manager` | 2 | 0 | Hotkey manager dialog for viewing and customizing ... |
| `casare_rpa.presentation.canvas.ui.toolbars.main_toolbar` | 1 | 0 | Main Toolbar UI Component. |
| `casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget` | 1 | 3 | AI Settings Widget - Reusable credential and model... |
| `casare_rpa.presentation.canvas.ui.widgets.execution_timeline` | 3 | 0 | Execution Timeline for CasareRPA. |
| `casare_rpa.presentation.canvas.ui.widgets.output_console_widget` | 1 | 0 | Output Console Widget UI Component. |
| `casare_rpa.presentation.canvas.ui.widgets.performance_dashboard` | 8 | 1 | Performance Dashboard for CasareRPA Canvas. |
| `casare_rpa.presentation.canvas.ui.widgets.robot_override_widget` | 1 | 0 | Robot Override Widget for Node-Level Robot Targeti... |
| `casare_rpa.presentation.canvas.ui.widgets.search_widget` | 1 | 0 | Search Widget UI Component. |
| `casare_rpa.presentation.canvas.ui.widgets.tenant_selector` | 2 | 0 | Tenant Selector Widget. |
| `casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget` | 1 | 0 | Variable Editor Widget UI Component. |
| `casare_rpa.presentation.canvas.visual_nodes.ai_ml.nodes` | 7 | 2 | Visual nodes for AI/ML category. |
| `casare_rpa.presentation.canvas.visual_nodes.base_visual_node` | 1 | 0 | Base Visual Node for CasareRPA. |
| `casare_rpa.presentation.canvas.visual_nodes.basic.nodes` | 3 | 0 | Visual nodes for basic category. |
| `casare_rpa.presentation.canvas.visual_nodes.browser.nodes` | 18 | 0 | Visual nodes for browser category. |
| `casare_rpa.presentation.canvas.visual_nodes.control_flow.nodes` | 19 | 0 | Visual nodes for control_flow category. |
| `casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes` | 32 | 0 | Visual nodes for data operations category. |
| `casare_rpa.presentation.canvas.visual_nodes.database.nodes` | 10 | 0 | Visual nodes for database category. |
| `casare_rpa.presentation.canvas.visual_nodes.desktop_automation.nodes` | 36 | 0 | Visual nodes for desktop_automation category. |
| `casare_rpa.presentation.canvas.visual_nodes.document.nodes` | 5 | 1 | Visual nodes for Document AI category. |
| `casare_rpa.presentation.canvas.visual_nodes.email.nodes` | 8 | 0 | Visual nodes for email category. |
| `casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes` | 9 | 0 | Visual nodes for error_handling category. |
| `casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes` | 40 | 0 | Visual nodes for file_operations category. |
| `casare_rpa.presentation.canvas.visual_nodes.google.calendar_nodes` | 12 | 0 | Visual nodes for Google Calendar operations. |
| `casare_rpa.presentation.canvas.visual_nodes.google.docs_nodes` | 10 | 0 | Visual nodes for Google Docs operations. |
| `casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes` | 17 | 0 | Visual nodes for Google Drive operations. |
| `casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes` | 21 | 0 | Visual nodes for Gmail operations. |
| `casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes` | 21 | 0 | Visual nodes for Google Sheets operations. |
| `casare_rpa.presentation.canvas.visual_nodes.messaging.nodes` | 4 | 0 | Visual nodes for messaging category (Telegram, Wha... |
| `casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes` | 5 | 0 | Visual nodes for Telegram action nodes (edit, dele... |
| `casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes` | 7 | 0 | Visual nodes for WhatsApp messaging. |
| `casare_rpa.presentation.canvas.visual_nodes.office_automation.nodes` | 12 | 0 | Visual nodes for office_automation category. |
| `casare_rpa.presentation.canvas.visual_nodes.rest_api.nodes` | 7 | 2 | Visual nodes for rest_api category. |
| `casare_rpa.presentation.canvas.visual_nodes.scripts.nodes` | 5 | 0 | Visual nodes for scripts category. |
| `casare_rpa.presentation.canvas.visual_nodes.system.nodes` | 13 | 0 | Visual nodes for system category. |
| `casare_rpa.presentation.canvas.visual_nodes.triggers.base` | 1 | 0 | CasareRPA - Base Visual Trigger Node |
| `casare_rpa.presentation.canvas.visual_nodes.triggers.nodes` | 17 | 0 | CasareRPA - Visual Trigger Nodes |
| `casare_rpa.presentation.canvas.visual_nodes.utility.nodes` | 26 | 0 | Visual nodes for utility category. |
| `casare_rpa.presentation.canvas.visual_nodes.variable.nodes` | 3 | 0 | Visual nodes for variable category. |
| `casare_rpa.presentation.setup.config_manager` | 5 | 0 | Client Configuration Manager. |
| `casare_rpa.presentation.setup.setup_wizard` | 6 | 1 | Setup Wizard for CasareRPA Client. |

## casare_rpa.presentation.canvas.app

**File:** `src\casare_rpa\presentation\canvas\app.py`


Main application class with qasync integration (Refactored).

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.

Reduced from 3,112 lines to ~400 lines by extracting components.


### Functions

#### `main`

```python
def main() -> int
```

Main entry point for the application.

Returns:
    Application exit code


### CasareRPAApp


Main application class integrating Qt with asyncio (Refactored).

Uses qasync to bridge PySide6's event loop with Python's asyncio,
enabling async workflows with Playwright to run within the Qt application.

Responsibilities:
- Qt application initialization
- Component lifecycle management with explicit dependency ordering
- Event loop integration
- Signal routing

Business logic delegated to controllers:
- WorkflowController: New/Open/Save/Template operations
- ExecutionController: Workflow execution and debugging
- NodeController: Node type registration (no dependencies)
- SelectorController: Element selector integration
- PreferencesController: Settings management
- AutosaveController: Automatic saving

Note: Triggers are now visual nodes on the canvas (not a background system).

Component Initialization Order:
1. NodeRegistryComponent - Must be first (registers all node types)
2. All other components - Depend on node registry being initialized


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the application. |
| `cleanup()` | `None` | Cleanup all controllers. |
| `get_autosave_controller()` | `AutosaveController` | Get the autosave controller. |
| `get_execution_controller()` | `ExecutionController` | Get the execution controller. |
| `get_node_controller()` | `NodeController` | Get the node controller. |
| `get_preferences_controller()` | `PreferencesController` | Get the preferences controller. |
| `get_selector_controller()` | `SelectorController` | Get the selector controller. |
| `get_workflow_controller()` | `WorkflowController` | Get the workflow controller. |
| `run()` | `int` | Run the application. |
| `async run_async()` | `int` | Run the application asynchronously. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the application.

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup all controllers.

##### `get_autosave_controller`

```python
def get_autosave_controller() -> AutosaveController
```

Get the autosave controller.

##### `get_execution_controller`

```python
def get_execution_controller() -> ExecutionController
```

Get the execution controller.

##### `get_node_controller`

```python
def get_node_controller() -> NodeController
```

Get the node controller.

##### `get_preferences_controller`

```python
def get_preferences_controller() -> PreferencesController
```

Get the preferences controller.

##### `get_selector_controller`

```python
def get_selector_controller() -> SelectorController
```

Get the selector controller.

##### `get_workflow_controller`

```python
def get_workflow_controller() -> WorkflowController
```

Get the workflow controller.

##### `run`

```python
def run() -> int
```

Run the application.

Returns:
    Application exit code

##### `run_async`

```python
async def run_async() -> int
```

Run the application asynchronously.

This method allows the application to be started from
an async context if needed.

Returns:
    Application exit code

---

## casare_rpa.presentation.canvas.component_factory

**File:** `src\casare_rpa\presentation\canvas\component_factory.py`


Component factory for lazy component creation with singleton caching.

Implements singleton pattern for deferred component initialization,
supporting the 3-tier loading strategy for startup optimization.

Tier 1 (CRITICAL): Immediate - NodeGraphWidget, WorkflowController
Tier 2 (NORMAL): showEvent - PropertiesPanel, DebugPanel, VariablesPanel
Tier 3 (DEFERRED): Lazy factory - OutputConsole, dialogs


### ComponentFactory


Lazy component creation with singleton caching.

Provides factory methods for deferred component creation, ensuring
each component is only instantiated once and reused on subsequent
access. Supports the 3-tier loading strategy for startup optimization.

Thread Safety:
    This class is NOT thread-safe. All component creation should
    happen on the main Qt thread.

Usage:
    # Get or create a component
    console = ComponentFactory.get_or_create(
        "output_console",
        lambda: OutputConsole(parent)
    )

    # Clear cache (for tests or cleanup)
    ComponentFactory.clear()


**Attributes:**

- `_creation_times: Dict[str, float]`
- `_instances: Dict[str, QWidget]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `clear()` | `None` | Clear all cached components. |
| `get(component_name)` | `Optional[QWidget]` | Get component from cache without creating. |
| `get_cached_count()` | `int` | Get number of cached components. |
| `get_or_create(component_name, factory)` | `T` | Get existing component or create new one using factory. |
| `get_stats()` | `Dict[str, float]` | Get creation time statistics for cached components. |
| `has(component_name)` | `bool` | Check if component exists in cache. |
| `remove(component_name)` | `Optional[QWidget]` | Remove component from cache. |

#### Method Details

##### `clear`

```python
@classmethod
def clear() -> None
```

Clear all cached components.

Should be called during cleanup or in tests to reset state.
Does NOT destroy the widgets - caller must handle widget cleanup.

##### `get`

```python
@classmethod
def get(component_name: str) -> Optional[QWidget]
```

Get component from cache without creating.

Args:
    component_name: Unique identifier for the component.

Returns:
    Cached component or None if not found.

**Parameters:**

- `component_name: str` *(required)*

##### `get_cached_count`

```python
@classmethod
def get_cached_count() -> int
```

Get number of cached components.

Returns:
    Number of components currently in cache.

##### `get_or_create`

```python
@classmethod
def get_or_create(component_name: str, factory: Callable[[], T]) -> T
```

Get existing component or create new one using factory.

Args:
    component_name: Unique identifier for the component.
    factory: Callable that creates the component if not cached.

Returns:
    The cached or newly created component instance.

Raises:
    RuntimeError: If factory fails to create component.

**Parameters:**

- `component_name: str` *(required)*
- `factory: Callable[[], T]` *(required)*

##### `get_stats`

```python
@classmethod
def get_stats() -> Dict[str, float]
```

Get creation time statistics for cached components.

Returns:
    Dict mapping component names to creation times in milliseconds.

##### `has`

```python
@classmethod
def has(component_name: str) -> bool
```

Check if component exists in cache.

Args:
    component_name: Unique identifier for the component.

Returns:
    True if component is cached, False otherwise.

**Parameters:**

- `component_name: str` *(required)*

##### `remove`

```python
@classmethod
def remove(component_name: str) -> Optional[QWidget]
```

Remove component from cache.

Args:
    component_name: Unique identifier for the component.

Returns:
    Removed component or None if not found.

**Parameters:**

- `component_name: str` *(required)*

---

## casare_rpa.presentation.canvas.components.action_manager

**File:** `src\casare_rpa\presentation\canvas\components\action_manager.py`


Action manager for MainWindow QActions.

Centralizes creation and management of all QAction instances.


### ActionManager


Manages QAction creation and hotkey configuration.

Responsibilities:
- Create all QActions for menus and toolbars
- Load and apply saved hotkey settings
- Provide action lookup by name


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize action manager. |
| `create_actions()` | `None` | Create all actions for menus and toolbar. |
| `get_action(name)` | `Optional[QAction]` | Get action by name. |
| `get_all_actions()` | `Dict[str, QAction]` | Get all registered actions. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize action manager.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `create_actions`

```python
def create_actions() -> None
```

Create all actions for menus and toolbar.

##### `get_action`

```python
def get_action(name: str) -> Optional[QAction]
```

Get action by name.

Args:
    name: Action name

Returns:
    QAction or None if not found

**Parameters:**

- `name: str` *(required)*

##### `get_all_actions`

```python
def get_all_actions() -> Dict[str, QAction]
```

Get all registered actions.

Returns:
    Dictionary of action name to QAction

---

## casare_rpa.presentation.canvas.components.dock_creator

**File:** `src\casare_rpa\presentation\canvas\components\dock_creator.py`


Dock widget creator for MainWindow.

Centralizes creation of dock widgets (panels).


### DockCreator


Creates dock widgets for MainWindow.

Responsibilities:
- Create bottom panel dock
- Create variable inspector dock
- Create properties panel
- Create execution timeline dock
- Connect dock signals


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize dock creator. |
| `create_analytics_panel()` | `'AnalyticsPanel'` | Create the Analytics Panel for bottleneck detection and exec... |
| `create_bottom_panel()` | `'BottomPanelDock'` | Create the unified bottom panel with Variables, Output, Log,... |
| `create_debug_panel(debug_controller)` | `'DebugPanel'` | Create the Debug Panel dock for debugging workflow execution... |
| `create_execution_timeline_dock()` | `tuple[QDockWidget, 'ExecutionTimeline']` | Create the Execution Timeline dock for visualizing workflow ... |
| `create_process_mining_panel()` | `'ProcessMiningPanel'` | Create the Process Mining Panel for AI-powered process disco... |
| `create_properties_panel()` | `'PropertiesPanel'` | Create the properties panel for selected node editing. |
| `create_robot_picker_panel(robot_controller)` | `'RobotPickerPanel'` | Create the Robot Picker Panel for selecting robots and execu... |
| `create_variable_inspector_dock()` | `'VariableInspectorDock'` | Create the Variable Inspector dock for real-time variable va... |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize dock creator.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `create_analytics_panel`

```python
def create_analytics_panel() -> 'AnalyticsPanel'
```

Create the Analytics Panel for bottleneck detection and execution analysis.

Connects to the Orchestrator REST API for:
- Bottleneck Detection: Identify slow/failing nodes
- Execution Analysis: Trends, patterns, insights
- Timeline visualization

Returns:
    Created AnalyticsPanel instance

##### `create_bottom_panel`

```python
def create_bottom_panel() -> 'BottomPanelDock'
```

Create the unified bottom panel with Variables, Output, Log, Validation tabs.

Returns:
    Created BottomPanelDock instance

##### `create_debug_panel`

```python
def create_debug_panel(debug_controller: Optional['DebugController'] = None) -> 'DebugPanel'
```

Create the Debug Panel dock for debugging workflow execution.

Features:
- Call Stack visualization
- Watch Expressions
- Breakpoint management
- REPL console
- Execution snapshots

Args:
    debug_controller: Optional debug controller for integration

Returns:
    Created DebugPanel instance

**Parameters:**

- `debug_controller: Optional['DebugController'] = None`

##### `create_execution_timeline_dock`

```python
def create_execution_timeline_dock() -> tuple[QDockWidget, 'ExecutionTimeline']
```

Create the Execution Timeline dock for visualizing workflow execution.

Returns:
    Tuple of (QDockWidget, ExecutionTimeline)

##### `create_process_mining_panel`

```python
def create_process_mining_panel() -> 'ProcessMiningPanel'
```

Create the Process Mining Panel for AI-powered process discovery.

Features:
- Process Discovery: Build process models from execution logs
- Variant Analysis: See different execution paths
- Conformance Checking: Compare actual vs expected
- Optimization Insights: AI-generated recommendations

Returns:
    Created ProcessMiningPanel instance

##### `create_properties_panel`

```python
def create_properties_panel() -> 'PropertiesPanel'
```

Create the properties panel for selected node editing.

Returns:
    Created PropertiesPanel instance

##### `create_robot_picker_panel`

```python
def create_robot_picker_panel(robot_controller: Optional['RobotController'] = None) -> 'RobotPickerPanel'
```

Create the Robot Picker Panel for selecting robots and execution mode.

Features:
- Execution mode toggle: Local vs Cloud
- Tree view of available robots with status indicators
- Robot filtering by capability
- Refresh button to update robot list

Args:
    robot_controller: Optional robot controller for integration

Returns:
    Created RobotPickerPanel instance

**Parameters:**

- `robot_controller: Optional['RobotController'] = None`

##### `create_variable_inspector_dock`

```python
def create_variable_inspector_dock() -> 'VariableInspectorDock'
```

Create the Variable Inspector dock for real-time variable values.

Returns:
    Created VariableInspectorDock instance

---

## casare_rpa.presentation.canvas.components.fleet_dashboard_manager

**File:** `src\casare_rpa\presentation\canvas\components\fleet_dashboard_manager.py`


Fleet dashboard manager for MainWindow.

Centralizes fleet dashboard dialog interactions and orchestrator API calls.


### FleetDashboardManager


Manages fleet dashboard dialog and orchestrator interactions.

Responsibilities:
- Open and configure fleet dashboard dialog
- Refresh fleet data from orchestrator/local
- Handle robot CRUD operations
- Handle job operations (cancel, retry)
- Handle schedule operations (toggle, edit, delete, run now)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize fleet dashboard manager. |
| `dialog()` | `Optional['FleetDashboardDialog']` | Get current fleet dashboard dialog. |
| `open_dashboard()` | `None` | Open the fleet management dashboard dialog. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize fleet dashboard manager.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `dialog`

```python
@property
def dialog() -> Optional['FleetDashboardDialog']
```

Get current fleet dashboard dialog.

##### `open_dashboard`

```python
def open_dashboard() -> None
```

Open the fleet management dashboard dialog.

---

## casare_rpa.presentation.canvas.components.menu_builder

**File:** `src\casare_rpa\presentation\canvas\components\menu_builder.py`


Menu builder for MainWindow menu bar.

Centralizes menu creation and structure.


### MenuBuilder


Builds the menu bar structure for MainWindow.

Responsibilities:
- Create menu bar with 6 menus
- Organize actions into logical groups
- Handle recent files menu


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize menu builder. |
| `create_menus()` | `None` | Create menu bar and all menus (6-menu structure). |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize menu builder.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `create_menus`

```python
def create_menus() -> None
```

Create menu bar and all menus (6-menu structure).

---

## casare_rpa.presentation.canvas.components.status_bar_manager

**File:** `src\casare_rpa\presentation\canvas\components\status_bar_manager.py`


Status bar manager for MainWindow.

Centralizes status bar creation, updates, and tab toggles.


### StatusBarManager


Manages the status bar for MainWindow.

Responsibilities:
- Create enhanced status bar with zoom, node count, toggles
- Handle tab toggle buttons (Vars, Out, Log, Valid)
- Update execution status indicator


**Attributes:**

- `STATUS_BAR_STYLE: str`
- `STATUS_COLORS: dict`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize status bar manager. |
| `create_status_bar()` | `QStatusBar` | Create enhanced status bar with zoom, node count, and quick ... |
| `set_execution_status(status)` | `None` | Update execution status indicator. |
| `update_button_states()` | `None` | Update status bar button states based on panel visibility. |
| `update_node_count(count)` | `None` | Update the node count display. |
| `update_zoom_display(zoom_percent)` | `None` | Update the zoom level display. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize status bar manager.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `create_status_bar`

```python
def create_status_bar() -> QStatusBar
```

Create enhanced status bar with zoom, node count, and quick toggles.

Returns:
    Created QStatusBar instance

##### `set_execution_status`

```python
def set_execution_status(status: str) -> None
```

Update execution status indicator.

Args:
    status: One of 'ready', 'running', 'paused', 'error', 'success'

**Parameters:**

- `status: str` *(required)*

##### `update_button_states`

```python
def update_button_states() -> None
```

Update status bar button states based on panel visibility.

##### `update_node_count`

```python
def update_node_count(count: int) -> None
```

Update the node count display.

Args:
    count: Number of nodes

**Parameters:**

- `count: int` *(required)*

##### `update_zoom_display`

```python
def update_zoom_display(zoom_percent: float) -> None
```

Update the zoom level display.

Args:
    zoom_percent: Current zoom percentage

**Parameters:**

- `zoom_percent: float` *(required)*

---

## casare_rpa.presentation.canvas.components.toolbar_builder

**File:** `src\casare_rpa\presentation\canvas\components\toolbar_builder.py`


Toolbar builder for MainWindow toolbar.

Centralizes toolbar creation and styling.


### ToolbarBuilder


Builds the main toolbar for MainWindow.

Responsibilities:
- Create compact unified toolbar
- Apply modern dark theme styling
- Organize execution and automation controls


**Attributes:**

- `TOOLBAR_STYLE: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize toolbar builder. |
| `create_toolbar()` | `QToolBar` | Create unified compact toolbar with execution and debug cont... |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize toolbar builder.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `create_toolbar`

```python
def create_toolbar() -> QToolBar
```

Create unified compact toolbar with execution and debug controls.

Returns:
    Created QToolBar instance

---

## casare_rpa.presentation.canvas.connections.auto_connect

**File:** `src\casare_rpa\presentation\canvas\connections\auto_connect.py`


Auto-connect feature for node graph.

Provides automatic connection suggestions while dragging nodes
with visual feedback (faded connection lines) and right-click
to confirm connections or disconnect nodes.

Now uses ConnectionValidator for type-safe connection checking.


### AutoConnectManager

**Inherits from:** `QObject`


Manages automatic connection suggestions and interactions.

Features:
- Shows faded connection lines to nearest compatible ports while dragging
- Right-click while dragging to create suggested connections
- Right-click on connected node to disconnect all its connections


**Attributes:**

- `connection_suggested: Signal`
- `disconnection_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | - | Initialize the auto-connect manager. |
| `eventFilter(watched, event)` | - | Filter events to detect node dragging and right-clicks. |
| `get_max_distance()` | `float` | Get the current maximum distance for suggestions. |
| `is_active()` | `bool` | Check if auto-connect is active. |
| `reset_drag_state()` | - | Public method to reset drag state - useful after operations ... |
| `set_active(active)` | - | Enable or disable the auto-connect feature. |
| `set_max_distance(distance)` | - | Set the maximum distance for suggesting connections. |

#### Method Details

##### `__init__`

```python
def __init__(graph: NodeGraph, parent: Optional[QObject] = None)
```

Initialize the auto-connect manager.

Args:
    graph: NodeGraph instance to manage
    parent: Optional parent QObject

**Parameters:**

- `graph: NodeGraph` *(required)*
- `parent: Optional[QObject] = None`

##### `eventFilter`

```python
def eventFilter(watched, event)
```

Filter events to detect node dragging and right-clicks.

**Parameters:**

- `watched` *(required)*
- `event` *(required)*

##### `get_max_distance`

```python
def get_max_distance() -> float
```

Get the current maximum distance for suggestions.

##### `is_active`

```python
def is_active() -> bool
```

Check if auto-connect is active.

##### `reset_drag_state`

```python
def reset_drag_state()
```

Public method to reset drag state - useful after operations that might corrupt state.

##### `set_active`

```python
def set_active(active: bool)
```

Enable or disable the auto-connect feature.

**Parameters:**

- `active: bool` *(required)*

##### `set_max_distance`

```python
def set_max_distance(distance: float)
```

Set the maximum distance for suggesting connections.

**Parameters:**

- `distance: float` *(required)*

---

## casare_rpa.presentation.canvas.connections.connection_cutter

**File:** `src\casare_rpa\presentation\canvas\connections\connection_cutter.py`


Connection cutter for node graph.

Provides Houdini-style connection cutting: hold Y and drag LMB
to slice through connection lines and disconnect them.


### ConnectionCutter

**Inherits from:** `QObject`


Manages connection cutting via Y + LMB drag.

Hold Y key and drag with left mouse button to draw a cutting line.
Any connections that intersect with the cutting line will be disconnected
when the mouse is released.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | - | Initialize the connection cutter. |
| `eventFilter(watched, event)` | - | Filter events to detect Y + LMB drag for cutting. |
| `is_active()` | `bool` | Check if connection cutter is active. |
| `set_active(active)` | - | Enable or disable the connection cutter. |

#### Method Details

##### `__init__`

```python
def __init__(graph: NodeGraph, parent: Optional[QObject] = None)
```

Initialize the connection cutter.

Args:
    graph: NodeGraph instance to manage
    parent: Optional parent QObject

**Parameters:**

- `graph: NodeGraph` *(required)*
- `parent: Optional[QObject] = None`

##### `eventFilter`

```python
def eventFilter(watched, event)
```

Filter events to detect Y + LMB drag for cutting.

**Parameters:**

- `watched` *(required)*
- `event` *(required)*

##### `is_active`

```python
def is_active() -> bool
```

Check if connection cutter is active.

##### `set_active`

```python
def set_active(active: bool)
```

Enable or disable the connection cutter.

**Parameters:**

- `active: bool` *(required)*

---

## casare_rpa.presentation.canvas.connections.connection_validator

**File:** `src\casare_rpa\presentation\canvas\connections\connection_validator.py`


Connection Validator for CasareRPA Canvas.

Provides validation services for port connections with strict type checking.
Follows Single Responsibility Principle - handles only connection validation.

References:
- "Clean Architecture" by Robert C. Martin - Single Responsibility Principle
- "The Design of Everyday Things" by Don Norman - Error Prevention


### Functions

#### `get_connection_validator`

```python
def get_connection_validator() -> ConnectionValidator
```

Get the singleton ConnectionValidator instance.

#### `validate_connection`

```python
def validate_connection(source_node: 'VisualNode', source_port: str, target_node: 'VisualNode', target_port: str) -> ConnectionValidation
```

Validate a connection between two ports.

Convenience function for quick validation.

Args:
    source_node: The node with the output port
    source_port: Name of the output port
    target_node: The node with the input port
    target_port: Name of the input port

Returns:
    ConnectionValidation with result and message


### ConnectionValidation

**Decorators:** `@dataclass`


Result of a connection validation check.

Attributes:
    result: The ValidationResult enum value
    is_valid: Quick boolean check for validity
    message: Human-readable description
    source_type: DataType of the source port (if applicable)
    target_type: DataType of the target port (if applicable)


**Attributes:**

- `is_valid: bool`
- `message: str`
- `result: ValidationResult`
- `source_type: Optional[DataType]`
- `target_type: Optional[DataType]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `invalid(result, message, source_type, ...)` | `'ConnectionValidation'` | Create an invalid connection result. |
| `valid(message, source_type, target_type)` | `'ConnectionValidation'` | Create a valid connection result. |

#### Method Details

##### `invalid`

```python
@classmethod
def invalid(result: ValidationResult, message: str, source_type: Optional[DataType] = None, target_type: Optional[DataType] = None) -> 'ConnectionValidation'
```

Create an invalid connection result.

**Parameters:**

- `result: ValidationResult` *(required)*
- `message: str` *(required)*
- `source_type: Optional[DataType] = None`
- `target_type: Optional[DataType] = None`

##### `valid`

```python
@classmethod
def valid(message: str = 'Connection valid', source_type: Optional[DataType] = None, target_type: Optional[DataType] = None) -> 'ConnectionValidation'
```

Create a valid connection result.

**Parameters:**

- `message: str = 'Connection valid'`
- `source_type: Optional[DataType] = None`
- `target_type: Optional[DataType] = None`

### ConnectionValidator


Validates port connections between nodes.

Implements strict type checking - invalid connections are blocked entirely.
Uses PortTypeRegistry for type compatibility rules.

Usage:
    validator = ConnectionValidator()
    result = validator.validate_connection(source_node, "output", target_node, "input")
    if not result.is_valid:
        show_error(result.message)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize validator with type registry. |
| `get_compatible_ports(source_node, source_port_name, target_node)` | `List[str]` | Get list of compatible input ports on target node. |
| `get_incompatible_ports(source_node, source_port_name, target_node)` | `List[str]` | Get list of incompatible input ports on target node. |
| `validate_connection(source_node, source_port_name, target_node, ...)` | `ConnectionValidation` | Validate a proposed connection between two ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize validator with type registry.

##### `get_compatible_ports`

```python
def get_compatible_ports(source_node: 'VisualNode', source_port_name: str, target_node: 'VisualNode') -> List[str]
```

Get list of compatible input ports on target node.

Args:
    source_node: The node with the output port
    source_port_name: Name of the output port
    target_node: The node to find compatible ports on

Returns:
    List of port names that can accept the connection

**Parameters:**

- `source_node: 'VisualNode'` *(required)*
- `source_port_name: str` *(required)*
- `target_node: 'VisualNode'` *(required)*

##### `get_incompatible_ports`

```python
def get_incompatible_ports(source_node: 'VisualNode', source_port_name: str, target_node: 'VisualNode') -> List[str]
```

Get list of incompatible input ports on target node.

Useful for visual feedback - highlighting ports that can't receive.

Args:
    source_node: The node with the output port
    source_port_name: Name of the output port
    target_node: The node to find incompatible ports on

Returns:
    List of port names that cannot accept the connection

**Parameters:**

- `source_node: 'VisualNode'` *(required)*
- `source_port_name: str` *(required)*
- `target_node: 'VisualNode'` *(required)*

##### `validate_connection`

```python
def validate_connection(source_node: 'VisualNode', source_port_name: str, target_node: 'VisualNode', target_port_name: str) -> ConnectionValidation
```

Validate a proposed connection between two ports.

Args:
    source_node: The node with the output port
    source_port_name: Name of the output port
    target_node: The node with the input port
    target_port_name: Name of the input port

Returns:
    ConnectionValidation with result and message

**Parameters:**

- `source_node: 'VisualNode'` *(required)*
- `source_port_name: str` *(required)*
- `target_node: 'VisualNode'` *(required)*
- `target_port_name: str` *(required)*

### ValidationResult

**Inherits from:** `Enum`


Result codes for connection validation.


**Attributes:**

- `ALREADY_CONNECTED: auto`
- `DIRECTION_MISMATCH: auto`
- `EXEC_DATA_MISMATCH: auto`
- `INCOMPATIBLE_TYPES: auto`
- `PORT_NOT_FOUND: auto`
- `SELF_CONNECTION: auto`
- `VALID: auto`

---

## casare_rpa.presentation.canvas.connections.node_insert

**File:** `src\casare_rpa\presentation\canvas\connections\node_insert.py`


Node insertion on connection drop.

Allows dragging a node onto an existing connection line to insert it in-between.
Shows visual feedback (orange highlight) when node overlaps a connection.
Automatically spaces nodes apart with 30px gaps when needed.


### NodeInsertManager

**Inherits from:** `QObject`


Manages inserting nodes onto existing connections.

Features:
- Detects when a dragged node overlaps an exec connection
- Highlights the connection with orange color
- On drop, inserts the node in-between by reconnecting ports
- Auto-spaces nodes with 30px gaps when too close


**Attributes:**

- `node_inserted: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | - | Initialize the node insert manager. |
| `debug_find_pipes()` | - | Debug method to list all pipes in the scene. |
| `eventFilter(watched, event)` | - | Filter events - mostly handled by timer now, but keep for cl... |
| `is_active()` | `bool` | Check if node insert is active. |
| `set_active(active)` | - | Enable or disable the node insert feature. |

#### Method Details

##### `__init__`

```python
def __init__(graph: NodeGraph, parent: Optional[QObject] = None)
```

Initialize the node insert manager.

**Parameters:**

- `graph: NodeGraph` *(required)*
- `parent: Optional[QObject] = None`

##### `debug_find_pipes`

```python
def debug_find_pipes()
```

Debug method to list all pipes in the scene.

##### `eventFilter`

```python
def eventFilter(watched, event)
```

Filter events - mostly handled by timer now, but keep for cleanup.

**Parameters:**

- `watched` *(required)*
- `event` *(required)*

##### `is_active`

```python
def is_active() -> bool
```

Check if node insert is active.

##### `set_active`

```python
def set_active(active: bool)
```

Enable or disable the node insert feature.

**Parameters:**

- `active: bool` *(required)*

---

## casare_rpa.presentation.canvas.controllers.autosave_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\autosave_controller.py`


Autosave controller for automatic workflow saving.

Handles automatic workflow saving functionality:
- Periodic autosave based on settings
- Autosave timer management
- Settings synchronization


### AutosaveController

**Inherits from:** `BaseController`


Manages automatic workflow saving.

Single Responsibility: Periodic autosave execution and timer management.

Signals:
    autosave_triggered: Emitted when autosave is triggered
    autosave_completed: Emitted when autosave completes successfully
    autosave_failed: Emitted when autosave fails (str: error_message)


**Attributes:**

- `autosave_completed: Signal`
- `autosave_failed: Signal`
- `autosave_triggered: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize autosave controller. |
| `cleanup()` | `None` | Clean up resources. |
| `disable_autosave()` | `None` | Disable autosave. |
| `enable_autosave(interval_minutes)` | `None` | Enable autosave with specified interval. |
| `initialize()` | `None` | Initialize controller and setup autosave timer. |
| `is_enabled()` | `bool` | Check if autosave is currently enabled. |
| `trigger_autosave_now()` | `None` | Manually trigger an autosave immediately. |
| `update_interval(interval_minutes)` | `None` | Update autosave interval. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize autosave controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `disable_autosave`

```python
def disable_autosave() -> None
```

Disable autosave.

##### `enable_autosave`

```python
def enable_autosave(interval_minutes: int) -> None
```

Enable autosave with specified interval.

Args:
    interval_minutes: Autosave interval in minutes

**Parameters:**

- `interval_minutes: int` *(required)*

##### `initialize`

```python
def initialize() -> None
```

Initialize controller and setup autosave timer.

##### `is_enabled`

```python
def is_enabled() -> bool
```

Check if autosave is currently enabled.

Returns:
    bool: True if autosave timer is active

##### `trigger_autosave_now`

```python
def trigger_autosave_now() -> None
```

Manually trigger an autosave immediately.

##### `update_interval`

```python
def update_interval(interval_minutes: int) -> None
```

Update autosave interval.

Args:
    interval_minutes: New interval in minutes

**Parameters:**

- `interval_minutes: int` *(required)*

---

## casare_rpa.presentation.canvas.controllers.base_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\base_controller.py`


Base controller class for Canvas controllers.

All controllers follow the same pattern for consistency and lifecycle management.


### BaseController

**Inherits from:** `QObject`


Base class for all Canvas controllers.

Controllers are responsible for:
- Handling user interactions from UI
- Updating model/state
- Coordinating between components
- Emitting signals for UI updates

Controllers should NOT:
- Directly manipulate UI widgets (use signals instead)
- Contain domain logic (delegate to use cases/services)
- Access infrastructure directly (use dependency injection)

Lifecycle:
    1. __init__: Store references, initialize state
    2. initialize: Setup connections, load resources
    3. cleanup: Release resources, disconnect signals


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window, parent)` | - | Initialize base controller. |
| `cleanup()` | `None` | Clean up controller resources. |
| `initialize()` | `None` | Initialize controller resources and connections. |
| `is_initialized()` | `bool` | Check if controller is initialized. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow', parent: Optional[QObject] = None)
```

Initialize base controller.

Args:
    main_window: Reference to main window for accessing shared components
    parent: Optional parent QObject for Qt ownership

**Parameters:**

- `main_window: 'MainWindow'` *(required)*
- `parent: Optional[QObject] = None`

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

Called when main window is closing.
Override to disconnect signals and release resources.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller resources and connections.

Called after all controllers are instantiated.
Override to setup signal/slot connections and load initial state.

##### `is_initialized`

```python
@property
def is_initialized() -> bool
```

Check if controller is initialized.

### QABCMeta

**Inherits from:** `type(QObject)`, `ABCMeta`


Metaclass that combines QObject and ABC.


---

## casare_rpa.presentation.canvas.controllers.connection_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\connection_controller.py`


Connection management controller.

Handles all connection-related operations:
- Connection creation and deletion
- Connection validation
- Port compatibility checking
- Auto-connect mode


### ConnectionController

**Inherits from:** `BaseController`


Manages connections between nodes in the workflow graph.

Single Responsibility: Connection lifecycle and validation.

Signals:
    connection_created: Emitted when a connection is created (str: source_id, str: target_id)
    connection_deleted: Emitted when a connection is deleted (str: source_id, str: target_id)
    connection_validation_error: Emitted when connection validation fails (str: error_message)
    auto_connect_toggled: Emitted when auto-connect mode changes (bool: enabled)


**Attributes:**

- `auto_connect_toggled: Signal`
- `connection_created: Signal`
- `connection_deleted: Signal`
- `connection_validation_error: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize connection controller. |
| `auto_connect_enabled()` | `bool` | Check if auto-connect mode is enabled. |
| `cleanup()` | `None` | Clean up resources. |
| `create_connection(source_node_id, source_port, target_node_id, ...)` | `bool` | Create a connection between two nodes. |
| `delete_connection(source_node_id, target_node_id)` | `None` | Delete a connection between two nodes. |
| `initialize()` | `None` | Initialize controller. |
| `toggle_auto_connect(enabled)` | `None` | Toggle auto-connect mode. |
| `validate_connection(source_node_id, source_port, target_node_id, ...)` | `Tuple[bool, Optional[str]]` | Validate a connection before creation. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize connection controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `auto_connect_enabled`

```python
@property
def auto_connect_enabled() -> bool
```

Check if auto-connect mode is enabled.

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `create_connection`

```python
def create_connection(source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> bool
```

Create a connection between two nodes.

Args:
    source_node_id: ID of source node
    source_port: Name of source port
    target_node_id: ID of target node
    target_port: Name of target port

Returns:
    True if connection was created, False if validation failed

**Parameters:**

- `source_node_id: str` *(required)*
- `source_port: str` *(required)*
- `target_node_id: str` *(required)*
- `target_port: str` *(required)*

##### `delete_connection`

```python
def delete_connection(source_node_id: str, target_node_id: str) -> None
```

Delete a connection between two nodes.

Args:
    source_node_id: ID of source node
    target_node_id: ID of target node

**Parameters:**

- `source_node_id: str` *(required)*
- `target_node_id: str` *(required)*

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `toggle_auto_connect`

```python
def toggle_auto_connect(enabled: bool) -> None
```

Toggle auto-connect mode.

Args:
    enabled: True to enable auto-connect, False to disable

**Parameters:**

- `enabled: bool` *(required)*

##### `validate_connection`

```python
def validate_connection(source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> Tuple[bool, Optional[str]]
```

Validate a connection before creation.

Args:
    source_node_id: ID of source node
    source_port: Name of source port
    target_node_id: ID of target node
    target_port: Name of target port

Returns:
    Tuple of (is_valid, error_message)

**Parameters:**

- `source_node_id: str` *(required)*
- `source_port: str` *(required)*
- `target_node_id: str` *(required)*
- `target_port: str` *(required)*

---

## casare_rpa.presentation.canvas.controllers.event_bus_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\event_bus_controller.py`


Event bus controller for centralized event routing.

Handles event coordination between controllers:
- Cross-controller communication
- Event filtering and logging
- Event history tracking
- Debugging support


### Event

**Decorators:** `@dataclass`


Represents an event in the system.


**Attributes:**

- `data: Dict[str, Any]`
- `source: str`
- `timestamp: datetime`
- `type: str`

### EventBusController

**Inherits from:** `BaseController`


Centralized event bus for controller communication.

Single Responsibility: Event routing and coordination.

This controller acts as a mediator between other controllers,
enabling loose coupling and centralized event logging.

Signals:
    event_dispatched: Emitted when any event is dispatched (Event)


**Attributes:**

- `event_dispatched: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize event bus controller. |
| `cleanup()` | `None` | Clean up resources. |
| `clear_event_history()` | `None` | Clear event history. |
| `disable_event_filtering()` | `None` | Disable event filtering. |
| `dispatch(event_type, source, data)` | `None` | Dispatch an event to all subscribers. |
| `enable_event_filtering(event_types)` | `None` | Enable filtering to block specific event types. |
| `get_event_history(count)` | `List[Event]` | Get recent event history. |
| `get_event_types()` | `List[str]` | Get list of all subscribed event types. |
| `get_subscriber_count(event_type)` | `int` | Get number of subscribers. |
| `initialize()` | `None` | Initialize controller. |
| `subscribe(event_type, callback)` | `None` | Subscribe to an event type. |
| `unsubscribe(event_type, callback)` | `None` | Unsubscribe from an event type. |

#### Method Details

##### `__init__`

```python
def __init__(main_window)
```

Initialize event bus controller.

**Parameters:**

- `main_window` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `clear_event_history`

```python
def clear_event_history() -> None
```

Clear event history.

##### `disable_event_filtering`

```python
def disable_event_filtering() -> None
```

Disable event filtering.

##### `dispatch`

```python
def dispatch(event_type: str, source: str, data: Optional[Dict[str, Any]] = None) -> None
```

Dispatch an event to all subscribers.

Args:
    event_type: Type of event to dispatch
    source: Source controller/component name
    data: Optional event data

**Parameters:**

- `event_type: str` *(required)*
- `source: str` *(required)*
- `data: Optional[Dict[str, Any]] = None`

##### `enable_event_filtering`

```python
def enable_event_filtering(event_types: List[str]) -> None
```

Enable filtering to block specific event types.

Args:
    event_types: List of event types to filter out

**Parameters:**

- `event_types: List[str]` *(required)*

##### `get_event_history`

```python
def get_event_history(count: Optional[int] = None) -> List[Event]
```

Get recent event history.

Args:
    count: Number of recent events to return (None for all)

Returns:
    List of recent events

**Parameters:**

- `count: Optional[int] = None`

##### `get_event_types`

```python
def get_event_types() -> List[str]
```

Get list of all subscribed event types.

Returns:
    List of event type names

##### `get_subscriber_count`

```python
def get_subscriber_count(event_type: Optional[str] = None) -> int
```

Get number of subscribers.

Args:
    event_type: Specific event type, or None for total count

Returns:
    Number of subscribers

**Parameters:**

- `event_type: Optional[str] = None`

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `subscribe`

```python
def subscribe(event_type: str, callback: Callable[[Event], None]) -> None
```

Subscribe to an event type.

Args:
    event_type: Type of event to subscribe to
    callback: Function to call when event occurs

**Parameters:**

- `event_type: str` *(required)*
- `callback: Callable[[Event], None]` *(required)*

##### `unsubscribe`

```python
def unsubscribe(event_type: str, callback: Callable[[Event], None]) -> None
```

Unsubscribe from an event type.

Args:
    event_type: Type of event to unsubscribe from
    callback: Callback function to remove

**Parameters:**

- `event_type: str` *(required)*
- `callback: Callable[[Event], None]` *(required)*

### EventTypes


Standard event types used across controllers.


**Attributes:**

- `CONNECTION_CREATED: str`
- `CONNECTION_DELETED: str`
- `EXECUTION_COMPLETED: str`
- `EXECUTION_ERROR: str`
- `EXECUTION_PAUSED: str`
- `EXECUTION_RESUMED: str`
- `EXECUTION_STARTED: str`
- `EXECUTION_STOPPED: str`
- `NODE_DESELECTED: str`
- `NODE_DISABLED: str`
- `NODE_ENABLED: str`
- `NODE_PROPERTY_CHANGED: str`
- `NODE_SELECTED: str`
- `PANEL_TAB_CHANGED: str`
- `PANEL_TOGGLED: str`
- `VALIDATION_COMPLETED: str`
- `VALIDATION_ERROR: str`
- `VALIDATION_STARTED: str`
- `WORKFLOW_CLOSED: str`
- `WORKFLOW_CREATED: str`
- `WORKFLOW_LOADED: str`
- `WORKFLOW_MODIFIED: str`
- `WORKFLOW_SAVED: str`

---

## casare_rpa.presentation.canvas.controllers.example_workflow_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\example_workflow_controller.py`


Example Workflow Controller demonstrating EventBus usage.

This controller showcases best practices for using the EventBus system:
    - Inherits from EventHandler for automatic subscription management
    - Uses @event_handler decorator for clean event handling
    - Publishes events for state changes
    - Minimal coupling to other components

This serves as a template for other controllers to follow.


### ExampleWorkflowController

**Inherits from:** `EventHandler`


Example controller for workflow lifecycle management.

Demonstrates EventBus usage patterns:
    - Event subscription via @event_handler decorator
    - Event publishing for state changes
    - Automatic cleanup via EventHandler base class

Responsibilities:
    - Create new workflows
    - Open existing workflows
    - Save workflows
    - Track workflow state (modified, current file)

Events Published:
    - WORKFLOW_NEW: When new workflow is created
    - WORKFLOW_OPENED: When workflow is loaded from file
    - WORKFLOW_SAVED: When workflow is saved to file
    - WORKFLOW_MODIFIED: When workflow has unsaved changes

Events Subscribed:
    - NODE_ADDED: Marks workflow as modified
    - NODE_REMOVED: Marks workflow as modified
    - CONNECTION_ADDED: Marks workflow as modified
    - CONNECTION_REMOVED: Marks workflow as modified

Example:
    # Create controller
    controller = ExampleWorkflowController()

    # Controller automatically subscribes to events
    # and publishes events when state changes

    # Create new workflow
    await controller.new_workflow("My Workflow")

    # Save workflow
    await controller.save_workflow(Path("workflow.json"))

    # Cleanup when done
    controller.cleanup()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - | Initialize workflow controller. |
| `cleanup()` | `None` | Cleanup controller resources. |
| `async close_workflow()` | `None` | Close current workflow. |
| `current_file()` | `Optional[Path]` | Get current workflow file path. |
| `is_modified()` | `bool` | Check if workflow has unsaved changes. |
| `mark_modified()` | `None` | Mark workflow as having unsaved changes. |
| `async new_workflow(name)` | `None` | Create a new workflow. |
| `async open_workflow(file_path)` | `None` | Open an existing workflow from file. |
| `async save_workflow(file_path)` | `None` | Save workflow to file. |
| `workflow_name()` | `Optional[str]` | Get current workflow name. |

#### Method Details

##### `__init__`

```python
def __init__()
```

Initialize workflow controller.

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup controller resources.

Automatically unsubscribes from all events via EventHandler base class.

##### `close_workflow`

```python
async def close_workflow() -> None
```

Close current workflow.

Events Published:
    WORKFLOW_CLOSED: When workflow is closed

##### `current_file`

```python
@property
def current_file() -> Optional[Path]
```

Get current workflow file path.

##### `is_modified`

```python
@property
def is_modified() -> bool
```

Check if workflow has unsaved changes.

##### `mark_modified`

```python
def mark_modified() -> None
```

Mark workflow as having unsaved changes.

Events Published:
    WORKFLOW_MODIFIED: When workflow is marked modified

##### `new_workflow`

```python
async def new_workflow(name: str = 'Untitled') -> None
```

Create a new workflow.

Args:
    name: Name for the new workflow

Events Published:
    WORKFLOW_NEW: When workflow is created

**Parameters:**

- `name: str = 'Untitled'`

##### `open_workflow`

```python
async def open_workflow(file_path: Path) -> None
```

Open an existing workflow from file.

Args:
    file_path: Path to workflow file

Events Published:
    WORKFLOW_OPENED: When workflow is loaded

Raises:
    FileNotFoundError: If file doesn't exist
    ValueError: If file is invalid

**Parameters:**

- `file_path: Path` *(required)*

##### `save_workflow`

```python
async def save_workflow(file_path: Optional[Path] = None) -> None
```

Save workflow to file.

Args:
    file_path: Path to save to (uses current file if None)

Events Published:
    WORKFLOW_SAVED: When workflow is saved
    WORKFLOW_SAVE_AS: When workflow is saved with new filename

Raises:
    ValueError: If no file path specified and no current file

**Parameters:**

- `file_path: Optional[Path] = None`

##### `workflow_name`

```python
@property
def workflow_name() -> Optional[str]
```

Get current workflow name.

---

## casare_rpa.presentation.canvas.controllers.execution_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\execution_controller.py`


Workflow execution controller.

Handles all execution-related operations:
- Run/Pause/Resume/Stop
- Run to node (partial execution)
- Run single node (isolated execution)
- Debug mode controls
- EventBus integration for node visual feedback


### ExecutionController

**Inherits from:** `BaseController`


Manages workflow execution lifecycle.

Single Responsibility: Execution control and state management.

Signals:
    execution_started: Emitted when workflow execution starts
    execution_paused: Emitted when workflow execution is paused
    execution_resumed: Emitted when workflow execution is resumed
    execution_stopped: Emitted when workflow execution is stopped
    execution_completed: Emitted when workflow execution completes
    execution_error: Emitted when workflow execution fails (str: error)
    run_to_node_requested: Emitted when user wants to run to a specific node (str: node_id)
    run_single_node_requested: Emitted when user wants to run only one node (str: node_id)


**Attributes:**

- `execution_completed: Signal`
- `execution_error: Signal`
- `execution_paused: Signal`
- `execution_resumed: Signal`
- `execution_started: Signal`
- `execution_stopped: Signal`
- `run_single_node_requested: Signal`
- `run_to_node_requested: Signal`
- `trigger_fired: Signal`
- `trigger_listening_started: Signal`
- `trigger_listening_stopped: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize execution controller. |
| `cleanup()` | `None` | Clean up resources. |
| `async cleanup_async()` | `None` | Async cleanup that properly awaits task cancellation. |
| `initialize()` | `None` | Initialize controller. |
| `is_listening()` | `bool` | Check if trigger is actively listening. |
| `is_paused()` | `bool` | Check if workflow is currently paused. |
| `is_running()` | `bool` | Check if workflow is currently executing. |
| `on_execution_completed()` | `None` | Handle workflow execution completion. |
| `on_execution_error(error_message)` | `None` | Handle workflow execution error. |
| `pause_workflow()` | `None` | Pause running workflow. |
| `resume_workflow()` | `None` | Resume paused workflow. |
| `run_all_workflows()` | `None` | Run all workflows on canvas concurrently (Shift+F3). |
| `run_single_node()` | `None` | Run only the selected node in isolation (F5). |
| `run_to_node()` | `None` | Run workflow up to the selected node (F4). |
| `run_workflow()` | `None` | Run workflow from start to end (F3). |
| `set_workflow_runner(runner)` | `None` | Set the workflow runner instance. |
| `start_trigger_listening()` | `None` | Start listening for trigger events (F9). |
| `stop_trigger_listening()` | `None` | Stop listening for trigger events (F10 or Esc). |
| `stop_workflow()` | `None` | Stop running workflow. |
| `toggle_pause(checked)` | `None` | Toggle pause/resume state. |
| `toggle_trigger_listening()` | `None` | Toggle trigger listening on/off. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize execution controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

Note: BaseController.cleanup() is synchronous by design (called during Qt
widget destruction). We cannot await task cancellation here. The task's
CancelledError will be handled in _run_workflow_async() which logs and
exits gracefully. For truly clean shutdown, call cleanup_async() if an
event loop is available.

##### `cleanup_async`

```python
async def cleanup_async() -> None
```

Async cleanup that properly awaits task cancellation.

Use this method when an event loop is available for proper async cleanup.
Falls back to sync cleanup for non-async resources.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `is_listening`

```python
@property
def is_listening() -> bool
```

Check if trigger is actively listening.

##### `is_paused`

```python
@property
def is_paused() -> bool
```

Check if workflow is currently paused.

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if workflow is currently executing.

##### `on_execution_completed`

```python
def on_execution_completed() -> None
```

Handle workflow execution completion.

##### `on_execution_error`

```python
def on_execution_error(error_message: str) -> None
```

Handle workflow execution error.

Args:
    error_message: Error description

**Parameters:**

- `error_message: str` *(required)*

##### `pause_workflow`

```python
def pause_workflow() -> None
```

Pause running workflow.

##### `resume_workflow`

```python
def resume_workflow() -> None
```

Resume paused workflow.

##### `run_all_workflows`

```python
def run_all_workflows() -> None
```

Run all workflows on canvas concurrently (Shift+F3).

When the canvas contains multiple independent workflows (each with its
own StartNode), this executes them all in parallel. Each workflow gets
SHARED variables but SEPARATE browser instances.

##### `run_single_node`

```python
def run_single_node() -> None
```

Run only the selected node in isolation (F5).

##### `run_to_node`

```python
def run_to_node() -> None
```

Run workflow up to the selected node (F4).

##### `run_workflow`

```python
def run_workflow() -> None
```

Run workflow from start to end (F3).

Auto-detects trigger nodes: if workflow has a trigger, starts listening mode
instead of one-shot execution.

##### `set_workflow_runner`

```python
def set_workflow_runner(runner: 'CanvasWorkflowRunner') -> None
```

Set the workflow runner instance.

Called by CasareRPAApp after initialization.

Args:
    runner: CanvasWorkflowRunner instance

**Parameters:**

- `runner: 'CanvasWorkflowRunner'` *(required)*

##### `start_trigger_listening`

```python
def start_trigger_listening() -> None
```

Start listening for trigger events (F9).

For workflows with a trigger node, this activates background listening.
When the trigger fires (e.g., schedule interval), the workflow executes.

##### `stop_trigger_listening`

```python
def stop_trigger_listening() -> None
```

Stop listening for trigger events (F10 or Esc).

Stops the active trigger and returns to idle state.

##### `stop_workflow`

```python
def stop_workflow() -> None
```

Stop running workflow.

##### `toggle_pause`

```python
def toggle_pause(checked: bool) -> None
```

Toggle pause/resume state.

Args:
    checked: True to pause, False to resume

**Parameters:**

- `checked: bool` *(required)*

##### `toggle_trigger_listening`

```python
def toggle_trigger_listening() -> None
```

Toggle trigger listening on/off.

---

## casare_rpa.presentation.canvas.controllers.menu_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\menu_controller.py`


Menu and action management controller.

Handles all menu-related operations:
- Menu bar creation and updates
- Toolbar creation and updates
- Action state management
- Hotkey management
- Recent files menu
- About and help dialogs
- Desktop selector builder


### MenuController

**Inherits from:** `BaseController`


Manages menus, toolbars, and actions.

Single Responsibility: Menu/action lifecycle and state management.

Signals:
    action_state_changed: Emitted when an action's enabled state changes (str: action_name, bool: enabled)
    recent_files_updated: Emitted when recent files list is updated
    hotkey_changed: Emitted when a hotkey is modified (str: action_name, str: new_shortcut)
    recent_file_opened: Emitted when a recent file is opened (str: file_path)
    recent_files_cleared: Emitted when recent files list is cleared
    about_dialog_shown: Emitted when about dialog is displayed
    desktop_selector_shown: Emitted when desktop selector builder is displayed


**Attributes:**

- `about_dialog_shown: Signal`
- `action_state_changed: Signal`
- `desktop_selector_shown: Signal`
- `hotkey_changed: Signal`
- `recent_file_opened: Signal`
- `recent_files_cleared: Signal`
- `recent_files_updated: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize menu controller. |
| `add_recent_file(file_path)` | `None` | Add a file to the recent files list. |
| `check_for_updates()` | `None` | Check for application updates. |
| `cleanup()` | `None` | Clean up resources. |
| `clear_recent_files()` | `None` | Clear the recent files list. |
| `get_recent_files()` | `List[dict]` | Get the list of recent files. |
| `initialize()` | `None` | Initialize controller. |
| `open_command_palette()` | `None` | Open the command palette dialog. |
| `open_hotkey_manager()` | `None` | Open the hotkey manager dialog. |
| `open_performance_dashboard()` | `None` | Open the performance dashboard dialog. |
| `open_preferences()` | `None` | Open the preferences dialog. |
| `open_recent_file(file_path)` | `None` | Open a recent file by path. |
| `show_about_dialog()` | `None` | Show the About dialog with application information. |
| `show_desktop_selector_builder()` | `None` | Show the Desktop Selector Builder dialog. |
| `show_documentation()` | `None` | Open the documentation in the default web browser. |
| `show_keyboard_shortcuts()` | `None` | Show the keyboard shortcuts dialog. |
| `update_action_state(action_name, enabled)` | `None` | Update an action's enabled state. |
| `update_recent_files_menu()` | `None` | Update the recent files submenu. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize menu controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `add_recent_file`

```python
def add_recent_file(file_path: Path) -> None
```

Add a file to the recent files list.

Args:
    file_path: Path to the workflow file to add

**Parameters:**

- `file_path: Path` *(required)*

##### `check_for_updates`

```python
def check_for_updates() -> None
```

Check for application updates.

Checks for newer versions and notifies the user.

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `clear_recent_files`

```python
def clear_recent_files() -> None
```

Clear the recent files list.

Removes all entries from the recent files list and updates the menu.

##### `get_recent_files`

```python
def get_recent_files() -> List[dict]
```

Get the list of recent files.

Returns:
    List of dicts with 'path', 'name', 'last_opened' keys

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `open_command_palette`

```python
def open_command_palette() -> None
```

Open the command palette dialog.

##### `open_hotkey_manager`

```python
def open_hotkey_manager() -> None
```

Open the hotkey manager dialog.

##### `open_performance_dashboard`

```python
def open_performance_dashboard() -> None
```

Open the performance dashboard dialog.

##### `open_preferences`

```python
def open_preferences() -> None
```

Open the preferences dialog.

##### `open_recent_file`

```python
def open_recent_file(file_path: str) -> None
```

Open a recent file by path.

Args:
    file_path: Path to the file to open

**Parameters:**

- `file_path: str` *(required)*

##### `show_about_dialog`

```python
def show_about_dialog() -> None
```

Show the About dialog with application information.

Displays version info, credits, and application description.

##### `show_desktop_selector_builder`

```python
def show_desktop_selector_builder() -> None
```

Show the Desktop Selector Builder dialog.

Opens the visual tool for building desktop element selectors.

##### `show_documentation`

```python
def show_documentation() -> None
```

Open the documentation in the default web browser.

Opens the online documentation or local docs if available.

##### `show_keyboard_shortcuts`

```python
def show_keyboard_shortcuts() -> None
```

Show the keyboard shortcuts dialog.

Displays a reference dialog with all available keyboard shortcuts.

##### `update_action_state`

```python
def update_action_state(action_name: str, enabled: bool) -> None
```

Update an action's enabled state.

Args:
    action_name: Name of action (e.g., "save", "run", "pause")
    enabled: True to enable, False to disable

**Parameters:**

- `action_name: str` *(required)*
- `enabled: bool` *(required)*

##### `update_recent_files_menu`

```python
def update_recent_files_menu() -> None
```

Update the recent files submenu.

---

## casare_rpa.presentation.canvas.controllers.node_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\node_controller.py`


Node operations controller.

Handles all node-related operations:
- Node selection and navigation
- Node enable/disable state
- Node search and filtering
- Property updates
- Node registry initialization and management


### NodeController

**Inherits from:** `BaseController`


Manages node operations in the workflow graph.

Single Responsibility: Node manipulation and state management.

Signals:
    node_selected: Emitted when a node is selected (str: node_id)
    node_deselected: Emitted when a node is deselected (str: node_id)
    node_disabled: Emitted when a node is disabled (str: node_id)
    node_enabled: Emitted when a node is enabled (str: node_id)
    node_navigated: Emitted when navigating to a node (str: node_id)
    node_property_changed: Emitted when node property changes (str: node_id, str: property, Any: value)


**Attributes:**

- `node_deselected: Signal`
- `node_disabled: Signal`
- `node_enabled: Signal`
- `node_navigated: Signal`
- `node_property_changed: Signal`
- `node_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize node controller. |
| `cleanup()` | `None` | Clean up resources. |
| `disable_all_selected()` | `None` | Toggle disable state on all selected nodes (hotkey 5). |
| `find_node()` | `None` | Open the node search dialog (Ctrl+F). |
| `get_nearest_exec_out()` | `None` | Find and select the closest exec_out port to cursor (hotkey ... |
| `get_selected_nodes()` | `list` | Get list of currently selected node IDs. |
| `initialize()` | `None` | Initialize controller. |
| `navigate_to_node(node_id)` | `None` | Navigate to and select a specific node. |
| `select_nearest_node()` | `None` | Select the nearest node to the current mouse cursor position... |
| `toggle_disable_node()` | `None` | Toggle disable state on nearest node to mouse (hotkey 4). |
| `update_node_property(node_id, property_name, value)` | `None` | Update a node's property. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize node controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `disable_all_selected`

```python
def disable_all_selected() -> None
```

Toggle disable state on all selected nodes (hotkey 5).

If any selected node is enabled, disables all.
If all selected nodes are disabled, enables all.

##### `find_node`

```python
def find_node() -> None
```

Open the node search dialog (Ctrl+F).

##### `get_nearest_exec_out`

```python
def get_nearest_exec_out() -> None
```

Find and select the closest exec_out port to cursor (hotkey 3).

Searches all nodes for exec_out ports and finds the one closest
to the mouse cursor position, then starts a live connection from it.

##### `get_selected_nodes`

```python
def get_selected_nodes() -> list
```

Get list of currently selected node IDs.

Returns:
    List of node_id strings for selected nodes

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `navigate_to_node`

```python
def navigate_to_node(node_id: str) -> None
```

Navigate to and select a specific node.

Args:
    node_id: ID of node to navigate to

**Parameters:**

- `node_id: str` *(required)*

##### `select_nearest_node`

```python
def select_nearest_node() -> None
```

Select the nearest node to the current mouse cursor position (hotkey 2).

##### `toggle_disable_node`

```python
def toggle_disable_node() -> None
```

Toggle disable state on nearest node to mouse (hotkey 4).

Disabled nodes are bypassed during execution.

##### `update_node_property`

```python
def update_node_property(node_id: str, property_name: str, value) -> None
```

Update a node's property.

Args:
    node_id: ID of node to update
    property_name: Name of property to change
    value: New property value

**Parameters:**

- `node_id: str` *(required)*
- `property_name: str` *(required)*
- `value` *(required)*

---

## casare_rpa.presentation.canvas.controllers.panel_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\panel_controller.py`


Panel visibility and management controller.

Handles all panel-related operations:
- Bottom panel (Output, Log, Variables, Validation tabs)
- Properties panel (right dock)
- Variable inspector dock
- Execution timeline dock
- Minimap overlay
- Panel state persistence


### PanelController

**Inherits from:** `BaseController`


Manages panel visibility and state.

Single Responsibility: Panel lifecycle and visibility management.

Signals:
    bottom_panel_toggled: Emitted when bottom panel visibility changes (bool: visible)
    properties_panel_toggled: Emitted when properties panel visibility changes (bool: visible)
    variable_inspector_toggled: Emitted when variable inspector visibility changes (bool: visible)
    minimap_toggled: Emitted when minimap visibility changes (bool: visible)
    panel_tab_changed: Emitted when active tab changes (str: tab_name)


**Attributes:**

- `bottom_panel_toggled: Signal`
- `minimap_toggled: Signal`
- `panel_tab_changed: Signal`
- `properties_panel_toggled: Signal`
- `variable_inspector_toggled: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize panel controller. |
| `cleanup()` | `None` | Clean up resources. |
| `get_validation_errors()` | `list` | Get current validation errors. |
| `hide_bottom_panel()` | `None` | Hide the bottom panel. |
| `hide_minimap()` | `None` | Hide the minimap overlay. |
| `hide_variable_inspector()` | `None` | Hide the Variable Inspector dock. |
| `initialize()` | `None` | Initialize controller. |
| `navigate_to_node(node_id)` | `None` | Handle navigation to a node from a panel. |
| `show_bottom_panel()` | `None` | Show the bottom panel. |
| `show_minimap()` | `None` | Show the minimap overlay. |
| `show_panel_tab(tab_name)` | `None` | Switch to a specific tab in the bottom panel. |
| `show_validation_tab_if_errors()` | `None` | Show validation tab if there are validation errors. |
| `show_variable_inspector()` | `None` | Show the Variable Inspector dock. |
| `toggle_bottom_panel(visible)` | `None` | Toggle bottom panel visibility. |
| `toggle_minimap(visible)` | `None` | Toggle minimap overlay visibility. |
| `toggle_panel_tab(tab_name)` | `None` | Toggle bottom panel to specific tab or hide if already on th... |
| `toggle_properties_panel(visible)` | `None` | Toggle properties panel visibility. |
| `toggle_variable_inspector(visible)` | `None` | Toggle variable inspector visibility. |
| `trigger_validation()` | `None` | Trigger workflow validation and update validation panel. |
| `update_status_bar_buttons()` | `None` | Update status bar button states based on current panel visib... |
| `update_variables_panel(variables)` | `None` | Update the variables panel with new values. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize panel controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `get_validation_errors`

```python
def get_validation_errors() -> list
```

Get current validation errors.

Returns:
    List of validation error messages

##### `hide_bottom_panel`

```python
def hide_bottom_panel() -> None
```

Hide the bottom panel.

##### `hide_minimap`

```python
def hide_minimap() -> None
```

Hide the minimap overlay.

##### `hide_variable_inspector`

```python
def hide_variable_inspector() -> None
```

Hide the Variable Inspector dock.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `navigate_to_node`

```python
def navigate_to_node(node_id: str) -> None
```

Handle navigation to a node from a panel.

Args:
    node_id: ID of node to navigate to

**Parameters:**

- `node_id: str` *(required)*

##### `show_bottom_panel`

```python
def show_bottom_panel() -> None
```

Show the bottom panel.

##### `show_minimap`

```python
def show_minimap() -> None
```

Show the minimap overlay.

##### `show_panel_tab`

```python
def show_panel_tab(tab_name: str) -> None
```

Switch to a specific tab in the bottom panel.

Args:
    tab_name: Name of tab to show (e.g., "Output", "Log", "Variables", "Validation")

**Parameters:**

- `tab_name: str` *(required)*

##### `show_validation_tab_if_errors`

```python
def show_validation_tab_if_errors() -> None
```

Show validation tab if there are validation errors.

##### `show_variable_inspector`

```python
def show_variable_inspector() -> None
```

Show the Variable Inspector dock.

##### `toggle_bottom_panel`

```python
def toggle_bottom_panel(visible: bool) -> None
```

Toggle bottom panel visibility.

Args:
    visible: True to show, False to hide

**Parameters:**

- `visible: bool` *(required)*

##### `toggle_minimap`

```python
def toggle_minimap(visible: bool) -> None
```

Toggle minimap overlay visibility.

Args:
    visible: True to show, False to hide

**Parameters:**

- `visible: bool` *(required)*

##### `toggle_panel_tab`

```python
def toggle_panel_tab(tab_name: str) -> None
```

Toggle bottom panel to specific tab or hide if already on that tab.

Args:
    tab_name: Tab name to toggle ('variables', 'output', 'log', 'validation', 'history')

**Parameters:**

- `tab_name: str` *(required)*

##### `toggle_properties_panel`

```python
def toggle_properties_panel(visible: bool) -> None
```

Toggle properties panel visibility.

Args:
    visible: True to show, False to hide

**Parameters:**

- `visible: bool` *(required)*

##### `toggle_variable_inspector`

```python
def toggle_variable_inspector(visible: bool) -> None
```

Toggle variable inspector visibility.

Args:
    visible: True to show, False to hide

**Parameters:**

- `visible: bool` *(required)*

##### `trigger_validation`

```python
def trigger_validation() -> None
```

Trigger workflow validation and update validation panel.

##### `update_status_bar_buttons`

```python
def update_status_bar_buttons() -> None
```

Update status bar button states based on current panel visibility and tab.

##### `update_variables_panel`

```python
def update_variables_panel(variables: dict) -> None
```

Update the variables panel with new values.

Args:
    variables: Dictionary of variable name -> value

**Parameters:**

- `variables: dict` *(required)*

---

## casare_rpa.presentation.canvas.controllers.preferences_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\preferences_controller.py`


Preferences controller for user settings and configuration.

Handles application preferences and settings:
- Settings management
- Hotkey configuration
- Theme management
- Preference persistence


### PreferencesController

**Inherits from:** `BaseController`


Manages user preferences and settings.

Single Responsibility: Settings and configuration management.

Signals:
    preferences_updated: Emitted when preferences are updated
    theme_changed: Emitted when theme is changed (str: theme_name)
    hotkey_updated: Emitted when hotkey is updated (str: action, str: hotkey)
    setting_changed: Emitted when individual setting changes (str: key, Any: value)


**Attributes:**

- `hotkey_updated: Signal`
- `preferences_updated: Signal`
- `setting_changed: Signal`
- `theme_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize preferences controller. |
| `cleanup()` | `None` | Clean up resources. |
| `get_autosave_interval()` | `int` | Get autosave interval in minutes. |
| `get_hotkeys()` | `Dict[str, str]` | Get all hotkey bindings. |
| `get_setting(key, default)` | `Any` | Get a setting value. |
| `get_settings_manager()` | `Any` | Get the settings manager instance. |
| `initialize()` | `None` | Initialize controller and setup event subscriptions. |
| `is_autosave_enabled()` | `bool` | Check if autosave is enabled. |
| `reset_preferences()` | `bool` | Reset preferences to defaults. |
| `save_preferences()` | `bool` | Save preferences to disk. |
| `set_setting(key, value)` | `bool` | Set a setting value. |
| `set_theme(theme_name)` | `bool` | Set the application theme. |
| `update_hotkey(action, hotkey)` | `bool` | Update a hotkey binding. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize preferences controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `get_autosave_interval`

```python
def get_autosave_interval() -> int
```

Get autosave interval in minutes.

Returns:
    int: Autosave interval in minutes

##### `get_hotkeys`

```python
def get_hotkeys() -> Dict[str, str]
```

Get all hotkey bindings.

Returns:
    dict: Action to hotkey mapping

##### `get_setting`

```python
def get_setting(key: str, default: Any = None) -> Any
```

Get a setting value.

Args:
    key: Setting key
    default: Default value if setting not found

Returns:
    Setting value or default

**Parameters:**

- `key: str` *(required)*
- `default: Any = None`

##### `get_settings_manager`

```python
def get_settings_manager() -> Any
```

Get the settings manager instance.

Returns:
    SettingsManager instance

##### `initialize`

```python
def initialize() -> None
```

Initialize controller and setup event subscriptions.

##### `is_autosave_enabled`

```python
def is_autosave_enabled() -> bool
```

Check if autosave is enabled.

Returns:
    bool: True if autosave is enabled

##### `reset_preferences`

```python
def reset_preferences() -> bool
```

Reset preferences to defaults.

Returns:
    bool: True if successful

##### `save_preferences`

```python
def save_preferences() -> bool
```

Save preferences to disk.

Returns:
    bool: True if successful

##### `set_setting`

```python
def set_setting(key: str, value: Any) -> bool
```

Set a setting value.

Args:
    key: Setting key
    value: Setting value

Returns:
    bool: True if successful

**Parameters:**

- `key: str` *(required)*
- `value: Any` *(required)*

##### `set_theme`

```python
def set_theme(theme_name: str) -> bool
```

Set the application theme.

Args:
    theme_name: Name of the theme

Returns:
    bool: True if successful

**Parameters:**

- `theme_name: str` *(required)*

##### `update_hotkey`

```python
def update_hotkey(action: str, hotkey: str) -> bool
```

Update a hotkey binding.

Args:
    action: Action name
    hotkey: Hotkey string (e.g., "Ctrl+S")

Returns:
    bool: True if successful

**Parameters:**

- `action: str` *(required)*
- `hotkey: str` *(required)*

---

## casare_rpa.presentation.canvas.controllers.project_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\project_controller.py`


Project controller for managing projects in the Canvas UI.

Coordinates between the ProjectManagerDialog and the application layer use cases.


### ProjectController

**Inherits from:** `BaseController`


Controller for project management operations.

Responsibilities:
- Show project manager dialog
- Create new projects
- Open existing projects
- Track current project state
- Coordinate with application layer use cases

Signals:
    project_opened: Emitted when a project is opened (Project)
    project_closed: Emitted when project is closed
    project_created: Emitted when new project created (Project)


**Attributes:**

- `project_closed: Signal`
- `project_created: Signal`
- `project_opened: Signal`
- `scenario_opened: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize project controller. |
| `cleanup()` | `None` | Clean up controller resources. |
| `close_project()` | `None` | Close the current project. |
| `current_project()` | `Optional['Project']` | Get current project. |
| `async get_recent_projects()` | `List['ProjectIndexEntry']` | Get list of recent projects. |
| `has_project()` | `bool` | Check if a project is currently open. |
| `initialize()` | `None` | Initialize controller and setup repository. |
| `show_project_manager()` | `None` | Show project manager dialog. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize project controller.

Args:
    main_window: Reference to main window

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

##### `close_project`

```python
def close_project() -> None
```

Close the current project.

##### `current_project`

```python
@property
def current_project() -> Optional['Project']
```

Get current project.

##### `get_recent_projects`

```python
async def get_recent_projects() -> List['ProjectIndexEntry']
```

Get list of recent projects.

Returns:
    List of recent project index entries

##### `has_project`

```python
@property
def has_project() -> bool
```

Check if a project is currently open.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller and setup repository.

##### `show_project_manager`

```python
def show_project_manager() -> None
```

Show project manager dialog.

---

## casare_rpa.presentation.canvas.controllers.robot_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\robot_controller.py`


Robot Controller for Canvas UI.

Manages robot selection, listing, and job submission for cloud execution.
Coordinates between the UI panel and application use cases.
Connects to remote orchestrator API for real robot fleet management.


### RobotController

**Inherits from:** `BaseController`


Controller for robot management and job submission.

Responsibilities:
- Fetch and display robot list from orchestrator API
- Handle robot selection for cloud execution
- Manage execution mode (local vs cloud)
- Submit jobs to selected robots
- Coordinate with RobotPickerPanel UI
- Real-time updates via WebSocket

Signals:
    robots_updated: Emitted when robot list is updated (List[Robot])
    robot_selected: Emitted when a robot is selected (robot_id: str)
    execution_mode_changed: Emitted when mode changes ('local' or 'cloud')
    job_submitted: Emitted when job is submitted (job_id: str)
    job_submission_failed: Emitted on submission error (error: str)
    connection_status_changed: Emitted when orchestrator connection changes (connected: bool)


**Attributes:**

- `connection_status_changed: Signal`
- `execution_mode_changed: Signal`
- `job_submission_failed: Signal`
- `job_submitted: Signal`
- `robot_selected: Signal`
- `robots_updated: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize Robot Controller. |
| `cleanup()` | `None` | Clean up controller resources. |
| `clear_selection()` | `None` | Clear current robot selection. |
| `async connect_to_orchestrator(url)` | `bool` | Connect to orchestrator API with automatic fallback. |
| `async disconnect_from_orchestrator()` | `None` | Disconnect from orchestrator. |
| `execution_mode()` | `str` | Get current execution mode ('local' or 'cloud'). |
| `async get_available_robots()` | `list` | Get list of robots that can accept jobs. |
| `async get_robot_logs(robot_id, limit, since)` | `List[dict]` | Get logs for a specific robot. |
| `async get_robot_metrics(robot_id)` | `dict` | Get detailed metrics for a specific robot. |
| `async get_robots_by_capability(capability)` | `list` | Get robots with a specific capability. |
| `get_selected_robot()` | - | Get the currently selected robot entity. |
| `async get_statistics()` | `dict` | Get robot fleet statistics from orchestrator. |
| `has_robot_selected()` | `bool` | Check if a robot is currently selected. |
| `initialize()` | `None` | Initialize controller resources and connections. |
| `is_cloud_mode()` | `bool` | Check if cloud execution mode is enabled. |
| `is_connected()` | `bool` | Check if connected to orchestrator. |
| `is_local_mode()` | `bool` | Check if local execution mode is enabled. |
| `orchestrator_url()` | `Optional[str]` | Get configured orchestrator URL. |
| `async pause_robot(robot_id)` | `bool` | Send pause command to a remote robot. |
| `async refresh_robots()` | `None` | Fetch robots from orchestrator API and update UI. |
| `async restart_all_robots()` | `Dict[str, bool]` | Send restart command to all robots. |
| `async restart_robot(robot_id)` | `bool` | Send restart command to a remote robot. |
| `async resume_robot(robot_id)` | `bool` | Send resume command to a paused robot. |
| `robots()` | `list` | Get current robot list. |
| `select_robot(robot_id)` | `None` | Select a robot by ID. |
| `selected_robot_id()` | `Optional[str]` | Get currently selected robot ID. |
| `set_execution_mode(mode)` | `None` | Set execution mode. |
| `set_panel(panel)` | `None` | Set the robot picker panel reference. |
| `async start_robot(robot_id)` | `bool` | Send start command to a remote robot. |
| `async stop_all_robots(force)` | `Dict[str, bool]` | Send stop command to all online robots. |
| `async stop_robot(robot_id, force)` | `bool` | Send stop command to a remote robot. |
| `async submit_job(workflow_data, variables, robot_id)` | `Optional[str]` | Submit job to selected robot via orchestrator API. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize Robot Controller.

Args:
    main_window: Reference to main window for accessing shared components

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

##### `clear_selection`

```python
def clear_selection() -> None
```

Clear current robot selection.

##### `connect_to_orchestrator`

```python
async def connect_to_orchestrator(url: Optional[str] = None) -> bool
```

Connect to orchestrator API with automatic fallback.

Tries URLs in order:
1. Provided URL (if any)
2. Configured URL (from config.yaml or env)
3. CASARE_API_URL env var (Cloudflare tunnel)
4. Localhost (http://localhost:8000) - fallback

Args:
    url: Optional orchestrator URL (uses fallback list if None)

Returns:
    True if connected successfully to any URL

**Parameters:**

- `url: Optional[str] = None`

##### `disconnect_from_orchestrator`

```python
async def disconnect_from_orchestrator() -> None
```

Disconnect from orchestrator.

##### `execution_mode`

```python
@property
def execution_mode() -> str
```

Get current execution mode ('local' or 'cloud').

##### `get_available_robots`

```python
async def get_available_robots() -> list
```

Get list of robots that can accept jobs.

Returns:
    List of available Robot entities

##### `get_robot_logs`

```python
async def get_robot_logs(robot_id: str, limit: int = 100, since: Optional[str] = None) -> List[dict]
```

Get logs for a specific robot.

Args:
    robot_id: Robot ID
    limit: Max number of log entries
    since: Optional ISO timestamp to get logs after

Returns:
    List of log entry dictionaries

**Parameters:**

- `robot_id: str` *(required)*
- `limit: int = 100`
- `since: Optional[str] = None`

##### `get_robot_metrics`

```python
async def get_robot_metrics(robot_id: str) -> dict
```

Get detailed metrics for a specific robot.

Args:
    robot_id: Robot ID

Returns:
    Dictionary with robot metrics (CPU, memory, jobs, etc.)

**Parameters:**

- `robot_id: str` *(required)*

##### `get_robots_by_capability`

```python
async def get_robots_by_capability(capability: str) -> list
```

Get robots with a specific capability.

Args:
    capability: Required capability string

Returns:
    List of robots with the capability

**Parameters:**

- `capability: str` *(required)*

##### `get_selected_robot`

```python
def get_selected_robot()
```

Get the currently selected robot entity.

Returns:
    Selected Robot entity or None

##### `get_statistics`

```python
async def get_statistics() -> dict
```

Get robot fleet statistics from orchestrator.

Returns:
    Dictionary with fleet statistics

##### `has_robot_selected`

```python
@property
def has_robot_selected() -> bool
```

Check if a robot is currently selected.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller resources and connections.

Called after all controllers are instantiated.
Sets up connections to robot picker panel signals.

##### `is_cloud_mode`

```python
@property
def is_cloud_mode() -> bool
```

Check if cloud execution mode is enabled.

##### `is_connected`

```python
@property
def is_connected() -> bool
```

Check if connected to orchestrator.

##### `is_local_mode`

```python
@property
def is_local_mode() -> bool
```

Check if local execution mode is enabled.

##### `orchestrator_url`

```python
@property
def orchestrator_url() -> Optional[str]
```

Get configured orchestrator URL.

##### `pause_robot`

```python
async def pause_robot(robot_id: str) -> bool
```

Send pause command to a remote robot.

Paused robots won't accept new jobs but complete current ones.

Args:
    robot_id: Robot ID to pause

Returns:
    True if command sent successfully

**Parameters:**

- `robot_id: str` *(required)*

##### `refresh_robots`

```python
async def refresh_robots() -> None
```

Fetch robots from orchestrator API and update UI.

Uses OrchestratorClient to fetch from remote API.
Falls back to local storage if not connected.

Emits robots_updated signal when complete.

##### `restart_all_robots`

```python
async def restart_all_robots() -> Dict[str, bool]
```

Send restart command to all robots.

Returns:
    Dictionary mapping robot_id to success status

##### `restart_robot`

```python
async def restart_robot(robot_id: str) -> bool
```

Send restart command to a remote robot.

Args:
    robot_id: Robot ID to restart

Returns:
    True if command sent successfully

**Parameters:**

- `robot_id: str` *(required)*

##### `resume_robot`

```python
async def resume_robot(robot_id: str) -> bool
```

Send resume command to a paused robot.

Args:
    robot_id: Robot ID to resume

Returns:
    True if command sent successfully

**Parameters:**

- `robot_id: str` *(required)*

##### `robots`

```python
@property
def robots() -> list
```

Get current robot list.

##### `select_robot`

```python
def select_robot(robot_id: str) -> None
```

Select a robot by ID.

Args:
    robot_id: Robot ID to select

**Parameters:**

- `robot_id: str` *(required)*

##### `selected_robot_id`

```python
@property
def selected_robot_id() -> Optional[str]
```

Get currently selected robot ID.

##### `set_execution_mode`

```python
def set_execution_mode(mode: str) -> None
```

Set execution mode.

Args:
    mode: 'local' or 'cloud'

**Parameters:**

- `mode: str` *(required)*

##### `set_panel`

```python
def set_panel(panel) -> None
```

Set the robot picker panel reference.

Called by DockCreator after panel is created.

Args:
    panel: RobotPickerPanel instance

**Parameters:**

- `panel` *(required)*

##### `start_robot`

```python
async def start_robot(robot_id: str) -> bool
```

Send start command to a remote robot.

Args:
    robot_id: Robot ID to start

Returns:
    True if command sent successfully

**Parameters:**

- `robot_id: str` *(required)*

##### `stop_all_robots`

```python
async def stop_all_robots(force: bool = False) -> Dict[str, bool]
```

Send stop command to all online robots.

Args:
    force: If True, force stop even if jobs are running

Returns:
    Dictionary mapping robot_id to success status

**Parameters:**

- `force: bool = False`

##### `stop_robot`

```python
async def stop_robot(robot_id: str, force: bool = False) -> bool
```

Send stop command to a remote robot.

Args:
    robot_id: Robot ID to stop
    force: If True, force stop even if job is running

Returns:
    True if command sent successfully

**Parameters:**

- `robot_id: str` *(required)*
- `force: bool = False`

##### `submit_job`

```python
async def submit_job(workflow_data: dict, variables: Optional[dict] = None, robot_id: Optional[str] = None) -> Optional[str]
```

Submit job to selected robot via orchestrator API.

Args:
    workflow_data: Workflow JSON data to execute
    variables: Optional initial variables
    robot_id: Optional specific robot ID (uses selected robot if None)

Returns:
    Job ID if submitted successfully, None on failure

**Parameters:**

- `workflow_data: dict` *(required)*
- `variables: Optional[dict] = None`
- `robot_id: Optional[str] = None`

---

## casare_rpa.presentation.canvas.controllers.scheduling_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\scheduling_controller.py`


Scheduling controller for workflow scheduling management.

Handles all scheduling-related operations:
- Schedule workflow dialogs
- Manage schedules dialog
- Run scheduled workflows
- Schedule state management


### SchedulingController

**Inherits from:** `BaseController`


Manages workflow scheduling operations.

Single Responsibility: Schedule creation, management, and execution.

Signals:
    schedule_created: Emitted when a schedule is created (WorkflowSchedule)
    schedule_deleted: Emitted when a schedule is deleted (str: schedule_id)
    schedule_updated: Emitted when a schedule is modified (WorkflowSchedule)
    schedule_run_requested: Emitted when user wants to run a schedule (WorkflowSchedule)
    schedules_changed: Emitted when schedules list is modified


**Attributes:**

- `schedule_created: Signal`
- `schedule_deleted: Signal`
- `schedule_run_requested: Signal`
- `schedule_updated: Signal`
- `schedules_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize scheduling controller. |
| `cleanup()` | `None` | Clean up controller resources. |
| `delete_schedule(schedule_id)` | `bool` | Delete a schedule by ID. |
| `get_schedule_count()` | `int` | Get the number of active schedules. |
| `get_schedules()` | `List[Any]` | Get all active schedules. |
| `initialize()` | `None` | Initialize controller resources and connections. |
| `manage_schedules()` | `None` | Open dialog to view and manage all schedules. |
| `run_scheduled_workflow(schedule)` | `None` | Run a scheduled workflow immediately. |
| `schedule_workflow()` | `None` | Open dialog to schedule the current workflow. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize scheduling controller.

Args:
    main_window: Reference to main window for accessing shared components

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

##### `delete_schedule`

```python
def delete_schedule(schedule_id: str) -> bool
```

Delete a schedule by ID.

Args:
    schedule_id: ID of the schedule to delete

Returns:
    True if deletion was successful

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_schedule_count`

```python
def get_schedule_count() -> int
```

Get the number of active schedules.

Returns:
    Number of schedules

##### `get_schedules`

```python
def get_schedules() -> List[Any]
```

Get all active schedules.

Returns:
    List of WorkflowSchedule objects

##### `initialize`

```python
def initialize() -> None
```

Initialize controller resources and connections.

##### `manage_schedules`

```python
def manage_schedules() -> None
```

Open dialog to view and manage all schedules.

##### `run_scheduled_workflow`

```python
def run_scheduled_workflow(schedule) -> None
```

Run a scheduled workflow immediately.

Args:
    schedule: The WorkflowSchedule to run

**Parameters:**

- `schedule` *(required)*

##### `schedule_workflow`

```python
def schedule_workflow() -> None
```

Open dialog to schedule the current workflow.

Checks if workflow is saved first, prompting user to save if needed.

---

## casare_rpa.presentation.canvas.controllers.selector_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\selector_controller.py`


Selector controller for element picker functionality.

Handles browser and desktop element selection:
- Desktop element picker
- Browser element picker (via SelectorIntegration)
- Selector management and updates


### SelectorController

**Inherits from:** `BaseController`


Manages element selector functionality.

Single Responsibility: Coordinate element picking and selector updates.

Signals:
    selector_picked: Emitted when selector is picked (str: selector_value, str: selector_type)
    picker_started: Emitted when picker mode starts
    picker_stopped: Emitted when picker mode stops


**Attributes:**

- `picker_started: Signal`
- `picker_stopped: Signal`
- `selector_picked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize selector controller. |
| `cleanup()` | `None` | Clean up resources. |
| `get_selector_integration()` | - | Get the selector integration instance. |
| `initialize()` | `None` | Initialize controller and setup event subscriptions. |
| `async initialize_for_page(page)` | `None` | Initialize selector functionality for a Playwright page. |
| `is_picker_active()` | `bool` | Check if picker mode is currently active. |
| `async start_picker(target_node, target_property)` | `None` | Start element picker mode. |
| `async start_recording()` | `None` | Start workflow recording mode. |
| `async stop_picker()` | `None` | Stop selector picker mode. |
| `async stop_recording()` | `None` | Stop workflow recording mode. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize selector controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `get_selector_integration`

```python
def get_selector_integration()
```

Get the selector integration instance.

Returns:
    SelectorIntegration instance

##### `initialize`

```python
def initialize() -> None
```

Initialize controller and setup event subscriptions.

##### `initialize_for_page`

```python
async def initialize_for_page(page: Any) -> None
```

Initialize selector functionality for a Playwright page.

Args:
    page: Playwright Page object

**Parameters:**

- `page: Any` *(required)*

##### `is_picker_active`

```python
def is_picker_active() -> bool
```

Check if picker mode is currently active.

Returns:
    bool: True if picker is active

##### `start_picker`

```python
async def start_picker(target_node: Optional[Any] = None, target_property: str = 'selector') -> None
```

Start element picker mode.

Args:
    target_node: Optional node to update with picked selector
    target_property: Property name to update (default: "selector")

**Parameters:**

- `target_node: Optional[Any] = None`
- `target_property: str = 'selector'`

##### `start_recording`

```python
async def start_recording() -> None
```

Start workflow recording mode.

##### `stop_picker`

```python
async def stop_picker() -> None
```

Stop selector picker mode.

##### `stop_recording`

```python
async def stop_recording() -> None
```

Stop workflow recording mode.

---

## casare_rpa.presentation.canvas.controllers.ui_state_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\ui_state_controller.py`


UI State Controller for Canvas.

Manages persistence and restoration of UI state including:
- Window geometry (size, position)
- Dock widget positions and visibility
- Panel states
- Recent files list
- Last opened directory
- UI preferences


### UIStateController

**Inherits from:** `BaseController`


Controller for managing UI state persistence.

Handles saving and restoring:
- Window geometry and state
- Dock widget positions and visibility
- Panel tab selections
- Recent files list
- Last opened directory
- Various UI preferences

Signals:
    state_saved: Emitted after state is successfully saved
    state_restored: Emitted after state is successfully restored
    state_reset: Emitted after state is reset to defaults
    recent_files_changed: Emitted when recent files list changes (list[dict])


**Attributes:**

- `recent_files_changed: Signal`
- `state_reset: Signal`
- `state_restored: Signal`
- `state_saved: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize UI state controller. |
| `add_recent_file(file_path)` | `None` | Add a file to the recent files list. |
| `cleanup()` | `None` | Clean up controller resources. |
| `clear_recent_files()` | `None` | Clear the entire recent files list. |
| `get_auto_save_enabled()` | `bool` | Check if auto-save is enabled. |
| `get_auto_validate_enabled()` | `bool` | Check if auto-validation is enabled. |
| `get_last_directory()` | `Optional[Path]` | Get the last opened directory. |
| `get_recent_files()` | `List[dict]` | Get the recent files list. |
| `get_settings()` | `Optional[QSettings]` | Get the QSettings instance for advanced usage. |
| `initialize()` | `None` | Initialize controller resources and connections. |
| `is_initialized()` | `bool` | Check if controller is initialized. |
| `remove_recent_file(file_path)` | `None` | Remove a file from the recent files list. |
| `reset_state()` | `None` | Clear all saved UI state and reset to defaults. |
| `restore_panel_states()` | `None` | Restore all panel visibility states from settings. |
| `restore_state()` | `None` | Restore all UI state from QSettings. |
| `restore_window_geometry()` | `None` | Restore window size and position from settings. |
| `save_panel_states()` | `None` | Save all panel visibility states to settings. |
| `save_state()` | `None` | Save all UI state to QSettings. |
| `save_window_geometry()` | `None` | Save window size and position to settings. |
| `schedule_auto_save()` | `None` | Schedule an automatic state save. |
| `set_auto_save_enabled(enabled)` | `None` | Enable or disable auto-save. |
| `set_auto_validate_enabled(enabled)` | `None` | Enable or disable auto-validation. |
| `set_last_directory(directory)` | `None` | Set the last opened directory. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize UI state controller.

Args:
    main_window: Reference to main window

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `add_recent_file`

```python
def add_recent_file(file_path: Path) -> None
```

Add a file to the recent files list.

Args:
    file_path: Path to the workflow file

**Parameters:**

- `file_path: Path` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

##### `clear_recent_files`

```python
def clear_recent_files() -> None
```

Clear the entire recent files list.

##### `get_auto_save_enabled`

```python
def get_auto_save_enabled() -> bool
```

Check if auto-save is enabled.

Returns:
    True if auto-save is enabled

##### `get_auto_validate_enabled`

```python
def get_auto_validate_enabled() -> bool
```

Check if auto-validation is enabled.

Returns:
    True if auto-validation is enabled

##### `get_last_directory`

```python
def get_last_directory() -> Optional[Path]
```

Get the last opened directory.

Returns:
    Path to last directory, or None if not set or invalid

##### `get_recent_files`

```python
def get_recent_files() -> List[dict]
```

Get the recent files list.

Returns:
    List of dicts with 'path', 'name', 'last_opened' keys

##### `get_settings`

```python
def get_settings() -> Optional[QSettings]
```

Get the QSettings instance for advanced usage.

Returns:
    QSettings instance or None

##### `initialize`

```python
def initialize() -> None
```

Initialize controller resources and connections.

##### `is_initialized`

```python
def is_initialized() -> bool
```

Check if controller is initialized.

##### `remove_recent_file`

```python
def remove_recent_file(file_path: Path) -> None
```

Remove a file from the recent files list.

Args:
    file_path: Path to remove

**Parameters:**

- `file_path: Path` *(required)*

##### `reset_state`

```python
def reset_state() -> None
```

Clear all saved UI state and reset to defaults.

This removes all persisted settings and allows the UI
to use its default layout and configuration.

##### `restore_panel_states`

```python
def restore_panel_states() -> None
```

Restore all panel visibility states from settings.

##### `restore_state`

```python
def restore_state() -> None
```

Restore all UI state from QSettings.

Restores window geometry, dock positions, panel visibility,
and other UI preferences from the previous session.

##### `restore_window_geometry`

```python
def restore_window_geometry() -> None
```

Restore window size and position from settings.

##### `save_panel_states`

```python
def save_panel_states() -> None
```

Save all panel visibility states to settings.

##### `save_state`

```python
def save_state() -> None
```

Save all UI state to QSettings.

Saves window geometry, dock positions, panel visibility,
and other UI preferences.

##### `save_window_geometry`

```python
def save_window_geometry() -> None
```

Save window size and position to settings.

##### `schedule_auto_save`

```python
def schedule_auto_save() -> None
```

Schedule an automatic state save.

Uses debouncing to avoid excessive saves when multiple
state changes occur in quick succession.

##### `set_auto_save_enabled`

```python
def set_auto_save_enabled(enabled: bool) -> None
```

Enable or disable auto-save.

Args:
    enabled: Whether to enable auto-save

**Parameters:**

- `enabled: bool` *(required)*

##### `set_auto_validate_enabled`

```python
def set_auto_validate_enabled(enabled: bool) -> None
```

Enable or disable auto-validation.

Args:
    enabled: Whether to enable auto-validation

**Parameters:**

- `enabled: bool` *(required)*

##### `set_last_directory`

```python
def set_last_directory(directory: Path) -> None
```

Set the last opened directory.

Args:
    directory: Path to directory

**Parameters:**

- `directory: Path` *(required)*

---

## casare_rpa.presentation.canvas.controllers.viewport_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\viewport_controller.py`


Viewport controller for canvas view management.

Handles all viewport-related operations:
- Frame creation and management
- Minimap creation and positioning
- Zoom display updates
- Viewport state management


### ViewportController

**Inherits from:** `BaseController`


Manages canvas viewport operations.

Single Responsibility: Viewport display and frame management.

Signals:
    frame_created: Emitted when a frame is created (NodeFrame)
    zoom_changed: Emitted when zoom level changes (float: zoom_percent)
    minimap_toggled: Emitted when minimap visibility changes (bool: visible)
    viewport_reset: Emitted when viewport is reset to default


**Attributes:**

- `frame_created: Signal`
- `minimap_toggled: Signal`
- `viewport_reset: Signal`
- `zoom_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize viewport controller. |
| `center_on_node(node_id)` | `None` | Center viewport on a specific node. |
| `cleanup()` | `None` | Clean up controller resources. |
| `create_frame()` | `None` | Create a frame around selected nodes or an empty frame. |
| `create_minimap(node_graph)` | `None` | Create minimap overlay widget for the node graph. |
| `fit_to_view()` | `None` | Fit all nodes in the current view. |
| `get_current_zoom()` | `float` | Get current zoom level. |
| `hide_minimap()` | `None` | Hide the minimap overlay. |
| `initialize()` | `None` | Initialize controller resources and connections. |
| `is_minimap_visible()` | `bool` | Check if minimap is currently visible. |
| `position_minimap()` | `None` | Position minimap at bottom-left of central widget. |
| `reset_viewport()` | `None` | Reset viewport to default state (100% zoom, centered). |
| `show_minimap()` | `None` | Show the minimap overlay. |
| `toggle_minimap(checked)` | `None` | Toggle minimap visibility. |
| `update_zoom_display(zoom_percent)` | `None` | Update zoom level display and emit signal. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize viewport controller.

Args:
    main_window: Reference to main window for accessing shared components

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `center_on_node`

```python
def center_on_node(node_id: str) -> None
```

Center viewport on a specific node.

Args:
    node_id: ID of the node to center on

**Parameters:**

- `node_id: str` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up controller resources.

##### `create_frame`

```python
def create_frame() -> None
```

Create a frame around selected nodes or an empty frame.

If nodes are selected, creates a frame containing them.
Otherwise, creates an empty frame at the canvas center.

##### `create_minimap`

```python
def create_minimap(node_graph) -> None
```

Create minimap overlay widget for the node graph.

Args:
    node_graph: The NodeGraph instance to create minimap for

**Parameters:**

- `node_graph` *(required)*

##### `fit_to_view`

```python
def fit_to_view() -> None
```

Fit all nodes in the current view.

##### `get_current_zoom`

```python
def get_current_zoom() -> float
```

Get current zoom level.

Returns:
    Current zoom level as percentage

##### `hide_minimap`

```python
def hide_minimap() -> None
```

Hide the minimap overlay.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller resources and connections.

##### `is_minimap_visible`

```python
def is_minimap_visible() -> bool
```

Check if minimap is currently visible.

Returns:
    True if minimap is visible

##### `position_minimap`

```python
def position_minimap() -> None
```

Position minimap at bottom-left of central widget.

##### `reset_viewport`

```python
def reset_viewport() -> None
```

Reset viewport to default state (100% zoom, centered).

##### `show_minimap`

```python
def show_minimap() -> None
```

Show the minimap overlay.

##### `toggle_minimap`

```python
def toggle_minimap(checked: bool) -> None
```

Toggle minimap visibility.

Args:
    checked: True to show, False to hide

**Parameters:**

- `checked: bool` *(required)*

##### `update_zoom_display`

```python
def update_zoom_display(zoom_percent: float) -> None
```

Update zoom level display and emit signal.

Args:
    zoom_percent: Current zoom level as percentage

**Parameters:**

- `zoom_percent: float` *(required)*

---

## casare_rpa.presentation.canvas.controllers.workflow_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\workflow_controller.py`


Workflow lifecycle controller.

Handles all workflow-related operations:
- New/Open/Save/Save As/Close
- Import/Export
- Validation
- File management


### WorkflowController

**Inherits from:** `BaseController`


Manages workflow lifecycle operations.

Single Responsibility: Workflow file management and validation.

Signals:
    workflow_created: Emitted when new workflow is created
    workflow_loaded: Emitted when workflow is opened (str: file_path)
    workflow_saved: Emitted when workflow is saved (str: file_path)
    workflow_imported: Emitted when workflow is imported (str: file_path)
    workflow_exported: Emitted when nodes are exported (str: file_path)
    workflow_closed: Emitted when workflow is closed
    current_file_changed: Emitted when current file changes (Optional[Path])
    modified_changed: Emitted when modified state changes (bool)


**Attributes:**

- `current_file_changed: Signal`
- `modified_changed: Signal`
- `workflow_closed: Signal`
- `workflow_created: Signal`
- `workflow_exported: Signal`
- `workflow_imported: Signal`
- `workflow_imported_json: Signal`
- `workflow_loaded: Signal`
- `workflow_saved: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize workflow controller. |
| `check_unsaved_changes()` | `bool` | Check for unsaved changes and prompt user. |
| `check_validation_before_run()` | `bool` | Check validation before running workflow. |
| `cleanup()` | `None` | Clean up resources. |
| `close_workflow()` | `bool` | Close the current workflow. |
| `current_file()` | `Optional[Path]` | Get the current workflow file path. |
| `export_selected_nodes()` | `None` | Export selected nodes to a workflow file. |
| `import_workflow()` | `None` | Import nodes from another workflow. |
| `initialize()` | `None` | Initialize controller. |
| `is_modified()` | `bool` | Check if workflow has unsaved changes. |
| `new_from_template()` | `None` | Create a new workflow from a template. |
| `new_workflow()` | `None` | Create a new empty workflow. |
| `open_workflow()` | `None` | Open an existing workflow file. |
| `paste_workflow()` | `None` | Paste workflow JSON from clipboard and import nodes. |
| `async run_local()` | `None` | Execute workflow locally in Canvas (current behavior). |
| `async run_on_robot()` | `None` | Submit workflow to LAN robot via Orchestrator API. |
| `save_workflow()` | `None` | Save the current workflow. |
| `save_workflow_as()` | `None` | Save the workflow with a new name. |
| `set_current_file(file_path)` | `None` | Set the current workflow file path. |
| `set_modified(modified)` | `None` | Set the modified state of the workflow. |
| `setup_drag_drop_import()` | `None` | Setup drag-and-drop support for importing workflow JSON file... |
| `async submit_for_internet_robots()` | `None` | Submit workflow for internet robots (client PCs). |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow')
```

Initialize workflow controller.

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `check_unsaved_changes`

```python
def check_unsaved_changes() -> bool
```

Check for unsaved changes and prompt user.

Returns:
    True if safe to proceed, False if cancelled

##### `check_validation_before_run`

```python
def check_validation_before_run() -> bool
```

Check validation before running workflow.

Returns:
    True if workflow is valid or user wants to run anyway,
    False if validation errors exist and user cancels

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `close_workflow`

```python
def close_workflow() -> bool
```

Close the current workflow.

Returns:
    True if workflow was closed, False if cancelled

##### `current_file`

```python
@property
def current_file() -> Optional[Path]
```

Get the current workflow file path.

##### `export_selected_nodes`

```python
def export_selected_nodes() -> None
```

Export selected nodes to a workflow file.

##### `import_workflow`

```python
def import_workflow() -> None
```

Import nodes from another workflow.

##### `initialize`

```python
def initialize() -> None
```

Initialize controller.

##### `is_modified`

```python
@property
def is_modified() -> bool
```

Check if workflow has unsaved changes.

##### `new_from_template`

```python
def new_from_template() -> None
```

Create a new workflow from a template.

##### `new_workflow`

```python
def new_workflow() -> None
```

Create a new empty workflow.

##### `open_workflow`

```python
def open_workflow() -> None
```

Open an existing workflow file.

##### `paste_workflow`

```python
def paste_workflow() -> None
```

Paste workflow JSON from clipboard and import nodes.

Validates the clipboard content as valid workflow JSON and
emits workflow_imported_json signal for the app to handle.

##### `run_local`

```python
async def run_local() -> None
```

Execute workflow locally in Canvas (current behavior).

This is the existing local execution - no changes needed.
The execution controller handles this via execute_workflow().

##### `run_on_robot`

```python
async def run_on_robot() -> None
```

Submit workflow to LAN robot via Orchestrator API.

Flow:
1. Serialize current workflow
2. Submit via OrchestratorClient with execution_mode=lan
3. Orchestrator queues job for LAN robots
4. Show confirmation with job_id

##### `save_workflow`

```python
def save_workflow() -> None
```

Save the current workflow.

##### `save_workflow_as`

```python
def save_workflow_as() -> None
```

Save the workflow with a new name.

##### `set_current_file`

```python
def set_current_file(file_path: Optional[Path]) -> None
```

Set the current workflow file path.

Args:
    file_path: Path to workflow file, or None for new workflow

**Parameters:**

- `file_path: Optional[Path]` *(required)*

##### `set_modified`

```python
def set_modified(modified: bool) -> None
```

Set the modified state of the workflow.

Args:
    modified: True if workflow has unsaved changes

**Parameters:**

- `modified: bool` *(required)*

##### `setup_drag_drop_import`

```python
def setup_drag_drop_import() -> None
```

Setup drag-and-drop support for importing workflow JSON files.

Allows users to drag .json workflow files directly onto the canvas
to import nodes at the drop position.

Extracted from: canvas/components/dragdrop_component.py

##### `submit_for_internet_robots`

```python
async def submit_for_internet_robots() -> None
```

Submit workflow for internet robots (client PCs).

Flow:
1. Serialize current workflow
2. Submit via OrchestratorClient with execution_mode=internet
3. Orchestrator queues job for internet robots
4. Show confirmation with workflow_id

---

## casare_rpa.presentation.canvas.debugger.debug_controller

**File:** `src\casare_rpa\presentation\canvas\debugger\debug_controller.py`


Debug Controller for interactive workflow debugging.

Provides comprehensive debugging capabilities:
- Breakpoint management (regular, conditional, hit-count)
- Step-through execution (step over, step into, step out)
- Variable inspection at each step
- Expression evaluation
- Call stack visualization
- Execution state snapshot/restore
- Watch expressions


### Breakpoint

**Decorators:** `@dataclass`


Represents a breakpoint on a workflow node.

Attributes:
    node_id: ID of the node where breakpoint is set
    enabled: Whether breakpoint is active
    breakpoint_type: Type of breakpoint
    condition: Python expression for conditional breakpoints
    hit_count_target: Number of hits before triggering (for hit-count breakpoints)
    log_message: Message to log (for log points, supports {variable} syntax)
    hit_count: Current number of times this breakpoint has been hit
    created_at: Timestamp when breakpoint was created


**Attributes:**

- `breakpoint_type: BreakpointType`
- `condition: Optional[str]`
- `created_at: datetime`
- `enabled: bool`
- `hit_count: int`
- `hit_count_target: int`
- `log_message: Optional[str]`
- `node_id: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `reset_hit_count()` | `None` | Reset hit count to zero. |
| `should_break(context)` | `bool` | Determine if execution should break at this breakpoint. |

#### Method Details

##### `reset_hit_count`

```python
def reset_hit_count() -> None
```

Reset hit count to zero.

##### `should_break`

```python
def should_break(context: 'ExecutionContext') -> bool
```

Determine if execution should break at this breakpoint.

Args:
    context: Current execution context for evaluating conditions

Returns:
    True if execution should pause at this breakpoint

**Parameters:**

- `context: 'ExecutionContext'` *(required)*

### BreakpointType

**Inherits from:** `Enum`


Type of breakpoint.


**Attributes:**

- `CONDITIONAL: auto`
- `HIT_COUNT: auto`
- `LOG_POINT: auto`
- `REGULAR: auto`

### CallStackFrame

**Decorators:** `@dataclass`


Represents a frame in the debug call stack.

Attributes:
    node_id: ID of the node in this frame
    node_name: Display name of the node
    node_type: Type of the node (e.g., "IfNode", "LoopNode")
    local_variables: Variables local to this frame
    entry_time: When execution entered this frame


**Attributes:**

- `entry_time: datetime`
- `local_variables: Dict[str, Any]`
- `node_id: str`
- `node_name: str`
- `node_type: str`

### DebugController

**Inherits from:** `QObject`


Controller for interactive workflow debugging.

Manages breakpoints, stepping, variable inspection, and debug state.

Signals:
    debug_mode_changed: Emitted when debug mode is toggled (bool: enabled)
    breakpoint_added: Emitted when breakpoint is added (str: node_id)
    breakpoint_removed: Emitted when breakpoint is removed (str: node_id)
    breakpoint_hit: Emitted when execution hits a breakpoint (str: node_id)
    step_completed: Emitted when a step operation completes (str: node_id)
    variables_updated: Emitted when variables change (dict: variables)
    call_stack_updated: Emitted when call stack changes (list: frames)
    watch_updated: Emitted when watch expressions are evaluated (list: watches)
    snapshot_created: Emitted when snapshot is created (str: snapshot_id)
    execution_paused: Emitted when execution is paused for debugging
    execution_resumed: Emitted when execution resumes from debug pause


**Attributes:**

- `breakpoint_added: Signal`
- `breakpoint_hit: Signal`
- `breakpoint_removed: Signal`
- `call_stack_updated: Signal`
- `debug_mode_changed: Signal`
- `execution_paused: Signal`
- `execution_resumed: Signal`
- `snapshot_created: Signal`
- `step_completed: Signal`
- `variables_updated: Signal`
- `watch_updated: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | - | Initialize debug controller. |
| `add_breakpoint(node_id, breakpoint_type, condition, ...)` | `Breakpoint` | Add a breakpoint to a node. |
| `add_watch(expression)` | `WatchExpression` | Add a watch expression. |
| `async check_breakpoint(node_id, context)` | `bool` | Check if execution should pause at a breakpoint. |
| `cleanup()` | `None` | Clean up debug controller resources. |
| `clear_all_breakpoints()` | `int` | Remove all breakpoints. |
| `clear_repl()` | `None` | Clear REPL state and history. |
| `continue_execution()` | `None` | Continue execution until next breakpoint or end. |
| `create_snapshot(description)` | `ExecutionSnapshot` | Create a snapshot of current execution state. |
| `delete_snapshot(snapshot_id)` | `bool` | Delete a snapshot. |
| `enable_debug_mode(enabled)` | `None` | Enable or disable debug mode. |
| `evaluate_expression(expression)` | `tuple[Any, Optional[str]]` | Evaluate an expression in the current debug context. |
| `get_all_breakpoints()` | `List[Breakpoint]` | Get all breakpoints. |
| `get_breakpoint(node_id)` | `Optional[Breakpoint]` | Get breakpoint for a node. |
| `get_call_stack()` | `List[CallStackFrame]` | Get current call stack. |
| `get_repl_history()` | `List[str]` | Get REPL command history. |
| `get_snapshots()` | `List[ExecutionSnapshot]` | Get all snapshots. |
| `get_variable_value(name)` | `tuple[Any, bool]` | Get the value of a variable in the current context. |
| `get_watches()` | `List[WatchExpression]` | Get all watch expressions. |
| `has_breakpoint(node_id)` | `bool` | Check if a node has a breakpoint. |
| `is_debug_mode()` | `bool` | Check if debug mode is enabled. |
| `pop_call_stack()` | `Optional[CallStackFrame]` | Pop a frame from the call stack. |
| `push_call_stack(node_id, node_name, node_type)` | `None` | Push a new frame onto the call stack. |
| `remove_breakpoint(node_id)` | `bool` | Remove a breakpoint from a node. |
| `remove_watch(expression)` | `bool` | Remove a watch expression. |
| `restore_snapshot(snapshot_id)` | `bool` | Restore execution state from a snapshot. |
| `set_variable_value(name, value)` | `bool` | Set a variable value in the current context. |
| `async should_pause_for_step(node_id, context)` | `bool` | Check if execution should pause based on step mode. |
| `step_into()` | `None` | Execute current node and pause at next node (including neste... |
| `step_out()` | `None` | Continue execution until returning from current scope. |
| `step_over()` | `None` | Execute current node and pause at next node (same level). |
| `toggle_breakpoint(node_id)` | `bool` | Toggle breakpoint on a node. |
| `toggle_breakpoint_enabled(node_id)` | `bool` | Toggle enabled state of an existing breakpoint. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: Optional['MainWindow'] = None)
```

Initialize debug controller.

Args:
    main_window: Optional reference to main window for UI integration

**Parameters:**

- `main_window: Optional['MainWindow'] = None`

##### `add_breakpoint`

```python
def add_breakpoint(node_id: str, breakpoint_type: BreakpointType = BreakpointType.REGULAR, condition: Optional[str] = None, hit_count_target: int = 1, log_message: Optional[str] = None) -> Breakpoint
```

Add a breakpoint to a node.

Args:
    node_id: ID of the node to set breakpoint on
    breakpoint_type: Type of breakpoint
    condition: Python expression for conditional breakpoints
    hit_count_target: Hit count threshold for hit-count breakpoints
    log_message: Message for log points

Returns:
    The created Breakpoint object

**Parameters:**

- `node_id: str` *(required)*
- `breakpoint_type: BreakpointType = BreakpointType.REGULAR`
- `condition: Optional[str] = None`
- `hit_count_target: int = 1`
- `log_message: Optional[str] = None`

##### `add_watch`

```python
def add_watch(expression: str) -> WatchExpression
```

Add a watch expression.

Args:
    expression: Python expression to watch

Returns:
    The created WatchExpression

**Parameters:**

- `expression: str` *(required)*

##### `check_breakpoint`

```python
async def check_breakpoint(node_id: str, context: 'ExecutionContext') -> bool
```

Check if execution should pause at a breakpoint.

Called by DebugExecutor before each node execution.

Args:
    node_id: ID of the node about to execute
    context: Current execution context

Returns:
    True if execution was paused (breakpoint hit)

**Parameters:**

- `node_id: str` *(required)*
- `context: 'ExecutionContext'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up debug controller resources.

##### `clear_all_breakpoints`

```python
def clear_all_breakpoints() -> int
```

Remove all breakpoints.

Returns:
    Number of breakpoints removed

##### `clear_repl`

```python
def clear_repl() -> None
```

Clear REPL state and history.

##### `continue_execution`

```python
def continue_execution() -> None
```

Continue execution until next breakpoint or end.

##### `create_snapshot`

```python
def create_snapshot(description: str = '') -> ExecutionSnapshot
```

Create a snapshot of current execution state.

Args:
    description: Optional description for the snapshot

Returns:
    The created snapshot

**Parameters:**

- `description: str = ''`

##### `delete_snapshot`

```python
def delete_snapshot(snapshot_id: str) -> bool
```

Delete a snapshot.

Args:
    snapshot_id: ID of snapshot to delete

Returns:
    True if snapshot was deleted

**Parameters:**

- `snapshot_id: str` *(required)*

##### `enable_debug_mode`

```python
def enable_debug_mode(enabled: bool = True) -> None
```

Enable or disable debug mode.

Args:
    enabled: Whether to enable debug mode

**Parameters:**

- `enabled: bool = True`

##### `evaluate_expression`

```python
def evaluate_expression(expression: str) -> tuple[Any, Optional[str]]
```

Evaluate an expression in the current debug context.

Args:
    expression: Python expression to evaluate

Returns:
    Tuple of (result, error_message). Error is None on success.

**Parameters:**

- `expression: str` *(required)*

##### `get_all_breakpoints`

```python
def get_all_breakpoints() -> List[Breakpoint]
```

Get all breakpoints.

Returns:
    List of all breakpoints

##### `get_breakpoint`

```python
def get_breakpoint(node_id: str) -> Optional[Breakpoint]
```

Get breakpoint for a node.

Args:
    node_id: ID of the node

Returns:
    Breakpoint object or None if not found

**Parameters:**

- `node_id: str` *(required)*

##### `get_call_stack`

```python
def get_call_stack() -> List[CallStackFrame]
```

Get current call stack.

Returns:
    List of call stack frames (most recent last)

##### `get_repl_history`

```python
def get_repl_history() -> List[str]
```

Get REPL command history.

Returns:
    List of executed expressions

##### `get_snapshots`

```python
def get_snapshots() -> List[ExecutionSnapshot]
```

Get all snapshots.

Returns:
    List of snapshots

##### `get_variable_value`

```python
def get_variable_value(name: str) -> tuple[Any, bool]
```

Get the value of a variable in the current context.

Args:
    name: Variable name

Returns:
    Tuple of (value, found). Found is False if variable doesn't exist.

**Parameters:**

- `name: str` *(required)*

##### `get_watches`

```python
def get_watches() -> List[WatchExpression]
```

Get all watch expressions.

Returns:
    List of watch expressions

##### `has_breakpoint`

```python
def has_breakpoint(node_id: str) -> bool
```

Check if a node has a breakpoint.

Args:
    node_id: ID of the node

Returns:
    True if node has a breakpoint

**Parameters:**

- `node_id: str` *(required)*

##### `is_debug_mode`

```python
@property
def is_debug_mode() -> bool
```

Check if debug mode is enabled.

##### `pop_call_stack`

```python
def pop_call_stack() -> Optional[CallStackFrame]
```

Pop a frame from the call stack.

Returns:
    The popped frame, or None if stack was empty

##### `push_call_stack`

```python
def push_call_stack(node_id: str, node_name: str, node_type: str) -> None
```

Push a new frame onto the call stack.

Args:
    node_id: ID of the node
    node_name: Display name of the node
    node_type: Type of the node

**Parameters:**

- `node_id: str` *(required)*
- `node_name: str` *(required)*
- `node_type: str` *(required)*

##### `remove_breakpoint`

```python
def remove_breakpoint(node_id: str) -> bool
```

Remove a breakpoint from a node.

Args:
    node_id: ID of the node to remove breakpoint from

Returns:
    True if breakpoint was removed, False if not found

**Parameters:**

- `node_id: str` *(required)*

##### `remove_watch`

```python
def remove_watch(expression: str) -> bool
```

Remove a watch expression.

Args:
    expression: Expression to remove

Returns:
    True if watch was removed

**Parameters:**

- `expression: str` *(required)*

##### `restore_snapshot`

```python
def restore_snapshot(snapshot_id: str) -> bool
```

Restore execution state from a snapshot.

Note: This restores variables only. Execution path cannot be rewound.

Args:
    snapshot_id: ID of snapshot to restore

Returns:
    True if snapshot was restored

**Parameters:**

- `snapshot_id: str` *(required)*

##### `set_variable_value`

```python
def set_variable_value(name: str, value: Any) -> bool
```

Set a variable value in the current context.

Args:
    name: Variable name
    value: Value to set

Returns:
    True if successful

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*

##### `should_pause_for_step`

```python
async def should_pause_for_step(node_id: str, context: 'ExecutionContext') -> bool
```

Check if execution should pause based on step mode.

Called by DebugExecutor after each node execution.

Args:
    node_id: ID of the node just executed
    context: Current execution context

Returns:
    True if execution should pause

**Parameters:**

- `node_id: str` *(required)*
- `context: 'ExecutionContext'` *(required)*

##### `step_into`

```python
def step_into() -> None
```

Execute current node and pause at next node (including nested).

Steps into sub-workflows or nested control structures.

##### `step_out`

```python
def step_out() -> None
```

Continue execution until returning from current scope.

Continues until exiting the current control structure.

##### `step_over`

```python
def step_over() -> None
```

Execute current node and pause at next node (same level).

Does not step into sub-workflows or nested structures.

##### `toggle_breakpoint`

```python
def toggle_breakpoint(node_id: str) -> bool
```

Toggle breakpoint on a node.

Args:
    node_id: ID of the node to toggle breakpoint on

Returns:
    True if breakpoint is now enabled, False if disabled/removed

**Parameters:**

- `node_id: str` *(required)*

##### `toggle_breakpoint_enabled`

```python
def toggle_breakpoint_enabled(node_id: str) -> bool
```

Toggle enabled state of an existing breakpoint.

Args:
    node_id: ID of the node

Returns:
    New enabled state, or False if breakpoint not found

**Parameters:**

- `node_id: str` *(required)*

### ExecutionSnapshot

**Decorators:** `@dataclass`


Snapshot of execution state for restore capability.

Attributes:
    snapshot_id: Unique identifier for this snapshot
    node_id: Node ID where snapshot was taken
    variables: Copy of all variables at snapshot time
    execution_path: Nodes executed up to this point
    timestamp: When snapshot was created
    description: Optional user description


**Attributes:**

- `description: str`
- `execution_path: List[str]`
- `node_id: str`
- `snapshot_id: str`
- `timestamp: datetime`
- `variables: Dict[str, Any]`

### WatchExpression

**Decorators:** `@dataclass`


Watch expression for monitoring values during debugging.

Attributes:
    expression: Python expression to evaluate
    last_value: Last evaluated value
    last_error: Error message if evaluation failed
    enabled: Whether watch is active


**Attributes:**

- `enabled: bool`
- `expression: str`
- `last_error: Optional[str]`
- `last_value: Any`

---

## casare_rpa.presentation.canvas.desktop.desktop_recording_panel

**File:** `src\casare_rpa\presentation\canvas\desktop\desktop_recording_panel.py`


Desktop Recording Panel for CasareRPA

Provides UI for recording desktop actions and generating workflows.


### ActionListItem

**Inherits from:** `QListWidgetItem`


Custom list item for displaying recorded actions.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(action, index)` | - |  |

#### Method Details

##### `__init__`

```python
def __init__(action: DesktopRecordedAction, index: int)
```

**Parameters:**

- `action: DesktopRecordedAction` *(required)*
- `index: int` *(required)*

### DesktopRecordingPanel

**Inherits from:** `QDockWidget`


Dockable panel for desktop action recording.

Features:
- Start/Stop/Pause recording
- Live action list display
- Generate workflow from recording
- Clear and delete actions


**Attributes:**

- `workflow_generated: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - |  |
| `keyPressEvent(event)` | - | Handle key press events for global hotkeys. |

#### Method Details

##### `__init__`

```python
def __init__(parent = None)
```

**Parameters:**

- `parent = None`

##### `keyPressEvent`

```python
def keyPressEvent(event)
```

Handle key press events for global hotkeys.

**Parameters:**

- `event` *(required)*

---

## casare_rpa.presentation.canvas.desktop.rich_comment_node

**File:** `src\casare_rpa\presentation\canvas\desktop\rich_comment_node.py`


Rich Comment Node

Enhanced comment node with rich text formatting, colors, and styling options.


### Functions

#### `create_markdown_comment`

```python
def create_markdown_comment(text: str) -> str
```

Convert markdown-style text to HTML for rich comments.

Supported syntax:
- **bold** or __bold__
- *italic* or _italic_
- # Heading
- - List item
- [link](url)

Args:
    text: Markdown-style text

Returns:
    HTML string

#### `get_comment_shortcuts`

```python
def get_comment_shortcuts() -> str
```

Get help text for comment formatting shortcuts.

Returns:
    Help text string


### VisualHeaderCommentNode

**Inherits from:** `VisualNode`


Large header comment for section titles.

Features:
- Large, bold text
- Centered alignment
- Underline
- Color themes


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize header comment node. |
| `setup_ports()` | `None` | Setup ports for header. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize header comment node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for header.

### VisualRichCommentNode

**Inherits from:** `VisualNode`


Enhanced visual comment node with rich text formatting.

Features:
- Rich text (bold, italic, underline)
- Text colors
- Font sizes
- Lists and formatting
- Markdown-style shortcuts


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize rich comment node. |
| `setup_ports()` | `None` | Setup ports for comment node. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize rich comment node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for comment node.

### VisualStickyNoteNode

**Inherits from:** `VisualNode`


Sticky note style comment node.

Features:
- Colored sticky note appearance
- Predefined color themes
- Large text area
- No execution ports


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`
- `THEMES: dict`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize sticky note node. |
| `setup_ports()` | `None` | Setup ports for sticky note. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize sticky note node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for sticky note.

---

## casare_rpa.presentation.canvas.events.domain_bridge

**File:** `src\casare_rpa\presentation\canvas\events\domain_bridge.py`


Domain-to-Presentation Event Bridge.

Bridges events from the domain EventBus to the presentation EventBus,
allowing Canvas UI components to receive execution events from the domain layer.

This maintains clean architecture separation:
- Domain layer publishes simple execution events
- Presentation layer receives and handles them via this bridge
- No direct dependency from domain to presentation

Usage:
    from casare_rpa.presentation.canvas.events.domain_bridge import DomainEventBridge

    # Create and start bridge (typically in MainWindow initialization)
    bridge = DomainEventBridge()
    bridge.start()

    # Stop when closing application
    bridge.stop()


### Functions

#### `start_domain_bridge`

```python
def start_domain_bridge() -> DomainEventBridge
```

Start the domain event bridge.

Convenience function to create and start the bridge in one call.

Returns:
    Running DomainEventBridge instance


### DomainEventBridge


Bridges domain events to presentation events.

Subscribes to all relevant domain events and re-publishes them as
presentation events with appropriate type mapping and data transformation.

This allows:
- Canvas UI to react to execution events
- Debug panels to show real-time execution status
- Logging panel to display execution logs

Thread Safety:
    This bridge runs on the main thread and forwards events synchronously.
    Domain events published from async code are still delivered correctly
    because the domain EventBus handlers are called synchronously.

Example:
    # In MainWindow.__init__()
    self._domain_bridge = DomainEventBridge()
    self._domain_bridge.start()

    # In MainWindow.closeEvent()
    self._domain_bridge.stop()


**Attributes:**

- `_instance: Optional['DomainEventBridge']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(domain_bus, presentation_bus)` | `None` | Initialize domain event bridge. |
| `__new__()` | `'DomainEventBridge'` | Singleton pattern - only one bridge needed. |
| `__repr__()` | `str` | String representation. |
| `is_running()` | `bool` | Check if bridge is currently running. |
| `reset_instance()` | `None` | Reset singleton instance (for testing). |
| `start()` | `None` | Start bridging domain events to presentation. |
| `stop()` | `None` | Stop bridging domain events. |

#### Method Details

##### `__init__`

```python
def __init__(domain_bus: Optional[DomainEventBus] = None, presentation_bus: Optional[PresentationEventBus] = None) -> None
```

Initialize domain event bridge.

Args:
    domain_bus: Domain EventBus instance (defaults to global)
    presentation_bus: Presentation EventBus instance (defaults to singleton)

**Parameters:**

- `domain_bus: Optional[DomainEventBus] = None`
- `presentation_bus: Optional[PresentationEventBus] = None`

##### `__new__`

```python
def __new__() -> 'DomainEventBridge'
```

Singleton pattern - only one bridge needed.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if bridge is currently running.

##### `reset_instance`

```python
@classmethod
def reset_instance() -> None
```

Reset singleton instance (for testing).

##### `start`

```python
def start() -> None
```

Start bridging domain events to presentation.

Subscribes to all mapped domain event types.

##### `stop`

```python
def stop() -> None
```

Stop bridging domain events.

Unsubscribes from all domain event types.

---

## casare_rpa.presentation.canvas.events.event

**File:** `src\casare_rpa\presentation\canvas\events\event.py`


Event data structures for the Canvas event system.

This module defines the Event class and related data structures used
for event-driven communication between components.

Events are immutable, timestamped objects that carry information about
what happened, where it happened, and any associated data.

Usage:
    from casare_rpa.presentation.canvas.events import Event, EventType, EventPriority

    # Create an event
    event = Event(
        type=EventType.WORKFLOW_NEW,
        source="WorkflowController",
        data={"workflow_id": "123", "name": "My Workflow"}
    )

    # Access event properties
    print(event.type)       # EventType.WORKFLOW_NEW
    print(event.source)     # "WorkflowController"
    print(event.timestamp)  # 1234567890.123
    print(event.data)       # {"workflow_id": "123", "name": "My Workflow"}


### Event

**Decorators:** `@dataclass`


Immutable event object.

Events represent something that has happened in the system that
other components may want to react to.

Attributes:
    type: The type of event (from EventType enum)
    source: Component/controller that emitted the event
    data: Optional payload data associated with the event
    timestamp: Unix timestamp when event was created
    priority: Priority level for event processing
    event_id: Unique identifier for this event instance
    correlation_id: ID linking related events together

Examples:
    # Simple event
    event = Event(
        type=EventType.NODE_ADDED,
        source="NodeController"
    )

    # Event with data
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )

    # High priority event
    event = Event(
        type=EventType.ERROR_OCCURRED,
        source="SystemMonitor",
        data={"error": "Out of memory"},
        priority=EventPriority.CRITICAL
    )

    # Correlated events
    event1 = Event(
        type=EventType.EXECUTION_STARTED,
        source="ExecutionController",
        correlation_id="exec-123"
    )
    event2 = Event(
        type=EventType.EXECUTION_COMPLETED,
        source="ExecutionController",
        correlation_id="exec-123"
    )


**Attributes:**

- `correlation_id: Optional[str]`
- `data: Optional[dict[str, Any]]`
- `event_id: str`
- `priority: EventPriority`
- `source: str`
- `timestamp: float`
- `type: EventType`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate event after initialization. |
| `__repr__()` | `str` | Detailed representation of event. |
| `__str__()` | `str` | String representation of event. |
| `category()` | `EventCategory` | Get the category of this event. |
| `datetime()` | `datetime` | Get timestamp as datetime object. |
| `get(key, default)` | `Any` | Get value from event data. |
| `has_data(key)` | `bool` | Check if event has specific data key. |
| `is_high_priority()` | `bool` | Check if this is a high or critical priority event. |
| `to_dict()` | `dict[str, Any]` | Convert event to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate event after initialization.

##### `__repr__`

```python
def __repr__() -> str
```

Detailed representation of event.

##### `__str__`

```python
def __str__() -> str
```

String representation of event.

##### `category`

```python
@property
def category() -> EventCategory
```

Get the category of this event.

Returns:
    EventCategory: The category this event belongs to

##### `datetime`

```python
@property
def datetime() -> datetime
```

Get timestamp as datetime object.

Returns:
    datetime: Event timestamp as datetime

##### `get`

```python
def get(key: str, default: Any = None) -> Any
```

Get value from event data.

Args:
    key: Data key to retrieve
    default: Default value if key not found

Returns:
    Value from data dict or default

**Parameters:**

- `key: str` *(required)*
- `default: Any = None`

##### `has_data`

```python
def has_data(key: str) -> bool
```

Check if event has specific data key.

Args:
    key: Data key to check

Returns:
    bool: True if key exists in data

**Parameters:**

- `key: str` *(required)*

##### `is_high_priority`

```python
def is_high_priority() -> bool
```

Check if this is a high or critical priority event.

Returns:
    bool: True if priority is HIGH or CRITICAL

##### `to_dict`

```python
def to_dict() -> dict[str, Any]
```

Convert event to dictionary.

Useful for serialization and logging.

Returns:
    dict: Event as dictionary

### EventFilter

**Decorators:** `@dataclass`


Filter for subscribing to specific events.

Allows subscribing to events based on type, category, source, or priority.

Examples:
    # Filter by type
    filter = EventFilter(types=[EventType.WORKFLOW_NEW, EventType.WORKFLOW_SAVED])

    # Filter by category
    filter = EventFilter(categories=[EventCategory.WORKFLOW])

    # Filter by source
    filter = EventFilter(sources=["WorkflowController"])

    # Filter by priority
    filter = EventFilter(min_priority=EventPriority.HIGH)

    # Combined filters (AND logic)
    filter = EventFilter(
        categories=[EventCategory.EXECUTION],
        min_priority=EventPriority.NORMAL
    )


**Attributes:**

- `categories: Optional[list[EventCategory]]`
- `max_priority: Optional[EventPriority]`
- `min_priority: Optional[EventPriority]`
- `sources: Optional[list[str]]`
- `types: Optional[list[EventType]]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__str__()` | `str` | String representation of filter. |
| `matches(event)` | `bool` | Check if event matches this filter. |

#### Method Details

##### `__str__`

```python
def __str__() -> str
```

String representation of filter.

##### `matches`

```python
def matches(event: Event) -> bool
```

Check if event matches this filter.

All specified criteria must match (AND logic).

Args:
    event: Event to check

Returns:
    bool: True if event matches filter

**Parameters:**

- `event: Event` *(required)*

### EventPriority

**Inherits from:** `Enum`


Priority levels for event handling.

Higher priority events are processed before lower priority events
when multiple events are queued.


**Attributes:**

- `CRITICAL: int`
- `HIGH: int`
- `LOW: int`
- `NORMAL: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__gt__(other)` | `bool` | Compare priorities (higher value = higher priority). |
| `__lt__(other)` | `bool` | Compare priorities (higher value = higher priority). |

#### Method Details

##### `__gt__`

```python
def __gt__(other: 'EventPriority') -> bool
```

Compare priorities (higher value = higher priority).

**Parameters:**

- `other: 'EventPriority'` *(required)*

##### `__lt__`

```python
def __lt__(other: 'EventPriority') -> bool
```

Compare priorities (higher value = higher priority).

**Parameters:**

- `other: 'EventPriority'` *(required)*

---

## casare_rpa.presentation.canvas.events.event_batcher

**File:** `src\casare_rpa\presentation\canvas\events\event_batcher.py`


EventBatcher for high-frequency event batching.

Batches high-frequency events (VARIABLE_UPDATED, NODE_PROPERTY_CHANGED,
NODE_POSITION_CHANGED) to reduce handler calls and improve UI responsiveness.

Uses a 16ms batching interval targeting 60fps UI updates.

Usage:
    from casare_rpa.presentation.canvas.events import EventBatcher, Event, EventType

    batcher = EventBatcher(interval_ms=16)

    # Batch high-frequency events
    batcher.batch(Event(
        type=EventType.VARIABLE_UPDATED,
        source="VariableController",
        data={"name": "counter", "value": 1}
    ))

    # Non-batchable events publish immediately
    batcher.batch(Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    ))


### EventBatcher


Batches high-frequency events to reduce handler calls.

High-frequency events like VARIABLE_UPDATED, NODE_PROPERTY_CHANGED, and
NODE_POSITION_CHANGED are batched over a configurable interval (default 16ms
for 60fps). When the interval elapses, a single batched event is published
containing all accumulated events.

Non-batchable events are published immediately without batching.

Attributes:
    interval_ms: Batching interval in milliseconds (default 16 for 60fps)
    pending: Map of event types to lists of pending events
    timer: QTimer for flush scheduling

Thread Safety:
    This class is designed for use on the Qt main thread only.
    QTimer ensures proper Qt event loop integration.


**Attributes:**

- `BATCHABLE_EVENTS: Set[EventType]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(interval_ms)` | `None` | Initialize EventBatcher. |
| `__repr__()` | `str` | String representation of EventBatcher. |
| `batch(event)` | `None` | Submit event for batching or immediate publication. |
| `clear()` | `None` | Clear all pending events without publishing. |
| `flush_now()` | `None` | Force immediate flush of all pending events. |
| `has_pending()` | `bool` | Check if there are pending events. |
| `pending_count()` | `int` | Get total count of pending events. |

#### Method Details

##### `__init__`

```python
def __init__(interval_ms: int = DEFAULT_BATCH_INTERVAL_MS) -> None
```

Initialize EventBatcher.

Args:
    interval_ms: Batching interval in milliseconds.
                Default is 16ms (~60fps).

**Parameters:**

- `interval_ms: int = DEFAULT_BATCH_INTERVAL_MS`

##### `__repr__`

```python
def __repr__() -> str
```

String representation of EventBatcher.

##### `batch`

```python
def batch(event: Event) -> None
```

Submit event for batching or immediate publication.

If event type is in BATCHABLE_EVENTS, the event is queued and will
be published as part of a batched event when the timer fires.

If event type is not batchable, the event is published immediately
to ensure critical events are not delayed.

Args:
    event: Event to batch or publish immediately

**Parameters:**

- `event: Event` *(required)*

##### `clear`

```python
def clear() -> None
```

Clear all pending events without publishing.

Useful for cleanup or when pending events should be discarded.

##### `flush_now`

```python
def flush_now() -> None
```

Force immediate flush of all pending events.

Useful for testing or when immediate processing is required.

##### `has_pending`

```python
def has_pending() -> bool
```

Check if there are pending events.

Returns:
    bool: True if there are events waiting to be flushed

##### `pending_count`

```python
def pending_count() -> int
```

Get total count of pending events.

Returns:
    int: Total number of pending events across all types

---

## casare_rpa.presentation.canvas.events.event_bus

**File:** `src\casare_rpa\presentation\canvas\events\event_bus.py`


Central event bus for Canvas UI component communication.

The EventBus is a singleton that provides centralized event routing,
replacing scattered Qt signal/slot connections with a unified,
type-safe event system.

Features:
    - Type-safe event subscription and publishing
    - Event filtering by type, category, source, priority
    - Priority-based event handling
    - Event history for debugging
    - Performance metrics
    - Thread-safe operation

Usage:
    from casare_rpa.presentation.canvas.events import EventBus, Event, EventType

    # Get singleton instance
    bus = EventBus()

    # Subscribe to events
    def on_workflow_saved(event: Event) -> None:
        print(f"Workflow saved: {event.data['file_path']}")

    bus.subscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)

    # Publish events
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )
    bus.publish(event)

    # Unsubscribe
    bus.unsubscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)


### EventBus


Singleton event bus for centralized event routing.

The EventBus allows components to communicate without direct coupling.
Components publish events when something happens, and other components
subscribe to events they care about.

Thread Safety:
    All public methods are thread-safe using a re-entrant lock.

Performance:
    - Event publishing: O(n) where n = number of subscribers
    - Event subscription: O(1)
    - Event unsubscription: O(n) where n = number of subscribers for that type

Attributes:
    _instance: Singleton instance (class variable)
    _subscribers: Map of event types to handler lists
    _wildcard_subscribers: Handlers that receive all events
    _filtered_subscribers: Handlers with custom filters
    _history: Recent event history for debugging
    _metrics: Performance metrics
    _lock: Thread safety lock


**Attributes:**

- `_instance: Optional['EventBus']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - | Initialize the event bus (only runs once). |
| `__new__()` | `'EventBus'` | Ensure only one instance exists (Singleton pattern). |
| `__repr__()` | `str` | String representation of EventBus. |
| `clear_all_subscribers()` | `None` | Clear all event subscribers. |
| `clear_history()` | `None` | Clear event history. |
| `enable_history(enabled)` | `None` | Enable or disable event history tracking. |
| `get_history(event_type, category, source, ...)` | `list[Event]` | Get event history with optional filtering. |
| `get_metrics()` | `dict[str, Any]` | Get performance metrics. |
| `publish(event)` | `None` | Publish an event to all subscribers. |
| `reset_instance()` | `None` | Reset the singleton instance. |
| `reset_metrics()` | `None` | Reset performance metrics. |
| `subscribe(event_type, handler)` | `None` | Subscribe to a specific event type. |
| `subscribe_all(handler)` | `None` | Subscribe to all events (wildcard subscription). |
| `subscribe_filtered(event_filter, handler)` | `None` | Subscribe to events matching a custom filter. |
| `unsubscribe(event_type, handler)` | `bool` | Unsubscribe from a specific event type. |
| `unsubscribe_all(handler)` | `bool` | Unsubscribe from all events (wildcard). |
| `unsubscribe_filtered(event_filter, handler)` | `bool` | Unsubscribe from filtered events. |

#### Method Details

##### `__init__`

```python
def __init__()
```

Initialize the event bus (only runs once).

##### `__new__`

```python
def __new__() -> 'EventBus'
```

Ensure only one instance exists (Singleton pattern).

Returns:
    EventBus: The singleton instance

##### `__repr__`

```python
def __repr__() -> str
```

String representation of EventBus.

##### `clear_all_subscribers`

```python
def clear_all_subscribers() -> None
```

Clear all event subscribers.

WARNING: This should only be used during cleanup or testing.

##### `clear_history`

```python
def clear_history() -> None
```

Clear event history.

##### `enable_history`

```python
def enable_history(enabled: bool = True) -> None
```

Enable or disable event history tracking.

Args:
    enabled: Whether to track event history

**Parameters:**

- `enabled: bool = True`

##### `get_history`

```python
def get_history(event_type: Optional[EventType] = None, category: Optional[EventCategory] = None, source: Optional[str] = None, limit: Optional[int] = None) -> list[Event]
```

Get event history with optional filtering.

Args:
    event_type: Filter by event type
    category: Filter by event category
    source: Filter by event source
    limit: Maximum number of events to return

Returns:
    list[Event]: Filtered event history (most recent first)

Example:
    # Get all workflow events
    events = bus.get_history(category=EventCategory.WORKFLOW)

    # Get last 10 events
    events = bus.get_history(limit=10)

    # Get all events from WorkflowController
    events = bus.get_history(source="WorkflowController")

**Parameters:**

- `event_type: Optional[EventType] = None`
- `category: Optional[EventCategory] = None`
- `source: Optional[str] = None`
- `limit: Optional[int] = None`

##### `get_metrics`

```python
def get_metrics() -> dict[str, Any]
```

Get performance metrics.

Returns:
    dict: Metrics including event counts, timing, errors, and cache stats

Example:
    metrics = bus.get_metrics()
    print(f"Events published: {metrics['events_published']}")
    print(f"Average handler time: {metrics['avg_handler_time']:.4f}s")
    print(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")

##### `publish`

```python
def publish(event: Event) -> None
```

Publish an event to all subscribers.

Events are delivered to:
1. Type-specific subscribers
2. Filtered subscribers (if filter matches)
3. Wildcard subscribers (all events)

Uses caching for filtered subscriber lists to improve performance
on repeated events with the same type and source.

Args:
    event: Event to publish

Example:
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )
    bus.publish(event)

**Parameters:**

- `event: Event` *(required)*

##### `reset_instance`

```python
@classmethod
def reset_instance() -> None
```

Reset the singleton instance.

WARNING: This should only be used during testing.
Creates a new EventBus instance, discarding the old one.

##### `reset_metrics`

```python
def reset_metrics() -> None
```

Reset performance metrics.

##### `subscribe`

```python
def subscribe(event_type: EventType, handler: EventHandler) -> None
```

Subscribe to a specific event type.

Args:
    event_type: Type of event to subscribe to
    handler: Function to call when event is published

Raises:
    TypeError: If handler is not callable

Example:
    def on_node_added(event: Event) -> None:
        print(f"Node added: {event.data['node_id']}")

    bus.subscribe(EventType.NODE_ADDED, on_node_added)

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: EventHandler` *(required)*

##### `subscribe_all`

```python
def subscribe_all(handler: EventHandler) -> None
```

Subscribe to all events (wildcard subscription).

Useful for logging, debugging, or analytics.

Args:
    handler: Function to call for every event

Raises:
    TypeError: If handler is not callable

Example:
    def log_all_events(event: Event) -> None:
        logger.info(f"Event: {event}")

    bus.subscribe_all(log_all_events)

**Parameters:**

- `handler: EventHandler` *(required)*

##### `subscribe_filtered`

```python
def subscribe_filtered(event_filter: EventFilter, handler: EventHandler) -> None
```

Subscribe to events matching a custom filter.

Args:
    event_filter: Filter defining which events to receive
    handler: Function to call when matching event is published

Raises:
    TypeError: If handler is not callable

Example:
    # Subscribe to all workflow events
    filter = EventFilter(categories=[EventCategory.WORKFLOW])
    bus.subscribe_filtered(filter, on_workflow_event)

    # Subscribe to high-priority execution events
    filter = EventFilter(
        categories=[EventCategory.EXECUTION],
        min_priority=EventPriority.HIGH
    )
    bus.subscribe_filtered(filter, on_critical_execution_event)

**Parameters:**

- `event_filter: EventFilter` *(required)*
- `handler: EventHandler` *(required)*

##### `unsubscribe`

```python
def unsubscribe(event_type: EventType, handler: EventHandler) -> bool
```

Unsubscribe from a specific event type.

Args:
    event_type: Type of event to unsubscribe from
    handler: Handler function to remove

Returns:
    bool: True if handler was found and removed, False otherwise

Example:
    bus.unsubscribe(EventType.NODE_ADDED, on_node_added)

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: EventHandler` *(required)*

##### `unsubscribe_all`

```python
def unsubscribe_all(handler: EventHandler) -> bool
```

Unsubscribe from all events (wildcard).

Args:
    handler: Handler function to remove

Returns:
    bool: True if handler was found and removed, False otherwise

**Parameters:**

- `handler: EventHandler` *(required)*

##### `unsubscribe_filtered`

```python
def unsubscribe_filtered(event_filter: EventFilter, handler: EventHandler) -> bool
```

Unsubscribe from filtered events.

Args:
    event_filter: Filter that was used for subscription
    handler: Handler function to remove

Returns:
    bool: True if handler was found and removed, False otherwise

**Parameters:**

- `event_filter: EventFilter` *(required)*
- `handler: EventHandler` *(required)*

---

## casare_rpa.presentation.canvas.events.event_contracts

**File:** `src\casare_rpa\presentation\canvas\events\event_contracts.py`


Event Data Contracts for CasareRPA Event Bus System.

This module defines TypedDict contracts for all event data payloads,
ensuring type safety and documentation for event-driven communication.

Usage:
    from casare_rpa.presentation.canvas.events.event_contracts import (
        NodeExecutionStartedData,
        WorkflowSavedData,
    )

    # Type-safe event creation
    data: NodeExecutionStartedData = {
        "node_id": "node_123",
        "node_type": "ClickElementNode",
        "node_name": "Click Login Button",
    }
    event = Event(
        type=EventType.NODE_EXECUTION_STARTED,
        source="ExecutionController",
        data=data
    )


### BatchedEventsData

**Inherits from:** `TypedDict`


Data for batched event delivery (from EventBatcher).


**Attributes:**

- `batched_events: List[Any]`
- `count: int`

### BreakpointHitData

**Inherits from:** `TypedDict`


Data for BREAKPOINT_HIT event.


**Attributes:**

- `execution_id: str`
- `node_id: str`
- `variables: Dict[str, Any]`

### ConnectionAddedData

**Inherits from:** `TypedDict`


Data for CONNECTION_ADDED event.


**Attributes:**

- `connection_id: str`
- `source_node_id: str`
- `source_port: str`
- `target_node_id: str`
- `target_port: str`

### ConnectionRemovedData

**Inherits from:** `TypedDict`


Data for CONNECTION_REMOVED event.


**Attributes:**

- `connection_id: str`
- `source_node_id: str`
- `target_node_id: str`

### DebugCallStackUpdatedData

**Inherits from:** `TypedDict`


Data for DEBUG_CALL_STACK_UPDATED event.


**Attributes:**

- `current_frame: int`
- `frames: List[Dict[str, Any]]`

### ErrorOccurredData

**Inherits from:** `TypedDict`


Data for ERROR_OCCURRED event.


**Attributes:**

- `error: str`
- `error_code: str`
- `source: str`
- `traceback: Optional[str]`

### ExecutionCompletedData

**Inherits from:** `TypedDict`


Data for EXECUTION_COMPLETED event.


**Attributes:**

- `duration_ms: float`
- `execution_id: str`
- `nodes_executed: int`
- `results: Dict[str, Any]`
- `status: str`
- `workflow_id: str`

### ExecutionFailedData

**Inherits from:** `TypedDict`


Data for EXECUTION_FAILED event.


**Attributes:**

- `duration_ms: float`
- `error: str`
- `error_code: str`
- `execution_id: str`
- `failed_node_id: Optional[str]`
- `workflow_id: str`

### ExecutionPausedData

**Inherits from:** `TypedDict`


Data for EXECUTION_PAUSED event.


**Attributes:**

- `current_node_id: Optional[str]`
- `execution_id: str`
- `reason: str`

### ExecutionResumedData

**Inherits from:** `TypedDict`


Data for EXECUTION_RESUMED event.


**Attributes:**

- `execution_id: str`

### ExecutionStartedData

**Inherits from:** `TypedDict`


Data for EXECUTION_STARTED event.


**Attributes:**

- `execution_id: str`
- `mode: str`
- `total_nodes: int`
- `workflow_id: str`
- `workflow_name: str`

### ExecutionStoppedData

**Inherits from:** `TypedDict`


Data for EXECUTION_STOPPED event.


**Attributes:**

- `execution_id: str`
- `reason: str`

### LogMessageData

**Inherits from:** `TypedDict`


Data for LOG_MESSAGE event.


**Attributes:**

- `level: str`
- `message: str`
- `source: str`
- `timestamp: str`

### NodeAddedData

**Inherits from:** `TypedDict`


Data for NODE_ADDED event.


**Attributes:**

- `node_id: str`
- `node_name: str`
- `node_type: str`
- `position: tuple[float, float]`

### NodeExecutionCompletedData

**Inherits from:** `TypedDict`


Data for NODE_EXECUTION_COMPLETED event.


**Attributes:**

- `duration_ms: float`
- `node_id: str`
- `node_type: str`
- `output_values: Dict[str, Any]`
- `result: Dict[str, Any]`

### NodeExecutionFailedData

**Inherits from:** `TypedDict`


Data for NODE_EXECUTION_FAILED event.


**Attributes:**

- `error: str`
- `error_code: str`
- `node_id: str`
- `node_type: str`
- `retryable: bool`
- `traceback: Optional[str]`

### NodeExecutionSkippedData

**Inherits from:** `TypedDict`


Data for NODE_EXECUTION_SKIPPED event.


**Attributes:**

- `node_id: str`
- `reason: str`

### NodeExecutionStartedData

**Inherits from:** `TypedDict`


Data for NODE_EXECUTION_STARTED event.


**Attributes:**

- `node_id: str`
- `node_name: str`
- `node_type: str`

### NodePositionChangedData

**Inherits from:** `TypedDict`


Data for NODE_POSITION_CHANGED event.


**Attributes:**

- `node_id: str`
- `old_position: tuple[float, float]`
- `position: tuple[float, float]`

### NodePropertyChangedData

**Inherits from:** `TypedDict`


Data for NODE_PROPERTY_CHANGED event.


**Attributes:**

- `new_value: Any`
- `node_id: str`
- `old_value: Any`
- `property_name: str`

### NodeRemovedData

**Inherits from:** `TypedDict`


Data for NODE_REMOVED event.


**Attributes:**

- `node_id: str`
- `node_type: str`

### NodeSelectedData

**Inherits from:** `TypedDict`


Data for NODE_SELECTED event.


**Attributes:**

- `node_id: str`
- `node_ids: List[str]`

### PanelToggledData

**Inherits from:** `TypedDict`


Data for PANEL_TOGGLED event.


**Attributes:**

- `panel_name: str`
- `visible: bool`

### PerformanceMetricData

**Inherits from:** `TypedDict`


Data for PERFORMANCE_METRIC event.


**Attributes:**

- `context: Dict[str, Any]`
- `metric_name: str`
- `unit: str`
- `value: float`

### ProjectClosedData

**Inherits from:** `TypedDict`


Data for PROJECT_CLOSED event.


**Attributes:**

- `project_path: str`

### ProjectOpenedData

**Inherits from:** `TypedDict`


Data for PROJECT_OPENED event.


**Attributes:**

- `project_name: str`
- `project_path: str`
- `scenario_count: int`

### ScenarioOpenedData

**Inherits from:** `TypedDict`


Data for SCENARIO_OPENED event.


**Attributes:**

- `project_name: str`
- `scenario_name: str`
- `scenario_path: str`

### ThemeChangedData

**Inherits from:** `TypedDict`


Data for THEME_CHANGED event.


**Attributes:**

- `theme: str`

### TriggerCreatedData

**Inherits from:** `TypedDict`


Data for TRIGGER_CREATED event.


**Attributes:**

- `config: Dict[str, Any]`
- `trigger_id: str`
- `trigger_type: str`
- `workflow_id: str`

### TriggerFiredData

**Inherits from:** `TypedDict`


Data for TRIGGER_FIRED event.


**Attributes:**

- `payload: Dict[str, Any]`
- `trigger_id: str`
- `trigger_type: str`
- `workflow_id: str`

### VariableDeletedData

**Inherits from:** `TypedDict`


Data for VARIABLE_DELETED event.


**Attributes:**

- `name: str`
- `scope: str`

### VariableSetData

**Inherits from:** `TypedDict`


Data for VARIABLE_SET / VARIABLE_UPDATED event.


**Attributes:**

- `name: str`
- `node_id: Optional[str]`
- `old_value: Any`
- `scope: str`
- `value: Any`

### WorkflowClosedData

**Inherits from:** `TypedDict`


Data for WORKFLOW_CLOSED event.


**Attributes:**

- `file_path: Optional[str]`
- `workflow_id: str`

### WorkflowModifiedData

**Inherits from:** `TypedDict`


Data for WORKFLOW_MODIFIED event.


**Attributes:**

- `modified: bool`
- `workflow_id: str`

### WorkflowNewData

**Inherits from:** `TypedDict`


Data for WORKFLOW_NEW event.


**Attributes:**

- `workflow_id: str`
- `workflow_name: str`

### WorkflowOpenedData

**Inherits from:** `TypedDict`


Data for WORKFLOW_OPENED event.


**Attributes:**

- `file_path: str`
- `workflow_id: str`
- `workflow_name: str`

### WorkflowSavedData

**Inherits from:** `TypedDict`


Data for WORKFLOW_SAVED event.


**Attributes:**

- `file_path: str`
- `workflow_id: str`
- `workflow_name: str`

### ZoomChangedData

**Inherits from:** `TypedDict`


Data for ZOOM_CHANGED event.


**Attributes:**

- `old_zoom_level: float`
- `zoom_level: float`

---

## casare_rpa.presentation.canvas.events.event_handler

**File:** `src\casare_rpa\presentation\canvas\events\event_handler.py`


Event handler decorators and base class for Canvas components.

This module provides utilities for creating event-driven components
that subscribe to and handle events from the EventBus.

Features:
    - @event_handler decorator for method-based handlers
    - EventHandler base class for component event handling
    - Automatic subscription/unsubscription management
    - Type-safe event handling patterns

Usage:
    from casare_rpa.presentation.canvas.events import (
        EventHandler, event_handler, EventType, Event
    )

    # Using EventHandler base class
    class MyController(EventHandler):
        def __init__(self):
            super().__init__()

            # Subscribe to events
            self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)

        def on_workflow_new(self, event: Event) -> None:
            print(f"New workflow: {event.data}")

        def cleanup(self):
            # Automatically unsubscribes from all events
            super().cleanup()

    # Using decorator
    class MyComponent:
        def __init__(self):
            self.bus = EventBus()

        @event_handler(EventType.NODE_ADDED)
        def on_node_added(self, event: Event) -> None:
            print(f"Node added: {event.data['node_id']}")


### Functions

#### `event_handler`

```python
def event_handler(event_type: Optional[EventType] = None, event_filter: Optional[EventFilter] = None) -> Callable
```

Decorator for marking methods as event handlers.

Can be used with EventType for specific events, EventFilter for
filtered subscriptions, or no arguments for manual subscription.

Args:
    event_type: Specific event type to handle (optional)
    event_filter: Custom filter for events (optional)

Returns:
    Decorated function with event handling metadata

Examples:
    # Handle specific event type
    @event_handler(EventType.WORKFLOW_SAVED)
    def on_workflow_saved(self, event: Event) -> None:
        print(f"Saved: {event.data['file_path']}")

    # Handle filtered events
    filter = EventFilter(categories=[EventCategory.EXECUTION])
    @event_handler(event_filter=filter)
    def on_execution_event(self, event: Event) -> None:
        print(f"Execution event: {event.type}")

    # Mark handler for manual subscription
    @event_handler()
    def on_custom_event(self, event: Event) -> None:
        print(f"Custom event: {event}")


### EventHandler


Base class for components that handle events.

Provides automatic subscription management and cleanup.
Subclasses can override event handler methods decorated with
@event_handler or use the subscribe() method directly.

Features:
    - Automatic subscription management
    - Cleanup on destruction
    - Type-safe event handling
    - Subscription tracking

Examples:
    class WorkflowController(EventHandler):
        def __init__(self):
            super().__init__()

            # Manual subscription
            self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)
            self.subscribe(EventType.WORKFLOW_OPENED, self.on_workflow_opened)

        def on_workflow_new(self, event: Event) -> None:
            logger.info(f"New workflow: {event.data}")

        def on_workflow_opened(self, event: Event) -> None:
            logger.info(f"Opened workflow: {event.data['file_path']}")

        def cleanup(self):
            # Automatically unsubscribes from all events
            super().cleanup()

    # Alternative using decorators
    class NodeController(EventHandler):
        def __init__(self):
            super().__init__()
            self._auto_subscribe_decorated_handlers()

        @event_handler(EventType.NODE_ADDED)
        def on_node_added(self, event: Event) -> None:
            logger.info(f"Node added: {event.data['node_id']}")

        @event_handler(EventType.NODE_REMOVED)
        def on_node_removed(self, event: Event) -> None:
            logger.info(f"Node removed: {event.data['node_id']}")


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__del__()` | - | Cleanup on destruction. |
| `__init__(event_bus)` | - | Initialize event handler. |
| `cleanup()` | `None` | Cleanup event subscriptions. |
| `publish(event)` | `None` | Publish an event to the event bus. |
| `subscribe(event_type, handler)` | `None` | Subscribe to a specific event type. |
| `subscribe_all(handler)` | `None` | Subscribe to all events (wildcard). |
| `subscribe_filtered(event_filter, handler)` | `None` | Subscribe to events matching a filter. |
| `unsubscribe(event_type, handler)` | `bool` | Unsubscribe from specific event type. |
| `unsubscribe_all(handler)` | `bool` | Unsubscribe from all events (wildcard). |
| `unsubscribe_filtered(event_filter, handler)` | `bool` | Unsubscribe from filtered events. |

#### Method Details

##### `__del__`

```python
def __del__()
```

Cleanup on destruction.

##### `__init__`

```python
def __init__(event_bus: Optional[EventBus] = None)
```

Initialize event handler.

Args:
    event_bus: EventBus instance to use (defaults to singleton)

**Parameters:**

- `event_bus: Optional[EventBus] = None`

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup event subscriptions.

Should be called when component is destroyed.
Automatically unsubscribes from all events.

##### `publish`

```python
def publish(event: Event) -> None
```

Publish an event to the event bus.

Args:
    event: Event to publish

Example:
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source=self.__class__.__name__,
        data={"file_path": str(path)}
    )
    self.publish(event)

**Parameters:**

- `event: Event` *(required)*

##### `subscribe`

```python
def subscribe(event_type: EventType, handler: Callable[[Event], None]) -> None
```

Subscribe to a specific event type.

Tracks subscription for automatic cleanup.

Args:
    event_type: Type of event to subscribe to
    handler: Handler function (can be method)

Example:
    self.subscribe(EventType.WORKFLOW_SAVED, self.on_workflow_saved)

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: Callable[[Event], None]` *(required)*

##### `subscribe_all`

```python
def subscribe_all(handler: Callable[[Event], None]) -> None
```

Subscribe to all events (wildcard).

Args:
    handler: Handler function for all events

Example:
    self.subscribe_all(self.log_all_events)

**Parameters:**

- `handler: Callable[[Event], None]` *(required)*

##### `subscribe_filtered`

```python
def subscribe_filtered(event_filter: EventFilter, handler: Callable[[Event], None]) -> None
```

Subscribe to events matching a filter.

Args:
    event_filter: Filter defining which events to receive
    handler: Handler function for matching events

Example:
    filter = EventFilter(categories=[EventCategory.WORKFLOW])
    self.subscribe_filtered(filter, self.on_workflow_event)

**Parameters:**

- `event_filter: EventFilter` *(required)*
- `handler: Callable[[Event], None]` *(required)*

##### `unsubscribe`

```python
def unsubscribe(event_type: EventType, handler: Callable[[Event], None]) -> bool
```

Unsubscribe from specific event type.

Args:
    event_type: Event type to unsubscribe from
    handler: Handler function to remove

Returns:
    bool: True if unsubscribed successfully

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: Callable[[Event], None]` *(required)*

##### `unsubscribe_all`

```python
def unsubscribe_all(handler: Callable[[Event], None]) -> bool
```

Unsubscribe from all events (wildcard).

Args:
    handler: Handler function to remove

Returns:
    bool: True if unsubscribed successfully

**Parameters:**

- `handler: Callable[[Event], None]` *(required)*

##### `unsubscribe_filtered`

```python
def unsubscribe_filtered(event_filter: EventFilter, handler: Callable[[Event], None]) -> bool
```

Unsubscribe from filtered events.

Args:
    event_filter: Filter used for subscription
    handler: Handler function to remove

Returns:
    bool: True if unsubscribed successfully

**Parameters:**

- `event_filter: EventFilter` *(required)*
- `handler: Callable[[Event], None]` *(required)*

---

## casare_rpa.presentation.canvas.events.event_types

**File:** `src\casare_rpa\presentation\canvas\events\event_types.py`


Event type definitions for the Canvas event system.

This module defines all event types that can be emitted and subscribed to
within the Canvas UI. Events are organized by category for better organization.

Event Naming Convention:
    - Use NOUN_VERB pattern (e.g., WORKFLOW_NEW, NODE_ADDED)
    - Past tense for completed actions (e.g., NODE_ADDED, WORKFLOW_SAVED)
    - Present tense for ongoing actions (e.g., EXECUTION_RUNNING)
    - Use descriptive names that clearly indicate what happened

Usage:
    from casare_rpa.presentation.canvas.events import EventType

    event_type = EventType.WORKFLOW_NEW
    print(event_type.name)  # "WORKFLOW_NEW"
    print(event_type.value)  # unique integer


### EventCategory

**Inherits from:** `Enum`


Categories for organizing event types.

Used for event filtering and logging.


**Attributes:**

- `CONNECTION: str`
- `DEBUG: str`
- `EXECUTION: str`
- `NODE: str`
- `PROJECT: str`
- `SYSTEM: str`
- `TRIGGER: str`
- `UI: str`
- `VARIABLE: str`
- `WORKFLOW: str`

### EventType

**Inherits from:** `Enum`


Comprehensive enumeration of all Canvas event types.

Each event type represents a specific action or state change
in the Canvas UI that components can react to.

Organization:
    - Workflow events (20+)
    - Node events (15+)
    - Connection events (10+)
    - Execution events (15+)
    - UI events (10+)
    - System events (10+)
    - Project events (10+)
    - Variable events (5+)
    - Debug events (5+)
    - Trigger events (5+)

Total: 100+ event types


**Attributes:**

- `AUTOSAVE_COMPLETED: auto`
- `AUTOSAVE_FAILED: auto`
- `AUTOSAVE_TRIGGERED: auto`
- `BREAKPOINT_HIT: auto`
- `BROWSER_PREVIEW_OPENED: auto`
- `CLIPBOARD_UPDATED: auto`
- `COMMAND_PALETTE_OPENED: auto`
- `CONNECTION_ADDED: auto`
- `CONNECTION_DESELECTED: auto`
- `CONNECTION_REMOVED: auto`
- `CONNECTION_REROUTED: auto`
- `CONNECTION_SELECTED: auto`
- `CONNECTION_VALIDATED: auto`
- `CONNECTION_VALIDATION_FAILED: auto`
- `DEBUG_CALL_STACK_UPDATED: auto`
- `DEBUG_MODE_DISABLED: auto`
- `DEBUG_MODE_ENABLED: auto`
- `DEBUG_OUTPUT: auto`
- `ERROR_OCCURRED: auto`
- `EXECUTION_CANCELLED: auto`
- `EXECUTION_COMPLETED: auto`
- `EXECUTION_FAILED: auto`
- `EXECUTION_HISTORY_UPDATED: auto`
- `EXECUTION_PAUSED: auto`
- `EXECUTION_RESUMED: auto`
- `EXECUTION_STARTED: auto`
- `EXECUTION_STEP_INTO: auto`
- `EXECUTION_STEP_OUT: auto`
- `EXECUTION_STEP_OVER: auto`
- `EXECUTION_STOPPED: auto`
- `EXECUTION_TRACE_UPDATED: auto`
- `HOTKEY_TRIGGERED: auto`
- `INFO_MESSAGE: auto`
- `LOG_MESSAGE: auto`
- `MEMORY_WARNING: auto`
- `MINIMAP_TOGGLED: auto`
- `NODES_GROUPED: auto`
- `NODES_UNGROUPED: auto`
- `NODE_ADDED: auto`
- `NODE_BREAKPOINT_ADDED: auto`
- `NODE_BREAKPOINT_REMOVED: auto`
- `NODE_CONFIG_UPDATED: auto`
- `NODE_COPIED: auto`
- `NODE_CUT: auto`
- `NODE_DESELECTED: auto`
- `NODE_DISABLED: auto`
- `NODE_DUPLICATED: auto`
- `NODE_ENABLED: auto`
- `NODE_EXECUTION_COMPLETED: auto`
- `NODE_EXECUTION_FAILED: auto`
- `NODE_EXECUTION_SKIPPED: auto`
- `NODE_EXECUTION_STARTED: auto`
- `NODE_FILTER_APPLIED: auto`
- `NODE_PASTED: auto`
- `NODE_POSITION_CHANGED: auto`
- `NODE_PROPERTY_CHANGED: auto`
- `NODE_REMOVED: auto`
- `NODE_RENAMED: auto`
- `NODE_SEARCH_OPENED: auto`
- `NODE_SELECTED: auto`
- `NODE_SELECTION_CHANGED: auto`
- `PANEL_CLOSED: auto`
- `PANEL_OPENED: auto`
- `PANEL_RESIZED: auto`
- `PANEL_TAB_CHANGED: auto`
- `PANEL_TOGGLED: auto`
- `PERFORMANCE_METRIC: auto`
- `PORT_CONNECTED: auto`
- `PORT_DISCONNECTED: auto`
- `PORT_VALUE_CHANGED: auto`
- `PREFERENCES_UPDATED: auto`
- `PROJECT_CLOSED: auto`
- `PROJECT_CREATED: auto`
- `PROJECT_DELETED: auto`
- `PROJECT_OPENED: auto`
- `PROJECT_RENAMED: auto`
- `PROJECT_STRUCTURE_CHANGED: auto`
- `SCENARIO_CREATED: auto`
- `SCENARIO_DELETED: auto`
- `SCENARIO_OPENED: auto`
- `SELECTOR_PICKED: auto`
- `SELECTOR_PICKER_OPENED: auto`
- `THEME_CHANGED: auto`
- `TRIGGER_CREATED: auto`
- `TRIGGER_DELETED: auto`
- `TRIGGER_DISABLED: auto`
- `TRIGGER_ENABLED: auto`
- `TRIGGER_FIRED: auto`
- `TRIGGER_UPDATED: auto`
- `VARIABLE_CLEARED: auto`
- `VARIABLE_DELETED: auto`
- `VARIABLE_INSPECTOR_UPDATED: auto`
- `VARIABLE_SCOPE_CHANGED: auto`
- `VARIABLE_SET: auto`
- `VARIABLE_UPDATED: auto`
- `VIEW_CENTERED: auto`
- `VIEW_FIT_TO_SELECTION: auto`
- `WARNING_ISSUED: auto`
- `WATCH_EXPRESSION_ADDED: auto`
- `WATCH_EXPRESSION_REMOVED: auto`
- `WORKFLOW_CLOSED: auto`
- `WORKFLOW_DUPLICATED: auto`
- `WORKFLOW_EXPORTED: auto`
- `WORKFLOW_HISTORY_CLEARED: auto`
- `WORKFLOW_IMPORTED: auto`
- `WORKFLOW_METADATA_UPDATED: auto`
- `WORKFLOW_MODIFIED: auto`
- `WORKFLOW_NEW: auto`
- `WORKFLOW_OPENED: auto`
- `WORKFLOW_REDO: auto`
- `WORKFLOW_RENAMED: auto`
- `WORKFLOW_SAVED: auto`
- `WORKFLOW_SAVED_AS_TEMPLATE: auto`
- `WORKFLOW_SAVE_AS: auto`
- `WORKFLOW_TEMPLATE_APPLIED: auto`
- `WORKFLOW_UNDO: auto`
- `WORKFLOW_VALIDATED: auto`
- `WORKFLOW_VALIDATION_FAILED: auto`
- `ZOOM_CHANGED: auto`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__repr__()` | `str` | Detailed representation of event type. |
| `__str__()` | `str` | String representation of event type. |
| `category()` | `EventCategory` | Get the category of this event type. |

#### Method Details

##### `__repr__`

```python
def __repr__() -> str
```

Detailed representation of event type.

##### `__str__`

```python
def __str__() -> str
```

String representation of event type.

##### `category`

```python
@property
def category() -> EventCategory
```

Get the category of this event type.

Returns:
    EventCategory: The category this event belongs to

---

## casare_rpa.presentation.canvas.events.lazy_subscription

**File:** `src\casare_rpa\presentation\canvas\events\lazy_subscription.py`


Lazy event subscription for EventBus optimization.

Provides visibility-based subscription that activates when component becomes
visible and deactivates when hidden, reducing EventBus overhead for panels
that are not currently in view.

Uses Qt event filters for cleaner interception without handler mutation.

Usage:
    from casare_rpa.presentation.canvas.events import LazySubscription, EventType

    class DebugPanel(QDockWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self._lazy_subs = [
                LazySubscription(EventType.NODE_EXECUTION_STARTED, self.on_exec_started, self),
                LazySubscription(EventType.NODE_EXECUTION_COMPLETED, self.on_exec_completed, self),
            ]


### LazySubscription

**Inherits from:** `QObject`


Subscription that activates when component becomes visible.

Uses Qt event filter to intercept show/hide events and automatically
subscribe/unsubscribe from EventBus, reducing subscription overhead
when panels are hidden.

Attributes:
    event_type: EventType to subscribe to
    handler: Callback function for events
    component: QWidget whose visibility controls subscription
    active: Whether subscription is currently active


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(event_type, handler, component)` | `None` | Initialize lazy subscription. |
| `activate()` | `None` | Activate subscription (subscribe to EventBus). |
| `cleanup()` | `None` | Remove event filter and deactivate subscription. |
| `deactivate()` | `None` | Deactivate subscription (unsubscribe from EventBus). |
| `eventFilter(watched, event)` | `bool` | Qt event filter to intercept show/hide events. |

#### Method Details

##### `__init__`

```python
def __init__(event_type: EventType, handler: Callable, component: 'QWidget') -> None
```

Initialize lazy subscription.

Args:
    event_type: EventType to subscribe to
    handler: Callback function to invoke on event
    component: QWidget whose visibility controls subscription

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: Callable` *(required)*
- `component: 'QWidget'` *(required)*

##### `activate`

```python
def activate() -> None
```

Activate subscription (subscribe to EventBus).

##### `cleanup`

```python
def cleanup() -> None
```

Remove event filter and deactivate subscription.

Should be called when LazySubscription is no longer needed.

##### `deactivate`

```python
def deactivate() -> None
```

Deactivate subscription (unsubscribe from EventBus).

##### `eventFilter`

```python
def eventFilter(watched: QObject, event: QEvent) -> bool
```

Qt event filter to intercept show/hide events.

Args:
    watched: Object being watched
    event: Event to filter

Returns:
    False to allow event propagation

**Parameters:**

- `watched: QObject` *(required)*
- `event: QEvent` *(required)*

### LazySubscriptionGroup


Manages multiple LazySubscriptions for a single component.

Convenience class to handle multiple event subscriptions that should
all activate/deactivate together based on component visibility.

Usage:
    self._lazy_group = LazySubscriptionGroup(self, [
        (EventType.NODE_EXECUTION_STARTED, self.on_exec_started),
        (EventType.NODE_EXECUTION_COMPLETED, self.on_exec_completed),
    ])


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(component, subscriptions)` | `None` | Initialize lazy subscription group. |
| `activate_all()` | `None` | Force activate all subscriptions. |
| `active()` | `bool` | Check if subscriptions are active. |
| `cleanup()` | `None` | Cleanup all subscriptions. |
| `deactivate_all()` | `None` | Force deactivate all subscriptions. |

#### Method Details

##### `__init__`

```python
def __init__(component: QWidget, subscriptions: List[tuple[EventType, Callable]]) -> None
```

Initialize lazy subscription group.

Args:
    component: QWidget whose visibility controls subscriptions
    subscriptions: List of (EventType, handler) tuples

**Parameters:**

- `component: QWidget` *(required)*
- `subscriptions: List[tuple[EventType, Callable]]` *(required)*

##### `activate_all`

```python
def activate_all() -> None
```

Force activate all subscriptions.

##### `active`

```python
@property
def active() -> bool
```

Check if subscriptions are active.

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup all subscriptions.

##### `deactivate_all`

```python
def deactivate_all() -> None
```

Force deactivate all subscriptions.

---

## casare_rpa.presentation.canvas.events.qt_signal_bridge

**File:** `src\casare_rpa\presentation\canvas\events\qt_signal_bridge.py`


Qt Signal Bridge for EventBus integration.

This module provides a bridge between the EventBus and Qt's signal/slot system,
allowing Qt widgets to emit and receive events through Qt signals while the
underlying system uses the EventBus.

This enables:
    - Gradual migration from Qt signals to EventBus
    - Compatibility with existing Qt-based code
    - Cross-thread event handling via Qt's event loop

Usage:
    from casare_rpa.presentation.canvas.events import QtSignalBridge, EventType, Event

    # Create bridge
    bridge = QtSignalBridge()

    # Connect Qt slots to events
    bridge.workflow_event.connect(on_workflow_event)
    bridge.node_event.connect(on_node_event)
    bridge.execution_event.connect(on_execution_event)

    # Publish event (automatically emits Qt signal)
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )
    bridge.publish(event)  # Emits workflow_event signal


### QtEventEmitter

**Inherits from:** `QObject`


Qt-friendly event emitter for controllers and components.

This class wraps EventBus publishing with Qt signal emission,
allowing controllers to emit events that work with both EventBus
subscribers and Qt signal/slot connections.

Useful for controllers that need to support both EventBus and
legacy Qt signal code during migration.

Example:
    class WorkflowController(QObject):
        def __init__(self):
            super().__init__()
            self.emitter = QtEventEmitter(self)

            # Connect to Qt signals if needed
            self.emitter.event_emitted.connect(self.on_event)

        async def save_workflow(self, path: Path) -> None:
            # ... save logic ...

            # Emit event (goes to both EventBus and Qt signals)
            event = Event(
                type=EventType.WORKFLOW_SAVED,
                source="WorkflowController",
                data={"file_path": str(path)}
            )
            self.emitter.emit(event)

        def on_event(self, event: Event) -> None:
            print(f"Event: {event}")


**Attributes:**

- `event_emitted: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, event_bus)` | - | Initialize Qt event emitter. |
| `emit(event)` | `None` | Emit event to both EventBus and Qt signals. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QObject] = None, event_bus: Optional[EventBus] = None)
```

Initialize Qt event emitter.

Args:
    parent: Parent QObject
    event_bus: EventBus instance (defaults to singleton)

**Parameters:**

- `parent: Optional[QObject] = None`
- `event_bus: Optional[EventBus] = None`

##### `emit`

```python
def emit(event: Event) -> None
```

Emit event to both EventBus and Qt signals.

Args:
    event: Event to emit

Example:
    event = Event(
        type=EventType.NODE_SELECTED,
        source="NodeController",
        data={"node_id": "123"}
    )
    self.emitter.emit(event)

**Parameters:**

- `event: Event` *(required)*

### QtEventSubscriber

**Inherits from:** `QObject`


Qt-friendly event subscriber for widgets.

This class provides Qt signal-based subscription to EventBus events,
allowing Qt widgets to receive events through signal/slot connections
instead of callback functions.

Example:
    class WorkflowPanel(QWidget):
        def __init__(self):
            super().__init__()
            self.subscriber = QtEventSubscriber(self)

            # Subscribe to specific event types
            self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
            self.subscriber.subscribe(EventType.WORKFLOW_OPENED)

            # Connect to signal
            self.subscriber.event_received.connect(self.on_event)

        def on_event(self, event: Event) -> None:
            if event.type == EventType.WORKFLOW_SAVED:
                self.update_status(f"Saved: {event.data['file_path']}")
            elif event.type == EventType.WORKFLOW_OPENED:
                self.update_status(f"Opened: {event.data['file_path']}")


**Attributes:**

- `event_received: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__del__()` | - | Cleanup on destruction. |
| `__init__(parent, event_bus)` | - | Initialize Qt event subscriber. |
| `cleanup()` | `None` | Cleanup all subscriptions. |
| `subscribe(event_type)` | `None` | Subscribe to specific event type. |
| `unsubscribe(event_type)` | `None` | Unsubscribe from specific event type. |

#### Method Details

##### `__del__`

```python
def __del__()
```

Cleanup on destruction.

##### `__init__`

```python
def __init__(parent: Optional[QObject] = None, event_bus: Optional[EventBus] = None)
```

Initialize Qt event subscriber.

Args:
    parent: Parent QObject
    event_bus: EventBus instance (defaults to singleton)

**Parameters:**

- `parent: Optional[QObject] = None`
- `event_bus: Optional[EventBus] = None`

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup all subscriptions.

Should be called when widget is destroyed.

##### `subscribe`

```python
def subscribe(event_type: EventType) -> None
```

Subscribe to specific event type.

Events will be emitted via the event_received signal.

Args:
    event_type: Type of event to subscribe to

Example:
    subscriber.subscribe(EventType.WORKFLOW_SAVED)
    subscriber.event_received.connect(on_event)

**Parameters:**

- `event_type: EventType` *(required)*

##### `unsubscribe`

```python
def unsubscribe(event_type: EventType) -> None
```

Unsubscribe from specific event type.

Args:
    event_type: Type of event to unsubscribe from

**Parameters:**

- `event_type: EventType` *(required)*

### QtSignalBridge

**Inherits from:** `QObject`


Bridge between EventBus and Qt signals.

This class subscribes to all EventBus events and re-emits them as
Qt signals, allowing Qt widgets to use signal/slot connections
while maintaining EventBus architecture.

Signals:
    event_emitted: Generic signal for all events
    workflow_event: Signal for workflow-related events
    node_event: Signal for node-related events
    connection_event: Signal for connection-related events
    execution_event: Signal for execution-related events
    ui_event: Signal for UI-related events
    system_event: Signal for system-related events
    project_event: Signal for project-related events
    variable_event: Signal for variable-related events
    debug_event: Signal for debug-related events
    trigger_event: Signal for trigger-related events

Example:
    # In a Qt widget
    class MyWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.bridge = QtSignalBridge()

            # Connect to specific category signals
            self.bridge.workflow_event.connect(self.on_workflow_event)
            self.bridge.execution_event.connect(self.on_execution_event)

        def on_workflow_event(self, event: Event) -> None:
            if event.type == EventType.WORKFLOW_SAVED:
                self.update_title(event.data['file_path'])

        def on_execution_event(self, event: Event) -> None:
            if event.type == EventType.EXECUTION_STARTED:
                self.show_progress_bar()


**Attributes:**

- `connection_event: Signal`
- `debug_event: Signal`
- `event_emitted: Signal`
- `execution_event: Signal`
- `node_event: Signal`
- `project_event: Signal`
- `system_event: Signal`
- `trigger_event: Signal`
- `ui_event: Signal`
- `variable_event: Signal`
- `workflow_event: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__del__()` | - | Cleanup on destruction. |
| `__init__(event_bus, parent)` | - | Initialize Qt signal bridge. |
| `cleanup()` | `None` | Cleanup signal bridge. |
| `publish(event)` | `None` | Publish event to EventBus (which will trigger Qt signals). |

#### Method Details

##### `__del__`

```python
def __del__()
```

Cleanup on destruction.

##### `__init__`

```python
def __init__(event_bus: Optional[EventBus] = None, parent: Optional[QObject] = None)
```

Initialize Qt signal bridge.

Args:
    event_bus: EventBus instance to bridge (defaults to singleton)
    parent: Parent QObject (for Qt ownership)

**Parameters:**

- `event_bus: Optional[EventBus] = None`
- `parent: Optional[QObject] = None`

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup signal bridge.

Unsubscribes from EventBus to prevent memory leaks.

##### `publish`

```python
def publish(event: Event) -> None
```

Publish event to EventBus (which will trigger Qt signals).

This is a convenience method for publishing events that will
be emitted as Qt signals.

Args:
    event: Event to publish

Example:
    event = Event(
        type=EventType.NODE_ADDED,
        source="NodeController",
        data={"node_id": "123"}
    )
    bridge.publish(event)

**Parameters:**

- `event: Event` *(required)*

---

## casare_rpa.presentation.canvas.execution.canvas_workflow_runner

**File:** `src\casare_rpa\presentation\canvas\execution\canvas_workflow_runner.py`


Canvas Workflow Runner.

Bridges serialized workflow from Canvas to Application layer execution.
Supports both one-time execution and trigger-based listening.


### CanvasWorkflowRunner


Runs workflows from the Canvas context.

Coordinates:
- WorkflowSerializer to get workflow data from graph
- load_workflow_from_dict to create WorkflowSchema
- ExecuteWorkflowUseCase for actual execution
- EventBus for progress notifications (handled by use case)
- Trigger activation for trigger-based workflows


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(serializer, event_bus, main_window)` | - | Initialize the workflow runner. |
| `is_listening()` | `bool` | Check if trigger is actively listening. |
| `is_paused()` | `bool` | Check if workflow is currently paused. |
| `is_running()` | `bool` | Check if workflow is currently running. |
| `pause()` | `None` | Pause workflow execution (legacy method). |
| `resume()` | `None` | Resume workflow execution (legacy method). |
| `async run_all_workflows(pause_event)` | `bool` | Execute all workflows on canvas concurrently (Shift+F3). |
| `async run_workflow(target_node_id, single_node)` | `bool` | Execute the workflow. |
| `async run_workflow_with_pause_support(pause_event, target_node_id, single_node)` | `bool` | Execute workflow with pause/resume support. |
| `async start_listening()` | `bool` | Start trigger listening mode. |
| `stop()` | `None` | Stop workflow execution. |
| `async stop_listening()` | `bool` | Stop trigger listening mode. |
| `trigger_run_count()` | `int` | Get number of times trigger has fired. |

#### Method Details

##### `__init__`

```python
def __init__(serializer: 'WorkflowSerializer', event_bus: 'EventBus', main_window: 'MainWindow')
```

Initialize the workflow runner.

Args:
    serializer: WorkflowSerializer instance
    event_bus: EventBus for publishing execution events
    main_window: MainWindow for accessing settings

**Parameters:**

- `serializer: 'WorkflowSerializer'` *(required)*
- `event_bus: 'EventBus'` *(required)*
- `main_window: 'MainWindow'` *(required)*

##### `is_listening`

```python
@property
def is_listening() -> bool
```

Check if trigger is actively listening.

##### `is_paused`

```python
@property
def is_paused() -> bool
```

Check if workflow is currently paused.

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if workflow is currently running.

##### `pause`

```python
def pause() -> None
```

Pause workflow execution (legacy method).

NOTE: This method is for legacy run_workflow() calls. Workflows started
via run_workflow_with_pause_support() (called by ExecutionLifecycleManager)
have full pause/resume support via asyncio.Event.

This legacy method only sets UI state flag and has no effect on execution.

##### `resume`

```python
def resume() -> None
```

Resume workflow execution (legacy method).

NOTE: This method is for legacy run_workflow() calls. Workflows started
via run_workflow_with_pause_support() (called by ExecutionLifecycleManager)
have full pause/resume support via asyncio.Event.

This legacy method only clears UI state flag and has no effect on execution.

##### `run_all_workflows`

```python
async def run_all_workflows(pause_event: asyncio.Event) -> bool
```

Execute all workflows on canvas concurrently (Shift+F3).

NOTE: Shortcut is Shift+F3 (not Shift+F5 which is Stop).

When the canvas contains multiple independent workflows (each with its
own StartNode), this method executes them all in parallel. Each workflow
gets SHARED variables but SEPARATE browser instances.

Args:
    pause_event: Event for pause/resume coordination

Returns:
    True if at least one workflow completed successfully, False if all failed

**Parameters:**

- `pause_event: asyncio.Event` *(required)*

##### `run_workflow`

```python
async def run_workflow(target_node_id: Optional[str] = None, single_node: bool = False) -> bool
```

Execute the workflow.

Args:
    target_node_id: For Run-To-Node (F4), stop at this node
    single_node: For Run-Single-Node (F5), execute only this node

Returns:
    True if completed successfully, False otherwise

**Parameters:**

- `target_node_id: Optional[str] = None`
- `single_node: bool = False`

##### `run_workflow_with_pause_support`

```python
async def run_workflow_with_pause_support(pause_event: asyncio.Event, target_node_id: Optional[str] = None, single_node: bool = False) -> bool
```

Execute workflow with pause/resume support.

This method is called by ExecutionLifecycleManager to run workflows
with pause coordination.

Args:
    pause_event: Event for pause/resume coordination
    target_node_id: For Run-To-Node (F4), stop at this node.
                    For Run-Single-Node (F5), run only this node.
    single_node: If True, execute only the target_node_id node (F5 mode)

Returns:
    True if completed successfully, False otherwise

**Parameters:**

- `pause_event: asyncio.Event` *(required)*
- `target_node_id: Optional[str] = None`
- `single_node: bool = False`

##### `start_listening`

```python
async def start_listening() -> bool
```

Start trigger listening mode.

For workflows with a trigger node as entry point, this creates
and activates the trigger to listen for events. When the trigger
fires, the workflow is executed with the trigger payload.

Returns:
    True if listening started successfully, False otherwise

##### `stop`

```python
def stop() -> None
```

Stop workflow execution.

Signals the ExecuteWorkflowUseCase to stop at the next opportunity
(after the current node completes). The use case checks _stop_requested
flag in its execution loop.

##### `stop_listening`

```python
async def stop_listening() -> bool
```

Stop trigger listening mode.

Returns:
    True if stopped successfully, False otherwise

##### `trigger_run_count`

```python
@property
def trigger_run_count() -> int
```

Get number of times trigger has fired.

---

## casare_rpa.presentation.canvas.graph.category_utils

**File:** `src\casare_rpa\presentation\canvas\graph\category_utils.py`


Category Utilities - Hierarchical category path support.

Provides utilities for parsing, building, and managing hierarchical
node categories with arbitrary depth (e.g., "google/gmail/send").

Features:
- CategoryPath dataclass for parsing paths like "google/gmail/send"
- Category tree building from flat category lists
- Display name resolution with leaf fallback
- Color inheritance with distinct subcategory shades


### Functions

#### `build_category_tree`

```python
def build_category_tree(categories: List[str]) -> CategoryNode
```

Build a hierarchical tree structure from flat category paths.

Args:
    categories: List of category path strings (e.g., ["google/gmail", "browser/navigation"])

Returns:
    Root CategoryNode with children representing the hierarchy

#### `get_all_parent_paths`

```python
def get_all_parent_paths(category_path: str) -> List[str]
```

Get all parent paths for a category.

Args:
    category_path: Full category path (e.g., "google/gmail/send")

Returns:
    List of parent paths ["google", "google/gmail"]

#### `get_category_color`

```python
def get_category_color(category_path: str) -> QColor
```

Get color for a category, with distinct shades for subcategories.

Subcategories get progressively lighter shades of their parent's color.
Each depth level lightens by ~15%.

Args:
    category_path: Full category path (e.g., "google/gmail/send")

Returns:
    QColor for the category

#### `get_category_color_with_alpha`

```python
def get_category_color_with_alpha(category_path: str, alpha: int = 180) -> QColor
```

Get category color with transparency for child nodes.

Args:
    category_path: Full category path
    alpha: Alpha value (0-255)

Returns:
    QColor with alpha applied

#### `get_category_sort_key`

```python
def get_category_sort_key(category_path: str) -> Tuple[int, str]
```

Get sort key for a category path.

Sorts by:
1. Root category order (from CATEGORY_ORDER)
2. Alphabetically within same root

Args:
    category_path: Full category path

Returns:
    Tuple for sorting (order_index, path)

#### `get_display_name`

```python
def get_display_name(category_path: str) -> str
```

Get the display name for a category path.

Uses leaf name lookup, falling back to title case.

Args:
    category_path: Full category path (e.g., "google/gmail/send")

Returns:
    Human-readable display name (e.g., "Send")

#### `get_full_display_path`

```python
def get_full_display_path(category_path: str, separator: str = ' > ') -> str
```

Get full display path with all levels.

Args:
    category_path: Full category path (e.g., "google/gmail/send")
    separator: String to join parts

Returns:
    Full display path (e.g., "Google Workspace > Gmail > Send")

#### `normalize_category`

```python
def normalize_category(category_path: str) -> str
```

Normalize category path, applying aliases.

Args:
    category_path: Category path (possibly using old names)

Returns:
    Normalized path using new names

#### `update_category_counts`

```python
def update_category_counts(tree: CategoryNode, category_node_counts: Dict[str, int]) -> None
```

Update node counts in the category tree.

Args:
    tree: Root of category tree
    category_node_counts: Dict mapping category path -> number of nodes


### CategoryNode

**Decorators:** `@dataclass`


Node in a category tree structure.


**Attributes:**

- `children: Dict[str, 'CategoryNode']`
- `name: str`
- `node_count: int`
- `path: str`
- `total_count: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `add_child(name, path)` | `'CategoryNode'` | Add or get a child category node. |
| `get_all_paths()` | `List[str]` | Get all paths in this subtree (including self). |
| `has_nodes()` | `bool` | Check if this category or any descendant has nodes. |

#### Method Details

##### `add_child`

```python
def add_child(name: str, path: str) -> 'CategoryNode'
```

Add or get a child category node.

**Parameters:**

- `name: str` *(required)*
- `path: str` *(required)*

##### `get_all_paths`

```python
def get_all_paths() -> List[str]
```

Get all paths in this subtree (including self).

##### `has_nodes`

```python
def has_nodes() -> bool
```

Check if this category or any descendant has nodes.

### CategoryPath

**Decorators:** `@dataclass`


Immutable representation of a hierarchical category path.

Examples:
    CategoryPath.parse("google/gmail/send")
    -> CategoryPath(parts=["google", "gmail", "send"])

    CategoryPath.parse("basic")
    -> CategoryPath(parts=["basic"])


**Attributes:**

- `parts: Tuple[str, ...]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__bool__()` | `bool` | Check if path is non-empty. |
| `__str__()` | `str` | Convert back to path string. |
| `depth()` | `int` | Get the nesting depth (1 = top-level). |
| `is_ancestor_of(other)` | `bool` | Check if this path is an ancestor of another. |
| `is_descendant_of(other)` | `bool` | Check if this path is a descendant of another. |
| `leaf()` | `str` | Get the leaf (deepest) category. |
| `parent()` | `Optional['CategoryPath']` | Get parent path, or None if root. |
| `parent_path()` | `str` | Get parent as string path. |
| `parse(path)` | `'CategoryPath'` | Parse a category path string into parts. |
| `root()` | `str` | Get the root (top-level) category. |

#### Method Details

##### `__bool__`

```python
def __bool__() -> bool
```

Check if path is non-empty.

##### `__str__`

```python
def __str__() -> str
```

Convert back to path string.

##### `depth`

```python
@property
def depth() -> int
```

Get the nesting depth (1 = top-level).

##### `is_ancestor_of`

```python
def is_ancestor_of(other: 'CategoryPath') -> bool
```

Check if this path is an ancestor of another.

**Parameters:**

- `other: 'CategoryPath'` *(required)*

##### `is_descendant_of`

```python
def is_descendant_of(other: 'CategoryPath') -> bool
```

Check if this path is a descendant of another.

**Parameters:**

- `other: 'CategoryPath'` *(required)*

##### `leaf`

```python
@property
def leaf() -> str
```

Get the leaf (deepest) category.

##### `parent`

```python
@property
def parent() -> Optional['CategoryPath']
```

Get parent path, or None if root.

##### `parent_path`

```python
@property
def parent_path() -> str
```

Get parent as string path.

##### `parse`

```python
@classmethod
def parse(path: str) -> 'CategoryPath'
```

Parse a category path string into parts.

**Parameters:**

- `path: str` *(required)*

##### `root`

```python
@property
def root() -> str
```

Get the root (top-level) category.

---

## casare_rpa.presentation.canvas.graph.collapse_components

**File:** `src\casare_rpa\presentation\canvas\graph\collapse_components.py`


Collapse Components for NodeFrame

Contains UI components related to frame collapse/expand functionality:
- CollapseButton: Clickable button to toggle collapse state
- ExposedPortIndicator: Visual indicator for external port connections

Following Single Responsibility Principle - these components handle ONLY
collapse-related UI elements.


### CollapseButton

**Inherits from:** `QGraphicsRectItem`


A clickable button to collapse/expand a frame.

Visual design:
- Rounded square button in frame header
- Shows "-" when expanded (click to collapse)
- Shows "+" when collapsed (click to expand)
- Hover highlight for better UX


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - | Initialize collapse button. |
| `hoverEnterEvent(event)` | - | Handle hover enter. |
| `hoverLeaveEvent(event)` | - | Handle hover leave. |
| `mousePressEvent(event)` | - | Handle click to toggle collapse. |
| `paint(painter, option, widget)` | - | Paint the collapse button. |

#### Method Details

##### `__init__`

```python
def __init__(parent: 'NodeFrame')
```

Initialize collapse button.

Args:
    parent: Parent NodeFrame

**Parameters:**

- `parent: 'NodeFrame'` *(required)*

##### `hoverEnterEvent`

```python
def hoverEnterEvent(event)
```

Handle hover enter.

**Parameters:**

- `event` *(required)*

##### `hoverLeaveEvent`

```python
def hoverLeaveEvent(event)
```

Handle hover leave.

**Parameters:**

- `event` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event)
```

Handle click to toggle collapse.

**Parameters:**

- `event` *(required)*

##### `paint`

```python
def paint(painter: QPainter, option, widget = None)
```

Paint the collapse button.

**Parameters:**

- `painter: QPainter` *(required)*
- `option` *(required)*
- `widget = None`

### ExposedPortIndicator

**Inherits from:** `QGraphicsEllipseItem`


Visual indicator for exposed ports on collapsed frames.

Shows which ports are connected externally when frame is collapsed.
Color-coded by port type for consistency with the type system.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(port_name, is_output, color, ...)` | - | Initialize exposed port indicator. |

#### Method Details

##### `__init__`

```python
def __init__(port_name: str, is_output: bool, color: QColor, parent: QGraphicsItem)
```

Initialize exposed port indicator.

Args:
    port_name: Name of the port
    is_output: True if output port, False if input
    color: Port type color
    parent: Parent graphics item

**Parameters:**

- `port_name: str` *(required)*
- `is_output: bool` *(required)*
- `color: QColor` *(required)*
- `parent: QGraphicsItem` *(required)*

### ExposedPortManager


Manages exposed port indicators for a NodeFrame.

Responsible for:
- Creating indicators for external connections
- Positioning indicators on frame edges
- Clearing indicators on expand


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(frame)` | - | Initialize port manager. |
| `clear()` | `None` | Remove all exposed port indicators. |
| `create_exposed_ports()` | `None` | Create indicators for ports connected to nodes outside this ... |
| `indicators()` | `list[ExposedPortIndicator]` | Get list of current indicators. |

#### Method Details

##### `__init__`

```python
def __init__(frame: 'NodeFrame')
```

Initialize port manager.

Args:
    frame: Parent NodeFrame

**Parameters:**

- `frame: 'NodeFrame'` *(required)*

##### `clear`

```python
def clear() -> None
```

Remove all exposed port indicators.

##### `create_exposed_ports`

```python
def create_exposed_ports() -> None
```

Create indicators for ports connected to nodes outside this frame.

##### `indicators`

```python
@property
def indicators() -> list[ExposedPortIndicator]
```

Get list of current indicators.

---

## casare_rpa.presentation.canvas.graph.composite_node_creator

**File:** `src\casare_rpa\presentation\canvas\graph\composite_node_creator.py`


Composite Node Creator for CasareRPA Canvas.

Handles creation of composite nodes that spawn multiple paired nodes:
- For Loop (Start + End)
- While Loop (Start + End)
- Try/Catch/Finally (3 nodes)

Follows Single Responsibility Principle - handles composite node creation only.


### CompositeNodeCreator

**Inherits from:** `QObject`


Creates composite nodes that consist of multiple paired nodes.

Handles the creation of:
- For Loop: Creates ForLoopStart + ForLoopEnd with automatic pairing
- While Loop: Creates WhileLoopStart + WhileLoopEnd with automatic pairing
- Try/Catch/Finally: Creates 3 nodes with automatic pairing

Usage:
    creator = CompositeNodeCreator(graph)
    creator.handle_composite_node(composite_marker_node)


**Attributes:**

- `HORIZONTAL_SPACING: int`
- `TRY_CATCH_SPACING: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | `None` | Initialize composite node creator. |
| `create_for_loop_pair(x, y)` | `Optional[Tuple]` | Create a For Loop Start + End pair at the given position. |
| `create_try_catch_finally(x, y)` | `Optional[Tuple]` | Create a Try/Catch/Finally block with three nodes side-by-si... |
| `create_while_loop_pair(x, y)` | `Optional[Tuple]` | Create a While Loop Start + End pair at the given position. |
| `graph()` | `'NodeGraph'` | Get the underlying graph. |
| `handle_composite_node(composite_node)` | `None` | Handle creation of composite nodes (e.g., For Loop creates S... |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', parent: Optional[QObject] = None) -> None
```

Initialize composite node creator.

Args:
    graph: The NodeGraphQt NodeGraph instance
    parent: Optional parent QObject

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `parent: Optional[QObject] = None`

##### `create_for_loop_pair`

```python
def create_for_loop_pair(x: float, y: float) -> Optional[Tuple]
```

Create a For Loop Start + End pair at the given position.

Layout: Side-by-side with large spacing for workflow nodes
    ForLoopStart (x, y) -------- ForLoopEnd (x + 600, y)

Args:
    x: X position for the start node
    y: Y position for the start node

Returns:
    Tuple of (start_node, end_node) or None if creation failed

**Parameters:**

- `x: float` *(required)*
- `y: float` *(required)*

##### `create_try_catch_finally`

```python
def create_try_catch_finally(x: float, y: float) -> Optional[Tuple]
```

Create a Try/Catch/Finally block with three nodes side-by-side.

Layout: Side-by-side with large spacing for workflow nodes
    Try (x, y) -------- Catch (x + 450, y) -------- Finally (x + 900, y)

IDs are automatically paired - no user configuration needed.

Args:
    x: X position for the Try node
    y: Y position for the Try node

Returns:
    Tuple of (try_node, catch_node, finally_node) or None if creation failed

**Parameters:**

- `x: float` *(required)*
- `y: float` *(required)*

##### `create_while_loop_pair`

```python
def create_while_loop_pair(x: float, y: float) -> Optional[Tuple]
```

Create a While Loop Start + End pair at the given position.

Layout: Side-by-side with large spacing for workflow nodes
    WhileLoopStart (x, y) -------- WhileLoopEnd (x + 600, y)

Args:
    x: X position for the start node
    y: Y position for the start node

Returns:
    Tuple of (start_node, end_node) or None if creation failed

**Parameters:**

- `x: float` *(required)*
- `y: float` *(required)*

##### `graph`

```python
@property
def graph() -> 'NodeGraph'
```

Get the underlying graph.

##### `handle_composite_node`

```python
def handle_composite_node(composite_node) -> None
```

Handle creation of composite nodes (e.g., For Loop creates Start + End).

Replaces the marker composite node with the actual nodes it represents,
connects them together, and sets up pairing.

Args:
    composite_node: The composite marker node that was created

**Parameters:**

- `composite_node` *(required)*

---

## casare_rpa.presentation.canvas.graph.custom_node_item

**File:** `src\casare_rpa\presentation\canvas\graph\custom_node_item.py`


Custom node graphics item for CasareRPA.

Provides custom styling including:
- Bright yellow border on selection
- Animated running state indicator
- Completion checkmark
- Icon display

Now uses centralized AnimationCoordinator for performance with many nodes.

References:
- "Designing Data-Intensive Applications" - Resource pooling


### AnimationCoordinator


Singleton coordinator for all node animations.

Instead of each node having its own timer, this coordinator uses a
single timer to drive all animated nodes. This significantly reduces
CPU usage when many nodes are running simultaneously.

Usage:
    coordinator = AnimationCoordinator.get_instance()
    coordinator.register(node_item)  # Start animating
    coordinator.unregister(node_item)  # Stop animating


**Attributes:**

- `_instance: Optional['AnimationCoordinator']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - | Initialize the animation coordinator. |
| `animated_count()` | `int` | Get the number of currently animated nodes. |
| `get_instance()` | `'AnimationCoordinator'` | Get the singleton instance. |
| `is_running()` | `bool` | Check if the animation timer is running. |
| `register(node)` | `None` | Start animating a node. |
| `unregister(node)` | `None` | Stop animating a node. |

#### Method Details

##### `__init__`

```python
def __init__()
```

Initialize the animation coordinator.

##### `animated_count`

```python
@property
def animated_count() -> int
```

Get the number of currently animated nodes.

##### `get_instance`

```python
@classmethod
def get_instance() -> 'AnimationCoordinator'
```

Get the singleton instance.

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if the animation timer is running.

##### `register`

```python
def register(node: 'CasareNodeItem') -> None
```

Start animating a node.

Args:
    node: The CasareNodeItem to animate

**Parameters:**

- `node: 'CasareNodeItem'` *(required)*

##### `unregister`

```python
def unregister(node: 'CasareNodeItem') -> None
```

Stop animating a node.

Args:
    node: The CasareNodeItem to stop animating

**Parameters:**

- `node: 'CasareNodeItem'` *(required)*

### CasareNodeItem

**Inherits from:** `NodeItem`


Custom node item with enhanced visual feedback.

Features:
- Yellow border on selection
- Animated dotted border when running
- Checkmark overlay when completed
- Error icon when failed
- Execution time badge
- Icon display


**Attributes:**

- `BADGE_AREA_HEIGHT: int`
- `_time_font: Optional[QFont]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(name, parent)` | - |  |
| `borderColor()` | - | Get current border color based on state. |
| `boundingRect()` | `QRectF` | Override bounding rect to include space above for execution ... |
| `clear_execution_state()` | - | Reset all execution state for workflow restart. |
| `clear_robot_override()` | - | Clear robot override state for this node. |
| `get_robot_override_tooltip()` | `Optional[str]` | Get tooltip text for robot override indicator. |
| `get_time_font()` | `QFont` | Get cached font for execution time display. |
| `paint(painter, option, widget)` | - | Custom paint method for the node. |
| `setBorderColor(r, g, b, ...)` | - | Set normal border color. |
| `set_completed(completed)` | - | Set node completed state. |
| `set_error(has_error)` | - | Set node error state. |
| `set_execution_time(time_seconds)` | - | Set execution time to display. |
| `set_icon(pixmap)` | - | Set custom node icon. |
| `set_robot_override(has_override, is_capability_based)` | `None` | Set robot override state for this node. |
| `set_running(running)` | - | Set node running state. |

#### Method Details

##### `__init__`

```python
def __init__(name = 'node', parent = None)
```

**Parameters:**

- `name = 'node'`
- `parent = None`

##### `borderColor`

```python
def borderColor()
```

Get current border color based on state.

##### `boundingRect`

```python
def boundingRect() -> QRectF
```

Override bounding rect to include space above for execution time badge.

##### `clear_execution_state`

```python
def clear_execution_state()
```

Reset all execution state for workflow restart.

Note: Robot override state is NOT cleared here as it's configuration,
not execution state. Override persists across workflow runs.

##### `clear_robot_override`

```python
def clear_robot_override()
```

Clear robot override state for this node.

##### `get_robot_override_tooltip`

```python
def get_robot_override_tooltip() -> Optional[str]
```

Get tooltip text for robot override indicator.

Returns:
    Tooltip text if override exists, None otherwise

##### `get_time_font`

```python
@classmethod
def get_time_font() -> QFont
```

Get cached font for execution time display.

##### `paint`

```python
def paint(painter, option, widget)
```

Custom paint method for the node.

**Parameters:**

- `painter` *(required)*
- `option` *(required)*
- `widget` *(required)*

##### `setBorderColor`

```python
def setBorderColor(r, g, b, a = 255)
```

Set normal border color.

**Parameters:**

- `r` *(required)*
- `g` *(required)*
- `b` *(required)*
- `a = 255`

##### `set_completed`

```python
def set_completed(completed: bool)
```

Set node completed state.

**Parameters:**

- `completed: bool` *(required)*

##### `set_error`

```python
def set_error(has_error: bool)
```

Set node error state.

**Parameters:**

- `has_error: bool` *(required)*

##### `set_execution_time`

```python
def set_execution_time(time_seconds: Optional[float])
```

Set execution time to display.

Args:
    time_seconds: Execution time in seconds, or None to clear

**Parameters:**

- `time_seconds: Optional[float]` *(required)*

##### `set_icon`

```python
def set_icon(pixmap: QPixmap)
```

Set custom node icon.

**Parameters:**

- `pixmap: QPixmap` *(required)*

##### `set_robot_override`

```python
def set_robot_override(has_override: bool, is_capability_based: bool = False) -> None
```

Set robot override state for this node.

Args:
    has_override: Whether this node has a robot override
    is_capability_based: True if override is capability-based, False if specific robot

**Parameters:**

- `has_override: bool` *(required)*
- `is_capability_based: bool = False`

##### `set_running`

```python
def set_running(running: bool)
```

Set node running state.

Uses centralized AnimationCoordinator for efficient animation.

Args:
    running: True to show running animation, False to stop

**Parameters:**

- `running: bool` *(required)*

---

## casare_rpa.presentation.canvas.graph.custom_pipe

**File:** `src\casare_rpa\presentation\canvas\graph\custom_pipe.py`


Custom pipe styling for node connections.

Provides:
- Dotted line style when dragging connections
- Connection labels showing data type
- Output preview on hover


### Functions

#### `get_show_connection_labels`

```python
def get_show_connection_labels() -> bool
```

Check if connection labels are enabled.

#### `set_show_connection_labels`

```python
def set_show_connection_labels(show: bool) -> None
```

Enable or disable connection labels globally.


### CasarePipe

**Inherits from:** `PipeItem`


Custom pipe with:
- Dotted style when being dragged
- Optional data type label on the connection
- Output preview on hover
- Insert highlight when node is dragged over


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - | Initialize custom pipe. |
| `hoverEnterEvent(event)` | `None` | Handle hover enter. |
| `hoverLeaveEvent(event)` | `None` | Handle hover leave. |
| `is_insert_highlighted()` | `bool` | Check if pipe is currently insert-highlighted. |
| `paint(painter, option, widget)` | - | Paint the pipe with custom styling. |
| `set_insert_highlight(highlight)` | `None` | Set insert highlight state (when node is dragged over this p... |
| `set_label(text)` | `None` | Set the connection label text. |
| `set_output_value(value)` | `None` | Set the output value for preview. |
| `set_show_label(show)` | `None` | Enable or disable label display. |

#### Method Details

##### `__init__`

```python
def __init__()
```

Initialize custom pipe.

##### `hoverEnterEvent`

```python
def hoverEnterEvent(event) -> None
```

Handle hover enter.

**Parameters:**

- `event` *(required)*

##### `hoverLeaveEvent`

```python
def hoverLeaveEvent(event) -> None
```

Handle hover leave.

**Parameters:**

- `event` *(required)*

##### `is_insert_highlighted`

```python
def is_insert_highlighted() -> bool
```

Check if pipe is currently insert-highlighted.

##### `paint`

```python
def paint(painter, option, widget)
```

Paint the pipe with custom styling.

**Parameters:**

- `painter` *(required)*
- `option` *(required)*
- `widget` *(required)*

##### `set_insert_highlight`

```python
def set_insert_highlight(highlight: bool) -> None
```

Set insert highlight state (when node is dragged over this pipe).

**Parameters:**

- `highlight: bool` *(required)*

##### `set_label`

```python
def set_label(text: str) -> None
```

Set the connection label text.

**Parameters:**

- `text: str` *(required)*

##### `set_output_value`

```python
def set_output_value(value) -> None
```

Set the output value for preview.

**Parameters:**

- `value` *(required)*

##### `set_show_label`

```python
def set_show_label(show: bool) -> None
```

Enable or disable label display.

**Parameters:**

- `show: bool` *(required)*

---

## casare_rpa.presentation.canvas.graph.event_filters

**File:** `src\casare_rpa\presentation\canvas\graph\event_filters.py`


Event filters for CasareRPA Canvas.

Contains Qt event filters used by NodeGraphWidget for handling
various mouse and keyboard interactions.

Follows Single Responsibility Principle - each filter handles one interaction type.


### ConnectionDropFilter

**Inherits from:** `QObject`


Event filter to detect when a connection pipe is dropped on empty space.

Shows a node search menu to create and auto-connect a new node.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, widget)` | - |  |
| `eventFilter(obj, event)` | - |  |

#### Method Details

##### `__init__`

```python
def __init__(graph, widget)
```

**Parameters:**

- `graph` *(required)*
- `widget` *(required)*

##### `eventFilter`

```python
def eventFilter(obj, event)
```

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

### OutputPortMMBFilter

**Inherits from:** `QObject`


Event filter to detect middle mouse button clicks on output ports.

Creates a SetVariable node connected to the clicked output port.
Excludes exec ports (exec_in, exec_out, etc.)

Behavior:
    - LMB: Normal behavior (drag connection)
    - MMB on output port: Create SetVariable node


**Attributes:**

- `EXEC_PORT_NAMES: set`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, widget)` | - |  |
| `eventFilter(obj, event)` | - | Handle middle mouse button click to create SetVariable node. |

#### Method Details

##### `__init__`

```python
def __init__(graph, widget)
```

**Parameters:**

- `graph` *(required)*
- `widget` *(required)*

##### `eventFilter`

```python
def eventFilter(obj, event)
```

Handle middle mouse button click to create SetVariable node.

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

### TooltipBlocker

**Inherits from:** `QObject`


Event filter to block tooltips on the graph canvas.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `eventFilter(obj, event)` | - |  |

#### Method Details

##### `eventFilter`

```python
def eventFilter(obj, event)
```

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

---

## casare_rpa.presentation.canvas.graph.frame_factory

**File:** `src\casare_rpa\presentation\canvas\graph\frame_factory.py`


Frame Factory

Factory functions for creating and managing NodeFrames.
Also contains NodeGraphQt-compatible FrameNode class.

Separates creation logic from core frame implementation.


### Functions

#### `add_frame_menu_actions`

```python
def add_frame_menu_actions(graph_menu)
```

Add frame-related actions to the graph context menu.

Args:
    graph_menu: Context menu to add actions to

#### `create_frame`

```python
def create_frame(graph_view, title: str = 'Group', color_name: str = 'blue', position: Tuple[float, float] = (0, 0), size: Tuple[float, float] = (400, 300), graph = None) -> 'NodeFrame'
```

Create a node frame in the graph view.

Args:
    graph_view: NodeGraph view to add frame to
    title: Frame title
    color_name: Color theme name from FRAME_COLORS
    position: (x, y) position tuple
    size: (width, height) size tuple
    graph: NodeGraph instance for node lookup (optional)

Returns:
    Created NodeFrame instance

#### `group_selected_nodes`

```python
def group_selected_nodes(graph_view, title: str = 'Group', selected_nodes: List = None) -> Optional['NodeFrame']
```

Create a frame around currently selected nodes.

Args:
    graph_view: NodeGraph viewer
    title: Frame title
    selected_nodes: List of selected nodes (if None, will be fetched)

Returns:
    Created frame or None if no nodes selected


### FrameNode

**Inherits from:** `NodeObject`


NodeGraphQt-compatible frame node for grouping.


**Attributes:**

- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_frame_rect()` | `QRectF` | Get the frame's bounding rectangle. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_frame_rect`

```python
def get_frame_rect() -> QRectF
```

Get the frame's bounding rectangle.

---

## casare_rpa.presentation.canvas.graph.frame_managers

**File:** `src\casare_rpa\presentation\canvas\graph\frame_managers.py`


Frame Managers

Contains management components for NodeFrame:
- FrameBoundsManager: Centralized timer for bounds checking
- FrameDeletedCmd: Undo command for frame deletion

Following Single Responsibility Principle - separating manager concerns
from the frame UI component.


### FrameBoundsManager

**Inherits from:** `QObject`


Centralized manager for all frame bounds checking.

Instead of each frame having its own 100ms timer, this manager uses
a single timer to check all frames. This significantly reduces CPU
usage when there are many frames.

Usage:
    manager = FrameBoundsManager.get_instance()
    manager.register_frame(frame)
    manager.unregister_frame(frame)


**Attributes:**

- `_instance: Optional['FrameBoundsManager']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - | Initialize the bounds manager. |
| `frame_count()` | `int` | Get the number of registered frames. |
| `get_instance()` | `'FrameBoundsManager'` | Get the singleton instance. |
| `is_running()` | `bool` | Check if the timer is running. |
| `register_frame(frame)` | `None` | Register a frame for bounds checking. |
| `reset_instance()` | `None` | Reset the singleton instance (for testing). |
| `unregister_frame(frame)` | `None` | Unregister a frame from bounds checking. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QObject] = None)
```

Initialize the bounds manager.

**Parameters:**

- `parent: Optional[QObject] = None`

##### `frame_count`

```python
@property
def frame_count() -> int
```

Get the number of registered frames.

##### `get_instance`

```python
@classmethod
def get_instance() -> 'FrameBoundsManager'
```

Get the singleton instance.

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if the timer is running.

##### `register_frame`

```python
def register_frame(frame: 'NodeFrame') -> None
```

Register a frame for bounds checking.

**Parameters:**

- `frame: 'NodeFrame'` *(required)*

##### `reset_instance`

```python
@classmethod
def reset_instance() -> None
```

Reset the singleton instance (for testing).

##### `unregister_frame`

```python
def unregister_frame(frame: 'NodeFrame') -> None
```

Unregister a frame from bounds checking.

**Parameters:**

- `frame: 'NodeFrame'` *(required)*

### FrameDeletedCmd

**Inherits from:** `QUndoCommand`


Undo command for frame deletion.

Stores all frame state to allow restoring the frame on undo.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(frame, scene, description)` | - |  |
| `redo()` | - | Delete the frame again. |
| `undo()` | - | Restore the deleted frame. |

#### Method Details

##### `__init__`

```python
def __init__(frame: 'NodeFrame', scene, description: str = 'Delete Frame')
```

**Parameters:**

- `frame: 'NodeFrame'` *(required)*
- `scene` *(required)*
- `description: str = 'Delete Frame'`

##### `redo`

```python
def redo()
```

Delete the frame again.

##### `undo`

```python
def undo()
```

Restore the deleted frame.

---

## casare_rpa.presentation.canvas.graph.frame_renderer

**File:** `src\casare_rpa\presentation\canvas\graph\frame_renderer.py`


Frame Renderer

Handles all painting/rendering logic for NodeFrame.
Separates rendering concerns from state management and user interaction.

Following Single Responsibility Principle - this module handles ONLY
visual rendering of frames.


### FrameRenderer


Renders NodeFrame visuals.

Responsible for:
- Drawing frame background and border
- Selection highlight
- Drop target highlight
- Collapsed state appearance
- Node count indicator


**Attributes:**

- `CORNER_RADIUS: int`
- `NODE_COUNT_FONT_FAMILY: str`
- `NODE_COUNT_FONT_SIZE: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(frame)` | - | Initialize renderer. |
| `paint(painter, option, widget)` | `None` | Paint the frame. |

#### Method Details

##### `__init__`

```python
def __init__(frame: 'NodeFrame')
```

Initialize renderer.

Args:
    frame: NodeFrame to render

**Parameters:**

- `frame: 'NodeFrame'` *(required)*

##### `paint`

```python
def paint(painter: QPainter, option, widget = None) -> None
```

Paint the frame.

Handles all visual states:
- Normal state
- Selected state
- Drop target state
- Collapsed state

Args:
    painter: QPainter to draw with
    option: Style options (unused)
    widget: Widget being painted on (unused)

**Parameters:**

- `painter: QPainter` *(required)*
- `option` *(required)*
- `widget = None`

### TitleRenderer


Renders and manages frame title label.

Responsible for:
- Title text rendering
- Font scaling based on frame size
- Title positioning


**Attributes:**

- `BASE_FONT_SIZE: int`
- `BASE_WIDTH: int`
- `FONT_FAMILY: str`
- `LEFT_MARGIN: int`
- `MAX_FONT_SIZE: int`
- `MIN_FONT_SIZE: int`
- `RIGHT_MARGIN: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_font_size(frame_width)` | `int` | Calculate appropriate font size based on frame width. |
| `create_font(frame_width)` | `QFont` | Create font for title based on frame width. |
| `get_available_width(frame_width)` | `float` | Calculate available width for title text. |

#### Method Details

##### `calculate_font_size`

```python
@classmethod
def calculate_font_size(frame_width: float) -> int
```

Calculate appropriate font size based on frame width.

Args:
    frame_width: Width of the frame

Returns:
    Font size in points

**Parameters:**

- `frame_width: float` *(required)*

##### `create_font`

```python
@classmethod
def create_font(frame_width: float) -> QFont
```

Create font for title based on frame width.

Args:
    frame_width: Width of the frame

Returns:
    QFont sized appropriately

**Parameters:**

- `frame_width: float` *(required)*

##### `get_available_width`

```python
@classmethod
def get_available_width(frame_width: float) -> float
```

Calculate available width for title text.

Args:
    frame_width: Width of the frame

Returns:
    Available width for title

**Parameters:**

- `frame_width: float` *(required)*

---

## casare_rpa.presentation.canvas.graph.minimap

**File:** `src\casare_rpa\presentation\canvas\graph\minimap.py`


Minimap widget for the node graph.

Provides a bird's-eye view of the entire node graph with viewport indicator.
Overlays on the bottom-left corner of the canvas.

Now uses event-driven updates for better performance with large workflows.

References:
- "Designing Data-Intensive Applications" by Kleppmann - Event Sourcing


### Minimap

**Inherits from:** `QWidget`


Minimap widget showing overview of node graph.

Displays nodes as colored rectangles and shows current viewport.
Clicking on minimap navigates the main view.

Now uses event-driven updates for better performance:
- Connects to node_created/nodes_deleted signals
- Only updates when viewport or nodes change
- Reduced timer interval (200ms instead of 100ms)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(node_graph, parent)` | - | Initialize minimap. |
| `get_stats()` | `dict` | Get update statistics. |
| `mark_dirty()` | `None` | Manually mark minimap as needing update. |
| `set_update_interval(interval_ms)` | - | Set minimap update interval. |
| `set_visible(visible)` | - | Show or hide minimap. |

#### Method Details

##### `__init__`

```python
def __init__(node_graph: NodeGraph, parent: Optional[QWidget] = None)
```

Initialize minimap.

Args:
    node_graph: NodeGraph instance to display
    parent: Parent widget

**Parameters:**

- `node_graph: NodeGraph` *(required)*
- `parent: Optional[QWidget] = None`

##### `get_stats`

```python
def get_stats() -> dict
```

Get update statistics.

##### `mark_dirty`

```python
def mark_dirty() -> None
```

Manually mark minimap as needing update.

##### `set_update_interval`

```python
def set_update_interval(interval_ms: int)
```

Set minimap update interval.

Args:
    interval_ms: Update interval in milliseconds

**Parameters:**

- `interval_ms: int` *(required)*

##### `set_visible`

```python
def set_visible(visible: bool)
```

Show or hide minimap.

Args:
    visible: True to show, False to hide

**Parameters:**

- `visible: bool` *(required)*

### MinimapChangeTracker


Tracks changes to determine when minimap needs update.

Uses event sourcing pattern - only update when something changed.
This reduces CPU usage significantly for large workflows.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(viewport_tolerance)` | - | Initialize change tracker. |
| `commit_update(viewport, node_count)` | `None` | Mark current state as rendered. |
| `mark_dirty()` | `None` | Mark state as dirty - requires update. |
| `should_update(current_viewport, node_count)` | `bool` | Check if minimap needs redraw. |

#### Method Details

##### `__init__`

```python
def __init__(viewport_tolerance: float = 2.0)
```

Initialize change tracker.

Args:
    viewport_tolerance: Tolerance for viewport position changes

**Parameters:**

- `viewport_tolerance: float = 2.0`

##### `commit_update`

```python
def commit_update(viewport: QRectF, node_count: int) -> None
```

Mark current state as rendered.

Args:
    viewport: Current viewport rectangle
    node_count: Number of nodes

**Parameters:**

- `viewport: QRectF` *(required)*
- `node_count: int` *(required)*

##### `mark_dirty`

```python
def mark_dirty() -> None
```

Mark state as dirty - requires update.

##### `should_update`

```python
def should_update(current_viewport: QRectF, node_count: int) -> bool
```

Check if minimap needs redraw.

Args:
    current_viewport: Current viewport rectangle
    node_count: Number of nodes in the graph

Returns:
    True if update is needed

**Parameters:**

- `current_viewport: QRectF` *(required)*
- `node_count: int` *(required)*

### MinimapView

**Inherits from:** `QGraphicsView`


Custom QGraphicsView for minimap display.


**Attributes:**

- `viewport_clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - | Initialize minimap view. |
| `drawForeground(painter, rect)` | - | Draw minimap content. |
| `mouseMoveEvent(event)` | - | Handle mouse drag to navigate main view. |
| `mousePressEvent(event)` | - | Handle mouse press to navigate main view. |
| `mouseReleaseEvent(event)` | - | Handle mouse release. |
| `update_minimap(node_rects, viewport_rect, graph_bounds)` | - | Update minimap display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None)
```

Initialize minimap view.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `drawForeground`

```python
def drawForeground(painter, rect)
```

Draw minimap content.

**Parameters:**

- `painter` *(required)*
- `rect` *(required)*

##### `mouseMoveEvent`

```python
def mouseMoveEvent(event)
```

Handle mouse drag to navigate main view.

**Parameters:**

- `event` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event)
```

Handle mouse press to navigate main view.

**Parameters:**

- `event` *(required)*

##### `mouseReleaseEvent`

```python
def mouseReleaseEvent(event)
```

Handle mouse release.

**Parameters:**

- `event` *(required)*

##### `update_minimap`

```python
def update_minimap(node_rects, viewport_rect, graph_bounds)
```

Update minimap display.

Args:
    node_rects: List of (QRectF, QColor) for each node
    viewport_rect: QRectF of visible viewport in scene coords
    graph_bounds: QRectF of entire graph bounds

**Parameters:**

- `node_rects` *(required)*
- `viewport_rect` *(required)*
- `graph_bounds` *(required)*

---

## casare_rpa.presentation.canvas.graph.node_creation_helper

**File:** `src\casare_rpa\presentation\canvas\graph\node_creation_helper.py`


Node Creation Helper for CasareRPA Canvas.

Handles node creation operations including:
- Drag-and-drop node creation
- SetVariable node creation from port MMB click
- Auto-connect after node creation

Follows Single Responsibility Principle - handles node creation assistance only.


### NodeCreationHelper

**Inherits from:** `QObject`


Assists with node creation operations on the canvas.

Handles:
- Creating nodes from drag-drop
- Creating SetVariable nodes from port MMB click
- Auto-connecting newly created nodes

Usage:
    helper = NodeCreationHelper(graph)
    helper.create_set_variable_for_port(port_item)


**Attributes:**

- `DEFAULT_X_GAP: int`
- `DEFAULT_Y_OFFSET: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent, y_offset, ...)` | `None` | Initialize node creation helper. |
| `auto_connect_new_node(new_node, source_port_item)` | `bool` | Auto-connect a newly created node to the source port. |
| `create_node_at_position(node_type, identifier, position)` | `Optional[object]` | Create a node at the specified position from a drag-drop ope... |
| `create_set_variable_for_port(source_port_item)` | `Optional[object]` | Create a SetVariable node connected to the clicked output po... |
| `graph()` | `'NodeGraph'` | Get the underlying graph. |
| `x_gap()` | `float` | Get horizontal gap for SetVariable nodes. |
| `x_gap(value)` | `None` | Set horizontal gap for SetVariable nodes. |
| `y_offset()` | `float` | Get vertical offset for SetVariable nodes. |
| `y_offset(value)` | `None` | Set vertical offset for SetVariable nodes. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', parent: Optional[QObject] = None, y_offset: float = DEFAULT_Y_OFFSET, x_gap: float = DEFAULT_X_GAP) -> None
```

Initialize node creation helper.

Args:
    graph: The NodeGraphQt NodeGraph instance
    parent: Optional parent QObject
    y_offset: Vertical offset for SetVariable nodes
    x_gap: Horizontal gap for SetVariable nodes

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `parent: Optional[QObject] = None`
- `y_offset: float = DEFAULT_Y_OFFSET`
- `x_gap: float = DEFAULT_X_GAP`

##### `auto_connect_new_node`

```python
def auto_connect_new_node(new_node, source_port_item) -> bool
```

Auto-connect a newly created node to the source port.

Args:
    new_node: The newly created node
    source_port_item: The port item that was dragged from (PortItem from viewer)

Returns:
    True if connection was made, False otherwise

**Parameters:**

- `new_node` *(required)*
- `source_port_item` *(required)*

##### `create_node_at_position`

```python
def create_node_at_position(node_type: str, identifier: str, position: Tuple[float, float]) -> Optional[object]
```

Create a node at the specified position from a drag-drop operation.

Args:
    node_type: The node class name
    identifier: The node identifier prefix
    position: Tuple of (x, y) scene coordinates

Returns:
    The created node or None if creation failed

**Parameters:**

- `node_type: str` *(required)*
- `identifier: str` *(required)*
- `position: Tuple[float, float]` *(required)*

##### `create_set_variable_for_port`

```python
def create_set_variable_for_port(source_port_item) -> Optional[object]
```

Create a SetVariable node connected to the clicked output port.

Args:
    source_port_item: The output port item that was clicked (PortItem from viewer)

Returns:
    The created SetVariable node or None if creation failed

**Parameters:**

- `source_port_item` *(required)*

##### `graph`

```python
@property
def graph() -> 'NodeGraph'
```

Get the underlying graph.

##### `x_gap`

```python
@property
def x_gap() -> float
```

Get horizontal gap for SetVariable nodes.

##### `x_gap`

```python
@property
def x_gap(value: float) -> None
```

Set horizontal gap for SetVariable nodes.

**Parameters:**

- `value: float` *(required)*

##### `y_offset`

```python
@property
def y_offset() -> float
```

Get vertical offset for SetVariable nodes.

##### `y_offset`

```python
@property
def y_offset(value: float) -> None
```

Set vertical offset for SetVariable nodes.

**Parameters:**

- `value: float` *(required)*

---

## casare_rpa.presentation.canvas.graph.node_frame

**File:** `src\casare_rpa\presentation\canvas\graph\node_frame.py`


Node Frame/Group System

Allows users to create visual frames around groups of nodes for organization.

Rendering logic delegated to specialized renderer modules:
- style_manager.py: Color palettes and styling
- collapse_components.py: Collapse button and port indicators
- frame_renderer.py: Paint logic
- frame_managers.py: Bounds manager and undo commands
- frame_factory.py: Factory functions

References:
- "Designing Data-Intensive Applications" - Resource pooling


### NodeFrame

**Inherits from:** `QGraphicsRectItem`


A visual frame/backdrop for grouping nodes.

Features:
- Resizable colored rectangle
- Editable title label (double-click to edit)
- Multiple color themes
- Nodes can be grouped within the frame
- Collapsible to hide internal nodes


**Attributes:**

- `COLLAPSED_HEIGHT: int`
- `COLLAPSED_WIDTH: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, color, width, ...)` | - |  |
| `add_node(node)` | - | Add a node to this frame's group. |
| `collapse()` | `None` | Collapse the frame to hide internal nodes. |
| `contextMenuEvent(event)` | - | Show context menu with frame options. |
| `deserialize(data, node_map)` | `'NodeFrame'` | Create frame from serialized data. |
| `expand()` | `None` | Expand the frame to show internal nodes. |
| `hoverMoveEvent(event)` | - | Change cursor when hovering over resize corner. |
| `is_collapsed()` | `bool` | Check if frame is collapsed. |
| `itemChange(change, value)` | - | Handle item changes, particularly position changes. |
| `keyPressEvent(event)` | - | Handle key press events. |
| `mouseDoubleClickEvent(event)` | - | Handle double-click to edit title. |
| `mouseMoveEvent(event)` | - | Handle mouse move for resizing. |
| `mousePressEvent(event)` | - | Handle mouse press for movement or resizing. |
| `mouseReleaseEvent(event)` | - | Handle mouse release. |
| `paint(painter, option, widget)` | - | Delegate painting to the renderer. |
| `remove_node(node)` | - | Remove a node from this frame's group. |
| `serialize()` | `Dict[str, Any]` | Serialize frame to dictionary. |
| `set_color(color)` | - | Change the frame color. |
| `set_graph(graph)` | - | Set the graph reference for all frames to use for node looku... |
| `set_title(title)` | - | Update the frame title. |
| `toggle_collapse()` | `None` | Toggle between collapsed and expanded state. |

#### Method Details

##### `__init__`

```python
def __init__(title: str = 'Group', color: QColor = None, width: float = 400, height: float = 300, parent = None)
```

**Parameters:**

- `title: str = 'Group'`
- `color: QColor = None`
- `width: float = 400`
- `height: float = 300`
- `parent = None`

##### `add_node`

```python
def add_node(node)
```

Add a node to this frame's group.

**Parameters:**

- `node` *(required)*

##### `collapse`

```python
def collapse() -> None
```

Collapse the frame to hide internal nodes.

##### `contextMenuEvent`

```python
def contextMenuEvent(event)
```

Show context menu with frame options.

**Parameters:**

- `event` *(required)*

##### `deserialize`

```python
@classmethod
def deserialize(data: Dict[str, Any], node_map: Optional[Dict[str, Any]] = None) -> 'NodeFrame'
```

Create frame from serialized data.

**Parameters:**

- `data: Dict[str, Any]` *(required)*
- `node_map: Optional[Dict[str, Any]] = None`

##### `expand`

```python
def expand() -> None
```

Expand the frame to show internal nodes.

##### `hoverMoveEvent`

```python
def hoverMoveEvent(event)
```

Change cursor when hovering over resize corner.

**Parameters:**

- `event` *(required)*

##### `is_collapsed`

```python
@property
def is_collapsed() -> bool
```

Check if frame is collapsed.

##### `itemChange`

```python
def itemChange(change, value)
```

Handle item changes, particularly position changes.

**Parameters:**

- `change` *(required)*
- `value` *(required)*

##### `keyPressEvent`

```python
def keyPressEvent(event)
```

Handle key press events.

**Parameters:**

- `event` *(required)*

##### `mouseDoubleClickEvent`

```python
def mouseDoubleClickEvent(event)
```

Handle double-click to edit title.

**Parameters:**

- `event` *(required)*

##### `mouseMoveEvent`

```python
def mouseMoveEvent(event)
```

Handle mouse move for resizing.

**Parameters:**

- `event` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event)
```

Handle mouse press for movement or resizing.

**Parameters:**

- `event` *(required)*

##### `mouseReleaseEvent`

```python
def mouseReleaseEvent(event)
```

Handle mouse release.

**Parameters:**

- `event` *(required)*

##### `paint`

```python
def paint(painter: QPainter, option, widget = None)
```

Delegate painting to the renderer.

**Parameters:**

- `painter: QPainter` *(required)*
- `option` *(required)*
- `widget = None`

##### `remove_node`

```python
def remove_node(node)
```

Remove a node from this frame's group.

**Parameters:**

- `node` *(required)*

##### `serialize`

```python
def serialize() -> Dict[str, Any]
```

Serialize frame to dictionary.

##### `set_color`

```python
def set_color(color: QColor)
```

Change the frame color.

**Parameters:**

- `color: QColor` *(required)*

##### `set_graph`

```python
@classmethod
def set_graph(graph)
```

Set the graph reference for all frames to use for node lookup.

**Parameters:**

- `graph` *(required)*

##### `set_title`

```python
def set_title(title: str)
```

Update the frame title.

**Parameters:**

- `title: str` *(required)*

##### `toggle_collapse`

```python
def toggle_collapse() -> None
```

Toggle between collapsed and expanded state.

---

## casare_rpa.presentation.canvas.graph.node_graph_widget

**File:** `src\casare_rpa\presentation\canvas\graph\node_graph_widget.py`


Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.

The NodeGraphQt library has several bugs and limitations that are fixed
via wrapper classes in node_widgets.py. All fixes are applied at module
load time by calling apply_all_node_widget_fixes().


### NodeGraphWidget

**Inherits from:** `QWidget`


Widget wrapper for NodeGraphQt's NodeGraph.

Provides a Qt widget container for the node graph editor
with custom styling and configuration.

Now includes connection validation with strict type checking.


**Attributes:**

- `connection_blocked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the node graph widget. |
| `auto_connect()` | `AutoConnectManager` | Get the auto-connect manager. |
| `center_on_nodes()` | `None` | Center the view on all nodes. |
| `clear_graph()` | `None` | Clear all nodes and connections from the graph. |
| `clear_selection()` | `None` | Clear node selection. |
| `eventFilter(obj, event)` | - | Event filter to capture Tab key press and right-click for co... |
| `fit_to_selection()` | `None` | Fit the view to the selected nodes. |
| `get_selected_nodes()` | `list` | Get the currently selected nodes. |
| `graph()` | `NodeGraph` | Get the underlying NodeGraph instance. |
| `is_auto_connect_enabled()` | `bool` | Check if auto-connect is enabled. |
| `node_insert()` | `NodeInsertManager` | Get the node insert manager. |
| `quick_actions()` | `NodeQuickActions` | Get the quick actions manager. |
| `reset_zoom()` | `None` | Reset zoom to 100%. |
| `selection()` | `SelectionManager` | Get the selection manager. |
| `set_auto_connect_distance(distance)` | `None` | Set the maximum distance for auto-connect suggestions. |
| `set_auto_connect_enabled(enabled)` | `None` | Enable or disable the auto-connect feature. |
| `set_import_callback(callback)` | `None` | Set callback for importing workflow data. |
| `set_import_file_callback(callback)` | `None` | Set callback for importing workflow from file. |
| `setup_drag_drop()` | `None` | Enable drag and drop support for importing workflow JSON fil... |
| `zoom_in()` | `None` | Zoom in the graph view. |
| `zoom_out()` | `None` | Zoom out the graph view. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the node graph widget.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `auto_connect`

```python
@property
def auto_connect() -> AutoConnectManager
```

Get the auto-connect manager.

Returns:
    AutoConnectManager instance

##### `center_on_nodes`

```python
def center_on_nodes() -> None
```

Center the view on all nodes.

##### `clear_graph`

```python
def clear_graph() -> None
```

Clear all nodes and connections from the graph.

##### `clear_selection`

```python
def clear_selection() -> None
```

Clear node selection.

##### `eventFilter`

```python
def eventFilter(obj, event)
```

Event filter to capture Tab key press and right-click for context menu.

Args:
    obj: Object that received the event
    event: The event

Returns:
    True if event was handled, False otherwise

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `fit_to_selection`

```python
def fit_to_selection() -> None
```

Fit the view to the selected nodes.

##### `get_selected_nodes`

```python
def get_selected_nodes() -> list
```

Get the currently selected nodes.

Returns:
    List of selected node objects

##### `graph`

```python
@property
def graph() -> NodeGraph
```

Get the underlying NodeGraph instance.

Returns:
    NodeGraph instance

##### `is_auto_connect_enabled`

```python
def is_auto_connect_enabled() -> bool
```

Check if auto-connect is enabled.

Returns:
    True if auto-connect is enabled

##### `node_insert`

```python
@property
def node_insert() -> NodeInsertManager
```

Get the node insert manager.

Returns:
    NodeInsertManager instance

##### `quick_actions`

```python
@property
def quick_actions() -> NodeQuickActions
```

Get the quick actions manager.

Returns:
    NodeQuickActions instance

##### `reset_zoom`

```python
def reset_zoom() -> None
```

Reset zoom to 100%.

##### `selection`

```python
@property
def selection() -> SelectionManager
```

Get the selection manager.

Returns:
    SelectionManager instance

##### `set_auto_connect_distance`

```python
def set_auto_connect_distance(distance: float) -> None
```

Set the maximum distance for auto-connect suggestions.

Args:
    distance: Maximum distance in pixels

**Parameters:**

- `distance: float` *(required)*

##### `set_auto_connect_enabled`

```python
def set_auto_connect_enabled(enabled: bool) -> None
```

Enable or disable the auto-connect feature.

Args:
    enabled: Whether to enable auto-connect

**Parameters:**

- `enabled: bool` *(required)*

##### `set_import_callback`

```python
def set_import_callback(callback) -> None
```

Set callback for importing workflow data.

Args:
    callback: Function(data: dict, position: tuple) -> ImportResult

**Parameters:**

- `callback` *(required)*

##### `set_import_file_callback`

```python
def set_import_file_callback(callback) -> None
```

Set callback for importing workflow from file.

Args:
    callback: Function(file_path: str, position: tuple) -> None

**Parameters:**

- `callback` *(required)*

##### `setup_drag_drop`

```python
def setup_drag_drop() -> None
```

Enable drag and drop support for importing workflow JSON files.

Must be called after widget is initialized. Enables dropping
.json files directly onto the canvas to import nodes.

##### `zoom_in`

```python
def zoom_in() -> None
```

Zoom in the graph view.

##### `zoom_out`

```python
def zoom_out() -> None
```

Zoom out the graph view.

---

## casare_rpa.presentation.canvas.graph.node_icons

**File:** `src\casare_rpa\presentation\canvas\graph\node_icons.py`


Node Icon System

Professional icon generation for all CasareRPA node types using
Unicode symbols and custom drawing.


### Functions

#### `clear_icon_cache`

```python
def clear_icon_cache()
```

Clear both icon caches (pixmap and path).

#### `create_category_icon`

```python
def create_category_icon(category: str, size: int = 24) -> str
```

Create an icon representing a category.

Args:
    category: Category name
    size: Icon size in pixels

Returns:
    Path to saved icon PNG file

#### `create_node_icon`

```python
def create_node_icon(node_name: str, size: int = 24, custom_color: Optional[QColor] = None) -> str
```

Create a professional icon for a node type.

Args:
    node_name: Name of the node (e.g., "Click Element")
    size: Icon size in pixels
    custom_color: Override category color

Returns:
    Path to saved icon PNG file

#### `create_node_icon_pixmap`

```python
def create_node_icon_pixmap(node_name: str, size: int = 24, custom_color: Optional[QColor] = None) -> QPixmap
```

Create a professional icon for a node type and return QPixmap directly.
This is the optimized version that avoids file I/O.

Args:
    node_name: Name of the node (e.g., "Click Element")
    size: Icon size in pixels
    custom_color: Override category color

Returns:
    QPixmap containing the rendered icon

#### `get_all_node_icons`

```python
def get_all_node_icons() -> Dict[str, Tuple[str, str]]
```

Get all registered node icons.

Returns:
    Dictionary mapping node names to (symbol, category) tuples

#### `get_cached_node_icon`

```python
def get_cached_node_icon(node_name: str, size: int = 24) -> QPixmap
```

Get a cached node icon QPixmap or create it if not cached.
Uses in-memory QPixmap cache for lightning-fast rendering performance.

Args:
    node_name: Name of the node
    size: Icon size

Returns:
    QPixmap containing the icon

#### `get_cached_node_icon_path`

```python
def get_cached_node_icon_path(node_name: str, size: int = 24) -> str
```

Get a cached node icon file path or create it if not cached.
Uses file path cache for NodeGraphQt model.icon (required for JSON serialization).

This function generates the file only once per node type and caches the path,
avoiding repeated file I/O while still providing a serializable path.

Args:
    node_name: Name of the node
    size: Icon size

Returns:
    File path to the cached icon PNG

#### `get_node_color`

```python
def get_node_color(node_name: str) -> QColor
```

Get the category color for a node type.

Args:
    node_name: Name of the node

Returns:
    QColor for the node category

#### `register_custom_icon`

```python
def register_custom_icon(node_name: str, symbol: str, category: str)
```

Register a custom icon for a node type.

Args:
    node_name: Name of the node
    symbol: Unicode symbol to use
    category: Category name


---

## casare_rpa.presentation.canvas.graph.node_quick_actions

**File:** `src\casare_rpa\presentation\canvas\graph\node_quick_actions.py`


Node Quick Actions for CasareRPA.

Provides a context menu with quick actions when right-clicking on nodes.


### Functions

#### `setup_node_quick_actions`

```python
def setup_node_quick_actions(graph: 'NodeGraph') -> NodeQuickActions
```

Setup quick actions for a node graph.

Args:
    graph: The NodeGraph instance

Returns:
    NodeQuickActions manager instance


### NodeQuickActions

**Inherits from:** `QObject`


Manages quick actions context menu for nodes.

Provides common operations like run, duplicate, delete, copy
when right-clicking on nodes in the canvas.

Signals:
    run_node_requested: Emitted when user wants to run a node (node_id)
    run_to_node_requested: Emitted when user wants to run to a node (node_id)
    duplicate_requested: Emitted when user wants to duplicate nodes
    delete_requested: Emitted when user wants to delete nodes
    rename_requested: Emitted when user wants to rename a node (node_id)
    copy_requested: Emitted when user wants to copy nodes
    paste_requested: Emitted when user wants to paste nodes
    center_view_requested: Emitted when user wants to center on node (node_id)


**Attributes:**

- `center_view_requested: Signal`
- `copy_requested: Signal`
- `delete_requested: Signal`
- `duplicate_requested: Signal`
- `paste_requested: Signal`
- `rename_requested: Signal`
- `run_node_requested: Signal`
- `run_to_node_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | `None` | Initialize the quick actions manager. |
| `eventFilter(obj, event)` | `bool` | Event filter to intercept right-clicks on nodes. |
| `set_auto_connect_manager(manager)` | `None` | Set reference to AutoConnectManager for drag state checking. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', parent: Optional[QObject] = None) -> None
```

Initialize the quick actions manager.

Args:
    graph: The NodeGraph instance
    parent: Optional parent object

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `parent: Optional[QObject] = None`

##### `eventFilter`

```python
def eventFilter(obj, event) -> bool
```

Event filter to intercept right-clicks on nodes.

Args:
    obj: Object that received the event
    event: The event

Returns:
    True if event was handled, False otherwise

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `set_auto_connect_manager`

```python
def set_auto_connect_manager(manager) -> None
```

Set reference to AutoConnectManager for drag state checking.

Args:
    manager: The AutoConnectManager instance

**Parameters:**

- `manager` *(required)*

---

## casare_rpa.presentation.canvas.graph.node_registry

**File:** `src\casare_rpa\presentation\canvas\graph\node_registry.py`


Node registry and factory for creating and managing nodes.

This module provides the NodeRegistry for registering visual nodes
and the NodeFactory for creating node instances.

AUTO-DISCOVERY SYSTEM:
When adding new nodes, you only need to:
1. Create the CasareRPA node class in nodes/ directory
2. Create the visual node class in presentation/canvas/visual_nodes/ with CASARE_NODE_CLASS attribute
3. That's it! The mapping is built automatically.

The CASARE_NODE_CLASS attribute on visual nodes specifies the CasareRPA node class name.
For desktop nodes, set CASARE_NODE_MODULE = "desktop" to look up from desktop_nodes module.


### Functions

#### `clear_node_type_caches`

```python
def clear_node_type_caches() -> None
```

Clear all LRU caches for node type lookups.

Use this when the node registry is modified or during testing.

#### `create_node_from_type`

```python
def create_node_from_type(graph, node_type: str, node_id: Optional[str] = None, config: Optional[dict] = None, position: Optional[tuple] = None) -> Optional[Any]
```

Create a visual node with linked CasareRPA node from node type name.

This is the recommended way to create nodes programmatically.

Args:
    graph: NodeGraph instance
    node_type: Node type name (e.g., "MessageBoxNode")
    node_id: Optional specific node ID (auto-generated if not provided)
    config: Optional config dict for the CasareRPA node
    position: Optional (x, y) position tuple

Returns:
    Created visual node with linked CasareRPA node, or None on failure

Example:
    node = create_node_from_type(
        graph, "MessageBoxNode",
        config={"message": "Hello!"},
        position=(100, 200)
    )

#### `get_all_node_types`

```python
def get_all_node_types() -> List[str]
```

Get list of all registered node type names.

Returns:
    List of node type names (e.g., ["StartNode", "EndNode", "MessageBoxNode", ...])

#### `get_cache_stats`

```python
def get_cache_stats() -> Dict[str, Any]
```

Get statistics for all node type lookup caches.

Returns:
    Dictionary with cache info for each cached function

#### `get_casare_class_for_type`

```python
def get_casare_class_for_type(node_type: str) -> Optional[Type]
```

Get the CasareRPA node class for a node type name.

Uses LRU caching for performance (256 entries).

Args:
    node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

Returns:
    CasareRPA node class or None if not found

#### `get_casare_node_mapping`

```python
def get_casare_node_mapping() -> Dict[Type, Type]
```

Get the mapping from visual node classes to CasareRPA node classes.

The mapping is built lazily on first access using auto-discovery.

Returns:
    Dictionary mapping visual node classes to CasareRPA node classes

#### `get_identifier_for_type`

```python
def get_identifier_for_type(node_type: str) -> Optional[str]
```

Get the graph.create_node() identifier for a node type.

Uses LRU caching for performance (256 entries).

Args:
    node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

Returns:
    Identifier string for graph.create_node() or None if not found

Example:
    identifier = get_identifier_for_type("MessageBoxNode")
    node = graph.create_node(identifier)

#### `get_node_factory`

```python
def get_node_factory() -> NodeFactory
```

Get the global node factory instance.

Returns:
    NodeFactory instance

#### `get_node_registry`

```python
def get_node_registry() -> NodeRegistry
```

Get the global node registry instance.

Returns:
    NodeRegistry instance

#### `get_node_type_mapping`

```python
def get_node_type_mapping() -> Dict[str, tuple]
```

Get the unified mapping from node type names to classes.

This is the SINGLE SOURCE OF TRUTH for node lookups.
Use this instead of building your own mappings!

Returns:
    Dict mapping node_type (e.g., "MessageBoxNode") to tuple of:
    (visual_class, identifier_for_create_node, casare_class_or_None)

Example:
    mapping = get_node_type_mapping()
    visual_class, identifier, casare_class = mapping["MessageBoxNode"]
    node = graph.create_node(identifier)

#### `get_visual_class_for_type`

```python
def get_visual_class_for_type(node_type: str) -> Optional[Type]
```

Get the visual node class for a node type name.

Uses LRU caching for performance (256 entries).

Args:
    node_type: Node type name (e.g., "MessageBoxNode", "StartNode")

Returns:
    Visual node class or None if not found

#### `is_valid_node_type`

```python
def is_valid_node_type(node_type: str) -> bool
```

Check if a node type name is valid/registered.

Args:
    node_type: Node type name to check

Returns:
    True if node type exists, False otherwise


### NodeFactory


Factory for creating node instances.

Handles creation of both visual and CasareRPA node instances
and links them together.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize node factory. |
| `create_casare_node(visual_node, **kwargs)` | `Optional[object]` | Create a CasareRPA node instance for a visual node. |
| `create_linked_node(graph, node_class, pos, ...)` | `Tuple[Any, object]` | Create both visual and CasareRPA nodes and link them. |
| `create_visual_node(graph, node_class, pos)` | `Any` | Create a visual node instance in the graph. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize node factory.

##### `create_casare_node`

```python
def create_casare_node(visual_node: Any, **kwargs) -> Optional[object]
```

Create a CasareRPA node instance for a visual node.

Args:
    visual_node: Visual node instance
    **kwargs: Additional arguments for node creation

Returns:
    Created CasareRPA node instance or None

**Parameters:**

- `visual_node: Any` *(required)*
- `**kwargs`

##### `create_linked_node`

```python
def create_linked_node(graph: NodeGraph, node_class: Type, pos: Optional[Tuple[int, int]] = None, **kwargs) -> Tuple[Any, object]
```

Create both visual and CasareRPA nodes and link them.

Args:
    graph: NodeGraph instance
    node_class: Visual node class
    pos: Optional position (x, y) for the node
    **kwargs: Additional arguments for CasareRPA node creation

Returns:
    Tuple of (visual_node, casare_node)

**Parameters:**

- `graph: NodeGraph` *(required)*
- `node_class: Type` *(required)*
- `pos: Optional[Tuple[int, int]] = None`
- `**kwargs`

##### `create_visual_node`

```python
def create_visual_node(graph: NodeGraph, node_class: Type, pos: Optional[Tuple[int, int]] = None) -> Any
```

Create a visual node instance in the graph.

Args:
    graph: NodeGraph instance
    node_class: Visual node class
    pos: Optional position (x, y) for the node

Returns:
    Created visual node instance

**Parameters:**

- `graph: NodeGraph` *(required)*
- `node_class: Type` *(required)*
- `pos: Optional[Tuple[int, int]] = None`

### NodeRegistry


Registry for visual nodes.

Manages node type registration with NodeGraphQt and provides
node discovery functionality.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize node registry. |
| `get_all_nodes()` | `List[Type]` | Get all registered node classes. |
| `get_all_nodes_in_category(category)` | `List[Type]` | Get all nodes in a category including all subcategories. |
| `get_categories()` | `List[str]` | Get all registered categories. |
| `get_node_class(node_name)` | `Optional[Type]` | Get a node class by name. |
| `get_nodes_by_category(category)` | `List[Type]` | Get all nodes in a specific category (exact match only). |
| `get_root_categories()` | `List[str]` | Get all root (top-level) categories. |
| `get_subcategories(parent)` | `List[str]` | Get immediate subcategories of a parent category. |
| `register_all_nodes(graph)` | `None` | Register all CasareRPA nodes with a NodeGraph. |
| `register_node(node_class, graph)` | `None` | Register a visual node class. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize node registry.

##### `get_all_nodes`

```python
def get_all_nodes() -> List[Type]
```

Get all registered node classes.

Returns:
    List of all node classes

##### `get_all_nodes_in_category`

```python
def get_all_nodes_in_category(category: str) -> List[Type]
```

Get all nodes in a category including all subcategories.

Args:
    category: Category path (e.g., "google" returns nodes from
              google, google/gmail, google/sheets, etc.)

Returns:
    List of node classes in the category and all subcategories

**Parameters:**

- `category: str` *(required)*

##### `get_categories`

```python
def get_categories() -> List[str]
```

Get all registered categories.

Returns:
    List of category names (all levels)

##### `get_node_class`

```python
def get_node_class(node_name: str) -> Optional[Type]
```

Get a node class by name.

Args:
    node_name: Name of the node

Returns:
    Node class or None if not found

**Parameters:**

- `node_name: str` *(required)*

##### `get_nodes_by_category`

```python
def get_nodes_by_category(category: str) -> List[Type]
```

Get all nodes in a specific category (exact match only).

Args:
    category: Category path (e.g., "google/gmail")

Returns:
    List of node classes in the exact category

**Parameters:**

- `category: str` *(required)*

##### `get_root_categories`

```python
def get_root_categories() -> List[str]
```

Get all root (top-level) categories.

Returns:
    List of root category names

##### `get_subcategories`

```python
def get_subcategories(parent: str) -> List[str]
```

Get immediate subcategories of a parent category.

Args:
    parent: Parent category path (e.g., "google")

Returns:
    List of immediate subcategory names (e.g., ["gmail", "sheets", "docs"])

**Parameters:**

- `parent: str` *(required)*

##### `register_all_nodes`

```python
def register_all_nodes(graph: NodeGraph) -> None
```

Register all CasareRPA nodes with a NodeGraph.

Args:
    graph: NodeGraph instance to register nodes with

**Parameters:**

- `graph: NodeGraph` *(required)*

##### `register_node`

```python
def register_node(node_class: Type, graph: Optional[NodeGraph] = None) -> None
```

Register a visual node class.

Args:
    node_class: Visual node class to register
    graph: Optional NodeGraph instance to register with

**Parameters:**

- `node_class: Type` *(required)*
- `graph: Optional[NodeGraph] = None`

---

## casare_rpa.presentation.canvas.graph.node_widgets

**File:** `src\casare_rpa\presentation\canvas\graph\node_widgets.py`


Custom Node Widget Wrappers for NodeGraphQt.

This module provides wrapper classes that extend NodeGraphQt's widget classes
with custom behavior and styling, replacing the monkey-patches in node_graph_widget.py.

Classes:
    CasareComboBox: Fixes combo dropdown z-order issue
    CasareCheckBox: Adds dark blue checkbox styling
    CasareLivePipe: Fixes draw_index_pointer text_pos bug
    CasarePipeItem: Fixes draw_path viewer None crash


### Functions

#### `apply_all_node_widget_fixes`

```python
def apply_all_node_widget_fixes() -> None
```

Apply all NodeGraphQt widget fixes.

This should be called once at module load time to apply all fixes
before any NodeGraphQt widgets are created.

The fixes include:
- LivePipeItem.draw_index_pointer text_pos bug fix
- PipeItem.draw_path viewer None crash fix
- NodeGraph._on_node_data_dropped QUrl TypeError fix
- NodeBaseItem._add_port font handling fix
- QGraphicsTextItem.font() -1 point size fix
- NodeItem.paint selection styling fix

Note: CasareComboBox and CasareCheckBox fixes are applied per-widget
via the patched __init__ methods installed below.


### CasareCheckBox


Mixin/wrapper that applies dark blue checkbox styling with white checkmark.

Provides a consistent VSCode-like dark theme styling for checkboxes
inside nodes, with proper hover and checked states.

Usage:
    # Apply to a NodeCheckBox instance
    CasareCheckBox.apply_styling(node_checkbox_widget)


**Attributes:**

- `_checkmark_path: Optional[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_styling(node_widget)` | `None` | Apply dark blue styling to a NodeCheckBox widget. |

#### Method Details

##### `apply_styling`

```python
@classmethod
def apply_styling(node_widget) -> None
```

Apply dark blue styling to a NodeCheckBox widget.

Args:
    node_widget: NodeCheckBox instance from NodeGraphQt

**Parameters:**

- `node_widget` *(required)*

### CasareComboBox


Mixin/wrapper that fixes combo dropdown z-order in QGraphicsProxyWidget.

When QComboBox is embedded in a QGraphicsProxyWidget, the dropdown popup
can get clipped by other widgets in the same node. This fix ensures the
popup appears as a top-level window above all graphics items by raising
the z-value when the popup is shown.

Usage:
    # Apply to a NodeComboBox instance
    CasareComboBox.apply_fix(node_combo_widget)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix(node_widget)` | `None` | Apply z-order fix to a NodeComboBox widget. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix(node_widget) -> None
```

Apply z-order fix to a NodeComboBox widget.

Args:
    node_widget: NodeComboBox instance from NodeGraphQt

**Parameters:**

- `node_widget` *(required)*

### CasareLivePipe


Wrapper that fixes the draw_index_pointer text_pos bug in LivePipeItem.

The original NodeGraphQt code has a bug where text_pos is undefined
when viewer_layout_direction() returns None. This wrapper provides
a fixed version that always initializes text_pos with a default value.

Usage:
    # Apply fix at module load time
    CasareLivePipe.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the draw_index_pointer fix to LivePipeItem. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the draw_index_pointer fix to LivePipeItem.

### CasareNodeBaseFontFix


Fix for NodeBase._add_port() font handling bug.

The original NodeGraphQt code at node_base.py:921-922 has:
    text.font().setPointSize(8)
    text.setFont(text.font())

This is buggy because text.font() returns a copy. The setPointSize(8)
modifies the copy, then setFont() applies the unmodified original font
which may have -1 as its point size if no font was explicitly set.

This fix patches _add_port to properly create and set the font.

Usage:
    # Apply fix at module load time
    CasareNodeBaseFontFix.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the font fix to NodeItem._add_port. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the font fix to NodeItem._add_port.

### CasareNodeDataDropFix


Wrapper that fixes the _on_node_data_dropped QUrl TypeError in NodeGraph.

The original NodeGraphQt code fails when dragging files onto the canvas
because it tries to join QUrl objects as strings without converting them.

Error: TypeError: sequence item 0: expected str instance, PySide6.QtCore.QUrl found

Usage:
    # Apply fix at module load time
    CasareNodeDataDropFix.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the _on_node_data_dropped fix to NodeGraph. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the _on_node_data_dropped fix to NodeGraph.

### CasareNodeItemPaintFix


Custom paint fix for NodeItem to provide VSCode-style selection border.

Replaces the default NodeItem.paint with a version that:
- Uses rounded corners (8px radius)
- Shows thick blue border (3px) when selected (#007ACC)
- Prevents dotted selection boxes on child items

Usage:
    # Apply fix at module load time
    CasareNodeItemPaintFix.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the custom paint fix to NodeItem. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the custom paint fix to NodeItem.

### CasarePipeItemFix


Wrapper that fixes the draw_path viewer None crash in PipeItem.

The original NodeGraphQt code crashes when viewer() returns None,
which can happen during workflow loading or undo/redo operations.
This wrapper adds a None check before proceeding.

Usage:
    # Apply fix at module load time
    CasarePipeItemFix.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the draw_path fix to PipeItem. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the draw_path fix to PipeItem.

### CasareViewerFontFix


Fix for NodeViewer font initialization that can cause QFont -1 warnings.

When QGraphicsTextItem.font() returns a font without an explicit point size,
it may have -1 as the point size. This fix ensures fonts are properly
initialized before calling setPointSize().

Usage:
    # Apply fix at module load time
    CasareViewerFontFix.apply_fix()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `apply_fix()` | `None` | Apply the font fix to NodeViewer._set_viewer_pan_zoom. |

#### Method Details

##### `apply_fix`

```python
@staticmethod
def apply_fix() -> None
```

Apply the font fix to NodeViewer._set_viewer_pan_zoom.

---

## casare_rpa.presentation.canvas.graph.port_shapes

**File:** `src\casare_rpa\presentation\canvas\graph\port_shapes.py`


Port Shape Drawing Functions for CasareRPA Canvas.

Provides shape rendering for different data types to ensure accessibility
for color-blind users. Each DataType has a distinct shape in addition to color.

References:
- "The Design of Everyday Things" by Don Norman - Accessibility & Affordances
- WCAG 2.1 - Don't rely on color alone to convey information


### Functions

#### `draw_circle`

```python
def draw_circle(painter: QPainter, center: QPointF, radius: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a filled circle (default shape for most types).

Args:
    painter: QPainter to draw with
    center: Center point of the circle
    radius: Radius of the circle
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_circle_with_dot`

```python
def draw_circle_with_dot(painter: QPainter, center: QPointF, radius: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a circle with a center dot (for BROWSER type).

Args:
    painter: QPainter to draw with
    center: Center point
    radius: Outer radius
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_diamond`

```python
def draw_diamond(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a diamond shape (for BOOLEAN type).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Size (distance from center to vertex)
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_hexagon`

```python
def draw_hexagon(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a hexagon (for DICT type).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Radius (center to vertex)
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_hollow_circle`

```python
def draw_hollow_circle(painter: QPainter, center: QPointF, radius: float, border_color: QColor, border_width: float = 2.0) -> None
```

Draw a hollow circle (for ANY/wildcard type).

Args:
    painter: QPainter to draw with
    center: Center point of the circle
    radius: Radius of the circle
    border_color: Border color
    border_width: Border line width

#### `draw_pentagon`

```python
def draw_pentagon(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a pentagon (for ELEMENT type).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Radius (center to vertex)
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_port_shape`

```python
def draw_port_shape(painter: QPainter, center: QPointF, size: float, data_type: Optional[DataType], fill_color: Tuple[int, int, int, int], border_color: Optional[Tuple[int, int, int, int]] = None, is_exec: bool = False, is_output: bool = False) -> None
```

Draw the appropriate port shape based on data type.

Args:
    painter: QPainter to draw with
    center: Center point of the port
    size: Size/radius of the port
    data_type: The DataType (None for exec ports)
    fill_color: RGBA tuple for fill color
    border_color: RGBA tuple for border (darker fill if None)
    is_exec: True if this is an execution flow port
    is_output: True if this is an output port (affects triangle direction)

#### `draw_rounded_square`

```python
def draw_rounded_square(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5, corner_radius: float = 3.0) -> None
```

Draw a rounded square (for PAGE type).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Half-width of the square
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width
    corner_radius: Radius of rounded corners

#### `draw_square`

```python
def draw_square(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5) -> None
```

Draw a square (for LIST type).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Half-width of the square
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width

#### `draw_triangle`

```python
def draw_triangle(painter: QPainter, center: QPointF, size: float, fill_color: QColor, border_color: QColor, border_width: float = 1.5, pointing_right: bool = True) -> None
```

Draw a triangle (for EXEC ports - execution flow).

Args:
    painter: QPainter to draw with
    center: Center point
    size: Size of the triangle
    fill_color: Fill color
    border_color: Border color
    border_width: Border line width
    pointing_right: If True, points right; if False, points left

#### `get_shape_description`

```python
def get_shape_description(data_type: Optional[DataType]) -> str
```

Get a human-readable description of the shape for a type.

Useful for tooltips and accessibility.

Args:
    data_type: The DataType (None for exec)

Returns:
    Description string

#### `get_shape_for_type`

```python
def get_shape_for_type(data_type: Optional[DataType]) -> str
```

Get the shape name for a data type.

Args:
    data_type: The DataType (None for exec)

Returns:
    Shape name string


---

## casare_rpa.presentation.canvas.graph.selection_manager

**File:** `src\casare_rpa\presentation\canvas\graph\selection_manager.py`


Selection Manager for CasareRPA Canvas.

Handles all node and frame selection operations for the node graph widget.
Follows Single Responsibility Principle - manages selection state only.


### SelectionManager

**Inherits from:** `QObject`


Manages selection operations for the node graph.

Provides a clean interface for:
- Selecting/deselecting nodes
- Multi-selection handling
- Frame selection
- Selection queries

Usage:
    manager = SelectionManager(graph)
    manager.select_nodes([node1, node2])
    selected = manager.get_selected_nodes()


**Attributes:**

- `frame_deselected: Signal`
- `frame_selected: Signal`
- `selection_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | `None` | Initialize selection manager. |
| `add_to_selection(node)` | `None` | Add a node to the current selection without clearing. |
| `center_on_selection()` | `None` | Center the view on the currently selected nodes. |
| `clear_selection()` | `None` | Clear all node and frame selection. |
| `delete_selected_frames()` | `bool` | Delete any selected frames in the scene. |
| `fit_to_selection()` | `None` | Fit the view to show all selected nodes. |
| `get_selected_frames()` | `List` | Get all selected frames. |
| `get_selected_node_ids()` | `List[str]` | Get IDs of currently selected nodes. |
| `get_selected_nodes()` | `List` | Get the currently selected nodes. |
| `get_selection_count()` | `int` | Get the number of selected nodes. |
| `graph()` | `'NodeGraph'` | Get the underlying graph. |
| `has_selection()` | `bool` | Check if any nodes are selected. |
| `is_selected(node)` | `bool` | Check if a node is selected. |
| `remove_from_selection(node)` | `None` | Remove a node from the current selection. |
| `select_all()` | `None` | Select all nodes in the graph. |
| `select_node(node)` | `None` | Select a single node, clearing other selections. |
| `select_nodes(nodes)` | `None` | Select multiple nodes. |
| `select_nodes_in_frame(frame)` | `None` | Select all nodes contained within a frame. |
| `toggle_selection(node)` | `None` | Toggle selection state of a node. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', parent: Optional[QObject] = None) -> None
```

Initialize selection manager.

Args:
    graph: The NodeGraphQt NodeGraph instance
    parent: Optional parent QObject

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `parent: Optional[QObject] = None`

##### `add_to_selection`

```python
def add_to_selection(node) -> None
```

Add a node to the current selection without clearing.

Args:
    node: The node to add to selection

**Parameters:**

- `node` *(required)*

##### `center_on_selection`

```python
def center_on_selection() -> None
```

Center the view on the currently selected nodes.

##### `clear_selection`

```python
def clear_selection() -> None
```

Clear all node and frame selection.

##### `delete_selected_frames`

```python
def delete_selected_frames() -> bool
```

Delete any selected frames in the scene.

Returns:
    True if any frames were deleted, False otherwise

##### `fit_to_selection`

```python
def fit_to_selection() -> None
```

Fit the view to show all selected nodes.

##### `get_selected_frames`

```python
def get_selected_frames() -> List
```

Get all selected frames.

Returns:
    List of selected NodeFrame items

##### `get_selected_node_ids`

```python
def get_selected_node_ids() -> List[str]
```

Get IDs of currently selected nodes.

Returns:
    List of selected node IDs

##### `get_selected_nodes`

```python
def get_selected_nodes() -> List
```

Get the currently selected nodes.

Returns:
    List of selected node objects

##### `get_selection_count`

```python
def get_selection_count() -> int
```

Get the number of selected nodes.

Returns:
    Number of selected nodes

##### `graph`

```python
@property
def graph() -> 'NodeGraph'
```

Get the underlying graph.

##### `has_selection`

```python
def has_selection() -> bool
```

Check if any nodes are selected.

Returns:
    True if at least one node is selected

##### `is_selected`

```python
def is_selected(node) -> bool
```

Check if a node is selected.

Args:
    node: The node to check

Returns:
    True if node is selected

**Parameters:**

- `node` *(required)*

##### `remove_from_selection`

```python
def remove_from_selection(node) -> None
```

Remove a node from the current selection.

Args:
    node: The node to remove from selection

**Parameters:**

- `node` *(required)*

##### `select_all`

```python
def select_all() -> None
```

Select all nodes in the graph.

##### `select_node`

```python
def select_node(node) -> None
```

Select a single node, clearing other selections.

Args:
    node: The node to select

**Parameters:**

- `node` *(required)*

##### `select_nodes`

```python
def select_nodes(nodes: List) -> None
```

Select multiple nodes.

Args:
    nodes: List of nodes to select

**Parameters:**

- `nodes: List` *(required)*

##### `select_nodes_in_frame`

```python
def select_nodes_in_frame(frame) -> None
```

Select all nodes contained within a frame.

Args:
    frame: The NodeFrame to get nodes from

**Parameters:**

- `frame` *(required)*

##### `toggle_selection`

```python
def toggle_selection(node) -> None
```

Toggle selection state of a node.

Args:
    node: The node to toggle

**Parameters:**

- `node` *(required)*

---

## casare_rpa.presentation.canvas.graph.style_manager

**File:** `src\casare_rpa\presentation\canvas\graph\style_manager.py`


Frame Style Manager

Centralized styling for NodeFrame components.
Consolidates color palettes, themes, and style application logic.

Following Single Responsibility Principle - this module handles ONLY visual styling.


### CollapseButtonStyle


Style constants for collapse button.


**Attributes:**

- `BACKGROUND_HOVER: QColor`
- `BACKGROUND_NORMAL: QColor`
- `BORDER_COLOR: QColor`
- `CORNER_RADIUS: int`
- `MARGIN: int`
- `SIZE: int`
- `SYMBOL_COLOR: QColor`
- `SYMBOL_SIZE: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_background_color(is_hovered)` | `QColor` | Get background color based on hover state. |

#### Method Details

##### `get_background_color`

```python
@classmethod
def get_background_color(is_hovered: bool) -> QColor
```

Get background color based on hover state.

**Parameters:**

- `is_hovered: bool` *(required)*

### ExposedPortStyle


Style constants for exposed port indicators.


**Attributes:**

- `BORDER_DARKEN: int`
- `BORDER_WIDTH: float`
- `MARGIN: int`
- `SIZE: int`
- `SPACING: int`

### FrameStyleManager


Manages visual styling for NodeFrame components.

Responsibilities:
- Color palette management
- Brush and pen creation
- Port type color resolution
- Theme application


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_frame_brush(color)` | `QBrush` | Create brush for frame fill. |
| `create_frame_pen(color, width, style, ...)` | `QPen` | Create pen for frame border. |
| `get_collapsed_brush(color)` | `QBrush` | Get brush for collapsed frame fill. |
| `get_collapsed_pen(color)` | `QPen` | Get pen for collapsed frame border. |
| `get_drop_target_brush()` | `QBrush` | Get brush for drop target fill. |
| `get_drop_target_pen()` | `QPen` | Get pen for drop target highlight. |
| `get_frame_color(color_name)` | `QColor` | Get frame color by name. |
| `get_node_count_color(frame_color)` | `QColor` | Get color for collapsed node count text. |
| `get_port_color(port)` | `QColor` | Get color for a port based on its type. |
| `get_selection_pen()` | `QPen` | Get pen for selected frame highlight. |
| `get_title_color()` | `QColor` | Get color for frame title text. |

#### Method Details

##### `create_frame_brush`

```python
@staticmethod
def create_frame_brush(color: QColor) -> QBrush
```

Create brush for frame fill.

**Parameters:**

- `color: QColor` *(required)*

##### `create_frame_pen`

```python
@staticmethod
def create_frame_pen(color: QColor, width: int = 2, style: Qt.PenStyle = Qt.PenStyle.DashLine, darken_factor: int = 120) -> QPen
```

Create pen for frame border.

Args:
    color: Base color
    width: Line width
    style: Pen style (solid, dash, etc.)
    darken_factor: How much to darken the color (100 = no change)

Returns:
    QPen for drawing frame border

**Parameters:**

- `color: QColor` *(required)*
- `width: int = 2`
- `style: Qt.PenStyle = Qt.PenStyle.DashLine`
- `darken_factor: int = 120`

##### `get_collapsed_brush`

```python
@staticmethod
def get_collapsed_brush(color: QColor) -> QBrush
```

Get brush for collapsed frame fill.

**Parameters:**

- `color: QColor` *(required)*

##### `get_collapsed_pen`

```python
@staticmethod
def get_collapsed_pen(color: QColor) -> QPen
```

Get pen for collapsed frame border.

**Parameters:**

- `color: QColor` *(required)*

##### `get_drop_target_brush`

```python
@staticmethod
def get_drop_target_brush() -> QBrush
```

Get brush for drop target fill.

##### `get_drop_target_pen`

```python
@staticmethod
def get_drop_target_pen() -> QPen
```

Get pen for drop target highlight.

##### `get_frame_color`

```python
@staticmethod
def get_frame_color(color_name: str) -> QColor
```

Get frame color by name.

Args:
    color_name: Color name (case-insensitive)

Returns:
    QColor for the frame

**Parameters:**

- `color_name: str` *(required)*

##### `get_node_count_color`

```python
@staticmethod
def get_node_count_color(frame_color: QColor) -> QColor
```

Get color for collapsed node count text.

**Parameters:**

- `frame_color: QColor` *(required)*

##### `get_port_color`

```python
@staticmethod
def get_port_color(port) -> QColor
```

Get color for a port based on its type.

Args:
    port: Port object with node() method

Returns:
    QColor for the port

**Parameters:**

- `port` *(required)*

##### `get_selection_pen`

```python
@staticmethod
def get_selection_pen() -> QPen
```

Get pen for selected frame highlight.

##### `get_title_color`

```python
@staticmethod
def get_title_color() -> QColor
```

Get color for frame title text.

---

## casare_rpa.presentation.canvas.graph.viewport_culling

**File:** `src\casare_rpa\presentation\canvas\graph\viewport_culling.py`


Viewport Culling Manager for CasareRPA Canvas.

Implements spatial partitioning for efficient visibility queries in large
workflows (100+ nodes). Uses a grid-based spatial hash for O(1) lookups.

References:
- "Designing Data-Intensive Applications" by Kleppmann - Partitioning
- Qt Graphics View Framework - Viewport optimization patterns


### Functions

#### `create_viewport_culler_for_graph`

```python
def create_viewport_culler_for_graph(graph_widget, cell_size: int = 500, margin: int = 200) -> ViewportCullingManager
```

Create and integrate a ViewportCullingManager with a NodeGraphWidget.

Args:
    graph_widget: The NodeGraphWidget to optimize
    cell_size: Spatial hash cell size
    margin: Viewport margin for culling

Returns:
    Configured ViewportCullingManager


### SpatialHash


Grid-based spatial hash for efficient spatial queries.

Divides the scene into cells and tracks which nodes occupy each cell.
Supports fast queries for nodes within a rectangular region.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(cell_size)` | - | Initialize the spatial hash. |
| `cell_count()` | `int` | Get the number of active cells. |
| `clear()` | `None` | Clear all nodes from the spatial hash. |
| `insert(node_id, rect)` | `None` | Insert or update a node in the spatial hash. |
| `node_count()` | `int` | Get the number of nodes in the spatial hash. |
| `query(rect)` | `Set[str]` | Query for all nodes that may intersect with the given rectan... |
| `remove(node_id)` | `None` | Remove a node from the spatial hash. |

#### Method Details

##### `__init__`

```python
def __init__(cell_size: int = 500)
```

Initialize the spatial hash.

Args:
    cell_size: Size of each grid cell in scene units (pixels)

**Parameters:**

- `cell_size: int = 500`

##### `cell_count`

```python
@property
def cell_count() -> int
```

Get the number of active cells.

##### `clear`

```python
def clear() -> None
```

Clear all nodes from the spatial hash.

##### `insert`

```python
def insert(node_id: str, rect: QRectF) -> None
```

Insert or update a node in the spatial hash.

Args:
    node_id: Unique identifier for the node
    rect: Bounding rectangle of the node in scene coordinates

**Parameters:**

- `node_id: str` *(required)*
- `rect: QRectF` *(required)*

##### `node_count`

```python
@property
def node_count() -> int
```

Get the number of nodes in the spatial hash.

##### `query`

```python
def query(rect: QRectF) -> Set[str]
```

Query for all nodes that may intersect with the given rectangle.

Args:
    rect: Query rectangle in scene coordinates

Returns:
    Set of node IDs that may intersect (may include false positives)

**Parameters:**

- `rect: QRectF` *(required)*

##### `remove`

```python
def remove(node_id: str) -> None
```

Remove a node from the spatial hash.

Args:
    node_id: Unique identifier for the node

**Parameters:**

- `node_id: str` *(required)*

### ViewportCullingManager

**Inherits from:** `QObject`


Manages visibility culling for large node graphs.

Tracks node positions in a spatial hash and provides efficient
queries for nodes visible within the current viewport.

Features:
- Spatial partitioning with configurable cell size
- Margin-based culling (keep nodes slightly outside viewport)
- Visibility state tracking to minimize show/hide calls
- Pipe culling (hide connections to hidden nodes)

Usage:
    culling = ViewportCullingManager(graph_widget)
    culling.update_viewport(viewport_rect)  # Call on pan/zoom


**Attributes:**

- `visibility_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(cell_size, margin, parent)` | - | Initialize the viewport culling manager. |
| `clear()` | `None` | Clear all nodes and pipes from the culling manager. |
| `get_stats()` | `Dict` | Get culling statistics. |
| `get_visible_nodes()` | `Set[str]` | Get the set of currently visible node IDs. |
| `is_enabled()` | `bool` | Check if culling is enabled. |
| `register_node(node_id, node_item, rect)` | `None` | Register a node with the culling manager. |
| `register_pipe(pipe_id, source_node_id, target_node_id, ...)` | `None` | Register a pipe (connection) for visibility culling. |
| `set_enabled(enabled)` | `None` | Enable or disable culling. |
| `unregister_node(node_id)` | `None` | Remove a node from the culling manager. |
| `unregister_pipe(pipe_id)` | `None` | Remove a pipe from the culling manager. |
| `update_node_position(node_id, rect)` | `None` | Update a node's position in the spatial hash. |
| `update_viewport(viewport_rect)` | `Tuple[Set[str], Set[str]]` | Update visibility based on the current viewport. |

#### Method Details

##### `__init__`

```python
def __init__(cell_size: int = 500, margin: int = 200, parent: Optional[QObject] = None)
```

Initialize the viewport culling manager.

Args:
    cell_size: Size of spatial hash cells (larger = fewer cells)
    margin: Extra margin around viewport for culling
    parent: Optional parent QObject

**Parameters:**

- `cell_size: int = 500`
- `margin: int = 200`
- `parent: Optional[QObject] = None`

##### `clear`

```python
def clear() -> None
```

Clear all nodes and pipes from the culling manager.

##### `get_stats`

```python
def get_stats() -> Dict
```

Get culling statistics.

##### `get_visible_nodes`

```python
def get_visible_nodes() -> Set[str]
```

Get the set of currently visible node IDs.

##### `is_enabled`

```python
def is_enabled() -> bool
```

Check if culling is enabled.

##### `register_node`

```python
def register_node(node_id: str, node_item: object, rect: QRectF) -> None
```

Register a node with the culling manager.

Args:
    node_id: Unique identifier for the node
    node_item: The QGraphicsItem for the node
    rect: Bounding rectangle in scene coordinates

**Parameters:**

- `node_id: str` *(required)*
- `node_item: object` *(required)*
- `rect: QRectF` *(required)*

##### `register_pipe`

```python
def register_pipe(pipe_id: str, source_node_id: str, target_node_id: str, pipe_item: object) -> None
```

Register a pipe (connection) for visibility culling.

Pipes are shown only when both source and target nodes are visible.

Args:
    pipe_id: Unique identifier for the pipe
    source_node_id: ID of the source node
    target_node_id: ID of the target node
    pipe_item: The QGraphicsItem for the pipe

**Parameters:**

- `pipe_id: str` *(required)*
- `source_node_id: str` *(required)*
- `target_node_id: str` *(required)*
- `pipe_item: object` *(required)*

##### `set_enabled`

```python
def set_enabled(enabled: bool) -> None
```

Enable or disable culling.

When disabled, all nodes remain visible.

Args:
    enabled: Whether culling should be active

**Parameters:**

- `enabled: bool` *(required)*

##### `unregister_node`

```python
def unregister_node(node_id: str) -> None
```

Remove a node from the culling manager.

Args:
    node_id: Unique identifier for the node

**Parameters:**

- `node_id: str` *(required)*

##### `unregister_pipe`

```python
def unregister_pipe(pipe_id: str) -> None
```

Remove a pipe from the culling manager.

Args:
    pipe_id: Unique identifier for the pipe

**Parameters:**

- `pipe_id: str` *(required)*

##### `update_node_position`

```python
def update_node_position(node_id: str, rect: QRectF) -> None
```

Update a node's position in the spatial hash.

Call this when a node is moved.

Args:
    node_id: Unique identifier for the node
    rect: New bounding rectangle in scene coordinates

**Parameters:**

- `node_id: str` *(required)*
- `rect: QRectF` *(required)*

##### `update_viewport`

```python
def update_viewport(viewport_rect: QRectF) -> Tuple[Set[str], Set[str]]
```

Update visibility based on the current viewport.

Args:
    viewport_rect: Current viewport rectangle in scene coordinates

Returns:
    Tuple of (newly_visible_ids, newly_hidden_ids)

**Parameters:**

- `viewport_rect: QRectF` *(required)*

---

## casare_rpa.presentation.canvas.initializers.controller_registrar

**File:** `src\casare_rpa\presentation\canvas\initializers\controller_registrar.py`


Controller registration and wiring for MainWindow.

Extracts controller instantiation, initialization, and signal/slot
connections from MainWindow to improve separation of concerns.

Usage:
    registrar = ControllerRegistrar(main_window)
    registrar.register_all()

    # When app.py sets external controllers:
    registrar.set_external_controllers(
        workflow_controller,
        execution_controller,
        node_controller,
        selector_controller
    )


### ControllerRegistrar


Handles controller registration and wiring for MainWindow.

Responsibilities:
- Instantiate MainWindow-specific controllers
- Initialize controllers in correct order
- Wire signal/slot connections between controllers and MainWindow
- Manage external controller injection (from app.py)
- Handle controller cleanup

Controller Categories:
1. MainWindow-specific: Created and owned by MainWindow
   - ConnectionController, PanelController, MenuController
   - EventBusController, ViewportController, SchedulingController
   - UIStateController, ProjectController, RobotController

2. External: Created by app.py and injected
   - WorkflowController, ExecutionController, NodeController
   - SelectorController


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize the registrar. |
| `cleanup_all()` | `None` | Clean up all controllers. |
| `register_all()` | `None` | Register and initialize all MainWindow-specific controllers. |
| `set_external_controllers(workflow_controller, execution_controller, node_controller, ...)` | `None` | Set externally created controllers (from app.py). |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize the registrar.

Args:
    main_window: The MainWindow instance to register controllers for

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup_all`

```python
def cleanup_all() -> None
```

Clean up all controllers.

Called during MainWindow close event.

##### `register_all`

```python
def register_all() -> None
```

Register and initialize all MainWindow-specific controllers.

Controllers are instantiated, then initialized in order.
External controllers (workflow, execution, node) are set to None
and must be injected later via set_external_controllers().

##### `set_external_controllers`

```python
def set_external_controllers(workflow_controller: 'WorkflowController', execution_controller: 'ExecutionController', node_controller: 'NodeController', selector_controller: Optional['SelectorController'] = None) -> None
```

Set externally created controllers (from app.py).

These controllers are created by app.py because they need
access to components not available during MainWindow init.

Args:
    workflow_controller: Manages workflow lifecycle
    execution_controller: Manages workflow execution
    node_controller: Manages node operations
    selector_controller: Optional selector/picker controller

**Parameters:**

- `workflow_controller: 'WorkflowController'` *(required)*
- `execution_controller: 'ExecutionController'` *(required)*
- `node_controller: 'NodeController'` *(required)*
- `selector_controller: Optional['SelectorController'] = None`

---

## casare_rpa.presentation.canvas.initializers.ui_component_initializer

**File:** `src\casare_rpa\presentation\canvas\initializers\ui_component_initializer.py`


UI Component Initializer for MainWindow.

Handles initialization of panels, docks, debug components, and validation
timers in a structured, tiered loading approach.


### UIComponentInitializer


Initializes UI components for MainWindow in a tiered approach.

Responsibilities:
- Load NORMAL tier components (panels, docks) after window shown
- Create debug components (toolbar, panel)
- Setup validation timer for real-time validation
- Coordinate with DockCreator for panel creation

Tiered Loading:
- CRITICAL: Window setup, actions, menus, toolbar (immediate)
- NORMAL: Panels, docks, debug components (after showEvent)
- DEFERRED: Dialogs, heavy features (on first use)

Attributes:
    _main_window: Reference to parent MainWindow
    _normal_components_loaded: Flag tracking NORMAL tier load status


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize the UI component initializer. |
| `cleanup()` | `None` | Cleanup initializer resources. |
| `ensure_normal_components_loaded()` | `None` | Ensure NORMAL tier components are loaded (idempotent). |
| `is_normal_loaded()` | `bool` | Check if NORMAL tier components are loaded. |
| `load_normal_components()` | `None` | Load NORMAL tier components after window is shown. |
| `schedule_deferred_load(delay_ms)` | `None` | Schedule NORMAL tier load after a delay. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize the UI component initializer.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Cleanup initializer resources.

Stops validation timer if active.

##### `ensure_normal_components_loaded`

```python
def ensure_normal_components_loaded() -> None
```

Ensure NORMAL tier components are loaded (idempotent).

##### `is_normal_loaded`

```python
@property
def is_normal_loaded() -> bool
```

Check if NORMAL tier components are loaded.

##### `load_normal_components`

```python
def load_normal_components() -> None
```

Load NORMAL tier components after window is shown.

Creates:
- Bottom panel (Variables, Output, Log, Validation)
- Variable inspector dock
- Properties panel
- Execution timeline dock
- Debug components (toolbar, panel)
- Process mining panel
- Robot picker panel
- Validation timer

##### `schedule_deferred_load`

```python
def schedule_deferred_load(delay_ms: int = 100) -> None
```

Schedule NORMAL tier load after a delay.

Used by showEvent to defer loading until window is visible.

Args:
    delay_ms: Delay in milliseconds before loading (default: 100)

**Parameters:**

- `delay_ms: int = 100`

---

## casare_rpa.presentation.canvas.main_window

**File:** `src\casare_rpa\presentation\canvas\main_window.py`


Main application window for CasareRPA.

This module provides the MainWindow class which serves as the primary
GUI container for the RPA platform.


### MainWindow

**Inherits from:** `QMainWindow`


Main application window for CasareRPA.

Provides the primary UI container with menu bar, toolbar, status bar,
and central widget area for the node graph editor.

Signals:
    workflow_new: Emitted when user requests new workflow
    workflow_new_from_template: Emitted when user selects a template (TemplateInfo)
    workflow_open: Emitted when user requests to open workflow (str: file path)
    workflow_save: Emitted when user requests to save workflow
    workflow_save_as: Emitted when user requests save as (str: file path)
    workflow_run: Emitted when user requests to run workflow
    workflow_pause: Emitted when user requests to pause workflow
    workflow_resume: Emitted when user requests to resume workflow
    workflow_stop: Emitted when user requests to stop workflow


**Attributes:**

- `preferences_saved: Signal`
- `save_as_scenario_requested: Signal`
- `trigger_workflow_requested: Signal`
- `workflow_export_selected: Signal`
- `workflow_import: Signal`
- `workflow_import_json: Signal`
- `workflow_new: Signal`
- `workflow_new_from_template: Signal`
- `workflow_open: Signal`
- `workflow_pause: Signal`
- `workflow_resume: Signal`
- `workflow_run: Signal`
- `workflow_run_all: Signal`
- `workflow_run_single_node: Signal`
- `workflow_run_to_node: Signal`
- `workflow_save: Signal`
- `workflow_save_as: Signal`
- `workflow_stop: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the main window. |
| `add_to_recent_files(file_path)` | `None` |  |
| `bottom_panel()` | `Optional['BottomPanelDock']` |  |
| `closeEvent(event)` | `None` |  |
| `command_palette()` | - |  |
| `ensure_normal_components_loaded()` | `None` | Ensure NORMAL tier components are loaded (idempotent). |
| `execution_timeline()` | `Optional['ExecutionTimeline']` |  |
| `get_bottom_panel()` | `Optional['BottomPanelDock']` |  |
| `get_command_palette()` | - |  |
| `get_current_file()` | `Optional[Path]` |  |
| `get_execution_history_viewer()` | - |  |
| `get_execution_timeline()` | `Optional['ExecutionTimeline']` |  |
| `get_graph()` | - |  |
| `get_log_viewer()` | - |  |
| `get_minimap()` | - |  |
| `get_node_controller()` | - |  |
| `get_node_registry()` | - |  |
| `get_process_mining_panel()` | - |  |
| `get_project_controller()` | - |  |
| `get_properties_panel()` | `Optional['PropertiesPanel']` |  |
| `get_recent_files_menu()` | - |  |
| `get_robot_controller()` | - |  |
| `get_robot_picker_panel()` | - |  |
| `get_scheduling_controller()` | - |  |
| `get_ui_state_controller()` | `Optional['UIStateController']` |  |
| `get_validation_panel()` | - |  |
| `get_variable_inspector()` | - |  |
| `get_variable_inspector_dock()` | - |  |
| `get_viewport_controller()` | - |  |
| `get_workflow_runner()` | - |  |
| `graph()` | - |  |
| `hide_bottom_panel()` | `None` |  |
| `hide_log_viewer()` | `None` |  |
| `hide_minimap()` | `None` |  |
| `hide_validation_panel()` | `None` |  |
| `is_auto_connect_enabled()` | `bool` | Check if auto-connect mode is enabled. |
| `is_auto_validate_enabled()` | `bool` |  |
| `is_modified()` | `bool` |  |
| `minimap()` | - |  |
| `node_controller()` | - |  |
| `node_registry()` | - |  |
| `on_workflow_changed()` | `None` |  |
| `process_mining_panel()` | - |  |
| `properties_panel()` | `Optional['PropertiesPanel']` |  |
| `recent_files_menu()` | - |  |
| `reset_ui_state()` | `None` |  |
| `resizeEvent(event)` | - |  |
| `robot_picker_panel()` | - |  |
| `scheduling_controller()` | - |  |
| `set_auto_validate(enabled)` | `None` |  |
| `set_browser_running(running)` | `None` |  |
| `set_central_widget(widget)` | `None` |  |
| `set_controllers(workflow_controller, execution_controller, node_controller, ...)` | `None` | Set externally created controllers (from app.py) via registr... |
| `set_current_file(file_path)` | `None` |  |
| `set_execution_status(status)` | `None` | Update execution status indicator. |
| `set_modified(modified)` | `None` |  |
| `set_workflow_data_provider(provider)` | `None` |  |
| `showEvent(event)` | `None` | Handle window show event - load NORMAL tier components. |
| `show_bottom_panel()` | `None` |  |
| `show_execution_history()` | `None` |  |
| `show_log_viewer()` | `None` |  |
| `show_minimap()` | `None` |  |
| `show_status(message, duration)` | `None` |  |
| `show_validation_panel()` | `None` |  |
| `show_variable_inspector()` | `None` |  |
| `trigger_workflow_run()` | `None` | Handle workflow run request from visual trigger node. |
| `update_node_count(count)` | `None` | Update the node count display in status bar. |
| `update_properties_panel(node)` | `None` |  |
| `update_zoom_display(zoom_percent)` | `None` | Update the zoom level display in status bar. |
| `validate_current_workflow(show_panel)` | `'ValidationResult'` |  |
| `validation_panel()` | - |  |
| `variable_inspector_dock()` | - |  |
| `viewport_controller()` | - |  |
| `workflow_runner()` | - |  |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the main window.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_to_recent_files`

```python
def add_to_recent_files(file_path) -> None
```

**Parameters:**

- `file_path` *(required)*

##### `bottom_panel`

```python
@property
def bottom_panel() -> Optional['BottomPanelDock']
```

##### `closeEvent`

```python
def closeEvent(event) -> None
```

**Parameters:**

- `event` *(required)*

##### `command_palette`

```python
@property
def command_palette()
```

##### `ensure_normal_components_loaded`

```python
def ensure_normal_components_loaded() -> None
```

Ensure NORMAL tier components are loaded (idempotent).

##### `execution_timeline`

```python
@property
def execution_timeline() -> Optional['ExecutionTimeline']
```

##### `get_bottom_panel`

```python
def get_bottom_panel() -> Optional['BottomPanelDock']
```

##### `get_command_palette`

```python
def get_command_palette()
```

##### `get_current_file`

```python
def get_current_file() -> Optional[Path]
```

##### `get_execution_history_viewer`

```python
def get_execution_history_viewer()
```

##### `get_execution_timeline`

```python
def get_execution_timeline() -> Optional['ExecutionTimeline']
```

##### `get_graph`

```python
def get_graph()
```

##### `get_log_viewer`

```python
def get_log_viewer()
```

##### `get_minimap`

```python
def get_minimap()
```

##### `get_node_controller`

```python
def get_node_controller()
```

##### `get_node_registry`

```python
def get_node_registry()
```

##### `get_process_mining_panel`

```python
def get_process_mining_panel()
```

##### `get_project_controller`

```python
def get_project_controller()
```

##### `get_properties_panel`

```python
def get_properties_panel() -> Optional['PropertiesPanel']
```

##### `get_recent_files_menu`

```python
def get_recent_files_menu()
```

##### `get_robot_controller`

```python
def get_robot_controller()
```

##### `get_robot_picker_panel`

```python
def get_robot_picker_panel()
```

##### `get_scheduling_controller`

```python
def get_scheduling_controller()
```

##### `get_ui_state_controller`

```python
def get_ui_state_controller() -> Optional['UIStateController']
```

##### `get_validation_panel`

```python
def get_validation_panel()
```

##### `get_variable_inspector`

```python
def get_variable_inspector()
```

##### `get_variable_inspector_dock`

```python
def get_variable_inspector_dock()
```

##### `get_viewport_controller`

```python
def get_viewport_controller()
```

##### `get_workflow_runner`

```python
def get_workflow_runner()
```

##### `graph`

```python
@property
def graph()
```

##### `hide_bottom_panel`

```python
def hide_bottom_panel() -> None
```

##### `hide_log_viewer`

```python
def hide_log_viewer() -> None
```

##### `hide_minimap`

```python
def hide_minimap() -> None
```

##### `hide_validation_panel`

```python
def hide_validation_panel() -> None
```

##### `is_auto_connect_enabled`

```python
def is_auto_connect_enabled() -> bool
```

Check if auto-connect mode is enabled.

##### `is_auto_validate_enabled`

```python
def is_auto_validate_enabled() -> bool
```

##### `is_modified`

```python
def is_modified() -> bool
```

##### `minimap`

```python
@property
def minimap()
```

##### `node_controller`

```python
@property
def node_controller()
```

##### `node_registry`

```python
@property
def node_registry()
```

##### `on_workflow_changed`

```python
def on_workflow_changed() -> None
```

##### `process_mining_panel`

```python
@property
def process_mining_panel()
```

##### `properties_panel`

```python
@property
def properties_panel() -> Optional['PropertiesPanel']
```

##### `recent_files_menu`

```python
@property
def recent_files_menu()
```

##### `reset_ui_state`

```python
def reset_ui_state() -> None
```

##### `resizeEvent`

```python
def resizeEvent(event)
```

**Parameters:**

- `event` *(required)*

##### `robot_picker_panel`

```python
@property
def robot_picker_panel()
```

##### `scheduling_controller`

```python
@property
def scheduling_controller()
```

##### `set_auto_validate`

```python
def set_auto_validate(enabled: bool) -> None
```

**Parameters:**

- `enabled: bool` *(required)*

##### `set_browser_running`

```python
def set_browser_running(running: bool) -> None
```

**Parameters:**

- `running: bool` *(required)*

##### `set_central_widget`

```python
def set_central_widget(widget: QWidget) -> None
```

**Parameters:**

- `widget: QWidget` *(required)*

##### `set_controllers`

```python
def set_controllers(workflow_controller, execution_controller, node_controller, selector_controller: Optional[SelectorController] = None) -> None
```

Set externally created controllers (from app.py) via registrar.

**Parameters:**

- `workflow_controller` *(required)*
- `execution_controller` *(required)*
- `node_controller` *(required)*
- `selector_controller: Optional[SelectorController] = None`

##### `set_current_file`

```python
def set_current_file(file_path: Optional[Path]) -> None
```

**Parameters:**

- `file_path: Optional[Path]` *(required)*

##### `set_execution_status`

```python
def set_execution_status(status: str) -> None
```

Update execution status indicator.

**Parameters:**

- `status: str` *(required)*

##### `set_modified`

```python
def set_modified(modified: bool) -> None
```

**Parameters:**

- `modified: bool` *(required)*

##### `set_workflow_data_provider`

```python
def set_workflow_data_provider(provider: callable) -> None
```

**Parameters:**

- `provider: callable` *(required)*

##### `showEvent`

```python
def showEvent(event) -> None
```

Handle window show event - load NORMAL tier components.

**Parameters:**

- `event` *(required)*

##### `show_bottom_panel`

```python
def show_bottom_panel() -> None
```

##### `show_execution_history`

```python
def show_execution_history() -> None
```

##### `show_log_viewer`

```python
def show_log_viewer() -> None
```

##### `show_minimap`

```python
def show_minimap() -> None
```

##### `show_status`

```python
def show_status(message: str, duration: int = 3000) -> None
```

**Parameters:**

- `message: str` *(required)*
- `duration: int = 3000`

##### `show_validation_panel`

```python
def show_validation_panel() -> None
```

##### `show_variable_inspector`

```python
def show_variable_inspector() -> None
```

##### `trigger_workflow_run`

```python
def trigger_workflow_run() -> None
```

Handle workflow run request from visual trigger node.

##### `update_node_count`

```python
def update_node_count(count: int) -> None
```

Update the node count display in status bar.

**Parameters:**

- `count: int` *(required)*

##### `update_properties_panel`

```python
def update_properties_panel(node) -> None
```

**Parameters:**

- `node` *(required)*

##### `update_zoom_display`

```python
def update_zoom_display(zoom_percent: float) -> None
```

Update the zoom level display in status bar.

**Parameters:**

- `zoom_percent: float` *(required)*

##### `validate_current_workflow`

```python
def validate_current_workflow(show_panel: bool = True) -> 'ValidationResult'
```

**Parameters:**

- `show_panel: bool = True`

##### `validation_panel`

```python
@property
def validation_panel()
```

##### `variable_inspector_dock`

```python
@property
def variable_inspector_dock()
```

##### `viewport_controller`

```python
@property
def viewport_controller()
```

##### `workflow_runner`

```python
@property
def workflow_runner()
```

---

## casare_rpa.presentation.canvas.port_type_system

**File:** `src\casare_rpa\presentation\canvas\port_type_system.py`


Port Type System for CasareRPA (Presentation Layer).

Provides centralized type registry, compatibility rules, and visual metadata
for port types. This module handles visual concerns (colors, shapes) and
belongs in the presentation layer.

References:
- "Clean Architecture" by Robert C. Martin - Dependency Inversion Principle
- "Designing Data-Intensive Applications" - Type safety for data flow


### Functions

#### `get_port_type_registry`

```python
def get_port_type_registry() -> PortTypeRegistry
```

Get the singleton PortTypeRegistry instance.

#### `get_type_color`

```python
def get_type_color(data_type: DataType) -> Tuple[int, int, int, int]
```

Get the RGBA color for a data type.

Convenience function for quick color lookup.

Args:
    data_type: The DataType to get color for

Returns:
    RGBA tuple (r, g, b, a)

#### `is_types_compatible`

```python
def is_types_compatible(source: DataType, target: DataType) -> bool
```

Check if source type can connect to target type.

Convenience function for quick type checking.

Args:
    source: The output port's data type
    target: The input port's data type

Returns:
    True if connection is allowed, False otherwise


### DefaultCompatibilityRule


Default type compatibility rules.

Rules:
1. ANY accepts/provides all types (universal wildcard)
2. Same types are always compatible
3. Numeric types (INTEGER, FLOAT) are cross-compatible
4. All types can connect to STRING (implicit conversion)
5. LIST/DICT require exact type match
6. PAGE, BROWSER, ELEMENT require exact type match


**Attributes:**

- `BOOLEAN_COMPATIBLE: Set[DataType]`
- `FLOAT_COMPATIBLE: Set[DataType]`
- `INTEGER_COMPATIBLE: Set[DataType]`
- `STRICT_TYPES: Set[DataType]`
- `STRING_COMPATIBLE: Set[DataType]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_incompatibility_reason(source, target)` | `Optional[str]` | Get human-readable reason why types are incompatible. |
| `is_compatible(source, target)` | `bool` | Check if source type can connect to target type. |

#### Method Details

##### `get_incompatibility_reason`

```python
def get_incompatibility_reason(source: DataType, target: DataType) -> Optional[str]
```

Get human-readable reason why types are incompatible.

Args:
    source: The output port's data type
    target: The input port's data type

Returns:
    Reason string if incompatible, None if compatible

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

##### `is_compatible`

```python
def is_compatible(source: DataType, target: DataType) -> bool
```

Check if source type can connect to target type.

Args:
    source: The output port's data type
    target: The input port's data type

Returns:
    True if connection is allowed, False otherwise

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

### PortShape

**Inherits from:** `Enum`


Shape types for port rendering (accessibility feature).


**Attributes:**

- `CIRCLE: auto`
- `CIRCLE_DOT: auto`
- `DIAMOND: auto`
- `HEXAGON: auto`
- `HOLLOW_CIRCLE: auto`
- `PENTAGON: auto`
- `ROUNDED_SQUARE: auto`
- `SQUARE: auto`
- `TRIANGLE: auto`

### PortTypeInfo

**Decorators:** `@dataclass`


Immutable metadata for a port data type.

Attributes:
    data_type: The DataType enum value
    display_name: Human-readable name for UI
    color: RGBA tuple for port visual color
    shape: Shape identifier for accessibility
    description: Tooltip description


**Attributes:**

- `color: Tuple[int, int, int, int]`
- `data_type: DataType`
- `description: str`
- `display_name: str`
- `shape: str`

### PortTypeRegistry


Singleton registry for port types with colors, shapes, and compatibility.

Provides centralized access to:
- Type visual metadata (colors, shapes)
- Type compatibility checking
- Type information lookup

Usage:
    registry = PortTypeRegistry()
    color = registry.get_type_color(DataType.STRING)
    is_valid = registry.is_compatible(DataType.INTEGER, DataType.FLOAT)


**Attributes:**

- `EXEC_COLOR: Tuple[int, int, int, int]`
- `TYPE_COLORS: Dict[DataType, Tuple[int, int, int, int]]`
- `TYPE_SHAPES: Dict[DataType, PortShape]`
- `_instance: Optional['PortTypeRegistry']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__new__()` | `'PortTypeRegistry'` | Ensure singleton instance. |
| `get_compatible_types(source)` | `Set[DataType]` | Get all types that are compatible with the source type. |
| `get_exec_color()` | `Tuple[int, int, int, int]` | Get the color for execution ports. |
| `get_incompatibility_reason(source, target)` | `Optional[str]` | Get human-readable reason why types are incompatible. |
| `get_type_color(data_type)` | `Tuple[int, int, int, int]` | Get the RGBA color for a data type. |
| `get_type_info(data_type)` | `PortTypeInfo` | Get metadata for a data type. |
| `get_type_shape(data_type)` | `PortShape` | Get the shape for a data type (for accessibility). |
| `is_compatible(source, target)` | `bool` | Check if source type can connect to target type. |
| `set_compatibility_rule(rule)` | `None` | Set a custom compatibility rule (Open/Closed Principle). |

#### Method Details

##### `__new__`

```python
def __new__() -> 'PortTypeRegistry'
```

Ensure singleton instance.

##### `get_compatible_types`

```python
def get_compatible_types(source: DataType) -> Set[DataType]
```

Get all types that are compatible with the source type.

Args:
    source: The source data type

Returns:
    Set of DataTypes that can receive data from source

**Parameters:**

- `source: DataType` *(required)*

##### `get_exec_color`

```python
def get_exec_color() -> Tuple[int, int, int, int]
```

Get the color for execution ports.

##### `get_incompatibility_reason`

```python
def get_incompatibility_reason(source: DataType, target: DataType) -> Optional[str]
```

Get human-readable reason why types are incompatible.

Args:
    source: The output port's data type
    target: The input port's data type

Returns:
    Reason string if incompatible, None if compatible

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

##### `get_type_color`

```python
def get_type_color(data_type: DataType) -> Tuple[int, int, int, int]
```

Get the RGBA color for a data type.

Args:
    data_type: The DataType to get color for

Returns:
    RGBA tuple (r, g, b, a) where each component is 0-255

**Parameters:**

- `data_type: DataType` *(required)*

##### `get_type_info`

```python
def get_type_info(data_type: DataType) -> PortTypeInfo
```

Get metadata for a data type.

Args:
    data_type: The DataType to look up

Returns:
    PortTypeInfo with color, shape, and description

**Parameters:**

- `data_type: DataType` *(required)*

##### `get_type_shape`

```python
def get_type_shape(data_type: DataType) -> PortShape
```

Get the shape for a data type (for accessibility).

Args:
    data_type: The DataType to get shape for

Returns:
    PortShape enum value

**Parameters:**

- `data_type: DataType` *(required)*

##### `is_compatible`

```python
def is_compatible(source: DataType, target: DataType) -> bool
```

Check if source type can connect to target type.

Args:
    source: The output port's data type
    target: The input port's data type

Returns:
    True if connection is allowed, False otherwise

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

##### `set_compatibility_rule`

```python
def set_compatibility_rule(rule: TypeCompatibilityRule) -> None
```

Set a custom compatibility rule (Open/Closed Principle).

Allows extending type checking without modifying this class.

Args:
    rule: Object implementing TypeCompatibilityRule protocol

**Parameters:**

- `rule: TypeCompatibilityRule` *(required)*

### TypeCompatibilityRule

**Inherits from:** `Protocol`


Protocol for type compatibility checking (Open/Closed Principle).


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_incompatibility_reason(source, target)` | `Optional[str]` | Get human-readable reason why types are incompatible. |
| `is_compatible(source, target)` | `bool` | Check if source type can connect to target type. |

#### Method Details

##### `get_incompatibility_reason`

```python
def get_incompatibility_reason(source: DataType, target: DataType) -> Optional[str]
```

Get human-readable reason why types are incompatible.

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

##### `is_compatible`

```python
def is_compatible(source: DataType, target: DataType) -> bool
```

Check if source type can connect to target type.

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

---

## casare_rpa.presentation.canvas.resources

**File:** `src\casare_rpa\presentation\canvas\resources.py`


CasareRPA - Resource Cache for Icons and Pixmaps

Provides caching for Qt resource objects (QIcon, QPixmap) to avoid
repeated file I/O and object creation. Uses LRU-style eviction.

Performance Impact:
- Reduces icon loading time by 80-90% on cache hits
- Minimizes memory fragmentation from repeated pixmap creation
- Thread-safe via RLock for cache operations


### Functions

#### `get_cached_icon`

```python
def get_cached_icon(path: str) -> 'QIcon'
```

Get a cached QIcon.

This is a convenience wrapper around ResourceCache.get_icon().

Args:
    path: Path to the icon file

Returns:
    Cached QIcon instance

#### `get_cached_pixmap`

```python
def get_cached_pixmap(path: str, width: int = -1, height: int = -1) -> 'QPixmap'
```

Get a cached QPixmap.

This is a convenience wrapper around ResourceCache.get_pixmap().

Args:
    path: Path to the image file
    width: Target width (-1 for original)
    height: Target height (-1 for original)

Returns:
    Cached QPixmap instance


### ResourceCache


Cached resource loader for icons and pixmaps.

Uses class-level dictionaries with size tracking for LRU-style eviction.
All methods are classmethods for global singleton-like behavior.

Cache Statistics:
- _icon_hits / _icon_misses: Track icon cache performance
- _pixmap_hits / _pixmap_misses: Track pixmap cache performance


**Attributes:**

- `MAX_ICON_CACHE_SIZE: int`
- `MAX_PIXMAP_CACHE_SIZE: int`
- `_icon_cache: Dict[str, 'QIcon']`
- `_icon_hits: int`
- `_icon_misses: int`
- `_pixmap_cache: Dict[Tuple[str, int, int], 'QPixmap']`
- `_pixmap_hits: int`
- `_pixmap_misses: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `clear()` | `None` | Clear all caches. |
| `get_icon(path)` | `'QIcon'` | Get a cached QIcon instance. |
| `get_pixmap(path, width, height)` | `'QPixmap'` | Get a cached QPixmap instance, optionally scaled. |
| `get_stats()` | `Dict[str, int]` | Get cache statistics. |
| `preload_icons(paths)` | `None` | Preload a list of icons into the cache. |

#### Method Details

##### `clear`

```python
@classmethod
def clear() -> None
```

Clear all caches.

Use this for testing or when memory pressure is high.

##### `get_icon`

```python
@classmethod
def get_icon(path: str) -> 'QIcon'
```

Get a cached QIcon instance.

Args:
    path: Path to the icon file

Returns:
    QIcon instance (cached or newly created)

**Parameters:**

- `path: str` *(required)*

##### `get_pixmap`

```python
@classmethod
def get_pixmap(path: str, width: int = -1, height: int = -1) -> 'QPixmap'
```

Get a cached QPixmap instance, optionally scaled.

Args:
    path: Path to the image file
    width: Target width (-1 for original)
    height: Target height (-1 for original)

Returns:
    QPixmap instance (cached or newly created)

**Parameters:**

- `path: str` *(required)*
- `width: int = -1`
- `height: int = -1`

##### `get_stats`

```python
@classmethod
def get_stats() -> Dict[str, int]
```

Get cache statistics.

Returns:
    Dictionary with hit/miss counts and cache sizes

##### `preload_icons`

```python
@classmethod
def preload_icons(paths: list) -> None
```

Preload a list of icons into the cache.

Useful during application startup to warm the cache.

Args:
    paths: List of icon file paths to preload

**Parameters:**

- `paths: list` *(required)*

---

## casare_rpa.presentation.canvas.search.command_palette

**File:** `src\casare_rpa\presentation\canvas\search\command_palette.py`


Command Palette for CasareRPA.

A VS Code-style command palette for quick access to all actions via keyboard.


### CommandItem

**Decorators:** `@dataclass`


Represents a command in the palette.


**Attributes:**

- `action: Optional[QAction]`
- `callback: Optional[Callable]`
- `category: str`
- `description: str`
- `name: str`
- `shortcut: str`

### CommandPalette

**Inherits from:** `QDialog`


VS Code-style command palette for quick action access.

Features:
- Fuzzy search through all commands
- Keyboard navigation (Up/Down/Enter/Escape)
- Shows shortcuts for each command
- Categorized commands

Signals:
    command_executed: Emitted when a command is executed (command_name: str)


**Attributes:**

- `command_executed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the command palette. |
| `clear_commands()` | `None` | Clear all registered commands. |
| `eventFilter(obj, event)` | `bool` | Handle keyboard navigation in search input. |
| `keyPressEvent(event)` | `None` | Handle key press events. |
| `register_action(action, category, description)` | `None` | Register a QAction with the command palette. |
| `register_callback(name, callback, shortcut, ...)` | `None` | Register a custom callback with the command palette. |
| `show_palette()` | `None` | Show the command palette. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the command palette.

Args:
    parent: Parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear_commands`

```python
def clear_commands() -> None
```

Clear all registered commands.

##### `eventFilter`

```python
def eventFilter(obj, event) -> bool
```

Handle keyboard navigation in search input.

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `keyPressEvent`

```python
def keyPressEvent(event: QKeyEvent) -> None
```

Handle key press events.

**Parameters:**

- `event: QKeyEvent` *(required)*

##### `register_action`

```python
def register_action(action: QAction, category: str = 'General', description: str = '') -> None
```

Register a QAction with the command palette.

Args:
    action: The action to register
    category: Category for grouping
    description: Optional description override

**Parameters:**

- `action: QAction` *(required)*
- `category: str = 'General'`
- `description: str = ''`

##### `register_callback`

```python
def register_callback(name: str, callback: Callable, shortcut: str = '', description: str = '', category: str = 'General') -> None
```

Register a custom callback with the command palette.

Args:
    name: Command name
    callback: Function to call
    shortcut: Display shortcut text
    description: Command description
    category: Category for grouping

**Parameters:**

- `name: str` *(required)*
- `callback: Callable` *(required)*
- `shortcut: str = ''`
- `description: str = ''`
- `category: str = 'General'`

##### `show_palette`

```python
def show_palette() -> None
```

Show the command palette.

---

## casare_rpa.presentation.canvas.search.node_search

**File:** `src\casare_rpa\presentation\canvas\search\node_search.py`


Node Search Dialog for CasareRPA.

Provides Ctrl+F search functionality to find and navigate to nodes in the canvas.


### NodeSearchDialog

**Inherits from:** `QDialog`


Node search dialog for finding nodes in the canvas.

Features:
- Fuzzy search by node name
- Filter by node type
- Navigate to selected node
- Highlight matches

Signals:
    node_selected: Emitted when user selects a node (node_id: str)


**Attributes:**

- `node_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, parent)` | `None` | Initialize the node search dialog. |
| `eventFilter(obj, event)` | `bool` | Handle keyboard navigation. |
| `keyPressEvent(event)` | `None` | Handle key press. |
| `show_search()` | `None` | Show the search dialog. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', parent: Optional[QWidget] = None) -> None
```

Initialize the node search dialog.

Args:
    graph: The NodeGraph instance to search
    parent: Parent widget

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `parent: Optional[QWidget] = None`

##### `eventFilter`

```python
def eventFilter(obj, event) -> bool
```

Handle keyboard navigation.

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `keyPressEvent`

```python
def keyPressEvent(event: QKeyEvent) -> None
```

Handle key press.

**Parameters:**

- `event: QKeyEvent` *(required)*

##### `show_search`

```python
def show_search() -> None
```

Show the search dialog.

### NodeSearchResult

**Decorators:** `@dataclass`


Search result item.


**Attributes:**

- `category: str`
- `name: str`
- `node_id: str`
- `node_type: str`

---

## casare_rpa.presentation.canvas.search.node_search_dialog

**File:** `src\casare_rpa\presentation\canvas\search\node_search_dialog.py`


Node search dialog for quick node creation.

Provides a blazingly fast fuzzy search interface for finding and creating nodes.

Performance optimizations:
- Uses SearchIndex for pre-computed search data
- Near-instant search (5ms debounce only to batch rapid keystrokes)
- Incremental result caching
- Lightweight UI updates


### NodeSearchDialog

**Inherits from:** `QDialog`


Dialog for searching and selecting nodes to create.

Features:
- Blazingly fast fuzzy search
- Abbreviation matching (e.g., "lf" -> "List Filter")
- Keyboard navigation (Up/Down/Enter/Esc)
- Real-time results with minimal latency


**Attributes:**

- `DEBOUNCE_DELAY_MS: int`
- `node_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - | Initialize the search dialog. |
| `keyPressEvent(event)` | - | Handle keyboard events. |
| `set_node_items(items)` | - | Set the available node items and build the search index. |
| `showEvent(event)` | - | Focus search input when dialog is shown. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None)
```

Initialize the search dialog.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `keyPressEvent`

```python
def keyPressEvent(event: QKeyEvent)
```

Handle keyboard events.

**Parameters:**

- `event: QKeyEvent` *(required)*

##### `set_node_items`

```python
def set_node_items(items: List[Tuple[str, str, str]])
```

Set the available node items and build the search index.

Args:
    items: List of (category, name, description) tuples

**Parameters:**

- `items: List[Tuple[str, str, str]]` *(required)*

##### `showEvent`

```python
def showEvent(event)
```

Focus search input when dialog is shown.

**Parameters:**

- `event` *(required)*

---

## casare_rpa.presentation.canvas.search.searchable_menu

**File:** `src\casare_rpa\presentation\canvas\search\searchable_menu.py`


Searchable context menu for node creation.

Provides a context menu with search functionality at the top.


### SearchableNodeMenu

**Inherits from:** `QMenu`


Context menu with integrated search functionality.

Features:
- Search field at the top of the menu
- Real-time filtering of menu items as you type
- Fuzzy matching (e.g., "b l" matches "Browser Launch")
- Keyboard navigation
- Shift+Enter to create node and auto-connect to last node


**Attributes:**

- `node_creation_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, parent)` | - | Initialize the searchable menu. |
| `add_node_item(category, name, description, ...)` | - | Add a node item to the menu. |
| `build_menu()` | - | Build the menu structure with all node items organized by ca... |
| `eventFilter(obj, event)` | - | Handle keyboard events in the search input. |
| `setup_search()` | - | Setup the search input at the top of the menu. |
| `showEvent(event)` | - | Focus search input when menu is shown. |

#### Method Details

##### `__init__`

```python
def __init__(title: str = '', parent = None)
```

Initialize the searchable menu.

**Parameters:**

- `title: str = ''`
- `parent = None`

##### `add_node_item`

```python
def add_node_item(category: str, name: str, description: str, callback: Callable)
```

Add a node item to the menu.

Args:
    category: Node category
    name: Node name
    description: Node description
    callback: Function to call when node is selected

**Parameters:**

- `category: str` *(required)*
- `name: str` *(required)*
- `description: str` *(required)*
- `callback: Callable` *(required)*

##### `build_menu`

```python
def build_menu()
```

Build the menu structure with all node items organized by category.

##### `eventFilter`

```python
def eventFilter(obj, event)
```

Handle keyboard events in the search input.

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `setup_search`

```python
def setup_search()
```

Setup the search input at the top of the menu.

##### `showEvent`

```python
def showEvent(event)
```

Focus search input when menu is shown.

**Parameters:**

- `event` *(required)*

---

## casare_rpa.presentation.canvas.selectors.desktop_selector_builder

**File:** `src\casare_rpa\presentation\canvas\selectors\desktop_selector_builder.py`


Desktop Selector Builder Dialog

Modern UiPath-inspired dialog for visually building desktop element selectors
with element picking, tree view, and multiple selector strategies.


### DesktopSelectorBuilder

**Inherits from:** `QDialog`


Main dialog for building desktop element selectors.

Features:
- Element picker with hover highlighting
- Hierarchical element tree viewer
- Multiple selector generation strategies
- Real-time validation
- JSON selector editor
- Properties panel


**Attributes:**

- `selector_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, target_node, target_property)` | - |  |
| `get_selected_selector()` | `Optional[Dict[str, Any]]` | Get the selected selector dictionary |

#### Method Details

##### `__init__`

```python
def __init__(parent = None, target_node = None, target_property: str = 'selector')
```

**Parameters:**

- `parent = None`
- `target_node = None`
- `target_property: str = 'selector'`

##### `get_selected_selector`

```python
def get_selected_selector() -> Optional[Dict[str, Any]]
```

Get the selected selector dictionary

---

## casare_rpa.presentation.canvas.selectors.element_picker

**File:** `src\casare_rpa\presentation\canvas\selectors\element_picker.py`


Element Picker Overlay

Full-screen transparent overlay for visually selecting desktop UI elements
with hover highlighting and click-to-select functionality.


### Functions

#### `activate_element_picker`

```python
def activate_element_picker(callback_on_select = None, callback_on_cancel = None)
```

Activate element picker overlay.

Args:
    callback_on_select: Function to call with selected DesktopElement
    callback_on_cancel: Function to call when cancelled

Returns:
    ElementPickerOverlay instance


### ElementPickerOverlay

**Inherits from:** `QWidget`


Full-screen transparent overlay for picking desktop elements.

Features:
- Transparent background
- Red highlight on hover
- Click to select element
- ESC to cancel
- Global hotkey support (Ctrl+Shift+F3)


**Attributes:**

- `cancelled: Signal`
- `element_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - |  |
| `closeEvent(event)` | - | Cleanup on close |
| `keyPressEvent(event)` | - | Handle key press - ESC to cancel |
| `mousePressEvent(event)` | - | Handle mouse click - select element |
| `paintEvent(event)` | - | Paint the highlight overlay |

#### Method Details

##### `__init__`

```python
def __init__(parent = None)
```

**Parameters:**

- `parent = None`

##### `closeEvent`

```python
def closeEvent(event)
```

Cleanup on close

**Parameters:**

- `event` *(required)*

##### `keyPressEvent`

```python
def keyPressEvent(event)
```

Handle key press - ESC to cancel

**Parameters:**

- `event` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event)
```

Handle mouse click - select element

**Parameters:**

- `event` *(required)*

##### `paintEvent`

```python
def paintEvent(event)
```

Paint the highlight overlay

**Parameters:**

- `event` *(required)*

---

## casare_rpa.presentation.canvas.selectors.element_tree_widget

**File:** `src\casare_rpa\presentation\canvas\selectors\element_tree_widget.py`


Element Tree Widget

Hierarchical tree view for displaying desktop UI element structure
with lazy loading and custom styling.


### ElementTreeItem

**Inherits from:** `QTreeWidgetItem`


Custom tree item that holds a DesktopElement reference


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(element, parent)` | - |  |
| `load_children()` | - | Lazy load children elements |

#### Method Details

##### `__init__`

```python
def __init__(element: DesktopElement, parent = None)
```

**Parameters:**

- `element: DesktopElement` *(required)*
- `parent = None`

##### `load_children`

```python
def load_children()
```

Lazy load children elements

### ElementTreeWidget

**Inherits from:** `QWidget`


Widget containing element tree view with search functionality


**Attributes:**

- `element_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - |  |
| `expand_to_element(target_element)` | `None` | Expand tree to show and select a specific element. |
| `get_selected_element()` | `Optional[DesktopElement]` | Get the currently selected element |
| `load_tree(root_element)` | - | Load element tree starting from root element |
| `refresh()` | - | Refresh the tree from current root element |

#### Method Details

##### `__init__`

```python
def __init__(parent = None)
```

**Parameters:**

- `parent = None`

##### `expand_to_element`

```python
def expand_to_element(target_element: DesktopElement) -> None
```

Expand tree to show and select a specific element.

Requires walking up the tree to find the path from root to target.
Currently not implemented - would need parent tracking in DesktopElement.

Args:
    target_element: Element to expand to

**Parameters:**

- `target_element: DesktopElement` *(required)*

##### `get_selected_element`

```python
def get_selected_element() -> Optional[DesktopElement]
```

Get the currently selected element

##### `load_tree`

```python
def load_tree(root_element: DesktopElement)
```

Load element tree starting from root element

Args:
    root_element: Root DesktopElement to display

**Parameters:**

- `root_element: DesktopElement` *(required)*

##### `refresh`

```python
def refresh()
```

Refresh the tree from current root element

---

## casare_rpa.presentation.canvas.selectors.selector_dialog

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_dialog.py`


Selector Picker Dialog - PySide6 UI
Beautiful, modern dialog for managing and testing selectors


### SelectorDialog

**Inherits from:** `QDialog`


Modern dialog for selecting and testing element selectors
Shows all generated strategies with validation and preview


**Attributes:**

- `selector_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(fingerprint, test_callback, target_node, ...)` | - |  |
| `apply_styles()` | - | Apply dark mode styling |
| `get_selected_selector()` | `tuple[str, str]` | Get the selected selector value and type |
| `populate_data()` | - | Populate selectors list with strategies |
| `setup_ui()` | - | Build the UI layout |

#### Method Details

##### `__init__`

```python
def __init__(fingerprint: ElementFingerprint, test_callback: Optional[Callable] = None, target_node = None, target_property: str = 'selector', parent = None)
```

**Parameters:**

- `fingerprint: ElementFingerprint` *(required)*
- `test_callback: Optional[Callable] = None`
- `target_node = None`
- `target_property: str = 'selector'`
- `parent = None`

##### `apply_styles`

```python
def apply_styles()
```

Apply dark mode styling

##### `get_selected_selector`

```python
def get_selected_selector() -> tuple[str, str]
```

Get the selected selector value and type

##### `populate_data`

```python
def populate_data()
```

Populate selectors list with strategies

##### `setup_ui`

```python
def setup_ui()
```

Build the UI layout

---

## casare_rpa.presentation.canvas.selectors.selector_integration

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_integration.py`


Selector Integration Module
Connects selector picking to the main application and node graph


### SelectorIntegration

**Inherits from:** `QObject`


Integrates selector picking with the main application
Manages global hotkeys and node property updates


**Attributes:**

- `recording_complete: Signal`
- `selector_picked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - |  |
| `async initialize_for_page(page)` | - | Initialize selector functionality for a Playwright page |
| `is_active()` | `bool` | Check if any selector mode is active |
| `is_picking()` | `bool` | Check if picking mode is active |
| `is_recording()` | `bool` | Check if recording mode is active |
| `async start_picking(target_node, target_property)` | - | Start selector picking mode |
| `async start_recording()` | - | Start workflow recording mode |
| `async stop_selector_mode()` | - | Stop any active selector mode |

#### Method Details

##### `__init__`

```python
def __init__(parent = None)
```

**Parameters:**

- `parent = None`

##### `initialize_for_page`

```python
async def initialize_for_page(page)
```

Initialize selector functionality for a Playwright page

Args:
    page: Playwright Page object

**Parameters:**

- `page` *(required)*

##### `is_active`

```python
@property
def is_active() -> bool
```

Check if any selector mode is active

##### `is_picking`

```python
@property
def is_picking() -> bool
```

Check if picking mode is active

##### `is_recording`

```python
@property
def is_recording() -> bool
```

Check if recording mode is active

##### `start_picking`

```python
async def start_picking(target_node = None, target_property: str = 'selector')
```

Start selector picking mode

Args:
    target_node: Optional node to update with selected selector
    target_property: Property name to update (default: "selector")

**Parameters:**

- `target_node = None`
- `target_property: str = 'selector'`

##### `start_recording`

```python
async def start_recording()
```

Start workflow recording mode

##### `stop_selector_mode`

```python
async def stop_selector_mode()
```

Stop any active selector mode

---

## casare_rpa.presentation.canvas.selectors.selector_strategy

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_strategy.py`


Desktop Selector Strategy Generator

Auto-generates multiple selector strategies for desktop UI elements
with confidence scoring and validation.


### Functions

#### `filter_best_selectors`

```python
def filter_best_selectors(strategies: List[SelectorStrategy], max_count: int = 5) -> List[SelectorStrategy]
```

Filter to keep only the best selector strategies.

Args:
    strategies: List of all generated strategies
    max_count: Maximum number to keep

Returns:
    Filtered list of best strategies

#### `generate_selectors`

```python
def generate_selectors(element: DesktopElement, parent_control: Optional[auto.Control] = None) -> List[SelectorStrategy]
```

Generate multiple selector strategies for a desktop element.

Strategies (in priority order):
1. AutomationId - Most reliable if available
2. Name - Good for buttons, labels
3. ControlType + Name - Specific matching
4. ControlType + Index - Fallback
5. Path-based - Hierarchical selector

Args:
    element: DesktopElement to generate selectors for
    parent_control: Optional parent control for relative selectors

Returns:
    List of SelectorStrategy objects, sorted by confidence/score

#### `validate_selector_uniqueness`

```python
def validate_selector_uniqueness(selector: SelectorStrategy, parent_control: auto.Control, timeout: float = 2.0) -> bool
```

Validate if a selector is unique (finds exactly one element).

Args:
    selector: SelectorStrategy to validate
    parent_control: Parent control to search within
    timeout: Timeout for search

Returns:
    True if selector finds exactly one element


### ConfidenceLevel

**Inherits from:** `Enum`


Confidence level for selector reliability


**Attributes:**

- `HIGH: str`
- `LOW: str`
- `MEDIUM: str`

### SelectorStrategy

**Decorators:** `@dataclass`


Represents a single selector strategy with metadata


**Attributes:**

- `confidence: ConfidenceLevel`
- `description: str`
- `is_unique: bool`
- `properties: Dict[str, Any]`
- `score: float`
- `strategy: str`
- `value: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Convert to selector dictionary format |

#### Method Details

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to selector dictionary format

---

## casare_rpa.presentation.canvas.selectors.selector_validator

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_validator.py`


Selector Validator

Real-time validation of desktop selectors with performance metrics
and visual feedback.


### Functions

#### `validate_selector_sync`

```python
def validate_selector_sync(selector: Dict[str, Any], parent_control: Optional[auto.Control] = None) -> ValidationResult
```

Convenience function to validate a selector synchronously.

Args:
    selector: Selector dictionary
    parent_control: Parent control to search within

Returns:
    ValidationResult


### SelectorValidator


Validates desktop selectors in real-time


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent_control)` | - | Initialize validator |
| `get_element_at_position(x, y)` | `Optional[DesktopElement]` | Get element at screen position. |
| `highlight_matches(selector, max_count)` | - | Highlight all elements matching selector (for debugging). |
| `quick_check(selector)` | `bool` | Quick check if selector finds at least one element. |
| `validate(selector, find_all)` | `ValidationResult` | Validate a selector. |
| `validate_multiple(selectors)` | `List[ValidationResult]` | Validate multiple selectors. |

#### Method Details

##### `__init__`

```python
def __init__(parent_control: Optional[auto.Control] = None)
```

Initialize validator

Args:
    parent_control: Parent control to search within (None = desktop root)

**Parameters:**

- `parent_control: Optional[auto.Control] = None`

##### `get_element_at_position`

```python
def get_element_at_position(x: int, y: int) -> Optional[DesktopElement]
```

Get element at screen position.

Args:
    x: Screen X coordinate
    y: Screen Y coordinate

Returns:
    DesktopElement if found, None otherwise

**Parameters:**

- `x: int` *(required)*
- `y: int` *(required)*

##### `highlight_matches`

```python
def highlight_matches(selector: Dict[str, Any], max_count: int = 10)
```

Highlight all elements matching selector (for debugging).

Args:
    selector: Selector dictionary
    max_count: Maximum number of elements to highlight

Note:
    This is a stub - actual highlighting would require additional UI support

**Parameters:**

- `selector: Dict[str, Any]` *(required)*
- `max_count: int = 10`

##### `quick_check`

```python
def quick_check(selector: Dict[str, Any]) -> bool
```

Quick check if selector finds at least one element.

Args:
    selector: Selector dictionary

Returns:
    True if at least one element found

**Parameters:**

- `selector: Dict[str, Any]` *(required)*

##### `validate`

```python
def validate(selector: Dict[str, Any], find_all: bool = False) -> ValidationResult
```

Validate a selector.

Args:
    selector: Selector dictionary to validate
    find_all: If True, find all matching elements; if False, stop at first match

Returns:
    ValidationResult with status and metrics

**Parameters:**

- `selector: Dict[str, Any]` *(required)*
- `find_all: bool = False`

##### `validate_multiple`

```python
def validate_multiple(selectors: List[Dict[str, Any]]) -> List[ValidationResult]
```

Validate multiple selectors.

Args:
    selectors: List of selector dictionaries

Returns:
    List of ValidationResult objects

**Parameters:**

- `selectors: List[Dict[str, Any]]` *(required)*

### ValidationResult

**Decorators:** `@dataclass`


Result of selector validation


**Attributes:**

- `element_count: int`
- `elements: Optional[List[DesktopElement]]`
- `error_message: Optional[str]`
- `execution_time_ms: float`
- `status: ValidationStatus`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `color()` | `str` | Get status color (hex) |
| `icon()` | `str` | Get status icon |
| `is_unique()` | `bool` | Check if selector is unique (finds exactly one element) |
| `is_valid()` | `bool` | Check if selector is valid (finds at least one element) |
| `message()` | `str` | Get human-readable status message |

#### Method Details

##### `color`

```python
@property
def color() -> str
```

Get status color (hex)

##### `icon`

```python
@property
def icon() -> str
```

Get status icon

##### `is_unique`

```python
@property
def is_unique() -> bool
```

Check if selector is unique (finds exactly one element)

##### `is_valid`

```python
@property
def is_valid() -> bool
```

Check if selector is valid (finds at least one element)

##### `message`

```python
@property
def message() -> str
```

Get human-readable status message

### ValidationStatus

**Inherits from:** `Enum`


Validation result status


**Attributes:**

- `ERROR: str`
- `NOT_FOUND: str`
- `VALID_MULTIPLE: str`
- `VALID_UNIQUE: str`

---

## casare_rpa.presentation.canvas.serialization.workflow_deserializer

**File:** `src\casare_rpa\presentation\canvas\serialization\workflow_deserializer.py`


Workflow Deserializer for Canvas.

Loads workflow JSON and recreates visual nodes in NodeGraphQt graph.
This is the inverse of WorkflowSerializer.


### WorkflowDeserializer


Deserializes workflow JSON back into NodeGraphQt visual graph.

Reads workflow JSON files and recreates:
- Visual nodes with their properties
- Connections between nodes
- Node positions
- Variables and settings


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, main_window)` | - | Initialize the deserializer. |
| `deserialize(workflow_data)` | `bool` | Deserialize workflow dict into visual graph. |
| `load_from_file(file_path)` | `bool` | Load workflow from JSON file. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', main_window)
```

Initialize the deserializer.

Args:
    graph: NodeGraphQt NodeGraph instance
    main_window: MainWindow for accessing bottom panel

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `main_window` *(required)*

##### `deserialize`

```python
def deserialize(workflow_data: Dict) -> bool
```

Deserialize workflow dict into visual graph.

Args:
    workflow_data: Workflow dictionary (from WorkflowSerializer format)

Returns:
    True if deserialized successfully, False otherwise

**Parameters:**

- `workflow_data: Dict` *(required)*

##### `load_from_file`

```python
def load_from_file(file_path: str) -> bool
```

Load workflow from JSON file.

Args:
    file_path: Path to the workflow JSON file

Returns:
    True if loaded successfully, False otherwise

**Parameters:**

- `file_path: str` *(required)*

---

## casare_rpa.presentation.canvas.serialization.workflow_serializer

**File:** `src\casare_rpa\presentation\canvas\serialization\workflow_serializer.py`


Workflow Serializer for Canvas.

Converts NodeGraphQt visual graph to workflow JSON dict matching
the format expected by load_workflow_from_dict().


### WorkflowSerializer


Serializes NodeGraphQt graph to workflow JSON.

Extracts nodes, connections, variables, and frames from the visual graph
and converts them to the workflow schema format used by the execution engine.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, main_window)` | - | Initialize the serializer. |
| `serialize()` | `dict` | Serialize the entire graph to workflow dict. |

#### Method Details

##### `__init__`

```python
def __init__(graph: 'NodeGraph', main_window: 'MainWindow')
```

Initialize the serializer.

Args:
    graph: NodeGraphQt NodeGraph instance
    main_window: MainWindow for accessing bottom panel variables

**Parameters:**

- `graph: 'NodeGraph'` *(required)*
- `main_window: 'MainWindow'` *(required)*

##### `serialize`

```python
def serialize() -> dict
```

Serialize the entire graph to workflow dict.

Returns:
    Complete workflow dict matching WorkflowSchema format

---

## casare_rpa.presentation.canvas.services.trigger_event_handler

**File:** `src\casare_rpa\presentation\canvas\services\trigger_event_handler.py`


CasareRPA - Qt Trigger Event Handler

Presentation layer implementation of the TriggerEventHandler protocol.
Bridges application-layer trigger events to the Qt UI.

Architecture:
    Application Layer (TriggerEventHandler Protocol)
           ^
           |
    Presentation Layer (QtTriggerEventHandler - implements protocol)
           |
           v
    Qt Components (MainWindow, BottomPanel, etc.)


### Functions

#### `create_trigger_event_handler`

```python
def create_trigger_event_handler(main_window: Optional['MainWindow'] = None) -> 'QtTriggerEventHandler'
```

Factory function to create a QtTriggerEventHandler.

Args:
    main_window: The main window instance. If None, will return
                 a handler that logs warnings when methods are called.

Returns:
    QtTriggerEventHandler instance


### QtTriggerEventHandler


Qt-based implementation of TriggerEventHandler protocol.

Handles trigger events from CanvasTriggerRunner by delegating to
Qt UI components. All UI operations are marshaled to the main thread
using Qt's thread-safe mechanisms.

This class implements the TriggerEventHandler protocol from
casare_rpa.application.execution.interfaces.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize with the MainWindow reference. |
| `get_trigger_count(trigger_id)` | `int` | Get the current execution count for a trigger. |
| `request_workflow_run()` | `None` | Request the application to run the current workflow. |
| `update_trigger_stats(trigger_id, count, last_triggered)` | `None` | Update the UI with trigger statistics. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize with the MainWindow reference.

Args:
    main_window: The main application window

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `get_trigger_count`

```python
def get_trigger_count(trigger_id: str) -> int
```

Get the current execution count for a trigger.

Note: This method may be called from a background thread,
so we access the UI data carefully.

Args:
    trigger_id: The ID of the trigger

Returns:
    Current execution count, or 0 if not found

**Parameters:**

- `trigger_id: str` *(required)*

##### `request_workflow_run`

```python
def request_workflow_run() -> None
```

Request the application to run the current workflow.

Uses QMetaObject.invokeMethod to ensure the call happens
on the Qt main thread, regardless of which thread this
method is called from.

##### `update_trigger_stats`

```python
def update_trigger_stats(trigger_id: str, count: int, last_triggered: str) -> None
```

Update the UI with trigger statistics.

Uses QTimer.singleShot to ensure the UI update happens
on the main thread.

Args:
    trigger_id: The ID of the trigger that fired
    count: The new execution count
    last_triggered: ISO timestamp of when the trigger last fired

**Parameters:**

- `trigger_id: str` *(required)*
- `count: int` *(required)*
- `last_triggered: str` *(required)*

---

## casare_rpa.presentation.canvas.services.websocket_bridge

**File:** `src\casare_rpa\presentation\canvas\services\websocket_bridge.py`


WebSocket Bridge Service for Fleet Dashboard.

Bridges async WebSocket events from OrchestratorClient to Qt signals
for thread-safe UI updates. Implements exponential backoff reconnection.


### Functions

#### `get_websocket_bridge`

```python
def get_websocket_bridge() -> WebSocketBridge
```

Get or create singleton WebSocketBridge.


### JobStatusUpdate

**Decorators:** `@dataclass`


Real-time job status update.


**Attributes:**

- `current_node: str`
- `error_message: str`
- `job_id: str`
- `progress: int`
- `status: str`
- `timestamp: Optional[datetime]`

### QueueMetricsUpdate

**Decorators:** `@dataclass`


Real-time queue metrics update.


**Attributes:**

- `active_jobs: int`
- `completed_today: int`
- `depth: int`
- `failed_today: int`
- `timestamp: Optional[datetime]`

### RobotStatusUpdate

**Decorators:** `@dataclass`


Real-time robot status update.


**Attributes:**

- `cpu_percent: float`
- `current_job: Optional[str]`
- `memory_mb: float`
- `robot_id: str`
- `status: str`
- `timestamp: Optional[datetime]`

### WebSocketBridge

**Inherits from:** `QObject`


Bridge between async WebSocket events and Qt signals.

Features:
- Converts OrchestratorClient callbacks to Qt signals
- Thread-safe signal emission for UI updates
- Exponential backoff reconnection (1s, 2s, 4s, 8s, max 60s)
- Automatic reconnection on disconnect
- Connection status tracking

Usage:
    bridge = WebSocketBridge()
    bridge.robot_status_changed.connect(on_robot_update)
    await bridge.connect(orchestrator_client)


**Attributes:**

- `connection_error: Signal`
- `connection_status_changed: Signal`
- `job_status_changed: Signal`
- `jobs_batch_updated: Signal`
- `queue_metrics_changed: Signal`
- `robot_status_changed: Signal`
- `robots_batch_updated: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize WebSocket bridge. |
| `async connect(client)` | `bool` | Connect bridge to OrchestratorClient and start receiving eve... |
| `async disconnect()` | `None` | Disconnect bridge from WebSocket. |
| `is_connected()` | `bool` | Check if bridge is connected to WebSocket. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QObject] = None) -> None
```

Initialize WebSocket bridge.

**Parameters:**

- `parent: Optional[QObject] = None`

##### `connect`

```python
async def connect(client: 'OrchestratorClient') -> bool
```

Connect bridge to OrchestratorClient and start receiving events.

Args:
    client: OrchestratorClient instance

Returns:
    True if connected successfully

**Parameters:**

- `client: 'OrchestratorClient'` *(required)*

##### `disconnect`

```python
async def disconnect() -> None
```

Disconnect bridge from WebSocket.

##### `is_connected`

```python
@property
def is_connected() -> bool
```

Check if bridge is connected to WebSocket.

---

## casare_rpa.presentation.canvas.theme

**File:** `src\casare_rpa\presentation\canvas\theme.py`


Unified Theme System for CasareRPA Canvas.

Provides consistent styling across the visual workflow editor,
aligned with the Orchestrator color palette for a cohesive look.


### Functions

#### `get_canvas_stylesheet`

```python
def get_canvas_stylesheet() -> str
```

Generate the main Canvas application stylesheet.

Returns:
    Complete QSS stylesheet for the Canvas application.

#### `get_node_status_color`

```python
def get_node_status_color(status: str) -> str
```

Get the color for a node execution status.

Args:
    status: Node status string (idle, running, success, error, skipped)

Returns:
    Hex color string for the status.

#### `get_status_color`

```python
def get_status_color(status: str) -> str
```

Get color for a general status string.

Args:
    status: Status string.

Returns:
    Hex color string.

#### `get_wire_color`

```python
def get_wire_color(data_type: str) -> str
```

Get the color for a connection wire based on data type.

Args:
    data_type: The data type of the connection.

Returns:
    Hex color string for the wire.


### CanvasThemeColors

**Decorators:** `@dataclass`


VSCode Dark+ theme colors - exact replication from microsoft/vscode repository.

Colors sourced from dark_vs.json and dark_plus.json for pixel-perfect VSCode appearance.


**Attributes:**

- `accent_error: str`
- `accent_hover: str`
- `accent_primary: str`
- `accent_secondary: str`
- `accent_success: str`
- `accent_warning: str`
- `bg_canvas: str`
- `bg_dark: str`
- `bg_darkest: str`
- `bg_header: str`
- `bg_hover: str`
- `bg_light: str`
- `bg_lighter: str`
- `bg_medium: str`
- `bg_node: str`
- `bg_node_header: str`
- `bg_node_selected: str`
- `bg_panel: str`
- `bg_selected: str`
- `border: str`
- `border_dark: str`
- `border_focus: str`
- `border_light: str`
- `dock_title_bg: str`
- `dock_title_text: str`
- `input_bg: str`
- `node_breakpoint: str`
- `node_error: str`
- `node_idle: str`
- `node_running: str`
- `node_skipped: str`
- `node_success: str`
- `selection_bg: str`
- `splitter_handle: str`
- `status_error: str`
- `status_idle: str`
- `status_info: str`
- `status_running: str`
- `status_success: str`
- `status_warning: str`
- `text_disabled: str`
- `text_header: str`
- `text_muted: str`
- `text_primary: str`
- `text_secondary: str`
- `toolbar_bg: str`
- `toolbar_border: str`
- `toolbar_button_hover: str`
- `toolbar_button_pressed: str`
- `wire_bool: str`
- `wire_data: str`
- `wire_dict: str`
- `wire_exec: str`
- `wire_list: str`
- `wire_number: str`
- `wire_string: str`

---

## casare_rpa.presentation.canvas.ui.action_factory

**File:** `src\casare_rpa\presentation\canvas\ui\action_factory.py`


Action Factory for MainWindow.

This module provides a factory class for creating and configuring QActions
used in the MainWindow's menus, toolbar, and keyboard shortcuts.

Extracts ~400 lines of action creation code from MainWindow to improve
maintainability and reduce MainWindow's line count.


### ActionFactory

**Inherits from:** `QObject`


Factory for creating and managing MainWindow actions.

This class centralizes all QAction creation, configuration, and
hotkey loading for the MainWindow. It reduces code duplication
and makes action management more maintainable.

Attributes:
    actions: Dictionary of action_name -> QAction
    main_window: Reference to parent MainWindow

Example:
    factory = ActionFactory(main_window)
    factory.create_all_actions()
    factory.load_hotkeys(hotkey_settings)

    # Access actions
    run_action = factory.actions["run"]


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize the action factory. |
| `actions()` | `Dict[str, QAction]` | Dictionary of all created actions. |
| `create_all_actions()` | `None` | Create all actions for the MainWindow. |
| `get_action(name)` | `Optional[QAction]` | Get action by name. |
| `load_hotkeys(hotkey_settings)` | `None` | Load saved hotkeys and apply them to actions. |
| `set_actions_enabled(action_names, enabled)` | `None` | Enable or disable multiple actions at once. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize the action factory.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `actions`

```python
@property
def actions() -> Dict[str, QAction]
```

Dictionary of all created actions.

##### `create_all_actions`

```python
def create_all_actions() -> None
```

Create all actions for the MainWindow.

##### `get_action`

```python
def get_action(name: str) -> Optional[QAction]
```

Get action by name.

Args:
    name: Action name

Returns:
    QAction or None if not found

**Parameters:**

- `name: str` *(required)*

##### `load_hotkeys`

```python
def load_hotkeys(hotkey_settings) -> None
```

Load saved hotkeys and apply them to actions.

Args:
    hotkey_settings: HotkeySettings instance with saved shortcuts

**Parameters:**

- `hotkey_settings` *(required)*

##### `set_actions_enabled`

```python
def set_actions_enabled(action_names: List[str], enabled: bool) -> None
```

Enable or disable multiple actions at once.

Args:
    action_names: List of action names to modify
    enabled: Whether to enable or disable

**Parameters:**

- `action_names: List[str]` *(required)*
- `enabled: bool` *(required)*

---

## casare_rpa.presentation.canvas.ui.base_widget

**File:** `src\casare_rpa\presentation\canvas\ui\base_widget.py`


Base widget class for all UI components.

Provides common patterns, stylesheet management, and signal/slot conventions
for all reusable UI widgets in the CasareRPA Canvas application.


### BaseDialog

**Inherits from:** `BaseWidget`


Base class for dialogs.

Extends BaseWidget with dialog-specific functionality like
accept/reject handling and validation.

Signals:
    accepted: Emitted when dialog is accepted
    rejected: Emitted when dialog is rejected


**Attributes:**

- `accepted: Signal`
- `rejected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the dialog. |
| `get_result()` | `Optional[Any]` | Get dialog result. |
| `set_result(result)` | `None` | Set dialog result. |
| `validate()` | `bool` | Validate dialog input. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the dialog.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `get_result`

```python
def get_result() -> Optional[Any]
```

Get dialog result.

Returns:
    Dialog result value

##### `set_result`

```python
def set_result(result: Any) -> None
```

Set dialog result.

Args:
    result: Result value

**Parameters:**

- `result: Any` *(required)*

##### `validate`

```python
def validate() -> bool
```

Validate dialog input.

Override this method to implement custom validation logic.

Returns:
    True if validation passes, False otherwise

### BaseDockWidget

**Inherits from:** `BaseWidget`


Base class for dockable panels.

Extends BaseWidget with dock-specific functionality like
visibility toggles and position management.

Signals:
    visibility_changed: Emitted when dock visibility changes (bool: visible)


**Attributes:**

- `visibility_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, parent)` | `None` | Initialize the dock widget. |
| `get_title()` | `str` | Get dock widget title. |
| `set_title(title)` | `None` | Set dock widget title. |

#### Method Details

##### `__init__`

```python
def __init__(title: str, parent: Optional[QWidget] = None) -> None
```

Initialize the dock widget.

Args:
    title: Dock widget title
    parent: Optional parent widget

**Parameters:**

- `title: str` *(required)*
- `parent: Optional[QWidget] = None`

##### `get_title`

```python
def get_title() -> str
```

Get dock widget title.

Returns:
    Dock title

##### `set_title`

```python
def set_title(title: str) -> None
```

Set dock widget title.

Args:
    title: New dock title

**Parameters:**

- `title: str` *(required)*

### BaseWidget

**Inherits from:** `QWidget`


Abstract base class for all reusable UI widgets.

Provides:
- Consistent initialization pattern
- Stylesheet management
- Common signals
- Logging integration

Signals:
    value_changed: Emitted when widget value changes (object: new_value)
    state_changed: Emitted when widget state changes (str: state_name, Any: state_value)


**Attributes:**

- `state_changed: Signal`
- `value_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the base widget. |
| `apply_stylesheet()` | `None` | Apply component stylesheet. |
| `clear_state()` | `None` | Clear all internal state. |
| `connect_signals()` | `None` | Connect internal signal/slot connections. |
| `get_state(key, default)` | `Any` | Get internal state value. |
| `is_initialized()` | `bool` | Check if widget is fully initialized. |
| `set_state(key, value)` | `None` | Set internal state value. |
| `setup_ui()` | `None` | Set up the user interface elements. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the base widget.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `apply_stylesheet`

```python
def apply_stylesheet() -> None
```

Apply component stylesheet.

Override this method to customize component appearance.
Default implementation applies dark theme styles.

##### `clear_state`

```python
def clear_state() -> None
```

Clear all internal state.

##### `connect_signals`

```python
def connect_signals() -> None
```

Connect internal signal/slot connections.

Override this method to set up signal/slot connections
between child widgets. Default implementation does nothing.

##### `get_state`

```python
def get_state(key: str, default: Any = None) -> Any
```

Get internal state value.

Args:
    key: State key
    default: Default value if key not found

Returns:
    State value or default

**Parameters:**

- `key: str` *(required)*
- `default: Any = None`

##### `is_initialized`

```python
def is_initialized() -> bool
```

Check if widget is fully initialized.

Returns:
    True if initialization completed successfully

##### `set_state`

```python
def set_state(key: str, value: Any) -> None
```

Set internal state value.

Args:
    key: State key
    value: State value

**Parameters:**

- `key: str` *(required)*
- `value: Any` *(required)*

##### `setup_ui`

```python
def setup_ui() -> None
```

Set up the user interface elements.

This method must be implemented by subclasses to create
and arrange all UI widgets.

### QABCMeta

**Inherits from:** `type(QWidget)`, `ABCMeta`


Metaclass combining Qt's metaclass with ABCMeta.


---

## casare_rpa.presentation.canvas.ui.debug_panel

**File:** `src\casare_rpa\presentation\canvas\ui\debug_panel.py`


Enhanced Debug Panel UI Component.

Provides comprehensive debugging capabilities:
- Execution logs with filtering
- Variable inspector with real-time updates
- Call stack visualization
- Watch expressions
- Breakpoint management (regular, conditional, hit-count)
- Expression evaluation / Debug REPL console
- Execution state snapshot/restore

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.


### DebugPanel

**Inherits from:** `QDockWidget`


Enhanced dockable debug panel for interactive workflow debugging.

Features:
- Execution logs with filtering and navigation
- Variable inspector with tree view
- Call stack visualization
- Watch expressions
- Breakpoint management with conditions
- Debug REPL console for expression evaluation
- Execution snapshots

Signals:
    navigate_to_node: Emitted when user requests to navigate to node (str: node_id)
    breakpoint_toggled: Emitted when breakpoint is toggled (str: node_id, bool: enabled)
    breakpoint_condition_changed: Emitted when condition is set (str: node_id, str: condition)
    watch_added: Emitted when watch expression is added (str: expression)
    watch_removed: Emitted when watch expression is removed (str: expression)
    step_over_requested: Emitted when step over is requested
    step_into_requested: Emitted when step into is requested
    step_out_requested: Emitted when step out is requested
    continue_requested: Emitted when continue is requested
    snapshot_requested: Emitted when snapshot is requested
    snapshot_restore_requested: Emitted when snapshot restore is requested (str: id)
    expression_evaluated: Emitted when expression is evaluated (str: expr, result)
    clear_requested: Emitted when user requests to clear logs


**Attributes:**

- `COL_LEVEL: int`
- `COL_MESSAGE: int`
- `COL_NODE: int`
- `COL_TIME: int`
- `breakpoint_condition_changed: Signal`
- `breakpoint_toggled: Signal`
- `clear_requested: Signal`
- `continue_requested: Signal`
- `expression_evaluated: Signal`
- `navigate_to_node: Signal`
- `snapshot_requested: Signal`
- `snapshot_restore_requested: Signal`
- `step_into_requested: Signal`
- `step_out_requested: Signal`
- `step_over_requested: Signal`
- `watch_added: Signal`
- `watch_removed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, debug_controller)` | `None` | Initialize the enhanced debug panel. |
| `add_breakpoint_to_list(node_id, node_name, bp_type, ...)` | `None` | Add a breakpoint to the list display. |
| `add_log(level, message, node_id, ...)` | `None` | Add a log entry. |
| `clear_breakpoints()` | `None` | Clear all breakpoints from display. |
| `clear_logs()` | `None` | Clear all log entries. |
| `remove_breakpoint_from_list(node_id)` | `None` | Remove a breakpoint from the list display. |
| `set_debug_controller(controller)` | `None` | Set the debug controller for integration. |
| `update_call_stack(frames)` | `None` | Update the call stack display. |
| `update_variables(variables)` | `None` | Update the variable inspector with new values. |
| `update_watches(watches)` | `None` | Update the watch expressions display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None, debug_controller: Optional['DebugController'] = None) -> None
```

Initialize the enhanced debug panel.

Args:
    parent: Optional parent widget
    debug_controller: Optional debug controller for integration

**Parameters:**

- `parent: Optional[QWidget] = None`
- `debug_controller: Optional['DebugController'] = None`

##### `add_breakpoint_to_list`

```python
def add_breakpoint_to_list(node_id: str, node_name: str, bp_type: str = 'Regular', condition: str = '', hit_count: int = 0, enabled: bool = True) -> None
```

Add a breakpoint to the list display.

Args:
    node_id: Node ID
    node_name: Node display name
    bp_type: Breakpoint type
    condition: Condition expression
    hit_count: Current hit count
    enabled: Whether enabled

**Parameters:**

- `node_id: str` *(required)*
- `node_name: str` *(required)*
- `bp_type: str = 'Regular'`
- `condition: str = ''`
- `hit_count: int = 0`
- `enabled: bool = True`

##### `add_log`

```python
def add_log(level: str, message: str, node_id: Optional[str] = None, node_name: Optional[str] = None) -> None
```

Add a log entry.

Args:
    level: Log level (Info, Warning, Error, Success)
    message: Log message
    node_id: Optional node ID
    node_name: Optional node name

**Parameters:**

- `level: str` *(required)*
- `message: str` *(required)*
- `node_id: Optional[str] = None`
- `node_name: Optional[str] = None`

##### `clear_breakpoints`

```python
def clear_breakpoints() -> None
```

Clear all breakpoints from display.

##### `clear_logs`

```python
def clear_logs() -> None
```

Clear all log entries.

##### `remove_breakpoint_from_list`

```python
def remove_breakpoint_from_list(node_id: str) -> None
```

Remove a breakpoint from the list display.

**Parameters:**

- `node_id: str` *(required)*

##### `set_debug_controller`

```python
def set_debug_controller(controller: 'DebugController') -> None
```

Set the debug controller for integration.

Args:
    controller: Debug controller instance

**Parameters:**

- `controller: 'DebugController'` *(required)*

##### `update_call_stack`

```python
def update_call_stack(frames: List['CallStackFrame']) -> None
```

Update the call stack display.

Args:
    frames: List of call stack frames

**Parameters:**

- `frames: List['CallStackFrame']` *(required)*

##### `update_variables`

```python
def update_variables(variables: Dict[str, Any]) -> None
```

Update the variable inspector with new values.

Args:
    variables: Dictionary of variable name -> value

**Parameters:**

- `variables: Dict[str, Any]` *(required)*

##### `update_watches`

```python
def update_watches(watches: List['WatchExpression']) -> None
```

Update the watch expressions display.

Args:
    watches: List of watch expressions

**Parameters:**

- `watches: List['WatchExpression']` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\credential_manager_dialog.py`


Credential Manager Dialog UI Component.

Full-featured dialog for managing encrypted credentials:
- API Keys (LLM providers)
- Username/Password pairs
- Database connections
- Custom credentials


### ApiKeyTestThread

**Inherits from:** `QThread`


Thread for running API key tests.


**Attributes:**

- `finished: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(provider, api_key, parent)` | - |  |
| `run()` | - | Run the test in this thread. |
| `start()` | - | Start the thread and connect signals. |

#### Method Details

##### `__init__`

```python
def __init__(provider: str, api_key: str, parent = None)
```

**Parameters:**

- `provider: str` *(required)*
- `api_key: str` *(required)*
- `parent = None`

##### `run`

```python
def run()
```

Run the test in this thread.

##### `start`

```python
def start()
```

Start the thread and connect signals.

### ApiKeyTestWorker

**Inherits from:** `QObject`


Worker for testing API keys in a background thread.


**Attributes:**

- `finished: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(provider, api_key)` | `None` |  |
| `run()` | `None` | Test the API key by making a minimal API call. |

#### Method Details

##### `__init__`

```python
def __init__(provider: str, api_key: str) -> None
```

**Parameters:**

- `provider: str` *(required)*
- `api_key: str` *(required)*

##### `run`

```python
def run() -> None
```

Test the API key by making a minimal API call.

### CredentialManagerDialog

**Inherits from:** `QDialog`


Credential management dialog.

Features:
- Add/Edit/Delete credentials
- Organize by category (LLM, Database, Email, Custom)
- Secure display (masked values)
- Search and filter
- Import/Export (future)

Signals:
    credentials_changed: Emitted when credentials are modified


**Attributes:**

- `credentials_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize credential manager dialog. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize credential manager dialog.

**Parameters:**

- `parent: Optional[QWidget] = None`

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_dashboard

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_dashboard.py`


Fleet Dashboard Dialog for CasareRPA Canvas.

Comprehensive admin dashboard for robot fleet management with robots, jobs,
schedules, analytics, and API keys tabs. Supports multi-tenant filtering
and real-time updates via WebSocketBridge.


### FleetDashboardDialog

**Inherits from:** `QDialog`


Full admin dashboard for robot fleet management.

Features:
- Robots tab: View and manage registered robots
- Jobs tab: Monitor job queue and history
- Schedules tab: Manage workflow schedules
- Analytics tab: Fleet statistics and charts
- API Keys tab: Manage robot API keys
- Tenant filtering: Filter by tenant (super admin only)

Signals:
    robot_selected: Emitted when a robot is selected (robot_id)
    robot_edited: Emitted when a robot is edited (robot_id, robot_data)
    robot_deleted: Emitted when a robot is deleted (robot_id)
    job_cancelled: Emitted when a job is cancelled (job_id)
    job_retried: Emitted when a job is retried (job_id)
    schedule_enabled_changed: Emitted when schedule is toggled (schedule_id, enabled)
    schedule_edited: Emitted when schedule edit requested (schedule_id)
    schedule_deleted: Emitted when schedule is deleted (schedule_id)
    schedule_run_now: Emitted when run now is clicked (schedule_id)
    api_key_generated: Emitted when API key generation requested (config_dict)
    api_key_revoked: Emitted when API key revoked (key_id)
    api_key_rotated: Emitted when API key rotation requested (key_id)
    tenant_changed: Emitted when tenant filter changes (tenant_id or None)
    refresh_requested: Emitted when any tab requests refresh


**Attributes:**

- `api_key_generated: Signal`
- `api_key_revoked: Signal`
- `api_key_rotated: Signal`
- `job_cancelled: Signal`
- `job_retried: Signal`
- `refresh_requested: Signal`
- `robot_deleted: Signal`
- `robot_edited: Signal`
- `robot_selected: Signal`
- `schedule_deleted: Signal`
- `schedule_edited: Signal`
- `schedule_enabled_changed: Signal`
- `schedule_run_now: Signal`
- `tenant_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Fleet Dashboard dialog. |
| `connect_websocket_bridge(bridge)` | `None` | Connect to WebSocketBridge for real-time updates. |
| `disconnect_websocket_bridge(bridge)` | `None` | Disconnect from WebSocketBridge. |
| `get_current_tenant_id()` | `Optional[str]` | Get currently selected tenant ID. |
| `get_selected_job()` | `Optional[Dict[str, Any]]` | Get currently selected job from jobs tab. |
| `set_connection_status(connected, message)` | `None` | Set the connection status indicator. |
| `set_current_tenant(tenant_id)` | `None` | Set current tenant selection. |
| `set_status(message)` | `None` | Set status bar message. |
| `set_super_admin(is_super_admin)` | `None` | Set whether current user is a super admin. |
| `show_analytics_tab()` | `None` | Switch to analytics tab. |
| `show_api_keys_tab()` | `None` | Switch to API keys tab. |
| `show_jobs_tab()` | `None` | Switch to jobs tab. |
| `show_robots_tab()` | `None` | Switch to robots tab. |
| `show_schedules_tab()` | `None` | Switch to schedules tab. |
| `update_analytics(analytics)` | `None` | Update analytics tab with new data. |
| `update_api_keys(api_keys)` | `None` | Update API keys tab with new data. |
| `update_api_keys_robots(robots)` | `None` | Update robots list in API keys tab. |
| `update_jobs(jobs)` | `None` | Update jobs tab with new data. |
| `update_robots(robots)` | `None` | Update robots tab with new data. |
| `update_schedules(schedules)` | `None` | Update schedules tab with new data. |
| `update_tenants(tenants)` | `None` | Update available tenants list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Fleet Dashboard dialog.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `connect_websocket_bridge`

```python
def connect_websocket_bridge(bridge: 'WebSocketBridge') -> None
```

Connect to WebSocketBridge for real-time updates.

Subscribes to robot status, job status, and queue metrics events.

Args:
    bridge: WebSocketBridge instance

**Parameters:**

- `bridge: 'WebSocketBridge'` *(required)*

##### `disconnect_websocket_bridge`

```python
def disconnect_websocket_bridge(bridge: 'WebSocketBridge') -> None
```

Disconnect from WebSocketBridge.

Args:
    bridge: WebSocketBridge instance to disconnect

**Parameters:**

- `bridge: 'WebSocketBridge'` *(required)*

##### `get_current_tenant_id`

```python
def get_current_tenant_id() -> Optional[str]
```

Get currently selected tenant ID.

Returns:
    Tenant ID or None if "All Tenants" selected.

##### `get_selected_job`

```python
def get_selected_job() -> Optional[Dict[str, Any]]
```

Get currently selected job from jobs tab.

##### `set_connection_status`

```python
def set_connection_status(connected: bool, message: str = '') -> None
```

Set the connection status indicator.

Args:
    connected: Whether connected to orchestrator
    message: Optional status message

**Parameters:**

- `connected: bool` *(required)*
- `message: str = ''`

##### `set_current_tenant`

```python
def set_current_tenant(tenant_id: Optional[str]) -> None
```

Set current tenant selection.

Args:
    tenant_id: Tenant ID or None for "All Tenants".

**Parameters:**

- `tenant_id: Optional[str]` *(required)*

##### `set_status`

```python
def set_status(message: str) -> None
```

Set status bar message.

Args:
    message: Status message to display

**Parameters:**

- `message: str` *(required)*

##### `set_super_admin`

```python
def set_super_admin(is_super_admin: bool) -> None
```

Set whether current user is a super admin.

Super admins can see and switch between all tenants.

Args:
    is_super_admin: True if user is super admin.

**Parameters:**

- `is_super_admin: bool` *(required)*

##### `show_analytics_tab`

```python
def show_analytics_tab() -> None
```

Switch to analytics tab.

##### `show_api_keys_tab`

```python
def show_api_keys_tab() -> None
```

Switch to API keys tab.

##### `show_jobs_tab`

```python
def show_jobs_tab() -> None
```

Switch to jobs tab.

##### `show_robots_tab`

```python
def show_robots_tab() -> None
```

Switch to robots tab.

##### `show_schedules_tab`

```python
def show_schedules_tab() -> None
```

Switch to schedules tab.

##### `update_analytics`

```python
def update_analytics(analytics: Dict[str, Any]) -> None
```

Update analytics tab with new data.

Args:
    analytics: Analytics data dictionary

**Parameters:**

- `analytics: Dict[str, Any]` *(required)*

##### `update_api_keys`

```python
def update_api_keys(api_keys: List[Dict[str, Any]]) -> None
```

Update API keys tab with new data.

Args:
    api_keys: List of API key dictionaries.

**Parameters:**

- `api_keys: List[Dict[str, Any]]` *(required)*

##### `update_api_keys_robots`

```python
def update_api_keys_robots(robots: List[Dict[str, Any]]) -> None
```

Update robots list in API keys tab.

Args:
    robots: List of robot dictionaries for key generation dropdown.

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*

##### `update_jobs`

```python
def update_jobs(jobs: List[Dict[str, Any]]) -> None
```

Update jobs tab with new data.

Args:
    jobs: List of job dictionaries

**Parameters:**

- `jobs: List[Dict[str, Any]]` *(required)*

##### `update_robots`

```python
def update_robots(robots: List['Robot']) -> None
```

Update robots tab with new data.

Args:
    robots: List of Robot entities

**Parameters:**

- `robots: List['Robot']` *(required)*

##### `update_schedules`

```python
def update_schedules(schedules: List[Dict[str, Any]]) -> None
```

Update schedules tab with new data.

Args:
    schedules: List of schedule dictionaries

**Parameters:**

- `schedules: List[Dict[str, Any]]` *(required)*

##### `update_tenants`

```python
def update_tenants(tenants: List[Dict[str, Any]]) -> None
```

Update available tenants list.

Args:
    tenants: List of tenant dictionaries with 'id' and 'name' keys.

**Parameters:**

- `tenants: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.analytics_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\analytics_tab.py`


Analytics Tab Widget for Fleet Dashboard.

Displays fleet statistics and charts using Qt widgets.
Supports real-time queue metrics updates via WebSocketBridge.


### AnalyticsTabWidget

**Inherits from:** `QWidget`


Widget for displaying fleet analytics and statistics.

Features:
- Statistics cards (robots online, jobs today, success rate)
- Job status distribution (pie chart)
- Robot utilization (bar chart)
- Error distribution (bar chart)
- Jobs over time (simple trend)

Signals:
    refresh_requested: Emitted when refresh is clicked


**Attributes:**

- `refresh_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `update_active_jobs(running, completed_today)` | `None` | Update active jobs count in real-time. |
| `update_analytics(analytics)` | `None` | Update all analytics widgets with new data. |
| `update_fleet_status(active_robots, total_robots)` | `None` | Update fleet status in real-time. |
| `update_queue_metrics(update)` | `None` | Handle real-time queue metrics update from WebSocket. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `update_active_jobs`

```python
def update_active_jobs(running: int, completed_today: int) -> None
```

Update active jobs count in real-time.

Args:
    running: Number of running jobs
    completed_today: Jobs completed today

**Parameters:**

- `running: int` *(required)*
- `completed_today: int` *(required)*

##### `update_analytics`

```python
def update_analytics(analytics: Dict[str, Any]) -> None
```

Update all analytics widgets with new data.

**Parameters:**

- `analytics: Dict[str, Any]` *(required)*

##### `update_fleet_status`

```python
def update_fleet_status(active_robots: int, total_robots: int) -> None
```

Update fleet status in real-time.

Args:
    active_robots: Number of online robots
    total_robots: Total number of robots

**Parameters:**

- `active_robots: int` *(required)*
- `total_robots: int` *(required)*

##### `update_queue_metrics`

```python
def update_queue_metrics(update: 'QueueMetricsUpdate') -> None
```

Handle real-time queue metrics update from WebSocket.

Updates queue depth card without full analytics refresh.

Args:
    update: QueueMetricsUpdate from WebSocketBridge

**Parameters:**

- `update: 'QueueMetricsUpdate'` *(required)*

### BarChart

**Inherits from:** `QWidget`


Simple horizontal bar chart widget.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, parent)` | `None` |  |
| `paintEvent(event)` | `None` | Paint the bar chart. |
| `set_data(data, max_value)` | `None` | Set chart data as list of (label, value, color) tuples. |

#### Method Details

##### `__init__`

```python
def __init__(title: str = '', parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `title: str = ''`
- `parent: Optional[QWidget] = None`

##### `paintEvent`

```python
def paintEvent(event) -> None
```

Paint the bar chart.

**Parameters:**

- `event` *(required)*

##### `set_data`

```python
def set_data(data: List[tuple], max_value: Optional[float] = None) -> None
```

Set chart data as list of (label, value, color) tuples.

**Parameters:**

- `data: List[tuple]` *(required)*
- `max_value: Optional[float] = None`

### PieChart

**Inherits from:** `QWidget`


Simple pie chart widget.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, parent)` | `None` |  |
| `paintEvent(event)` | `None` | Paint the pie chart. |
| `set_data(data)` | `None` | Set chart data as list of (label, value, color) tuples. |

#### Method Details

##### `__init__`

```python
def __init__(title: str = '', parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `title: str = ''`
- `parent: Optional[QWidget] = None`

##### `paintEvent`

```python
def paintEvent(event) -> None
```

Paint the pie chart.

**Parameters:**

- `event` *(required)*

##### `set_data`

```python
def set_data(data: List[tuple]) -> None
```

Set chart data as list of (label, value, color) tuples.

**Parameters:**

- `data: List[tuple]` *(required)*

### StatCard

**Inherits from:** `QFrame`


Card widget displaying a single statistic.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, value, subtitle, ...)` | `None` |  |
| `set_value(value, subtitle)` | `None` | Update card value and subtitle. |

#### Method Details

##### `__init__`

```python
def __init__(title: str, value: str = '-', subtitle: str = '', color: QColor = QColor(76, 175, 80), parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `title: str` *(required)*
- `value: str = '-'`
- `subtitle: str = ''`
- `color: QColor = QColor(76, 175, 80)`
- `parent: Optional[QWidget] = None`

##### `set_value`

```python
def set_value(value: str, subtitle: str = '') -> None
```

Update card value and subtitle.

**Parameters:**

- `value: str` *(required)*
- `subtitle: str = ''`

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.api_keys_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\api_keys_tab.py`


API Keys Tab Widget for Fleet Dashboard.

Manages robot API keys with tenant isolation support.


### ApiKeysTabWidget

**Inherits from:** `QWidget`


Widget for managing API keys in the fleet dashboard.

Wraps ApiKeyPanel and adds tenant filtering support.

Signals:
    key_generated: Emitted when new key requested (config_dict)
    key_revoked: Emitted when key revoked (key_id)
    key_rotated: Emitted when key rotation requested (key_id)
    refresh_requested: Emitted when refresh clicked


**Attributes:**

- `key_generated: Signal`
- `key_revoked: Signal`
- `key_rotated: Signal`
- `refresh_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `set_tenant(tenant_id)` | `None` | Set current tenant for filtering. |
| `update_api_keys(api_keys)` | `None` | Update API keys list. |
| `update_robots(robots)` | `None` | Update available robots list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `set_tenant`

```python
def set_tenant(tenant_id: Optional[str]) -> None
```

Set current tenant for filtering.

Args:
    tenant_id: Tenant ID or None for all tenants.

**Parameters:**

- `tenant_id: Optional[str]` *(required)*

##### `update_api_keys`

```python
def update_api_keys(api_keys: List[Dict[str, Any]]) -> None
```

Update API keys list.

Args:
    api_keys: List of API key dictionaries.

**Parameters:**

- `api_keys: List[Dict[str, Any]]` *(required)*

##### `update_robots`

```python
def update_robots(robots: List[Dict[str, Any]]) -> None
```

Update available robots list.

Args:
    robots: List of robot dictionaries.

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\base_tab.py`


Base Tab Widget for Fleet Dashboard.

Provides common functionality for all fleet dashboard tabs:
- Refresh button management
- Timer-based auto-refresh
- Status label
- Common styling


### BaseTabWidget

**Inherits from:** `QWidget`


Base class for fleet dashboard tab widgets.

Provides:
- Automatic refresh timer
- Refresh button state management
- Status label updates
- Common styling

Subclasses must implement:
- _setup_content(): Create tab-specific UI
- _apply_additional_styles(): Add tab-specific styles


**Attributes:**

- `refresh_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(tab_name, parent)` | `None` | Initialize base tab widget. |
| `pause_auto_refresh()` | `None` | Pause automatic refresh timer. |
| `resume_auto_refresh()` | `None` | Resume automatic refresh timer. |
| `set_refresh_interval(interval_ms)` | `None` | Set refresh interval. |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `set_status(message)` | `None` | Set status label message. |

#### Method Details

##### `__init__`

```python
def __init__(tab_name: str, parent: Optional[QWidget] = None) -> None
```

Initialize base tab widget.

Args:
    tab_name: Name for refresh interval lookup (robots, jobs, etc.)
    parent: Optional parent widget

**Parameters:**

- `tab_name: str` *(required)*
- `parent: Optional[QWidget] = None`

##### `pause_auto_refresh`

```python
def pause_auto_refresh() -> None
```

Pause automatic refresh timer.

##### `resume_auto_refresh`

```python
def resume_auto_refresh() -> None
```

Resume automatic refresh timer.

##### `set_refresh_interval`

```python
def set_refresh_interval(interval_ms: int) -> None
```

Set refresh interval.

Args:
    interval_ms: Interval in milliseconds

**Parameters:**

- `interval_ms: int` *(required)*

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

Args:
    refreshing: True if refresh in progress

**Parameters:**

- `refreshing: bool` *(required)*

##### `set_status`

```python
def set_status(message: str) -> None
```

Set status label message.

Args:
    message: Status message to display

**Parameters:**

- `message: str` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\jobs_tab.py`


Jobs Tab Widget for Fleet Dashboard.

Displays job queue and history with monitoring capabilities.
Supports real-time job updates with progress bars via WebSocketBridge.


### JobsTabWidget

**Inherits from:** `QWidget`


Widget for displaying and monitoring jobs.

Features:
- Job table with status, robot, workflow, timing
- Status filter (pending, running, completed, failed)
- Search by workflow name
- Job details panel
- Log viewer
- Cancel/Retry actions

Signals:
    job_selected: Emitted when job is selected (job_id)
    job_cancelled: Emitted when job is cancelled (job_id)
    job_retried: Emitted when job is retried (job_id)
    refresh_requested: Emitted when refresh is clicked


**Attributes:**

- `job_cancelled: Signal`
- `job_retried: Signal`
- `job_selected: Signal`
- `refresh_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `create_progress_bar_widget(progress, status)` | `QProgressBar` | Create a progress bar widget for job row. |
| `get_job_by_id(job_id)` | `Optional[Dict[str, Any]]` | Get job dict by ID. |
| `get_selected_job()` | `Optional[Dict[str, Any]]` | Get currently selected job. |
| `handle_batch_job_updates(updates)` | `None` | Handle batch of job status updates efficiently. |
| `handle_job_status_update(update)` | `None` | Handle real-time job status update from WebSocket. |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `update_jobs(jobs)` | `None` | Update table with job list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `create_progress_bar_widget`

```python
def create_progress_bar_widget(progress: int, status: str) -> QProgressBar
```

Create a progress bar widget for job row.

Args:
    progress: Progress percentage (0-100)
    status: Job status for color coding

Returns:
    Configured QProgressBar widget

**Parameters:**

- `progress: int` *(required)*
- `status: str` *(required)*

##### `get_job_by_id`

```python
def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]
```

Get job dict by ID.

Args:
    job_id: Job identifier

Returns:
    Job dictionary or None

**Parameters:**

- `job_id: str` *(required)*

##### `get_selected_job`

```python
def get_selected_job() -> Optional[Dict[str, Any]]
```

Get currently selected job.

##### `handle_batch_job_updates`

```python
def handle_batch_job_updates(updates: List['JobStatusUpdate']) -> None
```

Handle batch of job status updates efficiently.

Args:
    updates: List of JobStatusUpdate objects

**Parameters:**

- `updates: List['JobStatusUpdate']` *(required)*

##### `handle_job_status_update`

```python
def handle_job_status_update(update: 'JobStatusUpdate') -> None
```

Handle real-time job status update from WebSocket.

Updates the job row in place without full table refresh.

Args:
    update: JobStatusUpdate from WebSocketBridge

**Parameters:**

- `update: 'JobStatusUpdate'` *(required)*

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `update_jobs`

```python
def update_jobs(jobs: List[Dict[str, Any]]) -> None
```

Update table with job list.

**Parameters:**

- `jobs: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\robots_tab.py`


Robots Tab Widget for Fleet Dashboard.

Displays robot fleet with management capabilities.
Supports real-time status updates via WebSocketBridge.


### RobotEditDialog

**Inherits from:** `QDialog`


Dialog for editing robot properties.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robot, parent)` | `None` |  |
| `get_robot_data()` | `Dict` | Get robot data from form. |

#### Method Details

##### `__init__`

```python
def __init__(robot: Optional['Robot'] = None, parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `robot: Optional['Robot'] = None`
- `parent: Optional[QWidget] = None`

##### `get_robot_data`

```python
def get_robot_data() -> Dict
```

Get robot data from form.

### RobotsTabWidget

**Inherits from:** `QWidget`


Widget for displaying and managing robots.

Features:
- Table view of all robots
- Status filter
- Search
- Add/Edit/Delete actions
- Context menu
- Real-time status updates

Signals:
    robot_selected: Emitted when robot is selected (robot_id)
    robot_edited: Emitted when robot is edited (robot_id, robot_data)
    robot_deleted: Emitted when robot is deleted (robot_id)
    refresh_requested: Emitted when refresh is clicked


**Attributes:**

- `refresh_requested: Signal`
- `robot_deleted: Signal`
- `robot_details_requested: Signal`
- `robot_edited: Signal`
- `robot_force_stop_requested: Signal`
- `robot_logs_requested: Signal`
- `robot_metrics_requested: Signal`
- `robot_pause_requested: Signal`
- `robot_restart_requested: Signal`
- `robot_resume_requested: Signal`
- `robot_run_workflow_requested: Signal`
- `robot_selected: Signal`
- `robot_start_requested: Signal`
- `robot_stop_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `get_robot_by_id(robot_id)` | `Optional['Robot']` | Get robot entity by ID. |
| `handle_batch_robot_updates(updates)` | `None` | Handle batch of robot status updates efficiently. |
| `handle_robot_status_update(update)` | `None` | Handle real-time robot status update from WebSocket. |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `update_robots(robots)` | `None` | Update table with robot list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `get_robot_by_id`

```python
def get_robot_by_id(robot_id: str) -> Optional['Robot']
```

Get robot entity by ID.

Args:
    robot_id: Robot identifier

Returns:
    Robot entity or None

**Parameters:**

- `robot_id: str` *(required)*

##### `handle_batch_robot_updates`

```python
def handle_batch_robot_updates(updates: List['RobotStatusUpdate']) -> None
```

Handle batch of robot status updates efficiently.

Args:
    updates: List of RobotStatusUpdate objects

**Parameters:**

- `updates: List['RobotStatusUpdate']` *(required)*

##### `handle_robot_status_update`

```python
def handle_robot_status_update(update: 'RobotStatusUpdate') -> None
```

Handle real-time robot status update from WebSocket.

Updates the robot row in place without full table refresh.

Args:
    update: RobotStatusUpdate from WebSocketBridge

**Parameters:**

- `update: 'RobotStatusUpdate'` *(required)*

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `update_robots`

```python
def update_robots(robots: List['Robot']) -> None
```

Update table with robot list.

**Parameters:**

- `robots: List['Robot']` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\schedules_tab.py`


Schedules Tab Widget for Fleet Dashboard.

Displays workflow schedules with management capabilities.


### SchedulesTabWidget

**Inherits from:** `QWidget`


Widget for displaying and managing workflow schedules.

Features:
- Schedule table with frequency, next run, last run
- Enable/Disable toggle
- Search and filter
- Edit/Delete actions
- Run now capability

Signals:
    schedule_selected: Emitted when schedule is selected (schedule_id)
    schedule_enabled_changed: Emitted when schedule is enabled/disabled (schedule_id, enabled)
    schedule_edited: Emitted when schedule edit is requested (schedule_id)
    schedule_deleted: Emitted when schedule is deleted (schedule_id)
    schedule_run_now: Emitted when run now is clicked (schedule_id)
    refresh_requested: Emitted when refresh is clicked


**Attributes:**

- `refresh_requested: Signal`
- `schedule_deleted: Signal`
- `schedule_edited: Signal`
- `schedule_enabled_changed: Signal`
- `schedule_run_now: Signal`
- `schedule_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `update_schedules(schedules)` | `None` | Update table with schedule list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `update_schedules`

```python
def update_schedules(schedules: List[Dict[str, Any]]) -> None
```

Update table with schedule list.

**Parameters:**

- `schedules: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.node_properties_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\node_properties_dialog.py`


Node Properties Dialog UI Component.

Modal dialog for editing comprehensive node properties.


### NodePropertiesDialog

**Inherits from:** `QDialog`


Dialog for editing node properties.

Features:
- Basic properties (name, description)
- Input/output configuration
- Advanced settings
- Validation

Signals:
    properties_changed: Emitted when properties are saved (dict: properties)


**Attributes:**

- `properties_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(node_id, node_type, properties, ...)` | `None` | Initialize node properties dialog. |
| `get_properties()` | `Dict[str, Any]` | Get the current properties. |

#### Method Details

##### `__init__`

```python
def __init__(node_id: str, node_type: str, properties: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None
```

Initialize node properties dialog.

Args:
    node_id: Node ID
    node_type: Node type name
    properties: Current node properties
    parent: Optional parent widget

**Parameters:**

- `node_id: str` *(required)*
- `node_type: str` *(required)*
- `properties: Optional[Dict[str, Any]] = None`
- `parent: Optional[QWidget] = None`

##### `get_properties`

```python
def get_properties() -> Dict[str, Any]
```

Get the current properties.

Returns:
    Dictionary of properties

---

## casare_rpa.presentation.canvas.ui.dialogs.preferences_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\preferences_dialog.py`


Preferences Dialog UI Component.

Modal dialog for editing application-wide preferences and settings.
Extracted from canvas/dialogs/preferences_dialog.py for reusability.


### PreferencesDialog

**Inherits from:** `QDialog`


Application preferences dialog.

Features:
- General settings (theme, language)
- Autosave settings
- Editor settings
- Performance settings

Signals:
    preferences_changed: Emitted when preferences are saved (dict: preferences)


**Attributes:**

- `preferences_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(preferences, parent)` | `None` | Initialize preferences dialog. |
| `get_preferences()` | `Dict[str, Any]` | Get the current preferences. |

#### Method Details

##### `__init__`

```python
def __init__(preferences: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None
```

Initialize preferences dialog.

Args:
    preferences: Current preferences
    parent: Optional parent widget

**Parameters:**

- `preferences: Optional[Dict[str, Any]] = None`
- `parent: Optional[QWidget] = None`

##### `get_preferences`

```python
def get_preferences() -> Dict[str, Any]
```

Get the current preferences.

Returns:
    Dictionary of preferences

---

## casare_rpa.presentation.canvas.ui.dialogs.project_manager_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\project_manager_dialog.py`


Project Manager Dialog UI Component.

Dialog for creating, opening, and managing CasareRPA projects.


### ProjectManagerDialog

**Inherits from:** `QDialog`


Dialog for managing CasareRPA projects.

Features:
- Create new projects
- Open recent projects
- Browse for existing projects
- View project details
- View and open scenarios within projects

Signals:
    project_created: Emitted when new project created (Project)
    project_opened: Emitted when project opened (str: path)
    project_deleted: Emitted when project deleted (str: project_id)
    scenario_opened: Emitted when scenario opened (str: project_path, str: scenario_path)


**Attributes:**

- `project_created: Signal`
- `project_deleted: Signal`
- `project_opened: Signal`
- `scenario_opened: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(recent_projects, parent)` | `None` | Initialize project manager dialog. |
| `update_recent_projects(projects)` | `None` | Update the recent projects list. |

#### Method Details

##### `__init__`

```python
def __init__(recent_projects: Optional[List['ProjectIndexEntry']] = None, parent: Optional[QWidget] = None) -> None
```

Initialize project manager dialog.

Args:
    recent_projects: List of recent project entries
    parent: Optional parent widget

**Parameters:**

- `recent_projects: Optional[List['ProjectIndexEntry']] = None`
- `parent: Optional[QWidget] = None`

##### `update_recent_projects`

```python
def update_recent_projects(projects: List['ProjectIndexEntry']) -> None
```

Update the recent projects list.

Args:
    projects: New list of project entries

**Parameters:**

- `projects: List['ProjectIndexEntry']` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.recording_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\recording_dialog.py`


Recording Preview Dialog

Shows recorded actions and allows editing before generating workflow.


### RecordingPreviewDialog

**Inherits from:** `QDialog`


Dialog for previewing and editing recorded actions.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(actions, parent)` | - | Initialize recording preview dialog. |
| `get_actions()` | `list` | Get the edited actions. |

#### Method Details

##### `__init__`

```python
def __init__(actions: list, parent = None)
```

Initialize recording preview dialog.

Args:
    actions: List of recorded action dictionaries
    parent: Parent widget

**Parameters:**

- `actions: list` *(required)*
- `parent = None`

##### `get_actions`

```python
def get_actions() -> list
```

Get the edited actions.

Returns:
    List of action dictionaries

---

## casare_rpa.presentation.canvas.ui.dialogs.remote_robot_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\remote_robot_dialog.py`


Remote Robot Management Dialog.

Provides UI for managing robots remotely including viewing details,
starting/stopping, and updating configuration.


### RemoteRobotDialog

**Inherits from:** `QDialog`


Dialog for remote robot management.

Features:
- View robot details and metrics
- Start/stop robot remotely
- Update robot configuration
- View current jobs
- Monitor health metrics

Signals:
    robot_started: Emitted when start requested (robot_id)
    robot_stopped: Emitted when stop requested (robot_id)
    robot_restarted: Emitted when restart requested (robot_id)
    config_updated: Emitted when config updated (robot_id, config_dict)
    refresh_requested: Emitted when refresh clicked


**Attributes:**

- `config_updated: Signal`
- `refresh_requested: Signal`
- `robot_restarted: Signal`
- `robot_started: Signal`
- `robot_stopped: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robot_id, robot_data, parent)` | `None` |  |
| `append_log(message, level)` | `None` | Append a log message. |
| `update_robot(robot_data)` | `None` | Update dialog with new robot data. |

#### Method Details

##### `__init__`

```python
def __init__(robot_id: str, robot_data: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `robot_id: str` *(required)*
- `robot_data: Optional[Dict[str, Any]] = None`
- `parent: Optional[QWidget] = None`

##### `append_log`

```python
def append_log(message: str, level: str = 'info') -> None
```

Append a log message.

**Parameters:**

- `message: str` *(required)*
- `level: str = 'info'`

##### `update_robot`

```python
def update_robot(robot_data: Dict[str, Any]) -> None
```

Update dialog with new robot data.

**Parameters:**

- `robot_data: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\schedule_dialog.py`


Schedule Dialog for CasareRPA Canvas.
Allows scheduling workflows directly from the Canvas editor.


### ScheduleDialog

**Inherits from:** `QDialog`


Dialog for creating/editing a workflow schedule.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow_path, workflow_name, schedule, ...)` | - |  |

#### Method Details

##### `__init__`

```python
def __init__(workflow_path: Optional[Path] = None, workflow_name: str = 'Untitled', schedule: Optional[WorkflowSchedule] = None, parent: Optional[QWidget] = None)
```

**Parameters:**

- `workflow_path: Optional[Path] = None`
- `workflow_name: str = 'Untitled'`
- `schedule: Optional[WorkflowSchedule] = None`
- `parent: Optional[QWidget] = None`

### ScheduleManagerDialog

**Inherits from:** `QDialog`


Dialog for managing all workflow schedules.


**Attributes:**

- `run_schedule: Signal`
- `schedule_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(schedules, parent)` | - |  |
| `get_schedules()` | `List[WorkflowSchedule]` | Get the current list of schedules. |

#### Method Details

##### `__init__`

```python
def __init__(schedules: List[WorkflowSchedule], parent: Optional[QWidget] = None)
```

**Parameters:**

- `schedules: List[WorkflowSchedule]` *(required)*
- `parent: Optional[QWidget] = None`

##### `get_schedules`

```python
def get_schedules() -> List[WorkflowSchedule]
```

Get the current list of schedules.

---

## casare_rpa.presentation.canvas.ui.dialogs.template_browser_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\template_browser_dialog.py`


Template Browser Dialog

Provides a dialog for browsing and selecting workflow templates.
Users can filter by category, search, and preview template descriptions.


### Functions

#### `show_template_browser`

```python
def show_template_browser(parent: Optional[QWidget] = None) -> Optional[TemplateInfo]
```

Show the template browser dialog and return the selected template.

Args:
    parent: Parent widget

Returns:
    Selected TemplateInfo or None if cancelled


### TemplateBrowserDialog

**Inherits from:** `QDialog`


Dialog for browsing and selecting workflow templates.

Signals:
    template_selected: Emitted when a template is selected (TemplateInfo)


**Attributes:**

- `template_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | - | Initialize the template browser dialog. |
| `get_selected_template()` | `Optional[TemplateInfo]` | Get the selected template. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None)
```

Initialize the template browser dialog.

Args:
    parent: Parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `get_selected_template`

```python
def get_selected_template() -> Optional[TemplateInfo]
```

Get the selected template.

Returns:
    Selected TemplateInfo or None

---

## casare_rpa.presentation.canvas.ui.dialogs.update_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\update_dialog.py`


Update Dialog UI Component.

Modal dialog for application update notifications and downloads.
Integrates with TUF UpdateManager for secure software updates.


### UpdateDialog

**Inherits from:** `QDialog`


Application update notification and download dialog.

Features:
- Display update availability with version info
- Show release notes
- Download progress with speed indicator
- Skip version / Remind later options
- Restart prompt after download

Signals:
    update_accepted: Emitted when user clicks Download/Install
    update_skipped: Emitted when user clicks Skip This Version
    update_postponed: Emitted when user clicks Remind Later


**Attributes:**

- `update_accepted: Signal`
- `update_postponed: Signal`
- `update_skipped: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(update_info, update_manager, parent)` | `None` | Initialize update dialog. |
| `is_download_complete()` | `bool` | Check if download is complete. |
| `is_downloading()` | `bool` | Check if download is in progress. |
| `update_info()` | `UpdateInfo` | Get the update info. |
| `update_progress(progress)` | `None` | Update download progress display. |

#### Method Details

##### `__init__`

```python
def __init__(update_info: UpdateInfo, update_manager: Optional[UpdateManager] = None, parent: Optional[QWidget] = None) -> None
```

Initialize update dialog.

Args:
    update_info: Information about the available update
    update_manager: Optional update manager for download/install
    parent: Optional parent widget

**Parameters:**

- `update_info: UpdateInfo` *(required)*
- `update_manager: Optional[UpdateManager] = None`
- `parent: Optional[QWidget] = None`

##### `is_download_complete`

```python
@property
def is_download_complete() -> bool
```

Check if download is complete.

##### `is_downloading`

```python
@property
def is_downloading() -> bool
```

Check if download is in progress.

##### `update_info`

```python
@property
def update_info() -> UpdateInfo
```

Get the update info.

##### `update_progress`

```python
def update_progress(progress: DownloadProgress) -> None
```

Update download progress display.

Args:
    progress: Current download progress

**Parameters:**

- `progress: DownloadProgress` *(required)*

### UpdateNotificationWidget

**Inherits from:** `QWidget`


Small notification widget for status bar or toolbar.

Shows when an update is available with a clickable label.

Signals:
    clicked: Emitted when notification is clicked


**Attributes:**

- `clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(update_info, parent)` | `None` | Initialize notification widget. |
| `mousePressEvent(event)` | `None` | Handle mouse press. |
| `set_update_info(update_info)` | `None` | Set update info and update visibility. |

#### Method Details

##### `__init__`

```python
def __init__(update_info: Optional[UpdateInfo] = None, parent: Optional[QWidget] = None) -> None
```

Initialize notification widget.

Args:
    update_info: Optional update info
    parent: Optional parent widget

**Parameters:**

- `update_info: Optional[UpdateInfo] = None`
- `parent: Optional[QWidget] = None`

##### `mousePressEvent`

```python
def mousePressEvent(event) -> None
```

Handle mouse press.

**Parameters:**

- `event` *(required)*

##### `set_update_info`

```python
def set_update_info(update_info: Optional[UpdateInfo]) -> None
```

Set update info and update visibility.

Args:
    update_info: Update info or None to hide

**Parameters:**

- `update_info: Optional[UpdateInfo]` *(required)*

---

## casare_rpa.presentation.canvas.ui.dialogs.workflow_settings_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\workflow_settings_dialog.py`


Workflow Settings Dialog UI Component.

Modal dialog for editing workflow-level settings and metadata.


### WorkflowSettingsDialog

**Inherits from:** `QDialog`


Dialog for editing workflow settings.

Features:
- Workflow metadata (name, description, author)
- Execution settings
- Variable defaults
- Error handling configuration

Signals:
    settings_changed: Emitted when settings are saved (dict: settings)


**Attributes:**

- `settings_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(settings, parent)` | `None` | Initialize workflow settings dialog. |
| `get_settings()` | `Dict[str, Any]` | Get the current settings. |

#### Method Details

##### `__init__`

```python
def __init__(settings: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None
```

Initialize workflow settings dialog.

Args:
    settings: Current workflow settings
    parent: Optional parent widget

**Parameters:**

- `settings: Optional[Dict[str, Any]] = None`
- `parent: Optional[QWidget] = None`

##### `get_settings`

```python
def get_settings() -> Dict[str, Any]
```

Get the current settings.

Returns:
    Dictionary of settings

---

## casare_rpa.presentation.canvas.ui.icons

**File:** `src\casare_rpa\presentation\canvas\ui\icons.py`


CasareRPA - Icon Provider for Toolbar Actions.

Uses Qt's built-in standard icons for consistent, theme-aware icons
that work on all platforms without external assets.

For custom icons, use ResourceCache.get_icon(path) from resources.py.


### Functions

#### `get_toolbar_icon`

```python
def get_toolbar_icon(name: str) -> 'QIcon'
```

Convenience function to get a toolbar icon.

Args:
    name: Action name

Returns:
    QIcon for the action


### ToolbarIcons


Provides icons for toolbar actions using Qt standard icons.

Qt standard icons are:
- Always available (no external files needed)
- Theme-aware (respect system theme on all platforms)
- Properly scaled for different DPI settings

Usage:
    icon = ToolbarIcons.get_icon("run")
    action.setIcon(icon)


**Attributes:**

- `_style: Optional['QStyle']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_all_icons()` | `dict` | Get all available toolbar icons. |
| `get_icon(name)` | `'QIcon'` | Get a toolbar icon by action name. |

#### Method Details

##### `get_all_icons`

```python
@classmethod
def get_all_icons() -> dict
```

Get all available toolbar icons.

Returns:
    Dictionary mapping action names to QIcon instances

##### `get_icon`

```python
@classmethod
def get_icon(name: str) -> 'QIcon'
```

Get a toolbar icon by action name.

Args:
    name: Action name (e.g., "run", "stop", "save")

Returns:
    QIcon for the action, or empty QIcon if not found

**Parameters:**

- `name: str` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.analytics_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\analytics_panel.py`


Analytics Panel UI Component.

Provides bottleneck detection and execution analysis views
connected to the Orchestrator REST API.


### AnalyticsPanel

**Inherits from:** `QDockWidget`


Dockable panel for Analytics connected to Orchestrator API.

Features:
- Bottleneck Detection: Identify slow/failing nodes
- Execution Analysis: Trends, patterns, insights
- Timeline visualization

Signals:
    workflow_selected: Emitted when workflow is selected (str: workflow_id)
    bottleneck_clicked: Emitted when bottleneck is clicked (dict: bottleneck_data)
    insight_clicked: Emitted when insight is clicked (dict: insight_data)


**Attributes:**

- `bottleneck_clicked: Signal`
- `insight_clicked: Signal`
- `workflow_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the analytics panel. |
| `cleanup()` | `None` | Clean up resources. |
| `hideEvent(event)` | `None` | Handle hide event. |
| `set_api_url(url)` | `None` | Set the API base URL dynamically. |
| `set_api_url(url)` | `None` | Set the API base URL. |
| `showEvent(event)` | `None` | Handle show event. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the analytics panel.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `hideEvent`

```python
def hideEvent(event) -> None
```

Handle hide event.

**Parameters:**

- `event` *(required)*

##### `set_api_url`

```python
def set_api_url(url: str) -> None
```

Set the API base URL dynamically.

Args:
    url: Base URL for orchestrator (e.g., https://tunnel.example.com)

**Parameters:**

- `url: str` *(required)*

##### `set_api_url`

```python
def set_api_url(url: str) -> None
```

Set the API base URL.

**Parameters:**

- `url: str` *(required)*

##### `showEvent`

```python
def showEvent(event) -> None
```

Handle show event.

**Parameters:**

- `event` *(required)*

### ApiWorker

**Inherits from:** `QObject`


Worker for background API calls.


**Attributes:**

- `error: Signal`
- `finished: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(url, method)` | `None` | Initialize worker. |
| `run()` | `None` | Execute the API call. |

#### Method Details

##### `__init__`

```python
def __init__(url: str, method: str = 'GET') -> None
```

Initialize worker.

**Parameters:**

- `url: str` *(required)*
- `method: str = 'GET'`

##### `run`

```python
def run() -> None
```

Execute the API call.

---

## casare_rpa.presentation.canvas.ui.panels.api_key_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\api_key_panel.py`


API Key Management Panel for Fleet Dashboard.

Provides UI for managing robot API keys including generation, revocation,
and viewing usage statistics.


### ApiKeyPanel

**Inherits from:** `QWidget`


Panel for managing robot API keys.

Features:
- List all API keys for tenant
- Generate new API key
- Revoke API key
- Copy key to clipboard (one-time view)
- Show key usage statistics

Signals:
    key_generated: Emitted when new key requested (config_dict)
    key_revoked: Emitted when key revoked (key_id)
    key_rotated: Emitted when key rotation requested (key_id)
    refresh_requested: Emitted when refresh clicked


**Attributes:**

- `key_generated: Signal`
- `key_revoked: Signal`
- `key_rotated: Signal`
- `refresh_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `set_refreshing(refreshing)` | `None` | Set refresh button state. |
| `set_tenant(tenant_id)` | `None` | Set current tenant for filtering. |
| `update_api_keys(api_keys)` | `None` | Update table with API key list. |
| `update_robots(robots)` | `None` | Update available robots list. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state.

**Parameters:**

- `refreshing: bool` *(required)*

##### `set_tenant`

```python
def set_tenant(tenant_id: str) -> None
```

Set current tenant for filtering.

**Parameters:**

- `tenant_id: str` *(required)*

##### `update_api_keys`

```python
def update_api_keys(api_keys: List[Dict[str, Any]]) -> None
```

Update table with API key list.

**Parameters:**

- `api_keys: List[Dict[str, Any]]` *(required)*

##### `update_robots`

```python
def update_robots(robots: List[Dict[str, Any]]) -> None
```

Update available robots list.

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*

### GenerateApiKeyDialog

**Inherits from:** `QDialog`


Dialog for generating a new API key.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robots, parent)` | `None` |  |
| `get_key_config()` | `Dict[str, Any]` | Get key configuration from form. |
| `set_generated_key(raw_key)` | `None` | Display the generated key (called by parent after actual gen... |

#### Method Details

##### `__init__`

```python
def __init__(robots: List[Dict[str, Any]], parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*
- `parent: Optional[QWidget] = None`

##### `get_key_config`

```python
def get_key_config() -> Dict[str, Any]
```

Get key configuration from form.

##### `set_generated_key`

```python
def set_generated_key(raw_key: str) -> None
```

Display the generated key (called by parent after actual generation).

**Parameters:**

- `raw_key: str` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock

**File:** `src\casare_rpa\presentation\canvas\ui\panels\bottom_panel_dock.py`


Bottom Panel Dock for CasareRPA.

Main dockable container with tabs for Variables, Output, Log, Validation, and History.
Provides Power Automate/UiPath-style bottom panel functionality.

Note: Triggers are now visual nodes on the canvas (not a separate tab).


### BottomPanelDock

**Inherits from:** `QDockWidget`


Dockable bottom panel with tabs for Variables, Output, Log, Validation, and History.

This panel provides a Power Automate/UiPath-style interface for:
- Variables: Global workflow variables with design/runtime modes
- Output: Workflow outputs and return values
- Log: Real-time execution logs
- Validation: Workflow validation issues
- History: Execution history with timing and status

Note: Triggers are now visual nodes on the canvas.

Signals:
    variables_changed: Emitted when variables are modified
    validation_requested: Emitted when user requests manual validation
    issue_clicked: Emitted when a validation issue is clicked (location: str)
    navigate_to_node: Emitted when user wants to navigate to a node (node_id: str)
    history_clear_requested: Emitted when user requests to clear history


**Attributes:**

- `TAB_HISTORY: int`
- `TAB_LOG: int`
- `TAB_OUTPUT: int`
- `TAB_TERMINAL: int`
- `TAB_VALIDATION: int`
- `TAB_VARIABLES: int`
- `history_clear_requested: Signal`
- `issue_clicked: Signal`
- `navigate_to_node: Signal`
- `validation_requested: Signal`
- `variables_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the bottom panel dock. |
| `add_output(name, value, timestamp)` | `None` | Add an output to the Output tab. |
| `append_history_entry(entry)` | `None` | Append a single entry to the execution history. |
| `clear_history()` | `None` | Clear execution history. |
| `clear_log()` | `None` | Clear the execution log. |
| `clear_outputs()` | `None` | Clear all outputs. |
| `clear_terminal()` | `None` | Clear the Terminal tab. |
| `clear_validation()` | `None` | Clear validation results. |
| `execution_finished()` | `None` | Handle workflow execution completion. |
| `get_history_tab()` | `'HistoryTab'` | Get the History tab widget. |
| `get_log_tab()` | `'LogTab'` | Get the Log tab widget. |
| `get_output_tab()` | `'OutputTab'` | Get the Output tab widget. |
| `get_terminal_tab()` | `'TerminalTab'` | Get the Terminal tab widget. |
| `get_validation_errors_blocking()` | `List[Dict]` | Get current validation errors synchronously. |
| `get_validation_tab()` | `'ValidationTab'` | Get the Validation tab widget. |
| `get_variables()` | `Dict[str, Any]` | Get current workflow variables. |
| `get_variables_tab()` | `'VariablesTab'` | Get the Variables tab widget. |
| `has_validation_errors()` | `bool` | Check if there are validation errors. |
| `log_event(event)` | `None` | Log an execution event. |
| `log_message(message, level, node_id)` | `None` | Log a custom message. |
| `prepare_for_execution()` | `None` | Prepare panel for workflow execution (preserves panel visibi... |
| `reset()` | `None` | Reset all tabs to initial state. |
| `set_runtime_mode(enabled)` | `None` | Switch between design mode and runtime mode. |
| `set_validation_result(result)` | `None` | Set validation results. |
| `set_variables(variables)` | `None` | Set workflow variables (design mode). |
| `set_workflow_result(success, message)` | `None` | Set the final workflow result. |
| `show_history_tab()` | `None` | Show and focus the History tab. |
| `show_log_tab()` | `None` | Show and focus the Log tab. |
| `show_output_tab()` | `None` | Show and focus the Output tab. |
| `show_terminal_tab()` | `None` | Show and focus the Terminal tab. |
| `show_validation_tab()` | `None` | Show and focus the Validation tab. |
| `show_variables_tab()` | `None` | Show and focus the Variables tab. |
| `terminal_write(text, level)` | `None` | Write text to the Terminal tab. |
| `terminal_write_stderr(text)` | `None` | Write stderr text to the Terminal tab. |
| `terminal_write_stdout(text)` | `None` | Write stdout text to the Terminal tab. |
| `update_history(history)` | `None` | Update the execution history display. |
| `update_runtime_values(values)` | `None` | Update variable values during runtime. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the bottom panel dock.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_output`

```python
def add_output(name: str, value: Any, timestamp: Optional[str] = None) -> None
```

Add an output to the Output tab.

Args:
    name: Output name/key
    value: Output value
    timestamp: Optional timestamp string

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*
- `timestamp: Optional[str] = None`

##### `append_history_entry`

```python
def append_history_entry(entry: Dict[str, Any]) -> None
```

Append a single entry to the execution history.

Args:
    entry: Execution history entry with keys:
           - timestamp: ISO timestamp string
           - node_id: Node identifier
           - node_type: Type of the node
           - execution_time: Time in seconds
           - status: 'success' or 'failed'

**Parameters:**

- `entry: Dict[str, Any]` *(required)*

##### `clear_history`

```python
def clear_history() -> None
```

Clear execution history.

##### `clear_log`

```python
def clear_log() -> None
```

Clear the execution log.

##### `clear_outputs`

```python
def clear_outputs() -> None
```

Clear all outputs.

##### `clear_terminal`

```python
def clear_terminal() -> None
```

Clear the Terminal tab.

##### `clear_validation`

```python
def clear_validation() -> None
```

Clear validation results.

##### `execution_finished`

```python
def execution_finished() -> None
```

Handle workflow execution completion.

##### `get_history_tab`

```python
def get_history_tab() -> 'HistoryTab'
```

Get the History tab widget.

##### `get_log_tab`

```python
def get_log_tab() -> 'LogTab'
```

Get the Log tab widget.

##### `get_output_tab`

```python
def get_output_tab() -> 'OutputTab'
```

Get the Output tab widget.

##### `get_terminal_tab`

```python
def get_terminal_tab() -> 'TerminalTab'
```

Get the Terminal tab widget.

##### `get_validation_errors_blocking`

```python
def get_validation_errors_blocking() -> List[Dict]
```

Get current validation errors synchronously.

Returns:
    List of validation error dictionaries

##### `get_validation_tab`

```python
def get_validation_tab() -> 'ValidationTab'
```

Get the Validation tab widget.

##### `get_variables`

```python
def get_variables() -> Dict[str, Any]
```

Get current workflow variables.

Returns:
    Dict of variable definitions

##### `get_variables_tab`

```python
def get_variables_tab() -> 'VariablesTab'
```

Get the Variables tab widget.

##### `has_validation_errors`

```python
def has_validation_errors() -> bool
```

Check if there are validation errors.

##### `log_event`

```python
def log_event(event: 'Event') -> None
```

Log an execution event.

Args:
    event: Event to log

**Parameters:**

- `event: 'Event'` *(required)*

##### `log_message`

```python
def log_message(message: str, level: str = 'info', node_id: Optional[str] = None) -> None
```

Log a custom message.

Args:
    message: Message text
    level: Log level (info, warning, error, success)
    node_id: Optional associated node ID

**Parameters:**

- `message: str` *(required)*
- `level: str = 'info'`
- `node_id: Optional[str] = None`

##### `prepare_for_execution`

```python
def prepare_for_execution() -> None
```

Prepare panel for workflow execution (preserves panel visibility).

##### `reset`

```python
def reset() -> None
```

Reset all tabs to initial state.

##### `set_runtime_mode`

```python
def set_runtime_mode(enabled: bool) -> None
```

Switch between design mode and runtime mode.

Args:
    enabled: True for runtime mode, False for design mode

**Parameters:**

- `enabled: bool` *(required)*

##### `set_validation_result`

```python
def set_validation_result(result: 'ValidationResult') -> None
```

Set validation results.

Args:
    result: ValidationResult to display

**Parameters:**

- `result: 'ValidationResult'` *(required)*

##### `set_variables`

```python
def set_variables(variables: Dict[str, Any]) -> None
```

Set workflow variables (design mode).

Args:
    variables: Dict of variable definitions

**Parameters:**

- `variables: Dict[str, Any]` *(required)*

##### `set_workflow_result`

```python
def set_workflow_result(success: bool, message: str) -> None
```

Set the final workflow result.

Args:
    success: Whether workflow completed successfully
    message: Result message

**Parameters:**

- `success: bool` *(required)*
- `message: str` *(required)*

##### `show_history_tab`

```python
def show_history_tab() -> None
```

Show and focus the History tab.

##### `show_log_tab`

```python
def show_log_tab() -> None
```

Show and focus the Log tab.

##### `show_output_tab`

```python
def show_output_tab() -> None
```

Show and focus the Output tab.

##### `show_terminal_tab`

```python
def show_terminal_tab() -> None
```

Show and focus the Terminal tab.

##### `show_validation_tab`

```python
def show_validation_tab() -> None
```

Show and focus the Validation tab.

##### `show_variables_tab`

```python
def show_variables_tab() -> None
```

Show and focus the Variables tab.

##### `terminal_write`

```python
def terminal_write(text: str, level: str = 'info') -> None
```

Write text to the Terminal tab.

Args:
    text: Text to write
    level: Output level (info, warning, error, success, debug)

**Parameters:**

- `text: str` *(required)*
- `level: str = 'info'`

##### `terminal_write_stderr`

```python
def terminal_write_stderr(text: str) -> None
```

Write stderr text to the Terminal tab.

**Parameters:**

- `text: str` *(required)*

##### `terminal_write_stdout`

```python
def terminal_write_stdout(text: str) -> None
```

Write stdout text to the Terminal tab.

**Parameters:**

- `text: str` *(required)*

##### `update_history`

```python
def update_history(history: List[Dict[str, Any]]) -> None
```

Update the execution history display.

Args:
    history: List of execution history entries

**Parameters:**

- `history: List[Dict[str, Any]]` *(required)*

##### `update_runtime_values`

```python
def update_runtime_values(values: Dict[str, Any]) -> None
```

Update variable values during runtime.

Args:
    values: Dict of {variable_name: current_value}

**Parameters:**

- `values: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.history_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\history_tab.py`


History Tab for the Bottom Panel.

Displays the execution history of a workflow with timestamps,
node information, and execution metrics.


### HistoryTab

**Inherits from:** `QWidget`


History tab widget for viewing workflow execution history.

Displays a chronological list of all executed nodes with:
- Timestamp
- Node ID
- Node Type
- Execution Time
- Status (success/failed)

Signals:
    node_selected: Emitted when user selects a node from history (str: node_id)
    clear_requested: Emitted when user requests to clear history


**Attributes:**

- `clear_requested: Signal`
- `node_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the history tab. |
| `append_entry(entry)` | `None` | Append a single entry to the history. |
| `clear()` | `None` | Clear all history entries. |
| `get_entry_count()` | `int` | Get total number of history entries. |
| `scroll_to_bottom()` | `None` | Scroll to the bottom of the history. |
| `update_history(history)` | `None` | Update the displayed execution history. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the history tab.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `append_entry`

```python
def append_entry(entry: Dict[str, Any]) -> None
```

Append a single entry to the history.

Args:
    entry: Execution history entry

**Parameters:**

- `entry: Dict[str, Any]` *(required)*

##### `clear`

```python
def clear() -> None
```

Clear all history entries.

##### `get_entry_count`

```python
def get_entry_count() -> int
```

Get total number of history entries.

##### `scroll_to_bottom`

```python
def scroll_to_bottom() -> None
```

Scroll to the bottom of the history.

##### `update_history`

```python
def update_history(history: List[Dict[str, Any]]) -> None
```

Update the displayed execution history.

Args:
    history: List of execution history entries

**Parameters:**

- `history: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.log_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\log_tab.py`


Log Tab for the Bottom Panel.

Provides real-time execution log display with filtering and navigation.


### LogTab

**Inherits from:** `QWidget`


Log tab widget for displaying execution logs.

Features:
- Filter by log level
- Click to navigate to node
- Auto-scroll toggle
- Export to file

Signals:
    navigate_to_node: Emitted when user wants to navigate to a node


**Attributes:**

- `COL_LEVEL: int`
- `COL_MESSAGE: int`
- `COL_NODE: int`
- `COL_TIME: int`
- `navigate_to_node: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Log tab. |
| `clear()` | `None` | Clear the log. |
| `get_entry_count()` | `int` | Get the number of log entries. |
| `log_event(event)` | `None` | Log an execution event. |
| `log_message(message, level, node_id)` | `None` | Log a custom message. |
| `set_max_entries(max_entries)` | `None` | Set maximum number of log entries. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Log tab.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear`

```python
def clear() -> None
```

Clear the log.

##### `get_entry_count`

```python
def get_entry_count() -> int
```

Get the number of log entries.

##### `log_event`

```python
def log_event(event: 'Event') -> None
```

Log an execution event.

Args:
    event: Event to log

**Parameters:**

- `event: 'Event'` *(required)*

##### `log_message`

```python
def log_message(message: str, level: str = 'info', node_id: Optional[str] = None) -> None
```

Log a custom message.

Args:
    message: Message text
    level: Log level (info, warning, error, success)
    node_id: Optional associated node ID

**Parameters:**

- `message: str` *(required)*
- `level: str = 'info'`
- `node_id: Optional[str] = None`

##### `set_max_entries`

```python
def set_max_entries(max_entries: int) -> None
```

Set maximum number of log entries.

**Parameters:**

- `max_entries: int` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.log_viewer_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\log_viewer_panel.py`


Log Viewer Panel for Robot Log Streaming.

Provides real-time log display from remote robots with filtering,
searching, and export capabilities. Connects to orchestrator via
WebSocket for live streaming.


### LogStreamWorker

**Inherits from:** `QObject`


Worker for WebSocket log streaming in background thread.


**Attributes:**

- `connected: Signal`
- `disconnected: Signal`
- `error: Signal`
- `log_received: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(orchestrator_url, api_secret, robot_id, ...)` | `None` | Initialize worker with connection parameters. |
| `run()` | `None` | Run the WebSocket connection loop. |
| `stop()` | `None` | Stop the worker. |

#### Method Details

##### `__init__`

```python
def __init__(orchestrator_url: str, api_secret: str, robot_id: Optional[str] = None, tenant_id: Optional[str] = None, min_level: str = 'DEBUG') -> None
```

Initialize worker with connection parameters.

**Parameters:**

- `orchestrator_url: str` *(required)*
- `api_secret: str` *(required)*
- `robot_id: Optional[str] = None`
- `tenant_id: Optional[str] = None`
- `min_level: str = 'DEBUG'`

##### `run`

```python
def run() -> None
```

Run the WebSocket connection loop.

##### `stop`

```python
def stop() -> None
```

Stop the worker.

### LogViewerPanel

**Inherits from:** `QDockWidget`


Dockable panel for viewing robot logs.

Features:
- Real-time log display with auto-scroll
- Level filtering (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Text search/filter
- Robot selector
- Export to file
- Connection status indicator

Signals:
    robot_selected: Emitted when robot is selected (str: robot_id)


**Attributes:**

- `COL_LEVEL: int`
- `COL_MESSAGE: int`
- `COL_ROBOT: int`
- `COL_SOURCE: int`
- `COL_TIME: int`
- `robot_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the log viewer panel. |
| `add_robot(robot_id, robot_name)` | `None` | Add a robot to the selector. |
| `cleanup()` | `None` | Clean up resources. |
| `clear()` | `None` | Clear the log table. |
| `clear_robots()` | `None` | Clear robot selector except 'All Robots'. |
| `configure(orchestrator_url, api_secret, tenant_id)` | `None` | Configure connection settings. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the log viewer panel.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_robot`

```python
def add_robot(robot_id: str, robot_name: str) -> None
```

Add a robot to the selector.

Args:
    robot_id: Robot UUID.
    robot_name: Display name.

**Parameters:**

- `robot_id: str` *(required)*
- `robot_name: str` *(required)*

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `clear`

```python
def clear() -> None
```

Clear the log table.

##### `clear_robots`

```python
def clear_robots() -> None
```

Clear robot selector except 'All Robots'.

##### `configure`

```python
def configure(orchestrator_url: str, api_secret: str, tenant_id: Optional[str] = None) -> None
```

Configure connection settings.

Args:
    orchestrator_url: Orchestrator WebSocket URL (ws:// or wss://).
    api_secret: Admin API secret for authentication.
    tenant_id: Optional tenant ID.

**Parameters:**

- `orchestrator_url: str` *(required)*
- `api_secret: str` *(required)*
- `tenant_id: Optional[str] = None`

---

## casare_rpa.presentation.canvas.ui.panels.minimap_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\minimap_panel.py`


Minimap Panel UI Component.

Provides a bird's-eye view of the workflow graph with viewport indicator.
Extracted from canvas/graph/minimap.py for reusability.


### MinimapChangeTracker


Tracks changes to determine when minimap needs update.

Uses event sourcing pattern to reduce unnecessary redraws.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(viewport_tolerance)` | `None` | Initialize change tracker. |
| `commit_update(viewport, node_count)` | `None` | Mark current state as rendered. |
| `mark_dirty()` | `None` | Mark state as dirty - requires update. |
| `should_update(current_viewport, node_count)` | `bool` | Check if minimap needs redraw. |

#### Method Details

##### `__init__`

```python
def __init__(viewport_tolerance: float = 2.0) -> None
```

Initialize change tracker.

Args:
    viewport_tolerance: Tolerance for viewport position changes

**Parameters:**

- `viewport_tolerance: float = 2.0`

##### `commit_update`

```python
def commit_update(viewport: QRectF, node_count: int) -> None
```

Mark current state as rendered.

Args:
    viewport: Current viewport rectangle
    node_count: Number of nodes

**Parameters:**

- `viewport: QRectF` *(required)*
- `node_count: int` *(required)*

##### `mark_dirty`

```python
def mark_dirty() -> None
```

Mark state as dirty - requires update.

##### `should_update`

```python
def should_update(current_viewport: QRectF, node_count: int) -> bool
```

Check if minimap needs redraw.

Args:
    current_viewport: Current viewport rectangle
    node_count: Number of nodes in the graph

Returns:
    True if update is needed

**Parameters:**

- `current_viewport: QRectF` *(required)*
- `node_count: int` *(required)*

### MinimapPanel

**Inherits from:** `QWidget`


Minimap panel widget for workflow overview.

Features:
- Bird's-eye view of entire workflow
- Viewport indicator
- Click to navigate
- Auto-scaling

Signals:
    viewport_clicked: Emitted when user clicks on minimap (QPointF: scene_pos)


**Attributes:**

- `viewport_clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize minimap panel. |
| `hideEvent(event)` | `None` | Handle hide event. |
| `mark_dirty()` | `None` | Mark minimap as needing update. |
| `set_graph_view(graph_view)` | `None` | Set the main graph view to track. |
| `showEvent(event)` | `None` | Handle show event. |
| `update_minimap()` | `None` | Update minimap display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize minimap panel.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `hideEvent`

```python
def hideEvent(event) -> None
```

Handle hide event.

Args:
    event: Hide event

**Parameters:**

- `event` *(required)*

##### `mark_dirty`

```python
def mark_dirty() -> None
```

Mark minimap as needing update.

##### `set_graph_view`

```python
def set_graph_view(graph_view) -> None
```

Set the main graph view to track.

Args:
    graph_view: NodeGraphQt view instance

**Parameters:**

- `graph_view` *(required)*

##### `showEvent`

```python
def showEvent(event) -> None
```

Handle show event.

Args:
    event: Show event

**Parameters:**

- `event` *(required)*

##### `update_minimap`

```python
def update_minimap() -> None
```

Update minimap display.

### MinimapView

**Inherits from:** `QGraphicsView`


Custom QGraphicsView for minimap display.

Provides a simplified view of the workflow graph.


**Attributes:**

- `viewport_clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize minimap view. |
| `drawForeground(painter, rect)` | `None` | Draw viewport indicator overlay. |
| `mousePressEvent(event)` | - | Handle mouse press to navigate. |
| `set_viewport_rect(rect)` | `None` | Set the viewport indicator rectangle. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize minimap view.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `drawForeground`

```python
def drawForeground(painter: QPainter, rect: QRectF) -> None
```

Draw viewport indicator overlay.

Args:
    painter: QPainter instance
    rect: Scene rectangle to draw

**Parameters:**

- `painter: QPainter` *(required)*
- `rect: QRectF` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event)
```

Handle mouse press to navigate.

Args:
    event: Mouse event

**Parameters:**

- `event` *(required)*

##### `set_viewport_rect`

```python
def set_viewport_rect(rect: QRectF) -> None
```

Set the viewport indicator rectangle.

Args:
    rect: Viewport rectangle in scene coordinates

**Parameters:**

- `rect: QRectF` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.output_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\output_tab.py`


Output Tab for the Bottom Panel.

Displays workflow outputs and return values.


### OutputTab

**Inherits from:** `QWidget`


Output tab widget for displaying workflow outputs.

Features:
- Output variables set by nodes
- Final workflow result/status
- Timestamps for each output
- Value preview panel


**Attributes:**

- `COL_NAME: int`
- `COL_TIME: int`
- `COL_TYPE: int`
- `COL_VALUE: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Output tab. |
| `add_output(name, value, timestamp)` | `None` | Add an output to the table. |
| `clear()` | `None` | Clear all outputs. |
| `get_output_count()` | `int` | Get the number of outputs. |
| `get_outputs()` | `dict` | Get all outputs as a dictionary. |
| `set_workflow_result(success, message)` | `None` | Set the final workflow result. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Output tab.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_output`

```python
def add_output(name: str, value: Any, timestamp: Optional[str] = None) -> None
```

Add an output to the table.

Args:
    name: Output name/key
    value: Output value
    timestamp: Optional timestamp string

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*
- `timestamp: Optional[str] = None`

##### `clear`

```python
def clear() -> None
```

Clear all outputs.

##### `get_output_count`

```python
def get_output_count() -> int
```

Get the number of outputs.

##### `get_outputs`

```python
def get_outputs() -> dict
```

Get all outputs as a dictionary.

Returns:
    Dict of {name: value}

##### `set_workflow_result`

```python
def set_workflow_result(success: bool, message: str) -> None
```

Set the final workflow result.

Args:
    success: Whether workflow completed successfully
    message: Result message

**Parameters:**

- `success: bool` *(required)*
- `message: str` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.process_mining_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\process_mining_panel.py`


Process Mining Panel UI Component.

Provides AI-powered process discovery, variant analysis, conformance checking,
and optimization insights from workflow execution logs.


### AIEnhanceWorker

**Inherits from:** `QObject`


Worker for background AI enhancement of process insights.


**Attributes:**

- `error: Signal`
- `finished: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(insights, model, provider, ...)` | `None` | Initialize worker with insights data. |
| `run()` | `None` | Execute the AI enhancement. |

#### Method Details

##### `__init__`

```python
def __init__(insights: List[Dict[str, Any]], model: str, provider: str, process_model: Dict[str, Any]) -> None
```

Initialize worker with insights data.

**Parameters:**

- `insights: List[Dict[str, Any]]` *(required)*
- `model: str` *(required)*
- `provider: str` *(required)*
- `process_model: Dict[str, Any]` *(required)*

##### `run`

```python
def run() -> None
```

Execute the AI enhancement.

### ProcessMiningPanel

**Inherits from:** `QDockWidget`


Dockable panel for Process Mining capabilities.

Features:
- Process Discovery: Build process models from execution logs
- Variant Analysis: See different execution paths
- Conformance Checking: Compare actual vs expected
- Optimization Insights: AI-generated recommendations

Signals:
    workflow_selected: Emitted when workflow is selected (str: workflow_id)
    insight_clicked: Emitted when insight is clicked (dict: insight_data)


**Attributes:**

- `insight_clicked: Signal`
- `workflow_selected: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the process mining panel. |
| `add_demo_data()` | `None` | Add demo data for testing. |
| `cleanup()` | `None` | Clean up resources. |
| `get_ai_settings()` | `dict` | Get current AI model settings. |
| `hideEvent(event)` | `None` | Handle hide event. |
| `showEvent(event)` | `None` | Handle show event. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the process mining panel.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_demo_data`

```python
def add_demo_data() -> None
```

Add demo data for testing.

##### `cleanup`

```python
def cleanup() -> None
```

Clean up resources.

##### `get_ai_settings`

```python
def get_ai_settings() -> dict
```

Get current AI model settings.

Returns:
    Dict with provider and model keys.

##### `hideEvent`

```python
def hideEvent(event) -> None
```

Handle hide event.

**Parameters:**

- `event` *(required)*

##### `showEvent`

```python
def showEvent(event) -> None
```

Handle show event.

**Parameters:**

- `event` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.properties_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\properties_panel.py`


Properties Panel UI Component.

Dockable panel that displays and edits properties of the selected node.
Extracted from canvas/panels/properties_panel.py for reusability.


### CollapsibleSection

**Inherits from:** `QWidget`


A collapsible section widget with header and content area.

Provides expandable/collapsible sections similar to UiPath, n8n, and VS Code.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, parent)` | `None` | Initialize collapsible section. |
| `add_property_row(label, widget)` | `QWidget` | Add a label + widget row to content area. |
| `add_widget(widget)` | `None` | Add widget to content area. |

#### Method Details

##### `__init__`

```python
def __init__(title: str, parent: Optional[QWidget] = None) -> None
```

Initialize collapsible section.

Args:
    title: Section title
    parent: Optional parent widget

**Parameters:**

- `title: str` *(required)*
- `parent: Optional[QWidget] = None`

##### `add_property_row`

```python
def add_property_row(label: str, widget: QWidget) -> QWidget
```

Add a label + widget row to content area.

Args:
    label: Property label text
    widget: Property input widget

Returns:
    Row container widget

**Parameters:**

- `label: str` *(required)*
- `widget: QWidget` *(required)*

##### `add_widget`

```python
def add_widget(widget: QWidget) -> None
```

Add widget to content area.

Args:
    widget: Widget to add

**Parameters:**

- `widget: QWidget` *(required)*

### PropertiesPanel

**Inherits from:** `QDockWidget`


Dockable properties panel for editing selected node properties.

Features:
- Node information display (name, type, ID)
- Collapsible property sections
- Type-aware property editors
- Real-time property updates

Signals:
    property_changed: Emitted when property value changes (str: node_id, str: property_name, object: value)
    robot_override_changed: Emitted when node robot override changes (str: node_id, dict: override_config)
    robot_override_cleared: Emitted when node robot override is cleared (str: node_id)


**Attributes:**

- `property_changed: Signal`
- `robot_override_changed: Signal`
- `robot_override_cleared: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the properties panel. |
| `refresh()` | `None` | Refresh the properties display. |
| `set_available_robots(robots)` | `None` | Update the list of available robots for selection. |
| `set_cloud_mode(enabled)` | `None` | Enable or disable cloud execution mode. |
| `set_node(node)` | `None` | Set the node to display properties for. |
| `set_node_override(override)` | `None` | Set the current node's robot override configuration. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the properties panel.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `refresh`

```python
def refresh() -> None
```

Refresh the properties display.

##### `set_available_robots`

```python
def set_available_robots(robots: List[Dict[str, Any]]) -> None
```

Update the list of available robots for selection.

Args:
    robots: List of robot dictionaries with id, name, status keys

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*

##### `set_cloud_mode`

```python
def set_cloud_mode(enabled: bool) -> None
```

Enable or disable cloud execution mode.

When cloud mode is enabled, the robot override section is shown.
Robot overrides only apply to cloud execution.

Args:
    enabled: Whether cloud execution mode is enabled

**Parameters:**

- `enabled: bool` *(required)*

##### `set_node`

```python
def set_node(node: Optional['BaseNode']) -> None
```

Set the node to display properties for.

Args:
    node: The selected node, or None to clear

**Parameters:**

- `node: Optional['BaseNode']` *(required)*

##### `set_node_override`

```python
def set_node_override(override: Optional[Dict[str, Any]]) -> None
```

Set the current node's robot override configuration.

Called when a node is selected to load its existing override.

Args:
    override: Override configuration dict or None

**Parameters:**

- `override: Optional[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.robot_picker_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\robot_picker_panel.py`


Robot Picker Panel UI Component.

Dockable panel for selecting robots and toggling execution mode.
Allows users to choose between local execution and cloud robot submission.


### RobotPickerPanel

**Inherits from:** `QDockWidget`


Panel to select robots and execution mode.

Features:
- Execution mode toggle: Local vs Cloud
- Tree view of available robots with status indicators
- Robot filtering by capability
- Refresh button to update robot list
- Status indicators: green=online, yellow=busy, red=offline, gray=maintenance

Signals:
    robot_selected: Emitted when user selects a robot (robot_id: str)
    execution_mode_changed: Emitted when execution mode changes ('local' or 'cloud')
    refresh_requested: Emitted when user requests robot list refresh


**Attributes:**

- `execution_mode_changed: Signal`
- `refresh_requested: Signal`
- `robot_selected: Signal`
- `submit_to_cloud_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Robot Picker Panel. |
| `clear_selection()` | `None` | Clear robot selection. |
| `get_execution_mode()` | `str` | Get current execution mode. |
| `get_selected_robot()` | `Optional[str]` | Get selected robot ID. |
| `is_connected()` | `bool` | Get orchestrator connection status. |
| `refresh()` | `None` | Trigger a refresh of the robot list. |
| `select_robot(robot_id)` | `bool` | Select a robot by ID. |
| `set_connected(connected)` | `None` | Set orchestrator connection status. |
| `set_execution_mode(mode)` | `None` | Set execution mode programmatically. |
| `set_refreshing(refreshing)` | `None` | Set refresh button state during refresh operation. |
| `set_submitting(submitting)` | `None` | Set submit button state during submission. |
| `show_submit_result(success, message)` | `None` | Show result of job submission. |
| `update_robots(robots)` | `None` | Update robot list from data. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Robot Picker Panel.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear_selection`

```python
def clear_selection() -> None
```

Clear robot selection.

##### `get_execution_mode`

```python
def get_execution_mode() -> str
```

Get current execution mode.

Returns:
    'local' or 'cloud'

##### `get_selected_robot`

```python
def get_selected_robot() -> Optional[str]
```

Get selected robot ID.

Returns:
    Selected robot ID or None

##### `is_connected`

```python
def is_connected() -> bool
```

Get orchestrator connection status.

Returns:
    True if connected to orchestrator

##### `refresh`

```python
def refresh() -> None
```

Trigger a refresh of the robot list.

##### `select_robot`

```python
def select_robot(robot_id: str) -> bool
```

Select a robot by ID.

Args:
    robot_id: Robot ID to select

Returns:
    True if robot was found and selected

**Parameters:**

- `robot_id: str` *(required)*

##### `set_connected`

```python
def set_connected(connected: bool) -> None
```

Set orchestrator connection status.

Args:
    connected: True if connected to orchestrator

**Parameters:**

- `connected: bool` *(required)*

##### `set_execution_mode`

```python
def set_execution_mode(mode: str) -> None
```

Set execution mode programmatically.

Args:
    mode: 'local' or 'cloud'

**Parameters:**

- `mode: str` *(required)*

##### `set_refreshing`

```python
def set_refreshing(refreshing: bool) -> None
```

Set refresh button state during refresh operation.

Args:
    refreshing: True to show refreshing state

**Parameters:**

- `refreshing: bool` *(required)*

##### `set_submitting`

```python
def set_submitting(submitting: bool) -> None
```

Set submit button state during submission.

Args:
    submitting: True to show submitting state

**Parameters:**

- `submitting: bool` *(required)*

##### `show_submit_result`

```python
def show_submit_result(success: bool, message: str) -> None
```

Show result of job submission.

Args:
    success: Whether submission succeeded
    message: Result message (job ID or error)

**Parameters:**

- `success: bool` *(required)*
- `message: str` *(required)*

##### `update_robots`

```python
def update_robots(robots: List['Robot']) -> None
```

Update robot list from data.

Args:
    robots: List of Robot entities to display

**Parameters:**

- `robots: List['Robot']` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.terminal_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\terminal_tab.py`


Terminal Tab for the Bottom Panel.

Provides raw stdout/stderr output display during workflow execution.


### TerminalTab

**Inherits from:** `QWidget`


Terminal tab widget for displaying raw output.

Wraps OutputConsoleWidget to show stdout/stderr during workflow execution.
Provides a VSCode-style terminal experience.

Signals:
    output_received: Emitted when new output is received


**Attributes:**

- `output_received: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Terminal tab. |
| `append_debug(text)` | `None` | Append debug message. |
| `append_error(text)` | `None` | Append error message. |
| `append_info(text)` | `None` | Append info message. |
| `append_success(text)` | `None` | Append success message. |
| `append_warning(text)` | `None` | Append warning message. |
| `clear()` | `None` | Clear the terminal. |
| `get_line_count()` | `int` | Get the number of lines in the terminal. |
| `get_text()` | `str` | Get all terminal text. |
| `write(text, level)` | `None` | Write text to the terminal. |
| `write_stderr(text)` | `None` | Write stderr text to the terminal. |
| `write_stdout(text)` | `None` | Write stdout text to the terminal. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Terminal tab.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `append_debug`

```python
def append_debug(text: str) -> None
```

Append debug message.

**Parameters:**

- `text: str` *(required)*

##### `append_error`

```python
def append_error(text: str) -> None
```

Append error message.

**Parameters:**

- `text: str` *(required)*

##### `append_info`

```python
def append_info(text: str) -> None
```

Append info message.

**Parameters:**

- `text: str` *(required)*

##### `append_success`

```python
def append_success(text: str) -> None
```

Append success message.

**Parameters:**

- `text: str` *(required)*

##### `append_warning`

```python
def append_warning(text: str) -> None
```

Append warning message.

**Parameters:**

- `text: str` *(required)*

##### `clear`

```python
def clear() -> None
```

Clear the terminal.

##### `get_line_count`

```python
def get_line_count() -> int
```

Get the number of lines in the terminal.

##### `get_text`

```python
def get_text() -> str
```

Get all terminal text.

##### `write`

```python
def write(text: str, level: str = 'info') -> None
```

Write text to the terminal.

Args:
    text: Text to write
    level: Output level (info, warning, error, success, debug)

**Parameters:**

- `text: str` *(required)*
- `level: str = 'info'`

##### `write_stderr`

```python
def write_stderr(text: str) -> None
```

Write stderr text to the terminal.

Args:
    text: Text from stderr

**Parameters:**

- `text: str` *(required)*

##### `write_stdout`

```python
def write_stdout(text: str) -> None
```

Write stdout text to the terminal.

Args:
    text: Text from stdout

**Parameters:**

- `text: str` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.validation_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\validation_tab.py`


Validation Tab for the Bottom Panel.

Provides workflow validation results display with navigation support.


### ValidationTab

**Inherits from:** `QWidget`


Validation tab widget for displaying workflow validation results.

Features:
- Tree view with errors/warnings grouped by type
- Click to navigate to node
- Auto-validate on change
- Manual validate button

Signals:
    validation_requested: Emitted when user requests manual validation
    issue_clicked: Emitted when user clicks an issue (location: str)


**Attributes:**

- `issue_clicked: Signal`
- `validation_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the Validation tab. |
| `clear()` | `None` | Clear validation results. |
| `get_all_errors()` | `list` | Get all validation errors as a list of dictionaries. |
| `get_issue_count()` | `tuple` | Get the count of errors and warnings. |
| `get_result()` | `Optional['ValidationResult']` | Get the last validation result. |
| `has_errors()` | `bool` | Check if there are validation errors. |
| `set_result(result)` | `None` | Update with validation results. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the Validation tab.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear`

```python
def clear() -> None
```

Clear validation results.

##### `get_all_errors`

```python
def get_all_errors() -> list
```

Get all validation errors as a list of dictionaries.

Returns:
    List of error dictionaries with keys: severity, code, message, location, suggestion

##### `get_issue_count`

```python
def get_issue_count() -> tuple
```

Get the count of errors and warnings.

Returns:
    Tuple of (error_count, warning_count)

##### `get_result`

```python
def get_result() -> Optional['ValidationResult']
```

Get the last validation result.

##### `has_errors`

```python
def has_errors() -> bool
```

Check if there are validation errors.

##### `set_result`

```python
def set_result(result: 'ValidationResult') -> None
```

Update with validation results.

Args:
    result: ValidationResult to display

**Parameters:**

- `result: 'ValidationResult'` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.variable_inspector_dock

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variable_inspector_dock.py`


Variable Inspector Dock - Runtime variable value viewer.

Shows real-time variable values during workflow execution.


### VariableInspectorDock

**Inherits from:** `QDockWidget`


Dock widget for inspecting runtime variable values.

Shows variable values during workflow execution, separate from
the design-time Variables panel.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the variable inspector dock. |
| `clear()` | `None` | Clear all displayed variables. |
| `update_variables(variables)` | `None` | Update displayed variables. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the variable inspector dock.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear`

```python
def clear() -> None
```

Clear all displayed variables.

##### `update_variables`

```python
def update_variables(variables: Dict[str, Any]) -> None
```

Update displayed variables.

Args:
    variables: Dictionary of variable name -> value

**Parameters:**

- `variables: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.variables_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variables_panel.py`


Variables Panel UI Component.

Provides workflow variable management with inline editing similar to UiPath.
Extracted from canvas/panels/variables_tab.py for reusability.

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.


### TypeComboDelegate

**Inherits from:** `QStyledItemDelegate`


Delegate for type selection dropdown in table.

Provides a dropdown for selecting variable types when editing.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `createEditor(parent, option, index)` | - | Create combo box editor. |
| `setEditorData(editor, index)` | - | Set editor data from model. |
| `setModelData(editor, model, index)` | - | Set model data from editor. |

#### Method Details

##### `createEditor`

```python
def createEditor(parent, option, index)
```

Create combo box editor.

Args:
    parent: Parent widget
    option: Style option
    index: Model index

Returns:
    QComboBox editor

**Parameters:**

- `parent` *(required)*
- `option` *(required)*
- `index` *(required)*

##### `setEditorData`

```python
def setEditorData(editor, index)
```

Set editor data from model.

Args:
    editor: Editor widget
    index: Model index

**Parameters:**

- `editor` *(required)*
- `index` *(required)*

##### `setModelData`

```python
def setModelData(editor, model, index)
```

Set model data from editor.

Args:
    editor: Editor widget
    model: Data model
    index: Model index

**Parameters:**

- `editor` *(required)*
- `model` *(required)*
- `index` *(required)*

### VariablesPanel

**Inherits from:** `QDockWidget`


Dockable variables panel for workflow variable management.

Features:
- Inline variable creation
- Type selection
- Default value editing
- Scope indicators
- Design/Runtime modes

Signals:
    variable_added: Emitted when variable is added (str: name, str: type, Any: default_value)
    variable_changed: Emitted when variable is modified (str: name, str: type, Any: default_value)
    variable_removed: Emitted when variable is removed (str: name)
    variables_changed: Emitted when variables dict changes (dict: all_variables)


**Attributes:**

- `COL_DEFAULT: int`
- `COL_NAME: int`
- `COL_SCOPE: int`
- `COL_TYPE: int`
- `variable_added: Signal`
- `variable_changed: Signal`
- `variable_removed: Signal`
- `variables_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the variables panel. |
| `add_variable(name, var_type, default_value, ...)` | `None` | Add a variable to the panel. |
| `clear_variables()` | `None` | Clear all variables. |
| `get_variables()` | `Dict[str, Dict[str, Any]]` | Get all variables. |
| `remove_variable(name)` | `None` | Remove a variable from the panel. |
| `set_runtime_mode(enabled)` | `None` | Set runtime mode. |
| `update_variable_value(name, value)` | `None` | Update variable value (runtime mode). |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the variables panel.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_variable`

```python
def add_variable(name: str, var_type: str = 'String', default_value: Any = '', scope: str = 'Workflow') -> None
```

Add a variable to the panel.

Args:
    name: Variable name
    var_type: Variable type
    default_value: Default value
    scope: Variable scope

**Parameters:**

- `name: str` *(required)*
- `var_type: str = 'String'`
- `default_value: Any = ''`
- `scope: str = 'Workflow'`

##### `clear_variables`

```python
def clear_variables() -> None
```

Clear all variables.

##### `get_variables`

```python
def get_variables() -> Dict[str, Dict[str, Any]]
```

Get all variables.

Returns:
    Dictionary of all variables

##### `remove_variable`

```python
def remove_variable(name: str) -> None
```

Remove a variable from the panel.

Args:
    name: Variable name

**Parameters:**

- `name: str` *(required)*

##### `set_runtime_mode`

```python
def set_runtime_mode(enabled: bool) -> None
```

Set runtime mode.

In runtime mode, variable values are displayed but not editable.

Args:
    enabled: True for runtime mode, False for design mode

**Parameters:**

- `enabled: bool` *(required)*

##### `update_variable_value`

```python
def update_variable_value(name: str, value: Any) -> None
```

Update variable value (runtime mode).

Args:
    name: Variable name
    value: New value

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*

---

## casare_rpa.presentation.canvas.ui.panels.variables_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variables_tab.py`


Variables Tab - QWidget wrapper for VariablesPanel.

Provides tab-compatible interface for bottom panel integration.


### VariablesTab

**Inherits from:** `QWidget`


Tab wrapper for VariablesPanel.

Signals:
    variables_changed: Emitted when variables dict changes


**Attributes:**

- `variables_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the variables tab. |
| `clear()` | `None` | Clear all variables. |
| `get_variables()` | `Dict[str, Dict[str, Any]]` | Get current variables. |
| `set_runtime_mode(enabled)` | `None` | Switch between design mode and runtime mode. |
| `set_variables(variables)` | `None` | Set variables. |
| `update_runtime_values(values)` | `None` | Update variable values during runtime. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the variables tab.

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `clear`

```python
def clear() -> None
```

Clear all variables.

##### `get_variables`

```python
def get_variables() -> Dict[str, Dict[str, Any]]
```

Get current variables.

##### `set_runtime_mode`

```python
def set_runtime_mode(enabled: bool) -> None
```

Switch between design mode and runtime mode.

Args:
    enabled: True for runtime mode, False for design mode

**Parameters:**

- `enabled: bool` *(required)*

##### `set_variables`

```python
def set_variables(variables: Dict[str, Dict[str, Any]]) -> None
```

Set variables.

**Parameters:**

- `variables: Dict[str, Dict[str, Any]]` *(required)*

##### `update_runtime_values`

```python
def update_runtime_values(values: Dict[str, Any]) -> None
```

Update variable values during runtime.

Args:
    values: Dict of {variable_name: current_value}

**Parameters:**

- `values: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.signal_bridge

**File:** `src\casare_rpa\presentation\canvas\ui\signal_bridge.py`


Signal Bridge for MainWindow Controller Connections.

This module provides a bridge class that connects controller signals
to MainWindow handlers and other controllers. Extracts ~400 lines
of signal/slot connection code from MainWindow.


### BottomPanelSignalBridge

**Inherits from:** `QObject`


Bridge that connects BottomPanel signals to MainWindow handlers.

Handles variable changes and validation requests from the bottom panel dock widget.

Note: Triggers are now visual nodes on the canvas (not managed via bottom panel).


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize the bottom panel signal bridge. |
| `connect_bottom_panel(panel)` | `None` | Connect BottomPanelDock signals to MainWindow handlers. |
| `connect_execution_timeline(timeline, dock)` | `None` | Connect ExecutionTimeline signals to MainWindow handlers. |
| `connect_properties_panel(panel)` | `None` | Connect PropertiesPanel signals to MainWindow handlers. |
| `connect_variable_inspector(dock)` | `None` | Connect VariableInspectorDock signals to MainWindow handlers... |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize the bottom panel signal bridge.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `connect_bottom_panel`

```python
def connect_bottom_panel(panel) -> None
```

Connect BottomPanelDock signals to MainWindow handlers.

Args:
    panel: BottomPanelDock instance

**Parameters:**

- `panel` *(required)*

##### `connect_execution_timeline`

```python
def connect_execution_timeline(timeline, dock) -> None
```

Connect ExecutionTimeline signals to MainWindow handlers.

Args:
    timeline: ExecutionTimeline widget
    dock: QDockWidget containing the timeline

**Parameters:**

- `timeline` *(required)*
- `dock` *(required)*

##### `connect_properties_panel`

```python
def connect_properties_panel(panel) -> None
```

Connect PropertiesPanel signals to MainWindow handlers.

Args:
    panel: PropertiesPanel instance

**Parameters:**

- `panel` *(required)*

##### `connect_variable_inspector`

```python
def connect_variable_inspector(dock) -> None
```

Connect VariableInspectorDock signals to MainWindow handlers.

Args:
    dock: VariableInspectorDock instance

**Parameters:**

- `dock` *(required)*

### ControllerSignalBridge

**Inherits from:** `QObject`


Bridge that connects controller signals to MainWindow handlers.

This class centralizes all signal/slot connections between controllers
and the MainWindow, reducing code in MainWindow and making the
signal flow easier to understand and maintain.

The bridge is responsible for:
- Connecting workflow controller signals (new, open, save, etc.)
- Connecting execution controller signals (start, pause, stop, etc.)
- Connecting node controller signals (select, deselect, etc.)
- Connecting panel controller signals (toggle, show, hide, etc.)
- Forwarding events between controllers when needed

Example:
    bridge = ControllerSignalBridge(main_window)
    bridge.connect_all_controllers(
        workflow_controller,
        execution_controller,
        node_controller,
        ...
    )


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(main_window)` | `None` | Initialize the signal bridge. |
| `connect_all_controllers(workflow_controller, execution_controller, node_controller, ...)` | `None` | Connect all controller signals to MainWindow handlers. |

#### Method Details

##### `__init__`

```python
def __init__(main_window: 'MainWindow') -> None
```

Initialize the signal bridge.

Args:
    main_window: Parent MainWindow instance

**Parameters:**

- `main_window: 'MainWindow'` *(required)*

##### `connect_all_controllers`

```python
def connect_all_controllers(workflow_controller: Optional['WorkflowController'] = None, execution_controller: Optional['ExecutionController'] = None, node_controller: Optional['NodeController'] = None, connection_controller: Optional['ConnectionController'] = None, panel_controller: Optional['PanelController'] = None, menu_controller: Optional['MenuController'] = None, event_bus_controller: Optional['EventBusController'] = None, viewport_controller: Optional['ViewportController'] = None, scheduling_controller: Optional['SchedulingController'] = None, ui_state_controller: Optional['UIStateController'] = None) -> None
```

Connect all controller signals to MainWindow handlers.

Args:
    workflow_controller: Workflow management controller
    execution_controller: Workflow execution controller
    node_controller: Node management controller
    connection_controller: Connection management controller
    panel_controller: Panel/dock management controller
    menu_controller: Menu/dialog management controller
    event_bus_controller: EventBus integration controller
    viewport_controller: Viewport/zoom management controller
    scheduling_controller: Workflow scheduling controller
    ui_state_controller: UI state persistence controller

Note: Triggers are now visual nodes on the canvas (not a controller).

**Parameters:**

- `workflow_controller: Optional['WorkflowController'] = None`
- `execution_controller: Optional['ExecutionController'] = None`
- `node_controller: Optional['NodeController'] = None`
- `connection_controller: Optional['ConnectionController'] = None`
- `panel_controller: Optional['PanelController'] = None`
- `menu_controller: Optional['MenuController'] = None`
- `event_bus_controller: Optional['EventBusController'] = None`
- `viewport_controller: Optional['ViewportController'] = None`
- `scheduling_controller: Optional['SchedulingController'] = None`
- `ui_state_controller: Optional['UIStateController'] = None`

---

## casare_rpa.presentation.canvas.ui.toolbars.hotkey_manager

**File:** `src\casare_rpa\presentation\canvas\ui\toolbars\hotkey_manager.py`


Hotkey manager dialog for viewing and customizing keyboard shortcuts.

This module provides a dialog for users to view, edit, and customize
all keyboard shortcuts in the application.


### HotkeyEditor

**Inherits from:** `QDialog`


Dialog for editing a single hotkey.


**Attributes:**

- `hotkey_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(action_name, current_shortcut, parent)` | - | Initialize hotkey editor dialog. |
| `get_shortcut()` | `str` | Get the new shortcut string. |
| `keyPressEvent(event)` | - | Capture key press events. |

#### Method Details

##### `__init__`

```python
def __init__(action_name: str, current_shortcut: str, parent = None)
```

Initialize hotkey editor dialog.

Args:
    action_name: Name of the action being edited
    current_shortcut: Current keyboard shortcut
    parent: Parent widget

**Parameters:**

- `action_name: str` *(required)*
- `current_shortcut: str` *(required)*
- `parent = None`

##### `get_shortcut`

```python
def get_shortcut() -> str
```

Get the new shortcut string.

##### `keyPressEvent`

```python
def keyPressEvent(event)
```

Capture key press events.

**Parameters:**

- `event` *(required)*

### HotkeyManagerDialog

**Inherits from:** `QDialog`


Dialog for managing all application hotkeys.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(actions, parent)` | - | Initialize hotkey manager dialog. |

#### Method Details

##### `__init__`

```python
def __init__(actions: Dict[str, QAction], parent = None)
```

Initialize hotkey manager dialog.

Args:
    actions: Dictionary mapping action names to QAction objects
    parent: Parent widget

**Parameters:**

- `actions: Dict[str, QAction]` *(required)*
- `parent = None`

---

## casare_rpa.presentation.canvas.ui.toolbars.main_toolbar

**File:** `src\casare_rpa\presentation\canvas\ui\toolbars\main_toolbar.py`


Main Toolbar UI Component.

Provides primary workflow actions (new, open, save, run, etc.).


### MainToolbar

**Inherits from:** `QToolBar`


Main toolbar for workflow operations.

Features:
- New workflow
- Open workflow
- Save workflow
- Run workflow
- Pause/Resume
- Stop
- Undo/Redo

Signals:
    new_requested: Emitted when user requests new workflow
    open_requested: Emitted when user requests to open workflow
    save_requested: Emitted when user requests to save workflow
    save_as_requested: Emitted when user requests save as
    run_requested: Emitted when user requests to run workflow
    pause_requested: Emitted when user requests to pause workflow
    resume_requested: Emitted when user requests to resume workflow
    stop_requested: Emitted when user requests to stop workflow
    undo_requested: Emitted when user requests undo
    redo_requested: Emitted when user requests redo


**Attributes:**

- `new_requested: Signal`
- `open_requested: Signal`
- `pause_requested: Signal`
- `redo_requested: Signal`
- `resume_requested: Signal`
- `run_requested: Signal`
- `save_as_requested: Signal`
- `save_requested: Signal`
- `stop_requested: Signal`
- `undo_requested: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize the main toolbar. |
| `set_execution_state(is_running, is_paused)` | `None` | Update toolbar based on execution state. |
| `set_redo_enabled(enabled)` | `None` | Set redo action enabled state. |
| `set_undo_enabled(enabled)` | `None` | Set undo action enabled state. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize the main toolbar.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `set_execution_state`

```python
def set_execution_state(is_running: bool, is_paused: bool = False) -> None
```

Update toolbar based on execution state.

Args:
    is_running: Whether workflow is currently executing
    is_paused: Whether workflow is paused

**Parameters:**

- `is_running: bool` *(required)*
- `is_paused: bool = False`

##### `set_redo_enabled`

```python
def set_redo_enabled(enabled: bool) -> None
```

Set redo action enabled state.

Args:
    enabled: Whether redo is available

**Parameters:**

- `enabled: bool` *(required)*

##### `set_undo_enabled`

```python
def set_undo_enabled(enabled: bool) -> None
```

Set undo action enabled state.

Args:
    enabled: Whether undo is available

**Parameters:**

- `enabled: bool` *(required)*

---

## casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\ai_settings_widget.py`


AI Settings Widget - Reusable credential and model selector for AI features.

Provides a standardized way to select:
- API Key / Credential (from credential store)
- AI Provider (OpenAI, Anthropic, Google, etc.)
- Model (filtered by provider)


### Functions

#### `detect_provider_from_model`

```python
def detect_provider_from_model(model: str) -> str
```

Detect provider from model name.

Args:
    model: Model identifier

Returns:
    Provider name

#### `get_all_models`

```python
def get_all_models() -> List[str]
```

Get flat list of all available models.

#### `get_llm_credentials`

```python
def get_llm_credentials() -> List[Dict[str, Any]]
```

Get available LLM credentials from credential store.

Returns:
    List of credential dicts with id, name, provider fields.


### AISettingsWidget

**Inherits from:** `QWidget`


Reusable widget for AI credential and model selection.

Signals:
    settings_changed: Emitted when any setting changes (dict with provider, model, credential)
    credential_changed: Emitted when credential changes (str: credential_id)
    provider_changed: Emitted when provider changes (str: provider_name)
    model_changed: Emitted when model changes (str: model_id)


**Attributes:**

- `credential_changed: Signal`
- `model_changed: Signal`
- `provider_changed: Signal`
- `settings_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, title, show_credential, ...)` | `None` | Initialize AI settings widget. |
| `apply_dark_style()` | `None` | Apply dark theme styling. |
| `get_credential_id()` | `Optional[str]` | Get currently selected credential ID. |
| `get_model()` | `str` | Get currently selected model. |
| `get_provider()` | `str` | Get currently selected provider. |
| `get_settings()` | `Dict[str, Any]` | Get current AI settings. |
| `refresh_credentials()` | `None` | Refresh the credentials list. |
| `set_model(model)` | `None` | Set the selected model. |
| `set_provider(provider)` | `None` | Set the selected provider. |
| `set_settings(settings)` | `None` | Set AI settings. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None, title: str = 'AI Settings', show_credential: bool = True, show_provider: bool = True, show_model: bool = True, compact: bool = False) -> None
```

Initialize AI settings widget.

Args:
    parent: Parent widget
    title: Group box title (empty for no group box)
    show_credential: Whether to show credential selector
    show_provider: Whether to show provider selector
    show_model: Whether to show model selector
    compact: Use compact layout (horizontal)

**Parameters:**

- `parent: Optional[QWidget] = None`
- `title: str = 'AI Settings'`
- `show_credential: bool = True`
- `show_provider: bool = True`
- `show_model: bool = True`
- `compact: bool = False`

##### `apply_dark_style`

```python
def apply_dark_style() -> None
```

Apply dark theme styling.

##### `get_credential_id`

```python
def get_credential_id() -> Optional[str]
```

Get currently selected credential ID.

##### `get_model`

```python
def get_model() -> str
```

Get currently selected model.

##### `get_provider`

```python
def get_provider() -> str
```

Get currently selected provider.

##### `get_settings`

```python
def get_settings() -> Dict[str, Any]
```

Get current AI settings.

Returns:
    Dict with credential_id, provider, model keys.

##### `refresh_credentials`

```python
def refresh_credentials() -> None
```

Refresh the credentials list.

##### `set_model`

```python
def set_model(model: str) -> None
```

Set the selected model.

**Parameters:**

- `model: str` *(required)*

##### `set_provider`

```python
def set_provider(provider: str) -> None
```

Set the selected provider.

**Parameters:**

- `provider: str` *(required)*

##### `set_settings`

```python
def set_settings(settings: Dict[str, Any]) -> None
```

Set AI settings.

Args:
    settings: Dict with credential_id, provider, model keys.

**Parameters:**

- `settings: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.widgets.execution_timeline

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\execution_timeline.py`


Execution Timeline for CasareRPA.

Visual timeline showing node execution order and timing.


### ExecutionTimeline

**Inherits from:** `QWidget`


Visual timeline of workflow execution.

Shows node executions as horizontal bars with timing information.

Signals:
    node_clicked: Emitted when a node bar is clicked (node_id: str)


**Attributes:**

- `node_clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `add_event(node_id, node_name, event_type, ...)` | `None` | Add an execution event. |
| `clear()` | `None` | Clear the timeline. |
| `end_execution()` | `None` | Mark the end of execution. |
| `get_events()` | `List[TimelineEvent]` | Get all timeline events. |
| `start_execution()` | `None` | Mark the start of execution. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `add_event`

```python
def add_event(node_id: str, node_name: str, event_type: str, duration_ms: Optional[float] = None, error_message: Optional[str] = None) -> None
```

Add an execution event.

Args:
    node_id: Node ID
    node_name: Display name
    event_type: 'started', 'completed', or 'error'
    duration_ms: Execution duration in milliseconds
    error_message: Error message if failed

**Parameters:**

- `node_id: str` *(required)*
- `node_name: str` *(required)*
- `event_type: str` *(required)*
- `duration_ms: Optional[float] = None`
- `error_message: Optional[str] = None`

##### `clear`

```python
def clear() -> None
```

Clear the timeline.

##### `end_execution`

```python
def end_execution() -> None
```

Mark the end of execution.

##### `get_events`

```python
def get_events() -> List[TimelineEvent]
```

Get all timeline events.

##### `start_execution`

```python
def start_execution() -> None
```

Mark the start of execution.

### TimelineBar

**Inherits from:** `QWidget`


Individual timeline bar representing a node execution.


**Attributes:**

- `clicked: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(event, start_time, total_duration, ...)` | `None` |  |
| `enterEvent(event)` | `None` |  |
| `leaveEvent(event)` | `None` |  |
| `mousePressEvent(event)` | `None` |  |
| `paintEvent(event)` | `None` | Paint the timeline bar. |

#### Method Details

##### `__init__`

```python
def __init__(event: TimelineEvent, start_time: datetime, total_duration: float, parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `event: TimelineEvent` *(required)*
- `start_time: datetime` *(required)*
- `total_duration: float` *(required)*
- `parent: Optional[QWidget] = None`

##### `enterEvent`

```python
def enterEvent(event) -> None
```

**Parameters:**

- `event` *(required)*

##### `leaveEvent`

```python
def leaveEvent(event) -> None
```

**Parameters:**

- `event` *(required)*

##### `mousePressEvent`

```python
def mousePressEvent(event) -> None
```

**Parameters:**

- `event` *(required)*

##### `paintEvent`

```python
def paintEvent(event) -> None
```

Paint the timeline bar.

**Parameters:**

- `event` *(required)*

### TimelineEvent

**Decorators:** `@dataclass`


Represents an event on the timeline.


**Attributes:**

- `duration_ms: Optional[float]`
- `error_message: Optional[str]`
- `event_type: str`
- `node_id: str`
- `node_name: str`
- `timestamp: datetime`

---

## casare_rpa.presentation.canvas.ui.widgets.output_console_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\output_console_widget.py`


Output Console Widget UI Component.

Provides console-style output display for workflow execution.


### OutputConsoleWidget

**Inherits from:** `BaseWidget`


Console widget for displaying execution output.

Features:
- Colored output (info, warning, error, success)
- Auto-scroll
- Clear functionality
- Timestamp display
- Copy to clipboard


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize output console widget. |
| `append_debug(text)` | `None` | Append debug message. |
| `append_error(text)` | `None` | Append error message. |
| `append_info(text)` | `None` | Append info message. |
| `append_line(text, level, timestamp)` | `None` | Append a line to the console. |
| `append_success(text)` | `None` | Append success message. |
| `append_warning(text)` | `None` | Append warning message. |
| `clear()` | `None` | Clear console contents. |
| `get_text()` | `str` | Get all console text. |
| `set_auto_scroll(enabled)` | `None` | Set auto-scroll enabled state. |
| `set_max_lines(max_lines)` | `None` | Set maximum number of lines to keep. |
| `set_show_timestamps(enabled)` | `None` | Set timestamp display enabled state. |
| `setup_ui()` | `None` | Set up the user interface. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize output console widget.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `append_debug`

```python
def append_debug(text: str) -> None
```

Append debug message.

Args:
    text: Message text

**Parameters:**

- `text: str` *(required)*

##### `append_error`

```python
def append_error(text: str) -> None
```

Append error message.

Args:
    text: Message text

**Parameters:**

- `text: str` *(required)*

##### `append_info`

```python
def append_info(text: str) -> None
```

Append info message.

Args:
    text: Message text

**Parameters:**

- `text: str` *(required)*

##### `append_line`

```python
def append_line(text: str, level: str = 'info', timestamp: bool = True) -> None
```

Append a line to the console.

Args:
    text: Text to append
    level: Message level (info, warning, error, success)
    timestamp: Whether to include timestamp

**Parameters:**

- `text: str` *(required)*
- `level: str = 'info'`
- `timestamp: bool = True`

##### `append_success`

```python
def append_success(text: str) -> None
```

Append success message.

Args:
    text: Message text

**Parameters:**

- `text: str` *(required)*

##### `append_warning`

```python
def append_warning(text: str) -> None
```

Append warning message.

Args:
    text: Message text

**Parameters:**

- `text: str` *(required)*

##### `clear`

```python
def clear() -> None
```

Clear console contents.

##### `get_text`

```python
def get_text() -> str
```

Get all console text.

Returns:
    Console text content

##### `set_auto_scroll`

```python
def set_auto_scroll(enabled: bool) -> None
```

Set auto-scroll enabled state.

Args:
    enabled: Whether to enable auto-scroll

**Parameters:**

- `enabled: bool` *(required)*

##### `set_max_lines`

```python
def set_max_lines(max_lines: int) -> None
```

Set maximum number of lines to keep.

Args:
    max_lines: Maximum number of lines

**Parameters:**

- `max_lines: int` *(required)*

##### `set_show_timestamps`

```python
def set_show_timestamps(enabled: bool) -> None
```

Set timestamp display enabled state.

Args:
    enabled: Whether to show timestamps

**Parameters:**

- `enabled: bool` *(required)*

##### `setup_ui`

```python
def setup_ui() -> None
```

Set up the user interface.

---

## casare_rpa.presentation.canvas.ui.widgets.performance_dashboard

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\performance_dashboard.py`


Performance Dashboard for CasareRPA Canvas.

Displays real-time performance metrics including:
- System resources (CPU, memory)
- Node execution statistics
- Workflow execution timing
- Connection pool metrics
- Cache hit rates


### Functions

#### `show_performance_dashboard`

```python
def show_performance_dashboard(parent: Optional[QWidget] = None) -> None
```

Show the performance dashboard dialog.


### CountersGaugesPanel

**Inherits from:** `QGroupBox`


Panel displaying raw counters and gauges.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_metrics(counters, gauges)` | `None` | Update counters and gauges display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_metrics`

```python
def update_metrics(counters: Dict[str, int], gauges: Dict[str, float]) -> None
```

Update counters and gauges display.

**Parameters:**

- `counters: Dict[str, int]` *(required)*
- `gauges: Dict[str, float]` *(required)*

### HistogramWidget

**Inherits from:** `QWidget`


Widget displaying a histogram with percentile bars.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_data(histogram_data)` | `None` | Update the histogram display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_data`

```python
def update_data(histogram_data: Dict[str, Any]) -> None
```

Update the histogram display.

**Parameters:**

- `histogram_data: Dict[str, Any]` *(required)*

### MetricCard

**Inherits from:** `QFrame`


A card widget displaying a single metric with label and value.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(title, value, subtitle, ...)` | `None` |  |
| `set_color(color)` | `None` | Set the value text color. |
| `set_value(value, subtitle)` | `None` | Update the displayed value. |

#### Method Details

##### `__init__`

```python
def __init__(title: str, value: str = '0', subtitle: str = '', parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `title: str` *(required)*
- `value: str = '0'`
- `subtitle: str = ''`
- `parent: Optional[QWidget] = None`

##### `set_color`

```python
def set_color(color: str) -> None
```

Set the value text color.

**Parameters:**

- `color: str` *(required)*

##### `set_value`

```python
def set_value(value: str, subtitle: str = '') -> None
```

Update the displayed value.

**Parameters:**

- `value: str` *(required)*
- `subtitle: str = ''`

### NodeMetricsPanel

**Inherits from:** `QGroupBox`


Panel displaying node execution metrics.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_metrics(node_data)` | `None` | Update node metrics display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_metrics`

```python
def update_metrics(node_data: Dict[str, Any]) -> None
```

Update node metrics display.

**Parameters:**

- `node_data: Dict[str, Any]` *(required)*

### PerformanceDashboardDialog

**Inherits from:** `QDialog`


Performance Dashboard Dialog.

Displays comprehensive performance metrics with live updates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `closeEvent(event)` | `None` | Handle dialog close. |
| `register_pool_callback(callback)` | `None` | Register a callback for collecting pool metrics. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `closeEvent`

```python
def closeEvent(event) -> None
```

Handle dialog close.

**Parameters:**

- `event` *(required)*

##### `register_pool_callback`

```python
def register_pool_callback(callback) -> None
```

Register a callback for collecting pool metrics.

**Parameters:**

- `callback` *(required)*

### PoolMetricsPanel

**Inherits from:** `QGroupBox`


Panel displaying connection pool metrics.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_metrics(pool_data)` | `None` | Update pool metrics display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_metrics`

```python
def update_metrics(pool_data: Dict[str, Dict[str, Any]]) -> None
```

Update pool metrics display.

**Parameters:**

- `pool_data: Dict[str, Dict[str, Any]]` *(required)*

### SystemMetricsPanel

**Inherits from:** `QGroupBox`


Panel displaying system resource metrics.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_metrics(system_data)` | `None` | Update system metrics display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_metrics`

```python
def update_metrics(system_data: Dict[str, Any]) -> None
```

Update system metrics display.

**Parameters:**

- `system_data: Dict[str, Any]` *(required)*

### WorkflowMetricsPanel

**Inherits from:** `QGroupBox`


Panel displaying workflow execution metrics.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `update_metrics(workflow_data)` | `None` | Update workflow metrics display. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `update_metrics`

```python
def update_metrics(workflow_data: Dict[str, Any]) -> None
```

Update workflow metrics display.

**Parameters:**

- `workflow_data: Dict[str, Any]` *(required)*

---

## casare_rpa.presentation.canvas.ui.widgets.robot_override_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\robot_override_widget.py`


Robot Override Widget for Node-Level Robot Targeting.

Provides UI for configuring node-level robot overrides within workflows.
Allows users to target specific robots or required capabilities for individual nodes.


### RobotOverrideWidget

**Inherits from:** `QWidget`


Widget for configuring node robot override.

Allows users to override the workflow's default robot assignment
for individual nodes, either by selecting a specific robot or
by specifying required capabilities.

Features:
- Enable/disable override checkbox
- Mode selector: Specific Robot vs By Capability
- Robot dropdown for specific mode
- Capability checkboxes for capability mode
- Reason field for documentation

Signals:
    override_changed: Emitted when override config changes (dict with config)
    override_cleared: Emitted when override is disabled/cleared


**Attributes:**

- `override_changed: Signal`
- `override_cleared: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` | Initialize robot override widget. |
| `get_override()` | `Optional[Dict[str, Any]]` | Get current override configuration from widget. |
| `is_override_enabled()` | `bool` | Check if override is currently enabled. |
| `set_available_robots(robots)` | `None` | Update robot dropdown with available robots. |
| `set_cloud_mode(enabled)` | `None` | Enable/disable based on cloud execution mode. |
| `set_override(override)` | `None` | Load existing override configuration into widget. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None) -> None
```

Initialize robot override widget.

Args:
    parent: Optional parent widget

**Parameters:**

- `parent: Optional[QWidget] = None`

##### `get_override`

```python
def get_override() -> Optional[Dict[str, Any]]
```

Get current override configuration from widget.

Returns:
    Override dict or None if disabled. Dict contains:
        - robot_id: Specific robot ID (if specific mode)
        - required_capabilities: List of capability strings (if capability mode)
        - reason: Optional reason string
        - is_active: Always True when returned

##### `is_override_enabled`

```python
def is_override_enabled() -> bool
```

Check if override is currently enabled.

Returns:
    True if override is enabled

##### `set_available_robots`

```python
def set_available_robots(robots: List[Dict[str, Any]]) -> None
```

Update robot dropdown with available robots.

Args:
    robots: List of robot dicts with 'id', 'name', 'status' keys

**Parameters:**

- `robots: List[Dict[str, Any]]` *(required)*

##### `set_cloud_mode`

```python
def set_cloud_mode(enabled: bool) -> None
```

Enable/disable based on cloud execution mode.

When cloud mode is disabled, this widget should be hidden
as robot overrides only apply to cloud execution.

Args:
    enabled: Whether cloud execution mode is enabled

**Parameters:**

- `enabled: bool` *(required)*

##### `set_override`

```python
def set_override(override: Optional[Dict[str, Any]]) -> None
```

Load existing override configuration into widget.

Args:
    override: Override dict with keys:
        - robot_id: Optional specific robot ID
        - required_capabilities: List of capability strings
        - reason: Optional reason string
        - is_active: Whether override is active

**Parameters:**

- `override: Optional[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.widgets.search_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\search_widget.py`


Search Widget UI Component.

Provides search functionality with fuzzy matching.


### SearchWidget

**Inherits from:** `BaseWidget`


Search widget with fuzzy matching.

Features:
- Live search with fuzzy matching
- Result list with navigation
- Keyboard shortcuts
- Clear functionality

Signals:
    item_selected: Emitted when item is selected (str: item_text, object: item_data)
    search_cleared: Emitted when search is cleared


**Attributes:**

- `item_selected: Signal`
- `search_cleared: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(placeholder, parent)` | `None` | Initialize search widget. |
| `add_item(text, data)` | `None` | Add a searchable item. |
| `clear_items()` | `None` | Clear all items. |
| `clear_search()` | `None` | Clear search input and show all results. |
| `eventFilter(obj, event)` | `bool` | Handle keyboard navigation. |
| `focus_search()` | `None` | Focus the search input. |
| `set_fuzzy_match_function(func)` | `None` | Set custom fuzzy match function. |
| `set_items(items)` | `None` | Set searchable items. |
| `setup_ui()` | `None` | Set up the user interface. |

#### Method Details

##### `__init__`

```python
def __init__(placeholder: str = 'Search...', parent: Optional[QWidget] = None) -> None
```

Initialize search widget.

Args:
    placeholder: Placeholder text for search input
    parent: Optional parent widget

**Parameters:**

- `placeholder: str = 'Search...'`
- `parent: Optional[QWidget] = None`

##### `add_item`

```python
def add_item(text: str, data: object = None) -> None
```

Add a searchable item.

Args:
    text: Item display text
    data: Optional item data

**Parameters:**

- `text: str` *(required)*
- `data: object = None`

##### `clear_items`

```python
def clear_items() -> None
```

Clear all items.

##### `clear_search`

```python
def clear_search() -> None
```

Clear search input and show all results.

##### `eventFilter`

```python
def eventFilter(obj, event) -> bool
```

Handle keyboard navigation.

Args:
    obj: Event object
    event: Event

Returns:
    True if event was handled

**Parameters:**

- `obj` *(required)*
- `event` *(required)*

##### `focus_search`

```python
def focus_search() -> None
```

Focus the search input.

##### `set_fuzzy_match_function`

```python
def set_fuzzy_match_function(func: Callable[[str, str], bool]) -> None
```

Set custom fuzzy match function.

Args:
    func: Function that takes (query, item_text) and returns bool

**Parameters:**

- `func: Callable[[str, str], bool]` *(required)*

##### `set_items`

```python
def set_items(items: List[tuple]) -> None
```

Set searchable items.

Args:
    items: List of (text, data) tuples

**Parameters:**

- `items: List[tuple]` *(required)*

##### `setup_ui`

```python
def setup_ui() -> None
```

Set up the user interface.

---

## casare_rpa.presentation.canvas.ui.widgets.tenant_selector

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\tenant_selector.py`


Tenant Selector Widget.

Provides a dropdown for admin users to switch between tenants.
Super admins can select "All Tenants" to view all robots.


### TenantFilterWidget

**Inherits from:** `TenantSelectorWidget`


Tenant filter widget variant for use in data tables.

Same as TenantSelectorWidget but with "All Tenants" selected by default
and designed for filtering lists rather than context switching.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, show_all_option)` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None, show_all_option: bool = True) -> None
```

**Parameters:**

- `parent: Optional[QWidget] = None`
- `show_all_option: bool = True`

### TenantSelectorWidget

**Inherits from:** `QWidget`


Widget for selecting active tenant.

Features:
- Dropdown to switch between tenants
- "All Tenants" option for super admin
- Shows current tenant name
- Refresh button

Signals:
    tenant_changed: Emitted when tenant selection changes (tenant_id or None for all)
    refresh_requested: Emitted when refresh is clicked


**Attributes:**

- `ALL_TENANTS: str`
- `refresh_requested: Signal`
- `tenant_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent, show_all_option, label_text)` | `None` | Initialize the tenant selector. |
| `count()` | `int` | Get number of tenants in dropdown (excluding 'All Tenants'). |
| `get_current_tenant_id()` | `Optional[str]` | Get currently selected tenant ID. |
| `get_current_tenant_name()` | `str` | Get currently selected tenant name. |
| `is_all_tenants_selected()` | `bool` | Check if "All Tenants" is currently selected. |
| `setEnabled(enabled)` | `None` | Enable or disable the selector. |
| `set_current_tenant(tenant_id)` | `None` | Set current tenant selection programmatically. |
| `set_show_all_option(show)` | `None` | Set whether to show "All Tenants" option. |
| `set_show_refresh(show)` | `None` | Set whether to show refresh button. |
| `set_super_admin(is_super_admin)` | `None` | Set whether current user is a super admin. |
| `update_tenants(tenants)` | `None` | Update the list of available tenants. |

#### Method Details

##### `__init__`

```python
def __init__(parent: Optional[QWidget] = None, show_all_option: bool = True, label_text: str = 'Tenant:') -> None
```

Initialize the tenant selector.

Args:
    parent: Parent widget.
    show_all_option: Whether to show "All Tenants" option.
    label_text: Label text before dropdown.

**Parameters:**

- `parent: Optional[QWidget] = None`
- `show_all_option: bool = True`
- `label_text: str = 'Tenant:'`

##### `count`

```python
def count() -> int
```

Get number of tenants in dropdown (excluding 'All Tenants').

##### `get_current_tenant_id`

```python
def get_current_tenant_id() -> Optional[str]
```

Get currently selected tenant ID.

Returns:
    Tenant ID string, or None if "All Tenants" is selected.

##### `get_current_tenant_name`

```python
def get_current_tenant_name() -> str
```

Get currently selected tenant name.

Returns:
    Tenant name or "All Tenants".

##### `is_all_tenants_selected`

```python
def is_all_tenants_selected() -> bool
```

Check if "All Tenants" is currently selected.

Returns:
    True if "All Tenants" is selected.

##### `setEnabled`

```python
def setEnabled(enabled: bool) -> None
```

Enable or disable the selector.

**Parameters:**

- `enabled: bool` *(required)*

##### `set_current_tenant`

```python
def set_current_tenant(tenant_id: Optional[str]) -> None
```

Set current tenant selection programmatically.

Args:
    tenant_id: Tenant ID to select, or None for "All Tenants".

**Parameters:**

- `tenant_id: Optional[str]` *(required)*

##### `set_show_all_option`

```python
def set_show_all_option(show: bool) -> None
```

Set whether to show "All Tenants" option.

Args:
    show: True to show option.

**Parameters:**

- `show: bool` *(required)*

##### `set_show_refresh`

```python
def set_show_refresh(show: bool) -> None
```

Set whether to show refresh button.

Args:
    show: True to show button.

**Parameters:**

- `show: bool` *(required)*

##### `set_super_admin`

```python
def set_super_admin(is_super_admin: bool) -> None
```

Set whether current user is a super admin.

Super admins can see "All Tenants" option.

Args:
    is_super_admin: True if user is super admin.

**Parameters:**

- `is_super_admin: bool` *(required)*

##### `update_tenants`

```python
def update_tenants(tenants: List[Dict[str, Any]]) -> None
```

Update the list of available tenants.

Args:
    tenants: List of tenant dictionaries with 'id' and 'name' keys.

**Parameters:**

- `tenants: List[Dict[str, Any]]` *(required)*

---

## casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\variable_editor_widget.py`


Variable Editor Widget UI Component.

Provides inline variable editing functionality.


### VariableEditorWidget

**Inherits from:** `BaseWidget`


Widget for editing a single variable.

Features:
- Variable name input
- Type selection
- Value input
- Validation

Signals:
    variable_changed: Emitted when variable changes (str: name, str: type, Any: value)


**Attributes:**

- `variable_changed: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(name, var_type, value, ...)` | `None` | Initialize variable editor widget. |
| `get_remove_button()` | `QPushButton` | Get the remove button for connecting signals. |
| `get_variable()` | `Dict[str, Any]` | Get variable data. |
| `set_variable(name, var_type, value)` | `None` | Set variable data. |
| `setup_ui()` | `None` | Set up the user interface. |

#### Method Details

##### `__init__`

```python
def __init__(name: str = '', var_type: str = 'String', value: Any = '', parent: Optional[QWidget] = None) -> None
```

Initialize variable editor widget.

Args:
    name: Variable name
    var_type: Variable type
    value: Variable value
    parent: Optional parent widget

**Parameters:**

- `name: str = ''`
- `var_type: str = 'String'`
- `value: Any = ''`
- `parent: Optional[QWidget] = None`

##### `get_remove_button`

```python
def get_remove_button() -> QPushButton
```

Get the remove button for connecting signals.

Returns:
    Remove button widget

##### `get_variable`

```python
def get_variable() -> Dict[str, Any]
```

Get variable data.

Returns:
    Dictionary with name, type, and value

##### `set_variable`

```python
def set_variable(name: str, var_type: str, value: Any) -> None
```

Set variable data.

Args:
    name: Variable name
    var_type: Variable type
    value: Variable value

**Parameters:**

- `name: str` *(required)*
- `var_type: str` *(required)*
- `value: Any` *(required)*

##### `setup_ui`

```python
def setup_ui() -> None
```

Set up the user interface.

---

## casare_rpa.presentation.canvas.visual_nodes.ai_ml.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\ai_ml\nodes.py`


Visual nodes for AI/ML category.

Provides visual node wrappers for LLM operations including:
- Text completion
- Multi-turn chat
- Data extraction
- Summarization
- Classification
- Translation

Features:
- Dynamic model filtering based on selected credential provider
- Live model fetching from provider APIs (cached)


### Functions

#### `get_llm_credentials`

```python
def get_llm_credentials() -> List[Tuple[str, str]]
```

Get available LLM credentials for dropdown.

Returns:
    List of (id, display_name) tuples, with "Auto-detect" as first option.

#### `get_models_for_credential`

```python
def get_models_for_credential(credential_name: str) -> List[str]
```

Get models filtered by the credential's provider.

Args:
    credential_name: The selected credential name

Returns:
    List of model IDs for that provider, or all models if auto-detect


### LLMVisualNodeMixin


Mixin for LLM visual nodes with credential-model linking.

When credential selection changes, the model dropdown is automatically
filtered to show only models from that provider.


**Attributes:**

- `_credential_widget: Any`
- `_model_widget: Any`

### VisualLLMChatNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMChatNode.

Multi-turn chat conversation with an LLM.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM chat node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM chat node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLLMClassifyNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMClassifyNode.

Classify text into categories using an LLM.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM classify node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM classify node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLLMCompletionNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMCompletionNode.

Generate text completion from a prompt using LLM.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM completion node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM completion node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLLMExtractDataNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMExtractDataNode.

Extract structured data from text using JSON schema.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM extract data node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM extract data node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLLMSummarizeNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMSummarizeNode.

Summarize text using an LLM.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM summarize node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM summarize node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLLMTranslateNode

**Inherits from:** `VisualNode`, `LLMVisualNodeMixin`


Visual representation of LLMTranslateNode.

Translate text to another language using an LLM.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize LLM translate node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize LLM translate node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.base_visual_node

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\base_visual_node.py`


Base Visual Node for CasareRPA.

This module provides the base VisualNode class to avoid circular imports.


### VisualNode

**Inherits from:** `NodeGraphQtBaseNode`


Base class for visual nodes in NodeGraphQt.

Bridges CasareRPA BaseNode with NodeGraphQt visual representation.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize visual node. |
| `add_exec_input(name)` | `None` | Add an execution flow input port. |
| `add_exec_output(name)` | `None` | Add an execution flow output port. |
| `add_typed_input(name, data_type)` | `None` | Add an input port with type information. |
| `add_typed_output(name, data_type)` | `None` | Add an output port with type information. |
| `ensure_casare_node()` | `Optional[CasareBaseNode]` | Ensure this visual node has a CasareRPA node, creating one i... |
| `get_casare_node()` | `Optional[CasareBaseNode]` | Get the underlying CasareRPA node instance. |
| `get_port_type(port_name)` | `Optional[DataType]` | Get the DataType for a port. |
| `is_exec_port(port_name)` | `bool` | Check if a port is an execution flow port. |
| `set_casare_node(node)` | `None` | Set the underlying CasareRPA node instance. |
| `setup_ports()` | `None` | Setup node ports. |
| `sync_types_from_casare_node()` | `None` | Propagate type information from the linked CasareRPA node. |
| `update_execution_time(time_seconds)` | `None` | Update the displayed execution time. |
| `update_status(status)` | `None` | Update node visual status. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize visual node.

##### `add_exec_input`

```python
def add_exec_input(name: str = 'exec_in') -> None
```

Add an execution flow input port.

Exec ports use None as their type marker.
Exec inputs accept multiple connections to support merging execution paths.

Args:
    name: Port name (default: "exec_in")

**Parameters:**

- `name: str = 'exec_in'`

##### `add_exec_output`

```python
def add_exec_output(name: str = 'exec_out') -> None
```

Add an execution flow output port.

Exec ports use None as their type marker.

Args:
    name: Port name (default: "exec_out")

**Parameters:**

- `name: str = 'exec_out'`

##### `add_typed_input`

```python
def add_typed_input(name: str, data_type: DataType = DataType.ANY) -> None
```

Add an input port with type information.

Args:
    name: Port name
    data_type: The DataType for this port

**Parameters:**

- `name: str` *(required)*
- `data_type: DataType = DataType.ANY`

##### `add_typed_output`

```python
def add_typed_output(name: str, data_type: DataType = DataType.ANY) -> None
```

Add an output port with type information.

Args:
    name: Port name
    data_type: The DataType for this port

**Parameters:**

- `name: str` *(required)*
- `data_type: DataType = DataType.ANY`

##### `ensure_casare_node`

```python
def ensure_casare_node() -> Optional[CasareBaseNode]
```

Ensure this visual node has a CasareRPA node, creating one if necessary.
Use this before any operation that requires the CasareRPA node.

Returns:
    The CasareRPA node instance, or None if creation failed

##### `get_casare_node`

```python
def get_casare_node() -> Optional[CasareBaseNode]
```

Get the underlying CasareRPA node instance.

Returns:
    CasareRPA node instance or None

##### `get_port_type`

```python
def get_port_type(port_name: str) -> Optional[DataType]
```

Get the DataType for a port.

Args:
    port_name: Name of the port

Returns:
    DataType if it's a data port, None if it's an exec port

**Parameters:**

- `port_name: str` *(required)*

##### `is_exec_port`

```python
def is_exec_port(port_name: str) -> bool
```

Check if a port is an execution flow port.

Args:
    port_name: Name of the port

Returns:
    True if this is an execution port

**Parameters:**

- `port_name: str` *(required)*

##### `set_casare_node`

```python
def set_casare_node(node: CasareBaseNode) -> None
```

Set the underlying CasareRPA node instance.

Args:
    node: CasareRPA node instance

**Parameters:**

- `node: CasareBaseNode` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup node ports.

Override this method in subclasses to define ports.

##### `sync_types_from_casare_node`

```python
def sync_types_from_casare_node() -> None
```

Propagate type information from the linked CasareRPA node.

Call this after the CasareRPA node is set to automatically
populate port type information.

##### `update_execution_time`

```python
def update_execution_time(time_seconds: Optional[float]) -> None
```

Update the displayed execution time.

Args:
    time_seconds: Execution time in seconds, or None to clear

**Parameters:**

- `time_seconds: Optional[float]` *(required)*

##### `update_status`

```python
def update_status(status: str) -> None
```

Update node visual status.

Args:
    status: Node status (idle, running, success, error)

**Parameters:**

- `status: str` *(required)*

---

## casare_rpa.presentation.canvas.visual_nodes.basic.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\basic\nodes.py`


Visual nodes for basic category.


### VisualCommentNode

**Inherits from:** `VisualNode`


Visual representation of CommentNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize comment node. |
| `setup_ports()` | `None` | Setup ports for comment node. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize comment node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for comment node.

### VisualEndNode

**Inherits from:** `VisualNode`


Visual representation of EndNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports for end node. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for end node.

### VisualStartNode

**Inherits from:** `VisualNode`


Visual representation of StartNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports for start node. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports for start node.

---

## casare_rpa.presentation.canvas.visual_nodes.browser.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\browser\nodes.py`


Visual nodes for browser category.

Widget Auto-Generation:
-----------------------
Visual nodes automatically inherit widgets from their domain node's @node_schema
decorator via the __node_schema__ attribute (defined in casare_rpa.domain.decorators).

When a VisualNode is instantiated:
1. BaseVisualNode.__init__() checks if domain_node_class has __node_schema__
2. If found, widgets are auto-generated from PropertyDef declarations
3. Manual widget creation in __init__() should be AVOIDED to prevent duplicates

Nodes with manual widgets:
- GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode (navigation category)
- ClickElementNode, TypeTextNode, SelectDropdownNode (interaction category)
- ExtractTextNode, GetAttributeNode (data extraction category)
- ScreenshotNode, WaitNode, WaitForElementNode, WaitForNavigationNode (utility category)

These nodes still use manual widgets because their domain nodes haven't been
migrated to @node_schema yet. Once migrated, remove manual widgets from __init__().


### VisualClickElementNode

**Inherits from:** `VisualNode`


Visual representation of ClickElementNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize click element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize click element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCloseBrowserNode

**Inherits from:** `VisualNode`


Visual representation of CloseBrowserNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualDownloadFileNode

**Inherits from:** `VisualNode`


Visual representation of DownloadFileNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize download file node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize download file node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExtractTextNode

**Inherits from:** `VisualNode`


Visual representation of ExtractTextNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize extract text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize extract text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetAllImagesNode

**Inherits from:** `VisualNode`


Visual representation of GetAllImagesNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize get all images node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize get all images node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetAttributeNode

**Inherits from:** `VisualNode`


Visual representation of GetAttributeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize get attribute node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize get attribute node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGoBackNode

**Inherits from:** `VisualNode`


Visual representation of GoBackNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize go back node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize go back node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGoForwardNode

**Inherits from:** `VisualNode`


Visual representation of GoForwardNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize go forward node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize go forward node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGoToURLNode

**Inherits from:** `VisualNode`


Visual representation of GoToURLNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize go to URL node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize go to URL node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLaunchBrowserNode

**Inherits from:** `VisualNode`


Visual representation of LaunchBrowserNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize launch browser node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize launch browser node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualNewTabNode

**Inherits from:** `VisualNode`


Visual representation of NewTabNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRefreshPageNode

**Inherits from:** `VisualNode`


Visual representation of RefreshPageNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize refresh page node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize refresh page node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualScreenshotNode

**Inherits from:** `VisualNode`


Visual representation of ScreenshotNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize screenshot node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize screenshot node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSelectDropdownNode

**Inherits from:** `VisualNode`


Visual representation of SelectDropdownNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize select dropdown node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize select dropdown node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTypeTextNode

**Inherits from:** `VisualNode`


Visual representation of TypeTextNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize type text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize type text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWaitForElementNode

**Inherits from:** `VisualNode`


Visual representation of WaitForElementNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize wait for element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize wait for element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWaitForNavigationNode

**Inherits from:** `VisualNode`


Visual representation of WaitForNavigationNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize wait for navigation node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize wait for navigation node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWaitNode

**Inherits from:** `VisualNode`


Visual representation of WaitNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize wait node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize wait node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.control_flow.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\control_flow\nodes.py`


Visual nodes for control_flow category.


### VisualBreakNode

**Inherits from:** `VisualNode`


Visual representation of BreakNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Break node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Break node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCatchNode

**Inherits from:** `VisualNode`


Visual representation of CatchNode.
Note: This is created automatically by VisualTryCatchFinallyNode composite.
Hidden from menu - use "Try/Catch/Finally" instead.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Catch node. |
| `set_paired_try(try_node_id)` | `None` | Set the paired Try node ID (called automatically). |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Catch node.

##### `set_paired_try`

```python
def set_paired_try(try_node_id: str) -> None
```

Set the paired Try node ID (called automatically).

**Parameters:**

- `try_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualContinueNode

**Inherits from:** `VisualNode`


Visual representation of ContinueNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Continue node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Continue node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualFinallyNode

**Inherits from:** `VisualNode`


Visual representation of FinallyNode.
Note: This is created automatically by VisualTryCatchFinallyNode composite.
Hidden from menu - use "Try/Catch/Finally" instead.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Finally node. |
| `set_paired_try(try_node_id)` | `None` | Set the paired Try node ID (called automatically). |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Finally node.

##### `set_paired_try`

```python
def set_paired_try(try_node_id: str) -> None
```

Set the paired Try node ID (called automatically).

**Parameters:**

- `try_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualForLoopEndNode

**Inherits from:** `VisualNode`


Visual representation of ForLoopEndNode.
Note: This is created automatically by VisualForLoopNode composite.
Hidden from menu - use "For Loop" instead which creates both Start and End.


**Attributes:**

- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize For Loop End node. |
| `set_paired_start(start_node_id)` | `None` | Set the paired ForLoopStart node ID (automatic, not user-con... |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize For Loop End node.

##### `set_paired_start`

```python
def set_paired_start(start_node_id: str) -> None
```

Set the paired ForLoopStart node ID (automatic, not user-configurable).

**Parameters:**

- `start_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualForLoopNode

**Inherits from:** `VisualNode`


Composite For Loop - creates both ForLoopStart and ForLoopEnd nodes.

This is a marker class that appears in the menu. When selected,
special handling in node_graph_widget creates both Start and End nodes
and connects them together.


**Attributes:**

- `COMPOSITE_CREATES: list`
- `COMPOSITE_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize For Loop composite (not actually used - see node_... |
| `setup_ports()` | `None` | Setup ports (not actually used - composite creates real node... |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize For Loop composite (not actually used - see node_graph_widget).

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports (not actually used - composite creates real nodes).

### VisualForLoopStartNode

**Inherits from:** `VisualNode`


Visual representation of ForLoopStartNode.
Note: This is created automatically by VisualForLoopNode composite.
Hidden from menu - use "For Loop" instead which creates both Start and End.

Supports two modes (configured via properties panel):
    - items: ForEach mode - iterates over collections (lists, dicts, strings)
    - range: Counter mode - iterates over numeric range (start, end, step)

When iterating over a dict, current_key provides the key for each item.


**Attributes:**

- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize For Loop Start node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize For Loop Start node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualForkJoinNode

**Inherits from:** `VisualNode`


Composite Fork/Join - creates both ForkNode and JoinNode together.

This is a marker class that appears in the menu. When selected,
special handling creates Fork and Join nodes placed with space
between them for adding parallel branch nodes.

Layout:
    ForkNode ──┬── branch_1 ──→ [space for nodes] ──┬──→ JoinNode
               ├── branch_2 ──→ [space for nodes] ──┤
               └── branch_3 ──→ [space for nodes] ──┘


**Attributes:**

- `COMPOSITE_CREATES: list`
- `COMPOSITE_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Fork/Join composite. |
| `setup_ports()` | `None` | Setup ports (not used - composite creates real nodes). |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Fork/Join composite.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports (not used - composite creates real nodes).

### VisualForkNode

**Inherits from:** `VisualNode`


Visual representation of ForkNode.

Splits execution into multiple parallel branches that execute concurrently.
Use with JoinNode to synchronize branches back together.

Note: Created automatically by VisualForkJoinNode composite.
Can also be added independently from menu.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Fork node. |
| `set_paired_join(join_node_id)` | `None` | Set the paired JoinNode ID. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Fork node.

##### `set_paired_join`

```python
def set_paired_join(join_node_id: str) -> None
```

Set the paired JoinNode ID.

**Parameters:**

- `join_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualIfNode

**Inherits from:** `VisualNode`


Visual representation of IfNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize If node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize If node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualJoinNode

**Inherits from:** `VisualNode`


Visual representation of JoinNode.

Synchronizes parallel branches from a ForkNode.
Waits for all branches to complete before continuing execution.

Note: Created automatically by VisualForkJoinNode composite.
Can also be added independently from menu.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Join node. |
| `set_paired_fork(fork_node_id)` | `None` | Set the paired ForkNode ID. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Join node.

##### `set_paired_fork`

```python
def set_paired_fork(fork_node_id: str) -> None
```

Set the paired ForkNode ID.

**Parameters:**

- `fork_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMergeNode

**Inherits from:** `VisualNode`


Visual representation of MergeNode.

Allows multiple execution paths to converge into a single path.
Connect multiple exec outputs to this node's exec_in, then continue
from exec_out to the next node.

Example:
    If ──┬── TRUE ─────────┬──→ Merge ──→ Send Email
         └── FALSE → Zip ──┘


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Merge node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Merge node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualParallelForEachNode

**Inherits from:** `VisualNode`


Visual representation of ParallelForEachNode.

Processes list items concurrently in batches. Unlike regular ForLoop
which processes items one-by-one, this node processes multiple items
at the same time (up to batch_size).

Example:
    ParallelForEach ──→ ProcessURL ──→ SaveResult
        │
        ├─ items: [url1, url2, url3, ...]
        ├─ batch_size: 5 (process 5 at a time)
        └─ Outputs: current_item, current_index, results


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Parallel ForEach node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Parallel ForEach node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSwitchNode

**Inherits from:** `VisualNode`


Visual representation of SwitchNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Switch node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Switch node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTryCatchFinallyNode

**Inherits from:** `VisualNode`


Composite Try/Catch/Finally - creates all three nodes together.

This is a marker class that appears in the menu. When selected,
special handling creates Try, Catch, and Finally nodes
placed side-by-side with automatic ID pairing.


**Attributes:**

- `COMPOSITE_CREATES: list`
- `COMPOSITE_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Try/Catch/Finally composite. |
| `setup_ports()` | `None` | Setup ports (not actually used - composite creates real node... |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Try/Catch/Finally composite.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports (not actually used - composite creates real nodes).

### VisualTryNode

**Inherits from:** `VisualNode`


Visual representation of TryNode.
Note: This is created automatically by VisualTryCatchFinallyNode composite.
Hidden from menu - use "Try/Catch/Finally" instead.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Try node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Try node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhileLoopEndNode

**Inherits from:** `VisualNode`


Visual representation of WhileLoopEndNode.
Hidden from menu - use "While Loop" instead.


**Attributes:**

- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize While Loop End node. |
| `set_paired_start(start_node_id)` | `None` | Set the paired WhileLoopStart node ID (automatic, not user-c... |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize While Loop End node.

##### `set_paired_start`

```python
def set_paired_start(start_node_id: str) -> None
```

Set the paired WhileLoopStart node ID (automatic, not user-configurable).

**Parameters:**

- `start_node_id: str` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhileLoopNode

**Inherits from:** `VisualNode`


Composite While Loop - creates both WhileLoopStart and WhileLoopEnd nodes.

This is a marker class that appears in the menu. When selected,
special handling creates both Start and End nodes connected together.


**Attributes:**

- `COMPOSITE_CREATES: list`
- `COMPOSITE_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize While Loop composite. |
| `setup_ports()` | `None` | Setup ports (not used - composite creates real nodes). |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize While Loop composite.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports (not used - composite creates real nodes).

### VisualWhileLoopStartNode

**Inherits from:** `VisualNode`


Visual representation of WhileLoopStartNode.
Hidden from menu - use "While Loop" instead.


**Attributes:**

- `INTERNAL_NODE: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize While Loop Start node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize While Loop Start node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\data_operations\nodes.py`


Visual nodes for data operations category.


### VisualComparisonNode

**Inherits from:** `VisualNode`


Visual representation of ComparisonNode.

Widgets are auto-generated from ComparisonNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualConcatenateNode

**Inherits from:** `VisualNode`


Visual representation of ConcatenateNode.

Widgets are auto-generated from ConcatenateNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCreateDictNode

**Inherits from:** `VisualNode`


Visual representation of CreateDictNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualCreateListNode

**Inherits from:** `VisualNode`


Visual representation of CreateListNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualDictGetNode

**Inherits from:** `VisualNode`


Visual representation of DictGetNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictHasKeyNode

**Inherits from:** `VisualNode`


Visual representation of DictHasKeyNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictItemsNode

**Inherits from:** `VisualNode`


Visual representation of DictItemsNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictKeysNode

**Inherits from:** `VisualNode`


Visual representation of DictKeysNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictMergeNode

**Inherits from:** `VisualNode`


Visual representation of DictMergeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictRemoveNode

**Inherits from:** `VisualNode`


Visual representation of DictRemoveNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictSetNode

**Inherits from:** `VisualNode`


Visual representation of DictSetNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictToJsonNode

**Inherits from:** `VisualNode`


Visual representation of DictToJsonNode.

Widgets are auto-generated from DictToJsonNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualDictValuesNode

**Inherits from:** `VisualNode`


Visual representation of DictValuesNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualFormatStringNode

**Inherits from:** `VisualNode`


Visual representation of FormatStringNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetPropertyNode

**Inherits from:** `VisualNode`


Visual representation of GetPropertyNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualJsonParseNode

**Inherits from:** `VisualNode`


Visual representation of JsonParseNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualListAppendNode

**Inherits from:** `VisualNode`


Visual representation of ListAppendNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListContainsNode

**Inherits from:** `VisualNode`


Visual representation of ListContainsNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListFilterNode

**Inherits from:** `VisualNode`


Visual representation of ListFilterNode.

Widgets are auto-generated from ListFilterNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListFlattenNode

**Inherits from:** `VisualNode`


Visual representation of ListFlattenNode.

Widgets are auto-generated from ListFlattenNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListGetItemNode

**Inherits from:** `VisualNode`


Visual representation of ListGetItemNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualListJoinNode

**Inherits from:** `VisualNode`


Visual representation of ListJoinNode.

Widgets are auto-generated from ListJoinNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListLengthNode

**Inherits from:** `VisualNode`


Visual representation of ListLengthNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListMapNode

**Inherits from:** `VisualNode`


Visual representation of ListMapNode.

Widgets are auto-generated from ListMapNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListReduceNode

**Inherits from:** `VisualNode`


Visual representation of ListReduceNode.

Widgets are auto-generated from ListReduceNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListReverseNode

**Inherits from:** `VisualNode`


Visual representation of ListReverseNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListSliceNode

**Inherits from:** `VisualNode`


Visual representation of ListSliceNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListSortNode

**Inherits from:** `VisualNode`


Visual representation of ListSortNode.

Widgets are auto-generated from ListSortNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualListUniqueNode

**Inherits from:** `VisualNode`


Visual representation of ListUniqueNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualMathOperationNode

**Inherits from:** `VisualNode`


Visual representation of MathOperationNode.

Widgets are auto-generated from MathOperationNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | - | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports()
```

Setup ports.

### VisualRegexMatchNode

**Inherits from:** `VisualNode`


Visual representation of RegexMatchNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRegexReplaceNode

**Inherits from:** `VisualNode`


Visual representation of RegexReplaceNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.database.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\database\nodes.py`


Visual nodes for database category.


### VisualBeginTransactionNode

**Inherits from:** `VisualNode`


Visual representation of BeginTransactionNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Begin Transaction node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Begin Transaction node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCloseDatabaseNode

**Inherits from:** `VisualNode`


Visual representation of CloseDatabaseNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Close Database node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Close Database node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCommitTransactionNode

**Inherits from:** `VisualNode`


Visual representation of CommitTransactionNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Commit Transaction node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Commit Transaction node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualDatabaseConnectNode

**Inherits from:** `VisualNode`


Visual representation of DatabaseConnectNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Database Connect node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Database Connect node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExecuteBatchNode

**Inherits from:** `VisualNode`


Visual representation of ExecuteBatchNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Execute Batch node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Execute Batch node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExecuteNonQueryNode

**Inherits from:** `VisualNode`


Visual representation of ExecuteNonQueryNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Execute Non-Query node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Execute Non-Query node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExecuteQueryNode

**Inherits from:** `VisualNode`


Visual representation of ExecuteQueryNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Execute Query node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Execute Query node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetTableColumnsNode

**Inherits from:** `VisualNode`


Visual representation of GetTableColumnsNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Get Table Columns node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Get Table Columns node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRollbackTransactionNode

**Inherits from:** `VisualNode`


Visual representation of RollbackTransactionNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Rollback Transaction node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Rollback Transaction node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTableExistsNode

**Inherits from:** `VisualNode`


Visual representation of TableExistsNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Table Exists node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Table Exists node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.desktop_automation.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\desktop_automation\nodes.py`


Visual nodes for desktop_automation category.


### VisualActivateWindowNode

**Inherits from:** `VisualNode`


Visual representation of ActivateWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Activate Window node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Activate Window node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCaptureElementImageNode

**Inherits from:** `VisualNode`


Visual representation of CaptureElementImageNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Capture Element Image node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Capture Element Image node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCaptureScreenshotNode

**Inherits from:** `VisualNode`


Visual representation of CaptureScreenshotNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Capture Screenshot node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Capture Screenshot node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCheckCheckboxNode

**Inherits from:** `VisualNode`


Visual representation of CheckCheckboxNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Check Checkbox node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Check Checkbox node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualClickElementDesktopNode

**Inherits from:** `VisualNode`


Visual representation of ClickElementNode (Desktop).


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Click Element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Click Element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCloseApplicationNode

**Inherits from:** `VisualNode`


Visual representation of CloseApplicationNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Close Application node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Close Application node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualCompareImagesNode

**Inherits from:** `VisualNode`


Visual representation of CompareImagesNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Compare Images node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Compare Images node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualDesktopWaitForElementNode

**Inherits from:** `VisualNode`


Visual representation of desktop WaitForElementNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Wait For Desktop Element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Wait For Desktop Element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualDragMouseNode

**Inherits from:** `VisualNode`


Visual representation of DragMouseNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Drag Mouse node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Drag Mouse node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExpandTreeItemNode

**Inherits from:** `VisualNode`


Visual representation of ExpandTreeItemNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Expand Tree Item node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Expand Tree Item node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualFindElementNode

**Inherits from:** `VisualNode`


Visual representation of FindElementNode (Desktop).


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Find Element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Find Element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetElementPropertyNode

**Inherits from:** `VisualNode`


Visual representation of GetElementPropertyNode (Desktop).


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Get Element Property node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Get Element Property node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetElementTextNode

**Inherits from:** `VisualNode`


Visual representation of GetElementTextNode (Desktop).


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Get Element Text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Get Element Text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetMousePositionNode

**Inherits from:** `VisualNode`


Visual representation of GetMousePositionNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetWindowListNode

**Inherits from:** `VisualNode`


Visual representation of GetWindowListNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Get Window List node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Get Window List node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetWindowPropertiesNode

**Inherits from:** `VisualNode`


Visual representation of GetWindowPropertiesNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLaunchApplicationNode

**Inherits from:** `VisualNode`


Visual representation of LaunchApplicationNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Launch Application node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Launch Application node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMaximizeWindowNode

**Inherits from:** `VisualNode`


Visual representation of MaximizeWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMinimizeWindowNode

**Inherits from:** `VisualNode`


Visual representation of MinimizeWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMouseClickNode

**Inherits from:** `VisualNode`


Visual representation of MouseClickNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Mouse Click node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Mouse Click node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMoveMouseNode

**Inherits from:** `VisualNode`


Visual representation of MoveMouseNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Move Mouse node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Move Mouse node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMoveWindowNode

**Inherits from:** `VisualNode`


Visual representation of MoveWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Move Window node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Move Window node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualOCRExtractTextNode

**Inherits from:** `VisualNode`


Visual representation of OCRExtractTextNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize OCR Extract Text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize OCR Extract Text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualResizeWindowNode

**Inherits from:** `VisualNode`


Visual representation of ResizeWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Resize Window node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Resize Window node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRestoreWindowNode

**Inherits from:** `VisualNode`


Visual representation of RestoreWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualScrollElementNode

**Inherits from:** `VisualNode`


Visual representation of ScrollElementNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Scroll Element node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Scroll Element node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSelectFromDropdownNode

**Inherits from:** `VisualNode`


Visual representation of SelectFromDropdownNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Select From Dropdown node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Select From Dropdown node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSelectRadioButtonNode

**Inherits from:** `VisualNode`


Visual representation of SelectRadioButtonNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSelectTabNode

**Inherits from:** `VisualNode`


Visual representation of SelectTabNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Select Tab node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Select Tab node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSendHotKeyNode

**Inherits from:** `VisualNode`


Visual representation of SendHotKeyNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Send Hotkey node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Send Hotkey node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSendKeysNode

**Inherits from:** `VisualNode`


Visual representation of SendKeysNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Send Keys node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Send Keys node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSetWindowStateNode

**Inherits from:** `VisualNode`


Visual representation of SetWindowStateNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Set Window State node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Set Window State node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTypeTextDesktopNode

**Inherits from:** `VisualNode`


Visual representation of TypeTextNode (Desktop).


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Type Text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Type Text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualVerifyElementExistsNode

**Inherits from:** `VisualNode`


Visual representation of VerifyElementExistsNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Verify Element Exists node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Verify Element Exists node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualVerifyElementPropertyNode

**Inherits from:** `VisualNode`


Visual representation of VerifyElementPropertyNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Verify Element Property node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Verify Element Property node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWaitForWindowNode

**Inherits from:** `VisualNode`


Visual representation of WaitForWindowNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Wait For Window node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Wait For Window node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.document.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\document\nodes.py`


Visual nodes for Document AI category.

Provides visual node wrappers for document processing operations including:
- Document classification
- Invoice extraction
- Form extraction
- Table extraction
- Extraction validation


### Functions

#### `get_llm_credentials`

```python
def get_llm_credentials() -> List[Tuple[str, str]]
```

Get available LLM credentials for dropdown.

Returns:
    List of (id, display_name) tuples, with "Auto-detect" as first option.


### VisualClassifyDocumentNode

**Inherits from:** `VisualNode`


Visual representation of ClassifyDocumentNode.

Classify documents into categories (invoice, receipt, form, etc.)


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize classify document node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize classify document node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExtractFormNode

**Inherits from:** `VisualNode`


Visual representation of ExtractFormNode.

Extract fields from forms using a custom schema.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize extract form node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize extract form node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExtractInvoiceNode

**Inherits from:** `VisualNode`


Visual representation of ExtractInvoiceNode.

Extract vendor, amounts, dates, and line items from invoices.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize extract invoice node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize extract invoice node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExtractTableNode

**Inherits from:** `VisualNode`


Visual representation of ExtractTableNode.

Extract tabular data from documents.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize extract table node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize extract table node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualValidateExtractionNode

**Inherits from:** `VisualNode`


Visual representation of ValidateExtractionNode.

Validate extracted data and flag for human review.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize validate extraction node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize validate extraction node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.email.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\email\nodes.py`


Visual nodes for email category.


### VisualDeleteEmailNode

**Inherits from:** `VisualNode`


Visual representation of DeleteEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Delete Email node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Delete Email node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualFilterEmailsNode

**Inherits from:** `VisualNode`


Visual representation of FilterEmailsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Filter Emails node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Filter Emails node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualGetEmailContentNode

**Inherits from:** `VisualNode`


Visual representation of GetEmailContentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Get Email Content node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Get Email Content node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMarkEmailNode

**Inherits from:** `VisualNode`


Visual representation of MarkEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Mark Email node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Mark Email node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualMoveEmailNode

**Inherits from:** `VisualNode`


Visual representation of MoveEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Move Email node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Move Email node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualReadEmailsNode

**Inherits from:** `VisualNode`


Visual representation of ReadEmailsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Read Emails node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Read Emails node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSaveAttachmentNode

**Inherits from:** `VisualNode`


Visual representation of SaveAttachmentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Save Attachment node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Save Attachment node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSendEmailNode

**Inherits from:** `VisualNode`


Visual representation of SendEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Send Email node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Send Email node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\error_handling\nodes.py`


Visual nodes for error_handling category.


### VisualAssertNode

**Inherits from:** `VisualNode`


Visual representation of AssertNode.

Widgets are auto-generated from AssertNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualErrorRecoveryNode

**Inherits from:** `VisualNode`


Visual representation of ErrorRecoveryNode.

Widgets are auto-generated from ErrorRecoveryNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualLogErrorNode

**Inherits from:** `VisualNode`


Visual representation of LogErrorNode.

Widgets auto-generated from LogErrorNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | - | Return the CasareRPA node class for schema lookup. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `get_node_class`

```python
def get_node_class()
```

Return the CasareRPA node class for schema lookup.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualOnErrorNode

**Inherits from:** `VisualNode`


Visual representation of OnErrorNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRetryFailNode

**Inherits from:** `VisualNode`


Visual representation of RetryFailNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRetryNode

**Inherits from:** `VisualNode`


Visual representation of RetryNode.

Widgets are auto-generated from RetryNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualRetrySuccessNode

**Inherits from:** `VisualNode`


Visual representation of RetrySuccessNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualThrowErrorNode

**Inherits from:** `VisualNode`


Visual representation of ThrowErrorNode.

Widgets are auto-generated from ThrowErrorNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWebhookNotifyNode

**Inherits from:** `VisualNode`


Visual representation of WebhookNotifyNode.

Widgets are auto-generated from WebhookNotifyNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\file_operations\nodes.py`


Visual nodes for file_operations category.


### VisualAppendFileNode

**Inherits from:** `VisualNode`


Visual representation of AppendFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCopyFileNode

**Inherits from:** `VisualNode`


Visual representation of CopyFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDeleteFileNode

**Inherits from:** `VisualNode`


Visual representation of DeleteFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualExtractPDFPagesNode

**Inherits from:** `VisualNode`


Visual representation of ExtractPDFPagesNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPConnectNode

**Inherits from:** `VisualNode`


Visual representation of FTPConnectNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPDeleteNode

**Inherits from:** `VisualNode`


Visual representation of FTPDeleteNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPDisconnectNode

**Inherits from:** `VisualNode`


Visual representation of FTPDisconnectNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPDownloadNode

**Inherits from:** `VisualNode`


Visual representation of FTPDownloadNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPGetSizeNode

**Inherits from:** `VisualNode`


Visual representation of FTPGetSizeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPListNode

**Inherits from:** `VisualNode`


Visual representation of FTPListNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPMakeDirNode

**Inherits from:** `VisualNode`


Visual representation of FTPMakeDirNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPRemoveDirNode

**Inherits from:** `VisualNode`


Visual representation of FTPRemoveDirNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPRenameNode

**Inherits from:** `VisualNode`


Visual representation of FTPRenameNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFTPUploadNode

**Inherits from:** `VisualNode`


Visual representation of FTPUploadNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFileExistsNode

**Inherits from:** `VisualNode`


Visual representation of FileExistsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetFileInfoNode

**Inherits from:** `VisualNode`


Visual representation of GetFileInfoNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetFileSizeNode

**Inherits from:** `VisualNode`


Visual representation of GetFileSizeNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetPDFInfoNode

**Inherits from:** `VisualNode`


Visual representation of GetPDFInfoNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetXMLAttributeNode

**Inherits from:** `VisualNode`


Visual representation of GetXMLAttributeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetXMLElementNode

**Inherits from:** `VisualNode`


Visual representation of GetXMLElementNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualJsonToXMLNode

**Inherits from:** `VisualNode`


Visual representation of JsonToXMLNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualListFilesNode

**Inherits from:** `VisualNode`


Visual representation of ListFilesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualMergePDFsNode

**Inherits from:** `VisualNode`


Visual representation of MergePDFsNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualMoveFileNode

**Inherits from:** `VisualNode`


Visual representation of MoveFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualPDFToImagesNode

**Inherits from:** `VisualNode`


Visual representation of PDFToImagesNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualParseXMLNode

**Inherits from:** `VisualNode`


Visual representation of ParseXMLNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualReadCsvNode

**Inherits from:** `VisualNode`


Visual representation of ReadCSVNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualReadFileNode

**Inherits from:** `VisualNode`


Visual representation of ReadFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualReadJsonNode

**Inherits from:** `VisualNode`


Visual representation of ReadJSONFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualReadPDFTextNode

**Inherits from:** `VisualNode`


Visual representation of ReadPDFTextNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualReadXMLFileNode

**Inherits from:** `VisualNode`


Visual representation of ReadXMLFileNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSplitPDFNode

**Inherits from:** `VisualNode`


Visual representation of SplitPDFNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualUnzipFileNode

**Inherits from:** `VisualNode`


Visual representation of UnzipFilesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualWriteCsvNode

**Inherits from:** `VisualNode`


Visual representation of WriteCSVNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualWriteFileNode

**Inherits from:** `VisualNode`


Visual representation of WriteFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualWriteJsonNode

**Inherits from:** `VisualNode`


Visual representation of WriteJSONFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualWriteXMLFileNode

**Inherits from:** `VisualNode`


Visual representation of WriteXMLFileNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualXMLToJsonNode

**Inherits from:** `VisualNode`


Visual representation of XMLToJsonNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualXPathQueryNode

**Inherits from:** `VisualNode`


Visual representation of XPathQueryNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualZipFilesNode

**Inherits from:** `VisualNode`


Visual representation of ZipFilesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.google.calendar_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\calendar_nodes.py`


Visual nodes for Google Calendar operations.


### VisualCalendarCreateCalendarNode

**Inherits from:** `VisualNode`


Visual representation of CalendarCreateCalendarNode.

Creates a new secondary calendar.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarCreateEventNode

**Inherits from:** `VisualNode`


Visual representation of CalendarCreateEventNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarDeleteCalendarNode

**Inherits from:** `VisualNode`


Visual representation of CalendarDeleteCalendarNode.

Deletes a secondary calendar.
Cannot delete the primary calendar.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarDeleteEventNode

**Inherits from:** `VisualNode`


Visual representation of CalendarDeleteEventNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarGetCalendarNode

**Inherits from:** `VisualNode`


Visual representation of CalendarGetCalendarNode.

Gets metadata for a single calendar.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarGetEventNode

**Inherits from:** `VisualNode`


Visual representation of CalendarGetEventNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarGetFreeBusyNode

**Inherits from:** `VisualNode`


Visual representation of CalendarGetFreeBusyNode.

Returns free/busy information for a set of calendars.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarListCalendarsNode

**Inherits from:** `VisualNode`


Visual representation of CalendarListCalendarsNode.

Lists all calendars accessible by the user.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarListEventsNode

**Inherits from:** `VisualNode`


Visual representation of CalendarListEventsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarMoveEventNode

**Inherits from:** `VisualNode`


Visual representation of CalendarMoveEventNode.

Moves an event from one calendar to another.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarQuickAddNode

**Inherits from:** `VisualNode`


Visual representation of CalendarQuickAddNode.

Creates events using natural language text like:
- "Meeting at 3pm tomorrow"
- "Dinner with John on Friday at 7pm"


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualCalendarUpdateEventNode

**Inherits from:** `VisualNode`


Visual representation of CalendarUpdateEventNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.google.docs_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\docs_nodes.py`


Visual nodes for Google Docs operations.


### VisualDocsBatchUpdateNode

**Inherits from:** `VisualNode`


Visual representation of DocsBatchUpdateNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsCreateDocumentNode

**Inherits from:** `VisualNode`


Visual representation of DocsCreateDocumentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsDeleteContentNode

**Inherits from:** `VisualNode`


Visual representation of DocsDeleteContentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsGetContentNode

**Inherits from:** `VisualNode`


Visual representation of DocsGetTextNode (gets document content).


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsGetDocumentNode

**Inherits from:** `VisualNode`


Visual representation of DocsGetDocumentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsInsertImageNode

**Inherits from:** `VisualNode`


Visual representation of DocsInsertImageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsInsertTableNode

**Inherits from:** `VisualNode`


Visual representation of DocsInsertTableNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsInsertTextNode

**Inherits from:** `VisualNode`


Visual representation of DocsInsertTextNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsReplaceTextNode

**Inherits from:** `VisualNode`


Visual representation of DocsReplaceTextNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDocsUpdateStyleNode

**Inherits from:** `VisualNode`


Visual representation of DocsApplyStyleNode (updates text styling).


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\drive_nodes.py`


Visual nodes for Google Drive operations.


### VisualDriveBatchCopyNode

**Inherits from:** `VisualNode`


Visual representation of DriveBatchCopyNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveBatchDeleteNode

**Inherits from:** `VisualNode`


Visual representation of DriveBatchDeleteNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveBatchMoveNode

**Inherits from:** `VisualNode`


Visual representation of DriveBatchMoveNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveCopyFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveCopyFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveCreateFolderNode

**Inherits from:** `VisualNode`


Visual representation of DriveCreateFolderNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveDeleteFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveDeleteFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveDownloadFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveDownloadFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveExportFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveExportFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveGetFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveGetFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveGetPermissionsNode

**Inherits from:** `VisualNode`


Visual representation of DriveGetPermissionsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveListFilesNode

**Inherits from:** `VisualNode`


Visual representation of DriveListFilesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveMoveFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveMoveFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveRemovePermissionNode

**Inherits from:** `VisualNode`


Visual representation of DriveRemovePermissionNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveRenameFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveRenameFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveSearchFilesNode

**Inherits from:** `VisualNode`


Visual representation of DriveSearchFilesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveShareFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveShareFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDriveUploadFileNode

**Inherits from:** `VisualNode`


Visual representation of DriveUploadFileNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\gmail_nodes.py`


Visual nodes for Gmail operations.


### VisualGmailArchiveEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailArchiveEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailBatchDeleteNode

**Inherits from:** `VisualNode`


Visual representation of GmailBatchDeleteNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailBatchModifyNode

**Inherits from:** `VisualNode`


Visual representation of GmailBatchModifyNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailBatchSendNode

**Inherits from:** `VisualNode`


Visual representation of GmailBatchSendNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailCreateDraftNode

**Inherits from:** `VisualNode`


Visual representation of GmailCreateDraftNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailDeleteEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailDeleteEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailForwardEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailForwardEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailGetAttachmentNode

**Inherits from:** `VisualNode`


Visual representation of GmailGetAttachmentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailGetEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailGetEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailGetThreadNode

**Inherits from:** `VisualNode`


Visual representation of GmailGetThreadNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailListEmailsNode

**Inherits from:** `VisualNode`


Visual representation of GmailListEmailsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailMarkAsReadNode

**Inherits from:** `VisualNode`


Visual representation of GmailMarkAsReadNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailMarkAsUnreadNode

**Inherits from:** `VisualNode`


Visual representation of GmailMarkAsUnreadNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailModifyLabelsNode

**Inherits from:** `VisualNode`


Visual representation of GmailModifyLabelsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailMoveToTrashNode

**Inherits from:** `VisualNode`


Visual representation of GmailMoveToTrashNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailReplyToEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailReplyToEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailSearchEmailsNode

**Inherits from:** `VisualNode`


Visual representation of GmailSearchEmailsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailSendDraftNode

**Inherits from:** `VisualNode`


Visual representation of GmailSendDraftNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailSendEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailSendEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailSendWithAttachmentNode

**Inherits from:** `VisualNode`


Visual representation of GmailSendWithAttachmentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGmailStarEmailNode

**Inherits from:** `VisualNode`


Visual representation of GmailStarEmailNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\sheets_nodes.py`


Visual nodes for Google Sheets operations.


### VisualSheetsAddSheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsAddSheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsAppendRowNode

**Inherits from:** `VisualNode`


Visual representation of SheetsAppendRowNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsAutoResizeNode

**Inherits from:** `VisualNode`


Visual representation of SheetsAutoResizeNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsBatchClearNode

**Inherits from:** `VisualNode`


Visual representation of SheetsBatchClearNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsBatchGetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsBatchGetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsBatchUpdateNode

**Inherits from:** `VisualNode`


Visual representation of SheetsBatchUpdateNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsClearRangeNode

**Inherits from:** `VisualNode`


Visual representation of SheetsClearRangeNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsCreateSpreadsheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsCreateSpreadsheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsDeleteColumnNode

**Inherits from:** `VisualNode`


Visual representation of SheetsDeleteColumnNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsDeleteRowNode

**Inherits from:** `VisualNode`


Visual representation of SheetsDeleteRowNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsDeleteSheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsDeleteSheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsDuplicateSheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsDuplicateSheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsFormatCellsNode

**Inherits from:** `VisualNode`


Visual representation of SheetsFormatCellsNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsGetCellNode

**Inherits from:** `VisualNode`


Visual representation of SheetsGetCellNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsGetRangeNode

**Inherits from:** `VisualNode`


Visual representation of SheetsGetRangeNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsGetSpreadsheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsGetSpreadsheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsInsertColumnNode

**Inherits from:** `VisualNode`


Visual representation of SheetsInsertColumnNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsInsertRowNode

**Inherits from:** `VisualNode`


Visual representation of SheetsInsertRowNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsRenameSheetNode

**Inherits from:** `VisualNode`


Visual representation of SheetsRenameSheetNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsSetCellNode

**Inherits from:** `VisualNode`


Visual representation of SheetsSetCellNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualSheetsWriteRangeNode

**Inherits from:** `VisualNode`


Visual representation of SheetsWriteRangeNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.messaging.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\nodes.py`


Visual nodes for messaging category (Telegram, WhatsApp).


### VisualTelegramSendDocumentNode

**Inherits from:** `VisualNode`


Visual representation of TelegramSendDocumentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Send Document node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Send Document node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramSendLocationNode

**Inherits from:** `VisualNode`


Visual representation of TelegramSendLocationNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Send Location node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Send Location node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramSendMessageNode

**Inherits from:** `VisualNode`


Visual representation of TelegramSendMessageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Send Message node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Send Message node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramSendPhotoNode

**Inherits from:** `VisualNode`


Visual representation of TelegramSendPhotoNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Send Photo node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Send Photo node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\telegram_action_nodes.py`


Visual nodes for Telegram action nodes (edit, delete, media group, callback).


### VisualTelegramAnswerCallbackNode

**Inherits from:** `VisualNode`


Visual representation of TelegramAnswerCallbackNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Answer Callback node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Answer Callback node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramDeleteMessageNode

**Inherits from:** `VisualNode`


Visual representation of TelegramDeleteMessageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Delete Message node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Delete Message node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramEditMessageNode

**Inherits from:** `VisualNode`


Visual representation of TelegramEditMessageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Edit Message node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Edit Message node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramGetUpdatesNode

**Inherits from:** `VisualNode`


Visual representation of TelegramGetUpdatesNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Get Updates node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Get Updates node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualTelegramSendMediaGroupNode

**Inherits from:** `VisualNode`


Visual representation of TelegramSendMediaGroupNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Telegram Send Media Group node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Telegram Send Media Group node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\whatsapp_nodes.py`


Visual nodes for WhatsApp messaging.


### VisualWhatsAppSendDocumentNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendDocumentNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Document node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Document node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendImageNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendImageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Image node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Image node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendInteractiveNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendInteractiveNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Interactive node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Interactive node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendLocationNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendLocationNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Location node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Location node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendMessageNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendMessageNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Message node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Message node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendTemplateNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendTemplateNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Template node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Template node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWhatsAppSendVideoNode

**Inherits from:** `VisualNode`


Visual representation of WhatsAppSendVideoNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize WhatsApp Send Video node. |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize WhatsApp Send Video node.

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.office_automation.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\office_automation\nodes.py`


Visual nodes for office_automation category.


### VisualExcelCloseNode

**Inherits from:** `VisualNode`


Visual representation of ExcelCloseNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Excel Close node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Excel Close node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExcelGetRangeNode

**Inherits from:** `VisualNode`


Visual representation of ExcelGetRangeNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Excel Get Range node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Excel Get Range node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExcelOpenNode

**Inherits from:** `VisualNode`


Visual representation of ExcelOpenNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Excel Open node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Excel Open node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExcelReadCellNode

**Inherits from:** `VisualNode`


Visual representation of ExcelReadCellNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Excel Read Cell node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Excel Read Cell node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualExcelWriteCellNode

**Inherits from:** `VisualNode`


Visual representation of ExcelWriteCellNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Excel Write Cell node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Excel Write Cell node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualOutlookGetInboxCountNode

**Inherits from:** `VisualNode`


Visual representation of OutlookGetInboxCountNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Outlook Get Inbox Count node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Outlook Get Inbox Count node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualOutlookReadEmailsNode

**Inherits from:** `VisualNode`


Visual representation of OutlookReadEmailsNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Outlook Read Emails node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Outlook Read Emails node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualOutlookSendEmailNode

**Inherits from:** `VisualNode`


Visual representation of OutlookSendEmailNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Outlook Send Email node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Outlook Send Email node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWordCloseNode

**Inherits from:** `VisualNode`


Visual representation of WordCloseNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Word Close node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Word Close node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWordGetTextNode

**Inherits from:** `VisualNode`


Visual representation of WordGetTextNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWordOpenNode

**Inherits from:** `VisualNode`


Visual representation of WordOpenNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Word Open node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Word Open node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualWordReplaceTextNode

**Inherits from:** `VisualNode`


Visual representation of WordReplaceTextNode.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize Word Replace Text node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize Word Replace Text node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.rest_api.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\rest_api\nodes.py`


Visual nodes for rest_api category.


### VisualBuildUrlNode

**Inherits from:** `VisualNode`


Visual representation of BuildUrlNode.

Widgets are auto-generated from BuildUrlNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualHttpAuthNode

**Inherits from:** `VisualNode`


Visual representation of HttpAuthNode.

Widgets are auto-generated from HttpAuthNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualHttpDownloadFileNode

**Inherits from:** `VisualNode`


Visual representation of HttpDownloadFileNode.

Widgets are auto-generated from HttpDownloadFileNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualHttpRequestNode

**Inherits from:** `VisualNode`


Visual representation of HttpRequestNode.

Widgets are auto-generated from HttpRequestNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualHttpUploadFileNode

**Inherits from:** `VisualNode`


Visual representation of HttpUploadFileNode.

Widgets are auto-generated from HttpUploadFileNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualParseJsonResponseNode

**Inherits from:** `VisualNode`


Visual representation of ParseJsonResponseNode.

Widgets are auto-generated from ParseJsonResponseNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSetHttpHeadersNode

**Inherits from:** `VisualNode`


Visual representation of SetHttpHeadersNode.

Widgets are auto-generated from SetHttpHeadersNode's @node_schema decorator.


**Attributes:**

- `CASARE_NODE_MODULE: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.canvas.visual_nodes.scripts.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\scripts\nodes.py`


Visual nodes for scripts category.


### VisualEvalExpressionNode

**Inherits from:** `VisualNode`


Visual representation of EvalExpressionNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunBatchScriptNode

**Inherits from:** `VisualNode`


Visual representation of RunBatchScriptNode.

Widgets are auto-generated from RunBatchScriptNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunJavaScriptNode

**Inherits from:** `VisualNode`


Visual representation of RunJavaScriptNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunPythonFileNode

**Inherits from:** `VisualNode`


Visual representation of RunPythonFileNode.

Widgets are auto-generated from RunPythonFileNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunPythonScriptNode

**Inherits from:** `VisualNode`


Visual representation of RunPythonScriptNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.system.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\system\nodes.py`


Visual nodes for system category.


### VisualClipboardClearNode

**Inherits from:** `VisualNode`


Visual representation of ClipboardClearNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualClipboardCopyNode

**Inherits from:** `VisualNode`


Visual representation of ClipboardCopyNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualClipboardPasteNode

**Inherits from:** `VisualNode`


Visual representation of ClipboardPasteNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetServiceStatusNode

**Inherits from:** `VisualNode`


Visual representation of GetServiceStatusNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualInputDialogNode

**Inherits from:** `VisualNode`


Visual representation of InputDialogNode.

Widgets auto-generated from InputDialogNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualListServicesNode

**Inherits from:** `VisualNode`


Visual representation of ListServicesNode.

Widgets auto-generated from ListServicesNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualMessageBoxNode

**Inherits from:** `VisualNode`


Visual representation of MessageBoxNode.

Widgets auto-generated from MessageBoxNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRestartServiceNode

**Inherits from:** `VisualNode`


Visual representation of RestartServiceNode.

Widgets auto-generated from RestartServiceNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunCommandNode

**Inherits from:** `VisualNode`


Visual representation of RunCommandNode.

Widgets auto-generated from RunCommandNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRunPowerShellNode

**Inherits from:** `VisualNode`


Visual representation of RunPowerShellNode.

Widgets auto-generated from RunPowerShellNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualStartServiceNode

**Inherits from:** `VisualNode`


Visual representation of StartServiceNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualStopServiceNode

**Inherits from:** `VisualNode`


Visual representation of StopServiceNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTooltipNode

**Inherits from:** `VisualNode`


Visual representation of TooltipNode.

Widgets auto-generated from TooltipNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `get_node_class()` | `type` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `get_node_class`

```python
def get_node_class() -> type
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.triggers.base

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\triggers\base.py`


CasareRPA - Base Visual Trigger Node

Base class for all visual trigger nodes. Provides distinct styling
and behavior for trigger nodes on the canvas.


### VisualTriggerNode

**Inherits from:** `VisualNode`


Base class for visual trigger nodes.

Trigger nodes have distinct visual styling:
- Purple accent color (triggers are special entry points)
- No exec_in port (triggers start workflows)
- Listening badge when active


**Attributes:**

- `IS_TRIGGER: bool`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize visual trigger node. |
| `is_listening()` | `bool` | Check if this trigger is actively listening. |
| `set_listening(listening)` | `None` | Set the listening state and update visual appearance. |
| `setup_ports()` | `None` | Setup trigger node ports. |
| `update_status(status)` | `None` | Update node visual status. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize visual trigger node.

##### `is_listening`

```python
@property
def is_listening() -> bool
```

Check if this trigger is actively listening.

##### `set_listening`

```python
def set_listening(listening: bool) -> None
```

Set the listening state and update visual appearance.

Args:
    listening: True if trigger is actively listening

**Parameters:**

- `listening: bool` *(required)*

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup trigger node ports.

Trigger nodes have NO exec_in - they start workflows.
Override in subclasses to add specific data output ports.

##### `update_status`

```python
def update_status(status: str) -> None
```

Update node visual status.

Overrides base to maintain trigger-specific colors.

Args:
    status: Node status (idle, running, success, error, listening)

**Parameters:**

- `status: str` *(required)*

---

## casare_rpa.presentation.canvas.visual_nodes.triggers.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\triggers\nodes.py`


CasareRPA - Visual Trigger Nodes

All visual trigger node implementations for the canvas.


### VisualAppEventTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of AppEventTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualCalendarTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of CalendarTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualChatTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of ChatTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualDriveTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of DriveTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualEmailTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of EmailTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualErrorTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of ErrorTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualFileWatchTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of FileWatchTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualFormTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of FormTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualGmailTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of GmailTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualRSSFeedTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of RSSFeedTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualSSETriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of SSETriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualScheduleTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of ScheduleTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualSheetsTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of SheetsTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualTelegramTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of TelegramTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualWebhookTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of WebhookTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualWhatsAppTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of WhatsAppTriggerNode.


**Attributes:**

- `CASARE_NODE_CLASS: str`
- `NODE_CATEGORY: str`
- `NODE_NAME: str`

### VisualWorkflowCallTriggerNode

**Inherits from:** `VisualTriggerNode`


Visual representation of WorkflowCallTriggerNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

---

## casare_rpa.presentation.canvas.visual_nodes.utility.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\utility\nodes.py`


Visual nodes for utility category.


### VisualDateTimeAddNode

**Inherits from:** `VisualNode`


Visual representation of DateTimeAddNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDateTimeCompareNode

**Inherits from:** `VisualNode`


Visual representation of DateTimeCompareNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualDateTimeDiffNode

**Inherits from:** `VisualNode`


Visual representation of DateTimeDiffNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualFormatDateTimeNode

**Inherits from:** `VisualNode`


Visual representation of FormatDateTimeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetCurrentDateTimeNode

**Inherits from:** `VisualNode`


Visual representation of GetCurrentDateTimeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualGetTimestampNode

**Inherits from:** `VisualNode`


Visual representation of GetTimestampNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualParseDateTimeNode

**Inherits from:** `VisualNode`


Visual representation of ParseDateTimeNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRandomChoiceNode

**Inherits from:** `VisualNode`


Visual representation of RandomChoiceNode.

Widgets are auto-generated from RandomChoiceNode's @node_schema decorator.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRandomNumberNode

**Inherits from:** `VisualNode`


Visual representation of RandomNumberNode.

Widgets are auto-generated from RandomNumberNode's @node_schema decorator.
min_value/max_value are input ports, not schema properties.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRandomStringNode

**Inherits from:** `VisualNode`


Visual representation of RandomStringNode.

Widgets are auto-generated from RandomStringNode's @node_schema decorator.
length is an input port, not a schema property.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualRandomUUIDNode

**Inherits from:** `VisualNode`


Visual representation of RandomUUIDNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualShuffleListNode

**Inherits from:** `VisualNode`


Visual representation of ShuffleListNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextCaseNode

**Inherits from:** `VisualNode`


Visual representation of TextCaseNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextContainsNode

**Inherits from:** `VisualNode`


Visual representation of TextContainsNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextCountNode

**Inherits from:** `VisualNode`


Visual representation of TextCountNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextEndsWithNode

**Inherits from:** `VisualNode`


Visual representation of TextEndsWithNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextExtractNode

**Inherits from:** `VisualNode`


Visual representation of TextExtractNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextJoinNode

**Inherits from:** `VisualNode`


Visual representation of TextJoinNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextLinesNode

**Inherits from:** `VisualNode`


Visual representation of TextLinesNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextPadNode

**Inherits from:** `VisualNode`


Visual representation of TextPadNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextReplaceNode

**Inherits from:** `VisualNode`


Visual representation of TextReplaceNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextReverseNode

**Inherits from:** `VisualNode`


Visual representation of TextReverseNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextSplitNode

**Inherits from:** `VisualNode`


Visual representation of TextSplitNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextStartsWithNode

**Inherits from:** `VisualNode`


Visual representation of TextStartsWithNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextSubstringNode

**Inherits from:** `VisualNode`


Visual representation of TextSubstringNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `setup_ports()` | `None` |  |

#### Method Details

##### `setup_ports`

```python
def setup_ports() -> None
```

### VisualTextTrimNode

**Inherits from:** `VisualNode`


Visual representation of TextTrimNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `setup_ports()` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `setup_ports`

```python
def setup_ports() -> None
```

---

## casare_rpa.presentation.canvas.visual_nodes.variable.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\variable\nodes.py`


Visual nodes for variable category.


### VisualGetVariableNode

**Inherits from:** `VisualNode`


Visual representation of GetVariableNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize get variable node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize get variable node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualIncrementVariableNode

**Inherits from:** `VisualNode`


Visual representation of IncrementVariableNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize increment variable node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize increment variable node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

### VisualSetVariableNode

**Inherits from:** `VisualNode`


Visual representation of SetVariableNode.


**Attributes:**

- `NODE_CATEGORY: str`
- `NODE_NAME: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize set variable node. |
| `setup_ports()` | `None` | Setup ports. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize set variable node.

##### `setup_ports`

```python
def setup_ports() -> None
```

Setup ports.

---

## casare_rpa.presentation.setup.config_manager

**File:** `src\casare_rpa\presentation\setup\config_manager.py`


Client Configuration Manager.

Handles loading, saving, and validation of client configuration
for CasareRPA Robot + Designer installations.


### ClientConfig

**Decorators:** `@dataclass`


Complete client configuration.

Contains all settings for CasareRPA client installation including
orchestrator connection, robot settings, and logging preferences.


**Attributes:**

- `first_run_complete: bool`
- `logging: LoggingConfig`
- `orchestrator: OrchestratorConfig`
- `robot: RobotConfig`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'ClientConfig'` | Create configuration from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Convert configuration to dictionary for serialization. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'ClientConfig'
```

Create configuration from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert configuration to dictionary for serialization.

### ClientConfigManager


Manages client configuration file operations.

Handles:
- Loading configuration from file
- Saving configuration to file
- Configuration validation
- Default value generation


**Attributes:**

- `DEFAULT_CONFIG_DIR: Any`
- `DEFAULT_CONFIG_FILE: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(config_dir, config_file)` | `None` | Initialize configuration manager. |
| `config_exists()` | `bool` | Check if configuration file exists. |
| `create_default()` | `ClientConfig` | Create default configuration. |
| `ensure_directories()` | `None` | Create configuration directories if they don't exist. |
| `load()` | `ClientConfig` | Load configuration from file. |
| `needs_setup()` | `bool` | Check if first-run setup is needed. |
| `save(config)` | `None` | Save configuration to file. |
| `async test_connection(url, api_key)` | `tuple[bool, str]` | Test connection to orchestrator. |
| `validate_api_key(api_key)` | `Optional[str]` | Validate API key format. |
| `validate_robot_name(name)` | `Optional[str]` | Validate robot name. |
| `validate_url(url)` | `Optional[str]` | Validate orchestrator URL. |

#### Method Details

##### `__init__`

```python
def __init__(config_dir: Optional[Path] = None, config_file: Optional[str] = None) -> None
```

Initialize configuration manager.

Args:
    config_dir: Directory for configuration files
    config_file: Name of configuration file

**Parameters:**

- `config_dir: Optional[Path] = None`
- `config_file: Optional[str] = None`

##### `config_exists`

```python
def config_exists() -> bool
```

Check if configuration file exists.

##### `create_default`

```python
def create_default() -> ClientConfig
```

Create default configuration.

Returns:
    ClientConfig with default values

##### `ensure_directories`

```python
def ensure_directories() -> None
```

Create configuration directories if they don't exist.

##### `load`

```python
def load() -> ClientConfig
```

Load configuration from file.

Returns:
    ClientConfig instance

Raises:
    FileNotFoundError: If config file doesn't exist
    ValueError: If config file is invalid

##### `needs_setup`

```python
def needs_setup() -> bool
```

Check if first-run setup is needed.

Returns:
    True if setup wizard should be shown

##### `save`

```python
def save(config: ClientConfig) -> None
```

Save configuration to file.

Args:
    config: Configuration to save

**Parameters:**

- `config: ClientConfig` *(required)*

##### `test_connection`

```python
async def test_connection(url: str, api_key: Optional[str] = None) -> tuple[bool, str]
```

Test connection to orchestrator.

Args:
    url: Orchestrator WebSocket URL
    api_key: Optional API key for authentication

Returns:
    Tuple of (success, message)

**Parameters:**

- `url: str` *(required)*
- `api_key: Optional[str] = None`

##### `validate_api_key`

```python
def validate_api_key(api_key: str) -> Optional[str]
```

Validate API key format.

Args:
    api_key: API key to validate

Returns:
    Error message if invalid, None if valid

**Parameters:**

- `api_key: str` *(required)*

##### `validate_robot_name`

```python
def validate_robot_name(name: str) -> Optional[str]
```

Validate robot name.

Args:
    name: Robot name to validate

Returns:
    Error message if invalid, None if valid

**Parameters:**

- `name: str` *(required)*

##### `validate_url`

```python
def validate_url(url: str) -> Optional[str]
```

Validate orchestrator URL.

Args:
    url: URL to validate

Returns:
    Error message if invalid, None if valid

**Parameters:**

- `url: str` *(required)*

### LoggingConfig

**Decorators:** `@dataclass`


Configuration for logging.


**Attributes:**

- `directory: str`
- `level: str`
- `max_size_mb: int`
- `retention_days: int`

### OrchestratorConfig

**Decorators:** `@dataclass`


Configuration for orchestrator connection.


**Attributes:**

- `api_key: str`
- `max_reconnect_delay: float`
- `reconnect_delay: float`
- `url: str`
- `verify_ssl: bool`

### RobotConfig

**Decorators:** `@dataclass`


Configuration for robot agent.


**Attributes:**

- `capabilities: List[str]`
- `environment: str`
- `max_concurrent_jobs: int`
- `name: str`
- `tags: List[str]`

---

## casare_rpa.presentation.setup.setup_wizard

**File:** `src\casare_rpa\presentation\setup\setup_wizard.py`


Setup Wizard for CasareRPA Client.

First-run configuration wizard that guides users through:
1. Welcome and overview
2. Orchestrator connection setup
3. Robot configuration
4. Capability selection
5. Summary and completion

Triggered automatically when config file is missing or first_run_complete is False.


### Functions

#### `show_setup_wizard_if_needed`

```python
def show_setup_wizard_if_needed(parent = None) -> Optional[ClientConfig]
```

Show setup wizard if first-run configuration is needed.

Args:
    parent: Parent widget for the wizard

Returns:
    ClientConfig if setup completed, None if cancelled or not needed


### CapabilitiesPage

**Inherits from:** `QWizardPage`


Robot capabilities configuration page.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__(parent = None) -> None
```

**Parameters:**

- `parent = None`

### OrchestratorPage

**Inherits from:** `QWizardPage`


Orchestrator connection configuration page.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(config_manager, parent)` | `None` |  |
| `isComplete()` | `bool` | Check if page is complete. Allow empty URL for local-only mo... |

#### Method Details

##### `__init__`

```python
def __init__(config_manager: ClientConfigManager, parent = None) -> None
```

**Parameters:**

- `config_manager: ClientConfigManager` *(required)*
- `parent = None`

##### `isComplete`

```python
def isComplete() -> bool
```

Check if page is complete. Allow empty URL for local-only mode.

### RobotConfigPage

**Inherits from:** `QWizardPage`


Robot configuration page.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `isComplete()` | `bool` | Check if page is complete. |

#### Method Details

##### `__init__`

```python
def __init__(parent = None) -> None
```

**Parameters:**

- `parent = None`

##### `isComplete`

```python
def isComplete() -> bool
```

Check if page is complete.

### SetupWizard

**Inherits from:** `QWizard`


First-run setup wizard for CasareRPA client.

Guides users through initial configuration of orchestrator connection
and robot settings. Saves configuration to APPDATA/CasareRPA/config.yaml.

Signals:
    setup_complete: Emitted when setup finishes successfully (config: ClientConfig)
    setup_cancelled: Emitted when user cancels setup


**Attributes:**

- `PAGE_CAPABILITIES: int`
- `PAGE_ORCHESTRATOR: int`
- `PAGE_ROBOT: int`
- `PAGE_SUMMARY: int`
- `PAGE_WELCOME: int`
- `setup_cancelled: Signal`
- `setup_complete: Signal`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(config_manager, parent)` | `None` | Initialize setup wizard. |
| `accept()` | `None` | Handle wizard completion. |
| `reject()` | `None` | Handle wizard cancellation. |

#### Method Details

##### `__init__`

```python
def __init__(config_manager: Optional[ClientConfigManager] = None, parent = None) -> None
```

Initialize setup wizard.

Args:
    config_manager: Configuration manager instance
    parent: Parent widget

**Parameters:**

- `config_manager: Optional[ClientConfigManager] = None`
- `parent = None`

##### `accept`

```python
def accept() -> None
```

Handle wizard completion.

##### `reject`

```python
def reject() -> None
```

Handle wizard cancellation.

### SummaryPage

**Inherits from:** `QWizardPage`


Summary page showing configuration overview.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |
| `initializePage()` | `None` | Initialize page when shown. |

#### Method Details

##### `__init__`

```python
def __init__(parent = None) -> None
```

**Parameters:**

- `parent = None`

##### `initializePage`

```python
def initializePage() -> None
```

Initialize page when shown.

### WelcomePage

**Inherits from:** `QWizardPage`


Welcome page with overview of setup process.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(parent)` | `None` |  |

#### Method Details

##### `__init__`

```python
def __init__(parent = None) -> None
```

**Parameters:**

- `parent = None`

---
