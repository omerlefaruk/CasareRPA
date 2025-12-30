# CasareRPA Project Rules: Authoritative Reference

**Last Updated:** 2025-12-25
**Version:** 2.0 (Token-Optimized Index)

---

## Quick Reference

| Topic | File | Lines |
|-------|------|-------|
| **Coding Standards** | `rules/coding-standards.md` | ~60 |
| **Architecture** | `rules/architecture.md` | ~80 |
| **Testing** | `rules/testing.md` | ~120 |
| **Mocking** | `rules/mocking.md` | ~70 |
| **Protocols** | `rules/protocols.md` | ~85 |
| **Commands** | `rules/commands.md` | ~100 |
| **Error Handling** | `rules/error-handling.md` | ~60 |
| **Performance/Security** | `rules/performance-security.md` | ~75 |
| **Documentation** | `rules/documentation.md` | ~65 |

**Total:** ~625 lines (split from 1,372 lines → 54% reduction)

---

## Core Principles (Non-Negotiable)

1. **INDEX-FIRST**: Read `_index.md` before grep/glob
2. **KISS**: Minimal code that works
3. **NO SILENT FAILURES**: All external calls in try/except, use loguru
4. **THEME ONLY**: No hardcoded hex colors
5. **WORKTREES**: Never work on main/master
6. **CLEAN DDD**: Strict layer boundaries (Presentation → Application → Domain ← Infrastructure)

---

## Layer Dependencies

```
Presentation (UI)
    ↓ depends on
Application (Use Cases)
    ↓ depends on    ↓ depends on
Domain (Logic)     Infrastructure (Adapters)
```

**Rules:**
- Domain: NO external deps, NO I/O
- Application: imports Domain + Infrastructure interfaces
- Infrastructure: implements Domain interfaces
- Presentation: imports Application only

---

## Key Cross-References

| Topic | Location |
|-------|----------|
| Node templates | `.brain/docs/node-templates-core.md` |
| System patterns | `.brain/systemPatterns.md` |
| Agent definitions | `.claude/agents/_index.md` |
| Decision trees | `.brain/decisions/` |

---

## Quick Commands

```bash
# Test
pytest tests/ -v -m "not slow"    # Fast
pytest tests/ -v --cov=casare_rpa  # Coverage

# Quality
ruff check src/
ruff format src/
mypy src/

# Git
git worktree add .worktrees/feature -b feature main
python scripts/create_worktree.py "feature-name"
```

---

**Status:** AUTHORITATIVE. This index points to focused rule files in `.brain/rules/`.
**For details:** See specific rule file listed above.
