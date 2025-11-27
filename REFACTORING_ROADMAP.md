# CasareRPA Refactoring Roadmap

**Last Updated**: November 27, 2025
**Status**: Week 3 Complete, Week 4 In Progress
**Version**: v2.1 (migrating to v3.0)

---

## Executive Summary

This document consolidates all refactoring work from Weeks 1-3 and provides a comprehensive roadmap to v3.0. Based on exploration of the current codebase, we have made substantial progress with clean architecture implementation, but significant work remains to complete the migration.

**Key Achievement**: WorkflowRunner refactoring is COMPLETE ✅ (518 lines compatibility wrapper, fully decomposed into domain/application/infrastructure layers)

**Immediate Priority**: Complete MainWindow controller integration (currently only 31% delegation rate)

---

## Completed Work (Weeks 1-3)

### Week 1: Foundation & Visual Nodes ✅ COMPLETE

**Objective**: Fix navigation bottleneck and establish clean architecture foundation

**Achievements**:
1. **Visual Nodes Organization** (95% navigation improvement)
   - Split `visual_nodes.py`: 3,793 lines → 141 nodes across 26 files in 12 categories
   - Category-based directory structure in `presentation/canvas/visual_nodes/`
   - Compatibility layer maintains backward compatibility
   - 6 smoke tests passing

2. **Clean Architecture Scaffolding**
   - Created `domain/`, `application/`, `infrastructure/`, `presentation/` directories
   - Established dependency flow patterns (dependencies point inward)
   - Foundation for Domain-Driven Design (DDD)

3. **GitHub Community Health** (100%)
   - LICENSE (MIT), CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
   - Updated `pyproject.toml` with proper dependencies and version constraints

4. **ExecutionResult Migration - Phase 1**
   - Migrated 32 data operation nodes to ExecutionResult pattern
   - Pattern: `{"success": bool, "data": dict, "error": str, "next_nodes": list}`

**Metrics**:
- Files created: 26
- Navigation improvement: 95%
- Code organization: 12 categories
- Breaking changes: 1 (duplicate node removed)

---

### Week 2: Clean Architecture Migration ✅ COMPLETE

**Objective**: Extract domain entities and implement clean architecture layers

**Achievements**:
1. **Domain Layer Created** (15 files, 3,201 lines)
   - **Entities**: Workflow, WorkflowMetadata, NodeConnection, ExecutionState, Project, Scenario
   - **Value Objects**: DataType, Port, PortDirection, PortType, ExecutionResult, ExecutionStatus
   - **Domain Services**: ExecutionOrchestrator (pure routing logic), ProjectContext (variable resolution)
   - **Zero external dependencies** (pure Python business logic)

2. **Infrastructure Layer Created** (3 files, 673 lines)
   - **BrowserResourceManager**: Playwright browser lifecycle management
   - **ProjectStorage**: File system persistence for projects
   - **Adapters**: External system integrations isolated

3. **Application Layer Created** (1 file, ~558 lines)
   - **ExecuteWorkflowUseCase**: Orchestrates domain + infrastructure
   - Coordinates workflow execution with proper separation of concerns

4. **WorkflowRunner Refactored** ✅ COMPLETE
   - Original: ~1,404 lines monolithic
   - Current: 518 lines (thin compatibility wrapper)
   - Domain: ExecutionOrchestrator (539 lines) + ExecutionState (294 lines) = 833 lines
   - Infrastructure: BrowserResourceManager (194 lines) + ExecutionContext facade (445 lines) = 639 lines
   - Application: ExecuteWorkflowUseCase (558 lines)
   - **All 242 nodes use ExecutionResult pattern** ✅

5. **Compatibility Layers**
   - All `core/` modules converted to re-export wrappers with DeprecationWarning
   - Migration paths documented
   - Timeline: Remove in v3.0

6. **CI/CD Pipeline**
   - GitHub Actions: Test, Lint (Ruff + MyPy), Security (pip-audit)
   - Pre-commit hooks: Basic checks, Ruff formatter
   - PR template created

7. **Test Expansion**
   - Tests: 34 → 269 (7.9x increase)
   - Node coverage: 10% → 30%
   - Categories tested: Control flow, data operations, scripts, system nodes

**Metrics**:
- Domain LOC: 3,201 lines (pure business logic)
- Infrastructure LOC: 673 lines
- Application LOC: 558 lines
- Test increase: 235 new tests
- Node coverage: 30% (71/238 nodes)

---

### Week 3: Component Decomposition ✅ COMPLETE

**Objective**: Extract controllers and components for better modularity

**Achievements**:

1. **Day 1: Controllers Extracted** (7 controllers, 1,974 lines)
   - **BaseController**: Abstract base with lifecycle management (74 lines)
   - **WorkflowController**: File operations (358 lines, 8 signals)
   - **ExecutionController**: Execution control (336 lines, 8 signals)
   - **NodeController**: Node operations (300 lines, 6 signals)
   - **ConnectionController**: Connection management (164 lines, 4 signals)
   - **PanelController**: Panel visibility (206 lines, 5 signals)
   - **MenuController**: Menu/action management (239 lines, 3 signals)
   - **EventBusController**: Event coordination (244 lines)

2. **Day 2: CasareRPAApp Decomposed** (3,112 → 392 lines, 87.4% reduction)
   - **9 Components extracted**: 1,619 lines total
   - WorkflowLifecycleComponent (582 lines)
   - ExecutionComponent (336 lines)
   - NodeRegistryComponent (42 lines)
   - SelectorComponent (48 lines)
   - TriggerComponent (115 lines)
   - ProjectComponent (53 lines)
   - PreferencesComponent (54 lines)
   - DragDropComponent (206 lines)
   - AutosaveComponent (109 lines)
   - **Integration: COMPLETE** ✅

3. **Day 3: UI Components Extracted** (16 components, 5,046 lines)
   - **Base Classes**: BaseWidget, BaseDockWidget, BaseDialog (395 lines)
   - **Panels** (4): Properties, Debug, Variables, Minimap (1,664 lines)
   - **Toolbars** (3): Main, Debug, Zoom (768 lines)
   - **Dialogs** (3): NodeProperties, WorkflowSettings, Preferences (1,299 lines)
   - **Widgets** (3): VariableEditor, OutputConsole, Search (765 lines)
   - Comprehensive README with signal/slot map and usage examples

4. **Coupling Fixes**
   - Removed 34+ direct private member accesses
   - Added 10 accessor methods to MainWindow
   - TYPE_CHECKING guards prevent circular imports
   - All controllers use public API only

5. **EventBus System**
   - **115+ event types** across 10 categories
   - Pub/sub pattern for loose coupling
   - Event history tracking (1000 events)
   - Qt integration via QtSignalBridge
   - Performance metrics and debugging support

**Metrics**:
- Controllers: 7 files, 1,974 lines
- Components: 9 files, 1,619 lines (CasareRPAApp reduced 87.4%)
- UI Components: 16 files, 5,046 lines
- EventBus: 115+ event types
- Coupling: 0 direct private access (down from 34+)

---

## Current State Analysis (Post-Week 3)

### Integration Status

**CasareRPAApp** ✅ COMPLETE
- Status: 100% integrated
- Size: 436 lines (down from 3,112 lines)
- All 9 components properly initialized and working

**MainWindow** ✅ IMPROVED (69% delegation rate)
- Status: Controllers integrated with property-based access
- Size: 1,938 lines (reduced from 2,504 lines - 23% reduction)
- Controllers: 12 controllers initialized (including TriggerController, UIStateController)
- 99/143 methods delegate to controllers (69%)
- Methods: 143 total, avg 11.7 lines/method
- Properties added for all major components (graph, controllers, panels)

**WorkflowRunner** ✅ COMPLETE
- Status: Fully refactored
- Size: 518 lines (compatibility wrapper)
- Domain/Application/Infrastructure split complete
- All nodes use ExecutionResult pattern

### Test Coverage

**Current**: 525 tests, 42/242 nodes tested (17.4%)

**Breakdown**:
- Presentation layer: ~80% coverage ✅
- Controllers: 127 tests ✅
- Components: 42 tests ✅
- UI Widgets: 74 tests ✅
- Event system: 50 tests ✅
- Validation: 130 tests ✅
- **Domain layer: 0% coverage** ❌
- **Application layer: 0% coverage** ❌
- **Node layer: 17.4%** ❌

**Critical Gaps**:
- Desktop automation: 48 nodes, 0% (CRITICAL)
- Browser automation: 18 nodes, 0% (CRITICAL)
- Error handling: 10 nodes, 0%
- HTTP/Database/Email: 30 nodes, 0%
- Remaining nodes: 94 nodes, 0%

### Large Files Requiring Attention

**Critical** (>2000 lines):
1. `visual_nodes.py` - 4,285 lines (DEPRECATED, ready for v3.0 deletion)
2. `desktop/context.py` - 2,540 lines

**Improved** (moved out of critical):
- `main_window.py` - 1,938 lines (down from 2,504 lines - 23% reduction)

**High Priority** (1500-2000 lines):
4. `nodes/file_nodes.py` - 1,834 lines
5. `nodes/http_nodes.py` - 1,822 lines
6. `canvas/graph/node_graph_widget.py` - 1,743 lines
7. `nodes/database_nodes.py` - 1,593 lines

**Medium Priority** (1000-1500 lines):
8-13. Various node files and graph components

---

## Remaining Work - Roadmap to v3.0

### Priority 1: Complete MainWindow Controller Integration (Week 4)
**Status**: IMPROVED - 69% delegation achieved (up from 31%)
**Target**: Reduce MainWindow from 2,504 → 1,000-1,200 lines (50%+ reduction)
**Current**: 1,938 lines (23% reduction achieved)

**Phase 4.1: Extract Remaining Logic to Existing Controllers** (3-5 days)

**To NodeController** (~150 lines):
- `_on_select_nearest_node()` (42 lines)
- `_on_toggle_disable_node()` (67 lines)
- `_on_find_node()` - Node search dialog
- Methods: 3 → NodeController

**To WorkflowController** (~100 lines):
- `_on_paste_workflow()` - Clipboard workflow import
- `_check_validation_before_save()` - Save validation
- `_check_validation_before_run()` - Run validation
- Methods: 3 → WorkflowController

**To PanelController** (~600 lines):
- Panel creation methods (6 methods)
- Panel toggle/visibility methods (8 methods)
- UI state save/restore (4 methods)
- Methods: 18 → PanelController

**Phase 4.2: Create New Controllers** (2-3 days)

**ViewportController** (NEW, ~150 lines):
- `_on_create_frame()` - Frame creation (~40 lines)
- Minimap management (4 methods, ~50 lines)
- Zoom display updates (~30 lines)
- Frame state management (~30 lines)

**SchedulingController** (NEW, ~150 lines):
- `_on_schedule_workflow()` (~40 lines)
- `_on_manage_schedules()` (~50 lines)
- `_on_run_scheduled_workflow()` (~30 lines)
- Schedule state management (~30 lines)

**Phase 4.3: Integration & Testing** (2-3 days)
- Update all method calls to delegate to controllers
- Verify all signals connected properly
- Full regression testing (all 525 tests must pass)
- Manual smoke testing of UI

**Deliverables**:
- MainWindow: 2,504 → ~1,000-1,200 lines
- 2 new controllers: ViewportController, SchedulingController
- ~1,000 lines moved to controllers
- 100% controller delegation for extracted logic
- All tests passing

---

### Priority 2: Test Coverage Expansion (Weeks 4-5)
**Status**: CRITICAL - Only 17.4% node coverage
**Target**: 60% coverage (145/242 nodes tested)
**Long-term**: 100% coverage by v3.0

**Phase 4.4: Desktop Automation Tests** (Week 4, 5 days)
- **48 nodes to test** (HIGHEST PRIORITY - core RPA feature)
- Create 8 test files:
  ```
  tests/nodes/desktop/
  ├── test_application_nodes.py (4 nodes, ~15 tests)
  ├── test_element_nodes.py (5 nodes, ~20 tests)
  ├── test_interaction_nodes.py (6 nodes, ~20 tests)
  ├── test_mouse_keyboard_nodes.py (6 nodes, ~20 tests)
  ├── test_office_nodes.py (12 nodes, ~40 tests)
  ├── test_screenshot_ocr_nodes.py (4 nodes, ~15 tests)
  ├── test_wait_verification_nodes.py (4 nodes, ~15 tests)
  └── test_window_nodes.py (7 nodes, ~25 tests)
  ```
- Total: ~170 tests
- Use mocking for UI automation (avoid real desktop interactions)
- Test ExecutionResult pattern compliance

**Phase 5.1: Browser Automation Tests** (Week 5, 2 days)
- **18 nodes to test** (web RPA critical path)
- Create 5 test files:
  ```
  tests/nodes/browser/
  ├── test_browser_nodes.py (5 nodes, ~15 tests)
  ├── test_navigation_nodes.py (4 nodes, ~12 tests)
  ├── test_interaction_nodes.py (3 nodes, ~10 tests)
  ├── test_data_extraction_nodes.py (3 nodes, ~10 tests)
  └── test_wait_nodes.py (3 nodes, ~10 tests)
  ```
- Total: ~57 tests
- Use Playwright test fixtures
- Test both mock and real browser scenarios

**Phase 5.2: Critical Nodes Tests** (Week 5, 3 days)
- **40 nodes to test** (error handling, HTTP, database, email)
- Create test files:
  ```
  tests/nodes/
  ├── test_error_handling_nodes.py (10 nodes, ~35 tests)
  ├── test_http_nodes.py (12 nodes, ~40 tests)
  ├── test_database_nodes.py (10 nodes, ~35 tests)
  └── test_email_nodes.py (8 nodes, ~30 tests)
  ```
- Total: ~140 tests
- Mock external services (HTTP servers, databases, SMTP)

**Phase 5.3: Remaining Core Nodes** (Week 6, 3 days)
- **39 nodes to test**
- Create test files:
  ```
  tests/nodes/
  ├── test_basic_nodes.py (3 nodes, ~10 tests)
  ├── test_datetime_nodes.py (7 nodes, ~25 tests)
  ├── test_text_nodes.py (14 nodes, ~45 tests)
  ├── test_random_nodes.py (5 nodes, ~15 tests)
  ├── test_xml_nodes.py (8 nodes, ~25 tests)
  ├── test_pdf_nodes.py (6 nodes, ~20 tests)
  ├── test_ftp_nodes.py (10 nodes, ~35 tests)
  └── test_utility_nodes.py (4 nodes, ~12 tests)
  ```
- Total: ~187 tests

**Testing Deliverables** (Weeks 4-6):
- Desktop: 48 nodes, ~170 tests
- Browser: 18 nodes, ~57 tests
- Critical: 40 nodes, ~140 tests
- Remaining: 39 nodes, ~187 tests
- **Total: 145 nodes tested, ~554 new tests**
- **Coverage: 17.4% → 60% (3.4x increase)**

---

### Priority 3: Domain & Application Layer Tests (Week 6)
**Status**: CRITICAL - 0% coverage on core business logic
**Target**: 100% domain/application coverage

**Phase 6.1: Domain Entity Tests** (2 days)
```
tests/domain/entities/
├── test_workflow.py (~30 tests)
├── test_project.py (~25 tests)
├── test_execution_state.py (~30 tests)
└── test_node_connection.py (~15 tests)
```
Total: ~100 tests

**Phase 6.2: Domain Services Tests** (2 days)
```
tests/domain/services/
├── test_execution_orchestrator.py (~40 tests)
└── test_project_context.py (~30 tests)
```
Total: ~70 tests

**Phase 6.3: Application Layer Tests** (1 day)
```
tests/application/use_cases/
└── test_execute_workflow.py (~30 tests)
```
Total: ~30 tests

**Deliverables**:
- Domain layer: ~200 tests, 100% coverage
- Application layer: ~30 tests, 100% coverage

---

### Priority 4: Performance Optimization (Week 7)
**Status**: LOW PRIORITY - Focus on "quick wins"
**Target**: Ensure refactored architecture has minimal overhead

**Phase 7.1: Performance Baseline** (1 day)
- Measure startup time (current: ? seconds)
- Measure workflow execution time (100-node workflow)
- Memory profiling (long-running Canvas session)
- EventBus overhead measurement

**Phase 7.2: Quick Win Optimizations** (2-3 days)
1. **EventBus optimization**
   - Lazy subscription (subscribe only when needed)
   - Event batching for high-frequency events
   - Filtered subscription optimization

2. **Component initialization**
   - Lazy load non-critical components
   - Parallel initialization where possible
   - Deferred UI panel creation

3. **Import optimization**
   - Remove unused imports
   - Lazy imports for heavy modules

4. **Caching**
   - Node registry caching
   - Icon/resource caching
   - Workflow validation result caching

**Deliverables**:
- Performance benchmark suite
- 20%+ improvement in startup time
- 10%+ improvement in execution time
- Memory usage stable (<500 MB for typical session)

---

## v3.0 End Goal & Vision

### Target Architecture (v3.0)

**Clean Architecture Layers** (Fully Realized):
```
presentation/
├── canvas/
│   ├── main_window.py (~800 lines, pure UI coordination)
│   ├── controllers/ (9 controllers, ~2,500 lines)
│   ├── components/ (9 components, ~1,600 lines)
│   ├── ui/ (16 UI components, ~5,000 lines)
│   ├── visual_nodes/ (141 nodes, organized by category)
│   └── graph/ (NodeGraphWidget, optimized)

application/
├── use_cases/
│   ├── execute_workflow.py
│   ├── validate_workflow.py
│   ├── save_workflow.py
│   └── load_workflow.py

domain/
├── entities/ (Workflow, Node, Project - pure logic)
├── services/ (ExecutionOrchestrator, ProjectContext)
├── value_objects/ (Port, DataType, ExecutionResult)
└── repositories/ (interfaces only)

infrastructure/
├── resources/ (BrowserResourceManager, DesktopResourceManager)
├── persistence/ (ProjectStorage, WorkflowStorage)
└── adapters/ (Playwright, UIAutomation wrappers)
```

**Key Metrics (v3.0)**:
- Average file size: <800 lines
- Test coverage: 100%
- No files >1500 lines
- All compatibility layers removed
- Zero deprecation warnings
- Clean import paths (no core.* imports)

### Breaking Changes in v3.0

**Removals**:
1. `core/` compatibility layer → Use `domain/` directly
2. `visual_nodes.py` (4,285 lines) → Use `presentation/canvas/visual_nodes/`
3. Old `ExecutionContext` pattern → Use `ExecuteWorkflowUseCase`
4. Direct `NodeStatus` imports → Use `domain.value_objects.types`

**Import Migrations**:
```python
# v2.x (deprecated)
from casare_rpa.core.types import NodeStatus
from casare_rpa.core.workflow_schema import WorkflowSchema
from casare_rpa.core import Port

# v3.0 (required)
from casare_rpa.domain.value_objects.types import NodeStatus
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.value_objects import Port
```

**Migration Tools**:
- Automated import rewriter script
- Deprecation warning scanner
- Test suite for v3.0 compatibility

### Quality Gates for v3.0

**Must Pass**:
- ✅ 100% test coverage (all 242 nodes + domain + application)
- ✅ All 1,400+ tests passing
- ✅ Performance benchmarks met
- ✅ Zero critical bugs
- ✅ All deprecation warnings removed
- ✅ Documentation complete (API, architecture, migration guides)
- ✅ All files <1500 lines
- ✅ Clean architecture principles validated

---

## EventBus System

**Status**: Production-ready in Presentation layer (v2.1)

**Purpose**: Unified event-driven architecture for Canvas UI components. Replaces scattered Qt signal/slot connections with centralized event routing for loose coupling.

### Architecture

```
Components (Controllers, Views, Panels)
    ↓ Subscribe / Publish ↓
EventBus (Singleton)
    - Event routing
    - Subscription management
    - Event history (1000 events)
    - Performance metrics
    ↓ Bidirectional ↓
QtSignalBridge
    - Qt signal emission
    - EventBus ↔ Qt signals
```

### Core Components

**Location**: `src/casare_rpa/presentation/canvas/events/`

1. **EventType (Enum)** - 115+ event types across 10 categories
2. **Event (Dataclass)** - Immutable event with type, source, data, timestamp, priority
3. **EventBus (Singleton)** - Central routing with subscribe/publish/history/metrics
4. **EventHandler (Base Class)** - Auto subscription management, cleanup
5. **QtSignalBridge** - Bidirectional EventBus ↔ Qt signals

### Event Categories (115+ total)

1. **Workflow (20+)**: NEW, OPENED, SAVED, CLOSED, MODIFIED, VALIDATED, IMPORTED, EXPORTED
2. **Node (20+)**: ADDED, REMOVED, SELECTED, PROPERTY_CHANGED, DISABLED, BREAKPOINT_ADDED
3. **Connection (10+)**: ADDED, REMOVED, VALIDATED, PORT_CONNECTED, PORT_DISCONNECTED
4. **Execution (15+)**: STARTED, PAUSED, RESUMED, STOPPED, COMPLETED, FAILED, NODE_EXECUTION_*
5. **UI (15+)**: PANEL_TOGGLED, ZOOM_CHANGED, THEME_CHANGED, MINIMAP_TOGGLED
6. **System (10+)**: ERROR_OCCURRED, LOG_MESSAGE, AUTOSAVE_*, MEMORY_WARNING
7. **Project (10+)**: PROJECT_CREATED/OPENED/CLOSED, SCENARIO_CREATED/OPENED
8. **Variable (5+)**: VARIABLE_SET, VARIABLE_UPDATED, VARIABLE_DELETED
9. **Debug (5+)**: DEBUG_MODE_ENABLED, BREAKPOINT_HIT, VARIABLE_INSPECTOR_UPDATED
10. **Trigger (5+)**: TRIGGER_CREATED/UPDATED/DELETED, TRIGGER_FIRED

### Key Features

- **Loose Coupling**: Components communicate through events without direct dependencies
- **Type Safety**: Full type hints and compile-time event type checking
- **Debuggability**: Event history tracking and performance metrics
- **Qt Compatibility**: Seamless integration with existing Qt signal/slot code
- **Thread Safety**: Safe concurrent event publishing and subscription
- **Testability**: Easy to mock and test event-driven logic

### Usage Examples

**Basic Subscription and Publishing**:
```python
from casare_rpa.presentation.canvas.events import EventBus, Event, EventType

bus = EventBus()

# Subscribe
def on_workflow_saved(event: Event) -> None:
    print(f"Workflow saved: {event.data['file_path']}")

bus.subscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)

# Publish
event = Event(
    type=EventType.WORKFLOW_SAVED,
    source="WorkflowController",
    data={"file_path": "/path/to/workflow.json"}
)
bus.publish(event)
```

**Using EventHandler Base Class**:
```python
from casare_rpa.presentation.canvas.events import EventHandler, Event, EventType, event_handler

class MyController(EventHandler):
    def __init__(self):
        super().__init__()
        self._auto_subscribe_decorated_handlers()

    @event_handler(EventType.WORKFLOW_NEW)
    def on_workflow_new(self, event: Event) -> None:
        print(f"New workflow: {event.data['name']}")

    def save_workflow(self, path: Path) -> None:
        # ... save logic ...
        self.publish(Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        ))
```

**Qt Integration**:
```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import QtEventSubscriber, EventType

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.subscriber = QtEventSubscriber(self)
        self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
        self.subscriber.event_received.connect(self.on_event)

    def on_event(self, event: Event) -> None:
        if event.type == EventType.WORKFLOW_SAVED:
            self.statusBar().showMessage(f"Saved: {event.data['file_path']}")
```

### Performance Metrics

EventBus tracks:
- Events published/handled count
- Total/average handler execution time
- Error count
- Subscriber counts

```python
metrics = bus.get_metrics()
print(f"Events published: {metrics['events_published']}")
print(f"Avg handler time: {metrics['avg_handler_time']:.4f}s")
```

### Best Practices

1. **Handler Performance**: Keep handlers fast (< 100ms), offload heavy work to background threads
2. **Event Frequency**: Debounce high-frequency events, batch related events
3. **Memory Management**: Always call `cleanup()` when destroying components
4. **Debugging**: Use event history for debugging (`bus.get_history(limit=10)`)

### Migration from Qt Signals

**Before (Qt Signals)**:
```python
class WorkflowController(QObject):
    workflow_saved = Signal(str)  # file_path

    def save_workflow(self, path: Path):
        self.workflow_saved.emit(str(path))
```

**After (EventBus)**:
```python
class WorkflowController(EventHandler):
    def save_workflow(self, path: Path):
        self.publish(Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        ))
```

### Future Enhancements

- Event replay for debugging
- Remote events (Robot/Orchestrator sync)
- Event validation and schema checking
- Performance profiling and middleware

---

## Success Metrics

### Week 4 Targets
- ✅ MainWindow: 2,504 → 1,000-1,200 lines (50% reduction)
- ✅ 2 new controllers created
- ✅ 100% delegation for extracted logic
- ✅ Desktop tests: 15 nodes tested (~60 tests)

### Weeks 5-6 Targets
- ✅ Node coverage: 17% → 60% (145/242 nodes)
- ✅ Domain layer: 100% coverage
- ✅ Application layer: 100% coverage
- ✅ Total tests: 525 → 1,200+

### Week 7 Targets
- ✅ Performance: 20%+ startup improvement
- ✅ Integration tests: Complete
- ✅ All 1,200+ tests passing

### v3.0 Targets (TBD)
- ✅ Test coverage: 100%
- ✅ All files <1500 lines
- ✅ Compatibility layers removed
- ✅ Zero deprecation warnings
- ✅ Documentation complete

---

**Last Updated**: November 27, 2025
**Next Update**: End of Week 4
