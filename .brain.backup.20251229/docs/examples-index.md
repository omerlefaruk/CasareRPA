# Code Examples Index

**Parent:** `.brain/docs/_index.md` | **Last Updated:** 2025-12-25

## Node Templates (Primary Reference)

| Category | File | Lines |
|----------|------|-------|
| Browser, Desktop, Control Flow | `node-templates-core.md` | ~350 |
| File, String, List, Variable | `node-templates-data.md` | ~490 |
| HTTP, Google, System, Dialog | `node-templates-services.md` | ~490 |

**Usage:** Reference these templates when creating new nodes. DO NOT copy code - use patterns.

## Architecture Examples

| Pattern | Location |
|---------|----------|
| Node execution pattern | `node-templates-core.md` Template 1 |
| Event bus usage | `.brain/systemPatterns.md` |
| Domain event | `.claude/rules/02-architecture.md` |
| Async/await patterns | `.brain/rules/coding-standards.md` |

## Rule File Examples

| Topic | File | Key Example |
|-------|------|-------------|
| Docstring format | `rules/documentation.md` | Google style |
| Exception handling | `rules/error-handling.md` | Layer-specific patterns |
| Mocking | `rules/mocking.md` | Always/Never mock tables |
| Async best practices | `rules/performance-security.md` | Concurrent execution |

---

**Note:** For runnable code examples, see `tests/conftest.py` for test patterns and `src/casare_rpa/nodes/` for production implementations.
