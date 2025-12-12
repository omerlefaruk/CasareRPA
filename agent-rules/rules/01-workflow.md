# 5-Phase Workflow

Every task follows this workflow. Skip phases only when explicitly justified.

## Phase 1: RESEARCH
- Read `_index.md` files in relevant directories
- Check `.brain/context/current.md` for session state
- Review existing patterns in codebase

## Phase 2: PLAN
- Create plan in `.brain/plans/` or artifact
- Document approach, risks, alternatives
- Get user approval for significant changes

## Phase 3: EXECUTE
- Implement in small, testable increments
- Follow coding standards strictly
- Commit logical units of work

## Phase 4: VALIDATE
- Run tests: `pytest tests/ -v`
- Verify no regressions
- Test edge cases

## Phase 5: DOCS
- Update `_index.md` files
- Update `.brain/` context
- Add/update docstrings
