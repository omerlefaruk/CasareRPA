---
description: Checklist for documenting new patterns or rules discovered during work
---
# New Pattern Checklist

Use this checklist whenever a task reveals a new reusable pattern, rule, or constraint.

## 1. Validate the Pattern
- Confirm it is reproducible and not a one-off.
- Identify affected layers (domain/application/infrastructure/presentation/nodes).

## 2. Update the Canonical Guide
- Update `AGENTS.md`.
- Run `python scripts/sync_agent_guides.py` to sync `CLAUDE.md` and `GEMINI.md`.

## 3. Update Rule Sources
- Add/adjust relevant `../rules/*.md` entries.
- Update `.brain/systemPatterns.md` or `.brain/errors.md` if it is a reusable pattern or error fix.
- Add to `.brain/decisions/` if it changes a decision flow.

## 4. Update Indexes
- Update `.brain/_index.md` if new docs were added.
- Update any affected `_index.md` in the codebase.

## 5. Add Evidence
- Add tests or a minimal example.
- Reference concrete files and paths in the docs.

## 6. Session Context
- Update `.brain/context/current.md` with the new rule and where it was recorded.
