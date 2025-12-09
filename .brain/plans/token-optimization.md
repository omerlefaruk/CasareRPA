# Token Optimization Plan

**Created**: 2025-12-09
**Status**: COMPLETE (P0 implemented)
**Impact**: High (affects all agent operations)

---

## Problem Statement

Current token usage is inefficient across planning, searching, and execution phases:

| Issue | Current State | Token Impact |
|-------|---------------|--------------|
| `activeContext.md` bloat | 2,240 lines (95 KB) | ~25K tokens loaded per agent |
| All agents read same context | 3 files on startup | Redundant reads |
| Large UI files | 2,000-4,300 lines each | Full file reads waste tokens |
| No context scoping | All agents get all context | Over-fetching |

---

## Optimization Strategy

### Phase 1: Context File Restructuring (Quick Wins)

**1.1 Split activeContext.md**

```
.brain/
├── context/
│   ├── current.md          # Only active session (< 50 lines)
│   ├── recent.md           # Last 3 completed tasks (~100 lines)
│   └── archive/
│       └── 2025-12-week50.md  # Historical (not loaded by default)
├── systemPatterns.md       # Keep as-is (stable reference)
└── projectRules.md         # Keep as-is (stable reference)
```

**Token savings**: ~20K tokens per agent invocation

**1.2 Agent-Specific Context Loading**

| Agent Type | Required Context | Skip |
|------------|------------------|------|
| explore | current.md only | patterns, rules |
| architect | current.md, patterns | rules (knows them) |
| builder | current.md, rules | patterns |
| quality | current.md only | patterns, rules |
| reviewer | current.md only | patterns, rules |

**Implementation**: Add `context-scope` to agent front matter:
```yaml
---
name: explore
context-scope: [current]  # Only loads .brain/context/current.md
---
```

---

### Phase 2: Search Optimization

**2.1 Create Module Index Files**

Add `_index.md` to key directories for fast discovery:

```
src/casare_rpa/nodes/_index.md
  Contains: Node name → file path → one-line description
  Size: ~50 lines (vs reading all 132 node files)
```

```
src/casare_rpa/presentation/canvas/_index.md
  Contains: Widget/Dialog → file path → purpose
  Size: ~80 lines (vs 277 files)
```

**Token savings**: 90% reduction when searching for "where is X implemented"

**2.2 Standardize Search Patterns**

Create `.claude/search-patterns.json`:
```json
{
  "find_node": "grep 'class.*Node.*:' nodes/",
  "find_widget": "grep 'class.*Widget\\|Dialog' presentation/",
  "find_service": "grep 'class.*Service' application/",
  "find_tests": "glob 'tests/**/test_*.py'"
}
```

---

### Phase 3: Large File Decomposition

**3.1 Priority Splits** (files > 2000 lines)

| File | Lines | Split Into |
|------|-------|------------|
| `node_graph_widget.py` | 2,483 | `graph_core.py`, `graph_events.py`, `graph_rendering.py`, `graph_selection.py` |
| `node_widgets.py` | 2,214 | `base_widgets.py`, `input_widgets.py`, `output_widgets.py`, `custom_widgets.py` |
| `dialog_nodes.py` | 4,303 | Split by dialog type (message, input, file, etc.) |
| `unified_selector_dialog.py` | 2,598 | `selector_ui.py`, `selector_logic.py`, `selector_preview.py` |

**Token savings**: When editing a specific feature, load only relevant module (~500 lines vs 2500)

**3.2 Lazy Import Pattern**

For large modules, use lazy imports:
```python
# presentation/canvas/graph/__init__.py
def get_node_graph_widget():
    from .graph_core import NodeGraphWidget
    return NodeGraphWidget
```

---

### Phase 4: Agent Protocol Optimization

**4.1 Tiered Exploration**

Update explore agent with explicit tiers:

```markdown
## Exploration Tiers (MANDATORY)

### Tier 1: Index-First (< 500 tokens)
1. Check _index.md files first
2. Only proceed to Tier 2 if index insufficient

### Tier 2: Targeted Search (< 2000 tokens)
1. Grep for specific pattern
2. Read only matched file sections (offset/limit)

### Tier 3: Deep Dive (< 5000 tokens)
1. Full file reads only when modifying
2. Read related test files
```

**4.2 Response Compression**

Add to all agent configs:
```markdown
## Output Rules
- Use tables over prose
- Max 10 lines per finding
- Reference files as `file.py:line` not full paths
- Skip obvious context ("As we can see..." etc.)
```

---

### Phase 5: Execution Optimization

**5.1 Edit-Only File Loading**

Before editing, use Read with offset/limit:
```python
# Instead of reading entire 2500-line file:
Read(file_path, offset=500, limit=100)  # Just the section to modify
```

**5.2 Parallel Tool Calls**

Enforce parallel reads when files are independent:
```
# BAD: Sequential (3 round trips)
Read(file_a) → Read(file_b) → Read(file_c)

# GOOD: Parallel (1 round trip)
[Read(file_a), Read(file_b), Read(file_c)]
```

**5.3 Context Caching Protocol**

Add to CLAUDE.md:
```markdown
## Context Caching
- If you read a file earlier in this session, don't re-read it
- Reference by: "As seen in file.py (read above)..."
- Exception: If user says file changed, re-read it
```

---

## Implementation Order

| Priority | Task | Effort | Token Savings |
|----------|------|--------|---------------|
| P0 | Split activeContext.md | 30 min | ~20K/agent |
| P0 | Add context-scope to agents | 20 min | ~15K/agent |
| P1 | Create _index.md files | 1 hour | ~5K/search |
| P1 | Update explore agent tiers | 30 min | ~3K/exploration |
| P2 | Split large UI files | 4 hours | ~8K/edit |
| P2 | Add search-patterns.json | 15 min | Cognitive overhead |
| P3 | Lazy import pattern | 2 hours | Startup time |

---

## Metrics to Track

1. **Tokens per agent invocation** (before/after)
2. **Files read per task** (should decrease 50%)
3. **Round trips** (parallel vs sequential)
4. **Context reload frequency** (should be zero)

---

## Rollback Plan

All changes are additive:
- Old import paths continue to work
- activeContext.md can be regenerated from archive
- Index files are supplementary (not required)

---

## Files to Create/Modify

### New Files
- `.brain/context/current.md`
- `.brain/context/recent.md`
- `.brain/context/archive/` (directory)
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/presentation/canvas/_index.md`
- `.claude/search-patterns.json`

### Modified Files
- `.claude/agents/explore.md` (add context-scope, tiers)
- `.claude/agents/architect.md` (add context-scope)
- `.claude/agents/builder.md` (add context-scope)
- `.claude/agents/quality.md` (add context-scope)
- `.claude/agents/reviewer.md` (add context-scope)
- `CLAUDE.md` (add context caching protocol)

---

## Success Criteria

- [ ] Agent startup loads < 5K tokens of context (vs current ~25K)
- [ ] Code searches find targets in < 3 tool calls
- [ ] File edits read only affected sections
- [ ] Zero redundant file reads per session
