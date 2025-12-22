# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Rules Directory Structure & Cross-Reference Analysis

**Analysis Date**: 2025-12-14
**Total Files Analyzed**: 61 markdown files across 2 rule systems
**Status**: CRITICAL ISSUES DETECTED - Missing backlinks and duplicate systems

---

## Executive Summary

CasareRPA maintains **TWO SEPARATE but INTERCONNECTED rule systems**:

1. **`.claude/rules/`** (8 files) - Core implementation rules
2. **`agent-rules/rules/`** (12 files) - Agent execution & workflow rules

**Critical Finding**: The systems reference each other inconsistently. `.claude/rules/` files do NOT reference `agent-rules/`, and vice versa. `CLAUDE.md` is the only file linking to both systems.

---

## Directory Structure

```
CasareRPA/
├── CLAUDE.md                          [Hub document - main entry point]
├── .claude/
│   ├── rules/                         [8 core rules]
│   │   ├── 01-core.md                 [5-phase workflow, KISS principle]
│   │   ├── 02-architecture.md         [DDD 2025, layer patterns]
│   │   ├── 03-nodes.md                [Node development checklist]
│   │   ├── 04-ddd-events.md           [Typed event system reference]
│   │   ├── ui/
│   │   │   ├── theme-rules.md         [THEME.* usage]
│   │   │   └── signal-slot-rules.md   [@Slot decorator, Qt patterns]
│   │   └── nodes/
│   │       └── node-registration.md   [5-step registration checklist]
│   ├── agents/                        [10 agent definitions]
│   │   ├── explore.md, builder.md, architect.md, ... (no rules refs)
│   ├── commands/                      [4 command definitions]
│   │   └── implement-feature.md, fix-feature.md, ...
│   └── skills/                        [12 skill definitions]
│
└── agent-rules/
    ├── rules/                         [12 rules files - PARALLEL to .claude/rules]
    │   ├── 00-role.md                 [Agent role & philosophy]
    │   ├── 01-workflow.md             [5-phase workflow (duplicate)]
    │   ├── 02-coding-standards.md     [Code quality]
    │   ├── 03-architecture.md         [DDD patterns (duplicate)]
    │   ├── 04-agents.md               [Agent invocation]
    │   ├── 05-triggers.md             [Command triggers]
    │   ├── 06-enforcement.md          [Rules enforcement]
    │   ├── 07-tools.md                [Tool usage, MCP tools]
    │   ├── 08-token-optimization.md   [Token budgets]
    │   ├── 09-brain-protocol.md       [.brain/ directory protocol]
    │   ├── 10-node-workflow.md        [Node implementation flow]
    │   ├── 11-node-templates.md       [Node template reference]
    │   ├── agents/                    [Agent definitions - mirrors .claude]
    │   ├── commands/                  [Command definitions]
    │   └── skills/                    [Skill definitions]
    └── _index.md                      [MISSING]
```

---

## Rule Files Comparison

### .claude/rules/ System (8 files)

| File | Purpose | Link Backlinks | .brain Refs |
|------|---------|---|---|
| **01-core.md** | 5-phase workflow, KISS, error handling, THEME | ❌ NO to CLAUDE.md | ✅ `.brain/context/current.md` |
| **02-architecture.md** | DDD 2025, layers, patterns, aggregates | ❌ NO to CLAUDE.md | ✅ `.brain/{context,projectRules,systemPatterns,docs/*}` |
| **03-nodes.md** | Node creation workflow, port API, categories | ❌ NO to CLAUDE.md | ✅ `.brain/docs/{node-templates,node-checklist}.md` |
| **04-ddd-events.md** | Typed events, EventBus, event classes | ❌ NO to CLAUDE.md | ❌ NONE |
| **ui/theme-rules.md** | THEME constant usage, no hardcoded colors | ❌ NO to CLAUDE.md | ✅ `.brain/docs/{ui-standards,widget-rules}.md` |
| **ui/signal-slot-rules.md** | @Slot decorator, no lambdas, cleanup pattern | ❌ NO to CLAUDE.md | ❌ NONE (references real files) |
| **nodes/node-registration.md** | 5-step registration, visual node sync | ❌ NO to CLAUDE.md | ❌ NONE |

**Key Issue**: None of these files reference `CLAUDE.md` or `agent-rules/` system.

### agent-rules/rules/ System (12 files)

| File | Purpose | CLAUDE.md Ref | .claude/rules Ref | .brain Refs |
|------|---------|---|---|---|
| **00-role.md** | Agent philosophy, DDD, async, testing | ❌ NO | ❌ NO | ✅ `.brain/` |
| **01-workflow.md** | 5-phase workflow (DUPLICATE) | ❌ NO | ❌ NO | ✅ `.brain/context/current.md`, `.brain/plans/` |
| **02-coding-standards.md** | Code quality, type hints, imports | ❌ NO | ❌ NO | ❌ NONE |
| **03-architecture.md** | DDD patterns (DUPLICATE of .claude) | ❌ NO | ❌ NO | ❌ NONE |
| **04-agents.md** | Agent invocation from rules | ❌ NO | ❌ NO | ❌ NONE |
| **05-triggers.md** | Command trigger patterns | ❌ NO | ❌ NO | ❌ NONE |
| **06-enforcement.md** | Rules enforcement mechanisms | ❌ NO | ❌ NO | ❌ NONE |
| **07-tools.md** | Tool usage (view_file, grep, MCP) | ✅ YES (mentioned) | ❌ NO | ❌ NONE |
| **08-token-optimization.md** | Token budget, Qdrant-first | ❌ NO | ❌ NO | ❌ NONE |
| **09-brain-protocol.md** | .brain/ directory protocol | ❌ NO | ❌ NO | ✅ `.brain/context`, `.brain/plans`, `.brain/systemPatterns` |
| **10-node-workflow.md** | Node implementation flow | ❌ NO | ❌ NO | ✅ `.brain/decisions/add-node.md` |
| **11-node-templates.md** | Node template reference | ❌ NO | ❌ NO | ❌ NONE |

**Key Issue**: Most files don't reference `CLAUDE.md` or `.claude/rules/`.

---

## Cross-Reference Map

### What Links Where

**CLAUDE.md → (Hub)**
```
CLAUDE.md
├── .claude/rules/01-core.md                    ✅
├── .claude/rules/02-architecture.md            ✅
├── .claude/rules/03-nodes.md                   ✅
├── .claude/rules/04-ddd-events.md              ✅
├── .claude/rules/ui/theme-rules.md             ✅
├── .claude/rules/ui/signal-slot-rules.md       ✅
├── .claude/rules/nodes/node-registration.md    ✅
├── .brain/docs/node-templates.md               ✅
├── .brain/docs/node-checklist.md               ✅
└── .brain/projectRules.md                      ✅
```

**.claude/rules/ → (Sources)**
```
01-core.md
├── .brain/context/current.md                   ✅

02-architecture.md
├── .brain/context/current.md                   ✅
├── .brain/projectRules.md                      ✅
├── .brain/systemPatterns.md                    ✅
└── .brain/docs/*                               ✅

03-nodes.md
├── .brain/docs/node-templates.md               ✅
└── .brain/docs/node-checklist.md               ✅

04-ddd-events.md
├── (NO BACKLINKS)                              ❌

ui/theme-rules.md
├── .brain/docs/ui-standards.md                 ✅
└── .brain/docs/widget-rules.md                 ✅

ui/signal-slot-rules.md
├── coordinators/signal_coordinator.py (code)   ✅
├── ui/debug_panel.py (code)                    ✅
└── controllers/execution_controller.py (code)  ✅

nodes/node-registration.md
├── (NO .brain REFS)                            ❌
```

**agent-rules/rules/ → (Sources)**
```
00-role.md
├── .brain/ (general)                           ✅

01-workflow.md
├── .brain/context/current.md                   ✅
├── .brain/plans/                               ✅

02-coding-standards.md
├── (NO BACKLINKS)                              ❌

03-architecture.md
├── (NO BACKLINKS)                              ❌

09-brain-protocol.md
├── .brain/context/current.md                   ✅
├── .brain/plans/                               ✅
├── .brain/systemPatterns.md                    ✅

10-node-workflow.md
├── .brain/decisions/add-node.md                ✅

11-node-templates.md
├── (NO BACKLINKS)                              ❌
```

### Missing Backlinks (CRITICAL)

Files that do NOT reference their source documents:

#### In .claude/rules/
- **04-ddd-events.md** - No .brain references, not linked from CLAUDE.md's index table
- **nodes/node-registration.md** - Orphaned, no .brain documentation

#### In agent-rules/rules/
- **02-coding-standards.md** - Unreferenced
- **03-architecture.md** - Duplicate of .claude, unlinked
- **04-agents.md** - Agent invocation rules, orphaned
- **05-triggers.md** - Command trigger rules, orphaned
- **06-enforcement.md** - Rules enforcement, orphaned
- **07-tools.md** - Only mentions "CLAUDE.md" not linked back
- **08-token-optimization.md** - Orphaned despite critical content
- **11-node-templates.md** - Node templates, unreferenced

#### Between Systems
- **`.claude/rules/` does NOT reference `agent-rules/rules/`** ❌
- **`agent-rules/rules/` does NOT reference `.claude/rules/`** ❌
- **Only `CLAUDE.md` serves as bridge** ⚠️

---

## Content Duplication Issues

### Duplicate Content (Same Topics, Different Files)

1. **5-Phase Workflow**
   - `.claude/rules/01-core.md` - RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
   - `agent-rules/rules/01-workflow.md` - RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
   - **CONFLICT**: Slightly different emphasis

2. **DDD Architecture**
   - `.claude/rules/02-architecture.md` - Full DDD 2025 patterns
   - `agent-rules/rules/03-architecture.md` - Shorter version
   - **CONFLICT**: Inconsistent detail level

3. **Node Development**
   - `.claude/rules/03-nodes.md` - 8-step checklist
   - `agent-rules/rules/10-node-workflow.md` - Workflow emphasis
   - `agent-rules/rules/11-node-templates.md` - Template reference
   - **CONFLICT**: 3 files for one topic

### Unique Content (Not Duplicated)

- **.claude/rules/ui/*** - Theme and signal/slot rules (unique to .claude)
- **agent-rules/rules/0[4-8].md** - Agent control, triggers, tools, token optimization (unique to agent-rules)
- **agent-rules/rules/09-brain-protocol.md** - .brain/ directory usage (unique to agent-rules)

---

## Missing Documentation

### Index Files Missing

- **`agent-rules/_index.md`** ❌ MISSING - Should serve as entry point for agent-rules system
- **`.claude/rules/_index.md`** ❌ MISSING - Should organize .claude rules

### Cross-System Documentation

- **No document explaining relationship between `.claude/rules/` and `agent-rules/rules/`**
- **No master index showing which rules apply to which agents**
- **No decision tree for "which rule do I follow"**

### Missing .brain/ Documentation Referenced

Files referenced but not found in git status:
- `.brain/docs/node-templates.md` ✅ Mentioned, should exist
- `.brain/docs/node-checklist.md` ✅ Mentioned, should exist
- `.brain/docs/ui-standards.md` ✅ Mentioned, exists (widget-rules.md found)
- `.brain/projectRules.md` ✅ Mentioned, should exist
- `.brain/systemPatterns.md` ✅ Mentioned, should exist
- `.brain/decisions/add-node.md` ✅ Mentioned, decisions/ dir exists

---

## Link Status by Category

### ✅ Well-Linked

- **`.claude/rules/01-core.md`** - Links to `.brain/context/current.md`
- **`.claude/rules/02-architecture.md`** - Links to 4 .brain files
- **`.claude/rules/03-nodes.md`** - Links to 2 .brain files
- **`CLAUDE.md`** - Links to all 7 `.claude/rules/` files

### ⚠️ Partially Linked

- **`.claude/rules/ui/theme-rules.md`** - Links to 2 .brain files but not referenced from CLAUDE.md table
- **`.claude/rules/ui/signal-slot-rules.md`** - Links to code files, not referenced from CLAUDE.md table
- **`agent-rules/rules/00-role.md`** - Generic .brain reference
- **`agent-rules/rules/01-workflow.md`** - Links to .brain/ but not CLAUDE.md
- **`agent-rules/rules/09-brain-protocol.md`** - Links to .brain/ correctly

### ❌ Orphaned (No Backlinks)

- **`.claude/rules/04-ddd-events.md`** - Referenced nowhere
- **`.claude/rules/nodes/node-registration.md`** - Referenced nowhere
- **`agent-rules/rules/02-coding-standards.md`** - Referenced nowhere
- **`agent-rules/rules/03-architecture.md`** - Referenced nowhere
- **`agent-rules/rules/04-agents.md`** - Referenced nowhere
- **`agent-rules/rules/05-triggers.md`** - Referenced nowhere
- **`agent-rules/rules/06-enforcement.md`** - Referenced nowhere
- **`agent-rules/rules/07-tools.md`** - Only mentions CLAUDE.md, not linked back
- **`agent-rules/rules/08-token-optimization.md`** - Referenced nowhere
- **`agent-rules/rules/11-node-templates.md`** - Referenced nowhere

---

## Recommendations

### IMMEDIATE (High Priority)

1. **Create `.claude/rules/_index.md`**
   ```markdown
   # .claude/rules Index

   Core implementation rules for CasareRPA developers.

   ## Core Rules
   - [01-core.md](01-core.md) - 5-phase workflow, standards
   - [02-architecture.md](02-architecture.md) - DDD 2025 patterns
   - [03-nodes.md](03-nodes.md) - Node development
   - [04-ddd-events.md](04-ddd-events.md) - Event system

   ## UI/Presentation Rules
   - [ui/theme-rules.md](ui/theme-rules.md) - Theme usage
   - [ui/signal-slot-rules.md](ui/signal-slot-rules.md) - Qt patterns

   ## Node Registration
   - [nodes/node-registration.md](nodes/node-registration.md) - Registration steps

   **See also**: [CLAUDE.md](../../CLAUDE.md) for overview
   ```

2. **Create `agent-rules/_index.md`**
   ```markdown
   # agent-rules Index

   Agent execution rules and workflows.

   ## Workflow & Roles
   - [00-role.md](rules/00-role.md) - Agent philosophy
   - [01-workflow.md](rules/01-workflow.md) - 5-phase execution

   ## Implementation Rules
   - [02-coding-standards.md](rules/02-coding-standards.md) - Code quality
   - [03-architecture.md](rules/03-architecture.md) - DDD patterns

   ## Agent Control
   - [04-agents.md](rules/04-agents.md) - Agent invocation
   - [05-triggers.md](rules/05-triggers.md) - Command triggers
   - [06-enforcement.md](rules/06-enforcement.md) - Enforcement

   ## Tools & Optimization
   - [07-tools.md](rules/07-tools.md) - Available tools
   - [08-token-optimization.md](rules/08-token-optimization.md) - Token budgets

   ## Documentation Protocols
   - [09-brain-protocol.md](rules/09-brain-protocol.md) - .brain/ usage
   - [10-node-workflow.md](rules/10-node-workflow.md) - Node workflow
   - [11-node-templates.md](rules/11-node-templates.md) - Node templates
   ```

3. **Add to `CLAUDE.md` "Rules Reference" section:**
   ```markdown
   ## Rules Reference

   ### Core Implementation Rules (.claude/rules/)
   See [.claude/rules/_index.md](.claude/rules/_index.md)
   | Topic | File |
   |-------|------|
   | Workflow & Standards | `.claude/rules/01-core.md` |
   | Architecture & DDD | `.claude/rules/02-architecture.md` |
   | Node Development | `.claude/rules/03-nodes.md` |
   | Events System | `.claude/rules/04-ddd-events.md` |
   | UI Theme | `.claude/rules/ui/theme-rules.md` |
   | Qt Signals | `.claude/rules/ui/signal-slot-rules.md` |
   | Node Registration | `.claude/rules/nodes/node-registration.md` |

   ### Agent Execution Rules (agent-rules/rules/)
   See [agent-rules/_index.md](agent-rules/_index.md)
   ```

4. **Add bidirectional links:**
   - `.claude/rules/01-core.md` should reference `agent-rules/rules/01-workflow.md` with note: "See also agent execution workflow"
   - `agent-rules/rules/01-workflow.md` should reference `.claude/rules/01-core.md` with note: "Implements these standards"
   - All architecture docs should cross-reference each other

### SHORT TERM (1-2 days)

5. **Consolidate duplicate content:**
   - `.claude/rules/02-architecture.md` is authoritative for DDD patterns
   - `agent-rules/rules/03-architecture.md` should reference it: "See `.claude/rules/02-architecture.md` for full DDD reference"
   - Same for workflow files

6. **Add missing backlinks:**
   - Add `.brain/` references to `.claude/rules/04-ddd-events.md`
   - Add `.brain/` references to `.claude/rules/nodes/node-registration.md`
   - Add CLAUDE.md references to orphaned `agent-rules/rules/*.md` files

7. **Update CLAUDE.md "On-Demand Docs" section:**
   ```markdown
   ## On-Demand Docs (Load When Needed)
   - `.claude/rules/_index.md` - **Start here for rules overview**
   - `.brain/docs/node-templates.md` - Full node templates
   - `.brain/docs/node-checklist.md` - Node implementation steps
   - `.brain/projectRules.md` - Full coding standards
   - `.brain/systemPatterns.md` - Architecture patterns
   ```

### MEDIUM TERM (1 week)

8. **Create system integration document:**
   - `.claude/rules/00-system.md` explaining relationship between systems
   - Decision tree: "Which rule applies to my situation?"
   - When to use `.claude/rules/` vs `agent-rules/rules/`

9. **Add "Master Rules Index":**
   - Document in root: `RULES_MASTER_INDEX.md`
   - Single source of truth for rule locations
   - Searchable by topic

10. **Establish maintenance protocol:**
    - When adding rules, update both `_index.md` files
    - When referencing external docs, add backlinks
    - Quarterly review for duplicates and orphaned files

---

## File-by-File Linking Status

### .claude/rules/ (7 files)

✅ = Has backlinks or is referenced
⚠️ = Partially referenced
❌ = No backlinks

```
.claude/rules/
├── 01-core.md                    ✅ → CLAUDE.md + .brain/context
├── 02-architecture.md            ✅ → CLAUDE.md + .brain/{3 files}
├── 03-nodes.md                   ✅ → CLAUDE.md + .brain/{2 files}
├── 04-ddd-events.md              ❌ → NOWHERE
├── ui/
│   ├── theme-rules.md            ⚠️ → CLAUDE.md (not in table) + .brain/{2 files}
│   └── signal-slot-rules.md      ⚠️ → CLAUDE.md (not in table) + code refs
└── nodes/
    └── node-registration.md      ❌ → NOWHERE
```

### agent-rules/rules/ (12 files)

```
agent-rules/rules/
├── 00-role.md                    ⚠️ → .brain/ only
├── 01-workflow.md                ⚠️ → .brain/{2 items}
├── 02-coding-standards.md        ❌ → NOWHERE
├── 03-architecture.md            ❌ → NOWHERE
├── 04-agents.md                  ❌ → NOWHERE
├── 05-triggers.md                ❌ → NOWHERE
├── 06-enforcement.md             ❌ → NOWHERE
├── 07-tools.md                   ⚠️ → mentions CLAUDE.md only
├── 08-token-optimization.md      ❌ → NOWHERE
├── 09-brain-protocol.md          ✅ → .brain/{3 items}
├── 10-node-workflow.md           ✅ → .brain/decisions/add-node.md
└── 11-node-templates.md          ❌ → NOWHERE
```

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total markdown files in rules | 19 |
| Files with backlinks | 6 (31%) |
| Files with partial backlinks | 5 (26%) |
| Orphaned files (no backlinks) | 8 (42%) |
| Cross-system links | 0 ❌ |
| Index files (_index.md) | 0 ❌ |
| Duplicate topics | 3 |
| Missing .brain files referenced | 5 |

---

## Conclusion

The rule system has **grown organically** without centralized governance:

1. **Two parallel systems** (`.claude/` vs `agent-rules/`) without integration
2. **No index files** to organize or navigate either system
3. **42% of rules are orphaned** - not linked from anywhere
4. **No cross-system references** - they exist independently
5. **Duplicate content** about workflows, architecture, nodes

**Impact**: New developers must know to look in CLAUDE.md as hub, then navigate to scattered rule files. Maintenance is difficult due to duplication.

**Fix Priority**: Create index files + consolidate duplicates + establish bidirectional linking in 3-5 days.
