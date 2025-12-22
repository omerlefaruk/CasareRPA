---
description: Standard QA and self-review checklist before finishing a task
---
# QA Checklist

Use this checklist before concluding implementation work.

## Self Code Review
- Re-read changed files for correctness and style.
- Confirm type hints, imports, and error handling are consistent.
- Verify rules compliance (theme, slots, node standards, HTTP client).

## QA / Tests
- Run relevant tests or document why not run.
- Verify edge cases and error paths.
- Note any remaining risks.

## Docs / Rules
- Update AGENTS.md and sync CLAUDE.md + GEMINI.md if patterns/rules changed.
- Update `../rules/` and `.brain/` as needed.
- Update docs in `docs/` if behavior changed.
