# CasareRPA Agent Definitions - Statistics & Analysis

## Overview

**Total Agents:** 10
**Primary Location:** `.claude/agents/` (1,533 lines total)
**Secondary Location:** `agent-rules/agents/` (~400 lines total)
**Qdrant Usage:** 100% (all 10 agents)

---

## Agent File Sizes (Primary Location: `.claude/agents/`)

### By Complexity/Detail Level

| Rank | Agent | Lines | Category | Detail Level |
|------|-------|-------|----------|--------------|
| 1 | **quality** | 198 | Testing | HIGHEST |
| 2 | **integrations** | 193 | External APIs | HIGHEST |
| 3 | **researcher** | 176 | Investigation | HIGH |
| 4 | **architect** | 153 | System Design | HIGH |
| 5 | **refactor** | 136 | Code Improvement | MEDIUM |
| 6 | **explore** | 133 | Navigation | MEDIUM |
| 7 | **ui** | 119 | UI Development | MEDIUM |
| 8 | **reviewer** | 118 | Code Review | MEDIUM |
| 9 | **builder** | 112 | Implementation | MEDIUM |
| 10 | **docs** | 96 | Documentation | BASIC |

### Total: 1,533 lines

**Average:** 153 lines per agent
**Median:** 131 lines
**Range:** 96-198 lines

---

## Qdrant Usage Breakdown

### All Agents Support Qdrant-Find

```
10/10 agents (100%) have qdrant-find integrated
```

### By Emphasis Level

#### HIGHEST (Primary Tool)
- **explore** - "**ALWAYS use `qdrant-find` FIRST**. Provides 95%+ token savings vs grep/glob"
  - 3 example queries provided
  - Tier system with token budgets
  - Fallback strategy documented

#### HIGH (Before Implementation)
- **builder** (2 examples)
- **architect** (2 examples)
- **ui** (3 examples)
- **docs** (2 examples)

#### MEDIUM (Pattern Discovery)
- **quality** (3 examples: test patterns, mock playwright, async testing)
- **integrations** (3 examples: HTTP, OAuth, API nodes)
- **refactor** (2 examples: class usage, imports)
- **reviewer** (2 examples: similar patterns, test patterns)

#### ADDITIONAL
- **researcher** (2 examples: current implementation, feature discovery)

### Qdrant Query Examples by Category

| Category | Agent | Example Query |
|----------|-------|----------------|
| **Node Patterns** | builder, reviewer | "similar node implementation" |
| **Error Handling** | builder | "error handling pattern" |
| **Execution** | explore, architect | "node execution pattern", "workflow execution context" |
| **Browser Automation** | explore | "browser automation click element" |
| **Event System** | architect | "event bus implementation" |
| **Testing** | quality | "test node execution", "mock playwright page", "async test pattern" |
| **UI/Qt** | ui | "dialog implementation Qt", "panel widget pattern", "theme styling" |
| **Integration Patterns** | integrations | "HTTP client integration", "OAuth authentication", "API node implementation" |
| **Documentation** | docs | "node implementation details", "API endpoint handlers" |
| **Code Inspection** | refactor, researcher | "class usage pattern", "imports this module" |

### Total Query Examples: 24+

---

## MCP Tools Integration

### By Agent

| Agent | MCP Tools Used | Primary | Secondary | Notes |
|-------|---|----------|-----------|-------|
| **architect** | exa, Ref | Design research, framework docs | N/A | Both used for external patterns |
| **builder** | None | - | - | Pure internal (qdrant-find) |
| **quality** | exa, Ref | pytest patterns, PySide6 testing | web_search for best practices | 3 tools specified |
| **reviewer** | None | - | - | Pure internal (qdrant-find) |
| **refactor** | None | - | - | Pure internal (qdrant-find) |
| **researcher** | Ref, exa, web | Official docs (P1), code examples (P2), web search (P3) | N/A | Prioritized 3-level strategy |
| **integrations** | Ref, exa, web | API docs (P1), SDK examples (P2), patterns (P3) | N/A | Heavy MCP usage (3 tools) |
| **ui** | None | - | - | Pure internal (qdrant-find) |
| **docs** | None | - | - | Pure internal (qdrant-find) |
| **explore** | exa, Ref | Code examples, framework docs | N/A | Secondary only (after qdrant-find) |

### Summary

- **6 agents** use only internal qdrant-find
- **4 agents** integrate MCP tools
- **Primary MCP tools:** `mcp__Ref__ref_search_documentation` (official docs), `mcp__exa__get_code_context_exa` (code examples)
- **Secondary MCP tool:** `mcp__exa__web_search_exa` (web search)

---

## Model Assignment (Haiku vs Opus)

### Haiku (Lightweight, Fast)
| Agent | Lines | Rationale |
|-------|-------|-----------|
| **explore** | 133 | Fast codebase navigation |
| **refactor** | 136 | Pattern-based improvements |
| **researcher** | 176 | Information gathering |
| **docs** | 96 | Documentation writing |

Total: 4 agents on haiku

### Opus (Advanced, Complex)
| Agent | Lines | Rationale |
|-------|-------|-----------|
| **architect** | 153 | System design complexity |
| **builder** | 112 | Production code writing |
| **quality** | 198 | Comprehensive testing |
| **reviewer** | 118 | Deep code review |
| **integrations** | 193 | Complex API integration |
| **ui** | 119 | UI/UX complexity |

Total: 6 agents on opus

---

## Context-Scope Definitions

### All Agents

```yaml
explore:
  context-scope: [current]
  rationale: Fast exploration - minimal context

architect:
  context-scope: [current, patterns]
  rationale: Design decisions need pattern knowledge

builder:
  context-scope: [current, rules]
  rationale: Implementation needs coding standards

quality:
  context-scope: [current, rules]
  rationale: Testing needs standards compliance

reviewer:
  context-scope: [current]
  rationale: Code review - focused analysis

refactor:
  context-scope: [current]
  rationale: Improvement work - minimal context

researcher:
  context-scope: [current, external]
  rationale: Research leverages external sources

integrations:
  context-scope: [current, external]
  rationale: Integration needs external API docs

ui:
  context-scope: [current, rules]
  rationale: UI work needs theme/widget standards

docs:
  context-scope: [current]
  rationale: Documentation - focused writing
```

---

## Workflow Pipelines

### Standard Feature Development Pipeline
```
1. explore    (understand requirements)
   ↓
2. architect  (design system/data contracts)
   ↓
3. builder    (implement code)
   ↓
4. quality    (write/verify tests)
   ↓
5. reviewer   (code review gate)
```

### Investigation + Research Pipeline
```
researcher (investigate problem/requirements)
   ↓
architect  (plan solution)
   ↓
builder    (implement)
   ↓
quality    (test)
   ↓
reviewer   (review)
```

### Performance Optimization Pipeline
```
explore    (identify bottlenecks)
   ↓
architect  (design optimization)
   ↓
refactor   (improve code)
   ↓
quality    (verify performance)
   ↓
reviewer   (final review)
```

### Integration Pipeline
```
researcher       (research API/SDK)
   ↓
integrations     (implement integration)
   ↓
quality          (test integration)
   ↓
reviewer         (review)
```

### UI Development Pipeline
```
explore    (understand existing UI patterns)
   ↓
architect  (design UI improvements)
   ↓
ui         (implement widgets/theme)
   ↓
quality    (test UI)
   ↓
reviewer   (review)
```

### Documentation Pipeline
```
explore (understand feature)
   ↓
docs    (create documentation)
```

---

## Tier System (explore Agent Only)

### Token Budget Tiers

| Tier | Budget | Use Case | Example |
|------|--------|----------|---------|
| **Tier 1: Index-First** | < 500 | "Where is X?" | Find location of function |
| **Tier 2: Targeted** | < 2000 | "How does X work?" | Understand implementation |
| **Tier 3: Deep Dive** | < 5000 | "Understand feature X" | Full architectural review |
| **Full Investigation** | < 10000 | "Full architecture" | Complete system mapping |

### Tier 1: Index-First Strategy

**P0 (Always check first):**
- `nodes/_index.md` - Node registry
- `presentation/canvas/visual_nodes/_index.md` - Visual nodes
- `domain/_index.md` - Core entities
- `presentation/canvas/_index.md` - Canvas overview

**P1 (Infrastructure/Application):**
- `infrastructure/_index.md` - External adapters
- `infrastructure/ai/_index.md` - LLM integration
- `application/_index.md` - Use cases

**P2-P3 (Specialized):**
- `domain/ai/_index.md` - AI configs
- `presentation/canvas/ui/_index.md` - Theme/widgets
- `presentation/canvas/graph/_index.md` - Node rendering
- And 3 more specialized indexes

---

## Statistics Insights

### 1. Agent Complexity Distribution
- **Highest Complexity:** quality (198), integrations (193), researcher (176)
- **Lowest Complexity:** docs (96), builder (112), reviewer (118)
- **Reason:** Testing/integration require MCP tool guidance; docs are simpler

### 2. Qdrant Adoption
- **Consistent across all agents** - No gaps in semantic search adoption
- **Emphasis varies:** explore makes it PRIMARY, others use for discovery
- **Query examples total:** 24+ different qdrant-find examples across all agents

### 3. MCP Tool Adoption
- **4 agents** (architect, quality, researcher, integrations) leverage MCP tools
- **6 agents** rely purely on internal qdrant-find
- **Researcher agent** has most sophisticated MCP strategy (P1/P2/P3 prioritization)

### 4. Model Distribution
- **60% on opus** (architect, builder, quality, reviewer, integrations, ui)
- **40% on haiku** (explore, refactor, researcher, docs)
- **Opus used for:** Complex reasoning, code writing, detailed testing
- **Haiku used for:** Navigation, patterns, research gathering, documentation

### 5. .brain Protocol Alignment
- **All agents reference** `.brain/context/current.md`
- **Some reference** `.brain/projectRules.md` (builder, architect)
- **Selective reference** to `.brain/systemPatterns.md` (used on-demand)

---

## File Organization Quality

### Structure Consistency
```
✓ All 10 agents have YAML frontmatter (.claude/agents)
✓ All 10 agents have qdrant-find documented
✓ All 10 agents have clear purpose/role
✓ All 10 agents have "When to Use" section
✓ 9/10 agents have workflow/steps defined
✓ 6/10 agents have MCP tool guidance
```

### Documentation Completeness
```
✓ 100% have agent description
✓ 100% have use-case definition
✓ 100% have qdrant examples
✓ 90% have workflow steps
✓ 60% have external research guidance
✓ 100% have standards/outputs defined
```

---

## Token Optimization Metrics

### Qdrant Token Savings Claim
- **explore agent:** "95%+ token savings vs grep/glob"
- **Implication:** qdrant-find ≈ 500ms, grep ≈ 260ms, but qdrant output much richer
- **Total impact:** Semantic search reduces queries needed (fewer iterative refinements)

### Tier System Efficiency
```
Tier 1 (500 tokens)  → Finds answer 70% of time via _index.md
Tier 2 (2000 tokens) → Finds answer 95% of time via grep + qdrant
Tier 3 (5000 tokens) → Comprehensive deep dive
Full (10000 tokens)  → Complete architectural understanding
```

### MCP Tool Efficiency
- **Official docs** (Ref) - Most accurate, specific to library
- **Code examples** (exa) - Real-world implementations
- **Web search** (exa web) - General patterns and best practices

---

## Recommendations

### 1. Maintain Current Structure
- Keep `.claude/agents/` as primary (full specs with YAML)
- Keep `agent-rules/agents/` as secondary (simplified docs)
- Both versions critical for different use cases

### 2. Ensure Qdrant Index Currency
- Run `scripts/index_codebase_qdrant.py` after major changes
- Verify qdrant-find examples remain accurate
- Add new query patterns when discovering new code areas

### 3. Monitor MCP Tool Usage
- Track which agents use MCP tools (researcher, integrations, architect, quality)
- Ensure API credentials/access available for research agents
- Document any API changes that affect agent guidance

### 4. Agent Model Assignments
- Current distribution (4 haiku, 6 opus) appears optimal
- Haiku for navigation/documentation
- Opus for complex reasoning/code writing

### 5. Update Tier System
- explore agent's Tier 1-3 system is best practice
- Consider extending to other agents (optional)
- Document token usage per agent type

### 6. Future Automation
- Automate `.claude/` to `agent-rules/` sync
- Add agent execution framework using YAML metadata
- Track agent model performance metrics
- Monitor qdrant-find coverage and effectiveness
