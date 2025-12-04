# Application Layer Functions

**Total:** 652 functions

## casare_rpa.application.dependency_injection.container

**File:** `src\casare_rpa\application\dependency_injection\container.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DIContainer | `self` | `None` | DUNDER |
| `_cleanup` | DIContainer | `self` | `None` | INTERNAL |
| `_register` | DIContainer | `self, name: str, implementation: Optional[Type[Any]], ...` | `None` | INTERNAL |
| `clear` | DIContainer | `self` | `None` | USED |
| `create_scope` | DIContainer | `self` | `-` | UNUSED |
| `get_instance` | DIContainer | `cls` | `'DIContainer'` | USED |
| `is_registered` | DIContainer | `self, name: str` | `bool` | UNUSED |
| `register_instance` | DIContainer | `self, name: str, instance: T` | `None` | UNUSED |
| `register_scoped` | DIContainer | `self, name: str, implementation: Optional[Type[T]], ...` | `None` | UNUSED |
| `register_singleton` | DIContainer | `self, name: str, implementation: Optional[Type[T]], ...` | `None` | USED |
| `register_transient` | DIContainer | `self, name: str, implementation: Optional[Type[T]], ...` | `None` | UNUSED |
| `reset_instance` | DIContainer | `cls` | `None` | UNUSED |
| `resolve` | DIContainer | `self, name: str` | `Any` | USED |
| `resolve_optional` | DIContainer | `self, name: str` | `Optional[Any]` | USED |
| `create_instance` | Registration | `self, container: 'DIContainer'` | `Any` | USED |
| `__init__` | Scope | `self, container: 'DIContainer'` | `None` | DUNDER |
| `dispose` | Scope | `self` | `None` | USED |
| `get_or_create` | Scope | `self, registration: Registration` | `Any` | USED |
| `__init__` | TypedContainer | `self, name: str` | `None` | DUNDER |
| `get` | TypedContainer | `self` | `T` | USED |
| `get_optional` | TypedContainer | `self` | `Optional[T]` | UNUSED |


## casare_rpa.application.dependency_injection.providers

**File:** `src\casare_rpa\application\dependency_injection\providers.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `register_all_providers` | - | `container: 'DIContainer'` | `None` | UNUSED |
| `register` | BaseProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `config_factory` | ConfigProvider | `` | `Any` | UNUSED |
| `register` | ConfigProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `event_bus_factory` | EventBusProvider | `` | `Any` | UNUSED |
| `register` | EventBusProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `api_key_store_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `credential_store_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `error_handler_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `healing_telemetry_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `memory_queue_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `migration_registry_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `recovery_registry_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `register` | InfrastructureProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `robot_metrics_factory` | InfrastructureProvider | `` | `Any` | UNUSED |
| `__init__` | OutputCaptureController | `self` | `None` | DUNDER |
| `dispose` | OutputCaptureController | `self` | `None` | USED |
| `remove_callbacks` | OutputCaptureController | `self` | `None` | USED |
| `set_callbacks` | OutputCaptureController | `self, stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `None` | USED |
| `register` | PresentationProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `recent_files_factory` | StorageProvider | `` | `Any` | UNUSED |
| `register` | StorageProvider | `cls, container: 'DIContainer'` | `None` | USED |
| `schedule_storage_factory` | StorageProvider | `` | `Any` | UNUSED |
| `settings_manager_factory` | StorageProvider | `` | `Any` | UNUSED |
| `template_loader_factory` | StorageProvider | `` | `Any` | UNUSED |
| `__init__` | UILogController | `self` | `None` | DUNDER |
| `dispose` | UILogController | `self` | `None` | USED |
| `remove_callback` | UILogController | `self` | `None` | USED |
| `set_callback` | UILogController | `self, callback: Callable[[str, str, str, str], None], min_level: str` | `None` | UNUSED |


## casare_rpa.application.dependency_injection.singleton

**File:** `src\casare_rpa\application\dependency_injection\singleton.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_singleton_accessor` | - | `factory: Callable[[], T], name: Optional[str]` | `tuple[Callable[[], T], Callable[[], None]]` | UNUSED |
| `__init__` | LazySingleton | `self, factory: Callable[[], T], name: Optional[str]` | `None` | DUNDER |
| `get` | LazySingleton | `self` | `T` | USED |
| `reset` | LazySingleton | `self` | `None` | USED |
| `__init__` | Singleton | `self, factory: Callable[[], T], name: Optional[str], ...` | `None` | DUNDER |
| `get` | Singleton | `self` | `T` | USED |
| `get_optional` | Singleton | `self` | `Optional[T]` | UNUSED |
| `is_initialized` | Singleton | `self` | `bool` | UNUSED |
| `reset` | Singleton | `self` | `None` | USED |
| `set` | Singleton | `self, instance: T` | `None` | USED |


## casare_rpa.application.execution.interfaces

**File:** `src\casare_rpa\application\execution\interfaces.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CallbackTriggerEventHandler | `self, on_workflow_run: Optional[Callable[[], None]], on_stats_update: Optional[Callable[[str, int, str], None]], ...` | `None` | DUNDER |
| `get_trigger_count` | CallbackTriggerEventHandler | `self, trigger_id: str` | `int` | USED |
| `request_workflow_run` | CallbackTriggerEventHandler | `self` | `None` | USED |
| `update_trigger_stats` | CallbackTriggerEventHandler | `self, trigger_id: str, count: int, ...` | `None` | USED |
| `get_trigger_count` | NullTriggerEventHandler | `self, trigger_id: str` | `int` | USED |
| `request_workflow_run` | NullTriggerEventHandler | `self` | `None` | USED |
| `update_trigger_stats` | NullTriggerEventHandler | `self, trigger_id: str, count: int, ...` | `None` | USED |
| `get_trigger_count` | TriggerEventHandler | `self, trigger_id: str` | `int` | USED |
| `request_workflow_run` | TriggerEventHandler | `self` | `None` | USED |
| `update_trigger_stats` | TriggerEventHandler | `self, trigger_id: str, count: int, ...` | `None` | USED |


## casare_rpa.application.execution.trigger_runner

**File:** `src\casare_rpa\application\execution\trigger_runner.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CanvasTriggerRunner | `self, event_handler: Optional[TriggerEventHandler]` | `None` | DUNDER |
| `async _on_trigger_event` | CanvasTriggerRunner | `self, event: TriggerEvent` | `None` | INTERNAL |
| `_update_trigger_stats` | CanvasTriggerRunner | `self, trigger_id: str` | `None` | INTERNAL |
| `active_trigger_count` | CanvasTriggerRunner | `self` | `int` | UNUSED |
| `clear_last_trigger_event` | CanvasTriggerRunner | `self` | `None` | UNUSED |
| `get_last_trigger_event` | CanvasTriggerRunner | `self` | `Optional[TriggerEvent]` | UNUSED |
| `is_running` | CanvasTriggerRunner | `self` | `bool` | USED |
| `set_event_handler` | CanvasTriggerRunner | `self, handler: TriggerEventHandler` | `None` | UNUSED |
| `async start_triggers` | CanvasTriggerRunner | `self, triggers: List[Dict[str, Any]]` | `int` | UNUSED |
| `async stop_triggers` | CanvasTriggerRunner | `self` | `None` | UNUSED |


## casare_rpa.application.orchestrator.orchestrator_engine

**File:** `src\casare_rpa\application\orchestrator\orchestrator_engine.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | OrchestratorEngine | `self, service: Optional[Any], load_balancing: str, ...` | `-` | DUNDER |
| `async _load_robots` | OrchestratorEngine | `self` | `-` | INTERNAL |
| `async _load_schedules` | OrchestratorEngine | `self` | `-` | INTERNAL |
| `async _notify_robot_cancel` | OrchestratorEngine | `self, job: Job` | `-` | INTERNAL |
| `async _on_job_dispatched` | OrchestratorEngine | `self, job: Job, robot: Robot` | `-` | INTERNAL |
| `_on_job_state_change` | OrchestratorEngine | `self, job: Job, old_status: JobStatus, ...` | `-` | INTERNAL |
| `_on_robot_status_change` | OrchestratorEngine | `self, robot: Robot, old_status: RobotStatus, ...` | `-` | INTERNAL |
| `async _on_schedule_trigger` | OrchestratorEngine | `self, schedule: Schedule` | `-` | INTERNAL |
| `async _on_server_job_complete` | OrchestratorEngine | `self, job_id: str, result: Dict` | `-` | INTERNAL |
| `async _on_server_job_failed` | OrchestratorEngine | `self, job_id: str, error_message: str` | `-` | INTERNAL |
| `async _on_server_job_progress` | OrchestratorEngine | `self, job_id: str, progress: int, ...` | `-` | INTERNAL |
| `async _on_server_robot_connect` | OrchestratorEngine | `self, robot: Robot` | `-` | INTERNAL |
| `async _on_server_robot_disconnect` | OrchestratorEngine | `self, robot_id: str` | `-` | INTERNAL |
| `async _on_trigger_fired` | OrchestratorEngine | `self, event: 'TriggerEvent'` | `-` | INTERNAL |
| `async _persist_job` | OrchestratorEngine | `self, job: Job` | `-` | INTERNAL |
| `async _persist_loop` | OrchestratorEngine | `self` | `-` | INTERNAL |
| `async _release_robot` | OrchestratorEngine | `self, job: Job` | `-` | INTERNAL |
| `async _schedule_future_job` | OrchestratorEngine | `self, job: Job, run_time: datetime` | `Optional[Job]` | INTERNAL |
| `async _timeout_check_loop` | OrchestratorEngine | `self` | `-` | INTERNAL |
| `available_robots` | OrchestratorEngine | `self` | `List[Robot]` | UNUSED |
| `async cancel_job` | OrchestratorEngine | `self, job_id: str, reason: str` | `bool` | UNUSED |
| `async complete_job` | OrchestratorEngine | `self, job_id: str, result: Optional[Dict]` | `bool` | USED |
| `connected_robots` | OrchestratorEngine | `self` | `List[str]` | UNUSED |
| `async create_schedule` | OrchestratorEngine | `self, name: str, workflow_id: str, ...` | `Optional[Schedule]` | UNUSED |
| `async delete_schedule` | OrchestratorEngine | `self, schedule_id: str` | `bool` | USED |
| `async disable_trigger` | OrchestratorEngine | `self, trigger_id: str` | `bool` | UNUSED |
| `async dispatch_job_to_robot` | OrchestratorEngine | `self, job: Job, robot_id: str` | `bool` | UNUSED |
| `async enable_trigger` | OrchestratorEngine | `self, trigger_id: str` | `bool` | UNUSED |
| `async fail_job` | OrchestratorEngine | `self, job_id: str, error_message: str` | `bool` | USED |
| `async fire_trigger_manually` | OrchestratorEngine | `self, trigger_id: str, payload: Optional[Dict]` | `bool` | UNUSED |
| `get_dispatcher_stats` | OrchestratorEngine | `self` | `Dict[str, Any]` | UNUSED |
| `get_queue_stats` | OrchestratorEngine | `self` | `Dict[str, Any]` | USED |
| `get_trigger_manager` | OrchestratorEngine | `self` | `Optional['TriggerManager']` | UNUSED |
| `get_trigger_stats` | OrchestratorEngine | `self` | `Dict[str, Any]` | UNUSED |
| `get_upcoming_schedules` | OrchestratorEngine | `self, limit: int` | `List[Dict[str, Any]]` | UNUSED |
| `async on_trigger_event` | OrchestratorEngine | `event: 'TriggerEvent'` | `-` | UNUSED |
| `async register_robot` | OrchestratorEngine | `self, robot_id: str, name: str, ...` | `Robot` | USED |
| `async register_trigger` | OrchestratorEngine | `self, trigger_config: Dict[str, Any], scenario_id: str, ...` | `bool` | USED |
| `async retry_job` | OrchestratorEngine | `self, job_id: str` | `Optional[Job]` | UNUSED |
| `async robot_heartbeat` | OrchestratorEngine | `self, robot_id: str` | `bool` | UNUSED |
| `server_port` | OrchestratorEngine | `self` | `int` | UNUSED |
| `async start` | OrchestratorEngine | `self` | `-` | USED |
| `async start_server` | OrchestratorEngine | `self, host: str, port: int` | `-` | UNUSED |
| `async stop` | OrchestratorEngine | `self` | `-` | USED |
| `async submit_job` | OrchestratorEngine | `self, workflow_id: str, workflow_name: str, ...` | `Optional[Job]` | USED |
| `async toggle_schedule` | OrchestratorEngine | `self, schedule_id: str, enabled: bool` | `bool` | USED |
| `async unregister_trigger` | OrchestratorEngine | `self, trigger_id: str` | `bool` | USED |
| `async update_job_progress` | OrchestratorEngine | `self, job_id: str, progress: int, ...` | `bool` | USED |
| `async update_robot_status` | OrchestratorEngine | `self, robot_id: str, status: RobotStatus` | `bool` | USED |


## casare_rpa.application.orchestrator.services.dispatcher_service

**File:** `src\casare_rpa\application\orchestrator\services\dispatcher_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobDispatcher | `self, strategy: LoadBalancingStrategy, dispatch_interval_seconds: int, ...` | `-` | DUNDER |
| `async _check_robot_health` | JobDispatcher | `self` | `-` | INTERNAL |
| `async _dispatch_loop` | JobDispatcher | `self, job_queue: JobQueue` | `-` | INTERNAL |
| `async _dispatch_pending_jobs` | JobDispatcher | `self, job_queue: JobQueue` | `-` | INTERNAL |
| `async _health_check_loop` | JobDispatcher | `self` | `-` | INTERNAL |
| `_select_affinity` | JobDispatcher | `self, job: Job, candidates: List[Robot]` | `Optional[Robot]` | INTERNAL |
| `_select_least_loaded` | JobDispatcher | `self, candidates: List[Robot]` | `Optional[Robot]` | INTERNAL |
| `_select_random` | JobDispatcher | `self, candidates: List[Robot]` | `Optional[Robot]` | INTERNAL |
| `_select_round_robin` | JobDispatcher | `self, candidates: List[Robot]` | `Optional[Robot]` | INTERNAL |
| `create_pool` | JobDispatcher | `self, name: str, tags: Optional[List[str]], ...` | `RobotPool` | USED |
| `delete_pool` | JobDispatcher | `self, name: str` | `bool` | UNUSED |
| `get_all_pools` | JobDispatcher | `self` | `Dict[str, RobotPool]` | USED |
| `get_all_robots` | JobDispatcher | `self` | `List[Robot]` | USED |
| `get_available_robots` | JobDispatcher | `self` | `List[Robot]` | USED |
| `get_pool` | JobDispatcher | `self, name: str` | `Optional[RobotPool]` | USED |
| `get_robot` | JobDispatcher | `self, robot_id: str` | `Optional[Robot]` | USED |
| `get_robots_by_status` | JobDispatcher | `self, status: RobotStatus` | `List[Robot]` | UNUSED |
| `get_stats` | JobDispatcher | `self` | `Dict[str, Any]` | USED |
| `record_job_result` | JobDispatcher | `self, job: Job, success: bool` | `-` | USED |
| `register_robot` | JobDispatcher | `self, robot: Robot, pool_name: str` | `bool` | USED |
| `select_robot` | JobDispatcher | `self, job: Job, pool_name: Optional[str]` | `Optional[Robot]` | USED |
| `set_callbacks` | JobDispatcher | `self, on_robot_status_change: Optional[Callable[[Robot, RobotStatus, RobotStatus], None]], on_job_dispatched: Optional[Callable[[Job, Robot], None]]` | `-` | USED |
| `async start` | JobDispatcher | `self, job_queue: JobQueue` | `-` | USED |
| `async stop` | JobDispatcher | `self` | `-` | USED |
| `unregister_robot` | JobDispatcher | `self, robot_id: str` | `-` | USED |
| `update_robot` | JobDispatcher | `self, robot: Robot` | `-` | USED |
| `update_robot_heartbeat` | JobDispatcher | `self, robot_id: str` | `-` | USED |
| `__init__` | RobotPool | `self, name: str, tags: Optional[List[str]], ...` | `-` | DUNDER |
| `add_robot` | RobotPool | `self, robot: Robot` | `bool` | USED |
| `can_accept_job` | RobotPool | `self` | `bool` | USED |
| `get_available_robots` | RobotPool | `self` | `List[Robot]` | USED |
| `get_current_job_count` | RobotPool | `self` | `int` | USED |
| `get_robots` | RobotPool | `self` | `List[Robot]` | USED |
| `is_workflow_allowed` | RobotPool | `self, workflow_id: str` | `bool` | UNUSED |
| `online_count` | RobotPool | `self` | `int` | UNUSED |
| `remove_robot` | RobotPool | `self, robot_id: str` | `-` | USED |
| `utilization` | RobotPool | `self` | `float` | UNUSED |


## casare_rpa.application.orchestrator.services.distribution_service

**File:** `src\casare_rpa\application\orchestrator\services\distribution_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobRouter | `self` | `-` | DUNDER |
| `add_route` | JobRouter | `self, environment: str, robot_ids: List[str]` | `-` | UNUSED |
| `add_tag_route` | JobRouter | `self, tag: str, robot_ids: List[str]` | `-` | UNUSED |
| `clear_routes` | JobRouter | `self` | `-` | UNUSED |
| `get_eligible_robots` | JobRouter | `self, job: Job, all_robots: List[Robot]` | `List[Robot]` | UNUSED |
| `set_fallback_robots` | JobRouter | `self, robot_ids: List[str]` | `-` | UNUSED |
| `__init__` | RobotSelector | `self` | `-` | DUNDER |
| `_select_by_affinity` | RobotSelector | `self, job: Job, robots: List[Robot]` | `Robot` | INTERNAL |
| `_select_by_capability` | RobotSelector | `self, job: Job, robots: List[Robot]` | `Robot` | INTERNAL |
| `_select_least_loaded` | RobotSelector | `self, robots: List[Robot]` | `Robot` | INTERNAL |
| `_select_random` | RobotSelector | `self, robots: List[Robot]` | `Robot` | INTERNAL |
| `_select_round_robin` | RobotSelector | `self, robots: List[Robot]` | `Robot` | INTERNAL |
| `clear_affinity` | RobotSelector | `self, workflow_id: str` | `-` | UNUSED |
| `clear_all_affinity` | RobotSelector | `self` | `-` | UNUSED |
| `score` | RobotSelector | `robot: Robot` | `tuple` | UNUSED |
| `select` | RobotSelector | `self, job: Job, available_robots: List[Robot], ...` | `Optional[Robot]` | USED |
| `__init__` | WorkflowDistributor | `self, max_retries: int, retry_delay: float, ...` | `-` | DUNDER |
| `_find_matching_rule` | WorkflowDistributor | `self, job: Job` | `Optional[DistributionRule]` | INTERNAL |
| `_record_result` | WorkflowDistributor | `self, result: DistributionResult` | `-` | INTERNAL |
| `add_rule` | WorkflowDistributor | `self, rule: DistributionRule` | `-` | UNUSED |
| `clear_rules` | WorkflowDistributor | `self` | `-` | UNUSED |
| `async distribute` | WorkflowDistributor | `self, job: Job, available_robots: List[Robot], ...` | `DistributionResult` | USED |
| `async distribute_batch` | WorkflowDistributor | `self, jobs: List[Job], available_robots: List[Robot]` | `List[DistributionResult]` | UNUSED |
| `get_recent_results` | WorkflowDistributor | `self, limit: int` | `List[DistributionResult]` | UNUSED |
| `get_statistics` | WorkflowDistributor | `self` | `Dict[str, Any]` | USED |
| `remove_rule` | WorkflowDistributor | `self, name: str` | `bool` | UNUSED |
| `set_callbacks` | WorkflowDistributor | `self, on_success: Optional[Callable], on_failure: Optional[Callable]` | `-` | USED |
| `set_send_job_function` | WorkflowDistributor | `self, fn: Callable` | `-` | UNUSED |


## casare_rpa.application.orchestrator.services.job_lifecycle_service

**File:** `src\casare_rpa\application\orchestrator\services\job_lifecycle_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobLifecycleService | `self, job_repository: JobRepository, robot_management_service: Optional['RobotManagementService']` | `-` | DUNDER |
| `async cancel_job` | JobLifecycleService | `self, job_id: str, reason: str` | `bool` | UNUSED |
| `async connect` | JobLifecycleService | `self` | `bool` | USED |
| `async create_job` | JobLifecycleService | `self, workflow_id: str, workflow_name: str, ...` | `Optional[Job]` | USED |
| `async dispatch_workflow_file` | JobLifecycleService | `self, file_path: Path, robot_id: str, ...` | `Optional[Job]` | UNUSED |
| `async get_job` | JobLifecycleService | `self, job_id: str` | `Optional[Job]` | USED |
| `async get_jobs` | JobLifecycleService | `self, limit: int, status: Optional[JobStatus], ...` | `List[Job]` | USED |
| `async get_queued_jobs` | JobLifecycleService | `self` | `List[Job]` | UNUSED |
| `async get_running_jobs` | JobLifecycleService | `self` | `List[Job]` | USED |
| `is_cloud_mode` | JobLifecycleService | `self` | `bool` | UNUSED |
| `async retry_job` | JobLifecycleService | `self, job_id: str` | `Optional[Job]` | UNUSED |
| `set_robot_management_service` | JobLifecycleService | `self, robot_service: 'RobotManagementService'` | `None` | UNUSED |
| `async update_job_status` | JobLifecycleService | `self, job_id: str, status: JobStatus, ...` | `bool` | USED |


## casare_rpa.application.orchestrator.services.job_queue_manager

**File:** `src\casare_rpa\application\orchestrator\services\job_queue_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobDeduplicator | `self, window_seconds: int` | `-` | DUNDER |
| `_cleanup` | JobDeduplicator | `self` | `-` | INTERNAL |
| `_compute_hash` | JobDeduplicator | `self, workflow_id: str, robot_id: Optional[str], ...` | `str` | INTERNAL |
| `is_duplicate` | JobDeduplicator | `self, workflow_id: str, robot_id: Optional[str], ...` | `bool` | USED |
| `record` | JobDeduplicator | `self, workflow_id: str, robot_id: Optional[str], ...` | `str` | USED |
| `__init__` | JobQueue | `self, dedup_window_seconds: int, default_timeout_seconds: int, ...` | `-` | DUNDER |
| `_finish_job` | JobQueue | `self, job_id: str, new_status: JobStatus, ...` | `Tuple[bool, str]` | INTERNAL |
| `cancel` | JobQueue | `self, job_id: str, reason: str` | `Tuple[bool, str]` | USED |
| `check_timeouts` | JobQueue | `self` | `List[str]` | USED |
| `complete` | JobQueue | `self, job_id: str, result: Optional[Dict]` | `Tuple[bool, str]` | USED |
| `dequeue` | JobQueue | `self, robot: Robot` | `Optional[Job]` | USED |
| `enqueue` | JobQueue | `self, job: Job, check_duplicate: bool, ...` | `Tuple[bool, str]` | USED |
| `fail` | JobQueue | `self, job_id: str, error_message: str` | `Tuple[bool, str]` | USED |
| `get_job` | JobQueue | `self, job_id: str` | `Optional[Job]` | USED |
| `get_queue_depth` | JobQueue | `self` | `int` | USED |
| `get_queue_stats` | JobQueue | `self` | `Dict[str, Any]` | USED |
| `get_queued_jobs` | JobQueue | `self` | `List[Job]` | UNUSED |
| `get_robot_jobs` | JobQueue | `self, robot_id: str` | `List[Job]` | UNUSED |
| `get_running_jobs` | JobQueue | `self` | `List[Job]` | USED |
| `timeout` | JobQueue | `self, job_id: str` | `Tuple[bool, str]` | USED |
| `update_progress` | JobQueue | `self, job_id: str, progress: int, ...` | `bool` | USED |
| `can_transition` | JobStateMachine | `cls, from_state: JobStatus, to_state: JobStatus` | `bool` | USED |
| `is_active` | JobStateMachine | `cls, status: JobStatus` | `bool` | USED |
| `is_terminal` | JobStateMachine | `cls, status: JobStatus` | `bool` | USED |
| `transition` | JobStateMachine | `cls, job: Job, to_state: JobStatus` | `Job` | USED |
| `__init__` | JobTimeoutManager | `self, default_timeout_seconds: int` | `-` | DUNDER |
| `get_remaining_time` | JobTimeoutManager | `self, job_id: str` | `Optional[timedelta]` | UNUSED |
| `get_timed_out_jobs` | JobTimeoutManager | `self` | `List[str]` | USED |
| `start_tracking` | JobTimeoutManager | `self, job_id: str, timeout_seconds: Optional[int]` | `-` | USED |
| `stop_tracking` | JobTimeoutManager | `self, job_id: str` | `-` | USED |
| `from_job` | PriorityQueueItem | `cls, job: Job` | `'PriorityQueueItem'` | USED |


## casare_rpa.application.orchestrator.services.metrics_service

**File:** `src\casare_rpa\application\orchestrator\services\metrics_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_parse_date` | MetricsService | `self, date_str` | `Optional[datetime]` | INTERNAL |
| `async calculate_dashboard_metrics` | MetricsService | `self, robots: List[Robot], jobs: List[Job], ...` | `DashboardMetrics` | UNUSED |
| `async calculate_job_history` | MetricsService | `self, jobs: List[Job], days: int` | `List[JobHistoryEntry]` | UNUSED |


## casare_rpa.application.orchestrator.services.result_collector_service

**File:** `src\casare_rpa\application\orchestrator\services\result_collector_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | ExecutionStatistics | `self` | `Dict[str, Any]` | USED |
| `duration_seconds` | JobResult | `self` | `float` | UNUSED |
| `from_dict` | JobResult | `cls, data: Dict[str, Any]` | `'JobResult'` | USED |
| `is_success` | JobResult | `self` | `bool` | UNUSED |
| `to_dict` | JobResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | ResultCollector | `self, max_results: int, max_logs_per_job: int` | `-` | DUNDER |
| `async _store_result` | ResultCollector | `self, result: JobResult` | `-` | INTERNAL |
| `add_log` | ResultCollector | `self, job_id: str, level: str, ...` | `-` | USED |
| `add_log_batch` | ResultCollector | `self, job_id: str, entries: List[Dict[str, Any]]` | `-` | UNUSED |
| `clear` | ResultCollector | `self` | `-` | USED |
| `async collect_cancellation` | ResultCollector | `self, job: Job, reason: str` | `JobResult` | UNUSED |
| `async collect_failure` | ResultCollector | `self, job: Job, error_message: str, ...` | `JobResult` | UNUSED |
| `async collect_result` | ResultCollector | `self, job: Job, result_data: Optional[Dict[str, Any]], ...` | `JobResult` | UNUSED |
| `async collect_timeout` | ResultCollector | `self, job: Job` | `JobResult` | UNUSED |
| `get_failed_results` | ResultCollector | `self, limit: int` | `List[JobResult]` | UNUSED |
| `get_hourly_stats` | ResultCollector | `self, hours: int, workflow_id: Optional[str]` | `List[Dict[str, Any]]` | UNUSED |
| `get_recent_results` | ResultCollector | `self, limit: int` | `List[JobResult]` | UNUSED |
| `get_result` | ResultCollector | `self, job_id: str` | `Optional[JobResult]` | USED |
| `get_results_by_robot` | ResultCollector | `self, robot_id: str` | `List[JobResult]` | UNUSED |
| `get_results_by_workflow` | ResultCollector | `self, workflow_id: str` | `List[JobResult]` | UNUSED |
| `get_robot_stats` | ResultCollector | `self` | `Dict[str, ExecutionStatistics]` | UNUSED |
| `get_statistics` | ResultCollector | `self, workflow_id: Optional[str], robot_id: Optional[str], ...` | `ExecutionStatistics` | USED |
| `get_workflow_stats` | ResultCollector | `self` | `Dict[str, ExecutionStatistics]` | UNUSED |
| `pending_log_count` | ResultCollector | `self` | `int` | UNUSED |
| `result_count` | ResultCollector | `self` | `int` | UNUSED |
| `set_callbacks` | ResultCollector | `self, on_result_received: Optional[Callable], on_result_stored: Optional[Callable]` | `-` | USED |
| `to_csv` | ResultExporter | `results: List[JobResult]` | `str` | UNUSED |
| `to_json` | ResultExporter | `results: List[JobResult], pretty: bool` | `str` | USED |
| `to_summary` | ResultExporter | `results: List[JobResult]` | `Dict[str, Any]` | UNUSED |


## casare_rpa.application.orchestrator.services.robot_management_service

**File:** `src\casare_rpa\application\orchestrator\services\robot_management_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotManagementService | `self, robot_repository: RobotRepository` | `-` | DUNDER |
| `async connect` | RobotManagementService | `self` | `bool` | USED |
| `async get_available_robots` | RobotManagementService | `self` | `List[Robot]` | USED |
| `async get_robot` | RobotManagementService | `self, robot_id: str` | `Optional[Robot]` | USED |
| `async get_robots` | RobotManagementService | `self` | `List[Robot]` | USED |
| `is_cloud_mode` | RobotManagementService | `self` | `bool` | UNUSED |
| `async update_robot_status` | RobotManagementService | `self, robot_id: str, status: RobotStatus` | `bool` | USED |


## casare_rpa.application.orchestrator.services.schedule_management_service

**File:** `src\casare_rpa\application\orchestrator\services\schedule_management_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ScheduleManagementService | `self, schedule_repository: ScheduleRepository` | `-` | DUNDER |
| `async connect` | ScheduleManagementService | `self` | `bool` | USED |
| `async delete_schedule` | ScheduleManagementService | `self, schedule_id: str` | `bool` | USED |
| `async get_schedule` | ScheduleManagementService | `self, schedule_id: str` | `Optional[Schedule]` | USED |
| `async get_schedules` | ScheduleManagementService | `self, enabled_only: bool` | `List[Schedule]` | USED |
| `is_cloud_mode` | ScheduleManagementService | `self` | `bool` | UNUSED |
| `async save_schedule` | ScheduleManagementService | `self, schedule: Schedule` | `bool` | USED |
| `async toggle_schedule` | ScheduleManagementService | `self, schedule_id: str, enabled: bool` | `bool` | USED |


## casare_rpa.application.orchestrator.services.scheduling_coordinator

**File:** `src\casare_rpa\application\orchestrator\services\scheduling_coordinator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `calculate_next_run` | - | `frequency: ScheduleFrequency, cron_expression: str, timezone: str, ...` | `Optional[datetime]` | USED |
| `frequency_to_interval` | - | `frequency: ScheduleFrequency` | `Optional[timedelta]` | USED |
| `parse_cron_expression` | - | `cron_expr: str` | `Dict[str, str]` | USED |
| `__init__` | JobScheduler | `self, on_schedule_trigger: Optional[Callable[[Schedule], Any]], timezone: str` | `-` | DUNDER |
| `_create_trigger` | JobScheduler | `self, schedule: Schedule` | `-` | INTERNAL |
| `async _execute_schedule` | JobScheduler | `self, schedule_id: str` | `-` | INTERNAL |
| `add_schedule` | JobScheduler | `self, schedule: Schedule` | `bool` | USED |
| `disable_schedule` | JobScheduler | `self, schedule_id: str` | `bool` | USED |
| `enable_schedule` | JobScheduler | `self, schedule_id: str` | `bool` | USED |
| `get_next_runs` | JobScheduler | `self, limit: int` | `List[Dict[str, Any]]` | USED |
| `get_schedule_info` | JobScheduler | `self, schedule_id: str` | `Optional[Dict[str, Any]]` | UNUSED |
| `pause_all` | JobScheduler | `self` | `-` | UNUSED |
| `remove_schedule` | JobScheduler | `self, schedule_id: str` | `bool` | USED |
| `resume_all` | JobScheduler | `self` | `-` | UNUSED |
| `async start` | JobScheduler | `self` | `-` | USED |
| `async stop` | JobScheduler | `self` | `-` | USED |
| `update_schedule` | JobScheduler | `self, schedule: Schedule` | `bool` | USED |
| `__init__` | ScheduleManager | `self, job_creator: Callable[[Schedule], Any], timezone: str` | `-` | DUNDER |
| `async _on_trigger` | ScheduleManager | `self, schedule: Schedule` | `-` | INTERNAL |
| `add_schedule` | ScheduleManager | `self, schedule: Schedule` | `bool` | USED |
| `disable_schedule` | ScheduleManager | `self, schedule_id: str` | `bool` | USED |
| `enable_schedule` | ScheduleManager | `self, schedule_id: str` | `bool` | USED |
| `get_all_schedules` | ScheduleManager | `self` | `List[Schedule]` | USED |
| `get_schedule` | ScheduleManager | `self, schedule_id: str` | `Optional[Schedule]` | USED |
| `get_upcoming_runs` | ScheduleManager | `self, limit: int` | `List[Dict[str, Any]]` | USED |
| `remove_schedule` | ScheduleManager | `self, schedule_id: str` | `bool` | USED |
| `async start` | ScheduleManager | `self` | `-` | USED |
| `async stop` | ScheduleManager | `self` | `-` | USED |
| `update_schedule` | ScheduleManager | `self, schedule: Schedule` | `bool` | USED |


## casare_rpa.application.orchestrator.services.workflow_management_service

**File:** `src\casare_rpa\application\orchestrator\services\workflow_management_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowManagementService | `self, workflow_repository: WorkflowRepository` | `-` | DUNDER |
| `async connect` | WorkflowManagementService | `self` | `bool` | USED |
| `async delete_workflow` | WorkflowManagementService | `self, workflow_id: str` | `bool` | USED |
| `async get_workflow` | WorkflowManagementService | `self, workflow_id: str` | `Optional[Workflow]` | USED |
| `async get_workflows` | WorkflowManagementService | `self, status: Optional[WorkflowStatus]` | `List[Workflow]` | USED |
| `async import_workflow_from_file` | WorkflowManagementService | `self, file_path: Path` | `Optional[Workflow]` | UNUSED |
| `is_cloud_mode` | WorkflowManagementService | `self` | `bool` | UNUSED |
| `async save_workflow` | WorkflowManagementService | `self, workflow: Workflow` | `bool` | USED |


## casare_rpa.application.orchestrator.use_cases.assign_robot

**File:** `src\casare_rpa\application\orchestrator\use_cases\assign_robot.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AssignRobotUseCase | `self, robot_repository: RobotRepository, assignment_repository: WorkflowAssignmentRepository, ...` | `None` | DUNDER |
| `async activate_node_override` | AssignRobotUseCase | `self, workflow_id: str, node_id: str` | `bool` | UNUSED |
| `async assign_to_node` | AssignRobotUseCase | `self, workflow_id: str, node_id: str, ...` | `NodeRobotOverride` | UNUSED |
| `async assign_to_workflow` | AssignRobotUseCase | `self, workflow_id: str, robot_id: str, ...` | `RobotAssignment` | USED |
| `async deactivate_node_override` | AssignRobotUseCase | `self, workflow_id: str, node_id: str` | `bool` | UNUSED |
| `async get_active_node_overrides` | AssignRobotUseCase | `self, workflow_id: str` | `List[NodeRobotOverride]` | UNUSED |
| `async get_node_overrides` | AssignRobotUseCase | `self, workflow_id: str` | `List[NodeRobotOverride]` | UNUSED |
| `async get_workflow_assignments` | AssignRobotUseCase | `self, workflow_id: str` | `List[RobotAssignment]` | UNUSED |
| `async remove_all_node_overrides_for_robot` | AssignRobotUseCase | `self, robot_id: str` | `int` | UNUSED |
| `async remove_node_override` | AssignRobotUseCase | `self, workflow_id: str, node_id: str` | `bool` | UNUSED |
| `async remove_workflow_assignment` | AssignRobotUseCase | `self, workflow_id: str, robot_id: str` | `bool` | UNUSED |
| `async set_default_robot` | AssignRobotUseCase | `self, workflow_id: str, robot_id: str` | `None` | UNUSED |
| `async unassign_robot_from_all_workflows` | AssignRobotUseCase | `self, robot_id: str` | `int` | UNUSED |


## casare_rpa.application.orchestrator.use_cases.execute_job

**File:** `src\casare_rpa\application\orchestrator\use_cases\execute_job.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecuteJobUseCase | `self, job_repository: JobRepository, robot_repository: RobotRepository` | `-` | DUNDER |
| `async execute` | ExecuteJobUseCase | `self, job_id: str` | `Job` | USED |


## casare_rpa.application.orchestrator.use_cases.execute_local

**File:** `src\casare_rpa\application\orchestrator\use_cases\execute_local.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecuteLocalUseCase | `self, event_bus: Optional[EventBus]` | `None` | DUNDER |
| `_parse_workflow` | ExecuteLocalUseCase | `self, workflow_data: Dict[str, Any]` | `WorkflowSchema` | INTERNAL |
| `async execute` | ExecuteLocalUseCase | `self, workflow_data: Dict[str, Any], variables: Optional[Dict[str, Any]], ...` | `ExecutionResult` | USED |
| `async execute_from_json` | ExecuteLocalUseCase | `self, workflow_json: str, variables: Optional[Dict[str, Any]], ...` | `ExecutionResult` | UNUSED |
| `__init__` | ExecutionResult | `self, success: bool, workflow_name: str, ...` | `None` | DUNDER |
| `__repr__` | ExecutionResult | `self` | `str` | DUNDER |
| `progress` | ExecutionResult | `self` | `float` | UNUSED |
| `to_dict` | ExecutionResult | `self` | `Dict[str, Any]` | USED |


## casare_rpa.application.orchestrator.use_cases.list_robots

**File:** `src\casare_rpa\application\orchestrator\use_cases\list_robots.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ListRobotsUseCase | `self, robot_repository: RobotRepository, assignment_repository: Optional[WorkflowAssignmentRepository]` | `None` | DUNDER |
| `async get_all` | ListRobotsUseCase | `self` | `List[Robot]` | USED |
| `async get_available` | ListRobotsUseCase | `self` | `List[Robot]` | USED |
| `async get_busy` | ListRobotsUseCase | `self` | `List[Robot]` | UNUSED |
| `async get_by_capabilities` | ListRobotsUseCase | `self, capabilities: List[RobotCapability]` | `List[Robot]` | USED |
| `async get_by_capability` | ListRobotsUseCase | `self, capability: RobotCapability` | `List[Robot]` | USED |
| `async get_by_id` | ListRobotsUseCase | `self, robot_id: str` | `Optional[Robot]` | USED |
| `async get_by_name` | ListRobotsUseCase | `self, name: str` | `Optional[Robot]` | UNUSED |
| `async get_default_for_workflow` | ListRobotsUseCase | `self, workflow_id: str` | `Optional[Robot]` | USED |
| `async get_for_workflow` | ListRobotsUseCase | `self, workflow_id: str` | `List[Robot]` | UNUSED |
| `async get_offline` | ListRobotsUseCase | `self` | `List[Robot]` | UNUSED |
| `async get_online` | ListRobotsUseCase | `self` | `List[Robot]` | UNUSED |
| `async get_statistics` | ListRobotsUseCase | `self` | `dict` | USED |
| `async get_with_available_capacity` | ListRobotsUseCase | `self, min_capacity: int` | `List[Robot]` | UNUSED |
| `async search` | ListRobotsUseCase | `self, query: str` | `List[Robot]` | USED |


## casare_rpa.application.orchestrator.use_cases.submit_job

**File:** `src\casare_rpa\application\orchestrator\use_cases\submit_job.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SubmitJobUseCase | `self, job_repository: JobRepository, robot_repository: RobotRepository, ...` | `None` | DUNDER |
| `_analyze_workflow_capabilities` | SubmitJobUseCase | `self, workflow_data: Dict[str, Any]` | `Optional[Set[RobotCapability]]` | INTERNAL |
| `async _dispatch_job` | SubmitJobUseCase | `self, job: Job, robot: Optional[Robot]` | `None` | INTERNAL |
| `_prepare_workflow_json` | SubmitJobUseCase | `self, workflow_data: Dict[str, Any], variables: Optional[Dict[str, Any]]` | `str` | INTERNAL |
| `async execute` | SubmitJobUseCase | `self, workflow_id: str, workflow_data: Dict[str, Any], ...` | `Job` | USED |


## casare_rpa.application.scheduling.schedule_storage

**File:** `src\casare_rpa\application\scheduling\schedule_storage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_storage_singleton` | - | `` | `ScheduleStorage` | INTERNAL |
| `get_schedule_storage` | - | `` | `ScheduleStorage` | USED |
| `reset_schedule_storage` | - | `` | `None` | UNUSED |
| `set_schedule_storage` | - | `storage: ScheduleStorage` | `None` | UNUSED |
| `__init__` | ScheduleStorage | `self, storage_path: Optional[Path]` | `-` | DUNDER |
| `_load_raw` | ScheduleStorage | `self` | `List[Dict[str, Any]]` | INTERNAL |
| `_save_raw` | ScheduleStorage | `self, data: List[Dict[str, Any]]` | `bool` | INTERNAL |
| `delete_schedule` | ScheduleStorage | `self, schedule_id: str` | `bool` | USED |
| `get_all_schedules` | ScheduleStorage | `self` | `List[WorkflowSchedule]` | USED |
| `get_due_schedules` | ScheduleStorage | `self` | `List[WorkflowSchedule]` | UNUSED |
| `get_enabled_schedules` | ScheduleStorage | `self` | `List[WorkflowSchedule]` | USED |
| `get_schedule` | ScheduleStorage | `self, schedule_id: str` | `Optional[WorkflowSchedule]` | USED |
| `get_schedules_for_workflow` | ScheduleStorage | `self, workflow_path: str` | `List[WorkflowSchedule]` | UNUSED |
| `mark_schedule_run` | ScheduleStorage | `self, schedule_id: str, success: bool, ...` | `bool` | UNUSED |
| `save_all_schedules` | ScheduleStorage | `self, schedules: List[WorkflowSchedule]` | `bool` | USED |
| `save_schedule` | ScheduleStorage | `self, schedule: WorkflowSchedule` | `bool` | USED |


## casare_rpa.application.services.execution_lifecycle_manager

**File:** `src\casare_rpa\application\services\execution_lifecycle_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionLifecycleManager | `self` | `-` | DUNDER |
| `async _cleanup_session` | ExecutionLifecycleManager | `self` | `-` | INTERNAL |
| `async _force_cleanup` | ExecutionLifecycleManager | `self` | `-` | INTERNAL |
| `async _kill_orphaned_browsers` | ExecutionLifecycleManager | `self` | `-` | INTERNAL |
| `async _run_all_workflows_with_session` | ExecutionLifecycleManager | `self, workflow_runner, session_id: str, ...` | `-` | INTERNAL |
| `async _run_workflow_with_session` | ExecutionLifecycleManager | `self, workflow_runner, session_id: str, ...` | `-` | INTERNAL |
| `async _track_browser_pid` | ExecutionLifecycleManager | `self, context` | `-` | INTERNAL |
| `get_session_info` | ExecutionLifecycleManager | `self` | `Optional[dict]` | UNUSED |
| `get_state` | ExecutionLifecycleManager | `self` | `ExecutionState` | USED |
| `is_running` | ExecutionLifecycleManager | `self` | `bool` | USED |
| `async pause_workflow` | ExecutionLifecycleManager | `self` | `bool` | USED |
| `async resume_workflow` | ExecutionLifecycleManager | `self` | `bool` | USED |
| `async start_workflow` | ExecutionLifecycleManager | `self, workflow_runner, force_cleanup: bool, ...` | `bool` | USED |
| `async start_workflow_run_all` | ExecutionLifecycleManager | `self, workflow_runner, force_cleanup: bool` | `bool` | USED |
| `async stop_workflow` | ExecutionLifecycleManager | `self, force: bool` | `bool` | USED |
| `__post_init__` | ExecutionSession | `self` | `-` | DUNDER |


## casare_rpa.application.services.orchestrator_client

**File:** `src\casare_rpa\application\services\orchestrator_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AiohttpClient | `self` | `None` | DUNDER |
| `async _get_session` | AiohttpClient | `self` | `-` | INTERNAL |
| `async close` | AiohttpClient | `self` | `None` | USED |
| `async post` | AiohttpClient | `self, url: str, json: Dict[str, Any]` | `tuple[int, Dict[str, Any], str]` | USED |
| `async close` | HttpClient | `self` | `None` | USED |
| `async post` | HttpClient | `self, url: str, json: Dict[str, Any]` | `tuple[int, Dict[str, Any], str]` | USED |
| `__init__` | OrchestratorClient | `self, orchestrator_url: str, http_client: Optional[HttpClient]` | `None` | DUNDER |
| `async close` | OrchestratorClient | `self` | `None` | USED |
| `async submit_workflow` | OrchestratorClient | `self, workflow_name: str, workflow_json: Dict[str, Any], ...` | `WorkflowSubmissionResult` | USED |


## casare_rpa.application.services.port_type_service

**File:** `src\casare_rpa\application\services\port_type_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_port_type_registry` | - | `` | `PortTypeRegistry` | USED |
| `get_type_color` | - | `data_type: DataType` | `Tuple[int, int, int, int]` | USED |
| `is_types_compatible` | - | `source: DataType, target: DataType` | `bool` | UNUSED |
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


## casare_rpa.application.services.template_loader

**File:** `src\casare_rpa\application\services\template_loader.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TemplateLibraryService | `self, loader: Optional[TemplateLoader]` | `None` | DUNDER |
| `browse_templates` | TemplateLibraryService | `self, category: Optional[TemplateCategory], difficulty: Optional[str], ...` | `List[WorkflowTemplate]` | UNUSED |
| `get_featured_templates` | TemplateLibraryService | `self` | `List[WorkflowTemplate]` | UNUSED |
| `get_template_for_instantiation` | TemplateLibraryService | `self, template_id: str` | `Optional[WorkflowTemplate]` | UNUSED |
| `get_templates_for_category_page` | TemplateLibraryService | `self, category: TemplateCategory` | `Dict[str, any]` | UNUSED |
| `initialize` | TemplateLibraryService | `self` | `None` | USED |
| `__init__` | TemplateLoader | `self, templates_dir: Optional[Path]` | `None` | DUNDER |
| `_get_default_templates_dir` | TemplateLoader | `` | `Path` | INTERNAL |
| `_load_template_file` | TemplateLoader | `self, file_path: Path` | `Optional[WorkflowTemplate]` | INTERNAL |
| `get_all_templates` | TemplateLoader | `self` | `List[WorkflowTemplate]` | USED |
| `get_categories_with_counts` | TemplateLoader | `self` | `Dict[str, int]` | USED |
| `get_popular_templates` | TemplateLoader | `self, limit: int` | `List[WorkflowTemplate]` | USED |
| `get_template` | TemplateLoader | `self, template_id: str` | `Optional[WorkflowTemplate]` | USED |
| `get_template_statistics` | TemplateLoader | `self` | `Dict[str, any]` | USED |
| `get_templates_by_category` | TemplateLoader | `self, category: TemplateCategory` | `List[WorkflowTemplate]` | USED |
| `get_templates_by_difficulty` | TemplateLoader | `self, difficulty: str` | `List[WorkflowTemplate]` | UNUSED |
| `get_top_rated_templates` | TemplateLoader | `self, limit: int, min_ratings: int` | `List[WorkflowTemplate]` | USED |
| `load_templates` | TemplateLoader | `self, force_reload: bool` | `int` | USED |
| `reload` | TemplateLoader | `self` | `int` | USED |
| `search_templates` | TemplateLoader | `self, query: str, category: Optional[TemplateCategory], ...` | `List[WorkflowTemplate]` | USED |


## casare_rpa.application.use_cases.error_recovery

**File:** `src\casare_rpa\application\use_cases\error_recovery.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async handle_node_error` | - | `exception: Exception, node_id: NodeId, node_type: str, ...` | `RecoveryResult` | UNUSED |
| `__init__` | ErrorRecoveryIntegration | `self, config: Optional[ErrorRecoveryConfig]` | `None` | DUNDER |
| `create_custom_handler` | ErrorRecoveryIntegration | `self, name: str, handler_func: Callable[[ErrorContext], Optional[RecoveryDecision]]` | `None` | UNUSED |
| `get_report` | ErrorRecoveryIntegration | `self` | `Dict[str, Any]` | UNUSED |
| `set_execution_context` | ErrorRecoveryIntegration | `self, context: 'ExecutionContext'` | `None` | USED |
| `async wrap_node_execution` | ErrorRecoveryIntegration | `self, node_id: NodeId, node_type: str, ...` | `tuple[bool, Any]` | UNUSED |
| `__init__` | ErrorRecoveryUseCase | `self, config: Optional[ErrorRecoveryConfig], error_registry: Optional[ErrorHandlerRegistry], ...` | `None` | DUNDER |
| `_aggregate_error` | ErrorRecoveryUseCase | `self, context: ErrorContext` | `None` | INTERNAL |
| `_build_recovery_result` | ErrorRecoveryUseCase | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `RecoveryResult` | INTERNAL |
| `_emit_error_event` | ErrorRecoveryUseCase | `self, context: ErrorContext, decision: RecoveryDecision` | `None` | INTERNAL |
| `async _execute_recovery` | ErrorRecoveryUseCase | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `RecoveryResult` | INTERNAL |
| `_update_circuit_breaker` | ErrorRecoveryUseCase | `self, context: ErrorContext, success: bool` | `None` | INTERNAL |
| `get_error_report` | ErrorRecoveryUseCase | `self` | `Dict[str, Any]` | USED |
| `get_node_error_history` | ErrorRecoveryUseCase | `self, node_id: NodeId, limit: int` | `List[Dict[str, Any]]` | UNUSED |
| `async handle_error` | ErrorRecoveryUseCase | `self, exception: Exception, node_id: NodeId, ...` | `RecoveryResult` | USED |
| `record_success` | ErrorRecoveryUseCase | `self, node_id: NodeId, node_type: str` | `None` | USED |
| `reset` | ErrorRecoveryUseCase | `self` | `None` | USED |
| `__repr__` | RecoveryResult | `self` | `str` | DUNDER |


## casare_rpa.application.use_cases.execute_workflow

**File:** `src\casare_rpa\application\use_cases\execute_workflow.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_create_node_from_dict` | - | `node_data: dict` | `Any` | INTERNAL |
| `__init__` | ExecuteWorkflowUseCase | `self, workflow: WorkflowSchema, event_bus: Optional[EventBus], ...` | `None` | DUNDER |
| `__repr__` | ExecuteWorkflowUseCase | `self` | `str` | DUNDER |
| `async _execute_branch_to_join` | ExecuteWorkflowUseCase | `self, start_node_id: str, branch_context: ExecutionContext, ...` | `None` | INTERNAL |
| `async _execute_from_node` | ExecuteWorkflowUseCase | `self, start_node_id: NodeId` | `None` | INTERNAL |
| `async _execute_from_node_with_context` | ExecuteWorkflowUseCase | `self, start_node_id: NodeId, context: ExecutionContext` | `None` | INTERNAL |
| `async _execute_item_body` | ExecuteWorkflowUseCase | `self, start_node_id: str, item_context: ExecutionContext, ...` | `None` | INTERNAL |
| `async _execute_parallel_branches` | ExecuteWorkflowUseCase | `self, fork_result: Dict[str, Any]` | `None` | INTERNAL |
| `async _execute_parallel_branches_async` | ExecuteWorkflowUseCase | `self, fork_result: Dict[str, Any], nodes_to_execute: List[NodeId]` | `None` | INTERNAL |
| `async _execute_parallel_foreach_batch` | ExecuteWorkflowUseCase | `self, foreach_result: Dict[str, Any], foreach_node_id: str` | `None` | INTERNAL |
| `async _execute_parallel_foreach_batch_async` | ExecuteWorkflowUseCase | `self, foreach_result: Dict[str, Any], current_node_id: str, ...` | `None` | INTERNAL |
| `async _execute_parallel_workflows` | ExecuteWorkflowUseCase | `self, start_nodes: List[NodeId]` | `None` | INTERNAL |
| `async _execute_single_node` | ExecuteWorkflowUseCase | `self, node_id: NodeId` | `None` | INTERNAL |
| `_finalize_execution` | ExecuteWorkflowUseCase | `self` | `bool` | INTERNAL |
| `_get_node_instance` | ExecuteWorkflowUseCase | `self, node_id: str` | `Any` | INTERNAL |
| `_handle_execution_failure` | ExecuteWorkflowUseCase | `self, node_id: NodeId, result: Optional[Dict[str, Any]], ...` | `bool` | INTERNAL |
| `_handle_special_results` | ExecuteWorkflowUseCase | `self, current_node_id: NodeId, exec_result: Any, ...` | `Optional[bool]` | INTERNAL |
| `current_node_id` | ExecuteWorkflowUseCase | `self` | `Optional[NodeId]` | UNUSED |
| `end_time` | ExecuteWorkflowUseCase | `self` | `Optional[datetime]` | UNUSED |
| `async execute` | ExecuteWorkflowUseCase | `self, run_all: bool` | `bool` | USED |
| `async execute_branch` | ExecuteWorkflowUseCase | `branch_port: str` | `Tuple[str, Dict[str, Any], bool]` | USED |
| `async execute_single_workflow` | ExecuteWorkflowUseCase | `start_id: NodeId, index: int` | `Tuple[str, bool]` | USED |
| `executed_nodes` | ExecuteWorkflowUseCase | `self` | `Set[NodeId]` | UNUSED |
| `async process_item` | ExecuteWorkflowUseCase | `item: Any, index: int` | `Tuple[int, Any, bool]` | USED |
| `start_time` | ExecuteWorkflowUseCase | `self` | `Optional[datetime]` | UNUSED |
| `stop` | ExecuteWorkflowUseCase | `self` | `None` | USED |


## casare_rpa.application.use_cases.execution_state_manager

**File:** `src\casare_rpa\application\use_cases\execution_state_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionSettings | `self, continue_on_error: bool, node_timeout: float, ...` | `None` | DUNDER |
| `__init__` | ExecutionStateManager | `self, workflow: WorkflowSchema, orchestrator: ExecutionOrchestrator, ...` | `None` | DUNDER |
| `_calculate_subgraph` | ExecutionStateManager | `self` | `None` | INTERNAL |
| `calculate_progress` | ExecutionStateManager | `self` | `float` | USED |
| `duration` | ExecutionStateManager | `self` | `float` | UNUSED |
| `emit_event` | ExecutionStateManager | `self, event_type: EventType, data: Dict[str, Any], ...` | `None` | USED |
| `execution_error` | ExecutionStateManager | `self` | `Optional[str]` | UNUSED |
| `get_execution_summary` | ExecutionStateManager | `self` | `Dict[str, Any]` | USED |
| `is_failed` | ExecutionStateManager | `self` | `bool` | UNUSED |
| `is_stopped` | ExecutionStateManager | `self` | `bool` | USED |
| `mark_completed` | ExecutionStateManager | `self` | `None` | USED |
| `mark_failed` | ExecutionStateManager | `self, error: str` | `None` | USED |
| `mark_node_executed` | ExecutionStateManager | `self, node_id: NodeId` | `None` | USED |
| `mark_target_reached` | ExecutionStateManager | `self, node_id: NodeId` | `bool` | USED |
| `async pause_checkpoint` | ExecutionStateManager | `self` | `None` | USED |
| `set_current_node` | ExecutionStateManager | `self, node_id: Optional[NodeId]` | `None` | USED |
| `should_execute_node` | ExecutionStateManager | `self, node_id: NodeId` | `bool` | USED |
| `start_execution` | ExecutionStateManager | `self` | `None` | USED |
| `stop` | ExecutionStateManager | `self` | `None` | USED |
| `target_reached` | ExecutionStateManager | `self` | `bool` | UNUSED |
| `total_nodes` | ExecutionStateManager | `self` | `int` | UNUSED |


## casare_rpa.application.use_cases.node_executor

**File:** `src\casare_rpa\application\use_cases\node_executor.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeExecutionResult | `self, success: bool, result: Optional[Dict[str, Any]], ...` | `None` | DUNDER |
| `__init__` | NodeExecutor | `self, context: ExecutionContext, event_bus: Optional[EventBus], ...` | `None` | DUNDER |
| `_emit_event` | NodeExecutor | `self, event_type: EventType, data: Dict[str, Any], ...` | `None` | INTERNAL |
| `async _execute_with_timeout` | NodeExecutor | `self, node: Any` | `Dict[str, Any]` | INTERNAL |
| `_handle_bypassed_node` | NodeExecutor | `self, node: Any` | `NodeExecutionResult` | INTERNAL |
| `_handle_exception` | NodeExecutor | `self, node: Any, exception: Exception, ...` | `NodeExecutionResult` | INTERNAL |
| `_process_result` | NodeExecutor | `self, node: Any, result: Optional[Dict[str, Any]], ...` | `NodeExecutionResult` | INTERNAL |
| `_validate_node` | NodeExecutor | `self, node: Any, start_time: float` | `Optional[NodeExecutionResult]` | INTERNAL |
| `async execute` | NodeExecutor | `self, node: Any` | `NodeExecutionResult` | USED |
| `__init__` | NodeExecutorWithTryCatch | `self, context: ExecutionContext, event_bus: Optional[EventBus], ...` | `None` | DUNDER |
| `_handle_exception` | NodeExecutorWithTryCatch | `self, node: Any, exception: Exception, ...` | `NodeExecutionResult` | INTERNAL |


## casare_rpa.application.use_cases.project_management

**File:** `src\casare_rpa\application\use_cases\project_management.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CreateProjectUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | CreateProjectUseCase | `self, name: str, path: Path, ...` | `ProjectResult` | USED |
| `__init__` | CreateScenarioUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | CreateScenarioUseCase | `self, project_id: str, name: str, ...` | `ScenarioResult` | USED |
| `__init__` | DeleteProjectUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | DeleteProjectUseCase | `self, project_id: str, remove_files: bool` | `ProjectResult` | USED |
| `__init__` | DeleteScenarioUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | DeleteScenarioUseCase | `self, project_id: str, scenario_id: str` | `ScenarioResult` | USED |
| `__init__` | ListProjectsUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | ListProjectsUseCase | `self, limit: Optional[int]` | `ProjectListResult` | USED |
| `__init__` | ListScenariosUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | ListScenariosUseCase | `self, project_id: str` | `List[Scenario]` | USED |
| `__init__` | LoadProjectUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | LoadProjectUseCase | `self, project_id: Optional[str], path: Optional[Path]` | `ProjectResult` | USED |
| `__init__` | LoadScenarioUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | LoadScenarioUseCase | `self, project_id: str, scenario_id: str` | `ScenarioResult` | USED |
| `__post_init__` | ProjectListResult | `self` | `-` | DUNDER |
| `__init__` | SaveProjectUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | SaveProjectUseCase | `self, project: Project` | `ProjectResult` | USED |
| `__init__` | SaveScenarioUseCase | `self, repository: ProjectRepository` | `None` | DUNDER |
| `async execute` | SaveScenarioUseCase | `self, project_id: str, scenario: Scenario` | `ScenarioResult` | USED |


## casare_rpa.application.use_cases.template_management

**File:** `src\casare_rpa\application\use_cases\template_management.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CloneTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | CloneTemplateUseCase | `self, template_id: str, new_name: Optional[str]` | `Optional[WorkflowTemplate]` | USED |
| `__init__` | CreateTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `_map_variable_type` | CreateTemplateUseCase | `self, var_type: str` | `str` | INTERNAL |
| `async execute` | CreateTemplateUseCase | `self, name: str, description: str, ...` | `WorkflowTemplate` | USED |
| `async from_workflow` | CreateTemplateUseCase | `self, workflow_data: Dict[str, Any], name: str, ...` | `WorkflowTemplate` | UNUSED |
| `__init__` | DeleteTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | DeleteTemplateUseCase | `self, template_id: str` | `bool` | USED |
| `__init__` | ExportTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async to_file` | ExportTemplateUseCase | `self, template_id: str, file_path: Path` | `bool` | UNUSED |
| `async to_json` | ExportTemplateUseCase | `self, template_id: str` | `Optional[bytes]` | USED |
| `__init__` | GetTemplateCategoriesUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | GetTemplateCategoriesUseCase | `self` | `Dict[str, int]` | USED |
| `__init__` | GetTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async all` | GetTemplateUseCase | `self` | `List[WorkflowTemplate]` | USED |
| `async builtin` | GetTemplateUseCase | `self` | `List[WorkflowTemplate]` | UNUSED |
| `async by_category` | GetTemplateUseCase | `self, category: TemplateCategory` | `List[WorkflowTemplate]` | UNUSED |
| `async by_id` | GetTemplateUseCase | `self, template_id: str` | `Optional[WorkflowTemplate]` | UNUSED |
| `async user_created` | GetTemplateUseCase | `self` | `List[WorkflowTemplate]` | UNUSED |
| `__init__` | ImportTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async from_file` | ImportTemplateUseCase | `self, file_path: Path, overwrite: bool` | `WorkflowTemplate` | USED |
| `async from_json` | ImportTemplateUseCase | `self, json_data: bytes, overwrite: bool` | `WorkflowTemplate` | USED |
| `__init__` | InstantiateTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | InstantiateTemplateUseCase | `self, template_id: str, parameter_values: Dict[str, Any], ...` | `TemplateInstantiationResult` | USED |
| `__init__` | RateTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | RateTemplateUseCase | `self, template_id: str, rating: float` | `bool` | USED |
| `__init__` | SearchTemplatesUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `_apply_filters` | SearchTemplatesUseCase | `self, templates: List[WorkflowTemplate], criteria: TemplateSearchCriteria` | `List[WorkflowTemplate]` | INTERNAL |
| `_sort_templates` | SearchTemplatesUseCase | `self, templates: List[WorkflowTemplate], criteria: TemplateSearchCriteria` | `List[WorkflowTemplate]` | INTERNAL |
| `async execute` | SearchTemplatesUseCase | `self, criteria: TemplateSearchCriteria` | `TemplateSearchResult` | USED |
| `async delete` | TemplateRepository | `self, template_id: str` | `bool` | USED |
| `async exists` | TemplateRepository | `self, template_id: str` | `bool` | USED |
| `async get_all` | TemplateRepository | `self` | `List[WorkflowTemplate]` | USED |
| `async get_by_category` | TemplateRepository | `self, category: TemplateCategory` | `List[WorkflowTemplate]` | USED |
| `async get_by_id` | TemplateRepository | `self, template_id: str` | `Optional[WorkflowTemplate]` | USED |
| `async save` | TemplateRepository | `self, template: WorkflowTemplate` | `None` | USED |
| `async search` | TemplateRepository | `self, query: str, category: Optional[TemplateCategory], ...` | `List[WorkflowTemplate]` | USED |
| `__init__` | UpdateTemplateUseCase | `self, repository: TemplateRepository` | `None` | DUNDER |
| `async execute` | UpdateTemplateUseCase | `self, template_id: str, updates: Dict[str, Any]` | `Optional[WorkflowTemplate]` | USED |


## casare_rpa.application.use_cases.validate_workflow

**File:** `src\casare_rpa\application\use_cases\validate_workflow.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ValidateWorkflowUseCase | `self` | `None` | DUNDER |
| `_compute_hash` | ValidateWorkflowUseCase | `self, workflow: Any` | `str` | INTERNAL |
| `_validate` | ValidateWorkflowUseCase | `self, workflow: Any` | `ValidationResult` | INTERNAL |
| `clear_cache` | ValidateWorkflowUseCase | `cls` | `None` | USED |
| `execute` | ValidateWorkflowUseCase | `self, workflow: Any` | `ValidationResult` | USED |
| `get_cache_stats` | ValidateWorkflowUseCase | `cls` | `Dict[str, Any]` | UNUSED |
| `invalidate_cache` | ValidateWorkflowUseCase | `self, workflow: Optional[Any]` | `None` | USED |
| `error_count` | ValidationResult | `self` | `int` | UNUSED |
| `errors` | ValidationResult | `self` | `List[ValidationIssue]` | USED |
| `warning_count` | ValidationResult | `self` | `int` | UNUSED |
| `warnings` | ValidationResult | `self` | `List[ValidationIssue]` | UNUSED |


## casare_rpa.application.use_cases.variable_resolver

**File:** `src\casare_rpa\application\use_cases\variable_resolver.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TryCatchErrorHandler | `self, context: ExecutionContext` | `None` | DUNDER |
| `capture_error` | TryCatchErrorHandler | `self, error_msg: str, error_type: str, ...` | `bool` | USED |
| `capture_from_result` | TryCatchErrorHandler | `self, result: Optional[Dict[str, Any]], node_id: str` | `bool` | USED |
| `find_catch_node_id` | TryCatchErrorHandler | `self` | `Optional[str]` | USED |
| `__init__` | VariableResolver | `self, workflow: WorkflowSchema, node_getter: callable` | `None` | DUNDER |
| `_get_data_output_ports` | VariableResolver | `self, output_ports_dict: Dict[str, Any]` | `List[str]` | INTERNAL |
| `transfer_data` | VariableResolver | `self, connection: Any` | `None` | USED |
| `transfer_inputs_to_node` | VariableResolver | `self, node_id: str` | `None` | USED |
| `validate_output_ports` | VariableResolver | `self, node: Any, result: Dict[str, Any]` | `bool` | USED |


## casare_rpa.application.use_cases.workflow_migration

**File:** `src\casare_rpa\application\use_cases\workflow_migration.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_registry_singleton` | - | `` | `MigrationRuleRegistry` | INTERNAL |
| `decorator` | - | `func: Callable[[NodeData], NodeData]` | `Callable[[NodeData], NodeData]` | UNUSED |
| `get_rule_registry` | - | `` | `MigrationRuleRegistry` | USED |
| `register_migration_rule` | - | `node_type: str, from_version_range: Tuple[str, str], to_version_range: Tuple[str, str], ...` | `Callable` | UNUSED |
| `reset_rule_registry` | - | `` | `None` | UNUSED |
| `__init__` | AutoMigrationPolicy | `self, auto_patch_updates: bool, auto_minor_updates: bool, ...` | `None` | DUNDER |
| `from_dict` | AutoMigrationPolicy | `cls, data: Dict[str, Any]` | `'AutoMigrationPolicy'` | USED |
| `manual` | AutoMigrationPolicy | `cls` | `'AutoMigrationPolicy'` | UNUSED |
| `permissive` | AutoMigrationPolicy | `cls` | `'AutoMigrationPolicy'` | UNUSED |
| `should_auto_migrate` | AutoMigrationPolicy | `self, from_version: SemanticVersion, to_version: SemanticVersion, ...` | `Tuple[bool, str]` | UNUSED |
| `strict` | AutoMigrationPolicy | `cls` | `'AutoMigrationPolicy'` | UNUSED |
| `to_dict` | AutoMigrationPolicy | `self` | `Dict[str, Any]` | USED |
| `to_dict` | MigrationResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | MigrationRuleRegistry | `self` | `None` | DUNDER |
| `find_rules` | MigrationRuleRegistry | `self, node_type: str, from_version: SemanticVersion, ...` | `List[NodeMigrationRule]` | USED |
| `register` | MigrationRuleRegistry | `self, rule: NodeMigrationRule` | `None` | USED |
| `__init__` | NodeMigrationRule | `self, node_type: str, from_version_range: Tuple[str, str], ...` | `None` | DUNDER |
| `applies_to` | NodeMigrationRule | `self, node_type: str, from_version: SemanticVersion, ...` | `bool` | USED |
| `__init__` | VersionPinManager | `self, version_history: VersionHistory` | `None` | DUNDER |
| `from_dict` | VersionPinManager | `cls, data: Dict[str, Any], version_history: VersionHistory` | `'VersionPinManager'` | USED |
| `get_execution_version` | VersionPinManager | `self, job_id: str` | `Optional[WorkflowVersion]` | UNUSED |
| `get_jobs_pinned_to_version` | VersionPinManager | `self, version_str: str` | `List[str]` | UNUSED |
| `get_pinned_version` | VersionPinManager | `self, job_id: str` | `Optional[str]` | UNUSED |
| `pin_job` | VersionPinManager | `self, job_id: str, version_str: str, ...` | `bool` | UNUSED |
| `to_dict` | VersionPinManager | `self` | `Dict[str, Any]` | USED |
| `unpin_job` | VersionPinManager | `self, job_id: str` | `bool` | UNUSED |
| `validate_pins` | VersionPinManager | `self` | `List[Tuple[str, str]]` | UNUSED |
| `__init__` | WorkflowMigrationUseCase | `self, version_history: VersionHistory, event_bus: Optional[EventBus], ...` | `None` | DUNDER |
| `_build_migration_steps` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `None` | INTERNAL |
| `_determine_version_bump` | WorkflowMigrationUseCase | `self, compatibility: CompatibilityResult` | `str` | INTERNAL |
| `_emit_event` | WorkflowMigrationUseCase | `self, event_type: EventType, data: Dict[str, JsonValue]` | `None` | INTERNAL |
| `async _rollback_migration` | WorkflowMigrationUseCase | `self, context: MigrationContext, result: MigrationResult` | `None` | INTERNAL |
| `_step_migrate_nodes` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `bool` | INTERNAL |
| `_step_migrate_variables` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `bool` | INTERNAL |
| `_step_update_connections` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `bool` | INTERNAL |
| `_step_update_settings` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `bool` | INTERNAL |
| `_step_validate_result` | WorkflowMigrationUseCase | `self, context: MigrationContext` | `bool` | INTERNAL |
| `check_migration_feasibility` | WorkflowMigrationUseCase | `self, from_version: str, to_version: str` | `Tuple[bool, CompatibilityResult, str]` | USED |
| `async migrate` | WorkflowMigrationUseCase | `self, from_version: str, to_version: str, ...` | `MigrationResult` | UNUSED |
| `async validate_running_jobs` | WorkflowMigrationUseCase | `self, target_version: str, running_job_ids: List[str]` | `Tuple[bool, List[str]]` | UNUSED |


## casare_rpa.application.workflow.recent_files

**File:** `src\casare_rpa\application\workflow\recent_files.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_manager_singleton` | - | `` | `RecentFilesManager` | INTERNAL |
| `get_recent_files_manager` | - | `` | `RecentFilesManager` | USED |
| `reset_recent_files_manager` | - | `` | `None` | UNUSED |
| `__init__` | RecentFilesManager | `self` | `None` | DUNDER |
| `_load` | RecentFilesManager | `self` | `None` | INTERNAL |
| `_save` | RecentFilesManager | `self` | `None` | INTERNAL |
| `add_file` | RecentFilesManager | `self, file_path: Path` | `None` | USED |
| `clear` | RecentFilesManager | `self` | `None` | USED |
| `get_recent_files` | RecentFilesManager | `self` | `List[dict]` | USED |
| `remove_file` | RecentFilesManager | `self, file_path: Path` | `None` | USED |


## casare_rpa.application.workflow.workflow_import

**File:** `src\casare_rpa\application\workflow\workflow_import.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `import_workflow_data` | - | `graph, node_factory, workflow_data: dict, ...` | `Tuple[dict, Dict[str, str]]` | UNUSED |
| `__init__` | WorkflowImporter | `self, graph, node_factory` | `-` | DUNDER |
| `apply_position_offset` | WorkflowImporter | `self, workflow_data: dict, offset: Tuple[float, float]` | `dict` | USED |
| `calculate_import_position` | WorkflowImporter | `self, workflow_data: dict, drop_position: Optional[Tuple[float, float]]` | `Tuple[float, float]` | USED |
| `get_existing_node_ids` | WorkflowImporter | `self` | `Set[str]` | USED |
| `remap_node_ids` | WorkflowImporter | `self, workflow_data: dict` | `Tuple[dict, Dict[str, str]]` | USED |
