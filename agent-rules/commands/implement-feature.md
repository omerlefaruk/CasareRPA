---
description: Implement a new feature with full agent orchestration. Modes: implement (default), refactor, optimize, extend
arguments:
  - name: scope
    description: Scope hint (domain, application, infrastructure, presentation, nodes)
    required: false
  - name: mode
    description: Mode (implement, refactor, optimize, extend). Default is implement.
    required: false
---

# Implement Feature

Execute the full automated workflow with parallel agents. Reference: `agent-rules/commands/implement-feature.md`

## Mode: $ARGUMENTS.mode (default: implement)

## Parallel Execution Rule

> **CRITICAL**: Launch up to **5 agents in parallel** when tasks are independent.

## Phase 1: RESEARCH (Parallel - 2-3 agents)

Launch explore agents in parallel:

```
Task(subagent_type="explore", prompt="Find existing implementations related to the feature in src/casare_rpa/$ARGUMENTS.scope/. Look for similar patterns, classes, architecture. Return: file paths, class structure, dependencies.")

Task(subagent_type="explore", prompt="Find test patterns for $ARGUMENTS.scope layer in tests/. Return: fixture names, test structure, mocking patterns.")

Task(subagent_type="researcher", prompt="Research best practices for the feature. Check external documentation if integrating with APIs.")
```

## Phase 2: PLAN (architect)

```
Task(subagent_type="architect", prompt="""
Create implementation plan for the feature.

Scope: $ARGUMENTS.scope
Mode: $ARGUMENTS.mode

Create plan in .brain/plans/{feature-name}.md with:
- Files to create/modify
- Agent assignments (builder, ui, integrations, refactor)
- Parallel opportunities
- Risks and mitigation
- Test plan

Follow patterns from explore findings and .brain/systemPatterns.md
""")
```

**Gate**: "Plan ready. Approve REVIEW PLAN?"

## Phase 2b: REVIEW PLAN (reviewer)

```
Task(subagent_type="reviewer", prompt="""
Review the plan for completeness, risks, and alignment with rules.
Approve or list issues before any implementation.
""")
```

**Gate**: "Plan reviewed. Approve TESTS FIRST?"

## Phase 3: TESTS FIRST (quality)

```
Task(subagent_type="quality", prompt="""
Write tests first for the feature.
Location: tests/$ARGUMENTS.scope/
Follow patterns from explore phase.
""")
```

## Phase 4: IMPLEMENT (Parallel - 2-5 agents)

### For mode=implement or mode=extend:
```
Task(subagent_type="builder", prompt="Implement domain/application layer code following plan")
Task(subagent_type="integrations", prompt="Implement infrastructure/API integrations following plan")
Task(subagent_type="ui", prompt="Implement presentation layer UI components following plan")
```

### For mode=refactor:
```
Task(subagent_type="refactor", prompt="Restructure code following plan, maintain existing behavior")
```

### For mode=optimize:
```
Task(subagent_type="quality", prompt="mode=perf: Profile and identify bottlenecks")
Task(subagent_type="refactor", prompt="Optimize identified bottlenecks")
```

## Phase 5: CODE REVIEW + QA (Sequential Loop)

### Reviewer Agent:
```
Task(subagent_type="reviewer", prompt="""
Review implementation.

Check:
- Error handling on all external calls
- Type hints complete
- No hardcoded colors/credentials
- Tests cover happy path + errors
- Follows existing patterns

Output: APPROVED or ISSUES with file:line references
""")
```

### Quality Agent:
```
Task(subagent_type="quality", prompt="""
Run tests and QA checks.
Report failures and required fixes.
""")
```

**Loop**: If ISSUES/FAILURES → fix → re-run tests → re-review

## Phase 6: DOCS (docs)

```
Task(subagent_type="docs", prompt="""
Update documentation:
- Update relevant _index.md files
- Update .brain/context/current.md with changes
- Add docstrings where missing
""")
```

## Completion

Report:
- Files created/modified
- Tests passing
- Review: APPROVED
- Agent flow used
