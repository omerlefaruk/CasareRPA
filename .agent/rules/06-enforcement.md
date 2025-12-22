---
description: Enforcement of rules and boundaries
---

# Enforcement

## Hard Constraints

1. **No External Imports in Domain**: The domain layer must remain pure.
2. **No Synchronous I/O in Async Contexts**: Do not block the event loop.
3. **No Hardcoded Secrets**: Use the credential manager.
