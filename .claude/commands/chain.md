---
description: |
  Enhanced agent chaining with smart classification, dynamic loops, dependencies, cost optimization, and predictive timing.
  Task types: implement, fix, refactor, research, extend, clone, test, docs, security, ui, integration
argument-hint: "<task_type> <description> [options]"

agent: architect
subtask: true
---

# Chain: $ARGUMENTS.task_type - $ARGUMENTS.description

**Enhanced Agent Chaining v2.0** | Reference: `.claude/rules/06-protocol.md`

---

## Auto-Detection

If task_type is `auto` or omitted, classify the task:

```
TASK CLASSIFICATION FOR: "$ARGUMENTS.description"

Analyze the request and classify into:
- Task Type: implement, fix, refactor, research, extend, clone, test, docs, security, ui, integration
- Complexity: TRIVIAL (1), SIMPLE (2), MODERATE (3), COMPLEX (4), EPIC (5)
- Estimated Duration: minutes
- Risk Level: LOW, MEDIUM, HIGH, CRITICAL
- Suggested Parallel: agents that can run together
- Confidence: 0.0-1.0

Classification Rules:
- "add", "create", "implement" → implement
- "bug", "fix", "error", "broken" → fix
- "clean", "refactor", "reorganize" → refactor
- "how", "research", "find", "compare" → research
- "extend", "enhance", "improve existing" → extend
- "copy", "clone", "similar to" → clone
- "test", "coverage", "verify" → test
- "document", "doc", "readme" → docs
- "security", "vulnerability", "auth" → security
- "ui", "interface", "widget", "dialog" → ui
- "api", "integration", "external" → integration

Complexity Scoring:
- TRIVIAL (1): Single line fix, config change, < 1 hour
- SIMPLE (2): Small feature, simple bug, 1-4 hours
- MODERATE (3): Medium feature, multiple files, 4-8 hours
- COMPLEX (4): Large feature, architecture changes, 8-24 hours
- EPIC (5): Multi-feature, breaking changes, 24+ hours

Output Format:
```
CLASSIFIED: implement
COMPLEXITY: MODERATE (3)
ESTIMATED: 45 minutes
RISK: MEDIUM
CONFIDENCE: 0.87
SUGGESTED PARALLEL: --parallel=ui
REASONING: "Contains 'add new' keyword, mentions 'node' category, references existing patterns"
```
```

---

## Options

| Option | Description |
|--------|-------------|
| `--parallel=<agents>` | Run agents in parallel (e.g., `security,docs,ui`) |
| `--priority=<level>` | Priority: `high`, `normal`, `low` |
| `--max-iterations=<n>` | Max loop iterations (default: 3) |
| `--timeout=<seconds>` | Agent timeout (default: 600s) |
| `--dry-run` | Preview chain without execution |
| `--skip-review` | Skip reviewer gate (not recommended) |
| `--cost-budget=<USD>` | Max cost limit (e.g., `5.00`) |
| `--max-time=<minutes>` | Max execution time |
| `--depends-on=<chains>` | Comma-separated chain dependencies |
| `--provides=<features>` | Comma-separated features this provides |
| `--smart-select=true` | Enable ML-based task classification |

---

## Task Type Chains

| Task | Chain | Exit |
|------|-------|------|
| implement | EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER | APPROVED |
| fix | EXPLORE → BUILDER → QUALITY → REVIEWER | APPROVED |
| refactor | EXPLORE → REFACTOR → QUALITY → REVIEWER | APPROVED |
| research | EXPLORE → RESEARCHER → APPROVAL | Human |
| extend | EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER | APPROVED |
| clone | EXPLORE → BUILDER → QUALITY → REVIEWER | APPROVED |
| test | EXPLORE → QUALITY → REVIEWER | APPROVED |
| docs | EXPLORE → DOCS → REVIEWER | APPROVED |
| security | EXPLORE → SECURITY-AUDITOR → REVIEWER | APPROVED |
| ui | EXPLORE → UI → QUALITY → REVIEWER | APPROVED |
| integration | EXPLORE → INTEGRATIONS → QUALITY → REVIEWER | APPROVED |

---

## Phase 1: EXPLORE (Parallel - 3 agents)

```
PARALLEL EXPLORE AGENTS LAUNCHING...

!Task(subagent_type="explore", model="haiku", prompt="CODE SEARCH: Find existing implementations, patterns, architecture for: $ARGUMENTS.description
Search: src/casare_rpa/ for similar code, patterns, modules
Return: file paths, class names, dependencies, existing patterns")

!Task(subagent_type="explore", model="haiku", prompt="TEST SEARCH: Find test patterns for: $ARGUMENTS.description
Search: tests/ for similar test structures, fixtures
Return: test file locations, fixture names, mocking patterns used")

!Task(subagent_type="explore", model="haiku", prompt="RULES SEARCH: Find relevant rules and docs for: $ARGUMENTS.description
Search: .claude/rules/, .brain/, docs/
Return: applicable rules, patterns to follow, gotchas, constraints")

WAIT FOR ALL EXPLORE AGENTS...
AGGREGATE FINDINGS...
```

---

## Phase 2: ARCHITECT (implement, extend only)

```
!Task(subagent_type="architect", model="sonnet", prompt="CREATE PLAN for: $ARGUMENTS.description

Task Type: $ARGUMENTS.task_type
Complexity: {from classification}
Estimated: {from classification}

Create plan in .claude/plans/chain-{timestamp}-{slug}.md:
1. Files to create/modify (with paths)
2. Agent assignments per file
3. Parallel execution opportunities
4. Risks and mitigation strategies
5. Test approach and fixtures needed
6. Dependencies to satisfy

Follow: .claude/rules/02-architecture.md, .brain/systemPatterns.md")

GATE: "Plan ready at .claude/plans/chain-{timestamp}.md. Approve to continue? (y/n)"
```

---

## Phase 3: BUILD (Task-specific)

### implement/extend → PARALLEL BUILD
```
!Task(subagent_type="builder", model="opus", prompt="IMPLEMENT: Domain/Application layer for $ARGUMENTS.description
Follow the approved plan. Use get_parameter() not self.config.get(). Add error handling.")

!Task(subagent_type="integrations", model="sonnet", prompt="IMPLEMENT: Infrastructure/API for $ARGUMENTS.description
Use UnifiedHttpClient. Add proper error handling.")

!Task(subagent_type="ui", model="sonnet", prompt="IMPLEMENT: Presentation/UI for $ARGUMENTS.description
Use THEME constants, no hex colors. Use functools.partial for signal captures.")

WAIT FOR BUILD AGENTS...
```

### fix → SINGLE BUILDER
```
!Task(subagent_type="builder", model="opus", prompt="FIX ROOT CAUSE: $ARGUMENTS.description
Minimal change only. Fix the bug, don't refactor. Add error handling.")
```

### refactor → SINGLE REFACTOR
```
!Task(subagent_type="refactor", model="opus", prompt="REFACTOR: $ARGUMENTS.description
Follow plan. Maintain existing behavior. Update tests if needed.")
```

### clone → SINGLE BUILDER
```
!Task(subagent_type="builder", model="opus", prompt="CLONE PATTERN: $ARGUMENTS.description
Follow existing patterns from explore phase. Maintain consistency.")
```

### security → SECURITY AUDITOR
```
!Task(subagent_type="security-auditor", model="opus", prompt="SECURITY AUDIT: $ARGUMENTS.description
Check: OWASP Top 10, hardcoded secrets, XSS, SQL injection, CSRF, auth bypass.")
```

### ui → UI SPECIALIST
```
!Task(subagent_type="ui", model="sonnet", prompt="IMPLEMENT UI: $ARGUMENTS.description
Use THEME constants only. Use @Slot() decorators. Use functools.partial for captures.")
```

### integration → INTEGRATIONS
```
!Task(subagent_type="integrations", model="sonnet", prompt="IMPLEMENT INTEGRATION: $ARGUMENTS.description
Use UnifiedHttpClient. Add retry logic. Handle errors gracefully.")
```

---

## Phase 4: QUALITY

```
!Task(subagent_type="quality", model="sonnet", prompt="QA CHECKS for: $ARGUMENTS.description

1. Run: pytest tests/affected/ -v --tb=short
2. Run: ruff check src/affected/
3. Run: mypy src/affected/ (if applicable)
4. Check for: unused imports, missing type hints

Report: PASS/FAIL with specific failures to fix.")
```

---

## Phase 5: REVIEWER (Dynamic Loop)

```
!Task(subagent_type="reviewer", model="sonnet", prompt="CODE REVIEW: $ARGUMENTS.description

Check:
- Error handling on all external calls (loguru)
- Type hints complete on public APIs
- No hardcoded colors (use THEME) or credentials
- Tests cover happy path + errors
- Follows existing patterns
- Domain purity maintained (no infra imports)

CLASSIFY ISSUES by SEVERITY:
- CRITICAL (5): Security vuln, data loss risk
- HIGH (4): Core functionality broken
- MEDIUM (3): Feature impaired
- LOW (2): Style, best practices
- COSMETIC (1): Formatting

OUTPUT: APPROVED or ISSUES with file:line:severity")
```

---

## Dynamic Loop Logic

### Issue Severity Routing

```
IF ISSUES FOUND:
  FOR EACH issue:
    CASE severity OF
      CRITICAL: ESCALATE immediately (no loops)
      HIGH: Max 1 iteration → BUILDER
      MEDIUM: Max 2 iterations → BUILDER
      LOW: Max 3 iterations → REFACTOR or auto-fix
      COSMETIC: Max 3 iterations → auto-fix

  LOOP_DECISION = {
    "can_continue": iteration < max_for_highest_severity,
    "action": determine_action(highest_severity),
    "auto_fix_available": count_auto_fixable(issues)
  }

  IF NOT can_continue:
    ESCALATE to human
  ELSE IF auto_fix_available > 0:
    APPLY auto-fixes for LOW/COSMETIC issues
    CONTINUE loop for remaining issues
  ELSE:
    CONTINUE to appropriate agent
```

### Loop Progress Display

```
═══════════════════════════════════════════════════════════════
  LOOP STATUS: Iteration {current}/{max}
  Task: $ARGUMENTS.description
───────────────────────────────────────────────────────────────
  Issues: CRITICAL: {c}  HIGH: {h}  MEDIUM: {m}  LOW: {l}  COSMETIC: {cos}
  Decision: {decision}
  Next Action: {agent}
  Auto-Fixable: {auto_fix_count} issues
═══════════════════════════════════════════════════════════════
```

---

## Cross-Chain Dependencies

### Dependency Declaration

```
IF --depends-on specified:
  DEPENDENCY_GRAPH = {
    "current_chain": {
      "depends_on": ARGUMENTS.depends_on.split(','),
      "provides": ARGUMENTS.provides.split(',') if --provides else []
    }
  }

  CHECK: All dependencies satisfied?
    IF NOT: WAIT or BLOCK with message
    IF YES: PROCEED with execution

  DETECT CONFLICTS:
    - File overwrite conflicts
    - API endpoint conflicts
    - Schema conflicts
    - Resource conflicts

  IF CONFLICTS FOUND:
    REPORT and REQUEST RESOLUTION
```

---

## Cost Tracking

### Cost Estimation

```
COST_MODEL = {
  "explore": {"tokens": 2000, "cost": 0.02},
  "architect": {"tokens": 4000, "cost": 0.08},
  "builder": {"tokens": 8000, "cost": 0.32},
  "quality": {"tokens": 3000, "cost": 0.03},
  "reviewer": {"tokens": 4000, "cost": 0.08},
}

ESTIMATED_COST = SUM(agent_costs) * iterations

IF --cost-budget specified AND ESTIMATED_COST > budget:
  WARN user and request confirmation
```

### Cost Optimization Suggestions

```
OPTIMIZATION_CHECK:
  IF cost > budget:
    SUGGEST:
      1. Use cheaper model for EXPLORE (haiku)
      2. Enable parallel execution
      3. Reduce context size
      4. Enable early termination for docs/test
```

### Cost Dashboard

```
═══════════════════════════════════════════════════════════════
  COST TRACKING
───────────────────────────────────────────────────────────────
  Estimated Total: ${estimated}
  Current Spend: ${current}

  By Agent:
    EXPLORE:   ${explore_cost}
    ARCHITECT: ${architect_cost}
    BUILDER:   ${builder_cost}
    QUALITY:   ${quality_cost}
    REVIEWER:  ${reviewer_cost}

  Budget Remaining: ${budget - current}
═══════════════════════════════════════════════════════════════
```

---

## Predictive Timing

### Time Estimation

```
COMPLEXITY_DURATION = {
  "TRIVIAL": 15,   # minutes
  "SIMPLE": 45,
  "MODERATE": 120,
  "COMPLEX": 300,
  "EPIC": 720
}

BASE_DURATION = COMPLEXITY_DURATION[complexity]
ESTIMATED_DURATION = BASE_DURATION * (1 + iteration_count * 0.5)

CONFIDENCE = {
  "TRIVIAL": 0.95,
  "SIMPLE": 0.85,
  "MODERATE": 0.75,
  "COMPLEX": 0.60,
  "EPIC": 0.40
}
```

### Milestone Tracking

```
TIMELINE:
  Phase 1: EXPLORE    {5 min}   ████████████░░░░░░░░░░░░░░░░░░
  Phase 2: ARCHITECT  {10 min}  ████████████████████████████░░░░
  Phase 3: BUILDER    {20 min}  ████████████████████████████████
  Phase 4: QUALITY    {7 min}   ████████████████████░░░░░░░░░░░
  Phase 5: REVIEWER   {3 min}   ████████████████░░░░░░░░░░░░░░░

  Total: {estimated} min (P50)
  Confidence: {confidence}%
  P90: {p90_estimate} min
```

---

## Phase 6: DOCS

```
!Task(subagent_type="docs", model="sonnet", prompt="UPDATE DOCS for: $ARGUMENTS.description

1. Update relevant _index.md files
2. Update .brain/context/current.md
3. Add docstrings where missing
4. Update CLAUDE.md if rules/patterns changed")
```

---

## Completion Report

```
═══════════════════════════════════════════════════════════════
  CHAIN COMPLETED
───────────────────────────────────────────────────────────────
  Task Type:    $ARGUMENTS.task_type
  Description:  $ARGUMENTS.description
  Complexity:   {complexity}
  Iterations:   {actual_iterations}
  Duration:     {actual_duration} min (estimated: {estimated})
  Cost:         ${actual_cost} (estimated: ${estimated_cost})
  Files:        {files_created} created, {files_modified} modified
  Tests:        {test_status}
  Review:       {review_status}

  Dependencies Satisfied: {dep_status}
  Conflicts Resolved: {conflict_count}
═══════════════════════════════════════════════════════════════
```

---

## Error Escalation

```
═══════════════════════════════════════════════════════════════
  [ERROR] CHAIN FAILED AFTER {max_iterations} ITERATIONS
───────────────────────────────────────────────────────────────
  Task: $ARGUMENTS.description

  Last Review: ISSUES REMAINING ({remaining_count})
  ┌──────────────────────────────────────────────────────────┐
  │ CRITICAL: {critical_issues}                             │
  │   {issue_details}                                        │
  │ HIGH: {high_issues}                                     │
  │   {issue_details}                                        │
  │ MEDIUM: {medium_issues}                                 │
  │   {issue_details}                                        │
  └──────────────────────────────────────────────────────────┘

  [ESCALATION] Human review required for:
  - {escalation_reasons}

  Suggested Actions:
  1. {suggestion_1}
  2. {suggestion_2}
═══════════════════════════════════════════════════════════════
```

---

## Quick Reference

### Minimal Usage
```bash
/chain auto "Add OAuth2 support for Google APIs"
```

### Full Usage
```bash
/chain implement "Add OAuth2 support for Google APIs" \
  --parallel=security,ui \
  --priority=high \
  --max-iterations=3 \
  --cost-budget=5.00 \
  --max-time=60 \
  --depends-on=base-http-client \
  --provides=oauth2-authentication \
  --smart-select=true
```

### Task Auto-Detection Keywords
- `add/create/new` → implement
- `bug/broken/error` → fix
- `clean/refactor` → refactor
- `research/find/how` → research
- `extend/improve/enhance` → extend
- `copy/clone/similar` → clone
- `test/verify` → test
- `document/readme` → docs
- `security/auth/vuln` → security
- `ui/widget/dialog` → ui
- `api/integration/external` → integration
