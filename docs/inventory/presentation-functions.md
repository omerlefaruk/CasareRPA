# Presentation Layer Functions

**Total:** 3253 functions

## casare_rpa.presentation

**File:** `src\casare_rpa\presentation\__init__.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_config_manager` | - | `` | `-` | UNUSED |
| `get_setup_wizard` | - | `` | `-` | UNUSED |
| `show_setup_if_needed` | - | `parent` | `-` | UNUSED |


## casare_rpa.presentation.canvas.app

**File:** `src\casare_rpa\presentation\canvas\app.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `main` | - | `` | `int` | USED |
| `__init__` | CasareRPAApp | `self` | `None` | DUNDER |
| `_connect_components` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_connect_ui_signals` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_create_ui` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_get_all_controllers` | CasareRPAApp | `self` | `list` | INTERNAL |
| `_initialize_components` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_debug_continue` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_debug_mode_toggled` | CasareRPAApp | `self, enabled: bool` | `None` | INTERNAL |
| `_on_debug_step` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_delete_selected` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_duplicate_nodes` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_save_as_scenario` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_scenario_opened` | CasareRPAApp | `self, project_path: str, scenario_path: str` | `None` | INTERNAL |
| `_on_step_mode_toggled` | CasareRPAApp | `self, enabled: bool` | `None` | INTERNAL |
| `_on_workflow_load` | CasareRPAApp | `self, file_path: str` | `None` | INTERNAL |
| `_on_workflow_new` | CasareRPAApp | `self` | `None` | INTERNAL |
| `_on_workflow_save` | CasareRPAApp | `self, file_path: str` | `None` | INTERNAL |
| `_setup_qt_application` | CasareRPAApp | `self` | `None` | INTERNAL |
| `cleanup` | CasareRPAApp | `self` | `None` | USED |
| `get_autosave_controller` | CasareRPAApp | `self` | `AutosaveController` | UNUSED |
| `get_execution_controller` | CasareRPAApp | `self` | `ExecutionController` | UNUSED |
| `get_node_controller` | CasareRPAApp | `self` | `NodeController` | USED |
| `get_preferences_controller` | CasareRPAApp | `self` | `PreferencesController` | UNUSED |
| `get_selector_controller` | CasareRPAApp | `self` | `SelectorController` | UNUSED |
| `get_workflow_controller` | CasareRPAApp | `self` | `WorkflowController` | UNUSED |
| `run` | CasareRPAApp | `self` | `int` | USED |
| `async run_async` | CasareRPAApp | `self` | `int` | UNUSED |


## casare_rpa.presentation.canvas.component_factory

**File:** `src\casare_rpa\presentation\canvas\component_factory.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `clear` | ComponentFactory | `cls` | `None` | USED |
| `get` | ComponentFactory | `cls, component_name: str` | `Optional[QWidget]` | USED |
| `get_cached_count` | ComponentFactory | `cls` | `int` | UNUSED |
| `get_or_create` | ComponentFactory | `cls, component_name: str, factory: Callable[[], T]` | `T` | USED |
| `get_stats` | ComponentFactory | `cls` | `Dict[str, float]` | USED |
| `has` | ComponentFactory | `cls, component_name: str` | `bool` | UNUSED |
| `remove` | ComponentFactory | `cls, component_name: str` | `Optional[QWidget]` | USED |


## casare_rpa.presentation.canvas.components.action_manager

**File:** `src\casare_rpa\presentation\canvas\components\action_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ActionManager | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_create_action` | ActionManager | `self, name: str, text: str, ...` | `QAction` | INTERNAL |
| `_load_hotkeys` | ActionManager | `self` | `None` | INTERNAL |
| `create_actions` | ActionManager | `self` | `None` | USED |
| `get_action` | ActionManager | `self, name: str` | `Optional[QAction]` | USED |
| `get_all_actions` | ActionManager | `self` | `Dict[str, QAction]` | USED |


## casare_rpa.presentation.canvas.components.dock_creator

**File:** `src\casare_rpa\presentation\canvas\components\dock_creator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DockCreator | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_find_view_menu` | DockCreator | `self` | `-` | INTERNAL |
| `_update_analytics_url` | DockCreator | `self, analytics_panel: 'AnalyticsPanel', connected: bool` | `None` | INTERNAL |
| `create_analytics_panel` | DockCreator | `self` | `'AnalyticsPanel'` | USED |
| `create_bottom_panel` | DockCreator | `self` | `'BottomPanelDock'` | USED |
| `create_debug_panel` | DockCreator | `self, debug_controller: Optional['DebugController']` | `'DebugPanel'` | USED |
| `create_execution_timeline_dock` | DockCreator | `self` | `tuple[QDockWidget, 'ExecutionTimeline']` | USED |
| `create_process_mining_panel` | DockCreator | `self` | `'ProcessMiningPanel'` | USED |
| `create_properties_panel` | DockCreator | `self` | `'PropertiesPanel'` | USED |
| `create_robot_picker_panel` | DockCreator | `self, robot_controller: Optional['RobotController']` | `'RobotPickerPanel'` | USED |
| `create_variable_inspector_dock` | DockCreator | `self` | `'VariableInspectorDock'` | USED |


## casare_rpa.presentation.canvas.components.fleet_dashboard_manager

**File:** `src\casare_rpa\presentation\canvas\components\fleet_dashboard_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FleetDashboardManager | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `async _cancel_job` | FleetDashboardManager | `self, job_id: str` | `None` | INTERNAL |
| `_check_connection_and_refresh` | FleetDashboardManager | `self` | `None` | INTERNAL |
| `async _delete_robot` | FleetDashboardManager | `self, robot_id: str` | `None` | INTERNAL |
| `async _delete_schedule` | FleetDashboardManager | `self, schedule_id: str` | `None` | INTERNAL |
| `async _get_analytics` | FleetDashboardManager | `self, robots: List[Any], jobs: List[Dict[str, Any]]` | `Dict[str, Any]` | INTERNAL |
| `async _get_jobs` | FleetDashboardManager | `self` | `List[Dict[str, Any]]` | INTERNAL |
| `async _get_robots` | FleetDashboardManager | `self` | `List[Any]` | INTERNAL |
| `async _get_schedules` | FleetDashboardManager | `self` | `List[Dict[str, Any]]` | INTERNAL |
| `_on_job_cancelled` | FleetDashboardManager | `self, job_id: str` | `None` | INTERNAL |
| `_on_job_retried` | FleetDashboardManager | `self, job_id: str` | `None` | INTERNAL |
| `_on_refresh_requested` | FleetDashboardManager | `self` | `None` | INTERNAL |
| `_on_robot_deleted` | FleetDashboardManager | `self, robot_id: str` | `None` | INTERNAL |
| `_on_robot_edited` | FleetDashboardManager | `self, robot_id: str, robot_data: dict` | `None` | INTERNAL |
| `_on_schedule_deleted` | FleetDashboardManager | `self, schedule_id: str` | `None` | INTERNAL |
| `_on_schedule_edited` | FleetDashboardManager | `self, schedule_id: str` | `None` | INTERNAL |
| `_on_schedule_run_now` | FleetDashboardManager | `self, schedule_id: str` | `None` | INTERNAL |
| `_on_schedule_toggled` | FleetDashboardManager | `self, schedule_id: str, enabled: bool` | `None` | INTERNAL |
| `async _refresh_all_data` | FleetDashboardManager | `self` | `None` | INTERNAL |
| `async _retry_job` | FleetDashboardManager | `self, job_id: str` | `None` | INTERNAL |
| `_robot_controller` | FleetDashboardManager | `self` | `Optional['RobotController']` | INTERNAL |
| `async _run_schedule_now` | FleetDashboardManager | `self, schedule_id: str` | `None` | INTERNAL |
| `_scheduling_controller` | FleetDashboardManager | `self` | `Optional['SchedulingController']` | INTERNAL |
| `async _toggle_schedule` | FleetDashboardManager | `self, schedule_id: str, enabled: bool` | `None` | INTERNAL |
| `async _update_robot` | FleetDashboardManager | `self, robot_id: str, robot_data: dict` | `None` | INTERNAL |
| `async connect_and_refresh` | FleetDashboardManager | `` | `-` | USED |
| `dialog` | FleetDashboardManager | `self` | `Optional['FleetDashboardDialog']` | UNUSED |
| `open_dashboard` | FleetDashboardManager | `self` | `None` | USED |


## casare_rpa.presentation.canvas.components.menu_builder

**File:** `src\casare_rpa\presentation\canvas\components\menu_builder.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MenuBuilder | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_create_automation_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `_create_edit_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `_create_file_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `_create_help_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `_create_run_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `_create_view_menu` | MenuBuilder | `self, menubar, mw: 'MainWindow'` | `QMenu` | INTERNAL |
| `create_menus` | MenuBuilder | `self` | `None` | USED |


## casare_rpa.presentation.canvas.components.status_bar_manager

**File:** `src\casare_rpa\presentation\canvas\components\status_bar_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | StatusBarManager | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_add_separator` | StatusBarManager | `self, status_bar: QStatusBar` | `None` | INTERNAL |
| `_create_toggle_button` | StatusBarManager | `self, text: str, tooltip: str, ...` | `QPushButton` | INTERNAL |
| `_toggle_panel_tab` | StatusBarManager | `self, tab_name: str` | `None` | INTERNAL |
| `create_status_bar` | StatusBarManager | `self` | `QStatusBar` | USED |
| `set_execution_status` | StatusBarManager | `self, status: str` | `None` | USED |
| `update_button_states` | StatusBarManager | `self` | `None` | USED |
| `update_node_count` | StatusBarManager | `self, count: int` | `None` | USED |
| `update_zoom_display` | StatusBarManager | `self, zoom_percent: float` | `None` | USED |


## casare_rpa.presentation.canvas.components.toolbar_builder

**File:** `src\casare_rpa\presentation\canvas\components\toolbar_builder.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ToolbarBuilder | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `create_toolbar` | ToolbarBuilder | `self` | `QToolBar` | USED |


## casare_rpa.presentation.canvas.connections.auto_connect

**File:** `src\casare_rpa\presentation\canvas\connections\auto_connect.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AutoConnectManager | `self, graph: NodeGraph, parent: Optional[QObject]` | `-` | DUNDER |
| `_apply_suggested_connections` | AutoConnectManager | `self` | `-` | INTERNAL |
| `_are_nodes_connected` | AutoConnectManager | `self, from_node: BaseNode, to_node: BaseNode` | `bool` | INTERNAL |
| `_are_ports_compatible` | AutoConnectManager | `self, port1, port2` | `bool` | INTERNAL |
| `_calculate_distance` | AutoConnectManager | `self, pos1: QPointF, pos2: QPointF` | `float` | INTERNAL |
| `_clear_suggestions` | AutoConnectManager | `self` | `-` | INTERNAL |
| `_disable_context_menu` | AutoConnectManager | `self` | `-` | INTERNAL |
| `_disconnect_node` | AutoConnectManager | `self, node: BaseNode` | `-` | INTERNAL |
| `_draw_suggestion_lines` | AutoConnectManager | `self, suggestions: List[Tuple[BaseNode, str, BaseNode, str]]` | `-` | INTERNAL |
| `_find_closest_connections` | AutoConnectManager | `self, node: BaseNode, other_nodes: List[BaseNode]` | `List[Tuple[BaseNode, str, BaseNode, str]]` | INTERNAL |
| `_get_node_at_position` | AutoConnectManager | `self, pos` | `Optional[BaseNode]` | INTERNAL |
| `_get_node_center` | AutoConnectManager | `self, node: BaseNode` | `Optional[QPointF]` | INTERNAL |
| `_get_port_scene_pos` | AutoConnectManager | `self, node: BaseNode, port_name: str, ...` | `Optional[QPointF]` | INTERNAL |
| `_on_nodes_deleted` | AutoConnectManager | `self, node_ids` | `-` | INTERNAL |
| `_restore_context_menu` | AutoConnectManager | `self` | `-` | INTERNAL |
| `_setup_event_filters` | AutoConnectManager | `self` | `-` | INTERNAL |
| `_update_suggestions` | AutoConnectManager | `self` | `-` | INTERNAL |
| `eventFilter` | AutoConnectManager | `self, watched, event` | `-` | USED |
| `get_max_distance` | AutoConnectManager | `self` | `float` | UNUSED |
| `is_active` | AutoConnectManager | `self` | `bool` | USED |
| `reset_drag_state` | AutoConnectManager | `self` | `-` | UNUSED |
| `set_active` | AutoConnectManager | `self, active: bool` | `-` | USED |
| `set_max_distance` | AutoConnectManager | `self, distance: float` | `-` | USED |


## casare_rpa.presentation.canvas.connections.connection_cutter

**File:** `src\casare_rpa\presentation\canvas\connections\connection_cutter.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ConnectionCutter | `self, graph: NodeGraph, parent: Optional[QObject]` | `-` | DUNDER |
| `_cancel_cut` | ConnectionCutter | `self` | `-` | INTERNAL |
| `_create_cut_visual` | ConnectionCutter | `self, start_pos: QPointF` | `-` | INTERNAL |
| `_cut_intersecting_connections` | ConnectionCutter | `self` | `int` | INTERNAL |
| `_cut_via_node_iteration` | ConnectionCutter | `self, cut_segments: List[QLineF]` | `int` | INTERNAL |
| `_finish_cut` | ConnectionCutter | `self` | `-` | INTERNAL |
| `_get_port_position` | ConnectionCutter | `self, port` | `Optional[QPointF]` | INTERNAL |
| `_item_intersects_cut` | ConnectionCutter | `self, item: QGraphicsItem, cut_segments: List[QLineF]` | `bool` | INTERNAL |
| `_line_intersects_rect` | ConnectionCutter | `self, line: QLineF, rect: QRectF` | `bool` | INTERNAL |
| `_remove_cut_visual` | ConnectionCutter | `self` | `-` | INTERNAL |
| `_set_cut_cursor` | ConnectionCutter | `self, cutting: bool` | `-` | INTERNAL |
| `_setup_event_filters` | ConnectionCutter | `self` | `-` | INTERNAL |
| `_start_cut` | ConnectionCutter | `self, pos` | `-` | INTERNAL |
| `_update_cut` | ConnectionCutter | `self, pos` | `-` | INTERNAL |
| `_update_cut_visual` | ConnectionCutter | `self, current_pos: QPointF` | `-` | INTERNAL |
| `eventFilter` | ConnectionCutter | `self, watched, event` | `-` | USED |
| `is_active` | ConnectionCutter | `self` | `bool` | USED |
| `set_active` | ConnectionCutter | `self, active: bool` | `-` | USED |


## casare_rpa.presentation.canvas.connections.connection_validator

**File:** `src\casare_rpa\presentation\canvas\connections\connection_validator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_connection_validator` | - | `` | `ConnectionValidator` | USED |
| `validate_connection` | - | `source_node: 'VisualNode', source_port: str, target_node: 'VisualNode', ...` | `ConnectionValidation` | USED |
| `invalid` | ConnectionValidation | `cls, result: ValidationResult, message: str, ...` | `'ConnectionValidation'` | USED |
| `valid` | ConnectionValidation | `cls, message: str, source_type: Optional[DataType], ...` | `'ConnectionValidation'` | USED |
| `__init__` | ConnectionValidator | `self` | `None` | DUNDER |
| `_get_port_type` | ConnectionValidator | `self, node: 'VisualNode', port_name: str` | `Optional[DataType]` | INTERNAL |
| `_is_exec_port` | ConnectionValidator | `self, port_name: str, data_type: Optional[DataType]` | `bool` | INTERNAL |
| `get_compatible_ports` | ConnectionValidator | `self, source_node: 'VisualNode', source_port_name: str, ...` | `List[str]` | UNUSED |
| `get_incompatible_ports` | ConnectionValidator | `self, source_node: 'VisualNode', source_port_name: str, ...` | `List[str]` | UNUSED |
| `validate_connection` | ConnectionValidator | `self, source_node: 'VisualNode', source_port_name: str, ...` | `ConnectionValidation` | USED |


## casare_rpa.presentation.canvas.connections.node_insert

**File:** `src\casare_rpa\presentation\canvas\connections\node_insert.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_name` | - | `obj` | `str` | INTERNAL |
| `__init__` | NodeInsertManager | `self, graph: NodeGraph, parent: Optional[QObject]` | `-` | DUNDER |
| `_auto_space_nodes` | NodeInsertManager | `self, source_node: BaseNode, new_node: BaseNode, ...` | `-` | INTERNAL |
| `_calculate_distance` | NodeInsertManager | `self, p1, p2` | `float` | INTERNAL |
| `_check_drag_state` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_clear_highlight` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_do_visual_update` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_find_closest_intersecting_exec_pipe` | NodeInsertManager | `self, node_rect: QRectF` | `Tuple[Optional[object], float]` | INTERNAL |
| `_find_exec_ports` | NodeInsertManager | `self, node: BaseNode` | `Tuple[Optional[object], Optional[object]]` | INTERNAL |
| `_force_visual_update` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_get_node_scene_rect` | NodeInsertManager | `self, node: BaseNode` | `Optional[QRectF]` | INTERNAL |
| `_insert_node_on_pipe` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_is_exec_pipe` | NodeInsertManager | `self, pipe` | `bool` | INTERNAL |
| `_node_intersects_pipe` | NodeInsertManager | `self, node_rect: QRectF, pipe` | `bool` | INTERNAL |
| `_setup_event_filters` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_update_highlight` | NodeInsertManager | `self` | `-` | INTERNAL |
| `_verify_pipe_visuals` | NodeInsertManager | `self` | `-` | INTERNAL |
| `debug_find_pipes` | NodeInsertManager | `self` | `-` | UNUSED |
| `eventFilter` | NodeInsertManager | `self, watched, event` | `-` | USED |
| `is_active` | NodeInsertManager | `self` | `bool` | USED |
| `set_active` | NodeInsertManager | `self, active: bool` | `-` | USED |


## casare_rpa.presentation.canvas.controllers.autosave_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\autosave_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AutosaveController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_handle_autosave_failure` | AutosaveController | `self, error_message: str` | `None` | INTERNAL |
| `_on_autosave_timer` | AutosaveController | `self` | `None` | INTERNAL |
| `_on_preferences_updated` | AutosaveController | `self, event: Event` | `None` | INTERNAL |
| `_on_workflow_closed` | AutosaveController | `self, event: Event` | `None` | INTERNAL |
| `_on_workflow_opened` | AutosaveController | `self, event: Event` | `None` | INTERNAL |
| `_on_workflow_saved` | AutosaveController | `self, event: Event` | `None` | INTERNAL |
| `_perform_autosave` | AutosaveController | `self` | `None` | INTERNAL |
| `_update_timer_from_settings` | AutosaveController | `self` | `None` | INTERNAL |
| `cleanup` | AutosaveController | `self` | `None` | USED |
| `disable_autosave` | AutosaveController | `self` | `None` | USED |
| `enable_autosave` | AutosaveController | `self, interval_minutes: int` | `None` | USED |
| `initialize` | AutosaveController | `self` | `None` | USED |
| `is_enabled` | AutosaveController | `self` | `bool` | USED |
| `trigger_autosave_now` | AutosaveController | `self` | `None` | UNUSED |
| `update_interval` | AutosaveController | `self, interval_minutes: int` | `None` | UNUSED |


## casare_rpa.presentation.canvas.controllers.base_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\base_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BaseController | `self, main_window: 'MainWindow', parent: Optional[QObject]` | `-` | DUNDER |
| `cleanup` | BaseController | `self` | `None` | USED |
| `initialize` | BaseController | `self` | `None` | USED |
| `is_initialized` | BaseController | `self` | `bool` | UNUSED |


## casare_rpa.presentation.canvas.controllers.connection_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\connection_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ConnectionController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_get_graph` | ConnectionController | `self` | `-` | INTERNAL |
| `auto_connect_enabled` | ConnectionController | `self` | `bool` | UNUSED |
| `cleanup` | ConnectionController | `self` | `None` | USED |
| `create_connection` | ConnectionController | `self, source_node_id: str, source_port: str, ...` | `bool` | UNUSED |
| `delete_connection` | ConnectionController | `self, source_node_id: str, target_node_id: str` | `None` | UNUSED |
| `initialize` | ConnectionController | `self` | `None` | USED |
| `toggle_auto_connect` | ConnectionController | `self, enabled: bool` | `None` | UNUSED |
| `validate_connection` | ConnectionController | `self, source_node_id: str, source_port: str, ...` | `Tuple[bool, Optional[str]]` | USED |


## casare_rpa.presentation.canvas.controllers.event_bus_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\event_bus_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | EventBusController | `self, main_window` | `-` | DUNDER |
| `_add_to_history` | EventBusController | `self, event: Event` | `None` | INTERNAL |
| `cleanup` | EventBusController | `self` | `None` | USED |
| `clear_event_history` | EventBusController | `self` | `None` | UNUSED |
| `disable_event_filtering` | EventBusController | `self` | `None` | UNUSED |
| `dispatch` | EventBusController | `self, event_type: str, source: str, ...` | `None` | UNUSED |
| `enable_event_filtering` | EventBusController | `self, event_types: List[str]` | `None` | UNUSED |
| `get_event_history` | EventBusController | `self, count: Optional[int]` | `List[Event]` | UNUSED |
| `get_event_types` | EventBusController | `self` | `List[str]` | UNUSED |
| `get_subscriber_count` | EventBusController | `self, event_type: Optional[str]` | `int` | UNUSED |
| `initialize` | EventBusController | `self` | `None` | USED |
| `subscribe` | EventBusController | `self, event_type: str, callback: Callable[[Event], None]` | `None` | USED |
| `unsubscribe` | EventBusController | `self, event_type: str, callback: Callable[[Event], None]` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.example_workflow_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\example_workflow_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExampleWorkflowController | `self` | `-` | DUNDER |
| `_on_connection_added` | ExampleWorkflowController | `self, event: Event` | `None` | INTERNAL |
| `_on_connection_removed` | ExampleWorkflowController | `self, event: Event` | `None` | INTERNAL |
| `_on_node_added` | ExampleWorkflowController | `self, event: Event` | `None` | INTERNAL |
| `_on_node_property_changed` | ExampleWorkflowController | `self, event: Event` | `None` | INTERNAL |
| `_on_node_removed` | ExampleWorkflowController | `self, event: Event` | `None` | INTERNAL |
| `cleanup` | ExampleWorkflowController | `self` | `None` | USED |
| `async close_workflow` | ExampleWorkflowController | `self` | `None` | UNUSED |
| `current_file` | ExampleWorkflowController | `self` | `Optional[Path]` | UNUSED |
| `is_modified` | ExampleWorkflowController | `self` | `bool` | UNUSED |
| `mark_modified` | ExampleWorkflowController | `self` | `None` | USED |
| `async new_workflow` | ExampleWorkflowController | `self, name: str` | `None` | USED |
| `async open_workflow` | ExampleWorkflowController | `self, file_path: Path` | `None` | USED |
| `async save_workflow` | ExampleWorkflowController | `self, file_path: Optional[Path]` | `None` | USED |
| `workflow_name` | ExampleWorkflowController | `self` | `Optional[str]` | UNUSED |


## casare_rpa.presentation.canvas.controllers.execution_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\execution_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_build_node_index` | ExecutionController | `self` | `None` | INTERNAL |
| `_check_validation_before_run` | ExecutionController | `self` | `bool` | INTERNAL |
| `_find_visual_node` | ExecutionController | `self, node_id: str` | `-` | INTERNAL |
| `_has_trigger_node` | ExecutionController | `self` | `bool` | INTERNAL |
| `_on_browser_page_ready` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_node_completed` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_node_error` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_node_started` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_workflow_completed` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_workflow_error` | ExecutionController | `self, event` | `None` | INTERNAL |
| `_on_workflow_stopped` | ExecutionController | `self, event` | `None` | INTERNAL |
| `async _pause_workflow_async` | ExecutionController | `self` | `None` | INTERNAL |
| `_reset_all_node_visuals` | ExecutionController | `self` | `None` | INTERNAL |
| `async _resume_workflow_async` | ExecutionController | `self` | `None` | INTERNAL |
| `async _run_workflow_async` | ExecutionController | `self` | `None` | INTERNAL |
| `_setup_event_bus` | ExecutionController | `self` | `None` | INTERNAL |
| `_setup_log_tab_bridge` | ExecutionController | `self` | `None` | INTERNAL |
| `_setup_terminal_bridge` | ExecutionController | `self` | `None` | INTERNAL |
| `async _start_listening_async` | ExecutionController | `self` | `None` | INTERNAL |
| `async _stop_listening_async` | ExecutionController | `self` | `None` | INTERNAL |
| `async _stop_workflow_async` | ExecutionController | `self` | `None` | INTERNAL |
| `_update_execution_actions` | ExecutionController | `self, running: bool` | `None` | INTERNAL |
| `_update_trigger_node_visual` | ExecutionController | `self, listening: bool` | `None` | INTERNAL |
| `cleanup` | ExecutionController | `self` | `None` | USED |
| `async cleanup_async` | ExecutionController | `self` | `None` | UNUSED |
| `enable_browser_actions` | ExecutionController | `` | `-` | UNUSED |
| `initialize` | ExecutionController | `self` | `None` | USED |
| `is_listening` | ExecutionController | `self` | `bool` | UNUSED |
| `is_paused` | ExecutionController | `self` | `bool` | UNUSED |
| `is_running` | ExecutionController | `self` | `bool` | USED |
| `log_callback` | ExecutionController | `level: str, message: str, module: str, ...` | `None` | UNUSED |
| `on_execution_completed` | ExecutionController | `self` | `None` | USED |
| `on_execution_error` | ExecutionController | `self, error_message: str` | `None` | USED |
| `on_log_received` | ExecutionController | `level: str, message: str, module: str, ...` | `None` | UNUSED |
| `on_stderr_received` | ExecutionController | `text: str` | `None` | UNUSED |
| `on_stdout_received` | ExecutionController | `text: str` | `None` | UNUSED |
| `pause_workflow` | ExecutionController | `self` | `None` | USED |
| `resume_workflow` | ExecutionController | `self` | `None` | USED |
| `run_all_workflows` | ExecutionController | `self` | `None` | USED |
| `run_single_node` | ExecutionController | `self` | `None` | USED |
| `run_to_node` | ExecutionController | `self` | `None` | USED |
| `run_workflow` | ExecutionController | `self` | `None` | USED |
| `set_workflow_runner` | ExecutionController | `self, runner: 'CanvasWorkflowRunner'` | `None` | USED |
| `start_trigger_listening` | ExecutionController | `self` | `None` | USED |
| `stderr_callback` | ExecutionController | `text: str` | `None` | UNUSED |
| `stdout_callback` | ExecutionController | `text: str` | `None` | UNUSED |
| `stop_trigger_listening` | ExecutionController | `self` | `None` | USED |
| `stop_workflow` | ExecutionController | `self` | `None` | USED |
| `toggle_pause` | ExecutionController | `self, checked: bool` | `None` | USED |
| `toggle_trigger_listening` | ExecutionController | `self` | `None` | UNUSED |
| `__init__` | _ThreadSafeLogBridge | `self, parent: Optional[QObject]` | `-` | DUNDER |
| `emit_log` | _ThreadSafeLogBridge | `self, level: str, message: str, ...` | `None` | USED |
| `__init__` | _ThreadSafeTerminalBridge | `self, parent: Optional[QObject]` | `-` | DUNDER |
| `emit_stderr` | _ThreadSafeTerminalBridge | `self, text: str` | `None` | USED |
| `emit_stdout` | _ThreadSafeTerminalBridge | `self, text: str` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.menu_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\menu_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MenuController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_collect_actions` | MenuController | `self` | `None` | INTERNAL |
| `_get_all_preferences` | MenuController | `self, settings_manager` | `dict` | INTERNAL |
| `_on_open_recent_file` | MenuController | `self, file_path: str` | `None` | INTERNAL |
| `_reload_hotkeys` | MenuController | `self` | `None` | INTERNAL |
| `_save_preferences` | MenuController | `self, settings_manager, prefs: dict` | `None` | INTERNAL |
| `add_recent_file` | MenuController | `self, file_path: Path` | `None` | USED |
| `check_for_updates` | MenuController | `self` | `None` | USED |
| `cleanup` | MenuController | `self` | `None` | USED |
| `clear_recent_files` | MenuController | `self` | `None` | USED |
| `get_recent_files` | MenuController | `self` | `List[dict]` | USED |
| `initialize` | MenuController | `self` | `None` | USED |
| `open_command_palette` | MenuController | `self` | `None` | USED |
| `open_hotkey_manager` | MenuController | `self` | `None` | USED |
| `open_performance_dashboard` | MenuController | `self` | `None` | USED |
| `open_preferences` | MenuController | `self` | `None` | USED |
| `open_recent_file` | MenuController | `self, file_path: str` | `None` | USED |
| `show_about_dialog` | MenuController | `self` | `None` | USED |
| `show_desktop_selector_builder` | MenuController | `self` | `None` | USED |
| `show_documentation` | MenuController | `self` | `None` | USED |
| `show_keyboard_shortcuts` | MenuController | `self` | `None` | USED |
| `update_action_state` | MenuController | `self, action_name: str, enabled: bool` | `None` | UNUSED |
| `update_recent_files_menu` | MenuController | `self` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.node_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\node_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_get_graph` | NodeController | `self` | `-` | INTERNAL |
| `_initialize_node_registry` | NodeController | `self` | `None` | INTERNAL |
| `cleanup` | NodeController | `self` | `None` | USED |
| `disable_all_selected` | NodeController | `self` | `None` | USED |
| `find_node` | NodeController | `self` | `None` | USED |
| `get_nearest_exec_out` | NodeController | `self` | `None` | USED |
| `get_selected_nodes` | NodeController | `self` | `list` | USED |
| `initialize` | NodeController | `self` | `None` | USED |
| `navigate_to_node` | NodeController | `self, node_id: str` | `None` | USED |
| `select_nearest_node` | NodeController | `self` | `None` | USED |
| `toggle_disable_node` | NodeController | `self` | `None` | USED |
| `update_node_property` | NodeController | `self, node_id: str, property_name: str, ...` | `None` | UNUSED |


## casare_rpa.presentation.canvas.controllers.panel_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\panel_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | PanelController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_position_minimap` | PanelController | `self` | `None` | INTERNAL |
| `cleanup` | PanelController | `self` | `None` | USED |
| `get_validation_errors` | PanelController | `self` | `list` | USED |
| `hide_bottom_panel` | PanelController | `self` | `None` | USED |
| `hide_minimap` | PanelController | `self` | `None` | USED |
| `hide_variable_inspector` | PanelController | `self` | `None` | USED |
| `initialize` | PanelController | `self` | `None` | USED |
| `navigate_to_node` | PanelController | `self, node_id: str` | `None` | USED |
| `show_bottom_panel` | PanelController | `self` | `None` | USED |
| `show_minimap` | PanelController | `self` | `None` | USED |
| `show_panel_tab` | PanelController | `self, tab_name: str` | `None` | USED |
| `show_validation_tab_if_errors` | PanelController | `self` | `None` | UNUSED |
| `show_variable_inspector` | PanelController | `self` | `None` | USED |
| `toggle_bottom_panel` | PanelController | `self, visible: bool` | `None` | UNUSED |
| `toggle_minimap` | PanelController | `self, visible: bool` | `None` | USED |
| `toggle_panel_tab` | PanelController | `self, tab_name: str` | `None` | USED |
| `toggle_properties_panel` | PanelController | `self, visible: bool` | `None` | USED |
| `toggle_variable_inspector` | PanelController | `self, visible: bool` | `None` | UNUSED |
| `trigger_validation` | PanelController | `self` | `None` | USED |
| `update_status_bar_buttons` | PanelController | `self` | `None` | USED |
| `update_variables_panel` | PanelController | `self, variables: dict` | `None` | UNUSED |


## casare_rpa.presentation.canvas.controllers.preferences_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\preferences_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | PreferencesController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_on_preferences_updated_event` | PreferencesController | `self, event: Event` | `None` | INTERNAL |
| `_on_theme_changed_event` | PreferencesController | `self, event: Event` | `None` | INTERNAL |
| `cleanup` | PreferencesController | `self` | `None` | USED |
| `get_autosave_interval` | PreferencesController | `self` | `int` | USED |
| `get_hotkeys` | PreferencesController | `self` | `Dict[str, str]` | UNUSED |
| `get_setting` | PreferencesController | `self, key: str, default: Any` | `Any` | USED |
| `get_settings_manager` | PreferencesController | `self` | `Any` | USED |
| `initialize` | PreferencesController | `self` | `None` | USED |
| `is_autosave_enabled` | PreferencesController | `self` | `bool` | USED |
| `reset_preferences` | PreferencesController | `self` | `bool` | UNUSED |
| `save_preferences` | PreferencesController | `self` | `bool` | UNUSED |
| `set_setting` | PreferencesController | `self, key: str, value: Any` | `bool` | USED |
| `set_theme` | PreferencesController | `self, theme_name: str` | `bool` | UNUSED |
| `update_hotkey` | PreferencesController | `self, action: str, hotkey: str` | `bool` | UNUSED |


## casare_rpa.presentation.canvas.controllers.project_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\project_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ProjectController | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `async _create_project_async` | ProjectController | `self, project_data: dict` | `None` | INTERNAL |
| `_handle_create_result` | ProjectController | `self, future` | `None` | INTERNAL |
| `_handle_open_result` | ProjectController | `self, future` | `None` | INTERNAL |
| `_handle_scenario_open_result` | ProjectController | `self, future` | `None` | INTERNAL |
| `_on_project_created` | ProjectController | `self, project_data: dict` | `None` | INTERNAL |
| `_on_project_opened` | ProjectController | `self, path: str` | `None` | INTERNAL |
| `_on_project_removed` | ProjectController | `self, project_id: str` | `None` | INTERNAL |
| `_on_scenario_opened` | ProjectController | `self, project_path: str, scenario_path: str` | `None` | INTERNAL |
| `async _open_project_async` | ProjectController | `self, path: Path` | `None` | INTERNAL |
| `async _open_scenario_async` | ProjectController | `self, project_path: Path, scenario_path: Path` | `None` | INTERNAL |
| `async _remove_project_async` | ProjectController | `self, project_id: str` | `None` | INTERNAL |
| `_setup_repository` | ProjectController | `self` | `None` | INTERNAL |
| `_show_dialog_with_projects` | ProjectController | `self, recent_projects: List['ProjectIndexEntry']` | `None` | INTERNAL |
| `_show_error` | ProjectController | `self, title: str, message: str` | `None` | INTERNAL |
| `cleanup` | ProjectController | `self` | `None` | USED |
| `close_project` | ProjectController | `self` | `None` | UNUSED |
| `current_project` | ProjectController | `self` | `Optional['Project']` | UNUSED |
| `async get_recent_projects` | ProjectController | `self` | `List['ProjectIndexEntry']` | USED |
| `has_project` | ProjectController | `self` | `bool` | UNUSED |
| `initialize` | ProjectController | `self` | `None` | USED |
| `show_project_manager` | ProjectController | `self` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.robot_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\robot_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotController | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_connect_panel_signals` | RobotController | `self` | `None` | INTERNAL |
| `_convert_robot_data` | RobotController | `self, robot_data_list: list` | `list` | INTERNAL |
| `_get_api_key_from_config` | RobotController | `self` | `Optional[str]` | INTERNAL |
| `async _get_local_robots` | RobotController | `self` | `list` | INTERNAL |
| `_get_orchestrator_url_from_config` | RobotController | `self` | `Optional[str]` | INTERNAL |
| `_get_orchestrator_url_list` | RobotController | `self` | `List[str]` | INTERNAL |
| `_get_workflow_data` | RobotController | `self` | `Optional[dict]` | INTERNAL |
| `_get_workflow_variables` | RobotController | `self` | `Optional[dict]` | INTERNAL |
| `_init_orchestrator_client` | RobotController | `self` | `None` | INTERNAL |
| `_on_orchestrator_connected` | RobotController | `self, data: dict` | `None` | INTERNAL |
| `_on_orchestrator_disconnected` | RobotController | `self, data: dict` | `None` | INTERNAL |
| `_on_orchestrator_error` | RobotController | `self, data: dict` | `None` | INTERNAL |
| `_on_panel_mode_changed` | RobotController | `self, mode: str` | `None` | INTERNAL |
| `_on_panel_refresh_requested` | RobotController | `self` | `None` | INTERNAL |
| `_on_panel_robot_selected` | RobotController | `self, robot_id: str` | `None` | INTERNAL |
| `_on_robot_status_update` | RobotController | `self, data: dict` | `None` | INTERNAL |
| `_on_submit_to_cloud_requested` | RobotController | `self` | `None` | INTERNAL |
| `async _submit_current_workflow` | RobotController | `self` | `None` | INTERNAL |
| `cleanup` | RobotController | `self` | `None` | USED |
| `clear_selection` | RobotController | `self` | `None` | USED |
| `async connect_to_orchestrator` | RobotController | `self, url: Optional[str]` | `bool` | USED |
| `async disconnect_from_orchestrator` | RobotController | `self` | `None` | UNUSED |
| `execution_mode` | RobotController | `self` | `str` | UNUSED |
| `async get_available_robots` | RobotController | `self` | `list` | USED |
| `async get_robot_logs` | RobotController | `self, robot_id: str, limit: int, ...` | `List[dict]` | UNUSED |
| `async get_robot_metrics` | RobotController | `self, robot_id: str` | `dict` | USED |
| `async get_robots_by_capability` | RobotController | `self, capability: str` | `list` | UNUSED |
| `get_selected_robot` | RobotController | `self` | `-` | USED |
| `async get_statistics` | RobotController | `self` | `dict` | USED |
| `has_robot_selected` | RobotController | `self` | `bool` | UNUSED |
| `initialize` | RobotController | `self` | `None` | USED |
| `is_cloud_mode` | RobotController | `self` | `bool` | UNUSED |
| `is_connected` | RobotController | `self` | `bool` | USED |
| `is_local_mode` | RobotController | `self` | `bool` | UNUSED |
| `orchestrator_url` | RobotController | `self` | `Optional[str]` | UNUSED |
| `async pause_robot` | RobotController | `self, robot_id: str` | `bool` | UNUSED |
| `async refresh_robots` | RobotController | `self` | `None` | USED |
| `async restart_all_robots` | RobotController | `self` | `Dict[str, bool]` | UNUSED |
| `async restart_robot` | RobotController | `self, robot_id: str` | `bool` | USED |
| `async resume_robot` | RobotController | `self, robot_id: str` | `bool` | UNUSED |
| `robots` | RobotController | `self` | `list` | UNUSED |
| `select_robot` | RobotController | `self, robot_id: str` | `None` | USED |
| `selected_robot_id` | RobotController | `self` | `Optional[str]` | UNUSED |
| `set_execution_mode` | RobotController | `self, mode: str` | `None` | USED |
| `set_panel` | RobotController | `self, panel` | `None` | USED |
| `async start_robot` | RobotController | `self, robot_id: str` | `bool` | UNUSED |
| `async stop_all_robots` | RobotController | `self, force: bool` | `Dict[str, bool]` | UNUSED |
| `async stop_robot` | RobotController | `self, robot_id: str, force: bool` | `bool` | USED |
| `async submit_job` | RobotController | `self, workflow_data: dict, variables: Optional[dict], ...` | `Optional[str]` | USED |


## casare_rpa.presentation.canvas.controllers.scheduling_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\scheduling_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SchedulingController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_execute_scheduled_workflow` | SchedulingController | `self, schedule, workflow_path: Path` | `None` | INTERNAL |
| `_load_schedules` | SchedulingController | `self` | `None` | INTERNAL |
| `_on_schedule_saved` | SchedulingController | `self, schedule` | `None` | INTERNAL |
| `_prompt_save_workflow` | SchedulingController | `self` | `bool` | INTERNAL |
| `_save_all_schedules` | SchedulingController | `self, dialog` | `None` | INTERNAL |
| `_show_schedule_error` | SchedulingController | `self, error_message: str` | `None` | INTERNAL |
| `cleanup` | SchedulingController | `self` | `None` | USED |
| `delete_schedule` | SchedulingController | `self, schedule_id: str` | `bool` | USED |
| `get_schedule_count` | SchedulingController | `self` | `int` | UNUSED |
| `get_schedules` | SchedulingController | `self` | `List[Any]` | USED |
| `initialize` | SchedulingController | `self` | `None` | USED |
| `manage_schedules` | SchedulingController | `self` | `None` | USED |
| `run_scheduled_workflow` | SchedulingController | `self, schedule` | `None` | USED |
| `schedule_workflow` | SchedulingController | `self` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.selector_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\selector_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SelectorController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_on_picker_opened_event` | SelectorController | `self, event: Event` | `None` | INTERNAL |
| `_on_recording_complete` | SelectorController | `self, actions: list` | `None` | INTERNAL |
| `_on_selector_picked` | SelectorController | `self, selector_value: str, selector_type: str` | `None` | INTERNAL |
| `cleanup` | SelectorController | `self` | `None` | USED |
| `get_selector_integration` | SelectorController | `self` | `-` | UNUSED |
| `initialize` | SelectorController | `self` | `None` | USED |
| `async initialize_for_page` | SelectorController | `self, page: Any` | `None` | USED |
| `is_picker_active` | SelectorController | `self` | `bool` | UNUSED |
| `async start_picker` | SelectorController | `self, target_node: Optional[Any], target_property: str` | `None` | USED |
| `async start_recording` | SelectorController | `self` | `None` | USED |
| `async stop_picker` | SelectorController | `self` | `None` | UNUSED |
| `async stop_recording` | SelectorController | `self` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.ui_state_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\ui_state_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | UIStateController | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_connect_dock_signals` | UIStateController | `self` | `None` | INTERNAL |
| `_on_auto_save_timeout` | UIStateController | `self` | `None` | INTERNAL |
| `add_recent_file` | UIStateController | `self, file_path: Path` | `None` | USED |
| `cleanup` | UIStateController | `self` | `None` | USED |
| `clear_recent_files` | UIStateController | `self` | `None` | USED |
| `get_auto_save_enabled` | UIStateController | `self` | `bool` | UNUSED |
| `get_auto_validate_enabled` | UIStateController | `self` | `bool` | UNUSED |
| `get_last_directory` | UIStateController | `self` | `Optional[Path]` | UNUSED |
| `get_recent_files` | UIStateController | `self` | `List[dict]` | USED |
| `get_settings` | UIStateController | `self` | `Optional[QSettings]` | USED |
| `initialize` | UIStateController | `self` | `None` | USED |
| `is_initialized` | UIStateController | `self` | `bool` | UNUSED |
| `remove_recent_file` | UIStateController | `self, file_path: Path` | `None` | UNUSED |
| `reset_state` | UIStateController | `self` | `None` | USED |
| `restore_panel_states` | UIStateController | `self` | `None` | USED |
| `restore_state` | UIStateController | `self` | `None` | USED |
| `restore_window_geometry` | UIStateController | `self` | `None` | USED |
| `save_panel_states` | UIStateController | `self` | `None` | USED |
| `save_state` | UIStateController | `self` | `None` | USED |
| `save_window_geometry` | UIStateController | `self` | `None` | USED |
| `schedule_auto_save` | UIStateController | `self` | `None` | USED |
| `set_auto_save_enabled` | UIStateController | `self, enabled: bool` | `None` | UNUSED |
| `set_auto_validate_enabled` | UIStateController | `self, enabled: bool` | `None` | UNUSED |
| `set_last_directory` | UIStateController | `self, directory: Path` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.viewport_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\viewport_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ViewportController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_get_graph` | ViewportController | `self` | `-` | INTERNAL |
| `_position_minimap` | ViewportController | `self` | `None` | INTERNAL |
| `_show_frame_error` | ViewportController | `self, error_message: str` | `None` | INTERNAL |
| `center_on_node` | ViewportController | `self, node_id: str` | `None` | UNUSED |
| `cleanup` | ViewportController | `self` | `None` | USED |
| `create_frame` | ViewportController | `self` | `None` | USED |
| `create_minimap` | ViewportController | `self, node_graph` | `None` | USED |
| `fit_to_view` | ViewportController | `self` | `None` | UNUSED |
| `get_current_zoom` | ViewportController | `self` | `float` | UNUSED |
| `hide_minimap` | ViewportController | `self` | `None` | USED |
| `initialize` | ViewportController | `self` | `None` | USED |
| `is_minimap_visible` | ViewportController | `self` | `bool` | UNUSED |
| `position_minimap` | ViewportController | `self` | `None` | USED |
| `reset_viewport` | ViewportController | `self` | `None` | UNUSED |
| `show_minimap` | ViewportController | `self` | `None` | USED |
| `toggle_minimap` | ViewportController | `self, checked: bool` | `None` | USED |
| `update_zoom_display` | ViewportController | `self, zoom_percent: float` | `None` | USED |


## casare_rpa.presentation.canvas.controllers.workflow_controller

**File:** `src\casare_rpa\presentation\canvas\controllers\workflow_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowController | `self, main_window: 'MainWindow'` | `-` | DUNDER |
| `_check_validation_before_save` | WorkflowController | `self` | `bool` | INTERNAL |
| `_get_orchestrator_client` | WorkflowController | `self` | `OrchestratorClient` | INTERNAL |
| `_update_save_action` | WorkflowController | `self` | `None` | INTERNAL |
| `_update_window_title` | WorkflowController | `self` | `None` | INTERNAL |
| `_validate_after_open` | WorkflowController | `self` | `None` | INTERNAL |
| `check_unsaved_changes` | WorkflowController | `self` | `bool` | USED |
| `check_validation_before_run` | WorkflowController | `self` | `bool` | UNUSED |
| `cleanup` | WorkflowController | `self` | `None` | USED |
| `close_workflow` | WorkflowController | `self` | `bool` | UNUSED |
| `current_file` | WorkflowController | `self` | `Optional[Path]` | UNUSED |
| `export_selected_nodes` | WorkflowController | `self` | `None` | USED |
| `import_workflow` | WorkflowController | `self` | `None` | USED |
| `initialize` | WorkflowController | `self` | `None` | USED |
| `is_modified` | WorkflowController | `self` | `bool` | UNUSED |
| `new_from_template` | WorkflowController | `self` | `None` | USED |
| `new_workflow` | WorkflowController | `self` | `None` | USED |
| `on_import_data` | WorkflowController | `data: dict, position: tuple` | `None` | UNUSED |
| `on_import_file` | WorkflowController | `file_path: str, position: tuple` | `None` | UNUSED |
| `open_workflow` | WorkflowController | `self` | `None` | USED |
| `paste_workflow` | WorkflowController | `self` | `None` | USED |
| `async run_local` | WorkflowController | `self` | `None` | USED |
| `async run_on_robot` | WorkflowController | `self` | `None` | USED |
| `save_workflow` | WorkflowController | `self` | `None` | USED |
| `save_workflow_as` | WorkflowController | `self` | `None` | USED |
| `set_current_file` | WorkflowController | `self, file_path: Optional[Path]` | `None` | USED |
| `set_modified` | WorkflowController | `self, modified: bool` | `None` | USED |
| `setup_drag_drop_import` | WorkflowController | `self` | `None` | USED |
| `async submit_for_internet_robots` | WorkflowController | `self` | `None` | USED |


## casare_rpa.presentation.canvas.debugger.debug_controller

**File:** `src\casare_rpa\presentation\canvas\debugger\debug_controller.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_evaluate_condition` | Breakpoint | `self, context: 'ExecutionContext'` | `bool` | INTERNAL |
| `_log_message` | Breakpoint | `self, context: 'ExecutionContext'` | `None` | INTERNAL |
| `reset_hit_count` | Breakpoint | `self` | `None` | UNUSED |
| `should_break` | Breakpoint | `self, context: 'ExecutionContext'` | `bool` | USED |
| `__init__` | DebugController | `self, main_window: Optional['MainWindow']` | `-` | DUNDER |
| `_evaluate_watches` | DebugController | `self` | `None` | INTERNAL |
| `async _pause_for_debug` | DebugController | `self` | `None` | INTERNAL |
| `_update_debug_state` | DebugController | `self` | `None` | INTERNAL |
| `add_breakpoint` | DebugController | `self, node_id: str, breakpoint_type: BreakpointType, ...` | `Breakpoint` | USED |
| `add_watch` | DebugController | `self, expression: str` | `WatchExpression` | UNUSED |
| `async check_breakpoint` | DebugController | `self, node_id: str, context: 'ExecutionContext'` | `bool` | USED |
| `cleanup` | DebugController | `self` | `None` | USED |
| `clear_all_breakpoints` | DebugController | `self` | `int` | UNUSED |
| `clear_repl` | DebugController | `self` | `None` | UNUSED |
| `continue_execution` | DebugController | `self` | `None` | USED |
| `create_snapshot` | DebugController | `self, description: str` | `ExecutionSnapshot` | USED |
| `delete_snapshot` | DebugController | `self, snapshot_id: str` | `bool` | USED |
| `enable_debug_mode` | DebugController | `self, enabled: bool` | `None` | UNUSED |
| `evaluate_expression` | DebugController | `self, expression: str` | `tuple[Any, Optional[str]]` | USED |
| `get_all_breakpoints` | DebugController | `self` | `List[Breakpoint]` | UNUSED |
| `get_breakpoint` | DebugController | `self, node_id: str` | `Optional[Breakpoint]` | USED |
| `get_call_stack` | DebugController | `self` | `List[CallStackFrame]` | UNUSED |
| `get_repl_history` | DebugController | `self` | `List[str]` | UNUSED |
| `get_snapshots` | DebugController | `self` | `List[ExecutionSnapshot]` | UNUSED |
| `get_variable_value` | DebugController | `self, name: str` | `tuple[Any, bool]` | UNUSED |
| `get_watches` | DebugController | `self` | `List[WatchExpression]` | UNUSED |
| `has_breakpoint` | DebugController | `self, node_id: str` | `bool` | UNUSED |
| `is_debug_mode` | DebugController | `self` | `bool` | UNUSED |
| `pop_call_stack` | DebugController | `self` | `Optional[CallStackFrame]` | USED |
| `push_call_stack` | DebugController | `self, node_id: str, node_name: str, ...` | `None` | USED |
| `remove_breakpoint` | DebugController | `self, node_id: str` | `bool` | USED |
| `remove_watch` | DebugController | `self, expression: str` | `bool` | UNUSED |
| `restore_snapshot` | DebugController | `self, snapshot_id: str` | `bool` | USED |
| `set_variable_value` | DebugController | `self, name: str, value: Any` | `bool` | UNUSED |
| `async should_pause_for_step` | DebugController | `self, node_id: str, context: 'ExecutionContext'` | `bool` | USED |
| `step_into` | DebugController | `self` | `None` | USED |
| `step_out` | DebugController | `self` | `None` | USED |
| `step_over` | DebugController | `self` | `None` | USED |
| `toggle_breakpoint` | DebugController | `self, node_id: str` | `bool` | USED |
| `toggle_breakpoint_enabled` | DebugController | `self, node_id: str` | `bool` | UNUSED |


## casare_rpa.presentation.canvas.desktop.desktop_recording_panel

**File:** `src\casare_rpa\presentation\canvas\desktop\desktop_recording_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ActionListItem | `self, action: DesktopRecordedAction, index: int` | `-` | DUNDER |
| `__init__` | DesktopRecordingPanel | `self, parent` | `-` | DUNDER |
| `_clear_all` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_delete_selected` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_generate_workflow` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_on_action_recorded` | DesktopRecordingPanel | `self, action: DesktopRecordedAction` | `-` | INTERNAL |
| `_on_recording_paused` | DesktopRecordingPanel | `self, paused: bool` | `-` | INTERNAL |
| `_on_recording_started` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_on_recording_stopped` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_renumber_items` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_setup_ui` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_toggle_pause` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_toggle_recording` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_update_timer_display` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `_update_ui_state` | DesktopRecordingPanel | `self` | `-` | INTERNAL |
| `keyPressEvent` | DesktopRecordingPanel | `self, event` | `-` | USED |


## casare_rpa.presentation.canvas.desktop.rich_comment_node

**File:** `src\casare_rpa\presentation\canvas\desktop\rich_comment_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_markdown_comment` | - | `text: str` | `str` | UNUSED |
| `get_comment_shortcuts` | - | `` | `str` | UNUSED |
| `__init__` | VisualHeaderCommentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualHeaderCommentNode | `self` | `None` | USED |
| `__init__` | VisualRichCommentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRichCommentNode | `self` | `None` | USED |
| `__init__` | VisualStickyNoteNode | `self` | `None` | DUNDER |
| `_apply_sticky_style` | VisualStickyNoteNode | `self` | `-` | INTERNAL |
| `setup_ports` | VisualStickyNoteNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.events.domain_bridge

**File:** `src\casare_rpa\presentation\canvas\events\domain_bridge.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `start_domain_bridge` | - | `` | `DomainEventBridge` | UNUSED |
| `__init__` | DomainEventBridge | `self, domain_bus: Optional[DomainEventBus], presentation_bus: Optional[PresentationEventBus]` | `None` | DUNDER |
| `__new__` | DomainEventBridge | `cls` | `'DomainEventBridge'` | DUNDER |
| `__repr__` | DomainEventBridge | `self` | `str` | DUNDER |
| `_get_priority` | DomainEventBridge | `self, event_type: DomainEventType` | `EventPriority` | INTERNAL |
| `_on_domain_event` | DomainEventBridge | `self, event: DomainEvent` | `None` | INTERNAL |
| `_transform_data` | DomainEventBridge | `self, event: DomainEvent` | `dict` | INTERNAL |
| `is_running` | DomainEventBridge | `self` | `bool` | USED |
| `reset_instance` | DomainEventBridge | `cls` | `None` | UNUSED |
| `start` | DomainEventBridge | `self` | `None` | USED |
| `stop` | DomainEventBridge | `self` | `None` | USED |


## casare_rpa.presentation.canvas.events.event

**File:** `src\casare_rpa\presentation\canvas\events\event.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_generate_event_id` | - | `` | `str` | INTERNAL |
| `__post_init__` | Event | `self` | `-` | DUNDER |
| `__repr__` | Event | `self` | `str` | DUNDER |
| `__str__` | Event | `self` | `str` | DUNDER |
| `category` | Event | `self` | `EventCategory` | UNUSED |
| `datetime` | Event | `self` | `datetime` | UNUSED |
| `get` | Event | `self, key: str, default: Any` | `Any` | USED |
| `has_data` | Event | `self, key: str` | `bool` | UNUSED |
| `is_high_priority` | Event | `self` | `bool` | UNUSED |
| `to_dict` | Event | `self` | `dict[str, Any]` | USED |
| `__str__` | EventFilter | `self` | `str` | DUNDER |
| `matches` | EventFilter | `self, event: Event` | `bool` | USED |
| `__gt__` | EventPriority | `self, other: 'EventPriority'` | `bool` | DUNDER |
| `__lt__` | EventPriority | `self, other: 'EventPriority'` | `bool` | DUNDER |


## casare_rpa.presentation.canvas.events.event_batcher

**File:** `src\casare_rpa\presentation\canvas\events\event_batcher.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | EventBatcher | `self, interval_ms: int` | `None` | DUNDER |
| `__repr__` | EventBatcher | `self` | `str` | DUNDER |
| `_flush` | EventBatcher | `self` | `None` | INTERNAL |
| `batch` | EventBatcher | `self, event: Event` | `None` | UNUSED |
| `clear` | EventBatcher | `self` | `None` | USED |
| `flush_now` | EventBatcher | `self` | `None` | USED |
| `has_pending` | EventBatcher | `self` | `bool` | UNUSED |
| `pending_count` | EventBatcher | `self` | `int` | USED |


## casare_rpa.presentation.canvas.events.event_bus

**File:** `src\casare_rpa\presentation\canvas\events\event_bus.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | EventBus | `self` | `-` | DUNDER |
| `__new__` | EventBus | `cls` | `'EventBus'` | DUNDER |
| `__repr__` | EventBus | `self` | `str` | DUNDER |
| `_call_handler` | EventBus | `self, handler: EventHandler, event: Event` | `None` | INTERNAL |
| `_invalidate_cache` | EventBus | `self, event_type: EventType` | `None` | INTERNAL |
| `clear_all_subscribers` | EventBus | `self` | `None` | UNUSED |
| `clear_history` | EventBus | `self` | `None` | USED |
| `enable_history` | EventBus | `self, enabled: bool` | `None` | UNUSED |
| `get_history` | EventBus | `self, event_type: Optional[EventType], category: Optional[EventCategory], ...` | `list[Event]` | USED |
| `get_metrics` | EventBus | `self` | `dict[str, Any]` | USED |
| `publish` | EventBus | `self, event: Event` | `None` | USED |
| `reset_instance` | EventBus | `cls` | `None` | UNUSED |
| `reset_metrics` | EventBus | `self` | `None` | UNUSED |
| `subscribe` | EventBus | `self, event_type: EventType, handler: EventHandler` | `None` | USED |
| `subscribe_all` | EventBus | `self, handler: EventHandler` | `None` | USED |
| `subscribe_filtered` | EventBus | `self, event_filter: EventFilter, handler: EventHandler` | `None` | USED |
| `unsubscribe` | EventBus | `self, event_type: EventType, handler: EventHandler` | `bool` | USED |
| `unsubscribe_all` | EventBus | `self, handler: EventHandler` | `bool` | USED |
| `unsubscribe_filtered` | EventBus | `self, event_filter: EventFilter, handler: EventHandler` | `bool` | USED |


## casare_rpa.presentation.canvas.events.event_handler

**File:** `src\casare_rpa\presentation\canvas\events\event_handler.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `decorator` | - | `func: Callable` | `Callable` | UNUSED |
| `event_handler` | - | `event_type: Optional[EventType], event_filter: Optional[EventFilter]` | `Callable` | USED |
| `wrapper` | - | `` | `-` | UNUSED |
| `__del__` | EventHandler | `self` | `-` | DUNDER |
| `__init__` | EventHandler | `self, event_bus: Optional[EventBus]` | `-` | DUNDER |
| `_auto_subscribe_decorated_handlers` | EventHandler | `self` | `None` | INTERNAL |
| `cleanup` | EventHandler | `self` | `None` | USED |
| `publish` | EventHandler | `self, event: Event` | `None` | USED |
| `subscribe` | EventHandler | `self, event_type: EventType, handler: Callable[[Event], None]` | `None` | USED |
| `subscribe_all` | EventHandler | `self, handler: Callable[[Event], None]` | `None` | USED |
| `subscribe_filtered` | EventHandler | `self, event_filter: EventFilter, handler: Callable[[Event], None]` | `None` | USED |
| `unsubscribe` | EventHandler | `self, event_type: EventType, handler: Callable[[Event], None]` | `bool` | USED |
| `unsubscribe_all` | EventHandler | `self, handler: Callable[[Event], None]` | `bool` | USED |
| `unsubscribe_filtered` | EventHandler | `self, event_filter: EventFilter, handler: Callable[[Event], None]` | `bool` | USED |


## casare_rpa.presentation.canvas.events.event_types

**File:** `src\casare_rpa\presentation\canvas\events\event_types.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__repr__` | EventType | `self` | `str` | DUNDER |
| `__str__` | EventType | `self` | `str` | DUNDER |
| `category` | EventType | `self` | `EventCategory` | UNUSED |


## casare_rpa.presentation.canvas.events.lazy_subscription

**File:** `src\casare_rpa\presentation\canvas\events\lazy_subscription.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LazySubscription | `self, event_type: EventType, handler: Callable, ...` | `None` | DUNDER |
| `activate` | LazySubscription | `self` | `None` | USED |
| `cleanup` | LazySubscription | `self` | `None` | USED |
| `deactivate` | LazySubscription | `self` | `None` | USED |
| `eventFilter` | LazySubscription | `self, watched: QObject, event: QEvent` | `bool` | USED |
| `__init__` | LazySubscriptionGroup | `self, component: QWidget, subscriptions: List[tuple[EventType, Callable]]` | `None` | DUNDER |
| `activate_all` | LazySubscriptionGroup | `self` | `None` | UNUSED |
| `active` | LazySubscriptionGroup | `self` | `bool` | UNUSED |
| `cleanup` | LazySubscriptionGroup | `self` | `None` | USED |
| `deactivate_all` | LazySubscriptionGroup | `self` | `None` | UNUSED |
| `__init__` | _SharedVisibilitySubscription | `self, event_type: EventType, handler: Callable, ...` | `None` | DUNDER |
| `activate` | _SharedVisibilitySubscription | `self` | `None` | USED |
| `deactivate` | _SharedVisibilitySubscription | `self` | `None` | USED |
| `wrapped_activate` | _SharedVisibilitySubscription | `` | `None` | UNUSED |
| `wrapped_deactivate` | _SharedVisibilitySubscription | `` | `None` | UNUSED |


## casare_rpa.presentation.canvas.events.qt_signal_bridge

**File:** `src\casare_rpa\presentation\canvas\events\qt_signal_bridge.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | QtEventEmitter | `self, parent: Optional[QObject], event_bus: Optional[EventBus]` | `-` | DUNDER |
| `emit` | QtEventEmitter | `self, event: Event` | `None` | USED |
| `__del__` | QtEventSubscriber | `self` | `-` | DUNDER |
| `__init__` | QtEventSubscriber | `self, parent: Optional[QObject], event_bus: Optional[EventBus]` | `-` | DUNDER |
| `cleanup` | QtEventSubscriber | `self` | `None` | USED |
| `handler` | QtEventSubscriber | `event: Event` | `None` | USED |
| `subscribe` | QtEventSubscriber | `self, event_type: EventType` | `None` | USED |
| `unsubscribe` | QtEventSubscriber | `self, event_type: EventType` | `None` | USED |
| `__del__` | QtSignalBridge | `self` | `-` | DUNDER |
| `__init__` | QtSignalBridge | `self, event_bus: Optional[EventBus], parent: Optional[QObject]` | `-` | DUNDER |
| `_on_event_bus_event` | QtSignalBridge | `self, event: Event` | `None` | INTERNAL |
| `cleanup` | QtSignalBridge | `self` | `None` | USED |
| `publish` | QtSignalBridge | `self, event: Event` | `None` | USED |


## casare_rpa.presentation.canvas.execution.canvas_workflow_runner

**File:** `src\casare_rpa\presentation\canvas\execution\canvas_workflow_runner.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CanvasWorkflowRunner | `self, serializer: 'WorkflowSerializer', event_bus: 'EventBus', ...` | `-` | DUNDER |
| `async _create_trigger` | CanvasWorkflowRunner | `self, trigger_node_type: str, trigger_config: Dict, ...` | `Optional['BaseTrigger']` | INTERNAL |
| `_find_trigger_node` | CanvasWorkflowRunner | `self, workflow_data: Dict` | `Optional[tuple]` | INTERNAL |
| `_get_continue_on_error` | CanvasWorkflowRunner | `self, workflow_data: Dict[str, Any]` | `bool` | INTERNAL |
| `_get_node_timeout` | CanvasWorkflowRunner | `self, workflow_data: Dict[str, Any]` | `float` | INTERNAL |
| `_get_project_context` | CanvasWorkflowRunner | `self` | `Optional['ProjectContext']` | INTERNAL |
| `async _on_trigger_fire` | CanvasWorkflowRunner | `self, event: 'TriggerEvent'` | `None` | INTERNAL |
| `is_listening` | CanvasWorkflowRunner | `self` | `bool` | UNUSED |
| `is_paused` | CanvasWorkflowRunner | `self` | `bool` | UNUSED |
| `is_running` | CanvasWorkflowRunner | `self` | `bool` | USED |
| `pause` | CanvasWorkflowRunner | `self` | `None` | USED |
| `resume` | CanvasWorkflowRunner | `self` | `None` | USED |
| `async run_all_workflows` | CanvasWorkflowRunner | `self, pause_event: asyncio.Event` | `bool` | USED |
| `async run_workflow` | CanvasWorkflowRunner | `self, target_node_id: Optional[str], single_node: bool` | `bool` | USED |
| `async run_workflow_with_pause_support` | CanvasWorkflowRunner | `self, pause_event: asyncio.Event, target_node_id: Optional[str], ...` | `bool` | USED |
| `async start_listening` | CanvasWorkflowRunner | `self` | `bool` | USED |
| `stop` | CanvasWorkflowRunner | `self` | `None` | USED |
| `async stop_listening` | CanvasWorkflowRunner | `self` | `bool` | USED |
| `trigger_run_count` | CanvasWorkflowRunner | `self` | `int` | UNUSED |


## casare_rpa.presentation.canvas.graph.category_utils

**File:** `src\casare_rpa\presentation\canvas\graph\category_utils.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_update_recursive` | - | `node: CategoryNode` | `int` | INTERNAL |
| `build_category_tree` | - | `categories: List[str]` | `CategoryNode` | UNUSED |
| `get_all_parent_paths` | - | `category_path: str` | `List[str]` | UNUSED |
| `get_category_color` | - | `category_path: str` | `QColor` | USED |
| `get_category_color_with_alpha` | - | `category_path: str, alpha: int` | `QColor` | UNUSED |
| `get_category_sort_key` | - | `category_path: str` | `Tuple[int, str]` | USED |
| `get_display_name` | - | `category_path: str` | `str` | USED |
| `get_full_display_path` | - | `category_path: str, separator: str` | `str` | UNUSED |
| `normalize_category` | - | `category_path: str` | `str` | UNUSED |
| `update_category_counts` | - | `tree: CategoryNode, category_node_counts: Dict[str, int]` | `None` | UNUSED |
| `add_child` | CategoryNode | `self, name: str, path: str` | `'CategoryNode'` | USED |
| `get_all_paths` | CategoryNode | `self` | `List[str]` | USED |
| `has_nodes` | CategoryNode | `self` | `bool` | UNUSED |
| `__bool__` | CategoryPath | `self` | `bool` | DUNDER |
| `__str__` | CategoryPath | `self` | `str` | DUNDER |
| `depth` | CategoryPath | `self` | `int` | UNUSED |
| `is_ancestor_of` | CategoryPath | `self, other: 'CategoryPath'` | `bool` | USED |
| `is_descendant_of` | CategoryPath | `self, other: 'CategoryPath'` | `bool` | UNUSED |
| `leaf` | CategoryPath | `self` | `str` | UNUSED |
| `parent` | CategoryPath | `self` | `Optional['CategoryPath']` | USED |
| `parent_path` | CategoryPath | `self` | `str` | UNUSED |
| `parse` | CategoryPath | `cls, path: str` | `'CategoryPath'` | USED |
| `root` | CategoryPath | `self` | `str` | UNUSED |


## casare_rpa.presentation.canvas.graph.collapse_components

**File:** `src\casare_rpa\presentation\canvas\graph\collapse_components.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CollapseButton | `self, parent: 'NodeFrame'` | `-` | DUNDER |
| `_update_position` | CollapseButton | `self` | `None` | INTERNAL |
| `hoverEnterEvent` | CollapseButton | `self, event` | `-` | USED |
| `hoverLeaveEvent` | CollapseButton | `self, event` | `-` | USED |
| `mousePressEvent` | CollapseButton | `self, event` | `-` | USED |
| `paint` | CollapseButton | `self, painter: QPainter, option, ...` | `-` | USED |
| `__init__` | ExposedPortIndicator | `self, port_name: str, is_output: bool, ...` | `-` | DUNDER |
| `__init__` | ExposedPortManager | `self, frame: 'NodeFrame'` | `-` | DUNDER |
| `_get_port_color` | ExposedPortManager | `self, port` | `QColor` | INTERNAL |
| `clear` | ExposedPortManager | `self` | `None` | USED |
| `create_exposed_ports` | ExposedPortManager | `self` | `None` | USED |
| `indicators` | ExposedPortManager | `self` | `list[ExposedPortIndicator]` | UNUSED |


## casare_rpa.presentation.canvas.graph.composite_node_creator

**File:** `src\casare_rpa\presentation\canvas\graph\composite_node_creator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CompositeNodeCreator | `self, graph: 'NodeGraph', parent: Optional[QObject]` | `None` | DUNDER |
| `_setup_loop_pairing` | CompositeNodeCreator | `self, start_node, end_node, ...` | `None` | INTERNAL |
| `_setup_try_catch_pairing` | CompositeNodeCreator | `self, try_node, catch_node, ...` | `None` | INTERNAL |
| `create_for_loop_pair` | CompositeNodeCreator | `self, x: float, y: float` | `Optional[Tuple]` | USED |
| `create_try_catch_finally` | CompositeNodeCreator | `self, x: float, y: float` | `Optional[Tuple]` | USED |
| `create_while_loop_pair` | CompositeNodeCreator | `self, x: float, y: float` | `Optional[Tuple]` | USED |
| `graph` | CompositeNodeCreator | `self` | `'NodeGraph'` | UNUSED |
| `handle_composite_node` | CompositeNodeCreator | `self, composite_node` | `None` | USED |
| `replace_composite` | CompositeNodeCreator | `` | `-` | UNUSED |


## casare_rpa.presentation.canvas.graph.custom_node_item

**File:** `src\casare_rpa\presentation\canvas\graph\custom_node_item.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AnimationCoordinator | `self` | `-` | DUNDER |
| `_tick` | AnimationCoordinator | `self` | `None` | INTERNAL |
| `animated_count` | AnimationCoordinator | `self` | `int` | UNUSED |
| `get_instance` | AnimationCoordinator | `cls` | `'AnimationCoordinator'` | USED |
| `is_running` | AnimationCoordinator | `self` | `bool` | USED |
| `register` | AnimationCoordinator | `self, node: 'CasareNodeItem'` | `None` | USED |
| `unregister` | AnimationCoordinator | `self, node: 'CasareNodeItem'` | `None` | USED |
| `__init__` | CasareNodeItem | `self, name, parent` | `-` | DUNDER |
| `_draw_checkmark` | CasareNodeItem | `self, painter, rect` | `-` | INTERNAL |
| `_draw_error_icon` | CasareNodeItem | `self, painter, rect` | `-` | INTERNAL |
| `_draw_execution_time` | CasareNodeItem | `self, painter, rect` | `-` | INTERNAL |
| `_draw_robot_override_icon` | CasareNodeItem | `self, painter, rect` | `-` | INTERNAL |
| `_draw_text` | CasareNodeItem | `self, painter, rect` | `-` | INTERNAL |
| `_get_node_rect` | CasareNodeItem | `self` | `QRectF` | INTERNAL |
| `borderColor` | CasareNodeItem | `self` | `-` | UNUSED |
| `boundingRect` | CasareNodeItem | `self` | `QRectF` | USED |
| `clear_execution_state` | CasareNodeItem | `self` | `-` | UNUSED |
| `clear_robot_override` | CasareNodeItem | `self` | `-` | UNUSED |
| `get_robot_override_tooltip` | CasareNodeItem | `self` | `Optional[str]` | UNUSED |
| `get_time_font` | CasareNodeItem | `cls` | `QFont` | USED |
| `paint` | CasareNodeItem | `self, painter, option, ...` | `-` | USED |
| `setBorderColor` | CasareNodeItem | `self, r, g, ...` | `-` | UNUSED |
| `set_completed` | CasareNodeItem | `self, completed: bool` | `-` | USED |
| `set_error` | CasareNodeItem | `self, has_error: bool` | `-` | USED |
| `set_execution_time` | CasareNodeItem | `self, time_seconds: Optional[float]` | `-` | USED |
| `set_icon` | CasareNodeItem | `self, pixmap: QPixmap` | `-` | UNUSED |
| `set_robot_override` | CasareNodeItem | `self, has_override: bool, is_capability_based: bool` | `None` | USED |
| `set_running` | CasareNodeItem | `self, running: bool` | `-` | USED |


## casare_rpa.presentation.canvas.graph.custom_pipe

**File:** `src\casare_rpa\presentation\canvas\graph\custom_pipe.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_show_connection_labels` | - | `` | `bool` | UNUSED |
| `set_show_connection_labels` | - | `show: bool` | `None` | UNUSED |
| `__init__` | CasarePipe | `self` | `-` | DUNDER |
| `_draw_label` | CasarePipe | `self, painter: QPainter` | `None` | INTERNAL |
| `_draw_output_preview` | CasarePipe | `self, painter: QPainter` | `None` | INTERNAL |
| `_format_output_value` | CasarePipe | `self, value` | `str` | INTERNAL |
| `_get_port_type_label` | CasarePipe | `self` | `str` | INTERNAL |
| `hoverEnterEvent` | CasarePipe | `self, event` | `None` | USED |
| `hoverLeaveEvent` | CasarePipe | `self, event` | `None` | USED |
| `is_insert_highlighted` | CasarePipe | `self` | `bool` | UNUSED |
| `paint` | CasarePipe | `self, painter, option, ...` | `-` | USED |
| `set_insert_highlight` | CasarePipe | `self, highlight: bool` | `None` | USED |
| `set_label` | CasarePipe | `self, text: str` | `None` | UNUSED |
| `set_output_value` | CasarePipe | `self, value` | `None` | USED |
| `set_show_label` | CasarePipe | `self, show: bool` | `None` | UNUSED |


## casare_rpa.presentation.canvas.graph.event_filters

**File:** `src\casare_rpa\presentation\canvas\graph\event_filters.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ConnectionDropFilter | `self, graph, widget` | `-` | DUNDER |
| `_show_search_after_release` | ConnectionDropFilter | `self` | `-` | INTERNAL |
| `eventFilter` | ConnectionDropFilter | `self, obj, event` | `-` | USED |
| `__init__` | OutputPortMMBFilter | `self, graph, widget` | `-` | DUNDER |
| `_find_port_at_position` | OutputPortMMBFilter | `self, viewer, scene_pos` | `-` | INTERNAL |
| `_is_exec_port` | OutputPortMMBFilter | `self, port_item` | `bool` | INTERNAL |
| `eventFilter` | OutputPortMMBFilter | `self, obj, event` | `-` | USED |
| `eventFilter` | TooltipBlocker | `self, obj, event` | `-` | USED |


## casare_rpa.presentation.canvas.graph.frame_factory

**File:** `src\casare_rpa\presentation\canvas\graph\frame_factory.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `add_frame_menu_actions` | - | `graph_menu` | `-` | UNUSED |
| `create_frame` | - | `graph_view, title: str, color_name: str, ...` | `'NodeFrame'` | USED |
| `group_selected_nodes` | - | `graph_view, title: str, selected_nodes: List` | `Optional['NodeFrame']` | USED |
| `__init__` | FrameNode | `self` | `-` | DUNDER |
| `get_frame_rect` | FrameNode | `self` | `QRectF` | UNUSED |


## casare_rpa.presentation.canvas.graph.frame_managers

**File:** `src\casare_rpa\presentation\canvas\graph\frame_managers.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FrameBoundsManager | `self, parent: Optional[QObject]` | `-` | DUNDER |
| `_batch_check` | FrameBoundsManager | `self` | `None` | INTERNAL |
| `frame_count` | FrameBoundsManager | `self` | `int` | UNUSED |
| `get_instance` | FrameBoundsManager | `cls` | `'FrameBoundsManager'` | USED |
| `is_running` | FrameBoundsManager | `self` | `bool` | USED |
| `register_frame` | FrameBoundsManager | `self, frame: 'NodeFrame'` | `None` | USED |
| `reset_instance` | FrameBoundsManager | `cls` | `None` | UNUSED |
| `unregister_frame` | FrameBoundsManager | `self, frame: 'NodeFrame'` | `None` | USED |
| `__init__` | FrameDeletedCmd | `self, frame: 'NodeFrame', scene, ...` | `-` | DUNDER |
| `_store_frame_state` | FrameDeletedCmd | `self` | `-` | INTERNAL |
| `redo` | FrameDeletedCmd | `self` | `-` | UNUSED |
| `undo` | FrameDeletedCmd | `self` | `-` | UNUSED |


## casare_rpa.presentation.canvas.graph.frame_renderer

**File:** `src\casare_rpa\presentation\canvas\graph\frame_renderer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FrameRenderer | `self, frame: 'NodeFrame'` | `-` | DUNDER |
| `_draw_node_count` | FrameRenderer | `self, painter: QPainter, rect: QRectF` | `None` | INTERNAL |
| `_get_pen_and_brush` | FrameRenderer | `self` | `tuple[QPen, QBrush]` | INTERNAL |
| `paint` | FrameRenderer | `self, painter: QPainter, option, ...` | `None` | USED |
| `calculate_font_size` | TitleRenderer | `cls, frame_width: float` | `int` | USED |
| `create_font` | TitleRenderer | `cls, frame_width: float` | `QFont` | USED |
| `get_available_width` | TitleRenderer | `cls, frame_width: float` | `float` | USED |


## casare_rpa.presentation.canvas.graph.minimap

**File:** `src\casare_rpa\presentation\canvas\graph\minimap.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | Minimap | `self, node_graph: NodeGraph, parent: Optional[QWidget]` | `-` | DUNDER |
| `_check_and_update` | Minimap | `self` | `None` | INTERNAL |
| `_connect_signals` | Minimap | `self` | `None` | INTERNAL |
| `_on_minimap_clicked` | Minimap | `self, scene_pos: QPointF` | `-` | INTERNAL |
| `_on_node_changed` | Minimap | `self, node` | `None` | INTERNAL |
| `_on_nodes_changed` | Minimap | `self, node_ids` | `None` | INTERNAL |
| `_update_minimap` | Minimap | `self` | `-` | INTERNAL |
| `get_stats` | Minimap | `self` | `dict` | USED |
| `mark_dirty` | Minimap | `self` | `None` | USED |
| `set_update_interval` | Minimap | `self, interval_ms: int` | `-` | UNUSED |
| `set_visible` | Minimap | `self, visible: bool` | `-` | UNUSED |
| `__init__` | MinimapChangeTracker | `self, viewport_tolerance: float` | `-` | DUNDER |
| `_rects_equal` | MinimapChangeTracker | `self, r1: QRectF, r2: QRectF` | `bool` | INTERNAL |
| `commit_update` | MinimapChangeTracker | `self, viewport: QRectF, node_count: int` | `None` | USED |
| `mark_dirty` | MinimapChangeTracker | `self` | `None` | USED |
| `should_update` | MinimapChangeTracker | `self, current_viewport: QRectF, node_count: int` | `bool` | USED |
| `__init__` | MinimapView | `self, parent: Optional[QWidget]` | `-` | DUNDER |
| `drawForeground` | MinimapView | `self, painter, rect` | `-` | UNUSED |
| `mouseMoveEvent` | MinimapView | `self, event` | `-` | USED |
| `mousePressEvent` | MinimapView | `self, event` | `-` | USED |
| `mouseReleaseEvent` | MinimapView | `self, event` | `-` | USED |
| `update_minimap` | MinimapView | `self, node_rects, viewport_rect, ...` | `-` | USED |


## casare_rpa.presentation.canvas.graph.node_creation_helper

**File:** `src\casare_rpa\presentation\canvas\graph\node_creation_helper.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeCreationHelper | `self, graph: 'NodeGraph', parent: Optional[QObject], ...` | `None` | DUNDER |
| `_connect_to_set_variable` | NodeCreationHelper | `self, source_port_item, set_var_node` | `bool` | INTERNAL |
| `_get_node_from_port_item` | NodeCreationHelper | `self, port_item` | `-` | INTERNAL |
| `_get_node_name` | NodeCreationHelper | `self, node` | `str` | INTERNAL |
| `_get_node_position_and_width` | NodeCreationHelper | `self, node` | `Tuple[QPointF, float]` | INTERNAL |
| `_refine_node_position` | NodeCreationHelper | `self, set_var_node, source_scene_pos: QPointF, ...` | `None` | INTERNAL |
| `_set_node_position` | NodeCreationHelper | `self, node, view, ...` | `None` | INTERNAL |
| `auto_connect_new_node` | NodeCreationHelper | `self, new_node, source_port_item` | `bool` | USED |
| `create_node_at_position` | NodeCreationHelper | `self, node_type: str, identifier: str, ...` | `Optional[object]` | USED |
| `create_set_variable_for_port` | NodeCreationHelper | `self, source_port_item` | `Optional[object]` | USED |
| `graph` | NodeCreationHelper | `self` | `'NodeGraph'` | UNUSED |
| `x_gap` | NodeCreationHelper | `self` | `float` | UNUSED |
| `x_gap` | NodeCreationHelper | `self, value: float` | `None` | UNUSED |
| `y_offset` | NodeCreationHelper | `self` | `float` | UNUSED |
| `y_offset` | NodeCreationHelper | `self, value: float` | `None` | UNUSED |


## casare_rpa.presentation.canvas.graph.node_frame

**File:** `src\casare_rpa\presentation\canvas\graph\node_frame.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeFrame | `self, title: str, color: QColor, ...` | `-` | DUNDER |
| `_apply_style` | NodeFrame | `self` | `-` | INTERNAL |
| `_capture_nodes_in_bounds` | NodeFrame | `self` | `None` | INTERNAL |
| `_check_node_bounds` | NodeFrame | `self` | `-` | INTERNAL |
| `_collect_pipes` | NodeFrame | `self, node` | `None` | INTERNAL |
| `_create_title_label` | NodeFrame | `self` | `-` | INTERNAL |
| `_delete_frame` | NodeFrame | `self, use_undo: bool` | `-` | INTERNAL |
| `_do_delete` | NodeFrame | `self` | `-` | INTERNAL |
| `_edit_title` | NodeFrame | `self` | `-` | INTERNAL |
| `_get_resize_corner` | NodeFrame | `self, pos` | `-` | INTERNAL |
| `_update_pipe_visibility` | NodeFrame | `self` | `None` | INTERNAL |
| `_update_title_geometry` | NodeFrame | `self` | `-` | INTERNAL |
| `add_node` | NodeFrame | `self, node` | `-` | USED |
| `collapse` | NodeFrame | `self` | `None` | USED |
| `contextMenuEvent` | NodeFrame | `self, event` | `-` | UNUSED |
| `deserialize` | NodeFrame | `cls, data: Dict[str, Any], node_map: Optional[Dict[str, Any]]` | `'NodeFrame'` | USED |
| `expand` | NodeFrame | `self` | `None` | USED |
| `hoverMoveEvent` | NodeFrame | `self, event` | `-` | USED |
| `is_collapsed` | NodeFrame | `self` | `bool` | UNUSED |
| `itemChange` | NodeFrame | `self, change, value` | `-` | USED |
| `keyPressEvent` | NodeFrame | `self, event` | `-` | USED |
| `mouseDoubleClickEvent` | NodeFrame | `self, event` | `-` | USED |
| `mouseMoveEvent` | NodeFrame | `self, event` | `-` | USED |
| `mousePressEvent` | NodeFrame | `self, event` | `-` | USED |
| `mouseReleaseEvent` | NodeFrame | `self, event` | `-` | USED |
| `paint` | NodeFrame | `self, painter: QPainter, option, ...` | `-` | USED |
| `remove_node` | NodeFrame | `self, node` | `-` | USED |
| `serialize` | NodeFrame | `self` | `Dict[str, Any]` | USED |
| `set_color` | NodeFrame | `self, color: QColor` | `-` | USED |
| `set_graph` | NodeFrame | `cls, graph` | `-` | USED |
| `set_title` | NodeFrame | `self, title: str` | `-` | USED |
| `toggle_collapse` | NodeFrame | `self` | `None` | USED |


## casare_rpa.presentation.canvas.graph.node_graph_widget

**File:** `src\casare_rpa\presentation\canvas\graph\node_graph_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeGraphWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_auto_connect_new_node` | NodeGraphWidget | `self, new_node, source_port_item` | `-` | INTERNAL |
| `_create_node_at_position` | NodeGraphWidget | `self, node_type: str, identifier: str, ...` | `None` | INTERNAL |
| `_create_set_variable_for_port` | NodeGraphWidget | `self, source_port_item` | `-` | INTERNAL |
| `_delete_selected_frames` | NodeGraphWidget | `self` | `bool` | INTERNAL |
| `_fix_mmb_panning` | NodeGraphWidget | `self` | `-` | INTERNAL |
| `_handle_composite_node_creation` | NodeGraphWidget | `self, composite_node` | `None` | INTERNAL |
| `_handle_drag_enter` | NodeGraphWidget | `self, event` | `None` | INTERNAL |
| `_handle_drag_move` | NodeGraphWidget | `self, event` | `None` | INTERNAL |
| `_handle_drop` | NodeGraphWidget | `self, event` | `None` | INTERNAL |
| `_on_culling_node_created` | NodeGraphWidget | `self, node` | `None` | INTERNAL |
| `_on_culling_nodes_deleted` | NodeGraphWidget | `self, node_ids` | `None` | INTERNAL |
| `_on_culling_pipe_created` | NodeGraphWidget | `self, input_port, output_port` | `None` | INTERNAL |
| `_on_culling_pipe_deleted` | NodeGraphWidget | `self, input_port, output_port` | `None` | INTERNAL |
| `_on_node_created_check_duplicate` | NodeGraphWidget | `self, node` | `None` | INTERNAL |
| `_on_port_connected` | NodeGraphWidget | `self, input_port, output_port` | `None` | INTERNAL |
| `_on_session_changed` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `_patch_viewer_for_connection_search` | NodeGraphWidget | `self` | `-` | INTERNAL |
| `_propagate_control_flow_frame` | NodeGraphWidget | `self, source_node, target_node` | `None` | INTERNAL |
| `_setup_connection_validation` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `_setup_graph` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `_setup_paste_hook` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `_setup_viewport_culling` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `_show_connection_search` | NodeGraphWidget | `self, source_port, scene_pos` | `-` | INTERNAL |
| `_sync_visual_properties_to_casare_node` | NodeGraphWidget | `self, visual_node, casare_node` | `None` | INTERNAL |
| `_update_viewport_culling` | NodeGraphWidget | `self` | `None` | INTERNAL |
| `auto_connect` | NodeGraphWidget | `self` | `AutoConnectManager` | UNUSED |
| `center_on_nodes` | NodeGraphWidget | `self` | `None` | UNUSED |
| `clear_graph` | NodeGraphWidget | `self` | `None` | UNUSED |
| `clear_selection` | NodeGraphWidget | `self` | `None` | USED |
| `eventFilter` | NodeGraphWidget | `self, obj, event` | `-` | USED |
| `fit_to_selection` | NodeGraphWidget | `self` | `None` | USED |
| `get_selected_nodes` | NodeGraphWidget | `self` | `list` | USED |
| `graph` | NodeGraphWidget | `self` | `NodeGraph` | UNUSED |
| `is_auto_connect_enabled` | NodeGraphWidget | `self` | `bool` | UNUSED |
| `node_insert` | NodeGraphWidget | `self` | `NodeInsertManager` | UNUSED |
| `on_node_created` | NodeGraphWidget | `node` | `-` | UNUSED |
| `quick_actions` | NodeGraphWidget | `self` | `NodeQuickActions` | UNUSED |
| `reset_zoom` | NodeGraphWidget | `self` | `None` | USED |
| `selection` | NodeGraphWidget | `self` | `SelectionManager` | UNUSED |
| `set_auto_connect_distance` | NodeGraphWidget | `self, distance: float` | `None` | UNUSED |
| `set_auto_connect_enabled` | NodeGraphWidget | `self, enabled: bool` | `None` | USED |
| `set_import_callback` | NodeGraphWidget | `self, callback` | `None` | USED |
| `set_import_file_callback` | NodeGraphWidget | `self, callback` | `None` | USED |
| `setup_drag_drop` | NodeGraphWidget | `self` | `None` | USED |
| `tab_on_node_created` | NodeGraphWidget | `node` | `-` | UNUSED |
| `zoom_in` | NodeGraphWidget | `self` | `None` | UNUSED |
| `zoom_out` | NodeGraphWidget | `self` | `None` | UNUSED |


## casare_rpa.presentation.canvas.graph.node_icons

**File:** `src\casare_rpa\presentation\canvas\graph\node_icons.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `clear_icon_cache` | - | `` | `-` | UNUSED |
| `create_category_icon` | - | `category: str, size: int` | `str` | UNUSED |
| `create_node_icon` | - | `node_name: str, size: int, custom_color: Optional[QColor]` | `str` | USED |
| `create_node_icon_pixmap` | - | `node_name: str, size: int, custom_color: Optional[QColor]` | `QPixmap` | USED |
| `get_all_node_icons` | - | `` | `Dict[str, Tuple[str, str]]` | UNUSED |
| `get_cached_node_icon` | - | `node_name: str, size: int` | `QPixmap` | UNUSED |
| `get_cached_node_icon_path` | - | `node_name: str, size: int` | `str` | USED |
| `get_node_color` | - | `node_name: str` | `QColor` | UNUSED |
| `register_custom_icon` | - | `node_name: str, symbol: str, category: str` | `-` | UNUSED |


## casare_rpa.presentation.canvas.graph.node_quick_actions

**File:** `src\casare_rpa\presentation\canvas\graph\node_quick_actions.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `setup_node_quick_actions` | - | `graph: 'NodeGraph'` | `NodeQuickActions` | UNUSED |
| `__init__` | NodeQuickActions | `self, graph: 'NodeGraph', parent: Optional[QObject]` | `None` | DUNDER |
| `_get_node_at_pos` | NodeQuickActions | `self, pos: QPointF` | `-` | INTERNAL |
| `_get_selected_node_id` | NodeQuickActions | `self` | `Optional[str]` | INTERNAL |
| `_on_center_view` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_copy` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_copy_node_id` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_delete` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_duplicate` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_rename` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_run_node` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_on_run_to_node` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_setup_context_menu` | NodeQuickActions | `self` | `None` | INTERNAL |
| `_show_node_context_menu` | NodeQuickActions | `self, pos` | `None` | INTERNAL |
| `_show_rename_dialog` | NodeQuickActions | `self` | `None` | INTERNAL |
| `eventFilter` | NodeQuickActions | `self, obj, event` | `bool` | USED |
| `set_auto_connect_manager` | NodeQuickActions | `self, manager` | `None` | USED |


## casare_rpa.presentation.canvas.graph.node_registry

**File:** `src\casare_rpa\presentation\canvas\graph\node_registry.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_build_casare_node_mapping` | - | `` | `Dict[Type, Type]` | INTERNAL |
| `_build_node_type_mapping` | - | `` | `Dict[str, tuple]` | INTERNAL |
| `clear_node_type_caches` | - | `` | `None` | UNUSED |
| `create_node_from_type` | - | `graph, node_type: str, node_id: Optional[str], ...` | `Optional[Any]` | UNUSED |
| `get_all_node_types` | - | `` | `List[str]` | UNUSED |
| `get_cache_stats` | - | `` | `Dict[str, Any]` | UNUSED |
| `get_casare_class_for_type` | - | `node_type: str` | `Optional[Type]` | UNUSED |
| `get_casare_node_mapping` | - | `` | `Dict[Type, Type]` | USED |
| `get_identifier_for_type` | - | `node_type: str` | `Optional[str]` | UNUSED |
| `get_node_factory` | - | `` | `NodeFactory` | USED |
| `get_node_registry` | - | `` | `NodeRegistry` | USED |
| `get_node_type_mapping` | - | `` | `Dict[str, tuple]` | USED |
| `get_visual_class_for_type` | - | `node_type: str` | `Optional[Type]` | UNUSED |
| `is_valid_node_type` | - | `node_type: str` | `bool` | UNUSED |
| `__init__` | NodeFactory | `self` | `None` | DUNDER |
| `create_casare_node` | NodeFactory | `self, visual_node: Any` | `Optional[object]` | USED |
| `create_linked_node` | NodeFactory | `self, graph: NodeGraph, node_class: Type, ...` | `Tuple[Any, object]` | UNUSED |
| `create_visual_node` | NodeFactory | `self, graph: NodeGraph, node_class: Type, ...` | `Any` | USED |
| `__init__` | NodeRegistry | `self` | `None` | DUNDER |
| `create_node` | NodeRegistry | `` | `-` | USED |
| `create_node` | NodeRegistry | `` | `-` | USED |
| `create_node` | NodeRegistry | `` | `-` | USED |
| `get_all_nodes` | NodeRegistry | `self` | `List[Type]` | UNUSED |
| `get_all_nodes_in_category` | NodeRegistry | `self, category: str` | `List[Type]` | UNUSED |
| `get_categories` | NodeRegistry | `self` | `List[str]` | USED |
| `get_node_class` | NodeRegistry | `self, node_name: str` | `Optional[Type]` | UNUSED |
| `get_nodes_by_category` | NodeRegistry | `self, category: str` | `List[Type]` | USED |
| `get_or_create_submenu` | NodeRegistry | `parent_menu, category_path: str` | `-` | USED |
| `get_root_categories` | NodeRegistry | `self` | `List[str]` | UNUSED |
| `get_subcategories` | NodeRegistry | `self, parent: str` | `List[str]` | UNUSED |
| `make_creator` | NodeRegistry | `cls` | `-` | USED |
| `make_creator` | NodeRegistry | `cls` | `-` | USED |
| `make_creator` | NodeRegistry | `cls` | `-` | USED |
| `on_menu_shown` | NodeRegistry | `` | `-` | UNUSED |
| `on_search_changed` | NodeRegistry | `text` | `-` | UNUSED |
| `register_all_nodes` | NodeRegistry | `self, graph: NodeGraph` | `None` | USED |
| `register_node` | NodeRegistry | `self, node_class: Type, graph: Optional[NodeGraph]` | `None` | USED |
| `_auto_connect_nodes` | SearchLineEdit | `self, graph, source_node, ...` | `-` | INTERNAL |
| `_find_node_by_id` | SearchLineEdit | `self, node_id` | `-` | INTERNAL |
| `keyPressEvent` | SearchLineEdit | `self, event` | `-` | USED |


## casare_rpa.presentation.canvas.graph.node_widgets

**File:** `src\casare_rpa\presentation\canvas\graph\node_widgets.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_install_widget_init_patches` | - | `` | `None` | INTERNAL |
| `apply_all_node_widget_fixes` | - | `` | `None` | UNUSED |
| `patched_checkbox_init` | - | `self, parent, name, ...` | `-` | UNUSED |
| `patched_combo_init` | - | `self, parent, name, ...` | `-` | UNUSED |
| `_get_checkmark_path` | CasareCheckBox | `cls` | `str` | INTERNAL |
| `apply_styling` | CasareCheckBox | `cls, node_widget` | `None` | USED |
| `apply_fix` | CasareComboBox | `node_widget` | `None` | USED |
| `patched_hide_popup` | CasareComboBox | `` | `-` | UNUSED |
| `patched_show_popup` | CasareComboBox | `` | `-` | UNUSED |
| `apply_fix` | CasareLivePipe | `` | `None` | USED |
| `fixed_draw_index_pointer` | CasareLivePipe | `self, start_port, cursor_pos, ...` | `-` | UNUSED |
| `apply_fix` | CasareNodeBaseFontFix | `` | `None` | USED |
| `fixed_add_port` | CasareNodeBaseFontFix | `self, port` | `-` | UNUSED |
| `apply_fix` | CasareNodeDataDropFix | `` | `None` | USED |
| `fixed_on_node_data_dropped` | CasareNodeDataDropFix | `self, data, pos` | `-` | UNUSED |
| `apply_fix` | CasareNodeItemPaintFix | `` | `None` | USED |
| `patched_paint` | CasareNodeItemPaintFix | `self, painter, option, ...` | `-` | UNUSED |
| `apply_fix` | CasarePipeItemFix | `` | `None` | USED |
| `fixed_draw_path` | CasarePipeItemFix | `self, start_port, end_port, ...` | `-` | UNUSED |
| `apply_fix` | CasareViewerFontFix | `` | `None` | USED |
| `safe_font` | CasareViewerFontFix | `self` | `-` | UNUSED |


## casare_rpa.presentation.canvas.graph.port_shapes

**File:** `src\casare_rpa\presentation\canvas\graph\port_shapes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `draw_circle` | - | `painter: QPainter, center: QPointF, radius: float, ...` | `None` | USED |
| `draw_circle_with_dot` | - | `painter: QPainter, center: QPointF, radius: float, ...` | `None` | USED |
| `draw_diamond` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `draw_hexagon` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `draw_hollow_circle` | - | `painter: QPainter, center: QPointF, radius: float, ...` | `None` | USED |
| `draw_pentagon` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `draw_port_shape` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | UNUSED |
| `draw_rounded_square` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `draw_square` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `draw_triangle` | - | `painter: QPainter, center: QPointF, size: float, ...` | `None` | USED |
| `get_shape_description` | - | `data_type: Optional[DataType]` | `str` | UNUSED |
| `get_shape_for_type` | - | `data_type: Optional[DataType]` | `str` | UNUSED |


## casare_rpa.presentation.canvas.graph.selection_manager

**File:** `src\casare_rpa\presentation\canvas\graph\selection_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SelectionManager | `self, graph: 'NodeGraph', parent: Optional[QObject]` | `None` | DUNDER |
| `add_to_selection` | SelectionManager | `self, node` | `None` | UNUSED |
| `center_on_selection` | SelectionManager | `self` | `None` | UNUSED |
| `clear_selection` | SelectionManager | `self` | `None` | USED |
| `delete_selected_frames` | SelectionManager | `self` | `bool` | USED |
| `fit_to_selection` | SelectionManager | `self` | `None` | USED |
| `get_selected_frames` | SelectionManager | `self` | `List` | UNUSED |
| `get_selected_node_ids` | SelectionManager | `self` | `List[str]` | UNUSED |
| `get_selected_nodes` | SelectionManager | `self` | `List` | USED |
| `get_selection_count` | SelectionManager | `self` | `int` | UNUSED |
| `graph` | SelectionManager | `self` | `'NodeGraph'` | UNUSED |
| `has_selection` | SelectionManager | `self` | `bool` | UNUSED |
| `is_selected` | SelectionManager | `self, node` | `bool` | UNUSED |
| `remove_from_selection` | SelectionManager | `self, node` | `None` | UNUSED |
| `select_all` | SelectionManager | `self` | `None` | UNUSED |
| `select_node` | SelectionManager | `self, node` | `None` | UNUSED |
| `select_nodes` | SelectionManager | `self, nodes: List` | `None` | USED |
| `select_nodes_in_frame` | SelectionManager | `self, frame` | `None` | UNUSED |
| `toggle_selection` | SelectionManager | `self, node` | `None` | UNUSED |


## casare_rpa.presentation.canvas.graph.style_manager

**File:** `src\casare_rpa\presentation\canvas\graph\style_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_background_color` | CollapseButtonStyle | `cls, is_hovered: bool` | `QColor` | USED |
| `create_frame_brush` | FrameStyleManager | `color: QColor` | `QBrush` | USED |
| `create_frame_pen` | FrameStyleManager | `color: QColor, width: int, style: Qt.PenStyle, ...` | `QPen` | USED |
| `get_collapsed_brush` | FrameStyleManager | `color: QColor` | `QBrush` | USED |
| `get_collapsed_pen` | FrameStyleManager | `color: QColor` | `QPen` | USED |
| `get_drop_target_brush` | FrameStyleManager | `` | `QBrush` | USED |
| `get_drop_target_pen` | FrameStyleManager | `` | `QPen` | USED |
| `get_frame_color` | FrameStyleManager | `color_name: str` | `QColor` | UNUSED |
| `get_node_count_color` | FrameStyleManager | `frame_color: QColor` | `QColor` | USED |
| `get_port_color` | FrameStyleManager | `port` | `QColor` | USED |
| `get_selection_pen` | FrameStyleManager | `` | `QPen` | USED |
| `get_title_color` | FrameStyleManager | `` | `QColor` | USED |


## casare_rpa.presentation.canvas.graph.viewport_culling

**File:** `src\casare_rpa\presentation\canvas\graph\viewport_culling.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_on_node_created` | - | `culler: ViewportCullingManager, node` | `None` | INTERNAL |
| `_on_nodes_deleted` | - | `culler: ViewportCullingManager, node_ids: List[str]` | `None` | INTERNAL |
| `create_viewport_culler_for_graph` | - | `graph_widget, cell_size: int, margin: int` | `ViewportCullingManager` | UNUSED |
| `__init__` | SpatialHash | `self, cell_size: int` | `-` | DUNDER |
| `_get_cells_for_rect` | SpatialHash | `self, rect: QRectF` | `Set[Tuple[int, int]]` | INTERNAL |
| `cell_count` | SpatialHash | `self` | `int` | UNUSED |
| `clear` | SpatialHash | `self` | `None` | USED |
| `insert` | SpatialHash | `self, node_id: str, rect: QRectF` | `None` | USED |
| `node_count` | SpatialHash | `self` | `int` | UNUSED |
| `query` | SpatialHash | `self, rect: QRectF` | `Set[str]` | USED |
| `remove` | SpatialHash | `self, node_id: str` | `None` | USED |
| `__init__` | ViewportCullingManager | `self, cell_size: int, margin: int, ...` | `-` | DUNDER |
| `_apply_visibility_changes` | ViewportCullingManager | `self, show_ids: Set[str], hide_ids: Set[str]` | `None` | INTERNAL |
| `_show_all_nodes` | ViewportCullingManager | `self` | `None` | INTERNAL |
| `_show_all_pipes` | ViewportCullingManager | `self` | `None` | INTERNAL |
| `_update_pipe_visibility` | ViewportCullingManager | `self` | `int` | INTERNAL |
| `clear` | ViewportCullingManager | `self` | `None` | USED |
| `get_stats` | ViewportCullingManager | `self` | `Dict` | USED |
| `get_visible_nodes` | ViewportCullingManager | `self` | `Set[str]` | UNUSED |
| `is_enabled` | ViewportCullingManager | `self` | `bool` | USED |
| `register_node` | ViewportCullingManager | `self, node_id: str, node_item: object, ...` | `None` | USED |
| `register_pipe` | ViewportCullingManager | `self, pipe_id: str, source_node_id: str, ...` | `None` | USED |
| `set_enabled` | ViewportCullingManager | `self, enabled: bool` | `None` | USED |
| `unregister_node` | ViewportCullingManager | `self, node_id: str` | `None` | USED |
| `unregister_pipe` | ViewportCullingManager | `self, pipe_id: str` | `None` | USED |
| `update_node_position` | ViewportCullingManager | `self, node_id: str, rect: QRectF` | `None` | UNUSED |
| `update_viewport` | ViewportCullingManager | `self, viewport_rect: QRectF` | `Tuple[Set[str], Set[str]]` | USED |


## casare_rpa.presentation.canvas.initializers.controller_registrar

**File:** `src\casare_rpa\presentation\canvas\initializers\controller_registrar.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ControllerRegistrar | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_connect_controller_signals` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_connect_execution_signals` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_connect_node_signals` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_connect_panel_signals` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_connect_workflow_signals` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_initialize_controllers` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_on_current_file_changed` | ControllerRegistrar | `self, file: Optional[Path]` | `None` | INTERNAL |
| `_on_execution_completed` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_on_execution_error` | ControllerRegistrar | `self, error: str` | `None` | INTERNAL |
| `_on_execution_started` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_on_execution_stopped` | ControllerRegistrar | `self` | `None` | INTERNAL |
| `_on_modified_changed` | ControllerRegistrar | `self, modified: bool` | `None` | INTERNAL |
| `cleanup_all` | ControllerRegistrar | `self` | `None` | USED |
| `register_all` | ControllerRegistrar | `self` | `None` | USED |
| `set_external_controllers` | ControllerRegistrar | `self, workflow_controller: 'WorkflowController', execution_controller: 'ExecutionController', ...` | `None` | USED |


## casare_rpa.presentation.canvas.initializers.ui_component_initializer

**File:** `src\casare_rpa\presentation\canvas\initializers\ui_component_initializer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | UIComponentInitializer | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_create_debug_components` | UIComponentInitializer | `self` | `None` | INTERNAL |
| `_find_view_menu` | UIComponentInitializer | `self` | `Optional['QMenu']` | INTERNAL |
| `_setup_validation_timer` | UIComponentInitializer | `self` | `None` | INTERNAL |
| `cleanup` | UIComponentInitializer | `self` | `None` | USED |
| `ensure_normal_components_loaded` | UIComponentInitializer | `self` | `None` | USED |
| `is_normal_loaded` | UIComponentInitializer | `self` | `bool` | UNUSED |
| `load_normal_components` | UIComponentInitializer | `self` | `None` | USED |
| `schedule_deferred_load` | UIComponentInitializer | `self, delay_ms: int` | `None` | USED |


## casare_rpa.presentation.canvas.main_window

**File:** `src\casare_rpa\presentation\canvas\main_window.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MainWindow | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_cleanup_controllers` | MainWindow | `self` | `None` | INTERNAL |
| `_create_minimap` | MainWindow | `self, node_graph` | `None` | INTERNAL |
| `_do_deferred_validation` | MainWindow | `self` | `None` | INTERNAL |
| `_find_view_menu` | MainWindow | `self` | `-` | INTERNAL |
| `_get_or_create_command_palette` | MainWindow | `self` | `'CommandPalette'` | INTERNAL |
| `_get_workflow_data` | MainWindow | `self` | `Optional[dict]` | INTERNAL |
| `_init_controllers` | MainWindow | `self` | `None` | INTERNAL |
| `_load_auto_connect_preference` | MainWindow | `self` | `None` | INTERNAL |
| `_load_normal_components` | MainWindow | `self` | `None` | INTERNAL |
| `_on_about` | MainWindow | `self` | `None` | INTERNAL |
| `_on_check_updates` | MainWindow | `self` | `None` | INTERNAL |
| `_on_clear_breakpoints` | MainWindow | `self` | `None` | INTERNAL |
| `_on_clear_recent_files` | MainWindow | `self` | `None` | INTERNAL |
| `_on_create_frame` | MainWindow | `self` | `None` | INTERNAL |
| `_on_credential_manager` | MainWindow | `self` | `None` | INTERNAL |
| `_on_credentials_changed` | MainWindow | `self` | `None` | INTERNAL |
| `_on_debug_continue` | MainWindow | `self` | `None` | INTERNAL |
| `_on_debug_mode_toggled` | MainWindow | `self, enabled: bool` | `None` | INTERNAL |
| `_on_debug_step_into` | MainWindow | `self` | `None` | INTERNAL |
| `_on_debug_step_out` | MainWindow | `self` | `None` | INTERNAL |
| `_on_debug_step_over` | MainWindow | `self` | `None` | INTERNAL |
| `_on_debug_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_disable_all_selected` | MainWindow | `self` | `None` | INTERNAL |
| `_on_export_selected` | MainWindow | `self` | `None` | INTERNAL |
| `_on_find_node` | MainWindow | `self` | `None` | INTERNAL |
| `_on_fleet_dashboard` | MainWindow | `self` | `None` | INTERNAL |
| `_on_get_exec_out` | MainWindow | `self` | `None` | INTERNAL |
| `_on_import_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_manage_schedules` | MainWindow | `self` | `None` | INTERNAL |
| `_on_navigate_to_node` | MainWindow | `self, node_id: str` | `None` | INTERNAL |
| `_on_new_from_template` | MainWindow | `self` | `None` | INTERNAL |
| `_on_new_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_open_command_palette` | MainWindow | `self` | `None` | INTERNAL |
| `_on_open_desktop_selector_builder` | MainWindow | `self` | `None` | INTERNAL |
| `_on_open_hotkey_manager` | MainWindow | `self` | `None` | INTERNAL |
| `_on_open_performance_dashboard` | MainWindow | `self` | `None` | INTERNAL |
| `_on_open_recent_file` | MainWindow | `self, path: str` | `None` | INTERNAL |
| `_on_open_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_panel_variables_changed` | MainWindow | `self, variables: dict` | `None` | INTERNAL |
| `_on_paste_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_pause_workflow` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_pick_selector` | MainWindow | `self` | `None` | INTERNAL |
| `_on_preferences` | MainWindow | `self` | `None` | INTERNAL |
| `_on_project_manager` | MainWindow | `self` | `None` | INTERNAL |
| `_on_property_panel_changed` | MainWindow | `self, node_id: str, prop_name: str, ...` | `None` | INTERNAL |
| `_on_run_all_workflows` | MainWindow | `self` | `None` | INTERNAL |
| `_on_run_local` | MainWindow | `self` | `None` | INTERNAL |
| `_on_run_on_robot` | MainWindow | `self` | `None` | INTERNAL |
| `_on_run_scheduled_workflow` | MainWindow | `self, schedule` | `None` | INTERNAL |
| `_on_run_single_node` | MainWindow | `self` | `None` | INTERNAL |
| `_on_run_to_node` | MainWindow | `self` | `None` | INTERNAL |
| `_on_run_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_save_as_scenario` | MainWindow | `self` | `None` | INTERNAL |
| `_on_save_as_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_save_ui_layout` | MainWindow | `self` | `None` | INTERNAL |
| `_on_save_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_schedule_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_select_nearest_node` | MainWindow | `self` | `None` | INTERNAL |
| `_on_show_documentation` | MainWindow | `self` | `None` | INTERNAL |
| `_on_show_keyboard_shortcuts` | MainWindow | `self` | `None` | INTERNAL |
| `_on_start_listening` | MainWindow | `self` | `None` | INTERNAL |
| `_on_stop_listening` | MainWindow | `self` | `None` | INTERNAL |
| `_on_stop_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_submit` | MainWindow | `self` | `None` | INTERNAL |
| `_on_toggle_auto_connect` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_bottom_panel` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_breakpoint` | MainWindow | `self` | `None` | INTERNAL |
| `_on_toggle_disable_node` | MainWindow | `self` | `None` | INTERNAL |
| `_on_toggle_minimap` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_panel` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_properties` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_recording` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_toggle_variable_inspector` | MainWindow | `self, checked: bool` | `None` | INTERNAL |
| `_on_validate_workflow` | MainWindow | `self` | `None` | INTERNAL |
| `_on_validation_issue_clicked` | MainWindow | `self, location: str` | `None` | INTERNAL |
| `_position_minimap` | MainWindow | `self` | `None` | INTERNAL |
| `_register_command_palette_actions` | MainWindow | `self` | `None` | INTERNAL |
| `_schedule_ui_state_save` | MainWindow | `self` | `None` | INTERNAL |
| `_select_node_by_id` | MainWindow | `self, node_id: str` | `None` | INTERNAL |
| `_setup_window` | MainWindow | `self` | `None` | INTERNAL |
| `_toggle_panel_tab` | MainWindow | `self, tab_name: str` | `None` | INTERNAL |
| `_update_actions` | MainWindow | `self` | `None` | INTERNAL |
| `_update_status_bar_buttons` | MainWindow | `self` | `None` | INTERNAL |
| `add_to_recent_files` | MainWindow | `self, file_path` | `None` | USED |
| `bottom_panel` | MainWindow | `self` | `Optional['BottomPanelDock']` | UNUSED |
| `closeEvent` | MainWindow | `self, event` | `None` | USED |
| `command_palette` | MainWindow | `self` | `-` | UNUSED |
| `ensure_normal_components_loaded` | MainWindow | `self` | `None` | USED |
| `execution_timeline` | MainWindow | `self` | `Optional['ExecutionTimeline']` | UNUSED |
| `get_bottom_panel` | MainWindow | `self` | `Optional['BottomPanelDock']` | USED |
| `get_command_palette` | MainWindow | `self` | `-` | USED |
| `get_current_file` | MainWindow | `self` | `Optional[Path]` | USED |
| `get_execution_history_viewer` | MainWindow | `self` | `-` | UNUSED |
| `get_execution_timeline` | MainWindow | `self` | `Optional['ExecutionTimeline']` | USED |
| `get_graph` | MainWindow | `self` | `-` | USED |
| `get_log_viewer` | MainWindow | `self` | `-` | USED |
| `get_minimap` | MainWindow | `self` | `-` | USED |
| `get_node_controller` | MainWindow | `self` | `-` | USED |
| `get_node_registry` | MainWindow | `self` | `-` | USED |
| `get_process_mining_panel` | MainWindow | `self` | `-` | UNUSED |
| `get_project_controller` | MainWindow | `self` | `-` | USED |
| `get_properties_panel` | MainWindow | `self` | `Optional['PropertiesPanel']` | USED |
| `get_recent_files_menu` | MainWindow | `self` | `-` | USED |
| `get_robot_controller` | MainWindow | `self` | `-` | UNUSED |
| `get_robot_picker_panel` | MainWindow | `self` | `-` | UNUSED |
| `get_scheduling_controller` | MainWindow | `self` | `-` | UNUSED |
| `get_ui_state_controller` | MainWindow | `self` | `Optional['UIStateController']` | UNUSED |
| `get_validation_panel` | MainWindow | `self` | `-` | USED |
| `get_variable_inspector` | MainWindow | `self` | `-` | UNUSED |
| `get_variable_inspector_dock` | MainWindow | `self` | `-` | USED |
| `get_viewport_controller` | MainWindow | `self` | `-` | UNUSED |
| `get_workflow_runner` | MainWindow | `self` | `-` | UNUSED |
| `graph` | MainWindow | `self` | `-` | UNUSED |
| `hide_bottom_panel` | MainWindow | `self` | `None` | USED |
| `hide_log_viewer` | MainWindow | `self` | `None` | UNUSED |
| `hide_minimap` | MainWindow | `self` | `None` | USED |
| `hide_validation_panel` | MainWindow | `self` | `None` | UNUSED |
| `is_auto_connect_enabled` | MainWindow | `self` | `bool` | UNUSED |
| `is_auto_validate_enabled` | MainWindow | `self` | `bool` | UNUSED |
| `is_modified` | MainWindow | `self` | `bool` | UNUSED |
| `minimap` | MainWindow | `self` | `-` | UNUSED |
| `node_controller` | MainWindow | `self` | `-` | UNUSED |
| `node_registry` | MainWindow | `self` | `-` | UNUSED |
| `on_workflow_changed` | MainWindow | `self` | `None` | USED |
| `process_mining_panel` | MainWindow | `self` | `-` | UNUSED |
| `properties_panel` | MainWindow | `self` | `Optional['PropertiesPanel']` | UNUSED |
| `recent_files_menu` | MainWindow | `self` | `-` | UNUSED |
| `reset_ui_state` | MainWindow | `self` | `None` | UNUSED |
| `resizeEvent` | MainWindow | `self, event` | `-` | USED |
| `robot_picker_panel` | MainWindow | `self` | `-` | UNUSED |
| `scheduling_controller` | MainWindow | `self` | `-` | UNUSED |
| `set_auto_validate` | MainWindow | `self, enabled: bool` | `None` | UNUSED |
| `set_browser_running` | MainWindow | `self, running: bool` | `None` | USED |
| `set_central_widget` | MainWindow | `self, widget: QWidget` | `None` | USED |
| `set_controllers` | MainWindow | `self, workflow_controller, execution_controller, ...` | `None` | USED |
| `set_current_file` | MainWindow | `self, file_path: Optional[Path]` | `None` | USED |
| `set_execution_status` | MainWindow | `self, status: str` | `None` | USED |
| `set_modified` | MainWindow | `self, modified: bool` | `None` | USED |
| `set_workflow_data_provider` | MainWindow | `self, provider: callable` | `None` | USED |
| `showEvent` | MainWindow | `self, event` | `None` | USED |
| `show_bottom_panel` | MainWindow | `self` | `None` | USED |
| `show_execution_history` | MainWindow | `self` | `None` | UNUSED |
| `show_log_viewer` | MainWindow | `self` | `None` | UNUSED |
| `show_minimap` | MainWindow | `self` | `None` | USED |
| `show_status` | MainWindow | `self, message: str, duration: int` | `None` | USED |
| `show_validation_panel` | MainWindow | `self` | `None` | USED |
| `show_variable_inspector` | MainWindow | `self` | `None` | USED |
| `trigger_workflow_run` | MainWindow | `self` | `None` | UNUSED |
| `update_node_count` | MainWindow | `self, count: int` | `None` | USED |
| `update_properties_panel` | MainWindow | `self, node` | `None` | UNUSED |
| `update_zoom_display` | MainWindow | `self, zoom_percent: float` | `None` | USED |
| `validate_current_workflow` | MainWindow | `self, show_panel: bool` | `'ValidationResult'` | USED |
| `validation_panel` | MainWindow | `self` | `-` | UNUSED |
| `variable_inspector_dock` | MainWindow | `self` | `-` | UNUSED |
| `viewport_controller` | MainWindow | `self` | `-` | UNUSED |
| `workflow_runner` | MainWindow | `self` | `-` | UNUSED |


## casare_rpa.presentation.canvas.port_type_system

**File:** `src\casare_rpa\presentation\canvas\port_type_system.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_port_type_registry` | - | `` | `PortTypeRegistry` | USED |
| `get_type_color` | - | `data_type: DataType` | `Tuple[int, int, int, int]` | USED |
| `is_types_compatible` | - | `source: DataType, target: DataType` | `bool` | UNUSED |
| `get_incompatibility_reason` | DefaultCompatibilityRule | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `is_compatible` | DefaultCompatibilityRule | `self, source: DataType, target: DataType` | `bool` | USED |
| `__new__` | PortTypeRegistry | `cls` | `'PortTypeRegistry'` | DUNDER |
| `_initialize` | PortTypeRegistry | `self` | `None` | INTERNAL |
| `_register_default_types` | PortTypeRegistry | `self` | `None` | INTERNAL |
| `get_compatible_types` | PortTypeRegistry | `self, source: DataType` | `Set[DataType]` | UNUSED |
| `get_exec_color` | PortTypeRegistry | `self` | `Tuple[int, int, int, int]` | USED |
| `get_incompatibility_reason` | PortTypeRegistry | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `get_type_color` | PortTypeRegistry | `self, data_type: DataType` | `Tuple[int, int, int, int]` | USED |
| `get_type_info` | PortTypeRegistry | `self, data_type: DataType` | `PortTypeInfo` | USED |
| `get_type_shape` | PortTypeRegistry | `self, data_type: DataType` | `PortShape` | USED |
| `is_compatible` | PortTypeRegistry | `self, source: DataType, target: DataType` | `bool` | USED |
| `set_compatibility_rule` | PortTypeRegistry | `self, rule: TypeCompatibilityRule` | `None` | UNUSED |
| `get_incompatibility_reason` | TypeCompatibilityRule | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `is_compatible` | TypeCompatibilityRule | `self, source: DataType, target: DataType` | `bool` | USED |


## casare_rpa.presentation.canvas.resources

**File:** `src\casare_rpa\presentation\canvas\resources.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_cached_icon` | - | `path: str` | `'QIcon'` | UNUSED |
| `get_cached_pixmap` | - | `path: str, width: int, height: int` | `'QPixmap'` | UNUSED |
| `_evict_icons_if_needed` | ResourceCache | `cls` | `None` | INTERNAL |
| `_evict_pixmaps_if_needed` | ResourceCache | `cls` | `None` | INTERNAL |
| `clear` | ResourceCache | `cls` | `None` | USED |
| `get_icon` | ResourceCache | `cls, path: str` | `'QIcon'` | USED |
| `get_pixmap` | ResourceCache | `cls, path: str, width: int, ...` | `'QPixmap'` | USED |
| `get_stats` | ResourceCache | `cls` | `Dict[str, int]` | USED |
| `preload_icons` | ResourceCache | `cls, paths: list` | `None` | UNUSED |


## casare_rpa.presentation.canvas.search.command_palette

**File:** `src\casare_rpa\presentation\canvas\search\command_palette.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CommandPalette | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | CommandPalette | `self` | `None` | INTERNAL |
| `_calculate_match_score` | CommandPalette | `self, query: str, text: str` | `int` | INTERNAL |
| `_execute_selected` | CommandPalette | `self` | `None` | INTERNAL |
| `_filter_commands` | CommandPalette | `self, query: str` | `None` | INTERNAL |
| `_move_selection` | CommandPalette | `self, delta: int` | `None` | INTERNAL |
| `_on_item_clicked` | CommandPalette | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_item_double_clicked` | CommandPalette | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_search_changed` | CommandPalette | `self, text: str` | `None` | INTERNAL |
| `_setup_ui` | CommandPalette | `self` | `None` | INTERNAL |
| `_update_results_list` | CommandPalette | `self` | `None` | INTERNAL |
| `clear_commands` | CommandPalette | `self` | `None` | UNUSED |
| `eventFilter` | CommandPalette | `self, obj, event` | `bool` | USED |
| `keyPressEvent` | CommandPalette | `self, event: QKeyEvent` | `None` | USED |
| `register_action` | CommandPalette | `self, action: QAction, category: str, ...` | `None` | USED |
| `register_callback` | CommandPalette | `self, name: str, callback: Callable, ...` | `None` | UNUSED |
| `show_palette` | CommandPalette | `self` | `None` | USED |


## casare_rpa.presentation.canvas.search.node_search

**File:** `src\casare_rpa\presentation\canvas\search\node_search.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeSearchDialog | `self, graph: 'NodeGraph', parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `_execute_selected` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `_filter_nodes` | NodeSearchDialog | `self, query: str` | `None` | INTERNAL |
| `_load_nodes` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `_move_selection` | NodeSearchDialog | `self, delta: int` | `None` | INTERNAL |
| `_on_item_clicked` | NodeSearchDialog | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_item_double_clicked` | NodeSearchDialog | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_search_changed` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `_select_and_center_node` | NodeSearchDialog | `self, node_id: str` | `None` | INTERNAL |
| `_setup_ui` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `_update_results` | NodeSearchDialog | `self` | `None` | INTERNAL |
| `eventFilter` | NodeSearchDialog | `self, obj, event` | `bool` | USED |
| `keyPressEvent` | NodeSearchDialog | `self, event: QKeyEvent` | `None` | USED |
| `show_search` | NodeSearchDialog | `self` | `None` | USED |


## casare_rpa.presentation.canvas.search.node_search_dialog

**File:** `src\casare_rpa\presentation\canvas\search\node_search_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeSearchDialog | `self, parent: Optional[QWidget]` | `-` | DUNDER |
| `_do_search` | NodeSearchDialog | `self` | `-` | INTERNAL |
| `_on_item_selected` | NodeSearchDialog | `self, item: QListWidgetItem` | `-` | INTERNAL |
| `_on_search_changed` | NodeSearchDialog | `self, text: str` | `-` | INTERNAL |
| `_setup_ui` | NodeSearchDialog | `self` | `-` | INTERNAL |
| `_update_results` | NodeSearchDialog | `self, query: str` | `-` | INTERNAL |
| `keyPressEvent` | NodeSearchDialog | `self, event: QKeyEvent` | `-` | USED |
| `set_node_items` | NodeSearchDialog | `self, items: List[Tuple[str, str, str]]` | `-` | UNUSED |
| `showEvent` | NodeSearchDialog | `self, event` | `-` | USED |


## casare_rpa.presentation.canvas.search.searchable_menu

**File:** `src\casare_rpa\presentation\canvas\search\searchable_menu.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SearchableNodeMenu | `self, title: str, parent` | `-` | DUNDER |
| `_execute_first_visible_item` | SearchableNodeMenu | `self, auto_connect: bool` | `-` | INTERNAL |
| `_focus_first_visible_item` | SearchableNodeMenu | `self` | `-` | INTERNAL |
| `_on_search_changed` | SearchableNodeMenu | `self, text: str` | `-` | INTERNAL |
| `_show_all_items` | SearchableNodeMenu | `self` | `-` | INTERNAL |
| `add_node_item` | SearchableNodeMenu | `self, category: str, name: str, ...` | `-` | UNUSED |
| `build_menu` | SearchableNodeMenu | `self` | `-` | UNUSED |
| `eventFilter` | SearchableNodeMenu | `self, obj, event` | `-` | USED |
| `setup_search` | SearchableNodeMenu | `self` | `-` | UNUSED |
| `showEvent` | SearchableNodeMenu | `self, event` | `-` | USED |


## casare_rpa.presentation.canvas.selectors.desktop_selector_builder

**File:** `src\casare_rpa\presentation\canvas\selectors\desktop_selector_builder.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DesktopSelectorBuilder | `self, parent, target_node, ...` | `-` | DUNDER |
| `_apply_styles` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_connect_signals` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_create_editor_group` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_footer` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_header` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_left_panel` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_properties_group` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_right_panel` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_create_selectors_group` | DesktopSelectorBuilder | `self` | `QWidget` | INTERNAL |
| `_generate_selectors` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_load_desktop_root` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_on_copy_json` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_on_pick_element` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_on_refresh` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_on_selector_changed` | DesktopSelectorBuilder | `self, current: QListWidgetItem, previous: QListWidgetItem` | `-` | INTERNAL |
| `_on_tree_element_selected` | DesktopSelectorBuilder | `self, element: DesktopElement` | `-` | INTERNAL |
| `_on_use_selector` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_on_validate_all` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_setup_ui` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_update_for_selected_element` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_update_properties_table` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_update_selectors_list` | DesktopSelectorBuilder | `self` | `-` | INTERNAL |
| `_update_validation_status` | DesktopSelectorBuilder | `self, strategy: SelectorStrategy` | `-` | INTERNAL |
| `get_selected_selector` | DesktopSelectorBuilder | `self` | `Optional[Dict[str, Any]]` | USED |
| `on_cancelled` | DesktopSelectorBuilder | `` | `-` | UNUSED |
| `on_element_selected` | DesktopSelectorBuilder | `element: DesktopElement` | `-` | UNUSED |


## casare_rpa.presentation.canvas.selectors.element_picker

**File:** `src\casare_rpa\presentation\canvas\selectors\element_picker.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `activate_element_picker` | - | `callback_on_select, callback_on_cancel` | `-` | USED |
| `__init__` | ElementPickerOverlay | `self, parent` | `-` | DUNDER |
| `_is_overlay_or_child` | ElementPickerOverlay | `self, control: auto.Control` | `bool` | INTERNAL |
| `_setup_ui` | ElementPickerOverlay | `self` | `-` | INTERNAL |
| `_start_tracking` | ElementPickerOverlay | `self` | `-` | INTERNAL |
| `_update_element_info` | ElementPickerOverlay | `self, element: DesktopElement` | `-` | INTERNAL |
| `_update_hover_element` | ElementPickerOverlay | `self` | `-` | INTERNAL |
| `closeEvent` | ElementPickerOverlay | `self, event` | `-` | USED |
| `keyPressEvent` | ElementPickerOverlay | `self, event` | `-` | USED |
| `mousePressEvent` | ElementPickerOverlay | `self, event` | `-` | USED |
| `paintEvent` | ElementPickerOverlay | `self, event` | `-` | UNUSED |


## casare_rpa.presentation.canvas.selectors.element_tree_widget

**File:** `src\casare_rpa\presentation\canvas\selectors\element_tree_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ElementTreeItem | `self, element: DesktopElement, parent` | `-` | DUNDER |
| `_apply_styling` | ElementTreeItem | `self, element: DesktopElement` | `-` | INTERNAL |
| `_may_have_children` | ElementTreeItem | `self, element: DesktopElement` | `bool` | INTERNAL |
| `_set_control_type_icon` | ElementTreeItem | `self, control_type: str` | `-` | INTERNAL |
| `load_children` | ElementTreeItem | `self` | `-` | USED |
| `__init__` | ElementTreeWidget | `self, parent` | `-` | DUNDER |
| `_apply_styles` | ElementTreeWidget | `self` | `-` | INTERNAL |
| `_filter_items` | ElementTreeWidget | `self, search_text: str` | `-` | INTERNAL |
| `_has_matching_child` | ElementTreeWidget | `self, item: QTreeWidgetItem, search_text: str` | `bool` | INTERNAL |
| `_on_item_expanded` | ElementTreeWidget | `self, item: QTreeWidgetItem` | `-` | INTERNAL |
| `_on_search_changed` | ElementTreeWidget | `self, text: str` | `-` | INTERNAL |
| `_on_selection_changed` | ElementTreeWidget | `self` | `-` | INTERNAL |
| `_setup_ui` | ElementTreeWidget | `self` | `-` | INTERNAL |
| `_show_all_items` | ElementTreeWidget | `self` | `-` | INTERNAL |
| `expand_to_element` | ElementTreeWidget | `self, target_element: DesktopElement` | `None` | UNUSED |
| `get_selected_element` | ElementTreeWidget | `self` | `Optional[DesktopElement]` | UNUSED |
| `load_tree` | ElementTreeWidget | `self, root_element: DesktopElement` | `-` | USED |
| `refresh` | ElementTreeWidget | `self` | `-` | USED |


## casare_rpa.presentation.canvas.selectors.selector_dialog

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SelectorDialog | `self, fingerprint: ElementFingerprint, test_callback: Optional[Callable], ...` | `-` | DUNDER |
| `_create_details_panel` | SelectorDialog | `self` | `QWidget` | INTERNAL |
| `_create_footer` | SelectorDialog | `self` | `QWidget` | INTERNAL |
| `_create_header` | SelectorDialog | `self` | `QWidget` | INTERNAL |
| `_create_selectors_panel` | SelectorDialog | `self` | `QWidget` | INTERNAL |
| `_do_test` | SelectorDialog | `self, selector_value: str, selector_type: str` | `-` | INTERNAL |
| `_on_copy_selector` | SelectorDialog | `self` | `-` | INTERNAL |
| `_on_highlight_selector` | SelectorDialog | `self` | `-` | INTERNAL |
| `_on_selector_changed` | SelectorDialog | `self, current: QListWidgetItem, previous: QListWidgetItem` | `-` | INTERNAL |
| `_on_test_selector` | SelectorDialog | `self` | `-` | INTERNAL |
| `_on_use_selector` | SelectorDialog | `self` | `-` | INTERNAL |
| `apply_styles` | SelectorDialog | `self` | `-` | USED |
| `get_selected_selector` | SelectorDialog | `self` | `tuple[str, str]` | USED |
| `populate_data` | SelectorDialog | `self` | `-` | USED |
| `setup_ui` | SelectorDialog | `self` | `-` | USED |


## casare_rpa.presentation.canvas.selectors.selector_integration

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_integration.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SelectorIntegration | `self, parent` | `-` | DUNDER |
| `_handle_dialog_action` | SelectorIntegration | `self, selector_value: str, action: str` | `-` | INTERNAL |
| `_handle_element_selected` | SelectorIntegration | `self, fingerprint: ElementFingerprint` | `-` | INTERNAL |
| `_handle_recording_complete` | SelectorIntegration | `self, actions: list` | `-` | INTERNAL |
| `_update_node_property` | SelectorIntegration | `self, selector_value: str` | `-` | INTERNAL |
| `async initialize_for_page` | SelectorIntegration | `self, page` | `-` | USED |
| `is_active` | SelectorIntegration | `self` | `bool` | USED |
| `is_picking` | SelectorIntegration | `self` | `bool` | UNUSED |
| `is_recording` | SelectorIntegration | `self` | `bool` | USED |
| `async start_picking` | SelectorIntegration | `self, target_node, target_property: str` | `-` | USED |
| `async start_recording` | SelectorIntegration | `self` | `-` | USED |
| `async stop_selector_mode` | SelectorIntegration | `self` | `-` | USED |
| `test_callback` | SelectorIntegration | `selector_value: str, selector_type: str` | `Dict[str, Any]` | USED |


## casare_rpa.presentation.canvas.selectors.selector_strategy

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_strategy.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_calculate_element_index` | - | `element: DesktopElement, parent_control: auto.Control, control_type: str` | `int` | INTERNAL |
| `_generate_path_selector` | - | `element: DesktopElement` | `str` | INTERNAL |
| `filter_best_selectors` | - | `strategies: List[SelectorStrategy], max_count: int` | `List[SelectorStrategy]` | USED |
| `generate_selectors` | - | `element: DesktopElement, parent_control: Optional[auto.Control]` | `List[SelectorStrategy]` | USED |
| `validate_selector_uniqueness` | - | `selector: SelectorStrategy, parent_control: auto.Control, timeout: float` | `bool` | USED |
| `to_dict` | SelectorStrategy | `self` | `Dict[str, Any]` | USED |


## casare_rpa.presentation.canvas.selectors.selector_validator

**File:** `src\casare_rpa\presentation\canvas\selectors\selector_validator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `validate_selector_sync` | - | `selector: Dict[str, Any], parent_control: Optional[auto.Control]` | `ValidationResult` | UNUSED |
| `__init__` | SelectorValidator | `self, parent_control: Optional[auto.Control]` | `-` | DUNDER |
| `get_element_at_position` | SelectorValidator | `self, x: int, y: int` | `Optional[DesktopElement]` | UNUSED |
| `highlight_matches` | SelectorValidator | `self, selector: Dict[str, Any], max_count: int` | `-` | USED |
| `quick_check` | SelectorValidator | `self, selector: Dict[str, Any]` | `bool` | UNUSED |
| `validate` | SelectorValidator | `self, selector: Dict[str, Any], find_all: bool` | `ValidationResult` | USED |
| `validate_multiple` | SelectorValidator | `self, selectors: List[Dict[str, Any]]` | `List[ValidationResult]` | UNUSED |
| `color` | ValidationResult | `self` | `str` | UNUSED |
| `icon` | ValidationResult | `self` | `str` | UNUSED |
| `is_unique` | ValidationResult | `self` | `bool` | UNUSED |
| `is_valid` | ValidationResult | `self` | `bool` | UNUSED |
| `message` | ValidationResult | `self` | `str` | UNUSED |


## casare_rpa.presentation.canvas.serialization.workflow_deserializer

**File:** `src\casare_rpa\presentation\canvas\serialization\workflow_deserializer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowDeserializer | `self, graph: 'NodeGraph', main_window` | `-` | DUNDER |
| `_apply_config` | WorkflowDeserializer | `self, visual_node, config: Dict` | `None` | INTERNAL |
| `_build_node_type_map` | WorkflowDeserializer | `self` | `Dict[str, str]` | INTERNAL |
| `_create_connections` | WorkflowDeserializer | `self, connections: List[Dict], node_map: Dict` | `int` | INTERNAL |
| `_create_node` | WorkflowDeserializer | `self, node_id: str, node_data: Dict` | `Optional[Any]` | INTERNAL |
| `_find_node_identifier` | WorkflowDeserializer | `self, node_type: str` | `Optional[str]` | INTERNAL |
| `_get_node_type_map` | WorkflowDeserializer | `self` | `Dict[str, str]` | INTERNAL |
| `_has_property` | WorkflowDeserializer | `self, visual_node, prop_name: str` | `bool` | INTERNAL |
| `_restore_frames` | WorkflowDeserializer | `self, frames: List[Dict], node_map: Dict` | `None` | INTERNAL |
| `_restore_variables` | WorkflowDeserializer | `self, variables: Dict` | `None` | INTERNAL |
| `deserialize` | WorkflowDeserializer | `self, workflow_data: Dict` | `bool` | USED |
| `load_from_file` | WorkflowDeserializer | `self, file_path: str` | `bool` | USED |


## casare_rpa.presentation.canvas.serialization.workflow_serializer

**File:** `src\casare_rpa\presentation\canvas\serialization\workflow_serializer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowSerializer | `self, graph: 'NodeGraph', main_window: 'MainWindow'` | `-` | DUNDER |
| `_get_metadata` | WorkflowSerializer | `self` | `Dict[str, str]` | INTERNAL |
| `_get_settings` | WorkflowSerializer | `self` | `Dict[str, Any]` | INTERNAL |
| `_get_variables` | WorkflowSerializer | `self` | `Dict[str, dict]` | INTERNAL |
| `_serialize_connections` | WorkflowSerializer | `self` | `List[dict]` | INTERNAL |
| `_serialize_frames` | WorkflowSerializer | `self` | `List[dict]` | INTERNAL |
| `_serialize_node` | WorkflowSerializer | `self, visual_node` | `Optional[dict]` | INTERNAL |
| `_serialize_nodes` | WorkflowSerializer | `self` | `Dict[str, dict]` | INTERNAL |
| `serialize` | WorkflowSerializer | `self` | `dict` | USED |


## casare_rpa.presentation.canvas.services.trigger_event_handler

**File:** `src\casare_rpa\presentation\canvas\services\trigger_event_handler.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_trigger_event_handler` | - | `main_window: Optional['MainWindow']` | `'QtTriggerEventHandler'` | UNUSED |
| `__init__` | QtTriggerEventHandler | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `do_update` | QtTriggerEventHandler | `` | `None` | UNUSED |
| `get_trigger_count` | QtTriggerEventHandler | `self, trigger_id: str` | `int` | USED |
| `request_workflow_run` | QtTriggerEventHandler | `self` | `None` | USED |
| `update_trigger_stats` | QtTriggerEventHandler | `self, trigger_id: str, count: int, ...` | `None` | USED |


## casare_rpa.presentation.canvas.services.websocket_bridge

**File:** `src\casare_rpa\presentation\canvas\services\websocket_bridge.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_websocket_bridge` | - | `` | `WebSocketBridge` | UNUSED |
| `__init__` | WebSocketBridge | `self, parent: Optional[QObject]` | `None` | DUNDER |
| `_attempt_reconnect` | WebSocketBridge | `self` | `None` | INTERNAL |
| `_flush_batches` | WebSocketBridge | `self` | `None` | INTERNAL |
| `_on_connected` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_disconnected` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_error` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_job_update` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_queue_metrics` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_robot_status` | WebSocketBridge | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `async _reconnect_async` | WebSocketBridge | `self` | `None` | INTERNAL |
| `_schedule_reconnect` | WebSocketBridge | `self` | `None` | INTERNAL |
| `async connect` | WebSocketBridge | `self, client: 'OrchestratorClient'` | `bool` | USED |
| `async disconnect` | WebSocketBridge | `self` | `None` | USED |
| `is_connected` | WebSocketBridge | `self` | `bool` | USED |


## casare_rpa.presentation.canvas.theme

**File:** `src\casare_rpa\presentation\canvas\theme.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_canvas_stylesheet` | - | `` | `str` | USED |
| `get_node_status_color` | - | `status: str` | `str` | UNUSED |
| `get_status_color` | - | `status: str` | `str` | USED |
| `get_wire_color` | - | `data_type: str` | `str` | UNUSED |


## casare_rpa.presentation.canvas.ui.action_factory

**File:** `src\casare_rpa\presentation\canvas\ui\action_factory.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ActionFactory | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_create_action` | ActionFactory | `self, name: str, text: str, ...` | `QAction` | INTERNAL |
| `_create_edit_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `_create_file_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `_create_help_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `_create_tool_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `_create_view_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `_create_workflow_actions` | ActionFactory | `self` | `None` | INTERNAL |
| `actions` | ActionFactory | `self` | `Dict[str, QAction]` | USED |
| `create_all_actions` | ActionFactory | `self` | `None` | UNUSED |
| `get_action` | ActionFactory | `self, name: str` | `Optional[QAction]` | USED |
| `load_hotkeys` | ActionFactory | `self, hotkey_settings` | `None` | UNUSED |
| `set_actions_enabled` | ActionFactory | `self, action_names: List[str], enabled: bool` | `None` | USED |


## casare_rpa.presentation.canvas.ui.base_widget

**File:** `src\casare_rpa\presentation\canvas\ui\base_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BaseDialog | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `get_result` | BaseDialog | `self` | `Optional[Any]` | USED |
| `set_result` | BaseDialog | `self, result: Any` | `None` | USED |
| `validate` | BaseDialog | `self` | `bool` | USED |
| `__init__` | BaseDockWidget | `self, title: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `get_title` | BaseDockWidget | `self` | `str` | UNUSED |
| `set_title` | BaseDockWidget | `self, title: str` | `None` | USED |
| `__init__` | BaseWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_get_default_stylesheet` | BaseWidget | `self` | `str` | INTERNAL |
| `apply_stylesheet` | BaseWidget | `self` | `None` | USED |
| `clear_state` | BaseWidget | `self` | `None` | USED |
| `connect_signals` | BaseWidget | `self` | `None` | USED |
| `get_state` | BaseWidget | `self, key: str, default: Any` | `Any` | USED |
| `is_initialized` | BaseWidget | `self` | `bool` | UNUSED |
| `set_state` | BaseWidget | `self, key: str, value: Any` | `None` | UNUSED |
| `setup_ui` | BaseWidget | `self` | `None` | USED |


## casare_rpa.presentation.canvas.ui.debug_panel

**File:** `src\casare_rpa\presentation\canvas\ui\debug_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DebugPanel | `self, parent: Optional[QWidget], debug_controller: Optional['DebugController']` | `None` | DUNDER |
| `_add_snapshot_to_list` | DebugPanel | `self, snapshot: 'ExecutionSnapshot'` | `None` | INTERNAL |
| `_add_variable_item` | DebugPanel | `self, name: str, value: Any, ...` | `None` | INTERNAL |
| `_add_watch_expression` | DebugPanel | `self, expression: str` | `None` | INTERNAL |
| `_add_watch_from_input` | DebugPanel | `self` | `None` | INTERNAL |
| `_apply_styles` | DebugPanel | `self` | `None` | INTERNAL |
| `_clear_repl` | DebugPanel | `self` | `None` | INTERNAL |
| `_connect_debug_controller` | DebugPanel | `self` | `None` | INTERNAL |
| `_copy_to_clipboard` | DebugPanel | `self, text: str` | `None` | INTERNAL |
| `_create_breakpoints_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_call_stack_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_logs_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_repl_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_snapshot` | DebugPanel | `self` | `None` | INTERNAL |
| `_create_snapshots_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_step_toolbar` | DebugPanel | `self` | `QFrame` | INTERNAL |
| `_create_variables_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_create_watch_tab` | DebugPanel | `self` | `QWidget` | INTERNAL |
| `_delete_selected_snapshot` | DebugPanel | `self` | `None` | INTERNAL |
| `_disable_all_breakpoints` | DebugPanel | `self` | `None` | INTERNAL |
| `_edit_breakpoint_condition` | DebugPanel | `self, node_id: str, row: int` | `None` | INTERNAL |
| `_enable_all_breakpoints` | DebugPanel | `self` | `None` | INTERNAL |
| `_evaluate_repl_expression` | DebugPanel | `self` | `None` | INTERNAL |
| `_filter_variables` | DebugPanel | `self, text: str` | `None` | INTERNAL |
| `_on_auto_scroll_toggled` | DebugPanel | `self` | `None` | INTERNAL |
| `_on_bp_double_click` | DebugPanel | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_breakpoint_added` | DebugPanel | `self, node_id: str` | `None` | INTERNAL |
| `_on_breakpoint_hit_event` | DebugPanel | `self, event: 'Event'` | `None` | INTERNAL |
| `_on_breakpoint_hit_signal` | DebugPanel | `self, node_id: str` | `None` | INTERNAL |
| `_on_breakpoint_removed` | DebugPanel | `self, node_id: str` | `None` | INTERNAL |
| `_on_call_stack_double_click` | DebugPanel | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_call_stack_updated` | DebugPanel | `self, frames: list` | `None` | INTERNAL |
| `_on_clear_breakpoints` | DebugPanel | `self` | `None` | INTERNAL |
| `_on_execution_paused` | DebugPanel | `self` | `None` | INTERNAL |
| `_on_execution_resumed` | DebugPanel | `self` | `None` | INTERNAL |
| `_on_filter_changed` | DebugPanel | `self, filter_text: str` | `None` | INTERNAL |
| `_on_log_double_click` | DebugPanel | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_node_execution_completed` | DebugPanel | `self, event: 'Event'` | `None` | INTERNAL |
| `_on_node_execution_failed` | DebugPanel | `self, event: 'Event'` | `None` | INTERNAL |
| `_on_node_execution_started` | DebugPanel | `self, event: 'Event'` | `None` | INTERNAL |
| `_on_snapshot_created` | DebugPanel | `self, snapshot_id: str` | `None` | INTERNAL |
| `_on_step_completed` | DebugPanel | `self, node_id: str` | `None` | INTERNAL |
| `_on_variables_updated` | DebugPanel | `self, variables: dict` | `None` | INTERNAL |
| `_on_watch_updated` | DebugPanel | `self, watches: list` | `None` | INTERNAL |
| `_refresh_variables` | DebugPanel | `self` | `None` | INTERNAL |
| `_remove_breakpoint` | DebugPanel | `self, node_id: str` | `None` | INTERNAL |
| `_remove_selected_watch` | DebugPanel | `self` | `None` | INTERNAL |
| `_restore_selected_snapshot` | DebugPanel | `self` | `None` | INTERNAL |
| `_set_stepping_enabled` | DebugPanel | `self, enabled: bool` | `None` | INTERNAL |
| `_setup_connections` | DebugPanel | `self` | `None` | INTERNAL |
| `_setup_dock` | DebugPanel | `self` | `None` | INTERNAL |
| `_setup_lazy_subscriptions` | DebugPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | DebugPanel | `self` | `None` | INTERNAL |
| `_show_breakpoint_context_menu` | DebugPanel | `self, pos` | `None` | INTERNAL |
| `_show_variable_context_menu` | DebugPanel | `self, pos` | `None` | INTERNAL |
| `add_breakpoint_to_list` | DebugPanel | `self, node_id: str, node_name: str, ...` | `None` | USED |
| `add_log` | DebugPanel | `self, level: str, message: str, ...` | `None` | USED |
| `clear_breakpoints` | DebugPanel | `self` | `None` | USED |
| `clear_logs` | DebugPanel | `self` | `None` | UNUSED |
| `remove_breakpoint_from_list` | DebugPanel | `self, node_id: str` | `None` | USED |
| `set_debug_controller` | DebugPanel | `self, controller: 'DebugController'` | `None` | UNUSED |
| `set_item_visibility` | DebugPanel | `item: QTreeWidgetItem` | `bool` | USED |
| `update_call_stack` | DebugPanel | `self, frames: List['CallStackFrame']` | `None` | USED |
| `update_variables` | DebugPanel | `self, variables: Dict[str, Any]` | `None` | USED |
| `update_watches` | DebugPanel | `self, watches: List['WatchExpression']` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\credential_manager_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ApiKeyTestThread | `self, provider: str, api_key: str, ...` | `-` | DUNDER |
| `run` | ApiKeyTestThread | `self` | `-` | USED |
| `start` | ApiKeyTestThread | `self` | `-` | USED |
| `__init__` | ApiKeyTestWorker | `self, provider: str, api_key: str` | `None` | DUNDER |
| `_test_provider` | ApiKeyTestWorker | `self, provider: str, api_key: str` | `tuple[bool, str]` | INTERNAL |
| `run` | ApiKeyTestWorker | `self` | `None` | USED |
| `__init__` | CredentialManagerDialog | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_add_new_userpass` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_apply_styles` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_create_all_credentials_tab` | CredentialManagerDialog | `self` | `QWidget` | INTERNAL |
| `_create_api_keys_tab` | CredentialManagerDialog | `self` | `QWidget` | INTERNAL |
| `_create_userpass_tab` | CredentialManagerDialog | `self` | `QWidget` | INTERNAL |
| `_delete_api_key` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_delete_userpass` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_get_store` | CredentialManagerDialog | `self` | `-` | INTERNAL |
| `_load_credentials` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_on_api_provider_selected` | CredentialManagerDialog | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_credential_double_clicked` | CredentialManagerDialog | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_search_changed` | CredentialManagerDialog | `self, text: str` | `None` | INTERNAL |
| `_on_test_complete` | CredentialManagerDialog | `self, success: bool, message: str` | `None` | INTERNAL |
| `_on_userpass_selected` | CredentialManagerDialog | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_refresh_all_credentials` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_refresh_api_status` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_refresh_userpass_list` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_save_api_key` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_save_userpass` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_test_api_key` | CredentialManagerDialog | `self` | `None` | INTERNAL |
| `_toggle_api_key_visibility` | CredentialManagerDialog | `self, checked: bool` | `None` | INTERNAL |
| `_toggle_password_visibility` | CredentialManagerDialog | `self, checked: bool` | `None` | INTERNAL |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_dashboard

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_dashboard.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FleetDashboardDialog | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_connect_signals` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_job_selected` | FleetDashboardDialog | `self, job_id: str` | `None` | INTERNAL |
| `_on_realtime_connection_status` | FleetDashboardDialog | `self, connected: bool` | `None` | INTERNAL |
| `_on_realtime_job_status` | FleetDashboardDialog | `self, update: 'JobStatusUpdate'` | `None` | INTERNAL |
| `_on_realtime_jobs_batch` | FleetDashboardDialog | `self, updates: List['JobStatusUpdate']` | `None` | INTERNAL |
| `_on_realtime_queue_metrics` | FleetDashboardDialog | `self, update: 'QueueMetricsUpdate'` | `None` | INTERNAL |
| `_on_realtime_robot_status` | FleetDashboardDialog | `self, update: 'RobotStatusUpdate'` | `None` | INTERNAL |
| `_on_realtime_robots_batch` | FleetDashboardDialog | `self, updates: List['RobotStatusUpdate']` | `None` | INTERNAL |
| `_on_refresh_analytics` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_refresh_api_keys` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_refresh_jobs` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_refresh_robots` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_refresh_schedules` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `_on_schedule_selected` | FleetDashboardDialog | `self, schedule_id: str` | `None` | INTERNAL |
| `_on_tenant_changed` | FleetDashboardDialog | `self, tenant_id: Optional[str]` | `None` | INTERNAL |
| `_setup_ui` | FleetDashboardDialog | `self` | `None` | INTERNAL |
| `connect_websocket_bridge` | FleetDashboardDialog | `self, bridge: 'WebSocketBridge'` | `None` | UNUSED |
| `disconnect_websocket_bridge` | FleetDashboardDialog | `self, bridge: 'WebSocketBridge'` | `None` | UNUSED |
| `get_current_tenant_id` | FleetDashboardDialog | `self` | `Optional[str]` | USED |
| `get_selected_job` | FleetDashboardDialog | `self` | `Optional[Dict[str, Any]]` | USED |
| `set_connection_status` | FleetDashboardDialog | `self, connected: bool, message: str` | `None` | USED |
| `set_current_tenant` | FleetDashboardDialog | `self, tenant_id: Optional[str]` | `None` | USED |
| `set_status` | FleetDashboardDialog | `self, message: str` | `None` | USED |
| `set_super_admin` | FleetDashboardDialog | `self, is_super_admin: bool` | `None` | USED |
| `show_analytics_tab` | FleetDashboardDialog | `self` | `None` | UNUSED |
| `show_api_keys_tab` | FleetDashboardDialog | `self` | `None` | UNUSED |
| `show_jobs_tab` | FleetDashboardDialog | `self` | `None` | UNUSED |
| `show_robots_tab` | FleetDashboardDialog | `self` | `None` | UNUSED |
| `show_schedules_tab` | FleetDashboardDialog | `self` | `None` | UNUSED |
| `update_analytics` | FleetDashboardDialog | `self, analytics: Dict[str, Any]` | `None` | USED |
| `update_api_keys` | FleetDashboardDialog | `self, api_keys: List[Dict[str, Any]]` | `None` | USED |
| `update_api_keys_robots` | FleetDashboardDialog | `self, robots: List[Dict[str, Any]]` | `None` | USED |
| `update_jobs` | FleetDashboardDialog | `self, jobs: List[Dict[str, Any]]` | `None` | USED |
| `update_robots` | FleetDashboardDialog | `self, robots: List['Robot']` | `None` | USED |
| `update_schedules` | FleetDashboardDialog | `self, schedules: List[Dict[str, Any]]` | `None` | USED |
| `update_tenants` | FleetDashboardDialog | `self, tenants: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.analytics_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\analytics_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AnalyticsTabWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | AnalyticsTabWidget | `self` | `None` | INTERNAL |
| `_request_refresh` | AnalyticsTabWidget | `self` | `None` | INTERNAL |
| `_setup_ui` | AnalyticsTabWidget | `self` | `None` | INTERNAL |
| `set_refreshing` | AnalyticsTabWidget | `self, refreshing: bool` | `None` | USED |
| `update_active_jobs` | AnalyticsTabWidget | `self, running: int, completed_today: int` | `None` | UNUSED |
| `update_analytics` | AnalyticsTabWidget | `self, analytics: Dict[str, Any]` | `None` | USED |
| `update_fleet_status` | AnalyticsTabWidget | `self, active_robots: int, total_robots: int` | `None` | UNUSED |
| `update_queue_metrics` | AnalyticsTabWidget | `self, update: 'QueueMetricsUpdate'` | `None` | USED |
| `__init__` | BarChart | `self, title: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `paintEvent` | BarChart | `self, event` | `None` | UNUSED |
| `set_data` | BarChart | `self, data: List[tuple], max_value: Optional[float]` | `None` | USED |
| `__init__` | PieChart | `self, title: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `paintEvent` | PieChart | `self, event` | `None` | UNUSED |
| `set_data` | PieChart | `self, data: List[tuple]` | `None` | USED |
| `__init__` | StatCard | `self, title: str, value: str, ...` | `None` | DUNDER |
| `_setup_ui` | StatCard | `self` | `None` | INTERNAL |
| `set_value` | StatCard | `self, value: str, subtitle: str` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.api_keys_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\api_keys_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ApiKeysTabWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_setup_ui` | ApiKeysTabWidget | `self` | `None` | INTERNAL |
| `set_refreshing` | ApiKeysTabWidget | `self, refreshing: bool` | `None` | USED |
| `set_tenant` | ApiKeysTabWidget | `self, tenant_id: Optional[str]` | `None` | USED |
| `update_api_keys` | ApiKeysTabWidget | `self, api_keys: List[Dict[str, Any]]` | `None` | USED |
| `update_robots` | ApiKeysTabWidget | `self, robots: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\base_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BaseTabWidget | `self, tab_name: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_additional_styles` | BaseTabWidget | `self` | `None` | INTERNAL |
| `_apply_base_styles` | BaseTabWidget | `self` | `None` | INTERNAL |
| `_request_refresh` | BaseTabWidget | `self` | `None` | INTERNAL |
| `_setup_base_ui` | BaseTabWidget | `self` | `None` | INTERNAL |
| `_setup_content` | BaseTabWidget | `self` | `None` | INTERNAL |
| `pause_auto_refresh` | BaseTabWidget | `self` | `None` | UNUSED |
| `resume_auto_refresh` | BaseTabWidget | `self` | `None` | UNUSED |
| `set_refresh_interval` | BaseTabWidget | `self, interval_ms: int` | `None` | UNUSED |
| `set_refreshing` | BaseTabWidget | `self, refreshing: bool` | `None` | USED |
| `set_status` | BaseTabWidget | `self, message: str` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\jobs_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobsTabWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filters` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_apply_styles` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_on_cancel_job` | JobsTabWidget | `self, job: Dict[str, Any]` | `None` | INTERNAL |
| `_on_double_click` | JobsTabWidget | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_retry_job` | JobsTabWidget | `self, job: Dict[str, Any]` | `None` | INTERNAL |
| `_on_selection_changed` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_populate_table` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_request_refresh` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_setup_ui` | JobsTabWidget | `self` | `None` | INTERNAL |
| `_show_context_menu` | JobsTabWidget | `self, pos` | `None` | INTERNAL |
| `_show_job_details` | JobsTabWidget | `self, job: Dict[str, Any]` | `None` | INTERNAL |
| `_update_job_row` | JobsTabWidget | `self, row: int, update: 'JobStatusUpdate'` | `None` | INTERNAL |
| `_update_status_label` | JobsTabWidget | `self, visible: Optional[int]` | `None` | INTERNAL |
| `create_progress_bar_widget` | JobsTabWidget | `self, progress: int, status: str` | `QProgressBar` | UNUSED |
| `get_job_by_id` | JobsTabWidget | `self, job_id: str` | `Optional[Dict[str, Any]]` | UNUSED |
| `get_selected_job` | JobsTabWidget | `self` | `Optional[Dict[str, Any]]` | USED |
| `handle_batch_job_updates` | JobsTabWidget | `self, updates: List['JobStatusUpdate']` | `None` | USED |
| `handle_job_status_update` | JobsTabWidget | `self, update: 'JobStatusUpdate'` | `None` | USED |
| `set_refreshing` | JobsTabWidget | `self, refreshing: bool` | `None` | USED |
| `update_jobs` | JobsTabWidget | `self, jobs: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\robots_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotEditDialog | `self, robot: Optional['Robot'], parent: Optional[QWidget]` | `None` | DUNDER |
| `_on_save` | RobotEditDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | RobotEditDialog | `self` | `None` | INTERNAL |
| `get_robot_data` | RobotEditDialog | `self` | `Dict` | USED |
| `__init__` | RobotsTabWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filters` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_apply_styles` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_is_heartbeat_stale` | RobotsTabWidget | `self, timestamp: datetime` | `bool` | INTERNAL |
| `_on_add_robot` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_on_delete_robot` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_on_double_click` | RobotsTabWidget | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_edit_robot` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_on_run_workflow_on_robot` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_on_selection_changed` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_on_set_status` | RobotsTabWidget | `self, robot: 'Robot', status: str` | `None` | INTERNAL |
| `_on_view_robot_details` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_on_view_robot_logs` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_on_view_robot_metrics` | RobotsTabWidget | `self, robot: 'Robot'` | `None` | INTERNAL |
| `_populate_table` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_request_refresh` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_setup_ui` | RobotsTabWidget | `self` | `None` | INTERNAL |
| `_show_context_menu` | RobotsTabWidget | `self, pos` | `None` | INTERNAL |
| `_update_robot_row` | RobotsTabWidget | `self, row: int, update: 'RobotStatusUpdate'` | `None` | INTERNAL |
| `_update_status_label` | RobotsTabWidget | `self, visible: Optional[int]` | `None` | INTERNAL |
| `get_robot_by_id` | RobotsTabWidget | `self, robot_id: str` | `Optional['Robot']` | UNUSED |
| `handle_batch_robot_updates` | RobotsTabWidget | `self, updates: List['RobotStatusUpdate']` | `None` | USED |
| `handle_robot_status_update` | RobotsTabWidget | `self, update: 'RobotStatusUpdate'` | `None` | USED |
| `set_refreshing` | RobotsTabWidget | `self, refreshing: bool` | `None` | USED |
| `update_robots` | RobotsTabWidget | `self, robots: List['Robot']` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\fleet_tabs\schedules_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SchedulesTabWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filters` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_apply_styles` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_get_frequency_display` | SchedulesTabWidget | `self, schedule: Dict[str, Any]` | `str` | INTERNAL |
| `_on_add_schedule` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_on_delete_schedule` | SchedulesTabWidget | `self, schedule: Dict[str, Any]` | `None` | INTERNAL |
| `_on_double_click` | SchedulesTabWidget | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_edit_schedule` | SchedulesTabWidget | `self, schedule: Dict[str, Any]` | `None` | INTERNAL |
| `_on_enabled_changed` | SchedulesTabWidget | `self, schedule_id: str, state: int` | `None` | INTERNAL |
| `_on_run_now` | SchedulesTabWidget | `self, schedule: Dict[str, Any]` | `None` | INTERNAL |
| `_on_selection_changed` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_populate_table` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_request_refresh` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_setup_ui` | SchedulesTabWidget | `self` | `None` | INTERNAL |
| `_show_context_menu` | SchedulesTabWidget | `self, pos` | `None` | INTERNAL |
| `_update_status_label` | SchedulesTabWidget | `self, visible: Optional[int]` | `None` | INTERNAL |
| `set_refreshing` | SchedulesTabWidget | `self, refreshing: bool` | `None` | USED |
| `update_schedules` | SchedulesTabWidget | `self, schedules: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.node_properties_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\node_properties_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodePropertiesDialog | `self, node_id: str, node_type: str, ...` | `None` | DUNDER |
| `_apply_styles` | NodePropertiesDialog | `self` | `None` | INTERNAL |
| `_create_advanced_tab` | NodePropertiesDialog | `self` | `QWidget` | INTERNAL |
| `_create_basic_tab` | NodePropertiesDialog | `self` | `QWidget` | INTERNAL |
| `_gather_properties` | NodePropertiesDialog | `self` | `Dict[str, Any]` | INTERNAL |
| `_load_properties` | NodePropertiesDialog | `self` | `None` | INTERNAL |
| `_on_accept` | NodePropertiesDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | NodePropertiesDialog | `self` | `None` | INTERNAL |
| `_validate` | NodePropertiesDialog | `self` | `bool` | INTERNAL |
| `get_properties` | NodePropertiesDialog | `self` | `Dict[str, Any]` | UNUSED |


## casare_rpa.presentation.canvas.ui.dialogs.preferences_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\preferences_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | PreferencesDialog | `self, preferences: Optional[Dict[str, Any]], parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_preferences` | PreferencesDialog | `self` | `None` | INTERNAL |
| `_apply_styles` | PreferencesDialog | `self` | `None` | INTERNAL |
| `_create_autosave_tab` | PreferencesDialog | `self` | `QWidget` | INTERNAL |
| `_create_editor_tab` | PreferencesDialog | `self` | `QWidget` | INTERNAL |
| `_create_general_tab` | PreferencesDialog | `self` | `QWidget` | INTERNAL |
| `_create_performance_tab` | PreferencesDialog | `self` | `QWidget` | INTERNAL |
| `_gather_preferences` | PreferencesDialog | `self` | `Dict[str, Any]` | INTERNAL |
| `_load_preferences` | PreferencesDialog | `self` | `None` | INTERNAL |
| `_on_apply` | PreferencesDialog | `self` | `None` | INTERNAL |
| `_on_ok` | PreferencesDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | PreferencesDialog | `self` | `None` | INTERNAL |
| `get_preferences` | PreferencesDialog | `self` | `Dict[str, Any]` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.project_manager_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\project_manager_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ProjectManagerDialog | `self, recent_projects: Optional[List['ProjectIndexEntry']], parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_create_new_project_tab` | ProjectManagerDialog | `self` | `QWidget` | INTERNAL |
| `_create_recent_tab` | ProjectManagerDialog | `self` | `QWidget` | INTERNAL |
| `_get_scenarios_for_project` | ProjectManagerDialog | `self, project_path: str` | `List[dict]` | INTERNAL |
| `_load_recent_projects` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_browse` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_browse_new_location` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_create_project` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_open_selected` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_remove_from_list` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_on_tree_double_clicked` | ProjectManagerDialog | `self, item: QTreeWidgetItem, column: int` | `None` | INTERNAL |
| `_on_tree_selection_changed` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `_update_details_for_project` | ProjectManagerDialog | `self, entry: Optional['ProjectIndexEntry']` | `None` | INTERNAL |
| `_update_details_for_scenario` | ProjectManagerDialog | `self, data: dict` | `None` | INTERNAL |
| `_update_details_for_selection` | ProjectManagerDialog | `self, data: Optional[dict]` | `None` | INTERNAL |
| `_validate_new_project` | ProjectManagerDialog | `self` | `None` | INTERNAL |
| `update_recent_projects` | ProjectManagerDialog | `self, projects: List['ProjectIndexEntry']` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.dialogs.recording_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\recording_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RecordingPreviewDialog | `self, actions: list, parent` | `-` | DUNDER |
| `_load_actions` | RecordingPreviewDialog | `self` | `-` | INTERNAL |
| `_on_clear_all` | RecordingPreviewDialog | `self` | `-` | INTERNAL |
| `_on_delete_selected` | RecordingPreviewDialog | `self` | `-` | INTERNAL |
| `_setup_ui` | RecordingPreviewDialog | `self` | `-` | INTERNAL |
| `_truncate` | RecordingPreviewDialog | `self, text: str, max_length: int` | `str` | INTERNAL |
| `get_actions` | RecordingPreviewDialog | `self` | `list` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.remote_robot_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\remote_robot_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RemoteRobotDialog | `self, robot_id: str, robot_data: Optional[Dict[str, Any]], ...` | `None` | DUNDER |
| `_apply_styles` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_clear_logs` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_create_config_tab` | RemoteRobotDialog | `self` | `QWidget` | INTERNAL |
| `_create_details_tab` | RemoteRobotDialog | `self` | `QWidget` | INTERNAL |
| `_create_jobs_tab` | RemoteRobotDialog | `self` | `QWidget` | INTERNAL |
| `_create_logs_tab` | RemoteRobotDialog | `self` | `QWidget` | INTERNAL |
| `_create_metrics_tab` | RemoteRobotDialog | `self` | `QWidget` | INTERNAL |
| `_format_bytes` | RemoteRobotDialog | `self, bytes_val: int` | `str` | INTERNAL |
| `_on_cancel_job` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_on_restart` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_on_save_config` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_on_start` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_on_stop` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_populate_data` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_populate_jobs` | RemoteRobotDialog | `self, jobs: List[Dict[str, Any]]` | `None` | INTERNAL |
| `_populate_metrics` | RemoteRobotDialog | `self, metrics: Dict[str, Any]` | `None` | INTERNAL |
| `_request_refresh` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | RemoteRobotDialog | `self` | `None` | INTERNAL |
| `append_log` | RemoteRobotDialog | `self, message: str, level: str` | `None` | UNUSED |
| `update_robot` | RemoteRobotDialog | `self, robot_data: Dict[str, Any]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\schedule_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ScheduleDialog | `self, workflow_path: Optional[Path], workflow_name: str, ...` | `-` | DUNDER |
| `_build_schedule` | ScheduleDialog | `self` | `Optional[WorkflowSchedule]` | INTERNAL |
| `_load_schedule` | ScheduleDialog | `self, schedule: WorkflowSchedule` | `-` | INTERNAL |
| `_on_frequency_changed` | ScheduleDialog | `self, frequency: str` | `-` | INTERNAL |
| `_on_save` | ScheduleDialog | `self` | `-` | INTERNAL |
| `_setup_ui` | ScheduleDialog | `self` | `-` | INTERNAL |
| `_update_next_run_preview` | ScheduleDialog | `self` | `-` | INTERNAL |
| `__init__` | ScheduleManagerDialog | `self, schedules: List[WorkflowSchedule], parent: Optional[QWidget]` | `-` | DUNDER |
| `_on_delete` | ScheduleManagerDialog | `self, schedule: WorkflowSchedule` | `-` | INTERNAL |
| `_on_double_click` | ScheduleManagerDialog | `self, row: int, col: int` | `-` | INTERNAL |
| `_on_edit` | ScheduleManagerDialog | `self, schedule: WorkflowSchedule` | `-` | INTERNAL |
| `_on_run_now` | ScheduleManagerDialog | `self, schedule: WorkflowSchedule` | `-` | INTERNAL |
| `_on_toggle_enabled` | ScheduleManagerDialog | `self, schedule: WorkflowSchedule, enabled` | `-` | INTERNAL |
| `_setup_ui` | ScheduleManagerDialog | `self` | `-` | INTERNAL |
| `_show_context_menu` | ScheduleManagerDialog | `self, pos` | `-` | INTERNAL |
| `_update_table` | ScheduleManagerDialog | `self` | `-` | INTERNAL |
| `get_schedules` | ScheduleManagerDialog | `self` | `List[WorkflowSchedule]` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.template_browser_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\template_browser_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `show_template_browser` | - | `parent: Optional[QWidget]` | `Optional[TemplateInfo]` | USED |
| `__init__` | TemplateBrowserDialog | `self, parent: Optional[QWidget]` | `-` | DUNDER |
| `_create_ui` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `_filter_templates` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `_load_templates` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `_on_template_double_clicked` | TemplateBrowserDialog | `self, item: QListWidgetItem` | `-` | INTERNAL |
| `_on_template_selected` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `_on_use_template` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `_update_template_list` | TemplateBrowserDialog | `self` | `-` | INTERNAL |
| `get_selected_template` | TemplateBrowserDialog | `self` | `Optional[TemplateInfo]` | USED |


## casare_rpa.presentation.canvas.ui.dialogs.update_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\update_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | UpdateDialog | `self, update_info: UpdateInfo, update_manager: Optional[UpdateManager], ...` | `None` | DUNDER |
| `_apply_styles` | UpdateDialog | `self` | `None` | INTERNAL |
| `async _async_download` | UpdateDialog | `self` | `None` | INTERNAL |
| `_connect_signals` | UpdateDialog | `self` | `None` | INTERNAL |
| `_do_download` | UpdateDialog | `self` | `None` | INTERNAL |
| `_install_update` | UpdateDialog | `self` | `None` | INTERNAL |
| `_on_download_clicked` | UpdateDialog | `self` | `None` | INTERNAL |
| `_on_download_complete` | UpdateDialog | `self` | `None` | INTERNAL |
| `_on_download_error` | UpdateDialog | `self, error: str` | `None` | INTERNAL |
| `_on_remind_clicked` | UpdateDialog | `self` | `None` | INTERNAL |
| `_on_skip_clicked` | UpdateDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | UpdateDialog | `self` | `None` | INTERNAL |
| `_start_download` | UpdateDialog | `self` | `None` | INTERNAL |
| `async apply` | UpdateDialog | `` | `-` | USED |
| `async download` | UpdateDialog | `` | `-` | USED |
| `is_download_complete` | UpdateDialog | `self` | `bool` | UNUSED |
| `is_downloading` | UpdateDialog | `self` | `bool` | UNUSED |
| `update_info` | UpdateDialog | `self` | `UpdateInfo` | UNUSED |
| `update_progress` | UpdateDialog | `self, progress: DownloadProgress` | `None` | USED |
| `__init__` | UpdateNotificationWidget | `self, update_info: Optional[UpdateInfo], parent: Optional[QWidget]` | `None` | DUNDER |
| `mousePressEvent` | UpdateNotificationWidget | `self, event` | `None` | USED |
| `set_update_info` | UpdateNotificationWidget | `self, update_info: Optional[UpdateInfo]` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.dialogs.workflow_settings_dialog

**File:** `src\casare_rpa\presentation\canvas\ui\dialogs\workflow_settings_dialog.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowSettingsDialog | `self, settings: Optional[Dict[str, Any]], parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | WorkflowSettingsDialog | `self` | `None` | INTERNAL |
| `_create_execution_tab` | WorkflowSettingsDialog | `self` | `QWidget` | INTERNAL |
| `_create_general_tab` | WorkflowSettingsDialog | `self` | `QWidget` | INTERNAL |
| `_create_variables_tab` | WorkflowSettingsDialog | `self` | `QWidget` | INTERNAL |
| `_gather_settings` | WorkflowSettingsDialog | `self` | `Dict[str, Any]` | INTERNAL |
| `_load_settings` | WorkflowSettingsDialog | `self` | `None` | INTERNAL |
| `_on_accept` | WorkflowSettingsDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | WorkflowSettingsDialog | `self` | `None` | INTERNAL |
| `_validate` | WorkflowSettingsDialog | `self` | `bool` | INTERNAL |
| `get_settings` | WorkflowSettingsDialog | `self` | `Dict[str, Any]` | USED |


## casare_rpa.presentation.canvas.ui.icons

**File:** `src\casare_rpa\presentation\canvas\ui\icons.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_toolbar_icon` | - | `name: str` | `'QIcon'` | USED |
| `_get_style` | ToolbarIcons | `cls` | `'QStyle'` | INTERNAL |
| `get_all_icons` | ToolbarIcons | `cls` | `dict` | UNUSED |
| `get_icon` | ToolbarIcons | `cls, name: str` | `'QIcon'` | USED |


## casare_rpa.presentation.canvas.ui.panels.analytics_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\analytics_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AnalyticsPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_auto_refresh` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_check_api_connection` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_create_bottlenecks_tab` | AnalyticsPanel | `self` | `QWidget` | INTERNAL |
| `_create_execution_tab` | AnalyticsPanel | `self` | `QWidget` | INTERNAL |
| `_create_header` | AnalyticsPanel | `self` | `QHBoxLayout` | INTERNAL |
| `_create_timeline_tab` | AnalyticsPanel | `self` | `QWidget` | INTERNAL |
| `_get_orchestrator_url` | AnalyticsPanel | `self` | `str` | INTERNAL |
| `_load_bottlenecks` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_load_execution_analysis` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_load_timeline` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_load_workflows` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_on_bottleneck_selected` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_on_insight_selected` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_on_workflow_changed` | AnalyticsPanel | `self, index: int` | `None` | INTERNAL |
| `_run_analysis` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_setup_dock` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_setup_refresh_timer` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | AnalyticsPanel | `self` | `None` | INTERNAL |
| `_update_bottlenecks_ui` | AnalyticsPanel | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_update_execution_ui` | AnalyticsPanel | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_update_timeline_ui` | AnalyticsPanel | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `cleanup` | AnalyticsPanel | `self` | `None` | USED |
| `hideEvent` | AnalyticsPanel | `self, event` | `None` | USED |
| `set_api_url` | AnalyticsPanel | `self, url: str` | `None` | USED |
| `set_api_url` | AnalyticsPanel | `self, url: str` | `None` | USED |
| `showEvent` | AnalyticsPanel | `self, event` | `None` | USED |
| `__init__` | ApiWorker | `self, url: str, method: str` | `None` | DUNDER |
| `async _fetch` | ApiWorker | `self` | `Dict[str, Any]` | INTERNAL |
| `run` | ApiWorker | `self` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.api_key_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\api_key_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ApiKeyPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filters` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_apply_styles` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_on_generate_key` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_on_revoke_key` | ApiKeyPanel | `self, key: Dict[str, Any]` | `None` | INTERNAL |
| `_on_rotate_key` | ApiKeyPanel | `self, key: Dict[str, Any]` | `None` | INTERNAL |
| `_on_view_details` | ApiKeyPanel | `self, key: Dict[str, Any]` | `None` | INTERNAL |
| `_populate_table` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_request_refresh` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_show_context_menu` | ApiKeyPanel | `self, pos` | `None` | INTERNAL |
| `_update_stats` | ApiKeyPanel | `self` | `None` | INTERNAL |
| `_update_status_label` | ApiKeyPanel | `self, visible: Optional[int]` | `None` | INTERNAL |
| `set_refreshing` | ApiKeyPanel | `self, refreshing: bool` | `None` | USED |
| `set_tenant` | ApiKeyPanel | `self, tenant_id: str` | `None` | USED |
| `update_api_keys` | ApiKeyPanel | `self, api_keys: List[Dict[str, Any]]` | `None` | USED |
| `update_robots` | ApiKeyPanel | `self, robots: List[Dict[str, Any]]` | `None` | USED |
| `__init__` | GenerateApiKeyDialog | `self, robots: List[Dict[str, Any]], parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | GenerateApiKeyDialog | `self` | `None` | INTERNAL |
| `_copy_key` | GenerateApiKeyDialog | `self` | `None` | INTERNAL |
| `_on_expires_changed` | GenerateApiKeyDialog | `self, state: int` | `None` | INTERNAL |
| `_on_generate` | GenerateApiKeyDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | GenerateApiKeyDialog | `self` | `None` | INTERNAL |
| `get_key_config` | GenerateApiKeyDialog | `self` | `Dict[str, Any]` | USED |
| `set_generated_key` | GenerateApiKeyDialog | `self, raw_key: str` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock

**File:** `src\casare_rpa\presentation\canvas\ui\panels\bottom_panel_dock.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BottomPanelDock | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | BottomPanelDock | `self` | `None` | INTERNAL |
| `_create_tabs` | BottomPanelDock | `self` | `None` | INTERNAL |
| `_on_history_clear_requested` | BottomPanelDock | `self` | `None` | INTERNAL |
| `_on_variables_changed` | BottomPanelDock | `self, variables: Dict[str, Any]` | `None` | INTERNAL |
| `_setup_dock` | BottomPanelDock | `self` | `None` | INTERNAL |
| `_setup_ui` | BottomPanelDock | `self` | `None` | INTERNAL |
| `_update_tab_badges` | BottomPanelDock | `self` | `None` | INTERNAL |
| `add_output` | BottomPanelDock | `self, name: str, value: Any, ...` | `None` | USED |
| `append_history_entry` | BottomPanelDock | `self, entry: Dict[str, Any]` | `None` | USED |
| `clear_history` | BottomPanelDock | `self` | `None` | USED |
| `clear_log` | BottomPanelDock | `self` | `None` | USED |
| `clear_outputs` | BottomPanelDock | `self` | `None` | USED |
| `clear_terminal` | BottomPanelDock | `self` | `None` | USED |
| `clear_validation` | BottomPanelDock | `self` | `None` | UNUSED |
| `execution_finished` | BottomPanelDock | `self` | `None` | UNUSED |
| `get_history_tab` | BottomPanelDock | `self` | `'HistoryTab'` | USED |
| `get_log_tab` | BottomPanelDock | `self` | `'LogTab'` | USED |
| `get_output_tab` | BottomPanelDock | `self` | `'OutputTab'` | UNUSED |
| `get_terminal_tab` | BottomPanelDock | `self` | `'TerminalTab'` | UNUSED |
| `get_validation_errors_blocking` | BottomPanelDock | `self` | `List[Dict]` | USED |
| `get_validation_tab` | BottomPanelDock | `self` | `'ValidationTab'` | USED |
| `get_variables` | BottomPanelDock | `self` | `Dict[str, Any]` | USED |
| `get_variables_tab` | BottomPanelDock | `self` | `'VariablesTab'` | USED |
| `has_validation_errors` | BottomPanelDock | `self` | `bool` | UNUSED |
| `log_event` | BottomPanelDock | `self, event: 'Event'` | `None` | USED |
| `log_message` | BottomPanelDock | `self, message: str, level: str, ...` | `None` | USED |
| `prepare_for_execution` | BottomPanelDock | `self` | `None` | UNUSED |
| `reset` | BottomPanelDock | `self` | `None` | USED |
| `set_runtime_mode` | BottomPanelDock | `self, enabled: bool` | `None` | USED |
| `set_validation_result` | BottomPanelDock | `self, result: 'ValidationResult'` | `None` | UNUSED |
| `set_variables` | BottomPanelDock | `self, variables: Dict[str, Any]` | `None` | USED |
| `set_workflow_result` | BottomPanelDock | `self, success: bool, message: str` | `None` | USED |
| `show_history_tab` | BottomPanelDock | `self` | `None` | USED |
| `show_log_tab` | BottomPanelDock | `self` | `None` | USED |
| `show_output_tab` | BottomPanelDock | `self` | `None` | USED |
| `show_terminal_tab` | BottomPanelDock | `self` | `None` | UNUSED |
| `show_validation_tab` | BottomPanelDock | `self` | `None` | USED |
| `show_variables_tab` | BottomPanelDock | `self` | `None` | USED |
| `terminal_write` | BottomPanelDock | `self, text: str, level: str` | `None` | UNUSED |
| `terminal_write_stderr` | BottomPanelDock | `self, text: str` | `None` | USED |
| `terminal_write_stdout` | BottomPanelDock | `self, text: str` | `None` | USED |
| `update_history` | BottomPanelDock | `self, history: List[Dict[str, Any]]` | `None` | USED |
| `update_runtime_values` | BottomPanelDock | `self, values: Dict[str, Any]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.history_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\history_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HistoryTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_add_entry_to_table` | HistoryTab | `self, entry: Dict[str, Any], number: int` | `None` | INTERNAL |
| `_apply_filter` | HistoryTab | `self` | `None` | INTERNAL |
| `_apply_styles` | HistoryTab | `self` | `None` | INTERNAL |
| `_on_clear` | HistoryTab | `self` | `None` | INTERNAL |
| `_on_filter_changed` | HistoryTab | `self, filter_text: str` | `None` | INTERNAL |
| `_on_selection_changed` | HistoryTab | `self` | `None` | INTERNAL |
| `_setup_ui` | HistoryTab | `self` | `None` | INTERNAL |
| `_should_show_entry` | HistoryTab | `self, entry: Dict[str, Any]` | `bool` | INTERNAL |
| `_update_statistics` | HistoryTab | `self` | `None` | INTERNAL |
| `append_entry` | HistoryTab | `self, entry: Dict[str, Any]` | `None` | USED |
| `clear` | HistoryTab | `self` | `None` | USED |
| `get_entry_count` | HistoryTab | `self` | `int` | USED |
| `scroll_to_bottom` | HistoryTab | `self` | `None` | UNUSED |
| `update_history` | HistoryTab | `self, history: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.log_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\log_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LogTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filter` | LogTab | `self` | `None` | INTERNAL |
| `_apply_styles` | LogTab | `self` | `None` | INTERNAL |
| `_get_level_color` | LogTab | `self, level: str` | `QColor` | INTERNAL |
| `_on_auto_scroll_toggled` | LogTab | `self, checked: bool` | `None` | INTERNAL |
| `_on_double_click` | LogTab | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_export` | LogTab | `self` | `None` | INTERNAL |
| `_on_filter_changed` | LogTab | `self, filter_text: str` | `None` | INTERNAL |
| `_setup_ui` | LogTab | `self` | `None` | INTERNAL |
| `_trim_log` | LogTab | `self` | `None` | INTERNAL |
| `clear` | LogTab | `self` | `None` | USED |
| `get_entry_count` | LogTab | `self` | `int` | USED |
| `log_event` | LogTab | `self, event: 'Event'` | `None` | USED |
| `log_message` | LogTab | `self, message: str, level: str, ...` | `None` | USED |
| `set_max_entries` | LogTab | `self, max_entries: int` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.panels.log_viewer_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\log_viewer_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LogStreamWorker | `self, orchestrator_url: str, api_secret: str, ...` | `None` | DUNDER |
| `async _connect` | LogStreamWorker | `self` | `None` | INTERNAL |
| `async _connect_loop` | LogStreamWorker | `self` | `None` | INTERNAL |
| `run` | LogStreamWorker | `self` | `None` | USED |
| `stop` | LogStreamWorker | `self` | `None` | USED |
| `__init__` | LogViewerPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_add_log_entry` | LogViewerPanel | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_apply_filters` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_apply_styles` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_connect` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_disconnect` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_get_level_color` | LogViewerPanel | `self, level: str` | `QColor` | INTERNAL |
| `_on_auto_scroll_changed` | LogViewerPanel | `self, state: int` | `None` | INTERNAL |
| `_on_connected` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_on_disconnected` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_on_error` | LogViewerPanel | `self, error_msg: str` | `None` | INTERNAL |
| `_on_export` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_on_level_changed` | LogViewerPanel | `self, level: str` | `None` | INTERNAL |
| `_on_log_received` | LogViewerPanel | `self, data: Dict[str, Any]` | `None` | INTERNAL |
| `_on_pause_clicked` | LogViewerPanel | `self, checked: bool` | `None` | INTERNAL |
| `_on_robot_changed` | LogViewerPanel | `self, index: int` | `None` | INTERNAL |
| `_on_search_changed` | LogViewerPanel | `self, text: str` | `None` | INTERNAL |
| `_setup_dock` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | LogViewerPanel | `self` | `None` | INTERNAL |
| `_toggle_connection` | LogViewerPanel | `self` | `None` | INTERNAL |
| `add_robot` | LogViewerPanel | `self, robot_id: str, robot_name: str` | `None` | USED |
| `cleanup` | LogViewerPanel | `self` | `None` | USED |
| `clear` | LogViewerPanel | `self` | `None` | USED |
| `clear_robots` | LogViewerPanel | `self` | `None` | UNUSED |
| `configure` | LogViewerPanel | `self, orchestrator_url: str, api_secret: str, ...` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.minimap_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\minimap_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MinimapChangeTracker | `self, viewport_tolerance: float` | `None` | DUNDER |
| `_rects_equal` | MinimapChangeTracker | `self, r1: QRectF, r2: QRectF` | `bool` | INTERNAL |
| `commit_update` | MinimapChangeTracker | `self, viewport: QRectF, node_count: int` | `None` | USED |
| `mark_dirty` | MinimapChangeTracker | `self` | `None` | USED |
| `should_update` | MinimapChangeTracker | `self, current_viewport: QRectF, node_count: int` | `bool` | USED |
| `__init__` | MinimapPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | MinimapPanel | `self` | `None` | INTERNAL |
| `_on_update_timer` | MinimapPanel | `self` | `None` | INTERNAL |
| `_on_viewport_clicked` | MinimapPanel | `self, scene_pos: QPointF` | `None` | INTERNAL |
| `_setup_ui` | MinimapPanel | `self` | `None` | INTERNAL |
| `hideEvent` | MinimapPanel | `self, event` | `None` | USED |
| `mark_dirty` | MinimapPanel | `self` | `None` | USED |
| `set_graph_view` | MinimapPanel | `self, graph_view` | `None` | UNUSED |
| `showEvent` | MinimapPanel | `self, event` | `None` | USED |
| `update_minimap` | MinimapPanel | `self` | `None` | USED |
| `__init__` | MinimapView | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `drawForeground` | MinimapView | `self, painter: QPainter, rect: QRectF` | `None` | UNUSED |
| `mousePressEvent` | MinimapView | `self, event` | `-` | USED |
| `set_viewport_rect` | MinimapView | `self, rect: QRectF` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.output_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\output_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | OutputTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | OutputTab | `self` | `None` | INTERNAL |
| `_format_value` | OutputTab | `self, value: Any` | `str` | INTERNAL |
| `_format_value_for_preview` | OutputTab | `self, value: Any` | `str` | INTERNAL |
| `_get_type_name` | OutputTab | `self, value: Any` | `str` | INTERNAL |
| `_on_selection_changed` | OutputTab | `self` | `None` | INTERNAL |
| `_setup_ui` | OutputTab | `self` | `None` | INTERNAL |
| `_update_status` | OutputTab | `self` | `None` | INTERNAL |
| `add_output` | OutputTab | `self, name: str, value: Any, ...` | `None` | USED |
| `clear` | OutputTab | `self` | `None` | USED |
| `get_output_count` | OutputTab | `self` | `int` | USED |
| `get_outputs` | OutputTab | `self` | `dict` | UNUSED |
| `set_workflow_result` | OutputTab | `self, success: bool, message: str` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.process_mining_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\process_mining_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AIEnhanceWorker | `self, insights: List[Dict[str, Any]], model: str, ...` | `None` | DUNDER |
| `async _enhance_async` | AIEnhanceWorker | `self` | `List[Dict[str, Any]]` | INTERNAL |
| `_get_llm_manager` | AIEnhanceWorker | `self` | `-` | INTERNAL |
| `run` | AIEnhanceWorker | `self` | `None` | USED |
| `__init__` | ProcessMiningPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_auto_refresh` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_check_api_key_status` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_create_ai_settings` | ProcessMiningPanel | `self` | `QGroupBox` | INTERNAL |
| `_create_conformance_tab` | ProcessMiningPanel | `self` | `QWidget` | INTERNAL |
| `_create_discovery_tab` | ProcessMiningPanel | `self` | `QWidget` | INTERNAL |
| `_create_header` | ProcessMiningPanel | `self` | `QHBoxLayout` | INTERNAL |
| `_create_insights_tab` | ProcessMiningPanel | `self` | `QWidget` | INTERNAL |
| `_create_stats_group` | ProcessMiningPanel | `self` | `QGroupBox` | INTERNAL |
| `_create_variants_tab` | ProcessMiningPanel | `self` | `QWidget` | INTERNAL |
| `_enhance_insights_with_ai` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_get_llm_manager` | ProcessMiningPanel | `self` | `-` | INTERNAL |
| `_get_miner` | ProcessMiningPanel | `self` | `-` | INTERNAL |
| `_load_workflows` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_on_ai_enhance_error` | ProcessMiningPanel | `self, error_msg: str` | `None` | INTERNAL |
| `_on_ai_enhance_finished` | ProcessMiningPanel | `self, enhanced_insights: List[Dict[str, Any]]` | `None` | INTERNAL |
| `_on_insight_clicked` | ProcessMiningPanel | `self, item: QTreeWidgetItem, column: int` | `None` | INTERNAL |
| `_on_manage_credentials` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_on_provider_changed` | ProcessMiningPanel | `self, provider: str` | `None` | INTERNAL |
| `_on_variant_selected` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_on_workflow_changed` | ProcessMiningPanel | `self, index: int` | `None` | INTERNAL |
| `_refresh_data` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_run_conformance_check` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_run_discovery` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_setup_dock` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_setup_refresh_timer` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_update_insights` | ProcessMiningPanel | `self, insights: List[Dict[str, Any]]` | `None` | INTERNAL |
| `_update_model_display` | ProcessMiningPanel | `self, model: Dict[str, Any]` | `None` | INTERNAL |
| `_update_model_list` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `_update_variants` | ProcessMiningPanel | `self` | `None` | INTERNAL |
| `add_demo_data` | ProcessMiningPanel | `self` | `None` | UNUSED |
| `cleanup` | ProcessMiningPanel | `self` | `None` | USED |
| `get_ai_settings` | ProcessMiningPanel | `self` | `dict` | USED |
| `hideEvent` | ProcessMiningPanel | `self, event` | `None` | USED |
| `showEvent` | ProcessMiningPanel | `self, event` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.properties_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\properties_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CollapsibleSection | `self, title: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `_setup_ui` | CollapsibleSection | `self` | `None` | INTERNAL |
| `_toggle` | CollapsibleSection | `self` | `None` | INTERNAL |
| `add_property_row` | CollapsibleSection | `self, label: str, widget: QWidget` | `QWidget` | USED |
| `add_widget` | CollapsibleSection | `self, widget: QWidget` | `None` | USED |
| `__init__` | PropertiesPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | PropertiesPanel | `self` | `None` | INTERNAL |
| `_build_properties` | PropertiesPanel | `self, node: 'BaseNode'` | `None` | INTERNAL |
| `_clear_properties` | PropertiesPanel | `self` | `None` | INTERNAL |
| `_create_property_widget` | PropertiesPanel | `self, name: str, value: Any, ...` | `Optional[QWidget]` | INTERNAL |
| `_create_target_robot_section` | PropertiesPanel | `self` | `QWidget` | INTERNAL |
| `_on_property_changed` | PropertiesPanel | `self, name: str, value: Any` | `None` | INTERNAL |
| `_on_robot_override_changed` | PropertiesPanel | `self, config: Dict[str, Any]` | `None` | INTERNAL |
| `_on_robot_override_cleared` | PropertiesPanel | `self` | `None` | INTERNAL |
| `_setup_dock` | PropertiesPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | PropertiesPanel | `self` | `None` | INTERNAL |
| `_update_node_override_indicator` | PropertiesPanel | `self, has_override: bool` | `None` | INTERNAL |
| `refresh` | PropertiesPanel | `self` | `None` | USED |
| `set_available_robots` | PropertiesPanel | `self, robots: List[Dict[str, Any]]` | `None` | USED |
| `set_cloud_mode` | PropertiesPanel | `self, enabled: bool` | `None` | USED |
| `set_node` | PropertiesPanel | `self, node: Optional['BaseNode']` | `None` | USED |
| `set_node_override` | PropertiesPanel | `self, override: Optional[Dict[str, Any]]` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.panels.robot_picker_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\robot_picker_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotPickerPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_filter` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_apply_styles` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_can_submit` | RobotPickerPanel | `self` | `bool` | INTERNAL |
| `_create_robot_item` | RobotPickerPanel | `self, robot: 'Robot'` | `QTreeWidgetItem` | INTERNAL |
| `_find_robot_by_id` | RobotPickerPanel | `self, robot_id: str` | `Optional['Robot']` | INTERNAL |
| `_on_filter_changed` | RobotPickerPanel | `self, index: int` | `None` | INTERNAL |
| `_on_mode_changed` | RobotPickerPanel | `self, checked: bool` | `None` | INTERNAL |
| `_on_refresh_clicked` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_on_robot_double_clicked` | RobotPickerPanel | `self, item: QTreeWidgetItem, column: int` | `None` | INTERNAL |
| `_on_robot_selection_changed` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_on_submit_clicked` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_reset_status_label` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_set_status_icon` | RobotPickerPanel | `self, item: QTreeWidgetItem, status: 'RobotStatus'` | `None` | INTERNAL |
| `_setup_dock` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `_update_submit_button_state` | RobotPickerPanel | `self` | `None` | INTERNAL |
| `clear_selection` | RobotPickerPanel | `self` | `None` | USED |
| `get_execution_mode` | RobotPickerPanel | `self` | `str` | USED |
| `get_selected_robot` | RobotPickerPanel | `self` | `Optional[str]` | USED |
| `is_connected` | RobotPickerPanel | `self` | `bool` | USED |
| `refresh` | RobotPickerPanel | `self` | `None` | USED |
| `select_robot` | RobotPickerPanel | `self, robot_id: str` | `bool` | USED |
| `set_connected` | RobotPickerPanel | `self, connected: bool` | `None` | USED |
| `set_execution_mode` | RobotPickerPanel | `self, mode: str` | `None` | USED |
| `set_refreshing` | RobotPickerPanel | `self, refreshing: bool` | `None` | USED |
| `set_submitting` | RobotPickerPanel | `self, submitting: bool` | `None` | USED |
| `show_submit_result` | RobotPickerPanel | `self, success: bool, message: str` | `None` | USED |
| `update_robots` | RobotPickerPanel | `self, robots: List['Robot']` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.terminal_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\terminal_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TerminalTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | TerminalTab | `self` | `None` | INTERNAL |
| `_on_output_received` | TerminalTab | `self, text: str, level: str` | `None` | INTERNAL |
| `_setup_ui` | TerminalTab | `self` | `None` | INTERNAL |
| `append_debug` | TerminalTab | `self, text: str` | `None` | USED |
| `append_error` | TerminalTab | `self, text: str` | `None` | USED |
| `append_info` | TerminalTab | `self, text: str` | `None` | USED |
| `append_success` | TerminalTab | `self, text: str` | `None` | USED |
| `append_warning` | TerminalTab | `self, text: str` | `None` | USED |
| `clear` | TerminalTab | `self` | `None` | USED |
| `get_line_count` | TerminalTab | `self` | `int` | UNUSED |
| `get_text` | TerminalTab | `self` | `str` | USED |
| `write` | TerminalTab | `self, text: str, level: str` | `None` | USED |
| `write_stderr` | TerminalTab | `self, text: str` | `None` | USED |
| `write_stdout` | TerminalTab | `self, text: str` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.validation_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\validation_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ValidationTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_add_issue_group` | ValidationTab | `self, title: str, issues: list, ...` | `None` | INTERNAL |
| `_apply_styles` | ValidationTab | `self` | `None` | INTERNAL |
| `_get_severity_color` | ValidationTab | `self, severity: str` | `QColor` | INTERNAL |
| `_get_severity_prefix` | ValidationTab | `self, severity: str` | `str` | INTERNAL |
| `_on_item_clicked` | ValidationTab | `self, item: QTreeWidgetItem, column: int` | `None` | INTERNAL |
| `_on_item_double_clicked` | ValidationTab | `self, item: QTreeWidgetItem, column: int` | `None` | INTERNAL |
| `_setup_ui` | ValidationTab | `self` | `None` | INTERNAL |
| `_update_status` | ValidationTab | `self, result: 'ValidationResult'` | `None` | INTERNAL |
| `clear` | ValidationTab | `self` | `None` | USED |
| `get_all_errors` | ValidationTab | `self` | `list` | USED |
| `get_issue_count` | ValidationTab | `self` | `tuple` | USED |
| `get_result` | ValidationTab | `self` | `Optional['ValidationResult']` | USED |
| `has_errors` | ValidationTab | `self` | `bool` | USED |
| `set_result` | ValidationTab | `self, result: 'ValidationResult'` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.variable_inspector_dock

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variable_inspector_dock.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VariableInspectorDock | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_setup_ui` | VariableInspectorDock | `self` | `None` | INTERNAL |
| `clear` | VariableInspectorDock | `self` | `None` | USED |
| `update_variables` | VariableInspectorDock | `self, variables: Dict[str, Any]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.variables_panel

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variables_panel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `createEditor` | TypeComboDelegate | `self, parent, option, ...` | `-` | UNUSED |
| `setEditorData` | TypeComboDelegate | `self, editor, index` | `-` | UNUSED |
| `setModelData` | TypeComboDelegate | `self, editor, model, ...` | `-` | UNUSED |
| `__init__` | VariablesPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_scope_filter` | VariablesPanel | `self` | `None` | INTERNAL |
| `_apply_styles` | VariablesPanel | `self` | `None` | INTERNAL |
| `_on_add_variable` | VariablesPanel | `self` | `None` | INTERNAL |
| `_on_clear_all` | VariablesPanel | `self` | `None` | INTERNAL |
| `_on_execution_completed` | VariablesPanel | `self, event: Event` | `None` | INTERNAL |
| `_on_execution_started` | VariablesPanel | `self, event: Event` | `None` | INTERNAL |
| `_on_item_changed` | VariablesPanel | `self, item: QTableWidgetItem` | `None` | INTERNAL |
| `_on_remove_variable` | VariablesPanel | `self` | `None` | INTERNAL |
| `_on_scope_filter_changed` | VariablesPanel | `self, scope: str` | `None` | INTERNAL |
| `_on_variable_deleted_event` | VariablesPanel | `self, event: Event` | `None` | INTERNAL |
| `_on_variable_set_event` | VariablesPanel | `self, event: Event` | `None` | INTERNAL |
| `_on_variable_updated_event` | VariablesPanel | `self, event: Event` | `None` | INTERNAL |
| `_setup_dock` | VariablesPanel | `self` | `None` | INTERNAL |
| `_setup_lazy_subscriptions` | VariablesPanel | `self` | `None` | INTERNAL |
| `_setup_ui` | VariablesPanel | `self` | `None` | INTERNAL |
| `add_variable` | VariablesPanel | `self, name: str, var_type: str, ...` | `None` | USED |
| `clear_variables` | VariablesPanel | `self` | `None` | USED |
| `get_variables` | VariablesPanel | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `remove_variable` | VariablesPanel | `self, name: str` | `None` | USED |
| `set_runtime_mode` | VariablesPanel | `self, enabled: bool` | `None` | USED |
| `update_variable_value` | VariablesPanel | `self, name: str, value: Any` | `None` | USED |


## casare_rpa.presentation.canvas.ui.panels.variables_tab

**File:** `src\casare_rpa\presentation\canvas\ui\panels\variables_tab.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VariablesTab | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `clear` | VariablesTab | `self` | `None` | USED |
| `get_variables` | VariablesTab | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `set_runtime_mode` | VariablesTab | `self, enabled: bool` | `None` | USED |
| `set_variables` | VariablesTab | `self, variables: Dict[str, Dict[str, Any]]` | `None` | USED |
| `update_runtime_values` | VariablesTab | `self, values: Dict[str, Any]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.signal_bridge

**File:** `src\casare_rpa\presentation\canvas\ui\signal_bridge.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BottomPanelSignalBridge | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `connect_bottom_panel` | BottomPanelSignalBridge | `self, panel` | `None` | UNUSED |
| `connect_execution_timeline` | BottomPanelSignalBridge | `self, timeline, dock` | `None` | UNUSED |
| `connect_properties_panel` | BottomPanelSignalBridge | `self, panel` | `None` | UNUSED |
| `connect_variable_inspector` | BottomPanelSignalBridge | `self, dock` | `None` | UNUSED |
| `__init__` | ControllerSignalBridge | `self, main_window: 'MainWindow'` | `None` | DUNDER |
| `_connect_execution_controller` | ControllerSignalBridge | `self, controller: 'ExecutionController'` | `None` | INTERNAL |
| `_connect_node_controller` | ControllerSignalBridge | `self, controller: 'NodeController'` | `None` | INTERNAL |
| `_connect_panel_controller` | ControllerSignalBridge | `self, controller: 'PanelController'` | `None` | INTERNAL |
| `_connect_workflow_controller` | ControllerSignalBridge | `self, controller: 'WorkflowController'` | `None` | INTERNAL |
| `_on_current_file_changed` | ControllerSignalBridge | `self, file` | `None` | INTERNAL |
| `_on_execution_completed` | ControllerSignalBridge | `self` | `None` | INTERNAL |
| `_on_execution_error` | ControllerSignalBridge | `self, error: str` | `None` | INTERNAL |
| `_on_execution_started` | ControllerSignalBridge | `self` | `None` | INTERNAL |
| `_on_execution_stopped` | ControllerSignalBridge | `self` | `None` | INTERNAL |
| `_on_modified_changed` | ControllerSignalBridge | `self, modified: bool` | `None` | INTERNAL |
| `connect_all_controllers` | ControllerSignalBridge | `self, workflow_controller: Optional['WorkflowController'], execution_controller: Optional['ExecutionController'], ...` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.toolbars.hotkey_manager

**File:** `src\casare_rpa\presentation\canvas\ui\toolbars\hotkey_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HotkeyEditor | `self, action_name: str, current_shortcut: str, ...` | `-` | DUNDER |
| `_accept` | HotkeyEditor | `self` | `-` | INTERNAL |
| `_clear_shortcut` | HotkeyEditor | `self` | `-` | INTERNAL |
| `_setup_ui` | HotkeyEditor | `self` | `-` | INTERNAL |
| `get_shortcut` | HotkeyEditor | `self` | `str` | USED |
| `keyPressEvent` | HotkeyEditor | `self, event` | `-` | USED |
| `__init__` | HotkeyManagerDialog | `self, actions: Dict[str, QAction], parent` | `-` | DUNDER |
| `_check_conflict` | HotkeyManagerDialog | `self, current_action: str, new_shortcut: str` | `bool` | INTERNAL |
| `_edit_hotkey` | HotkeyManagerDialog | `self, index` | `-` | INTERNAL |
| `_filter_table` | HotkeyManagerDialog | `self` | `-` | INTERNAL |
| `_populate_table` | HotkeyManagerDialog | `self` | `-` | INTERNAL |
| `_reset_all` | HotkeyManagerDialog | `self` | `-` | INTERNAL |
| `_save_hotkeys` | HotkeyManagerDialog | `self` | `-` | INTERNAL |
| `_setup_ui` | HotkeyManagerDialog | `self` | `-` | INTERNAL |


## casare_rpa.presentation.canvas.ui.toolbars.main_toolbar

**File:** `src\casare_rpa\presentation\canvas\ui\toolbars\main_toolbar.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MainToolbar | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | MainToolbar | `self` | `None` | INTERNAL |
| `_create_actions` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_new` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_open` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_pause` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_redo` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_resume` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_run` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_save` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_save_as` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_stop` | MainToolbar | `self` | `None` | INTERNAL |
| `_on_undo` | MainToolbar | `self` | `None` | INTERNAL |
| `_update_actions_state` | MainToolbar | `self` | `None` | INTERNAL |
| `set_execution_state` | MainToolbar | `self, is_running: bool, is_paused: bool` | `None` | UNUSED |
| `set_redo_enabled` | MainToolbar | `self, enabled: bool` | `None` | UNUSED |
| `set_undo_enabled` | MainToolbar | `self, enabled: bool` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\ai_settings_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `detect_provider_from_model` | - | `model: str` | `str` | USED |
| `get_all_models` | - | `` | `List[str]` | USED |
| `get_llm_credentials` | - | `` | `List[Dict[str, Any]]` | USED |
| `__init__` | AISettingsWidget | `self, parent: Optional[QWidget], title: str, ...` | `None` | DUNDER |
| `_connect_signals` | AISettingsWidget | `self` | `None` | INTERNAL |
| `_emit_settings_changed` | AISettingsWidget | `self` | `None` | INTERNAL |
| `_load_credentials` | AISettingsWidget | `self` | `None` | INTERNAL |
| `_on_credential_changed` | AISettingsWidget | `self, index: int` | `None` | INTERNAL |
| `_on_model_changed` | AISettingsWidget | `self, model: str` | `None` | INTERNAL |
| `_on_provider_changed` | AISettingsWidget | `self, provider: str` | `None` | INTERNAL |
| `_setup_ui` | AISettingsWidget | `self` | `None` | INTERNAL |
| `_update_models` | AISettingsWidget | `self` | `None` | INTERNAL |
| `apply_dark_style` | AISettingsWidget | `self` | `None` | UNUSED |
| `get_credential_id` | AISettingsWidget | `self` | `Optional[str]` | UNUSED |
| `get_model` | AISettingsWidget | `self` | `str` | UNUSED |
| `get_provider` | AISettingsWidget | `self` | `str` | UNUSED |
| `get_settings` | AISettingsWidget | `self` | `Dict[str, Any]` | USED |
| `refresh_credentials` | AISettingsWidget | `self` | `None` | UNUSED |
| `set_model` | AISettingsWidget | `self, model: str` | `None` | UNUSED |
| `set_provider` | AISettingsWidget | `self, provider: str` | `None` | UNUSED |
| `set_settings` | AISettingsWidget | `self, settings: Dict[str, Any]` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.widgets.execution_timeline

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\execution_timeline.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionTimeline | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | ExecutionTimeline | `self` | `None` | INTERNAL |
| `_rebuild_timeline` | ExecutionTimeline | `self` | `None` | INTERNAL |
| `_setup_ui` | ExecutionTimeline | `self` | `None` | INTERNAL |
| `add_event` | ExecutionTimeline | `self, node_id: str, node_name: str, ...` | `None` | USED |
| `clear` | ExecutionTimeline | `self` | `None` | USED |
| `end_execution` | ExecutionTimeline | `self` | `None` | USED |
| `get_events` | ExecutionTimeline | `self` | `List[TimelineEvent]` | UNUSED |
| `start_execution` | ExecutionTimeline | `self` | `None` | USED |
| `__init__` | TimelineBar | `self, event: TimelineEvent, start_time: datetime, ...` | `None` | DUNDER |
| `enterEvent` | TimelineBar | `self, event` | `None` | UNUSED |
| `leaveEvent` | TimelineBar | `self, event` | `None` | UNUSED |
| `mousePressEvent` | TimelineBar | `self, event` | `None` | USED |
| `paintEvent` | TimelineBar | `self, event` | `None` | UNUSED |


## casare_rpa.presentation.canvas.ui.widgets.output_console_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\output_console_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | OutputConsoleWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_on_auto_scroll_toggled` | OutputConsoleWidget | `self, checked: bool` | `None` | INTERNAL |
| `_on_copy` | OutputConsoleWidget | `self` | `None` | INTERNAL |
| `_on_timestamps_toggled` | OutputConsoleWidget | `self, checked: bool` | `None` | INTERNAL |
| `append_debug` | OutputConsoleWidget | `self, text: str` | `None` | USED |
| `append_error` | OutputConsoleWidget | `self, text: str` | `None` | USED |
| `append_info` | OutputConsoleWidget | `self, text: str` | `None` | USED |
| `append_line` | OutputConsoleWidget | `self, text: str, level: str, ...` | `None` | USED |
| `append_success` | OutputConsoleWidget | `self, text: str` | `None` | USED |
| `append_warning` | OutputConsoleWidget | `self, text: str` | `None` | USED |
| `clear` | OutputConsoleWidget | `self` | `None` | USED |
| `get_text` | OutputConsoleWidget | `self` | `str` | USED |
| `set_auto_scroll` | OutputConsoleWidget | `self, enabled: bool` | `None` | UNUSED |
| `set_max_lines` | OutputConsoleWidget | `self, max_lines: int` | `None` | UNUSED |
| `set_show_timestamps` | OutputConsoleWidget | `self, enabled: bool` | `None` | UNUSED |
| `setup_ui` | OutputConsoleWidget | `self` | `None` | USED |


## casare_rpa.presentation.canvas.ui.widgets.performance_dashboard

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\performance_dashboard.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `show_performance_dashboard` | - | `parent: Optional[QWidget]` | `None` | UNUSED |
| `__init__` | CountersGaugesPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_metrics` | CountersGaugesPanel | `self, counters: Dict[str, int], gauges: Dict[str, float]` | `None` | USED |
| `__init__` | HistogramWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_data` | HistogramWidget | `self, histogram_data: Dict[str, Any]` | `None` | USED |
| `__init__` | MetricCard | `self, title: str, value: str, ...` | `None` | DUNDER |
| `set_color` | MetricCard | `self, color: str` | `None` | USED |
| `set_value` | MetricCard | `self, value: str, subtitle: str` | `None` | USED |
| `__init__` | NodeMetricsPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_metrics` | NodeMetricsPanel | `self, node_data: Dict[str, Any]` | `None` | USED |
| `__init__` | PerformanceDashboardDialog | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_collect_pool_metrics` | PerformanceDashboardDialog | `self` | `Dict[str, Dict[str, Any]]` | INTERNAL |
| `_connect_signals` | PerformanceDashboardDialog | `self` | `None` | INTERNAL |
| `_refresh_metrics` | PerformanceDashboardDialog | `self` | `None` | INTERNAL |
| `_reset_metrics` | PerformanceDashboardDialog | `self` | `None` | INTERNAL |
| `_setup_ui` | PerformanceDashboardDialog | `self` | `None` | INTERNAL |
| `_start_refresh` | PerformanceDashboardDialog | `self` | `None` | INTERNAL |
| `_update_refresh_interval` | PerformanceDashboardDialog | `self, interval_text: str` | `None` | INTERNAL |
| `closeEvent` | PerformanceDashboardDialog | `self, event` | `None` | USED |
| `register_pool_callback` | PerformanceDashboardDialog | `self, callback` | `None` | UNUSED |
| `__init__` | PoolMetricsPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_metrics` | PoolMetricsPanel | `self, pool_data: Dict[str, Dict[str, Any]]` | `None` | USED |
| `__init__` | SystemMetricsPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_metrics` | SystemMetricsPanel | `self, system_data: Dict[str, Any]` | `None` | USED |
| `__init__` | WorkflowMetricsPanel | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `update_metrics` | WorkflowMetricsPanel | `self, workflow_data: Dict[str, Any]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.widgets.robot_override_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\robot_override_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotOverrideWidget | `self, parent: Optional[QWidget]` | `None` | DUNDER |
| `_apply_styles` | RobotOverrideWidget | `self` | `None` | INTERNAL |
| `_connect_signals` | RobotOverrideWidget | `self` | `None` | INTERNAL |
| `_emit_override_changed` | RobotOverrideWidget | `self` | `None` | INTERNAL |
| `_on_clear_clicked` | RobotOverrideWidget | `self` | `None` | INTERNAL |
| `_on_enable_changed` | RobotOverrideWidget | `self, enabled: bool` | `None` | INTERNAL |
| `_on_mode_changed` | RobotOverrideWidget | `self, index: int` | `None` | INTERNAL |
| `_setup_ui` | RobotOverrideWidget | `self` | `None` | INTERNAL |
| `get_override` | RobotOverrideWidget | `self` | `Optional[Dict[str, Any]]` | USED |
| `is_override_enabled` | RobotOverrideWidget | `self` | `bool` | UNUSED |
| `set_available_robots` | RobotOverrideWidget | `self, robots: List[Dict[str, Any]]` | `None` | USED |
| `set_cloud_mode` | RobotOverrideWidget | `self, enabled: bool` | `None` | USED |
| `set_override` | RobotOverrideWidget | `self, override: Optional[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.widgets.search_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\search_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SearchWidget | `self, placeholder: str, parent: Optional[QWidget]` | `None` | DUNDER |
| `_matches` | SearchWidget | `self, query: str, text: str` | `bool` | INTERNAL |
| `_on_item_activated` | SearchWidget | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_item_double_clicked` | SearchWidget | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_on_return_pressed` | SearchWidget | `self` | `None` | INTERNAL |
| `_on_search_changed` | SearchWidget | `self, text: str` | `None` | INTERNAL |
| `_select_item` | SearchWidget | `self, item: QListWidgetItem` | `None` | INTERNAL |
| `_update_results` | SearchWidget | `self` | `None` | INTERNAL |
| `_update_results_label` | SearchWidget | `self` | `None` | INTERNAL |
| `add_item` | SearchWidget | `self, text: str, data: object` | `None` | UNUSED |
| `clear_items` | SearchWidget | `self` | `None` | UNUSED |
| `clear_search` | SearchWidget | `self` | `None` | UNUSED |
| `eventFilter` | SearchWidget | `self, obj, event` | `bool` | USED |
| `focus_search` | SearchWidget | `self` | `None` | UNUSED |
| `set_fuzzy_match_function` | SearchWidget | `self, func: Callable[[str, str], bool]` | `None` | UNUSED |
| `set_items` | SearchWidget | `self, items: List[tuple]` | `None` | UNUSED |
| `setup_ui` | SearchWidget | `self` | `None` | USED |


## casare_rpa.presentation.canvas.ui.widgets.tenant_selector

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\tenant_selector.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TenantFilterWidget | `self, parent: Optional[QWidget], show_all_option: bool` | `None` | DUNDER |
| `_refresh_dropdown` | TenantFilterWidget | `self` | `None` | INTERNAL |
| `__init__` | TenantSelectorWidget | `self, parent: Optional[QWidget], show_all_option: bool, ...` | `None` | DUNDER |
| `_apply_styles` | TenantSelectorWidget | `self` | `None` | INTERNAL |
| `_on_refresh` | TenantSelectorWidget | `self` | `None` | INTERNAL |
| `_on_selection_changed` | TenantSelectorWidget | `self, index: int` | `None` | INTERNAL |
| `_refresh_dropdown` | TenantSelectorWidget | `self` | `None` | INTERNAL |
| `_setup_ui` | TenantSelectorWidget | `self` | `None` | INTERNAL |
| `count` | TenantSelectorWidget | `self` | `int` | USED |
| `get_current_tenant_id` | TenantSelectorWidget | `self` | `Optional[str]` | USED |
| `get_current_tenant_name` | TenantSelectorWidget | `self` | `str` | UNUSED |
| `is_all_tenants_selected` | TenantSelectorWidget | `self` | `bool` | UNUSED |
| `setEnabled` | TenantSelectorWidget | `self, enabled: bool` | `None` | USED |
| `set_current_tenant` | TenantSelectorWidget | `self, tenant_id: Optional[str]` | `None` | USED |
| `set_show_all_option` | TenantSelectorWidget | `self, show: bool` | `None` | UNUSED |
| `set_show_refresh` | TenantSelectorWidget | `self, show: bool` | `None` | UNUSED |
| `set_super_admin` | TenantSelectorWidget | `self, is_super_admin: bool` | `None` | USED |
| `update_tenants` | TenantSelectorWidget | `self, tenants: List[Dict[str, Any]]` | `None` | USED |


## casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget

**File:** `src\casare_rpa\presentation\canvas\ui\widgets\variable_editor_widget.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VariableEditorWidget | `self, name: str, var_type: str, ...` | `None` | DUNDER |
| `_convert_value` | VariableEditorWidget | `self, value: str, var_type: str` | `Any` | INTERNAL |
| `_on_value_changed` | VariableEditorWidget | `self` | `None` | INTERNAL |
| `get_remove_button` | VariableEditorWidget | `self` | `QPushButton` | UNUSED |
| `get_variable` | VariableEditorWidget | `self` | `Dict[str, Any]` | USED |
| `set_variable` | VariableEditorWidget | `self, name: str, var_type: str, ...` | `None` | USED |
| `setup_ui` | VariableEditorWidget | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.ai_ml.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\ai_ml\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_llm_credentials` | - | `` | `List[Tuple[str, str]]` | USED |
| `get_models_for_credential` | - | `credential_name: str` | `List[str]` | USED |
| `_on_credential_changed` | LLMVisualNodeMixin | `self, property_name: str, credential_name: str` | `None` | INTERNAL |
| `_setup_credential_model_link` | LLMVisualNodeMixin | `self` | `None` | INTERNAL |
| `__init__` | VisualLLMChatNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMChatNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMChatNode | `self` | `None` | USED |
| `__init__` | VisualLLMClassifyNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMClassifyNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMClassifyNode | `self` | `None` | USED |
| `__init__` | VisualLLMCompletionNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMCompletionNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMCompletionNode | `self` | `None` | USED |
| `__init__` | VisualLLMExtractDataNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMExtractDataNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMExtractDataNode | `self` | `None` | USED |
| `__init__` | VisualLLMSummarizeNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMSummarizeNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMSummarizeNode | `self` | `None` | USED |
| `__init__` | VisualLLMTranslateNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualLLMTranslateNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualLLMTranslateNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.base_visual_node

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\base_visual_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualNode | `self` | `None` | DUNDER |
| `_apply_category_colors` | VisualNode | `self` | `None` | INTERNAL |
| `_auto_create_casare_node` | VisualNode | `self` | `None` | INTERNAL |
| `_auto_create_widgets_from_schema` | VisualNode | `self` | `None` | INTERNAL |
| `_configure_port_colors` | VisualNode | `self` | `None` | INTERNAL |
| `_create_temp_icon` | VisualNode | `self` | `str` | INTERNAL |
| `_style_text_inputs` | VisualNode | `self` | `None` | INTERNAL |
| `add_exec_input` | VisualNode | `self, name: str` | `None` | USED |
| `add_exec_output` | VisualNode | `self, name: str` | `None` | USED |
| `add_typed_input` | VisualNode | `self, name: str, data_type: DataType` | `None` | USED |
| `add_typed_output` | VisualNode | `self, name: str, data_type: DataType` | `None` | USED |
| `ensure_casare_node` | VisualNode | `self` | `Optional[CasareBaseNode]` | UNUSED |
| `get_casare_node` | VisualNode | `self` | `Optional[CasareBaseNode]` | USED |
| `get_port_type` | VisualNode | `self, port_name: str` | `Optional[DataType]` | USED |
| `is_exec_port` | VisualNode | `self, port_name: str` | `bool` | USED |
| `set_casare_node` | VisualNode | `self, node: CasareBaseNode` | `None` | USED |
| `setup_ports` | VisualNode | `self` | `None` | USED |
| `sync_types_from_casare_node` | VisualNode | `self` | `None` | UNUSED |
| `update_execution_time` | VisualNode | `self, time_seconds: Optional[float]` | `None` | USED |
| `update_status` | VisualNode | `self, status: str` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.basic.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\basic\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualCommentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCommentNode | `self` | `None` | USED |
| `setup_ports` | VisualEndNode | `self` | `None` | USED |
| `setup_ports` | VisualStartNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.browser.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\browser\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualClickElementNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualClickElementNode | `self` | `None` | USED |
| `setup_ports` | VisualCloseBrowserNode | `self` | `None` | USED |
| `__init__` | VisualDownloadFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDownloadFileNode | `self` | `None` | USED |
| `__init__` | VisualExtractTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExtractTextNode | `self` | `None` | USED |
| `__init__` | VisualGetAllImagesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetAllImagesNode | `self` | `None` | USED |
| `__init__` | VisualGetAttributeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetAttributeNode | `self` | `None` | USED |
| `__init__` | VisualGoBackNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGoBackNode | `self` | `None` | USED |
| `__init__` | VisualGoForwardNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGoForwardNode | `self` | `None` | USED |
| `__init__` | VisualGoToURLNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGoToURLNode | `self` | `None` | USED |
| `__init__` | VisualLaunchBrowserNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualLaunchBrowserNode | `self` | `None` | USED |
| `setup_ports` | VisualNewTabNode | `self` | `None` | USED |
| `__init__` | VisualRefreshPageNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRefreshPageNode | `self` | `None` | USED |
| `__init__` | VisualScreenshotNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualScreenshotNode | `self` | `None` | USED |
| `__init__` | VisualSelectDropdownNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSelectDropdownNode | `self` | `None` | USED |
| `__init__` | VisualTypeTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTypeTextNode | `self` | `None` | USED |
| `__init__` | VisualWaitForElementNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWaitForElementNode | `self` | `None` | USED |
| `__init__` | VisualWaitForNavigationNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWaitForNavigationNode | `self` | `None` | USED |
| `__init__` | VisualWaitNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWaitNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.control_flow.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\control_flow\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualBreakNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualBreakNode | `self` | `None` | USED |
| `__init__` | VisualCatchNode | `self` | `None` | DUNDER |
| `set_paired_try` | VisualCatchNode | `self, try_node_id: str` | `None` | USED |
| `setup_ports` | VisualCatchNode | `self` | `None` | USED |
| `__init__` | VisualContinueNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualContinueNode | `self` | `None` | USED |
| `__init__` | VisualFinallyNode | `self` | `None` | DUNDER |
| `set_paired_try` | VisualFinallyNode | `self, try_node_id: str` | `None` | USED |
| `setup_ports` | VisualFinallyNode | `self` | `None` | USED |
| `__init__` | VisualForLoopEndNode | `self` | `None` | DUNDER |
| `set_paired_start` | VisualForLoopEndNode | `self, start_node_id: str` | `None` | USED |
| `setup_ports` | VisualForLoopEndNode | `self` | `None` | USED |
| `__init__` | VisualForLoopNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualForLoopNode | `self` | `None` | USED |
| `__init__` | VisualForLoopStartNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualForLoopStartNode | `self` | `None` | USED |
| `__init__` | VisualForkJoinNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualForkJoinNode | `self` | `None` | USED |
| `__init__` | VisualForkNode | `self` | `None` | DUNDER |
| `set_paired_join` | VisualForkNode | `self, join_node_id: str` | `None` | USED |
| `setup_ports` | VisualForkNode | `self` | `None` | USED |
| `__init__` | VisualIfNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualIfNode | `self` | `None` | USED |
| `__init__` | VisualJoinNode | `self` | `None` | DUNDER |
| `set_paired_fork` | VisualJoinNode | `self, fork_node_id: str` | `None` | USED |
| `setup_ports` | VisualJoinNode | `self` | `None` | USED |
| `__init__` | VisualMergeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualMergeNode | `self` | `None` | USED |
| `__init__` | VisualParallelForEachNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualParallelForEachNode | `self` | `None` | USED |
| `__init__` | VisualSwitchNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSwitchNode | `self` | `None` | USED |
| `__init__` | VisualTryCatchFinallyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTryCatchFinallyNode | `self` | `None` | USED |
| `__init__` | VisualTryNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTryNode | `self` | `None` | USED |
| `__init__` | VisualWhileLoopEndNode | `self` | `None` | DUNDER |
| `set_paired_start` | VisualWhileLoopEndNode | `self, start_node_id: str` | `None` | USED |
| `setup_ports` | VisualWhileLoopEndNode | `self` | `None` | USED |
| `__init__` | VisualWhileLoopNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWhileLoopNode | `self` | `None` | USED |
| `__init__` | VisualWhileLoopStartNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWhileLoopStartNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\data_operations\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_node_class` | VisualComparisonNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualComparisonNode | `self` | `-` | USED |
| `get_node_class` | VisualConcatenateNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualConcatenateNode | `self` | `None` | USED |
| `get_node_class` | VisualCreateDictNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualCreateDictNode | `self` | `-` | USED |
| `get_node_class` | VisualCreateListNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualCreateListNode | `self` | `None` | USED |
| `__init__` | VisualDictGetNode | `self` | `-` | DUNDER |
| `get_node_class` | VisualDictGetNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictGetNode | `self` | `-` | USED |
| `__init__` | VisualDictHasKeyNode | `self` | `-` | DUNDER |
| `get_node_class` | VisualDictHasKeyNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictHasKeyNode | `self` | `-` | USED |
| `get_node_class` | VisualDictItemsNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictItemsNode | `self` | `-` | USED |
| `get_node_class` | VisualDictKeysNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictKeysNode | `self` | `-` | USED |
| `get_node_class` | VisualDictMergeNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictMergeNode | `self` | `-` | USED |
| `__init__` | VisualDictRemoveNode | `self` | `-` | DUNDER |
| `get_node_class` | VisualDictRemoveNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictRemoveNode | `self` | `-` | USED |
| `__init__` | VisualDictSetNode | `self` | `-` | DUNDER |
| `get_node_class` | VisualDictSetNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictSetNode | `self` | `-` | USED |
| `get_node_class` | VisualDictToJsonNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictToJsonNode | `self` | `-` | USED |
| `get_node_class` | VisualDictValuesNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualDictValuesNode | `self` | `-` | USED |
| `get_node_class` | VisualFormatStringNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualFormatStringNode | `self` | `None` | USED |
| `get_node_class` | VisualGetPropertyNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualGetPropertyNode | `self` | `None` | USED |
| `get_node_class` | VisualJsonParseNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualJsonParseNode | `self` | `None` | USED |
| `get_node_class` | VisualListAppendNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListAppendNode | `self` | `-` | USED |
| `get_node_class` | VisualListContainsNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListContainsNode | `self` | `-` | USED |
| `get_node_class` | VisualListFilterNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListFilterNode | `self` | `-` | USED |
| `get_node_class` | VisualListFlattenNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListFlattenNode | `self` | `-` | USED |
| `get_node_class` | VisualListGetItemNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualListGetItemNode | `self` | `None` | USED |
| `get_node_class` | VisualListJoinNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListJoinNode | `self` | `-` | USED |
| `get_node_class` | VisualListLengthNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListLengthNode | `self` | `-` | USED |
| `get_node_class` | VisualListMapNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListMapNode | `self` | `-` | USED |
| `get_node_class` | VisualListReduceNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListReduceNode | `self` | `-` | USED |
| `get_node_class` | VisualListReverseNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListReverseNode | `self` | `-` | USED |
| `__init__` | VisualListSliceNode | `self` | `-` | DUNDER |
| `get_node_class` | VisualListSliceNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListSliceNode | `self` | `-` | USED |
| `get_node_class` | VisualListSortNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListSortNode | `self` | `-` | USED |
| `get_node_class` | VisualListUniqueNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualListUniqueNode | `self` | `-` | USED |
| `get_node_class` | VisualMathOperationNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualMathOperationNode | `self` | `-` | USED |
| `get_node_class` | VisualRegexMatchNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRegexMatchNode | `self` | `None` | USED |
| `get_node_class` | VisualRegexReplaceNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualRegexReplaceNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.database.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\database\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualBeginTransactionNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualBeginTransactionNode | `self` | `None` | USED |
| `__init__` | VisualCloseDatabaseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCloseDatabaseNode | `self` | `None` | USED |
| `__init__` | VisualCommitTransactionNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCommitTransactionNode | `self` | `None` | USED |
| `__init__` | VisualDatabaseConnectNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDatabaseConnectNode | `self` | `None` | USED |
| `__init__` | VisualExecuteBatchNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExecuteBatchNode | `self` | `None` | USED |
| `__init__` | VisualExecuteNonQueryNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExecuteNonQueryNode | `self` | `None` | USED |
| `__init__` | VisualExecuteQueryNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExecuteQueryNode | `self` | `None` | USED |
| `__init__` | VisualGetTableColumnsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetTableColumnsNode | `self` | `None` | USED |
| `__init__` | VisualRollbackTransactionNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRollbackTransactionNode | `self` | `None` | USED |
| `__init__` | VisualTableExistsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTableExistsNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.desktop_automation.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\desktop_automation\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualActivateWindowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualActivateWindowNode | `self` | `None` | USED |
| `__init__` | VisualCaptureElementImageNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCaptureElementImageNode | `self` | `None` | USED |
| `__init__` | VisualCaptureScreenshotNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCaptureScreenshotNode | `self` | `None` | USED |
| `__init__` | VisualCheckCheckboxNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCheckCheckboxNode | `self` | `None` | USED |
| `__init__` | VisualClickElementDesktopNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualClickElementDesktopNode | `self` | `None` | USED |
| `__init__` | VisualCloseApplicationNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCloseApplicationNode | `self` | `None` | USED |
| `__init__` | VisualCompareImagesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCompareImagesNode | `self` | `None` | USED |
| `__init__` | VisualDesktopWaitForElementNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDesktopWaitForElementNode | `self` | `None` | USED |
| `__init__` | VisualDragMouseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDragMouseNode | `self` | `None` | USED |
| `__init__` | VisualExpandTreeItemNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExpandTreeItemNode | `self` | `None` | USED |
| `__init__` | VisualFindElementNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFindElementNode | `self` | `None` | USED |
| `__init__` | VisualGetElementPropertyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetElementPropertyNode | `self` | `None` | USED |
| `__init__` | VisualGetElementTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetElementTextNode | `self` | `None` | USED |
| `setup_ports` | VisualGetMousePositionNode | `self` | `None` | USED |
| `__init__` | VisualGetWindowListNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetWindowListNode | `self` | `None` | USED |
| `setup_ports` | VisualGetWindowPropertiesNode | `self` | `None` | USED |
| `__init__` | VisualLaunchApplicationNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualLaunchApplicationNode | `self` | `None` | USED |
| `setup_ports` | VisualMaximizeWindowNode | `self` | `None` | USED |
| `setup_ports` | VisualMinimizeWindowNode | `self` | `None` | USED |
| `__init__` | VisualMouseClickNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualMouseClickNode | `self` | `None` | USED |
| `__init__` | VisualMoveMouseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualMoveMouseNode | `self` | `None` | USED |
| `__init__` | VisualMoveWindowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualMoveWindowNode | `self` | `None` | USED |
| `__init__` | VisualOCRExtractTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualOCRExtractTextNode | `self` | `None` | USED |
| `__init__` | VisualResizeWindowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualResizeWindowNode | `self` | `None` | USED |
| `setup_ports` | VisualRestoreWindowNode | `self` | `None` | USED |
| `__init__` | VisualScrollElementNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualScrollElementNode | `self` | `None` | USED |
| `__init__` | VisualSelectFromDropdownNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSelectFromDropdownNode | `self` | `None` | USED |
| `setup_ports` | VisualSelectRadioButtonNode | `self` | `None` | USED |
| `__init__` | VisualSelectTabNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSelectTabNode | `self` | `None` | USED |
| `__init__` | VisualSendHotKeyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSendHotKeyNode | `self` | `None` | USED |
| `__init__` | VisualSendKeysNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSendKeysNode | `self` | `None` | USED |
| `__init__` | VisualSetWindowStateNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSetWindowStateNode | `self` | `None` | USED |
| `__init__` | VisualTypeTextDesktopNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTypeTextDesktopNode | `self` | `None` | USED |
| `__init__` | VisualVerifyElementExistsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualVerifyElementExistsNode | `self` | `None` | USED |
| `__init__` | VisualVerifyElementPropertyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualVerifyElementPropertyNode | `self` | `None` | USED |
| `__init__` | VisualWaitForWindowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWaitForWindowNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.document.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\document\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_llm_credentials` | - | `` | `List[Tuple[str, str]]` | USED |
| `__init__` | VisualClassifyDocumentNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualClassifyDocumentNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualClassifyDocumentNode | `self` | `None` | USED |
| `__init__` | VisualExtractFormNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualExtractFormNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualExtractFormNode | `self` | `None` | USED |
| `__init__` | VisualExtractInvoiceNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualExtractInvoiceNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualExtractInvoiceNode | `self` | `None` | USED |
| `__init__` | VisualExtractTableNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualExtractTableNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualExtractTableNode | `self` | `None` | USED |
| `__init__` | VisualValidateExtractionNode | `self` | `None` | DUNDER |
| `_create_widgets` | VisualValidateExtractionNode | `self` | `None` | INTERNAL |
| `setup_ports` | VisualValidateExtractionNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.email.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\email\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualDeleteEmailNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualDeleteEmailNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualDeleteEmailNode | `self` | `None` | USED |
| `__init__` | VisualFilterEmailsNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualFilterEmailsNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualFilterEmailsNode | `self` | `None` | USED |
| `__init__` | VisualGetEmailContentNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualGetEmailContentNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualGetEmailContentNode | `self` | `None` | USED |
| `__init__` | VisualMarkEmailNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualMarkEmailNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualMarkEmailNode | `self` | `None` | USED |
| `__init__` | VisualMoveEmailNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualMoveEmailNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualMoveEmailNode | `self` | `None` | USED |
| `__init__` | VisualReadEmailsNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualReadEmailsNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualReadEmailsNode | `self` | `None` | USED |
| `__init__` | VisualSaveAttachmentNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualSaveAttachmentNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualSaveAttachmentNode | `self` | `None` | USED |
| `__init__` | VisualSendEmailNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualSendEmailNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualSendEmailNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\error_handling\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `setup_ports` | VisualAssertNode | `self` | `None` | USED |
| `setup_ports` | VisualErrorRecoveryNode | `self` | `None` | USED |
| `get_node_class` | VisualLogErrorNode | `self` | `-` | UNUSED |
| `setup_ports` | VisualLogErrorNode | `self` | `None` | USED |
| `setup_ports` | VisualOnErrorNode | `self` | `None` | USED |
| `setup_ports` | VisualRetryFailNode | `self` | `None` | USED |
| `setup_ports` | VisualRetryNode | `self` | `None` | USED |
| `setup_ports` | VisualRetrySuccessNode | `self` | `None` | USED |
| `setup_ports` | VisualThrowErrorNode | `self` | `None` | USED |
| `setup_ports` | VisualWebhookNotifyNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\file_operations\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualAppendFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualAppendFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualAppendFileNode | `self` | `None` | USED |
| `__init__` | VisualCopyFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualCopyFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualCopyFileNode | `self` | `None` | USED |
| `__init__` | VisualDeleteFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualDeleteFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualDeleteFileNode | `self` | `None` | USED |
| `setup_ports` | VisualExtractPDFPagesNode | `self` | `None` | USED |
| `__init__` | VisualFTPConnectNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFTPConnectNode | `self` | `None` | USED |
| `setup_ports` | VisualFTPDeleteNode | `self` | `None` | USED |
| `setup_ports` | VisualFTPDisconnectNode | `self` | `None` | USED |
| `__init__` | VisualFTPDownloadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFTPDownloadNode | `self` | `None` | USED |
| `setup_ports` | VisualFTPGetSizeNode | `self` | `None` | USED |
| `__init__` | VisualFTPListNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFTPListNode | `self` | `None` | USED |
| `__init__` | VisualFTPMakeDirNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFTPMakeDirNode | `self` | `None` | USED |
| `setup_ports` | VisualFTPRemoveDirNode | `self` | `None` | USED |
| `setup_ports` | VisualFTPRenameNode | `self` | `None` | USED |
| `__init__` | VisualFTPUploadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFTPUploadNode | `self` | `None` | USED |
| `__init__` | VisualFileExistsNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualFileExistsNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualFileExistsNode | `self` | `None` | USED |
| `__init__` | VisualGetFileInfoNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualGetFileInfoNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualGetFileInfoNode | `self` | `None` | USED |
| `__init__` | VisualGetFileSizeNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualGetFileSizeNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualGetFileSizeNode | `self` | `None` | USED |
| `setup_ports` | VisualGetPDFInfoNode | `self` | `None` | USED |
| `setup_ports` | VisualGetXMLAttributeNode | `self` | `None` | USED |
| `setup_ports` | VisualGetXMLElementNode | `self` | `None` | USED |
| `__init__` | VisualJsonToXMLNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualJsonToXMLNode | `self` | `None` | USED |
| `__init__` | VisualListFilesNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualListFilesNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualListFilesNode | `self` | `None` | USED |
| `setup_ports` | VisualMergePDFsNode | `self` | `None` | USED |
| `__init__` | VisualMoveFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualMoveFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualMoveFileNode | `self` | `None` | USED |
| `__init__` | VisualPDFToImagesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualPDFToImagesNode | `self` | `None` | USED |
| `setup_ports` | VisualParseXMLNode | `self` | `None` | USED |
| `__init__` | VisualReadCsvNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualReadCsvNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualReadCsvNode | `self` | `None` | USED |
| `__init__` | VisualReadFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualReadFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualReadFileNode | `self` | `None` | USED |
| `__init__` | VisualReadJsonNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualReadJsonNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualReadJsonNode | `self` | `None` | USED |
| `__init__` | VisualReadPDFTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualReadPDFTextNode | `self` | `None` | USED |
| `setup_ports` | VisualReadXMLFileNode | `self` | `None` | USED |
| `__init__` | VisualSplitPDFNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSplitPDFNode | `self` | `None` | USED |
| `__init__` | VisualUnzipFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualUnzipFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualUnzipFileNode | `self` | `None` | USED |
| `__init__` | VisualWriteCsvNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWriteCsvNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWriteCsvNode | `self` | `None` | USED |
| `__init__` | VisualWriteFileNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWriteFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWriteFileNode | `self` | `None` | USED |
| `__init__` | VisualWriteJsonNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWriteJsonNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWriteJsonNode | `self` | `None` | USED |
| `__init__` | VisualWriteXMLFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWriteXMLFileNode | `self` | `None` | USED |
| `__init__` | VisualXMLToJsonNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualXMLToJsonNode | `self` | `None` | USED |
| `setup_ports` | VisualXPathQueryNode | `self` | `None` | USED |
| `__init__` | VisualZipFilesNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualZipFilesNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualZipFilesNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.google.calendar_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\calendar_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualCalendarCreateCalendarNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarCreateCalendarNode | `self` | `None` | USED |
| `__init__` | VisualCalendarCreateEventNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarCreateEventNode | `self` | `None` | USED |
| `__init__` | VisualCalendarDeleteCalendarNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarDeleteCalendarNode | `self` | `None` | USED |
| `__init__` | VisualCalendarDeleteEventNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarDeleteEventNode | `self` | `None` | USED |
| `__init__` | VisualCalendarGetCalendarNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarGetCalendarNode | `self` | `None` | USED |
| `__init__` | VisualCalendarGetEventNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarGetEventNode | `self` | `None` | USED |
| `__init__` | VisualCalendarGetFreeBusyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarGetFreeBusyNode | `self` | `None` | USED |
| `__init__` | VisualCalendarListCalendarsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarListCalendarsNode | `self` | `None` | USED |
| `__init__` | VisualCalendarListEventsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarListEventsNode | `self` | `None` | USED |
| `__init__` | VisualCalendarMoveEventNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarMoveEventNode | `self` | `None` | USED |
| `__init__` | VisualCalendarQuickAddNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarQuickAddNode | `self` | `None` | USED |
| `__init__` | VisualCalendarUpdateEventNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualCalendarUpdateEventNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.google.docs_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\docs_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualDocsBatchUpdateNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsBatchUpdateNode | `self` | `None` | USED |
| `__init__` | VisualDocsCreateDocumentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsCreateDocumentNode | `self` | `None` | USED |
| `__init__` | VisualDocsDeleteContentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsDeleteContentNode | `self` | `None` | USED |
| `__init__` | VisualDocsGetContentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsGetContentNode | `self` | `None` | USED |
| `__init__` | VisualDocsGetDocumentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsGetDocumentNode | `self` | `None` | USED |
| `__init__` | VisualDocsInsertImageNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsInsertImageNode | `self` | `None` | USED |
| `__init__` | VisualDocsInsertTableNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsInsertTableNode | `self` | `None` | USED |
| `__init__` | VisualDocsInsertTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsInsertTextNode | `self` | `None` | USED |
| `__init__` | VisualDocsReplaceTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsReplaceTextNode | `self` | `None` | USED |
| `__init__` | VisualDocsUpdateStyleNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDocsUpdateStyleNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\drive_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualDriveBatchCopyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveBatchCopyNode | `self` | `None` | USED |
| `__init__` | VisualDriveBatchDeleteNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveBatchDeleteNode | `self` | `None` | USED |
| `__init__` | VisualDriveBatchMoveNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveBatchMoveNode | `self` | `None` | USED |
| `__init__` | VisualDriveCopyFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveCopyFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveCreateFolderNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveCreateFolderNode | `self` | `None` | USED |
| `__init__` | VisualDriveDeleteFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveDeleteFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveDownloadFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveDownloadFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveExportFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveExportFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveGetFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveGetFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveGetPermissionsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveGetPermissionsNode | `self` | `None` | USED |
| `__init__` | VisualDriveListFilesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveListFilesNode | `self` | `None` | USED |
| `__init__` | VisualDriveMoveFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveMoveFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveRemovePermissionNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveRemovePermissionNode | `self` | `None` | USED |
| `__init__` | VisualDriveRenameFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveRenameFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveSearchFilesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveSearchFilesNode | `self` | `None` | USED |
| `__init__` | VisualDriveShareFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveShareFileNode | `self` | `None` | USED |
| `__init__` | VisualDriveUploadFileNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualDriveUploadFileNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\gmail_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualGmailArchiveEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailArchiveEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailBatchDeleteNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailBatchDeleteNode | `self` | `None` | USED |
| `__init__` | VisualGmailBatchModifyNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailBatchModifyNode | `self` | `None` | USED |
| `__init__` | VisualGmailBatchSendNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailBatchSendNode | `self` | `None` | USED |
| `__init__` | VisualGmailCreateDraftNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailCreateDraftNode | `self` | `None` | USED |
| `__init__` | VisualGmailDeleteEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailDeleteEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailForwardEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailForwardEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailGetAttachmentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailGetAttachmentNode | `self` | `None` | USED |
| `__init__` | VisualGmailGetEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailGetEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailGetThreadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailGetThreadNode | `self` | `None` | USED |
| `__init__` | VisualGmailListEmailsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailListEmailsNode | `self` | `None` | USED |
| `__init__` | VisualGmailMarkAsReadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailMarkAsReadNode | `self` | `None` | USED |
| `__init__` | VisualGmailMarkAsUnreadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailMarkAsUnreadNode | `self` | `None` | USED |
| `__init__` | VisualGmailModifyLabelsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailModifyLabelsNode | `self` | `None` | USED |
| `__init__` | VisualGmailMoveToTrashNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailMoveToTrashNode | `self` | `None` | USED |
| `__init__` | VisualGmailReplyToEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailReplyToEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailSearchEmailsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailSearchEmailsNode | `self` | `None` | USED |
| `__init__` | VisualGmailSendDraftNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailSendDraftNode | `self` | `None` | USED |
| `__init__` | VisualGmailSendEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailSendEmailNode | `self` | `None` | USED |
| `__init__` | VisualGmailSendWithAttachmentNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailSendWithAttachmentNode | `self` | `None` | USED |
| `__init__` | VisualGmailStarEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGmailStarEmailNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\google\sheets_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualSheetsAddSheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsAddSheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsAppendRowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsAppendRowNode | `self` | `None` | USED |
| `__init__` | VisualSheetsAutoResizeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsAutoResizeNode | `self` | `None` | USED |
| `__init__` | VisualSheetsBatchClearNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsBatchClearNode | `self` | `None` | USED |
| `__init__` | VisualSheetsBatchGetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsBatchGetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsBatchUpdateNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsBatchUpdateNode | `self` | `None` | USED |
| `__init__` | VisualSheetsClearRangeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsClearRangeNode | `self` | `None` | USED |
| `__init__` | VisualSheetsCreateSpreadsheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsCreateSpreadsheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsDeleteColumnNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsDeleteColumnNode | `self` | `None` | USED |
| `__init__` | VisualSheetsDeleteRowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsDeleteRowNode | `self` | `None` | USED |
| `__init__` | VisualSheetsDeleteSheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsDeleteSheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsDuplicateSheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsDuplicateSheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsFormatCellsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsFormatCellsNode | `self` | `None` | USED |
| `__init__` | VisualSheetsGetCellNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsGetCellNode | `self` | `None` | USED |
| `__init__` | VisualSheetsGetRangeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsGetRangeNode | `self` | `None` | USED |
| `__init__` | VisualSheetsGetSpreadsheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsGetSpreadsheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsInsertColumnNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsInsertColumnNode | `self` | `None` | USED |
| `__init__` | VisualSheetsInsertRowNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsInsertRowNode | `self` | `None` | USED |
| `__init__` | VisualSheetsRenameSheetNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsRenameSheetNode | `self` | `None` | USED |
| `__init__` | VisualSheetsSetCellNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsSetCellNode | `self` | `None` | USED |
| `__init__` | VisualSheetsWriteRangeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSheetsWriteRangeNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.messaging.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualTelegramSendDocumentNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramSendDocumentNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramSendDocumentNode | `self` | `None` | USED |
| `__init__` | VisualTelegramSendLocationNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramSendLocationNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramSendLocationNode | `self` | `None` | USED |
| `__init__` | VisualTelegramSendMessageNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramSendMessageNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramSendMessageNode | `self` | `None` | USED |
| `__init__` | VisualTelegramSendPhotoNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramSendPhotoNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramSendPhotoNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\telegram_action_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualTelegramAnswerCallbackNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramAnswerCallbackNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramAnswerCallbackNode | `self` | `None` | USED |
| `__init__` | VisualTelegramDeleteMessageNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramDeleteMessageNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramDeleteMessageNode | `self` | `None` | USED |
| `__init__` | VisualTelegramEditMessageNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramEditMessageNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramEditMessageNode | `self` | `None` | USED |
| `__init__` | VisualTelegramGetUpdatesNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramGetUpdatesNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramGetUpdatesNode | `self` | `None` | USED |
| `__init__` | VisualTelegramSendMediaGroupNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTelegramSendMediaGroupNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTelegramSendMediaGroupNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\messaging\whatsapp_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualWhatsAppSendDocumentNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendDocumentNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendDocumentNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendImageNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendImageNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendImageNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendInteractiveNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendInteractiveNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendInteractiveNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendLocationNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendLocationNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendLocationNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendMessageNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendMessageNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendMessageNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendTemplateNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendTemplateNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendTemplateNode | `self` | `None` | USED |
| `__init__` | VisualWhatsAppSendVideoNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualWhatsAppSendVideoNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualWhatsAppSendVideoNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.office_automation.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\office_automation\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualExcelCloseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExcelCloseNode | `self` | `None` | USED |
| `__init__` | VisualExcelGetRangeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExcelGetRangeNode | `self` | `None` | USED |
| `__init__` | VisualExcelOpenNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExcelOpenNode | `self` | `None` | USED |
| `__init__` | VisualExcelReadCellNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExcelReadCellNode | `self` | `None` | USED |
| `__init__` | VisualExcelWriteCellNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualExcelWriteCellNode | `self` | `None` | USED |
| `__init__` | VisualOutlookGetInboxCountNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualOutlookGetInboxCountNode | `self` | `None` | USED |
| `__init__` | VisualOutlookReadEmailsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualOutlookReadEmailsNode | `self` | `None` | USED |
| `__init__` | VisualOutlookSendEmailNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualOutlookSendEmailNode | `self` | `None` | USED |
| `__init__` | VisualWordCloseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWordCloseNode | `self` | `None` | USED |
| `setup_ports` | VisualWordGetTextNode | `self` | `None` | USED |
| `__init__` | VisualWordOpenNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWordOpenNode | `self` | `None` | USED |
| `__init__` | VisualWordReplaceTextNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualWordReplaceTextNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.rest_api.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\rest_api\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_all_visual_node_classes` | - | `` | `-` | INTERNAL |
| `_get_visual_node_classes` | - | `` | `-` | INTERNAL |
| `setup_ports` | VisualBuildUrlNode | `self` | `None` | USED |
| `setup_ports` | VisualHttpAuthNode | `self` | `None` | USED |
| `setup_ports` | VisualHttpDownloadFileNode | `self` | `None` | USED |
| `setup_ports` | VisualHttpRequestNode | `self` | `None` | USED |
| `setup_ports` | VisualHttpUploadFileNode | `self` | `None` | USED |
| `setup_ports` | VisualParseJsonResponseNode | `self` | `None` | USED |
| `setup_ports` | VisualSetHttpHeadersNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.scripts.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\scripts\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_node_class` | VisualEvalExpressionNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualEvalExpressionNode | `self` | `None` | USED |
| `get_node_class` | VisualRunBatchScriptNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunBatchScriptNode | `self` | `None` | USED |
| `get_node_class` | VisualRunJavaScriptNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunJavaScriptNode | `self` | `None` | USED |
| `get_node_class` | VisualRunPythonFileNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunPythonFileNode | `self` | `None` | USED |
| `get_node_class` | VisualRunPythonScriptNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunPythonScriptNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.system.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\system\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_node_class` | VisualClipboardClearNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualClipboardClearNode | `self` | `None` | USED |
| `get_node_class` | VisualClipboardCopyNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualClipboardCopyNode | `self` | `None` | USED |
| `get_node_class` | VisualClipboardPasteNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualClipboardPasteNode | `self` | `None` | USED |
| `get_node_class` | VisualGetServiceStatusNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualGetServiceStatusNode | `self` | `None` | USED |
| `__init__` | VisualInputDialogNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualInputDialogNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualInputDialogNode | `self` | `None` | USED |
| `__init__` | VisualListServicesNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualListServicesNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualListServicesNode | `self` | `None` | USED |
| `__init__` | VisualMessageBoxNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualMessageBoxNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualMessageBoxNode | `self` | `None` | USED |
| `__init__` | VisualRestartServiceNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualRestartServiceNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRestartServiceNode | `self` | `None` | USED |
| `__init__` | VisualRunCommandNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualRunCommandNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunCommandNode | `self` | `None` | USED |
| `__init__` | VisualRunPowerShellNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualRunPowerShellNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualRunPowerShellNode | `self` | `None` | USED |
| `get_node_class` | VisualStartServiceNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualStartServiceNode | `self` | `None` | USED |
| `get_node_class` | VisualStopServiceNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualStopServiceNode | `self` | `None` | USED |
| `__init__` | VisualTooltipNode | `self` | `None` | DUNDER |
| `get_node_class` | VisualTooltipNode | `self` | `type` | UNUSED |
| `setup_ports` | VisualTooltipNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.triggers.base

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\triggers\base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualTriggerNode | `self` | `None` | DUNDER |
| `_apply_trigger_styling` | VisualTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualTriggerNode | `self` | `None` | INTERNAL |
| `is_listening` | VisualTriggerNode | `self` | `bool` | UNUSED |
| `set_listening` | VisualTriggerNode | `self, listening: bool` | `None` | USED |
| `setup_ports` | VisualTriggerNode | `self` | `None` | USED |
| `update_status` | VisualTriggerNode | `self, status: str` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.triggers.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\triggers\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_setup_payload_ports` | VisualAppEventTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualCalendarTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualChatTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualDriveTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualEmailTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualErrorTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualFileWatchTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualFormTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualGmailTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualRSSFeedTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualSSETriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualScheduleTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualSheetsTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualTelegramTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualWebhookTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualWhatsAppTriggerNode | `self` | `None` | INTERNAL |
| `_setup_payload_ports` | VisualWorkflowCallTriggerNode | `self` | `None` | INTERNAL |


## casare_rpa.presentation.canvas.visual_nodes.utility.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\utility\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `setup_ports` | VisualDateTimeAddNode | `self` | `None` | USED |
| `setup_ports` | VisualDateTimeCompareNode | `self` | `None` | USED |
| `setup_ports` | VisualDateTimeDiffNode | `self` | `None` | USED |
| `__init__` | VisualFormatDateTimeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualFormatDateTimeNode | `self` | `None` | USED |
| `__init__` | VisualGetCurrentDateTimeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetCurrentDateTimeNode | `self` | `None` | USED |
| `__init__` | VisualGetTimestampNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetTimestampNode | `self` | `None` | USED |
| `__init__` | VisualParseDateTimeNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualParseDateTimeNode | `self` | `None` | USED |
| `setup_ports` | VisualRandomChoiceNode | `self` | `None` | USED |
| `__init__` | VisualRandomNumberNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRandomNumberNode | `self` | `None` | USED |
| `__init__` | VisualRandomStringNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRandomStringNode | `self` | `None` | USED |
| `__init__` | VisualRandomUUIDNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualRandomUUIDNode | `self` | `None` | USED |
| `setup_ports` | VisualShuffleListNode | `self` | `None` | USED |
| `__init__` | VisualTextCaseNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextCaseNode | `self` | `None` | USED |
| `__init__` | VisualTextContainsNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextContainsNode | `self` | `None` | USED |
| `__init__` | VisualTextCountNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextCountNode | `self` | `None` | USED |
| `__init__` | VisualTextEndsWithNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextEndsWithNode | `self` | `None` | USED |
| `__init__` | VisualTextExtractNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextExtractNode | `self` | `None` | USED |
| `setup_ports` | VisualTextJoinNode | `self` | `None` | USED |
| `__init__` | VisualTextLinesNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextLinesNode | `self` | `None` | USED |
| `__init__` | VisualTextPadNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextPadNode | `self` | `None` | USED |
| `__init__` | VisualTextReplaceNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextReplaceNode | `self` | `None` | USED |
| `setup_ports` | VisualTextReverseNode | `self` | `None` | USED |
| `__init__` | VisualTextSplitNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextSplitNode | `self` | `None` | USED |
| `__init__` | VisualTextStartsWithNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextStartsWithNode | `self` | `None` | USED |
| `setup_ports` | VisualTextSubstringNode | `self` | `None` | USED |
| `__init__` | VisualTextTrimNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualTextTrimNode | `self` | `None` | USED |


## casare_rpa.presentation.canvas.visual_nodes.variable.nodes

**File:** `src\casare_rpa\presentation\canvas\visual_nodes\variable\nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VisualGetVariableNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualGetVariableNode | `self` | `None` | USED |
| `__init__` | VisualIncrementVariableNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualIncrementVariableNode | `self` | `None` | USED |
| `__init__` | VisualSetVariableNode | `self` | `None` | DUNDER |
| `setup_ports` | VisualSetVariableNode | `self` | `None` | USED |


## casare_rpa.presentation.setup.config_manager

**File:** `src\casare_rpa\presentation\setup\config_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | ClientConfig | `cls, data: Dict[str, Any]` | `'ClientConfig'` | USED |
| `to_dict` | ClientConfig | `self` | `Dict[str, Any]` | USED |
| `__init__` | ClientConfigManager | `self, config_dir: Optional[Path], config_file: Optional[str]` | `None` | DUNDER |
| `config_exists` | ClientConfigManager | `self` | `bool` | USED |
| `create_default` | ClientConfigManager | `self` | `ClientConfig` | USED |
| `ensure_directories` | ClientConfigManager | `self` | `None` | USED |
| `load` | ClientConfigManager | `self` | `ClientConfig` | USED |
| `needs_setup` | ClientConfigManager | `self` | `bool` | USED |
| `save` | ClientConfigManager | `self, config: ClientConfig` | `None` | USED |
| `async test_connection` | ClientConfigManager | `self, url: str, api_key: Optional[str]` | `tuple[bool, str]` | USED |
| `validate_api_key` | ClientConfigManager | `self, api_key: str` | `Optional[str]` | USED |
| `validate_robot_name` | ClientConfigManager | `self, name: str` | `Optional[str]` | UNUSED |
| `validate_url` | ClientConfigManager | `self, url: str` | `Optional[str]` | USED |


## casare_rpa.presentation.setup.setup_wizard

**File:** `src\casare_rpa\presentation\setup\setup_wizard.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `show_setup_wizard_if_needed` | - | `parent` | `Optional[ClientConfig]` | USED |
| `__init__` | CapabilitiesPage | `self, parent` | `None` | DUNDER |
| `_auto_detect_capabilities` | CapabilitiesPage | `self` | `None` | INTERNAL |
| `_setup_ui` | CapabilitiesPage | `self` | `None` | INTERNAL |
| `__init__` | OrchestratorPage | `self, config_manager: ClientConfigManager, parent` | `None` | DUNDER |
| `_on_api_key_changed` | OrchestratorPage | `self, text: str` | `None` | INTERNAL |
| `_on_url_changed` | OrchestratorPage | `self, text: str` | `None` | INTERNAL |
| `_run_connection_test` | OrchestratorPage | `self, url: str, api_key: str` | `None` | INTERNAL |
| `_setup_ui` | OrchestratorPage | `self` | `None` | INTERNAL |
| `_test_connection` | OrchestratorPage | `self` | `None` | INTERNAL |
| `_toggle_api_key_visibility` | OrchestratorPage | `self, checked: bool` | `None` | INTERNAL |
| `isComplete` | OrchestratorPage | `self` | `bool` | UNUSED |
| `__init__` | RobotConfigPage | `self, parent` | `None` | DUNDER |
| `_setup_ui` | RobotConfigPage | `self` | `None` | INTERNAL |
| `isComplete` | RobotConfigPage | `self` | `bool` | UNUSED |
| `__init__` | SetupWizard | `self, config_manager: Optional[ClientConfigManager], parent` | `None` | DUNDER |
| `_add_pages` | SetupWizard | `self` | `None` | INTERNAL |
| `_apply_styles` | SetupWizard | `self` | `None` | INTERNAL |
| `_gather_config` | SetupWizard | `self` | `None` | INTERNAL |
| `_setup_wizard` | SetupWizard | `self` | `None` | INTERNAL |
| `accept` | SetupWizard | `self` | `None` | USED |
| `reject` | SetupWizard | `self` | `None` | USED |
| `__init__` | SummaryPage | `self, parent` | `None` | DUNDER |
| `_setup_ui` | SummaryPage | `self` | `None` | INTERNAL |
| `initializePage` | SummaryPage | `self` | `None` | UNUSED |
| `__init__` | WelcomePage | `self, parent` | `None` | DUNDER |
| `_setup_ui` | WelcomePage | `self` | `None` | INTERNAL |
