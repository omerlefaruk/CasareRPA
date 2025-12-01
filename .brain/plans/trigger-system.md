# Trigger System Implementation Plan

## Status: PLANNING

## Brain Context
- Read: .brain/activeContext.md (current session state)
- Patterns: .brain/systemPatterns.md (architecture patterns & registry pattern)
- Rules: .brain/projectRules.md (coding standards)
- Reference: CLAUDE.md (project structure, TDD workflow)

## Overview

Trigger system enables CasareRPA workflows to be initiated by external or internal events. Current implementation is partially complete with base classes, registry, and several trigger implementations. This plan completes the trigger system by:

1. **Consolidating Domain Layer**: Define TriggerEvent, TriggerStatus, trigger lifecycle state machine
2. **Completing Infrastructure**: TriggerManager for lifecycle + event routing, HTTP webhook server, persistence adapters
3. **Integration with Orchestrator**: Route trigger events to job creation in Orchestrator API
4. **Canvas UI Integration**: Trigger management UI in presentation layer
5. **Testing & Documentation**: Full test coverage across domain/infra/application/presentation layers

**Key Responsibilities:**
1. Event Emission: Triggers detect events (scheduled, webhook, file watch, form submission, etc.)
2. Event Routing: TriggerManager routes TriggerEvents to job creation callback
3. Lifecycle Management: Start/stop/pause triggers, state persistence
4. HTTP Server: Webhook triggers require embedded HTTP server for receiving events
5. Configuration Management: Store trigger configs in database, reload on startup
6. Error Handling: Handle trigger failures, log events, retry logic

**Trigger Types Implemented:**
- MANUAL: Manual workflow execution
- SCHEDULED: Cron-based scheduling (via APScheduler)
- WEBHOOK: HTTP endpoint that accepts events
- FILE_WATCH: Monitor file system for changes
- EMAIL: Trigger from email receipt
- APP_EVENT: Trigger from Canvas application events
- FORM: Web form submission
- CHAT: Chat message received
- ERROR: Error in another workflow
- WORKFLOW_CALL: Call from another workflow

## Agents Assigned
- [ ] **Explore**: Analyze existing trigger implementations, test patterns, Canvas controller patterns
- [ ] **rpa-engine-architect**: Trigger lifecycle state machine, TriggerManager completion, event routing
- [ ] **chaos-qa-engineer**: Edge cases (rapid trigger fires, failed event callbacks, concurrent triggers)

## Architecture Context

### Current State
Trigger system exists at `src/casare_rpa/triggers/`:
- `base.py`: TriggerType enum, TriggerStatus enum, TriggerEvent dataclass, BaseTrigger ABC
- `registry.py`: TriggerRegistry singleton with register/get/create_instance methods
- `manager.py`: TriggerManager (partially complete) for lifecycle + event routing
- `implementations/`: Directory with trigger implementations (email, webhook, form, chat, error, scheduled, file_watch)

Canvas integration at `src/casare_rpa/presentation/canvas/`:
- `controllers/trigger_controller.py`: Manages trigger lifecycle from UI
- `ui/dialogs/trigger_config_dialog.py`: Configure triggers
- `ui/dialogs/trigger_type_selector.py`: Select trigger type
- `ui/panels/triggers_tab.py`: Trigger management panel

Application layer:
- `src/casare_rpa/application/execution/trigger_runner.py`: CanvasTriggerRunner manages Canvas triggers

### Design Principles
- **Clean Architecture**: Domain (trigger logic) ← Infrastructure (persistence, HTTP) ← Application (use cases) → Presentation (Canvas UI)
- **Registry Pattern**: TriggerRegistry (singleton) allows dynamic trigger discovery and instantiation
- **Event-Driven**: TriggerEvents decoupled from workflow execution via callback pattern
- **Async-First**: All I/O operations async (HTTP, file watch, scheduler)
- **Testability**: Mock all external APIs (file system, HTTP server, APScheduler)

### Existing Patterns
- **Registry Pattern**: TriggerRegistry.register() decorator + create_instance()
- **Event Callback**: `JobCreatorCallback = Callable[[TriggerEvent], Any]` - callback invoked on trigger fire
- **Base Class**: BaseTrigger ABC with start/stop lifecycle methods
- **Configuration**: BaseTriggerConfig dataclass with trigger metadata

## Implementation Steps

### Phase 1: Domain Layer (Trigger Logic)
- [ ] Review/complete TriggerEvent dataclass (payload, metadata handling)
- [ ] Document TriggerStatus lifecycle (INACTIVE → STARTING → ACTIVE → PAUSED → STOPPING → ERROR)
- [ ] Add trigger error types (BadConfiguration, EventCaptureError, CallbackError, etc.)
- [ ] Create TriggerValidator service (validate configs before instantiation)
  - Check required fields per trigger type
  - Validate cron expressions for scheduled triggers
  - Validate file patterns for file_watch triggers

### Phase 2: Infrastructure Layer (Adapters)
- [ ] **TriggerPersistence adapter** - Store/load trigger configs from database
  - Interface: ITriggerRepository (save, get_by_id, list, delete, list_by_workflow)
  - Implementation: DatabaseTriggerRepository (use SQLAlchemy/asyncpg)
- [ ] **Trigger HTTP Server** - Webhook trigger support
  - Embedded FastAPI server (already in deps as part of orchestrator)
  - Routes: POST /webhooks/{trigger_id}, GET /webhooks/status
  - Security: Webhook key validation (HMAC if specified)
- [ ] **File Watch adapter** - Monitor file system for changes
  - Use watchdog library (add to dependencies if missing)
  - Async file monitoring with debouncing
- [ ] **APScheduler integration** - Scheduled trigger support
  - AsyncIOScheduler for async job execution
  - Persistent job store (memory for now, DB optional)

### Phase 3: Application Layer (Use Cases)
- [ ] **CreateTriggerUseCase** - Create new trigger
  - Validate config via TriggerValidator
  - Save to persistence
  - Don't auto-start (Canvas explicitly calls StartTriggerUseCase)
- [ ] **StartTriggerUseCase** - Start a trigger
  - Load config from persistence
  - Create trigger instance via registry
  - Call trigger.start()
  - Track started triggers (in memory map)
- [ ] **StopTriggerUseCase** - Stop a trigger
  - Call trigger.stop()
  - Remove from tracking
  - Cleanup resources (close files, cancel scheduled jobs)
- [ ] **PauseTriggerUseCase** - Pause a trigger (suspend events, keep state)
  - Set TriggerStatus to PAUSED
  - For APScheduler triggers, suspend job
- [ ] **ResumeTriggerUseCase** - Resume paused trigger
  - Set TriggerStatus to ACTIVE
  - Resume job if APScheduler
- [ ] **DeleteTriggerUseCase** - Delete trigger configuration
  - Check if running, stop first
  - Delete from persistence

### Phase 4: TriggerManager Completion
- [ ] Implement trigger lifecycle methods (start_trigger, stop_trigger, pause_trigger, resume_trigger)
- [ ] Implement configuration management (register_trigger, get_trigger, list_triggers, delete_trigger)
- [ ] Implement HTTP server startup/shutdown (for webhook triggers)
- [ ] Implement trigger event callback routing
- [ ] Error handling & recovery (if trigger crashes, mark as ERROR status)
- [ ] Add metrics tracking (trigger fires, successes, failures, latency)

### Phase 5: Canvas Integration
- [ ] **Trigger Controller** - Orchestrate use cases from UI
  - create_trigger() → CreateTriggerUseCase
  - start_trigger() → StartTriggerUseCase
  - stop_trigger() → StopTriggerUseCase
  - pause_trigger() → PauseTriggerUseCase
  - resume_trigger() → ResumeTriggerUseCase
- [ ] **TriggerManager Instantiation** - Create and initialize TriggerManager in MainWindow
  - Connect job callback to OrchestratorEngine.submit_job()
  - Start/stop with Canvas application lifecycle
- [ ] **UI State Synchronization** - Update trigger list/status in real-time
  - EventBus to notify UI of trigger state changes
  - Trigger tab updates when trigger status changes

### Phase 6: Orchestrator API Integration
- [ ] Add trigger endpoints to Orchestrator API
  - POST /api/triggers - Create
  - GET /api/triggers/{id} - Get
  - GET /api/triggers - List
  - PUT /api/triggers/{id} - Update
  - DELETE /api/triggers/{id} - Delete
  - POST /api/triggers/{id}/start - Start
  - POST /api/triggers/{id}/stop - Stop
- [ ] Add trigger execution results endpoint
  - POST /api/trigger-executions - Log trigger events
  - GET /api/trigger-executions - Query history

### Phase 7: Testing & Documentation
- [ ] **Unit Tests (Domain)**
  - TriggerValidator: Valid/invalid configs per type
  - TriggerEvent: Serialization/deserialization
  - TriggerStatus transitions
- [ ] **Integration Tests (Infrastructure)**
  - TriggerPersistence: CRUD operations
  - HTTP server: Webhook request handling
  - File watch: File change detection
  - APScheduler: Job scheduling & execution
- [ ] **Application Tests**
  - Use cases: Mock persistence, verify behavior
  - Event routing: Mock callback, verify TriggerEvent passed correctly
- [ ] **Presentation Tests (Minimal)**
  - Trigger controller: Integration with use cases
  - Trigger tab: UI updates on state change
- [ ] **E2E Tests**
  - Full trigger lifecycle: Create → Start → Fire → Job created → Stop
  - Error scenarios: Failed event callback, trigger crash
- [ ] **Documentation**
  - Trigger implementation guide for developers
  - API reference for trigger endpoints
  - User guide for Canvas trigger management

## Files to Modify/Create

| File | Action | Description | Owner Agent |
|------|--------|-------------|-------------|
| `src/casare_rpa/domain/services/trigger_validator.py` | CREATE | Validate trigger configs per type | rpa-engine-architect |
| `src/casare_rpa/domain/exceptions/trigger_errors.py` | CREATE | Trigger-specific exceptions | rpa-engine-architect |
| `src/casare_rpa/infrastructure/persistence/repositories/trigger_repository.py` | CREATE | Store/load trigger configs (DB) | rpa-engine-architect |
| `src/casare_rpa/infrastructure/adapters/trigger_http_server.py` | CREATE | FastAPI server for webhooks | rpa-engine-architect |
| `src/casare_rpa/infrastructure/adapters/file_watch_adapter.py` | CREATE | Watchdog-based file monitoring | rpa-engine-architect |
| `src/casare_rpa/application/use_cases/create_trigger_use_case.py` | CREATE | Create trigger workflow | rpa-engine-architect |
| `src/casare_rpa/application/use_cases/start_trigger_use_case.py` | CREATE | Start trigger workflow | rpa-engine-architect |
| `src/casare_rpa/application/use_cases/stop_trigger_use_case.py` | CREATE | Stop trigger workflow | rpa-engine-architect |
| `src/casare_rpa/application/use_cases/pause_trigger_use_case.py` | CREATE | Pause trigger workflow | rpa-engine-architect |
| `src/casare_rpa/triggers/base.py` | MODIFY | Complete BaseTrigger interface, add status/error tracking | rpa-engine-architect |
| `src/casare_rpa/triggers/manager.py` | MODIFY | Complete TriggerManager implementation | rpa-engine-architect |
| `src/casare_rpa/presentation/canvas/controllers/trigger_controller.py` | MODIFY | Wire use cases to UI | rpa-engine-architect |
| `src/casare_rpa/presentation/canvas/app.py` | MODIFY | Initialize TriggerManager on startup | rpa-engine-architect |
| `src/casare_rpa/infrastructure/orchestrator/api/routers/triggers.py` | CREATE/MODIFY | Trigger API endpoints | rpa-engine-architect |
| `tests/domain/services/test_trigger_validator.py` | CREATE | Validator tests (SUCCESS, ERROR, EDGE_CASES) | chaos-qa-engineer |
| `tests/infrastructure/test_trigger_persistence.py` | CREATE | Persistence layer tests (CRUD) | chaos-qa-engineer |
| `tests/infrastructure/test_trigger_http_server.py` | CREATE | HTTP server tests (webhook requests) | chaos-qa-engineer |
| `tests/application/test_trigger_use_cases.py` | CREATE | Use case tests (with mocked persistence) | chaos-qa-engineer |
| `tests/presentation/test_trigger_controller.py` | CREATE | Controller integration tests (minimal) | chaos-qa-engineer |
| `tests/integration/test_trigger_lifecycle.py` | CREATE | Full trigger lifecycle E2E tests | chaos-qa-engineer |
| `docs/triggers.md` | CREATE | Trigger system user guide | rpa-docs-writer |
| `docs/api/triggers.md` | CREATE | Trigger API reference | rpa-docs-writer |

## Progress Log

- [2025-11-30] Plan created. Waiting for agent assignments & execution approval.
- TODO: Explore phase - Analyze existing code, test patterns
- TODO: Phase 1 (Domain) - TriggerValidator, error types
- TODO: Phase 2 (Infrastructure) - Persistence, HTTP server, file watch
- TODO: Phase 3 (Application) - Use cases
- TODO: Phase 4 (TriggerManager) - Complete lifecycle methods
- TODO: Phase 5 (Canvas) - UI integration
- TODO: Phase 6 (Orchestrator API) - API endpoints
- TODO: Phase 7 (Testing & Docs) - Full coverage

## Open Questions

1. **Persistence Storage**: Should trigger configs be stored in Orchestrator database or local file-based JSON in Canvas?
   - Affects: Phase 2 implementation, API endpoints
   - Owner: Architecture review

2. **Job Creation Callback**: Current signature is `Callable[[TriggerEvent], Any]`. Should callback return job_id? Should it handle failures?
   - Affects: TriggerManager implementation, error handling
   - Owner: Application design

3. **Trigger Deduplication**: If webhook receives duplicate requests (network retry), how to prevent duplicate job creation?
   - Options: Idempotency keys, event deduplication with TTL, request fingerprinting
   - Affects: Infrastructure design
   - Owner: Requirements clarification

4. **Concurrent Trigger Fires**: Can same trigger fire multiple times concurrently? Should events queue or drop?
   - Affects: TriggerManager event handling
   - Owner: Product requirements

5. **Trigger Error Recovery**: If trigger crashes (e.g., file watch exception), auto-restart or require manual intervention?
   - Affects: Error handling, state tracking
   - Owner: Operational requirements

6. **Webhook Security**: How to validate webhook requests? Secret keys? HMAC signature verification?
   - Affects: HTTP server implementation
   - Owner: Security requirements

7. **Rate Limiting**: Should triggers have rate limiting (max N events per minute)?
   - Affects: TriggerManager, use cases
   - Owner: Product requirements

8. **Backward Compatibility**: Old workflow files with v2 trigger format - auto-migration or deprecation warning?
   - Affects: Canvas loader, file format handling
   - Owner: Migration strategy

## Post-Completion Checklist

- [ ] All tests passing (pytest tests/ -v)
- [ ] Coverage targets met:
  - Domain: 90%+ (TriggerValidator, TriggerEvent, status transitions)
  - Infrastructure: 70%+ (persistence, HTTP server, file watch)
  - Application: 85%+ (use cases with mocked infra)
  - Presentation: 50%+ (minimal, controller integration)
- [ ] Code review passed (architecture patterns verified, clean code)
- [ ] Update .brain/activeContext.md with completion status
- [ ] Update .brain/systemPatterns.md if new patterns discovered
- [ ] Documentation complete:
  - User guide (Canvas trigger management)
  - API reference (trigger endpoints)
  - Implementation guide for developers
- [ ] Manual testing:
  - Trigger lifecycle in Canvas (create, start, fire, stop)
  - Webhook trigger accepts POST requests
  - Scheduled trigger fires on schedule
  - Job creation callback invoked with correct TriggerEvent
  - Error scenarios handled gracefully (invalid config, failed callback)
- [ ] Orchestrator API fully functional:
  - All trigger endpoints working
  - Persistence integration complete
  - Execution history logged
