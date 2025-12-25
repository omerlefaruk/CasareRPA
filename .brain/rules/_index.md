# Project Rules Index

**Parent:** `.brain/projectRules.md` | **Last Updated:** 2025-12-25

## Rules Files

| File | Purpose | Key Sections |
|------|---------|--------------|
| **coding-standards.md** | Naming, type hints, formatting | Naming conventions, type hints, import order |
| **architecture.md** | DDD layers, dependencies | Layer definitions, dependency injection, layer diagram |
| **testing.md** | Test patterns by layer | Domain, Application, Infrastructure, Presentation, Node testing |
| **mocking.md** | Mock/stub decisions | Always Mock, Never Mock, Context Dependent tables |
| **protocols.md** | Agent & worktree workflows | Brain updates, planning protocol, worktree commands |
| **commands.md** | Development commands | pytest flags, git workflow, commit format, branch naming |
| **error-handling.md** | Exception hierarchy | CasareRPAError base, layer patterns, troubleshooting |
| **performance-security.md** | Optimization & security | Async best practices, resource pooling, input validation |
| **documentation.md** | Docstring & README | Google style format, inline comments, README structure |

---

## Quick Lookups

### Exception Hierarchy
```
Exception
├── CasareRPAError (base)
│   ├── DomainError
│   ├── ApplicationError
│   └── InfrastructureError
```
See: `error-handling.md`

### Layer Diagram
```
Presentation → Application → Domain
                              ↑
                         Infrastructure
```
See: `architecture.md`

### Test Commands
```bash
pytest tests/ -v -m "not slow"  # Fast tests
pytest tests/ -v --cov=casare_rpa  # Coverage
pytest tests/path/test_file.py::test_name -vv  # Single
```
See: `commands.md`, `testing.md`

### Mocking Rules
| Layer | Mock Strategy |
|-------|---------------|
| Domain | No mocks (pure logic) |
| Application | Mock infrastructure |
| Infrastructure | Mock external services |
| Presentation | Mock Qt pieces |
See: `mocking.md`

---

## Cross-References

| Related | Location |
|---------|----------|
| System patterns | `.brain/systemPatterns.md` |
| Node templates | `.brain/docs/node-templates-*.md` |
| Agent rules | `.claude/rules/` |
| Decision trees | `.brain/decisions/` |
