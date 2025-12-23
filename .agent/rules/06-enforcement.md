---
description: Enforcement of rules and boundaries
---

# Enforcement

## Hard Constraints

1. **No External Imports in Domain**: The domain layer must remain pure.
2. **No Synchronous I/O in Async Contexts**: Do not block the event loop.
3. **No Hardcoded Secrets**: Use the credential manager.
<<<<<<< HEAD
=======

## Boundaries (Never)
1. **No Main Branch Work**: Do not work directly on `main`/`master` (use worktrees).
2. **No Destructive Commands**: No `git reset --hard`, `git checkout --`, `rm -rf` without explicit request.
3. **No Secret Leakage**: Never commit or print secrets/tokens.
4. **No Silent Errors**: Always log external failures with context.
5. **No Domain Violations**: Domain must not import infrastructure/presentation.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
