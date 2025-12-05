# Research: Unused Functions Analysis

## Executive Summary

The inventory documents **1807 potentially unused functions**. After analysis, these fall into several categories with different cleanup recommendations.

## Classification Categories

### 1. FALSE POSITIVES - Not Actually Unused (KEEP)

These functions are used but the static analysis missed the call pattern.

#### A. Decorator Functions (5 functions)
- `executable_node` - Used via `@executable_node` syntax (106 uses found)
- `node_schema` - Used via `@node_schema` syntax (93 uses found)
- `decorator` (multiple) - Internal decorator wrappers
- `wrapped_init`, `wrapped_define` - Decorator internals

**Reason:** Static analyzers miss decorator usage since `@decorator` isn't a direct function call.

#### B. CLI Entry Points (4 functions)
- `start_orchestrator` - Typer command handler
- `start_canvas` - Typer command handler
- `tunnel_start` - Typer command handler
- `run_auto_setup` - Typer command handler
- `setup_db` - Typer command handler

**Reason:** Called via Typer's command dispatch (`@app.command()`), not direct invocation.

#### C. FastAPI Route Handlers (~50+ functions)
Examples:
- `cancel_job`, `retry_job` - REST endpoints
- `health_check`, `liveness_check`, `readiness_check` - Health endpoints
- `list_robots`, `robot_heartbeat` - Robot management endpoints
- `create_schedule`, `list_schedules`, `trigger_schedule_now` - Schedule endpoints
- `websocket_live_jobs`, `websocket_robot_status` - WebSocket handlers
- All functions in `routers/` marked with `@router.get/post/delete/websocket`

**Reason:** Invoked by FastAPI/Starlette request routing, not direct code calls.

#### D. Property Accessors (~100+ functions)
Examples:
- `success_rate`, `failure_rate` - Computed properties on metrics classes
- `is_available`, `utilization` - Robot state properties
- `center_x`, `center_y` - Bounding box computed properties
- `workflow_name`, `mode`, `started_at` - ExecutionContext properties

**Reason:** Properties accessed via `.property_name` attribute access, not function calls.

#### E. Test-Only Utilities (~30 functions)
- `reset_event_bus` - Used in tests/conftest.py
- `reset_config_manager` - Used in tests/config/conftest.py
- `reset_schedule_storage` - Test cleanup utility
- `reset_healing_telemetry` - Test reset
- All `reset_*` and `*_instance` methods

**Reason:** Designed for test isolation, correctly excluded from production code paths.

### 2. PUBLIC API / INTERFACE METHODS (KEEP)

Functions that define interfaces, even if not currently called:

#### A. Repository Interface Methods
- `RobotRepository.get_all_online`, `get_by_environment`
- `TriggerRepository.get_by_scenario`, `get_by_type`, `delete_by_scenario`
- `ProjectRepository.get_project_credentials`, `get_global_credentials`

**Reason:** Abstract interface contracts - implementations must provide these.

#### B. Protocol Methods
- `ExecutionContextProtocol.resources`, `has_project_context`, `project_context`
- `PortTypeRegistryProtocol.get_compatible_types`
- `RobotPresenceProtocol.*` methods

**Reason:** Protocol definitions for type checking and interface contracts.

#### C. Entity/Value Object Methods
- `WorkflowSchema.add_connection`, `remove_connection`, `get_node`
- `NodeConnection.source_node`, `target_node`, etc.
- `Port.data_type`, `label`, `required`

**Reason:** Public API of domain objects - may be used by extensions or future features.

### 3. FUTURE FEATURES (KEEP with Review)

Functions for planned but not yet integrated features:

#### A. Advanced Scheduling System (~60 functions)
- `AdvancedScheduler.*` methods
- `BusinessCalendar.*` methods
- `SLAMonitor.*` methods
- `StateAffinityManager.*` methods
- `JobScheduler.pause_all`, `resume_all`

**Analysis:** Complex scheduling infrastructure exists but isn't fully wired into the UI.

**Recommendation:** KEEP - Valuable infrastructure. Wire into UI when ready.

#### B. Workflow Migration System (~15 functions)
- `WorkflowMigrationUseCase.migrate`, `validate_running_jobs`
- `VersionPinManager.*` methods
- `AutoMigrationPolicy.*` methods

**Recommendation:** KEEP - Migration support for version upgrades.

#### C. Template System (~16 functions)
- `TemplateLibraryService.*` methods
- `TemplateStorage.get_builtin`, `import_template`, `export_template`
- `CreateTemplateUseCase.from_workflow`

**Recommendation:** KEEP - Template marketplace/sharing feature.

#### D. Process Mining Analytics (~8 functions)
- `ProcessMiner.record_trace`
- `ProcessModel.get_edge_frequency`, `get_variant_path`
- `ExecutionTrace.*` properties

**Recommendation:** KEEP - Advanced analytics infrastructure.

### 4. ORCHESTRATOR INFRASTRUCTURE (KEEP)

These support distributed robot fleet management:

- `OrchestratorEngine.*` methods (~17 functions)
- `JobDispatcher.*` methods
- `WorkflowDistributor.*` methods
- `JobLifecycleService.*` methods
- `ResultCollector.*` methods

**Reason:** Orchestrator runs as separate service. Functions called via WebSocket/REST protocols.

### 5. DEBUGGING/OBSERVABILITY (KEEP)

Debugging infrastructure:

- `DebugExecutor.*` methods (~6 functions)
- `DebugController.*` methods (~16 functions)
- `BaseNode.set_breakpoint`, `has_breakpoint`, `get_debug_info`
- `Observability.*` methods
- `TelemetryProvider.*` methods

**Reason:** Debug features may not be exposed in UI but are valuable for development.

### 6. POTENTIALLY DEAD CODE (REVIEW/DELETE)

Functions that appear genuinely unused and may be refactoring leftovers:

#### A. Duplicate/Superseded Methods
- `Scenario.file_path` appears twice (lines 93 and 98) - likely copy-paste error
- `WorkflowTemplate.file_path` appears twice (lines 880 and 885)

**Recommendation:** DELETE the duplicate definitions.

#### B. Orphaned Helper Functions
- `replace_match` in variable_resolver.py - Appears to be unused internal helper
- `find_reachable_nodes` in validation/rules.py - Check if validation uses it

**Recommendation:** Review and DELETE if truly orphaned.

#### C. Incomplete Feature Stubs
- `DBOSCloudClient.destroy`, `health_check`, `get_postgres_connection_string`
- `CloudService.dispatch_job`

**Analysis:** DBOS cloud integration appears partially implemented.

**Recommendation:** KEEP if DBOS integration is planned, DELETE if abandoned.

### 7. DEPRECATION CANDIDATES (MARK DEPRECATED)

Functions that may be superseded by newer patterns:

- `schedule_storage.py` functions - Scheduling moved to orchestrator
- `import_workflow_data` in workflow_import.py - May be superseded by use cases

**Recommendation:** Mark with `@deprecated` decorator, remove in future version.

---

## Summary Statistics

| Category | Count (Est.) | Action |
|----------|-------------|--------|
| False Positives (decorators, CLI, routes, properties) | ~200 | KEEP (no action) |
| Interface/Protocol Methods | ~50 | KEEP (contracts) |
| Future Features | ~100 | KEEP (document plans) |
| Orchestrator Infrastructure | ~80 | KEEP (distributed system) |
| Debug/Observability | ~40 | KEEP (dev tools) |
| Duplicate Definitions | ~5 | DELETE |
| Orphaned Helpers | ~10 | REVIEW then DELETE |
| Incomplete Stubs | ~20 | REVIEW (keep or delete) |
| Deprecation Candidates | ~15 | MARK DEPRECATED |
| Node Properties/Methods | ~500+ | KEEP (extensive public API) |
| Remaining (actual unused) | ~700+ | REVIEW case-by-case |

---

## Recommended Cleanup Actions

### Immediate Actions (Low Risk)

1. **Remove duplicate property definitions** (2 files)
   - `Scenario.file_path` - remove duplicate
   - `WorkflowTemplate.file_path` - remove duplicate

2. **Add deprecation warnings** to scheduling functions in `application/scheduling/`
   - These moved to `infrastructure/orchestrator/scheduling/`

### Short-Term Actions (After Review)

3. **Audit orphaned helpers** in:
   - `domain/services/variable_resolver.py`
   - `domain/validation/rules.py`

4. **Decide on DBOS integration**
   - If continuing: document the plan
   - If abandoned: remove `cloud/dbos_cloud.py` stubs

### Documentation Actions

5. **Update inventory script** to recognize:
   - `@decorator` usage patterns
   - `@router.*` FastAPI patterns
   - `@app.command()` Typer patterns
   - Property accessor calls

6. **Add `# Used by: <context>` comments** to legitimate "unused" functions:
   - Test utilities
   - Interface methods
   - Entry points

---

## Technical Notes

The unused function detection likely used AST-based analysis looking for direct function calls. It missed:

1. **Decorator invocations:** `@func` is not recognized as calling `func`
2. **Attribute access:** `obj.property` accessing `@property def property(self)`
3. **Framework dispatch:** FastAPI/Typer registering handlers
4. **Protocol implementations:** Duck-typed interface adherence
5. **External callers:** WebSocket message handlers, test code

A more sophisticated analysis would use:
- Call graph including decorators
- Cross-module import tracking
- Test file analysis
- Framework-aware patterns (FastAPI, Typer, PySide6 signals)
