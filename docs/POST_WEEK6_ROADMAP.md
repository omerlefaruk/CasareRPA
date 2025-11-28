# Post-Week 6 Roadmap: Performance, Refactoring, and v3.0 Preparation

**Status**: Week 6 in progress (60% → 100% node coverage)
**Last Updated**: November 28, 2025
**Estimated Timeline**: 3-4 weeks
**Current Version**: v2.1 → Target: v3.0

---

## Quick Reference

- **Week 7-8**: Performance optimization (baseline + quick wins)
- **Ongoing**: Large file decomposition (8 files >1500 lines)
- **v3.0 Prep**: Compatibility layer removal, breaking changes
- **Final**: Quality gates and release criteria

---

## Week 7-8: Performance Optimization (5-7 days)

**Status**: Not started
**Priority**: Medium (post-Week 6)
**Target**: 20%+ startup improvement, 10%+ execution improvement

### Phase 7.1: Performance Baseline Measurement (1 day)

Establish performance metrics before optimization:

- [ ] **Startup time measurement**
  - Measure application launch time (cold start)
  - Measure MainWindow initialization time
  - Measure component/controller setup time
  - Current baseline: ? seconds (TBD)

- [ ] **Workflow execution time**
  - Create 100-node benchmark workflow
  - Measure end-to-end execution time
  - Measure per-node execution overhead
  - Current baseline: ? seconds (TBD)

- [ ] **Memory profiling**
  - Profile long-running Canvas session (1 hour)
  - Measure memory usage at startup, 30 min, 60 min
  - Identify memory leaks (if any)
  - Current baseline: ? MB (TBD)

- [ ] **EventBus overhead**
  - Measure event publish/subscribe latency
  - Profile handler execution time
  - Analyze high-frequency events
  - Current metrics available via `bus.get_metrics()`

**Deliverable**: Performance baseline report with all metrics

---

### Phase 7.2: Quick Win Optimizations (3-5 days)

Focus on low-effort, high-impact improvements:

#### 1. EventBus Optimization

- [ ] **Lazy subscription**
  - Subscribe only when component is visible/active
  - Unsubscribe when component is destroyed
  - Reduce idle subscription count

- [ ] **Event batching**
  - Batch high-frequency events (VARIABLE_UPDATED, NODE_PROPERTY_CHANGED)
  - Debounce UI update events (e.g., 16ms for 60fps)
  - Reduce event publish overhead

- [ ] **Filtered subscription optimization**
  - Cache filtered subscribers
  - Optimize event routing logic
  - Reduce unnecessary handler calls

**Target**: 10-20% reduction in EventBus overhead

#### 2. Component Initialization Optimization

- [ ] **Lazy load non-critical components**
  - Defer OutputConsole creation until first use
  - Defer panel creation until visibility toggle
  - Reduce MainWindow startup time

- [ ] **Parallel initialization**
  - Initialize independent controllers concurrently
  - Use asyncio.gather() for async components
  - Reduce sequential initialization bottlenecks

- [ ] **Deferred UI panel creation**
  - Create dock widgets on-demand
  - Reduce initial widget tree size
  - Improve startup responsiveness

**Target**: 20%+ reduction in startup time

#### 3. Import Optimization

- [ ] **Remove unused imports**
  - Audit all modules for unused imports
  - Remove dead code and orphaned dependencies
  - Reduce module load time

- [ ] **Lazy imports for heavy modules**
  - Defer Playwright import until first browser node
  - Defer UIAutomation import until first desktop node
  - Use `if TYPE_CHECKING:` for type-only imports

- [ ] **Import profiling**
  - Use `python -X importtime` to profile imports
  - Identify slowest imports
  - Optimize import order

**Target**: 10-15% reduction in startup time

#### 4. Caching

- [ ] **Node registry caching**
  - Cache node class lookups
  - Cache node metadata (category, display name)
  - Reduce repeated registry queries

- [ ] **Icon/resource caching**
  - Cache QIcon instances
  - Cache pixmaps and SVG renderers
  - Reduce file I/O overhead

- [ ] **Workflow validation caching**
  - Cache validation results for unchanged workflows
  - Invalidate cache on workflow modification
  - Reduce repeated validation overhead

**Target**: 5-10% improvement in workflow operations

---

### Deliverables

- [ ] Performance benchmark suite (automated)
- [ ] 20%+ improvement in startup time (baseline → optimized)
- [ ] 10%+ improvement in execution time (100-node workflow)
- [ ] Memory usage stable (<500 MB for typical 1-hour session)
- [ ] Performance report with before/after metrics

---

## Large File Refactoring (Ongoing)

**Status**: In progress (MainWindow reduced 23%)
**Priority**: High (code maintainability)
**Target**: All files <1500 lines

### Critical Files (>2000 lines)

| File | Current Size | Target Size | Approach | Status |
|------|-------------|-------------|----------|--------|
| `desktop/context.py` | 2,540 lines | <1000 lines | Extract desktop automation controllers | ⏳ Pending |
| `visual_nodes.py` | 4,285 lines | **DELETE** | Deprecated, remove in v3.0 | ✅ Ready for deletion |

**Actions**:
- [ ] **desktop/context.py refactoring**
  - Extract DesktopApplicationController (app management)
  - Extract DesktopElementController (element operations)
  - Extract DesktopInteractionController (mouse/keyboard)
  - Extract DesktopWindowController (window management)
  - Reduce to thin coordination layer (<1000 lines)

- [x] **visual_nodes.py deletion**
  - Already deprecated with compatibility layer
  - All imports migrated to category-based structure
  - Schedule for v3.0 removal

---

### High Priority Files (1500-2000 lines)

| File | Current Size | Target Size | Approach | Status |
|------|-------------|-------------|----------|--------|
| `nodes/file_nodes.py` | 1,834 lines | <1200 lines | Split into file_operations + structured_data | ⏳ Pending |
| `nodes/http_nodes.py` | 1,822 lines | <1200 lines | Split into http_basic + http_advanced + auth | ⏳ Pending |
| `canvas/graph/node_graph_widget.py` | 1,743 lines | <1200 lines | Extract graph interaction controllers | ⏳ Pending |
| `nodes/database_nodes.py` | 1,593 lines | <1200 lines | Split by database type (SQL vs NoSQL) | ⏳ Pending |

**Actions**:
- [ ] **file_nodes.py split**
  - Create `file_operations.py` (Read, Write, Copy, Move, Delete - ~800 lines)
  - Create `structured_data.py` (CSV, JSON, XML, ZIP - ~800 lines)
  - Update imports and tests

- [ ] **http_nodes.py split**
  - Create `http_basic.py` (GET, POST, PUT, DELETE - ~600 lines)
  - Create `http_advanced.py` (Auth, Headers, Sessions - ~600 lines)
  - Create `http_auth.py` (OAuth, JWT, API key - ~400 lines)

- [ ] **node_graph_widget.py refactoring**
  - Extract GraphInteractionController (drag/drop, selection)
  - Extract GraphRenderingController (painting, layout)
  - Extract GraphContextMenuController (right-click actions)
  - Reduce to <1200 lines

- [ ] **database_nodes.py split**
  - Create `sql_nodes.py` (Connect, Query, Transaction - ~800 lines)
  - Create `nosql_nodes.py` (MongoDB, Redis operations - ~800 lines)

---

### Medium Priority Files (1000-1500 lines)

**Defer to post-v3.0** (not blocking)

---

## v3.0 Migration Preparation (1-2 weeks)

**Status**: Planning phase
**Priority**: High (breaking release)
**Target**: Clean architecture fully realized, zero legacy code

### Target Architecture (v3.0)

**Clean separation achieved**:
```
presentation/
├── canvas/
│   ├── main_window.py            (~800 lines, pure UI coordination)
│   ├── controllers/              (12 controllers, ~3,000 lines)
│   ├── components/               (9 components, ~1,600 lines)
│   ├── ui/                       (16 UI components, ~5,000 lines)
│   ├── visual_nodes/             (141 nodes, category-based)
│   └── graph/                    (NodeGraphWidget, <1200 lines)

application/
├── use_cases/
│   ├── execute_workflow.py       (workflow execution)
│   ├── validate_workflow.py      (validation logic)
│   ├── save_workflow.py          (persistence)
│   └── load_workflow.py          (deserialization)

domain/
├── entities/                     (Workflow, Node, Project - pure logic)
├── services/                     (ExecutionOrchestrator, ProjectContext)
├── value_objects/                (Port, DataType, ExecutionResult)
└── repositories/                 (interfaces only)

infrastructure/
├── resources/                    (Browser, Desktop resource managers)
├── persistence/                  (Project, Workflow storage)
└── adapters/                     (Playwright, UIAutomation wrappers)
```

---

### Breaking Changes in v3.0

**Removals**:
- [ ] **Delete `core/` compatibility layer**
  - Remove `core/types.py` re-export wrapper
  - Remove `core/base_node.py` re-export wrapper
  - Remove `core/workflow_schema.py` re-export wrapper
  - All imports must use `domain/` directly

- [ ] **Delete `visual_nodes.py` monolith**
  - 4,285 lines deprecated file
  - All imports migrated to category-based structure
  - Remove compatibility layer

- [ ] **Remove old `ExecutionContext` pattern**
  - Deprecated in favor of `ExecuteWorkflowUseCase`
  - Clean up any remaining references
  - Update all execution paths

**Import Migrations Required**:

```python
# v2.x (deprecated) - WILL BREAK IN v3.0
from casare_rpa.core.types import NodeStatus, DataType
from casare_rpa.core.workflow_schema import WorkflowSchema
from casare_rpa.core import Port
from casare_rpa.presentation.canvas.visual_nodes.visual_nodes import VisualStartNode

# v3.0 (required)
from casare_rpa.domain.value_objects.types import NodeStatus, DataType
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.value_objects import Port
from casare_rpa.presentation.canvas.visual_nodes import VisualStartNode
```

**Actions**:
- [ ] Create automated import rewriter script
  - Parse all `.py` files in src/
  - Detect deprecated imports
  - Rewrite to v3.0 imports
  - Generate migration report

- [ ] Create deprecation warning scanner
  - Scan codebase for DeprecationWarning usage
  - List all files with deprecated imports
  - Generate cleanup checklist

- [ ] Update all internal imports
  - Run import rewriter on src/
  - Fix any broken imports
  - Verify all tests pass

- [ ] Update documentation
  - Update import examples in README
  - Update CLAUDE.md with v3.0 imports
  - Create MIGRATION_GUIDE_V3.md

---

### Migration Tools to Build

- [ ] **Automated Import Rewriter**
  - Script: `scripts/migrate_imports_v3.py`
  - Uses AST parsing (ast module)
  - Rewrites imports in-place
  - Generates diff report

- [ ] **Deprecation Warning Scanner**
  - Script: `scripts/scan_deprecations.py`
  - Searches for DeprecationWarning
  - Lists affected files
  - Generates cleanup report

- [ ] **Test Suite for v3.0 Compatibility**
  - Test: `tests/test_v3_compatibility.py`
  - Verifies zero deprecated imports
  - Verifies zero DeprecationWarnings
  - Gates v3.0 release

---

### Quality Gates for v3.0 Release

**All must pass before v3.0 release**:

- [ ] **Test Coverage: 100%**
  - All 242 nodes tested (currently 60%)
  - Domain layer: 100% (currently 84%)
  - Application layer: 100% (currently 34%)
  - Total tests: 1,400+ (currently 1,676)

- [ ] **All Tests Passing**
  - Zero failing tests
  - Zero flaky tests
  - All CI checks green

- [ ] **Performance Benchmarks Met**
  - Startup time: <target> seconds
  - Execution time: <target> seconds
  - Memory usage: <500 MB
  - EventBus overhead: <target> ms

- [ ] **Zero Critical Bugs**
  - No P0/P1 bugs in backlog
  - All known issues resolved or documented

- [ ] **Zero Deprecation Warnings**
  - All deprecated imports removed
  - All compatibility layers deleted
  - Clean test output

- [ ] **Documentation Complete**
  - API documentation (Sphinx/MkDocs)
  - Architecture guide (ARCHITECTURE.md)
  - Migration guide (MIGRATION_GUIDE_V3.md)
  - User manual updated

- [ ] **All Files <1500 Lines**
  - desktop/context.py: <1000 lines
  - file_nodes.py: <1200 lines (split)
  - http_nodes.py: <1200 lines (split)
  - node_graph_widget.py: <1200 lines
  - database_nodes.py: <1200 lines (split)
  - No files >1500 lines

- [ ] **Clean Architecture Principles Validated**
  - Dependency flow: Presentation → Application → Domain ← Infrastructure
  - Domain has zero external dependencies
  - All business logic in domain layer
  - Infrastructure implements domain interfaces

---

## Timeline and Dependencies

### Critical Path

```
Week 6 (IN PROGRESS)
  └─ Node test coverage: 60% → 100%
       ├─ Day 1: Office automation (42 tests)
       ├─ Day 2: Desktop advanced (58 tests)
       ├─ Day 3: File system (55 tests)
       ├─ Day 4: System + scripts (61 tests)
       └─ Day 5: Basic + verification (25 tests)

Week 7 (NEXT)
  └─ Performance optimization
       ├─ Day 1: Baseline measurement
       ├─ Day 2-3: EventBus + component init
       ├─ Day 4: Import optimization
       └─ Day 5: Caching + validation

Week 8 (PARALLEL)
  ├─ Large file refactoring
  │    ├─ desktop/context.py split
  │    ├─ file_nodes.py split
  │    └─ http_nodes.py split
  │
  └─ v3.0 migration prep
       ├─ Build import rewriter
       ├─ Build deprecation scanner
       └─ Create migration docs

Week 9-10 (FINAL)
  ├─ Run automated import rewriter
  ├─ Delete compatibility layers
  ├─ Verify all tests pass
  ├─ Performance validation
  └─ v3.0 release
```

---

## Success Metrics

### Week 7-8 Targets
- [ ] Performance: 20%+ startup improvement, 10%+ execution improvement
- [ ] Large files: 5 files refactored (8 total → 3 remaining)
- [ ] v3.0 prep: Migration tools built and tested

### v3.0 Release Targets
- [ ] Test coverage: 100% (all 242 nodes + domain + application)
- [ ] Performance: All benchmarks met
- [ ] Code quality: All files <1500 lines
- [ ] Clean architecture: Zero violations
- [ ] Documentation: Complete and accurate
- [ ] Zero breaking bugs

---

**Created**: November 28, 2025
**Status**: Ready for implementation (post-Week 6)
**Estimated Completion**: 3-4 weeks from Week 6 completion
