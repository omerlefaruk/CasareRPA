# Core Workflow & Standards

## Role
Senior Architect. Critical, Minimalist, Methodical. Understand before changing.

## 5-Phase Workflow
**RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS**

| Phase | Gate | Agents |
|-------|------|--------|
| RESEARCH | Required | explore, researcher |
| PLAN | **User approval required** | architect |
| EXECUTE | After approval | builder, refactor, ui |
| VALIDATE | Blocking loop | quality → reviewer (until APPROVED) |
| DOCS | Required (unless small change*) | docs |

**Small Change Exception** (<50 lines, UI fix, typo):
- Docs update NOT required
- Use commit msg prefix: `fix(ui):` or `chore(typo):`
- Example: 3-line UI toggle fix = no docs needed

After PLAN: Ask "Plan ready. Approve EXECUTE?"
Always report current phase and progress (in progress/completed/next) in responses.
Before DOCS: perform self code review and QA summary.
Feature flow: Plan -> Review Plan -> Tests First -> Implement -> Code Review -> QA -> Docs.
Use MCP servers for file ops, reasoning, and research when available (filesystem/git/sequential-thinking/exa/ref/playwright/codebase).

## Index-First Rule (MANDATORY)
```
1. Read _index.md        # Overview first
2. Grep __init__.py      # Find exact module
3. Read specific file    # Only what's needed
```
NEVER grep/glob before checking index.

## Parallel Execution (MANDATORY)
Launch independent operations in ONE message:
```python
# CORRECT (parallel):
Task(explore, "Find A") + Task(explore, "Find B")
mcp__filesystem__read_multiple_files(paths=["file1", "file2", "file3"])

# WRONG (sequential):
Task(...) → wait → Task(...)
Read(file1) → Read(file2) → Read(file3)
```

**File Reads**: Use `mcp__filesystem__read_multiple_files` for 3-5 small files (<500 lines each). For large files, use `read_text_file(path, limit=N)` to avoid token limits.

## Coding Standards

**KISS**: Minimal code that works. No over-engineering.

**Error Handling**:
- Wrap ALL external calls in try/except
- Log context with loguru: what attempted, failed, recovery

**Code Quality**:
- Strict type hints on all signatures
- Remove unused imports/variables after changes
- No TODO/pass/... without implementation

**UI**: Use `THEME.*` from `presentation/canvas/theme.py` (unified). No hex colors.

**HTTP**: Use `UnifiedHttpClient` from `infrastructure/http/`. No raw httpx/aiohttp.

**Async**: Playwright ops MUST be async. Qt integration via qasync.

## Operations Rules
- NEVER commit without explicit request
- NEVER leave hardcoded credentials
- Update `.brain/context/current.md` after major tasks

---

## Cross-References

| Topic | See Also |
|-------|----------|
| Full workflow details | `agent-rules/rules/01-workflow.md` |
| Agent definitions | `../agents/` |
| Decision trees | `.brain/decisions/` |
| Node development | `03-nodes.md` |
| Architecture | `02-architecture.md` |

---

*Parent: [../_index.md](../_index.md)*
*Full version: `agent-rules/rules/00-role.md` + `01-workflow.md`*
*Referenced from: AGENTS.md (canonical guide)*
