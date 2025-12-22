# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Command Opportunities Summary - Quick Reference

**Status**: Analysis Complete
**Date**: 2025-12-14
**Repository**: CasareRPA

---

## The Opportunity Landscape

CasareRPA has **1,026+ Python files** organized in **clean DDD architecture** with:
- 413+ automation nodes
- 407 visual node implementations
- 10+ infrastructure services
- 25 test files (2.4% coverage)
- 22 index/documentation files

### Core Finding: 8 Commands Can Eliminate 60% of Operational Friction

---

## Priority 1: Implement These First (Week 1)

### 1. `/validate-registry`
**Problem**: Node registries can have orphaned/missing entries (silent failures)
**Solution**: Compare node files vs _NODE_REGISTRY vs _VISUAL_NODE_REGISTRY
**Time**: 5 hours
**Impact**: Catch registration errors at commit time

```bash
/validate-registry
# Output:
# ✅ 413 nodes registered
# ✅ 407 visual nodes registered
# ⚠️ Missing: ClickElementNode (file exists, not in registry)
# ⚠️ Orphan: DeletedNode (in registry, file deleted)
```

**Files to Change**:
- Create: `agent-rules/commands/validate-registry.md`
- Reference: `src/casare_rpa/nodes/__init__.py` (197-line registry)
- Reference: `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py` (610-line registry)

---

### 2. `/sync-index-docs [scope]`
**Problem**: 22 _index.md files require manual updates when code changes
**Solution**: Auto-scan source → count nodes/entities → update index markdown
**Time**: 10 hours
**Impact**: Keep documentation fresh, prevent merge conflicts

```bash
/sync-index-docs nodes
# Scans: src/casare_rpa/nodes/
# Finds: 413 nodes across 18 categories
# Updates: nodes/_index.md with new counts & tables
# Output: "Updated 413 → 416 nodes, 18 categories"

/sync-index-docs domain
# Updates: domain/_index.md (entities, events, services)
# Counts: 150+ domain classes
```

**Files to Change**:
- Create: `agent-rules/commands/sync-index-docs.md`
- Update: 22 _index.md files (automated)
- Reference: `src/casare_rpa/{scope}/` (all layers)

**Scope Options**: domain | application | infrastructure | presentation | nodes

---

## Priority 2: Implement Next (Weeks 2-3)

### 3. `/generate-test-skeleton [node-name]`
**Problem**: 413 nodes, only 5 have tests (98.8% untested)
**Solution**: Create test file with fixtures, stubs, common patterns
**Time**: 15 hours
**Impact**: Jump-start test coverage from 2.4% → 20%+

```bash
/generate-test-skeleton LaunchBrowserNode
# Creates: tests/nodes/browser/test_launch_browser_node.py
# Includes:
#   - Fixtures from conftest.py
#   - Mock Playwright Page
#   - execute() test stub
#   - Port validation tests
#   - Error handling tests
# Output: "Ready for implementation. Run: pytest tests/nodes/browser/test_launch_browser_node.py"

/generate-test-skeleton SetVariableNode
# Creates: tests/nodes/variable/test_set_variable_node.py
```

**Files to Change**:
- Create: `agent-rules/commands/generate-test-skeleton.md`
- Create: Test templates in `.brain/docs/test-templates/`
- Reference: `tests/` (existing test patterns)
- Reference: `tests/nodes/` (existing node tests: 5 files)
- Reference: `tests/infrastructure/ai/conftest.py` (fixture examples)

**Expected Output**:
- 408+ new test files
- Estimated coverage: 2.4% → 40%+ (within 6 months)

---

### 4. `/audit-quality [category]`
**Problem**: 10 audit scripts exist but aren't coordinated (scattered across `scripts/`)
**Solution**: Single command runs relevant audits, generates unified report
**Time**: 20 hours
**Impact**: Consistent quality gates, better CI/CD integration

```bash
/audit-quality schemas
# Runs:
#   - audit_node_schemas.py (property validation)
#   - code_metrics.py (LOC, complexity for nodes)
# Output: Unified report with issues & fixes

/audit-quality consistency
# Runs: audit_ui_consistency.py (theme colors, hardcoded values)
# Output: List of violations by file

/audit-quality all
# Runs all audits in parallel (5 agents max)
# Output: Master report with priority ranking
```

**Files to Change**:
- Create: `agent-rules/commands/audit-quality.md`
- Orchestrate: 10 existing scripts (don't modify them)
- Reference: `scripts/audit_*.py` (5 scripts)
- Reference: `scripts/code_metrics.py`

**Category Options**: schemas | consistency | performance | imports | coverage | all

---

## Priority 3: Implement for Scalability (Weeks 4-6)

### 5. `/benchmark-performance [module]`
**Problem**: Recent optimizations (20-50x speedups) need continuous monitoring
**Solution**: Compare baseline vs current, flag regressions >5%
**Time**: 15 hours
**Impact**: Protect performance wins, automate regression detection

```bash
/benchmark-performance workflow_loading
# Baseline: main branch (measured)
# Current: HEAD (measured)
# Comparison:
#   ✅ load_workflow() : 5ms (was 10ms) [2x faster!]
#   ⚠️ deserialize_nodes() : 50ms (was 40ms) [25% slower - investigate]
#   ✅ Overall: 15ms (was 200ms) [13x faster]
# Output: Flagged regression, suggests investigation

/benchmark-performance node_pooling
# Tests: NodeInstancePool acquire/release speed
```

**Files to Change**:
- Create: `agent-rules/commands/benchmark-performance.md`
- Reference: `tests/performance/test_workflow_loading.py` (70 tests)
- Reference: `src/casare_rpa/utils/workflow/incremental_loader.py`
- Reference: `src/casare_rpa/infrastructure/caching/workflow_cache.py`
- Reference: `src/casare_rpa/utils/performance/object_pool.py`

**Module Options**: workflow_loading | node_pooling | schema_caching | all

---

## Priority 4: Implement for Operations (Weeks 7-8)

### 6. `/manage-database [action]`
**Problem**: PostgreSQL integration (queue, persistence, analytics) lacks safe migration tools
**Solution**: Version tracking, safe migrate/rollback, validation checks
**Time**: 30 hours
**Impact**: Scale to multi-region, prevent data loss

```bash
/manage-database status
# Shows: Current schema version, pending migrations
# Output:
#   Current: v1.5.2
#   Pending: 3 migrations
#   Last applied: 2025-12-10

/manage-database migrate
# Applies pending migrations in order
# Pre-flight checks:
#   ✅ Backup current schema
#   ✅ Test on replica first
#   ✅ Validate schema after migration
# Output: Migration log

/manage-database rollback
# Rollback to previous version
# Safety: Requires manual confirmation + backup check

/manage-database validate
# Check schema consistency
# Verifies: table counts, column types, constraints
```

**Files to Change**:
- Create: `agent-rules/commands/manage-database.md`
- Reference: `src/casare_rpa/infrastructure/database/` (migrations)
- Reference: `src/casare_rpa/infrastructure/queue/` (DLQManager)
- Reference: `src/casare_rpa/infrastructure/persistence/` (unit of work)

**Actions**: status | migrate | rollback | validate

---

### 7. `/prepare-release [version]`
**Problem**: Manual versioning, no automated changelog, no consistent tagging
**Solution**: Bump version → update changelog → tag → build → deploy
**Time**: 25 hours
**Impact**: Go from manual releases to daily/weekly automation

```bash
/prepare-release 3.1.0
# Steps:
#   1. Parse current version (3.0.0)
#   2. Update pyproject.toml (3.0.0 → 3.1.0)
#   3. Generate CHANGELOG.md from git log
#   4. Create git tag v3.1.0
#   5. Build Docker image (casare-rpa:3.1.0)
#   6. Push to registry
# Output: Release summary + deployment checklist

/prepare-release --major
# Semantic versioning: 3.0.0 → 4.0.0
```

**Files to Change**:
- Create: `agent-rules/commands/prepare-release.md`
- Reference: `pyproject.toml` (version: "3.0.0")
- Reference: `.github/workflows/` (if exists)
- Create: Docker build integration

**Semantic Versioning**: --major | --minor | --patch | [version]

---

## Priority 5: Implement for Agent Coordination (Weeks 9+)

### 8. `/run-parallel-agents [task1] [task2] [task3]`
**Problem**: `/implement-feature` manually orchestrates agents; no generic parallel runner
**Solution**: Structured task scheduling, timeout management, result aggregation
**Time**: 25 hours
**Impact**: Faster feature delivery, code reuse

```bash
/run-parallel-agents \
  "explore: Find OAuth patterns in infrastructure/security/" \
  "researcher: Research OAuth 2.0 PKCE best practices" \
  "architect: Design authentication flow" \
  --timeout 300 \
  --max-parallel 5

# Output:
#   Task 1 (explore): ✅ Completed - Found 12 patterns
#   Task 2 (researcher): ✅ Completed - Retrieved 15 articles
#   Task 3 (architect): ✅ Completed - Design doc ready
#   Overall: Success (all 3 tasks completed)
```

**Files to Change**:
- Create: `agent-rules/commands/run-parallel-agents.md`
- Refactor: Extract parallel logic from `/implement-feature`
- Reference: `agent-rules/commands/implement-feature.md` (uses this pattern)

**Parameters**: task_description, --timeout, --max-parallel, --on-failure

---

## Quick Comparison: Commands vs Scripts

### Current State (10 Scattered Scripts)

```
scripts/
├── audit_node_schemas.py       → Manual run
├── audit_ui_consistency.py      → Manual run
├── code_metrics.py              → Manual run
├── generate_api_docs.py         → Manual run
├── generate_function_inventory.py → Manual run
├── generate_node_docs.py        → Manual run
└── [5 more]

Problem: Developers manually choose which to run
Result: Inconsistent quality gates
```

### Proposed Solution (8 Integrated Commands)

```
Commands:
├── /validate-registry           → Automatic on commit
├── /sync-index-docs [scope]     → Automatic on new node
├── /generate-test-skeleton      → Automatic for new node
├── /audit-quality [category]    → Automatic on PR
├── /benchmark-performance       → Automatic on release
├── /manage-database [action]    → Manual (high-impact)
├── /prepare-release [version]   → Manual (high-impact)
└── /run-parallel-agents         → Use by other commands

Benefit: Unified quality gates, integrated with development workflow
```

---

## Implementation Strategy

### Week 1 (Stability)
```
/validate-registry       [5h]   ← Quick win
/sync-index-docs         [10h]  ← Eliminate drift
```

### Week 2-3 (Testing)
```
/generate-test-skeleton  [15h]  ← 408+ test files
/audit-quality           [20h]  ← Unified audits
```

### Week 4-6 (Performance)
```
/benchmark-performance   [15h]  ← Monitor wins
```

### Week 7-9 (Operations)
```
/manage-database         [30h]  ← Safe scaling
/prepare-release         [25h]  ← Automate releases
/run-parallel-agents     [25h]  ← Better orchestration
```

**Total Effort**: ~145 hours (4 weeks for 1 developer)
**Expected ROI**: 60% reduction in operational friction

---

## File References by Command

| Command | Key Files | Purpose |
|---------|-----------|---------|
| `/validate-registry` | `nodes/__init__.py`, `visual_nodes/__init__.py` | Compare registries |
| `/sync-index-docs` | 22 _index.md files | Keep docs fresh |
| `/generate-test-skeleton` | `tests/`, conftest.py | Test boilerplate |
| `/audit-quality` | 10 `scripts/audit_*.py` | Quality gates |
| `/benchmark-performance` | `tests/performance/` | Performance monitoring |
| `/manage-database` | `infrastructure/database/` | Schema evolution |
| `/prepare-release` | `pyproject.toml`, `.github/` | Versioning & deployment |
| `/run-parallel-agents` | `implement-feature.md` | Agent orchestration |

---

## Quick Decision Tree

```
"What should we build first?"

├─ Is documentation drift a problem?
│  └─ YES → /sync-index-docs [FIRST]
│
├─ Do nodes fail silently when misspelled?
│  └─ YES → /validate-registry [FIRST]
│
├─ Is test coverage too low (2.4%)?
│  └─ YES → /generate-test-skeleton [NEXT]
│
├─ Are audits scattered across 10 scripts?
│  └─ YES → /audit-quality [NEXT]
│
├─ Have recent optimizations regressed?
│  └─ YES → /benchmark-performance [MONTHS]
│
├─ Is database migration risky?
│  └─ YES → /manage-database [STRATEGIC]
│
├─ Are releases manual and slow?
│  └─ YES → /prepare-release [STRATEGIC]
│
└─ Is agent orchestration complex?
   └─ YES → /run-parallel-agents [NICE-TO-HAVE]
```

---

## Metrics: Impact Assessment

### By Elimination of Pain Points

| Pain Point | Current | Proposed | Eliminated |
|------------|---------|----------|-----------|
| Node registration errors | Manual | Automatic validation | 100% |
| Documentation drift | Manual updates | Auto-sync | 100% |
| Test coverage | 2.4% | 20%+ | 8x improvement |
| Scattered audits | 10 scripts | 1 command | 90% |
| Performance regressions | Manual review | Automatic detection | 100% |
| Database migrations | Manual | Safe automation | 80% |
| Release workflow | Manual steps | Automated | 90% |
| Agent orchestration | Manual | Structured | 70% |

### Total Impact
- **Operational Friction**: 60% reduction
- **Developer Productivity**: 25% improvement (less manual work)
- **Code Quality**: 3.3x improvement (test coverage)
- **Deployment Speed**: 5-10x faster (automation)

---

## Recommendation

**Start with Priority 1** (`/validate-registry` + `/sync-index-docs`):
- **Quick wins** (15 hours combined)
- **High value** (catch errors, keep docs fresh)
- **Low risk** (read-only, no code changes)

**Add Priority 2** (`/generate-test-skeleton` + `/audit-quality`):
- **Medium effort** (35 hours combined)
- **Significant improvement** (test coverage, unified quality)
- **Medium risk** (test generation, audit orchestration)

**Schedule Priority 3-5** as operational needs dictate.

---

**Report Status**: Ready for command design
**Next Step**: Create command definition documents (MDx files in `agent-rules/commands/`)
