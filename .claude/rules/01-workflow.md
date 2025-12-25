---
description: 5-Phase workflow, token optimization, and execution standards
---

# Workflow & Token Optimization

## 5-Phase Workflow

**RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS**

| Phase | Gate | Agents |
|-------|------|--------|
| RESEARCH | Required | explore, researcher |
| PLAN | **User approval required** | architect |
| EXECUTE | After approval | builder, refactor, ui |
| VALIDATE | Blocking loop | quality → reviewer (until APPROVED) |
| DOCS | Required | docs |

## Phase Details

### RESEARCH
1. Read relevant _index.md files
2. Check .brain/decisions/ for decision trees
3. Search existing code before creating new
4. Understand current patterns
5. Ensure worktree is created (do not work on main/master)

### PLAN
1. Create plan in `.claude/plans/{feature}.md`
2. Define clear success criteria
3. Identify affected files
4. Determine test strategy
5. Review the plan with the user and get approval before EXECUTE

### EXECUTE
1. Write tests first (TDD)
2. Implement changes following coding standards
3. Re-read relevant rules/design docs before implementation
4. Keep commits atomic
5. Use conventional commits: feat:, fix:, refactor:, test:, docs:

### VALIDATE
1. Run tests: `pytest tests/ -v`
2. Check for lint errors
3. Verify no regressions
4. Test in canvas: `python manage.py canvas`
5. Perform self code review and QA summary

### DOCS
1. Update _index.md files
2. Update `.brain/context/current.md`
3. Add decision tree if new pattern
4. Update CLAUDE.md if rules or patterns change

## Standards

**KISS**: Minimal code that works. No over-engineering.

**Index-First (MANDATORY)**:
```
1. Read _index.md        # Overview first
2. cclsp.find_definition # For symbol navigation (LSP)
3. Grep __init__.py      # Find exact module
4. Read specific file    # Only what's needed
```

**Parallel Execution (MANDATORY)**: Launch independent operations in ONE message.

**Error Handling**: Wrap ALL external calls in try/except. Log context with loguru.

**Code Quality**:
- Strict type hints on all signatures
- Remove unused imports/variables after changes
- No TODO/pass/... without implementation

**UI**: Use `THEME.*` from `presentation/canvas/ui/theme.py`. No hex colors.

**HTTP**: Use `UnifiedHttpClient` from `infrastructure/http/`. No raw httpx/aiohttp.

**Async**: Playwright ops MUST be async. Qt integration via qasync.

## Token Optimization

1. **Read selectively**: Don't dump 5000 line files if you need 10 lines
2. **Use summaries**: Rely on _index.md files
3. **Concise output**: Generate code, not essays
4. **Structured formats**: Prefer tables or short lists; use XML blocks when it reduces tokens

## Progress Reporting

Always report current phase and progress (in progress/completed/next) in responses.

After PLAN: Ask "Plan ready. Approve EXECUTE?"
Before DOCS: perform self code review and QA summary.
