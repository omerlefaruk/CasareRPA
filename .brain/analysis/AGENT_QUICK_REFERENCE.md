<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# CasareRPA Agent Quick Reference

## Agent Selection Matrix

| Task | Best Agent | Workflow | Qdrant Used |
|------|-----------|----------|------------|
| **Explore codebase** | explore | qdrant-find → index-first → grep | YES (PRIMARY) |
| **Design system** | architect | qdrant-find → design → impl plan | YES |
| **Implement feature** | builder | qdrant-find → code → complete | YES |
| **Write/fix tests** | quality | qdrant-find → test patterns → code | YES |
| **Code review** | reviewer | qdrant-find → compare → feedback | YES |
| **Optimize code** | refactor | qdrant-find → improve → verify | YES |
| **Research problem** | researcher | qdrant-find → mcp tools → report | YES |
| **API integration** | integrations | qdrant-find → mcp docs → impl | YES |
| **UI development** | ui | qdrant-find → patterns → widgets | YES |
| **Create docs** | docs | qdrant-find → understand → write | YES |

## Agent Models

```
explore      → haiku      (lightweight exploration)
architect    → opus       (complex design decisions)
builder      → opus       (production code writing)
quality      → opus       (comprehensive testing)
reviewer     → opus       (deep code review)
refactor     → haiku      (pattern-based improvements)
researcher   → haiku      (information gathering)
integrations → opus       (complex integrations)
ui           → opus       (UI/UX complexity)
docs         → haiku      (documentation writing)
```

## Qdrant Search Examples by Agent

### explore
```
qdrant-find: "browser automation click element"
qdrant-find: "error handling retry pattern"
qdrant-find: "workflow execution context"
```

### architect
```
qdrant-find: "node execution pattern"
qdrant-find: "event bus implementation"
```

### builder
```
qdrant-find: "similar node implementation"
qdrant-find: "error handling pattern"
```

### quality
```
qdrant-find: "test node execution"
qdrant-find: "mock playwright page"
qdrant-find: "async test pattern"
```

### reviewer
```
qdrant-find: "similar node pattern"
qdrant-find: "existing test patterns"
```

### refactor
```
qdrant-find: "class usage pattern"
qdrant-find: "imports this module"
```

### researcher
```
qdrant-find: "current implementation of X"
qdrant-find: "how feature Y works"
```

### integrations
```
qdrant-find: "HTTP client integration"
qdrant-find: "OAuth authentication"
qdrant-find: "API node implementation"
```

### ui
```
qdrant-find: "dialog implementation Qt"
qdrant-find: "panel widget pattern"
qdrant-find: "theme styling"
```

### docs
```
qdrant-find: "node implementation details"
qdrant-find: "API endpoint handlers"
```

## Qdrant Usage Emphasis

### Primary (HIGHEST PRIORITY)
- **explore** - "ALWAYS use `qdrant-find` FIRST. Provides 95%+ token savings vs grep/glob"

### Secondary (Pattern Discovery)
- **architect**, **builder**, **quality**, **refactor**, **ui**, **docs** - Use before implementing
- **integrations**, **researcher** - Use before researching alternatives

## MCP Tools by Agent

| Agent | MCP Tools | Priority |
|-------|-----------|----------|
| architect | exa (patterns), Ref (docs) | External research |
| integrations | Ref (API docs) > exa (SDK) > web search | P1 official, P2 examples, P3 patterns |
| researcher | Ref (docs) > exa (code) > web (general) | P1 official, P2 code, P3 best practices |
| quality | exa (patterns), Ref (pytest) | Test patterns & docs |

## Key File Locations

```
.claude/agents/              ← PRIMARY (full specs with YAML frontmatter)
agent-rules/agents/          ← SECONDARY (simplified reference)
.brain/context/current.md    ← Session state (read by all agents)
.brain/projectRules.md       ← Coding standards
.brain/systemPatterns.md     ← Architecture patterns
CLAUDE.md                    ← Project instructions
```

## Agent Pipeline

```
explore              ← Start here for understanding
    ↓
architect/builder    ← Plan and implement
    ↓
quality              ← Write tests
    ↓
reviewer             ← Code review gate
```

## When to NOT Use Qdrant

- Looking for exact class/function names → Use Grep
- Searching for import statements → Use Grep
- Finding specific file paths → Use Glob
- Qdrant returns no relevant results → Fall back to Grep

## Status: All 10 Agents Support Qdrant

Every agent in the codebase has been configured to use `qdrant-find` for semantic search:
- explore (primary emphasis)
- architect, builder, quality, reviewer, refactor, researcher, integrations, ui, docs (pattern discovery)

This represents a unified strategy across all development workflows to use semantic search as the first line of codebase navigation.
