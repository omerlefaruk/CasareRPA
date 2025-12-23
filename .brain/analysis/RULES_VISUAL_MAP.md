# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Rules System: Visual Navigation Map

## Current State (As-Is)

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLAUDE.md (HUB)                          │
│                      [Only entry point]                          │
└────┬──────────────────────────┬──────────────────────────────┬───┘
     │                          │                              │
     v                          v                              v
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  .claude/rules/  │  │ agent-rules/     │  │  .brain/         │
│                  │  │ rules/           │  │                  │
│ 7 files          │  │ 12 files         │  │ Referenced only  │
│ ISOLATED         │  │ ISOLATED         │  │ (no backlinks)   │
│                  │  │                  │  │                  │
│ ✅ 01-core.md    │  │ ⚠️ 00-role.md    │  │ ✅ Indexed by:   │
│ ✅ 02-arch...    │  │ ⚠️ 01-workflow   │  │   .claude/       │
│ ✅ 03-nodes.md   │  │ ❌ 02-coding...  │  │   agent-rules/   │
│ ❌ 04-events.md  │  │ ❌ 03-arch...    │  │                  │
│ ⚠️ ui/*           │  │ ❌ 04-agents.md  │  │ ❌ NOT indexed    │
│ ❌ nodes/reg...  │  │ ❌ 05-triggers.  │  │    by itself      │
│                  │  │ ❌ 06-enforce... │  │                  │
│                  │  │ ⚠️ 07-tools.md   │  │                  │
│                  │  │ ❌ 08-token...   │  │                  │
│                  │  │ ✅ 09-brain...   │  │                  │
│                  │  │ ✅ 10-node-wf.   │  │                  │
│                  │  │ ❌ 11-templates  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
     NO LINKS              NO LINKS            Referenced from
     between              between               .claude & agent-
     systems              systems               rules internally
```

## Desired State (To-Be)

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLAUDE.md (HUB)                            │
│             [Master entry point + navigation]                     │
└────┬──────────────────────┬───────────────────────┬──────────────┘
     │                      │                       │
     v                      v                       v
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ .claude/         │ │ agent-rules/     │ │ RULES_INDEX.md   │
│ _index.md ✅     │ │ _index.md ✅     │ │ [MASTER] ✅      │
│ [NEW]            │ │ [NEW]            │ │ [NEW]            │
│                  │ │                  │ │                  │
│ ├─01-core.md ✅  │ │ ├─00-role.md ✅  │ │ Organized by:    │
│ ├─02-arch ✅     │ │ ├─01-workflow ✅ │ │ • Phase (RPED)   │
│ ├─03-nodes ✅    │ │ ├─02-coding ✅   │ │ • Layer (DDD)    │
│ ├─04-events ✅   │ │ ├─03-arch ✅     │ │ • Topic (Node)   │
│ ├─ui/            │ │ ├─04-agents ✅   │ │ • Audience       │
│ │ ├─theme ✅     │ │ ├─05-triggers ✅ │ │                  │
│ │ └─signals ✅   │ │ ├─06-enforce ✅  │ │ Cross-links to:  │
│ └─nodes/         │ │ ├─07-tools ✅    │ │ • .claude/rules  │
│   └─register ✅  │ │ ├─08-tokens ✅   │ │ • agent-rules/   │
│                  │ │ ├─09-brain ✅    │ │ • .brain/docs    │
│ Bidirectional ◄─►│ │ ├─10-nodes ✅    │ │ • CLAUDE.md      │
│ cross-refs       │ │ └─11-templates ✅│ │                  │
│ between files    │ │                  │ │ Quintuples       │
│                  │ │ Index explains   │ │ searchability    │
│ No orphans       │ │ relationship to  │ │                  │
│ 7/7 linked       │ │ .claude/         │ │ Consolidates     │
│                  │ │ 12/12 linked     │ │ duplicates       │
└──────────────────┘ └──────────────────┘ └──────────────────┘
      LINKED              LINKED              LINKS ALL
     to index        to index + to .claude    SYSTEMS

                              │
                              v
                    ┌──────────────────┐
                    │  .brain/docs/    │
                    │  [Documentation] │
                    │                  │
                    │ All referenced   │
                    │ files indexed    │
                    │ with backlinks   │
                    │ from rules       │
                    └──────────────────┘
```

## Information Architecture: Topic-Based View

```
DEVELOPER NEEDS → RULES TO READ

"I need to implement a new feature"
  → CLAUDE.md → .claude/rules/01-core.md (5-phase)
  → RULES_INDEX.md → Topic: Feature Implementation
  → agent-rules/rules/01-workflow.md
  → agent-rules/rules/commands/implement-feature.md

"I need to understand DDD architecture"
  → CLAUDE.md → .claude/rules/02-architecture.md (authoritative)
  → .claude/rules/04-ddd-events.md (events deep dive)
  → agent-rules/rules/03-architecture.md (shorter version)
  → .brain/systemPatterns.md (examples)

"I need to create a new node"
  → CLAUDE.md → .claude/rules/03-nodes.md (checklist)
  → agent-rules/rules/10-node-workflow.md (workflow)
  → agent-rules/rules/11-node-templates.md (templates)
  → .claude/rules/nodes/node-registration.md (registration)
  → .brain/docs/node-templates.md (full examples)

"I need to follow Qt best practices"
  → CLAUDE.md → .claude/rules/ui/signal-slot-rules.md
  → .claude/rules/ui/theme-rules.md
  → .brain/docs/widget-rules.md

"I need to understand the event system"
  → CLAUDE.md → .claude/rules/04-ddd-events.md
  → domain/events/__init__.py (implementation)
  → .brain/systemPatterns.md (patterns)

"I need to optimize agent execution"
  → RULES_INDEX.md → Topic: Performance
  → agent-rules/rules/08-token-optimization.md
  → agent-rules/rules/07-tools.md (efficient tools)
  → .brain/docs/qdrant-quick-reference.md
```

## Linking Pattern: Current vs Desired

### Current Pattern (Broken)

```
File A: "See File B"
   ↓
File B: ???  ← No link back to A
   ↓
Developer: "Is B still used? Unclear"
```

### Desired Pattern (Bidirectional)

```
File A: "See File B for details" [link]
   ↓
File B: "Called from File A" [link back]
   ↓
Developer: "Clear relationship, traceable flow"
```

### Examples

**Current (Broken)**
```markdown
# .claude/rules/03-nodes.md
"See `.brain/docs/node-templates.md` for full templates."
```
BUT `.brain/docs/node-templates.md` doesn't mention:
- It comes from .claude/rules/03-nodes.md
- It's referenced by agent-rules/rules/11-node-templates.md
- It's supposed to be in .brain/

**Desired (Fixed)**
```markdown
# .claude/rules/03-nodes.md
See `.brain/docs/node-templates.md` [link] for full templates.
See also `agent-rules/rules/11-node-templates.md` [link] for template reference.

---

# .brain/docs/node-templates.md
Referenced from:
- `.claude/rules/03-nodes.md` [link] - Node development checklist
- `agent-rules/rules/11-node-templates.md` [link] - Template reference
---

# agent-rules/rules/11-node-templates.md
See also:
- `.claude/rules/03-nodes.md` [link] - Full 8-step checklist
- `.brain/docs/node-templates.md` [link] - Template examples
```

## System Health Indicators

### Current System ❌

| Indicator | Status | Impact |
|-----------|--------|--------|
| Index files | 0/2 ❌ | Can't navigate rules |
| Cross-links | 0 ❌ | Systems isolated |
| Backlinks | 31% ⚠️ | 8 files orphaned |
| Duplication | 3 items ⚠️ | Confusion, hard to maintain |
| .brain linkage | Partial ⚠️ | Some .brain files referenced nowhere |
| Master index | None ❌ | No single source of truth |

### Desired System ✅

| Indicator | Target | Impact |
|-----------|--------|--------|
| Index files | 2/2 ✅ | Clear navigation |
| Cross-links | 100% ✅ | Integrated systems |
| Backlinks | 100% ✅ | No orphans |
| Duplication | 0 ✅ | Single source per topic |
| .brain linkage | 100% ✅ | Full traceability |
| Master index | RULES_INDEX.md ✅ | One source of truth |

## Quick Reference: Where Is My Answer?

| Question | Current | Desired |
|----------|---------|---------|
| "What's the 5-phase workflow?" | 2 places + unclear which is canonical | 1 place + clearly referenced |
| "How do I create a node?" | 3 files scattered | 1 location + cross-links to all related docs |
| "What are the DDD patterns?" | 2 conflicting versions | 1 authoritative + references |
| "How do signals/slots work?" | 1 file + orphaned | 1 file + clearly indexed |
| "Where's the event system?" | 1 orphaned file | 1 file + multiple paths to find it |
| "What tools can I use?" | 1 orphaned file | 1 file + indexed as part of broader topic |

## Navigation Flow: Desired User Journey

```
Start: "I don't know where to begin"
   ↓
1. Read CLAUDE.md (5 min overview)
   ↓
2. Choose your path based on task:

   Path A: Learning Architecture
   → RULES_INDEX.md "Architecture" section
   → .claude/rules/02-architecture.md (DDD patterns)
   → agent-rules/rules/03-architecture.md (agent perspective)
   → .brain/systemPatterns.md (examples)

   Path B: Implementing Features
   → RULES_INDEX.md "Feature Implementation" section
   → .claude/rules/01-core.md (5-phase workflow)
   → agent-rules/commands/implement-feature.md (agent command)
   → Follow the command with your agents

   Path C: Creating Nodes
   → RULES_INDEX.md "Node Development" section
   → .claude/rules/03-nodes.md (start here)
   → .claude/rules/nodes/node-registration.md (registration)
   → agent-rules/rules/10-node-workflow.md (agent workflow)
   → agent-rules/rules/11-node-templates.md (templates)
   → .brain/docs/node-templates.md (full examples)

   Path D: UI Development
   → RULES_INDEX.md "UI/Presentation" section
   → .claude/rules/ui/theme-rules.md (theming)
   → .claude/rules/ui/signal-slot-rules.md (Qt patterns)
   → .brain/docs/widget-rules.md (widget standards)

End: Clear path + all relevant files linked in logical order
```

## Maintenance Protocol (After Fix)

### When Adding New Rule File

1. Add to appropriate `_index.md` (`.claude/rules/` or `agent-rules/rules/`)
2. Add backlinks section at bottom of file
3. Update RULES_INDEX.md with topic + file reference
4. Add link from CLAUDE.md if it's a core rule

### When Modifying Existing Rule

1. Update backlinks if topic changes
2. Update index references if it moves
3. Check for duplicate content in other systems
4. Add cross-references if related rules exist

### Quarterly Maintenance

1. Run: `grep -r "See .*\.md" agent-rules/ .claude/rules/ | grep -v _index.md`
2. Verify all references are correct
3. Check for orphaned files (not in any index)
4. Consolidate any new duplicates

---

## Impact Assessment

### Effort to Implement
- Create 2 index files: 1-2 hours
- Add backlinks to all 19 files: 2-3 hours
- Create RULES_INDEX.md: 1-2 hours
- Update CLAUDE.md: 30 minutes
- Test navigation paths: 1 hour
- **Total: 6-9 hours**

### Maintenance Overhead
- Minimal after initial setup
- ~30 min per new rule (already included in creation time)
- ~15 min per rule modification

### Benefits
- 100% improvement in navigability
- Eliminates orphaned content
- Reduces confusion about which rule applies
- Makes maintenance easier (can track all references)
- Supports new developers effectively
- Creates single source of truth for each topic
