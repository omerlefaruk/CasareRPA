# CasareRPA Agent Definitions Summary

## Overview

This document catalogs all agent definition files in the CasareRPA codebase. Two locations are used:
- **Primary (Active):** `.claude/agents/` - Full agent specifications with YAML frontmatter
- **Secondary (Reference):** `agent-rules/agents/` - Simplified versions without YAML

Both versions exist for documentation and agent configuration purposes.

---

## Agent Files Summary

### 1. EXPLORE Agent (Codebase Navigator)

**Files:**
- `.claude/agents/explore.md` - Primary (FULL SPEC)
- `agent-rules/agents/explore.md` - Reference (simplified)

**Purpose:** Fast codebase exploration specialist for finding patterns, files, and architecture.

**Key Skills:**
- Pattern discovery via semantic search
- File navigation and indexing
- Architecture understanding

**Qdrant Usage:** **YES - PRIMARY TOOL**
- Lines 10-11: "**ALWAYS use `qdrant-find` MCP tool FIRST** for any search query. Provides semantic search with 95%+ token savings"
- Example queries:
  ```
  qdrant-find: "browser automation click element"
  qdrant-find: "error handling retry pattern"
  qdrant-find: "workflow execution context"
  ```
- Fallback to Grep/Glob only for exact strings or when qdrant-find returns no results

**Model:** haiku (lightweight, fast exploration)

**Tier System:**
- **Tier 1** (<500 tokens): Index-first with `_index.md` files
- **Tier 2** (<2000 tokens): Targeted grep + qdrant-find searches
- **Tier 3** (<5000 tokens): Deep file dives for complex questions

---

### 2. ARCHITECT Agent (System Design & Implementation)

**Files:**
- `.claude/agents/architect.md` - Primary (FULL SPEC with detailed design guidance)
- `agent-rules/agents/architect.md` - Reference (simplified)

**Purpose:** Implementation specialist and system design authority. Handles both coding and architectural decisions.

**Key Skills:**
- System design and data contracts
- Python 3.12+, PySide6, Playwright, async patterns
- Node execution, event bus, distributed workflows
- Cross-component coordination (Canvas/Robot/Orchestrator)

**Qdrant Usage:** **YES**
- Line 32-35: Semantic search for discovering patterns:
  ```
  qdrant-find: "node execution pattern"
  qdrant-find: "event bus implementation"
  ```

**External Research Tools:**
- `mcp__exa__get_code_context_exa` - Code examples and patterns
- `mcp__Ref__ref_search_documentation` - Official framework docs
- `mcp__exa__web_search_exa` - Best practices and comparisons

**Model:** opus (advanced reasoning for design decisions)

**Output Format:**
- Complete, production-ready code (for implementation)
- Architecture diagrams and design documents (for planning)
- Implementation plans with acceptance criteria

**Pipeline:** Always followed by `quality` → `reviewer`

---

### 3. BUILDER Agent (Code Implementation)

**Files:**
- `.claude/agents/builder.md` - Primary (FULL SPEC)
- `agent-rules/agents/builder.md` - Reference (simplified)

**Purpose:** Production code writer following KISS and DDD principles.

**Key Skills:**
- Feature implementation
- Bug fixes and modifications
- Node creation and component development

**Qdrant Usage:** **YES**
- Lines 10-16: "Before implementing, use `qdrant-find` to discover existing patterns"
  ```
  qdrant-find: "similar node implementation"
  qdrant-find: "error handling pattern"
  ```

**Standards (Non-Negotiable):**
- Type hints on ALL functions
- Error handling with loguru (never silent failures)
- Async/await for I/O operations
- < 50 line functions
- No placeholder code (no TODO, pass, ...)

**Model:** opus (advanced reasoning)

**Pipeline:** Always followed by `quality` → `reviewer`

---

### 4. QUALITY Agent (Testing & QA)

**Files:**
- `.claude/agents/quality.md` - Primary (FULL SPEC)
- `agent-rules/agents/quality.md` - Reference (simplified)

**Purpose:** Testing specialist ensuring code quality through comprehensive test coverage.

**Key Skills:**
- Test writing and fixture creation
- Code review for quality
- CI/CD validation

**Qdrant Usage:** **YES**
- Lines 34-38: "Use `qdrant-find` to discover existing test patterns"
  ```
  qdrant-find: "test node execution"
  qdrant-find: "mock playwright page"
  qdrant-find: "async test pattern"
  ```

**Test Structure:**
- `tests/domain/` - Pure unit tests
- `tests/application/` - Mocked infrastructure
- `tests/infrastructure/` - Integration tests
- `tests/nodes/` - Node-specific tests

**External Research:**
- `mcp__exa__get_code_context_exa` - pytest and PySide6 patterns
- `mcp__exa__web_search_exa` - Playwright best practices
- `mcp__Ref__ref_search_documentation` - pytest fixtures and async

---

### 5. REVIEWER Agent (Code Review)

**Files:**
- `.claude/agents/reviewer.md` - Primary (FULL SPEC)
- `agent-rules/agents/reviewer.md` - Reference (simplified)

**Purpose:** Code review gate ensuring quality, correctness, and standards compliance.

**Key Skills:**
- Implementation review
- Security review
- Architecture compliance checking

**Qdrant Usage:** **YES**
- Lines 11-14: "Use `qdrant-find` to find similar implementations for comparison"
  ```
  qdrant-find: "similar node pattern"
  qdrant-find: "existing test patterns"
  ```

**Review Checklist:**
- Type hints present
- Tests included
- Error handling correct
- Async patterns correct
- Architecture compliance
- No security issues

---

### 6. REFACTOR Agent (Code Improvement)

**Files:**
- `.claude/agents/refactor.md` - Primary (FULL SPEC)
- `agent-rules/agents/refactor.md` - Reference (simplified)

**Purpose:** Code improvement specialist for optimization and technical debt reduction without changing functionality.

**Key Skills:**
- Performance optimization
- Code cleanup
- Pattern migration
- Debt reduction

**Qdrant Usage:** **YES**
- Lines 11-14: "Use `qdrant-find` to discover patterns and dependencies"
  ```
  qdrant-find: "class usage pattern"
  qdrant-find: "imports this module"
  ```

**Guidelines:**
- Small, incremental changes
- Tests must pass after each step
- Behavior must be preserved

---

### 7. RESEARCHER Agent (Investigation & Research)

**Files:**
- `.claude/agents/researcher.md` - Primary (FULL SPEC)
- `agent-rules/agents/researcher.md` - Reference (simplified)

**Purpose:** Investigation specialist for bug analysis, requirements research, and technology evaluation.

**Key Skills:**
- Problem investigation
- Requirements gathering
- Technology research
- API/SDK documentation lookup

**Qdrant Usage:** **YES**
- Lines 39-42: "Use `qdrant-find` to understand existing implementations before researching alternatives"
  ```
  qdrant-find: "current implementation of X"
  qdrant-find: "how feature Y works"
  ```

**Research Tools (MCP):**
- `mcp__Ref__ref_search_documentation` - Official docs (Priority 1)
- `mcp__exa__get_code_context_exa` - Code examples (Priority 2)
- `mcp__exa__web_search_exa` - Best practices (Priority 3)

**Strategy:**
1. Known library? → `ref_search_documentation`
2. Need code examples? → `get_code_context_exa`
3. General best practices? → `web_search_exa`

---

### 8. INTEGRATIONS Agent (External Service Integration)

**Files:**
- `.claude/agents/integrations.md` - Primary (FULL SPEC)
- `agent-rules/agents/integrations.md` - Reference (simplified)

**Purpose:** Integration specialist for API, database, and external service connections.

**Key Skills:**
- API integrations
- Database connections
- Authentication flows
- External service setup

**Qdrant Usage:** **YES**
- Lines 45-49: "Use `qdrant-find` to discover existing integration patterns"
  ```
  qdrant-find: "HTTP client integration"
  qdrant-find: "OAuth authentication"
  qdrant-find: "API node implementation"
  ```

**Research Tools (MCP):**
- `mcp__Ref__ref_search_documentation` - API docs (Priority 1)
- `mcp__exa__get_code_context_exa` - SDK examples (Priority 2)
- `mcp__exa__web_search_exa` - Patterns like circuit breaker (Priority 3)

**Key Areas:**
- `infrastructure/http/` - HTTP client
- `infrastructure/database/` - DB connections
- `infrastructure/security/` - Auth/credentials
- `infrastructure/resources/` - Google, LLM, etc.

---

### 9. UI Agent (PySide6 Development)

**Files:**
- `.claude/agents/ui.md` - Primary (FULL SPEC)
- `agent-rules/agents/ui.md` - Reference (simplified)

**Purpose:** PySide6 UI development specialist for Canvas designer interface.

**Key Skills:**
- Widget development
- Theme system implementation
- UX/accessibility improvements

**Qdrant Usage:** **YES**
- Lines 11-15: "Use `qdrant-find` to discover existing UI patterns"
  ```
  qdrant-find: "dialog implementation Qt"
  qdrant-find: "panel widget pattern"
  qdrant-find: "theme styling"
  ```

**Key Areas:**
- `presentation/canvas/` - Main canvas UI
- `presentation/canvas/ui/` - Theme system
- `presentation/canvas/widgets/` - Custom widgets
- `presentation/canvas/visual_nodes/` - Node UI representations

**Standards:**
- Inherit from `BaseWidget`
- Use signal/slot for communication
- Follow theme system (no hardcoded colors)
- Async operations via qasync

---

### 10. DOCS Agent (Documentation)

**Files:**
- `.claude/agents/docs.md` - Primary (FULL SPEC)
- `agent-rules/agents/docs.md` - Reference (simplified)

**Purpose:** Documentation specialist for creating and maintaining project documentation.

**Key Skills:**
- README updates
- API documentation
- User guides and tutorials
- Architecture documentation

**Qdrant Usage:** **YES**
- Lines 11-14: "Use `qdrant-find` to understand code before documenting"
  ```
  qdrant-find: "node implementation details"
  qdrant-find: "API endpoint handlers"
  ```

**Standards:**
- Clear, concise language
- Code examples where helpful
- Keep docs near code
- Update `_index.md` files

---

## Qdrant Usage Statistics

| Agent | Qdrant Used | Location | Query Count |
|-------|-----------|----------|------------|
| **explore** | YES (PRIMARY) | `.claude/agents/explore.md:10-21` | 3 examples |
| **architect** | YES | `.claude/agents/architect.md:32-35` | 2 examples |
| **builder** | YES | `.claude/agents/builder.md:10-16` | 2 examples |
| **quality** | YES | `.claude/agents/quality.md:34-38` | 3 examples |
| **reviewer** | YES | `.claude/agents/reviewer.md:11-14` | 2 examples |
| **refactor** | YES | `.claude/agents/refactor.md:11-14` | 2 examples |
| **researcher** | YES | `.claude/agents/researcher.md:39-42` | 2 examples |
| **integrations** | YES | `.claude/agents/integrations.md:45-49` | 3 examples |
| **ui** | YES | `.claude/agents/ui.md:11-15` | 3 examples |
| **docs** | YES | `.claude/agents/docs.md:11-14` | 2 examples |

**Summary:** All 10 agents use qdrant-find for semantic search. The EXPLORE agent emphasizes it as the PRIMARY tool (95%+ token savings), while others use it as a pattern discovery step before implementation.

---

## Key Insights

### 1. Semantic Search Strategy
- **explore agent** emphasizes qdrant-find as PRIMARY tool for ANY search query
- All other agents use `qdrant-find` for pattern discovery before work begins
- Fallback to Grep/Glob only for exact symbol lookups or when qdrant-find insufficient

### 2. Two-Location Pattern
- `.claude/agents/` contains FULL specifications with YAML frontmatter and detailed guidance
- `agent-rules/agents/` contains simplified reference versions (for documentation/onboarding)
- Primary location is `.claude/agents/` (active agent configurations)

### 3. Agent Pipeline
```
explore (discover)
  ↓
architect/builder (plan/implement)
  ↓
quality (test)
  ↓
reviewer (review)
```

### 4. MCP Tools Usage
- **Architect/Builder:** Use for external design research
- **Integrations:** Heavy MCP tool usage for API research
- **Researcher:** MCP tools are PRIMARY (external sources)
- **Quality:** MCP tools for testing patterns
- **All agents:** Prefer internal qdrant-find + Grep before MCP external search

### 5. Token Optimization
- explore agent's Tier system (Tier 1 < 500 tokens, Tier 2 < 2000, Tier 3 < 5000)
- qdrant-find claimed to save 95%+ tokens vs grep/glob
- Index-first approach (.brain files) before semantic search

---

## File Locations Reference

```
c:\Users\Rau\Desktop\CasareRPA\
├── .claude/agents/                     (PRIMARY - Full specs with YAML)
│   ├── architect.md
│   ├── builder.md
│   ├── docs.md
│   ├── explore.md
│   ├── integrations.md
│   ├── quality.md
│   ├── refactor.md
│   ├── researcher.md
│   ├── reviewer.md
│   └── ui.md
└── agent-rules/agents/                 (SECONDARY - Simplified reference)
    ├── architect.md
    ├── builder.md
    ├── docs.md
    ├── explore.md
    ├── integrations.md
    ├── quality.md
    ├── refactor.md
    ├── researcher.md
    ├── reviewer.md
    └── ui.md
```

---

## Related Configuration Files

- **`.mcp.json`** - MCP tool configuration
- **`.brain/context/current.md`** - Session state (referenced by all agents)
- **`.brain/projectRules.md`** - Coding standards (referenced by builder)
- **`.brain/systemPatterns.md`** - Architecture patterns (used selectively)
- **`CLAUDE.md`** - Project instructions with search strategy guidelines

---

## Recommendations for Future Enhancements

1. **Keep .claude/agents/ as primary source** - Contains full specifications with model hints, context-scope, and detailed guidance
2. **Qdrant indexing** - Ensure `scripts/index_codebase_qdrant.py` runs regularly to keep semantic search current
3. **Agent model assignments:**
   - `explore` → haiku (fast, lightweight)
   - `architect`, `builder`, `quality` → opus (complex reasoning)
   - Others → haiku or sonnet (standard tasks)
4. **Monitor qdrant coverage** - If certain patterns aren't discoverable, update indexing or add to grep fallback
