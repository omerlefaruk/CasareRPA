# 5-Phase Workflow

Every task follows this workflow. Skip phases only when explicitly justified.

## Phase 1: RESEARCH
- Read `_index.md` files in relevant directories
- Check `.brain/context/current.md` for session state
- Review existing patterns in codebase
- Ensure a worktree is created (do not work on main/master)

## Phase 2: PLAN
- Create plan in `.brain/plans/` or artifact
- Document approach, risks, alternatives
- Get user approval for significant changes
- Review the plan with the user before EXECUTE

## Phase 3: EXECUTE
- Write tests first (TDD)
- Implement in small, testable increments
- Follow coding standards strictly
- Commit logical units of work
- Re-read relevant rules/design docs before implementation
- If code changes in `src/`, plan corresponding doc/rule updates

## Phase 4: VALIDATE
- Run tests: `pytest tests/ -v`
- Verify no regressions
- Test edge cases
- Perform self code review and QA summary

## Phase 5: DOCS
- Update `_index.md` files
- Update `.brain/` context
- Add/update docstrings
- Update AGENTS.md (and sync CLAUDE.md + GEMINI.md) if rules or patterns change

## Feature Lifecycle (Mandatory)
Plan -> Review Plan -> Tests First -> Implement -> Code Review -> QA -> Docs.
Loop until clean if any errors or review issues appear.
