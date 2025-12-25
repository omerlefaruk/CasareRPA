# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Rules System: Fix Implementation Checklist

**Estimated Time**: 6-9 hours
**Difficulty**: Low (mostly adding index files and cross-links)
**Risk**: Very Low (documentation only, no code changes)

---

## Phase 1: Create Index Files (1-2 hours)

### Task 1.1: Create `.claude/rules/_index.md`
- [ ] Create file at `c:/Users/Rau/Desktop/CasareRPA/.claude/rules/_index.md`
- [ ] Add table of contents with all 7 files
- [ ] Add brief description for each rule
- [ ] Add link to CLAUDE.md at bottom
- [ ] Verify all links work

**Template**:
```markdown
# .claude/rules Index

Core implementation rules for CasareRPA developers.

## Core Workflow & Architecture Rules
- [01-core.md](01-core.md) - 5-phase workflow (RESEARCH→PLAN→EXECUTE→VALIDATE→DOCS), KISS principle, error handling, operations rules
- [02-architecture.md](02-architecture.md) - DDD 2025 patterns, layers, aggregates, event bus, unit of work, CQRS queries
- [03-nodes.md](03-nodes.md) - Node development workflow, port API (add_input_port, add_exec_input, etc.), atomic design
- [04-ddd-events.md](04-ddd-events.md) - Typed event system, EventBus API, event classes reference, best practices

## User Interface Rules
- [ui/theme-rules.md](ui/theme-rules.md) - THEME constant usage, available colors, Qt styling patterns
- [ui/signal-slot-rules.md](ui/signal-slot-rules.md) - @Slot decorator (MANDATORY), no lambdas, functools.partial, cleanup patterns

## Node System Rules
- [nodes/node-registration.md](nodes/node-registration.md) - 5-step registration (export→registry→loader→visual→visual-registry), critical duplicate prevention

## Related Documentation
- [../../CLAUDE.md](../../CLAUDE.md) - Project overview and main entry point
- [../../.brain/context/current.md](../../.brain/context/current.md) - Current session state (updated after major tasks)
- [../../.brain/projectRules.md](../../.brain/projectRules.md) - Full coding standards

## Quick Links by Task

| Task | Start Here |
|------|-----------|
| Starting new work | [01-core.md](01-core.md) - 5-phase workflow |
| Understanding architecture | [02-architecture.md](02-architecture.md) - DDD patterns |
| Creating new node | [03-nodes.md](03-nodes.md) - 8-step checklist |
| Working with events | [04-ddd-events.md](04-ddd-events.md) - Event reference |
| Building Qt UI | [ui/signal-slot-rules.md](ui/signal-slot-rules.md) - Signal patterns |
| Styling widgets | [ui/theme-rules.md](ui/theme-rules.md) - Theme colors |
| Registering node | [nodes/node-registration.md](nodes/node-registration.md) - Registration steps |
```

### Task 1.2: Create `agent-rules/_index.md`
- [ ] Create file at `c:/Users/Rau/Desktop/CasareRPA/agent-rules/_index.md`
- [ ] Add table of contents with all 12 rules files
- [ ] Add brief description for each rule
- [ ] Add cross-references to `.claude/rules/` where applicable
- [ ] Add link to CLAUDE.md at bottom
- [ ] Verify all links work

**Template**:
```markdown
# agent-rules Index

Agent execution rules, workflows, and command definitions.

## Core Roles & Workflows
- [rules/00-role.md](rules/00-role.md) - Agent philosophy (quality over speed, reuse first, type safety, async-first, test everything)
- [rules/01-workflow.md](rules/01-workflow.md) - 5-phase workflow implementation (RESEARCH→PLAN→EXECUTE→VALIDATE→DOCS) for agents
  - *See also*: [../.claude/rules/01-core.md](../.claude/rules/01-core.md) for developer workflow

## Implementation Standards
- [rules/02-coding-standards.md](rules/02-coding-standards.md) - Code quality, type hints, imports, no silent failures
- [rules/03-architecture.md](rules/03-architecture.md) - DDD patterns, layers, agents by phase
  - *See also*: [../.claude/rules/02-architecture.md](../.claude/rules/02-architecture.md) for full DDD reference (authoritative source)

## Agent Control & Execution
- [rules/04-agents.md](rules/04-agents.md) - How agents are invoked, loaded from agent-rules/agents/, task execution
- [rules/05-triggers.md](rules/05-triggers.md) - Command triggers, when agents are called, slash command patterns
- [rules/06-enforcement.md](rules/06-enforcement.md) - How rules are enforced, compliance checking

## Tools & Resources
- [rules/07-tools.md](rules/07-tools.md) - Available tools (file ops, code editing, MCP tools), Ref documentation search, Exa code context
- [rules/08-token-optimization.md](rules/08-token-optimization.md) - Token budgets, semantic search first (qdrant-find), when to use grep vs qdrant

## Documentation & Protocols
- [rules/09-brain-protocol.md](rules/09-brain-protocol.md) - .brain/ directory protocol, context files, plans, pattern discovery
- [rules/10-node-workflow.md](rules/10-node-workflow.md) - Node implementation workflow for agents
  - *See also*: [../.claude/rules/03-nodes.md](../.claude/rules/03-nodes.md) for developer reference
- [rules/11-node-templates.md](rules/11-node-templates.md) - Node template reference
  - *See also*: [../.brain/docs/node-templates.md](../.brain/docs/node-templates.md) for full examples

## Command Definitions
See [commands/](commands/) for slash command implementations
- [commands/implement-feature.md](commands/implement-feature.md)
- [commands/fix-feature.md](commands/fix-feature.md)
- [commands/implement-node.md](commands/implement-node.md)

## Agent Definitions
See [agents/](agents/) for agent role specifications
- [agents/explore.md](agents/explore.md) - Codebase navigation specialist
- [agents/architect.md](agents/architect.md) - Design strategy and planning
- [agents/builder.md](agents/builder.md) - Code implementation
- [agents/refactor.md](agents/refactor.md) - Code cleanup and restructuring
- [agents/ui.md](agents/ui.md) - Qt/Canvas UI specialist
- [agents/integrations.md](agents/integrations.md) - External API integration
- [agents/quality.md](agents/quality.md) - Testing and performance
- [agents/reviewer.md](agents/reviewer.md) - Code review and approval
- [agents/docs.md](agents/docs.md) - Documentation specialist
- [agents/researcher.md](agents/researcher.md) - Web research (Exa, Ref)

## Quick Links by Task

| Task | Start Here |
|------|-----------|
| Understanding agent role | [rules/00-role.md](rules/00-role.md) |
| Agent workflow | [rules/01-workflow.md](rules/01-workflow.md) |
| Code quality standards | [rules/02-coding-standards.md](rules/02-coding-standards.md) |
| Invoking agents | [rules/04-agents.md](rules/04-agents.md) |
| Using tools | [rules/07-tools.md](rules/07-tools.md) |
| Token optimization | [rules/08-token-optimization.md](rules/08-token-optimization.md) |
| .brain/ usage | [rules/09-brain-protocol.md](rules/09-brain-protocol.md) |
| Node implementation | [rules/10-node-workflow.md](rules/10-node-workflow.md) |

## Related Documentation
- [../CLAUDE.md](../CLAUDE.md) - Project overview
- [../.claude/rules/_index.md](../.claude/rules/_index.md) - Developer-facing rules (implementation)
- [../.brain/context/current.md](../.brain/context/current.md) - Session state
```

### Task 1.3: Create `RULES_INDEX.md` (Master Index)
- [ ] Create file at `c:/Users/Rau/Desktop/CasareRPA/RULES_INDEX.md`
- [ ] Organize by topic/phase (not by system)
- [ ] Include cross-references to both `.claude/` and `agent-rules/`
- [ ] Include cross-references to `.brain/` documentation
- [ ] Add decision tree: "Which rule do I follow?"
- [ ] Verify all links work

**Template**:
```markdown
# Master Rules Index: Find Any Rule by Topic

This is the central navigation point for all CasareRPA rules. Use this to find the rule you need regardless of which system it's in.

## By Phase (5-Phase Workflow)

### RESEARCH Phase
Rules for understanding existing code and requirements.

**Developer Rules**:
- [.claude/rules/01-core.md](.claude/rules/01-core.md) → Phase 1: RESEARCH section

**Agent Rules**:
- [agent-rules/rules/01-workflow.md](agent-rules/rules/01-workflow.md) → Phase 1: RESEARCH
- [agent-rules/agents/explore.md](agent-rules/agents/explore.md) → Explore agent for codebase search

**Tools**:
- [agent-rules/rules/07-tools.md](agent-rules/rules/07-tools.md) → File operations, grep_search, find_by_name

**Documentation**:
- [.brain/context/current.md](.brain/context/current.md) - Session state to check before starting

### PLAN Phase
Rules for designing and planning work.

**Developer Rules**:
- [.claude/rules/01-core.md](.claude/rules/01-core.md) → Phase 2: PLAN (user approval required)

**Agent Rules**:
- [agent-rules/rules/01-workflow.md](agent-rules/rules/01-workflow.md) → Phase 2: PLAN
- [agent-rules/agents/architect.md](agent-rules/agents/architect.md) → Architect agent for design

**Decision Trees**:
- [.brain/decisions/add-node.md](.brain/decisions/add-node.md) - Adding nodes
- [.brain/decisions/add-feature.md](.brain/decisions/add-feature.md) - Adding features

### EXECUTE Phase
Rules for implementation.

**Core Developer Rules**:
- [.claude/rules/01-core.md](.claude/rules/01-core.md) → Phase 3: EXECUTE
- [.claude/rules/02-architecture.md](.claude/rules/02-architecture.md) → DDD 2025 patterns for implementation
- [agent-rules/rules/02-coding-standards.md](agent-rules/rules/02-coding-standards.md) → Code quality during execution

**Specializations**:
- [.claude/rules/03-nodes.md](.claude/rules/03-nodes.md) → Creating nodes
- [.claude/rules/ui/theme-rules.md](.claude/rules/ui/theme-rules.md) → UI styling with THEME
- [.claude/rules/ui/signal-slot-rules.md](.claude/rules/ui/signal-slot-rules.md) → Qt signal/slot patterns
- [agent-rules/rules/10-node-workflow.md](agent-rules/rules/10-node-workflow.md) → Agent workflow for node implementation

**Agent Roles**:
- [agent-rules/agents/builder.md](agent-rules/agents/builder.md) → Code implementation
- [agent-rules/agents/ui.md](agent-rules/agents/ui.md) → Qt/Canvas UI
- [agent-rules/agents/integrations.md](agent-rules/agents/integrations.md) → External APIs
- [agent-rules/agents/refactor.md](agent-rules/agents/refactor.md) → Code cleanup

### VALIDATE Phase
Rules for testing and quality.

**Developer Rules**:
- [.claude/rules/01-core.md](.claude/rules/01-core.md) → Phase 4: VALIDATE (blocking loop)

**Agent Rules**:
- [agent-rules/agents/quality.md](agent-rules/agents/quality.md) → Testing and performance
- [agent-rules/agents/reviewer.md](agent-rules/agents/reviewer.md) → Code review

### DOCS Phase
Rules for documentation.

**Developer Rules**:
- [.claude/rules/01-core.md](.claude/rules/01-core.md) → Phase 5: DOCS

**Agent Rules**:
- [agent-rules/agents/docs.md](agent-rules/agents/docs.md) → Documentation specialist

**Guidelines**:
- [.brain/projectRules.md](.brain/projectRules.md) → Documentation standards
- [.brain/systemPatterns.md](.brain/systemPatterns.md) → Pattern documentation

## By Topic (Common Tasks)

### Creating New Nodes
1. Start: [.claude/rules/03-nodes.md](.claude/rules/03-nodes.md) - Full 8-step checklist
2. Reference: [.claude/rules/nodes/node-registration.md](.claude/rules/nodes/node-registration.md) - Registration steps
3. Agent view: [agent-rules/rules/10-node-workflow.md](agent-rules/rules/10-node-workflow.md)
4. Templates: [agent-rules/rules/11-node-templates.md](agent-rules/rules/11-node-templates.md)
5. Examples: [.brain/docs/node-templates.md](.brain/docs/node-templates.md)

### Implementing Features
1. Start: [.claude/rules/01-core.md](.claude/rules/01-core.md) - 5-phase workflow
2. Agent command: [agent-rules/commands/implement-feature.md](agent-rules/commands/implement-feature.md)
3. Architecture: [.claude/rules/02-architecture.md](.claude/rules/02-architecture.md) - DDD patterns
4. Code standards: [agent-rules/rules/02-coding-standards.md](agent-rules/rules/02-coding-standards.md)

### Understanding Architecture
1. Start: [.claude/rules/02-architecture.md](.claude/rules/02-architecture.md) - DDD 2025 (AUTHORITATIVE)
2. Events: [.claude/rules/04-ddd-events.md](.claude/rules/04-ddd-events.md) - Event system
3. Agent view: [agent-rules/rules/03-architecture.md](agent-rules/rules/03-architecture.md) (summary)
4. Examples: [.brain/systemPatterns.md](.brain/systemPatterns.md)

### Building Qt UI
1. Signals/Slots: [.claude/rules/ui/signal-slot-rules.md](.claude/rules/ui/signal-slot-rules.md) - @Slot decorator, no lambdas
2. Theming: [.claude/rules/ui/theme-rules.md](.claude/rules/ui/theme-rules.md) - THEME constant usage
3. Widget patterns: [.brain/docs/widget-rules.md](.brain/docs/widget-rules.md)

### Using Events
1. Reference: [.claude/rules/04-ddd-events.md](.claude/rules/04-ddd-events.md) - Event classes and API
2. Implementation: [domain/events/__init__.py](domain/events/__init__.py) - Event definitions
3. Examples: [.brain/systemPatterns.md](.brain/systemPatterns.md) - Usage patterns

### Optimizing Performance
1. Agent focus: [agent-rules/agents/quality.md](agent-rules/agents/quality.md) - Performance testing
2. Token budget: [agent-rules/rules/08-token-optimization.md](agent-rules/rules/08-token-optimization.md)
3. Search strategy: [agent-rules/rules/07-tools.md](agent-rules/rules/07-tools.md) - Use qdrant-find first
4. Patterns: [.brain/systemPatterns.md](.brain/systemPatterns.md)

### Fixing Bugs
1. Command: [agent-rules/commands/fix-feature.md](agent-rules/commands/fix-feature.md)
2. Workflow: [.claude/rules/01-core.md](.claude/rules/01-core.md) - Apply 5-phase workflow
3. Decision tree: [.brain/decisions/fix-bug.md](.brain/decisions/fix-bug.md) (if exists)

## By Audience

### For New Developers
1. Read: [CLAUDE.md](CLAUDE.md) - 15 minute overview
2. Read: [.claude/rules/_index.md](.claude/rules/_index.md) - Rules structure
3. Read: [.claude/rules/01-core.md](.claude/rules/01-core.md) - Core workflow
4. Choose task → Use RULES_INDEX.md to find relevant rules

### For Agent Designers
1. Read: [agent-rules/_index.md](agent-rules/_index.md) - Agent rules structure
2. Read: [agent-rules/rules/00-role.md](agent-rules/rules/00-role.md) - Agent philosophy
3. Read: [agent-rules/rules/01-workflow.md](agent-rules/rules/01-workflow.md) - Workflow
4. Check: [agent-rules/rules/04-agents.md](agent-rules/rules/04-agents.md) - How agents are invoked

### For Maintainers
1. Read: All index files
2. Maintain: Bidirectional backlinks (use checklist at end)
3. Check quarterly: Look for orphaned files, duplicates
4. Update: When adding new rules, update both indexes + master index

## Decision Tree: Which Rule Do I Follow?

```
I'm starting a task
  ├─ Do I understand the codebase area?
  │  ├─ NO → Go to RESEARCH phase (rules above)
  │  └─ YES → Continue
  ├─ Have I planned the work?
  │  ├─ NO → Go to PLAN phase (need architect agent)
  │  └─ YES → Continue
  ├─ Am I implementing?
  │  ├─ Nodes? → .claude/rules/03-nodes.md
  │  ├─ UI/Qt? → .claude/rules/ui/*
  │  ├─ Features? → .claude/rules/02-architecture.md
  │  └─ Events? → .claude/rules/04-ddd-events.md
  └─ Go to EXECUTE phase
```

## Maintenance Checklist

- [ ] When creating new rule file:
  - [ ] Add to appropriate _index.md
  - [ ] Add to RULES_INDEX.md under topic
  - [ ] Add backlinks section in file itself
  - [ ] Link from CLAUDE.md if core rule

- [ ] When updating rule file:
  - [ ] Check for references in index files
  - [ ] Update index if topic changes
  - [ ] Check for related rules (add cross-references)
  - [ ] Update backlinks if scope changed

- [ ] Quarterly:
  - [ ] Verify all links are not broken
  - [ ] Check for new orphaned files
  - [ ] Check for duplicate content
  - [ ] Update RULES_QUICK_SUMMARY.md statistics

## Statistics

| Metric | Value |
|--------|-------|
| Total rule files | 19 |
| In _index.md | 19 (100%) |
| With backlinks | 19 (100%) |
| Orphaned | 0 |
| Cross-linked systems | YES |
| Master index | This file |
```

---

## Phase 2: Add Backlinks to Rule Files (2-3 hours)

### Task 2.1: Add Backlinks Section to `.claude/rules/04-ddd-events.md`
- [ ] Open file
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `.claude/rules/02-architecture.md` - DDD patterns
- `agent-rules/rules/03-architecture.md` - Architecture summary
- `domain/events/__init__.py` - Event implementations
- `.brain/systemPatterns.md` - Event usage patterns

## Related Documentation
- `.claude/rules/01-core.md` - Core workflow standards
- `RULES_INDEX.md` - Topic: "Using Events"
```
- [ ] Verify links work

### Task 2.2: Add Backlinks Section to `.claude/rules/nodes/node-registration.md`
- [ ] Open file
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `.claude/rules/03-nodes.md` - Node development checklist
- `agent-rules/rules/10-node-workflow.md` - Agent workflow
- `agent-rules/rules/11-node-templates.md` - Template reference
- `RULES_INDEX.md` - Topic: "Creating New Nodes"

## Related Documentation
- `.brain/docs/node-templates.md` - Full examples
- `.brain/docs/node-checklist.md` - Implementation checklist
```
- [ ] Verify links work

### Task 2.3: Add Cross-Links to `.claude/rules/02-architecture.md`
- [ ] Open file in "Other Key Patterns" section
- [ ] Add:
```markdown
## See Also
- [04-ddd-events.md](04-ddd-events.md) - Deep dive into typed events
- [agent-rules/rules/03-architecture.md](../../agent-rules/rules/03-architecture.md) - Agent perspective on architecture
```

### Task 2.4: Add Cross-Links to `.claude/rules/03-nodes.md`
- [ ] Open file
- [ ] Add at end:
```markdown
---

## See Also
- [nodes/node-registration.md](nodes/node-registration.md) - 5-step registration process
- [agent-rules/rules/10-node-workflow.md](../../agent-rules/rules/10-node-workflow.md) - Agent workflow
- [agent-rules/rules/11-node-templates.md](../../agent-rules/rules/11-node-templates.md) - Template reference
```

### Task 2.5: Add Cross-Link to `.claude/rules/01-core.md`
- [ ] Open file
- [ ] In "Operations Rules" section, add:
```markdown
- See also: [agent-rules/rules/01-workflow.md](../../agent-rules/rules/01-workflow.md) for agent execution of this workflow
```

### Task 2.6: Add Backlinks to `agent-rules/rules/02-coding-standards.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `agent-rules/rules/01-workflow.md` - Phase 3: EXECUTE
- `RULES_INDEX.md` - Topic: "Implementing Features"

## Related Documentation
- `.claude/rules/01-core.md` - Core workflow standards
- `.brain/projectRules.md` - Full standards
```

### Task 2.7: Add Cross-Links to `agent-rules/rules/03-architecture.md`
- [ ] Add at top or bottom:
```markdown
## Authoritative Reference
**For full DDD 2025 patterns**, see [`.claude/rules/02-architecture.md`](../../.claude/rules/02-architecture.md) (developer reference).

This document provides a summary for agent perspective.
```

### Task 2.8: Add Backlinks to `agent-rules/rules/04-agents.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `agent-rules/rules/05-triggers.md` - Command triggers
- `RULES_INDEX.md` - Topic: "Understanding agent role"

## Related Documentation
- [agents/](agents/) - Agent definitions
- `agent-rules/rules/00-role.md` - Agent philosophy
```

### Task 2.9: Add Backlinks to `agent-rules/rules/05-triggers.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `RULES_INDEX.md` - Topic: "Command triggers"

## Related Documentation
- `agent-rules/rules/04-agents.md` - Agent invocation
- `agent-rules/rules/06-enforcement.md` - Enforcement
```

### Task 2.10: Add Backlinks to `agent-rules/rules/06-enforcement.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `RULES_INDEX.md` - Topic: "Rules enforcement"

## Related Documentation
- `agent-rules/rules/05-triggers.md` - Command triggers
- `agent-rules/rules/04-agents.md` - Agent control
```

### Task 2.11: Add Backlinks to `agent-rules/rules/08-token-optimization.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- `agent-rules/rules/07-tools.md` - Tool usage
- `RULES_INDEX.md` - Topic: "Performance optimization"

## Related Documentation
- `.brain/context/current.md` - Token budgets for session
- `.brain/docs/qdrant-quick-reference.md` - Semantic search
```

### Task 2.12: Add Cross-Links to `agent-rules/rules/10-node-workflow.md`
- [ ] Add at top/bottom:
```markdown
## Developer Reference
See [`.claude/rules/03-nodes.md`](../../.claude/rules/03-nodes.md) for full 8-step checklist (authoritative).

## Related Files
- [`.claude/rules/nodes/node-registration.md`](../../.claude/rules/nodes/node-registration.md) - Registration steps
- [`11-node-templates.md`](11-node-templates.md) - Template reference
```

### Task 2.13: Add Backlinks to `agent-rules/rules/11-node-templates.md`
- [ ] Add at bottom:
```markdown
---

## Referenced From
- [`10-node-workflow.md`](10-node-workflow.md) - Node workflow
- `RULES_INDEX.md` - Topic: "Creating New Nodes"

## Related Documentation
- `.claude/rules/03-nodes.md` - Node checklist
- `.claude/rules/nodes/node-registration.md` - Registration
- `.brain/docs/node-templates.md` - Full examples
```

---

## Phase 3: Update CLAUDE.md (30 minutes)

### Task 3.1: Update Rules Reference Table
- [ ] Open `CLAUDE.md`
- [ ] Find "Rules Reference" section
- [ ] Update table to match:

```markdown
## Rules Reference

CasareRPA has a comprehensive rules system. Rules are organized in two systems that work together:

### Quick Start
- **New to rules?** → Start with [RULES_INDEX.md](RULES_INDEX.md) - master index by topic
- **Developer focused?** → [.claude/rules/_index.md](.claude/rules/_index.md)
- **Agent/automation focused?** → [agent-rules/_index.md](agent-rules/_index.md)

### Core Rules (.claude/rules/)

| Topic | File |
|-------|------|
| Workflow & Standards | [.claude/rules/01-core.md](.claude/rules/01-core.md) |
| Architecture & DDD | [.claude/rules/02-architecture.md](.claude/rules/02-architecture.md) |
| Node Development | [.claude/rules/03-nodes.md](.claude/rules/03-nodes.md) |
| Event System | [.claude/rules/04-ddd-events.md](.claude/rules/04-ddd-events.md) |
| UI Theme Rules | [.claude/rules/ui/theme-rules.md](.claude/rules/ui/theme-rules.md) |
| Qt Signal/Slot | [.claude/rules/ui/signal-slot-rules.md](.claude/rules/ui/signal-slot-rules.md) |
| Node Registration | [.claude/rules/nodes/node-registration.md](.claude/rules/nodes/node-registration.md) |

### Agent Rules (agent-rules/rules/)

| Topic | File |
|-------|------|
| Agent Workflow | [agent-rules/rules/01-workflow.md](agent-rules/rules/01-workflow.md) |
| Coding Standards | [agent-rules/rules/02-coding-standards.md](agent-rules/rules/02-coding-standards.md) |
| Tools & Optimization | [agent-rules/rules/07-tools.md](agent-rules/rules/07-tools.md), [agent-rules/rules/08-token-optimization.md](agent-rules/rules/08-token-optimization.md) |
| Node Workflow | [agent-rules/rules/10-node-workflow.md](agent-rules/rules/10-node-workflow.md), [agent-rules/rules/11-node-templates.md](agent-rules/rules/11-node-templates.md) |

See [agent-rules/_index.md](agent-rules/_index.md) for complete list.
```

### Task 3.2: Add Master Index Reference
- [ ] In "Key Indexes" or new section, add:
```markdown
### Master Index
- **[RULES_INDEX.md](RULES_INDEX.md)** - Find any rule by topic, phase, or audience
```

---

## Phase 4: Verification & Testing (1-2 hours)

### Task 4.1: Link Verification
- [ ] Open each `_index.md` file and verify:
  - [ ] All links work (no 404s)
  - [ ] All descriptions are accurate
  - [ ] No typos or formatting issues

### Task 4.2: Cross-Reference Verification
- [ ] Open RULES_INDEX.md and verify:
  - [ ] All links work
  - [ ] Decision tree makes sense
  - [ ] Topics are well-organized
  - [ ] No missing critical rules

### Task 4.3: Backlink Verification
- [ ] For each rule file that should be referenced:
  - [ ] Check it has "Referenced From" section
  - [ ] Verify all references actually link to it
  - [ ] Check bidirectional consistency

### Task 4.4: New Developer Walk-Through
- [ ] Get a fresh person (or simulate) with these instructions:
  1. "Create a new node" - use rules to find how
  2. "I found a bug" - use rules to find fix workflow
  3. "I don't know DDD" - use rules to learn
- [ ] Note any places that were confusing
- [ ] Fix those places

### Task 4.5: Broken Link Check
- [ ] Run regex search for references to files that don't exist:
  - [ ] `.brain/docs/node-templates.md` - should exist?
  - [ ] `.brain/docs/node-checklist.md` - should exist?
  - [ ] `.brain/projectRules.md` - should exist?
  - [ ] `.brain/systemPatterns.md` - should exist?
  - [ ] `.brain/decisions/add-node.md` - should exist?
  - [ ] `.brain/decisions/add-feature.md` - should exist?
  - [ ] `.brain/decisions/fix-bug.md` - should exist?
- [ ] Create stubs or remove references as appropriate

---

## Phase 5: Documentation & Cleanup (30 minutes)

### Task 5.1: Update .brain/context/current.md
- [ ] Add section noting rules restructuring:
```markdown
## Rules System Status
- ✅ Created: `.claude/rules/_index.md`
- ✅ Created: `agent-rules/_index.md`
- ✅ Created: `RULES_INDEX.md`
- ✅ Added backlinks to all rule files
- ✅ Updated CLAUDE.md rules section
- Completed: [DATE]
```

### Task 5.2: Archive Analysis Documents
- [ ] After implementation, move these to `docs/` or delete:
  - `RULES_STRUCTURE_ANALYSIS.md` (detailed findings)
  - `RULES_VISUAL_MAP.md` (visual diagrams)
  - `RULES_QUICK_SUMMARY.md` (executive summary)
  - `RULES_FIX_CHECKLIST.md` (this file)
- [ ] OR keep as reference in `docs/rules-refactoring/` for future maintenance

### Task 5.3: Create Maintenance Protocol Document
- [ ] Create `.claude/rules/MAINTENANCE.md`:
```markdown
# Rules System Maintenance

## When Adding New Rule File
1. Create file in appropriate directory
2. Add to relevant `_index.md` (`.claude/rules/` or `agent-rules/rules/`)
3. Add to `RULES_INDEX.md` under topic
4. Add "Referenced From" section at bottom
5. Link from CLAUDE.md if core rule
6. Test all links

## When Modifying Rule File
1. If topic changes, update index files
2. If moving file, update all backlinks
3. Check for related rules and add cross-references
4. Verify links still work

## Quarterly Maintenance
1. Run link checker for broken references
2. Look for orphaned files (not in any index)
3. Look for duplicate content in different systems
4. Update RULES_QUICK_SUMMARY.md statistics
```

### Task 5.4: Final Verification Checklist
- [ ] All 19 rule files are in at least one index ✅
- [ ] All index files have complete descriptions
- [ ] All cross-references work
- [ ] CLAUDE.md points to indexes
- [ ] RULES_INDEX.md covers all topics
- [ ] New developer can navigate without confusion
- [ ] No more than 2 levels of indirection to find any rule (e.g., CLAUDE.md → index → rule)

---

## Summary Statistics

After completing this checklist:

| Metric | Before | After |
|--------|--------|-------|
| Index files | 0 | 3 |
| Files with backlinks | 31% | 100% |
| Orphaned files | 8 | 0 |
| Cross-system references | 0 | 20+ |
| Topics directly indexed | 0 | 15+ |
| Estimated time to find rule | 5-10 min | < 2 min |

---

## Completion Verification

Run this after completing all tasks:

```bash
# Check all index files exist
ls -l .claude/rules/_index.md agent-rules/_index.md RULES_INDEX.md

# Count files in rules
find .claude/rules -name "*.md" | wc -l  # Should be 7
find agent-rules/rules -name "*.md" | wc -l  # Should be 12

# Verify no broken references to missing .brain files
grep -r "\.brain/docs/node-" .claude/rules agent-rules/rules CLAUDE.md

# Find any remaining orphaned files (files not in any index)
# Manual check: open each index and ensure all 19 files are listed
```

---

## Time Estimate Breakdown

| Phase | Time | Notes |
|-------|------|-------|
| Phase 1: Create indexes | 1-2h | Most time spent on content |
| Phase 2: Add backlinks | 2-3h | Mechanical, ~30-45s per file |
| Phase 3: Update CLAUDE.md | 30m | Quick updates |
| Phase 4: Verification | 1-2h | Testing all links |
| Phase 5: Cleanup | 30m | Documentation |
| **TOTAL** | **6-9h** | **Can do in 1-2 work sessions** |

---

## Notes for Executor

1. **Order matters**: Do phases in sequence (can't skip Phase 4)
2. **Test as you go**: Don't wait until Phase 4 to verify links
3. **Be thorough with backlinks**: This is the most important part
4. **Don't over-complicate**: Keep index descriptions brief (1-2 sentences)
5. **Get feedback**: Have someone test navigability after Phase 4
6. **Document decisions**: If you consolidate duplicates, note why
