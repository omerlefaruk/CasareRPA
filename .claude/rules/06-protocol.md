---
description: Brain protocol and enhanced agent chaining v2.0
---

# Protocol & Chaining (Enhanced v2.0)

## Brain Protocol

### Brain Structure

| Directory | Purpose |
|-----------|---------|
| `.brain/context/` | Session state tracking |
| `.brain/decisions/` | Decision trees for common tasks |
| `.brain/docs/` | Long-lived documentation |

### Update Rules

- **Context Updates**: Update `.brain/context/current.md` at start and end of session
- **Decision Trees**: Document complex decisions in new decision tree files
- **System Patterns**: Add reusable patterns to `.brain/systemPatterns.md`

---

## Enhanced Agent Chaining

### Task Type to Chain Mapping

| Task | Chain | Exit |
|------|-------|------|
| **RESEARCH** | explorer → researcher | Human approval |
| **IMPLEMENT** | explorer → architect → builder → quality → reviewer | APPROVED |
| **REFACTOR** | explorer → refactor → quality → reviewer | APPROVED |
| **FIX** | explorer → builder → quality → reviewer | APPROVED |
| **EXTEND** | explorer → architect → builder → quality → reviewer | APPROVED |
| **TEST** | explorer → quality → reviewer | APPROVED |
| **DOCS** | explorer → docs → reviewer | APPROVED |
| **UI** | explorer → ui → quality → reviewer | APPROVED |
| **INTEGRATION** | explorer → integrations → quality → reviewer | APPROVED |
| **SECURITY** | explorer → security-auditor → reviewer | APPROVED |

**Note**: `explorer`, `refactor`, `integrations` are skills; others are agents.

---

## Enhanced Features (v2.0)

### 1. Smart Chain Selection

Auto-classify tasks when using `/chain auto`:

| Keyword Pattern | Task Type |
|-----------------|-----------|
| `add`, `create`, `implement`, `new` | implement |
| `bug`, `fix`, `error`, `broken` | fix |
| `clean`, `refactor`, `reorganize` | refactor |
| `how`, `research`, `find`, `compare` | research |
| `extend`, `enhance`, `improve existing` | extend |
| `copy`, `clone`, `similar to` | clone |
| `test`, `coverage`, `verify` | test |
| `document`, `doc`, `readme` | docs |
| `security`, `vulnerability`, `auth` | security |
| `ui`, `interface`, `widget`, `dialog` | ui |
| `api`, `integration`, `external` | integration |

**Complexity Levels**:
- TRIVIAL (1): Single line fix, config change, < 1 hour
- SIMPLE (2): Small feature, simple bug, 1-4 hours
- MODERATE (3): Medium feature, multiple files, 4-8 hours
- COMPLEX (4): Large feature, architecture changes, 8-24 hours
- EPIC (5): Multi-feature, breaking changes, 24+ hours

### 2. Dynamic Loop Adjustment

Severity-based iteration limits:

| Severity | Max Iterations | Route |
|----------|----------------|-------|
| CRITICAL (5) | 0 (immediate escalate) | Human |
| HIGH (4) | 1 | builder |
| MEDIUM (3) | 2 | builder |
| LOW (2) | 3 | refactor/auto-fix |
| COSMETIC (1) | 3 | auto-fix |

**Issue Categories**:
- SECURITY: Vulnerabilities, auth bypass
- CORRECTNESS: Logic bugs, core functionality
- PERFORMANCE: Speed, memory issues
- TYPE_SAFETY: Missing hints, wrong types
- ERROR_HANDLING: Missing try/except
- CODING_STANDARDS: Style, imports
- DOCUMENTATION: Missing docs
- ARCHITECTURE: DDD violations
- TESTING: Missing coverage

### 3. Cross-Chain Dependencies

```
--depends-on=chain1,chain2    # Chains that must complete first
--provides=feature1,feature2   # Features this chain provides
```

**Dependency Types**:
- BLOCKING: Must complete before dependent starts
- CONFLICTS: Cannot run in parallel
- PARALLEL: Safe to run together

**Conflict Detection**:
- File overwrite conflicts
- API endpoint conflicts
- Schema conflicts
- Resource conflicts

### 4. Cost Optimization

```
--cost-budget=5.00    # Max cost in USD
```

**Cost Model** (per 1M tokens):
| Model | Input | Output |
|-------|-------|--------|
| gpt-4 | $30 | $60 |
| gpt-4-turbo | $10 | $30 |
| claude-3-opus | $15 | $75 |
| claude-3-sonnet | $3 | $15 |
| haiku | $0.25 | $1.25 |

**Optimization Strategies**:
- Use haiku for EXPLORE
- Enable parallel execution
- Reduce context size
- Early termination for docs/test

### 5. Predictive Timing

```
--max-time=60    # Max execution time in minutes
```

**Duration Estimates** (by complexity):
| Complexity | Duration | Confidence |
|------------|----------|------------|
| TRIVIAL | 15 min | 95% |
| SIMPLE | 45 min | 85% |
| MODERATE | 120 min | 75% |
| COMPLEX | 300 min | 60% |
| EPIC | 720 min | 40% |

---

## Chain Command

```bash
/chain <task_type> "<description>" [options]

# Options:
--parallel=<agents>     # Run agents in parallel (e.g., security,docs,ui)
--priority=<level>      # high, normal, low
--max-iterations=<n>    # Override max loop iterations (default: 3)
--timeout=<seconds>     # Agent timeout (default: 600s)
--dry-run              # Preview without execution
--skip-review          # Skip reviewer gate (not recommended)
--cost-budget=<USD>    # Max cost limit
--max-time=<minutes>   # Max execution time
--depends-on=<chains>  # Chain dependencies
--provides=<features>  # Features provided
--smart-select=true    # Enable ML-based classification
```

---

## Recovery Strategies

| Issue Category | Route To |
|----------------|----------|
| Type safety | builder |
| Error handling | builder |
| Coding standards | refactor |
| Architecture | human |
| Security | security-auditor |

---

## Progress Format

```
[TIME] EXPLORE: Finding patterns...
[TIME] ARCHITECT: Designing...
[TIME] BUILDER: Implementing...
[TIME] REVIEWER: ISSUES (2) → Loop 1/3
[TIME] REVIEWER: APPROVED
```

---

## Completion Report

```
═══════════════════════════════════════════════════════════════
  CHAIN COMPLETED
───────────────────────────────────────────────────────────────
  Task Type:    {task_type}
  Description:  {description}
  Complexity:   {complexity}
  Iterations:   {iterations}
  Duration:     {actual} min (estimated: {estimated})
  Cost:         ${cost} (budget: ${budget})
  Files:        {created} created, {modified} modified
  Tests:        {test_status}
  Review:       {review_status}
═══════════════════════════════════════════════════════════════
```
