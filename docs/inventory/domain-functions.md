# Domain Layer Functions

**Total:** 586 functions

## casare_rpa.domain.credentials

**File:** `src\casare_rpa\domain\credentials.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _get_provider` | - | `context: ExecutionContextProtocol` | `Optional[CredentialProviderProtocol]` | INTERNAL |
| `async resolve_node_credential` | - | `context: ExecutionContextProtocol, node: Any, credential_name_param: str, ...` | `Optional[str]` | UNUSED |
| `async _get_credential_provider` | CredentialAwareMixin | `self, context: ExecutionContextProtocol` | `Optional[CredentialProviderProtocol]` | INTERNAL |
| `async _get_from_vault` | CredentialAwareMixin | `self, context: ExecutionContextProtocol, credential_name: str, ...` | `Optional[str]` | INTERNAL |
| `async _get_full_credential` | CredentialAwareMixin | `self, context: ExecutionContextProtocol, credential_name: str` | `Optional[ResolvedCredentialData]` | INTERNAL |
| `get_parameter` | CredentialAwareMixin | `self, name: str, default: Any` | `Any` | USED |
| `async resolve_credential` | CredentialAwareMixin | `self, context: ExecutionContextProtocol, credential_name_param: str, ...` | `Optional[str]` | USED |
| `async resolve_oauth_credentials` | CredentialAwareMixin | `self, context: ExecutionContextProtocol, credential_name_param: str, ...` | `tuple[Optional[str], Optional[str]]` | UNUSED |
| `async resolve_username_password` | CredentialAwareMixin | `self, context: ExecutionContextProtocol, credential_name_param: str, ...` | `tuple[Optional[str], Optional[str]]` | USED |
| `get_parameter` | HasGetParameter | `self, name: str, default: Any` | `Any` | USED |


## casare_rpa.domain.decorators

**File:** `src\casare_rpa\domain\decorators.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `decorator` | - | `cls: Type[T]` | `Type[T]` | UNUSED |
| `executable_node` | - | `cls: Type[T]` | `Type[T]` | UNUSED |
| `node_schema` | - | `` | `-` | UNUSED |
| `wrapped_define` | - | `self` | `None` | UNUSED |
| `wrapped_init` | - | `self, node_id: str` | `-` | UNUSED |


## casare_rpa.domain.entities.base_node

**File:** `src\casare_rpa\domain\entities\base_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BaseNode | `self, node_id: NodeId, config: Optional[NodeConfig]` | `None` | DUNDER |
| `__repr__` | BaseNode | `self` | `str` | DUNDER |
| `_define_ports` | BaseNode | `self` | `None` | INTERNAL |
| `_validate_config` | BaseNode | `self` | `tuple[bool, Optional[str]]` | INTERNAL |
| `add_input_port` | BaseNode | `self, name: str, data_type: DataType, ...` | `None` | USED |
| `add_output_port` | BaseNode | `self, name: str, data_type: DataType, ...` | `None` | USED |
| `deserialize` | BaseNode | `cls, data: SerializedNode` | `'BaseNode'` | USED |
| `async execute` | BaseNode | `self, context: Any` | `ExecutionResult` | USED |
| `get_debug_info` | BaseNode | `self` | `Dict[str, Any]` | UNUSED |
| `get_input_value` | BaseNode | `self, port_name: str, default: Any` | `Any` | USED |
| `get_output_value` | BaseNode | `self, port_name: str, default: Any` | `Any` | USED |
| `get_parameter` | BaseNode | `self, name: str, default: Any` | `Any` | USED |
| `get_status` | BaseNode | `self` | `NodeStatus` | USED |
| `has_breakpoint` | BaseNode | `self` | `bool` | UNUSED |
| `reset` | BaseNode | `self` | `None` | USED |
| `serialize` | BaseNode | `self` | `SerializedNode` | USED |
| `set_breakpoint` | BaseNode | `self, enabled: bool` | `None` | UNUSED |
| `set_input_value` | BaseNode | `self, port_name: str, value: Any` | `None` | USED |
| `set_output_value` | BaseNode | `self, port_name: str, value: Any` | `None` | USED |
| `set_status` | BaseNode | `self, status: NodeStatus, error_message: Optional[str]` | `None` | USED |
| `validate` | BaseNode | `self` | `tuple[bool, Optional[str]]` | USED |


## casare_rpa.domain.entities.execution_state

**File:** `src\casare_rpa\domain\entities\execution_state.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionState | `self, workflow_name: str, mode: ExecutionMode, ...` | `None` | DUNDER |
| `__repr__` | ExecutionState | `self` | `str` | DUNDER |
| `_build_variable_hierarchy` | ExecutionState | `self, runtime_vars: Optional[Dict[str, Any]]` | `Dict[str, Any]` | INTERNAL |
| `add_error` | ExecutionState | `self, node_id: NodeId, error_message: str` | `None` | USED |
| `clear_variables` | ExecutionState | `self` | `None` | USED |
| `delete_variable` | ExecutionState | `self, name: str` | `None` | USED |
| `get_errors` | ExecutionState | `self` | `List[tuple[NodeId, str]]` | UNUSED |
| `get_execution_path` | ExecutionState | `self` | `List[NodeId]` | UNUSED |
| `get_execution_summary` | ExecutionState | `self` | `Dict[str, Any]` | USED |
| `get_variable` | ExecutionState | `self, name: str, default: Any` | `Any` | USED |
| `has_project_context` | ExecutionState | `self` | `bool` | UNUSED |
| `has_variable` | ExecutionState | `self, name: str` | `bool` | USED |
| `is_stopped` | ExecutionState | `self` | `bool` | USED |
| `mark_completed` | ExecutionState | `self` | `None` | USED |
| `project_context` | ExecutionState | `self` | `Optional['ProjectContext']` | UNUSED |
| `resolve_credential_path` | ExecutionState | `self, alias: str` | `Optional[str]` | USED |
| `resolve_value` | ExecutionState | `self, value: Any` | `Any` | USED |
| `set_current_node` | ExecutionState | `self, node_id: NodeId` | `None` | USED |
| `set_variable` | ExecutionState | `self, name: str, value: Any` | `None` | USED |
| `stop` | ExecutionState | `self` | `None` | USED |


## casare_rpa.domain.entities.node_connection

**File:** `src\casare_rpa\domain\entities\node_connection.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__eq__` | NodeConnection | `self, other: object` | `bool` | DUNDER |
| `__hash__` | NodeConnection | `self` | `int` | DUNDER |
| `__init__` | NodeConnection | `self, source_node: NodeId, source_port: str, ...` | `None` | DUNDER |
| `__repr__` | NodeConnection | `self` | `str` | DUNDER |
| `from_dict` | NodeConnection | `cls, data: Dict[str, str]` | `'NodeConnection'` | USED |
| `source_id` | NodeConnection | `self` | `PortId` | UNUSED |
| `source_node` | NodeConnection | `self` | `NodeId` | UNUSED |
| `source_port` | NodeConnection | `self` | `str` | UNUSED |
| `target_id` | NodeConnection | `self` | `PortId` | UNUSED |
| `target_node` | NodeConnection | `self` | `NodeId` | UNUSED |
| `target_port` | NodeConnection | `self` | `str` | UNUSED |
| `to_dict` | NodeConnection | `self` | `Dict[str, str]` | USED |


## casare_rpa.domain.entities.project.base

**File:** `src\casare_rpa\domain\entities\project\base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `generate_project_id` | - | `` | `str` | USED |
| `generate_scenario_id` | - | `` | `str` | USED |


## casare_rpa.domain.entities.project.credentials

**File:** `src\casare_rpa\domain\entities\project\credentials.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | CredentialBinding | `cls, data: Dict[str, Any]` | `'CredentialBinding'` | USED |
| `to_dict` | CredentialBinding | `self` | `Dict[str, Any]` | USED |
| `from_dict` | CredentialBindingsFile | `cls, data: Dict[str, Any]` | `'CredentialBindingsFile'` | USED |
| `get_binding` | CredentialBindingsFile | `self, alias: str` | `Optional[CredentialBinding]` | UNUSED |
| `remove_binding` | CredentialBindingsFile | `self, alias: str` | `bool` | UNUSED |
| `resolve_vault_path` | CredentialBindingsFile | `self, alias: str` | `Optional[str]` | USED |
| `set_binding` | CredentialBindingsFile | `self, binding: CredentialBinding` | `None` | UNUSED |
| `to_dict` | CredentialBindingsFile | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.entities.project.index

**File:** `src\casare_rpa\domain\entities\project\index.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | ProjectIndexEntry | `cls, data: Dict[str, Any]` | `'ProjectIndexEntry'` | USED |
| `to_dict` | ProjectIndexEntry | `self` | `Dict[str, Any]` | USED |
| `add_project` | ProjectsIndex | `self, project: Project` | `None` | USED |
| `from_dict` | ProjectsIndex | `cls, data: Dict[str, Any]` | `'ProjectsIndex'` | USED |
| `get_project` | ProjectsIndex | `self, project_id: str` | `Optional[ProjectIndexEntry]` | USED |
| `get_recent_projects` | ProjectsIndex | `self, limit: Optional[int]` | `List[ProjectIndexEntry]` | USED |
| `remove_project` | ProjectsIndex | `self, project_id: str` | `bool` | USED |
| `to_dict` | ProjectsIndex | `self` | `Dict[str, Any]` | USED |
| `update_last_opened` | ProjectsIndex | `self, project_id: str` | `None` | USED |


## casare_rpa.domain.entities.project.project

**File:** `src\casare_rpa\domain\entities\project\project.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Project | `self` | `None` | DUNDER |
| `__repr__` | Project | `self` | `str` | DUNDER |
| `create_new` | Project | `cls, name: str, path: Path` | `'Project'` | USED |
| `credentials_file` | Project | `self` | `Optional[Path]` | UNUSED |
| `from_dict` | Project | `cls, data: Dict[str, Any]` | `'Project'` | USED |
| `path` | Project | `self` | `Optional[Path]` | USED |
| `path` | Project | `self, value: Path` | `None` | USED |
| `project_file` | Project | `self` | `Optional[Path]` | UNUSED |
| `scenarios_dir` | Project | `self` | `Optional[Path]` | UNUSED |
| `to_dict` | Project | `self` | `Dict[str, Any]` | USED |
| `touch_modified` | Project | `self` | `None` | USED |
| `variables_file` | Project | `self` | `Optional[Path]` | UNUSED |


## casare_rpa.domain.entities.project.scenario

**File:** `src\casare_rpa\domain\entities\project\scenario.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Scenario | `self` | `None` | DUNDER |
| `__repr__` | Scenario | `self` | `str` | DUNDER |
| `_validate_required_fields` | Scenario | `self` | `None` | INTERNAL |
| `create_new` | Scenario | `cls, name: str, project_id: str, ...` | `'Scenario'` | USED |
| `file_path` | Scenario | `self` | `Optional[Path]` | UNUSED |
| `file_path` | Scenario | `self, value: Path` | `None` | UNUSED |
| `from_dict` | Scenario | `cls, data: Dict[str, Any]` | `'Scenario'` | USED |
| `get_variable_value` | Scenario | `self, name: str, default: Any` | `Any` | UNUSED |
| `set_variable_value` | Scenario | `self, name: str, value: Any` | `None` | UNUSED |
| `to_dict` | Scenario | `self` | `Dict[str, Any]` | USED |
| `touch_modified` | Scenario | `self` | `None` | USED |


## casare_rpa.domain.entities.project.settings

**File:** `src\casare_rpa\domain\entities\project\settings.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | ProjectSettings | `cls, data: Dict[str, Any]` | `'ProjectSettings'` | USED |
| `to_dict` | ProjectSettings | `self` | `Dict[str, Any]` | USED |
| `from_dict` | ScenarioExecutionSettings | `cls, data: Dict[str, Any]` | `'ScenarioExecutionSettings'` | USED |
| `to_dict` | ScenarioExecutionSettings | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.entities.project.variables

**File:** `src\casare_rpa\domain\entities\project\variables.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | VariablesFile | `cls, data: Dict[str, Any]` | `'VariablesFile'` | USED |
| `get_default_values` | VariablesFile | `self` | `Dict[str, Any]` | USED |
| `get_variable` | VariablesFile | `self, name: str` | `Optional[Variable]` | USED |
| `remove_variable` | VariablesFile | `self, name: str` | `bool` | USED |
| `set_variable` | VariablesFile | `self, variable: Variable` | `None` | USED |
| `to_dict` | VariablesFile | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.entities.tenant

**File:** `src\casare_rpa\domain\entities\tenant.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Tenant | `self` | `None` | DUNDER |
| `__repr__` | Tenant | `self` | `str` | DUNDER |
| `activate` | Tenant | `self` | `None` | USED |
| `add_admin` | Tenant | `self, email: str` | `None` | UNUSED |
| `add_robot` | Tenant | `self, robot_id: str` | `None` | USED |
| `can_add_robot` | Tenant | `self` | `bool` | UNUSED |
| `deactivate` | Tenant | `self` | `None` | USED |
| `from_dict` | Tenant | `cls, data: Dict[str, Any]` | `'Tenant'` | USED |
| `has_robot` | Tenant | `self, robot_id: str` | `bool` | UNUSED |
| `is_admin` | Tenant | `self, email: str` | `bool` | UNUSED |
| `remove_admin` | Tenant | `self, email: str` | `None` | UNUSED |
| `remove_robot` | Tenant | `self, robot_id: str` | `None` | USED |
| `robot_count` | Tenant | `self` | `int` | UNUSED |
| `to_dict` | Tenant | `self` | `Dict[str, Any]` | USED |
| `update_settings` | Tenant | `self, settings: TenantSettings` | `None` | UNUSED |
| `__post_init__` | TenantId | `self` | `None` | DUNDER |
| `__str__` | TenantId | `self` | `str` | DUNDER |
| `generate` | TenantId | `cls` | `'TenantId'` | USED |
| `__post_init__` | TenantSettings | `self` | `None` | DUNDER |
| `from_dict` | TenantSettings | `cls, data: Dict[str, Any]` | `'TenantSettings'` | USED |
| `to_dict` | TenantSettings | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.entities.variable

**File:** `src\casare_rpa\domain\entities\variable.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Variable | `self` | `None` | DUNDER |
| `_validate_name` | Variable | `name: str` | `None` | INTERNAL |
| `_validate_type` | Variable | `var_type: str` | `None` | INTERNAL |
| `from_dict` | Variable | `cls, data: Dict[str, Any]` | `'Variable'` | USED |
| `to_dict` | Variable | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.entities.workflow

**File:** `src\casare_rpa\domain\entities\workflow.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowSchema | `self, metadata: Optional[WorkflowMetadata]` | `None` | DUNDER |
| `__repr__` | WorkflowSchema | `self` | `str` | DUNDER |
| `_infer_type` | WorkflowSchema | `self, value: Any` | `str` | INTERNAL |
| `add_connection` | WorkflowSchema | `self, connection: NodeConnection` | `None` | UNUSED |
| `add_node` | WorkflowSchema | `self, node_data: SerializedNode` | `None` | USED |
| `from_dict` | WorkflowSchema | `cls, data: SerializedWorkflow` | `'WorkflowSchema'` | USED |
| `get_connections_from` | WorkflowSchema | `self, node_id: NodeId` | `List[NodeConnection]` | UNUSED |
| `get_connections_to` | WorkflowSchema | `self, node_id: NodeId` | `List[NodeConnection]` | UNUSED |
| `get_node` | WorkflowSchema | `self, node_id: NodeId` | `Optional[SerializedNode]` | UNUSED |
| `remove_connection` | WorkflowSchema | `self, source_node: NodeId, source_port: str, ...` | `None` | UNUSED |
| `remove_node` | WorkflowSchema | `self, node_id: NodeId` | `None` | USED |
| `to_dict` | WorkflowSchema | `self` | `SerializedWorkflow` | USED |
| `validate` | WorkflowSchema | `self` | `tuple[bool, List[str]]` | USED |
| `validate_full` | WorkflowSchema | `self` | `'ValidationResult'` | USED |


## casare_rpa.domain.entities.workflow_metadata

**File:** `src\casare_rpa\domain\entities\workflow_metadata.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowMetadata | `self, name: str, description: str, ...` | `None` | DUNDER |
| `__repr__` | WorkflowMetadata | `self` | `str` | DUNDER |
| `_validate_name` | WorkflowMetadata | `name: str` | `None` | INTERNAL |
| `from_dict` | WorkflowMetadata | `cls, data: Dict[str, Any]` | `'WorkflowMetadata'` | USED |
| `to_dict` | WorkflowMetadata | `self` | `Dict[str, Any]` | USED |
| `update_modified_timestamp` | WorkflowMetadata | `self` | `None` | USED |


## casare_rpa.domain.entities.workflow_schedule

**File:** `src\casare_rpa\domain\entities\workflow_schedule.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `calculate_next_run` | WorkflowSchedule | `self, from_time: Optional[datetime]` | `Optional[datetime]` | USED |
| `frequency_display` | WorkflowSchedule | `self` | `str` | UNUSED |
| `from_dict` | WorkflowSchedule | `cls, data: Dict[str, Any]` | `'WorkflowSchedule'` | USED |
| `success_rate` | WorkflowSchedule | `self` | `float` | UNUSED |
| `to_dict` | WorkflowSchedule | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.errors.context

**File:** `src\casare_rpa\domain\errors\context.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | ErrorContext | `self` | `None` | DUNDER |
| `is_retryable` | ErrorContext | `self` | `bool` | UNUSED |
| `is_ui_error` | ErrorContext | `self` | `bool` | UNUSED |
| `to_dict` | ErrorContext | `self` | `Dict[str, Any]` | USED |
| `__repr__` | RecoveryDecision | `self` | `str` | DUNDER |


## casare_rpa.domain.errors.handlers.base

**File:** `src\casare_rpa\domain\errors\handlers\base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `can_handle` | ErrorHandler | `self, context: ErrorContext` | `bool` | USED |
| `classify` | ErrorHandler | `self, context: ErrorContext` | `ErrorContext` | USED |
| `decide_recovery` | ErrorHandler | `self, context: ErrorContext` | `RecoveryDecision` | USED |


## casare_rpa.domain.errors.handlers.node_handler

**File:** `src\casare_rpa\domain\errors\handlers\node_handler.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeErrorHandler | `self, node_types: Optional[List[str]], default_max_retries: int, ...` | `None` | DUNDER |
| `_calculate_retry_delay` | NodeErrorHandler | `self, retry_count: int` | `int` | INTERNAL |
| `_category_from_code` | NodeErrorHandler | `self, code: ErrorCode` | `ErrorCategory` | INTERNAL |
| `_category_from_exception` | NodeErrorHandler | `self, exc: Exception` | `ErrorCategory` | INTERNAL |
| `_classification_from_code` | NodeErrorHandler | `self, code: ErrorCode` | `ErrorClassification` | INTERNAL |
| `_classification_from_exception` | NodeErrorHandler | `self, exc: Exception` | `ErrorClassification` | INTERNAL |
| `_severity_from_code` | NodeErrorHandler | `self, code: ErrorCode` | `ErrorSeverity` | INTERNAL |
| `can_handle` | NodeErrorHandler | `self, context: ErrorContext` | `bool` | USED |
| `classify` | NodeErrorHandler | `self, context: ErrorContext` | `ErrorContext` | USED |
| `decide_recovery` | NodeErrorHandler | `self, context: ErrorContext` | `RecoveryDecision` | USED |


## casare_rpa.domain.errors.registry

**File:** `src\casare_rpa\domain\errors\registry.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_on_create_error_registry` | - | `instance: ErrorHandlerRegistry` | `None` | INTERNAL |
| `get_error_handler_registry` | - | `` | `ErrorHandlerRegistry` | USED |
| `reset_error_handler_registry` | - | `` | `None` | UNUSED |
| `__init__` | ErrorHandlerRegistry | `self` | `None` | DUNDER |
| `_find_handler` | ErrorHandlerRegistry | `self, context: ErrorContext` | `ErrorHandler` | INTERNAL |
| `_record_error` | ErrorHandlerRegistry | `self, context: ErrorContext` | `None` | INTERNAL |
| `_sanitize_config` | ErrorHandlerRegistry | `self, config: Dict[str, Any]` | `Dict[str, Any]` | INTERNAL |
| `_sanitize_variables` | ErrorHandlerRegistry | `self, variables: Dict[str, Any]` | `Dict[str, Any]` | INTERNAL |
| `clear_history` | ErrorHandlerRegistry | `self` | `None` | USED |
| `get_error_history` | ErrorHandlerRegistry | `self, node_id: Optional[NodeId], category: Optional[ErrorCategory], ...` | `List[ErrorContext]` | USED |
| `get_error_summary` | ErrorHandlerRegistry | `self` | `Dict[str, Any]` | USED |
| `handle_error` | ErrorHandlerRegistry | `self, exception: Exception, node_id: NodeId, ...` | `tuple[ErrorContext, RecoveryDecision]` | USED |
| `register_category_handler` | ErrorHandlerRegistry | `self, category: ErrorCategory, handler: ErrorHandler` | `None` | UNUSED |
| `register_custom_handler` | ErrorHandlerRegistry | `self, name: str, handler_func: CustomErrorHandlerFunc` | `None` | USED |
| `register_global_handler` | ErrorHandlerRegistry | `self, handler: ErrorHandler` | `None` | UNUSED |
| `register_node_handler` | ErrorHandlerRegistry | `self, node_type: str, handler: ErrorHandler` | `None` | UNUSED |
| `unregister_custom_handler` | ErrorHandlerRegistry | `self, name: str` | `bool` | UNUSED |


## casare_rpa.domain.events

**File:** `src\casare_rpa\domain\events.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_event_bus_singleton` | - | `` | `EventBus` | INTERNAL |
| `get_event_bus` | - | `` | `EventBus` | USED |
| `reset_event_bus` | - | `` | `None` | UNUSED |
| `__init__` | Event | `self, event_type: EventType, data: Optional[EventData], ...` | `None` | DUNDER |
| `__repr__` | Event | `self` | `str` | DUNDER |
| `to_dict` | Event | `self` | `Dict[str, Any]` | USED |
| `__init__` | EventBus | `self` | `None` | DUNDER |
| `__repr__` | EventBus | `self` | `str` | DUNDER |
| `clear_handlers` | EventBus | `self, event_type: Optional[EventType]` | `None` | USED |
| `clear_history` | EventBus | `self` | `None` | USED |
| `emit` | EventBus | `self, event_type: EventType, data: Optional[EventData], ...` | `None` | USED |
| `get_handler_count` | EventBus | `self, event_type: EventType` | `int` | UNUSED |
| `get_history` | EventBus | `self, event_type: Optional[EventType], limit: Optional[int]` | `List[Event]` | USED |
| `publish` | EventBus | `self, event: Event` | `None` | USED |
| `subscribe` | EventBus | `self, event_type: EventType, handler: EventHandler` | `None` | USED |
| `unsubscribe` | EventBus | `self, event_type: EventType, handler: EventHandler` | `None` | USED |
| `__init__` | EventLogger | `self, log_level: str` | `None` | DUNDER |
| `handle_event` | EventLogger | `self, event: Event` | `None` | UNUSED |
| `subscribe_all` | EventLogger | `self, event_bus: EventBus` | `None` | USED |
| `__init__` | EventRecorder | `self` | `None` | DUNDER |
| `export_to_dict` | EventRecorder | `self` | `List[Dict[str, Any]]` | UNUSED |
| `get_recorded_events` | EventRecorder | `self` | `List[Event]` | UNUSED |
| `handle_event` | EventRecorder | `self, event: Event` | `None` | UNUSED |
| `start_recording` | EventRecorder | `self` | `None` | USED |
| `stop_recording` | EventRecorder | `self` | `None` | USED |
| `subscribe_all` | EventRecorder | `self, event_bus: EventBus` | `None` | USED |


## casare_rpa.domain.orchestrator.entities.job

**File:** `src\casare_rpa\domain\orchestrator\entities\job.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Job | `self` | `-` | DUNDER |
| `can_transition_to` | Job | `self, new_status: JobStatus` | `bool` | USED |
| `duration_formatted` | Job | `self` | `str` | UNUSED |
| `from_dict` | Job | `cls, data: Dict[str, Any]` | `'Job'` | USED |
| `is_terminal` | Job | `self` | `bool` | USED |
| `to_dict` | Job | `self` | `Dict[str, Any]` | USED |
| `transition_to` | Job | `self, new_status: JobStatus` | `None` | USED |


## casare_rpa.domain.orchestrator.entities.robot

**File:** `src\casare_rpa\domain\orchestrator\entities\robot.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Robot | `self` | `-` | DUNDER |
| `assign_job` | Robot | `self, job_id: str` | `None` | USED |
| `assign_workflow` | Robot | `self, workflow_id: str` | `None` | UNUSED |
| `can_accept_job` | Robot | `self` | `bool` | USED |
| `complete_job` | Robot | `self, job_id: str` | `None` | USED |
| `current_jobs` | Robot | `self` | `int` | UNUSED |
| `from_dict` | Robot | `cls, data: Dict[str, Any]` | `'Robot'` | USED |
| `has_all_capabilities` | Robot | `self, capabilities: Set[RobotCapability]` | `bool` | USED |
| `has_capability` | Robot | `self, capability: RobotCapability` | `bool` | USED |
| `is_assigned_to_workflow` | Robot | `self, workflow_id: str` | `bool` | UNUSED |
| `is_available` | Robot | `self` | `bool` | UNUSED |
| `to_dict` | Robot | `self` | `Dict[str, Any]` | USED |
| `unassign_workflow` | Robot | `self, workflow_id: str` | `None` | UNUSED |
| `utilization` | Robot | `self` | `float` | UNUSED |


## casare_rpa.domain.orchestrator.entities.schedule

**File:** `src\casare_rpa\domain\orchestrator\entities\schedule.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Schedule | `self` | `-` | DUNDER |
| `from_dict` | Schedule | `cls, data: Dict[str, Any]` | `'Schedule'` | USED |
| `success_rate` | Schedule | `self` | `float` | UNUSED |
| `to_dict` | Schedule | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.orchestrator.entities.workflow

**File:** `src\casare_rpa\domain\orchestrator\entities\workflow.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | Workflow | `self` | `-` | DUNDER |
| `from_dict` | Workflow | `cls, data: Dict[str, Any]` | `'Workflow'` | USED |
| `success_rate` | Workflow | `self` | `float` | UNUSED |
| `to_dict` | Workflow | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.orchestrator.protocols.robot_protocol

**File:** `src\casare_rpa\domain\orchestrator\protocols\robot_protocol.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_json` | Message | `cls, json_str: str` | `'Message'` | USED |
| `to_json` | Message | `self` | `str` | USED |
| `disconnect` | MessageBuilder | `robot_id: str, reason: str` | `Message` | USED |
| `error` | MessageBuilder | `error_code: str, error_message: str, details: Optional[Dict[str, Any]], ...` | `Message` | USED |
| `heartbeat` | MessageBuilder | `robot_id: str, status: str, current_jobs: int, ...` | `Message` | USED |
| `heartbeat_ack` | MessageBuilder | `robot_id: str, correlation_id: Optional[str]` | `Message` | USED |
| `job_accept` | MessageBuilder | `job_id: str, robot_id: str, correlation_id: Optional[str]` | `Message` | USED |
| `job_assign` | MessageBuilder | `job_id: str, workflow_id: str, workflow_name: str, ...` | `Message` | USED |
| `job_cancel` | MessageBuilder | `job_id: str, reason: str` | `Message` | USED |
| `job_cancelled` | MessageBuilder | `job_id: str, robot_id: str, correlation_id: Optional[str]` | `Message` | USED |
| `job_complete` | MessageBuilder | `job_id: str, robot_id: str, result: Optional[Dict[str, Any]], ...` | `Message` | USED |
| `job_failed` | MessageBuilder | `job_id: str, robot_id: str, error_message: str, ...` | `Message` | USED |
| `job_progress` | MessageBuilder | `job_id: str, robot_id: str, progress: int, ...` | `Message` | USED |
| `job_reject` | MessageBuilder | `job_id: str, robot_id: str, reason: str, ...` | `Message` | USED |
| `log_batch` | MessageBuilder | `job_id: str, robot_id: str, entries: List[Dict[str, Any]]` | `Message` | USED |
| `log_entry` | MessageBuilder | `job_id: str, robot_id: str, level: str, ...` | `Message` | USED |
| `pause` | MessageBuilder | `robot_id: str` | `Message` | USED |
| `register` | MessageBuilder | `robot_id: str, robot_name: str, environment: str, ...` | `Message` | USED |
| `register_ack` | MessageBuilder | `robot_id: str, success: bool, message: str, ...` | `Message` | USED |
| `resume` | MessageBuilder | `robot_id: str` | `Message` | USED |
| `shutdown` | MessageBuilder | `robot_id: str, graceful: bool` | `Message` | USED |
| `status_request` | MessageBuilder | `robot_id: str` | `Message` | USED |
| `status_response` | MessageBuilder | `robot_id: str, status: str, current_jobs: int, ...` | `Message` | USED |


## casare_rpa.domain.orchestrator.repositories.job_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\job_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | JobRepository | `self, job_id: str` | `None` | USED |
| `async get_all` | JobRepository | `self` | `List[Job]` | USED |
| `async get_by_id` | JobRepository | `self, job_id: str` | `Optional[Job]` | USED |
| `async get_by_robot` | JobRepository | `self, robot_id: str` | `List[Job]` | USED |
| `async get_by_status` | JobRepository | `self, status: JobStatus` | `List[Job]` | USED |
| `async get_by_workflow` | JobRepository | `self, workflow_id: str` | `List[Job]` | USED |
| `async save` | JobRepository | `self, job: Job` | `None` | USED |


## casare_rpa.domain.orchestrator.repositories.robot_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\robot_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | RobotRepository | `self, robot_id: str` | `None` | USED |
| `async get_all` | RobotRepository | `self` | `List[Robot]` | USED |
| `async get_all_online` | RobotRepository | `self` | `List[Robot]` | UNUSED |
| `async get_by_environment` | RobotRepository | `self, environment: str` | `List[Robot]` | UNUSED |
| `async get_by_id` | RobotRepository | `self, robot_id: str` | `Optional[Robot]` | USED |
| `async save` | RobotRepository | `self, robot: Robot` | `None` | USED |
| `async update_status` | RobotRepository | `self, robot_id: str, status: RobotStatus` | `None` | USED |


## casare_rpa.domain.orchestrator.repositories.schedule_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\schedule_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | ScheduleRepository | `self, schedule_id: str` | `None` | USED |
| `async get_all` | ScheduleRepository | `self` | `List[Schedule]` | USED |
| `async get_by_id` | ScheduleRepository | `self, schedule_id: str` | `Optional[Schedule]` | USED |
| `async get_enabled` | ScheduleRepository | `self` | `List[Schedule]` | USED |
| `async save` | ScheduleRepository | `self, schedule: Schedule` | `None` | USED |


## casare_rpa.domain.orchestrator.repositories.trigger_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\trigger_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | TriggerRepository | `self, trigger_id: str` | `None` | USED |
| `async delete_by_scenario` | TriggerRepository | `self, scenario_id: str` | `int` | UNUSED |
| `async get_all` | TriggerRepository | `self` | `List[BaseTriggerConfig]` | USED |
| `async get_by_id` | TriggerRepository | `self, trigger_id: str` | `Optional[BaseTriggerConfig]` | USED |
| `async get_by_scenario` | TriggerRepository | `self, scenario_id: str` | `List[BaseTriggerConfig]` | UNUSED |
| `async get_by_type` | TriggerRepository | `self, trigger_type: TriggerType` | `List[BaseTriggerConfig]` | UNUSED |
| `async get_by_workflow` | TriggerRepository | `self, workflow_id: str` | `List[BaseTriggerConfig]` | USED |
| `async get_enabled` | TriggerRepository | `self` | `List[BaseTriggerConfig]` | USED |
| `async save` | TriggerRepository | `self, trigger: BaseTriggerConfig` | `None` | USED |


## casare_rpa.domain.orchestrator.repositories.workflow_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\workflow_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | WorkflowRepository | `self, workflow_id: str` | `None` | USED |
| `async get_all` | WorkflowRepository | `self` | `List[Workflow]` | USED |
| `async get_by_id` | WorkflowRepository | `self, workflow_id: str` | `Optional[Workflow]` | USED |
| `async get_by_status` | WorkflowRepository | `self, status: WorkflowStatus` | `List[Workflow]` | USED |
| `async save` | WorkflowRepository | `self, workflow: Workflow` | `None` | USED |


## casare_rpa.domain.orchestrator.services.robot_selection_service

**File:** `src\casare_rpa\domain\orchestrator\services\robot_selection_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_find_robot_by_id` | RobotSelectionService | `self, robot_id: str, robots: List[Robot]` | `Optional[Robot]` | INTERNAL |
| `_get_node_override` | RobotSelectionService | `self, workflow_id: str, node_id: str, ...` | `Optional[NodeRobotOverride]` | INTERNAL |
| `_get_workflow_assignment` | RobotSelectionService | `self, workflow_id: str, assignments: List[RobotAssignment]` | `Optional[str]` | INTERNAL |
| `_select_least_loaded` | RobotSelectionService | `self, robots: List[Robot]` | `Robot` | INTERNAL |
| `calculate_robot_scores` | RobotSelectionService | `self, robots: List[Robot], workflow_id: str, ...` | `Dict[str, float]` | UNUSED |
| `get_available_robots` | RobotSelectionService | `self, robots: List[Robot], required_capabilities: Optional[Set[RobotCapability]]` | `List[Robot]` | USED |
| `get_robots_by_capability` | RobotSelectionService | `self, robots: List[Robot], capability: RobotCapability, ...` | `List[Robot]` | UNUSED |
| `select_robot_for_node` | RobotSelectionService | `self, workflow_id: str, node_id: str, ...` | `str` | UNUSED |
| `select_robot_for_workflow` | RobotSelectionService | `self, workflow_id: str, robots: List[Robot], ...` | `str` | USED |


## casare_rpa.domain.orchestrator.value_objects.node_robot_override

**File:** `src\casare_rpa\domain\orchestrator\value_objects\node_robot_override.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | NodeRobotOverride | `self` | `-` | DUNDER |
| `__repr__` | NodeRobotOverride | `self` | `str` | DUNDER |
| `from_dict` | NodeRobotOverride | `cls, data: dict` | `'NodeRobotOverride'` | USED |
| `is_capability_based` | NodeRobotOverride | `self` | `bool` | UNUSED |
| `is_specific_robot` | NodeRobotOverride | `self` | `bool` | UNUSED |
| `to_dict` | NodeRobotOverride | `self` | `dict` | USED |


## casare_rpa.domain.orchestrator.value_objects.robot_assignment

**File:** `src\casare_rpa\domain\orchestrator\value_objects\robot_assignment.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | RobotAssignment | `self` | `-` | DUNDER |
| `__repr__` | RobotAssignment | `self` | `str` | DUNDER |
| `from_dict` | RobotAssignment | `cls, data: dict` | `'RobotAssignment'` | USED |
| `to_dict` | RobotAssignment | `self` | `dict` | USED |


## casare_rpa.domain.ports.port_type_interfaces

**File:** `src\casare_rpa\domain\ports\port_type_interfaces.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_incompatibility_reason` | DefaultCompatibilityRule | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `is_compatible` | DefaultCompatibilityRule | `self, source: DataType, target: DataType` | `bool` | USED |
| `get_compatible_types` | PortTypeRegistryProtocol | `self, source: DataType` | `Set[DataType]` | UNUSED |
| `get_exec_color` | PortTypeRegistryProtocol | `self` | `Tuple[int, int, int, int]` | USED |
| `get_incompatibility_reason` | PortTypeRegistryProtocol | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `get_type_color` | PortTypeRegistryProtocol | `self, data_type: DataType` | `Tuple[int, int, int, int]` | USED |
| `get_type_info` | PortTypeRegistryProtocol | `self, data_type: DataType` | `PortTypeInfo` | USED |
| `get_type_shape` | PortTypeRegistryProtocol | `self, data_type: DataType` | `PortShape` | USED |
| `is_compatible` | PortTypeRegistryProtocol | `self, source: DataType, target: DataType` | `bool` | USED |
| `get_incompatibility_reason` | TypeCompatibilityRule | `self, source: DataType, target: DataType` | `Optional[str]` | USED |
| `is_compatible` | TypeCompatibilityRule | `self, source: DataType, target: DataType` | `bool` | USED |


## casare_rpa.domain.protocols.credential_protocols

**File:** `src\casare_rpa\domain\protocols\credential_protocols.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async get_credential` | CredentialProviderProtocol | `self, alias: str, required: bool` | `Optional[ResolvedCredentialData]` | USED |
| `async get_credential_by_path` | CredentialProviderProtocol | `self, vault_path: str, alias: Optional[str]` | `ResolvedCredentialData` | USED |
| `register_bindings` | CredentialProviderProtocol | `self, bindings: Dict[str, str]` | `None` | USED |
| `get_variable` | ExecutionContextProtocol | `self, name: str, default: Any` | `Any` | USED |
| `has_project_context` | ExecutionContextProtocol | `self` | `bool` | UNUSED |
| `project_context` | ExecutionContextProtocol | `self` | `Optional[Any]` | UNUSED |
| `resolve_value` | ExecutionContextProtocol | `self, value: Any` | `Any` | USED |
| `resources` | ExecutionContextProtocol | `self` | `Dict[str, Any]` | UNUSED |


## casare_rpa.domain.repositories.project_repository

**File:** `src\casare_rpa\domain\repositories\project_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async delete` | ProjectRepository | `self, project_id: str, remove_files: bool` | `None` | USED |
| `async delete_scenario` | ProjectRepository | `self, project_id: str, scenario_id: str` | `None` | USED |
| `async exists` | ProjectRepository | `self, project_id: str` | `bool` | USED |
| `async get_all` | ProjectRepository | `self` | `List[Project]` | USED |
| `async get_by_id` | ProjectRepository | `self, project_id: str` | `Optional[Project]` | USED |
| `async get_by_path` | ProjectRepository | `self, path: Path` | `Optional[Project]` | USED |
| `async get_global_credentials` | ProjectRepository | `self` | `CredentialBindingsFile` | UNUSED |
| `async get_global_variables` | ProjectRepository | `self` | `VariablesFile` | USED |
| `async get_project_credentials` | ProjectRepository | `self, project_id: str` | `CredentialBindingsFile` | UNUSED |
| `async get_project_variables` | ProjectRepository | `self, project_id: str` | `VariablesFile` | USED |
| `async get_projects_index` | ProjectRepository | `self` | `ProjectsIndex` | USED |
| `async get_scenario` | ProjectRepository | `self, project_id: str, scenario_id: str` | `Optional[Scenario]` | USED |
| `async get_scenarios` | ProjectRepository | `self, project_id: str` | `List[Scenario]` | USED |
| `async save` | ProjectRepository | `self, project: Project` | `None` | USED |
| `async save_global_credentials` | ProjectRepository | `self, credentials: CredentialBindingsFile` | `None` | USED |
| `async save_global_variables` | ProjectRepository | `self, variables: VariablesFile` | `None` | USED |
| `async save_project_credentials` | ProjectRepository | `self, project_id: str, credentials: CredentialBindingsFile` | `None` | USED |
| `async save_project_variables` | ProjectRepository | `self, project_id: str, variables: VariablesFile` | `None` | USED |
| `async save_projects_index` | ProjectRepository | `self, index: ProjectsIndex` | `None` | USED |
| `async save_scenario` | ProjectRepository | `self, project_id: str, scenario: Scenario` | `None` | USED |
| `async update_project_opened` | ProjectRepository | `self, project_id: str` | `None` | USED |


## casare_rpa.domain.schemas.property_schema

**File:** `src\casare_rpa\domain\schemas\property_schema.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_coerce_value` | NodeSchema | `self, prop: PropertyDef, value: Any` | `Any` | INTERNAL |
| `_validate_type` | NodeSchema | `self, prop: PropertyDef, value: Any` | `bool` | INTERNAL |
| `get_default_config` | NodeSchema | `self` | `Dict[str, Any]` | USED |
| `get_property` | NodeSchema | `self, name: str` | `Optional[PropertyDef]` | USED |
| `validate_config` | NodeSchema | `self, config: Dict[str, Any]` | `Tuple[bool, str]` | USED |
| `__post_init__` | PropertyDef | `self` | `-` | DUNDER |


## casare_rpa.domain.services.execution_orchestrator

**File:** `src\casare_rpa\domain\services\execution_orchestrator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionOrchestrator | `self, workflow: WorkflowSchema` | `None` | DUNDER |
| `__repr__` | ExecutionOrchestrator | `self` | `str` | DUNDER |
| `_calculate_subgraph` | ExecutionOrchestrator | `self, start_node_id: NodeId, target_node_id: NodeId` | `Set[NodeId]` | INTERNAL |
| `_get_connections_from_port` | ExecutionOrchestrator | `self, node_id: NodeId, port_name: str` | `List` | INTERNAL |
| `build_dependency_graph` | ExecutionOrchestrator | `self` | `Dict[NodeId, Set[NodeId]]` | USED |
| `calculate_execution_path` | ExecutionOrchestrator | `self, start_node_id: NodeId, target_node_id: Optional[NodeId]` | `Set[NodeId]` | USED |
| `find_all_start_nodes` | ExecutionOrchestrator | `self` | `List[NodeId]` | USED |
| `find_loop_body_nodes` | ExecutionOrchestrator | `self, loop_node_id: NodeId` | `Set[NodeId]` | UNUSED |
| `find_start_node` | ExecutionOrchestrator | `self` | `Optional[NodeId]` | USED |
| `find_trigger_node` | ExecutionOrchestrator | `self` | `Optional[NodeId]` | UNUSED |
| `find_try_body_nodes` | ExecutionOrchestrator | `self, try_node_id: NodeId` | `Set[NodeId]` | UNUSED |
| `get_all_nodes` | ExecutionOrchestrator | `self` | `List[NodeId]` | UNUSED |
| `get_next_nodes` | ExecutionOrchestrator | `self, current_node_id: NodeId, execution_result: Optional[Dict[str, Any]]` | `List[NodeId]` | USED |
| `get_node_type` | ExecutionOrchestrator | `self, node_id: NodeId` | `str` | USED |
| `handle_control_flow` | ExecutionOrchestrator | `self, node_id: NodeId, result: Dict[str, Any]` | `Optional[str]` | UNUSED |
| `is_control_flow_node` | ExecutionOrchestrator | `self, node_id: NodeId` | `bool` | USED |
| `is_reachable` | ExecutionOrchestrator | `self, start_node_id: NodeId, target_node_id: NodeId` | `bool` | USED |
| `is_trigger_node` | ExecutionOrchestrator | `self, node_id: NodeId` | `bool` | UNUSED |
| `should_stop_on_error` | ExecutionOrchestrator | `self, error: Exception, settings: Dict[str, Any]` | `bool` | UNUSED |
| `validate_execution_order` | ExecutionOrchestrator | `self` | `tuple[bool, List[str]]` | UNUSED |


## casare_rpa.domain.services.project_context

**File:** `src\casare_rpa\domain\services\project_context.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ProjectContext | `self, project: Project, scenario: Optional[Scenario], ...` | `None` | DUNDER |
| `__repr__` | ProjectContext | `self` | `str` | DUNDER |
| `get_all_credential_aliases` | ProjectContext | `self` | `Dict[str, str]` | UNUSED |
| `get_default_browser` | ProjectContext | `self` | `str` | UNUSED |
| `get_global_variables` | ProjectContext | `self` | `Dict[str, Any]` | USED |
| `get_merged_variables` | ProjectContext | `self` | `Dict[str, Any]` | UNUSED |
| `get_project_variables` | ProjectContext | `self` | `Dict[str, Any]` | USED |
| `get_retry_count` | ProjectContext | `self` | `int` | UNUSED |
| `get_scenario_variables` | ProjectContext | `self` | `Dict[str, Any]` | USED |
| `get_stop_on_error` | ProjectContext | `self` | `bool` | USED |
| `get_timeout` | ProjectContext | `self` | `int` | USED |
| `get_variable` | ProjectContext | `self, name: str, default: Any` | `Any` | USED |
| `project` | ProjectContext | `self` | `Project` | UNUSED |
| `project_id` | ProjectContext | `self` | `str` | UNUSED |
| `project_name` | ProjectContext | `self` | `str` | UNUSED |
| `resolve_credential_path` | ProjectContext | `self, alias: str` | `Optional[str]` | USED |
| `scenario` | ProjectContext | `self` | `Optional[Scenario]` | UNUSED |
| `scenario_id` | ProjectContext | `self` | `Optional[str]` | UNUSED |
| `scenario_name` | ProjectContext | `self` | `Optional[str]` | UNUSED |


## casare_rpa.domain.services.variable_resolver

**File:** `src\casare_rpa\domain\services\variable_resolver.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `extract_variable_names` | - | `value: str` | `list` | UNUSED |
| `has_variables` | - | `value: str` | `bool` | UNUSED |
| `replace_match` | - | `match: re.Match` | `str` | UNUSED |
| `resolve_dict_variables` | - | `data: Dict[str, Any], variables: Dict[str, Any]` | `Dict[str, Any]` | USED |
| `resolve_variables` | - | `value: Any, variables: Dict[str, Any]` | `Any` | USED |


## casare_rpa.domain.validation.rules

**File:** `src\casare_rpa\domain\validation\rules.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `find_entry_points_and_reachable` | - | `nodes: Dict[str, Any], connections: List[Dict[str, Any]]` | `Tuple[List[str], Set[str]]` | USED |
| `find_reachable_nodes` | - | `nodes: Dict[str, Any], connections: List[Dict[str, Any]]` | `Set[str]` | UNUSED |
| `has_circular_dependency` | - | `nodes: Dict[str, Any], connections: List[Dict[str, Any]]` | `bool` | USED |
| `is_exec_input_port` | - | `port_name: str` | `bool` | USED |
| `is_exec_port` | - | `port_name: str` | `bool` | USED |
| `parse_connection` | - | `conn: Dict[str, Any]` | `Optional[Dict[str, str]]` | USED |


## casare_rpa.domain.validation.schemas

**File:** `src\casare_rpa\domain\validation\schemas.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_valid_node_types` | - | `` | `Set[str]` | INTERNAL |
| `get_valid_node_types` | - | `` | `Set[str]` | USED |


## casare_rpa.domain.validation.types

**File:** `src\casare_rpa\domain\validation\types.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | ValidationIssue | `self` | `Dict[str, Any]` | USED |
| `add_error` | ValidationResult | `self, code: str, message: str, ...` | `None` | USED |
| `add_info` | ValidationResult | `self, code: str, message: str, ...` | `None` | UNUSED |
| `add_warning` | ValidationResult | `self, code: str, message: str, ...` | `None` | USED |
| `error_count` | ValidationResult | `self` | `int` | UNUSED |
| `errors` | ValidationResult | `self` | `List[ValidationIssue]` | USED |
| `format_summary` | ValidationResult | `self` | `str` | USED |
| `merge` | ValidationResult | `self, other: 'ValidationResult'` | `None` | UNUSED |
| `to_dict` | ValidationResult | `self` | `Dict[str, Any]` | USED |
| `warning_count` | ValidationResult | `self` | `int` | UNUSED |
| `warnings` | ValidationResult | `self` | `List[ValidationIssue]` | UNUSED |


## casare_rpa.domain.validation.validators

**File:** `src\casare_rpa\domain\validation\validators.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_validate_connections` | - | `connections: List[Dict[str, str]], node_ids: Set[str], result: ValidationResult` | `None` | INTERNAL |
| `_validate_metadata` | - | `metadata: Dict[str, Any], result: ValidationResult` | `None` | INTERNAL |
| `_validate_node` | - | `node_id: str, node_data: Dict[str, Any], result: ValidationResult` | `None` | INTERNAL |
| `_validate_structure` | - | `data: Dict[str, Any], result: ValidationResult` | `None` | INTERNAL |
| `_validate_workflow_semantics` | - | `data: Dict[str, Any], result: ValidationResult` | `None` | INTERNAL |
| `quick_validate` | - | `data: Dict[str, Any]` | `Tuple[bool, List[str]]` | USED |
| `validate_connections` | - | `connections: List[Dict[str, str]], node_ids: Set[str]` | `ValidationResult` | UNUSED |
| `validate_node` | - | `node_id: str, node_data: Dict[str, Any]` | `ValidationResult` | UNUSED |
| `validate_workflow` | - | `data: Dict[str, Any]` | `ValidationResult` | USED |


## casare_rpa.domain.value_objects.log_entry

**File:** `src\casare_rpa\domain\value_objects\log_entry.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | LogBatch | `cls, data: Dict[str, Any], tenant_id: str` | `'LogBatch'` | USED |
| `to_dict` | LogBatch | `self` | `Dict[str, Any]` | USED |
| `__post_init__` | LogEntry | `self` | `None` | DUNDER |
| `from_dict` | LogEntry | `cls, data: Dict[str, Any]` | `'LogEntry'` | USED |
| `to_dict` | LogEntry | `self` | `Dict[str, Any]` | USED |
| `__ge__` | LogLevel | `self, other: 'LogLevel'` | `bool` | DUNDER |
| `__gt__` | LogLevel | `self, other: 'LogLevel'` | `bool` | DUNDER |
| `__le__` | LogLevel | `self, other: 'LogLevel'` | `bool` | DUNDER |
| `__lt__` | LogLevel | `self, other: 'LogLevel'` | `bool` | DUNDER |
| `from_string` | LogLevel | `cls, level: str` | `'LogLevel'` | USED |
| `severity` | LogLevel | `self` | `int` | UNUSED |
| `__post_init__` | LogQuery | `self` | `None` | DUNDER |
| `to_dict` | LogQuery | `self` | `Dict[str, Any]` | USED |
| `to_dict` | LogStats | `self` | `Dict[str, Any]` | USED |


## casare_rpa.domain.value_objects.port

**File:** `src\casare_rpa\domain\value_objects\port.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__eq__` | Port | `self, other: object` | `bool` | DUNDER |
| `__hash__` | Port | `self` | `int` | DUNDER |
| `__init__` | Port | `self, name: str, port_type: PortType, ...` | `None` | DUNDER |
| `__repr__` | Port | `self` | `str` | DUNDER |
| `_validate_name` | Port | `name: str` | `None` | INTERNAL |
| `data_type` | Port | `self` | `DataType` | UNUSED |
| `from_dict` | Port | `cls, data: PortDefinition` | `'Port'` | USED |
| `get_value` | Port | `self` | `Any` | USED |
| `label` | Port | `self` | `str` | UNUSED |
| `name` | Port | `self` | `str` | USED |
| `port_type` | Port | `self` | `PortType` | USED |
| `required` | Port | `self` | `bool` | UNUSED |
| `set_value` | Port | `self, value: Any` | `None` | USED |
| `to_dict` | Port | `self` | `PortDefinition` | USED |


## casare_rpa.domain.value_objects.types

**File:** `src\casare_rpa\domain\value_objects\types.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `category` | ErrorCode | `self` | `str` | UNUSED |
| `from_exception` | ErrorCode | `cls, exception: Exception` | `'ErrorCode'` | USED |
| `is_retryable` | ErrorCode | `self` | `bool` | UNUSED |


## casare_rpa.domain.workflow.templates

**File:** `src\casare_rpa\domain\workflow\templates.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_string` | TemplateCategory | `cls, value: str` | `'TemplateCategory'` | USED |
| `__post_init__` | TemplateMetadata | `self` | `None` | DUNDER |
| `from_dict` | TemplateMetadata | `cls, data: Dict[str, Any]` | `'TemplateMetadata'` | USED |
| `to_dict` | TemplateMetadata | `self` | `Dict[str, Any]` | USED |
| `touch_modified` | TemplateMetadata | `self` | `None` | USED |
| `from_dict` | TemplateParameter | `cls, data: Dict[str, Any]` | `'TemplateParameter'` | USED |
| `get_effective_value` | TemplateParameter | `self, provided_value: Optional[ParameterValue]` | `ParameterValue` | USED |
| `to_dict` | TemplateParameter | `self` | `Dict[str, Any]` | USED |
| `validate_value` | TemplateParameter | `self, value: ParameterValue` | `tuple[bool, Optional[str]]` | USED |
| `validate_value` | TemplateParameterType | `self, value: ParameterValue, constraints: Optional[ConstraintDict]` | `tuple[bool, Optional[str]]` | USED |
| `__post_init__` | TemplateReview | `self` | `None` | DUNDER |
| `__repr__` | TemplateReview | `self` | `str` | DUNDER |
| `create_new` | TemplateReview | `cls, template_id: str, rating: int, ...` | `'TemplateReview'` | USED |
| `from_dict` | TemplateReview | `cls, data: Dict[str, Any]` | `'TemplateReview'` | USED |
| `helpfulness_score` | TemplateReview | `self` | `float` | UNUSED |
| `mark_helpful` | TemplateReview | `self, helpful: bool` | `None` | UNUSED |
| `to_dict` | TemplateReview | `self` | `Dict[str, Any]` | USED |
| `update` | TemplateReview | `self, rating: Optional[int], title: Optional[str], ...` | `None` | USED |
| `add_rating` | TemplateUsageStats | `self, rating: float` | `None` | USED |
| `from_dict` | TemplateUsageStats | `cls, data: Dict[str, Any]` | `'TemplateUsageStats'` | USED |
| `record_use` | TemplateUsageStats | `self, success: bool` | `None` | USED |
| `success_rate` | TemplateUsageStats | `self` | `Optional[float]` | UNUSED |
| `to_dict` | TemplateUsageStats | `self` | `Dict[str, Any]` | USED |
| `__post_init__` | TemplateVersion | `self` | `None` | DUNDER |
| `__repr__` | TemplateVersion | `self` | `str` | DUNDER |
| `create_from_template` | TemplateVersion | `cls, template: 'WorkflowTemplate', version: str, ...` | `'TemplateVersion'` | UNUSED |
| `from_dict` | TemplateVersion | `cls, data: Dict[str, Any]` | `'TemplateVersion'` | USED |
| `publish` | TemplateVersion | `self, published_by: Optional[str]` | `None` | USED |
| `to_dict` | TemplateVersion | `self` | `Dict[str, Any]` | USED |
| `__repr__` | WorkflowTemplate | `self` | `str` | DUNDER |
| `_find_placeholders_recursive` | WorkflowTemplate | `self, obj: Union[str, Dict[str, JsonValue], List[JsonValue], JsonValue], placeholders: Set[str]` | `None` | INTERNAL |
| `_substitute_placeholders` | WorkflowTemplate | `self, obj: Union[str, Dict[str, JsonValue], List[JsonValue], JsonValue], values: Dict[str, ParameterValue]` | `Union[str, Dict[str, JsonValue], List[JsonValue], JsonValue]` | INTERNAL |
| `add_parameter` | WorkflowTemplate | `self, parameter: TemplateParameter` | `None` | USED |
| `category` | WorkflowTemplate | `self` | `TemplateCategory` | UNUSED |
| `clone` | WorkflowTemplate | `self, new_name: Optional[str]` | `'WorkflowTemplate'` | USED |
| `create_new` | WorkflowTemplate | `cls, name: str, description: str, ...` | `'WorkflowTemplate'` | USED |
| `export_json` | WorkflowTemplate | `self` | `bytes` | USED |
| `file_path` | WorkflowTemplate | `self` | `Optional[Path]` | UNUSED |
| `file_path` | WorkflowTemplate | `self, value: Path` | `None` | UNUSED |
| `find_placeholders` | WorkflowTemplate | `self` | `Set[str]` | USED |
| `from_dict` | WorkflowTemplate | `cls, data: Dict[str, Any]` | `'WorkflowTemplate'` | USED |
| `get_missing_parameters` | WorkflowTemplate | `self, values: Dict[str, ParameterValue]` | `List[str]` | USED |
| `get_parameter` | WorkflowTemplate | `self, name: str` | `Optional[TemplateParameter]` | USED |
| `get_parameters_by_group` | WorkflowTemplate | `self` | `Dict[str, List[TemplateParameter]]` | UNUSED |
| `get_required_parameters` | WorkflowTemplate | `self` | `List[TemplateParameter]` | UNUSED |
| `import_json` | WorkflowTemplate | `cls, json_data: bytes` | `'WorkflowTemplate'` | USED |
| `instantiate` | WorkflowTemplate | `self, values: Dict[str, ParameterValue], validate: bool` | `tuple[Dict[str, JsonValue], List[str]]` | USED |
| `name` | WorkflowTemplate | `self` | `str` | USED |
| `remove_parameter` | WorkflowTemplate | `self, name: str` | `bool` | UNUSED |
| `to_dict` | WorkflowTemplate | `self` | `Dict[str, Any]` | USED |
| `validate_parameters` | WorkflowTemplate | `self, values: Dict[str, ParameterValue]` | `tuple[bool, List[str]]` | USED |


## casare_rpa.domain.workflow.versioning

**File:** `src\casare_rpa\domain\workflow\versioning.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | BreakingChange | `self` | `Dict[str, Any]` | USED |
| `error_count` | CompatibilityResult | `self` | `int` | UNUSED |
| `has_breaking_changes` | CompatibilityResult | `self` | `bool` | UNUSED |
| `to_dict` | CompatibilityResult | `self` | `Dict[str, Any]` | USED |
| `__ge__` | SemanticVersion | `self, other: 'SemanticVersion'` | `bool` | DUNDER |
| `__gt__` | SemanticVersion | `self, other: 'SemanticVersion'` | `bool` | DUNDER |
| `__le__` | SemanticVersion | `self, other: 'SemanticVersion'` | `bool` | DUNDER |
| `__lt__` | SemanticVersion | `self, other: 'SemanticVersion'` | `bool` | DUNDER |
| `__post_init__` | SemanticVersion | `self` | `None` | DUNDER |
| `__str__` | SemanticVersion | `self` | `str` | DUNDER |
| `bump_major` | SemanticVersion | `self` | `'SemanticVersion'` | USED |
| `bump_minor` | SemanticVersion | `self` | `'SemanticVersion'` | USED |
| `bump_patch` | SemanticVersion | `self` | `'SemanticVersion'` | USED |
| `initial` | SemanticVersion | `cls` | `'SemanticVersion'` | USED |
| `is_compatible_with` | SemanticVersion | `self, other: 'SemanticVersion'` | `bool` | UNUSED |
| `is_prerelease` | SemanticVersion | `self` | `bool` | UNUSED |
| `parse` | SemanticVersion | `cls, version_string: str` | `'SemanticVersion'` | USED |
| `with_build` | SemanticVersion | `self, build: str` | `'SemanticVersion'` | UNUSED |
| `with_prerelease` | SemanticVersion | `self, prerelease: str` | `'SemanticVersion'` | UNUSED |
| `has_changes` | VersionDiff | `self` | `bool` | UNUSED |
| `to_dict` | VersionDiff | `self` | `Dict[str, Any]` | USED |
| `__init__` | VersionHistory | `self, workflow_id: str` | `None` | DUNDER |
| `__repr__` | VersionHistory | `self` | `str` | DUNDER |
| `_set_active_version` | VersionHistory | `self, version_str: str` | `None` | INTERNAL |
| `activate_version` | VersionHistory | `self, version_str: str` | `bool` | UNUSED |
| `active_version` | VersionHistory | `self` | `Optional[WorkflowVersion]` | UNUSED |
| `add_version` | VersionHistory | `self, version: WorkflowVersion` | `None` | USED |
| `can_rollback_to` | VersionHistory | `self, version_str: str` | `Tuple[bool, str]` | UNUSED |
| `check_compatibility` | VersionHistory | `self, from_version: str, to_version: str` | `CompatibilityResult` | USED |
| `create_new_version` | VersionHistory | `self, workflow_data: Dict[str, Any], bump_type: str, ...` | `WorkflowVersion` | USED |
| `from_dict` | VersionHistory | `cls, data: Dict[str, Any]` | `'VersionHistory'` | USED |
| `generate_diff` | VersionHistory | `self, from_version: str, to_version: str` | `Optional[VersionDiff]` | USED |
| `get_version` | VersionHistory | `self, version_str: str` | `Optional[WorkflowVersion]` | USED |
| `get_version_timeline` | VersionHistory | `self` | `List[Dict[str, Any]]` | UNUSED |
| `get_versions_by_status` | VersionHistory | `self, status: VersionStatus` | `List[WorkflowVersion]` | UNUSED |
| `latest_version` | VersionHistory | `self` | `Optional[WorkflowVersion]` | UNUSED |
| `to_dict` | VersionHistory | `self` | `Dict[str, Any]` | USED |
| `version_count` | VersionHistory | `self` | `int` | UNUSED |
| `__post_init__` | WorkflowVersion | `self` | `None` | DUNDER |
| `__repr__` | WorkflowVersion | `self` | `str` | DUNDER |
| `_compute_checksum` | WorkflowVersion | `self` | `None` | INTERNAL |
| `can_execute` | WorkflowVersion | `self` | `bool` | USED |
| `can_modify` | WorkflowVersion | `self` | `bool` | UNUSED |
| `from_dict` | WorkflowVersion | `cls, data: Dict[str, Any]` | `'WorkflowVersion'` | USED |
| `is_active` | WorkflowVersion | `self` | `bool` | USED |
| `is_archived` | WorkflowVersion | `self` | `bool` | USED |
| `is_deprecated` | WorkflowVersion | `self` | `bool` | UNUSED |
| `is_draft` | WorkflowVersion | `self` | `bool` | UNUSED |
| `to_dict` | WorkflowVersion | `self` | `Dict[str, Any]` | USED |
| `transition_to` | WorkflowVersion | `self, new_status: VersionStatus` | `bool` | USED |
