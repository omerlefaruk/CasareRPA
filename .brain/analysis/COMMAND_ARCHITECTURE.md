# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# CasareRPA Command Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         COMMAND LAYER (.claude/commands/)               │
│                                                                          │
│  /implement-feature  │  /implement-node  │  /fix-feature               │
│  (YAML + Template)   │  (YAML + Template) │  (YAML + Template)         │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (5-Phase Pattern)                │
│                                                                          │
│  Phase 1: RESEARCH (parallel)    ← explore, researcher agents          │
│  Phase 2: PLAN (sequential)       ← architect agent [USER GATE]        │
│  Phase 3: EXECUTE (parallel)      ← builder, ui, integrations, refactor│
│  Phase 4: VALIDATE (sequential)   ← quality, reviewer (loop)           │
│  Phase 5: DOCS (sequential)       ← docs agent                         │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                       AGENT LAYER (.claude/agents/)                     │
│                                                                          │
│  explore        architect       builder        ui          quality      │
│  researcher     (planner)       (coder)        (widgets)   (tester)    │
│                                                 refactor    reviewer     │
│                                                 (cleanup)   (gate)      │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                       RULES LAYER (.claude/rules/)                      │
│                                                                          │
│  01-core.md           ← Workflow, patterns, imports                    │
│  02-architecture.md   ← DDD layers, events, aggregates                 │
│  03-nodes.md          ← Node-specific rules                            │
│  04-ddd-events.md     ← Event definitions                              │
│  ui/theme-rules.md    ← Theme constants, colors                        │
│  ui/signal-slot-rules.md ← Qt decorators, connections                  │
│  nodes/node-registration.md ← Node registry patterns                   │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER (Planning Documents)                    │
│                                                                          │
│  .brain/plans/{feature}.md   ← Created by architect in PLAN phase     │
│  .brain/plans/node-{name}.md                                           │
│  .brain/plans/fix-{issue}.md                                           │
│                                                                          │
│  Contains:                                                              │
│  - Scope, files to create/modify                                       │
│  - Agent assignments & parallelization strategy                        │
│  - Risks & mitigation                                                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Command Definition Layer

**Location**: `.claude/commands/`

```
.claude/commands/
├── implement-feature.md
│   ├── YAML Frontmatter (description, arguments)
│   └── Template body with $ARGUMENTS variable substitution
│
├── implement-node.md
│   ├── YAML Frontmatter (node_name required, category/mode optional)
│   └── Template for 6 phases (+ REGISTRATION)
│
└── fix-feature.md
    ├── YAML Frontmatter (type optional, description required)
    └── Template for diagnosis + 4 phases
```

**YAML Metadata Format**:
```yaml
---
description: Brief description of what command does
arguments:
  - name: parameter_name
    description: What this parameter does
    required: true|false
  - name: mode
    description: Execution mode (implement|refactor|etc)
    required: false
---

# Markdown body with $ARGUMENTS.{param} variable substitution
```

### Reference Documentation Layer

**Location**: `agent-rules/commands/`

```
agent-rules/commands/
├── implement-feature.md
│   ├── Mode Router (implement, refactor, optimize, extend)
│   ├── Detailed Phase 1-5 with examples
│   └── Quick reference section
│
├── implement-node.md
│   ├── Mode Router (implement, extend, refactor, clone)
│   ├── Detailed Phase 1-6 with templates
│   ├── Registration pattern
│   └── Example invocations
│
└── fix-feature.md
    ├── Bug Type Router (crash, output, ui, perf, flaky)
    ├── Detailed diagnosis patterns
    ├── Common fix patterns
    └── Rollback instructions
```

### Agent Specification Layer

**Location**: `.claude/agents/`

```
.claude/agents/
├── explore.md
│   └── Fast codebase search using qdrant/grep
│       Output: Pattern discoveries, file paths
│
├── researcher.md
│   └── External research via MCP tools
│       Output: Best practices, API docs, solutions
│
├── architect.md
│   └── System design, create planning documents
│       Output: .brain/plans/{feature}.md with agent assignments
│
├── builder.md
│   └── Write new code following DDD patterns
│       Output: Python modules with decorators, type hints
│
├── refactor.md
│   └── Code cleanup, restructuring
│       Output: Cleaner, more maintainable code
│
├── ui.md
│   └── PySide6/Qt components, visual nodes
│       Output: Panels, dialogs, widgets, visual wrappers
│
├── integrations.md
│   └── External APIs, OAuth, databases
│       Output: Client classes, API adapters
│
├── quality.md
│   └── Tests (unit/integration), performance profiling
│       Output: Test files, performance reports
│
├── reviewer.md
│   └── Code review gate, checklist validation
│       Output: APPROVED or ISSUES (file:line format)
│
└── docs.md
    └── Documentation updates, index files
        Output: Updated _index.md, docstrings, context
```

### Project Standards Layer

**Location**: `.claude/rules/`

```
.claude/rules/
├── 01-core.md
│   ├── Workflow standards
│   ├── Import rules (DDD layer separation)
│   ├── Error handling (try/except + loguru)
│   └── Type hints requirement
│
├── 02-architecture.md
│   ├── DDD layer structure (domain, application, infrastructure, presentation)
│   ├── Aggregate roots, value objects
│   ├── Event patterns with typed dataclasses
│   └── CQRS query patterns
│
├── 03-nodes.md
│   ├── Node base class requirements
│   ├── Port definitions (exec, data types)
│   ├── Property decorators (@properties)
│   └── Async execute() pattern
│
├── 04-ddd-events.md
│   ├── Typed event definitions
│   ├── Event bus subscription patterns
│   ├── Event publishing rules
│   └── Complete event class reference
│
├── nodes/
│   └── node-registration.md
│       ├── _NODE_REGISTRY structure
│       ├── __init__.py exports
│       └── Visual node registration
│
└── ui/
    ├── theme-rules.md
    │   ├── THEME dictionary keys
    │   ├── Color usage patterns
    │   └── Hardcoded color violations
    │
    └── signal-slot-rules.md
        ├── @Slot decorator requirements
        ├── Connection patterns (functools.partial)
        └── Thread safety rules
```

---

## Phase Execution Model

### Phase 1: RESEARCH

**Goal**: Understand patterns, dependencies, best practices

```
┌─────────────────────────────────────────────────┐
│ RESEARCH (Parallel - up to 3 agents)            │
└─────────────────────────────────────────────────┘

Agent 1: explore
  ├─ Find similar patterns in target scope
  ├─ Search .brain/symbols.md for existing code
  ├─ Use qdrant-find for semantic search
  └─ Output: file paths, class structures, dependencies

Agent 2: explore (optional)
  ├─ Find test patterns
  ├─ Find fixtures and mocking strategies
  └─ Output: test structure, setup/teardown patterns

Agent 3: researcher (optional, for integrations/APIs)
  ├─ Research external APIs, SDKs, libraries
  ├─ Use MCP tools for web search
  └─ Output: best practices, documentation links

Gate: AUTO-PROCEED to PLAN
```

### Phase 2: PLAN

**Goal**: Create implementation strategy approved by user

```
┌─────────────────────────────────────────────────┐
│ PLAN (Sequential - 1 agent)                     │
└─────────────────────────────────────────────────┘

Agent: architect
  ├─ Review RESEARCH findings
  ├─ Design system architecture
  ├─ Create .brain/plans/{name}.md with:
  │  ├─ Files to create/modify
  │  ├─ Agent assignments (builder, ui, integrations, refactor)
  │  ├─ Parallel opportunities
  │  ├─ Risks & mitigation
  │  └─ Test plan
  └─ Output: Planning document

Gate: USER APPROVAL ("Plan ready. Approve?")
  ├─ APPROVED → EXECUTE
  └─ REJECTED → Provide feedback → architect revises
```

### Phase 3: EXECUTE

**Goal**: Implement code following plan

```
┌─────────────────────────────────────────────────┐
│ EXECUTE (Parallel - 2-5 agents)                 │
└─────────────────────────────────────────────────┘

Mode-dependent agent selection:

IMPLEMENT-FEATURE:
  ├─ implement → builder + ui + integrations (parallel)
  ├─ refactor  → refactor only
  ├─ optimize  → quality(perf) + refactor (parallel)
  └─ extend    → builder + refactor (parallel)

IMPLEMENT-NODE:
  ├─ implement → builder + ui + quality (parallel)
  ├─ extend    → builder + quality (parallel)
  ├─ refactor  → refactor + quality (parallel)
  └─ clone     → builder + ui + quality (parallel)

FIX-FEATURE:
  └─ fix       → builder + refactor (parallel)

Code Rules Applied (all agents):
  ├─ Theme constants only (THEME['bg_primary'])
  ├─ UnifiedHttpClient for HTTP
  ├─ @Slot decorators on all signal handlers
  ├─ Typed domain events
  ├─ Exec ports via add_exec_input()
  ├─ Try/except with loguru logging
  └─ Type hints on all methods

Gate: AUTO-PROCEED to VALIDATE
```

### Phase 4: VALIDATE

**Goal**: Verify code quality, tests pass, review approved

```
┌─────────────────────────────────────────────────┐
│ VALIDATE (Sequential Loop - 2 agents)           │
└─────────────────────────────────────────────────┘

Step 1: quality agent (test mode)
  ├─ Create test suite (if mode=implement/extend)
  ├─ Run pytest
  ├─ Cover: SUCCESS, ERROR, EDGE_CASES
  └─ Output: Test results, coverage

Step 2: reviewer agent
  ├─ Check: error handling, type hints, patterns
  ├─ Check: compliance with coding rules
  ├─ Output: APPROVED or ISSUES
  │
  │   APPROVED → DOCS
  │
  │   ISSUES (with file:line):
  │   └─ CRITICAL: Must fix before merge
  │      MAJOR: Should fix
  │      MINOR: Consider fixing

Loop Logic (if ISSUES):
  ├─ Agents fix issues
  ├─ quality re-runs tests
  ├─ reviewer re-checks
  └─ Loop until APPROVED

Gate: APPROVED by reviewer
```

### Phase 5: DOCS

**Goal**: Update documentation, index files, context

```
┌─────────────────────────────────────────────────┐
│ DOCS (Sequential - 1 agent)                     │
└─────────────────────────────────────────────────┘

Agent: docs
  ├─ Update _index.md files:
  │  ├─ nodes/_index.md (for nodes)
  │  ├─ visual_nodes/_index.md (for visual nodes)
  │  ├─ domain/{scope}/_index.md
  │  ├─ application/use_cases/_index.md
  │  └─ infrastructure/_index.md
  │
  ├─ Update .brain/context/current.md
  ├─ Add docstrings to new code
  └─ Output: Updated documentation

Gate: AUTO-PROCEED to COMPLETION
```

### Special Phase 5.5: REGISTRATION (Node Only)

**Goal**: Register new node in system

```
┌─────────────────────────────────────────────────┐
│ REGISTRATION (Sequential - builder)             │
│ [ONLY for /implement-node]                      │
└─────────────────────────────────────────────────┘

After VALIDATE APPROVED:

Agent: builder
  ├─ Update nodes/{category}/__init__.py
  ├─ Update nodes/registry_data.py
  ├─ Update visual_nodes/{category}/__init__.py
  └─ Output: Registered node ready for use

Gate: AUTO-PROCEED to DOCS
```

---

## Parameter System

### YAML Argument Processing

```yaml
# Definition in .claude/commands/implement-feature.md
---
arguments:
  - name: scope
    description: domain, application, infrastructure, presentation, nodes
    required: false
  - name: mode
    description: implement, refactor, optimize, extend
    required: false
---
```

### Template Variable Substitution

In command body:
```markdown
# When user invokes:
/implement-feature presentation

# Variables in template get substituted:
$ARGUMENTS.scope      → "presentation"
$ARGUMENTS.mode       → "implement" (default)

# Task becomes:
Task(subagent_type="explore",
     prompt="Find patterns in src/casare_rpa/presentation/")
```

### Parameter Types

| Parameter | Type | Default | Examples |
|-----------|------|---------|----------|
| scope | enum | none | domain, application, infrastructure, presentation, nodes |
| mode | enum | implement | implement, refactor, optimize, extend, clone |
| node_name | string | required | ClickElement, SendSlackMessage |
| category | enum | optional | browser, desktop, data, integration, system, flow, ai |
| type | enum | auto-detect | crash, output, ui, perf, flaky |
| description | string | required | "Node execution crashes with AttributeError" |

---

## Agent Collaboration Patterns

### Parallel Execution Strategy

**Rule**: "Launch up to 5 agents in parallel when tasks are independent"

#### When Parallelism Works
```
Task(explore, "Find patterns in domain/")
Task(explore, "Find patterns in infrastructure/")
Task(researcher, "Research OAuth best practices")
# All three launch simultaneously in single message
```

#### When Sequencing Required
```
PLAN GATE: User must approve before EXECUTE
VALIDATE LOOP: quality → reviewer → (fix if needed) → re-validate
DOCS: Single docs agent (sequential)
```

### Agent Dependencies

```
Independent (parallel):
├─ explore + explore (different scopes)
├─ builder + ui (different components)
├─ builder + integrations (different layers)
├─ quality(perf) + refactor (parallel optimization)
└─ explore + researcher (parallel discovery)

Dependent (sequential):
├─ PLAN → EXECUTE (user gate between)
├─ EXECUTE → VALIDATE (code must exist before testing)
├─ quality → reviewer (test must pass before review)
└─ reviewer → DOCS (documentation after approval)
```

---

## Command Router Logic

### Feature Router
```
/implement-feature [scope] [mode]

scope → Layer hint (determines agent focus)
mode  → Execution strategy
  ├─ implement → New feature (builder + ui + integrations)
  ├─ refactor  → Cleanup (refactor only)
  ├─ optimize  → Performance (quality(perf) + refactor)
  └─ extend    → Add to existing (builder + refactor)
```

### Node Router
```
/implement-node node_name [category] [mode]

node_name  → Node class name (REQUIRED)
category   → Browser/Desktop/Data/Integration/System/Flow/AI
mode       → Operation
  ├─ implement → Create new (builder + ui + quality)
  ├─ extend    → Add ports (builder + quality)
  ├─ refactor  → Cleanup (refactor + quality)
  └─ clone     → Variant (builder + ui + quality)
```

### Bug Router
```
/fix-feature [type] description

type        → Bug category (auto-detects from description)
  ├─ crash  → Exception (explore logs, error handling)
  ├─ output → Wrong results (trace data flow)
  ├─ ui     → Display (check signals, slots)
  ├─ perf   → Slow (profile with quality(perf))
  ├─ flaky  → Intermittent (check async, shared state)
  └─ auto   → Unknown (parallel exploration + research)

description → What's broken (REQUIRED)
```

---

## Coding Standards Application

All agents follow these rules during EXECUTE phase:

### Rule Sources
- `.claude/rules/01-core.md` - Import structure, error handling
- `.claude/rules/02-architecture.md` - DDD patterns, events
- `.claude/rules/03-nodes.md` - Node-specific patterns
- `.claude/rules/ui/theme-rules.md` - Color/theme usage
- `.claude/rules/ui/signal-slot-rules.md` - Qt decorators
- `.claude/rules/nodes/node-registration.md` - Registry pattern

### Enforcement
- **builder**: All rules apply (domain, application logic)
- **ui**: Theme rules + signal-slot rules
- **integrations**: Error handling + logging rules
- **refactor**: All rules + cleanup patterns
- **reviewer**: Checklist validation against rules

---

## Planning Document Structure

### File Location
```
.brain/plans/{context}.md

Where {context}:
- {feature-name}     → For /implement-feature
- node-{node-name}   → For /implement-node
- fix-{issue}        → For /fix-feature
```

### Document Format

```markdown
# [Feature|Node|Fix]: {Name}

## Scope / Category
{domain, application, infrastructure, presentation, nodes}

## Purpose
One sentence description.

## Files to Create
- src/casare_rpa/path/file.py - What it does

## Files to Modify
- src/casare_rpa/path/existing.py - What changes (line numbers)

## Agent Assignments

### Phase 1: RESEARCH
- explore: Find patterns in {scope}
- researcher: Research best practices (if applicable)

### Phase 3: EXECUTE
- builder: Create domain/application logic
- ui: Create UI components/panels
- integrations: Create API clients

### Phase 4: VALIDATE
- quality: Create test suite
- reviewer: Code review checklist

## Parallel Opportunities
- Phase 3A: builder + ui (independent components)
- Phase 3B: quality (while refactoring)

## Risks
1. Risk description → Mitigation strategy
2. Dependency on X → Use interface/mock

## Test Plan
- Unit tests: Coverage of success + error paths
- Integration tests: Cross-layer functionality
- Property-based: Edge cases

## Notes
Additional considerations, gotchas, dependencies.
```

---

## Completion Reporting

After all phases complete, command reports:

```
✓ Phase 1 RESEARCH
  ├─ Patterns discovered: N files
  ├─ Dependencies identified: X, Y, Z
  └─ Best practices: Summary

✓ Phase 2 PLAN
  ├─ Planning document: .brain/plans/{name}.md
  ├─ User approved: Yes
  └─ Agent assignments: builder(2), ui(1), quality(1)

✓ Phase 3 EXECUTE
  ├─ Files created: N
  ├─ Files modified: M
  └─ Lines of code: K

✓ Phase 4 VALIDATE
  ├─ Tests created: N tests
  ├─ Tests passing: N/N
  ├─ Coverage: X%
  └─ Review: APPROVED

✓ Phase 5 DOCS
  ├─ Files updated: _index.md (N files)
  ├─ Context updated: .brain/context/current.md
  └─ Docstrings added: N

[COMPLETION] Feature ready for use
[NEXT STEPS] How to use/test the new feature
```

---

## Integration Points

### External Systems

#### MCP Tools (used by researcher agent)
```
mcp__Ref__ref_search_documentation: "Framework documentation"
mcp__Ref__ref_read_url: "https://docs.example.com/..."
mcp__exa__get_code_context_exa: "Code examples" (tokensNum=5000)
mcp__exa__web_search_exa: "Web search query"
```

#### Project Systems
```
- .brain/symbols.md          ← Symbol registry
- .brain/errors.md           ← Error catalog
- .brain/systemPatterns.md   ← Existing patterns
- .brain/projectRules.md     ← Coding standards
- nodes/_index.md            ← Node catalog
```

#### Index Files (updated in DOCS phase)
```
src/casare_rpa/domain/_index.md
src/casare_rpa/application/_index.md
src/casare_rpa/infrastructure/_index.md
src/casare_rpa/presentation/canvas/_index.md
src/casare_rpa/nodes/_index.md
src/casare_rpa/presentation/canvas/visual_nodes/_index.md
```

---

## State & Context

### Session State
Location: `.brain/context/current.md`

Updated in DOCS phase with:
- Current focus/work
- Files created/modified
- Completed features
- Next steps

### Decision Trees
Location: `.brain/decisions/`

```
add-feature.md      ← How to add features by layer
add-node.md         ← How to create nodes step-by-step
fix-bug.md          ← Debugging strategy
```

---

## Summary

The CasareRPA command system provides:

1. **Three main commands**: Feature, Node, Bug Fix
2. **5-phase pattern**: RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
3. **Parallel execution**: Up to 5 agents in independent phases
4. **User gates**: PLAN approval required before execution
5. **Automated validation**: quality + reviewer loop until approved
6. **Planning documents**: `.brain/plans/` guide future development
7. **Comprehensive standards**: Rules layer ensures code quality
8. **Rich documentation**: Both machine-readable (.claude/) and human-readable (agent-rules/)
