# .brain Knowledge Base Index

Central knowledge repository for CasareRPA development. AI agents and developers start here.

## Quick Navigation

| Need to... | Go to |
|------------|-------|
| Add a new node | [decisions/add-node.md](decisions/add-node.md) |
| Add a feature | [decisions/add-feature.md](decisions/add-feature.md) |
| Fix a bug | [decisions/fix-bug.md](fix-bug.md) |
| Find a symbol | [symbols.md](symbols.md) |
| Understand architecture | [systemPatterns.md](systemPatterns.md) |
| Check coding standards | [projectRules.md](projectRules.md) |
| Debug an error | [errors.md](errors.md) |
| See current session | [context/current.md](context/current.md) |

## Directory Structure

| Directory | Purpose | Index |
|-----------|---------|-------|
| `decisions/` | Decision trees for common tasks | [decisions/_index.md](decisions/_index.md) |
| `docs/` | Technical documentation & guides | [docs/_index.md](docs/_index.md) |
| `.claude/plans/` | Implementation plans & research | See .claude/plans/_index.md |
| `context/` | Session state & history | See below |
| `analysis/` | Archived exploration reports (84 files) | [analysis/_index.md](analysis/_index.md) |

## Root Files

| File | Purpose | When to Use |
|------|---------|-------------|
| [symbols.md](symbols.md) | Symbol registry with file paths | Find class/function locations |
| [errors.md](errors.md) | Error catalog with solutions | Debug error codes |
| [dependencies.md](dependencies.md) | Dependency graph | Understand import rules |
| [projectRules.md](projectRules.md) | Full coding standards | Code review, new features |
| [systemPatterns.md](systemPatterns.md) | Architecture patterns | System design decisions |
| [activeContext.md](activeContext.md) | Active session context | Resume work |
| [performance-baseline.md](performance-baseline.md) | Performance benchmarks | Optimization work |

## Context Directory

Session state tracking (no index needed - simple structure):

| File | Purpose |
|------|---------|
| `context/current.md` | Current session state (updated frequently) |
| `context/recent.md` | Recent session history |
| `context/archive/` | Archived session states |

## Cross-References

### From CLAUDE.md
- CLAUDE.md references this index in "AI-Optimized Documentation" section
- Decision trees referenced in "Quick Lookup Files" table
- symbols.md, errors.md, dependencies.md all referenced

### From Agent Rules
- `agent-rules/rules/06-protocol.md` - Brain update protocol
- `agent-rules/agents/docs.md` - Documentation agent uses .brain/
- `.claude/commands/*.md` - All commands reference .claude/plans/

### From .claude Rules
- `.claude/rules/01-workflow.md` - References context/current.md updates
- `.claude/rules/06-protocol.md` - Brain protocol and agent chaining

## Update Protocol

When updating .brain/ files:
1. Update the relevant file content
2. Update this index if adding/removing files
3. Update `context/current.md` with change summary
4. Cross-reference in related files

---

*Last updated: 2025-12-23*
*Referenced from: CLAUDE.md, agent-rules/, .claude/rules/*
