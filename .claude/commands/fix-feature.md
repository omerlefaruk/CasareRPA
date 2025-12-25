---
description: Fix bugs and issues in existing features. Types: crash, output, ui, perf, flaky
arguments:
  - name: type
    description: Bug type (crash, output, ui, perf, flaky). Leave empty for unknown.
    required: false
  - name: description
    description: Description of the bug or issue
    required: true
---

# Fix Feature: $ARGUMENTS.description

Execute bug fix workflow with parallel diagnosis. Reference: `agent-rules/commands/fix-feature.md`

## Bug Type: $ARGUMENTS.type (auto-detect if empty)

## Parallel Execution Rule

> **CRITICAL**: Launch up to **5 agents in parallel** for diagnosis.

## Phase 1: DIAGNOSE (Parallel - 3-5 agents)

### For crash/exception:
```
Task(subagent_type="explore", prompt="Find stack trace in logs/ and error messages related to: $ARGUMENTS.description")
Task(subagent_type="explore", prompt="Find error handling and try/except blocks in suspected modules")
Task(subagent_type="explore", prompt="Find similar crash fixes in git log --oneline -50")
```

### For wrong output:
```
Task(subagent_type="explore", prompt="Trace data flow for: $ARGUMENTS.description. Find input→processing→output chain.")
Task(subagent_type="explore", prompt="Find where output is set/modified in suspected functions")
Task(subagent_type="explore", prompt="Find tests to understand expected behavior")
```

### For UI not updating:
```
Task(subagent_type="explore", prompt="Find signal connections and @Slot decorators in suspected widgets")
Task(subagent_type="explore", prompt="Find event subscriptions and bus.subscribe calls")
Task(subagent_type="explore", prompt="Check for thread safety issues - UI updates from background threads")
```

### For performance:
```
Task(subagent_type="explore", prompt="Find blocking calls and loops in suspected module")
Task(subagent_type="explore", prompt="Find async patterns and thread usage")
Task(subagent_type="quality", prompt="mode=perf: Profile the slow operation")
```

### For flaky test:
```
Task(subagent_type="explore", prompt="Find async/await patterns in test file")
Task(subagent_type="explore", prompt="Find shared state and fixtures that may cause race conditions")
```

### For unknown:
```
Task(subagent_type="explore", prompt="Search for: $ARGUMENTS.description in src/ and logs/")
Task(subagent_type="explore", prompt="Find related code and recent changes")
Task(subagent_type="researcher", prompt="Research error message or symptom: $ARGUMENTS.description")
```

## Phase 2: PLAN (architect)

```
Task(subagent_type="architect", prompt="""
Create fix plan for: $ARGUMENTS.description

Bug type: $ARGUMENTS.type

Based on diagnosis findings, create plan in .brain/plans/fix-{issue}.md with:
- Root cause (one sentence)
- Files to modify with line numbers
- Minimal fix approach
- Risk assessment (Low/Medium/High)
- Regression test needed

DO NOT refactor - fix only the root cause.
""")
```

**Gate**: "Fix plan ready. Approve?"

## Phase 3: FIX (Parallel - 1-2 agents)

```
Task(subagent_type="builder", prompt="""
Fix the root cause following the plan.

Rules:
- Minimal change only
- Add error handling if missing
- Add logging with loguru
- Maintain type hints
- Make fix reversible
""")

Task(subagent_type="refactor", prompt="""
If cleanup needed around the fix:
- Improve error handling in surrounding code
- Do NOT change unrelated code
""")
```

## Phase 4: VALIDATE (Sequential Loop)

### Quality Agent:
```
Task(subagent_type="quality", prompt="""
mode: test

1. Run specific test that reproduces the bug
2. Run regression tests for affected module
3. Verify no new warnings/errors in logs

pytest tests/{affected_module}/ -v
""")
```

### Reviewer Agent:
```
Task(subagent_type="reviewer", prompt="""
Review fix for: $ARGUMENTS.description

Check:
- [ ] Fix addresses root cause (not symptom)
- [ ] Minimal change (no unrelated modifications)
- [ ] Error handling added where needed
- [ ] Type hints preserved
- [ ] Tests pass (new + existing)
- [ ] No new warnings/errors

Output: APPROVED or ISSUES with file:line references
""")
```

**Loop**: If ISSUES → fix → quality → reviewer again

## Phase 5: DOCS (Optional)

If new error pattern discovered:
```
Task(subagent_type="docs", prompt="""
Update .brain/errors.md with new error entry:
- Error code/message
- Symptom
- Cause
- Fix
- Prevention
""")
```

## Rollback Plan

If fix causes more problems:
```bash
git stash  # Save current work
git checkout {file}  # Revert to last working state
```

## Completion

Report:
- Root cause identified
- Fix applied (file:line)
- Tests passing
- Review: APPROVED
- Rollback instructions if needed
