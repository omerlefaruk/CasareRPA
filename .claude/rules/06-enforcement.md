---
description: Enforcement of rules and boundaries
---

# Enforcement

## Hard Constraints

1. **No External Imports in Domain**: The domain layer must remain pure.
2. **No Synchronous I/O in Async Contexts**: Do not block the event loop.
3. **No Hardcoded Secrets**: Use the credential manager.

## Boundaries (Never)
1. **No Main Branch Work**: Do not work directly on `main`/`master` (use worktrees).
2. **No Destructive Commands**: No `git reset --hard`, `git checkout --`, `rm -rf` without explicit request.
3. **No Secret Leakage**: Never commit or print secrets/tokens.
4. **No Silent Errors**: Always log external failures with context.
5. **No Domain Violations**: Domain must not import infrastructure/presentation.

## Small Change Exception

Docs update NOT required for:
- **UI fixes**: colors, layout, toggle behavior, visibility
- **Typos**: spelling, comments
- **Tiny refactor**: <50 lines changed

Use commit prefix to signal small change:
- `fix(ui):` - UI behavior fix
- `chore(typo):` - Typo correction
- `refactor(small):` - Small refactor

Examples that skip docs:
- "Fix: credentials panel toggle on repeat press" → `fix(ui): toggle credentials panel`
- "Fix: missing import in utils.py" → `fix: add missing import`
- "Fix: typo in error message" → `chore(typo): fix error message`

Examples that REQUIRE docs:
- New node → DOCS required
- New feature → DOCS required
- API change → DOCS required
