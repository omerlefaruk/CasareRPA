# Application Layer API

**Modules:** 37 | **Classes:** 120 | **Functions:** 22


## Modules

| Module | Classes | Functions | Description |
|--------|---------|-----------|-------------|
| `casare_rpa.application.dependency_injection.container` | 5 | 0 | CasareRPA - Thread-Safe Dependency Injection Conta... |
| `casare_rpa.application.dependency_injection.providers` | 8 | 1 | CasareRPA - Dependency Providers. |
| `casare_rpa.application.dependency_injection.singleton` | 2 | 1 | CasareRPA - Thread-Safe Singleton Pattern. |
| `casare_rpa.application.execution.interfaces` | 3 | 0 | CasareRPA - Application Execution Interfaces |
| `casare_rpa.application.execution.trigger_runner` | 1 | 0 | CasareRPA - Canvas Trigger Runner |
| `casare_rpa.application.orchestrator.orchestrator_engine` | 1 | 0 | Orchestrator Engine - Integrates job queue, schedu... |
| `casare_rpa.application.orchestrator.services.dispatcher_service` | 3 | 0 | Job Dispatcher for CasareRPA Orchestrator. |
| `casare_rpa.application.orchestrator.services.distribution_service` | 6 | 0 | Workflow Distribution System for CasareRPA Orchest... |
| `casare_rpa.application.orchestrator.services.job_lifecycle_service` | 1 | 0 | Job lifecycle service. |
| `casare_rpa.application.orchestrator.services.job_queue_manager` | 6 | 0 | Job Queue Manager for CasareRPA Orchestrator. |
| `casare_rpa.application.orchestrator.services.metrics_service` | 1 | 0 | Metrics service. |
| `casare_rpa.application.orchestrator.services.result_collector_service` | 4 | 0 | Result Collection System for CasareRPA Orchestrato... |
| `casare_rpa.application.orchestrator.services.robot_management_service` | 1 | 0 | Robot management service. |
| `casare_rpa.application.orchestrator.services.schedule_management_service` | 1 | 0 | Schedule management service. |
| `casare_rpa.application.orchestrator.services.scheduling_coordinator` | 3 | 3 | Job Scheduler for CasareRPA Orchestrator. |
| `casare_rpa.application.orchestrator.services.workflow_management_service` | 1 | 0 | Workflow management service. |
| `casare_rpa.application.orchestrator.use_cases.assign_robot` | 1 | 0 | AssignRobotUseCase - Assign robots to workflows an... |
| `casare_rpa.application.orchestrator.use_cases.execute_job` | 1 | 0 | Execute Job use case. |
| `casare_rpa.application.orchestrator.use_cases.execute_local` | 2 | 0 | ExecuteLocalUseCase - Execute workflow locally wit... |
| `casare_rpa.application.orchestrator.use_cases.list_robots` | 1 | 0 | ListRobotsUseCase - List and filter robots. |
| `casare_rpa.application.orchestrator.use_cases.submit_job` | 1 | 0 | SubmitJobUseCase - Submit a job for cloud executio... |
| `casare_rpa.application.scheduling.schedule_storage` | 1 | 4 | Schedule Storage for CasareRPA Canvas. |
| `casare_rpa.application.services.execution_lifecycle_manager` | 3 | 0 | Execution Lifecycle Manager for CasareRPA. |
| `casare_rpa.application.services.orchestrator_client` | 4 | 0 | Orchestrator API client service. |
| `casare_rpa.application.services.port_type_service` | 1 | 3 | Port Type Service for CasareRPA. |
| `casare_rpa.application.services.template_loader` | 2 | 0 | CasareRPA - Application Service: Template Loader |
| `casare_rpa.application.use_cases.error_recovery` | 5 | 1 | CasareRPA - Error Recovery Orchestration Use Case |
| `casare_rpa.application.use_cases.execute_workflow` | 1 | 1 | CasareRPA - Application Use Case: Execute Workflow |
| `casare_rpa.application.use_cases.execution_state_manager` | 2 | 0 | CasareRPA - Execution State Manager |
| `casare_rpa.application.use_cases.node_executor` | 3 | 0 | CasareRPA - Node Executor |
| `casare_rpa.application.use_cases.project_management` | 13 | 0 | CasareRPA - Project Management Use Cases |
| `casare_rpa.application.use_cases.template_management` | 15 | 0 | CasareRPA - Application Use Cases: Template Manage... |
| `casare_rpa.application.use_cases.validate_workflow` | 3 | 0 | CasareRPA - Application Use Case: Validate Workflo... |
| `casare_rpa.application.use_cases.variable_resolver` | 2 | 0 | CasareRPA - Variable Resolver |
| `casare_rpa.application.use_cases.workflow_migration` | 9 | 4 | CasareRPA - Application Use Case: Workflow Migrati... |
| `casare_rpa.application.workflow.recent_files` | 1 | 3 | Recent Files Manager for CasareRPA. |
| `casare_rpa.application.workflow.workflow_import` | 2 | 1 | Workflow Import Module for CasareRPA. |

## casare_rpa.application.dependency_injection.container

**File:** `src\casare_rpa\application\dependency_injection\container.py`


CasareRPA - Thread-Safe Dependency Injection Container.

Provides lifecycle-aware dependency management with proper thread safety.
Supports singleton, scoped, and transient lifecycles.


### DIContainer


Thread-safe dependency injection container.

Features:
- Singleton pattern for container itself
- Thread-safe registration and resolution
- Lifecycle management (singleton, scoped, transient)
- Lazy initialization
- Proper cleanup on shutdown


**Attributes:**

- `_instance: Optional['DIContainer']`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the container. |
| `clear()` | `None` | Clear all registrations (for testing). |
| `create_scope()` | - | Create a new scope for scoped dependencies. |
| `get_instance()` | `'DIContainer'` | Get the singleton container instance. |
| `is_registered(name)` | `bool` | Check if a dependency is registered. |
| `register_instance(name, instance)` | `None` | Register an existing instance as a singleton. |
| `register_scoped(name, implementation, factory, ...)` | `None` | Register a scoped dependency. |
| `register_singleton(name, implementation, factory, ...)` | `None` | Register a singleton dependency. |
| `register_transient(name, implementation, factory, ...)` | `None` | Register a transient dependency. |
| `reset_instance()` | `None` | Reset the singleton instance (for testing). |
| `resolve(name)` | `Any` | Resolve a dependency by name. |
| `resolve_optional(name)` | `Optional[Any]` | Resolve a dependency, returning None if not registered. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the container.

##### `clear`

```python
def clear() -> None
```

Clear all registrations (for testing).

##### `create_scope`

```python
def create_scope()
```

Create a new scope for scoped dependencies.

Usage:
    with container.create_scope():
        ctx = container.resolve("execution_context")
        # ctx is scoped to this block

##### `get_instance`

```python
@classmethod
def get_instance() -> 'DIContainer'
```

Get the singleton container instance.

Thread-safe lazy initialization.

##### `is_registered`

```python
def is_registered(name: str) -> bool
```

Check if a dependency is registered.

**Parameters:**

- `name: str` *(required)*

##### `register_instance`

```python
def register_instance(name: str, instance: T) -> None
```

Register an existing instance as a singleton.

Useful for injecting pre-configured objects.

**Parameters:**

- `name: str` *(required)*
- `instance: T` *(required)*

##### `register_scoped`

```python
def register_scoped(name: str, implementation: Optional[Type[T]] = None, factory: Optional[Callable[..., T]] = None, dependencies: Optional[Dict[str, str]] = None) -> None
```

Register a scoped dependency.

Scoped dependencies are created once per scope (e.g., workflow execution).

**Parameters:**

- `name: str` *(required)*
- `implementation: Optional[Type[T]] = None`
- `factory: Optional[Callable[..., T]] = None`
- `dependencies: Optional[Dict[str, str]] = None`

##### `register_singleton`

```python
def register_singleton(name: str, implementation: Optional[Type[T]] = None, factory: Optional[Callable[..., T]] = None, dependencies: Optional[Dict[str, str]] = None) -> None
```

Register a singleton dependency.

Args:
    name: Unique name for the dependency
    implementation: Class to instantiate
    factory: Factory function to create instance
    dependencies: Map of param names to dependency names

**Parameters:**

- `name: str` *(required)*
- `implementation: Optional[Type[T]] = None`
- `factory: Optional[Callable[..., T]] = None`
- `dependencies: Optional[Dict[str, str]] = None`

##### `register_transient`

```python
def register_transient(name: str, implementation: Optional[Type[T]] = None, factory: Optional[Callable[..., T]] = None, dependencies: Optional[Dict[str, str]] = None) -> None
```

Register a transient dependency.

Transient dependencies are created fresh each time they are resolved.

**Parameters:**

- `name: str` *(required)*
- `implementation: Optional[Type[T]] = None`
- `factory: Optional[Callable[..., T]] = None`
- `dependencies: Optional[Dict[str, str]] = None`

##### `reset_instance`

```python
@classmethod
def reset_instance() -> None
```

Reset the singleton instance (for testing).

Disposes all registered dependencies before reset.

##### `resolve`

```python
def resolve(name: str) -> Any
```

Resolve a dependency by name.

Thread-safe resolution with proper lifecycle handling.

Args:
    name: Name of the registered dependency

Returns:
    The resolved instance

Raises:
    KeyError: If dependency not registered

**Parameters:**

- `name: str` *(required)*

##### `resolve_optional`

```python
def resolve_optional(name: str) -> Optional[Any]
```

Resolve a dependency, returning None if not registered.

Useful for optional dependencies.

**Parameters:**

- `name: str` *(required)*

### Lifecycle

**Inherits from:** `Enum`


Dependency lifecycle types.


**Attributes:**

- `SCOPED: auto`
- `SINGLETON: auto`
- `TRANSIENT: auto`

### Registration

**Decorators:** `@dataclass`


Represents a registered dependency.


**Attributes:**

- `dependencies: Dict[str, str]`
- `factory: Optional[Callable[..., Any]]`
- `implementation: Optional[Type[Any]]`
- `instance: Optional[Any]`
- `lifecycle: Lifecycle`
- `name: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_instance(container)` | `Any` | Create an instance of the registered type. |

#### Method Details

##### `create_instance`

```python
def create_instance(container: 'DIContainer') -> Any
```

Create an instance of the registered type.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### Scope


Represents a scope for scoped dependencies.

Used to create child containers that share singletons with parent
but have their own scoped instances.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(container)` | `None` | Initialize scope with reference to parent container. |
| `dispose()` | `None` | Dispose all scoped instances. |
| `get_or_create(registration)` | `Any` | Get or create a scoped instance. |

#### Method Details

##### `__init__`

```python
def __init__(container: 'DIContainer') -> None
```

Initialize scope with reference to parent container.

**Parameters:**

- `container: 'DIContainer'` *(required)*

##### `dispose`

```python
def dispose() -> None
```

Dispose all scoped instances.

##### `get_or_create`

```python
def get_or_create(registration: Registration) -> Any
```

Get or create a scoped instance.

**Parameters:**

- `registration: Registration` *(required)*

### TypedContainer

**Inherits from:** `Generic[T]`


Type-safe wrapper for accessing specific dependencies.

Provides compile-time type checking for dependency resolution.

Usage:
    config_provider = TypedContainer[Config]("config")
    config = config_provider.get()  # Returns Config type


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(name)` | `None` | Initialize with dependency name. |
| `get()` | `T` | Get the typed dependency instance. |
| `get_optional()` | `Optional[T]` | Get the typed dependency or None. |

#### Method Details

##### `__init__`

```python
def __init__(name: str) -> None
```

Initialize with dependency name.

**Parameters:**

- `name: str` *(required)*

##### `get`

```python
def get() -> T
```

Get the typed dependency instance.

##### `get_optional`

```python
def get_optional() -> Optional[T]
```

Get the typed dependency or None.

---

## casare_rpa.application.dependency_injection.providers

**File:** `src\casare_rpa\application\dependency_injection\providers.py`


CasareRPA - Dependency Providers.

Provider classes that encapsulate dependency registration and lifecycle.
Each provider is responsible for a related set of dependencies.

Usage:
    container = DIContainer.get_instance()
    ConfigProvider.register(container)
    EventBusProvider.register(container)


### Functions

#### `register_all_providers`

```python
def register_all_providers(container: 'DIContainer') -> None
```

Register all providers with the container.

Called once at application startup.


### BaseProvider


Base class for dependency providers.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register all dependencies managed by this provider. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register all dependencies managed by this provider.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### ConfigProvider

**Inherits from:** `BaseProvider`


Provider for configuration dependencies.

Manages:
- config: Main Config object (singleton, lazy-loaded from environment)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register configuration dependencies. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register configuration dependencies.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### EventBusProvider

**Inherits from:** `BaseProvider`


Provider for event system dependencies.

Manages:
- event_bus: Main EventBus instance (singleton)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register event system dependencies. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register event system dependencies.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### InfrastructureProvider

**Inherits from:** `BaseProvider`


Provider for infrastructure dependencies.

Manages:
- update_manager: UpdateManager (singleton)
- recovery_strategy_registry: RecoveryStrategyRegistry (singleton)
- migration_rule_registry: MigrationRuleRegistry (singleton)
- metrics_exporter: MetricsExporter (singleton)
- output_capture: OutputCapture controller (singleton)
- ui_log_controller: UI log sink controller (singleton)
- healing_telemetry: Browser healing telemetry (singleton)
- api_key_store: API key storage (singleton)
- credential_store: Credential storage (singleton)
- memory_queue: Memory queue (singleton)
- log_streaming_service: Log streaming (singleton)
- log_cleanup_job: Log cleanup scheduler (singleton)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register infrastructure dependencies. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register infrastructure dependencies.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### OutputCaptureController


Controller for stdout/stderr capture.

Manages the output capture lifecycle without using globals.
Thread-safe: Uses internal lock for state management.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the controller. |
| `dispose()` | `None` | Cleanup on shutdown. |
| `remove_callbacks()` | `None` | Remove callbacks and restore original streams. |
| `set_callbacks(stdout_callback, stderr_callback)` | `None` | Set output callbacks. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the controller.

##### `dispose`

```python
def dispose() -> None
```

Cleanup on shutdown.

##### `remove_callbacks`

```python
def remove_callbacks() -> None
```

Remove callbacks and restore original streams.

##### `set_callbacks`

```python
def set_callbacks(stdout_callback: Optional[Callable[[str], None]] = None, stderr_callback: Optional[Callable[[str], None]] = None) -> None
```

Set output callbacks.

Args:
    stdout_callback: Called with each line of stdout
    stderr_callback: Called with each line of stderr

**Parameters:**

- `stdout_callback: Optional[Callable[[str], None]] = None`
- `stderr_callback: Optional[Callable[[str], None]] = None`

### PresentationProvider

**Inherits from:** `BaseProvider`


Provider for presentation-layer dependencies.

Manages UI-related singletons that bridge infrastructure and presentation.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register presentation dependencies. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register presentation dependencies.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### StorageProvider

**Inherits from:** `BaseProvider`


Provider for storage dependencies.

Manages:
- schedule_storage: ScheduleStorage (singleton)
- recent_files_manager: RecentFilesManager (singleton)
- template_loader: TemplateLoader (singleton)
- settings_manager: SettingsManager (singleton)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `register(container)` | `None` | Register storage dependencies. |

#### Method Details

##### `register`

```python
@classmethod
def register(container: 'DIContainer') -> None
```

Register storage dependencies.

**Parameters:**

- `container: 'DIContainer'` *(required)*

### UILogController


Controller for UI log sink.

Manages the loguru UI sink lifecycle without using globals.
Thread-safe: Uses internal lock for state management.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the controller. |
| `dispose()` | `None` | Cleanup on shutdown. |
| `remove_callback()` | `None` | Remove UI log callback. |
| `set_callback(callback, min_level)` | `None` | Set UI log callback. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the controller.

##### `dispose`

```python
def dispose() -> None
```

Cleanup on shutdown.

##### `remove_callback`

```python
def remove_callback() -> None
```

Remove UI log callback.

##### `set_callback`

```python
def set_callback(callback: Callable[[str, str, str, str], None], min_level: str = 'DEBUG') -> None
```

Set UI log callback.

Args:
    callback: Function(level, message, module, timestamp)
    min_level: Minimum log level

**Parameters:**

- `callback: Callable[[str, str, str, str], None]` *(required)*
- `min_level: str = 'DEBUG'`

---

## casare_rpa.application.dependency_injection.singleton

**File:** `src\casare_rpa\application\dependency_injection\singleton.py`


CasareRPA - Thread-Safe Singleton Pattern.

Provides a reusable singleton pattern that replaces the use of the `global` keyword.
This module offers a drop-in replacement for global singleton accessors.

Usage:
    Instead of:
        _instance: Optional[MyClass] = None

        def get_instance() -> MyClass:
            global _instance
            if _instance is None:
                _instance = MyClass()
            return _instance

    Use:
        from casare_rpa.application.dependency_injection.singleton import Singleton

        _my_class_holder = Singleton(MyClass)

        def get_instance() -> MyClass:
            return _my_class_holder.get()

        def reset_instance() -> None:
            _my_class_holder.reset()


### Functions

#### `create_singleton_accessor`

```python
def create_singleton_accessor(factory: Callable[[], T], name: Optional[str] = None) -> tuple[Callable[[], T], Callable[[], None]]
```

Create get and reset functions for a singleton.

Convenience function that returns a pair of accessor functions.

Args:
    factory: Callable that creates the instance
    name: Optional name for logging

Returns:
    Tuple of (get_func, reset_func)

Example:
    get_config, reset_config = create_singleton_accessor(
        lambda: Config.from_env(),
        name="Config"
    )

    config = get_config()
    reset_config()  # For testing


### LazySingleton

**Inherits from:** `Generic[T]`


Lazily-initialized singleton with deferred factory.

Useful when the factory function depends on other modules
that may not be imported yet.

Example:
    def create_event_bus():
        from casare_rpa.domain.events import EventBus
        return EventBus()

    event_bus_holder = LazySingleton(create_event_bus)


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(factory, name)` | `None` | Initialize the lazy singleton holder. |
| `get()` | `T` | Get the singleton instance, creating if needed. |
| `reset()` | `None` | Reset the singleton instance. |

#### Method Details

##### `__init__`

```python
def __init__(factory: Callable[[], T], name: Optional[str] = None) -> None
```

Initialize the lazy singleton holder.

Args:
    factory: Callable that creates the instance (called lazily)
    name: Optional name for logging

**Parameters:**

- `factory: Callable[[], T]` *(required)*
- `name: Optional[str] = None`

##### `get`

```python
def get() -> T
```

Get the singleton instance, creating if needed.

##### `reset`

```python
def reset() -> None
```

Reset the singleton instance.

### Singleton

**Inherits from:** `Generic[T]`


Thread-safe singleton holder.

Provides lazy initialization and proper cleanup without using globals.

Type Parameters:
    T: The type of the singleton instance

Example:
    class ConfigManager:
        pass

    config_holder = Singleton(ConfigManager)

    def get_config() -> ConfigManager:
        return config_holder.get()

    def reset_config() -> None:
        config_holder.reset()


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(factory, name, on_create, ...)` | `None` | Initialize the singleton holder. |
| `get()` | `T` | Get the singleton instance. |
| `get_optional()` | `Optional[T]` | Get the singleton instance if it exists. |
| `is_initialized()` | `bool` | Check if the singleton has been initialized. |
| `reset()` | `None` | Reset the singleton instance. |
| `set(instance)` | `None` | Replace the singleton instance. |

#### Method Details

##### `__init__`

```python
def __init__(factory: Callable[[], T], name: Optional[str] = None, on_create: Optional[Callable[[T], None]] = None, on_dispose: Optional[Callable[[T], None]] = None) -> None
```

Initialize the singleton holder.

Args:
    factory: Callable that creates the instance
    name: Optional name for logging
    on_create: Optional callback after instance creation
    on_dispose: Optional callback before instance disposal

**Parameters:**

- `factory: Callable[[], T]` *(required)*
- `name: Optional[str] = None`
- `on_create: Optional[Callable[[T], None]] = None`
- `on_dispose: Optional[Callable[[T], None]] = None`

##### `get`

```python
def get() -> T
```

Get the singleton instance.

Uses double-checked locking for thread safety and performance.

Returns:
    The singleton instance

##### `get_optional`

```python
def get_optional() -> Optional[T]
```

Get the singleton instance if it exists.

Does not create the instance if it doesn't exist.

Returns:
    The singleton instance or None

##### `is_initialized`

```python
def is_initialized() -> bool
```

Check if the singleton has been initialized.

##### `reset`

```python
def reset() -> None
```

Reset the singleton instance.

Disposes the current instance and clears the reference.
Next call to get() will create a new instance.

##### `set`

```python
def set(instance: T) -> None
```

Replace the singleton instance.

Disposes the old instance if one exists.

Args:
    instance: New instance to use

**Parameters:**

- `instance: T` *(required)*

---

## casare_rpa.application.execution.interfaces

**File:** `src\casare_rpa\application\execution\interfaces.py`


CasareRPA - Application Execution Interfaces

Protocols (interfaces) for trigger execution that the presentation layer implements.
This allows the application layer to remain decoupled from presentation concerns.

Architecture:
    Presentation → implements → Application (Protocol) ← uses ← TriggerRunner


### CallbackTriggerEventHandler


Callback-based implementation of TriggerEventHandler.

Allows injecting custom callbacks for each operation.
Useful for testing or custom integrations.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(on_workflow_run, on_stats_update, on_get_count)` | `None` | Initialize with optional callbacks. |
| `get_trigger_count(trigger_id)` | `int` | Invoke the get count callback if set, else return 0. |
| `request_workflow_run()` | `None` | Invoke the workflow run callback if set. |
| `update_trigger_stats(trigger_id, count, last_triggered)` | `None` | Invoke the stats update callback if set. |

#### Method Details

##### `__init__`

```python
def __init__(on_workflow_run: Optional[Callable[[], None]] = None, on_stats_update: Optional[Callable[[str, int, str], None]] = None, on_get_count: Optional[Callable[[str], int]] = None) -> None
```

Initialize with optional callbacks.

Args:
    on_workflow_run: Called when workflow run is requested
    on_stats_update: Called with (trigger_id, count, timestamp)
    on_get_count: Called with trigger_id, returns count

**Parameters:**

- `on_workflow_run: Optional[Callable[[], None]] = None`
- `on_stats_update: Optional[Callable[[str, int, str], None]] = None`
- `on_get_count: Optional[Callable[[str], int]] = None`

##### `get_trigger_count`

```python
def get_trigger_count(trigger_id: str) -> int
```

Invoke the get count callback if set, else return 0.

**Parameters:**

- `trigger_id: str` *(required)*

##### `request_workflow_run`

```python
def request_workflow_run() -> None
```

Invoke the workflow run callback if set.

##### `update_trigger_stats`

```python
def update_trigger_stats(trigger_id: str, count: int, last_triggered: str) -> None
```

Invoke the stats update callback if set.

**Parameters:**

- `trigger_id: str` *(required)*
- `count: int` *(required)*
- `last_triggered: str` *(required)*

### NullTriggerEventHandler


Null implementation of TriggerEventHandler for headless/test environments.

Logs events but takes no action. Useful for:
- Unit testing without UI dependencies
- Robot-only execution without Canvas
- Development/debugging


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_trigger_count(trigger_id)` | `int` | Return 0 for headless mode (no persistent stats). |
| `request_workflow_run()` | `None` | Log workflow run request (no-op in headless mode). |
| `update_trigger_stats(trigger_id, count, last_triggered)` | `None` | Log stats update (no-op in headless mode). |

#### Method Details

##### `get_trigger_count`

```python
def get_trigger_count(trigger_id: str) -> int
```

Return 0 for headless mode (no persistent stats).

**Parameters:**

- `trigger_id: str` *(required)*

##### `request_workflow_run`

```python
def request_workflow_run() -> None
```

Log workflow run request (no-op in headless mode).

##### `update_trigger_stats`

```python
def update_trigger_stats(trigger_id: str, count: int, last_triggered: str) -> None
```

Log stats update (no-op in headless mode).

**Parameters:**

- `trigger_id: str` *(required)*
- `count: int` *(required)*
- `last_triggered: str` *(required)*

### TriggerEventHandler

**Inherits from:** `Protocol`

**Decorators:** `@runtime_checkable`


Protocol for handling trigger events from the application layer.

The presentation layer (Canvas app) implements this protocol to:
1. Request workflow execution when a trigger fires
2. Update trigger statistics in the UI

This abstraction allows CanvasTriggerRunner to work without
knowing about Qt, MainWindow, or any presentation details.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_trigger_count(trigger_id)` | `int` | Get the current execution count for a trigger. |
| `request_workflow_run()` | `None` | Request the application to run the current workflow. |
| `update_trigger_stats(trigger_id, count, last_triggered)` | `None` | Update the UI with trigger statistics. |

#### Method Details

##### `get_trigger_count`

```python
def get_trigger_count(trigger_id: str) -> int
```

Get the current execution count for a trigger.

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

This should be called on the main thread (for Qt applications).
The implementation handles thread-safety internally.

##### `update_trigger_stats`

```python
def update_trigger_stats(trigger_id: str, count: int, last_triggered: str) -> None
```

Update the UI with trigger statistics.

Args:
    trigger_id: The ID of the trigger that fired
    count: The new execution count
    last_triggered: ISO timestamp of when the trigger last fired

**Parameters:**

- `trigger_id: str` *(required)*
- `count: int` *(required)*
- `last_triggered: str` *(required)*

---

## casare_rpa.application.execution.trigger_runner

**File:** `src\casare_rpa\application\execution\trigger_runner.py`


CasareRPA - Canvas Trigger Runner

Manages trigger lifecycle in the Canvas application.
Starts/stops triggers and handles trigger events by running workflows.

Architecture:
    This is an APPLICATION layer component. It MUST NOT import from presentation.
    The TriggerEventHandler protocol allows presentation to inject callbacks.


### CanvasTriggerRunner


Manages triggers for the Canvas application.

When triggers are started, they actively monitor for events
and run the workflow when triggered.

The trigger runner uses a TriggerEventHandler to communicate
with the presentation layer without depending on it directly.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(event_handler)` | `None` | Initialize the trigger runner. |
| `active_trigger_count()` | `int` | Get the number of active triggers. |
| `clear_last_trigger_event()` | `None` | Clear the last trigger event. |
| `get_last_trigger_event()` | `Optional[TriggerEvent]` | Get the last trigger event (for injecting into workflow vari... |
| `is_running()` | `bool` | Check if triggers are running. |
| `set_event_handler(handler)` | `None` | Set or update the event handler. |
| `async start_triggers(triggers)` | `int` | Start all enabled triggers. |
| `async stop_triggers()` | `None` | Stop all active triggers. |

#### Method Details

##### `__init__`

```python
def __init__(event_handler: Optional[TriggerEventHandler] = None) -> None
```

Initialize the trigger runner.

Args:
    event_handler: Handler for trigger events. If None, uses
                   NullTriggerEventHandler (logs but takes no action).

**Parameters:**

- `event_handler: Optional[TriggerEventHandler] = None`

##### `active_trigger_count`

```python
@property
def active_trigger_count() -> int
```

Get the number of active triggers.

##### `clear_last_trigger_event`

```python
def clear_last_trigger_event() -> None
```

Clear the last trigger event.

##### `get_last_trigger_event`

```python
def get_last_trigger_event() -> Optional[TriggerEvent]
```

Get the last trigger event (for injecting into workflow variables).

##### `is_running`

```python
@property
def is_running() -> bool
```

Check if triggers are running.

##### `set_event_handler`

```python
def set_event_handler(handler: TriggerEventHandler) -> None
```

Set or update the event handler.

Args:
    handler: New event handler to use

**Parameters:**

- `handler: TriggerEventHandler` *(required)*

##### `start_triggers`

```python
async def start_triggers(triggers: List[Dict[str, Any]]) -> int
```

Start all enabled triggers.

Args:
    triggers: List of trigger configurations from the scenario

Returns:
    Number of triggers successfully started

**Parameters:**

- `triggers: List[Dict[str, Any]]` *(required)*

##### `stop_triggers`

```python
async def stop_triggers() -> None
```

Stop all active triggers.

---

## casare_rpa.application.orchestrator.orchestrator_engine

**File:** `src\casare_rpa\application\orchestrator\orchestrator_engine.py`


Orchestrator Engine - Integrates job queue, scheduler, dispatcher, and triggers.
The main orchestration logic for CasareRPA.


### OrchestratorEngine


Main orchestrator engine that coordinates all components.

Components:
- JobQueue: Priority queue with state machine
- JobScheduler: Cron-based scheduling
- JobDispatcher: Robot selection and load balancing
- TriggerManager: Event-based workflow triggers
- OrchestratorService: Data persistence

This is the primary interface for job management.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(service, load_balancing, dispatch_interval, ...)` | - | Initialize orchestrator engine. |
| `available_robots()` | `List[Robot]` | Get list of available robots. |
| `async cancel_job(job_id, reason)` | `bool` | Cancel a job. |
| `async complete_job(job_id, result)` | `bool` | Mark a job as completed (called by robot). |
| `connected_robots()` | `List[str]` | Get list of connected robot IDs. |
| `async create_schedule(name, workflow_id, workflow_name, ...)` | `Optional[Schedule]` | Create a new schedule. |
| `async delete_schedule(schedule_id)` | `bool` | Delete a schedule. |
| `async disable_trigger(trigger_id)` | `bool` | Disable a trigger. |
| `async dispatch_job_to_robot(job, robot_id)` | `bool` | Dispatch a job to a specific robot via WebSocket. |
| `async enable_trigger(trigger_id)` | `bool` | Enable a trigger. |
| `async fail_job(job_id, error_message)` | `bool` | Mark a job as failed (called by robot). |
| `async fire_trigger_manually(trigger_id, payload)` | `bool` | Manually fire a trigger. |
| `get_dispatcher_stats()` | `Dict[str, Any]` | Get dispatcher statistics. |
| `get_queue_stats()` | `Dict[str, Any]` | Get queue statistics. |
| `get_trigger_manager()` | `Optional['TriggerManager']` | Get the trigger manager instance. |
| `get_trigger_stats()` | `Dict[str, Any]` | Get trigger statistics. |
| `get_upcoming_schedules(limit)` | `List[Dict[str, Any]]` | Get upcoming scheduled runs. |
| `async register_robot(robot_id, name, environment, ...)` | `Robot` | Register a robot with the orchestrator. |
| `async register_trigger(trigger_config, scenario_id, workflow_id)` | `bool` | Register a trigger with the trigger manager. |
| `async retry_job(job_id)` | `Optional[Job]` | Retry a failed job. |
| `async robot_heartbeat(robot_id)` | `bool` | Process robot heartbeat. |
| `server_port()` | `int` | Get the server port. |
| `async start()` | - | Start the orchestrator engine. |
| `async start_server(host, port)` | - | Start WebSocket server for robot connections. |
| `async stop()` | - | Stop the orchestrator engine. |
| `async submit_job(workflow_id, workflow_name, workflow_json, ...)` | `Optional[Job]` | Submit a new job to the queue. |
| `async toggle_schedule(schedule_id, enabled)` | `bool` | Enable or disable a schedule. |
| `async unregister_trigger(trigger_id)` | `bool` | Unregister a trigger. |
| `async update_job_progress(job_id, progress, current_node)` | `bool` | Update job progress (called by robot). |
| `async update_robot_status(robot_id, status)` | `bool` | Update robot status. |

#### Method Details

##### `__init__`

```python
def __init__(service: Optional[Any] = None, load_balancing: str = 'least_loaded', dispatch_interval: int = 5, timeout_check_interval: int = 30, default_job_timeout: int = 3600, trigger_webhook_port: int = 8766)
```

Initialize orchestrator engine.

Args:
    service: Data persistence service providing robot, schedule, job, and workflow management.
             Must implement: connect(), get_robots(), get_schedules(), get_job(),
             save_schedule(), get_schedule(), toggle_schedule(), delete_schedule(),
             get_workflow(), update_robot_status()
    load_balancing: Load balancing strategy (round_robin, least_loaded, random, affinity)
    dispatch_interval: Seconds between dispatch attempts
    timeout_check_interval: Seconds between timeout checks
    default_job_timeout: Default job timeout in seconds
    trigger_webhook_port: Port for trigger webhook server

**Parameters:**

- `service: Optional[Any] = None`
- `load_balancing: str = 'least_loaded'`
- `dispatch_interval: int = 5`
- `timeout_check_interval: int = 30`
- `default_job_timeout: int = 3600`
- `trigger_webhook_port: int = 8766`

##### `available_robots`

```python
@property
def available_robots() -> List[Robot]
```

Get list of available robots.

##### `cancel_job`

```python
async def cancel_job(job_id: str, reason: str = 'Cancelled by user') -> bool
```

Cancel a job.

Args:
    job_id: Job ID to cancel
    reason: Cancellation reason

Returns:
    True if cancelled successfully

**Parameters:**

- `job_id: str` *(required)*
- `reason: str = 'Cancelled by user'`

##### `complete_job`

```python
async def complete_job(job_id: str, result: Optional[Dict] = None) -> bool
```

Mark a job as completed (called by robot).

Args:
    job_id: Job ID
    result: Job result data

Returns:
    True if completed successfully

**Parameters:**

- `job_id: str` *(required)*
- `result: Optional[Dict] = None`

##### `connected_robots`

```python
@property
def connected_robots() -> List[str]
```

Get list of connected robot IDs.

##### `create_schedule`

```python
async def create_schedule(name: str, workflow_id: str, workflow_name: str, frequency: ScheduleFrequency, cron_expression: str = '', robot_id: Optional[str] = None, priority: JobPriority = JobPriority.NORMAL, timezone: str = 'UTC', enabled: bool = True) -> Optional[Schedule]
```

Create a new schedule.

Args:
    name: Schedule name
    workflow_id: Workflow ID to run
    workflow_name: Workflow name
    frequency: Schedule frequency
    cron_expression: Cron expression (for CRON frequency)
    robot_id: Target robot (optional)
    priority: Job priority
    timezone: Timezone
    enabled: Whether schedule is enabled

Returns:
    Created schedule

**Parameters:**

- `name: str` *(required)*
- `workflow_id: str` *(required)*
- `workflow_name: str` *(required)*
- `frequency: ScheduleFrequency` *(required)*
- `cron_expression: str = ''`
- `robot_id: Optional[str] = None`
- `priority: JobPriority = JobPriority.NORMAL`
- `timezone: str = 'UTC'`
- `enabled: bool = True`

##### `delete_schedule`

```python
async def delete_schedule(schedule_id: str) -> bool
```

Delete a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `disable_trigger`

```python
async def disable_trigger(trigger_id: str) -> bool
```

Disable a trigger.

**Parameters:**

- `trigger_id: str` *(required)*

##### `dispatch_job_to_robot`

```python
async def dispatch_job_to_robot(job: Job, robot_id: str) -> bool
```

Dispatch a job to a specific robot via WebSocket.

Args:
    job: Job to dispatch
    robot_id: Target robot ID

Returns:
    True if dispatched successfully

**Parameters:**

- `job: Job` *(required)*
- `robot_id: str` *(required)*

##### `enable_trigger`

```python
async def enable_trigger(trigger_id: str) -> bool
```

Enable a trigger.

**Parameters:**

- `trigger_id: str` *(required)*

##### `fail_job`

```python
async def fail_job(job_id: str, error_message: str) -> bool
```

Mark a job as failed (called by robot).

Args:
    job_id: Job ID
    error_message: Error description

Returns:
    True if marked successfully

**Parameters:**

- `job_id: str` *(required)*
- `error_message: str` *(required)*

##### `fire_trigger_manually`

```python
async def fire_trigger_manually(trigger_id: str, payload: Optional[Dict] = None) -> bool
```

Manually fire a trigger.

Args:
    trigger_id: ID of the trigger to fire
    payload: Optional payload data

Returns:
    True if fired successfully

**Parameters:**

- `trigger_id: str` *(required)*
- `payload: Optional[Dict] = None`

##### `get_dispatcher_stats`

```python
def get_dispatcher_stats() -> Dict[str, Any]
```

Get dispatcher statistics.

##### `get_queue_stats`

```python
def get_queue_stats() -> Dict[str, Any]
```

Get queue statistics.

##### `get_trigger_manager`

```python
def get_trigger_manager() -> Optional['TriggerManager']
```

Get the trigger manager instance.

##### `get_trigger_stats`

```python
def get_trigger_stats() -> Dict[str, Any]
```

Get trigger statistics.

##### `get_upcoming_schedules`

```python
def get_upcoming_schedules(limit: int = 10) -> List[Dict[str, Any]]
```

Get upcoming scheduled runs.

**Parameters:**

- `limit: int = 10`

##### `register_robot`

```python
async def register_robot(robot_id: str, name: str, environment: str = 'default', max_concurrent_jobs: int = 1, tags: Optional[List[str]] = None) -> Robot
```

Register a robot with the orchestrator.

Args:
    robot_id: Robot ID
    name: Robot name
    environment: Robot environment/pool
    max_concurrent_jobs: Max concurrent jobs
    tags: Robot tags

Returns:
    Registered robot

**Parameters:**

- `robot_id: str` *(required)*
- `name: str` *(required)*
- `environment: str = 'default'`
- `max_concurrent_jobs: int = 1`
- `tags: Optional[List[str]] = None`

##### `register_trigger`

```python
async def register_trigger(trigger_config: Dict[str, Any], scenario_id: str, workflow_id: str) -> bool
```

Register a trigger with the trigger manager.

Args:
    trigger_config: Trigger configuration dictionary
    scenario_id: ID of the scenario this trigger belongs to
    workflow_id: ID of the workflow to execute

Returns:
    True if registered successfully

**Parameters:**

- `trigger_config: Dict[str, Any]` *(required)*
- `scenario_id: str` *(required)*
- `workflow_id: str` *(required)*

##### `retry_job`

```python
async def retry_job(job_id: str) -> Optional[Job]
```

Retry a failed job.

Args:
    job_id: Job ID to retry

Returns:
    New job if created successfully

**Parameters:**

- `job_id: str` *(required)*

##### `robot_heartbeat`

```python
async def robot_heartbeat(robot_id: str) -> bool
```

Process robot heartbeat.

Args:
    robot_id: Robot ID

Returns:
    True if processed

**Parameters:**

- `robot_id: str` *(required)*

##### `server_port`

```python
@property
def server_port() -> int
```

Get the server port.

##### `start`

```python
async def start()
```

Start the orchestrator engine.

##### `start_server`

```python
async def start_server(host: str = '0.0.0.0', port: int = 8765)
```

Start WebSocket server for robot connections.

Args:
    host: Server bind address
    port: Server port

**Parameters:**

- `host: str = '0.0.0.0'`
- `port: int = 8765`

##### `stop`

```python
async def stop()
```

Stop the orchestrator engine.

##### `submit_job`

```python
async def submit_job(workflow_id: str, workflow_name: str, workflow_json: str, robot_id: Optional[str] = None, priority: JobPriority = JobPriority.NORMAL, scheduled_time: Optional[datetime] = None, params: Optional[Dict] = None, check_duplicate: bool = True) -> Optional[Job]
```

Submit a new job to the queue.

Args:
    workflow_id: Workflow ID
    workflow_name: Workflow name
    workflow_json: Workflow JSON definition
    robot_id: Target robot ID (optional, any available if not specified)
    priority: Job priority
    scheduled_time: Future execution time (optional)
    params: Job parameters for deduplication
    check_duplicate: Whether to check for duplicates

Returns:
    Created job or None if failed

**Parameters:**

- `workflow_id: str` *(required)*
- `workflow_name: str` *(required)*
- `workflow_json: str` *(required)*
- `robot_id: Optional[str] = None`
- `priority: JobPriority = JobPriority.NORMAL`
- `scheduled_time: Optional[datetime] = None`
- `params: Optional[Dict] = None`
- `check_duplicate: bool = True`

##### `toggle_schedule`

```python
async def toggle_schedule(schedule_id: str, enabled: bool) -> bool
```

Enable or disable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*
- `enabled: bool` *(required)*

##### `unregister_trigger`

```python
async def unregister_trigger(trigger_id: str) -> bool
```

Unregister a trigger.

Args:
    trigger_id: ID of the trigger to unregister

Returns:
    True if unregistered successfully

**Parameters:**

- `trigger_id: str` *(required)*

##### `update_job_progress`

```python
async def update_job_progress(job_id: str, progress: int, current_node: str = '') -> bool
```

Update job progress (called by robot).

Args:
    job_id: Job ID
    progress: Progress percentage (0-100)
    current_node: Current node being executed

Returns:
    True if updated successfully

**Parameters:**

- `job_id: str` *(required)*
- `progress: int` *(required)*
- `current_node: str = ''`

##### `update_robot_status`

```python
async def update_robot_status(robot_id: str, status: RobotStatus) -> bool
```

Update robot status.

Args:
    robot_id: Robot ID
    status: New status

Returns:
    True if updated

**Parameters:**

- `robot_id: str` *(required)*
- `status: RobotStatus` *(required)*

---

## casare_rpa.application.orchestrator.services.dispatcher_service

**File:** `src\casare_rpa\application\orchestrator\services\dispatcher_service.py`


Job Dispatcher for CasareRPA Orchestrator.
Handles robot selection, load balancing, and job assignment.


### JobDispatcher


Dispatches jobs to robots with load balancing.

Features:
- Multiple load balancing strategies
- Robot pool support
- Concurrent job limits
- Workflow-robot affinity
- Health checking


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(strategy, dispatch_interval_seconds, health_check_interval_seconds, ...)` | - | Initialize dispatcher. |
| `create_pool(name, tags, max_concurrent_jobs, ...)` | `RobotPool` | Create a robot pool. |
| `delete_pool(name)` | `bool` | Delete a robot pool. |
| `get_all_pools()` | `Dict[str, RobotPool]` | Get all pools. |
| `get_all_robots()` | `List[Robot]` | Get all registered robots. |
| `get_available_robots()` | `List[Robot]` | Get all available robots. |
| `get_pool(name)` | `Optional[RobotPool]` | Get a pool by name. |
| `get_robot(robot_id)` | `Optional[Robot]` | Get robot by ID. |
| `get_robots_by_status(status)` | `List[Robot]` | Get robots by status. |
| `get_stats()` | `Dict[str, Any]` | Get dispatcher statistics. |
| `record_job_result(job, success)` | - | Record job result for affinity tracking. |
| `register_robot(robot, pool_name)` | `bool` | Register a robot with the dispatcher. |
| `select_robot(job, pool_name)` | `Optional[Robot]` | Select the best robot for a job. |
| `set_callbacks(on_robot_status_change, on_job_dispatched)` | - | Set event callbacks. |
| `async start(job_queue)` | - | Start the dispatcher. |
| `async stop()` | - | Stop the dispatcher. |
| `unregister_robot(robot_id)` | - | Unregister a robot. |
| `update_robot(robot)` | - | Update robot state. |
| `update_robot_heartbeat(robot_id)` | - | Update robot heartbeat timestamp. |

#### Method Details

##### `__init__`

```python
def __init__(strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED, dispatch_interval_seconds: int = 5, health_check_interval_seconds: int = 30, stale_robot_timeout_seconds: int = 60)
```

Initialize dispatcher.

Args:
    strategy: Load balancing strategy
    dispatch_interval_seconds: How often to dispatch jobs
    health_check_interval_seconds: How often to check robot health
    stale_robot_timeout_seconds: Mark robot offline if no heartbeat

**Parameters:**

- `strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED`
- `dispatch_interval_seconds: int = 5`
- `health_check_interval_seconds: int = 30`
- `stale_robot_timeout_seconds: int = 60`

##### `create_pool`

```python
def create_pool(name: str, tags: Optional[List[str]] = None, max_concurrent_jobs: Optional[int] = None, allowed_workflows: Optional[Set[str]] = None) -> RobotPool
```

Create a robot pool.

**Parameters:**

- `name: str` *(required)*
- `tags: Optional[List[str]] = None`
- `max_concurrent_jobs: Optional[int] = None`
- `allowed_workflows: Optional[Set[str]] = None`

##### `delete_pool`

```python
def delete_pool(name: str) -> bool
```

Delete a robot pool.

**Parameters:**

- `name: str` *(required)*

##### `get_all_pools`

```python
def get_all_pools() -> Dict[str, RobotPool]
```

Get all pools.

##### `get_all_robots`

```python
def get_all_robots() -> List[Robot]
```

Get all registered robots.

##### `get_available_robots`

```python
def get_available_robots() -> List[Robot]
```

Get all available robots.

##### `get_pool`

```python
def get_pool(name: str) -> Optional[RobotPool]
```

Get a pool by name.

**Parameters:**

- `name: str` *(required)*

##### `get_robot`

```python
def get_robot(robot_id: str) -> Optional[Robot]
```

Get robot by ID.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_robots_by_status`

```python
def get_robots_by_status(status: RobotStatus) -> List[Robot]
```

Get robots by status.

**Parameters:**

- `status: RobotStatus` *(required)*

##### `get_stats`

```python
def get_stats() -> Dict[str, Any]
```

Get dispatcher statistics.

##### `record_job_result`

```python
def record_job_result(job: Job, success: bool)
```

Record job result for affinity tracking.

Args:
    job: Completed job
    success: Whether job succeeded

**Parameters:**

- `job: Job` *(required)*
- `success: bool` *(required)*

##### `register_robot`

```python
def register_robot(robot: Robot, pool_name: str = 'default') -> bool
```

Register a robot with the dispatcher.

Args:
    robot: Robot to register
    pool_name: Pool to assign robot to

Returns:
    True if registered successfully

**Parameters:**

- `robot: Robot` *(required)*
- `pool_name: str = 'default'`

##### `select_robot`

```python
def select_robot(job: Job, pool_name: Optional[str] = None) -> Optional[Robot]
```

Select the best robot for a job.

Args:
    job: Job to assign
    pool_name: Optional pool to select from

Returns:
    Selected robot or None if no suitable robot

**Parameters:**

- `job: Job` *(required)*
- `pool_name: Optional[str] = None`

##### `set_callbacks`

```python
def set_callbacks(on_robot_status_change: Optional[Callable[[Robot, RobotStatus, RobotStatus], None]] = None, on_job_dispatched: Optional[Callable[[Job, Robot], None]] = None)
```

Set event callbacks.

**Parameters:**

- `on_robot_status_change: Optional[Callable[[Robot, RobotStatus, RobotStatus], None]] = None`
- `on_job_dispatched: Optional[Callable[[Job, Robot], None]] = None`

##### `start`

```python
async def start(job_queue: JobQueue)
```

Start the dispatcher.

Args:
    job_queue: Job queue to dispatch from

**Parameters:**

- `job_queue: JobQueue` *(required)*

##### `stop`

```python
async def stop()
```

Stop the dispatcher.

##### `unregister_robot`

```python
def unregister_robot(robot_id: str)
```

Unregister a robot.

**Parameters:**

- `robot_id: str` *(required)*

##### `update_robot`

```python
def update_robot(robot: Robot)
```

Update robot state.

**Parameters:**

- `robot: Robot` *(required)*

##### `update_robot_heartbeat`

```python
def update_robot_heartbeat(robot_id: str)
```

Update robot heartbeat timestamp.

**Parameters:**

- `robot_id: str` *(required)*

### LoadBalancingStrategy

**Inherits from:** `Enum`


Load balancing strategies for robot selection.


**Attributes:**

- `AFFINITY: str`
- `LEAST_LOADED: str`
- `RANDOM: str`
- `ROUND_ROBIN: str`

### RobotPool


A group of robots with shared configuration.

Pools can be used for:
- Environment separation (Production, Development, Test)
- Workload isolation
- Resource allocation


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(name, tags, max_concurrent_jobs, ...)` | - | Initialize robot pool. |
| `add_robot(robot)` | `bool` | Add a robot to the pool if it matches tags. |
| `can_accept_job()` | `bool` | Check if pool can accept more jobs. |
| `get_available_robots()` | `List[Robot]` | Get available robots in the pool. |
| `get_current_job_count()` | `int` | Get total jobs currently running in pool. |
| `get_robots()` | `List[Robot]` | Get all robots in the pool. |
| `is_workflow_allowed(workflow_id)` | `bool` | Check if workflow is allowed in this pool. |
| `online_count()` | `int` | Get count of online robots. |
| `remove_robot(robot_id)` | - | Remove a robot from the pool. |
| `utilization()` | `float` | Get pool utilization percentage. |

#### Method Details

##### `__init__`

```python
def __init__(name: str, tags: Optional[List[str]] = None, max_concurrent_jobs: Optional[int] = None, allowed_workflows: Optional[Set[str]] = None)
```

Initialize robot pool.

Args:
    name: Pool name
    tags: Tags that robots must have to be in this pool
    max_concurrent_jobs: Max jobs across all robots in pool
    allowed_workflows: Workflow IDs allowed in this pool

**Parameters:**

- `name: str` *(required)*
- `tags: Optional[List[str]] = None`
- `max_concurrent_jobs: Optional[int] = None`
- `allowed_workflows: Optional[Set[str]] = None`

##### `add_robot`

```python
def add_robot(robot: Robot) -> bool
```

Add a robot to the pool if it matches tags.

**Parameters:**

- `robot: Robot` *(required)*

##### `can_accept_job`

```python
def can_accept_job() -> bool
```

Check if pool can accept more jobs.

##### `get_available_robots`

```python
def get_available_robots() -> List[Robot]
```

Get available robots in the pool.

##### `get_current_job_count`

```python
def get_current_job_count() -> int
```

Get total jobs currently running in pool.

##### `get_robots`

```python
def get_robots() -> List[Robot]
```

Get all robots in the pool.

##### `is_workflow_allowed`

```python
def is_workflow_allowed(workflow_id: str) -> bool
```

Check if workflow is allowed in this pool.

**Parameters:**

- `workflow_id: str` *(required)*

##### `online_count`

```python
@property
def online_count() -> int
```

Get count of online robots.

##### `remove_robot`

```python
def remove_robot(robot_id: str)
```

Remove a robot from the pool.

**Parameters:**

- `robot_id: str` *(required)*

##### `utilization`

```python
@property
def utilization() -> float
```

Get pool utilization percentage.

---

## casare_rpa.application.orchestrator.services.distribution_service

**File:** `src\casare_rpa\application\orchestrator\services\distribution_service.py`


Workflow Distribution System for CasareRPA Orchestrator.
Handles intelligent job distribution to robots with load balancing and capability matching.


### DistributionResult

**Decorators:** `@dataclass`


Result of a job distribution attempt.


**Attributes:**

- `attempted_robots: List[str]`
- `job_id: str`
- `message: str`
- `retry_count: int`
- `robot_id: Optional[str]`
- `success: bool`

### DistributionRule

**Decorators:** `@dataclass`


Rule for job distribution.


**Attributes:**

- `environment: Optional[str]`
- `excluded_robots: List[str]`
- `name: str`
- `preferred_robots: List[str]`
- `priority_boost: int`
- `required_tags: List[str]`
- `strategy: DistributionStrategy`
- `workflow_pattern: str`

### DistributionStrategy

**Inherits from:** `Enum`


Strategies for distributing jobs to robots.


**Attributes:**

- `AFFINITY: str`
- `CAPABILITY_MATCH: str`
- `LEAST_LOADED: str`
- `RANDOM: str`
- `ROUND_ROBIN: str`

### JobRouter


Routes jobs to appropriate robots based on job metadata.

Handles job routing with support for:
- Environment-based routing
- Tag-based routing
- Priority handling
- Fallback strategies


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `add_route(environment, robot_ids)` | - | Add a route for an environment. |
| `add_tag_route(tag, robot_ids)` | - | Add a route for a tag. |
| `clear_routes()` | - | Clear all routes. |
| `get_eligible_robots(job, all_robots)` | `List[Robot]` | Get robots eligible to run a job. |
| `set_fallback_robots(robot_ids)` | - | Set fallback robots for unmatched jobs. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `add_route`

```python
def add_route(environment: str, robot_ids: List[str])
```

Add a route for an environment.

**Parameters:**

- `environment: str` *(required)*
- `robot_ids: List[str]` *(required)*

##### `add_tag_route`

```python
def add_tag_route(tag: str, robot_ids: List[str])
```

Add a route for a tag.

**Parameters:**

- `tag: str` *(required)*
- `robot_ids: List[str]` *(required)*

##### `clear_routes`

```python
def clear_routes()
```

Clear all routes.

##### `get_eligible_robots`

```python
def get_eligible_robots(job: Job, all_robots: List[Robot]) -> List[Robot]
```

Get robots eligible to run a job.

Args:
    job: Job to route
    all_robots: All available robots

Returns:
    List of eligible robots

**Parameters:**

- `job: Job` *(required)*
- `all_robots: List[Robot]` *(required)*

##### `set_fallback_robots`

```python
def set_fallback_robots(robot_ids: List[str])
```

Set fallback robots for unmatched jobs.

**Parameters:**

- `robot_ids: List[str]` *(required)*

### RobotSelector


Selects the best robot for a job based on various criteria.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - |  |
| `clear_affinity(workflow_id)` | - | Clear affinity for a workflow. |
| `clear_all_affinity()` | - | Clear all affinity mappings. |
| `select(job, available_robots, strategy, ...)` | `Optional[Robot]` | Select the best robot for a job. |

#### Method Details

##### `__init__`

```python
def __init__()
```

##### `clear_affinity`

```python
def clear_affinity(workflow_id: str)
```

Clear affinity for a workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `clear_all_affinity`

```python
def clear_all_affinity()
```

Clear all affinity mappings.

##### `select`

```python
def select(job: Job, available_robots: List[Robot], strategy: DistributionStrategy = DistributionStrategy.LEAST_LOADED, required_tags: Optional[List[str]] = None, preferred_robots: Optional[List[str]] = None, excluded_robots: Optional[List[str]] = None) -> Optional[Robot]
```

Select the best robot for a job.

Args:
    job: Job to assign
    available_robots: List of available robots
    strategy: Distribution strategy to use
    required_tags: Tags the robot must have
    preferred_robots: Preferred robot IDs
    excluded_robots: Robot IDs to exclude

Returns:
    Selected robot or None if no suitable robot found

**Parameters:**

- `job: Job` *(required)*
- `available_robots: List[Robot]` *(required)*
- `strategy: DistributionStrategy = DistributionStrategy.LEAST_LOADED`
- `required_tags: Optional[List[str]] = None`
- `preferred_robots: Optional[List[str]] = None`
- `excluded_robots: Optional[List[str]] = None`

### WorkflowDistributor


Distributes workflows to robots.

Integrates with the orchestrator server to send jobs to selected robots
and handles distribution rules, retries, and failure handling.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(max_retries, retry_delay, distribution_timeout)` | - | Initialize the workflow distributor. |
| `add_rule(rule)` | - | Add a distribution rule. |
| `clear_rules()` | - | Clear all distribution rules. |
| `async distribute(job, available_robots, strategy)` | `DistributionResult` | Distribute a job to an available robot. |
| `async distribute_batch(jobs, available_robots)` | `List[DistributionResult]` | Distribute multiple jobs to available robots. |
| `get_recent_results(limit)` | `List[DistributionResult]` | Get recent distribution results. |
| `get_statistics()` | `Dict[str, Any]` | Get distribution statistics. |
| `remove_rule(name)` | `bool` | Remove a distribution rule by name. |
| `set_callbacks(on_success, on_failure)` | - | Set distribution callbacks. |
| `set_send_job_function(fn)` | - | Set the function to send jobs to robots. |

#### Method Details

##### `__init__`

```python
def __init__(max_retries: int = 3, retry_delay: float = 5.0, distribution_timeout: float = 30.0)
```

Initialize the workflow distributor.

Args:
    max_retries: Maximum retry attempts per job
    retry_delay: Delay between retries in seconds
    distribution_timeout: Timeout for job acceptance

**Parameters:**

- `max_retries: int = 3`
- `retry_delay: float = 5.0`
- `distribution_timeout: float = 30.0`

##### `add_rule`

```python
def add_rule(rule: DistributionRule)
```

Add a distribution rule.

**Parameters:**

- `rule: DistributionRule` *(required)*

##### `clear_rules`

```python
def clear_rules()
```

Clear all distribution rules.

##### `distribute`

```python
async def distribute(job: Job, available_robots: List[Robot], strategy: Optional[DistributionStrategy] = None) -> DistributionResult
```

Distribute a job to an available robot.

Args:
    job: Job to distribute
    available_robots: List of available robots
    strategy: Optional strategy override

Returns:
    Distribution result

**Parameters:**

- `job: Job` *(required)*
- `available_robots: List[Robot]` *(required)*
- `strategy: Optional[DistributionStrategy] = None`

##### `distribute_batch`

```python
async def distribute_batch(jobs: List[Job], available_robots: List[Robot]) -> List[DistributionResult]
```

Distribute multiple jobs to available robots.

Args:
    jobs: Jobs to distribute
    available_robots: Available robots

Returns:
    List of distribution results

**Parameters:**

- `jobs: List[Job]` *(required)*
- `available_robots: List[Robot]` *(required)*

##### `get_recent_results`

```python
def get_recent_results(limit: int = 10) -> List[DistributionResult]
```

Get recent distribution results.

**Parameters:**

- `limit: int = 10`

##### `get_statistics`

```python
def get_statistics() -> Dict[str, Any]
```

Get distribution statistics.

##### `remove_rule`

```python
def remove_rule(name: str) -> bool
```

Remove a distribution rule by name.

**Parameters:**

- `name: str` *(required)*

##### `set_callbacks`

```python
def set_callbacks(on_success: Optional[Callable] = None, on_failure: Optional[Callable] = None)
```

Set distribution callbacks.

**Parameters:**

- `on_success: Optional[Callable] = None`
- `on_failure: Optional[Callable] = None`

##### `set_send_job_function`

```python
def set_send_job_function(fn: Callable)
```

Set the function to send jobs to robots.

**Parameters:**

- `fn: Callable` *(required)*

---

## casare_rpa.application.orchestrator.services.job_lifecycle_service

**File:** `src\casare_rpa\application\orchestrator\services\job_lifecycle_service.py`


Job lifecycle service.
Handles job creation, updates, cancellation, and retries.


### JobLifecycleService


Service for managing job lifecycle operations.
Supports both cloud (Supabase) and local storage modes.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(job_repository, robot_management_service)` | - | Initialize with injected repository and optional robot servi... |
| `async cancel_job(job_id, reason)` | `bool` | Cancel a pending or running job. |
| `async connect()` | `bool` | Connect to Supabase or fall back to local storage. |
| `async create_job(workflow_id, workflow_name, workflow_json, ...)` | `Optional[Job]` | Create a new job. |
| `async dispatch_workflow_file(file_path, robot_id, priority)` | `Optional[Job]` | Dispatch a workflow from a file to a robot. |
| `async get_job(job_id)` | `Optional[Job]` | Get a specific job by ID. |
| `async get_jobs(limit, status, robot_id)` | `List[Job]` | Get jobs with optional filtering. |
| `async get_queued_jobs()` | `List[Job]` | Get jobs waiting in queue. |
| `async get_running_jobs()` | `List[Job]` | Get currently running jobs. |
| `is_cloud_mode()` | `bool` | Check if using cloud (Supabase) mode. |
| `async retry_job(job_id)` | `Optional[Job]` | Retry a failed job by creating a new one with same parameter... |
| `set_robot_management_service(robot_service)` | `None` | Set the robot management service for robot lookups. |
| `async update_job_status(job_id, status, progress, ...)` | `bool` | Update job status and progress. |

#### Method Details

##### `__init__`

```python
def __init__(job_repository: JobRepository, robot_management_service: Optional['RobotManagementService'] = None)
```

Initialize with injected repository and optional robot service.

Args:
    job_repository: Repository for job persistence.
    robot_management_service: Service for robot lookups.
        If not provided, robot_name will not be auto-populated.

**Parameters:**

- `job_repository: JobRepository` *(required)*
- `robot_management_service: Optional['RobotManagementService'] = None`

##### `cancel_job`

```python
async def cancel_job(job_id: str, reason: str = '') -> bool
```

Cancel a pending or running job.

For running jobs, sets cancel_requested=True which the robot
will poll for and gracefully stop execution.

**Parameters:**

- `job_id: str` *(required)*
- `reason: str = ''`

##### `connect`

```python
async def connect() -> bool
```

Connect to Supabase or fall back to local storage.

##### `create_job`

```python
async def create_job(workflow_id: str, workflow_name: str, workflow_json: str, robot_id: str, robot_name: str = '', priority: JobPriority = JobPriority.NORMAL, scheduled_time: Optional[datetime] = None) -> Optional[Job]
```

Create a new job.

**Parameters:**

- `workflow_id: str` *(required)*
- `workflow_name: str` *(required)*
- `workflow_json: str` *(required)*
- `robot_id: str` *(required)*
- `robot_name: str = ''`
- `priority: JobPriority = JobPriority.NORMAL`
- `scheduled_time: Optional[datetime] = None`

##### `dispatch_workflow_file`

```python
async def dispatch_workflow_file(file_path: Path, robot_id: str, priority: JobPriority = JobPriority.NORMAL) -> Optional[Job]
```

Dispatch a workflow from a file to a robot.

Args:
    file_path: Path to the workflow JSON file.
    robot_id: ID of the robot to dispatch to.
    priority: Job priority level.

Returns:
    Created Job if successful, None otherwise.

**Parameters:**

- `file_path: Path` *(required)*
- `robot_id: str` *(required)*
- `priority: JobPriority = JobPriority.NORMAL`

##### `get_job`

```python
async def get_job(job_id: str) -> Optional[Job]
```

Get a specific job by ID.

**Parameters:**

- `job_id: str` *(required)*

##### `get_jobs`

```python
async def get_jobs(limit: int = 100, status: Optional[JobStatus] = None, robot_id: Optional[str] = None) -> List[Job]
```

Get jobs with optional filtering.

**Parameters:**

- `limit: int = 100`
- `status: Optional[JobStatus] = None`
- `robot_id: Optional[str] = None`

##### `get_queued_jobs`

```python
async def get_queued_jobs() -> List[Job]
```

Get jobs waiting in queue.

##### `get_running_jobs`

```python
async def get_running_jobs() -> List[Job]
```

Get currently running jobs.

##### `is_cloud_mode`

```python
@property
def is_cloud_mode() -> bool
```

Check if using cloud (Supabase) mode.

##### `retry_job`

```python
async def retry_job(job_id: str) -> Optional[Job]
```

Retry a failed job by creating a new one with same parameters.

**Parameters:**

- `job_id: str` *(required)*

##### `set_robot_management_service`

```python
def set_robot_management_service(robot_service: 'RobotManagementService') -> None
```

Set the robot management service for robot lookups.

Allows late injection of the service after construction.

Args:
    robot_service: The RobotManagementService instance.

**Parameters:**

- `robot_service: 'RobotManagementService'` *(required)*

##### `update_job_status`

```python
async def update_job_status(job_id: str, status: JobStatus, progress: int = 0, current_node: str = '', error_message: str = '', logs: str = '') -> bool
```

Update job status and progress.

**Parameters:**

- `job_id: str` *(required)*
- `status: JobStatus` *(required)*
- `progress: int = 0`
- `current_node: str = ''`
- `error_message: str = ''`
- `logs: str = ''`

---

## casare_rpa.application.orchestrator.services.job_queue_manager

**File:** `src\casare_rpa\application\orchestrator\services\job_queue_manager.py`


Job Queue Manager for CasareRPA Orchestrator.
Implements priority queue, state machine, deduplication, and timeout management.


### JobDeduplicator


Handles job deduplication to prevent duplicate job submissions.
Uses workflow_id + parameters hash to detect duplicates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(window_seconds)` | - | Initialize deduplicator. |
| `is_duplicate(workflow_id, robot_id, params)` | `bool` | Check if a job would be a duplicate. |
| `record(workflow_id, robot_id, params)` | `str` | Record a job submission for deduplication. |

#### Method Details

##### `__init__`

```python
def __init__(window_seconds: int = 300)
```

Initialize deduplicator.

Args:
    window_seconds: Time window for deduplication (default 5 minutes)

**Parameters:**

- `window_seconds: int = 300`

##### `is_duplicate`

```python
def is_duplicate(workflow_id: str, robot_id: Optional[str] = None, params: Optional[Dict] = None) -> bool
```

Check if a job would be a duplicate.

Args:
    workflow_id: Workflow ID
    robot_id: Target robot ID (optional)
    params: Job parameters (optional)

Returns:
    True if job would be duplicate

**Parameters:**

- `workflow_id: str` *(required)*
- `robot_id: Optional[str] = None`
- `params: Optional[Dict] = None`

##### `record`

```python
def record(workflow_id: str, robot_id: Optional[str] = None, params: Optional[Dict] = None) -> str
```

Record a job submission for deduplication.

Returns:
    The deduplication hash

**Parameters:**

- `workflow_id: str` *(required)*
- `robot_id: Optional[str] = None`
- `params: Optional[Dict] = None`

### JobQueue


Priority-based job queue with state management.

Features:
- Priority queue (Critical > High > Normal > Low)
- Job state machine
- Deduplication
- Timeout management
- Robot assignment


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(dedup_window_seconds, default_timeout_seconds, on_state_change)` | - | Initialize job queue. |
| `cancel(job_id, reason)` | `Tuple[bool, str]` | Cancel a job. |
| `check_timeouts()` | `List[str]` | Check for timed out jobs and mark them. |
| `complete(job_id, result)` | `Tuple[bool, str]` | Mark a job as completed. |
| `dequeue(robot)` | `Optional[Job]` | Get next job for a robot. |
| `enqueue(job, check_duplicate, params)` | `Tuple[bool, str]` | Add a job to the queue. |
| `fail(job_id, error_message)` | `Tuple[bool, str]` | Mark a job as failed. |
| `get_job(job_id)` | `Optional[Job]` | Get job by ID. |
| `get_queue_depth()` | `int` | Get number of jobs in queue. |
| `get_queue_stats()` | `Dict[str, Any]` | Get queue statistics. |
| `get_queued_jobs()` | `List[Job]` | Get all queued jobs. |
| `get_robot_jobs(robot_id)` | `List[Job]` | Get jobs assigned to a specific robot. |
| `get_running_jobs()` | `List[Job]` | Get all running jobs. |
| `timeout(job_id)` | `Tuple[bool, str]` | Mark a job as timed out. |
| `update_progress(job_id, progress, current_node)` | `bool` | Update job progress. |

#### Method Details

##### `__init__`

```python
def __init__(dedup_window_seconds: int = 300, default_timeout_seconds: int = 3600, on_state_change: Optional[Callable[[Job, JobStatus, JobStatus], None]] = None)
```

Initialize job queue.

Args:
    dedup_window_seconds: Deduplication time window
    default_timeout_seconds: Default job timeout
    on_state_change: Callback for state changes (job, old_state, new_state)

**Parameters:**

- `dedup_window_seconds: int = 300`
- `default_timeout_seconds: int = 3600`
- `on_state_change: Optional[Callable[[Job, JobStatus, JobStatus], None]] = None`

##### `cancel`

```python
def cancel(job_id: str, reason: str = 'Cancelled by user') -> Tuple[bool, str]
```

Cancel a job.

Args:
    job_id: Job ID
    reason: Cancellation reason

Returns:
    Tuple of (success, message)

**Parameters:**

- `job_id: str` *(required)*
- `reason: str = 'Cancelled by user'`

##### `check_timeouts`

```python
def check_timeouts() -> List[str]
```

Check for timed out jobs and mark them.

Returns:
    List of job IDs that were timed out

##### `complete`

```python
def complete(job_id: str, result: Optional[Dict] = None) -> Tuple[bool, str]
```

Mark a job as completed.

Args:
    job_id: Job ID
    result: Optional result data

Returns:
    Tuple of (success, message)

**Parameters:**

- `job_id: str` *(required)*
- `result: Optional[Dict] = None`

##### `dequeue`

```python
def dequeue(robot: Robot) -> Optional[Job]
```

Get next job for a robot.

Args:
    robot: Robot requesting work

Returns:
    Next job if available, None otherwise

**Parameters:**

- `robot: Robot` *(required)*

##### `enqueue`

```python
def enqueue(job: Job, check_duplicate: bool = True, params: Optional[Dict] = None) -> Tuple[bool, str]
```

Add a job to the queue.

Args:
    job: Job to enqueue
    check_duplicate: Whether to check for duplicates
    params: Optional parameters for deduplication

Returns:
    Tuple of (success, message)

**Parameters:**

- `job: Job` *(required)*
- `check_duplicate: bool = True`
- `params: Optional[Dict] = None`

##### `fail`

```python
def fail(job_id: str, error_message: str) -> Tuple[bool, str]
```

Mark a job as failed.

Args:
    job_id: Job ID
    error_message: Error description

Returns:
    Tuple of (success, message)

**Parameters:**

- `job_id: str` *(required)*
- `error_message: str` *(required)*

##### `get_job`

```python
def get_job(job_id: str) -> Optional[Job]
```

Get job by ID.

**Parameters:**

- `job_id: str` *(required)*

##### `get_queue_depth`

```python
def get_queue_depth() -> int
```

Get number of jobs in queue.

##### `get_queue_stats`

```python
def get_queue_stats() -> Dict[str, Any]
```

Get queue statistics.

##### `get_queued_jobs`

```python
def get_queued_jobs() -> List[Job]
```

Get all queued jobs.

##### `get_robot_jobs`

```python
def get_robot_jobs(robot_id: str) -> List[Job]
```

Get jobs assigned to a specific robot.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_running_jobs`

```python
def get_running_jobs() -> List[Job]
```

Get all running jobs.

##### `timeout`

```python
def timeout(job_id: str) -> Tuple[bool, str]
```

Mark a job as timed out.

Args:
    job_id: Job ID

Returns:
    Tuple of (success, message)

**Parameters:**

- `job_id: str` *(required)*

##### `update_progress`

```python
def update_progress(job_id: str, progress: int, current_node: str = '') -> bool
```

Update job progress.

Args:
    job_id: Job ID
    progress: Progress percentage (0-100)
    current_node: Current node being executed

Returns:
    True if updated successfully

**Parameters:**

- `job_id: str` *(required)*
- `progress: int` *(required)*
- `current_node: str = ''`

### JobStateError

**Inherits from:** `Exception`


Raised when an invalid state transition is attempted.


### JobStateMachine


Job state machine with valid transitions.

State Diagram:
    PENDING -> QUEUED -> RUNNING -> COMPLETED
                  |         |
                  |         +-> FAILED
                  |         +-> TIMEOUT
                  +-> CANCELLED

    Any state can transition to CANCELLED except terminal states.


**Attributes:**

- `ACTIVE_STATES: set`
- `TERMINAL_STATES: set`
- `VALID_TRANSITIONS: Dict[JobStatus, List[JobStatus]]`
- `WAITING_STATES: set`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `can_transition(from_state, to_state)` | `bool` | Check if a state transition is valid. |
| `is_active(status)` | `bool` | Check if status is active (running). |
| `is_terminal(status)` | `bool` | Check if status is terminal. |
| `transition(job, to_state)` | `Job` | Transition job to a new state. |

#### Method Details

##### `can_transition`

```python
@classmethod
def can_transition(from_state: JobStatus, to_state: JobStatus) -> bool
```

Check if a state transition is valid.

**Parameters:**

- `from_state: JobStatus` *(required)*
- `to_state: JobStatus` *(required)*

##### `is_active`

```python
@classmethod
def is_active(status: JobStatus) -> bool
```

Check if status is active (running).

**Parameters:**

- `status: JobStatus` *(required)*

##### `is_terminal`

```python
@classmethod
def is_terminal(status: JobStatus) -> bool
```

Check if status is terminal.

**Parameters:**

- `status: JobStatus` *(required)*

##### `transition`

```python
@classmethod
def transition(job: Job, to_state: JobStatus) -> Job
```

Transition job to a new state.
Raises JobStateError if transition is invalid.

**Parameters:**

- `job: Job` *(required)*
- `to_state: JobStatus` *(required)*

### JobTimeoutManager


Manages job timeouts.
Tracks running jobs and marks them as timed out if exceeded.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(default_timeout_seconds)` | - | Initialize timeout manager. |
| `get_remaining_time(job_id)` | `Optional[timedelta]` | Get remaining time before timeout. |
| `get_timed_out_jobs()` | `List[str]` | Get list of job IDs that have timed out. |
| `start_tracking(job_id, timeout_seconds)` | - | Start tracking a job's timeout. |
| `stop_tracking(job_id)` | - | Stop tracking a job's timeout. |

#### Method Details

##### `__init__`

```python
def __init__(default_timeout_seconds: int = 3600)
```

Initialize timeout manager.

Args:
    default_timeout_seconds: Default timeout (1 hour)

**Parameters:**

- `default_timeout_seconds: int = 3600`

##### `get_remaining_time`

```python
def get_remaining_time(job_id: str) -> Optional[timedelta]
```

Get remaining time before timeout.

**Parameters:**

- `job_id: str` *(required)*

##### `get_timed_out_jobs`

```python
def get_timed_out_jobs() -> List[str]
```

Get list of job IDs that have timed out.

##### `start_tracking`

```python
def start_tracking(job_id: str, timeout_seconds: Optional[int] = None)
```

Start tracking a job's timeout.

**Parameters:**

- `job_id: str` *(required)*
- `timeout_seconds: Optional[int] = None`

##### `stop_tracking`

```python
def stop_tracking(job_id: str)
```

Stop tracking a job's timeout.

**Parameters:**

- `job_id: str` *(required)*

### PriorityQueueItem

**Decorators:** `@dataclass`


Item in the priority queue.
Ordering: higher priority first, then earlier created_at.


**Attributes:**

- `created_at: datetime`
- `job: Job`
- `job_id: str`
- `priority: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_job(job)` | `'PriorityQueueItem'` | Create queue item from job. |

#### Method Details

##### `from_job`

```python
@classmethod
def from_job(job: Job) -> 'PriorityQueueItem'
```

Create queue item from job.

**Parameters:**

- `job: Job` *(required)*

---

## casare_rpa.application.orchestrator.services.metrics_service

**File:** `src\casare_rpa\application\orchestrator\services\metrics_service.py`


Metrics service.
Calculates dashboard KPIs and job history for visualization.


### MetricsService


Service for calculating orchestrator metrics and KPIs.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async calculate_dashboard_metrics(robots, jobs, workflows, ...)` | `DashboardMetrics` | Calculate dashboard KPI metrics. |
| `async calculate_job_history(jobs, days)` | `List[JobHistoryEntry]` | Get job execution history for charting. |

#### Method Details

##### `calculate_dashboard_metrics`

```python
async def calculate_dashboard_metrics(robots: List[Robot], jobs: List[Job], workflows: List[Workflow], schedules: List[Schedule]) -> DashboardMetrics
```

Calculate dashboard KPI metrics.

**Parameters:**

- `robots: List[Robot]` *(required)*
- `jobs: List[Job]` *(required)*
- `workflows: List[Workflow]` *(required)*
- `schedules: List[Schedule]` *(required)*

##### `calculate_job_history`

```python
async def calculate_job_history(jobs: List[Job], days: int = 7) -> List[JobHistoryEntry]
```

Get job execution history for charting.

**Parameters:**

- `jobs: List[Job]` *(required)*
- `days: int = 7`

---

## casare_rpa.application.orchestrator.services.result_collector_service

**File:** `src\casare_rpa\application\orchestrator\services\result_collector_service.py`


Result Collection System for CasareRPA Orchestrator.
Handles job result collection, storage, and analytics.


### ExecutionStatistics

**Decorators:** `@dataclass`


Statistics for job executions.


**Attributes:**

- `avg_duration_ms: float`
- `cancelled: int`
- `executions_per_hour: float`
- `failed: int`
- `max_duration_ms: int`
- `min_duration_ms: int`
- `success_rate: float`
- `successful: int`
- `throughput_per_minute: float`
- `timeout: int`
- `total_duration_ms: int`
- `total_executions: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary. |

#### Method Details

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to dictionary.

### JobResult

**Decorators:** `@dataclass`


Complete result of a job execution.


**Attributes:**

- `completed_at: Optional[datetime]`
- `duration_ms: int`
- `error_message: str`
- `error_type: str`
- `failed_node: str`
- `job_id: str`
- `logs: List[Dict[str, Any]]`
- `metadata: Dict[str, Any]`
- `progress: int`
- `result_data: Dict[str, Any]`
- `robot_id: str`
- `robot_name: str`
- `stack_trace: str`
- `started_at: Optional[datetime]`
- `status: JobStatus`
- `workflow_id: str`
- `workflow_name: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `duration_seconds()` | `float` | Get duration in seconds. |
| `from_dict(data)` | `'JobResult'` | Create from dictionary. |
| `is_success()` | `bool` | Check if job completed successfully. |
| `to_dict()` | `Dict[str, Any]` | Convert to dictionary. |

#### Method Details

##### `duration_seconds`

```python
@property
def duration_seconds() -> float
```

Get duration in seconds.

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'JobResult'
```

Create from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `is_success`

```python
@property
def is_success() -> bool
```

Check if job completed successfully.

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert to dictionary.

### ResultCollector


Collects and processes job results.

Handles:
- Result reception from robots
- Log aggregation
- Statistics computation
- Result persistence


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(max_results, max_logs_per_job)` | - | Initialize result collector. |
| `add_log(job_id, level, message, ...)` | - | Add a log entry for a job. |
| `add_log_batch(job_id, entries)` | - | Add multiple log entries for a job. |
| `clear()` | - | Clear all results. |
| `async collect_cancellation(job, reason)` | `JobResult` | Collect a cancelled job result. |
| `async collect_failure(job, error_message, error_type, ...)` | `JobResult` | Collect a failed job result. |
| `async collect_result(job, result_data, duration_ms)` | `JobResult` | Collect a successful job result. |
| `async collect_timeout(job)` | `JobResult` | Collect a timed-out job result. |
| `get_failed_results(limit)` | `List[JobResult]` | Get recent failed results. |
| `get_hourly_stats(hours, workflow_id)` | `List[Dict[str, Any]]` | Get hourly statistics. |
| `get_recent_results(limit)` | `List[JobResult]` | Get most recent results. |
| `get_result(job_id)` | `Optional[JobResult]` | Get a job result by ID. |
| `get_results_by_robot(robot_id)` | `List[JobResult]` | Get all results for a robot. |
| `get_results_by_workflow(workflow_id)` | `List[JobResult]` | Get all results for a workflow. |
| `get_robot_stats()` | `Dict[str, ExecutionStatistics]` | Get statistics per robot. |
| `get_statistics(workflow_id, robot_id, since)` | `ExecutionStatistics` | Get execution statistics. |
| `get_workflow_stats()` | `Dict[str, ExecutionStatistics]` | Get statistics per workflow. |
| `pending_log_count()` | `int` | Get number of jobs with pending logs. |
| `result_count()` | `int` | Get number of stored results. |
| `set_callbacks(on_result_received, on_result_stored)` | - | Set callbacks for result events. |

#### Method Details

##### `__init__`

```python
def __init__(max_results: int = 10000, max_logs_per_job: int = 1000)
```

Initialize result collector.

Args:
    max_results: Maximum results to keep in memory
    max_logs_per_job: Maximum log entries per job

**Parameters:**

- `max_results: int = 10000`
- `max_logs_per_job: int = 1000`

##### `add_log`

```python
def add_log(job_id: str, level: str, message: str, node_id: str = '', extra: Optional[Dict[str, Any]] = None)
```

Add a log entry for a job.

Args:
    job_id: Job ID
    level: Log level
    message: Log message
    node_id: Associated node ID
    extra: Extra data

**Parameters:**

- `job_id: str` *(required)*
- `level: str` *(required)*
- `message: str` *(required)*
- `node_id: str = ''`
- `extra: Optional[Dict[str, Any]] = None`

##### `add_log_batch`

```python
def add_log_batch(job_id: str, entries: List[Dict[str, Any]])
```

Add multiple log entries for a job.

Args:
    job_id: Job ID
    entries: Log entries

**Parameters:**

- `job_id: str` *(required)*
- `entries: List[Dict[str, Any]]` *(required)*

##### `clear`

```python
def clear()
```

Clear all results.

##### `collect_cancellation`

```python
async def collect_cancellation(job: Job, reason: str = '') -> JobResult
```

Collect a cancelled job result.

Args:
    job: Cancelled job
    reason: Cancellation reason

Returns:
    Created JobResult

**Parameters:**

- `job: Job` *(required)*
- `reason: str = ''`

##### `collect_failure`

```python
async def collect_failure(job: Job, error_message: str, error_type: str = 'ExecutionError', stack_trace: str = '', failed_node: str = '') -> JobResult
```

Collect a failed job result.

Args:
    job: Failed job
    error_message: Error description
    error_type: Error type/category
    stack_trace: Stack trace if available
    failed_node: Node that failed

Returns:
    Created JobResult

**Parameters:**

- `job: Job` *(required)*
- `error_message: str` *(required)*
- `error_type: str = 'ExecutionError'`
- `stack_trace: str = ''`
- `failed_node: str = ''`

##### `collect_result`

```python
async def collect_result(job: Job, result_data: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> JobResult
```

Collect a successful job result.

Args:
    job: Completed job
    result_data: Job output data
    duration_ms: Execution duration

Returns:
    Created JobResult

**Parameters:**

- `job: Job` *(required)*
- `result_data: Optional[Dict[str, Any]] = None`
- `duration_ms: int = 0`

##### `collect_timeout`

```python
async def collect_timeout(job: Job) -> JobResult
```

Collect a timed-out job result.

Args:
    job: Timed-out job

Returns:
    Created JobResult

**Parameters:**

- `job: Job` *(required)*

##### `get_failed_results`

```python
def get_failed_results(limit: int = 100) -> List[JobResult]
```

Get recent failed results.

**Parameters:**

- `limit: int = 100`

##### `get_hourly_stats`

```python
def get_hourly_stats(hours: int = 24, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]
```

Get hourly statistics.

Args:
    hours: Number of hours to look back
    workflow_id: Filter by workflow

Returns:
    List of hourly statistics

**Parameters:**

- `hours: int = 24`
- `workflow_id: Optional[str] = None`

##### `get_recent_results`

```python
def get_recent_results(limit: int = 100) -> List[JobResult]
```

Get most recent results.

**Parameters:**

- `limit: int = 100`

##### `get_result`

```python
def get_result(job_id: str) -> Optional[JobResult]
```

Get a job result by ID.

**Parameters:**

- `job_id: str` *(required)*

##### `get_results_by_robot`

```python
def get_results_by_robot(robot_id: str) -> List[JobResult]
```

Get all results for a robot.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_results_by_workflow`

```python
def get_results_by_workflow(workflow_id: str) -> List[JobResult]
```

Get all results for a workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_robot_stats`

```python
def get_robot_stats() -> Dict[str, ExecutionStatistics]
```

Get statistics per robot.

##### `get_statistics`

```python
def get_statistics(workflow_id: Optional[str] = None, robot_id: Optional[str] = None, since: Optional[datetime] = None) -> ExecutionStatistics
```

Get execution statistics.

Args:
    workflow_id: Filter by workflow
    robot_id: Filter by robot
    since: Only include results after this time

Returns:
    Execution statistics

**Parameters:**

- `workflow_id: Optional[str] = None`
- `robot_id: Optional[str] = None`
- `since: Optional[datetime] = None`

##### `get_workflow_stats`

```python
def get_workflow_stats() -> Dict[str, ExecutionStatistics]
```

Get statistics per workflow.

##### `pending_log_count`

```python
@property
def pending_log_count() -> int
```

Get number of jobs with pending logs.

##### `result_count`

```python
@property
def result_count() -> int
```

Get number of stored results.

##### `set_callbacks`

```python
def set_callbacks(on_result_received: Optional[Callable] = None, on_result_stored: Optional[Callable] = None)
```

Set callbacks for result events.

**Parameters:**

- `on_result_received: Optional[Callable] = None`
- `on_result_stored: Optional[Callable] = None`

### ResultExporter


Exports job results to various formats.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_csv(results)` | `str` | Export results to CSV. |
| `to_json(results, pretty)` | `str` | Export results to JSON. |
| `to_summary(results)` | `Dict[str, Any]` | Generate a summary report. |

#### Method Details

##### `to_csv`

```python
@staticmethod
def to_csv(results: List[JobResult]) -> str
```

Export results to CSV.

**Parameters:**

- `results: List[JobResult]` *(required)*

##### `to_json`

```python
@staticmethod
def to_json(results: List[JobResult], pretty: bool = False) -> str
```

Export results to JSON.

**Parameters:**

- `results: List[JobResult]` *(required)*
- `pretty: bool = False`

##### `to_summary`

```python
@staticmethod
def to_summary(results: List[JobResult]) -> Dict[str, Any]
```

Generate a summary report.

**Parameters:**

- `results: List[JobResult]` *(required)*

---

## casare_rpa.application.orchestrator.services.robot_management_service

**File:** `src\casare_rpa\application\orchestrator\services\robot_management_service.py`


Robot management service.
Handles robot registration, status updates, and availability checks.


### RobotManagementService


Service for managing robot lifecycle and status.
Supports both cloud (Supabase) and local storage modes.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robot_repository)` | - | Initialize with injected repository. |
| `async connect()` | `bool` | Connect to Supabase or fall back to local storage. |
| `async get_available_robots()` | `List[Robot]` | Get robots that can accept new jobs. |
| `async get_robot(robot_id)` | `Optional[Robot]` | Get a specific robot by ID. |
| `async get_robots()` | `List[Robot]` | Get all registered robots. |
| `is_cloud_mode()` | `bool` | Check if using cloud (Supabase) mode. |
| `async update_robot_status(robot_id, status)` | `bool` | Update robot status. |

#### Method Details

##### `__init__`

```python
def __init__(robot_repository: RobotRepository)
```

Initialize with injected repository.

**Parameters:**

- `robot_repository: RobotRepository` *(required)*

##### `connect`

```python
async def connect() -> bool
```

Connect to Supabase or fall back to local storage.

##### `get_available_robots`

```python
async def get_available_robots() -> List[Robot]
```

Get robots that can accept new jobs.

##### `get_robot`

```python
async def get_robot(robot_id: str) -> Optional[Robot]
```

Get a specific robot by ID.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_robots`

```python
async def get_robots() -> List[Robot]
```

Get all registered robots.

##### `is_cloud_mode`

```python
@property
def is_cloud_mode() -> bool
```

Check if using cloud (Supabase) mode.

##### `update_robot_status`

```python
async def update_robot_status(robot_id: str, status: RobotStatus) -> bool
```

Update robot status.

**Parameters:**

- `robot_id: str` *(required)*
- `status: RobotStatus` *(required)*

---

## casare_rpa.application.orchestrator.services.schedule_management_service

**File:** `src\casare_rpa\application\orchestrator\services\schedule_management_service.py`


Schedule management service.
Handles schedule CRUD operations and enable/disable toggling.


### ScheduleManagementService


Service for managing schedules.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(schedule_repository)` | - | Initialize with injected repository. |
| `async connect()` | `bool` | Connect to Supabase or fall back to local storage. |
| `async delete_schedule(schedule_id)` | `bool` | Delete a schedule. |
| `async get_schedule(schedule_id)` | `Optional[Schedule]` | Get a specific schedule by ID. |
| `async get_schedules(enabled_only)` | `List[Schedule]` | Get all schedules. |
| `is_cloud_mode()` | `bool` | Check if using cloud (Supabase) mode. |
| `async save_schedule(schedule)` | `bool` | Save or update a schedule. |
| `async toggle_schedule(schedule_id, enabled)` | `bool` | Enable or disable a schedule. |

#### Method Details

##### `__init__`

```python
def __init__(schedule_repository: ScheduleRepository)
```

Initialize with injected repository.

**Parameters:**

- `schedule_repository: ScheduleRepository` *(required)*

##### `connect`

```python
async def connect() -> bool
```

Connect to Supabase or fall back to local storage.

##### `delete_schedule`

```python
async def delete_schedule(schedule_id: str) -> bool
```

Delete a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_schedule`

```python
async def get_schedule(schedule_id: str) -> Optional[Schedule]
```

Get a specific schedule by ID.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_schedules`

```python
async def get_schedules(enabled_only: bool = False) -> List[Schedule]
```

Get all schedules.

**Parameters:**

- `enabled_only: bool = False`

##### `is_cloud_mode`

```python
@property
def is_cloud_mode() -> bool
```

Check if using cloud (Supabase) mode.

##### `save_schedule`

```python
async def save_schedule(schedule: Schedule) -> bool
```

Save or update a schedule.

**Parameters:**

- `schedule: Schedule` *(required)*

##### `toggle_schedule`

```python
async def toggle_schedule(schedule_id: str, enabled: bool) -> bool
```

Enable or disable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*
- `enabled: bool` *(required)*

---

## casare_rpa.application.orchestrator.services.scheduling_coordinator

**File:** `src\casare_rpa\application\orchestrator\services\scheduling_coordinator.py`


Job Scheduler for CasareRPA Orchestrator.
Implements cron-based scheduling using APScheduler.


### Functions

#### `calculate_next_run`

```python
def calculate_next_run(frequency: ScheduleFrequency, cron_expression: str = '', timezone: str = 'UTC', from_time: Optional[datetime] = None) -> Optional[datetime]
```

Calculate the next run time for a schedule.

Args:
    frequency: Schedule frequency
    cron_expression: Cron expression (for CRON frequency)
    timezone: Timezone
    from_time: Calculate from this time (default: now)

Returns:
    Next run datetime or None if cannot calculate

#### `frequency_to_interval`

```python
def frequency_to_interval(frequency: ScheduleFrequency) -> Optional[timedelta]
```

Convert schedule frequency to timedelta.

#### `parse_cron_expression`

```python
def parse_cron_expression(cron_expr: str) -> Dict[str, str]
```

Parse cron expression into APScheduler trigger kwargs.

Supports standard 5-field cron: minute hour day month weekday
Also supports 6-field with seconds: second minute hour day month weekday

Args:
    cron_expr: Cron expression string

Returns:
    Dict with cron trigger parameters


### JobScheduler


Scheduler for automated job execution.

Features:
- Cron-based scheduling
- Simple frequency scheduling (hourly, daily, weekly, monthly)
- One-time scheduled jobs
- Timezone support
- Schedule enable/disable
- Next run calculation


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(on_schedule_trigger, timezone)` | - | Initialize scheduler. |
| `add_schedule(schedule)` | `bool` | Add a schedule to the scheduler. |
| `disable_schedule(schedule_id)` | `bool` | Disable a schedule. |
| `enable_schedule(schedule_id)` | `bool` | Enable a schedule. |
| `get_next_runs(limit)` | `List[Dict[str, Any]]` | Get upcoming scheduled runs. |
| `get_schedule_info(schedule_id)` | `Optional[Dict[str, Any]]` | Get info about a specific schedule. |
| `pause_all()` | - | Pause all schedules. |
| `remove_schedule(schedule_id)` | `bool` | Remove a schedule from the scheduler. |
| `resume_all()` | - | Resume all schedules. |
| `async start()` | - | Start the scheduler. |
| `async stop()` | - | Stop the scheduler. |
| `update_schedule(schedule)` | `bool` | Update an existing schedule. |

#### Method Details

##### `__init__`

```python
def __init__(on_schedule_trigger: Optional[Callable[[Schedule], Any]] = None, timezone: str = 'UTC')
```

Initialize scheduler.

Args:
    on_schedule_trigger: Callback when schedule triggers (async or sync)
    timezone: Default timezone for schedules

**Parameters:**

- `on_schedule_trigger: Optional[Callable[[Schedule], Any]] = None`
- `timezone: str = 'UTC'`

##### `add_schedule`

```python
def add_schedule(schedule: Schedule) -> bool
```

Add a schedule to the scheduler.

Args:
    schedule: Schedule to add

Returns:
    True if added successfully

**Parameters:**

- `schedule: Schedule` *(required)*

##### `disable_schedule`

```python
def disable_schedule(schedule_id: str) -> bool
```

Disable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `enable_schedule`

```python
def enable_schedule(schedule_id: str) -> bool
```

Enable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_next_runs`

```python
def get_next_runs(limit: int = 10) -> List[Dict[str, Any]]
```

Get upcoming scheduled runs.

Args:
    limit: Maximum number of runs to return

Returns:
    List of upcoming run info

**Parameters:**

- `limit: int = 10`

##### `get_schedule_info`

```python
def get_schedule_info(schedule_id: str) -> Optional[Dict[str, Any]]
```

Get info about a specific schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `pause_all`

```python
def pause_all()
```

Pause all schedules.

##### `remove_schedule`

```python
def remove_schedule(schedule_id: str) -> bool
```

Remove a schedule from the scheduler.

Args:
    schedule_id: Schedule ID to remove

Returns:
    True if removed successfully

**Parameters:**

- `schedule_id: str` *(required)*

##### `resume_all`

```python
def resume_all()
```

Resume all schedules.

##### `start`

```python
async def start()
```

Start the scheduler.

##### `stop`

```python
async def stop()
```

Stop the scheduler.

##### `update_schedule`

```python
def update_schedule(schedule: Schedule) -> bool
```

Update an existing schedule.

Args:
    schedule: Updated schedule

Returns:
    True if updated successfully

**Parameters:**

- `schedule: Schedule` *(required)*

### ScheduleExecutionError

**Inherits from:** `Exception`


Raised when a scheduled job fails to execute.


### ScheduleManager


High-level schedule management.

Combines scheduler with persistence and job creation.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(job_creator, timezone)` | - | Initialize schedule manager. |
| `add_schedule(schedule)` | `bool` | Add a schedule. |
| `disable_schedule(schedule_id)` | `bool` | Disable a schedule. |
| `enable_schedule(schedule_id)` | `bool` | Enable a schedule. |
| `get_all_schedules()` | `List[Schedule]` | Get all schedules. |
| `get_schedule(schedule_id)` | `Optional[Schedule]` | Get a schedule by ID. |
| `get_upcoming_runs(limit)` | `List[Dict[str, Any]]` | Get upcoming scheduled runs. |
| `remove_schedule(schedule_id)` | `bool` | Remove a schedule. |
| `async start()` | - | Start the schedule manager. |
| `async stop()` | - | Stop the schedule manager. |
| `update_schedule(schedule)` | `bool` | Update a schedule. |

#### Method Details

##### `__init__`

```python
def __init__(job_creator: Callable[[Schedule], Any], timezone: str = 'UTC')
```

Initialize schedule manager.

Args:
    job_creator: Function to create jobs from schedules
    timezone: Default timezone

**Parameters:**

- `job_creator: Callable[[Schedule], Any]` *(required)*
- `timezone: str = 'UTC'`

##### `add_schedule`

```python
def add_schedule(schedule: Schedule) -> bool
```

Add a schedule.

**Parameters:**

- `schedule: Schedule` *(required)*

##### `disable_schedule`

```python
def disable_schedule(schedule_id: str) -> bool
```

Disable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `enable_schedule`

```python
def enable_schedule(schedule_id: str) -> bool
```

Enable a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_all_schedules`

```python
def get_all_schedules() -> List[Schedule]
```

Get all schedules.

##### `get_schedule`

```python
def get_schedule(schedule_id: str) -> Optional[Schedule]
```

Get a schedule by ID.

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_upcoming_runs`

```python
def get_upcoming_runs(limit: int = 10) -> List[Dict[str, Any]]
```

Get upcoming scheduled runs.

**Parameters:**

- `limit: int = 10`

##### `remove_schedule`

```python
def remove_schedule(schedule_id: str) -> bool
```

Remove a schedule.

**Parameters:**

- `schedule_id: str` *(required)*

##### `start`

```python
async def start()
```

Start the schedule manager.

##### `stop`

```python
async def stop()
```

Stop the schedule manager.

##### `update_schedule`

```python
def update_schedule(schedule: Schedule) -> bool
```

Update a schedule.

**Parameters:**

- `schedule: Schedule` *(required)*

---

## casare_rpa.application.orchestrator.services.workflow_management_service

**File:** `src\casare_rpa\application\orchestrator\services\workflow_management_service.py`


Workflow management service.
Handles workflow CRUD operations and file imports.


### WorkflowManagementService


Service for managing workflows.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow_repository)` | - | Initialize with injected repository. |
| `async connect()` | `bool` | Connect to Supabase or fall back to local storage. |
| `async delete_workflow(workflow_id)` | `bool` | Delete a workflow. |
| `async get_workflow(workflow_id)` | `Optional[Workflow]` | Get a specific workflow by ID. |
| `async get_workflows(status)` | `List[Workflow]` | Get all workflows. |
| `async import_workflow_from_file(file_path)` | `Optional[Workflow]` | Import a workflow from a JSON file. |
| `is_cloud_mode()` | `bool` | Check if using cloud (Supabase) mode. |
| `async save_workflow(workflow)` | `bool` | Save or update a workflow. |

#### Method Details

##### `__init__`

```python
def __init__(workflow_repository: WorkflowRepository)
```

Initialize with injected repository.

**Parameters:**

- `workflow_repository: WorkflowRepository` *(required)*

##### `connect`

```python
async def connect() -> bool
```

Connect to Supabase or fall back to local storage.

##### `delete_workflow`

```python
async def delete_workflow(workflow_id: str) -> bool
```

Delete a workflow.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_workflow`

```python
async def get_workflow(workflow_id: str) -> Optional[Workflow]
```

Get a specific workflow by ID.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_workflows`

```python
async def get_workflows(status: Optional[WorkflowStatus] = None) -> List[Workflow]
```

Get all workflows.

**Parameters:**

- `status: Optional[WorkflowStatus] = None`

##### `import_workflow_from_file`

```python
async def import_workflow_from_file(file_path: Path) -> Optional[Workflow]
```

Import a workflow from a JSON file.

**Parameters:**

- `file_path: Path` *(required)*

##### `is_cloud_mode`

```python
@property
def is_cloud_mode() -> bool
```

Check if using cloud (Supabase) mode.

##### `save_workflow`

```python
async def save_workflow(workflow: Workflow) -> bool
```

Save or update a workflow.

**Parameters:**

- `workflow: Workflow` *(required)*

---

## casare_rpa.application.orchestrator.use_cases.assign_robot

**File:** `src\casare_rpa\application\orchestrator\use_cases\assign_robot.py`


AssignRobotUseCase - Assign robots to workflows and nodes.

This use case manages the relationship between robots and workflows:
- Assign default robots to workflows
- Create node-level robot overrides for specific routing
- Remove assignments and overrides


### AssignRobotUseCase


Use case for assigning robots to workflows and nodes.

Provides operations for:
- Assigning a robot as the default for a workflow
- Creating node-level robot overrides
- Removing workflow assignments
- Removing node overrides

All operations validate that referenced robots exist before creating
assignments or overrides.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robot_repository, assignment_repository, override_repository)` | `None` | Initialize use case with repositories. |
| `async activate_node_override(workflow_id, node_id)` | `bool` | Reactivate a previously deactivated node override. |
| `async assign_to_node(workflow_id, node_id, robot_id, ...)` | `NodeRobotOverride` | Create a node-level robot override. |
| `async assign_to_workflow(workflow_id, robot_id, is_default, ...)` | `RobotAssignment` | Assign a robot as the default for a workflow. |
| `async deactivate_node_override(workflow_id, node_id)` | `bool` | Deactivate a node override (soft delete). |
| `async get_active_node_overrides(workflow_id)` | `List[NodeRobotOverride]` | Get only active node overrides for a workflow. |
| `async get_node_overrides(workflow_id)` | `List[NodeRobotOverride]` | Get all node overrides for a workflow. |
| `async get_workflow_assignments(workflow_id)` | `List[RobotAssignment]` | Get all robot assignments for a workflow. |
| `async remove_all_node_overrides_for_robot(robot_id)` | `int` | Remove all node overrides targeting a specific robot. |
| `async remove_node_override(workflow_id, node_id)` | `bool` | Remove a node-level robot override. |
| `async remove_workflow_assignment(workflow_id, robot_id)` | `bool` | Remove a workflow-robot assignment. |
| `async set_default_robot(workflow_id, robot_id)` | `None` | Set a specific robot as the default for a workflow. |
| `async unassign_robot_from_all_workflows(robot_id)` | `int` | Remove a robot from all workflow assignments. |

#### Method Details

##### `__init__`

```python
def __init__(robot_repository: RobotRepository, assignment_repository: WorkflowAssignmentRepository, override_repository: NodeOverrideRepository) -> None
```

Initialize use case with repositories.

Args:
    robot_repository: Repository for robot data.
    assignment_repository: Repository for workflow assignments.
    override_repository: Repository for node overrides.

**Parameters:**

- `robot_repository: RobotRepository` *(required)*
- `assignment_repository: WorkflowAssignmentRepository` *(required)*
- `override_repository: NodeOverrideRepository` *(required)*

##### `activate_node_override`

```python
async def activate_node_override(workflow_id: str, node_id: str) -> bool
```

Reactivate a previously deactivated node override.

Args:
    workflow_id: ID of the workflow.
    node_id: ID of the node.

Returns:
    True if override was activated, False if not found.

**Parameters:**

- `workflow_id: str` *(required)*
- `node_id: str` *(required)*

##### `assign_to_node`

```python
async def assign_to_node(workflow_id: str, node_id: str, robot_id: Optional[str] = None, required_capabilities: Optional[List[str]] = None, reason: Optional[str] = None, created_by: str = '') -> NodeRobotOverride
```

Create a node-level robot override.

This allows specific nodes within a workflow to run on different
robots than the workflow's default. Useful for:
- Nodes requiring specific capabilities (GPU, desktop automation)
- Load balancing specific heavy operations
- Routing sensitive operations to secure robots

Args:
    workflow_id: ID of the workflow containing the node.
    node_id: ID of the node to override.
    robot_id: Specific robot to use (None = use capability matching).
    required_capabilities: Required capabilities if robot_id is None.
    reason: Human-readable explanation for the override.
    created_by: User/system creating the override.

Returns:
    Created NodeRobotOverride.

Raises:
    RobotNotFoundError: If specified robot doesn't exist.
    InvalidAssignmentError: If both robot_id and capabilities are None,
        or if parameters are invalid.

**Parameters:**

- `workflow_id: str` *(required)*
- `node_id: str` *(required)*
- `robot_id: Optional[str] = None`
- `required_capabilities: Optional[List[str]] = None`
- `reason: Optional[str] = None`
- `created_by: str = ''`

##### `assign_to_workflow`

```python
async def assign_to_workflow(workflow_id: str, robot_id: str, is_default: bool = True, priority: int = 0, notes: Optional[str] = None, created_by: str = '') -> RobotAssignment
```

Assign a robot as the default for a workflow.

Args:
    workflow_id: ID of the workflow to assign.
    robot_id: ID of the robot to assign.
    is_default: Whether this is the default robot for the workflow.
    priority: Assignment priority (higher = preferred).
    notes: Optional notes about the assignment.
    created_by: User/system making the assignment.

Returns:
    Created RobotAssignment.

Raises:
    RobotNotFoundError: If the robot doesn't exist.
    InvalidAssignmentError: If assignment parameters are invalid.

**Parameters:**

- `workflow_id: str` *(required)*
- `robot_id: str` *(required)*
- `is_default: bool = True`
- `priority: int = 0`
- `notes: Optional[str] = None`
- `created_by: str = ''`

##### `deactivate_node_override`

```python
async def deactivate_node_override(workflow_id: str, node_id: str) -> bool
```

Deactivate a node override (soft delete).

Unlike remove_node_override, this keeps the override in the database
but marks it as inactive. Can be reactivated later.

Args:
    workflow_id: ID of the workflow.
    node_id: ID of the node.

Returns:
    True if override was deactivated, False if not found.

**Parameters:**

- `workflow_id: str` *(required)*
- `node_id: str` *(required)*

##### `get_active_node_overrides`

```python
async def get_active_node_overrides(workflow_id: str) -> List[NodeRobotOverride]
```

Get only active node overrides for a workflow.

Args:
    workflow_id: ID of the workflow.

Returns:
    List of active NodeRobotOverride objects.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_node_overrides`

```python
async def get_node_overrides(workflow_id: str) -> List[NodeRobotOverride]
```

Get all node overrides for a workflow.

Args:
    workflow_id: ID of the workflow.

Returns:
    List of NodeRobotOverride objects.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_workflow_assignments`

```python
async def get_workflow_assignments(workflow_id: str) -> List[RobotAssignment]
```

Get all robot assignments for a workflow.

Args:
    workflow_id: ID of the workflow.

Returns:
    List of RobotAssignment objects.

**Parameters:**

- `workflow_id: str` *(required)*

##### `remove_all_node_overrides_for_robot`

```python
async def remove_all_node_overrides_for_robot(robot_id: str) -> int
```

Remove all node overrides targeting a specific robot.

Useful when decommissioning a robot.

Args:
    robot_id: ID of the robot.

Returns:
    Number of overrides removed.

**Parameters:**

- `robot_id: str` *(required)*

##### `remove_node_override`

```python
async def remove_node_override(workflow_id: str, node_id: str) -> bool
```

Remove a node-level robot override.

Args:
    workflow_id: ID of the workflow.
    node_id: ID of the node.

Returns:
    True if override was removed, False if not found.

**Parameters:**

- `workflow_id: str` *(required)*
- `node_id: str` *(required)*

##### `remove_workflow_assignment`

```python
async def remove_workflow_assignment(workflow_id: str, robot_id: str) -> bool
```

Remove a workflow-robot assignment.

Args:
    workflow_id: ID of the workflow.
    robot_id: ID of the robot to unassign.

Returns:
    True if assignment was removed, False if not found.

**Parameters:**

- `workflow_id: str` *(required)*
- `robot_id: str` *(required)*

##### `set_default_robot`

```python
async def set_default_robot(workflow_id: str, robot_id: str) -> None
```

Set a specific robot as the default for a workflow.

If an assignment already exists, updates it to be the default.
Unsets any other default assignments for the workflow.

Args:
    workflow_id: ID of the workflow.
    robot_id: ID of the robot to set as default.

Raises:
    RobotNotFoundError: If robot doesn't exist.

**Parameters:**

- `workflow_id: str` *(required)*
- `robot_id: str` *(required)*

##### `unassign_robot_from_all_workflows`

```python
async def unassign_robot_from_all_workflows(robot_id: str) -> int
```

Remove a robot from all workflow assignments.

Useful when decommissioning a robot.

Args:
    robot_id: ID of the robot to unassign.

Returns:
    Number of assignments removed.

**Parameters:**

- `robot_id: str` *(required)*

---

## casare_rpa.application.orchestrator.use_cases.execute_job

**File:** `src\casare_rpa\application\orchestrator\use_cases\execute_job.py`


Execute Job use case.


### ExecuteJobUseCase


Use case for executing a job on a robot.

Orchestrates job execution workflow:
1. Validate job exists and can transition to RUNNING
2. Verify robot is available
3. Transition job to RUNNING state
4. Persist state changes


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(job_repository, robot_repository)` | - | Initialize use case with repository dependencies. |
| `async execute(job_id)` | `Job` | Execute a job. |

#### Method Details

##### `__init__`

```python
def __init__(job_repository: JobRepository, robot_repository: RobotRepository)
```

Initialize use case with repository dependencies.

Args:
    job_repository: Repository for job persistence
    robot_repository: Repository for robot data

**Parameters:**

- `job_repository: JobRepository` *(required)*
- `robot_repository: RobotRepository` *(required)*

##### `execute`

```python
async def execute(job_id: str) -> Job
```

Execute a job.

Args:
    job_id: ID of job to execute

Returns:
    Updated job with RUNNING status

Raises:
    ValueError: If job not found
    JobTransitionError: If job cannot transition to RUNNING

**Parameters:**

- `job_id: str` *(required)*

---

## casare_rpa.application.orchestrator.use_cases.execute_local

**File:** `src\casare_rpa\application\orchestrator\use_cases\execute_local.py`


ExecuteLocalUseCase - Execute workflow locally without orchestrator.

This use case provides direct local execution of workflows, bypassing the
orchestrator and job queue. Useful for:
- Canvas "Run" button (F5)
- Testing and development
- Single-machine execution


### ExecuteLocalUseCase


Use case for executing workflows locally.

This is a thin wrapper around ExecuteWorkflowUseCase that provides
a simpler interface for local execution without creating Job entities
or interacting with the orchestrator infrastructure.

Use this when:
- Running workflows from the Canvas UI
- Testing workflows locally
- Single-machine execution without cloud orchestration


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(event_bus)` | `None` | Initialize local execution use case. |
| `async execute(workflow_data, variables, run_to_node_id, ...)` | `ExecutionResult` | Execute a workflow locally. |
| `async execute_from_json(workflow_json, variables, run_to_node_id)` | `ExecutionResult` | Execute a workflow from JSON string. |

#### Method Details

##### `__init__`

```python
def __init__(event_bus: Optional[EventBus] = None) -> None
```

Initialize local execution use case.

Args:
    event_bus: Optional event bus for progress updates.

**Parameters:**

- `event_bus: Optional[EventBus] = None`

##### `execute`

```python
async def execute(workflow_data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None, run_to_node_id: Optional[str] = None, single_node: bool = False, continue_on_error: bool = False, node_timeout: float = 120.0) -> ExecutionResult
```

Execute a workflow locally.

This method does NOT create a Job entity - it performs direct execution.
Progress updates are emitted via the event bus.

Args:
    workflow_data: Serialized workflow dictionary.
    variables: Optional initial variables for execution.
    run_to_node_id: Optional target node ID for partial execution.
        If set, executes only nodes on the path to this node (F4 mode).
    single_node: If True and run_to_node_id is set, execute only that
        single node (F5 mode on single node).
    continue_on_error: Whether to continue execution after node errors.
    node_timeout: Timeout for individual node execution in seconds.

Returns:
    ExecutionResult containing outcome and data.

Raises:
    ValueError: If workflow_data is invalid.

**Parameters:**

- `workflow_data: Dict[str, Any]` *(required)*
- `variables: Optional[Dict[str, Any]] = None`
- `run_to_node_id: Optional[str] = None`
- `single_node: bool = False`
- `continue_on_error: bool = False`
- `node_timeout: float = 120.0`

##### `execute_from_json`

```python
async def execute_from_json(workflow_json: str, variables: Optional[Dict[str, Any]] = None, run_to_node_id: Optional[str] = None) -> ExecutionResult
```

Execute a workflow from JSON string.

Convenience method that parses JSON before execution.

Args:
    workflow_json: JSON string of workflow data.
    variables: Optional initial variables.
    run_to_node_id: Optional target node for partial execution.

Returns:
    ExecutionResult containing outcome and data.

Raises:
    ValueError: If JSON is invalid.

**Parameters:**

- `workflow_json: str` *(required)*
- `variables: Optional[Dict[str, Any]] = None`
- `run_to_node_id: Optional[str] = None`

### ExecutionResult


Result from local workflow execution.

Encapsulates the execution outcome including success status,
output variables, error information, and timing data.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(success, workflow_name, variables, ...)` | `None` | Initialize execution result. |
| `__repr__()` | `str` | String representation. |
| `progress()` | `float` | Get execution progress percentage. |
| `to_dict()` | `Dict[str, Any]` | Convert result to dictionary. |

#### Method Details

##### `__init__`

```python
def __init__(success: bool, workflow_name: str, variables: Dict[str, Any], error: Optional[str] = None, executed_nodes: int = 0, total_nodes: int = 0, duration_ms: int = 0) -> None
```

Initialize execution result.

Args:
    success: Whether execution completed successfully.
    workflow_name: Name of the executed workflow.
    variables: Final workflow variables after execution.
    error: Error message if execution failed.
    executed_nodes: Number of nodes executed.
    total_nodes: Total number of nodes in workflow.
    duration_ms: Execution duration in milliseconds.

**Parameters:**

- `success: bool` *(required)*
- `workflow_name: str` *(required)*
- `variables: Dict[str, Any]` *(required)*
- `error: Optional[str] = None`
- `executed_nodes: int = 0`
- `total_nodes: int = 0`
- `duration_ms: int = 0`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `progress`

```python
@property
def progress() -> float
```

Get execution progress percentage.

Returns:
    Progress as percentage (0-100).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Convert result to dictionary.

Returns:
    Dictionary representation of execution result.

---

## casare_rpa.application.orchestrator.use_cases.list_robots

**File:** `src\casare_rpa\application\orchestrator\use_cases\list_robots.py`


ListRobotsUseCase - List and filter robots.

This use case provides queries for robots with various filtering options:
- Get all registered robots
- Get available robots (can accept jobs)
- Get robots by capability
- Get robots assigned to a workflow


### ListRobotsUseCase


Use case for listing and filtering robots.

Provides read-only queries against the robot repository with
various filtering options. Useful for:
- Robot management UI
- Robot selection dialogs
- Monitoring dashboards


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(robot_repository, assignment_repository)` | `None` | Initialize use case with repositories. |
| `async get_all()` | `List[Robot]` | Get all registered robots. |
| `async get_available()` | `List[Robot]` | Get robots that can accept jobs. |
| `async get_busy()` | `List[Robot]` | Get all busy robots (at max capacity). |
| `async get_by_capabilities(capabilities)` | `List[Robot]` | Get robots with all specified capabilities. |
| `async get_by_capability(capability)` | `List[Robot]` | Get robots with a specific capability. |
| `async get_by_id(robot_id)` | `Optional[Robot]` | Get a specific robot by ID. |
| `async get_by_name(name)` | `Optional[Robot]` | Get a robot by name/hostname. |
| `async get_default_for_workflow(workflow_id)` | `Optional[Robot]` | Get the default robot for a workflow. |
| `async get_for_workflow(workflow_id)` | `List[Robot]` | Get robots assigned to a workflow. |
| `async get_offline()` | `List[Robot]` | Get all offline robots. |
| `async get_online()` | `List[Robot]` | Get all online robots. |
| `async get_statistics()` | `dict` | Get robot fleet statistics. |
| `async get_with_available_capacity(min_capacity)` | `List[Robot]` | Get robots with at least minimum available capacity. |
| `async search(query)` | `List[Robot]` | Search robots by name or tags. |

#### Method Details

##### `__init__`

```python
def __init__(robot_repository: RobotRepository, assignment_repository: Optional[WorkflowAssignmentRepository] = None) -> None
```

Initialize use case with repositories.

Args:
    robot_repository: Repository for robot data.
    assignment_repository: Optional repository for workflow assignments.
        Required for get_for_workflow().

**Parameters:**

- `robot_repository: RobotRepository` *(required)*
- `assignment_repository: Optional[WorkflowAssignmentRepository] = None`

##### `get_all`

```python
async def get_all() -> List[Robot]
```

Get all registered robots.

Returns:
    List of all Robot entities, sorted by name.

##### `get_available`

```python
async def get_available() -> List[Robot]
```

Get robots that can accept jobs.

A robot is available if:
- Status is ONLINE
- Has capacity for more jobs (current_jobs < max_concurrent_jobs)

Returns:
    List of available Robot entities, sorted by load (lowest first).

##### `get_busy`

```python
async def get_busy() -> List[Robot]
```

Get all busy robots (at max capacity).

Returns:
    List of robots with BUSY status.

##### `get_by_capabilities`

```python
async def get_by_capabilities(capabilities: List[RobotCapability]) -> List[Robot]
```

Get robots with all specified capabilities.

Args:
    capabilities: List of required capabilities.

Returns:
    List of robots with all specified capabilities.

**Parameters:**

- `capabilities: List[RobotCapability]` *(required)*

##### `get_by_capability`

```python
async def get_by_capability(capability: RobotCapability) -> List[Robot]
```

Get robots with a specific capability.

Args:
    capability: Required capability to filter by.

Returns:
    List of robots with the specified capability.

**Parameters:**

- `capability: RobotCapability` *(required)*

##### `get_by_id`

```python
async def get_by_id(robot_id: str) -> Optional[Robot]
```

Get a specific robot by ID.

Args:
    robot_id: ID of the robot.

Returns:
    Robot entity or None if not found.

**Parameters:**

- `robot_id: str` *(required)*

##### `get_by_name`

```python
async def get_by_name(name: str) -> Optional[Robot]
```

Get a robot by name/hostname.

Args:
    name: Name or hostname of the robot.

Returns:
    Robot entity or None if not found.

**Parameters:**

- `name: str` *(required)*

##### `get_default_for_workflow`

```python
async def get_default_for_workflow(workflow_id: str) -> Optional[Robot]
```

Get the default robot for a workflow.

Args:
    workflow_id: ID of the workflow.

Returns:
    Default Robot for the workflow, or None if not assigned.

Raises:
    ValueError: If assignment_repository was not provided.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_for_workflow`

```python
async def get_for_workflow(workflow_id: str) -> List[Robot]
```

Get robots assigned to a workflow.

Args:
    workflow_id: ID of the workflow.

Returns:
    List of robots assigned to the workflow.

Raises:
    ValueError: If assignment_repository was not provided.

**Parameters:**

- `workflow_id: str` *(required)*

##### `get_offline`

```python
async def get_offline() -> List[Robot]
```

Get all offline robots.

Returns:
    List of robots with OFFLINE status.

##### `get_online`

```python
async def get_online() -> List[Robot]
```

Get all online robots.

Returns:
    List of robots with ONLINE status.

##### `get_statistics`

```python
async def get_statistics() -> dict
```

Get robot fleet statistics.

Returns:
    Dictionary with fleet statistics.

##### `get_with_available_capacity`

```python
async def get_with_available_capacity(min_capacity: int = 1) -> List[Robot]
```

Get robots with at least minimum available capacity.

Args:
    min_capacity: Minimum number of job slots required.

Returns:
    List of robots with sufficient capacity.

**Parameters:**

- `min_capacity: int = 1`

##### `search`

```python
async def search(query: str) -> List[Robot]
```

Search robots by name or tags.

Args:
    query: Search query string.

Returns:
    List of robots matching the query.

**Parameters:**

- `query: str` *(required)*

---

## casare_rpa.application.orchestrator.use_cases.submit_job

**File:** `src\casare_rpa\application\orchestrator\use_cases\submit_job.py`


SubmitJobUseCase - Submit a job for cloud execution.

This use case orchestrates job submission by:
- Loading workflow assignments and overrides
- Selecting a robot (explicit or auto via RobotSelectionService)
- Creating a Job entity
- Persisting to repository
- Dispatching to robot via dispatcher


### SubmitJobUseCase


Use case for submitting a job for cloud execution.

Orchestrates the complete job submission workflow:
1. Load assignments/overrides for workflow
2. Select robot (explicit or auto via RobotSelectionService)
3. Create Job entity
4. Save to repository
5. Dispatch to robot via dispatcher
6. Return job with status

This use case coordinates domain logic (RobotSelectionService) with
infrastructure (repositories, dispatcher) following Clean Architecture.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(job_repository, robot_repository, assignment_repository, ...)` | `None` | Initialize use case with dependencies. |
| `async execute(workflow_id, workflow_data, robot_id, ...)` | `Job` | Submit a job for execution on a robot. |

#### Method Details

##### `__init__`

```python
def __init__(job_repository: JobRepository, robot_repository: RobotRepository, assignment_repository: WorkflowAssignmentRepository, override_repository: NodeOverrideRepository, robot_selection_service: RobotSelectionService, dispatcher: JobDispatcher) -> None
```

Initialize use case with dependencies.

Args:
    job_repository: Repository for job persistence.
    robot_repository: Repository for robot data.
    assignment_repository: Repository for workflow assignments.
    override_repository: Repository for node overrides.
    robot_selection_service: Domain service for robot selection.
    dispatcher: Job dispatcher for sending jobs to robots.

**Parameters:**

- `job_repository: JobRepository` *(required)*
- `robot_repository: RobotRepository` *(required)*
- `assignment_repository: WorkflowAssignmentRepository` *(required)*
- `override_repository: NodeOverrideRepository` *(required)*
- `robot_selection_service: RobotSelectionService` *(required)*
- `dispatcher: JobDispatcher` *(required)*

##### `execute`

```python
async def execute(workflow_id: str, workflow_data: Dict[str, Any], robot_id: Optional[str] = None, priority: JobPriority = JobPriority.NORMAL, variables: Optional[Dict[str, Any]] = None, timeout_seconds: int = 3600, workflow_name: Optional[str] = None, environment: str = 'default', created_by: str = '', scheduled_time: Optional[datetime] = None) -> Job
```

Submit a job for execution on a robot.

Args:
    workflow_id: ID of the workflow to execute.
    workflow_data: Serialized workflow JSON data.
    robot_id: Optional specific robot ID. If None, auto-selects.
    priority: Job priority level.
    variables: Optional variables to pass to workflow.
    timeout_seconds: Job timeout in seconds.
    workflow_name: Name of the workflow.
    environment: Execution environment.
    created_by: User/system that created the job.
    scheduled_time: Optional scheduled execution time.

Returns:
    Created Job entity with PENDING or QUEUED status.

Raises:
    NoAvailableRobotError: If no suitable robot is available.
    RobotNotFoundError: If specified robot doesn't exist.
    ValueError: If workflow_id is empty or invalid.

**Parameters:**

- `workflow_id: str` *(required)*
- `workflow_data: Dict[str, Any]` *(required)*
- `robot_id: Optional[str] = None`
- `priority: JobPriority = JobPriority.NORMAL`
- `variables: Optional[Dict[str, Any]] = None`
- `timeout_seconds: int = 3600`
- `workflow_name: Optional[str] = None`
- `environment: str = 'default'`
- `created_by: str = ''`
- `scheduled_time: Optional[datetime] = None`

---

## casare_rpa.application.scheduling.schedule_storage

**File:** `src\casare_rpa\application\scheduling\schedule_storage.py`


Schedule Storage for CasareRPA Canvas.
Handles persistence of workflow schedules to JSON files.


### Functions

#### `get_schedule_storage`

```python
def get_schedule_storage() -> ScheduleStorage
```

Get the schedule storage instance.

Returns:
    ScheduleStorage singleton instance

#### `reset_schedule_storage`

```python
def reset_schedule_storage() -> None
```

Reset the schedule storage singleton (for testing).

Clears the singleton so it will be recreated on next access.

#### `set_schedule_storage`

```python
def set_schedule_storage(storage: ScheduleStorage) -> None
```

Set the schedule storage instance (for testing).

Thread-safe replacement of the singleton.

Args:
    storage: ScheduleStorage instance to use


### ScheduleStorage


Handles storage and retrieval of workflow schedules.
Stores schedules in a JSON file in the user's config directory.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(storage_path)` | - | Initialize schedule storage. |
| `delete_schedule(schedule_id)` | `bool` | Delete a schedule by ID. |
| `get_all_schedules()` | `List[WorkflowSchedule]` | Get all saved schedules. |
| `get_due_schedules()` | `List[WorkflowSchedule]` | Get schedules that are due to run. |
| `get_enabled_schedules()` | `List[WorkflowSchedule]` | Get all enabled schedules. |
| `get_schedule(schedule_id)` | `Optional[WorkflowSchedule]` | Get a specific schedule by ID. |
| `get_schedules_for_workflow(workflow_path)` | `List[WorkflowSchedule]` | Get all schedules for a specific workflow. |
| `mark_schedule_run(schedule_id, success, error_message)` | `bool` | Mark a schedule as having run. |
| `save_all_schedules(schedules)` | `bool` | Save all schedules (replaces existing). |
| `save_schedule(schedule)` | `bool` | Save or update a schedule. |

#### Method Details

##### `__init__`

```python
def __init__(storage_path: Optional[Path] = None)
```

Initialize schedule storage.

Args:
    storage_path: Path to schedules JSON file. If None, uses default location.

**Parameters:**

- `storage_path: Optional[Path] = None`

##### `delete_schedule`

```python
def delete_schedule(schedule_id: str) -> bool
```

Delete a schedule by ID.

Args:
    schedule_id: Schedule ID to delete

Returns:
    True if deleted successfully

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_all_schedules`

```python
def get_all_schedules() -> List[WorkflowSchedule]
```

Get all saved schedules.

Returns:
    List of WorkflowSchedule objects

##### `get_due_schedules`

```python
def get_due_schedules() -> List[WorkflowSchedule]
```

Get schedules that are due to run.

Returns:
    List of schedules where next_run <= now

##### `get_enabled_schedules`

```python
def get_enabled_schedules() -> List[WorkflowSchedule]
```

Get all enabled schedules.

Returns:
    List of enabled WorkflowSchedule objects

##### `get_schedule`

```python
def get_schedule(schedule_id: str) -> Optional[WorkflowSchedule]
```

Get a specific schedule by ID.

Args:
    schedule_id: Schedule ID to find

Returns:
    WorkflowSchedule or None if not found

**Parameters:**

- `schedule_id: str` *(required)*

##### `get_schedules_for_workflow`

```python
def get_schedules_for_workflow(workflow_path: str) -> List[WorkflowSchedule]
```

Get all schedules for a specific workflow.

Args:
    workflow_path: Path to the workflow file

Returns:
    List of schedules for this workflow

**Parameters:**

- `workflow_path: str` *(required)*

##### `mark_schedule_run`

```python
def mark_schedule_run(schedule_id: str, success: bool, error_message: str = '') -> bool
```

Mark a schedule as having run.

Updates last_run, run_count, success/failure counts, and calculates next_run.

Args:
    schedule_id: Schedule ID
    success: Whether the run was successful
    error_message: Error message if failed

Returns:
    True if updated successfully

**Parameters:**

- `schedule_id: str` *(required)*
- `success: bool` *(required)*
- `error_message: str = ''`

##### `save_all_schedules`

```python
def save_all_schedules(schedules: List[WorkflowSchedule]) -> bool
```

Save all schedules (replaces existing).

Args:
    schedules: List of schedules to save

Returns:
    True if saved successfully

**Parameters:**

- `schedules: List[WorkflowSchedule]` *(required)*

##### `save_schedule`

```python
def save_schedule(schedule: WorkflowSchedule) -> bool
```

Save or update a schedule.

Args:
    schedule: Schedule to save

Returns:
    True if saved successfully

**Parameters:**

- `schedule: WorkflowSchedule` *(required)*

---

## casare_rpa.application.services.execution_lifecycle_manager

**File:** `src\casare_rpa\application\services\execution_lifecycle_manager.py`


Execution Lifecycle Manager for CasareRPA.

Centralized workflow execution lifecycle management with state machine,
resource cleanup, and browser process tracking.


### ExecutionLifecycleManager


Centralized workflow execution lifecycle management.

Features:
- State machine with atomic transitions
- Force cleanup of previous execution before new F3
- Browser PID tracking for orphan cleanup
- Pause/resume support with asyncio.Event
- Guaranteed cleanup on stop/cancel


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | - | Initialize lifecycle manager. |
| `get_session_info()` | `Optional[dict]` | Get current session information. |
| `get_state()` | `ExecutionState` | Get current execution state. |
| `is_running()` | `bool` | Check if workflow is running. |
| `async pause_workflow()` | `bool` | Pause workflow execution. |
| `async resume_workflow()` | `bool` | Resume paused workflow. |
| `async start_workflow(workflow_runner, force_cleanup, target_node_id, ...)` | `bool` | Start new workflow execution, cleaning up previous if needed... |
| `async start_workflow_run_all(workflow_runner, force_cleanup)` | `bool` | Start parallel execution of all workflows on canvas (Shift+F... |
| `async stop_workflow(force)` | `bool` | Stop workflow execution gracefully or forcefully. |

#### Method Details

##### `__init__`

```python
def __init__()
```

Initialize lifecycle manager.

##### `get_session_info`

```python
def get_session_info() -> Optional[dict]
```

Get current session information.

Returns:
    Dict with session info, or None if no active session

##### `get_state`

```python
def get_state() -> ExecutionState
```

Get current execution state.

Returns:
    Current ExecutionState

##### `is_running`

```python
def is_running() -> bool
```

Check if workflow is running.

Returns:
    True if running or paused

##### `pause_workflow`

```python
async def pause_workflow() -> bool
```

Pause workflow execution.

Returns:
    True if paused successfully, False otherwise

##### `resume_workflow`

```python
async def resume_workflow() -> bool
```

Resume paused workflow.

Returns:
    True if resumed successfully, False otherwise

##### `start_workflow`

```python
async def start_workflow(workflow_runner, force_cleanup: bool = True, target_node_id: Optional[str] = None, single_node: bool = False) -> bool
```

Start new workflow execution, cleaning up previous if needed.

Args:
    workflow_runner: CanvasWorkflowRunner instance
    force_cleanup: Force cleanup of previous execution if still running
    target_node_id: For Run-To-Node (F4), stop at this node.
                    For Run-Single-Node (F5), run only this node.
    single_node: If True, execute only the target_node_id node (F5 mode)

Returns:
    True if started successfully, False otherwise

**Parameters:**

- `workflow_runner` *(required)*
- `force_cleanup: bool = True`
- `target_node_id: Optional[str] = None`
- `single_node: bool = False`

##### `start_workflow_run_all`

```python
async def start_workflow_run_all(workflow_runner, force_cleanup: bool = True) -> bool
```

Start parallel execution of all workflows on canvas (Shift+F3).

When the canvas contains multiple independent workflows (each with its
own StartNode), this executes them all in parallel with SHARED variables
but SEPARATE browser instances.

Args:
    workflow_runner: CanvasWorkflowRunner instance
    force_cleanup: Force cleanup of previous execution if still running

Returns:
    True if started successfully, False otherwise

**Parameters:**

- `workflow_runner` *(required)*
- `force_cleanup: bool = True`

##### `stop_workflow`

```python
async def stop_workflow(force: bool = False) -> bool
```

Stop workflow execution gracefully or forcefully.

Args:
    force: Force stop immediately (cancel task)

Returns:
    True if stopped successfully, False otherwise

**Parameters:**

- `force: bool = False`

### ExecutionSession

**Decorators:** `@dataclass`


Tracks single workflow execution session.

Holds references to task, context, and use_case to enable
proper cleanup and cancellation.


**Attributes:**

- `context: Optional[object]`
- `pause_event: Optional[asyncio.Event]`
- `session_id: str`
- `start_time: datetime`
- `task: asyncio.Task`
- `use_case: Optional[object]`
- `workflow_name: str`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - | Initialize default values. |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

Initialize default values.

### ExecutionState

**Inherits from:** `str`, `Enum`


Execution state machine states.


**Attributes:**

- `CLEANING_UP: str`
- `ERROR: str`
- `FORCE_STOPPING: str`
- `IDLE: str`
- `PAUSED: str`
- `PAUSING: str`
- `RESUMING: str`
- `RUNNING: str`
- `STARTING: str`
- `STOPPING: str`

---

## casare_rpa.application.services.orchestrator_client

**File:** `src\casare_rpa\application\services\orchestrator_client.py`


Orchestrator API client service.

Application layer service that abstracts HTTP communication with the Orchestrator API.
This prevents Presentation layer from directly depending on Infrastructure (aiohttp).

Architecture: Presentation → Application (this) → Infrastructure (aiohttp)


### AiohttpClient


Default HTTP client implementation using aiohttp.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` |  |
| `async close()` | `None` | Close the HTTP session. |
| `async post(url, json)` | `tuple[int, Dict[str, Any], str]` | POST request with JSON payload. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

##### `close`

```python
async def close() -> None
```

Close the HTTP session.

##### `post`

```python
async def post(url: str, json: Dict[str, Any]) -> tuple[int, Dict[str, Any], str]
```

POST request with JSON payload.

**Parameters:**

- `url: str` *(required)*
- `json: Dict[str, Any]` *(required)*

### HttpClient

**Inherits from:** `Protocol`


Protocol for HTTP client abstraction (for testing).


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async close()` | `None` | Close the client and release resources. |
| `async post(url, json)` | `tuple[int, Dict[str, Any], str]` | POST request to URL with JSON payload. |

#### Method Details

##### `close`

```python
async def close() -> None
```

Close the client and release resources.

##### `post`

```python
async def post(url: str, json: Dict[str, Any]) -> tuple[int, Dict[str, Any], str]
```

POST request to URL with JSON payload.

Returns:
    Tuple of (status_code, json_response, error_text)

**Parameters:**

- `url: str` *(required)*
- `json: Dict[str, Any]` *(required)*

### OrchestratorClient


Application layer client for Orchestrator API.

Encapsulates all HTTP communication with the Orchestrator,
providing a clean interface for the Presentation layer.

Usage:
    client = OrchestratorClient(orchestrator_url="http://localhost:8000")
    result = await client.submit_workflow(
        workflow_name="My Workflow",
        workflow_json={"nodes": [...]},
        execution_mode="lan",
    )
    if result.success:
        print(f"Job ID: {result.job_id}")


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(orchestrator_url, http_client)` | `None` | Initialize Orchestrator client. |
| `async close()` | `None` | Close the client and release resources. |
| `async submit_workflow(workflow_name, workflow_json, execution_mode, ...)` | `WorkflowSubmissionResult` | Submit a workflow to the Orchestrator for execution. |

#### Method Details

##### `__init__`

```python
def __init__(orchestrator_url: str = 'http://localhost:8000', http_client: Optional[HttpClient] = None) -> None
```

Initialize Orchestrator client.

Args:
    orchestrator_url: Base URL for Orchestrator API
    http_client: Optional HTTP client (for testing). Uses AiohttpClient by default.

**Parameters:**

- `orchestrator_url: str = 'http://localhost:8000'`
- `http_client: Optional[HttpClient] = None`

##### `close`

```python
async def close() -> None
```

Close the client and release resources.

##### `submit_workflow`

```python
async def submit_workflow(workflow_name: str, workflow_json: Dict[str, Any], execution_mode: str = 'lan', trigger_type: str = 'manual', priority: int = 10, metadata: Optional[Dict[str, Any]] = None) -> WorkflowSubmissionResult
```

Submit a workflow to the Orchestrator for execution.

Args:
    workflow_name: Name of the workflow
    workflow_json: Serialized workflow definition
    execution_mode: "lan" for local robots, "internet" for remote robots
    trigger_type: "manual", "scheduled", or "webhook"
    priority: Job priority (0=highest, 20=lowest)
    metadata: Additional metadata for the job

Returns:
    WorkflowSubmissionResult with success status and IDs

**Parameters:**

- `workflow_name: str` *(required)*
- `workflow_json: Dict[str, Any]` *(required)*
- `execution_mode: str = 'lan'`
- `trigger_type: str = 'manual'`
- `priority: int = 10`
- `metadata: Optional[Dict[str, Any]] = None`

### WorkflowSubmissionResult

**Decorators:** `@dataclass`


Result of workflow submission to Orchestrator.


**Attributes:**

- `error: Optional[str]`
- `job_id: Optional[str]`
- `message: str`
- `schedule_id: Optional[str]`
- `success: bool`
- `workflow_id: Optional[str]`

---

## casare_rpa.application.services.port_type_service

**File:** `src\casare_rpa\application\services\port_type_service.py`


Port Type Service for CasareRPA.

Application layer service providing port type information, compatibility checking,
and visual metadata to the presentation layer. This follows Clean Architecture
by depending only on domain abstractions.


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


### PortTypeRegistry

**Inherits from:** `PortTypeRegistryProtocol`


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

---

## casare_rpa.application.services.template_loader

**File:** `src\casare_rpa\application\services\template_loader.py`


CasareRPA - Application Service: Template Loader
Service for loading and initializing workflow templates.

Handles loading built-in templates from the application directory
and provides access to the template library.


### TemplateLibraryService


High-level service for the template library.

Combines template loading with repository operations for a complete
template management solution.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(loader)` | `None` | Initialize template library service. |
| `browse_templates(category, difficulty, query, ...)` | `List[WorkflowTemplate]` | Browse templates with various filters. |
| `get_featured_templates()` | `List[WorkflowTemplate]` | Get featured/recommended templates. |
| `get_template_for_instantiation(template_id)` | `Optional[WorkflowTemplate]` | Get a template ready for instantiation. |
| `get_templates_for_category_page(category)` | `Dict[str, any]` | Get data for a category page. |
| `initialize()` | `None` | Initialize the template library by loading all templates. |

#### Method Details

##### `__init__`

```python
def __init__(loader: Optional[TemplateLoader] = None) -> None
```

Initialize template library service.

Args:
    loader: Template loader (creates default if None)

**Parameters:**

- `loader: Optional[TemplateLoader] = None`

##### `browse_templates`

```python
def browse_templates(category: Optional[TemplateCategory] = None, difficulty: Optional[str] = None, query: Optional[str] = None, tags: Optional[List[str]] = None, sort_by: str = 'name', limit: int = 50) -> List[WorkflowTemplate]
```

Browse templates with various filters.

Args:
    category: Optional category filter
    difficulty: Optional difficulty filter
    query: Optional search query
    tags: Optional tags filter
    sort_by: Sort field (name, rating, uses, date)
    limit: Maximum results

Returns:
    List of matching templates

**Parameters:**

- `category: Optional[TemplateCategory] = None`
- `difficulty: Optional[str] = None`
- `query: Optional[str] = None`
- `tags: Optional[List[str]] = None`
- `sort_by: str = 'name'`
- `limit: int = 50`

##### `get_featured_templates`

```python
def get_featured_templates() -> List[WorkflowTemplate]
```

Get featured/recommended templates.

Returns templates that are popular, well-rated, or hand-picked.

Returns:
    List of featured templates

##### `get_template_for_instantiation`

```python
def get_template_for_instantiation(template_id: str) -> Optional[WorkflowTemplate]
```

Get a template ready for instantiation.

Args:
    template_id: Template identifier

Returns:
    WorkflowTemplate or None if not found

**Parameters:**

- `template_id: str` *(required)*

##### `get_templates_for_category_page`

```python
def get_templates_for_category_page(category: TemplateCategory) -> Dict[str, any]
```

Get data for a category page.

Args:
    category: Category to display

Returns:
    Dictionary with templates and metadata

**Parameters:**

- `category: TemplateCategory` *(required)*

##### `initialize`

```python
def initialize() -> None
```

Initialize the template library by loading all templates.

### TemplateLoader


Service for loading and managing workflow templates.

Provides a high-level interface for template operations including:
- Loading built-in templates from disk
- Filtering templates by category
- Searching templates by name/tags
- Getting template statistics

Attributes:
    templates_dir: Path to templates directory
    templates: Dictionary of loaded templates by ID


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(templates_dir)` | `None` | Initialize template loader. |
| `get_all_templates()` | `List[WorkflowTemplate]` | Get all loaded templates. |
| `get_categories_with_counts()` | `Dict[str, int]` | Get all categories with template counts. |
| `get_popular_templates(limit)` | `List[WorkflowTemplate]` | Get most popular templates by usage. |
| `get_template(template_id)` | `Optional[WorkflowTemplate]` | Get a template by ID. |
| `get_template_statistics()` | `Dict[str, any]` | Get overall template library statistics. |
| `get_templates_by_category(category)` | `List[WorkflowTemplate]` | Get templates filtered by category. |
| `get_templates_by_difficulty(difficulty)` | `List[WorkflowTemplate]` | Get templates filtered by difficulty level. |
| `get_top_rated_templates(limit, min_ratings)` | `List[WorkflowTemplate]` | Get highest rated templates. |
| `load_templates(force_reload)` | `int` | Load all templates from disk. |
| `reload()` | `int` | Force reload all templates from disk. |
| `search_templates(query, category, tags)` | `List[WorkflowTemplate]` | Search templates by query string. |

#### Method Details

##### `__init__`

```python
def __init__(templates_dir: Optional[Path] = None) -> None
```

Initialize template loader.

Args:
    templates_dir: Path to templates directory. If None, uses default.

**Parameters:**

- `templates_dir: Optional[Path] = None`

##### `get_all_templates`

```python
def get_all_templates() -> List[WorkflowTemplate]
```

Get all loaded templates.

Returns:
    List of all templates

##### `get_categories_with_counts`

```python
def get_categories_with_counts() -> Dict[str, int]
```

Get all categories with template counts.

Returns:
    Dictionary mapping category names to counts

##### `get_popular_templates`

```python
def get_popular_templates(limit: int = 10) -> List[WorkflowTemplate]
```

Get most popular templates by usage.

Args:
    limit: Maximum number of templates to return

Returns:
    List of popular templates sorted by usage

**Parameters:**

- `limit: int = 10`

##### `get_template`

```python
def get_template(template_id: str) -> Optional[WorkflowTemplate]
```

Get a template by ID.

Args:
    template_id: Template identifier

Returns:
    WorkflowTemplate or None if not found

**Parameters:**

- `template_id: str` *(required)*

##### `get_template_statistics`

```python
def get_template_statistics() -> Dict[str, any]
```

Get overall template library statistics.

Returns:
    Dictionary with statistics

##### `get_templates_by_category`

```python
def get_templates_by_category(category: TemplateCategory) -> List[WorkflowTemplate]
```

Get templates filtered by category.

Args:
    category: Category to filter by

Returns:
    List of templates in the category

**Parameters:**

- `category: TemplateCategory` *(required)*

##### `get_templates_by_difficulty`

```python
def get_templates_by_difficulty(difficulty: str) -> List[WorkflowTemplate]
```

Get templates filtered by difficulty level.

Args:
    difficulty: Difficulty level (beginner, intermediate, advanced)

Returns:
    List of templates with the specified difficulty

**Parameters:**

- `difficulty: str` *(required)*

##### `get_top_rated_templates`

```python
def get_top_rated_templates(limit: int = 10, min_ratings: int = 1) -> List[WorkflowTemplate]
```

Get highest rated templates.

Args:
    limit: Maximum number of templates to return
    min_ratings: Minimum number of ratings required

Returns:
    List of top-rated templates

**Parameters:**

- `limit: int = 10`
- `min_ratings: int = 1`

##### `load_templates`

```python
def load_templates(force_reload: bool = False) -> int
```

Load all templates from disk.

Args:
    force_reload: If True, reload even if already loaded

Returns:
    Number of templates loaded

**Parameters:**

- `force_reload: bool = False`

##### `reload`

```python
def reload() -> int
```

Force reload all templates from disk.

Returns:
    Number of templates loaded

##### `search_templates`

```python
def search_templates(query: str, category: Optional[TemplateCategory] = None, tags: Optional[List[str]] = None) -> List[WorkflowTemplate]
```

Search templates by query string.

Searches template name, description, and tags.

Args:
    query: Search query string
    category: Optional category filter
    tags: Optional tags filter

Returns:
    List of matching templates

**Parameters:**

- `query: str` *(required)*
- `category: Optional[TemplateCategory] = None`
- `tags: Optional[List[str]] = None`

---

## casare_rpa.application.use_cases.error_recovery

**File:** `src\casare_rpa\application\use_cases\error_recovery.py`


CasareRPA - Error Recovery Orchestration Use Case

Coordinates error handling and recovery across domain and infrastructure layers.

This use case:
- Receives errors from node execution
- Uses ErrorHandlerRegistry (domain) for classification
- Uses RecoveryStrategyRegistry (infrastructure) for recovery execution
- Emits events for monitoring and logging
- Manages error aggregation and reporting

Architecture:
- Application layer: Orchestrates domain and infrastructure
- Domain: Error classification and handler decisions
- Infrastructure: Recovery strategy execution and screenshots


### Functions

#### `handle_node_error`

```python
async def handle_node_error(exception: Exception, node_id: NodeId, node_type: str, execution_context: 'ExecutionContext', **kwargs: Any) -> RecoveryResult
```

Handle a node error using the global error recovery system.

Convenience function for simple error handling without explicit use case creation.

Args:
    exception: The exception that occurred.
    node_id: ID of the node where error occurred.
    node_type: Type/class name of the node.
    execution_context: Current execution context.
    **kwargs: Additional arguments passed to handle_error.

Returns:
    RecoveryResult indicating what action was taken.


### ErrorAggregation

**Decorators:** `@dataclass`


Aggregates similar errors for reporting.


**Attributes:**

- `count: int`
- `error_key: str`
- `first_occurrence: datetime`
- `last_occurrence: datetime`
- `node_ids: Set[NodeId]`
- `sample_context: Optional[ErrorContext]`

### ErrorRecoveryConfig

**Decorators:** `@dataclass`


Configuration for error recovery orchestration.


**Attributes:**

- `circuit_breaker_failure_threshold: int`
- `circuit_breaker_recovery_seconds: float`
- `enable_auto_retry: bool`
- `enable_circuit_breaker: bool`
- `enable_escalation: bool`
- `enable_screenshots: bool`
- `error_aggregation_window_seconds: float`
- `max_consecutive_errors: int`

### ErrorRecoveryIntegration


Integration helper for connecting error recovery to workflow execution.

Provides convenience methods for common integration patterns.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(config)` | `None` | Initialize integration. |
| `create_custom_handler(name, handler_func)` | `None` | Register a custom error handler. |
| `get_report()` | `Dict[str, Any]` | Get error report. |
| `set_execution_context(context)` | `None` | Set the execution context for recovery operations. |
| `async wrap_node_execution(node_id, node_type, execute_func, ...)` | `tuple[bool, Any]` | Wrap node execution with automatic error handling. |

#### Method Details

##### `__init__`

```python
def __init__(config: Optional[ErrorRecoveryConfig] = None) -> None
```

Initialize integration.

Args:
    config: Recovery configuration.

**Parameters:**

- `config: Optional[ErrorRecoveryConfig] = None`

##### `create_custom_handler`

```python
def create_custom_handler(name: str, handler_func: Callable[[ErrorContext], Optional[RecoveryDecision]]) -> None
```

Register a custom error handler.

Args:
    name: Handler name.
    handler_func: Function that takes ErrorContext and returns RecoveryDecision.

**Parameters:**

- `name: str` *(required)*
- `handler_func: Callable[[ErrorContext], Optional[RecoveryDecision]]` *(required)*

##### `get_report`

```python
def get_report() -> Dict[str, Any]
```

Get error report.

##### `set_execution_context`

```python
def set_execution_context(context: 'ExecutionContext') -> None
```

Set the execution context for recovery operations.

Args:
    context: Current execution context.

**Parameters:**

- `context: 'ExecutionContext'` *(required)*

##### `wrap_node_execution`

```python
async def wrap_node_execution(node_id: NodeId, node_type: str, execute_func: Callable[..., Any], node_config: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> tuple[bool, Any]
```

Wrap node execution with automatic error handling.

Args:
    node_id: Node ID.
    node_type: Node type name.
    execute_func: Async function to execute.
    node_config: Node configuration.
    max_retries: Maximum retry attempts.

Returns:
    Tuple of (success, result_or_error).

**Parameters:**

- `node_id: NodeId` *(required)*
- `node_type: str` *(required)*
- `execute_func: Callable[..., Any]` *(required)*
- `node_config: Optional[Dict[str, Any]] = None`
- `max_retries: int = 3`

### ErrorRecoveryUseCase


Application use case for error recovery orchestration.

Coordinates:
- Domain: ErrorHandlerRegistry for classification and decisions
- Infrastructure: RecoveryStrategyRegistry for recovery execution
- Events: Progress and error notifications


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(config, error_registry, strategy_registry, ...)` | `None` | Initialize error recovery use case. |
| `get_error_report()` | `Dict[str, Any]` | Get comprehensive error report. |
| `get_node_error_history(node_id, limit)` | `List[Dict[str, Any]]` | Get error history for a specific node. |
| `async handle_error(exception, node_id, node_type, ...)` | `RecoveryResult` | Handle an error during node execution. |
| `record_success(node_id, node_type)` | `None` | Record successful node execution. |
| `reset()` | `None` | Reset all error tracking state. |

#### Method Details

##### `__init__`

```python
def __init__(config: Optional[ErrorRecoveryConfig] = None, error_registry: Optional[ErrorHandlerRegistry] = None, strategy_registry: Optional[RecoveryStrategyRegistry] = None, event_bus: Optional[EventBus] = None) -> None
```

Initialize error recovery use case.

Args:
    config: Recovery configuration.
    error_registry: Error handler registry (domain).
    strategy_registry: Recovery strategy registry (infrastructure).
    event_bus: Event bus for notifications.

**Parameters:**

- `config: Optional[ErrorRecoveryConfig] = None`
- `error_registry: Optional[ErrorHandlerRegistry] = None`
- `strategy_registry: Optional[RecoveryStrategyRegistry] = None`
- `event_bus: Optional[EventBus] = None`

##### `get_error_report`

```python
def get_error_report() -> Dict[str, Any]
```

Get comprehensive error report.

Returns:
    Dictionary with error statistics and aggregations.

##### `get_node_error_history`

```python
def get_node_error_history(node_id: NodeId, limit: int = 10) -> List[Dict[str, Any]]
```

Get error history for a specific node.

Args:
    node_id: Node ID to query.
    limit: Maximum results.

Returns:
    List of error contexts as dictionaries.

**Parameters:**

- `node_id: NodeId` *(required)*
- `limit: int = 10`

##### `handle_error`

```python
async def handle_error(exception: Exception, node_id: NodeId, node_type: str, execution_context: 'ExecutionContext', node_config: Optional[Dict[str, Any]] = None, execution_time_ms: float = 0.0, additional_data: Optional[Dict[str, Any]] = None) -> RecoveryResult
```

Handle an error during node execution.

This is the main entry point for error handling.

Args:
    exception: The exception that occurred.
    node_id: ID of the node where error occurred.
    node_type: Type/class name of the node.
    execution_context: Current execution context.
    node_config: Node configuration.
    execution_time_ms: How long the operation ran.
    additional_data: Extra context (URL, selector, etc.).

Returns:
    RecoveryResult indicating what action was taken.

**Parameters:**

- `exception: Exception` *(required)*
- `node_id: NodeId` *(required)*
- `node_type: str` *(required)*
- `execution_context: 'ExecutionContext'` *(required)*
- `node_config: Optional[Dict[str, Any]] = None`
- `execution_time_ms: float = 0.0`
- `additional_data: Optional[Dict[str, Any]] = None`

##### `record_success`

```python
def record_success(node_id: NodeId, node_type: str) -> None
```

Record successful node execution.

Call this after a node succeeds to:
- Reset consecutive error counter
- Clear retry count for the node
- Update circuit breaker

Args:
    node_id: Node that succeeded.
    node_type: Type of the node.

**Parameters:**

- `node_id: NodeId` *(required)*
- `node_type: str` *(required)*

##### `reset`

```python
def reset() -> None
```

Reset all error tracking state.

### RecoveryResult

**Decorators:** `@dataclass`


Result of a recovery attempt.


**Attributes:**

- `action_taken: RecoveryAction`
- `error_context: Optional[ErrorContext]`
- `message: str`
- `next_node_id: Optional[NodeId]`
- `retry_delay_ms: int`
- `should_abort: bool`
- `should_retry: bool`
- `should_skip: bool`
- `success: bool`

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

## casare_rpa.application.use_cases.execute_workflow

**File:** `src\casare_rpa\application\use_cases\execute_workflow.py`


CasareRPA - Application Use Case: Execute Workflow
Coordinates workflow execution across domain and infrastructure layers.

This use case orchestrates workflow execution by:
- Using ExecutionOrchestrator (domain) for routing decisions
- Using ExecutionContext (infrastructure) for execution and resources
- Using helper services for node execution, state management, and data transfer
- Emitting events via EventBus for progress tracking

Architecture:
- Domain logic: ExecutionOrchestrator makes routing decisions
- Infrastructure: ExecutionContext manages Playwright resources
- Application: This class coordinates them and publishes events

Refactored: Extracted helper services for Single Responsibility:
- ExecutionStateManager: State tracking, progress, pause/resume
- NodeExecutor: Node execution with metrics and lifecycle events
- VariableResolver: Data transfer between nodes, port validation


### ExecuteWorkflowUseCase


Application use case for executing workflows.

Coordinates:
- Domain: ExecutionOrchestrator for routing logic
- Domain: Workflow schema for node/connection data
- Infrastructure: ExecutionContext for resources and variables
- Infrastructure: EventBus for progress notifications
- Services: ExecutionStateManager, NodeExecutor, VariableResolver


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow, event_bus, settings, ...)` | `None` | Initialize execute workflow use case. |
| `__repr__()` | `str` | String representation. |
| `current_node_id()` | `Optional[NodeId]` | Get current node ID. |
| `end_time()` | `Optional[datetime]` | Get end time. |
| `async execute(run_all)` | `bool` | Execute the workflow. |
| `executed_nodes()` | `Set[NodeId]` | Get executed nodes set. |
| `start_time()` | `Optional[datetime]` | Get start time. |
| `stop()` | `None` | Stop workflow execution. |

#### Method Details

##### `__init__`

```python
def __init__(workflow: WorkflowSchema, event_bus: Optional[EventBus] = None, settings: Optional[ExecutionSettings] = None, initial_variables: Optional[Dict[str, Any]] = None, project_context: Optional[Any] = None, pause_event: Optional[asyncio.Event] = None) -> None
```

Initialize execute workflow use case.

Args:
    workflow: Workflow schema to execute
    event_bus: Optional event bus for progress updates
    settings: Execution settings
    initial_variables: Optional dict of variables to initialize
    project_context: Optional project context for scoped variables
    pause_event: Optional event for pause/resume coordination

**Parameters:**

- `workflow: WorkflowSchema` *(required)*
- `event_bus: Optional[EventBus] = None`
- `settings: Optional[ExecutionSettings] = None`
- `initial_variables: Optional[Dict[str, Any]] = None`
- `project_context: Optional[Any] = None`
- `pause_event: Optional[asyncio.Event] = None`

##### `__repr__`

```python
def __repr__() -> str
```

String representation.

##### `current_node_id`

```python
@property
def current_node_id() -> Optional[NodeId]
```

Get current node ID.

##### `end_time`

```python
@property
def end_time() -> Optional[datetime]
```

Get end time.

##### `execute`

```python
async def execute(run_all: bool = False) -> bool
```

Execute the workflow.

Args:
    run_all: If True, execute all StartNodes concurrently (Shift+F3).
             If False, execute only the first StartNode (default F3).

Returns:
    True if workflow completed successfully, False otherwise

**Parameters:**

- `run_all: bool = False`

##### `executed_nodes`

```python
@property
def executed_nodes() -> Set[NodeId]
```

Get executed nodes set.

##### `start_time`

```python
@property
def start_time() -> Optional[datetime]
```

Get start time.

##### `stop`

```python
def stop() -> None
```

Stop workflow execution.

---

## casare_rpa.application.use_cases.execution_state_manager

**File:** `src\casare_rpa\application\use_cases\execution_state_manager.py`


CasareRPA - Execution State Manager

Manages execution state including:
- Execution settings (timeout, continue_on_error, target node)
- Progress tracking (executed nodes, current node)
- Subgraph calculation for Run-To-Node feature
- Pause/resume coordination

Extracted from ExecuteWorkflowUseCase for Single Responsibility.


### ExecutionSettings


Execution settings value object.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(continue_on_error, node_timeout, target_node_id, ...)` | `None` | Initialize execution settings. |

#### Method Details

##### `__init__`

```python
def __init__(continue_on_error: bool = False, node_timeout: float = 120.0, target_node_id: Optional[NodeId] = None, single_node: bool = False) -> None
```

Initialize execution settings.

Args:
    continue_on_error: If True, continue workflow on node errors
    node_timeout: Timeout for individual node execution in seconds
    target_node_id: Optional target node for Run-To-Node (F4) or Run-Single-Node (F5)
    single_node: If True, execute only target_node_id (F5 mode)

**Parameters:**

- `continue_on_error: bool = False`
- `node_timeout: float = 120.0`
- `target_node_id: Optional[NodeId] = None`
- `single_node: bool = False`

### ExecutionStateManager


Manages execution state and progress tracking.

Responsibilities:
- Track executed nodes and current node
- Calculate subgraph for Run-To-Node feature
- Manage pause/resume state
- Emit progress events
- Track execution timing


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow, orchestrator, event_bus, ...)` | `None` | Initialize execution state manager. |
| `calculate_progress()` | `float` | Calculate execution progress as percentage. |
| `duration()` | `float` | Get execution duration in seconds. |
| `emit_event(event_type, data, node_id)` | `None` | Emit an event to the event bus. |
| `execution_error()` | `Optional[str]` | Get execution error message. |
| `get_execution_summary()` | `Dict[str, Any]` | Get execution summary. |
| `is_failed()` | `bool` | Check if execution failed. |
| `is_stopped()` | `bool` | Check if stop was requested. |
| `mark_completed()` | `None` | Mark execution as completed. |
| `mark_failed(error)` | `None` | Mark execution as failed with error. |
| `mark_node_executed(node_id)` | `None` | Mark a node as executed. |
| `mark_target_reached(node_id)` | `bool` | Check and mark if target node was reached. |
| `async pause_checkpoint()` | `None` | Pause checkpoint - wait if pause_event is cleared. |
| `set_current_node(node_id)` | `None` | Set the currently executing node. |
| `should_execute_node(node_id)` | `bool` | Check if a node should be executed based on subgraph filteri... |
| `start_execution()` | `None` | Mark execution as started. |
| `stop()` | `None` | Request execution stop. |
| `target_reached()` | `bool` | Check if target node was reached. |
| `total_nodes()` | `int` | Get total nodes to execute. |

#### Method Details

##### `__init__`

```python
def __init__(workflow: WorkflowSchema, orchestrator: ExecutionOrchestrator, event_bus: Optional[EventBus] = None, settings: Optional[ExecutionSettings] = None, pause_event: Optional[asyncio.Event] = None) -> None
```

Initialize execution state manager.

Args:
    workflow: Workflow schema being executed
    orchestrator: Domain orchestrator for routing decisions
    event_bus: Optional event bus for progress updates
    settings: Execution settings
    pause_event: Optional event for pause/resume coordination

**Parameters:**

- `workflow: WorkflowSchema` *(required)*
- `orchestrator: ExecutionOrchestrator` *(required)*
- `event_bus: Optional[EventBus] = None`
- `settings: Optional[ExecutionSettings] = None`
- `pause_event: Optional[asyncio.Event] = None`

##### `calculate_progress`

```python
def calculate_progress() -> float
```

Calculate execution progress as percentage.

Returns:
    Progress percentage (0-100)

##### `duration`

```python
@property
def duration() -> float
```

Get execution duration in seconds.

##### `emit_event`

```python
def emit_event(event_type: EventType, data: Dict[str, Any], node_id: Optional[NodeId] = None) -> None
```

Emit an event to the event bus.

Args:
    event_type: Type of event
    data: Event data payload
    node_id: Optional node ID associated with event

**Parameters:**

- `event_type: EventType` *(required)*
- `data: Dict[str, Any]` *(required)*
- `node_id: Optional[NodeId] = None`

##### `execution_error`

```python
@property
def execution_error() -> Optional[str]
```

Get execution error message.

##### `get_execution_summary`

```python
def get_execution_summary() -> Dict[str, Any]
```

Get execution summary.

Returns:
    Dictionary with execution statistics

##### `is_failed`

```python
@property
def is_failed() -> bool
```

Check if execution failed.

##### `is_stopped`

```python
@property
def is_stopped() -> bool
```

Check if stop was requested.

##### `mark_completed`

```python
def mark_completed() -> None
```

Mark execution as completed.

##### `mark_failed`

```python
def mark_failed(error: str) -> None
```

Mark execution as failed with error.

**Parameters:**

- `error: str` *(required)*

##### `mark_node_executed`

```python
def mark_node_executed(node_id: NodeId) -> None
```

Mark a node as executed.

**Parameters:**

- `node_id: NodeId` *(required)*

##### `mark_target_reached`

```python
def mark_target_reached(node_id: NodeId) -> bool
```

Check and mark if target node was reached.

Args:
    node_id: Node ID that just completed

Returns:
    True if this was the target node

**Parameters:**

- `node_id: NodeId` *(required)*

##### `pause_checkpoint`

```python
async def pause_checkpoint() -> None
```

Pause checkpoint - wait if pause_event is cleared.

This method should be called between nodes and optionally
during long-running node operations to support pause/resume.

##### `set_current_node`

```python
def set_current_node(node_id: Optional[NodeId]) -> None
```

Set the currently executing node.

**Parameters:**

- `node_id: Optional[NodeId]` *(required)*

##### `should_execute_node`

```python
def should_execute_node(node_id: NodeId) -> bool
```

Check if a node should be executed based on subgraph filtering.

Args:
    node_id: Node ID to check

Returns:
    True if node should be executed

**Parameters:**

- `node_id: NodeId` *(required)*

##### `start_execution`

```python
def start_execution() -> None
```

Mark execution as started.

##### `stop`

```python
def stop() -> None
```

Request execution stop.

##### `target_reached`

```python
@property
def target_reached() -> bool
```

Check if target node was reached.

##### `total_nodes`

```python
@property
def total_nodes() -> int
```

Get total nodes to execute.

---

## casare_rpa.application.use_cases.node_executor

**File:** `src\casare_rpa\application\use_cases\node_executor.py`


CasareRPA - Node Executor

Handles individual node execution including:
- Node validation and execution with timeout
- Status tracking and metrics recording
- Event emission for node lifecycle
- Bypass handling for disabled nodes

Extracted from ExecuteWorkflowUseCase for Single Responsibility.


### NodeExecutionResult


Result of a node execution.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(success, result, execution_time, ...)` | `None` | Initialize node execution result. |

#### Method Details

##### `__init__`

```python
def __init__(success: bool, result: Optional[Dict[str, Any]] = None, execution_time: float = 0.0, error_captured: bool = False) -> None
```

Initialize node execution result.

Args:
    success: Whether execution succeeded
    result: Result dictionary from node
    execution_time: Execution time in seconds
    error_captured: Whether error was captured by try-catch

**Parameters:**

- `success: bool` *(required)*
- `result: Optional[Dict[str, Any]] = None`
- `execution_time: float = 0.0`
- `error_captured: bool = False`

### NodeExecutor


Executes individual nodes with proper lifecycle management.

Responsibilities:
- Execute nodes with timeout
- Validate nodes before execution
- Track execution metrics
- Emit lifecycle events
- Handle bypassed/disabled nodes


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(context, event_bus, node_timeout, ...)` | `None` | Initialize node executor. |
| `async execute(node)` | `NodeExecutionResult` | Execute a single node with full lifecycle management. |

#### Method Details

##### `__init__`

```python
def __init__(context: ExecutionContext, event_bus: Optional[EventBus] = None, node_timeout: float = 120.0, progress_calculator: Optional[callable] = None) -> None
```

Initialize node executor.

Args:
    context: Execution context with resources and variables
    event_bus: Optional event bus for lifecycle events
    node_timeout: Timeout for individual node execution in seconds
    progress_calculator: Optional callable to calculate progress percentage

**Parameters:**

- `context: ExecutionContext` *(required)*
- `event_bus: Optional[EventBus] = None`
- `node_timeout: float = 120.0`
- `progress_calculator: Optional[callable] = None`

##### `execute`

```python
async def execute(node: Any) -> NodeExecutionResult
```

Execute a single node with full lifecycle management.

Args:
    node: The node instance to execute

Returns:
    NodeExecutionResult with success status and result data

**Parameters:**

- `node: Any` *(required)*

### NodeExecutorWithTryCatch

**Inherits from:** `NodeExecutor`


Extended NodeExecutor with try-catch block error capture.

Handles error capture for nodes inside try-catch blocks,
allowing errors to be routed to catch nodes instead of
failing the workflow.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(context, event_bus, node_timeout, ...)` | `None` | Initialize node executor with try-catch support. |

#### Method Details

##### `__init__`

```python
def __init__(context: ExecutionContext, event_bus: Optional[EventBus] = None, node_timeout: float = 120.0, progress_calculator: Optional[callable] = None, error_capturer: Optional[callable] = None) -> None
```

Initialize node executor with try-catch support.

Args:
    context: Execution context
    event_bus: Optional event bus for events
    node_timeout: Timeout for node execution
    progress_calculator: Optional callable for progress
    error_capturer: Callable to capture errors in try blocks

**Parameters:**

- `context: ExecutionContext` *(required)*
- `event_bus: Optional[EventBus] = None`
- `node_timeout: float = 120.0`
- `progress_calculator: Optional[callable] = None`
- `error_capturer: Optional[callable] = None`

---

## casare_rpa.application.use_cases.project_management

**File:** `src\casare_rpa\application\use_cases\project_management.py`


CasareRPA - Project Management Use Cases

Application layer use cases for project CRUD operations.
Orchestrates domain entities and infrastructure persistence.


### CreateProjectUseCase


Create a new project.

Creates folder structure, initializes project metadata,
and registers project in the index.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(name, path, description, ...)` | `ProjectResult` | Create a new project. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

Args:
    repository: Project repository for persistence

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(name: str, path: Path, description: str = '', author: str = '', tags: Optional[List[str]] = None) -> ProjectResult
```

Create a new project.

Args:
    name: Project name
    path: Path to project folder
    description: Project description
    author: Project author
    tags: List of tags

Returns:
    ProjectResult with created project or error

**Parameters:**

- `name: str` *(required)*
- `path: Path` *(required)*
- `description: str = ''`
- `author: str = ''`
- `tags: Optional[List[str]] = None`

### CreateScenarioUseCase


Create a new scenario in a project.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, name, workflow, ...)` | `ScenarioResult` | Create a new scenario. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str, name: str, workflow: Optional[dict] = None, tags: Optional[List[str]] = None) -> ScenarioResult
```

Create a new scenario.

Args:
    project_id: Parent project ID
    name: Scenario name
    workflow: Optional workflow dict to include
    tags: Optional tags

Returns:
    ScenarioResult with created scenario or error

**Parameters:**

- `project_id: str` *(required)*
- `name: str` *(required)*
- `workflow: Optional[dict] = None`
- `tags: Optional[List[str]] = None`

### DeleteProjectUseCase


Delete a project.

Removes from index and optionally deletes files.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, remove_files)` | `ProjectResult` | Delete a project. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str, remove_files: bool = False) -> ProjectResult
```

Delete a project.

Args:
    project_id: Project ID to delete
    remove_files: If True, also delete project folder from disk

Returns:
    ProjectResult indicating success or error

**Parameters:**

- `project_id: str` *(required)*
- `remove_files: bool = False`

### DeleteScenarioUseCase


Delete a scenario from a project.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, scenario_id)` | `ScenarioResult` | Delete a scenario. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str, scenario_id: str) -> ScenarioResult
```

Delete a scenario.

Args:
    project_id: Parent project ID
    scenario_id: Scenario ID to delete

Returns:
    ScenarioResult indicating success or error

**Parameters:**

- `project_id: str` *(required)*
- `scenario_id: str` *(required)*

### ListProjectsUseCase


List all registered projects.

Returns projects sorted by last_opened timestamp.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(limit)` | `ProjectListResult` | List projects. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(limit: Optional[int] = None) -> ProjectListResult
```

List projects.

Args:
    limit: Maximum number of projects to return

Returns:
    ProjectListResult with list of projects

**Parameters:**

- `limit: Optional[int] = None`

### ListScenariosUseCase


List all scenarios in a project.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id)` | `List[Scenario]` | List scenarios in a project. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str) -> List[Scenario]
```

List scenarios in a project.

Args:
    project_id: Project ID

Returns:
    List of scenarios

**Parameters:**

- `project_id: str` *(required)*

### LoadProjectUseCase


Load an existing project.

Loads project metadata and updates last_opened timestamp.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, path)` | `ProjectResult` | Load a project by ID or path. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: Optional[str] = None, path: Optional[Path] = None) -> ProjectResult
```

Load a project by ID or path.

Args:
    project_id: Project ID (preferred)
    path: Path to project folder (fallback)

Returns:
    ProjectResult with loaded project or error

**Parameters:**

- `project_id: Optional[str] = None`
- `path: Optional[Path] = None`

### LoadScenarioUseCase


Load a scenario from a project.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, scenario_id)` | `ScenarioResult` | Load a scenario. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str, scenario_id: str) -> ScenarioResult
```

Load a scenario.

Args:
    project_id: Parent project ID
    scenario_id: Scenario ID

Returns:
    ScenarioResult with loaded scenario or error

**Parameters:**

- `project_id: str` *(required)*
- `scenario_id: str` *(required)*

### ProjectListResult

**Decorators:** `@dataclass`


Result of listing projects.


**Attributes:**

- `error: Optional[str]`
- `projects: List[Project]`
- `success: bool`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__post_init__()` | - |  |

#### Method Details

##### `__post_init__`

```python
def __post_init__()
```

### ProjectResult

**Decorators:** `@dataclass`


Result of a project operation.


**Attributes:**

- `error: Optional[str]`
- `project: Optional[Project]`
- `success: bool`

### SaveProjectUseCase


Save project changes.

Updates project metadata and modified timestamp.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project)` | `ProjectResult` | Save project. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project: Project) -> ProjectResult
```

Save project.

Args:
    project: Project to save

Returns:
    ProjectResult with saved project or error

**Parameters:**

- `project: Project` *(required)*

### SaveScenarioUseCase


Save scenario changes.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(project_id, scenario)` | `ScenarioResult` | Save scenario. |

#### Method Details

##### `__init__`

```python
def __init__(repository: ProjectRepository) -> None
```

Initialize use case.

**Parameters:**

- `repository: ProjectRepository` *(required)*

##### `execute`

```python
async def execute(project_id: str, scenario: Scenario) -> ScenarioResult
```

Save scenario.

Args:
    project_id: Parent project ID
    scenario: Scenario to save

Returns:
    ScenarioResult with saved scenario or error

**Parameters:**

- `project_id: str` *(required)*
- `scenario: Scenario` *(required)*

### ScenarioResult

**Decorators:** `@dataclass`


Result of a scenario operation.


**Attributes:**

- `error: Optional[str]`
- `scenario: Optional[Scenario]`
- `success: bool`

---

## casare_rpa.application.use_cases.template_management

**File:** `src\casare_rpa\application\use_cases\template_management.py`


CasareRPA - Application Use Cases: Template Management

Use cases for managing workflow templates including CRUD operations,
search, filtering, instantiation, and import/export functionality.


### CloneTemplateUseCase


Use case for cloning templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(template_id, new_name)` | `Optional[WorkflowTemplate]` | Clone an existing template. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(template_id: str, new_name: Optional[str] = None) -> Optional[WorkflowTemplate]
```

Clone an existing template.

Args:
    template_id: Template to clone
    new_name: Optional name for the clone

Returns:
    Cloned template or None if source not found

**Parameters:**

- `template_id: str` *(required)*
- `new_name: Optional[str] = None`

### CreateTemplateUseCase


Use case for creating a new workflow template.

Creates templates from scratch or from existing workflows.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(name, description, category, ...)` | `WorkflowTemplate` | Create a new workflow template. |
| `async from_workflow(workflow_data, name, description, ...)` | `WorkflowTemplate` | Create a template from an existing workflow. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository for persistence

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(name: str, description: str, category: TemplateCategory, workflow_definition: Dict[str, Any], parameters: Optional[List[Dict[str, Any]]] = None, author: str = '', tags: Optional[List[str]] = None, difficulty: str = 'intermediate', requirements: Optional[List[str]] = None) -> WorkflowTemplate
```

Create a new workflow template.

Args:
    name: Template name
    description: Template description
    category: Template category
    workflow_definition: The workflow JSON to use as template base
    parameters: List of parameter definitions
    author: Template author
    tags: Optional tags for categorization
    difficulty: Difficulty level (beginner, intermediate, advanced)
    requirements: List of requirements/dependencies

Returns:
    Created WorkflowTemplate

Raises:
    ValueError: If template creation fails validation

**Parameters:**

- `name: str` *(required)*
- `description: str` *(required)*
- `category: TemplateCategory` *(required)*
- `workflow_definition: Dict[str, Any]` *(required)*
- `parameters: Optional[List[Dict[str, Any]]] = None`
- `author: str = ''`
- `tags: Optional[List[str]] = None`
- `difficulty: str = 'intermediate'`
- `requirements: Optional[List[str]] = None`

##### `from_workflow`

```python
async def from_workflow(workflow_data: Dict[str, Any], name: str, description: str, category: TemplateCategory, extract_variables: bool = True) -> WorkflowTemplate
```

Create a template from an existing workflow.

Args:
    workflow_data: Existing workflow JSON
    name: Template name
    description: Template description
    category: Template category
    extract_variables: Whether to extract workflow variables as parameters

Returns:
    Created WorkflowTemplate

**Parameters:**

- `workflow_data: Dict[str, Any]` *(required)*
- `name: str` *(required)*
- `description: str` *(required)*
- `category: TemplateCategory` *(required)*
- `extract_variables: bool = True`

### DeleteTemplateUseCase


Use case for deleting templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(template_id)` | `bool` | Delete a template. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(template_id: str) -> bool
```

Delete a template.

Args:
    template_id: Template to delete

Returns:
    True if deleted, False if not found

Raises:
    ValueError: If attempting to delete built-in template

**Parameters:**

- `template_id: str` *(required)*

### ExportTemplateUseCase


Use case for exporting templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async to_file(template_id, file_path)` | `bool` | Export template to file. |
| `async to_json(template_id)` | `Optional[bytes]` | Export template to JSON bytes. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `to_file`

```python
async def to_file(template_id: str, file_path: Path) -> bool
```

Export template to file.

Args:
    template_id: Template to export
    file_path: Destination file path

Returns:
    True if exported successfully

**Parameters:**

- `template_id: str` *(required)*
- `file_path: Path` *(required)*

##### `to_json`

```python
async def to_json(template_id: str) -> Optional[bytes]
```

Export template to JSON bytes.

Args:
    template_id: Template to export

Returns:
    JSON bytes or None if not found

**Parameters:**

- `template_id: str` *(required)*

### GetTemplateCategoriesUseCase


Use case for retrieving template categories with counts.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute()` | `Dict[str, int]` | Get all categories with template counts. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute() -> Dict[str, int]
```

Get all categories with template counts.

Returns:
    Dictionary mapping category names to template counts

### GetTemplateUseCase


Use case for retrieving templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async all()` | `List[WorkflowTemplate]` | Get all templates. |
| `async builtin()` | `List[WorkflowTemplate]` | Get all built-in templates. |
| `async by_category(category)` | `List[WorkflowTemplate]` | Get templates by category. |
| `async by_id(template_id)` | `Optional[WorkflowTemplate]` | Get template by ID. |
| `async user_created()` | `List[WorkflowTemplate]` | Get all user-created templates. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `all`

```python
async def all() -> List[WorkflowTemplate]
```

Get all templates.

Returns:
    List of all templates

##### `builtin`

```python
async def builtin() -> List[WorkflowTemplate]
```

Get all built-in templates.

Returns:
    List of built-in templates

##### `by_category`

```python
async def by_category(category: TemplateCategory) -> List[WorkflowTemplate]
```

Get templates by category.

Args:
    category: Template category

Returns:
    List of templates in category

**Parameters:**

- `category: TemplateCategory` *(required)*

##### `by_id`

```python
async def by_id(template_id: str) -> Optional[WorkflowTemplate]
```

Get template by ID.

Args:
    template_id: Template identifier

Returns:
    WorkflowTemplate or None if not found

**Parameters:**

- `template_id: str` *(required)*

##### `user_created`

```python
async def user_created() -> List[WorkflowTemplate]
```

Get all user-created templates.

Returns:
    List of user templates

### ImportTemplateUseCase


Use case for importing templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async from_file(file_path, overwrite)` | `WorkflowTemplate` | Import template from file. |
| `async from_json(json_data, overwrite)` | `WorkflowTemplate` | Import template from JSON bytes. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `from_file`

```python
async def from_file(file_path: Path, overwrite: bool = False) -> WorkflowTemplate
```

Import template from file.

Args:
    file_path: Path to template JSON file
    overwrite: Whether to overwrite existing template

Returns:
    Imported WorkflowTemplate

Raises:
    ValueError: If import fails
    FileNotFoundError: If file doesn't exist

**Parameters:**

- `file_path: Path` *(required)*
- `overwrite: bool = False`

##### `from_json`

```python
async def from_json(json_data: bytes, overwrite: bool = False) -> WorkflowTemplate
```

Import template from JSON bytes.

Args:
    json_data: JSON template data
    overwrite: Whether to overwrite existing template with same ID

Returns:
    Imported WorkflowTemplate

Raises:
    ValueError: If import fails or template exists and overwrite=False

**Parameters:**

- `json_data: bytes` *(required)*
- `overwrite: bool = False`

### InstantiateTemplateUseCase


Use case for instantiating templates into workflows.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(template_id, parameter_values, workflow_name)` | `TemplateInstantiationResult` | Instantiate a template with parameter values. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(template_id: str, parameter_values: Dict[str, Any], workflow_name: Optional[str] = None) -> TemplateInstantiationResult
```

Instantiate a template with parameter values.

Args:
    template_id: Template to instantiate
    parameter_values: Values for template parameters
    workflow_name: Optional name for the resulting workflow

Returns:
    TemplateInstantiationResult with workflow and any warnings/errors

**Parameters:**

- `template_id: str` *(required)*
- `parameter_values: Dict[str, Any]` *(required)*
- `workflow_name: Optional[str] = None`

### RateTemplateUseCase


Use case for rating templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(template_id, rating)` | `bool` | Rate a template. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(template_id: str, rating: float) -> bool
```

Rate a template.

Args:
    template_id: Template to rate
    rating: Rating value (1-5)

Returns:
    True if rating was recorded

Raises:
    ValueError: If rating is out of range

**Parameters:**

- `template_id: str` *(required)*
- `rating: float` *(required)*

### SearchTemplatesUseCase


Use case for searching and filtering templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(criteria)` | `TemplateSearchResult` | Search templates with criteria. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(criteria: TemplateSearchCriteria) -> TemplateSearchResult
```

Search templates with criteria.

Args:
    criteria: Search criteria

Returns:
    TemplateSearchResult with matching templates

**Parameters:**

- `criteria: TemplateSearchCriteria` *(required)*

### TemplateInstantiationResult

**Decorators:** `@dataclass`


Result of template instantiation.


**Attributes:**

- `errors: List[str]`
- `success: bool`
- `warnings: List[str]`
- `workflow: Optional[Dict[str, Any]]`

### TemplateRepository

**Inherits from:** `Protocol`


Repository interface for template persistence.

Implementations must provide all methods for template storage/retrieval.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `async delete(template_id)` | `bool` | Delete template by ID. |
| `async exists(template_id)` | `bool` | Check if template exists. |
| `async get_all()` | `List[WorkflowTemplate]` | Get all templates. |
| `async get_by_category(category)` | `List[WorkflowTemplate]` | Get templates by category. |
| `async get_by_id(template_id)` | `Optional[WorkflowTemplate]` | Get template by ID. |
| `async save(template)` | `None` | Save or update template. |
| `async search(query, category, tags)` | `List[WorkflowTemplate]` | Search templates. |

#### Method Details

##### `delete`

```python
async def delete(template_id: str) -> bool
```

Delete template by ID.

**Parameters:**

- `template_id: str` *(required)*

##### `exists`

```python
async def exists(template_id: str) -> bool
```

Check if template exists.

**Parameters:**

- `template_id: str` *(required)*

##### `get_all`

```python
async def get_all() -> List[WorkflowTemplate]
```

Get all templates.

##### `get_by_category`

```python
async def get_by_category(category: TemplateCategory) -> List[WorkflowTemplate]
```

Get templates by category.

**Parameters:**

- `category: TemplateCategory` *(required)*

##### `get_by_id`

```python
async def get_by_id(template_id: str) -> Optional[WorkflowTemplate]
```

Get template by ID.

**Parameters:**

- `template_id: str` *(required)*

##### `save`

```python
async def save(template: WorkflowTemplate) -> None
```

Save or update template.

**Parameters:**

- `template: WorkflowTemplate` *(required)*

##### `search`

```python
async def search(query: str, category: Optional[TemplateCategory] = None, tags: Optional[List[str]] = None) -> List[WorkflowTemplate]
```

Search templates.

**Parameters:**

- `query: str` *(required)*
- `category: Optional[TemplateCategory] = None`
- `tags: Optional[List[str]] = None`

### TemplateSearchCriteria

**Decorators:** `@dataclass`


Criteria for searching templates.


**Attributes:**

- `author: Optional[str]`
- `category: Optional[TemplateCategory]`
- `difficulty: Optional[str]`
- `is_builtin: Optional[bool]`
- `limit: int`
- `min_rating: Optional[float]`
- `offset: int`
- `query: str`
- `sort_by: str`
- `sort_desc: bool`
- `tags: List[str]`

### TemplateSearchResult

**Decorators:** `@dataclass`


Result of template search.


**Attributes:**

- `has_more: bool`
- `templates: List[WorkflowTemplate]`
- `total_count: int`

### UpdateTemplateUseCase


Use case for updating existing templates.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(repository)` | `None` | Initialize use case. |
| `async execute(template_id, updates)` | `Optional[WorkflowTemplate]` | Update an existing template. |

#### Method Details

##### `__init__`

```python
def __init__(repository: TemplateRepository) -> None
```

Initialize use case.

Args:
    repository: Template repository

**Parameters:**

- `repository: TemplateRepository` *(required)*

##### `execute`

```python
async def execute(template_id: str, updates: Dict[str, Any]) -> Optional[WorkflowTemplate]
```

Update an existing template.

Args:
    template_id: Template to update
    updates: Dictionary of fields to update

Returns:
    Updated template or None if not found

Raises:
    ValueError: If update contains invalid data

**Parameters:**

- `template_id: str` *(required)*
- `updates: Dict[str, Any]` *(required)*

---

## casare_rpa.application.use_cases.validate_workflow

**File:** `src\casare_rpa\application\use_cases\validate_workflow.py`


CasareRPA - Application Use Case: Validate Workflow

Provides workflow validation with hash-based caching for performance.
Validates workflow structure, connections, and node configurations.

Caching Strategy:
- SHA256 hash of workflow structure (nodes + connections)
- Cache invalidation on any workflow modification
- Thread-safe via threading.Lock

Performance Impact:
- Avoids re-validating unchanged workflows
- Typical hit rate: 80-95% during editing sessions
- Validation time reduced from ~50ms to <1ms on cache hit


### ValidateWorkflowUseCase


Application use case for validating workflows.

Uses hash-based caching to avoid re-validating unchanged workflows.
Thread-safe via threading.Lock for cache operations.

Validation Rules:
- Exactly one StartNode required
- At least one EndNode required
- All connections must reference valid nodes
- No orphan nodes (except Comment nodes)
- Node configurations must be valid


**Attributes:**

- `_cache: Dict[str, ValidationResult]`
- `_cache_hits: int`
- `_cache_misses: int`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the validation use case. |
| `clear_cache()` | `None` | Clear the entire validation cache. |
| `execute(workflow)` | `ValidationResult` | Validate a workflow. |
| `get_cache_stats()` | `Dict[str, Any]` | Get cache statistics. |
| `invalidate_cache(workflow)` | `None` | Invalidate the validation cache. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the validation use case.

##### `clear_cache`

```python
@classmethod
def clear_cache() -> None
```

Clear the entire validation cache.

##### `execute`

```python
def execute(workflow: Any) -> ValidationResult
```

Validate a workflow.

Args:
    workflow: Workflow to validate (WorkflowSchema or similar)

Returns:
    ValidationResult with is_valid flag and list of issues

**Parameters:**

- `workflow: Any` *(required)*

##### `get_cache_stats`

```python
@classmethod
def get_cache_stats() -> Dict[str, Any]
```

Get cache statistics.

Returns:
    Dictionary with hit/miss counts and hit rate

##### `invalidate_cache`

```python
def invalidate_cache(workflow: Optional[Any] = None) -> None
```

Invalidate the validation cache.

Args:
    workflow: If provided, only invalidate cache for this workflow.
             If None, clear entire cache.

**Parameters:**

- `workflow: Optional[Any] = None`

### ValidationIssue

**Decorators:** `@dataclass`


Represents a single validation issue.

Attributes:
    severity: "error", "warning", or "info"
    node_id: ID of the node with the issue (None for workflow-level issues)
    message: Human-readable description of the issue
    code: Machine-readable issue code (e.g., "NO_START_NODE")


**Attributes:**

- `code: str`
- `message: str`
- `node_id: Optional[str]`
- `severity: str`

### ValidationResult

**Decorators:** `@dataclass`


Result of workflow validation.

Attributes:
    is_valid: True if no errors (warnings allowed)
    issues: List of all validation issues found
    from_cache: True if this result was returned from cache


**Attributes:**

- `from_cache: bool`
- `is_valid: bool`
- `issues: List[ValidationIssue]`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `error_count()` | `int` | Count of error-level issues. |
| `errors()` | `List[ValidationIssue]` | Get only error-level issues. |
| `warning_count()` | `int` | Count of warning-level issues. |
| `warnings()` | `List[ValidationIssue]` | Get only warning-level issues. |

#### Method Details

##### `error_count`

```python
@property
def error_count() -> int
```

Count of error-level issues.

##### `errors`

```python
@property
def errors() -> List[ValidationIssue]
```

Get only error-level issues.

##### `warning_count`

```python
@property
def warning_count() -> int
```

Count of warning-level issues.

##### `warnings`

```python
@property
def warnings() -> List[ValidationIssue]
```

Get only warning-level issues.

---

## casare_rpa.application.use_cases.variable_resolver

**File:** `src\casare_rpa\application\use_cases\variable_resolver.py`


CasareRPA - Variable Resolver

Handles data transfer between nodes including:
- Port value resolution and transfer
- Output port validation after execution
- Error state capture for try-catch blocks

Extracted from ExecuteWorkflowUseCase for Single Responsibility.


### TryCatchErrorHandler


Handles try-catch block error capture and routing.

Extracted to separate error handling logic from execution flow.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(context)` | `None` | Initialize try-catch error handler. |
| `capture_error(error_msg, error_type, exception)` | `bool` | Check if we're inside a try block and capture the error if s... |
| `capture_from_result(result, node_id)` | `bool` | Capture error from a failed execution result. |
| `find_catch_node_id()` | `Optional[str]` | Find the catch node ID for the most recent active try block. |

#### Method Details

##### `__init__`

```python
def __init__(context: ExecutionContext) -> None
```

Initialize try-catch error handler.

Args:
    context: Execution context with variables

**Parameters:**

- `context: ExecutionContext` *(required)*

##### `capture_error`

```python
def capture_error(error_msg: str, error_type: str, exception: Exception) -> bool
```

Check if we're inside a try block and capture the error if so.

Args:
    error_msg: Error message
    error_type: Error type/class name
    exception: The original exception

Returns:
    True if error was captured by a try block, False otherwise

**Parameters:**

- `error_msg: str` *(required)*
- `error_type: str` *(required)*
- `exception: Exception` *(required)*

##### `capture_from_result`

```python
def capture_from_result(result: Optional[Dict[str, Any]], node_id: str) -> bool
```

Capture error from a failed execution result.

Args:
    result: Execution result (may be None or contain error)
    node_id: Node ID that failed

Returns:
    True if error was captured by a try block

**Parameters:**

- `result: Optional[Dict[str, Any]]` *(required)*
- `node_id: str` *(required)*

##### `find_catch_node_id`

```python
def find_catch_node_id() -> Optional[str]
```

Find the catch node ID for the most recent active try block.

Returns:
    Catch node ID if found, None otherwise

### VariableResolver


Resolves and transfers data between nodes.

Responsibilities:
- Transfer data from source output ports to target input ports
- Validate output ports have values after successful execution
- Capture errors in try-catch block state


**Attributes:**

- `CONTROL_FLOW_NODES: frozenset`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(workflow, node_getter)` | `None` | Initialize variable resolver. |
| `transfer_data(connection)` | `None` | Transfer data from source port to target port. |
| `transfer_inputs_to_node(node_id)` | `None` | Transfer all input data to a node from its connected sources... |
| `validate_output_ports(node, result)` | `bool` | Validate that required output ports have values after execut... |

#### Method Details

##### `__init__`

```python
def __init__(workflow: WorkflowSchema, node_getter: callable) -> None
```

Initialize variable resolver.

Args:
    workflow: Workflow schema with connections
    node_getter: Callable to get node instance by ID

**Parameters:**

- `workflow: WorkflowSchema` *(required)*
- `node_getter: callable` *(required)*

##### `transfer_data`

```python
def transfer_data(connection: Any) -> None
```

Transfer data from source port to target port.

Args:
    connection: The connection defining source and target

**Parameters:**

- `connection: Any` *(required)*

##### `transfer_inputs_to_node`

```python
def transfer_inputs_to_node(node_id: str) -> None
```

Transfer all input data to a node from its connected sources.

Args:
    node_id: Target node ID to transfer data to

**Parameters:**

- `node_id: str` *(required)*

##### `validate_output_ports`

```python
def validate_output_ports(node: Any, result: Dict[str, Any]) -> bool
```

Validate that required output ports have values after execution.

Logs warnings for output ports that have no value after successful execution.
This helps detect silent failures where nodes succeed but don't produce expected data.

Args:
    node: The executed node instance
    result: The execution result dictionary

Returns:
    True (validation is informational, doesn't block execution)

**Parameters:**

- `node: Any` *(required)*
- `result: Dict[str, Any]` *(required)*

---

## casare_rpa.application.use_cases.workflow_migration

**File:** `src\casare_rpa\application\use_cases\workflow_migration.py`


CasareRPA - Application Use Case: Workflow Migration
Handles version migration, compatibility checking, and rollback operations.

Coordinates:
- Domain: VersionHistory, WorkflowVersion, VersionDiff
- Domain: Breaking change detection and compatibility validation
- Infrastructure: Database persistence for versions
- Application: Event emission for migration progress


### Functions

#### `get_rule_registry`

```python
def get_rule_registry() -> MigrationRuleRegistry
```

Get the migration rule registry.

#### `register_migration_rule`

```python
def register_migration_rule(node_type: str, from_version_range: Tuple[str, str], to_version_range: Tuple[str, str], description: str = '') -> Callable
```

Decorator to register a node migration rule.

Example:
    @register_migration_rule("NavigateNode", ("1.0.0", "1.9.9"), ("2.0.0", "2.9.9"))
    def migrate_navigate_v1_to_v2(node_data: NodeData) -> NodeData:
        # Transform node data
        return transformed_data

#### `reset_rule_registry`

```python
def reset_rule_registry() -> None
```

Reset the migration rule registry (for testing).

Clears the singleton so it will be recreated on next access.


### AutoMigrationPolicy


Policy for automatic workflow version migrations.

Defines rules for when and how to automatically migrate
workflows to newer versions.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(auto_patch_updates, auto_minor_updates, auto_major_updates, ...)` | `None` | Initialize migration policy. |
| `from_dict(data)` | `'AutoMigrationPolicy'` | Create instance from dictionary. |
| `manual()` | `'AutoMigrationPolicy'` | Create a manual-only policy (no auto-migration). |
| `permissive()` | `'AutoMigrationPolicy'` | Create a permissive policy (auto-migrate most changes). |
| `should_auto_migrate(from_version, to_version, compatibility)` | `Tuple[bool, str]` | Check if auto-migration should proceed. |
| `strict()` | `'AutoMigrationPolicy'` | Create a strict policy (minimal auto-migration). |
| `to_dict()` | `Dict[str, Any]` | Serialize policy to dictionary. |

#### Method Details

##### `__init__`

```python
def __init__(auto_patch_updates: bool = True, auto_minor_updates: bool = False, auto_major_updates: bool = False, require_passing_validation: bool = True, max_breaking_changes: int = 0) -> None
```

Initialize migration policy.

Args:
    auto_patch_updates: Auto-migrate for patch version bumps
    auto_minor_updates: Auto-migrate for minor version bumps
    auto_major_updates: Auto-migrate for major version bumps
    require_passing_validation: Require validation pass before migration
    max_breaking_changes: Max allowed breaking changes for auto-migration

**Parameters:**

- `auto_patch_updates: bool = True`
- `auto_minor_updates: bool = False`
- `auto_major_updates: bool = False`
- `require_passing_validation: bool = True`
- `max_breaking_changes: int = 0`

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any]) -> 'AutoMigrationPolicy'
```

Create instance from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*

##### `manual`

```python
@classmethod
def manual() -> 'AutoMigrationPolicy'
```

Create a manual-only policy (no auto-migration).

##### `permissive`

```python
@classmethod
def permissive() -> 'AutoMigrationPolicy'
```

Create a permissive policy (auto-migrate most changes).

##### `should_auto_migrate`

```python
def should_auto_migrate(from_version: SemanticVersion, to_version: SemanticVersion, compatibility: CompatibilityResult) -> Tuple[bool, str]
```

Check if auto-migration should proceed.

Args:
    from_version: Current version
    to_version: Target version
    compatibility: Compatibility check result

Returns:
    Tuple of (should_migrate, reason)

**Parameters:**

- `from_version: SemanticVersion` *(required)*
- `to_version: SemanticVersion` *(required)*
- `compatibility: CompatibilityResult` *(required)*

##### `strict`

```python
@classmethod
def strict() -> 'AutoMigrationPolicy'
```

Create a strict policy (minimal auto-migration).

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize policy to dictionary.

### MigrationContext

**Decorators:** `@dataclass`


Context passed to migration steps.


**Attributes:**

- `compatibility: CompatibilityResult`
- `diff: VersionDiff`
- `errors: List[str]`
- `from_version: WorkflowVersion`
- `to_version: WorkflowVersion`
- `variables: Dict[str, JsonValue]`
- `warnings: List[str]`
- `workflow_data: WorkflowData`
- `workflow_id: str`

### MigrationResult

**Decorators:** `@dataclass`


Result of a migration operation.


**Attributes:**

- `breaking_changes_resolved: int`
- `completed_at: Optional[datetime]`
- `duration_ms: float`
- `errors: List[str]`
- `from_version: str`
- `migrated_data: Optional[WorkflowData]`
- `started_at: datetime`
- `status: MigrationStatus`
- `steps_completed: int`
- `success: bool`
- `to_version: str`
- `total_steps: int`
- `warnings: List[str]`
- `workflow_id: str`

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

### MigrationRuleRegistry


Registry of node migration rules.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize empty registry. |
| `find_rules(node_type, from_version, to_version)` | `List[NodeMigrationRule]` | Find all applicable rules for a migration. |
| `register(rule)` | `None` | Register a migration rule. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize empty registry.

##### `find_rules`

```python
def find_rules(node_type: str, from_version: SemanticVersion, to_version: SemanticVersion) -> List[NodeMigrationRule]
```

Find all applicable rules for a migration.

**Parameters:**

- `node_type: str` *(required)*
- `from_version: SemanticVersion` *(required)*
- `to_version: SemanticVersion` *(required)*

##### `register`

```python
def register(rule: NodeMigrationRule) -> None
```

Register a migration rule.

**Parameters:**

- `rule: NodeMigrationRule` *(required)*

### MigrationStatus

**Inherits from:** `Enum`


Status of a migration operation.


**Attributes:**

- `COMPLETED: auto`
- `FAILED: auto`
- `IN_PROGRESS: auto`
- `PENDING: auto`
- `ROLLED_BACK: auto`

### MigrationStep

**Decorators:** `@dataclass`


Represents a single step in the migration process.


**Attributes:**

- `action: Callable[['MigrationContext'], bool]`
- `completed: bool`
- `description: str`
- `error: Optional[str]`
- `name: str`
- `rollback_action: Optional[Callable[['MigrationContext'], bool]]`

### NodeMigrationRule


Rule for migrating a specific node type between versions.

Used to define how nodes should be transformed when their
schema changes between versions.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(node_type, from_version_range, to_version_range, ...)` | `None` | Initialize migration rule. |
| `applies_to(node_type, from_version, to_version)` | `bool` | Check if this rule applies to the given migration. |

#### Method Details

##### `__init__`

```python
def __init__(node_type: str, from_version_range: Tuple[str, str], to_version_range: Tuple[str, str], transformer: Callable[[NodeData], NodeData], description: str = '') -> None
```

Initialize migration rule.

Args:
    node_type: Type of node this rule applies to
    from_version_range: (min_version, max_version) for source
    to_version_range: (min_version, max_version) for target
    transformer: Function to transform node data
    description: Human-readable description

**Parameters:**

- `node_type: str` *(required)*
- `from_version_range: Tuple[str, str]` *(required)*
- `to_version_range: Tuple[str, str]` *(required)*
- `transformer: Callable[[NodeData], NodeData]` *(required)*
- `description: str = ''`

##### `applies_to`

```python
def applies_to(node_type: str, from_version: SemanticVersion, to_version: SemanticVersion) -> bool
```

Check if this rule applies to the given migration.

**Parameters:**

- `node_type: str` *(required)*
- `from_version: SemanticVersion` *(required)*
- `to_version: SemanticVersion` *(required)*

### VersionPinManager


Manages version pinning for scheduled jobs.

Allows jobs to be pinned to specific workflow versions,
preventing automatic updates that could break scheduled executions.


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(version_history)` | `None` | Initialize pin manager. |
| `from_dict(data, version_history)` | `'VersionPinManager'` | Create instance from dictionary. |
| `get_execution_version(job_id)` | `Optional[WorkflowVersion]` | Get the workflow version that should be used for job executi... |
| `get_jobs_pinned_to_version(version_str)` | `List[str]` | Get all job IDs pinned to a specific version. |
| `get_pinned_version(job_id)` | `Optional[str]` | Get pinned version for a job, or None if not pinned. |
| `pin_job(job_id, version_str, reason)` | `bool` | Pin a job to a specific version. |
| `to_dict()` | `Dict[str, Any]` | Serialize pins to dictionary. |
| `unpin_job(job_id)` | `bool` | Remove version pin from a job. |
| `validate_pins()` | `List[Tuple[str, str]]` | Validate all pins and return invalid ones. |

#### Method Details

##### `__init__`

```python
def __init__(version_history: VersionHistory) -> None
```

Initialize pin manager.

Args:
    version_history: VersionHistory for the workflow

**Parameters:**

- `version_history: VersionHistory` *(required)*

##### `from_dict`

```python
@classmethod
def from_dict(data: Dict[str, Any], version_history: VersionHistory) -> 'VersionPinManager'
```

Create instance from dictionary.

**Parameters:**

- `data: Dict[str, Any]` *(required)*
- `version_history: VersionHistory` *(required)*

##### `get_execution_version`

```python
def get_execution_version(job_id: str) -> Optional[WorkflowVersion]
```

Get the workflow version that should be used for job execution.

Returns pinned version if set, otherwise active version.

Args:
    job_id: Job identifier

Returns:
    WorkflowVersion to use for execution

**Parameters:**

- `job_id: str` *(required)*

##### `get_jobs_pinned_to_version`

```python
def get_jobs_pinned_to_version(version_str: str) -> List[str]
```

Get all job IDs pinned to a specific version.

**Parameters:**

- `version_str: str` *(required)*

##### `get_pinned_version`

```python
def get_pinned_version(job_id: str) -> Optional[str]
```

Get pinned version for a job, or None if not pinned.

**Parameters:**

- `job_id: str` *(required)*

##### `pin_job`

```python
def pin_job(job_id: str, version_str: str, reason: str = '') -> bool
```

Pin a job to a specific version.

Args:
    job_id: Job identifier
    version_str: Version to pin to
    reason: Reason for pinning

Returns:
    True if pinning succeeded

**Parameters:**

- `job_id: str` *(required)*
- `version_str: str` *(required)*
- `reason: str = ''`

##### `to_dict`

```python
def to_dict() -> Dict[str, Any]
```

Serialize pins to dictionary.

##### `unpin_job`

```python
def unpin_job(job_id: str) -> bool
```

Remove version pin from a job.

Args:
    job_id: Job identifier

Returns:
    True if job was unpinned

**Parameters:**

- `job_id: str` *(required)*

##### `validate_pins`

```python
def validate_pins() -> List[Tuple[str, str]]
```

Validate all pins and return invalid ones.

Returns:
    List of (job_id, reason) for invalid pins

### WorkflowMigrationUseCase


Application use case for migrating workflows between versions.

Provides:
- Automatic migration with registered rules
- Breaking change resolution
- Rollback support
- Progress tracking via events


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(version_history, event_bus, rule_registry)` | `None` | Initialize migration use case. |
| `check_migration_feasibility(from_version, to_version)` | `Tuple[bool, CompatibilityResult, str]` | Check if migration between versions is feasible. |
| `async migrate(from_version, to_version, dry_run)` | `MigrationResult` | Execute migration from one version to another. |
| `async validate_running_jobs(target_version, running_job_ids)` | `Tuple[bool, List[str]]` | Validate that migration is safe for running jobs. |

#### Method Details

##### `__init__`

```python
def __init__(version_history: VersionHistory, event_bus: Optional[EventBus] = None, rule_registry: Optional[MigrationRuleRegistry] = None) -> None
```

Initialize migration use case.

Args:
    version_history: VersionHistory for the workflow
    event_bus: Optional event bus for progress updates
    rule_registry: Optional custom rule registry

**Parameters:**

- `version_history: VersionHistory` *(required)*
- `event_bus: Optional[EventBus] = None`
- `rule_registry: Optional[MigrationRuleRegistry] = None`

##### `check_migration_feasibility`

```python
def check_migration_feasibility(from_version: str, to_version: str) -> Tuple[bool, CompatibilityResult, str]
```

Check if migration between versions is feasible.

Args:
    from_version: Source version string
    to_version: Target version string

Returns:
    Tuple of (feasible, compatibility_result, reason)

**Parameters:**

- `from_version: str` *(required)*
- `to_version: str` *(required)*

##### `migrate`

```python
async def migrate(from_version: str, to_version: str, dry_run: bool = False) -> MigrationResult
```

Execute migration from one version to another.

Args:
    from_version: Source version string
    to_version: Target version string
    dry_run: If True, simulate migration without persisting

Returns:
    MigrationResult with outcome details

**Parameters:**

- `from_version: str` *(required)*
- `to_version: str` *(required)*
- `dry_run: bool = False`

##### `validate_running_jobs`

```python
async def validate_running_jobs(target_version: str, running_job_ids: List[str]) -> Tuple[bool, List[str]]
```

Validate that migration is safe for running jobs.

Args:
    target_version: Version to migrate to
    running_job_ids: List of currently running job IDs

Returns:
    Tuple of (safe_to_migrate, conflicting_job_ids)

**Parameters:**

- `target_version: str` *(required)*
- `running_job_ids: List[str]` *(required)*

---

## casare_rpa.application.workflow.recent_files

**File:** `src\casare_rpa\application\workflow\recent_files.py`


Recent Files Manager for CasareRPA.

Manages a list of recently opened workflow files for quick access.


### Functions

#### `get_recent_files_manager`

```python
def get_recent_files_manager() -> RecentFilesManager
```

Get the recent files manager instance.

#### `reset_recent_files_manager`

```python
def reset_recent_files_manager() -> None
```

Reset the recent files manager singleton (for testing).

Clears the singleton so it will be recreated on next access.


### RecentFilesManager


Manages recent files list with persistence.

Features:
- Stores up to N recent files
- Persists across sessions
- Removes non-existent files
- Tracks last opened time


**Attributes:**

- `MAX_RECENT_FILES: int`
- `RECENT_FILES_PATH: Any`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | `None` | Initialize the recent files manager. |
| `add_file(file_path)` | `None` | Add a file to the recent files list. |
| `clear()` | `None` | Clear the recent files list. |
| `get_recent_files()` | `List[dict]` | Get the list of recent files. |
| `remove_file(file_path)` | `None` | Remove a specific file from the recent list. |

#### Method Details

##### `__init__`

```python
def __init__() -> None
```

Initialize the recent files manager.

##### `add_file`

```python
def add_file(file_path: Path) -> None
```

Add a file to the recent files list.

Args:
    file_path: Path to the workflow file

**Parameters:**

- `file_path: Path` *(required)*

##### `clear`

```python
def clear() -> None
```

Clear the recent files list.

##### `get_recent_files`

```python
def get_recent_files() -> List[dict]
```

Get the list of recent files.

Returns:
    List of dicts with 'path', 'name', 'last_opened' keys

##### `remove_file`

```python
def remove_file(file_path: Path) -> None
```

Remove a specific file from the recent list.

Args:
    file_path: Path to remove

**Parameters:**

- `file_path: Path` *(required)*

---

## casare_rpa.application.workflow.workflow_import

**File:** `src\casare_rpa\application\workflow\workflow_import.py`


Workflow Import Module for CasareRPA.

Handles importing/merging nodes from external workflows into the current canvas.
Supports:
- File import via menu
- JSON text paste
- Drag-and-drop JSON files


### Functions

#### `import_workflow_data`

```python
def import_workflow_data(graph, node_factory, workflow_data: dict, drop_position: Optional[Tuple[float, float]] = None) -> Tuple[dict, Dict[str, str]]
```

Prepare workflow data for import.

Convenience function that handles ID remapping and position calculation.

Args:
    graph: NodeGraphQt NodeGraph instance
    node_factory: NodeFactory instance
    workflow_data: Raw workflow JSON data
    drop_position: Optional drop location

Returns:
    Tuple of (prepared workflow data, id_mapping)


### ImportResult

**Decorators:** `@dataclass`


Result of an import operation.


**Attributes:**

- `error_message: Optional[str]`
- `imported_frames: List[Any]`
- `imported_nodes: List[str]`
- `success: bool`
- `warnings: List[str]`

### WorkflowImporter


Imports nodes from workflow JSON data into an existing graph.

Handles:
- ID remapping to prevent conflicts
- Position offsetting to avoid overlapping existing nodes
- Connection remapping to use new IDs
- Frame import with node reference updates


**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(graph, node_factory)` | - | Initialize importer. |
| `apply_position_offset(workflow_data, offset)` | `dict` | Apply position offset to all nodes and frames in workflow da... |
| `calculate_import_position(workflow_data, drop_position)` | `Tuple[float, float]` | Calculate position offset for imported nodes. |
| `get_existing_node_ids()` | `Set[str]` | Get set of all existing node IDs in the graph. |
| `remap_node_ids(workflow_data)` | `Tuple[dict, Dict[str, str]]` | Remap node IDs to avoid conflicts with existing nodes. |

#### Method Details

##### `__init__`

```python
def __init__(graph, node_factory)
```

Initialize importer.

Args:
    graph: NodeGraphQt NodeGraph instance
    node_factory: NodeFactory for creating nodes

**Parameters:**

- `graph` *(required)*
- `node_factory` *(required)*

##### `apply_position_offset`

```python
def apply_position_offset(workflow_data: dict, offset: Tuple[float, float]) -> dict
```

Apply position offset to all nodes and frames in workflow data.

Args:
    workflow_data: Workflow data (will be modified in place)
    offset: (offset_x, offset_y) tuple

Returns:
    Modified workflow data

**Parameters:**

- `workflow_data: dict` *(required)*
- `offset: Tuple[float, float]` *(required)*

##### `calculate_import_position`

```python
def calculate_import_position(workflow_data: dict, drop_position: Optional[Tuple[float, float]] = None) -> Tuple[float, float]
```

Calculate position offset for imported nodes.

Args:
    workflow_data: Workflow data with node positions
    drop_position: Optional drop location (for drag-and-drop)

Returns:
    (offset_x, offset_y) to add to all imported node positions

**Parameters:**

- `workflow_data: dict` *(required)*
- `drop_position: Optional[Tuple[float, float]] = None`

##### `get_existing_node_ids`

```python
def get_existing_node_ids() -> Set[str]
```

Get set of all existing node IDs in the graph.

##### `remap_node_ids`

```python
def remap_node_ids(workflow_data: dict) -> Tuple[dict, Dict[str, str]]
```

Remap node IDs to avoid conflicts with existing nodes.

Args:
    workflow_data: Raw workflow JSON data

Returns:
    Tuple of (modified workflow data, id_mapping dict)

**Parameters:**

- `workflow_data: dict` *(required)*

---
