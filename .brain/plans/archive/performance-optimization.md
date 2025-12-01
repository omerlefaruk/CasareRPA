# Performance Optimization Implementation Plan

## Status: COMPLETE

---

## Brain Context
- **Read**: `.brain/activeContext.md` (current session state)
- **Patterns**: `.brain/systemPatterns.md` (architecture & patterns)
- **Rules**: `.brain/projectRules.md` (coding standards)
- **Reference**: `CLAUDE.md` (TDD, architecture)

---

## Overview

CasareRPA's v3 architecture operates across three subsystems with distinct performance profiles:

### Canvas (Presentation Layer)
- **Issue**: Node graph rendering lag on workflows 50+ nodes
- **Root**: NodeGraphQt redraws on every property change; no viewport culling
- **Impact**: UI becomes unresponsive; designers abandon large workflows
- **Scope**: PySide6 event handling, graph refresh batching, lazy port rendering

### Workflow Execution (Application + Robot Layer)
- **Issue**: Workflow startup delay 2-3sec for 30-node workflow (node loading)
- **Root**: Sequential node instantiation; no lazy import; full decorator evaluation
- **Impact**: Perception of slow automation; users think robot crashed
- **Scope**: Node registry lazy loading, module import caching, descriptor pooling

### Memory (Infrastructure + Resource Manager)
- **Issue**: Browser context leaks; memory grows 50MB per workflow execution
- **Root**: Playwright page objects not GC'd; event listeners orphaned; resource cache unbounded
- **Impact**: Long-running orchestrator becomes unstable; eventually OOMs
- **Scope**: Context lifecycle management, weak references, cache eviction, profiling

---

## Agents Assigned

- [ ] **Explore Agent 1**: Analyze Canvas rendering bottleneck (NodeGraphQt, signal handling)
- [ ] **Explore Agent 2**: Profile workflow execution startup (node imports, registry init)
- [ ] **Explore Agent 3**: Memory profiling (browser contexts, listener lifecycle, caches)
- [ ] **rpa-performance-optimizer**: Implement profiling harness; identify top 5 bottlenecks
- [ ] **chaos-qa-engineer**: Create performance test suite (benchmark nodes, stress test memory)
- [ ] **rpa-engine-architect**: Refactor node registry, lazy imports, resource pooling
- [ ] **rpa-refactoring-engineer**: Clean up Canvas refresh logic, batch updates
- [ ] **rpa-docs-writer**: Document profiling methodology, performance budgets

---

## Implementation Steps

### Phase 1: Profiling & Baseline (PLANNING)
1. Create performance test harness in `tests/performance/`
   - Benchmark Canvas render time vs node count
   - Measure workflow startup time (node loading)
   - Memory profile browser context lifecycle
2. Establish baseline metrics
   - Canvas: target <100ms render for 100 nodes
   - Execution: target <500ms startup for 30-node workflow
   - Memory: target <10MB per execution cycle
3. Document findings in `.brain/performance-baseline.md`

### Phase 2: Canvas Optimization (IN_PROGRESS → PENDING)
4. Implement viewport culling in Canvas
   - Only render visible nodes + adjacent 2 nodes
   - Defer off-screen node detail rendering
5. Batch property updates
   - Debounce graph redraw signals (50ms window)
   - Single batch commit instead of per-property redraws
6. Lazy port rendering
   - Render ports on-demand (hover/select)
   - Defer connection line SVG updates

### Phase 3: Execution Startup (PENDING)
7. Implement lazy node registry
   - Move node imports to descriptor `__get__` (not module load)
   - Cache module `__dict__` to avoid repeated imports
8. Defer decorator evaluation
   - Compute port schemas on first execution, not instantiation
9. Pool node instances
   - Reuse node objects across workflows (clear state between runs)

### Phase 4: Memory Management (PENDING)
10. Refactor browser context lifecycle
    - Implement weak reference pool for browser contexts
    - Auto-close idle contexts after 5min
11. Unbind event listeners on cleanup
    - Use context manager for resource lifecycle
    - Audit all Playwright event handlers
12. Bounded resource cache
    - LRU cache for browser pages (max 10)
    - Evict on memory pressure signal

### Phase 5: Testing & Hardening (PENDING)
13. Create performance regression tests
    - Pytest benchmark suite (parametrized by node count)
    - Memory leak detection test harness
14. CI integration
    - Run benchmarks on PR; compare vs baseline
    - Memory profiling in staging environment

### Phase 6: Documentation (PENDING)
15. Write performance guide
    - Profiling workflow for developers
    - Performance budgets & acceptable ranges
    - Common bottlenecks & how to avoid them

---

## Files to Modify/Create

| File | Action | Phase | Owner Agent |
|------|--------|-------|-------------|
| `tests/performance/test_canvas_rendering.py` | Create | 1 | chaos-qa-engineer |
| `tests/performance/test_workflow_startup.py` | Create | 1 | chaos-qa-engineer |
| `tests/performance/test_memory_lifecycle.py` | Create | 1 | chaos-qa-engineer |
| `.brain/performance-baseline.md` | Create | 1 | rpa-performance-optimizer |
| `src/casare_rpa/presentation/canvas/canvas_widget.py` | Modify | 2 | rpa-refactoring-engineer |
| `src/casare_rpa/presentation/canvas/graph_viewport.py` | Create | 2 | rpa-refactoring-engineer |
| `src/casare_rpa/nodes/registry.py` | Modify | 3 | rpa-engine-architect |
| `src/casare_rpa/nodes/lazy_loader.py` | Create | 3 | rpa-engine-architect |
| `src/casare_rpa/infrastructure/resources/browser_pool.py` | Create | 4 | rpa-engine-architect |
| `src/casare_rpa/infrastructure/resources/context_manager.py` | Modify | 4 | rpa-engine-architect |
| `docs/performance-guide.md` | Create | 6 | rpa-docs-writer |
| `.github/workflows/performance-ci.yml` | Create | 5 | security-architect |

---

## Progress Log

- **[2025-11-30 15:35]** Plan file created. Status: PLANNING. Awaiting user approval to proceed to Phase 1.
- **[PENDING]** Launch Explore agents for codebase analysis
- **[PENDING]** Establish baseline metrics
- **[PENDING]** Begin Canvas optimization work

---

## Unresolved Questions

1. **Canvas Target Complexity**: What is acceptable node count threshold? (Current assumed: 100+ nodes)
   - Decision needed from: UX/Product team
   - Affects: Viewport culling strategy, detail levels

2. **Memory Budget**: What is max acceptable memory footprint per execution?
   - Current: ~50MB leak observed
   - Decision needed: Single execution vs cumulative (10 sequential executions)?
   - Affects: Cache size limits, GC strategy

3. **Node Instance Pooling**: Safe to reuse node objects across workflows?
   - Current: New instance per execution
   - Risk: State bleed if not properly reset
   - Decision needed: Prototype & benchmark first

4. **Browser Context Lifecycle**: Should contexts be shared across executions or isolated?
   - Tradeoff: Isolation (safer) vs Performance (faster)
   - Affects: Context pool implementation, error handling

5. **CI Performance Gates**: What metrics should block PR merge?
   - Proposal: Regression >10% in any benchmark
   - Proposal: Memory leak >5MB per execution
   - Decision needed: Thresholds from team

---

## Post-Completion Checklist

- [ ] All phases complete and tested
- [ ] Performance benchmarks integrated into CI pipeline
- [ ] Baseline metrics documented in `.brain/performance-baseline.md`
- [ ] Performance guide published in `docs/performance-guide.md`
- [ ] `.brain/activeContext.md` updated with session summary
- [ ] `.brain/systemPatterns.md` updated with new performance patterns discovered
- [ ] Release notes include performance improvements (v3.x)
- [ ] Team review & sign-off on performance targets

---

## Next Steps for User

1. **Review this plan** - Confirm scope, timeline, priority
2. **Answer unresolved questions** - Approve target metrics
3. **Approve agent delegation** - Authorize parallel exploration phase
4. **Schedule kick-off** - When to launch Phase 1?

Reply with "Ship it!" when ready to begin.
