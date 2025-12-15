---
description: 5-Phase workflow for all significant development tasks
---

# 5-Phase Workflow

Follow this workflow for all significant tasks:

## Overview

RESEARCH -> PLAN -> EXECUTE -> VALIDATE -> DOCS

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

## Phase 3: EXECUTE

1. Implement changes following coding standards
2. Write tests first (TDD)
3. Keep commits atomic
4. Use conventional commits: feat:, fix:, refactor:, test:, docs:

## Phase 4: VALIDATE

1. Run tests: pytest tests/ -v
2. Check for lint errors
3. Verify no regressions
4. Test in canvas: python manage.py canvas

## Phase 5: DOCS

1. Update _index.md files
2. Update .brain/context/current.md
3. Add decision tree if new pattern
4. Update GEMINI.md if rules change
