# Domain Layer API

**Modules:** 55 | **Classes:** 118 | **Functions:** 33


## Modules

| Module | Classes | Functions | Description |
|--------|---------|-----------|-------------|
| `casare_rpa.domain.credentials` | 2 | 2 | CasareRPA - Node Credential System |
| `casare_rpa.domain.decorators` | 0 | 2 | CasareRPA - Node Decorators |
| `casare_rpa.domain.entities.base_node` | 1 | 0 | CasareRPA - Base Node Abstract Class |
| `casare_rpa.domain.entities.execution_state` | 1 | 0 | CasareRPA - Domain Entity: Execution State |
| `casare_rpa.domain.entities.node_connection` | 1 | 0 | CasareRPA - Domain Entity: Node Connection |
| `casare_rpa.domain.entities.project.base` | 0 | 2 | CasareRPA - Project Base Constants and Utilities |
| `casare_rpa.domain.entities.project.credentials` | 2 | 0 | CasareRPA - Credential Bindings |
| `casare_rpa.domain.entities.project.index` | 2 | 0 | CasareRPA - Project Index |
| `casare_rpa.domain.entities.project.project` | 1 | 0 | CasareRPA - Project Entity |
| `casare_rpa.domain.entities.project.scenario` | 1 | 0 | CasareRPA - Scenario Entity |
| `casare_rpa.domain.entities.project.settings` | 2 | 0 | CasareRPA - Project Settings |
| `casare_rpa.domain.entities.project.variables` | 3 | 0 | CasareRPA - Project Variables |
| `casare_rpa.domain.entities.tenant` | 3 | 0 | Tenant domain entity. |
| `casare_rpa.domain.entities.variable` | 1 | 0 | CasareRPA - Domain Entity: Variable |
| `casare_rpa.domain.entities.workflow` | 1 | 0 | CasareRPA - Domain Entity: Workflow |
| `casare_rpa.domain.entities.workflow_metadata` | 1 | 0 | CasareRPA - Domain Entity: Workflow Metadata |
| `casare_rpa.domain.entities.workflow_schedule` | 2 | 0 | WorkflowSchedule domain entity. |
| `casare_rpa.domain.errors.context` | 2 | 0 | CasareRPA - Error Context and Recovery Decision. |
| `casare_rpa.domain.errors.handlers.base` | 1 | 0 | CasareRPA - Base Error Handler. |
| `casare_rpa.domain.errors.handlers.node_handler` | 1 | 0 | CasareRPA - Node Error Handler. |
| `casare_rpa.domain.errors.registry` | 1 | 3 | CasareRPA - Error Handler Registry. |
| `casare_rpa.domain.errors.types` | 4 | 0 | CasareRPA - Error Types and Enumerations. |
| `casare_rpa.domain.events` | 4 | 3 | CasareRPA - Domain Event System |
| `casare_rpa.domain.orchestrator.entities.dashboard_metrics` | 2 | 0 | Dashboard metrics value object. |
| `casare_rpa.domain.orchestrator.entities.job` | 3 | 0 | Job domain entity. |
| `casare_rpa.domain.orchestrator.entities.robot` | 3 | 0 | Robot domain entity. |
| `casare_rpa.domain.orchestrator.entities.schedule` | 2 | 0 | Schedule domain entity. |
| `casare_rpa.domain.orchestrator.entities.workflow` | 2 | 0 | Workflow domain entity. |
| `casare_rpa.domain.orchestrator.errors` | 12 | 0 | Domain errors for orchestrator. |
| `casare_rpa.domain.orchestrator.protocols.robot_protocol` | 3 | 0 | Robot Communication Protocol for CasareRPA Orchest... |
| `casare_rpa.domain.orchestrator.repositories.job_repository` | 1 | 0 | Job repository interface. |
| `casare_rpa.domain.orchestrator.repositories.robot_repository` | 1 | 0 | Robot repository interface. |
| `casare_rpa.domain.orchestrator.repositories.schedule_repository` | 1 | 0 | Schedule repository interface. |
| `casare_rpa.domain.orchestrator.repositories.trigger_repository` | 1 | 0 | Trigger repository interface. |
| `casare_rpa.domain.orchestrator.repositories.workflow_repository` | 1 | 0 | Workflow repository interface. |
| `casare_rpa.domain.orchestrator.services.robot_selection_service` | 1 | 0 | RobotSelectionService - Pure domain service for ro... |
| `casare_rpa.domain.orchestrator.value_objects.node_robot_override` | 1 | 0 | NodeRobotOverride value object for node-level robo... |
| `casare_rpa.domain.orchestrator.value_objects.robot_assignment` | 1 | 0 | RobotAssignment value object for workflow-level ro... |
| `casare_rpa.domain.ports.port_type_interfaces` | 5 | 0 | Domain Layer Port Type Interfaces. |
| `casare_rpa.domain.protocols.credential_protocols` | 3 | 0 | Domain Layer Credential Protocols. |
| `casare_rpa.domain.repositories.project_repository` | 1 | 0 | Project repository interface. |
| `casare_rpa.domain.schemas.property_schema` | 2 | 0 | Property schema system for declarative node config... |
| `casare_rpa.domain.schemas.property_types` | 1 | 0 | Property types for node configuration schema. |
| `casare_rpa.domain.services.execution_orchestrator` | 1 | 0 | CasareRPA - Domain Service: Execution Orchestrator |
| `casare_rpa.domain.services.project_context` | 1 | 0 | CasareRPA - Domain Service: Project Context |
| `casare_rpa.domain.services.variable_resolver` | 0 | 4 | Variable Resolution Utility for CasareRPA. |
| `casare_rpa.domain.validation.rules` | 0 | 6 | CasareRPA - Validation Rules Module |
| `casare_rpa.domain.validation.schemas` | 0 | 2 | CasareRPA - Validation Schemas Module |
| `casare_rpa.domain.validation.types` | 3 | 0 | CasareRPA - Validation Types Module |
| `casare_rpa.domain.validation.validators` | 0 | 9 | CasareRPA - Validators Module |
| `casare_rpa.domain.value_objects.log_entry` | 5 | 0 | LogEntry Value Object for Robot Log Streaming. |
| `casare_rpa.domain.value_objects.port` | 1 | 0 | CasareRPA - Port Value Object |
| `casare_rpa.domain.value_objects.types` | 6 | 0 | CasareRPA - Domain Layer Type Definitions |
| `casare_rpa.domain.workflow.templates` | 9 | 0 | CasareRPA - Domain Model: Workflow Templates |
| `casare_rpa.domain.workflow.versioning` | 8 | 0 | CasareRPA - Domain: Workflow Versioning |

## casare_rpa.domain.credentials

**File:** `src\casare_rpa\domain\credentials.py`


CasareRPA - Node Credential System

Provides standardized credential resolution for nodes that require authentication.
Integrates with VaultCredentialProvider for enterprise credential management.

Design:
- CredentialAwareMixin: Mixin for nodes that need credential resolution
- Standard PropertyDef constants for common credential types
- Fallback hierarchy: vault → project binding → direct parameter → environment

Architecture Note:
This module uses domain protocols (ExecutionContextProtocol, CredentialProviderProtocol)
to maintain domain layer purity. The infrastructure layer provides implementations.

Usage:
    from casare_rpa.domain.credentials import (
        CredentialAwareMixin,
        CREDENTIAL_NAME_PROP,
        API_KEY_PROP,
    )

    @node_schema(
        CREDENTIAL_NAME_PROP,
        API_KEY_PROP,
        ...
    )
    @executable_node
    class MyApiNode(CredentialAwareMixin, BaseNode):
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            # Get API key with automatic vault resolution
            api_key = await self.resolve_credential(
                context,
                credential_name_param="credential_name",
                direct_param="api_key",
                env_var="MY_API_KEY",
                credential_field="api_key",
            )


### Functions

#### `resolve_node_credential`

```python
async def resolve_node_credential(context: ExecutionContextProtocol, node: Any, credential_name_param: str = 'credential_name', direct_param: Optional[str] = None, env_var: Optional[str] = None, credential_field: str = 'api_key', required: bool = False) -> Optional[str]
```

Standalone credential resolution function.

For nodes that don't use the mixin pattern.

Args:
    context: ExecutionContext
    node: Node instance (must have get_parameter method)
    credential_name_param: Parameter name for credential alias
    direct_param: Parameter name for direct credential value
    env_var: Environment variable fallback
    credential_field: Field to extract from vault credential
    required: If True, raises error when not found

Returns:
    Credential value or None


### CredentialAwareMixin


Mixin for nodes that require credential resolution.

Provides a standardized way to resolve credentials from multiple sources:
1. Vault (via credential_name parameter)
2. Project bindings (via project context)
3. Direct parameter (e.g., api_key, password)
4. Environment variable
5. Context variable

Architecture Note:
Uses ExecutionContextProtocol to maintain domain purity. The actual
ExecutionContext from infrastructure layer implements this protocol.

IMPORTANT: This mixin requires the mixing class to implement `get_parameter(name, default)`.
BaseNode provides this implementation. The mixin does NOT inherit from HasGetParameter
Protocol to avoid breaking super().__init__() chains in MRO.

Usage:
    class MyNode(CredentialAwareMixin, BaseNode):
        async def execute(self, context):
            api_key = await self.resolve_credential(
                context,
                credential_name_param="credential_name",
                direct_param="api_key",
                env_var="MY_API_KEY",
                credential_field="api_key",
            )


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_parameter(name, default)` | `Any` | Get parameter value by name. |
| `async resolve_credential(context, credential_name_param, direct_param, ...)` | `Optional[str]` | Resolve a credential value from multiple sources. |
| `async resolve_oauth_credentials(context, credential_name_param, client_id_param, ...)` | `tuple[Optional[str], Optional[str]]` | Resolve OAuth client credentials (client_id, client_secret). |
| `async resolve_username_password(context, credential_name_param, username_param, ...)` | `tuple[Optional[str], Optional[str]]` | Resolve username and password credentials. |

#### Method Details

##### `get_parameter`

```python
def get_parameter(name: str, default: Any = None) -> Any
```

Get parameter value by name.

This method must be provided by the class this mixin is mixed with.
BaseNode provides this implementation.

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `resolve_credential`

```python
async def resolve_credential(context: ExecutionContextProtocol, credential_name_param: str = 'credential_name', direct_param: Optional[str] = None, env_var: Optional[str] = None, context_var: Optional[str] = None, credential_field: str = 'api_key', required: bool = False) -> Optional[str]
```

Resolve a credential value from multiple sources.

Resolution order:
1. Vault lookup (if credential_name is set)
2. Direct parameter value
3. Context variable
4. Environment variable

Args:
    context: ExecutionContext with credential provider
    credential_name_param: Parameter name for credential alias
    direct_param: Parameter name for direct credential value
    env_var: Environment variable name fallback
    context_var: Context variable name fallback
    credential_field: Field to extract from vault credential
                     (api_key, password, username, connection_string)
    required: If True, raises error when credential not found

Returns:
    Credential value or None if not found and not required

Raises:
    ValueError: If required=True and credential not found

**Parameters:**

- `context: ExecutionContextProtocol` *(required)*
- `credential_name_param: str = 'credential_name'`
- `direct_param: Optional[str] = None`
- `env_var: Optional[str] = None`
- `context_var: Optional[str] = None`
- `credential_field: str = 'api_key'`
- `required: bool = False`

##### `resolve_oauth_credentials`

```python
async def resolve_oauth_credentials(context: ExecutionContextProtocol, credential_name_param: str = 'credential_name', client_id_param: str = 'client_id', client_secret_param: str = 'client_secret', env_prefix: Optional[str] = None, required: bool = False) -> tuple[Optional[str], Optional[str]]
```

Resolve OAuth client credentials (client_id, client_secret).

Args:
    context: ExecutionContext
    credential_name_param: Parameter for credential alias
    client_id_param: Parameter for direct client ID
    client_secret_param: Parameter for direct client secret
    env_prefix: Environment variable prefix (e.g., "OAUTH" -> OAUTH_CLIENT_ID)
    required: If True, raises error when credentials not found

Returns:
    Tuple of (client_id, client_secret)

**Parameters:**

- `context: ExecutionContextProtocol` *(required)*
- `credential_name_param: str = 'credential_name'`
- `client_id_param: str = 'client_id'`
- `client_secret_param: str = 'client_secret'`
- `env_prefix: Optional[str] = None`
- `required: bool = False`

##### `resolve_username_password`

```python
async def resolve_username_password(context: ExecutionContextProtocol, credential_name_param: str = 'credential_name', username_param: str = 'username', password_param: str = 'password', env_prefix: Optional[str] = None, required: bool = False) -> tuple[Optional[str], Optional[str]]
```

Resolve username and password credentials.

Args:
    context: ExecutionContext
    credential_name_param: Parameter for credential alias
    username_param: Parameter for direct username
    password_param: Parameter for direct password
    env_prefix: Environment variable prefix (e.g., "SMTP" -> SMTP_USERNAME, SMTP_PASSWORD)
    required: If True, raises error when credentials not found

Returns:
    Tuple of (username, password)

**Parameters:**

- `context: ExecutionContextProtocol` *(required)*
- `credential_name_param: str = 'credential_name'`
- `username_param: str = 'username'`
- `password_param: str = 'password'`
- `env_prefix: Optional[str] = None`
- `required: bool = False`

### HasGetParameter

**Inherits from:** `Protocol`


Protocol for objects that have a get_parameter method.

NOTE: This is for type checking only. Do NOT use as a base class for mixins
that need to be combined with other classes (e.g., BaseNode). Protocol
classes have special __init__ behavior that breaks super().__init__() chains.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_parameter(name, default)` | `Any` | Get parameter value by name. |

#### Method Details

##### `get_parameter`

```python
def get_parameter(name: str, default: Any = None) -> Any
```

Get parameter value by name.

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

---

## casare_rpa.domain.decorators

**File:** `src\casare_rpa\domain\decorators.py`


CasareRPA - Node Decorators

Provides decorators for common node patterns:
- @executable_node: Auto-adds exec_in/exec_out ports
- @node_schema: Declarative property schema for nodes


### Functions

#### `executable_node`

```python
def executable_node() -> Type[T]
```

Decorator to automatically add exec_in/exec_out ports to a node class.

This decorator wraps the node's _define_ports method to prepend
the standard execution flow ports before defining node-specific ports.

Usage:
    @executable_node
    class MyNode(BaseNode):
        def _define_ports(self) -> None:
            # Only define data ports here
            self.add_input_port("data", DataType.STRING)
            self.add_output_port("result", DataType.STRING)

The decorator will automatically add:
    - Input port: exec_in (PortType.EXEC_INPUT)
    - Output port: exec_out (PortType.EXEC_OUTPUT)

Args:
    cls: The node class to decorate

Returns:
    The decorated class with modified _define_ports method

#### `node_schema`

```python
def node_schema(*property_defs: PropertyDef)
```

Decorator to attach property schema to node class.

Enables declarative property definitions that automatically:
- Generate default config
- Validate config on initialization
- Enable auto-widget generation in visual nodes

Usage:
    from casare_rpa.domain.schemas import PropertyType, PropertyDef
    from casare_rpa.domain.decorators import node_schema, executable_node

    @node_schema(
        PropertyDef("url", PropertyType.STRING, default="",
                   placeholder="https://example.com"),
        PropertyDef("timeout", PropertyType.INTEGER, default=30000),
        PropertyDef("browser_type", PropertyType.CHOICE, default="chromium",
                   choices=["chromium", "firefox", "webkit"]),
    )
    @executable_node
    class LaunchBrowserNode(BaseNode):
        def __init__(self, node_id: str, name: str = "Launch Browser", **kwargs):
            # Schema decorator automatically merges default_config
            config = kwargs.get("config", {})
            super().__init__(node_id, config)
            self.name = name

Args:
    *property_defs: Variable number of PropertyDef instances
    strict: If True, raise ValueError on validation failure.
            If False (default), log warning and continue (backward compatible).

Returns:
    Decorator function that attaches schema to class


---

## casare_rpa.domain.entities.base_node

**File:** `src\casare_rpa\domain\entities\base_node.py`


CasareRPA - Base Node Abstract Class
All automation nodes must inherit from this base class.


### BaseNode

**Inherits from:** `ABC`


Abstract base class for all automation nodes.

All nodes must implement:
- execute(): Core execution logic
- validate(): Input validation
- _define_ports(): Port definitions


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(node_id, config)` | `None` | Initialize base node. |
| `__repr__()` | `str` | String representation of node. |
| `add_input_port(name, data_type, label, ...)` | `None` | Add an input port to the node. |
| `add_output_port(name, data_type, label, ...)` | `None` | Add an output port to the node. |
| `deserialize(data)` | `'BaseNode'` | Create a node instance from serialized data. |
| `async execute(context)` | `ExecutionResult` | Execute the node's main logic. |
| `get_debug_info()` | `Dict[str, Any]` | Get debug information about this node. |
| `get_input_value(port_name, default)` | `Any` | Get the value of an input port. |
| `get_output_value(port_name, default)` | `Any` | Get the value of an output port. |
| `get_parameter(name, default)` | `Any` | Get parameter value from port (runtime) or config (design-ti... |
| `get_status()` | `NodeStatus` | Get current node status. |
| `has_breakpoint()` | `bool` | Check if this node has a breakpoint set. |
| `reset()` | `None` | Reset node to initial state. |
| `serialize()` | `SerializedNode` | Serialize node to dictionary for saving workflows. |
| `set_breakpoint(enabled)` | `None` | Enable or disable breakpoint on this node. |
| `set_input_value(port_name, value)` | `None` | Set the value of an input port. |
| `set_output_value(port_name, value)` | `None` | Set the value of an output port. |
| `set_status(status, error_message)` | `None` | Update node status. |
| `validate()` | `tuple[bool, Optional[str]]` | Validate node configuration and inputs. |

#### Method Details

##### `__init__`

```python
def __init__(node_id: NodeId, config: Optional[NodeConfig] = None) -> None
```

Initialize base node.

Args:
    node_id: Unique identifier for this node instance
    config: Node configuration dictionary

**Parameters:**

- `node_id: NodeId` *(required)*
- `config: Optional[NodeConfig] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation of node.

##### `add_input_port`

```python
def add_input_port(name: str, data_type: DataType, label: Optional[str] = None, required: bool = True) -> None
```

Add an input port to the node.

**Parameters:**

- `name: str` *(required)*
- `data_type: DataType` *(required)*
- `label: Optional[str] = None`
- `required: bool = True`

##### `add_output_port`

```python
def add_output_port(name: str, data_type: DataType, label: Optional[str] = None, required: bool = False) -> None
```

Add an output port to the node.

**Parameters:**

- `name: str` *(required)*
- `data_type: DataType` *(required)*
- `label: Optional[str] = None`
- `required: bool = False`

##### `deserialize`

```python
@classmethod
def deserialize(data: SerializedNode) -> 'BaseNode'
```

Create a node instance from serialized data.

Args:
    data: Serialized node dictionary

Returns:
    Node instance

**Parameters:**

- `data: SerializedNode` *(required)*

##### `execute`

```python
async def execute(context: Any) -> ExecutionResult
```

Execute the node's main logic.

Args:
    context: Execution context containing runtime state

Returns:
    Dictionary of output port values, or None

Raises:
    Exception: If execution fails

**Parameters:**

- `context: Any` *(required)*

##### `get_debug_info`

```python
def get_debug_info() -> Dict[str, Any]
```

Get debug information about this node.

Returns:
    Dictionary containing debug information

##### `get_input_value`

```python
def get_input_value(port_name: str, default: Any = None) -> Any
```

Get the value of an input port.

**Parameters:**

- `port_name: str` *(required)*
- `default: Any = None`

##### `get_output_value`

```python
def get_output_value(port_name: str, default: Any = None) -> Any
```

Get the value of an output port.

**Parameters:**

- `port_name: str` *(required)*
- `default: Any = None`

##### `get_parameter`

```python
def get_parameter(name: str, default: Any = None) -> Any
```

Get parameter value from port (runtime) or config (design-time).

Unified accessor for the dual-source pattern used by many nodes.
Prefers port value over config value to support runtime overrides.

This is the recommended way to access node parameters that can come
from either port connections OR the properties panel.

Args:
    name: Parameter name (must match both port name and config key)
    default: Default value if parameter not found in either source

Returns:
    Value from port if connected, otherwise from config, otherwise default

Example:
    # Old pattern (fragile):
    file_path = self.config.get("file_path") or self.get_input_value("file_path")

    # New pattern (recommended):
    file_path = self.get_parameter("file_path")

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `get_status`

```python
def get_status() -> NodeStatus
```

Get current node status.

##### `has_breakpoint`

```python
def has_breakpoint() -> bool
```

Check if this node has a breakpoint set.

##### `reset`

```python
def reset() -> None
```

Reset node to initial state.

##### `serialize`

```python
def serialize() -> SerializedNode
```

Serialize node to dictionary for saving workflows.

Returns:
    Dictionary containing node data

##### `set_breakpoint`

```python
def set_breakpoint(enabled: bool = True) -> None
```

Enable or disable breakpoint on this node.

Args:
    enabled: True to enable breakpoint, False to disable

**Parameters:**

- `enabled: bool = True`

##### `set_input_value`

```python
def set_input_value(port_name: str, value: Any) -> None
```

Set the value of an input port.

**Parameters:**

- `port_name: str` *(required)*
- `value: Any` *(required)*

##### `set_output_value`

```python
def set_output_value(port_name: str, value: Any) -> None
```

Set the value of an output port.

**Parameters:**

- `port_name: str` *(required)*
- `value: Any` *(required)*

##### `set_status`

```python
def set_status(status: NodeStatus, error_message: Optional[str] = None) -> None
```

Update node status.

**Parameters:**

- `status: NodeStatus` *(required)*
- `error_message: Optional[str] = None`

##### `validate`

```python
def validate() -> tuple[bool, Optional[str]]
```

Validate node configuration and inputs.

Checks both port values (runtime connections) and config values (design-time properties)
for required parameters. This supports the dual-source pattern used by many nodes where
values can come from either port connections OR the properties panel.

Returns:
    Tuple of (is_valid, error_message)

---

## casare_rpa.domain.entities.execution_state

**File:** `src\casare_rpa\domain\entities\execution_state.py`


CasareRPA - Domain Entity: Execution State
Manages runtime state and variables during workflow execution (pure domain logic).


### ExecutionState


Execution state entity - manages runtime state during workflow execution.

This is a pure domain entity that tracks:
- Variables and their values
- Execution flow (current node, execution path, errors)
- Execution metadata (workflow name, mode, timestamps)

It contains NO infrastructure concerns (no Playwright, no async resources).


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow_name, mode, initial_variables, ...)` | `None` | Initialize execution state. |
| `__repr__()` | `str` | String representation. |
| `add_error(node_id, error_message)` | `None` | Record an error during execution. |
| `clear_variables()` | `None` | Clear all variables. |
| `delete_variable(name)` | `None` | Delete a variable from the context. |
| `get_errors()` | `List[tuple[NodeId, str]]` | Get all recorded errors. |
| `get_execution_path()` | `List[NodeId]` | Get the execution path (list of executed node IDs). |
| `get_execution_summary()` | `Dict[str, Any]` | Get a summary of the execution. |
| `get_variable(name, default)` | `Any` | Get a variable from the context. |
| `has_project_context()` | `bool` | Check if a project context is available. |
| `has_variable(name)` | `bool` | Check if a variable exists. |
| `is_stopped()` | `bool` | Check if execution has been stopped. |
| `mark_completed()` | `None` | Mark the execution as completed. |
| `project_context()` | `Optional['ProjectContext']` | Get the project context (if any). |
| `resolve_credential_path(alias)` | `Optional[str]` | Resolve a credential alias to its Vault path. |
| `resolve_value(value)` | `Any` | Resolve {{variable_name}} patterns in a value. |
| `set_current_node(node_id)` | `None` | Set the currently executing node. |
| `set_variable(name, value)` | `None` | Set a variable in the context. |
| `stop()` | `None` | Signal that execution should stop. |

#### Method Details

##### `__init__`

```python
def __init__(workflow_name: str = 'Untitled', mode: ExecutionMode = ExecutionMode.NORMAL, initial_variables: Optional[Dict[str, Any]] = None, project_context: Optional['ProjectContext'] = None) -> None
```

Initialize execution state.

Args:
    workflow_name: Name of the workflow being executed
    mode: Execution mode (NORMAL, DEBUG, VALIDATE)
    initial_variables: Optional dict of variables to initialize
    project_context: Optional project context for variable scoping

**Parameters:**

- `workflow_name: str = 'Untitled'`
- `mode: ExecutionMode = ExecutionMode.NORMAL`
- `initial_variables: Optional[Dict[str, Any]] = None`
- `project_context: Optional['ProjectContext'] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `add_error`

```python
def add_error(node_id: NodeId, error_message: str) -> None
```

Record an error during execution.

Args:
    node_id: ID of node that encountered the error
    error_message: Error message

**Parameters:**

- `node_id: NodeId` *(required)*
- `error_message: str` *(required)*

##### `clear_variables`

```python
def clear_variables() -> None
```

Clear all variables.

##### `delete_variable`

```python
def delete_variable(name: str) -> None
```

Delete a variable from the context.

Args:
    name: Variable name

**Parameters:**

- `name: str` *(required)*

##### `get_errors`

```python
def get_errors() -> List[tuple[NodeId, str]]
```

Get all recorded errors.

Returns:
    List of (node_id, error_message) tuples

##### `get_execution_path`

```python
def get_execution_path() -> List[NodeId]
```

Get the execution path (list of executed node IDs).

Returns:
    List of node IDs in execution order

##### `get_execution_summary`

```python
def get_execution_summary() -> Dict[str, Any]
```

Get a summary of the execution.

Returns:
    Dictionary with execution statistics

##### `get_variable`

```python
def get_variable(name: str, default: Any = None) -> Any
```

Get a variable from the context.

Args:
    name: Variable name
    default: Default value if variable not found

Returns:
    Variable value or default

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `has_project_context`

```python
@property
def has_project_context() -> bool
```

Check if a project context is available.

##### `has_variable`

```python
def has_variable(name: str) -> bool
```

Check if a variable exists.

Args:
    name: Variable name

Returns:
    True if variable exists, False otherwise

**Parameters:**

- `name: str` *(required)*

##### `is_stopped`

```python
def is_stopped() -> bool
```

Check if execution has been stopped.

Returns:
    True if execution is stopped, False otherwise

##### `mark_completed`

```python
def mark_completed() -> None
```

Mark the execution as completed.

##### `project_context`

```python
@property
def project_context() -> Optional['ProjectContext']
```

Get the project context (if any).

##### `resolve_credential_path`

```python
def resolve_credential_path(alias: str) -> Optional[str]
```

Resolve a credential alias to its Vault path.

Uses the project context's credential binding resolution.

Args:
    alias: Credential alias to resolve

Returns:
    Vault path if found, None otherwise

**Parameters:**

- `alias: str` *(required)*

##### `resolve_value`

```python
def resolve_value(value: Any) -> Any
```

Resolve {{variable_name}} patterns in a value.

This enables UiPath/Power Automate style variable substitution
where users can reference global variables in node properties
using the {{variable_name}} syntax.

Args:
    value: The value to resolve (only strings are processed)

Returns:
    The resolved value with all {{variable}} patterns replaced.
    Non-string values are returned unchanged.

Examples:
    >>> state.set_variable("website", "google.com")
    >>> state.resolve_value("https://{{website}}")
    "https://google.com"

**Parameters:**

- `value: Any` *(required)*

##### `set_current_node`

```python
def set_current_node(node_id: NodeId) -> None
```

Set the currently executing node.

Args:
    node_id: ID of node being executed

**Parameters:**

- `node_id: NodeId` *(required)*

##### `set_variable`

```python
def set_variable(name: str, value: Any) -> None
```

Set a variable in the context.

Args:
    name: Variable name
    value: Variable value

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*

##### `stop`

```python
def stop() -> None
```

Signal that execution should stop.

---

## casare_rpa.domain.entities.node_connection

**File:** `src\casare_rpa\domain\entities\node_connection.py`


CasareRPA - Domain Entity: Node Connection
Represents a connection between two node ports in a workflow.


### NodeConnection


Represents a connection between two node ports.

A connection links the output of one node to the input of another,
defining the flow of data or execution control in a workflow.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__eq__(other)` | `bool` | Check equality based on connection endpoints. |
| `__hash__()` | `int` | Hash based on connection endpoints. |
| `__init__(source_node, source_port, target_node, ...)` | `None` | Initialize a connection. |
| `__repr__()` | `str` | String representation. |
| `from_dict(data)` | `'NodeConnection'` | Create connection from dictionary. |
| `source_id()` | `PortId` | Get full source port ID (node_id.port_name). |
| `source_node()` | `NodeId` | Get the source node ID. |
| `source_port()` | `str` | Get the source port name. |
| `target_id()` | `PortId` | Get full target port ID (node_id.port_name). |
| `target_node()` | `NodeId` | Get the target node ID. |
| `target_port()` | `str` | Get the target port name. |
| `to_dict()` | `Dict[str, str]` | Serialize connection to dictionary. |

#### Method Details

##### `__eq__`

```python
def __eq__(other: object) -> bool
```

Check equality based on connection endpoints.

**Parameters:**

- `other: object` *(required)*

##### `__hash__`

```python
def __hash__() -> int
```

Hash based on connection endpoints.

##### `__init__`

```python
def __init__(source_node: NodeId, source_port: str, target_node: NodeId, target_port: str) -> None
```

Initialize a connection.

Args:
    source_node: ID of source node
    source_port: Name of source port
    target_node: ID of target node
    target_port: Name of target port

**Parameters:**

- `source_node: NodeId` *(required)*
- `source_port: str` *(required)*
- `target_node: NodeId` *(required)*
- `target_port: str` *(required)*

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, str]) -> 'NodeConnection'
```

Create connection from dictionary.

Args:
    data: Dictionary containing connection data

Returns:
    NodeConnection instance

**Parameters:**

- `data: Dict[str, str]` *(required)*

##### `source_id`

```python
@property
def source_id() -> PortId
```

Get full source port ID (node_id.port_name).

##### `source_node`

```python
@property
def source_node() -> NodeId
```

Get the source node ID.

##### `source_port`

```python
@property
def source_port() -> str
```

Get the source port name.

##### `target_id`

```python
@property
def target_id() -> PortId
```

Get full target port ID (node_id.port_name).

##### `target_node`

```python
@property
def target_node() -> NodeId
```

Get the target node ID.

##### `target_port`

```python
@property
def target_port() -> str
```

Get the target port name.

##### `to_dict`

```python
def to_dict() -> Dict[str, str]
```

Serialize connection to dictionary.

Returns:
    Dictionary with connection data

---

## casare_rpa.domain.entities.project.base

**File:** `src\casare_rpa\domain\entities\project\base.py`


CasareRPA - Project Base Constants and Utilities

Constants and ID generators for project entities.


### Functions

#### `generate_project_id`

```python
def generate_project_id() -> str
```

Generate unique project ID.

#### `generate_scenario_id`

```python
def generate_scenario_id() -> str
```

Generate unique scenario ID.


---

## casare_rpa.domain.entities.project.credentials

**File:** `src\casare_rpa\domain\entities\project\credentials.py`


CasareRPA - Credential Bindings

Credential binding classes for project security management.


### CredentialBinding

**Decorators:** `@dataclass`


Maps a local alias to a Vault credential path.

Domain entity for credential reference management.

Attributes:
    alias: Local name used in workflows (e.g., "erp_login")
    vault_path: Path in HashiCorp Vault (e.g., "projects/proj_123/erp_creds")
    credential_type: Type of credential (username_password, api_key, etc.)
    description: Description of what this credential is for
    required: If True, workflow execution fails if credential is missing


**Attributes:**

- `alias: str`
- `credential_type: str`
- `description: str`
- `required: bool`
- `vault_path: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'CredentialBinding'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'CredentialBinding'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### CredentialBindingsFile

**Decorators:** `@dataclass`


Container for credential bindings in credentials.json files.


**Attributes:**

- `bindings: Dict[str, CredentialBinding]`
- `schema_version: str`
- `scope: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'CredentialBindingsFile'` | Create from dictionary. |
| `get_binding(alias)` | `Optional[CredentialBinding]` | Get binding by alias. |
| `remove_binding(alias)` | `bool` | Remove a binding. Returns True if removed. |
| `resolve_vault_path(alias)` | `Optional[str]` | Get the Vault path for an alias. |
| `set_binding(binding)` | `None` | Add or update a binding. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'CredentialBindingsFile'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_binding`

```python
def get_binding(alias: str) -> Optional[CredentialBinding]
```

Get binding by alias.

**Parameters:**

- `alias: str` *(required)*

##### `remove_binding`

```python
def remove_binding(alias: str) -> bool
```

Remove a binding. Returns True if removed.

**Parameters:**

- `alias: str` *(required)*

##### `resolve_vault_path`

```python
def resolve_vault_path(alias: str) -> Optional[str]
```

Get the Vault path for an alias.

**Parameters:**

- `alias: str` *(required)*

##### `set_binding`

```python
def set_binding(binding: CredentialBinding) -> None
```

Add or update a binding.

**Parameters:**

- `binding: CredentialBinding` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

---

## casare_rpa.domain.entities.project.index

**File:** `src\casare_rpa\domain\entities\project\index.py`


CasareRPA - Project Index

Project index classes for project registry management.


### ProjectIndexEntry

**Decorators:** `@dataclass`


Entry in the projects index for quick project lookup.

Domain value object for project registry tracking.


**Attributes:**

- `id: str`
- `last_opened: Optional[datetime]`
- `name: str`
- `path: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'ProjectIndexEntry'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'ProjectIndexEntry'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### ProjectsIndex

**Decorators:** `@dataclass`


Index of all known projects for the application.

Domain entity managing the project registry.
Stored in CONFIG_DIR/projects_index.json


**Attributes:**

- `projects: List[ProjectIndexEntry]`
- `recent_limit: int`
- `schema_version: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `add_project(project)` | `None` | Add or update a project in the index. |
| `from_dict(data)` | `'ProjectsIndex'` | Create from dictionary. |
| `get_project(project_id)` | `Optional[ProjectIndexEntry]` | Get a project entry by ID. |
| `get_recent_projects(limit)` | `List[ProjectIndexEntry]` | Get recently opened projects. |
| `remove_project(project_id)` | `bool` | Remove a project from the index. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |
| `update_last_opened(project_id)` | `None` | Update the last_opened timestamp for a project. |

#### Method Details

##### `add_project`

```python
def add_project(project: Project) -> None
```

Add or update a project in the index.

Args:
    project: Project to add

**Parameters:**

- `project: Project` *(required)*

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'ProjectsIndex'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_project`

```python
def get_project(project_id: str) -> Optional[ProjectIndexEntry]
```

Get a project entry by ID.

Args:
    project_id: Project ID to find

Returns:
    ProjectIndexEntry if found, None otherwise

**Parameters:**

- `project_id: str` *(required)*

##### `get_recent_projects`

```python
def get_recent_projects(limit: Optional[int] = None) -> List[ProjectIndexEntry]
```

Get recently opened projects.

Args:
    limit: Max number of projects to return

Returns:
    List of recent project entries

**Parameters:**

- `limit: Optional[int] = None`

##### `remove_project`

```python
def remove_project(project_id: str) -> bool
```

Remove a project from the index.

Args:
    project_id: ID of project to remove

Returns:
    True if project was removed

**Parameters:**

- `project_id: str` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

##### `update_last_opened`

```python
def update_last_opened(project_id: str) -> None
```

Update the last_opened timestamp for a project.

Args:
    project_id: ID of project to update

**Parameters:**

- `project_id: str` *(required)*

---

## casare_rpa.domain.entities.project.project

**File:** `src\casare_rpa\domain\entities\project\project.py`


CasareRPA - Project Entity

Main Project domain entity.


### Project

**Decorators:** `@dataclass`


Domain entity representing a CasareRPA project.

A project is a folder containing workflows, scenarios, variables,
and credential bindings organized for a specific automation goal.

Attributes:
    id: Unique project identifier (proj_uuid8)
    name: Human-readable project name
    description: Project description
    author: Project creator
    created_at: Creation timestamp
    modified_at: Last modification timestamp
    tags: List of tags for categorization
    settings: Project-level execution settings


**Attributes:**

- `_path: Optional[Path]`
- `author: str`
- `created_at: Optional[datetime]`
- `description: str`
- `id: str`
- `modified_at: Optional[datetime]`
- `name: str`
- `schema_version: str`
- `settings: ProjectSettings`
- `tags: List[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Initialize timestamps if not provided. |
| `__repr__()` | `str` | String representation. |
| `create_new(name, path, **kwargs)` | `'Project'` | Factory method to create a new project. |
| `credentials_file()` | `Optional[Path]` | Get credentials.json file path. |
| `from_dict(data)` | `'Project'` | Create from dictionary. |
| `path()` | `Optional[Path]` | Get project folder path. |
| `path(value)` | `None` | Set project folder path. |
| `project_file()` | `Optional[Path]` | Get project.json file path. |
| `scenarios_dir()` | `Optional[Path]` | Get scenarios directory path. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary for project.json. |
| `touch_modified()` | `None` | Update modified timestamp to current time. |
| `variables_file()` | `Optional[Path]` | Get variables.json file path. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Initialize timestamps if not provided.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `create_new`

```python
@classmethod
def create_new(name: str, path: Path, **kwargs: Any) -> 'Project'
```

Factory method to create a new project.

Args:
    name: Project name
    path: Path where project will be stored
    **kwargs: Additional project attributes

Returns:
    New Project instance with generated ID

**Parameters:**

- `name: str` *(required)*
- `path: Path` *(required)*
- `**kwargs: Any`

##### `credentials_file`

```python
@property
def credentials_file() -> Optional[Path]
```

Get credentials.json file path.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Project'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `path`

```python
@property
def path() -> Optional[Path]
```

Get project folder path.

##### `path`

```python
@property
def path(value: Path) -> None
```

Set project folder path.

**Parameters:**

- `value: Path` *(required)*

##### `project_file`

```python
@property
def project_file() -> Optional[Path]
```

Get project.json file path.

##### `scenarios_dir`

```python
@property
def scenarios_dir() -> Optional[Path]
```

Get scenarios directory path.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary for project.json.

##### `touch_modified`

```python
def touch_modified() -> None
```

Update modified timestamp to current time.

##### `variables_file`

```python
@property
def variables_file() -> Optional[Path]
```

Get variables.json file path.

---

## casare_rpa.domain.entities.project.scenario

**File:** `src\casare_rpa\domain\entities\project\scenario.py`


CasareRPA - Scenario Entity

Scenario domain entity - a workflow + data bundle.


### Scenario

**Decorators:** `@dataclass`


Domain entity representing a scenario: a workflow + data bundle.

Scenarios embed the full workflow JSON and include specific
variable values and credential bindings for execution.

Attributes:
    id: Unique scenario identifier (scen_uuid8)
    name: Human-readable scenario name
    project_id: Parent project ID
    description: Scenario description
    workflow: Embedded workflow (full WorkflowSchema dict)
    variable_values: Variable values for this scenario
    credential_bindings: Credential alias -> binding alias mappings
    execution_settings: Execution overrides


**Attributes:**

- `_file_path: Optional[Path]`
- `created_at: Optional[datetime]`
- `credential_bindings: Dict[str, str]`
- `description: str`
- `execution_settings: ScenarioExecutionSettings`
- `id: str`
- `modified_at: Optional[datetime]`
- `name: str`
- `project_id: str`
- `schema_version: str`
- `tags: List[str]`
- `triggers: List[Dict[str, Any]]`
- `variable_values: Dict[str, Any]`
- `workflow: Dict[str, Any]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Initialize timestamps and validate required fields. |
| `__repr__()` | `str` | String representation. |
| `create_new(name, project_id, workflow, ...)` | `'Scenario'` | Factory method to create a new scenario. |
| `file_path()` | `Optional[Path]` | Get scenario file path. |
| `file_path(value)` | `None` | Set scenario file path. |
| `from_dict(data)` | `'Scenario'` | Create from dictionary. |
| `get_variable_value(name, default)` | `Any` | Get a variable value, with optional default. |
| `set_variable_value(name, value)` | `None` | Set a variable value. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary for scenario JSON file. |
| `touch_modified()` | `None` | Update modified timestamp to current time. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Initialize timestamps and validate required fields.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `create_new`

```python
@classmethod
def create_new(name: str, project_id: str, workflow: Optional[Dict[str, Any]] = None, **kwargs: Any) -> 'Scenario'
```

Factory method to create a new scenario.

Args:
    name: Scenario name
    project_id: Parent project ID
    workflow: Optional workflow definition
    **kwargs: Additional scenario attributes

Returns:
    New Scenario instance with generated ID

**Parameters:**

- `name: str` *(required)*
- `project_id: str` *(required)*
- `workflow: Optional[Dict[str, Any]] = None`
- `**kwargs: Any`

##### `file_path`

```python
@property
def file_path() -> Optional[Path]
```

Get scenario file path.

##### `file_path`

```python
@property
def file_path(value: Path) -> None
```

Set scenario file path.

**Parameters:**

- `value: Path` *(required)*

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Scenario'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_variable_value`

```python
def get_variable_value(name: str, default: Any = None) -> Any
```

Get a variable value, with optional default.

Args:
    name: Variable name
    default: Default value if not found

Returns:
    Variable value or default

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `set_variable_value`

```python
def set_variable_value(name: str, value: Any) -> None
```

Set a variable value.

Args:
    name: Variable name
    value: Value to set

**Parameters:**

- `name: str` *(required)*
- `value: Any` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary for scenario JSON file.

##### `touch_modified`

```python
def touch_modified() -> None
```

Update modified timestamp to current time.

---

## casare_rpa.domain.entities.project.settings

**File:** `src\casare_rpa\domain\entities\project\settings.py`


CasareRPA - Project Settings

Project and scenario execution settings.


### ProjectSettings

**Decorators:** `@dataclass`


Project-level execution and behavior settings.

Domain value object for project configuration.


**Attributes:**

- `default_browser: str`
- `retry_count: int`
- `stop_on_error: bool`
- `timeout_seconds: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'ProjectSettings'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'ProjectSettings'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### ScenarioExecutionSettings

**Decorators:** `@dataclass`


Execution-time overrides for a scenario.

Domain value object for scenario execution configuration.


**Attributes:**

- `environment_override: Optional[str]`
- `priority: str`
- `timeout_override: Optional[int]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'ScenarioExecutionSettings'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'ScenarioExecutionSettings'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

---

## casare_rpa.domain.entities.project.variables

**File:** `src\casare_rpa\domain\entities\project\variables.py`


CasareRPA - Project Variables

Variable-related classes for project scope.
Uses the unified Variable class from domain.entities.variable.


### VariableScope

**Inherits from:** `Enum`


Scope for variable storage.


**Attributes:**

- `GLOBAL: str`
- `PROJECT: str`
- `SCENARIO: str`

### VariableType

**Inherits from:** `Enum`


Supported variable data types.


**Attributes:**

- `BOOLEAN: str`
- `DATATABLE: str`
- `DICT: str`
- `FLOAT: str`
- `INTEGER: str`
- `LIST: str`
- `STRING: str`

### VariablesFile

**Decorators:** `@dataclass`


Container for variables stored in variables.json files.
Used for both project and global variable storage.


**Attributes:**

- `schema_version: str`
- `scope: VariableScope`
- `variables: Dict[str, Variable]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'VariablesFile'` | Create from dictionary. |
| `get_default_values()` | `Dict[str, Any]` | Get dictionary of variable names to their default values. |
| `get_variable(name)` | `Optional[Variable]` | Get variable by name. |
| `remove_variable(name)` | `bool` | Remove a variable. Returns True if removed. |
| `set_variable(variable)` | `None` | Add or update a variable. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'VariablesFile'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_default_values`

```python
def get_default_values() -> Dict[str, Any]
```

Get dictionary of variable names to their default values.

##### `get_variable`

```python
def get_variable(name: str) -> Optional[Variable]
```

Get variable by name.

**Parameters:**

- `name: str` *(required)*

##### `remove_variable`

```python
def remove_variable(name: str) -> bool
```

Remove a variable. Returns True if removed.

**Parameters:**

- `name: str` *(required)*

##### `set_variable`

```python
def set_variable(variable: Variable) -> None
```

Add or update a variable.

**Parameters:**

- `variable: Variable` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

---

## casare_rpa.domain.entities.tenant

**File:** `src\casare_rpa\domain\entities\tenant.py`


Tenant domain entity.

Represents a tenant in a multi-tenant CasareRPA deployment.
Tenants have isolated robot fleets, workflows, and API keys.


### Tenant

**Decorators:** `@dataclass`


Tenant domain entity.

Represents an organization or client in a multi-tenant deployment.
Each tenant has isolated robots, workflows, and API keys.


**Attributes:**

- `admin_emails: List[str]`
- `contact_email: Optional[str]`
- `created_at: Optional[datetime]`
- `description: str`
- `id: TenantId`
- `is_active: bool`
- `name: str`
- `robot_ids: Set[str]`
- `settings: TenantSettings`
- `updated_at: Optional[datetime]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Validate domain invariants. |
| `__repr__()` | `str` |  |
| `activate()` | `None` | Activate the tenant. |
| `add_admin(email)` | `None` | Add an admin email to the tenant. |
| `add_robot(robot_id)` | `None` | Add a robot to this tenant. |
| `can_add_robot()` | `bool` | Check if tenant can add more robots. |
| `deactivate()` | `None` | Deactivate the tenant (soft delete). |
| `from_dict(data)` | `'Tenant'` | Create Tenant from dictionary. |
| `has_robot(robot_id)` | `bool` | Check if robot belongs to this tenant. |
| `is_admin(email)` | `bool` | Check if email is an admin of this tenant. |
| `remove_admin(email)` | `None` | Remove an admin email from the tenant. |
| `remove_robot(robot_id)` | `None` | Remove a robot from this tenant. |
| `robot_count()` | `int` | Get count of robots in this tenant. |
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary. |
| `update_settings(settings)` | `None` | Update tenant settings. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Validate domain invariants.

##### `__repr__`

```python
def __repr__() -> str
```

##### `activate`

```python
def activate() -> None
```

Activate the tenant.

##### `add_admin`

```python
def add_admin(email: str) -> None
```

Add an admin email to the tenant.

**Parameters:**

- `email: str` *(required)*

##### `add_robot`

```python
def add_robot(robot_id: str) -> None
```

Add a robot to this tenant.

Args:
    robot_id: ID of robot to add.

Raises:
    ValueError: If tenant is at robot capacity.

**Parameters:**

- `robot_id: str` *(required)*

##### `can_add_robot`

```python
@property
def can_add_robot() -> bool
```

Check if tenant can add more robots.

##### `deactivate`

```python
def deactivate() -> None
```

Deactivate the tenant (soft delete).

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Tenant'
```

Create Tenant from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `has_robot`

```python
def has_robot(robot_id: str) -> bool
```

Check if robot belongs to this tenant.

**Parameters:**

- `robot_id: str` *(required)*

##### `is_admin`

```python
def is_admin(email: str) -> bool
```

Check if email is an admin of this tenant.

**Parameters:**

- `email: str` *(required)*

##### `remove_admin`

```python
def remove_admin(email: str) -> None
```

Remove an admin email from the tenant.

**Parameters:**

- `email: str` *(required)*

##### `remove_robot`

```python
def remove_robot(robot_id: str) -> None
```

Remove a robot from this tenant.

Args:
    robot_id: ID of robot to remove.

**Parameters:**

- `robot_id: str` *(required)*

##### `robot_count`

```python
@property
def robot_count() -> int
```

Get count of robots in this tenant.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to dictionary.

##### `update_settings`

```python
def update_settings(settings: TenantSettings) -> None
```

Update tenant settings.

**Parameters:**

- `settings: TenantSettings` *(required)*

### TenantId

**Decorators:** `@dataclass`


Value Object: Tenant identifier.


**Attributes:**

- `value: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` |  |
| `__str__()` | `str` |  |
| `generate()` | `'TenantId'` | Generate a new unique TenantId. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

##### `__str__`

```python
def __str__() -> str
```

##### `generate`

```python
@classmethod
def generate() -> 'TenantId'
```

Generate a new unique TenantId.

### TenantSettings

**Decorators:** `@dataclass`


Settings for a tenant.


**Attributes:**

- `allowed_capabilities: List[str]`
- `custom_settings: Dict[str, Any]`
- `enable_audit_logging: bool`
- `job_retention_days: int`
- `max_api_keys_per_robot: int`
- `max_concurrent_jobs: int`
- `max_robots: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` |  |
| `from_dict(data)` | `'TenantSettings'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TenantSettings'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to dictionary.

---

## casare_rpa.domain.entities.variable

**File:** `src\casare_rpa\domain\entities\variable.py`


CasareRPA - Domain Entity: Variable

Unified variable definition for workflows and projects.
Consolidates VariableDefinition and ProjectVariable into a single class.


### Variable

**Decorators:** `@dataclass`


Unified variable definition for workflows, projects, and global scope.

This class represents a typed variable with metadata, usable across:
- Workflow variables
- Project variables
- Global variables

Attributes:
    name: Variable name (must be valid Python identifier)
    type: Variable type (String, Integer, Float, Boolean, List, Dict, DataTable)
    default_value: Default value for the variable
    description: Optional description of the variable's purpose
    sensitive: If True, value should be masked in UI (for passwords, etc.)
    readonly: If True, cannot be modified at runtime


**Attributes:**

- `default_value: Any`
- `description: str`
- `name: str`
- `readonly: bool`
- `sensitive: bool`
- `type: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Validate variable attributes after initialization. |
| `from_dict(data)` | `'Variable'` | Create from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Validate variable attributes after initialization.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Variable'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

---

## casare_rpa.domain.entities.workflow

**File:** `src\casare_rpa\domain\entities\workflow.py`


CasareRPA - Domain Entity: Workflow
Workflow aggregate root - manages nodes, connections, and workflow metadata.


### WorkflowSchema


Workflow aggregate root - manages nodes, connections, and workflow metadata.

Represents a complete workflow with nodes and connections.
Handles serialization and deserialization.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(metadata)` | `None` | Initialize workflow schema. |
| `__repr__()` | `str` | String representation. |
| `add_connection(connection)` | `None` | Add a connection between nodes. |
| `add_node(node_data)` | `None` | Add a node to the workflow. |
| `from_dict(data)` | `'WorkflowSchema'` | Create workflow from dictionary. |
| `get_connections_from(node_id)` | `List[NodeConnection]` | Get all connections originating from a node. |
| `get_connections_to(node_id)` | `List[NodeConnection]` | Get all connections targeting a node. |
| `get_node(node_id)` | `Optional[SerializedNode]` | Get a node by ID. |
| `remove_connection(source_node, source_port, target_node, ...)` | `None` | Remove a connection between nodes. |
| `remove_node(node_id)` | `None` | Remove a node and its connections from the workflow. |
| `to_dict()` | `SerializedWorkflow` | Serialize workflow to dictionary. |
| `validate()` | `tuple[bool, List[str]]` | Validate the workflow structure (simple interface). |
| `validate_full()` | `'ValidationResult'` | Perform comprehensive validation and return detailed result. |

#### Method Details

##### `__init__`

```python
def __init__(metadata: Optional[WorkflowMetadata] = None) -> None
```

Initialize workflow schema.

Args:
    metadata: Workflow metadata (creates default if None)

**Parameters:**

- `metadata: Optional[WorkflowMetadata] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `add_connection`

```python
def add_connection(connection: NodeConnection) -> None
```

Add a connection between nodes.

Args:
    connection: NodeConnection to add

Raises:
    ValueError: If source or target node doesn't exist

**Parameters:**

- `connection: NodeConnection` *(required)*

##### `add_node`

```python
def add_node(node_data: SerializedNode) -> None
```

Add a node to the workflow.

Ensures consistency between node_id field and dict key
to prevent NODE_ID_MISMATCH errors.

Args:
    node_data: Serialized node data

**Parameters:**

- `node_data: SerializedNode` *(required)*

##### `from_dict`

```python
@classmethod
def from_dict(data: SerializedWorkflow) -> 'WorkflowSchema'
```

Create workflow from dictionary.

Args:
    data: Serialized workflow data

Returns:
    WorkflowSchema instance

**Parameters:**

- `data: SerializedWorkflow` *(required)*

##### `get_connections_from`

```python
def get_connections_from(node_id: NodeId) -> List[NodeConnection]
```

Get all connections originating from a node.

Args:
    node_id: Source node ID

Returns:
    List of connections from this node

**Parameters:**

- `node_id: NodeId` *(required)*

##### `get_connections_to`

```python
def get_connections_to(node_id: NodeId) -> List[NodeConnection]
```

Get all connections targeting a node.

Args:
    node_id: Target node ID

Returns:
    List of connections to this node

**Parameters:**

- `node_id: NodeId` *(required)*

##### `get_node`

```python
def get_node(node_id: NodeId) -> Optional[SerializedNode]
```

Get a node by ID.

Args:
    node_id: Node ID to look up

Returns:
    Serialized node data or None if not found

**Parameters:**

- `node_id: NodeId` *(required)*

##### `remove_connection`

```python
def remove_connection(source_node: NodeId, source_port: str, target_node: NodeId, target_port: str) -> None
```

Remove a connection between nodes.

Args:
    source_node: Source node ID
    source_port: Source port name
    target_node: Target node ID
    target_port: Target port name

**Parameters:**

- `source_node: NodeId` *(required)*
- `source_port: str` *(required)*
- `target_node: NodeId` *(required)*
- `target_port: str` *(required)*

##### `remove_node`

```python
def remove_node(node_id: NodeId) -> None
```

Remove a node and its connections from the workflow.

Args:
    node_id: ID of node to remove

**Parameters:**

- `node_id: NodeId` *(required)*

##### `to_dict`

```python
def to_dict() -> SerializedWorkflow
```

Serialize workflow to dictionary.

Returns:
    Complete workflow data structure

##### `validate`

```python
def validate() -> tuple[bool, List[str]]
```

Validate the workflow structure (simple interface).

Returns:
    Tuple of (is_valid, list of error messages)

##### `validate_full`

```python
def validate_full() -> 'ValidationResult'
```

Perform comprehensive validation and return detailed result.

Returns:
    ValidationResult with all issues and suggestions

---

## casare_rpa.domain.entities.workflow_metadata

**File:** `src\casare_rpa\domain\entities\workflow_metadata.py`


CasareRPA - Domain Entity: Workflow Metadata
Represents workflow identity and versioning information.


### WorkflowMetadata


Workflow metadata entity - represents workflow identity and versioning.

This entity contains descriptive information about a workflow including
its name, author, version, and timestamps. It is part of the WorkflowSchema
aggregate root.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(name, description, author, ...)` | `None` | Initialize workflow metadata. |
| `__repr__()` | `str` | String representation. |
| `from_dict(data)` | `'WorkflowMetadata'` | Create metadata from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize metadata to dictionary. |
| `update_modified_timestamp()` | `None` | Update the modified timestamp to current time. |

#### Method Details

##### `__init__`

```python
def __init__(name: str, description: str = '', author: str = '', version: str = '1.0.0', tags: Optional[List[str]] = None) -> None
```

Initialize workflow metadata.

Args:
    name: Workflow name (required, non-empty)
    description: Workflow description
    author: Workflow creator
    version: Workflow version
    tags: List of tags for categorization

Raises:
    ValueError: If name is empty or whitespace-only

**Parameters:**

- `name: str` *(required)*
- `description: str = ''`
- `author: str = ''`
- `version: str = '1.0.0'`
- `tags: Optional[List[str]] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'WorkflowMetadata'
```

Create metadata from dictionary.

Args:
    data: Dictionary containing metadata fields

Returns:
    WorkflowMetadata instance

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize metadata to dictionary.

Returns:
    Dictionary representation of metadata

##### `update_modified_timestamp`

```python
def update_modified_timestamp() -> None
```

Update the modified timestamp to current time.

---

## casare_rpa.domain.entities.workflow_schedule

**File:** `src\casare_rpa\domain\entities\workflow_schedule.py`


WorkflowSchedule domain entity.

Represents a schedule for executing a workflow at specified times.
Pure domain logic - no UI or infrastructure dependencies.


### ScheduleFrequency

**Inherits from:** `str`, `Enum`


Schedule frequency types.


**Attributes:**

- `CRON: str`
- `DAILY: str`
- `HOURLY: str`
- `MONTHLY: str`
- `ONCE: str`
- `WEEKLY: str`

### WorkflowSchedule

**Decorators:** `@dataclass`


Workflow schedule entity.

Represents a schedule configuration for running a workflow
at specified times (once, hourly, daily, weekly, monthly, or cron).


**Attributes:**

- `created_at: Optional[datetime]`
- `cron_expression: str`
- `day_of_month: int`
- `day_of_week: int`
- `enabled: bool`
- `failure_count: int`
- `frequency: str`
- `id: str`
- `last_error: str`
- `last_run: Optional[datetime]`
- `name: str`
- `next_run: Optional[datetime]`
- `run_count: int`
- `success_count: int`
- `time_hour: int`
- `time_minute: int`
- `timezone: str`
- `workflow_name: str`
- `workflow_path: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_next_run(from_time)` | `Optional[datetime]` | Calculate the next run time based on frequency. |
| `frequency_display()` | `str` | Get human-readable frequency string. |
| `from_dict(data)` | `'WorkflowSchedule'` | Create from dictionary. |
| `success_rate()` | `float` | Calculate success rate percentage. |
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary for JSON serialization. |

#### Method Details

##### `calculate_next_run`

```python
def calculate_next_run(from_time: Optional[datetime] = None) -> Optional[datetime]
```

Calculate the next run time based on frequency.

**Parameters:**

- `from_time: Optional[datetime] = None`

##### `frequency_display`

```python
@property
def frequency_display() -> str
```

Get human-readable frequency string.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'WorkflowSchedule'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `success_rate`

```python
@property
def success_rate() -> float
```

Calculate success rate percentage.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to dictionary for JSON serialization.

---

## casare_rpa.domain.errors.context

**File:** `src\casare_rpa\domain\errors\context.py`


CasareRPA - Error Context and Recovery Decision.

Data classes for capturing error context and recovery decisions.


### ErrorContext

**Decorators:** `@dataclass`


Captures full context of an error occurrence.

Used for:
- Error analysis and classification
- Recovery decision making
- Logging and reporting
- Screenshot capture triggers (UI errors)


**Attributes:**

- `additional_data: Dict[str, Any]`
- `category: ErrorCategory`
- `classification: ErrorClassification`
- `error_code: Optional[ErrorCode]`
- `exception: Exception`
- `execution_time_ms: float`
- `max_retries: int`
- `message: str`
- `node_config: Dict[str, Any]`
- `node_id: NodeId`
- `node_type: str`
- `retry_count: int`
- `screenshot_path: Optional[str]`
- `severity: ErrorSeverity`
- `stack_trace: str`
- `timestamp: datetime`
- `variables: Dict[str, Any]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Post-initialization to set derived fields. |
| `is_retryable()` | `bool` | Check if error is potentially retryable. |
| `is_ui_error()` | `bool` | Check if this is a UI-related error (screenshot useful). |
| `to_dict()` | `Dict[str, Any]` | Serialize error context to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Post-initialization to set derived fields.

##### `is_retryable`

```python
@property
def is_retryable() -> bool
```

Check if error is potentially retryable.

##### `is_ui_error`

```python
@property
def is_ui_error() -> bool
```

Check if this is a UI-related error (screenshot useful).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize error context to dictionary.

Returns:
    Dictionary representation for logging/storage.

### RecoveryDecision

**Decorators:** `@dataclass`


Decision from error handler on how to recover.

Contains the recommended action and parameters for recovery.


**Attributes:**

- `action: RecoveryAction`
- `compensate_nodes: List[NodeId]`
- `continue_from_node: Optional[NodeId]`
- `escalation_message: str`
- `fallback_value: Any`
- `metadata: Dict[str, Any]`
- `reason: str`
- `retry_delay_ms: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__repr__()` | `str` | String representation. |

#### Method Details

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

---

## casare_rpa.domain.errors.handlers.base

**File:** `src\casare_rpa\domain\errors\handlers\base.py`


CasareRPA - Base Error Handler.

Abstract base class for error handlers.


### ErrorHandler

**Inherits from:** `ABC`


Abstract base class for error handlers.

Error handlers analyze errors and recommend recovery actions.
Subclasses implement domain-specific error handling logic.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `can_handle(context)` | `bool` | Check if this handler can handle the given error. |
| `classify(context)` | `ErrorContext` | Classify the error (set classification, category, severity). |
| `decide_recovery(context)` | `RecoveryDecision` | Decide recovery action for the error. |

#### Method Details

##### `can_handle`

```python
def can_handle(context: ErrorContext) -> bool
```

Check if this handler can handle the given error.

Args:
    context: Error context to evaluate.

Returns:
    True if this handler should process the error.

**Parameters:**

- `context: ErrorContext` *(required)*

##### `classify`

```python
def classify(context: ErrorContext) -> ErrorContext
```

Classify the error (set classification, category, severity).

Args:
    context: Error context to classify.

Returns:
    Updated error context with classification.

**Parameters:**

- `context: ErrorContext` *(required)*

##### `decide_recovery`

```python
def decide_recovery(context: ErrorContext) -> RecoveryDecision
```

Decide recovery action for the error.

Args:
    context: Classified error context.

Returns:
    Recovery decision with recommended action.

**Parameters:**

- `context: ErrorContext` *(required)*

---

## casare_rpa.domain.errors.handlers.node_handler

**File:** `src\casare_rpa\domain\errors\handlers\node_handler.py`


CasareRPA - Node Error Handler.

Default error handler for node execution errors.


### NodeErrorHandler

**Inherits from:** `ErrorHandler`


Default error handler for node execution errors.

Provides baseline error classification and recovery for all nodes.
Can be extended for node-type-specific handling.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(node_types, default_max_retries, retry_on_transient)` | `None` | Initialize node error handler. |
| `can_handle(context)` | `bool` | Check if this handler applies to the error's node type. |
| `classify(context)` | `ErrorContext` | Classify error based on error code and exception type. |
| `decide_recovery(context)` | `RecoveryDecision` | Decide recovery action based on classification. |

#### Method Details

##### `__init__`

```python
def __init__(node_types: Optional[List[str]] = None, default_max_retries: int = 3, retry_on_transient: bool = True) -> None
```

Initialize node error handler.

Args:
    node_types: List of node type names this handler applies to.
               None means all node types.
    default_max_retries: Default max retry attempts.
    retry_on_transient: Whether to recommend retry for transient errors.

**Parameters:**

- `node_types: Optional[List[str]] = None`
- `default_max_retries: int = 3`
- `retry_on_transient: bool = True`

##### `can_handle`

```python
def can_handle(context: ErrorContext) -> bool
```

Check if this handler applies to the error's node type.

Args:
    context: Error context.

Returns:
    True if handler should process this error.

**Parameters:**

- `context: ErrorContext` *(required)*

##### `classify`

```python
def classify(context: ErrorContext) -> ErrorContext
```

Classify error based on error code and exception type.

Args:
    context: Error context to classify.

Returns:
    Updated context with classification, category, severity.

**Parameters:**

- `context: ErrorContext` *(required)*

##### `decide_recovery`

```python
def decide_recovery(context: ErrorContext) -> RecoveryDecision
```

Decide recovery action based on classification.

Args:
    context: Classified error context.

Returns:
    Recovery decision.

**Parameters:**

- `context: ErrorContext` *(required)*

---

## casare_rpa.domain.errors.registry

**File:** `src\casare_rpa\domain\errors\registry.py`


CasareRPA - Error Handler Registry.

Registry for error handlers with global singleton access.


### Functions

#### `get_error_handler_registry`

```python
def get_error_handler_registry() -> ErrorHandlerRegistry
```

Get the global error handler registry (singleton).

Returns:
    Global ErrorHandlerRegistry instance.

#### `reset_error_handler_registry`

```python
def reset_error_handler_registry() -> None
```

Reset the global error handler registry (for testing).


### ErrorHandlerRegistry


Registry for error handlers.

Maintains a collection of error handlers organized by:
- Node type (specific handlers for specific nodes)
- Error category (handlers for error types)
- Global (fallback handlers)

Handlers are tried in order of specificity:
1. Node-type specific handlers
2. Error-category handlers
3. Global handlers


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize error handler registry. |
| `clear_history()` | `None` | Clear error history. |
| `get_error_history(node_id, category, limit)` | `List[ErrorContext]` | Get error history with optional filtering. |
| `get_error_summary()` | `Dict[str, Any]` | Get summary of error history. |
| `handle_error(exception, node_id, node_type, ...)` | `tuple[ErrorContext, RecoveryDecision]` | Handle an error and get recovery decision. |
| `register_category_handler(category, handler)` | `None` | Register handler for error category. |
| `register_custom_handler(name, handler_func)` | `None` | Register custom handler function (user-defined). |
| `register_global_handler(handler)` | `None` | Register global handler (fallback). |
| `register_node_handler(node_type, handler)` | `None` | Register handler for specific node type. |
| `unregister_custom_handler(name)` | `bool` | Unregister custom handler. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize error handler registry.

##### `clear_history`

```python
def clear_history() -> None
```

Clear error history.

##### `get_error_history`

```python
def get_error_history(node_id: Optional[NodeId] = None, category: Optional[ErrorCategory] = None, limit: int = 100) -> List[ErrorContext]
```

Get error history with optional filtering.

Args:
    node_id: Filter by node ID.
    category: Filter by error category.
    limit: Maximum results.

Returns:
    List of error contexts (most recent first).

**Parameters:**

- `node_id: Optional[NodeId] = None`
- `category: Optional[ErrorCategory] = None`
- `limit: int = 100`

##### `get_error_summary`

```python
def get_error_summary() -> Dict[str, Any]
```

Get summary of error history.

Returns:
    Dictionary with error statistics.

##### `handle_error`

```python
def handle_error(exception: Exception, node_id: NodeId, node_type: str, retry_count: int = 0, max_retries: int = 3, execution_time_ms: float = 0.0, node_config: Optional[Dict[str, Any]] = None, variables: Optional[Dict[str, Any]] = None, additional_data: Optional[Dict[str, Any]] = None) -> tuple[ErrorContext, RecoveryDecision]
```

Handle an error and get recovery decision.

Args:
    exception: The exception that occurred.
    node_id: ID of the node where error occurred.
    node_type: Type/class name of the node.
    retry_count: Number of retries already attempted.
    max_retries: Maximum retry attempts.
    execution_time_ms: How long the operation ran.
    node_config: Node configuration.
    variables: Execution context variables.
    additional_data: Extra context (URL, selector, etc.).

Returns:
    Tuple of (ErrorContext, RecoveryDecision).

**Parameters:**

- `exception: Exception` *(required)*
- `node_id: NodeId` *(required)*
- `node_type: str` *(required)*
- `retry_count: int = 0`
- `max_retries: int = 3`
- `execution_time_ms: float = 0.0`
- `node_config: Optional[Dict[str, Any]] = None`
- `variables: Optional[Dict[str, Any]] = None`
- `additional_data: Optional[Dict[str, Any]] = None`

##### `register_category_handler`

```python
def register_category_handler(category: ErrorCategory, handler: ErrorHandler) -> None
```

Register handler for error category.

Args:
    category: Error category.
    handler: Error handler instance.

**Parameters:**

- `category: ErrorCategory` *(required)*
- `handler: ErrorHandler` *(required)*

##### `register_custom_handler`

```python
def register_custom_handler(name: str, handler_func: CustomErrorHandlerFunc) -> None
```

Register custom handler function (user-defined).

Args:
    name: Unique handler name.
    handler_func: Function that takes ErrorContext and returns RecoveryDecision.

**Parameters:**

- `name: str` *(required)*
- `handler_func: CustomErrorHandlerFunc` *(required)*

##### `register_global_handler`

```python
def register_global_handler(handler: ErrorHandler) -> None
```

Register global handler (fallback).

Args:
    handler: Error handler instance.

**Parameters:**

- `handler: ErrorHandler` *(required)*

##### `register_node_handler`

```python
def register_node_handler(node_type: str, handler: ErrorHandler) -> None
```

Register handler for specific node type.

Args:
    node_type: Node class name (e.g., "NavigateNode").
    handler: Error handler instance.

**Parameters:**

- `node_type: str` *(required)*
- `handler: ErrorHandler` *(required)*

##### `unregister_custom_handler`

```python
def unregister_custom_handler(name: str) -> bool
```

Unregister custom handler.

Args:
    name: Handler name to remove.

Returns:
    True if handler was removed, False if not found.

**Parameters:**

- `name: str` *(required)*

---

## casare_rpa.domain.errors.types

**File:** `src\casare_rpa\domain\errors\types.py`


CasareRPA - Error Types and Enumerations.

Defines error classification types, categories, severity levels, and recovery actions.


### ErrorCategory

**Inherits from:** `Enum`


High-level error categories for classification.

Categories help determine recovery strategy:
- BROWSER: Web automation errors (Playwright)
- DESKTOP: Windows UI automation errors
- NETWORK: Connection, timeout, SSL errors
- DATA: Validation, parsing, type errors
- RESOURCE: File, memory, permission errors
- CONFIGURATION: Node/workflow config errors
- EXECUTION: Runtime execution errors
- UNKNOWN: Unclassified errors


**Attributes:**

- `BROWSER: auto`
- `CONFIGURATION: auto`
- `DATA: auto`
- `DESKTOP: auto`
- `EXECUTION: auto`
- `NETWORK: auto`
- `RESOURCE: auto`
- `UNKNOWN: auto`

### ErrorClassification

**Inherits from:** `Enum`


Error classification for recovery decisions.

TRANSIENT: Temporary errors that may succeed on retry
    - Network timeouts
    - Element temporarily not visible
    - Application busy/not responding

PERMANENT: Errors that will not resolve with retry
    - Invalid selector (element doesn't exist)
    - Permission denied
    - Configuration errors

UNKNOWN: Cannot determine if transient or permanent
    - First occurrence of new error
    - Generic exceptions


**Attributes:**

- `PERMANENT: auto`
- `TRANSIENT: auto`
- `UNKNOWN: auto`

### ErrorSeverity

**Inherits from:** `Enum`


Error severity levels.

Severity affects:
- Logging level
- Recovery strategy aggressiveness
- Human escalation threshold


**Attributes:**

- `CRITICAL: int`
- `HIGH: int`
- `LOW: int`
- `MEDIUM: int`

### RecoveryAction

**Inherits from:** `Enum`


Recommended recovery actions.

Actions the recovery system can take:
- RETRY: Attempt the operation again
- SKIP: Skip this node and continue
- FALLBACK: Use alternative path/value
- COMPENSATE: Run rollback operations
- ABORT: Stop workflow execution
- ESCALATE: Request human intervention


**Attributes:**

- `ABORT: auto`
- `COMPENSATE: auto`
- `ESCALATE: auto`
- `FALLBACK: auto`
- `RETRY: auto`
- `SKIP: auto`

---

## casare_rpa.domain.events

**File:** `src\casare_rpa\domain\events.py`


CasareRPA - Domain Event System

Provides event-driven communication between components.
Implements the Observer pattern for loose coupling.

This is the canonical location for event system components (v3.0).


### Functions

#### `get_event_bus`

```python
def get_event_bus() -> EventBus
```

Get the event bus instance (singleton).

Thread-safe lazy initialization.

Returns:
    EventBus instance

#### `reset_event_bus`

```python
def reset_event_bus() -> None
```

Reset the event bus singleton (primarily for testing).

Thread-safe cleanup of the singleton.


### Event


Represents a single event.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(event_type, data, node_id)` | `None` | Initialize an event. |
| `__repr__()` | `str` | String representation. |
| `to_dict()` | `Dict[str, Any]` | Serialize event to dictionary. |

#### Method Details

##### `__init__`

```python
def __init__(event_type: EventType, data: Optional[EventData] = None, node_id: Optional[NodeId] = None) -> None
```

Initialize an event.

Args:
    event_type: Type of event
    data: Event data payload
    node_id: ID of node that triggered the event (if applicable)

**Parameters:**

- `event_type: EventType` *(required)*
- `data: Optional[EventData] = None`
- `node_id: Optional[NodeId] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize event to dictionary.

### EventBus


Central event bus for publishing and subscribing to events.
Implements the Observer pattern.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize event bus. |
| `__repr__()` | `str` | String representation. |
| `clear_handlers(event_type)` | `None` | Clear event handlers. |
| `clear_history()` | `None` | Clear event history. |
| `emit(event_type, data, node_id)` | `None` | Create and publish an event (convenience method). |
| `get_handler_count(event_type)` | `int` | Get number of handlers for an event type. |
| `get_history(event_type, limit)` | `List[Event]` | Get event history. |
| `publish(event)` | `None` | Publish an event to all subscribed handlers. |
| `subscribe(event_type, handler)` | `None` | Subscribe a handler to an event type. |
| `unsubscribe(event_type, handler)` | `None` | Unsubscribe a handler from an event type. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize event bus.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `clear_handlers`

```python
def clear_handlers(event_type: Optional[EventType] = None) -> None
```

Clear event handlers.

Args:
    event_type: Specific event type to clear (None for all)

**Parameters:**

- `event_type: Optional[EventType] = None`

##### `clear_history`

```python
def clear_history() -> None
```

Clear event history.

##### `emit`

```python
def emit(event_type: EventType, data: Optional[EventData] = None, node_id: Optional[NodeId] = None) -> None
```

Create and publish an event (convenience method).

Args:
    event_type: Type of event
    data: Event data
    node_id: Node ID (if applicable)

**Parameters:**

- `event_type: EventType` *(required)*
- `data: Optional[EventData] = None`
- `node_id: Optional[NodeId] = None`

##### `get_handler_count`

```python
def get_handler_count(event_type: EventType) -> int
```

Get number of handlers for an event type.

**Parameters:**

- `event_type: EventType` *(required)*

##### `get_history`

```python
def get_history(event_type: Optional[EventType] = None, limit: Optional[int] = None) -> List[Event]
```

Get event history.

Args:
    event_type: Filter by event type (None for all events)
    limit: Maximum number of events to return

Returns:
    List of events (most recent first)

**Parameters:**

- `event_type: Optional[EventType] = None`
- `limit: Optional[int] = None`

##### `publish`

```python
def publish(event: Event) -> None
```

Publish an event to all subscribed handlers.

Args:
    event: Event to publish

**Parameters:**

- `event: Event` *(required)*

##### `subscribe`

```python
def subscribe(event_type: EventType, handler: EventHandler) -> None
```

Subscribe a handler to an event type.

Args:
    event_type: Type of event to listen for
    handler: Callback function to handle the event

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: EventHandler` *(required)*

##### `unsubscribe`

```python
def unsubscribe(event_type: EventType, handler: EventHandler) -> None
```

Unsubscribe a handler from an event type.

Args:
    event_type: Type of event
    handler: Handler to remove

**Parameters:**

- `event_type: EventType` *(required)*
- `handler: EventHandler` *(required)*

### EventLogger


Utility class to log events to console/file.
Can be subscribed to the event bus.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(log_level)` | `None` | Initialize event logger. |
| `handle_event(event)` | `None` | Handle an event by logging it. |
| `subscribe_all(event_bus)` | `None` | Subscribe to all event types on the bus. |

#### Method Details

##### `__init__`

```python
def __init__(log_level: str = 'INFO') -> None
```

Initialize event logger.

Args:
    log_level: Logging level (INFO, DEBUG, etc.)

**Parameters:**

- `log_level: str = 'INFO'`

##### `handle_event`

```python
def handle_event(event: Event) -> None
```

Handle an event by logging it.

Args:
    event: Event to log

**Parameters:**

- `event: Event` *(required)*

##### `subscribe_all`

```python
def subscribe_all(event_bus: EventBus) -> None
```

Subscribe to all event types on the bus.

**Parameters:**

- `event_bus: EventBus` *(required)*

### EventRecorder


Records events for replay or analysis.
Useful for debugging and testing.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize event recorder. |
| `export_to_dict()` | `List[Dict[str, Any]]` | Export recorded events as list of dictionaries. |
| `get_recorded_events()` | `List[Event]` | Get all recorded events. |
| `handle_event(event)` | `None` | Handle an event by recording it. |
| `start_recording()` | `None` | Start recording events. |
| `stop_recording()` | `None` | Stop recording events. |
| `subscribe_all(event_bus)` | `None` | Subscribe to all event types on the bus. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize event recorder.

##### `export_to_dict`

```python
def export_to_dict() -> List[Dict[str, Any]]
```

Export recorded events as list of dictionaries.

##### `get_recorded_events`

```python
def get_recorded_events() -> List[Event]
```

Get all recorded events.

##### `handle_event`

```python
def handle_event(event: Event) -> None
```

Handle an event by recording it.

Args:
    event: Event to record

**Parameters:**

- `event: Event` *(required)*

##### `start_recording`

```python
def start_recording() -> None
```

Start recording events.

##### `stop_recording`

```python
def stop_recording() -> None
```

Stop recording events.

##### `subscribe_all`

```python
def subscribe_all(event_bus: EventBus) -> None
```

Subscribe to all event types on the bus.

**Parameters:**

- `event_bus: EventBus` *(required)*

---

## casare_rpa.domain.orchestrator.entities.dashboard_metrics

**File:** `src\casare_rpa\domain\orchestrator\entities\dashboard_metrics.py`


Dashboard metrics value object.


### DashboardMetrics

**Decorators:** `@dataclass`


Dashboard KPI metrics value object.


**Attributes:**

- `avg_duration_ms: float`
- `job_history: List[JobHistoryEntry]`
- `jobs_completed_today: int`
- `jobs_failed_today: int`
- `jobs_queued: int`
- `jobs_running: int`
- `max_duration_ms: float`
- `min_duration_ms: float`
- `robot_utilization: float`
- `robots_busy: int`
- `robots_offline: int`
- `robots_online: int`
- `robots_total: int`
- `schedules_enabled: int`
- `schedules_total: int`
- `success_rate_month: float`
- `success_rate_today: float`
- `success_rate_week: float`
- `total_jobs_month: int`
- `total_jobs_today: int`
- `total_jobs_week: int`
- `workflows_published: int`
- `workflows_total: int`

### JobHistoryEntry

**Decorators:** `@dataclass`


Single job history entry for charts.


**Attributes:**

- `cancelled: int`
- `completed: int`
- `failed: int`
- `timestamp: str`

---

## casare_rpa.domain.orchestrator.entities.job

**File:** `src\casare_rpa\domain\orchestrator\entities\job.py`


Job domain entity.


### Job

**Decorators:** `@dataclass`


Job execution domain entity with state machine behavior.


**Attributes:**

- `VALID_TRANSITIONS: dict`
- `completed_at: Optional[datetime]`
- `created_at: Optional[datetime]`
- `created_by: str`
- `current_node: str`
- `duration_ms: int`
- `environment: str`
- `error_message: str`
- `id: str`
- `logs: str`
- `priority: JobPriority`
- `progress: int`
- `result: Dict[str, Any]`
- `robot_id: str`
- `robot_name: str`
- `scheduled_time: Optional[datetime]`
- `started_at: Optional[datetime]`
- `status: JobStatus`
- `workflow_id: str`
- `workflow_json: str`
- `workflow_name: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate domain invariants after initialization. |
| `can_transition_to(new_status)` | `bool` | Check if job can transition to a new status. |
| `duration_formatted()` | `str` | Get formatted duration string. |
| `from_dict(data)` | `'Job'` | Create Job from dictionary. |
| `is_terminal()` | `bool` | Check if job is in a terminal state. |
| `to_dict()` | `Dict[str, Any]` | Convert Job to dictionary. |
| `transition_to(new_status)` | `None` | Transition job to a new status. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate domain invariants after initialization.

##### `can_transition_to`

```python
def can_transition_to(new_status: JobStatus) -> bool
```

Check if job can transition to a new status.

Args:
    new_status: Target status to transition to.

Returns:
    True if transition is valid.

**Parameters:**

- `new_status: JobStatus` *(required)*

##### `duration_formatted`

```python
@property
def duration_formatted() -> str
```

Get formatted duration string.

Returns:
    Human-readable duration (e.g., "1.5s", "2.3m", "1.2h").

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Job'
```

Create Job from dictionary.

Args:
    data: Dictionary with job data.

Returns:
    Job instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `is_terminal`

```python
def is_terminal() -> bool
```

Check if job is in a terminal state.

Returns:
    True if job status is terminal (cannot transition further).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert Job to dictionary.

Returns:
    Dictionary representation of job.

##### `transition_to`

```python
def transition_to(new_status: JobStatus) -> None
```

Transition job to a new status.

Args:
    new_status: Target status to transition to.

Raises:
    JobTransitionError: If transition is invalid.

**Parameters:**

- `new_status: JobStatus` *(required)*

### JobPriority

**Inherits from:** `Enum`


Job priority levels.


**Attributes:**

- `CRITICAL: int`
- `HIGH: int`
- `LOW: int`
- `NORMAL: int`

### JobStatus

**Inherits from:** `Enum`


Job execution status.


**Attributes:**

- `CANCELLED: str`
- `COMPLETED: str`
- `FAILED: str`
- `PENDING: str`
- `QUEUED: str`
- `RUNNING: str`
- `TIMEOUT: str`

---

## casare_rpa.domain.orchestrator.entities.robot

**File:** `src\casare_rpa\domain\orchestrator\entities\robot.py`


Robot domain entity.


### Robot

**Decorators:** `@dataclass`


Robot agent domain entity with behavior and invariants.

Robots can be assigned to workflows (default robot for a workflow) and can
handle multiple concurrent jobs up to their max_concurrent_jobs limit.


**Attributes:**

- `assigned_workflows: List[str]`
- `capabilities: Set[RobotCapability]`
- `created_at: Optional[datetime]`
- `current_job_ids: List[str]`
- `environment: str`
- `id: str`
- `last_heartbeat: Optional[datetime]`
- `last_seen: Optional[datetime]`
- `max_concurrent_jobs: int`
- `metrics: Dict[str, Any]`
- `name: str`
- `status: RobotStatus`
- `tags: List[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate domain invariants after initialization. |
| `assign_job(job_id)` | `None` | Assign a job to this robot. |
| `assign_workflow(workflow_id)` | `None` | Assign this robot as default for a workflow. |
| `can_accept_job()` | `bool` | Check if robot can accept a new job. |
| `complete_job(job_id)` | `None` | Mark a job as completed on this robot. |
| `current_jobs()` | `int` | Get count of current jobs (backward compatibility). |
| `from_dict(data)` | `'Robot'` | Create Robot from dictionary. |
| `has_all_capabilities(capabilities)` | `bool` | Check if robot has all specified capabilities. |
| `has_capability(capability)` | `bool` | Check if robot has a specific capability. |
| `is_assigned_to_workflow(workflow_id)` | `bool` | Check if robot is assigned to a workflow. |
| `is_available()` | `bool` | Check if robot can accept new jobs. |
| `to_dict()` | `Dict[str, Any]` | Convert Robot to dictionary. |
| `unassign_workflow(workflow_id)` | `None` | Remove workflow assignment from this robot. |
| `utilization()` | `float` | Get robot utilization percentage. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate domain invariants after initialization.

##### `assign_job`

```python
def assign_job(job_id: str) -> None
```

Assign a job to this robot.

Args:
    job_id: ID of the job to assign.

Raises:
    RobotUnavailableError: If robot is not in ONLINE status.
    RobotAtCapacityError: If robot is at max concurrent jobs.
    DuplicateJobAssignmentError: If job is already assigned to this robot.

**Parameters:**

- `job_id: str` *(required)*

##### `assign_workflow`

```python
def assign_workflow(workflow_id: str) -> None
```

Assign this robot as default for a workflow.

Args:
    workflow_id: ID of the workflow to assign.

**Parameters:**

- `workflow_id: str` *(required)*

##### `can_accept_job`

```python
def can_accept_job() -> bool
```

Check if robot can accept a new job.

Same as is_available but with clearer naming for job assignment context.

Returns:
    True if robot is online and has capacity.

##### `complete_job`

```python
def complete_job(job_id: str) -> None
```

Mark a job as completed on this robot.

Args:
    job_id: ID of the completed job.

Raises:
    InvalidRobotStateError: If job is not assigned to this robot.

**Parameters:**

- `job_id: str` *(required)*

##### `current_jobs`

```python
@property
def current_jobs() -> int
```

Get count of current jobs (backward compatibility).

Returns:
    Number of jobs currently assigned to this robot.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Robot'
```

Create Robot from dictionary.

Args:
    data: Dictionary with robot data.

Returns:
    Robot instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `has_all_capabilities`

```python
def has_all_capabilities(capabilities: Set[RobotCapability]) -> bool
```

Check if robot has all specified capabilities.

Args:
    capabilities: Set of capabilities to check for.

Returns:
    True if robot has all specified capabilities.

**Parameters:**

- `capabilities: Set[RobotCapability]` *(required)*

##### `has_capability`

```python
def has_capability(capability: RobotCapability) -> bool
```

Check if robot has a specific capability.

Args:
    capability: Capability to check for.

Returns:
    True if robot has the capability.

**Parameters:**

- `capability: RobotCapability` *(required)*

##### `is_assigned_to_workflow`

```python
def is_assigned_to_workflow(workflow_id: str) -> bool
```

Check if robot is assigned to a workflow.

Args:
    workflow_id: ID of the workflow to check.

Returns:
    True if robot is assigned to the workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `is_available`

```python
@property
def is_available() -> bool
```

Check if robot can accept new jobs.

Returns:
    True if robot is online and has capacity for more jobs.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert Robot to dictionary.

Returns:
    Dictionary representation of robot.

##### `unassign_workflow`

```python
def unassign_workflow(workflow_id: str) -> None
```

Remove workflow assignment from this robot.

Args:
    workflow_id: ID of the workflow to unassign.

**Parameters:**

- `workflow_id: str` *(required)*

##### `utilization`

```python
@property
def utilization() -> float
```

Get robot utilization percentage.

Returns:
    Percentage of capacity currently in use (0-100).

### RobotCapability

**Inherits from:** `Enum`


Robot capabilities for workload routing.


**Attributes:**

- `BROWSER: str`
- `CLOUD: str`
- `DESKTOP: str`
- `GPU: str`
- `HIGH_MEMORY: str`
- `ON_PREMISE: str`
- `SECURE: str`

### RobotStatus

**Inherits from:** `Enum`


Robot connection status.


**Attributes:**

- `BUSY: str`
- `ERROR: str`
- `MAINTENANCE: str`
- `OFFLINE: str`
- `ONLINE: str`

---

## casare_rpa.domain.orchestrator.entities.schedule

**File:** `src\casare_rpa\domain\orchestrator\entities\schedule.py`


Schedule domain entity.


### Schedule

**Decorators:** `@dataclass`


Workflow schedule domain entity.


**Attributes:**

- `created_at: Optional[datetime]`
- `created_by: str`
- `cron_expression: str`
- `enabled: bool`
- `frequency: ScheduleFrequency`
- `id: str`
- `last_run: Optional[datetime]`
- `name: str`
- `next_run: Optional[datetime]`
- `priority: JobPriority`
- `robot_id: Optional[str]`
- `robot_name: str`
- `run_count: int`
- `success_count: int`
- `timezone: str`
- `workflow_id: str`
- `workflow_name: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate domain invariants after initialization. |
| `from_dict(data)` | `'Schedule'` | Create Schedule from dictionary. |
| `success_rate()` | `float` | Calculate success rate percentage. |
| `to_dict()` | `Dict[str, Any]` | Convert Schedule to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate domain invariants after initialization.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Schedule'
```

Create Schedule from dictionary.

Args:
    data: Dictionary with schedule data.

Returns:
    Schedule instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `success_rate`

```python
@property
def success_rate() -> float
```

Calculate success rate percentage.

Returns:
    Success rate as percentage (0-100).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert Schedule to dictionary.

Returns:
    Dictionary representation of schedule.

### ScheduleFrequency

**Inherits from:** `Enum`


Schedule frequency types.


**Attributes:**

- `CRON: str`
- `DAILY: str`
- `HOURLY: str`
- `MONTHLY: str`
- `ONCE: str`
- `WEEKLY: str`

---

## casare_rpa.domain.orchestrator.entities.workflow

**File:** `src\casare_rpa\domain\orchestrator\entities\workflow.py`


Workflow domain entity.


### Workflow

**Decorators:** `@dataclass`


Workflow definition domain entity.


**Attributes:**

- `avg_duration_ms: int`
- `created_at: Optional[datetime]`
- `created_by: str`
- `description: str`
- `execution_count: int`
- `id: str`
- `json_definition: str`
- `name: str`
- `status: WorkflowStatus`
- `success_count: int`
- `tags: List[str]`
- `updated_at: Optional[datetime]`
- `version: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate domain invariants after initialization. |
| `from_dict(data)` | `'Workflow'` | Create Workflow from dictionary. |
| `success_rate()` | `float` | Calculate success rate percentage. |
| `to_dict()` | `Dict[str, Any]` | Convert Workflow to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate domain invariants after initialization.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'Workflow'
```

Create Workflow from dictionary.

Args:
    data: Dictionary with workflow data.

Returns:
    Workflow instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `success_rate`

```python
@property
def success_rate() -> float
```

Calculate success rate percentage.

Returns:
    Success rate as percentage (0-100).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert Workflow to dictionary.

Returns:
    Dictionary representation of workflow.

### WorkflowStatus

**Inherits from:** `Enum`


Workflow lifecycle status.


**Attributes:**

- `ARCHIVED: str`
- `DRAFT: str`
- `PUBLISHED: str`

---

## casare_rpa.domain.orchestrator.errors

**File:** `src\casare_rpa\domain\orchestrator\errors.py`


Domain errors for orchestrator.


### DuplicateAssignmentError

**Inherits from:** `OrchestratorDomainError`


Raised when creating a duplicate assignment.


### DuplicateJobAssignmentError

**Inherits from:** `OrchestratorDomainError`


Raised when trying to assign a job that's already assigned to the robot.


### InvalidAssignmentError

**Inherits from:** `OrchestratorDomainError`


Raised when a robot assignment is invalid.

This can happen when:
- Assigning to a non-existent workflow
- Assigning to a non-existent robot
- Creating conflicting assignments


### InvalidJobStateError

**Inherits from:** `OrchestratorDomainError`


Raised when job operation violates state invariants.


### InvalidRobotStateError

**Inherits from:** `OrchestratorDomainError`


Raised when robot operation violates state invariants.


### JobNotFoundError

**Inherits from:** `OrchestratorDomainError`


Raised when specified job does not exist.


### JobTransitionError

**Inherits from:** `OrchestratorDomainError`


Raised when invalid job status transition attempted.


### NoAvailableRobotError

**Inherits from:** `OrchestratorDomainError`


Raised when no robot is available to handle a job.

This can happen when:
- All robots are offline
- All robots are at capacity
- No robots have required capabilities


### OrchestratorDomainError

**Inherits from:** `Exception`


Base exception for orchestrator domain errors.


### RobotAtCapacityError

**Inherits from:** `OrchestratorDomainError`


Raised when robot is at max concurrent jobs capacity.


### RobotNotFoundError

**Inherits from:** `OrchestratorDomainError`


Raised when specified robot does not exist.


### RobotUnavailableError

**Inherits from:** `OrchestratorDomainError`


Raised when robot is not available for job assignment.


---

## casare_rpa.domain.orchestrator.protocols.robot_protocol

**File:** `src\casare_rpa\domain\orchestrator\protocols\robot_protocol.py`


Robot Communication Protocol for CasareRPA Orchestrator.
Defines message types and serialization for orchestrator-robot communication.


### Message

**Decorators:** `@dataclass`


Base message class for all protocol messages.


**Attributes:**

- `correlation_id: Optional[str]`
- `id: str`
- `payload: Dict[str, Any]`
- `timestamp: str`
- `type: MessageType`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_json(json_str)` | `'Message'` | Deserialize message from JSON. |
| `to_json()` | `str` | Serialize message to JSON. |

#### Method Details

##### `from_json`

```python
@classmethod
def from_json(json_str: str) -> 'Message'
```

Deserialize message from JSON.

**Parameters:**

- `json_str: str` *(required)*

##### `to_json`

```python
def to_json() -> str
```

Serialize message to JSON.

### MessageBuilder


Helper class to build protocol messages.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `disconnect(robot_id, reason)` | `Message` | Build disconnect message. |
| `error(error_code, error_message, details, ...)` | `Message` | Build error message. |
| `heartbeat(robot_id, status, current_jobs, ...)` | `Message` | Build heartbeat message. |
| `heartbeat_ack(robot_id, correlation_id)` | `Message` | Build heartbeat acknowledgment. |
| `job_accept(job_id, robot_id, correlation_id)` | `Message` | Build job acceptance message. |
| `job_assign(job_id, workflow_id, workflow_name, ...)` | `Message` | Build job assignment message. |
| `job_cancel(job_id, reason)` | `Message` | Build job cancellation request. |
| `job_cancelled(job_id, robot_id, correlation_id)` | `Message` | Build job cancelled confirmation. |
| `job_complete(job_id, robot_id, result, ...)` | `Message` | Build job completion message. |
| `job_failed(job_id, robot_id, error_message, ...)` | `Message` | Build job failure message. |
| `job_progress(job_id, robot_id, progress, ...)` | `Message` | Build job progress update message. |
| `job_reject(job_id, robot_id, reason, ...)` | `Message` | Build job rejection message. |
| `log_batch(job_id, robot_id, entries)` | `Message` | Build batch log message. |
| `log_entry(job_id, robot_id, level, ...)` | `Message` | Build log entry message. |
| `pause(robot_id)` | `Message` | Build pause command. |
| `register(robot_id, robot_name, environment, ...)` | `Message` | Build robot registration message. |
| `register_ack(robot_id, success, message, ...)` | `Message` | Build registration acknowledgment. |
| `resume(robot_id)` | `Message` | Build resume command. |
| `shutdown(robot_id, graceful)` | `Message` | Build shutdown command. |
| `status_request(robot_id)` | `Message` | Build status request message. |
| `status_response(robot_id, status, current_jobs, ...)` | `Message` | Build status response message. |

#### Method Details

##### `disconnect`

```python
@staticmethod
def disconnect(robot_id: str, reason: str = '') -> Message
```

Build disconnect message.

**Parameters:**

- `robot_id: str` *(required)*
- `reason: str = ''`

##### `error`

```python
@staticmethod
def error(error_code: str, error_message: str, details: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> Message
```

Build error message.

**Parameters:**

- `error_code: str` *(required)*
- `error_message: str` *(required)*
- `details: Optional[Dict[str, Any]] = None`
- `correlation_id: Optional[str] = None`

##### `heartbeat`

```python
@staticmethod
def heartbeat(robot_id: str, status: str, current_jobs: int = 0, cpu_percent: float = 0.0, memory_percent: float = 0.0, disk_percent: float = 0.0, active_job_ids: Optional[List[str]] = None) -> Message
```

Build heartbeat message.

**Parameters:**

- `robot_id: str` *(required)*
- `status: str` *(required)*
- `current_jobs: int = 0`
- `cpu_percent: float = 0.0`
- `memory_percent: float = 0.0`
- `disk_percent: float = 0.0`
- `active_job_ids: Optional[List[str]] = None`

##### `heartbeat_ack`

```python
@staticmethod
def heartbeat_ack(robot_id: str, correlation_id: Optional[str] = None) -> Message
```

Build heartbeat acknowledgment.

**Parameters:**

- `robot_id: str` *(required)*
- `correlation_id: Optional[str] = None`

##### `job_accept`

```python
@staticmethod
def job_accept(job_id: str, robot_id: str, correlation_id: Optional[str] = None) -> Message
```

Build job acceptance message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `correlation_id: Optional[str] = None`

##### `job_assign`

```python
@staticmethod
def job_assign(job_id: str, workflow_id: str, workflow_name: str, workflow_json: str, priority: int = 1, timeout_seconds: int = 3600, parameters: Optional[Dict[str, Any]] = None) -> Message
```

Build job assignment message.

**Parameters:**

- `job_id: str` *(required)*
- `workflow_id: str` *(required)*
- `workflow_name: str` *(required)*
- `workflow_json: str` *(required)*
- `priority: int = 1`
- `timeout_seconds: int = 3600`
- `parameters: Optional[Dict[str, Any]] = None`

##### `job_cancel`

```python
@staticmethod
def job_cancel(job_id: str, reason: str = 'Cancelled by orchestrator') -> Message
```

Build job cancellation request.

**Parameters:**

- `job_id: str` *(required)*
- `reason: str = 'Cancelled by orchestrator'`

##### `job_cancelled`

```python
@staticmethod
def job_cancelled(job_id: str, robot_id: str, correlation_id: Optional[str] = None) -> Message
```

Build job cancelled confirmation.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `correlation_id: Optional[str] = None`

##### `job_complete`

```python
@staticmethod
def job_complete(job_id: str, robot_id: str, result: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> Message
```

Build job completion message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `result: Optional[Dict[str, Any]] = None`
- `duration_ms: int = 0`

##### `job_failed`

```python
@staticmethod
def job_failed(job_id: str, robot_id: str, error_message: str, error_type: str = 'ExecutionError', stack_trace: str = '', failed_node: str = '') -> Message
```

Build job failure message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `error_message: str` *(required)*
- `error_type: str = 'ExecutionError'`
- `stack_trace: str = ''`
- `failed_node: str = ''`

##### `job_progress`

```python
@staticmethod
def job_progress(job_id: str, robot_id: str, progress: int, current_node: str = '', message: str = '') -> Message
```

Build job progress update message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `progress: int` *(required)*
- `current_node: str = ''`
- `message: str = ''`

##### `job_reject`

```python
@staticmethod
def job_reject(job_id: str, robot_id: str, reason: str, correlation_id: Optional[str] = None) -> Message
```

Build job rejection message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `reason: str` *(required)*
- `correlation_id: Optional[str] = None`

##### `log_batch`

```python
@staticmethod
def log_batch(job_id: str, robot_id: str, entries: List[Dict[str, Any]]) -> Message
```

Build batch log message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `entries: List[Dict[str, Any]]` *(required)*

##### `log_entry`

```python
@staticmethod
def log_entry(job_id: str, robot_id: str, level: str, message: str, node_id: str = '', extra: Optional[Dict[str, Any]] = None) -> Message
```

Build log entry message.

**Parameters:**

- `job_id: str` *(required)*
- `robot_id: str` *(required)*
- `level: str` *(required)*
- `message: str` *(required)*
- `node_id: str = ''`
- `extra: Optional[Dict[str, Any]] = None`

##### `pause`

```python
@staticmethod
def pause(robot_id: str) -> Message
```

Build pause command.

**Parameters:**

- `robot_id: str` *(required)*

##### `register`

```python
@staticmethod
def register(robot_id: str, robot_name: str, environment: str = 'default', max_concurrent_jobs: int = 1, tags: Optional[List[str]] = None, capabilities: Optional[Dict[str, Any]] = None) -> Message
```

Build robot registration message.

**Parameters:**

- `robot_id: str` *(required)*
- `robot_name: str` *(required)*
- `environment: str = 'default'`
- `max_concurrent_jobs: int = 1`
- `tags: Optional[List[str]] = None`
- `capabilities: Optional[Dict[str, Any]] = None`

##### `register_ack`

```python
@staticmethod
def register_ack(robot_id: str, success: bool, message: str = '', config: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> Message
```

Build registration acknowledgment.

**Parameters:**

- `robot_id: str` *(required)*
- `success: bool` *(required)*
- `message: str = ''`
- `config: Optional[Dict[str, Any]] = None`
- `correlation_id: Optional[str] = None`

##### `resume`

```python
@staticmethod
def resume(robot_id: str) -> Message
```

Build resume command.

**Parameters:**

- `robot_id: str` *(required)*

##### `shutdown`

```python
@staticmethod
def shutdown(robot_id: str, graceful: bool = True) -> Message
```

Build shutdown command.

**Parameters:**

- `robot_id: str` *(required)*
- `graceful: bool = True`

##### `status_request`

```python
@staticmethod
def status_request(robot_id: str) -> Message
```

Build status request message.

**Parameters:**

- `robot_id: str` *(required)*

##### `status_response`

```python
@staticmethod
def status_response(robot_id: str, status: str, current_jobs: int, active_job_ids: List[str], uptime_seconds: int, system_info: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> Message
```

Build status response message.

**Parameters:**

- `robot_id: str` *(required)*
- `status: str` *(required)*
- `current_jobs: int` *(required)*
- `active_job_ids: List[str]` *(required)*
- `uptime_seconds: int` *(required)*
- `system_info: Optional[Dict[str, Any]] = None`
- `correlation_id: Optional[str] = None`

### MessageType

**Inherits from:** `Enum`


Types of messages exchanged between orchestrator and robot.


**Attributes:**

- `DISCONNECT: str`
- `ERROR: str`
- `HEARTBEAT: str`
- `HEARTBEAT_ACK: str`
- `JOB_ACCEPT: str`
- `JOB_ASSIGN: str`
- `JOB_CANCEL: str`
- `JOB_CANCELLED: str`
- `JOB_COMPLETE: str`
- `JOB_FAILED: str`
- `JOB_PROGRESS: str`
- `JOB_REJECT: str`
- `LOG_BATCH: str`
- `LOG_ENTRY: str`
- `PAUSE: str`
- `REGISTER: str`
- `REGISTER_ACK: str`
- `RESUME: str`
- `SHUTDOWN: str`
- `STATUS_REQUEST: str`
- `STATUS_RESPONSE: str`

---

## casare_rpa.domain.orchestrator.repositories.job_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\job_repository.py`


Job repository interface.


### JobRepository

**Inherits from:** `ABC`


Repository interface for Job aggregate.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(job_id)` | `None` | Delete job by ID. |
| `async get_all()` | `List[Job]` | Get all jobs. |
| `async get_by_id(job_id)` | `Optional[Job]` | Get job by ID. |
| `async get_by_robot(robot_id)` | `List[Job]` | Get jobs assigned to robot. |
| `async get_by_status(status)` | `List[Job]` | Get jobs by status. |
| `async get_by_workflow(workflow_id)` | `List[Job]` | Get jobs for workflow. |
| `async save(job)` | `None` | Save or update job. |

#### Method Details

##### `delete`

```python
async def delete(job_id: str) -> None
```

Delete job by ID.

**Parameters:**

- `job_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[Job]
```

Get all jobs.

##### `get_by_id`

```python
async def get_by_id(job_id: str) -> Optional[Job]
```

Get job by ID.

**Parameters:**

- `job_id: str` *(required)*

##### `get_by_robot`

```python
async def get_by_robot(robot_id: str) -> List[Job]
```

Get jobs assigned to robot.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_by_status`

```python
async def get_by_status(status: JobStatus) -> List[Job]
```

Get jobs by status.

**Parameters:**

- `status: JobStatus` *(required)*

##### `get_by_workflow`

```python
async def get_by_workflow(workflow_id: str) -> List[Job]
```

Get jobs for workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `save`

```python
async def save(job: Job) -> None
```

Save or update job.

**Parameters:**

- `job: Job` *(required)*

---

## casare_rpa.domain.orchestrator.repositories.robot_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\robot_repository.py`


Robot repository interface.


### RobotRepository

**Inherits from:** `ABC`


Repository interface for Robot aggregate.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(robot_id)` | `None` | Delete robot by ID. |
| `async get_all()` | `List[Robot]` | Get all robots. |
| `async get_all_online()` | `List[Robot]` | Get all online robots. |
| `async get_by_environment(environment)` | `List[Robot]` | Get robots in specific environment. |
| `async get_by_id(robot_id)` | `Optional[Robot]` | Get robot by ID. |
| `async save(robot)` | `None` | Save or update robot. |
| `async update_status(robot_id, status)` | `None` | Update robot status. |

#### Method Details

##### `delete`

```python
async def delete(robot_id: str) -> None
```

Delete robot by ID.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[Robot]
```

Get all robots.

##### `get_all_online`

```python
async def get_all_online() -> List[Robot]
```

Get all online robots.

##### `get_by_environment`

```python
async def get_by_environment(environment: str) -> List[Robot]
```

Get robots in specific environment.

**Parameters:**

- `environment: str` *(required)*

##### `get_by_id`

```python
async def get_by_id(robot_id: str) -> Optional[Robot]
```

Get robot by ID.

**Parameters:**

- `robot_id: str` *(required)*

##### `save`

```python
async def save(robot: Robot) -> None
```

Save or update robot.

**Parameters:**

- `robot: Robot` *(required)*

##### `update_status`

```python
async def update_status(robot_id: str, status: RobotStatus) -> None
```

Update robot status.

**Parameters:**

- `robot_id: str` *(required)*
- `status: RobotStatus` *(required)*

---

## casare_rpa.domain.orchestrator.repositories.schedule_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\schedule_repository.py`


Schedule repository interface.


### ScheduleRepository

**Inherits from:** `ABC`


Repository interface for Schedule aggregate.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(schedule_id)` | `None` | Delete schedule by ID. |
| `async get_all()` | `List[Schedule]` | Get all schedules. |
| `async get_by_id(schedule_id)` | `Optional[Schedule]` | Get schedule by ID. |
| `async get_enabled()` | `List[Schedule]` | Get all enabled schedules. |
| `async save(schedule)` | `None` | Save or update schedule. |

#### Method Details

##### `delete`

```python
async def delete(schedule_id: str) -> None
```

Delete schedule by ID.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[Schedule]
```

Get all schedules.

##### `get_by_id`

```python
async def get_by_id(schedule_id: str) -> Optional[Schedule]
```

Get schedule by ID.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_enabled`

```python
async def get_enabled() -> List[Schedule]
```

Get all enabled schedules.

##### `save`

```python
async def save(schedule: Schedule) -> None
```

Save or update schedule.

**Parameters:**

- `schedule: Schedule` *(required)*

---

## casare_rpa.domain.orchestrator.repositories.trigger_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\trigger_repository.py`


Trigger repository interface.


### TriggerRepository

**Inherits from:** `ABC`


Repository interface for Trigger aggregate.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(trigger_id)` | `None` | Delete trigger by ID. |
| `async delete_by_scenario(scenario_id)` | `int` | Delete all triggers for a scenario. Returns count deleted. |
| `async get_all()` | `List[BaseTriggerConfig]` | Get all triggers. |
| `async get_by_id(trigger_id)` | `Optional[BaseTriggerConfig]` | Get trigger by ID. |
| `async get_by_scenario(scenario_id)` | `List[BaseTriggerConfig]` | Get all triggers for a scenario. |
| `async get_by_type(trigger_type)` | `List[BaseTriggerConfig]` | Get all triggers of a specific type. |
| `async get_by_workflow(workflow_id)` | `List[BaseTriggerConfig]` | Get all triggers for a workflow. |
| `async get_enabled()` | `List[BaseTriggerConfig]` | Get all enabled triggers. |
| `async save(trigger)` | `None` | Save or update trigger. |

#### Method Details

##### `delete`

```python
async def delete(trigger_id: str) -> None
```

Delete trigger by ID.

**Parameters:**

- `trigger_id: str` *(required)*

##### `delete_by_scenario`

```python
async def delete_by_scenario(scenario_id: str) -> int
```

Delete all triggers for a scenario. Returns count deleted.

**Parameters:**

- `scenario_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[BaseTriggerConfig]
```

Get all triggers.

##### `get_by_id`

```python
async def get_by_id(trigger_id: str) -> Optional[BaseTriggerConfig]
```

Get trigger by ID.

**Parameters:**

- `trigger_id: str` *(required)*

##### `get_by_scenario`

```python
async def get_by_scenario(scenario_id: str) -> List[BaseTriggerConfig]
```

Get all triggers for a scenario.

**Parameters:**

- `scenario_id: str` *(required)*

##### `get_by_type`

```python
async def get_by_type(trigger_type: TriggerType) -> List[BaseTriggerConfig]
```

Get all triggers of a specific type.

**Parameters:**

- `trigger_type: TriggerType` *(required)*

##### `get_by_workflow`

```python
async def get_by_workflow(workflow_id: str) -> List[BaseTriggerConfig]
```

Get all triggers for a workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_enabled`

```python
async def get_enabled() -> List[BaseTriggerConfig]
```

Get all enabled triggers.

##### `save`

```python
async def save(trigger: BaseTriggerConfig) -> None
```

Save or update trigger.

**Parameters:**

- `trigger: BaseTriggerConfig` *(required)*

---

## casare_rpa.domain.orchestrator.repositories.workflow_repository

**File:** `src\casare_rpa\domain\orchestrator\repositories\workflow_repository.py`


Workflow repository interface.


### WorkflowRepository

**Inherits from:** `ABC`


Repository interface for Workflow aggregate.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(workflow_id)` | `None` | Delete workflow by ID. |
| `async get_all()` | `List[Workflow]` | Get all workflows. |
| `async get_by_id(workflow_id)` | `Optional[Workflow]` | Get workflow by ID. |
| `async get_by_status(status)` | `List[Workflow]` | Get workflows by status. |
| `async save(workflow)` | `None` | Save or update workflow. |

#### Method Details

##### `delete`

```python
async def delete(workflow_id: str) -> None
```

Delete workflow by ID.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[Workflow]
```

Get all workflows.

##### `get_by_id`

```python
async def get_by_id(workflow_id: str) -> Optional[Workflow]
```

Get workflow by ID.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_by_status`

```python
async def get_by_status(status: WorkflowStatus) -> List[Workflow]
```

Get workflows by status.

**Parameters:**

- `status: WorkflowStatus` *(required)*

##### `save`

```python
async def save(workflow: Workflow) -> None
```

Save or update workflow.

**Parameters:**

- `workflow: Workflow` *(required)*

---

## casare_rpa.domain.orchestrator.services.robot_selection_service

**File:** `src\casare_rpa\domain\orchestrator\services\robot_selection_service.py`


RobotSelectionService - Pure domain service for robot selection logic.

This is a PURE domain service with NO infrastructure dependencies:
- NO async/await
- NO database access
- NO external APIs
- NO I/O operations

All robot data and assignments must be passed in as parameters.


### RobotSelectionService


Domain service for selecting robots for workflow/node execution.

Selection priority (highest to lowest):
1. Node-level override (if exists and active)
2. Workflow default assignment
3. Auto-selection (least loaded available robot with required capabilities)

This service is stateless and operates on data passed to its methods.
All I/O (fetching robots, assignments) happens in the application layer.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_robot_scores(robots, workflow_id, assignments, ...)` | `Dict[str, float]` | Calculate selection scores for robots. |
| `get_available_robots(robots, required_capabilities)` | `List[Robot]` | Get list of available robots matching required capabilities. |
| `get_robots_by_capability(robots, capability, available_only)` | `List[Robot]` | Get robots that have a specific capability. |
| `select_robot_for_node(workflow_id, node_id, robots, ...)` | `str` | Select the best robot to execute a specific node. |
| `select_robot_for_workflow(workflow_id, robots, assignments, ...)` | `str` | Select the best robot to execute a workflow. |

#### Method Details

##### `calculate_robot_scores`

```python
def calculate_robot_scores(robots: List[Robot], workflow_id: str, assignments: List[RobotAssignment], required_capabilities: Optional[Set[RobotCapability]] = None) -> Dict[str, float]
```

Calculate selection scores for robots.

Scoring factors (higher = better):
- Availability: +100 if can accept job, 0 otherwise
- Assignment: +50 if assigned to workflow
- Capabilities: +20 per matching capability
- Load: +30 * (1 - utilization/100)
- Environment match: +10 if same environment

Args:
    robots: List of robots to score.
    workflow_id: Workflow being assigned.
    assignments: Current assignments.
    required_capabilities: Required capabilities.

Returns:
    Dictionary mapping robot_id to score.

**Parameters:**

- `robots: List[Robot]` *(required)*
- `workflow_id: str` *(required)*
- `assignments: List[RobotAssignment]` *(required)*
- `required_capabilities: Optional[Set[RobotCapability]] = None`

##### `get_available_robots`

```python
def get_available_robots(robots: List[Robot], required_capabilities: Optional[Set[RobotCapability]] = None) -> List[Robot]
```

Get list of available robots matching required capabilities.

A robot is available if:
- Status is ONLINE
- Has capacity for more jobs (current_jobs < max_concurrent_jobs)
- Has all required capabilities (if specified)

Args:
    robots: List of all robots to filter.
    required_capabilities: Optional capabilities to filter by.

Returns:
    List of available robots sorted by utilization (lowest first).

**Parameters:**

- `robots: List[Robot]` *(required)*
- `required_capabilities: Optional[Set[RobotCapability]] = None`

##### `get_robots_by_capability`

```python
def get_robots_by_capability(robots: List[Robot], capability: RobotCapability, available_only: bool = True) -> List[Robot]
```

Get robots that have a specific capability.

Args:
    robots: List of all robots to filter.
    capability: Capability to filter by.
    available_only: If True, only return available robots.

Returns:
    List of robots with the capability.

**Parameters:**

- `robots: List[Robot]` *(required)*
- `capability: RobotCapability` *(required)*
- `available_only: bool = True`

##### `select_robot_for_node`

```python
def select_robot_for_node(workflow_id: str, node_id: str, robots: List[Robot], assignments: List[RobotAssignment], overrides: List[NodeRobotOverride], default_capabilities: Optional[Set[RobotCapability]] = None) -> str
```

Select the best robot to execute a specific node.

Selection priority:
1. Active node-level override (if exists)
   a. Specific robot override
   b. Capability-based override
2. Workflow default assignment
3. Auto-selection

Args:
    workflow_id: ID of the workflow containing the node.
    node_id: ID of the node to execute.
    robots: List of all robots to consider.
    assignments: List of workflow-to-robot assignments.
    overrides: List of node-level robot overrides.
    default_capabilities: Default capabilities required if no override.

Returns:
    Robot ID of the selected robot.

Raises:
    NoAvailableRobotError: If no robot can handle the node.
    RobotNotFoundError: If specified robot doesn't exist.

**Parameters:**

- `workflow_id: str` *(required)*
- `node_id: str` *(required)*
- `robots: List[Robot]` *(required)*
- `assignments: List[RobotAssignment]` *(required)*
- `overrides: List[NodeRobotOverride]` *(required)*
- `default_capabilities: Optional[Set[RobotCapability]] = None`

##### `select_robot_for_workflow`

```python
def select_robot_for_workflow(workflow_id: str, robots: List[Robot], assignments: List[RobotAssignment], required_capabilities: Optional[Set[RobotCapability]] = None) -> str
```

Select the best robot to execute a workflow.

Selection logic:
1. Check for workflow assignment (default robot)
2. If assigned robot is available, use it
3. Otherwise, auto-select based on availability and capabilities

Args:
    workflow_id: ID of the workflow to execute.
    robots: List of all robots to consider.
    assignments: List of workflow-to-robot assignments.
    required_capabilities: Optional capabilities required for the workflow.

Returns:
    Robot ID of the selected robot.

Raises:
    NoAvailableRobotError: If no robot can handle the workflow.
    RobotNotFoundError: If assigned robot doesn't exist.

**Parameters:**

- `workflow_id: str` *(required)*
- `robots: List[Robot]` *(required)*
- `assignments: List[RobotAssignment]` *(required)*
- `required_capabilities: Optional[Set[RobotCapability]] = None`

---

## casare_rpa.domain.orchestrator.value_objects.node_robot_override

**File:** `src\casare_rpa\domain\orchestrator\value_objects\node_robot_override.py`


NodeRobotOverride value object for node-level robot routing.


### NodeRobotOverride

**Decorators:** `@dataclass`


Value object for node-level robot override within a workflow.

NodeRobotOverride allows specific nodes within a workflow to target a
different robot than the workflow's default. This is useful for:
- Nodes requiring specific capabilities (GPU, desktop automation)
- Load balancing specific heavy operations
- Routing sensitive operations to secure robots

When a node has an override, the RobotSelectionService will use the
override's robot_id instead of the workflow's default assignment.

Attributes:
    workflow_id: ID of the workflow containing the node.
    node_id: ID of the node to override.
    robot_id: ID of the specific robot to use (None = use capability matching).
    required_capabilities: Capabilities required (if robot_id is None).
    reason: Human-readable explanation for the override.
    created_at: When this override was created.
    created_by: User/system that created this override.
    is_active: Whether this override is currently active.


**Attributes:**

- `created_at: datetime`
- `created_by: str`
- `is_active: bool`
- `node_id: str`
- `reason: Optional[str]`
- `required_capabilities: frozenset`
- `robot_id: Optional[str]`
- `workflow_id: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate override invariants. |
| `__repr__()` | `str` | String representation. |
| `from_dict(data)` | `'NodeRobotOverride'` | Create NodeRobotOverride from dictionary. |
| `is_capability_based()` | `bool` | Check if this override is based on required capabilities. |
| `is_specific_robot()` | `bool` | Check if this override targets a specific robot. |
| `to_dict()` | `dict` | Serialize override to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate override invariants.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `from_dict`

```python
@classmethod
def from_dict(data: dict) -> 'NodeRobotOverride'
```

Create NodeRobotOverride from dictionary.

Args:
    data: Dictionary with override data.

Returns:
    NodeRobotOverride instance.

**Parameters:**

- `data: dict` *(required)*

##### `is_capability_based`

```python
@property
def is_capability_based() -> bool
```

Check if this override is based on required capabilities.

Returns:
    True if override uses capability matching, False if specific robot.

##### `is_specific_robot`

```python
@property
def is_specific_robot() -> bool
```

Check if this override targets a specific robot.

Returns:
    True if override specifies a robot_id, False if capability-based.

##### `to_dict`

```python
def to_dict() -> dict
```

Serialize override to dictionary.

Returns:
    Dictionary representation of the override.

---

## casare_rpa.domain.orchestrator.value_objects.robot_assignment

**File:** `src\casare_rpa\domain\orchestrator\value_objects\robot_assignment.py`


RobotAssignment value object for workflow-level robot assignments.


### RobotAssignment

**Decorators:** `@dataclass`


Value object representing a workflow-to-robot assignment.

RobotAssignment is immutable (frozen=True) and identifies the default robot
for executing a workflow. When a workflow is triggered, the orchestrator
first checks for a RobotAssignment to determine which robot should run it.

Attributes:
    workflow_id: ID of the workflow being assigned.
    robot_id: ID of the robot assigned to run this workflow.
    is_default: Whether this is the default assignment for the workflow.
    priority: Assignment priority (higher = preferred when multiple exist).
    created_at: When this assignment was created.
    created_by: User/system that created this assignment.
    notes: Optional notes about why this assignment was made.


**Attributes:**

- `created_at: datetime`
- `created_by: str`
- `is_default: bool`
- `notes: Optional[str]`
- `priority: int`
- `robot_id: str`
- `workflow_id: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Validate assignment invariants. |
| `__repr__()` | `str` | String representation. |
| `from_dict(data)` | `'RobotAssignment'` | Create RobotAssignment from dictionary. |
| `to_dict()` | `dict` | Serialize assignment to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Validate assignment invariants.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `from_dict`

```python
@classmethod
def from_dict(data: dict) -> 'RobotAssignment'
```

Create RobotAssignment from dictionary.

Args:
    data: Dictionary with assignment data.

Returns:
    RobotAssignment instance.

**Parameters:**

- `data: dict` *(required)*

##### `to_dict`

```python
def to_dict() -> dict
```

Serialize assignment to dictionary.

Returns:
    Dictionary representation of the assignment.

---

## casare_rpa.domain.ports.port_type_interfaces

**File:** `src\casare_rpa\domain\ports\port_type_interfaces.py`


Domain Layer Port Type Interfaces.

This module defines protocols and value objects for the port type system.
These are pure domain concepts with no external dependencies.

The actual implementation (colors, shapes, registry) lives in the
infrastructure layer (infrastructure.adapters.port_type_system).


### DefaultCompatibilityRule


Default type compatibility rules.

This is a domain service that defines the business rules for
port type compatibility. It has no external dependencies.

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

This is a domain value object describing port visual characteristics.

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

### PortTypeRegistryProtocol

**Inherits from:** `Protocol`


Protocol for port type registry.

Defines the interface that infrastructure implementations must provide.
Enables dependency inversion - domain code depends on this abstraction,
not the concrete registry implementation.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_compatible_types(source)` | `Set[DataType]` | Get all types that are compatible with the source type. |
| `get_exec_color()` | `Tuple[int, int, int, int]` | Get the color for execution ports. |
| `get_incompatibility_reason(source, target)` | `Optional[str]` | Get reason why types are incompatible. |
| `get_type_color(data_type)` | `Tuple[int, int, int, int]` | Get the RGBA color for a data type. |
| `get_type_info(data_type)` | `PortTypeInfo` | Get metadata for a data type. |
| `get_type_shape(data_type)` | `PortShape` | Get the shape for a data type (for accessibility). |
| `is_compatible(source, target)` | `bool` | Check if source type can connect to target type. |

#### Method Details

##### `get_compatible_types`

```python
def get_compatible_types(source: DataType) -> Set[DataType]
```

Get all types that are compatible with the source type.

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

Get reason why types are incompatible.

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

##### `get_type_color`

```python
def get_type_color(data_type: DataType) -> Tuple[int, int, int, int]
```

Get the RGBA color for a data type.

**Parameters:**

- `data_type: DataType` *(required)*

##### `get_type_info`

```python
def get_type_info(data_type: DataType) -> PortTypeInfo
```

Get metadata for a data type.

**Parameters:**

- `data_type: DataType` *(required)*

##### `get_type_shape`

```python
def get_type_shape(data_type: DataType) -> PortShape
```

Get the shape for a data type (for accessibility).

**Parameters:**

- `data_type: DataType` *(required)*

##### `is_compatible`

```python
def is_compatible(source: DataType, target: DataType) -> bool
```

Check if source type can connect to target type.

**Parameters:**

- `source: DataType` *(required)*
- `target: DataType` *(required)*

### TypeCompatibilityRule

**Inherits from:** `Protocol`


Protocol for type compatibility checking.

Implementations define rules for which port types can connect.
This follows the Open/Closed Principle - new rules can be added
without modifying existing code.


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

---

## casare_rpa.domain.protocols.credential_protocols

**File:** `src\casare_rpa\domain\protocols\credential_protocols.py`


Domain Layer Credential Protocols.

This module defines protocols for credential resolution that allow
the domain layer to remain pure (no infrastructure dependencies).

The actual implementations live in the infrastructure layer:
- ExecutionContext: infrastructure.execution.execution_context
- VaultCredentialProvider: infrastructure.security.credential_provider
- ResolvedCredential: infrastructure.security.credential_provider

These protocols follow Dependency Inversion Principle - domain code
depends on abstractions (protocols), not concrete implementations.


### CredentialProviderProtocol

**Inherits from:** `Protocol`

**Decorators:** `@runtime_checkable`


Protocol defining the interface for credential providers.

This protocol enables domain code to work with credentials
without depending on the infrastructure VaultCredentialProvider.

Infrastructure implementations must provide:
- get_credential(alias, required) -> ResolvedCredentialData or None
- get_credential_by_path(path, alias) -> ResolvedCredentialData
- register_bindings(bindings) -> None


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async get_credential(alias, required)` | `Optional[ResolvedCredentialData]` | Get credential by alias. |
| `async get_credential_by_path(vault_path, alias)` | `ResolvedCredentialData` | Get credential by direct vault path. |
| `register_bindings(bindings)` | `None` | Register multiple credential bindings. |

#### Method Details

##### `get_credential`

```python
async def get_credential(alias: str, required: bool = True) -> Optional[ResolvedCredentialData]
```

Get credential by alias.

Args:
    alias: Credential alias
    required: If True, raises error when not found

Returns:
    ResolvedCredentialData or None if not required and not found

Raises:
    SecretNotFoundError: If required and alias not registered

**Parameters:**

- `alias: str` *(required)*
- `required: bool = True`

##### `get_credential_by_path`

```python
async def get_credential_by_path(vault_path: str, alias: Optional[str] = None) -> ResolvedCredentialData
```

Get credential by direct vault path.

Args:
    vault_path: Full vault path
    alias: Optional alias for reference

Returns:
    ResolvedCredentialData with all extracted fields

**Parameters:**

- `vault_path: str` *(required)*
- `alias: Optional[str] = None`

##### `register_bindings`

```python
def register_bindings(bindings: Dict[str, str]) -> None
```

Register multiple credential bindings.

Args:
    bindings: Dictionary mapping alias to vault path

**Parameters:**

- `bindings: Dict[str, str]` *(required)*

### ExecutionContextProtocol

**Inherits from:** `Protocol`

**Decorators:** `@runtime_checkable`


Protocol defining the execution context interface for credential resolution.

This protocol allows CredentialAwareMixin to work with any execution
context implementation without importing from infrastructure.

The infrastructure ExecutionContext implements this protocol.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_variable(name, default)` | `Any` | Get a variable from the context. |
| `has_project_context()` | `bool` | Check if a project context is available. |
| `project_context()` | `Optional[Any]` | Get the project context (if any). |
| `resolve_value(value)` | `Any` | Resolve {{variable_name}} patterns in a value. |
| `resources()` | `Dict[str, Any]` | Get resources dictionary for storing/retrieving resources. |

#### Method Details

##### `get_variable`

```python
def get_variable(name: str, default: Any = None) -> Any
```

Get a variable from the context.

Args:
    name: Variable name
    default: Default value if variable not found

Returns:
    Variable value or default

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `has_project_context`

```python
@property
def has_project_context() -> bool
```

Check if a project context is available.

##### `project_context`

```python
@property
def project_context() -> Optional[Any]
```

Get the project context (if any).

##### `resolve_value`

```python
def resolve_value(value: Any) -> Any
```

Resolve {{variable_name}} patterns in a value.

Args:
    value: The value to resolve (only strings are processed)

Returns:
    The resolved value with all {{variable}} patterns replaced.

**Parameters:**

- `value: Any` *(required)*

##### `resources`

```python
@property
def resources() -> Dict[str, Any]
```

Get resources dictionary for storing/retrieving resources.

### ResolvedCredentialData

**Decorators:** `@dataclass`


Domain value object representing resolved credential data.

This is a pure data container with no infrastructure dependencies.
The infrastructure layer maps its ResolvedCredential to this type.

Attributes:
    alias: Credential alias/name used for lookup
    vault_path: Full path in the credential vault
    data: Raw credential data dictionary
    username: Extracted username (if present)
    password: Extracted password (if present)
    api_key: Extracted API key (if present)
    connection_string: Extracted connection string (if present)
    is_dynamic: Whether credential was dynamically generated
    expires_at: Expiration time for dynamic credentials


**Attributes:**

- `alias: str`
- `api_key: Optional[str]`
- `connection_string: Optional[str]`
- `data: Dict[str, Any]`
- `expires_at: Optional[datetime]`
- `is_dynamic: bool`
- `password: Optional[str]`
- `username: Optional[str]`
- `vault_path: str`

---

## casare_rpa.domain.repositories.project_repository

**File:** `src\casare_rpa\domain\repositories\project_repository.py`


Project repository interface.


### ProjectRepository

**Inherits from:** `ABC`


Repository interface for Project aggregate.

Defines the contract for project persistence operations.
Implementations can use file system, database, or cloud storage.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(project_id, remove_files)` | `None` | Delete project. |
| `async delete_scenario(project_id, scenario_id)` | `None` | Delete scenario from project. |
| `async exists(project_id)` | `bool` | Check if project exists. |
| `async get_all()` | `List[Project]` | Get all registered projects. |
| `async get_by_id(project_id)` | `Optional[Project]` | Get project by ID. |
| `async get_by_path(path)` | `Optional[Project]` | Get project by folder path. |
| `async get_global_credentials()` | `CredentialBindingsFile` | Get global credential bindings. |
| `async get_global_variables()` | `VariablesFile` | Get global variables. |
| `async get_project_credentials(project_id)` | `CredentialBindingsFile` | Get project-level credential bindings. |
| `async get_project_variables(project_id)` | `VariablesFile` | Get project-level variables. |
| `async get_projects_index()` | `ProjectsIndex` | Get the projects index (registry of all projects). |
| `async get_scenario(project_id, scenario_id)` | `Optional[Scenario]` | Get scenario by ID. |
| `async get_scenarios(project_id)` | `List[Scenario]` | Get all scenarios for a project. |
| `async save(project)` | `None` | Save or update project. |
| `async save_global_credentials(credentials)` | `None` | Save global credential bindings. |
| `async save_global_variables(variables)` | `None` | Save global variables. |
| `async save_project_credentials(project_id, credentials)` | `None` | Save project-level credential bindings. |
| `async save_project_variables(project_id, variables)` | `None` | Save project-level variables. |
| `async save_projects_index(index)` | `None` | Save the projects index. |
| `async save_scenario(project_id, scenario)` | `None` | Save scenario to project. |
| `async update_project_opened(project_id)` | `None` | Update last_opened timestamp for a project in the index. |

#### Method Details

##### `delete`

```python
async def delete(project_id: str, remove_files: bool = False) -> None
```

Delete project.

Args:
    project_id: Project ID to delete
    remove_files: If True, also delete project folder from disk

**Parameters:**

- `project_id: str` *(required)*
- `remove_files: bool = False`

##### `delete_scenario`

```python
async def delete_scenario(project_id: str, scenario_id: str) -> None
```

Delete scenario from project.

Args:
    project_id: Parent project ID
    scenario_id: Scenario ID to delete

**Parameters:**

- `project_id: str` *(required)*
- `scenario_id: str` *(required)*

##### `exists`

```python
async def exists(project_id: str) -> bool
```

Check if project exists.

Args:
    project_id: Project ID to check

Returns:
    True if project exists

**Parameters:**

- `project_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[Project]
```

Get all registered projects.

Returns:
    List of all projects from the index

##### `get_by_id`

```python
async def get_by_id(project_id: str) -> Optional[Project]
```

Get project by ID.

Args:
    project_id: Project ID (e.g., 'proj_a1b2c3d4')

Returns:
    Project if found, None otherwise

**Parameters:**

- `project_id: str` *(required)*

##### `get_by_path`

```python
async def get_by_path(path: Path) -> Optional[Project]
```

Get project by folder path.

Args:
    path: Path to project folder

Returns:
    Project if found, None otherwise

**Parameters:**

- `path: Path` *(required)*

##### `get_global_credentials`

```python
async def get_global_credentials() -> CredentialBindingsFile
```

Get global credential bindings.

Returns:
    CredentialBindingsFile (empty if not found)

##### `get_global_variables`

```python
async def get_global_variables() -> VariablesFile
```

Get global variables.

Returns:
    VariablesFile (empty if not found)

##### `get_project_credentials`

```python
async def get_project_credentials(project_id: str) -> CredentialBindingsFile
```

Get project-level credential bindings.

Args:
    project_id: Project ID

Returns:
    CredentialBindingsFile (empty if not found)

**Parameters:**

- `project_id: str` *(required)*

##### `get_project_variables`

```python
async def get_project_variables(project_id: str) -> VariablesFile
```

Get project-level variables.

Args:
    project_id: Project ID

Returns:
    VariablesFile (empty if not found)

**Parameters:**

- `project_id: str` *(required)*

##### `get_projects_index`

```python
async def get_projects_index() -> ProjectsIndex
```

Get the projects index (registry of all projects).

Returns:
    ProjectsIndex

##### `get_scenario`

```python
async def get_scenario(project_id: str, scenario_id: str) -> Optional[Scenario]
```

Get scenario by ID.

Args:
    project_id: Parent project ID
    scenario_id: Scenario ID

Returns:
    Scenario if found, None otherwise

**Parameters:**

- `project_id: str` *(required)*
- `scenario_id: str` *(required)*

##### `get_scenarios`

```python
async def get_scenarios(project_id: str) -> List[Scenario]
```

Get all scenarios for a project.

Args:
    project_id: Project ID

Returns:
    List of scenarios

**Parameters:**

- `project_id: str` *(required)*

##### `save`

```python
async def save(project: Project) -> None
```

Save or update project.

Creates folder structure if new project.
Updates modified timestamp automatically.

Args:
    project: Project to save (must have path set)

**Parameters:**

- `project: Project` *(required)*

##### `save_global_credentials`

```python
async def save_global_credentials(credentials: CredentialBindingsFile) -> None
```

Save global credential bindings.

Args:
    credentials: Credentials to save

**Parameters:**

- `credentials: CredentialBindingsFile` *(required)*

##### `save_global_variables`

```python
async def save_global_variables(variables: VariablesFile) -> None
```

Save global variables.

Args:
    variables: Variables to save

**Parameters:**

- `variables: VariablesFile` *(required)*

##### `save_project_credentials`

```python
async def save_project_credentials(project_id: str, credentials: CredentialBindingsFile) -> None
```

Save project-level credential bindings.

Args:
    project_id: Project ID
    credentials: Credentials to save

**Parameters:**

- `project_id: str` *(required)*
- `credentials: CredentialBindingsFile` *(required)*

##### `save_project_variables`

```python
async def save_project_variables(project_id: str, variables: VariablesFile) -> None
```

Save project-level variables.

Args:
    project_id: Project ID
    variables: Variables to save

**Parameters:**

- `project_id: str` *(required)*
- `variables: VariablesFile` *(required)*

##### `save_projects_index`

```python
async def save_projects_index(index: ProjectsIndex) -> None
```

Save the projects index.

Args:
    index: ProjectsIndex to save

**Parameters:**

- `index: ProjectsIndex` *(required)*

##### `save_scenario`

```python
async def save_scenario(project_id: str, scenario: Scenario) -> None
```

Save scenario to project.

Args:
    project_id: Parent project ID
    scenario: Scenario to save

**Parameters:**

- `project_id: str` *(required)*
- `scenario: Scenario` *(required)*

##### `update_project_opened`

```python
async def update_project_opened(project_id: str) -> None
```

Update last_opened timestamp for a project in the index.

Args:
    project_id: Project ID

**Parameters:**

- `project_id: str` *(required)*

---

## casare_rpa.domain.schemas.property_schema

**File:** `src\casare_rpa\domain\schemas\property_schema.py`


Property schema system for declarative node configuration.

Provides PropertyDef and NodeSchema for defining node properties
once and auto-generating config, widgets, and validation.


### NodeSchema

**Decorators:** `@dataclass`


Schema for a node's configuration properties.

Attached to node classes via @node_schema decorator.


**Attributes:**

- `properties: List[PropertyDef]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_default_config()` | `Dict[str, Any]` | Generate default configuration dictionary from schema. |
| `get_property(name)` | `Optional[PropertyDef]` | Get property definition by name. |
| `validate_config(config)` | `Tuple[bool, str]` | Validate configuration against schema. |

#### Method Details

##### `get_default_config`

```python
def get_default_config() -> Dict[str, Any]
```

Generate default configuration dictionary from schema.

Returns:
    Dict mapping property names to default values

##### `get_property`

```python
def get_property(name: str) -> Optional[PropertyDef]
```

Get property definition by name.

Args:
    name: Property name

Returns:
    PropertyDef if found, None otherwise

**Parameters:**

- `name: str` *(required)*

##### `validate_config`

```python
def validate_config(config: Dict[str, Any]) -> Tuple[bool, str]
```

Validate configuration against schema.

Args:
    config: Configuration dictionary to validate

Returns:
    Tuple of (is_valid, error_message)

**Parameters:**

- `config: Dict[str, Any]` *(required)*

### PropertyDef

**Decorators:** `@dataclass`


Definition of a single node property.

Used in @node_schema decorator to declaratively define
node configuration properties.


**Attributes:**

- `choices: Optional[List[str]]`
- `default: Any`
- `label: Optional[str]`
- `max_value: Optional[float]`
- `min_value: Optional[float]`
- `name: str`
- `placeholder: str`
- `readonly: bool`
- `required: bool`
- `tab: str`
- `tooltip: str`
- `type: PropertyType`
- `widget_class: Optional[Type]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Auto-generate label if not provided. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Auto-generate label if not provided.

---

## casare_rpa.domain.schemas.property_types

**File:** `src\casare_rpa\domain\schemas\property_types.py`


Property types for node configuration schema.

Defines the types of properties that can be used in node schemas.


### PropertyType

**Inherits from:** `str`, `Enum`


Types of properties for node configuration.


**Attributes:**

- `ANY: str`
- `BOOLEAN: str`
- `CHOICE: str`
- `CODE: str`
- `COLOR: str`
- `CUSTOM: str`
- `DATE: str`
- `DATETIME: str`
- `DIRECTORY_PATH: str`
- `FILE_PATH: str`
- `FILE_PATTERN: str`
- `FLOAT: str`
- `INTEGER: str`
- `JSON: str`
- `LIST: str`
- `MULTI_CHOICE: str`
- `SELECTOR: str`
- `STRING: str`
- `TEXT: str`
- `TIME: str`

---

## casare_rpa.domain.services.execution_orchestrator

**File:** `src\casare_rpa\domain\services\execution_orchestrator.py`


CasareRPA - Domain Service: Execution Orchestrator
Pure business logic for workflow execution orchestration.

This is a PURE domain service with NO infrastructure dependencies:
- NO async/await
- NO Playwright
- NO EventBus
- NO resource management

Handles:
- Connection traversal logic
- Control flow decisions (if/else, loops, branches)
- Execution path calculation (Run-To-Node feature)
- Dependency analysis


### ExecutionOrchestrator


Domain service for workflow execution logic.

Responsibilities:
- Determine execution order based on connections
- Handle control flow (loops, branches, try/catch)
- Track execution path
- Calculate subgraphs for Run-To-Node

Does NOT:
- Execute nodes (that's infrastructure)
- Manage resources (that's infrastructure)
- Emit events (that's application layer)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow)` | `None` | Initialize execution orchestrator. |
| `__repr__()` | `str` | String representation. |
| `build_dependency_graph()` | `Dict[NodeId, Set[NodeId]]` | Build execution dependency graph. |
| `calculate_execution_path(start_node_id, target_node_id)` | `Set[NodeId]` | Calculate the execution path from start to target (or all no... |
| `find_all_start_nodes()` | `List[NodeId]` | Find all StartNodes in workflow for parallel execution. |
| `find_loop_body_nodes(loop_node_id)` | `Set[NodeId]` | Find all nodes reachable from a loop's body output. |
| `find_start_node()` | `Optional[NodeId]` | Find the workflow entry point (StartNode or TriggerNode). |
| `find_trigger_node()` | `Optional[NodeId]` | Find the trigger node in workflow (if any). |
| `find_try_body_nodes(try_node_id)` | `Set[NodeId]` | Find all nodes reachable from a try node's try_body output. |
| `get_all_nodes()` | `List[NodeId]` | Get all node IDs in the workflow. |
| `get_next_nodes(current_node_id, execution_result)` | `List[NodeId]` | Determine next nodes to execute based on connections and res... |
| `get_node_type(node_id)` | `str` | Get the type of a node. |
| `handle_control_flow(node_id, result)` | `Optional[str]` | Process control flow signals (break/continue/return). |
| `is_control_flow_node(node_id)` | `bool` | Check if a node is a control flow node. |
| `is_reachable(start_node_id, target_node_id)` | `bool` | Check if target node is reachable from start node. |
| `is_trigger_node(node_id)` | `bool` | Check if a node is a trigger node. |
| `should_stop_on_error(error, settings)` | `bool` | Decide if error should halt execution. |
| `validate_execution_order()` | `tuple[bool, List[str]]` | Ensure no circular dependencies in workflow. |

#### Method Details

##### `__init__`

```python
def __init__(workflow: WorkflowSchema) -> None
```

Initialize execution orchestrator.

Args:
    workflow: Workflow schema with nodes and connections

**Parameters:**

- `workflow: WorkflowSchema` *(required)*

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `build_dependency_graph`

```python
def build_dependency_graph() -> Dict[NodeId, Set[NodeId]]
```

Build execution dependency graph.

Creates a directed graph where each node maps to its dependencies
(nodes that must execute before it).

Returns:
    Dictionary mapping node_id -> set of dependency node_ids

##### `calculate_execution_path`

```python
def calculate_execution_path(start_node_id: NodeId, target_node_id: Optional[NodeId] = None) -> Set[NodeId]
```

Calculate the execution path from start to target (or all nodes).

Uses BFS to find all nodes reachable from start.
If target is specified, finds all nodes on paths to target (subgraph).

Args:
    start_node_id: Starting node ID
    target_node_id: Optional target node ID (Run-To-Node)

Returns:
    Set of node IDs in the execution path

**Parameters:**

- `start_node_id: NodeId` *(required)*
- `target_node_id: Optional[NodeId] = None`

##### `find_all_start_nodes`

```python
def find_all_start_nodes() -> List[NodeId]
```

Find all StartNodes in workflow for parallel execution.

Unlike find_start_node() which returns the first one, this returns
all StartNodes to enable multi-workflow parallel execution.

Returns:
    List of all StartNode IDs in the workflow

##### `find_loop_body_nodes`

```python
def find_loop_body_nodes(loop_node_id: NodeId) -> Set[NodeId]
```

Find all nodes reachable from a loop's body output.

Used to track which nodes are inside a loop for break/continue handling.

Args:
    loop_node_id: ID of loop start node

Returns:
    Set of node IDs in loop body

**Parameters:**

- `loop_node_id: NodeId` *(required)*

##### `find_start_node`

```python
def find_start_node() -> Optional[NodeId]
```

Find the workflow entry point (StartNode or TriggerNode).

Trigger nodes are also valid entry points as they start workflows.

Returns:
    Node ID of entry point, or None if not found

##### `find_trigger_node`

```python
def find_trigger_node() -> Optional[NodeId]
```

Find the trigger node in workflow (if any).

Returns:
    Node ID of trigger node, or None if not found

##### `find_try_body_nodes`

```python
def find_try_body_nodes(try_node_id: NodeId) -> Set[NodeId]
```

Find all nodes reachable from a try node's try_body output.

Used to track which nodes are inside a try block for error routing.

Args:
    try_node_id: ID of try node

Returns:
    Set of node IDs in try body

**Parameters:**

- `try_node_id: NodeId` *(required)*

##### `get_all_nodes`

```python
def get_all_nodes() -> List[NodeId]
```

Get all node IDs in the workflow.

Returns:
    List of all node IDs

##### `get_next_nodes`

```python
def get_next_nodes(current_node_id: NodeId, execution_result: Optional[Dict[str, Any]] = None) -> List[NodeId]
```

Determine next nodes to execute based on connections and result.

Validates that specified ports have connections and logs warnings if not.

Handles:
- Dynamic routing (next_nodes in result)
- Control flow (break, continue)
- Default routing (all exec_out connections)

Args:
    current_node_id: ID of current node
    execution_result: Result from node execution

Returns:
    List of next node IDs to execute

**Parameters:**

- `current_node_id: NodeId` *(required)*
- `execution_result: Optional[Dict[str, Any]] = None`

##### `get_node_type`

```python
def get_node_type(node_id: NodeId) -> str
```

Get the type of a node.

Args:
    node_id: Node ID

Returns:
    Node type name, or empty string if not found

**Parameters:**

- `node_id: NodeId` *(required)*

##### `handle_control_flow`

```python
def handle_control_flow(node_id: NodeId, result: Dict[str, Any]) -> Optional[str]
```

Process control flow signals (break/continue/return).

Args:
    node_id: ID of node that returned result
    result: Execution result

Returns:
    Control flow signal name or None

**Parameters:**

- `node_id: NodeId` *(required)*
- `result: Dict[str, Any]` *(required)*

##### `is_control_flow_node`

```python
def is_control_flow_node(node_id: NodeId) -> bool
```

Check if a node is a control flow node.

Control flow nodes affect execution routing:
- IfNode, SwitchNode
- ForLoopStartNode, WhileLoopStartNode
- BreakNode, ContinueNode
- TryNode, CatchNode

Args:
    node_id: Node ID

Returns:
    True if node is a control flow node

**Parameters:**

- `node_id: NodeId` *(required)*

##### `is_reachable`

```python
def is_reachable(start_node_id: NodeId, target_node_id: NodeId) -> bool
```

Check if target node is reachable from start node.

Uses BFS to determine reachability.

Args:
    start_node_id: Starting node ID
    target_node_id: Target node ID

Returns:
    True if target is reachable from start

**Parameters:**

- `start_node_id: NodeId` *(required)*
- `target_node_id: NodeId` *(required)*

##### `is_trigger_node`

```python
def is_trigger_node(node_id: NodeId) -> bool
```

Check if a node is a trigger node.

Args:
    node_id: Node ID to check

Returns:
    True if the node is a trigger node

**Parameters:**

- `node_id: NodeId` *(required)*

##### `should_stop_on_error`

```python
def should_stop_on_error(error: Exception, settings: Dict[str, Any]) -> bool
```

Decide if error should halt execution.

Business logic for error handling:
- Check continue_on_error setting
- Check error severity
- Check if error is in try block

Args:
    error: Exception that occurred
    settings: Workflow settings

Returns:
    True if execution should stop

**Parameters:**

- `error: Exception` *(required)*
- `settings: Dict[str, Any]` *(required)*

##### `validate_execution_order`

```python
def validate_execution_order() -> tuple[bool, List[str]]
```

Ensure no circular dependencies in workflow.

Uses topological sort to detect cycles.

Returns:
    Tuple of (is_valid, list of error messages)

---

## casare_rpa.domain.services.project_context

**File:** `src\casare_rpa\domain\services\project_context.py`


CasareRPA - Domain Service: Project Context
Runtime context for project-scoped resources during workflow execution.

This is a domain service that manages variable and credential scoping
across global, project, and scenario levels.


### ProjectContext


Domain service providing runtime context for project-scoped resources.

Manages variable and credential resolution with proper scoping:
- Global variables (lowest priority)
- Project variables
- Scenario variables (highest priority)

The context is immutable after creation - it captures a snapshot
of the project state at the time of workflow execution.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(project, scenario, project_variables, ...)` | `None` | Initialize project context. |
| `__repr__()` | `str` | String representation. |
| `get_all_credential_aliases()` | `Dict[str, str]` | Get all available credential aliases with their Vault paths. |
| `get_default_browser()` | `str` | Get default browser setting from project. |
| `get_global_variables()` | `Dict[str, Any]` | Get global variable default values. |
| `get_merged_variables()` | `Dict[str, Any]` | Get merged variables from all scopes. |
| `get_project_variables()` | `Dict[str, Any]` | Get project variable default values. |
| `get_retry_count()` | `int` | Get retry count setting from project. |
| `get_scenario_variables()` | `Dict[str, Any]` | Get scenario variable values. |
| `get_stop_on_error()` | `bool` | Get stop-on-error setting from project. |
| `get_timeout()` | `int` | Get execution timeout in seconds. |
| `get_variable(name, default)` | `Any` | Get a variable value with scope fallback. |
| `project()` | `Project` | Get the project. |
| `project_id()` | `str` | Get the project ID. |
| `project_name()` | `str` | Get the project name. |
| `resolve_credential_path(alias)` | `Optional[str]` | Resolve a credential alias to its Vault path. |
| `scenario()` | `Optional[Scenario]` | Get the scenario (if any). |
| `scenario_id()` | `Optional[str]` | Get the scenario ID (if any). |
| `scenario_name()` | `Optional[str]` | Get the scenario name (if any). |

#### Method Details

##### `__init__`

```python
def __init__(project: Project, scenario: Optional[Scenario] = None, project_variables: Optional[VariablesFile] = None, project_credentials: Optional[CredentialBindingsFile] = None, global_variables: Optional[VariablesFile] = None, global_credentials: Optional[CredentialBindingsFile] = None) -> None
```

Initialize project context.

Args:
    project: The project being executed
    scenario: Optional scenario being executed
    project_variables: Project-scoped variables
    project_credentials: Project-scoped credential bindings
    global_variables: Global variables
    global_credentials: Global credential bindings

**Parameters:**

- `project: Project` *(required)*
- `scenario: Optional[Scenario] = None`
- `project_variables: Optional[VariablesFile] = None`
- `project_credentials: Optional[CredentialBindingsFile] = None`
- `global_variables: Optional[VariablesFile] = None`
- `global_credentials: Optional[CredentialBindingsFile] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `get_all_credential_aliases`

```python
def get_all_credential_aliases() -> Dict[str, str]
```

Get all available credential aliases with their Vault paths.

Merges global, project, and scenario bindings with proper priority.

Returns:
    Dictionary of alias -> vault_path

##### `get_default_browser`

```python
def get_default_browser() -> str
```

Get default browser setting from project.

Returns:
    Browser name (chromium, firefox, webkit)

##### `get_global_variables`

```python
def get_global_variables() -> Dict[str, Any]
```

Get global variable default values.

Returns:
    Dictionary of variable name -> default value

##### `get_merged_variables`

```python
def get_merged_variables() -> Dict[str, Any]
```

Get merged variables from all scopes.

Priority (highest to lowest):
- Scenario variable values
- Project variable defaults
- Global variable defaults

Returns:
    Dictionary of variable name -> value

##### `get_project_variables`

```python
def get_project_variables() -> Dict[str, Any]
```

Get project variable default values.

Returns:
    Dictionary of variable name -> default value

##### `get_retry_count`

```python
def get_retry_count() -> int
```

Get retry count setting from project.

Returns:
    Number of retries for failed operations

##### `get_scenario_variables`

```python
def get_scenario_variables() -> Dict[str, Any]
```

Get scenario variable values.

Returns:
    Dictionary of variable name -> value

##### `get_stop_on_error`

```python
def get_stop_on_error() -> bool
```

Get stop-on-error setting from project.

Returns:
    True if workflow should stop on error

##### `get_timeout`

```python
def get_timeout() -> int
```

Get execution timeout in seconds.

Returns scenario override if set, otherwise project default.

Returns:
    Timeout in seconds

##### `get_variable`

```python
def get_variable(name: str, default: Any = None) -> Any
```

Get a variable value with scope fallback.

Checks scenario, project, then global.

Args:
    name: Variable name
    default: Default value if not found

Returns:
    Variable value or default

**Parameters:**

- `name: str` *(required)*
- `default: Any = None`

##### `project`

```python
@property
def project() -> Project
```

Get the project.

##### `project_id`

```python
@property
def project_id() -> str
```

Get the project ID.

##### `project_name`

```python
@property
def project_name() -> str
```

Get the project name.

##### `resolve_credential_path`

```python
def resolve_credential_path(alias: str) -> Optional[str]
```

Resolve a credential alias to its Vault path.

Checks scenario, project, then global bindings.

Args:
    alias: Credential alias to resolve

Returns:
    Vault path if found, None otherwise

**Parameters:**

- `alias: str` *(required)*

##### `scenario`

```python
@property
def scenario() -> Optional[Scenario]
```

Get the scenario (if any).

##### `scenario_id`

```python
@property
def scenario_id() -> Optional[str]
```

Get the scenario ID (if any).

##### `scenario_name`

```python
@property
def scenario_name() -> Optional[str]
```

Get the scenario name (if any).

---

## casare_rpa.domain.services.variable_resolver

**File:** `src\casare_rpa\domain\services\variable_resolver.py`


Variable Resolution Utility for CasareRPA.

Provides functionality to resolve {{variable_name}} patterns in strings
with actual variable values from the execution context.


### Functions

#### `extract_variable_names`

```python
def extract_variable_names(value: str) -> list
```

Extract all variable names referenced in a string.

Args:
    value: String potentially containing {{variable}} patterns

Returns:
    List of variable names found in the string

Examples:
    >>> extract_variable_names("{{url}}/{{path}}")
    ["url", "path"]

#### `has_variables`

```python
def has_variables(value: str) -> bool
```

Check if a string contains any {{variable}} patterns.

Args:
    value: String to check

Returns:
    True if the string contains variable references

#### `resolve_dict_variables`

```python
def resolve_dict_variables(data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]
```

Resolve variables in all string values of a dictionary.

Args:
    data: Dictionary with potentially templated string values
    variables: Dict of variable name -> value

Returns:
    New dictionary with all string values resolved

#### `resolve_variables`

```python
def resolve_variables(value: Any, variables: Dict[str, Any]) -> Any
```

Replace {{variable_name}} patterns with actual values from variables dict.

This function supports the UiPath/Power Automate style variable substitution
where users can reference global variables in node properties using
the {{variable_name}} syntax.

Args:
    value: The value to resolve (only strings are processed)
    variables: Dict of variable name -> value

Returns:
    The resolved value with all {{variable}} patterns replaced.
    Non-string values are returned unchanged.

Examples:
    >>> resolve_variables("https://{{website}}", {"website": "google.com"})
    "https://google.com"

    >>> resolve_variables("Hello {{name}}!", {"name": "World"})
    "Hello World!"

    >>> resolve_variables(123, {"x": "y"})  # Non-string unchanged
    123


---

## casare_rpa.domain.validation.rules

**File:** `src\casare_rpa\domain\validation\rules.py`


CasareRPA - Validation Rules Module

Contains validation rules, constraints, and helper functions for connection parsing
and port type checking.


### Functions

#### `find_entry_points_and_reachable`

```python
def find_entry_points_and_reachable(nodes: Dict[str, Any], connections: List[Dict[str, Any]]) -> Tuple[List[str], Set[str]]
```

Find workflow entry points and all reachable nodes.

Entry points are nodes that:
1. Are named/typed as StartNode, OR
2. Have no incoming exec connections

Returns:
    Tuple of (entry_point_ids, reachable_node_ids)

#### `find_reachable_nodes`

```python
def find_reachable_nodes(nodes: Dict[str, Any], connections: List[Dict[str, Any]]) -> Set[str]
```

Legacy wrapper - find all reachable nodes from entry points.

#### `has_circular_dependency`

```python
def has_circular_dependency(nodes: Dict[str, Any], connections: List[Dict[str, Any]]) -> bool
```

Check for circular dependencies using iterative DFS on exec connections.

Uses an iterative approach (stack-based) instead of recursion to avoid
RecursionError on large workflows (500+ nodes).

#### `is_exec_input_port`

```python
def is_exec_input_port(port_name: str) -> bool
```

Check if a port is an execution INPUT port (receives exec flow).

#### `is_exec_port`

```python
def is_exec_port(port_name: str) -> bool
```

Check if a port name indicates an execution flow port.

#### `parse_connection`

```python
def parse_connection(conn: Dict[str, Any]) -> Optional[Dict[str, str]]
```

Parse a connection from any format into a normalized structure.

Handles:
- Format 1: {"source_node": "...", "source_port": "...", "target_node": "...", "target_port": "..."}
- Format 2: {"out": ["node_id", "port"], "in": ["node_id", "port"]}

Returns:
    Normalized dict with source_node, source_port, target_node, target_port
    or None if parsing fails


---

## casare_rpa.domain.validation.schemas

**File:** `src\casare_rpa\domain\validation\schemas.py`


CasareRPA - Validation Schemas Module

Contains schema definitions, constants, and type mappings for validation.


### Functions

#### `get_valid_node_types`

```python
def get_valid_node_types() -> Set[str]
```

Get the set of valid node types.


---

## casare_rpa.domain.validation.types

**File:** `src\casare_rpa\domain\validation\types.py`


CasareRPA - Validation Types Module

Contains type definitions for validation: enums, dataclasses, and type aliases.


### ValidationIssue

**Decorators:** `@dataclass`


Represents a single validation issue.


**Attributes:**

- `code: str`
- `location: Optional[str]`
- `message: str`
- `severity: ValidationSeverity`
- `suggestion: Optional[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### ValidationResult

**Decorators:** `@dataclass`


Result of a validation operation.


**Attributes:**

- `is_valid: bool`
- `issues: List[ValidationIssue]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `add_error(code, message, location, ...)` | `None` | Add an error-level issue. |
| `add_info(code, message, location)` | `None` | Add an info-level issue. |
| `add_warning(code, message, location, ...)` | `None` | Add a warning-level issue. |
| `error_count()` | `int` | Count of errors. |
| `errors()` | `List[ValidationIssue]` | Get only error-level issues. |
| `format_summary()` | `str` | Format a human-readable summary. |
| `merge(other)` | `None` | Merge another validation result into this one. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |
| `warning_count()` | `int` | Count of warnings. |
| `warnings()` | `List[ValidationIssue]` | Get only warning-level issues. |

#### Method Details

##### `add_error`

```python
def add_error(code: str, message: str, location: Optional[str] = None, suggestion: Optional[str] = None) -> None
```

Add an error-level issue.

**Parameters:**

- `code: str` *(required)*
- `message: str` *(required)*
- `location: Optional[str] = None`
- `suggestion: Optional[str] = None`

##### `add_info`

```python
def add_info(code: str, message: str, location: Optional[str] = None) -> None
```

Add an info-level issue.

**Parameters:**

- `code: str` *(required)*
- `message: str` *(required)*
- `location: Optional[str] = None`

##### `add_warning`

```python
def add_warning(code: str, message: str, location: Optional[str] = None, suggestion: Optional[str] = None) -> None
```

Add a warning-level issue.

**Parameters:**

- `code: str` *(required)*
- `message: str` *(required)*
- `location: Optional[str] = None`
- `suggestion: Optional[str] = None`

##### `error_count`

```python
@property
def error_count() -> int
```

Count of errors.

##### `errors`

```python
@property
def errors() -> List[ValidationIssue]
```

Get only error-level issues.

##### `format_summary`

```python
def format_summary() -> str
```

Format a human-readable summary.

##### `merge`

```python
def merge(other: 'ValidationResult') -> None
```

Merge another validation result into this one.

**Parameters:**

- `other: 'ValidationResult'` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

##### `warning_count`

```python
@property
def warning_count() -> int
```

Count of warnings.

##### `warnings`

```python
@property
def warnings() -> List[ValidationIssue]
```

Get only warning-level issues.

### ValidationSeverity

**Inherits from:** `Enum`


Severity level of validation issues.


**Attributes:**

- `ERROR: auto`
- `INFO: auto`
- `WARNING: auto`

---

## casare_rpa.domain.validation.validators

**File:** `src\casare_rpa\domain\validation\validators.py`


CasareRPA - Validators Module

Contains validation functions for workflows, nodes, and connections.


### Functions

#### `quick_validate`

```python
def quick_validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]
```

Quick validation returning simple tuple for backward compatibility.

Args:
    data: Workflow data to validate

Returns:
    Tuple of (is_valid, list of error messages)

#### `validate_connections`

```python
def validate_connections(connections: List[Dict[str, str]], node_ids: Set[str]) -> ValidationResult
```

Validate workflow connections.

Args:
    connections: List of connection dictionaries
    node_ids: Set of valid node IDs

Returns:
    ValidationResult for connections

#### `validate_node`

```python
def validate_node(node_id: str, node_data: Dict[str, Any]) -> ValidationResult
```

Validate a single node's data structure.

Args:
    node_id: Node identifier
    node_data: Node data dictionary

Returns:
    ValidationResult for this node

#### `validate_workflow`

```python
def validate_workflow(data: Dict[str, Any]) -> ValidationResult
```

Validate a complete workflow data structure.

Args:
    data: Serialized workflow dictionary

Returns:
    ValidationResult with all issues found


---

## casare_rpa.domain.value_objects.log_entry

**File:** `src\casare_rpa\domain\value_objects\log_entry.py`


LogEntry Value Object for Robot Log Streaming.

Defines immutable log entry value objects for streaming robot logs
to the orchestrator with 30-day retention policy.


### LogBatch

**Decorators:** `@dataclass`


Batch of log entries for efficient transmission.

Attributes:
    robot_id: ID of the robot sending the batch.
    entries: List of log entries.
    sequence: Sequence number for ordering/deduplication.


**Attributes:**

- `entries: tuple`
- `robot_id: str`
- `sequence: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data, tenant_id)` | `'LogBatch'` | Deserialize from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary for WebSocket transmission. |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any], tenant_id: str) -> 'LogBatch'
```

Deserialize from dictionary.

Args:
    data: Dictionary with batch data.
    tenant_id: Tenant ID to assign to entries.

Returns:
    LogBatch instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*
- `tenant_id: str` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary for WebSocket transmission.

Returns:
    Dictionary representation.

### LogEntry

**Decorators:** `@dataclass`


Immutable log entry value object.

Represents a single log message from a robot, including
metadata for routing and retention.

Attributes:
    id: Unique identifier for the log entry.
    robot_id: ID of the robot that generated this log.
    tenant_id: Tenant ID for multi-tenancy isolation.
    timestamp: When the log was generated.
    level: Log severity level.
    message: The log message content.
    source: Optional source identifier (module, node type, etc.).
    extra: Optional additional structured data.


**Attributes:**

- `extra: Optional[LogExtraData]`
- `id: str`
- `level: LogLevel`
- `message: str`
- `robot_id: str`
- `source: Optional[str]`
- `tenant_id: str`
- `timestamp: datetime`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Validate log entry data. |
| `from_dict(data)` | `'LogEntry'` | Deserialize from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Validate log entry data.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'LogEntry'
```

Deserialize from dictionary.

Args:
    data: Dictionary with log entry fields.

Returns:
    LogEntry instance.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

Returns:
    Dictionary representation suitable for JSON serialization.

### LogLevel

**Inherits from:** `Enum`


Log severity level.


**Attributes:**

- `CRITICAL: str`
- `DEBUG: str`
- `ERROR: str`
- `INFO: str`
- `TRACE: str`
- `WARNING: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__ge__(other)` | `bool` | Compare severity levels. |
| `__gt__(other)` | `bool` | Compare severity levels. |
| `__le__(other)` | `bool` | Compare severity levels. |
| `__lt__(other)` | `bool` | Compare severity levels. |
| `from_string(level)` | `'LogLevel'` | Convert string to LogLevel. |
| `severity()` | `int` | Get numeric severity (higher = more severe). |

#### Method Details

##### `__ge__`

```python
def __ge__(other: 'LogLevel') -> bool
```

Compare severity levels.

**Parameters:**

- `other: 'LogLevel'` *(required)*

##### `__gt__`

```python
def __gt__(other: 'LogLevel') -> bool
```

Compare severity levels.

**Parameters:**

- `other: 'LogLevel'` *(required)*

##### `__le__`

```python
def __le__(other: 'LogLevel') -> bool
```

Compare severity levels.

**Parameters:**

- `other: 'LogLevel'` *(required)*

##### `__lt__`

```python
def __lt__(other: 'LogLevel') -> bool
```

Compare severity levels.

**Parameters:**

- `other: 'LogLevel'` *(required)*

##### `from_string`

```python
@classmethod
def from_string(level: str) -> 'LogLevel'
```

Convert string to LogLevel.

Args:
    level: Level string (case-insensitive).

Returns:
    LogLevel enum value.

**Parameters:**

- `level: str` *(required)*

##### `severity`

```python
@property
def severity() -> int
```

Get numeric severity (higher = more severe).

### LogQuery

**Decorators:** `@dataclass`


Query parameters for searching logs.

Attributes:
    robot_id: Filter by robot ID (optional).
    tenant_id: Filter by tenant ID (required for multi-tenancy).
    start_time: Start of time range.
    end_time: End of time range.
    min_level: Minimum log level to include.
    source: Filter by source.
    search_text: Full-text search in message.
    limit: Maximum number of results.
    offset: Pagination offset.


**Attributes:**

- `end_time: Optional[datetime]`
- `limit: int`
- `min_level: LogLevel`
- `offset: int`
- `robot_id: Optional[str]`
- `search_text: Optional[str]`
- `source: Optional[str]`
- `start_time: Optional[datetime]`
- `tenant_id: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Validate query parameters. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Validate query parameters.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

Returns:
    Dictionary representation.

### LogStats

**Decorators:** `@dataclass`


Log statistics summary.

Attributes:
    tenant_id: Tenant ID.
    robot_id: Robot ID (optional, if robot-specific).
    total_count: Total log entries.
    by_level: Count by log level.
    oldest_log: Timestamp of oldest log.
    newest_log: Timestamp of newest log.
    storage_bytes: Estimated storage usage.


**Attributes:**

- `by_level: Dict[str, int]`
- `newest_log: Optional[datetime]`
- `oldest_log: Optional[datetime]`
- `robot_id: Optional[str]`
- `storage_bytes: int`
- `tenant_id: str`
- `total_count: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

Returns:
    Dictionary representation.

---

## casare_rpa.domain.value_objects.port

**File:** `src\casare_rpa\domain\value_objects\port.py`


CasareRPA - Port Value Object

Port is an immutable value object representing a connection point on a node.


### Port


Represents a single input or output port on a node.

This is a value object - once created, its core properties are immutable.
Only the value can be changed during workflow execution.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__eq__(other)` | `bool` | Check equality based on immutable properties. |
| `__hash__()` | `int` | Hash based on immutable properties. |
| `__init__(name, port_type, data_type, ...)` | `None` | Initialize a port. |
| `__repr__()` | `str` | String representation of port. |
| `data_type()` | `DataType` | Get data type (immutable). |
| `from_dict(data)` | `'Port'` | Create a Port from dictionary representation. |
| `get_value()` | `Any` | Get the port's value. |
| `label()` | `str` | Get display label (immutable). |
| `name()` | `str` | Get port name (immutable). |
| `port_type()` | `PortType` | Get port type (immutable). |
| `required()` | `bool` | Check if port is required (immutable). |
| `set_value(value)` | `None` | Set the port's value. |
| `to_dict()` | `PortDefinition` | Serialize port to dictionary. |

#### Method Details

##### `__eq__`

```python
def __eq__(other: object) -> bool
```

Check equality based on immutable properties.

Args:
    other: Other object to compare

Returns:
    True if ports have same immutable properties

**Parameters:**

- `other: object` *(required)*

##### `__hash__`

```python
def __hash__() -> int
```

Hash based on immutable properties.

##### `__init__`

```python
def __init__(name: str, port_type: PortType, data_type: DataType, label: Optional[str] = None, required: bool = True) -> None
```

Initialize a port.

Args:
    name: Unique port identifier within the node (non-empty, alphanumeric/underscore)
    port_type: Type of port (INPUT, OUTPUT, etc.)
    data_type: Data type this port accepts/provides
    label: Display label (defaults to name)
    required: Whether this port must be connected

Raises:
    ValueError: If name is empty, invalid format, or too long

**Parameters:**

- `name: str` *(required)*
- `port_type: PortType` *(required)*
- `data_type: DataType` *(required)*
- `label: Optional[str] = None`
- `required: bool = True`

##### `__repr__`

```python
def __repr__() -> str
```

String representation of port.

##### `data_type`

```python
@property
def data_type() -> DataType
```

Get data type (immutable).

##### `from_dict`

```python
@classmethod
def from_dict(data: PortDefinition) -> 'Port'
```

Create a Port from dictionary representation.

Args:
    data: Dictionary containing port definition

Returns:
    Port instance

**Parameters:**

- `data: PortDefinition` *(required)*

##### `get_value`

```python
def get_value() -> Any
```

Get the port's value.

##### `label`

```python
@property
def label() -> str
```

Get display label (immutable).

##### `name`

```python
@property
def name() -> str
```

Get port name (immutable).

##### `port_type`

```python
@property
def port_type() -> PortType
```

Get port type (immutable).

##### `required`

```python
@property
def required() -> bool
```

Check if port is required (immutable).

##### `set_value`

```python
def set_value(value: Any) -> None
```

Set the port's value.

**Parameters:**

- `value: Any` *(required)*

##### `to_dict`

```python
def to_dict() -> PortDefinition
```

Serialize port to dictionary.

Returns:
    Dictionary representation of the port

---

## casare_rpa.domain.value_objects.types

**File:** `src\casare_rpa\domain\value_objects\types.py`


CasareRPA - Domain Layer Type Definitions

This module defines core value objects for the domain layer:
- Enums: DataType, PortType, NodeStatus, ExecutionMode, EventType, ErrorCode
- Type aliases: NodeId, PortId, Connection, NodeConfig, etc.
- Constants: SCHEMA_VERSION, DEFAULT_TIMEOUT, etc.

All types here are framework-agnostic and represent pure domain concepts.


### DataType

**Inherits from:** `Enum`


Data types that can flow between nodes.


**Attributes:**

- `ANY: auto`
- `BOOLEAN: auto`
- `BROWSER: auto`
- `DB_CONNECTION: auto`
- `DESKTOP_ELEMENT: auto`
- `DICT: auto`
- `DOCUMENT: auto`
- `ELEMENT: auto`
- `EXEC: auto`
- `FLOAT: auto`
- `INTEGER: auto`
- `LIST: auto`
- `OBJECT: auto`
- `PAGE: auto`
- `STRING: auto`
- `WINDOW: auto`
- `WORKBOOK: auto`
- `WORKSHEET: auto`

### ErrorCode

**Inherits from:** `Enum`


Standardized error codes for consistent error handling across the application.

Error codes are grouped by category:
- 1xxx: General errors
- 2xxx: Browser/Web errors
- 3xxx: Desktop automation errors
- 4xxx: Data/Validation errors
- 5xxx: Configuration errors
- 6xxx: Network errors
- 7xxx: Resource errors


**Attributes:**

- `API_ERROR: int`
- `APPLICATION_LAUNCH_FAILED: int`
- `APPLICATION_NOT_RESPONDING: int`
- `BROWSER_CLOSED: int`
- `BROWSER_LAUNCH_FAILED: int`
- `BROWSER_NOT_FOUND: int`
- `CANCELLED: int`
- `CLICK_FAILED: int`
- `CONFIG_INVALID: int`
- `CONFIG_MISSING_KEY: int`
- `CONFIG_NOT_FOUND: int`
- `CONNECTION_REFUSED: int`
- `CONNECTION_TIMEOUT: int`
- `DESKTOP_ACTION_FAILED: int`
- `DESKTOP_ELEMENT_NOT_FOUND: int`
- `DESKTOP_ELEMENT_STALE: int`
- `DISK_FULL: int`
- `DNS_LOOKUP_FAILED: int`
- `DUPLICATE_VALUE: int`
- `ELEMENT_NOT_ENABLED: int`
- `ELEMENT_NOT_FOUND: int`
- `ELEMENT_NOT_VISIBLE: int`
- `ELEMENT_STALE: int`
- `EXPRESSION_ERROR: int`
- `FILE_ACCESS_DENIED: int`
- `FILE_NOT_FOUND: int`
- `HTTP_ERROR: int`
- `INTERNAL_ERROR: int`
- `INVALID_FORMAT: int`
- `INVALID_INPUT: int`
- `JAVASCRIPT_ERROR: int`
- `KEYBOARD_INPUT_FAILED: int`
- `MEMORY_ERROR: int`
- `MISSING_REQUIRED_FIELD: int`
- `MOUSE_ACTION_FAILED: int`
- `NAVIGATION_FAILED: int`
- `NETWORK_ERROR: int`
- `NODE_CONFIG_ERROR: int`
- `NOT_IMPLEMENTED: int`
- `PAGE_LOAD_FAILED: int`
- `PAGE_NOT_FOUND: int`
- `PARSE_ERROR: int`
- `PERMISSION_DENIED: int`
- `RESOURCE_EXHAUSTED: int`
- `RESOURCE_LOCKED: int`
- `RESOURCE_NOT_FOUND: int`
- `SCREENSHOT_FAILED: int`
- `SELECTOR_INVALID: int`
- `SERIALIZATION_ERROR: int`
- `SSL_ERROR: int`
- `TEMPLATE_ERROR: int`
- `TIMEOUT: int`
- `TYPE_FAILED: int`
- `TYPE_MISMATCH: int`
- `UI_AUTOMATION_ERROR: int`
- `UNKNOWN_ERROR: int`
- `VALIDATION_FAILED: int`
- `VALUE_OUT_OF_RANGE: int`
- `WINDOW_NOT_FOUND: int`
- `WORKFLOW_INVALID: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `category()` | `str` | Get the category name for this error code. |
| `from_exception(exception)` | `'ErrorCode'` | Map an exception to an appropriate error code. |
| `is_retryable()` | `bool` | Check if this error type is typically retryable. |

#### Method Details

##### `category`

```python
@property
def category() -> str
```

Get the category name for this error code.

##### `from_exception`

```python
@classmethod
def from_exception(exception: Exception) -> 'ErrorCode'
```

Map an exception to an appropriate error code.

Args:
    exception: The exception to map

Returns:
    The most appropriate ErrorCode

**Parameters:**

- `exception: Exception` *(required)*

##### `is_retryable`

```python
@property
def is_retryable() -> bool
```

Check if this error type is typically retryable.

### EventType

**Inherits from:** `Enum`


Types of events that can be emitted.


**Attributes:**

- `BROWSER_PAGE_READY: auto`
- `LOG_MESSAGE: auto`
- `NODE_COMPLETED: auto`
- `NODE_ERROR: auto`
- `NODE_SKIPPED: auto`
- `NODE_STARTED: auto`
- `VARIABLE_SET: auto`
- `WORKFLOW_COMPLETED: auto`
- `WORKFLOW_ERROR: auto`
- `WORKFLOW_PAUSED: auto`
- `WORKFLOW_PROGRESS: auto`
- `WORKFLOW_RESUMED: auto`
- `WORKFLOW_STARTED: auto`
- `WORKFLOW_STOPPED: auto`

### ExecutionMode

**Inherits from:** `Enum`


Execution mode for workflows.


**Attributes:**

- `DEBUG: auto`
- `NORMAL: auto`
- `VALIDATE: auto`

### NodeStatus

**Inherits from:** `Enum`


Execution status of a node.


**Attributes:**

- `CANCELLED: auto`
- `ERROR: auto`
- `IDLE: auto`
- `RUNNING: auto`
- `SKIPPED: auto`
- `SUCCESS: auto`

### PortType

**Inherits from:** `Enum`


Type of node port.


**Attributes:**

- `EXEC_INPUT: auto`
- `EXEC_OUTPUT: auto`
- `INPUT: auto`
- `OUTPUT: auto`

---

## casare_rpa.domain.workflow.templates

**File:** `src\casare_rpa\domain\workflow\templates.py`


CasareRPA - Domain Model: Workflow Templates

Template models for rapid workflow creation with parameterized configurations.
Templates define reusable workflow patterns that can be instantiated with
custom parameter values.


### ReviewStatus

**Inherits from:** `Enum`


Status of a template review.


**Attributes:**

- `HIDDEN: str`
- `PENDING: str`
- `PUBLISHED: str`
- `REMOVED: str`

### TemplateCategory

**Inherits from:** `Enum`


Categories for organizing workflow templates.


**Attributes:**

- `API_INTEGRATION: str`
- `CUSTOM: str`
- `DATABASE_OPERATIONS: str`
- `DATA_ENTRY: str`
- `DESKTOP_AUTOMATION: str`
- `EMAIL_PROCESSING: str`
- `EXCEL_AUTOMATION: str`
- `FILE_OPERATIONS: str`
- `GENERAL: str`
- `PDF_PROCESSING: str`
- `REPORT_GENERATION: str`
- `WEB_SCRAPING: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_string(value)` | `'TemplateCategory'` | Convert string to TemplateCategory. |

#### Method Details

##### `from_string`

```python
@classmethod
def from_string(value: str) -> 'TemplateCategory'
```

Convert string to TemplateCategory.

Args:
    value: Category string value

Returns:
    TemplateCategory enum value

Raises:
    ValueError: If value is not a valid category

**Parameters:**

- `value: str` *(required)*

### TemplateMetadata

**Decorators:** `@dataclass`


Metadata for a workflow template.

Contains descriptive and organizational information.


**Attributes:**

- `author: str`
- `category: TemplateCategory`
- `created_at: Optional[datetime]`
- `description: str`
- `difficulty: str`
- `estimated_duration: Optional[str]`
- `icon: str`
- `modified_at: Optional[datetime]`
- `name: str`
- `preview_image: str`
- `requirements: List[str]`
- `tags: List[str]`
- `version: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Initialize timestamps if not provided. |
| `from_dict(data)` | `'TemplateMetadata'` | Create metadata from dictionary. |
| `to_dict()` | `Dict[str, Any]` | Serialize metadata to dictionary. |
| `touch_modified()` | `None` | Update modified timestamp. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Initialize timestamps if not provided.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TemplateMetadata'
```

Create metadata from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize metadata to dictionary.

##### `touch_modified`

```python
def touch_modified() -> None
```

Update modified timestamp.

### TemplateParameter

**Decorators:** `@dataclass`


A configurable parameter within a workflow template.

Parameters define variable parts of a template that users must provide
values for when instantiating the template into a workflow.

Attributes:
    name: Parameter identifier (used in placeholder: {{param_name}})
    display_name: Human-readable name for UI
    description: Explanation of what this parameter controls
    param_type: Type of the parameter value
    default_value: Optional default value
    required: Whether the parameter must be provided
    constraints: Type-specific validation constraints
    group: Optional grouping for UI organization
    order: Display order within group


**Attributes:**

- `constraints: ConstraintDict`
- `default_value: Optional[ParameterValue]`
- `description: str`
- `display_name: str`
- `group: str`
- `name: str`
- `order: int`
- `param_type: TemplateParameterType`
- `required: bool`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_dict(data)` | `'TemplateParameter'` | Create parameter from dictionary. |
| `get_effective_value(provided_value)` | `ParameterValue` | Get the effective value considering defaults. |
| `to_dict()` | `Dict[str, Any]` | Serialize parameter to dictionary. |
| `validate_value(value)` | `tuple[bool, Optional[str]]` | Validate a value against this parameter's type and constrain... |

#### Method Details

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TemplateParameter'
```

Create parameter from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_effective_value`

```python
def get_effective_value(provided_value: Optional[ParameterValue]) -> ParameterValue
```

Get the effective value considering defaults.

Args:
    provided_value: User-provided value or None

Returns:
    Effective value (provided or default)

**Parameters:**

- `provided_value: Optional[ParameterValue]` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize parameter to dictionary.

##### `validate_value`

```python
def validate_value(value: ParameterValue) -> tuple[bool, Optional[str]]
```

Validate a value against this parameter's type and constraints.

Args:
    value: Value to validate

Returns:
    Tuple of (is_valid, error_message)

**Parameters:**

- `value: ParameterValue` *(required)*

### TemplateParameterType

**Inherits from:** `Enum`


Types of template parameters.


**Attributes:**

- `BOOLEAN: str`
- `CHOICE: str`
- `CREDENTIAL: str`
- `DIRECTORY_PATH: str`
- `EMAIL: str`
- `FILE_PATH: str`
- `FLOAT: str`
- `INTEGER: str`
- `JSON: str`
- `LIST: str`
- `SELECTOR: str`
- `STRING: str`
- `URL: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `validate_value(value, constraints)` | `tuple[bool, Optional[str]]` | Validate a value against this parameter type. |

#### Method Details

##### `validate_value`

```python
def validate_value(value: ParameterValue, constraints: Optional[ConstraintDict] = None) -> tuple[bool, Optional[str]]
```

Validate a value against this parameter type.

Args:
    value: Value to validate
    constraints: Optional validation constraints (min, max, choices, pattern, etc.)

Returns:
    Tuple of (is_valid, error_message)

**Parameters:**

- `value: ParameterValue` *(required)*
- `constraints: Optional[ConstraintDict] = None`

### TemplateReview

**Decorators:** `@dataclass`


A user review and rating for a workflow template.

Reviews help users evaluate templates before using them and provide
feedback to template authors.

Attributes:
    id: Unique review identifier
    template_id: ID of the reviewed template
    rating: Rating from 1-5
    title: Short review title
    review_text: Detailed review content
    reviewer_id: ID of the reviewer (if authenticated)
    reviewer_name: Display name of the reviewer
    verified_use: Whether the reviewer actually used the template
    template_version: Version of template when reviewed
    helpful_count: Number of users who found this helpful
    not_helpful_count: Number of users who found this not helpful
    status: Review moderation status
    created_at: When the review was created
    updated_at: When the review was last updated


**Attributes:**

- `created_at: Optional[datetime]`
- `helpful_count: int`
- `id: str`
- `not_helpful_count: int`
- `rating: int`
- `review_text: str`
- `reviewer_id: Optional[str]`
- `reviewer_name: str`
- `status: ReviewStatus`
- `template_id: str`
- `template_version: Optional[str]`
- `title: str`
- `updated_at: Optional[datetime]`
- `verified_use: bool`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Initialize timestamps and validate rating. |
| `__repr__()` | `str` | String representation. |
| `create_new(template_id, rating, reviewer_name, ...)` | `'TemplateReview'` | Factory method to create a new review. |
| `from_dict(data)` | `'TemplateReview'` | Create review from dictionary. |
| `helpfulness_score()` | `float` | Calculate helpfulness score as percentage. |
| `mark_helpful(helpful)` | `None` | Mark this review as helpful or not helpful. |
| `to_dict()` | `Dict[str, Any]` | Serialize review to dictionary. |
| `update(rating, title, review_text)` | `None` | Update the review content. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Initialize timestamps and validate rating.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `create_new`

```python
@classmethod
def create_new(template_id: str, rating: int, reviewer_name: str = 'Anonymous', reviewer_id: Optional[str] = None, title: str = '', review_text: str = '', template_version: Optional[str] = None) -> 'TemplateReview'
```

Factory method to create a new review.

Args:
    template_id: ID of the template being reviewed
    rating: Rating from 1-5
    reviewer_name: Display name of the reviewer
    reviewer_id: Optional ID of the reviewer
    title: Optional short title
    review_text: Optional detailed review
    template_version: Optional version being reviewed

Returns:
    New TemplateReview instance

Raises:
    ValueError: If rating is out of range

**Parameters:**

- `template_id: str` *(required)*
- `rating: int` *(required)*
- `reviewer_name: str = 'Anonymous'`
- `reviewer_id: Optional[str] = None`
- `title: str = ''`
- `review_text: str = ''`
- `template_version: Optional[str] = None`

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TemplateReview'
```

Create review from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `helpfulness_score`

```python
@property
def helpfulness_score() -> float
```

Calculate helpfulness score as percentage.

Returns:
    Percentage of helpful votes, or 0 if no votes

##### `mark_helpful`

```python
def mark_helpful(helpful: bool = True) -> None
```

Mark this review as helpful or not helpful.

Args:
    helpful: True if helpful, False if not helpful

**Parameters:**

- `helpful: bool = True`

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize review to dictionary.

##### `update`

```python
def update(rating: Optional[int] = None, title: Optional[str] = None, review_text: Optional[str] = None) -> None
```

Update the review content.

Args:
    rating: New rating (1-5)
    title: New title
    review_text: New review text

Raises:
    ValueError: If rating is out of range

**Parameters:**

- `rating: Optional[int] = None`
- `title: Optional[str] = None`
- `review_text: Optional[str] = None`

### TemplateUsageStats

**Decorators:** `@dataclass`


Usage statistics for a workflow template.

Tracks how templates are used for analytics and optimization.


**Attributes:**

- `average_rating: Optional[float]`
- `failed_instantiations: int`
- `last_used: Optional[datetime]`
- `rating_count: int`
- `successful_instantiations: int`
- `total_uses: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `add_rating(rating)` | `None` | Add a user rating (1-5 scale). |
| `from_dict(data)` | `'TemplateUsageStats'` | Create stats from dictionary. |
| `record_use(success)` | `None` | Record a template usage. |
| `success_rate()` | `Optional[float]` | Calculate success rate as percentage. |
| `to_dict()` | `Dict[str, Any]` | Serialize stats to dictionary. |

#### Method Details

##### `add_rating`

```python
def add_rating(rating: float) -> None
```

Add a user rating (1-5 scale).

Args:
    rating: Rating value between 1 and 5

Raises:
    ValueError: If rating is out of range

**Parameters:**

- `rating: float` *(required)*

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TemplateUsageStats'
```

Create stats from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `record_use`

```python
def record_use(success: bool) -> None
```

Record a template usage.

Args:
    success: Whether instantiation was successful

**Parameters:**

- `success: bool` *(required)*

##### `success_rate`

```python
@property
def success_rate() -> Optional[float]
```

Calculate success rate as percentage.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize stats to dictionary.

### TemplateVersion

**Decorators:** `@dataclass`


A specific version of a workflow template.

Tracks template changes over time for version history and rollback.

Attributes:
    id: Unique version identifier
    template_id: ID of the parent template
    version: Semantic version string
    version_number: Sequential version number
    change_summary: Description of changes
    breaking_changes: Whether this version has breaking changes
    workflow_definition: Full template snapshot
    parameters: Parameter definitions snapshot
    status: Version status
    published_at: When this version was published
    published_by: Who published this version
    created_at: When this version was created


**Attributes:**

- `breaking_changes: bool`
- `change_summary: str`
- `created_at: Optional[datetime]`
- `id: str`
- `parameters: List[Dict[str, Any]]`
- `published_at: Optional[datetime]`
- `published_by: Optional[str]`
- `status: str`
- `template_id: str`
- `version: str`
- `version_number: int`
- `workflow_definition: Dict[str, Any]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Initialize timestamps. |
| `__repr__()` | `str` | String representation. |
| `create_from_template(template, version, change_summary, ...)` | `'TemplateVersion'` | Create a version snapshot from a template. |
| `from_dict(data)` | `'TemplateVersion'` | Create version from dictionary. |
| `publish(published_by)` | `None` | Publish this version. |
| `to_dict()` | `Dict[str, Any]` | Serialize version to dictionary. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Initialize timestamps.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `create_from_template`

```python
@classmethod
def create_from_template(template: 'WorkflowTemplate', version: str, change_summary: str, breaking_changes: bool = False) -> 'TemplateVersion'
```

Create a version snapshot from a template.

Args:
    template: Template to snapshot
    version: Version string
    change_summary: Description of changes
    breaking_changes: Whether this is a breaking change

Returns:
    New TemplateVersion instance

**Parameters:**

- `template: 'WorkflowTemplate'` *(required)*
- `version: str` *(required)*
- `change_summary: str` *(required)*
- `breaking_changes: bool = False`

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'TemplateVersion'
```

Create version from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `publish`

```python
def publish(published_by: Optional[str] = None) -> None
```

Publish this version.

Args:
    published_by: ID of the publisher

**Parameters:**

- `published_by: Optional[str] = None`

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize version to dictionary.

### WorkflowTemplate

**Decorators:** `@dataclass`


A reusable workflow template with parameterized configuration.

Templates contain a workflow definition with placeholder values that
can be replaced with actual values when instantiating the template.

Placeholder syntax: {{parameter_name}}

Attributes:
    id: Unique template identifier
    metadata: Template descriptive metadata
    parameters: List of configurable parameters
    workflow_definition: The workflow JSON with placeholders
    usage_stats: Usage statistics
    is_builtin: Whether this is a built-in system template
    source: Template source (builtin, user, marketplace)
    marketplace_id: Optional marketplace identifier


**Attributes:**

- `_file_path: Optional[Path]`
- `id: str`
- `is_builtin: bool`
- `marketplace_id: Optional[str]`
- `metadata: TemplateMetadata`
- `parameters: List[TemplateParameter]`
- `source: str`
- `usage_stats: TemplateUsageStats`
- `workflow_definition: Dict[str, Any]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__repr__()` | `str` | String representation. |
| `add_parameter(parameter)` | `None` | Add a parameter to the template. |
| `category()` | `TemplateCategory` | Get template category. |
| `clone(new_name)` | `'WorkflowTemplate'` | Create a copy of this template. |
| `create_new(name, description, category, ...)` | `'WorkflowTemplate'` | Factory method to create a new template. |
| `export_json()` | `bytes` | Export template as JSON bytes. |
| `file_path()` | `Optional[Path]` | Get template file path. |
| `file_path(value)` | `None` | Set template file path. |
| `find_placeholders()` | `Set[str]` | Find all placeholders in the workflow definition. |
| `from_dict(data)` | `'WorkflowTemplate'` | Create template from dictionary. |
| `get_missing_parameters(values)` | `List[str]` | Get list of required parameters not provided. |
| `get_parameter(name)` | `Optional[TemplateParameter]` | Get a parameter by name. |
| `get_parameters_by_group()` | `Dict[str, List[TemplateParameter]]` | Group parameters by their group attribute. |
| `get_required_parameters()` | `List[TemplateParameter]` | Get list of required parameters without defaults. |
| `import_json(json_data)` | `'WorkflowTemplate'` | Import template from JSON bytes. |
| `instantiate(values, validate)` | `tuple[Dict[str, JsonValue], List[str]]` | Instantiate the template with provided parameter values. |
| `name()` | `str` | Get template name. |
| `remove_parameter(name)` | `bool` | Remove a parameter by name. |
| `to_dict()` | `Dict[str, Any]` | Serialize template to dictionary. |
| `validate_parameters(values)` | `tuple[bool, List[str]]` | Validate provided parameter values. |

#### Method Details

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `add_parameter`

```python
def add_parameter(parameter: TemplateParameter) -> None
```

Add a parameter to the template.

Args:
    parameter: Parameter to add

Raises:
    ValueError: If parameter name already exists

**Parameters:**

- `parameter: TemplateParameter` *(required)*

##### `category`

```python
@property
def category() -> TemplateCategory
```

Get template category.

##### `clone`

```python
def clone(new_name: Optional[str] = None) -> 'WorkflowTemplate'
```

Create a copy of this template.

Args:
    new_name: Optional new name for the clone

Returns:
    New WorkflowTemplate instance

**Parameters:**

- `new_name: Optional[str] = None`

##### `create_new`

```python
@classmethod
def create_new(name: str, description: str, category: TemplateCategory, workflow_definition: Optional[Dict[str, Any]] = None, **kwargs: Any) -> 'WorkflowTemplate'
```

Factory method to create a new template.

Args:
    name: Template name
    description: Template description
    category: Template category
    workflow_definition: Optional workflow JSON
    **kwargs: Additional template attributes

Returns:
    New WorkflowTemplate instance

**Parameters:**

- `name: str` *(required)*
- `description: str` *(required)*
- `category: TemplateCategory` *(required)*
- `workflow_definition: Optional[Dict[str, Any]] = None`
- `**kwargs: Any`

##### `export_json`

```python
def export_json() -> bytes
```

Export template as JSON bytes.

Returns:
    JSON-encoded template data

##### `file_path`

```python
@property
def file_path() -> Optional[Path]
```

Get template file path.

##### `file_path`

```python
@property
def file_path(value: Path) -> None
```

Set template file path.

**Parameters:**

- `value: Path` *(required)*

##### `find_placeholders`

```python
def find_placeholders() -> Set[str]
```

Find all placeholders in the workflow definition.

Returns:
    Set of placeholder names found in the template

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'WorkflowTemplate'
```

Create template from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `get_missing_parameters`

```python
def get_missing_parameters(values: Dict[str, ParameterValue]) -> List[str]
```

Get list of required parameters not provided.

Args:
    values: Provided parameter values

Returns:
    List of missing parameter names

**Parameters:**

- `values: Dict[str, ParameterValue]` *(required)*

##### `get_parameter`

```python
def get_parameter(name: str) -> Optional[TemplateParameter]
```

Get a parameter by name.

Args:
    name: Parameter name

Returns:
    TemplateParameter or None if not found

**Parameters:**

- `name: str` *(required)*

##### `get_parameters_by_group`

```python
def get_parameters_by_group() -> Dict[str, List[TemplateParameter]]
```

Group parameters by their group attribute.

Returns:
    Dictionary mapping group names to parameter lists

##### `get_required_parameters`

```python
def get_required_parameters() -> List[TemplateParameter]
```

Get list of required parameters without defaults.

##### `import_json`

```python
@classmethod
def import_json(json_data: bytes) -> 'WorkflowTemplate'
```

Import template from JSON bytes.

Args:
    json_data: JSON-encoded template data

Returns:
    WorkflowTemplate instance

Raises:
    ValueError: If JSON is invalid

**Parameters:**

- `json_data: bytes` *(required)*

##### `instantiate`

```python
def instantiate(values: Dict[str, ParameterValue], validate: bool = True) -> tuple[Dict[str, JsonValue], List[str]]
```

Instantiate the template with provided parameter values.

Creates a new workflow definition with placeholders replaced
by actual values.

Args:
    values: Dictionary of parameter values
    validate: Whether to validate parameters before instantiation

Returns:
    Tuple of (workflow_definition, list of warnings)

Raises:
    ValueError: If validation fails and validate=True

**Parameters:**

- `values: Dict[str, ParameterValue]` *(required)*
- `validate: bool = True`

##### `name`

```python
@property
def name() -> str
```

Get template name.

##### `remove_parameter`

```python
def remove_parameter(name: str) -> bool
```

Remove a parameter by name.

Args:
    name: Parameter name to remove

Returns:
    True if parameter was removed, False if not found

**Parameters:**

- `name: str` *(required)*

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize template to dictionary.

##### `validate_parameters`

```python
def validate_parameters(values: Dict[str, ParameterValue]) -> tuple[bool, List[str]]
```

Validate provided parameter values.

Args:
    values: Dictionary of parameter values

Returns:
    Tuple of (is_valid, list of error messages)

**Parameters:**

- `values: Dict[str, ParameterValue]` *(required)*

---

## casare_rpa.domain.workflow.versioning

**File:** `src\casare_rpa\domain\workflow\versioning.py`


CasareRPA - Domain: Workflow Versioning
Semantic versioning and version management for enterprise workflows.

Provides:
- Semantic versioning (major.minor.patch)
- Version status lifecycle (draft, active, deprecated, archived)
- Breaking change detection
- Diff generation between versions
- Backward compatibility validation


### BreakingChange

**Decorators:** `@dataclass`


Represents a breaking change between workflow versions.


**Attributes:**

- `change_type: BreakingChangeType`
- `description: str`
- `element_id: str`
- `new_value: Optional[Any]`
- `old_value: Optional[Any]`
- `severity: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### BreakingChangeType

**Inherits from:** `Enum`


Types of breaking changes between workflow versions.


**Attributes:**

- `CONNECTION_BROKEN: auto`
- `NODE_REMOVED: auto`
- `NODE_TYPE_CHANGED: auto`
- `PORT_REMOVED: auto`
- `PORT_TYPE_CHANGED: auto`
- `REQUIRED_PORT_ADDED: auto`
- `SETTING_REMOVED: auto`
- `VARIABLE_REMOVED: auto`
- `VARIABLE_TYPE_CHANGED: auto`

### CompatibilityResult

**Decorators:** `@dataclass`


Result of compatibility check between workflow versions.


**Attributes:**

- `auto_migratable: bool`
- `breaking_changes: List[BreakingChange]`
- `is_compatible: bool`
- `migration_required: bool`
- `warnings: List[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `error_count()` | `int` | Count breaking changes with error severity. |
| `has_breaking_changes()` | `bool` | Check if there are any breaking changes. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `error_count`

```python
@property
def error_count() -> int
```

Count breaking changes with error severity.

##### `has_breaking_changes`

```python
@property
def has_breaking_changes() -> bool
```

Check if there are any breaking changes.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### SemanticVersion

**Decorators:** `@dataclass`


Immutable semantic version following semver.org specification.

Version format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
- MAJOR: Incremented for breaking changes
- MINOR: Incremented for backward-compatible features
- PATCH: Incremented for backward-compatible bug fixes


**Attributes:**

- `SEMVER_PATTERN: Any`
- `build: Optional[str]`
- `major: int`
- `minor: int`
- `patch: int`
- `prerelease: Optional[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__ge__(other)` | `bool` |  |
| `__gt__(other)` | `bool` |  |
| `__le__(other)` | `bool` |  |
| `__lt__(other)` | `bool` | Compare versions for ordering. |
| `__post_init__()` | `None` | Validate version components. |
| `__str__()` | `str` | Format as version string. |
| `bump_major()` | `'SemanticVersion'` | Increment major version, reset minor and patch. |
| `bump_minor()` | `'SemanticVersion'` | Increment minor version, reset patch. |
| `bump_patch()` | `'SemanticVersion'` | Increment patch version. |
| `initial()` | `'SemanticVersion'` | Create initial version 1.0.0. |
| `is_compatible_with(other)` | `bool` | Check if this version is backward compatible with another. |
| `is_prerelease()` | `bool` | Check if this is a prerelease version. |
| `parse(version_string)` | `'SemanticVersion'` | Parse a version string into SemanticVersion. |
| `with_build(build)` | `'SemanticVersion'` | Create version with build metadata. |
| `with_prerelease(prerelease)` | `'SemanticVersion'` | Create version with prerelease tag. |

#### Method Details

##### `__ge__`

```python
def __ge__(other: 'SemanticVersion') -> bool
```

**Parameters:**

- `other: 'SemanticVersion'` *(required)*

##### `__gt__`

```python
def __gt__(other: 'SemanticVersion') -> bool
```

**Parameters:**

- `other: 'SemanticVersion'` *(required)*

##### `__le__`

```python
def __le__(other: 'SemanticVersion') -> bool
```

**Parameters:**

- `other: 'SemanticVersion'` *(required)*

##### `__lt__`

```python
def __lt__(other: 'SemanticVersion') -> bool
```

Compare versions for ordering.

**Parameters:**

- `other: 'SemanticVersion'` *(required)*

##### `__post_init__`

```python
def __post_init__() -> None
```

Validate version components.

##### `__str__`

```python
def __str__() -> str
```

Format as version string.

##### `bump_major`

```python
def bump_major() -> 'SemanticVersion'
```

Increment major version, reset minor and patch.

##### `bump_minor`

```python
def bump_minor() -> 'SemanticVersion'
```

Increment minor version, reset patch.

##### `bump_patch`

```python
def bump_patch() -> 'SemanticVersion'
```

Increment patch version.

##### `initial`

```python
@classmethod
def initial() -> 'SemanticVersion'
```

Create initial version 1.0.0.

##### `is_compatible_with`

```python
def is_compatible_with(other: 'SemanticVersion') -> bool
```

Check if this version is backward compatible with another.

Per semver, versions with same major version should be compatible
(assuming proper versioning practices).

Args:
    other: Version to check compatibility against

Returns:
    True if versions are compatible

**Parameters:**

- `other: 'SemanticVersion'` *(required)*

##### `is_prerelease`

```python
def is_prerelease() -> bool
```

Check if this is a prerelease version.

##### `parse`

```python
@classmethod
def parse(version_string: str) -> 'SemanticVersion'
```

Parse a version string into SemanticVersion.

Args:
    version_string: Version string (e.g., "1.2.3", "2.0.0-beta.1+build.123")

Returns:
    SemanticVersion instance

Raises:
    ValueError: If version string is invalid

**Parameters:**

- `version_string: str` *(required)*

##### `with_build`

```python
def with_build(build: str) -> 'SemanticVersion'
```

Create version with build metadata.

**Parameters:**

- `build: str` *(required)*

##### `with_prerelease`

```python
def with_prerelease(prerelease: str) -> 'SemanticVersion'
```

Create version with prerelease tag.

**Parameters:**

- `prerelease: str` *(required)*

### VersionDiff

**Decorators:** `@dataclass`


Represents differences between two workflow versions.


**Attributes:**

- `connections_added: List[Dict[str, str]]`
- `connections_removed: List[Dict[str, str]]`
- `from_version: str`
- `metadata_changed: Dict[str, Tuple[Any, Any]]`
- `nodes_added: Set[str]`
- `nodes_modified: Set[str]`
- `nodes_removed: Set[str]`
- `settings_changed: Dict[str, Tuple[Any, Any]]`
- `to_version: str`
- `variables_added: Set[str]`
- `variables_modified: Set[str]`
- `variables_removed: Set[str]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `has_changes()` | `bool` | Check if there are any changes. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary. |

#### Method Details

##### `has_changes`

```python
@property
def has_changes() -> bool
```

Check if there are any changes.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary.

### VersionHistory


Manages version history for a workflow.

Provides:
- Version creation and tracking
- Diff generation between versions
- Breaking change detection
- Rollback support


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow_id)` | `None` | Initialize version history. |
| `__repr__()` | `str` | String representation. |
| `activate_version(version_str)` | `bool` | Activate a specific version. |
| `active_version()` | `Optional[WorkflowVersion]` | Get the currently active version. |
| `add_version(version)` | `None` | Add a version to history. |
| `can_rollback_to(version_str)` | `Tuple[bool, str]` | Check if rollback to a version is safe. |
| `check_compatibility(from_version, to_version)` | `CompatibilityResult` | Check backward compatibility between versions. |
| `create_new_version(workflow_data, bump_type, change_summary, ...)` | `WorkflowVersion` | Create a new version based on the latest version. |
| `from_dict(data)` | `'VersionHistory'` | Create instance from dictionary. |
| `generate_diff(from_version, to_version)` | `Optional[VersionDiff]` | Generate diff between two versions. |
| `get_version(version_str)` | `Optional[WorkflowVersion]` | Get a specific version. |
| `get_version_timeline()` | `List[Dict[str, Any]]` | Get ordered timeline of all versions. |
| `get_versions_by_status(status)` | `List[WorkflowVersion]` | Get all versions with a specific status. |
| `latest_version()` | `Optional[WorkflowVersion]` | Get the most recent version (regardless of status). |
| `to_dict()` | `Dict[str, Any]` | Serialize version history. |
| `version_count()` | `int` | Get total number of versions. |

#### Method Details

##### `__init__`

```python
def __init__(workflow_id: str) -> None
```

Initialize version history.

Args:
    workflow_id: UUID of the workflow

**Parameters:**

- `workflow_id: str` *(required)*

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `activate_version`

```python
def activate_version(version_str: str) -> bool
```

Activate a specific version.

Args:
    version_str: Version to activate

Returns:
    True if activation succeeded

**Parameters:**

- `version_str: str` *(required)*

##### `active_version`

```python
@property
def active_version() -> Optional[WorkflowVersion]
```

Get the currently active version.

##### `add_version`

```python
def add_version(version: WorkflowVersion) -> None
```

Add a version to history.

Args:
    version: WorkflowVersion to add

Raises:
    ValueError: If version already exists

**Parameters:**

- `version: WorkflowVersion` *(required)*

##### `can_rollback_to`

```python
def can_rollback_to(version_str: str) -> Tuple[bool, str]
```

Check if rollback to a version is safe.

Args:
    version_str: Target rollback version

Returns:
    Tuple of (can_rollback, reason)

**Parameters:**

- `version_str: str` *(required)*

##### `check_compatibility`

```python
def check_compatibility(from_version: str, to_version: str) -> CompatibilityResult
```

Check backward compatibility between versions.

Args:
    from_version: Base version to compare against
    to_version: New version to check

Returns:
    CompatibilityResult with breaking changes

**Parameters:**

- `from_version: str` *(required)*
- `to_version: str` *(required)*

##### `create_new_version`

```python
def create_new_version(workflow_data: Dict[str, Any], bump_type: str = 'patch', change_summary: str = '', created_by: Optional[str] = None) -> WorkflowVersion
```

Create a new version based on the latest version.

Args:
    workflow_data: New workflow data
    bump_type: Version bump type ("major", "minor", "patch")
    change_summary: Description of changes
    created_by: User who created this version

Returns:
    New WorkflowVersion instance

**Parameters:**

- `workflow_data: Dict[str, Any]` *(required)*
- `bump_type: str = 'patch'`
- `change_summary: str = ''`
- `created_by: Optional[str] = None`

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'VersionHistory'
```

Create instance from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `generate_diff`

```python
def generate_diff(from_version: str, to_version: str) -> Optional[VersionDiff]
```

Generate diff between two versions.

Args:
    from_version: Source version string
    to_version: Target version string

Returns:
    VersionDiff or None if versions not found

**Parameters:**

- `from_version: str` *(required)*
- `to_version: str` *(required)*

##### `get_version`

```python
def get_version(version_str: str) -> Optional[WorkflowVersion]
```

Get a specific version.

**Parameters:**

- `version_str: str` *(required)*

##### `get_version_timeline`

```python
def get_version_timeline() -> List[Dict[str, Any]]
```

Get ordered timeline of all versions.

##### `get_versions_by_status`

```python
def get_versions_by_status(status: VersionStatus) -> List[WorkflowVersion]
```

Get all versions with a specific status.

**Parameters:**

- `status: VersionStatus` *(required)*

##### `latest_version`

```python
@property
def latest_version() -> Optional[WorkflowVersion]
```

Get the most recent version (regardless of status).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize version history.

##### `version_count`

```python
@property
def version_count() -> int
```

Get total number of versions.

### VersionStatus

**Inherits from:** `Enum`


Workflow version lifecycle status.


**Attributes:**

- `ACTIVE: auto`
- `ARCHIVED: auto`
- `DEPRECATED: auto`
- `DRAFT: auto`

### WorkflowVersion

**Decorators:** `@dataclass`


Represents a specific version of a workflow.

Captures the complete workflow state at a point in time,
including schema, metadata, and version information.


**Attributes:**

- `change_summary: str`
- `checksum: str`
- `connection_count: int`
- `created_at: datetime`
- `created_by: Optional[str]`
- `node_count: int`
- `parent_version: Optional[str]`
- `status: VersionStatus`
- `tags: List[str]`
- `version: SemanticVersion`
- `workflow_data: Dict[str, Any]`
- `workflow_id: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | `None` | Compute derived fields. |
| `__repr__()` | `str` | String representation. |
| `can_execute()` | `bool` | Check if this version can be executed. |
| `can_modify()` | `bool` | Check if this version can be modified. |
| `from_dict(data)` | `'WorkflowVersion'` | Create instance from dictionary. |
| `is_active()` | `bool` | Check if version is active. |
| `is_archived()` | `bool` | Check if version is archived. |
| `is_deprecated()` | `bool` | Check if version is deprecated. |
| `is_draft()` | `bool` | Check if version is in draft status. |
| `to_dict()` | `Dict[str, Any]` | Serialize to dictionary for storage. |
| `transition_to(new_status)` | `bool` | Attempt to transition to a new status. |

#### Method Details

##### `__post_init__`

```python
def __post_init__() -> None
```

Compute derived fields.

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `can_execute`

```python
def can_execute() -> bool
```

Check if this version can be executed.

##### `can_modify`

```python
def can_modify() -> bool
```

Check if this version can be modified.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'WorkflowVersion'
```

Create instance from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `is_active`

```python
def is_active() -> bool
```

Check if version is active.

##### `is_archived`

```python
def is_archived() -> bool
```

Check if version is archived.

##### `is_deprecated`

```python
def is_deprecated() -> bool
```

Check if version is deprecated.

##### `is_draft`

```python
def is_draft() -> bool
```

Check if version is in draft status.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize to dictionary for storage.

##### `transition_to`

```python
def transition_to(new_status: VersionStatus) -> bool
```

Attempt to transition to a new status.

Valid transitions:
- DRAFT -> ACTIVE
- ACTIVE -> DEPRECATED
- DEPRECATED -> ARCHIVED
- DEPRECATED -> ACTIVE (reactivation)

Args:
    new_status: Target status

Returns:
    True if transition was valid and executed

**Parameters:**

- `new_status: VersionStatus` *(required)*

---
