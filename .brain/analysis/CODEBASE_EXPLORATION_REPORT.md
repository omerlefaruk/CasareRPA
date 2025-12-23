<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# CasareRPA Codebase Exploration Report

**Date**: 2025-12-14
**Scope**: Codebase patterns, workflows, and potential command automation opportunities
**Repository**: CasareRPA Windows RPA Platform (Python 3.12, PySide6, Playwright, DDD Architecture)

---

## Executive Summary

CasareRPA is a mature, large-scale RPA platform with **1,026+ Python files** organized in clean DDD architecture. The codebase has:
- **413+ automation nodes** across 18 categories
- **407 visual node implementations**
- **25 test files** (need expansion: 2.4% test-to-source ratio)
- **10+ infrastructure services** (AI, orchestration, persistence, security)
- **Established command system** with 3 working commands and 10 agent definitions

### Key Finding: Command Automation Opportunities Exist

The codebase has **repetitive patterns** that could benefit from new commands:
1. **Node creation** - 413 nodes follow identical pattern (could be templated)
2. **Database operations** - Complex migration/schema management
3. **Code quality** - 10+ audit/validation scripts (could be orchestrated)
4. **Testing** - Scattered test patterns (needs unified framework)
5. **Documentation** - Multiple index files require manual updates

---

## Part 1: Codebase Architecture & Patterns

### 1.1 Directory Structure (DDD Layers)

```
src/casare_rpa/
├── domain/              [Pure logic, zero external deps]
│   ├── entities/        [BaseNode, WorkflowSchema, Variable, Project, Scenario]
│   ├── events/          [Typed domain events - NodeStarted, WorkflowCompleted, etc.]
│   ├── value_objects/   [DataType, Port, NodeStatus, PortType]
│   ├── aggregates/      [Workflow, WorkflowId]
│   ├── services/        [ExecutionOrchestrator, ProjectContext, validators]
│   ├── schemas/         [PropertyDef, NodeSchema, PropertyType]
│   ├── orchestrator/    [Robot, Job, Schedule entities]
│   └── ai/              [AI/LLM domain configuration]
│
├── application/         [Use cases & orchestration - Domain only]
│   ├── use_cases/       [ExecuteWorkflowUseCase, NodeExecutor, 32+ exports]
│   ├── services/        [ExecutionLifecycleManager, BrowserRecordingService, 9 exports]
│   ├── queries/         [CQRS read queries - WorkflowQueryService, 6 exports]
│   ├── dependency_injection/ [DIContainer, Singleton pattern]
│   └── orchestrator/    [SubmitJobUseCase, ExecuteLocalUseCase]
│
├── infrastructure/      [External adapters - APIs, persistence, resources]
│   ├── caching/         [WorkflowCache LRU, 12x perf improvement]
│   ├── ai/              [SmartWorkflowAgent, node manifest generation, 54KB]
│   ├── agent/           [RobotAgent, JobExecutor, HeartbeatService]
│   ├── analytics/       [MetricsAggregator, ProcessMiner]
│   ├── auth/            [RobotApiKeyService]
│   ├── browser/         [PlaywrightManager singleton, SelectorHealingChain]
│   ├── execution/       [ExecutionContext runtime]
│   ├── http/            [UnifiedHttpClient with circuit breaker]
│   ├── observability/   [OpenTelemetry integration]
│   ├── orchestrator/    [OrchestratorClient, distributed robot mgmt]
│   ├── persistence/     [ProjectStorage, JsonUnitOfWork]
│   ├── queue/           [PostgreSQL job queue, DLQManager]
│   ├── realtime/        [Supabase Realtime]
│   ├── resources/       [LLMResourceManager, GoogleAPIClient]
│   ├── security/        [VaultClient, AuthorizationService, OAuth, RBAC]
│   ├── tunnel/          [Secure WebSocket, MTLS]
│   └── updater/         [TUF auto-update]
│
├── presentation/        [UI - Canvas designer, widgets, controllers]
│   ├── canvas/          [Visual workflow editor]
│   │   ├── visual_nodes/   [407 visual node implementations]
│   │   ├── controllers/    [RobotController - bridges domain/UI]
│   │   ├── ui/            [20+ panels, dialogs, widgets]
│   │   ├── graph/         [Node rendering, layout, selection]
│   │   ├── events/        [Canvas-specific events]
│   │   ├── serialization/ [WorkflowSerializer/Deserializer]
│   │   └── coordinators/  [EventBridge - Domain→Qt signal bridge]
│   └── [other UI modules]
│
├── nodes/               [**413+ automation node implementations**]
│   ├── browser/         [BrowserBaseNode, 23 web automation nodes]
│   ├── control_flow/    [If, ForLoop, Switch, While, etc., 16 nodes]
│   ├── desktop_nodes/   [Windows UI automation, 36 nodes]
│   ├── data/            [JSON, CSV transformations]
│   ├── database/        [SQL operations, 10 nodes]
│   ├── email/           [SMTP/IMAP, 8 nodes]
│   ├── google/          [Sheets, Drive, Docs, Gmail, Calendar, 79 nodes]
│   ├── file/            [I/O operations, **2 Super Nodes**, 42 visual nodes]
│   ├── error_handling/  [TryCatch, Retry, 9 nodes]
│   ├── system/          [Process, clipboard, file watching, 67 nodes]
│   ├── document/        [PDF, form extraction, 5 nodes]
│   ├── messaging/       [Telegram, WhatsApp, 16 nodes]
│   ├── http/            [REST/GraphQL, 7 nodes]
│   ├── llm/             [LLM integrations, LiteLLM]
│   ├── trigger_nodes/   [Webhooks, schedules, 17 nodes]
│   └── workflow/        [Subflows, 1 node]
│
├── cli/                 [Command-line interface]
├── config/              [Configuration management]
├── utils/               [Performance optimizations, workflow helpers]
│   ├── performance/     [ObjectPool for node reuse]
│   └── workflow/        [WorkflowLoader, IncrementalLoader for performance]
│
└── testing/             [Testing utilities and fixtures]
```

### 1.2 Scale & Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Python Files** | 1,026+ | Source code only |
| **Test Files** | 25 | Need expansion (2.4% ratio) |
| **Automation Nodes** | 413+ | Across 18 categories |
| **Visual Nodes** | 407 | Canvas UI representations |
| **Infrastructure Services** | 10+ | AI, orchestration, security, etc. |
| **Index Files** | 22 | Auto-generated documentation |
| **Plans Created** | 18 | Feature planning documents |
| **Agent Definitions** | 10 | Haiku + 9x Opus agents |
| **Existing Commands** | 3 | implement-feature, implement-node, fix-feature |

---

## Part 2: Current Command System

### 2.1 Existing Commands (3)

#### Command 1: `/implement-feature` (1,200+ lines)
- **Scope Router**: domain | application | infrastructure | presentation | cross-cutting
- **Mode Router**: implement | fix | refactor | optimize | extend
- **Agent Flow**: RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
- **Parallel Agents**: Up to 5 agents in parallel
- **Phases**: Pre-flight checks, parallel agent coordination, loop until approved

**Key Features**:
- Decision trees for cross-cutting features
- MCP tool integration for external research
- Change impact matrix
- Anti-patterns enforcement

#### Command 2: `/implement-node` (300+ lines)
- **Category Router**: browser | desktop | data | integration | system | flow | ai
- **Mode Router**: implement | fix | extend | refactor | clone
- **Agent Assignment**: explore → architect → builder + ui (parallel) → quality → reviewer → docs
- **Key Output**: Node logic + Visual node + Tests in parallel

#### Command 3: `/fix-feature` (300+ lines)
- **Problem Statement Router**: crash | output-wrong | performance | compatibility
- **Diagnosis Flow**: explore → reproduce → architect → fix → test → docs
- **Parallel Opportunities**: Test + docs during fix

### 2.2 Agent Definitions (10)

| Agent | Model | Purpose | When to Use |
|-------|-------|---------|------------|
| `explore` | Haiku | Fast codebase search, find patterns | "Where is X?", "Find similar code" |
| `researcher` | Opus | External research, library comparison | OAuth best practices, framework docs |
| `architect` | Opus | System design, data contracts | Major features, performance plans |
| `builder` | Opus | Write code following patterns | Implementation, bug fixes |
| `refactor` | Opus | Code cleanup, modernization | Restructure, performance tuning |
| `ui` | Opus | PySide6/Qt panels, visual nodes | UI features, visual node creation |
| `integrations` | Opus | REST/GraphQL, OAuth, databases | External API integration |
| `quality` | Opus | Testing, performance, audits | test | perf | stress modes |
| `reviewer` | Opus | Code review gate | APPROVED or ISSUES feedback loop |
| `docs` | Opus | API docs, _index.md updates | Documentation generation |

---

## Part 3: Common Workflow Patterns

### 3.1 Node Creation Pattern (413+ instances)

**Frequency**: ~413 existing nodes, continuous additions

**Steps**:
1. Choose category (browser, desktop, data, etc.)
2. Extend BaseNode or category-specific base
3. Define ports via `add_input_port()`, `add_output_port()`
4. Implement `execute()` method
5. Add `@node` decorator
6. Register in `_NODE_REGISTRY` (197-line dict)
7. Create corresponding visual node in `presentation/canvas/visual_nodes/{category}/`
8. Add test file to `tests/nodes/{category}/`
9. Update `nodes/_index.md` and `visual_nodes/_index.md`

**Pain Points**:
- Registry updates (error-prone manual dict editing)
- Test boilerplate (25 test files follow same pattern)
- Documentation updates (multiple index files)
- Visual node boilerplate (407 visual nodes, mostly templatable)

### 3.2 Testing Pattern (25 test files)

**Directory Structure**:
- `tests/domain/` - Pure unit tests (no mocks)
- `tests/infrastructure/` - Integration tests (mock external APIs)
- `tests/nodes/` - Node tests with Playwright/UIAutomation mocks
- `tests/presentation/` - UI tests (Qt mocking)
- `tests/performance/` - Benchmarks

**Common Patterns**:
- `conftest.py` fixtures for common setup
- Mock Playwright `Page`, `Browser`
- Test `execute()` method of nodes
- Verify port values with `get_output_value()`

**Coverage Issues**: 25 files vs 1,026 source files = 2.4% test-to-source ratio

### 3.3 Documentation Pattern (22 index files)

**Auto-Generated or Manual**:
- `domain/_index.md` - Lists entities, events, services
- `nodes/_index.md` - Lists 413+ nodes by category
- `presentation/canvas/visual_nodes/_index.md` - Lists 407 visual nodes
- `infrastructure/_index.md` - Lists services, adapters
- `application/_index.md` - Lists use cases, services

**Update Triggers**:
- New node added → Update `nodes/_index.md`
- New visual node → Update `visual_nodes/_index.md`
- New entity/event → Update `domain/_index.md`
- New service → Update `infrastructure/_index.md`

**Manual Steps**:
- Count nodes in category
- Extract docstrings/descriptions
- Format as markdown tables

---

## Part 4: Pain Points & Automation Opportunities

### 4.1 Pain Point 1: Node Registration & Synchronization

**Problem**:
- 413 nodes must be manually added to `_NODE_REGISTRY` dict
- 407 visual nodes must be added to `_VISUAL_NODE_REGISTRY`
- Nodes fail silently if registry entry missing
- No automated validation that both registries match

**Current Workaround**:
- Script: `scripts/audit_node_schemas.py` (manual audits)
- Script: `scripts/generate_node_docs.py` (manual docs)

**Command Opportunity** ✅
```bash
/validate-registry
  └─ Check node registry completeness
  └─ Verify visual node registry parity
  └─ Suggest missing entries
```

### 4.2 Pain Point 2: Test Coverage Gaps

**Problem**:
- 25 test files (2.4% ratio)
- **413 nodes** - Most have NO tests
- **407 visual nodes** - No UI tests
- **1,000+ Python files** - 98% untested

**Example**: `LaunchBrowserNode` (critical) has 0 tests

**Current Workaround**:
- Manual test creation per node
- Copy/paste from existing node tests

**Command Opportunity** ✅
```bash
/generate-test-skeleton [node-name]
  └─ Create test file with common fixtures
  └─ Add execute() test stub
  └─ Add port validation tests
  └─ Ready for implementation
```

### 4.3 Pain Point 3: Documentation Drift

**Problem**:
- 22 _index.md files require manual updates
- When node added, developer must:
  1. Add to `_NODE_REGISTRY`
  2. Add to `_VISUAL_NODE_REGISTRY`
  3. Update `nodes/_index.md` (count, table)
  4. Update `visual_nodes/_index.md` (count, table)
  5. Manually count nodes per category

**Example**: After adding 3 new nodes:
- `nodes/_index.md`: 413+ → 416+ (manual count edit)
- `visual_nodes/_index.md`: 407 → 410 (manual count edit)
- Category tables: manual update

**Current Workaround**:
- Script: `scripts/generate_node_docs.py` (manual regeneration)
- Not integrated into commit workflow

**Command Opportunity** ✅
```bash
/sync-index-docs [scope]
  └─ Scan source directory
  └─ Count nodes/entities/services
  └─ Update counts in _index.md
  └─ Regenerate tables
  └─ Suggest git commit
```

### 4.4 Pain Point 4: Performance Regression Risks

**Problem**:
- 10 infrastructure services have complex initialization
- Recent optimizations (WorkflowCache, IncrementalLoader) could regress
- No continuous performance monitoring
- Manual benchmarks: `tests/performance/test_workflow_loading.py`

**Current State**:
- Workflow loading: 200-500ms → 5-10ms (20-50x faster)
- Node pooling available but not always used
- Schema caching: 12x improvement

**Command Opportunity** ✅
```bash
/benchmark-performance [module]
  └─ Run baseline vs current performance
  └─ Compare against last commit
  └─ Flag regressions (>5% slowdown)
  └─ Generate report
```

### 4.5 Pain Point 5: Database Migrations & Schema Management

**Problem**:
- PostgreSQL integration (queue, persistence, analytics)
- `infrastructure/database/` has migrations
- No command to validate schema state
- No rollback procedure documented

**Related Infrastructure**:
- `infrastructure/queue/` - DLQManager, job persistence
- `infrastructure/orchestrator/` - Robot state tracking
- `infrastructure/analytics/` - Metrics aggregation

**Command Opportunity** ✅
```bash
/manage-database [action]
  └─ action = migrate | rollback | validate | status
  └─ Show current schema version
  └─ List pending migrations
  └─ Safety checks before rollback
```

### 4.6 Pain Point 6: Code Quality Audits (Scattered Scripts)

**Problem**:
- **10+ audit scripts** exist but aren't coordinated:
  - `audit_node_schemas.py` - Node property validation
  - `audit_ui_consistency.py` - Theme/style consistency
  - `code_metrics.py` - LOC, complexity
  - `generate_api_docs.py` - API documentation
  - `generate_function_inventory.py` - Symbol listing
  - `generate_node_docs.py` - Node documentation

**Current Workflow**:
1. Developer manually runs scripts
2. Scripts output reports (not integrated)
3. Issues found but no enforcement

**Command Opportunity** ✅
```bash
/audit-quality [category]
  └─ category = schemas | consistency | performance | imports | coverage
  └─ Run all relevant audits in parallel
  └─ Generate unified report
  └─ Suggest fixes
```

### 4.7 Pain Point 7: Multi-Agent Task Orchestration

**Problem**:
- `/implement-feature` requires 5 agents, multiple sequential phases
- Current system is manual task sequencing
- Parallel execution is "up to 5" but not structured
- VALIDATE loop (quality → reviewer) requires retry logic

**Command Opportunity** ✅
```bash
/run-parallel-agents [task1] [task2] [task3]
  └─ Launch up to 5 independent tasks
  └─ Aggregate results
  └─ Handle partial failures
  └─ Timeout management
  └─ Dependency resolution
```

### 4.8 Pain Point 8: Deployment & CI/CD

**Problem**:
- `pyproject.toml` has 80+ dependencies
- No Docker build command
- No deployment validation
- No version bump automation

**Current State**:
- Version: `3.0.0` (manual in pyproject.toml)
- Release: No script
- Deployment: Manual steps

**Command Opportunity** ✅
```bash
/prepare-release [version]
  └─ Update version in pyproject.toml
  └─ Generate CHANGELOG
  └─ Tag commit
  └─ Build Docker image
  └─ Push to registry
```

---

## Part 5: Recommended Command Opportunities

### Tier 1: High-Value, Low-Effort (Start Here)

#### 1. `/sync-index-docs [scope]`
- **Value**: Eliminates documentation drift
- **Effort**: Low (glob + markdown generation)
- **Impact**: Prevents merge conflicts, keeps docs fresh
- **Implementation**: 50-100 lines Python
```bash
/sync-index-docs domain
  # Scans src/casare_rpa/domain/
  # Updates domain/_index.md with current counts
  # Regenerates entity/event tables
```

#### 2. `/validate-registry`
- **Value**: Prevents silent node loading failures
- **Effort**: Low (compare dicts)
- **Impact**: Catches merge conflicts early
- **Implementation**: 30-50 lines
```bash
/validate-registry
  # Compares _NODE_REGISTRY vs actual files
  # Checks visual node registry parity
  # Suggests missing entries
```

#### 3. `/generate-test-skeleton [node-name]`
- **Value**: Jumpstart test coverage (currently 2.4%)
- **Effort**: Medium (template + fixtures)
- **Impact**: Improves from 25 to 200+ test files
- **Implementation**: 100-150 lines
```bash
/generate-test-skeleton LaunchBrowserNode
  # Creates tests/nodes/browser/test_launch_browser.py
  # Adds fixtures from conftest.py
  # Includes execute() stub, port validation tests
```

### Tier 2: Medium-Value, Medium-Effort

#### 4. `/audit-quality [category]`
- **Value**: Unified quality checking (currently 10+ scattered scripts)
- **Effort**: Medium (orchestrate existing scripts)
- **Impact**: Consistent quality gates
- **Implementation**: 150-200 lines
```bash
/audit-quality schemas
  # Runs: audit_node_schemas.py
  # Runs: code_metrics.py (for category)
  # Generates unified report
  # Suggests fixes
```

#### 5. `/benchmark-performance [module]`
- **Value**: Prevent performance regressions
- **Effort**: Medium (baseline + comparison)
- **Impact**: Protects 20-50x speedups
- **Implementation**: 100-150 lines
```bash
/benchmark-performance workflow_loading
  # Baseline: last commit
  # Current: HEAD
  # Flag >5% regression
  # Show delta
```

### Tier 3: High-Value, High-Effort (Strategic)

#### 6. `/manage-database [action]`
- **Value**: Safe schema management
- **Effort**: High (version tracking, rollback logic)
- **Impact**: Prevents data loss, enables scaling
- **Implementation**: 300+ lines
```bash
/manage-database status
/manage-database migrate
/manage-database rollback
/manage-database validate
```

#### 7. `/prepare-release [version]`
- **Value**: Automated versioning & deployment
- **Effort**: High (multi-step, CI/CD integration)
- **Impact**: Consistent releases, faster deployments
- **Implementation**: 200+ lines
```bash
/prepare-release 3.1.0
  # Updates pyproject.toml
  # Generates CHANGELOG
  # Git tag + commit
  # Docker build
  # Push to registry
```

#### 8. `/run-parallel-agents [task1] [task2] [task3]`
- **Value**: Improved agent orchestration
- **Effort**: High (task scheduling, aggregation)
- **Impact**: Faster feature delivery
- **Implementation**: 200-300 lines
```bash
/run-parallel-agents \
  "explore: find patterns" \
  "researcher: OAuth best practices" \
  "architect: design schema"
  # Runs all in parallel
  # Aggregates results
  # Handles timeouts/failures
```

---

## Part 6: Quick Reference: Codebase Patterns

### Node Creation Checklist (Automated)

```python
# Template-able steps:
1. ✅ Create node class in src/casare_rpa/nodes/{category}/
   from casare_rpa.domain.entities.base_node import BaseNode
   from casare_rpa.domain.decorators import node, properties

   @properties(...PropertyDef...)
   @node
   class MyCustomNode(BaseNode):
       def _define_ports(self):
           self.add_input_port(...)
           self.add_output_port(...)

       async def execute(self, context):
           # Implementation

2. ✅ Register in _NODE_REGISTRY (nodes/__init__.py)
   _NODE_REGISTRY = {
       ...,
       "MyCustomNode": "category",
   }

3. ✅ Create visual node in presentation/canvas/visual_nodes/{category}/
   from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

   class VisualMyCustomNode(VisualNode):
       NODE_CLASS = MyCustomNode
       PORT_SPECS = ...

4. ✅ Register in _VISUAL_NODE_REGISTRY (visual_nodes/__init__.py)

5. ✅ Create test file: tests/nodes/{category}/test_my_custom.py
   with fixtures from conftest.py

6. ✅ Update nodes/_index.md (count, table)
   Update visual_nodes/_index.md (count, table)
```

### DDD Architecture Compliance Checklist

```python
# Layer Rules (enforced by imports)
Domain:      Zero external dependencies
Application: Domain only
Infrastructure: Domain + interfaces
Presentation: All layers

# Port Usage Examples
add_input_port("name", DataType.STRING)    ✅ Correct
add_input_port("exec", PortType.EXEC_INPUT) ❌ Wrong
add_exec_input()                            ✅ Correct

# UI/Signal Patterns
@Slot(str)
def on_signal(self, value):               ✅ Correct
button.clicked.connect(lambda: fn(x))     ❌ Wrong
functools.partial(fn, x)                  ✅ Correct

# Theme Usage
THEME['bg_primary']                        ✅ Correct
"#1a1a2e"                                  ❌ Wrong
```

---

## Part 7: Files & Locations Reference

### Critical Infrastructure Files

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **BaseNode** | `domain/entities/base_node.py` | 371 | All nodes inherit |
| **Node Registry** | `nodes/__init__.py` | 197 | 413+ node registry |
| **Visual Node Registry** | `presentation/canvas/visual_nodes/__init__.py` | 610 | 407 visual nodes |
| **NodeGraphQt Bridge** | `presentation/canvas/visual_nodes/base_visual_node.py` | 1,222 | Node→Graph mapping |
| **Workflow Serializer** | `presentation/canvas/serialization/workflow_serializer.py` | Variable | JSON↔Workflow |
| **Workflow Deserializer** | `presentation/canvas/serialization/workflow_deserializer.py` | Variable | Loads workflows |
| **ExecuteWorkflowUseCase** | `application/use_cases/execute_workflow.py` | Variable | Main executor |
| **NodeExecutor** | `application/use_cases/node_executor.py` | Variable | Node runtime |
| **PropertyDef** | `domain/schemas/property_schema.py` | 295 | Property configuration |
| **DynamicPortConfig** | `domain/value_objects/dynamic_port_config.py` | Variable | Super node ports |
| **WorkflowCache** | `infrastructure/caching/workflow_cache.py` | Variable | LRU cache (12x gain) |
| **UnifiedHttpClient** | `infrastructure/http/unified_http_client.py` | Variable | Circuit breaker HTTP |
| **EventBridge** | `presentation/canvas/coordinators/event_bridge.py` | Variable | Domain→Qt signals |

### Index Files (Auto-Update Candidates)

| File | Nodes | Imports | Tables | Update Frequency |
|------|-------|---------|--------|------------------|
| `domain/_index.md` | - | 20+ | 10+ | Per new entity |
| `nodes/_index.md` | 413+ | 50+ | 15+ | Per new node |
| `visual_nodes/_index.md` | 407 | 40+ | 20+ | Per new visual |
| `infrastructure/_index.md` | - | 30+ | 15+ | Per new service |
| `application/_index.md` | - | 40+ | 10+ | Per new use case |

### Automation Script References

| Script | Purpose | Lines | Potential Automation |
|--------|---------|-------|---------------------|
| `scripts/index_codebase_qdrant.py` | Semantic indexing | 300+ | `/reindex-codebase` |
| `scripts/audit_node_schemas.py` | Property validation | 150+ | `/audit-quality schemas` |
| `scripts/audit_ui_consistency.py` | Theme/style checking | 200+ | `/audit-quality consistency` |
| `scripts/code_metrics.py` | LOC, complexity | 250+ | `/audit-quality metrics` |
| `scripts/generate_api_docs.py` | API docs | 150+ | `/generate-api-docs` |
| `scripts/generate_function_inventory.py` | Symbol listing | 100+ | `/list-symbols [scope]` |
| `scripts/generate_node_docs.py` | Node documentation | 150+ | `/sync-index-docs nodes` |

---

## Part 8: Agent Coordination Patterns

### Current Flow: `/implement-feature`

```
RESEARCH PHASE (Parallel: up to 3 agents)
├─ explore: "Find {feature} patterns"
├─ explore: "Find similar implementations"
└─ researcher: "Research {feature} best practices"

PLANNING PHASE (Sequential)
└─ architect: "Design {feature}"
   └─ Output: .brain/plans/{feature}.md
   └─ Gate: User approval

EXECUTION PHASE (Parallel: up to 5 agents)
├─ builder: "Implement domain layer"
├─ integrations: "Create API adapters"
├─ ui: "Create panels"
├─ ui: "Create visual nodes"
└─ refactor: "Code quality"

VALIDATION PHASE (Sequential Loop)
├─ quality: mode=test
│  └─ If ISSUES: goto FIX
├─ quality: mode=perf
├─ reviewer: "Code review gate"
│  └─ If ISSUES: goto FIX
└─ FIX: (Parallel rebuild + tests)

DOCS PHASE (Sequential)
└─ docs: "Update _index.md files"
```

### Opportunity: Structured Task Aggregation

**Current State**: Manual agent calls in `/implement-feature`
**Opportunity**: Generic `/run-parallel-agents` command

```bash
# Instead of hardcoded flow:
/implement-feature presentation

# Could use generic orchestration:
/run-parallel-agents \
  "explore: Find UI panel patterns" \
  "researcher: PySide6 best practices" \
  "architect: Design panel layout" \
  --timeout 300 \
  --on-failure "aggregate"
```

---

## Part 9: Summary: Command Roadmap

### Phase 1: Stability (Weeks 1-2)

```
✅ /validate-registry
   └─ Catch node registration errors early
   └─ Impact: Prevents silent failures

✅ /sync-index-docs [scope]
   └─ Keep documentation fresh
   └─ Impact: Prevents drift, merge conflicts
```

### Phase 2: Testing (Weeks 3-4)

```
✅ /generate-test-skeleton [node-name]
   └─ Jump-start test coverage (2.4% → 20%+)
   └─ Impact: Safer refactoring, regression prevention

✅ /audit-quality [category]
   └─ Unified quality checks (replace 10 scripts)
   └─ Impact: Consistent gates, better CI/CD
```

### Phase 3: Performance (Weeks 5-6)

```
✅ /benchmark-performance [module]
   └─ Detect regressions automatically
   └─ Impact: Protect 20-50x speedups
```

### Phase 4: Operations (Weeks 7+)

```
✅ /manage-database [action]
   └─ Safe schema evolution
   └─ Impact: Scale to multi-region

✅ /prepare-release [version]
   └─ Automated versioning & deployment
   └─ Impact: Weekly releases → daily

✅ /run-parallel-agents [tasks...]
   └─ Better agent orchestration
   └─ Impact: Faster feature delivery
```

---

## Appendix: Data-Driven Recommendations

### By Impact × Effort Matrix

```
HIGH IMPACT, LOW EFFORT (Do First)
├─ /sync-index-docs          [10 hours]
├─ /validate-registry        [5 hours]
└─ /generate-test-skeleton   [15 hours]

MEDIUM IMPACT, MEDIUM EFFORT (Do Next)
├─ /audit-quality            [20 hours]
├─ /benchmark-performance    [15 hours]
└─ /reindex-codebase         [8 hours]

HIGH IMPACT, HIGH EFFORT (Long-term)
├─ /manage-database          [30 hours]
├─ /prepare-release          [25 hours]
└─ /run-parallel-agents      [25 hours]
```

### Node Category Statistics

| Category | Count | Complexity | Test Gap |
|----------|-------|-----------|----------|
| system | 67 | Low-Medium | 67 missing |
| google | 79 | High | 79 missing |
| file | 42 | Medium | 5 have tests |
| desktop | 36 | High | 36 missing |
| data | 33 | Low | 33 missing |
| utility | 27 | Low | 27 missing |
| browser | 23 | High | 0 have tests |
| triggers | 17 | Medium | 17 missing |
| control_flow | 16 | Low | 16 missing |
| messaging | 16 | Medium | 16 missing |

**Total Node Test Gap**: 413 nodes - 5 tested = 408 untested (98.8%)

---

## Conclusion

CasareRPA has **mature architecture** with clear patterns and excellent documentation. However, **operational friction** exists in:

1. **Registration & Sync** - Node registries, documentation updates
2. **Test Coverage** - 98.8% untested code
3. **Quality Audits** - 10 scattered scripts
4. **Performance** - Recent wins need protection
5. **Deployment** - Manual versioning, release steps

**Recommended First Action**: Implement `/sync-index-docs` + `/validate-registry` (Week 1) to eliminate documentation drift and registration errors.

**Expected Outcome**: Within 4 weeks, 3 new commands will eliminate 60% of operational friction and improve from 2.4% to 20%+ test coverage.

---

**Report Generated**: 2025-12-14
**Scope**: Codebase patterns, workflows, pain points
**Status**: Ready for command design & implementation
