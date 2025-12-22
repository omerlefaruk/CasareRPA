# CasareRPA Command Structure Analysis

## Overview

CasareRPA uses a **dual-layer command system**:
- **User-facing commands**: `.claude/commands/` (high-level, template-based)
- **Detailed agent guides**: `agent-rules/commands/` (comprehensive, for agent reference)

Both directories contain identical command logic but different presentation styles.

---

## 1. Command Locations

### Primary Location: `.claude/commands/`
```
.claude/commands/
├── implement-feature.md    (YAML frontmatter + templated prompts)
├── implement-node.md       (YAML frontmatter + templated prompts)
└── fix-feature.md          (YAML frontmatter + templated prompts)
```

**Purpose**: Machine-readable format with YAML metadata and template variable substitution.

### Reference Location: `agent-rules/commands/`
```
agent-rules/commands/
├── implement-feature.md    (Human-readable, detailed flow + examples)
├── implement-node.md       (Human-readable, detailed flow + examples)
└── fix-feature.md          (Human-readable, detailed flow + examples)
```

**Purpose**: Detailed reference guide for agents and understanding the architecture.

---

## 2. Command Structure Template

All commands follow this **5-phase execution pattern**:

### Phase 1: RESEARCH (Parallel Agents)
- **Agents**: `explore` (x1-3) + `researcher` (optional)
- **Parallelism**: Yes (up to 3 agents)
- **Output**: Pattern findings, dependencies, best practices

### Phase 2: PLAN (Sequential)
- **Agent**: `architect`
- **Parallelism**: No
- **Output**: `.brain/plans/{feature}.md` (user approval required)
- **Gate**: User review/approval before proceeding

### Phase 3: EXECUTE (Parallel Agents)
- **Agents**: `builder`, `ui`, `integrations`, `refactor` (mode-dependent)
- **Parallelism**: Yes (2-5 agents depending on scope)
- **Output**: Implemented code

### Phase 4: VALIDATE (Sequential Loop)
- **Agents**: `quality` → `reviewer` (loop)
- **Parallelism**: No (sequential validation)
- **Output**: Tests passing, review approved
- **Loop**: If ISSUES found, fix → re-validate

### Phase 5: DOCS (Sequential)
- **Agent**: `docs`
- **Parallelism**: No
- **Output**: Updated index files, context

---

## 3. Three Main Commands

### 3.1 `/implement-feature`

**YAML Metadata** (`.claude/commands/implement-feature.md`):
```yaml
description: Implement a new feature with full agent orchestration.
            Modes: implement (default), refactor, optimize, extend
arguments:
  - name: scope
    description: Scope hint (domain, application, infrastructure, presentation, nodes)
    required: false
  - name: mode
    description: Mode (implement, refactor, optimize, extend). Default is implement.
    required: false
```

**Parameters Accepted**:
- `scope`: Layer hint (domain|application|infrastructure|presentation|nodes)
- `mode`: Execution mode (implement|refactor|optimize|extend)

**Mode Router**:
```
├─ implement  → New feature from scratch (EXECUTE: builder, ui, integrations)
├─ refactor   → Cleanup existing code (EXECUTE: refactor only)
├─ optimize   → Performance improvement (EXECUTE: quality(perf) + refactor)
└─ extend     → Add to existing feature (EXECUTE: builder + refactor)
```

**Agent Flow**:
```
explore (parallel) → architect → builder/refactor/ui/integrations (parallel)
  → quality → reviewer (loop) → docs
```

**Parallel Agents in EXECUTE**:
- `builder`: Domain/application logic
- `ui`: UI components, visual nodes
- `integrations`: API clients, external services
- `refactor`: Code cleanup (mode=refactor or mode=optimize)

**Example Invocation**:
```bash
/implement-feature presentation
# "Add workflow template browser panel"
# → explore → architect → ui(panel) + ui(dialog) → quality → reviewer → docs

/implement-feature
# "Add real-time collaboration"
# → explore(x2) + researcher → architect → builder + integrations + ui(x2) → quality → reviewer → docs
```

---

### 3.2 `/implement-node`

**YAML Metadata** (`.claude/commands/implement-node.md`):
```yaml
description: Implement a new automation node with parallel agent orchestration.
            Modes: implement (default), extend, refactor, clone
arguments:
  - name: node_name
    description: Name of the node (e.g., GoogleSheetsRowRead, ClickElement)
    required: true
  - name: category
    description: Node category (browser, desktop, data, integration, system, flow, ai)
    required: false
  - name: mode
    description: Mode (implement, extend, refactor, clone). Default is implement.
    required: false
```

**Parameters Accepted**:
- `node_name`: Name of node to create (REQUIRED)
- `category`: Node category (browser|desktop|data|integration|system|flow|ai)
- `mode`: Execution mode (implement|extend|refactor|clone)

**Mode Router**:
```
├─ implement → Create new node (EXECUTE: builder + ui + quality)
├─ extend    → Add ports/properties (EXECUTE: builder + quality)
├─ refactor  → Improve code quality (EXECUTE: refactor + quality)
└─ clone     → Create variation (EXECUTE: builder + ui + quality)
```

**Agent Flow**:
```
explore → architect → builder + ui + quality (parallel)
  → reviewer (loop) → registration → docs
```

**Special Phase 5: REGISTRATION** (after validation):
- Update `nodes/{category}/__init__.py`
- Update `nodes/registry_data.py`
- Update `visual_nodes/{category}/__init__.py`

**Parallel Agents in EXECUTE**:
- `builder`: Node logic class + registration
- `ui`: Visual node wrapper
- `quality`: Unit tests

**Example Invocation**:
```bash
/implement-node browser
# "Click element with retry and wait"
# → explore → architect → builder + ui + quality → reviewer → registration → docs

/implement-node integration
# "Send Slack notification"
# → explore + researcher → architect → builder + ui + quality → reviewer → registration → docs
```

---

### 3.3 `/fix-feature`

**YAML Metadata** (`.claude/commands/fix-feature.md`):
```yaml
description: Fix bugs and issues in existing features.
            Types: crash, output, ui, perf, flaky
arguments:
  - name: type
    description: Bug type (crash, output, ui, perf, flaky). Leave empty for unknown.
    required: false
  - name: description
    description: Description of the bug or issue
    required: true
```

**Parameters Accepted**:
- `type`: Bug category (crash|output|ui|perf|flaky|auto-detect)
- `description`: Bug description (REQUIRED)

**Bug Type Router**:
```
├─ crash  → Exception, stack trace (explore: logs, error handling, git history)
├─ output → Wrong data (explore: data flow, assertions)
├─ ui     → Display issues (explore: signals, slots, threads)
├─ perf   → Slow/memory leak (explore: blocking calls + quality(perf))
├─ flaky  → Test intermittency (explore: async, shared state)
└─ auto   → Unknown (explore: code + researcher: web search)
```

**Agent Flow**:
```
explore(parallel) → architect → builder + refactor (parallel)
  → quality → reviewer (loop) → docs(optional)
```

**Parallel Diagnosis Agents**:
- Up to **5 agents** in parallel for discovery
- Bug-specific explore agents (3-5 agents)
- `researcher` for unknown bugs (web search)
- `quality` with perf mode for performance bugs

**Example Invocation**:
```bash
/fix-feature crash
# "Node execution crashes with AttributeError"
# → explore(x3) → architect → builder → quality → reviewer

/fix-feature perf
# "Canvas freezes when loading large workflow"
# → explore(x2) + quality(perf) → architect → refactor → quality → reviewer
```

---

## 4. Available Agents

### Agent Registry (`.claude/agents/`)

| Agent | Model | Primary Use | In Commands |
|-------|-------|-------------|------------|
| `explore` | haiku | Fast codebase search, pattern discovery | RESEARCH, DIAGNOSE |
| `researcher` | opus | External research, library docs, best practices | RESEARCH, DIAGNOSE |
| `architect` | opus | System design, data contracts, planning | PLAN |
| `builder` | opus | Write new code, DDD principles | EXECUTE, FIX |
| `refactor` | opus | Code cleanup, restructure, modernize | EXECUTE (mode=refactor) |
| `ui` | opus | PySide6/Qt panels, widgets, visual nodes | EXECUTE (implement/extend/clone) |
| `integrations` | opus | REST/GraphQL APIs, OAuth, databases | EXECUTE (infrastructure) |
| `quality` | opus | Tests (unit/integration), performance, stress | VALIDATE, DIAGNOSE(perf) |
| `reviewer` | opus | Code review gate (APPROVED or ISSUES) | VALIDATE |
| `docs` | opus | API docs, user guides, _index.md updates | DOCS phase |

---

## 5. Phase Execution Details

### RESEARCH Phase
```
Parallelism: YES (up to 3-4 agents)

For FEATURE implementation:
- Task(explore, "Find patterns in $ARGUMENTS.scope/")
- Task(explore, "Find test patterns in tests/")
- Task(researcher, "Research best practices")  # Optional

For NODE implementation:
- Task(explore, "Find similar nodes in nodes/$ARGUMENTS.category/")
- Task(explore, "Find base classes and decorators")
- Task(researcher, "Research external API")  # If integration node

For BUG fixing:
- Task(explore, "Find error in logs/")           # Parallel x3-5
- Task(explore, "Find related code")
- Task(explore, "Find git history")
- Task(researcher, "Research error message")     # If unknown bug
```

### PLAN Phase
```
Parallelism: NO (sequential)
Agent: architect

Outputs:
- File: .brain/plans/{feature|node|fix}-{name}.md
- Format: Markdown with sections (Scope, Files, Agents, Risks)

Gate: User review/approval required
  "Plan ready. Approve EXECUTE?"
```

### EXECUTE Phase
```
Parallelism: YES (2-5 agents)

Agent selection by scope/mode:

IMPLEMENT-FEATURE:
  ├─ implement: builder + ui + integrations
  ├─ refactor: refactor
  └─ optimize: quality(perf) + refactor

IMPLEMENT-NODE:
  ├─ implement: builder + ui + quality
  ├─ extend: builder + quality
  ├─ refactor: refactor + quality
  └─ clone: builder + ui + quality

FIX-FEATURE:
  └─ fix: builder + refactor (parallel)

Constraint: NO user gate between PLAN and EXECUTE
```

### VALIDATE Phase
```
Parallelism: NO (sequential loop)
Agents: quality → reviewer → (loop if ISSUES)

Quality Agent (quality):
  - mode: test
    ├─ Create test suite
    ├─ Run pytest
    └─ Cover SUCCESS, ERROR, EDGE_CASES

Reviewer Agent (reviewer):
  - Check: Error handling, type hints, patterns
  - Output: APPROVED or ISSUES (with file:line)

Loop Logic:
  If ISSUES:
    → fix → quality(re-test) → reviewer(re-review) → approved
  Else:
    → continue to DOCS
```

### DOCS Phase
```
Parallelism: NO (sequential)
Agent: docs

Tasks:
1. Update _index.md files
2. Update .brain/context/current.md
3. Add/update docstrings

Files to update (if applicable):
- domain/{scope}/_index.md
- nodes/_index.md (for nodes)
- visual_nodes/_index.md (for visual nodes)
- presentation/canvas/ui/panels/__init__.py
- application/use_cases/__init__.py
```

---

## 6. Parameter Processing & Template Variables

### .claude/commands/ Format (YAML + Template)

```yaml
---
description: Brief command description
arguments:
  - name: {param_name}
    description: What it's for
    required: true|false
---

# Command body with template variables:
$ARGUMENTS.{param_name}
$ARGUMENTS.mode
$ARGUMENTS.scope
```

**Template Variable Substitution**:
- `$ARGUMENTS.scope` → User-provided scope or default
- `$ARGUMENTS.mode` → User-provided mode (implement|refactor|optimize|extend)
- `$ARGUMENTS.node_name` → User-provided node name
- `$ARGUMENTS.category` → User-provided category
- `$ARGUMENTS.type` → Bug type or auto-detect
- `$ARGUMENTS.description` → User-provided description

**Example Variable Usage**:
```
Task(subagent_type="explore",
     prompt="Find patterns in src/casare_rpa/$ARGUMENTS.scope/")
# With scope="presentation" becomes:
Task(subagent_type="explore",
     prompt="Find patterns in src/casare_rpa/presentation/")
```

---

## 7. Agent Coordination Rules

### Parallel Execution Rules

**CRITICAL CONSTRAINT**: "Launch up to **5 agents in parallel** when tasks are independent"

```
# CORRECT - Parallel
Task(explore, "Find X")
Task(explore, "Find Y")
Task(researcher, "Research Z")
# All launch in single message

# WRONG - Sequential
Task(explore, "Find X")  → wait
Task(explore, "Find Y")  → wait
Task(researcher, "Research Z")
```

### Agent Dependencies

```
RESEARCH agents → PLAN → EXECUTE agents → VALIDATE agents → DOCS
   (parallel)     (seq)    (parallel)      (sequential loop)  (seq)

Sequential blocking points:
1. After PLAN: User approval required
2. After EXECUTE: Must pass validation before DOCS
3. During VALIDATE: quality → reviewer → (loop if issues)
```

### Phase Gate Locations

| Phase | Gate Type | Who Approves |
|-------|-----------|-------------|
| RESEARCH | Auto-proceed | No approval needed |
| PLAN | **User approval** | "Plan ready. Approve?" |
| EXECUTE | Auto-proceed | No approval needed (if PLAN approved) |
| VALIDATE | Auto-loop | If ISSUES, fix & re-validate |
| DOCS | Auto-proceed | No approval needed |

---

## 8. Coding Rules Applied by Agents

All agents follow these **non-negotiable rules** during EXECUTE:

| Rule | Correct | Wrong |
|------|---------|-------|
| **Theme** | `THEME['bg_primary']` | `"#1a1a2e"` |
| **HTTP** | `UnifiedHttpClient` | `httpx.get()` |
| **Signals** | `@Slot(str)` decorator | Missing decorator |
| **Connections** | `functools.partial(fn, arg)` | `lambda: fn(arg)` |
| **Events** | `NodeCompleted(node_id="x")` | `{"type": "done"}` |
| **Exec Ports** | `add_exec_input()` | `add_input_port("exec", EXEC_INPUT)` |
| **Errors** | `try/except` + loguru | Silent `pass` |

---

## 9. Command Flow Comparison

### Feature Implementation
```
Feature → RESEARCH (explore)
        → PLAN (architect) [USER GATE]
        → EXECUTE (builder/ui/integrations) [parallel]
        → VALIDATE (quality/reviewer) [loop]
        → DOCS (docs)
```

### Node Implementation
```
Node → RESEARCH (explore)
     → PLAN (architect) [USER GATE]
     → EXECUTE (builder/ui/quality) [parallel]
     → VALIDATE (reviewer) [loop]
     → REGISTRATION (builder)
     → DOCS (docs)
```

### Bug Fixing
```
Bug → DIAGNOSE (explore x3-5) [parallel]
    → PLAN (architect) [USER GATE]
    → FIX (builder/refactor) [parallel]
    → VALIDATE (quality/reviewer) [loop]
    → DOCS (docs) [optional]
```

---

## 10. File Structure Summary

### Commands Directory
```
.claude/
├── commands/                      # User-facing command specs
│   ├── implement-feature.md      # Template: YAML + $ARGUMENTS
│   ├── implement-node.md         # Template: YAML + $ARGUMENTS
│   └── fix-feature.md            # Template: YAML + $ARGUMENTS
│
├── agents/                        # Individual agent prompts
│   ├── explore.md                # Fast codebase search
│   ├── architect.md              # System design & planning
│   ├── builder.md                # Code implementation
│   ├── ui.md                     # PySide6/Qt components
│   ├── integrations.md           # API & external services
│   ├── refactor.md               # Code cleanup
│   ├── quality.md                # Testing & performance
│   ├── reviewer.md               # Code review gate
│   ├── researcher.md             # External research
│   └── docs.md                   # Documentation updates
│
└── rules/                         # Project coding standards
    ├── 01-core.md                # Workflow & standards
    ├── 02-architecture.md        # DDD patterns
    ├── 03-nodes.md               # Node development
    ├── 04-ddd-events.md          # Event definitions
    ├── nodes/
    │   └── node-registration.md
    └── ui/
        ├── theme-rules.md
        └── signal-slot-rules.md

agent-rules/
└── commands/                      # Detailed reference guides
    ├── implement-feature.md      # Full flow + examples
    ├── implement-node.md         # Full flow + examples
    └── fix-feature.md            # Full flow + examples
```

---

## 11. Reference Files in .brain/

### Planning & Documentation
```
.brain/
├── plans/                         # Feature/node/fix planning docs
│   ├── {feature-name}.md         # Created by architect in PLAN phase
│   ├── node-{name}.md            # Node specification
│   └── fix-{issue}.md            # Fix approach document
│
├── decisions/                     # Decision trees
│   ├── add-feature.md            # Feature decision tree
│   ├── add-node.md               # Node decision tree
│   └── fix-bug.md                # Bug fix decision tree
│
├── context/
│   └── current.md                # Session state (updated in DOCS phase)
│
└── docs/                          # Technical documentation
    ├── node-templates.md         # Node code templates
    ├── node-checklist.md         # Node implementation steps
    ├── super-node-pattern.md     # Super node pattern guide
    └── QDRANT_*.md               # Semantic search documentation
```

---

## 12. Key Takeaways

### Command Structure
1. **Two-layer system**: `.claude/commands/` (machine-readable) + `agent-rules/commands/` (human reference)
2. **5-phase pattern**: RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
3. **Parallel-first**: Launch independent agents simultaneously
4. **Sequential gates**: Only PLAN requires user approval; validation loops automatically

### Agent Coordination
1. **Specialized roles**: explore (search), architect (design), builder (code), ui (UI), quality (tests)
2. **Parallel execution**: Up to 5 agents in independent phases
3. **Sequential validation**: quality → reviewer → loop pattern

### Parameter System
1. **YAML metadata**: Defines arguments, defaults, requirements
2. **Template variables**: `$ARGUMENTS.{param_name}` in prompt templates
3. **Mode routing**: Different agent selections based on mode parameter
4. **Scope hints**: Layer-specific agent selection

### Quality Gates
1. **PLAN gate**: User must approve before EXECUTE
2. **VALIDATE loop**: Tests must pass, reviewer must approve
3. **Auto-proceed**: RESEARCH, EXECUTE, DOCS have no user gates

---

## 13. Usage Patterns

### When to Use `/implement-feature`
- Add new UI components (panels, dialogs)
- Create new use cases/handlers
- Integrate external APIs
- Refactor or optimize existing code
- Add to existing features

### When to Use `/implement-node`
- Create automation nodes (browser, desktop, integration)
- Add new capabilities to workflow engine
- Clone and modify existing nodes
- Extend nodes with new ports/properties

### When to Use `/fix-feature`
- Fix bugs/crashes
- Correct output errors
- Resolve UI display issues
- Fix performance problems
- Resolve flaky tests

---

## Example Invocation Patterns

### Full Implementation (5 parallel agents)
```bash
/implement-feature
> "Add OAuth login to canvas authentication"
Agents: explore(x2) + researcher → architect → builder + integrations + ui → quality → reviewer → docs
```

### Scoped Implementation (3 parallel agents)
```bash
/implement-feature presentation
> "Add workflow template browser"
Agents: explore(x2) → architect → ui(x2) → quality → reviewer → docs
```

### Node with Integration (4 parallel agents)
```bash
/implement-node integration
> "Slack notification node"
Agents: explore + researcher → architect → builder + ui + quality → reviewer → registration → docs
```

### Bug Diagnosis (5 parallel agents)
```bash
/fix-feature
> "Canvas freezes on large workflow load"
Agents: explore(x3) + quality(perf) → architect → refactor → quality → reviewer
```
