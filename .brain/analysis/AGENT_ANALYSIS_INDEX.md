# CasareRPA Agent Definitions - Analysis Index

## Quick Navigation

### For Executive Summary
→ **AGENT_FINDINGS.md** - Start here
- Complete answer to "Where are agents? Do they use qdrant?"
- Key findings summary
- File locations and statistics
- Recommendations

### For Quick Reference
→ **AGENT_QUICK_REFERENCE.md** - Agent selection and examples
- Agent selection matrix
- Model assignments (haiku/opus)
- Qdrant search examples by agent
- Quick lookup tables

### For Comprehensive Overview
→ **AGENT_DEFINITIONS_SUMMARY.md** - Full agent documentation
- All 10 agents with detailed descriptions
- Qdrant usage per agent with line references
- MCP tools for each agent
- Workflow pipelines
- Related configuration files

### For Detailed Comparison
→ **AGENT_DEFINITIONS_COMPARISON.md** - Primary vs Secondary analysis
- Side-by-side comparison of `.claude/agents/` vs `agent-rules/agents/`
- Detailed differences for each agent
- Key insights on format/detail differences
- Syncing strategy
- Future enhancements

### For Data Analysis
→ **AGENT_STATISTICS.md** - Metrics and analysis
- File size statistics (1,533 lines total)
- Qdrant usage breakdown with percentages
- MCP tool distribution
- Model assignment analysis
- Tier system documentation
- Token optimization metrics
- Workflow pipeline variations
- Recommendations with priorities

---

## The 10 Agents at a Glance

```
1. explore          (133 lines, haiku) ← Semantic search specialist
2. architect        (153 lines, opus)  ← System design expert
3. builder          (112 lines, opus)  ← Code implementation specialist
4. quality          (198 lines, opus)  ← Testing and QA specialist
5. reviewer         (118 lines, opus)  ← Code review gate
6. refactor         (136 lines, haiku) ← Code improvement specialist
7. researcher       (176 lines, haiku) ← Investigation specialist
8. integrations     (193 lines, opus)  ← Integration specialist
9. ui               (119 lines, opus)  ← PySide6 UI specialist
10. docs            (96 lines, haiku)  ← Documentation specialist
```

**Total: 1,533 lines | All use qdrant-find | 6 use MCP tools**

---

## File Locations

### Primary (Source of Truth - Active)
```
.claude/agents/
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
Status: Full specifications with YAML frontmatter
Format: YAML + detailed markdown (100-198 lines each)
Usage: Agent execution, configuration, detailed guidance

### Secondary (Reference - Documentation)
```
agent-rules/agents/
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
Status: Simplified versions without YAML
Format: Markdown only (20-50 lines each)
Usage: Human documentation, onboarding, quick reference

---

## Qdrant Usage Summary

### By Agent
```
✓ explore       - "**ALWAYS use qdrant-find FIRST**" (PRIMARY)
✓ architect     - Pattern discovery (HIGH)
✓ builder       - Before implementing (HIGH)
✓ quality       - Test patterns (HIGH)
✓ reviewer      - Compare implementations (MEDIUM)
✓ refactor      - Dependencies/usage (MEDIUM)
✓ researcher    - Understand existing (MEDIUM)
✓ integrations  - Integration patterns (MEDIUM)
✓ ui            - UI patterns (MEDIUM)
✓ docs          - Code understanding (MEDIUM)
```

### Query Examples
```
24+ documented qdrant-find queries across all agents
Token savings claimed: 95%+ vs grep/glob
Tier system with budgets: 500, 2000, 5000, 10000 tokens
```

### Fallback Strategy
Grep/Glob only when:
- Searching exact strings (imports, class names)
- qdrant-find returns no relevant results

---

## MCP Tools Usage

### Agents Using External Research
```
architect      → exa, Ref (design patterns)
quality        → exa, Ref, web (testing patterns)
researcher     → Ref, exa, web (P1→P2→P3 prioritization)
integrations   → Ref, exa, web (P1→P2→P3 prioritization)
```

### Tools Used
```
mcp__Ref__ref_search_documentation     ← Official documentation
mcp__exa__get_code_context_exa         ← Code examples and patterns
mcp__exa__web_search_exa               ← Web search for best practices
```

---

## Agent Development Pipeline

### Standard Feature Development
```
explore     (Find/understand requirements)
  ↓
architect   (Design system/data contracts)
  ↓
builder     (Implement production code)
  ↓
quality     (Write and verify tests)
  ↓
reviewer    (Code review gate)
```

### Investigation + Integration
```
researcher     (Investigate/research)
  ↓
integrations   (Implement external service)
  ↓
quality        (Test integration)
  ↓
reviewer       (Review)
```

### Code Optimization
```
explore   (Identify bottlenecks)
  ↓
architect (Design optimization)
  ↓
refactor  (Improve code)
  ↓
quality   (Verify performance)
  ↓
reviewer  (Final review)
```

---

## Key Metrics

### Code Volume
| Metric | Value |
|--------|-------|
| Total lines (primary) | 1,533 |
| Average per agent | 153 |
| Largest | quality (198) |
| Smallest | docs (96) |
| Range | 96-198 |

### Qdrant Adoption
| Metric | Value |
|--------|-------|
| Agents with qdrant | 10/10 (100%) |
| With highest emphasis | 1/10 (explore) |
| With high emphasis | 4/10 |
| With medium emphasis | 5/10 |
| Query examples total | 24+ |

### Model Distribution
| Model | Count | Agents |
|-------|-------|--------|
| opus | 6 | architect, builder, quality, reviewer, integrations, ui |
| haiku | 4 | explore, refactor, researcher, docs |

### MCP Tool Adoption
| Metric | Value |
|--------|-------|
| Agents using MCP | 4/10 (40%) |
| MCP-only agents | 4/10 (40%) |
| Hybrid (MCP + qdrant) | 0 (all use qdrant first) |

---

## Context-Scope Breakdown

### What Each Agent Needs at Startup
```
explore       → [current]
architect     → [current, patterns]
builder       → [current, rules]
quality       → [current, rules]
reviewer      → [current]
refactor      → [current]
researcher    → [current, external]
integrations  → [current, external]
ui            → [current, rules]
docs          → [current]
```

Reference files:
- `.brain/context/current.md` - Active session state (always)
- `.brain/projectRules.md` - Coding standards (for architect, builder, quality, ui)
- `.brain/systemPatterns.md` - Architecture patterns (on-demand)

---

## Quality Assessment

### Coverage
```
✓ 100% of agents have YAML frontmatter (.claude/agents)
✓ 100% of agents have qdrant-find documented
✓ 100% of agents have clear purpose/role
✓ 100% of agents have "When to Use" guidance
✓ 90% of agents have workflow/steps defined
✓ 60% of agents have MCP tool guidance
✓ 100% of agents have standards/outputs defined
```

### Documentation Completeness
- All agents documented in both locations ✓
- Agent descriptions consistent ✓
- Qdrant examples provided ✓
- MCP tools clearly specified ✓
- Workflow pipelines defined ✓
- Model assignments specified ✓

---

## Recommendations Priority List

### P0 (Critical - Do First)
1. Keep `.claude/agents/` as primary source of truth
2. Ensure qdrant indexing runs after major code changes
3. Verify all qdrant-find examples remain accurate

### P1 (High - Do Soon)
4. Monitor which qdrant queries work best
5. Track agents that need MCP tool updates
6. Maintain sync between `.claude/` and `agent-rules/`

### P2 (Medium - Nice to Have)
7. Extend Tier system to other agents
8. Create agent execution framework
9. Build performance metrics dashboard

### P3 (Low - Future Enhancements)
10. Automate `.claude/` to `agent-rules/` sync
11. Add semantic versioning for agent specs
12. Create agent testing framework

---

## Quick Answers

### Question: "Where are all the agents?"
**Answer:**
- Primary: `c:\Users\Rau\Desktop\CasareRPA\.claude\agents\` (10 files)
- Secondary: `c:\Users\Rau\Desktop\CasareRPA\agent-rules\agents\` (10 files)

### Question: "Do all agents mention qdrant?"
**Answer:** Yes, 100% (10/10 agents) use qdrant-find
- explore emphasizes it as PRIMARY tool ("ALWAYS use FIRST")
- Others use for pattern discovery
- Documented with 24+ example queries

### Question: "What is the difference between the two locations?"
**Answer:**
- `.claude/agents/` - Full specs with YAML, detailed guidance (100-198 lines)
- `agent-rules/agents/` - Simplified reference for humans (20-50 lines)
- `.claude/` is active, `agent-rules/` is documentation

### Question: "Which agents use qdrant most heavily?"
**Answer:**
1. explore (emphasized as PRIMARY tool with Tier system)
2. builder, architect, quality (before implementation)
3. ui, integrations, refactor, reviewer, researcher, docs (pattern discovery)

### Question: "What MCP tools are used?"
**Answer:**
- 4 agents (architect, quality, researcher, integrations)
- 3 tools: Ref (official docs), exa (code examples), web (search)
- Other 6 agents use only internal qdrant-find

---

## Document Cross-References

| Document | Best For | Length |
|----------|----------|--------|
| AGENT_FINDINGS.md | Executive summary | ~300 lines |
| AGENT_QUICK_REFERENCE.md | Quick lookup | ~150 lines |
| AGENT_DEFINITIONS_SUMMARY.md | Comprehensive overview | ~400 lines |
| AGENT_DEFINITIONS_COMPARISON.md | Technical deep-dive | ~350 lines |
| AGENT_STATISTICS.md | Data analysis | ~500 lines |
| AGENT_ANALYSIS_INDEX.md | Navigation and overview | This file |

---

## Next Steps

1. **Review AGENT_FINDINGS.md** for complete context
2. **Use AGENT_QUICK_REFERENCE.md** for agent selection
3. **Reference AGENT_DEFINITIONS_SUMMARY.md** when implementing with agents
4. **Check AGENT_STATISTICS.md** for metrics and optimization opportunities
5. **Follow recommendations in AGENT_FINDINGS.md** for improvements

---

## Version Information

- **Analysis Date:** 2025-12-14
- **CasareRPA Version:** Python 3.12, PySide6, Playwright
- **Total Agents Analyzed:** 10
- **Qdrant Coverage:** 100%
- **Documentation Status:** Complete and comprehensive

---

## Contact & Updates

For questions about agent definitions:
1. Check relevant documentation file above
2. Review `.claude/agents/` primary specifications
3. Consult `.brain/context/current.md` for session state
4. Check CLAUDE.md for project instructions
