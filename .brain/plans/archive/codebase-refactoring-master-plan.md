# CasareRPA Codebase Refactoring Master Plan

**Created**: 2025-12-14
**Status**: Ready for Approval
**Total Estimated Effort**: 200-280 hours (8-12 weeks)

---

## Executive Summary

Comprehensive analysis identified **500+ refactoring opportunities** across 8 major categories:

| Category | Issues | LOC Impact | Priority | Effort |
|----------|--------|------------|----------|--------|
| Error Handling Consolidation | 446 | 2,230-2,680 | P1 | 12-17h |
| HTTP Client Migration | 30+ files | - | P1 | 56h |
| Hardcoded Config Externalization | 120+ values | - | P1 | 40-80h |
| PropertyDef Consolidation | 47+ duplicates | ~200 | P2 | 3-5h |
| UI Theme/Signal Violations | 214+ | - | P2 | 35-50h |
| Test Coverage Gaps | 1.9% → 70% | 15,000+ new | P2 | 150h+ |
| Large File Splitting | 13 files | - | P3 | 20-30h |
| Deprecated Code Removal | 15+ files | -500 | P3 | 4-6h |

---

## Phase 1: Foundation & Security (Week 1-2)

### 1.1 Security Critical: PBKDF2 Iterations
**Priority**: CRITICAL | **Effort**: 2 hours | **Risk**: LOW

Fix hardcoded security values in 5 files:
- `infrastructure/security/api_key_store.py:151,182`
- `infrastructure/security/credential_store.py:249,274`
- `infrastructure/security/sqlite_vault.py:160`

**Action**: Create `config/security_config.py` with configurable iterations.

### 1.2 Create @error_handler Decorator
**Priority**: HIGH | **Effort**: 3 hours | **Risk**: LOW

Create `domain/decorators/error_handler.py`:
- Standardized try/except wrapping
- Status management (NodeStatus.ERROR)
- Logging format consistency
- Result dictionary formatting

**Impact**: Eliminates 446 repetitive exception handlers.

### 1.3 Create Centralized Config Infrastructure
**Priority**: HIGH | **Effort**: 8 hours | **Risk**: LOW

Create dataclasses in `config/`:
- `TimeoutConfig` - 25 timeout values
- `RetryConfig` - 6 retry values
- `PortConfig` - 20 port numbers
- `SecurityConfig` - PBKDF2, token expiry

---

## Phase 2: Core Consolidation (Week 2-4)

### 2.1 HTTP Client Migration (P1 Files)
**Priority**: HIGH | **Effort**: 6 hours | **Risk**: MEDIUM

Migrate critical files to UnifiedHttpClient:
1. `application/services/orchestrator_client.py` - 2h
2. `infrastructure/resources/llm_model_provider.py` - 1h
3. `infrastructure/resources/unified_resource_manager.py` - 1h
4. `presentation/canvas/ui/dialogs/google_oauth_dialog.py` - 1h
5. `presentation/canvas/ui/dialogs/credential_manager_dialog.py` - 1h

### 2.2 PropertyDef Consolidation
**Priority**: MEDIUM | **Effort**: 3-5 hours | **Risk**: LOW

Create property constants files:
- `nodes/file/property_constants.py` (~80 lines)
- `nodes/llm/property_constants.py` (~120 lines)

Follow pattern from `nodes/browser/property_constants.py`.

### 2.3 Error Handler Migration (Browser Nodes)
**Priority**: MEDIUM | **Effort**: 4-5 hours | **Risk**: LOW

Apply @error_handler to browser nodes:
- 15-20 execute() methods
- 65-80 LOC savings

---

## Phase 3: UI Refactoring (Week 3-5)

### 3.1 Theme Violations Fix
**Priority**: HIGH | **Effort**: 4-5 hours | **Risk**: LOW

Fix 51 hardcoded colors:
- `controllers/menu_controller.py:78-94` - 8 colors
- `graph/node_widgets.py:156-183` - 15 colors
- `controllers/execution_controller.py:178-193` - duplicate
- Variable/subflow nodes - remaining

### 3.2 Signal/Slot Compliance
**Priority**: HIGH | **Effort**: 4-5 hours | **Risk**: LOW

Fix 104 violations:
- Replace 11 lambda connections with functools.partial
- Add @Slot decorators to 93+ handler methods

Key files:
- `unified_selector_dialog.py:1519-1528` - 6 lambdas
- `main_window.py:294+` - 70+ missing @Slot
- `event_bridge.py:250-426` - 16 missing @Slot

### 3.3 Duplicate Stylesheet Consolidation
**Priority**: MEDIUM | **Effort**: 8 hours | **Risk**: LOW

Create centralized styles:
- `theme_system/dialogs.py` - MessageBox, button styles
- `theme_system/inputs.py` - CheckBox, input field styles
- `theme_system/widgets.py` - Common widget styles

---

## Phase 4: HTTP Client Complete Migration (Week 4-6)

### 4.1 P2 Files (Fleet Dashboard)
**Priority**: MEDIUM | **Effort**: 3-4 hours | **Risk**: MEDIUM

Migrate `fleet_dashboard_manager.py`:
- 7x httpx.AsyncClient calls
- Lines: 289, 340, 390, 441, 500, 570, 625

### 4.2 P3 Files (Infrastructure & Security)
**Priority**: MEDIUM | **Effort**: 20+ hours | **Risk**: MEDIUM

Migrate remaining files:
- `infrastructure/security/oauth_server.py`
- `infrastructure/security/google_oauth.py`
- `triggers/implementations/rss_trigger.py`
- `triggers/implementations/google_trigger_base.py`
- `nodes/utility_nodes.py`
- `nodes/error_handling_nodes.py`

**Do NOT change**:
- `triggers/manager.py` - aiohttp.web server
- `triggers/implementations/sse_trigger.py` - long-lived SSE
- `utils/pooling/http_session_pool.py` - internal implementation

---

## Phase 5: Error Handler Complete Migration (Week 5-7)

### 5.1 Super Nodes Migration
**Priority**: MEDIUM | **Effort**: 3-4 hours

Apply @error_handler to:
- File super nodes (60+ handlers)
- Email super nodes (50+ handlers)
- Database super nodes (35+ handlers)

### 5.2 Remaining Nodes
**Priority**: LOW | **Effort**: 5-6 hours

Apply to remaining categories:
- Google nodes (40+ handlers)
- Desktop automation (45+ handlers)
- Control flow (35+ handlers)

---

## Phase 6: Test Coverage Foundation (Week 6-8)

### 6.1 Test Infrastructure
**Priority**: HIGH | **Effort**: 6-8 hours | **Risk**: LOW

Create `tests/conftest.py`:
- Shared fixtures (execution_context, mock_context)
- Pytest markers (unit, integration, slow, ui)
- Common test utilities

### 6.2 Critical Domain Tests
**Priority**: CRITICAL | **Effort**: 30 hours

Create tests for:
- `domain/aggregates/workflow.py` - 0 tests currently
- `domain/entities/base_node.py` - 0 tests
- `domain/events/bus.py` - 0 tests

### 6.3 Critical Application Tests
**Priority**: CRITICAL | **Effort**: 20 hours

Create tests for:
- `application/orchestrator/orchestrator_engine.py`
- `application/use_cases/execute_workflow.py`

---

## Phase 7: Large File Splitting (Week 7-9)

### 7.1 Orchestrator Engine Split
**Priority**: MEDIUM | **Effort**: 8-10 hours | **Risk**: MEDIUM

Split `orchestrator_engine.py` (1,027 lines) into:
- `engine/core.py` - main orchestration
- `engine/job_manager.py` - job lifecycle
- `engine/robot_pool.py` - robot management
- `engine/scheduler.py` - scheduling logic

### 7.2 UI Component Splitting
**Priority**: LOW | **Effort**: 20-30 hours | **Risk**: MEDIUM

Split large components:
- `node_widgets.py` (2,375 lines) → 4 modules
- `unified_selector_dialog.py` (2,192 lines) → 4 components
- `ui_explorer_dialog.py` (2,155 lines)
- `variable_picker.py` (2,135 lines)

---

## Phase 8: Cleanup & Documentation (Week 9-10)

### 8.1 Deprecated Code Removal
**Priority**: LOW | **Effort**: 4-6 hours | **Risk**: LOW

Remove deprecated stubs:
- `nodes/navigation_nodes.py` - stub file
- `nodes/interaction_nodes.py` - stub file
- `nodes/text_nodes.py` - stub file
- `nodes/browser_nodes.py` - stub file

### 8.2 Index File Updates
**Priority**: LOW | **Effort**: 2 hours

Update `_index.md` files:
- `nodes/_index.md` - fix deprecated references
- `visual_nodes/_index.md` - update node count
- `application/_index.md` - remove scheduling reference

### 8.3 Analysis File Archival
**Priority**: LOW | **Effort**: 1 hour

Move root analysis files to `.brain/analysis/`:
- All `*_ANALYSIS*.md` files
- All `*_AUDIT*.md` files
- All `*_INDEX.md` analysis files

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | LOW | HIGH | Comprehensive test suite before refactoring |
| Performance regression | LOW | MEDIUM | Benchmark before/after |
| Merge conflicts | MEDIUM | LOW | Small, focused PRs |
| Incomplete migration | MEDIUM | LOW | Track progress in checklist |

---

## Success Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Bare except clauses | 2,556 | <50 | Phase 2-5 |
| Hardcoded colors | 51 | 0 | Phase 3 |
| Lambda connections | 11 | 0 | Phase 3 |
| Missing @Slot | 93+ | 0 | Phase 3 |
| Raw httpx usage | 734 | 0 | Phase 2,4 |
| Test coverage | 1.9% | 70% | Phase 6+ |
| Max file size | 2,375 | <500 | Phase 7 |

---

## Parallel Execution Opportunities

These tasks can run in parallel:
1. **Week 1-2**: Security fix + @error_handler decorator + Config infrastructure (3 devs)
2. **Week 2-4**: HTTP P1 migration + PropertyDef consolidation + Theme violations (3 devs)
3. **Week 4-6**: HTTP P2-P3 migration + Signal/Slot fixes + Error handler migration (3 devs)

---

## Agent Assignments (for /implement-feature)

| Phase | Agent | Task |
|-------|-------|------|
| 1.1 | builder | Security config |
| 1.2 | builder | @error_handler decorator |
| 1.3 | architect | Config infrastructure design |
| 2.1 | integrations | HTTP client migration |
| 2.2 | refactor | PropertyDef consolidation |
| 3.1-3.3 | ui | Theme/Signal/Style fixes |
| 5.* | refactor | Error handler migration |
| 6.* | quality | Test suite creation |
| 7.* | architect + builder | File splitting |

---

## Approval Checklist

- [ ] Review Phase 1 scope (Security + Foundation)
- [ ] Allocate developer resources
- [ ] Set up progress tracking
- [ ] Approve execution start

**Ready to proceed?** Approve to begin Phase 1 execution.
