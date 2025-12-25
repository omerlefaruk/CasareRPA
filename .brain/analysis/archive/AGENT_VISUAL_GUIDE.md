# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# CasareRPA Agent Framework - Visual Guide

## Agent Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CASARPA AGENT FRAMEWORK                           │
│                   All 10 Agents Use Qdrant-Find                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐    ┌──────────────────────────────┐
│   .claude/agents/ (PRIMARY)      │    │  agent-rules/agents/ (REF)   │
│   - Full Specifications          │    │  - Simplified Docs           │
│   - YAML Frontmatter             │    │  - No YAML                   │
│   - 1,533 lines total            │    │  - ~400 lines total          │
│   - 100-198 lines per agent      │    │  - 20-50 lines per agent     │
│   - Model assignment (haiku/opus)│    │  - No model info             │
│   - Active Execution             │    │  - Documentation Only        │
└──────────────────────────────────┘    └──────────────────────────────┘
```

---

## Qdrant Integration Map

```
                    QDRANT-FIND (Semantic Search)
                           |
                           v
    ┌──────────────────────────────────────────────────────────┐
    │         Used by ALL 10 Agents (100% Adoption)           │
    └──────────────────────────────────────────────────────────┘
           |                |                |
           v                v                v
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │   explore   │  │  architect   │  │   builder    │
    │  (PRIMARY)  │  │   (HIGH)     │  │   (HIGH)     │
    │  "ALWAYS    │  │  Pattern     │  │  "Before     │
    │   FIRST"    │  │  discovery   │  │   impl"      │
    └─────────────┘  └──────────────┘  └──────────────┘
           |                |                |
    ┌──────────────────────────────────────────────────────────┐
    │  Tier System (explore only)                              │
    │  Tier 1: 500 tokens   → Index-first (70% hit rate)      │
    │  Tier 2: 2000 tokens  → Grep+qdrant (95% hit rate)      │
    │  Tier 3: 5000 tokens  → Deep files                      │
    │  Full:   10000 tokens → Architecture review             │
    └──────────────────────────────────────────────────────────┘
           |
           v
    Fallback: Grep/Glob only if qdrant returns nothing
```

---

## Agent Development Pipeline Flow

### Standard Feature Development Workflow

```
    ┌─────────────┐
    │   START     │
    │ New Feature │
    └──────┬──────┘
           │
           v
    ┌──────────────────────────────┐
    │ EXPLORE (haiku, 133 lines)   │
    │ - Find patterns              │
    │ - Understand requirements    │
    │ - qdrant-find: semantic      │
    │ - Index-first approach       │
    └──────┬───────────────────────┘
           │
           v
    ┌──────────────────────────────┐
    │ ARCHITECT (opus, 153 lines)  │
    │ - Design system              │
    │ - Plan features              │
    │ - qdrant-find: patterns      │
    │ - MCP tools: research        │
    └──────┬───────────────────────┘
           │
           v
    ┌──────────────────────────────┐
    │ BUILDER (opus, 112 lines)    │
    │ - Write production code      │
    │ - Follow patterns            │
    │ - qdrant-find: before impl   │
    │ - Complete, tested code      │
    └──────┬───────────────────────┘
           │
           v
    ┌──────────────────────────────┐
    │ QUALITY (opus, 198 lines)    │
    │ - Write comprehensive tests  │
    │ - Verify coverage            │
    │ - qdrant-find: test patterns │
    │ - MCP tools: testing best-pr │
    └──────┬───────────────────────┘
           │
           v
    ┌──────────────────────────────┐
    │ REVIEWER (opus, 118 lines)   │
    │ - Code review gate           │
    │ - Quality assurance          │
    │ - qdrant-find: comparison    │
    │ - Approve/reject             │
    └──────┬───────────────────────┘
           │
           v
    ┌──────────────┐
    │  MERGE/SHIP  │
    └──────────────┘
```

### Alternative Pipelines

```
Investigation Pipeline:
researcher → architect → builder → quality → reviewer

Integration Pipeline:
researcher → integrations → quality → reviewer

Optimization Pipeline:
explore → architect → refactor → quality → reviewer

UI Development:
explore → architect → ui → quality → reviewer

Documentation:
explore → docs
```

---

## Agent Complexity & Model Distribution

```
                    AGENT SIZE & COMPLEXITY

    198 ├─ quality ━━━━━━━━━━━━━━━━━━━━━━ (opus)
    193 ├─ integrations ━━━━━━━━━━━━━━━━━ (opus)
    176 ├─ researcher ━━━━━━━━━━━━━━━━━ (haiku)
    153 ├─ architect ━━━━━━━━━━━━━━━━ (opus)
    136 ├─ refactor ━━━━━━━━━━━━━━ (haiku)
    133 ├─ explore ━━━━━━━━━━━━━━ (haiku)
    119 ├─ ui ━━━━━━━━━━━━━━ (opus)
    118 ├─ reviewer ━━━━━━━━━━━━━ (opus)
    112 ├─ builder ━━━━━━━━━━━ (opus)
     96 └─ docs ━━━━━━━━━ (haiku)

    Models:
    ┌────────────────────────────────────┐
    │ Opus (60%):   architect, builder,  │
    │              quality, reviewer,    │
    │              integrations, ui      │
    │ Haiku (40%):  explore, refactor,   │
    │              researcher, docs      │
    └────────────────────────────────────┘

    Complexity Pattern:
    Complex (opus):    design, code, testing, review, integration
    Simple (haiku):    navigation, optimization, research, docs
```

---

## Qdrant Usage Heat Map

```
        QDRANT USAGE INTENSITY BY AGENT

    explore     ████████████████████ (PRIMARY - "ALWAYS FIRST")
    architect   ████████████ (HIGH - Before design)
    builder     ████████████ (HIGH - Before implementation)
    quality     ████████████ (HIGH - Pattern discovery)
    ui          ████████ (MEDIUM - UI patterns)
    integrations████████ (MEDIUM - Integration patterns)
    refactor    ████████ (MEDIUM - Dependency analysis)
    reviewer    ████████ (MEDIUM - Comparison)
    researcher  ████████ (MEDIUM - Current state understanding)
    docs        ████████ (MEDIUM - Code understanding)

    Legend:
    ████████████████████ = PRIMARY (explore)
    ████████████          = HIGH (architect, builder, quality)
    ████████              = MEDIUM (ui, integrations, refactor, reviewer, researcher, docs)

    Total Qdrant Queries:  24+ documented examples across all agents
    Token Savings Claim:   95%+ vs grep/glob
    Coverage:              100% of agents (10/10)
```

---

## MCP Tool Integration Map

```
        MCP TOOLS FOR EXTERNAL RESEARCH

    ┌─────────────────────────────────────────────────┐
    │         MCP Tools (4 agents, 40% adoption)      │
    └─────────────────────────────────────────────────┘
         │                    │                    │
         v                    v                    v
    ┌──────────┐         ┌──────────┐         ┌──────────┐
    │architect │         │ quality  │         │researcher│
    │exa, Ref  │         │exa,Ref   │         │Ref>exa   │
    └──────────┘         │web       │         │>web      │
                         └──────────┘         └──────────┘
                                                   |
                                                   v
                                          ┌──────────────┐
                                          │integrations  │
                                          │Ref>exa>web   │
                                          │(Prioritized) │
                                          └──────────────┘

    ┌─────────────────────────────────────────────────┐
    │ Pure Qdrant-Find (6 agents, 60%)                │
    │ builder, reviewer, refactor, ui, docs, explore │
    └─────────────────────────────────────────────────┘

    Tools Used:
    ┌─────────────────────────────────────────┐
    │ Ref:  ref_search_documentation          │
    │       Official API and framework docs   │
    │                                         │
    │ Exa:  get_code_context_exa              │
    │       Real-world code examples          │
    │                                         │
    │ Web:  exa_web_search_exa                │
    │       Best practices and patterns       │
    └─────────────────────────────────────────┘
```

---

## Tier System (explore Agent Only)

```
             TOKEN BUDGET TIERS FOR CODEBASE EXPLORATION

    Budget     Search Scope         Success Rate    Example Query
    ──────────────────────────────────────────────────────────────────
    500 tokens  Index-first          70%            Where is function X?
                _index.md files      Quick answers  Find BrowserNode
                (Tier 1)                           Location lookup

    2,000       Grep + qdrant-find   95%            How does X work?
    tokens      Targeted search      Deep answer    Understand pattern
                (Tier 2)             Coverage       Multiple sources

    5,000       Deep dives           98%            Full feature
    tokens      Full file reads      Complete       understanding
                (Tier 3)             Context        Architecture review

    10,000      Comprehensive        99%            Complete system
    tokens      All sources          Thorough       architecture
                (Full)               Understanding  mapping

    Fast Path (explore-first):
    ┌─────────────────────────────────────────┐
    │ 1. Check .brain/context/current.md      │
    │ 2. Read relevant _index.md (P0)         │
    │ 3. Use qdrant-find for pattern search   │
    │ 4. Fallback to grep for exact matches   │
    │ 5. Only then read full files (Tier 3)   │
    └─────────────────────────────────────────┘
```

---

## Agent Context Scope Breakdown

```
            WHAT EACH AGENT NEEDS AT STARTUP

    explore       [current]              ← Session state only
    architect     [current, patterns]    ← Session + architecture
    builder       [current, rules]       ← Session + standards
    quality       [current, rules]       ← Session + standards
    reviewer      [current]              ← Session state only
    refactor      [current]              ← Session state only
    researcher    [current, external]    ← Session + MCP tools
    integrations  [current, external]    ← Session + MCP tools
    ui            [current, rules]       ← Session + UI standards
    docs          [current]              ← Session state only

    Reference Files:
    ┌────────────────────────────────────────┐
    │ .brain/context/current.md (always)     │
    │ ├─ Active session state                │
    │ └─ ~25 lines per session               │
    │                                        │
    │ .brain/projectRules.md (if needed)     │
    │ ├─ Coding standards                    │
    │ └─ Needed by: architect, builder, ui   │
    │                                        │
    │ .brain/systemPatterns.md (optional)    │
    │ ├─ Architecture patterns               │
    │ └─ Needed by: architect                │
    └────────────────────────────────────────┘
```

---

## File Organization Visual

```
c:\Users\Rau\Desktop\CasareRPA\
│
├── PRIMARY AGENT SPECS:
│   └── .claude/agents/
│       ├── architect.md       ← System design (opus, 153 lines)
│       ├── builder.md         ← Implementation (opus, 112 lines)
│       ├── quality.md         ← Testing (opus, 198 lines)
│       ├── reviewer.md        ← Code review (opus, 118 lines)
│       ├── integrations.md    ← APIs (opus, 193 lines)
│       ├── ui.md              ← UI dev (opus, 119 lines)
│       ├── explore.md         ← Navigation (haiku, 133 lines)
│       ├── refactor.md        ← Optimization (haiku, 136 lines)
│       ├── researcher.md      ← Investigation (haiku, 176 lines)
│       └── docs.md            ← Documentation (haiku, 96 lines)
│
├── SECONDARY REFERENCE:
│   └── agent-rules/agents/
│       ├── architect.md
│       ├── builder.md
│       ├── quality.md
│       └── ... (10 simplified versions)
│
├── CONFIGURATION:
│   ├── .claude.md             ← Agent instructions (THIS FILE)
│   ├── CLAUDE.md              ← Project instructions
│   └── .mcp.json              ← MCP tool config
│
└── DOCUMENTATION (NEW):
    ├── AGENT_FINDINGS.md                  ← Executive summary
    ├── AGENT_QUICK_REFERENCE.md           ← Quick lookup
    ├── AGENT_DEFINITIONS_SUMMARY.md       ← Comprehensive
    ├── AGENT_DEFINITIONS_COMPARISON.md    ← Primary vs Secondary
    ├── AGENT_STATISTICS.md                ← Data analysis
    ├── AGENT_ANALYSIS_INDEX.md            ← Navigation guide
    └── AGENT_VISUAL_GUIDE.md              ← This file
```

---

## Agent Selection Decision Tree

```
                    WHICH AGENT TO USE?

                         START
                           |
                           v
                   What's your task?
                    /    |    |    \
                   /     |    |     \
          Explore?  Code?  Test? Review?
            /         |      |        \
           /          |      |         \
          v           v      v          v
        explore    architect  quality   reviewer
                     |         |
              Implement?    Tests OK?
                  |            |
                  v            v
                builder      MERGE
                  |
              Code OK?
                  |
                  v
                quality
                  |
              Tests OK?
                  |
                  v
                reviewer
                  |
                 OK?
                  |
                  v
                MERGE

Alternative Paths:
├─ API Integration?    → researcher → integrations → quality → reviewer
├─ UI Development?     → explore → architect → ui → quality → reviewer
├─ Performance Issue?  → explore → architect → refactor → quality → reviewer
├─ Investigation?      → researcher → ...
├─ Documentation?      → docs
└─ Code Cleanup?       → refactor → quality → reviewer
```

---

## Summary Statistics Visual

```
╔════════════════════════════════════════════════════════════╗
║         CASARPA AGENT FRAMEWORK AT A GLANCE              ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Total Agents:              10                            ║
║  Primary Location:          .claude/agents/               ║
║  Total Lines:               1,533                         ║
║  Average per Agent:         153                           ║
║                                                            ║
║  Qdrant Coverage:           10/10 (100%)                  ║
║  Primary Emphasis:          1/10 (explore)               ║
║  High Emphasis:             4/10 (architect, builder, ...) ║
║  Medium Emphasis:           5/10 (refactor, ui, ...)     ║
║                                                            ║
║  MCP Tool Usage:            4/10 (40%)                    ║
║  Pure Qdrant:               6/10 (60%)                    ║
║                                                            ║
║  Model Distribution:                                       ║
║    Opus (Advanced):         6 agents                       ║
║    Haiku (Lightweight):     4 agents                       ║
║                                                            ║
║  Qdrant Query Examples:     24+                           ║
║  Token Savings Claim:       95%+ vs grep/glob             ║
║                                                            ║
║  Documentation Created:     6 comprehensive files         ║
║  Status:                    Production-Ready              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Next Steps Visual Path

```
                    GETTING STARTED

    1. Read Quick Answer
       ↓
    2. Check AGENT_FINDINGS.md (Executive Summary)
       ↓
    3. Use AGENT_QUICK_REFERENCE.md (Lookup Agent)
       ↓
    4. Read AGENT_DEFINITIONS_SUMMARY.md (Full Details)
       ↓
    5. Follow AGENT_DEFINITIONS_COMPARISON.md (Sync Strategy)
       ↓
    6. Reference AGENT_STATISTICS.md (Metrics & Optimization)
       ↓
    7. Use AGENT_ANALYSIS_INDEX.md (Navigation Guide)
       ↓
    8. Implement Recommendations
```

---

## Key Takeaways

```
✓ All 10 agents use qdrant-find for semantic search
✓ explore agent emphasizes it as PRIMARY tool (95%+ savings)
✓ Two-tier definition system: active + documentation
✓ 100% agent coverage with consistent patterns
✓ Strategic MCP tool integration (40% of agents)
✓ Clear workflow pipelines for different task types
✓ Token optimization strategies documented
✓ Production-ready, mature framework
```
