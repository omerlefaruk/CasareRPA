# Agent Chaining Master Plan

**Created**: 2025-12-25 | **Version**: 1.0 | **Status**: Active

## Executive Summary

This plan defines the automatic agent chaining system for CasareRPA development. It provides:
1. **Task Type Classification** - How to categorize work requests
2. **Agent Chain Templates** - Predefined chains for each task type
3. **Loop Recovery Logic** - How to handle errors and iterate
4. **Automation Commands** - CLI commands for triggering chains

## 1. Task Classification System

### Classification Algorithm

```
Input: User Request
       ↓
Classify Intent:
  - "Create/Make/Add/Implement" → IMPLEMENT
  - "Fix/Repair/Debug/Resolve" → FIX
  - "Research/Investigate/Analyze" → RESEARCH
  - "Refactor/Clean/Optimize" → REFACTOR
  - "Extend/Enhance/Add to" → EXTEND
  - "Clone/Duplicate/Copy" → CLONE
  - "Test/Verify/Check" → TEST
  - "Document/Write docs" → DOCS
  - "UI/Widget/Style" → UI
  - "Integrate/Connect/API" → INTEGRATION
  - "Security/Audit/Review" → SECURITY
       ↓
Determine Scope:
  - Files count, complexity, impact areas
       ↓
Select Chain:
  - Based on task type + scope
       ↓
Execute Chain:
  - Run agents in sequence with parallel where allowed
  - Handle loops automatically
```

### Intent Keywords Mapping

| Keyword Category | Keywords | Task Type |
|-----------------|----------|-----------|
| **Creation** | create, make, add, implement, build, develop | IMPLEMENT |
| **Repair** | fix, repair, debug, resolve, solve, correct | FIX |
| **Investigation** | research, investigate, analyze, explore, understand | RESEARCH |
| **Improvement** | refactor, clean, optimize, improve, enhance, modernize | REFACTOR |
| **Addition** | extend, enhance, add to, augment, expand | EXTEND |
| **Duplication** | clone, duplicate, copy, replicate | CLONE |
| **Verification** | test, verify, check, validate, ensure | TEST |
| **Documentation** | document, write docs, generate docs, update docs | DOCS |
| **Interface** | ui, widget, style, design, layout, component | UI |
| **Integration** | integrate, connect, api, service, external | INTEGRATION |
| **Security** | security, audit, review, scan, check vulnerabilities | SECURITY |

## 2. Agent Chain Templates

### Template 1: IMPLEMENT

**Use For**: New features, components, nodes, endpoints

```yaml
chain_name: "IMPLEMENT"
agents:
  - name: "explore"
    timeout: 300  # 5 minutes
    parallel_with: ["docs", "security"]

  - name: "architect"
    timeout: 600  # 10 minutes
    depends_on: ["explore"]

  - name: "builder"
    timeout: 1800  # 30 minutes
    depends_on: ["architect"]

  - name: "quality"
    timeout: 900  # 15 minutes
    depends_on: ["builder"]
    parallel_with: ["docs", "security"]

  - name: "reviewer"
    timeout: 600  # 10 minutes
    depends_on: ["quality"]

loop:
  max_iterations: 3
  trigger: "reviewer.issues"
  recovery:
    - agent: "builder"
      instruction_template: "Fix the following issues: {issues}"
    - agent: "quality"
      instruction_template: "Re-run tests after fixes: {test_scope}"

output_files:
  - "{component}.py"
  - "tests/{category}/test_{component}.py"
  - ".brain/plans/{component}-design.md"
```

### Template 2: FIX

**Use For**: Bug fixes, error resolution, crash repairs

```yaml
chain_name: "FIX"
agents:
  - name: "explore"
    timeout: 300  # 5 minutes
    goal: "Find bug location and root cause"

  - name: "builder"
    timeout: 900  # 15 minutes
    goal: "Implement fix with error handling"

  - name: "quality"
    timeout: 600  # 10 minutes
    goal: "Verify fix and run regression tests"

  - name: "reviewer"
    timeout: 600  # 10 minutes
    goal: "Review fix correctness"

loop:
  max_iterations: 3
  trigger: "reviewer.issues"
  recovery:
    - agent: "builder"
      instruction_template: "Address review comments: {issues}"

output_files:
  - "fix_{bug_id}.py" (if new file)
  - "tests/{category}/test_{bug_scenario}.py"
```

### Template 3: RESEARCH

**Use For**: Technical investigation, pattern research, feasibility studies

```yaml
chain_name: "RESEARCH"
agents:
  - name: "explore"
    timeout: 300  # 5 minutes
    goal: "Find existing patterns in codebase"

  - name: "researcher"
    timeout: 600  # 10 minutes
    goal: "Deep dive and external research"

loop:
  type: "none"  # Research doesn't loop automatically
  human_approval: true

output_files:
  - ".brain/research/{topic}-findings.md"
  - ".brain/plans/{topic}-recommendations.md"
```

### Template 4: REFACTOR

**Use For**: Code cleanup, pattern migration, technical debt reduction

```yaml
chain_name: "REFACTOR"
agents:
  - name: "explore"
    timeout: 300  # 5 minutes
    goal: "Understand current implementation"

  - name: "refactor"
    timeout: 1200  # 20 minutes
    goal: "Apply refactoring while preserving behavior"

  - name: "quality"
    timeout: 600  # 10 minutes
    goal: "Verify all tests pass"

  - name: "reviewer"
    timeout: 600  # 10 minutes
    goal: "Verify behavior preserved"

loop:
  max_iterations: 2
  trigger: "reviewer.issues"
  recovery:
    - agent: "refactor"
      instruction_template: "Fix refactoring issues: {issues}"

output_files:
  - "Refactoring summary in PR description"
  - ".brain/decisions/refactor-{timestamp}.md"
```

### Template 5: EXTEND

**Use For**: Adding features to existing components

```yaml
chain_name: "EXTEND"
agents:
  - name: "explore"
    timeout: 300
    goal: "Understand existing implementation"

  - name: "architect"
    timeout: 600
    goal: "Design extension approach"

  - name: "builder"
    timeout: 1200  # 20 minutes
    goal: "Implement extension"

  - name: "quality"
    timeout: 600
    goal: "Test extension"

  - name: "reviewer"
    timeout: 600
    goal: "Review extension"

loop:
  max_iterations: 3
  trigger: "reviewer.issues"
  recovery:
    - agent: "builder"
      instruction_template: "Fix extension issues: {issues}"
```

### Template 6: CLONE

**Use For**: Duplicating patterns to create new components

```yaml
chain_name: "CLONE"
agents:
  - name: "explore"
    timeout: 300
    goal: "Find source pattern to clone"

  - name: "builder"
    timeout: 1200
    goal: "Clone and adapt pattern"

  - name: "quality"
    timeout: 600
    goal: "Test cloned component"

  - name: "reviewer"
    timeout: 600
    goal: "Review clone"

loop:
  max_iterations: 2
  trigger: "reviewer.issues"
  recovery:
    - agent: "builder"
      instruction_template: "Fix clone issues: {issues}"
```

### Template 7: TEST

**Use For**: Adding tests, test coverage, verification

```yaml
chain_name: "TEST"
agents:
  - name: "explore"
    timeout: 300
    goal: "Understand component under test"

  - name: "quality"
    timeout: 900  # 15 minutes
    goal: "Create comprehensive tests"

  - name: "reviewer"
    timeout: 600
    goal: "Review test coverage"

loop:
  max_iterations: 2
  trigger: "reviewer.issues"
  recovery:
    - agent: "quality"
      instruction_template: "Add missing tests: {issues}"
```

### Template 8: DOCS

**Use For**: Documentation updates, API docs, guides

```yaml
chain_name: "DOCS"
agents:
  - name: "explore"
    timeout: 300
    goal: "Find relevant code to document"

  - name: "docs"
    timeout: 600
    goal: "Write documentation"

  - name: "reviewer"
    timeout: 600
    goal: "Review documentation"

loop:
  max_iterations: 2
  trigger: "reviewer.issues"
  recovery:
    - agent: "docs"
      instruction_template: "Update docs: {issues}"
```

### Template 9: UI

**Use For**: UI components, widgets, styling

```yaml
chain_name: "UI"
agents:
  - name: "explore"
    timeout: 300
    goal: "Find similar UI patterns"

  - name: "ui"
    timeout: 1200
    goal: "Implement UI component"

  - name: "quality"
    timeout: 600
    goal: "Test UI functionality"

  - name: "reviewer"
    timeout: 600
    goal: "Review UI implementation"

loop:
  max_iterations: 3
  trigger: "reviewer.issues"
  recovery:
    - agent: "ui"
      instruction_template: "Fix UI issues: {issues}"
```

### Template 10: INTEGRATION

**Use For**: External API integration, service connection

```yaml
chain_name: "INTEGRATION"
agents:
  - name: "explore"
    timeout: 300
    goal: "Find existing integration patterns"

  - name: "integrations"
    timeout: 1200
    goal: "Implement integration"

  - name: "quality"
    timeout: 600
    goal: "Test integration"

  - name: "reviewer"
    timeout: 600
    goal: "Review integration"

loop:
  max_iterations: 3
  trigger: "reviewer.issues"
  recovery:
    - agent: "integrations"
      instruction_template: "Fix integration issues: {issues}"
```

### Template 11: SECURITY

**Use For**: Security reviews, vulnerability assessment

```yaml
chain_name: "SECURITY"
agents:
  - name: "explore"
    timeout: 300
    goal: "Find security-relevant code"

  - name: "security-auditor"
    timeout: 900
    goal: "Identify security issues"

  - name: "reviewer"
    timeout: 600
    goal: "Review security findings"

loop:
  max_iterations: 2
  trigger: "reviewer.issues"
  recovery:
    - agent: "security-auditor"
      instruction_template: "Address security concerns: {issues}"
```

## 3. Loop Recovery Logic

### Recovery State Machine

```
                    ┌─────────────────┐
                    │  AGENT COMPLETE │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   REVIEWER?     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │ APPROVED  │  │  ISSUES   │  │  ERROR    │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐  ┌──────────────┐  ┌──────────────┐
        │ CHAIN   │  │ CHECK ITER   │  │ ERROR TYPE   │
        │ DONE    │  │ < MAX?       │  │ ANALYSIS     │
        └─────────┘  └──────┬───────┘  └──────┬───────┘
                            │                 │
              ┌─────────────┴─────────────┐   │
              │                           │   │
        ┌─────▼─────┐               ┌─────▼─────┐
        │ YES (Loop)│               │ NO (Fail) │
        └─────┬─────┘               └─────┬─────┘
              │                           │
              ▼                           ▼
        ┌──────────────┐           ┌──────────────┐
        │ CATEGORIZE   │           │ ESCALATE     │
        │ ISSUES       │           │ TO HUMAN     │
        └──────┬───────┘           └──────────────┘
               │
        ┌──────┴──────┬───────────────────────────┐
        │              │                           │
   ┌────▼────┐   ┌────▼────┐               ┌──────▼──────┐
   │ TYPE    │   │ LOGIC   │               │ ESCALATE    │
   │ SAFETY  │   │ ERRORS  │               │ (Complex)   │
   └────┬────┘   └────┬────┘               └─────────────┘
        │              │
        ▼              ▼
   ┌─────────┐   ┌─────────┐
   │ BUILDER │   │ARCHITECT│
   │ (Fix)   │   │ (Review)│
   └─────────┘   └─────────┘
```

### Issue Categorization

```python
def categorize_issues(issues: List[Issue]) -> IssueCategory:
    categories = {
        "type_safety": [],
        "error_handling": [],
        "coding_standards": [],
        "logic_errors": [],
        "performance": [],
        "security": [],
        "documentation": [],
        "architecture": [],
    }

    for issue in issues:
        if "type" in issue.description.lower() or "hint" in issue.description.lower():
            categories["type_safety"].append(issue)
        elif "error" in issue.description.lower() or "exception" in issue.description.lower():
            categories["error_handling"].append(issue)
        elif "style" in issue.description.lower() or "convention" in issue.description.lower():
            categories["coding_standards"].append(issue)
        elif "logic" in issue.description.lower() or "bug" in issue.description.lower():
            categories["logic_errors"].append(issue)
        elif "performance" in issue.description.lower() or "slow" in issue.description.lower():
            categories["performance"].append(issue)
        elif "security" in issue.description.lower() or "vulnerab" in issue.description.lower():
            categories["security"].append(issue)
        elif "doc" in issue.description.lower():
            categories["documentation"].append(issue)
        elif "design" in issue.description.lower() or "architect" in issue.description.lower():
            categories["architecture"].append(issue)

    return IssueCategory(categories)
```

### Recovery Agent Selection

```python
def select_recovery_agent(category: IssueCategory) -> RecoveryAction:
    # Priority order: logic errors first (affect correctness)
    if category.logic_errors:
        return RecoveryAction(
            agent="architect",
            instruction=f"Review logic design due to: {len(category.logic_errors)} logic errors"
        )

    if category.security:
        return RecoveryAction(
            agent="security-auditor",
            instruction=f"Address security concerns: {len(category.security)} issues"
        )

    if category.type_safety:
        return RecoveryAction(
            agent="builder",
            instruction=f"Fix type issues: {len(category.type_safety)} type errors"
        )

    if category.error_handling:
        return RecoveryAction(
            agent="builder",
            instruction=f"Add error handling: {len(category.error_handling)} missing handlers"
        )

    if category.coding_standards:
        return RecoveryAction(
            agent="refactor",
            instruction=f"Apply coding standards: {len(category.coding_standards)} violations"
        )

    if category.performance:
        return RecoveryAction(
            agent="refactor",
            instruction=f"Optimize performance: {len(category.performance)} issues"
        )

    if category.architecture:
        return RecoveryAction(
            agent="architect",
            instruction=f"Review architecture: {len(category.architecture)} concerns"
        )

    # Default: return to builder for any other issues
    return RecoveryAction(
        agent="builder",
        instruction=f"Fix remaining issues: {sum(len(c) for c in category.values())} total"
    )
```

## 4. Automation Commands

### Command Format

```bash
# Basic syntax
/chain <task-type> "<description>" [options]

# Examples
/chain implement "Add OAuth2 support for Google APIs"
/chain fix "Resolve null pointer in workflow loader"
/chain research "AI integration patterns for RPA"
/chain refactor "Clean up legacy HTTP client code"
```

### Command Options

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `--parallel` | `-p` | Agents to run in parallel | None |
| `--priority` | `-pr` | Priority level (high, normal, low) | normal |
| `--max-iterations` | `-m` | Maximum loop iterations | 3 |
| `--timeout` | `-t` | Agent timeout in seconds | varies |
| `--dry-run` | `-d` | Preview without execution | false |
| `--skip-review` | `-s` | Skip reviewer (not recommended) | false |
| `--output` | `-o` | Output format (text, json, markdown) | text |

### Parallel Execution Examples

```bash
# Run docs and security in parallel with main chain
/chain implement "New HTTP node" --parallel=docs,security

# High priority with extended timeout
/chain fix "Critical bug in executor" --priority=high --timeout=900

# Dry run to preview chain
/chain implement "Feature X" --dry-run

# Extended loop for complex refactoring
/chain refactor "Major architectural change" --max-iterations=5
```

### Chain Status Command

```bash
# Check running chains
/chain status

# Check specific chain
/chain status <chain-id>

# Kill running chain
/chain kill <chain-id>

# List recent chains
/chain history
```

## 5. Progress Tracking

### Status Output Format

```
══════════════════════════════════════════════════════════════
  CHAIN STATUS: IMPLEMENT - ClickElementNode
══════════════════════════════════════════════════════════════

Started: 2025-12-25 03:10:00 UTC
Duration: 32 minutes
Iteration: 1/3

Progress:
┌────────────────────────────────────────────────────────────┐
│ [✓] EXPLORE    ████████████████████████████████  100% (3m) │
│ [✓] ARCHITECT  ████████████████████████████████  100% (8m) │
│ [✓] BUILDER    ████████████████████████████████  100% (18m)│
│ [ ] QUALITY    ████████████░░░░░░░░░░░░░░░░░░   67% (10m) │
│ [ ] REVIEWER   Waiting for QUALITY...                    │
└────────────────────────────────────────────────────────────┘

Current Agent Output:
[QUALITY] Running pytest tests/nodes/browser/test_click.py...
[QUALITY] ✓ test_click_success - PASSED
[QUALITY] ✓ test_click_not_found - PASSED
[QUALITY] ✓ test_click_disabled - PASSED
[QUALITY] ✗ test_click_animation - FAILED (timing issue)

Recent Events:
[03:15] EXPLORE complete - Found 5 similar patterns
[03:23] ARCHITECT complete - Design saved to .brain/plans/click-node.md
[03:41] BUILDER complete - 3 files created
[03:41] QUALITY started - Running 6 tests
[03:47] QUALITY: 5/6 tests passed, 1 failing
```

### Loop Detection Message

```
[03:50] REVIEWER: ISSUES FOUND (3)
  1. Line 89: Missing error handling (HIGH)
  2. Line 156: Type hint should be Optional[str] (MEDIUM)
  3. Line 201: Add docstring (LOW)

[03:50] → Loop 1/3: Returning to BUILDER
  Recovery Strategy: Fix type safety and error handling issues

Progress:
┌────────────────────────────────────────────────────────────┐
│ Iteration 1/3 (In Progress)                                │
│ [✓] EXPLORE → [✓] ARCHITECT → [✓] BUILDER → [✓] QUALITY   │
│                                      ↗              ↘       │
│                            [LOOP 1] → BUILDER → QUALITY    │
│                                      ↗              ↘       │
│                            [LOOP 2] → BUILDER → QUALITY    │
│                                      ↗              ↘       │
│                            [LOOP 3] → BUILDER → QUALITY    │
│                                      ↗              ↘       │
│                                          REVIEWER (APPROVED│
└────────────────────────────────────────────────────────────┘
```

## 6. Integration Points

### OpenCode Integration

```json
{
  "chain_commands": {
    "implement": {
      "agent_sequence": ["explore", "architect", "builder", "quality", "reviewer"],
      "loop_condition": "reviewer.issues",
      "max_iterations": 3
    },
    "fix": {
      "agent_sequence": ["explore", "builder", "quality", "reviewer"],
      "loop_condition": "reviewer.issues",
      "max_iterations": 3
    }
  }
}
```

### MCP Tool Integration

```python
# Automatic chain trigger via MCP
def trigger_chain(task_type: str, description: str, options: dict):
    chain = load_chain_template(task_type)
    return execute_chain(chain, description, options)
```

### Git Integration

```bash
# Automatic chain trigger on PR
/chain implement "Feature X" --pr=123

# Link chain to PR
/chain link <chain-id> <pr-number>
```

## 7. Best Practices

### When to Use Each Chain

| Scenario | Recommended Chain | Rationale |
|----------|-------------------|-----------|
| New browser node | IMPLEMENT | Full design + test + review |
| Fix click selector bug | FIX | Focused on root cause |
| Research AI integration | RESEARCH | Investigation only |
| Clean up HTTP client | REFACTOR | Behavior preservation critical |
| Add retry to HTTP nodes | EXTEND | Need to understand existing |
| Clone browser node for API | CLONE | Pattern-based development |
| Add tests for edge cases | TEST | Test coverage focused |
| Update API documentation | DOCS | Documentation focus |
| Create new UI widget | UI | UI-specific patterns |
| Add Google Sheets integration | INTEGRATION | External API focus |
| Security audit for OAuth | SECURITY | Security-specific focus |

### Parallel Execution Guidelines

**DO**:
- Run EXPLORE with DOCS (different goals)
- Run QUALITY with SECURITY (different focus areas)
- Use parallel for non-dependent tasks

**DON'T**:
- Run BUILDER with anything (needs sequential)
- Run REVIEWER with anything (needs last)
- Skip EXPLORE even for "simple" tasks

### Chain Selection Heuristics

```python
def select_chain(request: str) -> ChainTemplate:
    # 1. Classify intent
    intent = classify_intent(request)

    # 2. Check for modifiers
    if "urgent" in request or "critical" in request:
        priority = "high"
    else:
        priority = "normal"

    # 3. Estimate complexity
    complexity = estimate_complexity(request)

    # 4. Select template
    if complexity == "high":
        template = get_template(intent, extended=True)
    else:
        template = get_template(intent)

    # 5. Apply priority adjustments
    if priority == "high":
        template.timeout *= 0.75  # Shorter timeouts

    return template
```

## 8. Metrics and Monitoring

### Chain Performance Metrics

```yaml
metrics:
  - name: "chain_duration"
    description: "Total time from start to approval"
    histogram: [5, 10, 15, 30, 60, 120] minutes

  - name: "loop_frequency"
    description: "How often chains need looping"
    counter: "loops_per_chain"

  - name: "approval_rate"
    description: "Percentage approved on first try"
    gauge: "first_try_approval_%"

  - name: "agent_contribution"
    description: "Time spent per agent"
    histogram: agent_breakdown

  - name: "issue_resolution"
    description: "Issues resolved per loop"
    gauge: "avg_issues_per_loop"
```

### Dashboard Queries

```sql
-- Average chain duration by type
SELECT task_type, AVG(duration_minutes)
FROM chains
GROUP BY task_type;

-- Loops by task type
SELECT task_type, COUNT(*) as total_loops
FROM chain_loops
GROUP BY task_type;

-- Common issue categories
SELECT issue_category, COUNT(*)
FROM reviewer_issues
GROUP BY issue_category;
```

## 9. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Chain stuck at EXPLORE | Semantic search taking too long | Increase timeout or simplify query |
| Quality tests never finish | Infinite test suite | Add test timeout, limit coverage |
| Reviewer always ISSUES | Strict review criteria | Adjust review guidelines |
| Max iterations reached | Complex issue | Manual intervention required |
| Parallel agents conflict | Shared resources | Sequential execution required |

### Recovery Commands

```bash
# Resume stuck chain
/chain resume <chain-id>

# Skip failing agent
/chain skip <chain-id> <agent-name>

# Retry with different timeout
/chain retry <chain-id> --timeout=900

# Cancel and restart
/chain cancel <chain-id>
/chain <type> "<task>" --resume-from=<checkpoint>
```

## 10. Future Enhancements

### Planned Features

1. **Smart Chain Selection** - ML-based task classification
2. **Dynamic Loop Adjustment** - Auto-adjust iterations based on issue severity
3. **Cross-Chain Dependencies** - Handle dependent features
4. **Cost Optimization** - Minimize token usage per chain
5. **Predictive Timing** - Estimate completion time based on history

### Roadmap

| Version | Feature | Target Date |
|---------|---------|-------------|
| v1.0 | Basic chaining | 2025-12-25 |
| v1.1 | Parallel execution | 2025-12-30 |
| v1.2 | Smart loop recovery | 2026-01-05 |
| v1.3 | Cost optimization | 2026-01-15 |
| v2.0 | ML-based selection | 2026-02-01 |

---

## Quick Reference

### Command Cheat Sheet

```bash
# Execute a chain
/chain <type> "<description>" [options]

# Check status
/chain status
/chain status <id>

# Manage chains
/chain kill <id>
/chain resume <id>
/chain retry <id> --timeout=900

# History
/chain history
/chain history --type=implement --days=7
```

### Chain Selection Quick Guide

```
New feature?          → /chain implement "..."
Bug fix?              → /chain fix "..."
Research?             → /chain research "..."
Cleanup code?         → /chain refactor "..."
Add tests?            → /chain test "..."
Update docs?          → /chain docs "..."
Security review?      → /chain security "..."
```

### Support

- Documentation: `.agent/rules/13-agent-chaining.md`
- Plan: `.brain/plans/agent-chaining-master-plan.md`
- Issues: Create issue in `.brain/issues/`
