---
description: 5-Phase workflow for all significant development tasks
---

# 5-Phase Workflow

Follow this workflow for all significant tasks:

## Overview

**RESEARCH -> PLAN -> EXECUTE -> VALIDATE -> DOCS**

## Small Change Exception (<50 lines)

If change is:
- UI fix (colors, layout, toggle behavior)
- Typo correction
- Trivial refactor (<50 lines changed)

**Skip docs phase.** Use commit prefix:
- `fix(ui):` for UI fixes
- `chore(typo):` for typos
- `refactor(small):` for tiny refactor

---

## Phase 1: RESEARCH

1. Read relevant _index.md files
2. Check .brain/decisions/ for decision trees
3. Search existing code before creating new
4. Understand current patterns in .brain/systemPatterns.md

## Phase 2: PLAN

1. Create plan in .brain/plans/{feature}.md
2. Define clear success criteria
3. Identify affected files
4. Determine test strategy
5. Review the plan with the user and get approval before EXECUTE

## Phase 3: EXECUTE

1. Write tests first (TDD)
2. Implement changes following coding standards
3. Keep commits atomic
4. Use conventional commits: feat:, fix:, refactor:, test:, docs:
5. If code changes in `src/`, plan corresponding doc/rule updates

## Phase 4: VALIDATE

1. Run tests: pytest tests/ -v
2. Check for lint errors
3. Verify no regressions
4. Test in canvas: python manage.py canvas
5. Perform self code review and QA summary

## Phase 5: DOCS

1. Update _index.md files
2. Update .brain/context/current.md
3. Add decision tree if new pattern
4. Update AGENTS.md (and sync CLAUDE.md + GEMINI.md) if rules or patterns change
5. Update any affected docs in docs/ when behavior or usage changes

## Feature Lifecycle (Mandatory)
Plan -> Review Plan -> Tests First -> Implement -> Code Review -> QA -> Docs.
Loop until clean if any errors or review issues appear.
