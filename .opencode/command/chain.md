---
description: |
  Execute automatic agent chaining with loop-based error recovery. Task types: implement, fix, refactor, research, extend, clone, test, docs, security, ui, integration
argument-hint: "<task_type> <description> [--parallel=<agents>] [--priority=<level>] [--max-iterations=<n>] [--timeout=<seconds>] [--dry-run] [--skip-review]"

agent: architect
subtask: true
---

# Chain: $ARGUMENTS.task_type - $ARGUMENTS.description

Execute automatic agent chaining with error recovery loops. Reference: `.opencode/rules/13-agent-chaining.md` and `.opencode/rules/14-agent-chaining-enhanced.md`

## Task Type: $ARGUMENTS.task_type

## Options (Optional)
- `--parallel=<agents>`: Run agents in parallel (security, docs)
- `--priority=<level>`: Priority (high, normal, low)
- `--max-iterations=<n>`: Override max loop iterations (default: 3)
- `--timeout=<seconds>`: Override agent timeout (default: 600s)
- `--dry-run`: Preview chain without execution
- `--skip-review`: Skip reviewer gate (not recommended)

## Task Type to Agent Chain Mapping

| Task Type | Chain |
|-----------|-------|
| implement | EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER |
| fix | EXPLORE → BUILDER → QUALITY → REVIEWER |
| refactor | EXPLORE → REFACTOR → QUALITY → REVIEWER |
| research | EXPLORE → RESEARCHER → APPROVAL |
| extend | EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER |
| clone | EXPLORE → BUILDER → QUALITY → REVIEWER |
| test | EXPLORE → QUALITY → REVIEWER |
| docs | EXPLORE → DOCS → REVIEWER |
| security | EXPLORE → SECURITY-AUDITOR → REVIEWER |
| ui | EXPLORE → UI → QUALITY → REVIEWER |
| integration | EXPLORE → INTEGRATIONS → QUALITY → REVIEWER |

## Phase 1: EXPLORE (Parallel - 2-3 agents)

Launch explore agents in parallel:

```
!Task(subagent_type="explore", prompt="Find existing implementations, patterns, and architecture related to: $ARGUMENTS.description. Search in src/casare_rpa/ for similar code. Return: file paths, class structure, dependencies, patterns to follow.")

!Task(subagent_type="explore", prompt="Find test patterns and quality checks for: $ARGUMENTS.description. Search tests/ for similar test structures. Return: fixture names, test structure, mocking patterns.")

!Task(subagent_type="explore", prompt="Find relevant rules and documentation for: $ARGUMENTS.description. Search .opencode/rules/, .brain/, and docs/. Return: relevant rules, patterns to follow, gotchas.")
```

## Phase 2: ARCHITECT (For implement, extend)

```
!Task(subagent_type="architect", prompt="Create implementation plan for: $ARGUMENTS.description

Task Type: $ARGUMENTS.task_type

Create plan in .brain/plans/chain-{timestamp}.md with:
- Files to create/modify
- Agent assignments
- Parallel opportunities
- Risks and mitigation
- Test approach

Follow patterns from explore findings and .opencode/rules/02-architecture.md")
```

**Gate**: "Plan ready. Approve to continue?"

## Phase 3: BUILD / IMPLEMENT (Parallel - 2-5 agents)

### For task_type=implement or task_type=extend:
```
 !Task(subagent_type="builder", prompt="Implement the solution following the plan for: $ARGUMENTS.description. Focus on domain/application layer code.")

 !Task(subagent_type="integrations", prompt="Implement infrastructure/API integrations for: $ARGUMENTS.description.")

 !Task(subagent_type="ui", prompt="Implement presentation layer UI components for: $ARGUMENTS.description if applicable.")
```

### For task_type=fix:
```
!Task(subagent_type="builder", prompt="Fix the root cause for: $ARGUMENTS.description. Minimal change only - fix the bug, don't refactor.")
```

### For task_type=refactor:
```
 !Task(subagent_type="refactor", prompt="Refactor code for: $ARGUMENTS.description. Follow plan, maintain existing behavior.")
```

### For task_type=clone:
```
 !Task(subagent_type="builder", prompt="Clone the pattern for: $ARGUMENTS.description. Follow existing patterns from explore phase.")
```

### For task_type=security:
```
 !Task(subagent_type="security-auditor", prompt="Security audit for: $ARGUMENTS.description. Check for vulnerabilities, OWASP Top 10 compliance.")
```

### For task_type=ui:
```
 !Task(subagent_type="ui", prompt="Implement UI for: $ARGUMENTS.description. Follow PySide6 dark theme patterns.")
```

### For task_type=integration:
```
 !Task(subagent_type="integrations", prompt="Implement integration for: $ARGUMENTS.description. Follow API integration patterns.")
```

## Phase 4: QUALITY (Tests)

```
 !Task(subagent_type="quality", prompt="Run tests and QA checks for: $ARGUMENTS.description

1. Run tests for affected modules
2. Check linting (ruff check)
3. Type checking (mypy if applicable)
4. Report failures and required fixes

pytest tests/ -v --tb=short")
```

## Phase 5: REVIEWER (Gate)

```
 !Task(subagent_type="reviewer", prompt="Review implementation for: $ARGUMENTS.description

Check:
- Error handling on all external calls
- Type hints complete
- No hardcoded colors/credentials
- Tests cover happy path + errors
- Follows existing patterns
- Domain purity maintained

Output: APPROVED or ISSUES with file:line references")
```

## Loop: If ISSUES → Fix → Quality → Review Again

```
Iteration 1/3
  ↓
REVIEWER: ISSUES FOUND (2)
  - Line 42: Missing error handling
  - Line 78: Type hint should be Optional[str]

  ↓ Loop back to BUILD for fixes
  ↓
QUALITY: Tests pass
  ↓
REVIEWER: APPROVED

✓ Chain completed in 2 iterations
```

## Phase 6: DOCS (For implement, extend, fix, refactor, clone)

```
 !Task(subagent_type="docs", prompt="Update documentation for: $ARGUMENTS.description

- Update relevant _index.md files
- Update .brain/context/current.md with changes
- Add docstrings where missing")
```

## Completion Report

```
═════════════════════════════════════════════════════════════
  CHAIN COMPLETED: $ARGUMENTS.task_type
  Task: $ARGUMENTS.description
  Iterations: 1
  Duration: ~60 minutes
  Files Created: N
  Files Modified: N
  Tests: All passing
  Review: APPROVED
═════════════════════════════════════════════════════════════
```

## Error Escalation (If max iterations exceeded)

```
[ERROR] Chain failed after 3 iterations
  Last Review: ISSUES (remaining: 2)
  - Complex architectural concern

[ESCALATION] Human review required
```
