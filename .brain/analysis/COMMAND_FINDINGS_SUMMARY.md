# Command Structure Findings - Executive Summary

## Quick Answer

CasareRPA uses a **sophisticated two-layer command system** designed for complex, multi-agent orchestration:

1. **User-facing layer** (`.claude/commands/`) - YAML + template variables
2. **Reference layer** (`agent-rules/commands/`) - Detailed flow + examples

Both coordinate the same **5-phase execution model** with parallel agent orchestration.

---

## Three Main Commands

| Command | Purpose | Required Args | Key Feature |
|---------|---------|---------------|------------|
| **`/implement-feature`** | New features, refactoring, optimization | None | Flexible modes (implement/refactor/optimize/extend) |
| **`/implement-node`** | Create automation nodes | `node_name` | 6 phases + registration step |
| **`/fix-feature`** | Fix bugs and issues | `description` | Smart bug type detection |

---

## The 5-Phase Pattern (Universal)

Every command follows this orchestration:

```
1. RESEARCH (parallel agents)     → explore, researcher
2. PLAN (architect)                → .brain/plans/{name}.md [USER GATE]
3. EXECUTE (parallel agents)       → builder, ui, integrations, refactor
4. VALIDATE (sequential loop)      → quality, reviewer (auto-loop on issues)
5. DOCS (documentation)            → docs agent
```

**Key insight**: Parallelism at phases 1 & 3, sequential validation at phase 4.

---

## File Structure

### Command Definitions (`.claude/commands/`)
```
implement-feature.md  ← YAML metadata + $ARGUMENTS template variables
implement-node.md     ← YAML metadata + $ARGUMENTS template variables
fix-feature.md        ← YAML metadata + $ARGUMENTS template variables
```

**Format**: YAML frontmatter defines arguments, Markdown body uses `$ARGUMENTS.param` substitution

### Detailed Guides (`agent-rules/commands/`)
```
implement-feature.md  ← 2,000+ word comprehensive guide with examples
implement-node.md     ← 2,500+ word guide with templates and registration
fix-feature.md        ← 2,000+ word guide with bug patterns and fixes
```

**Purpose**: Human-readable reference for agents and architects

### Agent Specifications (`.claude/agents/`)
10 specialized agents with distinct roles:
- **explore** (haiku) - Fast codebase search
- **researcher** (opus) - External research via MCP
- **architect** (opus) - System design and planning
- **builder** (opus) - Code implementation
- **refactor** (opus) - Code cleanup
- **ui** (opus) - Qt/PySide6 components
- **integrations** (opus) - API clients and services
- **quality** (opus) - Tests and performance
- **reviewer** (opus) - Code review gate
- **docs** (opus) - Documentation updates

### Standards Layer (`.claude/rules/`)
```
01-core.md               ← Workflow, imports, error handling
02-architecture.md       ← DDD patterns, events, aggregates
03-nodes.md             ← Node-specific patterns
04-ddd-events.md        ← Event definitions
ui/theme-rules.md       ← THEME constants, colors
ui/signal-slot-rules.md ← Qt decorators, connections
nodes/node-registration.md ← Registry pattern
```

---

## How Commands Work

### Phase 1: RESEARCH
```
Parallelism: YES (up to 3 agents)
Agents: explore (x1-2) + researcher (optional)

Task(explore, "Find patterns in $ARGUMENTS.scope/")
Task(explore, "Find test patterns")
Task(researcher, "Research best practices")  # Optional

Output: Pattern findings, dependencies
Gate: AUTO-PROCEED to PLAN
```

### Phase 2: PLAN
```
Parallelism: NO (sequential)
Agent: architect

Creates: .brain/plans/{feature-name}.md
├─ Files to create/modify
├─ Agent assignments
├─ Parallel opportunities
└─ Risks & mitigation

Gate: USER APPROVAL ("Plan ready. Approve?")
→ Required before EXECUTE
```

### Phase 3: EXECUTE
```
Parallelism: YES (2-5 agents)
Agents: Mode-dependent

/implement-feature modes:
├─ implement → builder + ui + integrations
├─ refactor → refactor only
├─ optimize → quality(perf) + refactor
└─ extend → builder + refactor

/implement-node modes:
├─ implement → builder + ui + quality
├─ extend → builder + quality
├─ refactor → refactor + quality
└─ clone → builder + ui + quality

/fix-feature:
└─ → builder + refactor

Code Rules Applied:
├─ THEME constants (not hardcoded colors)
├─ UnifiedHttpClient (not raw httpx)
├─ @Slot decorators (required on signal handlers)
├─ Typed domain events (not dicts)
├─ add_exec_input() (for exec ports)
├─ try/except + loguru (error handling)
└─ Type hints on all methods

Gate: AUTO-PROCEED to VALIDATE
```

### Phase 4: VALIDATE
```
Parallelism: NO (sequential loop)
Agents: quality → reviewer (loop)

quality (mode: test):
├─ Create test suite (if needed)
├─ Run pytest
└─ Cover SUCCESS, ERROR, EDGE_CASES

reviewer:
├─ Check error handling, type hints, patterns
├─ Output: APPROVED or ISSUES (file:line)
└─ Loop if ISSUES: fix → re-test → re-review

Gate: APPROVED by reviewer before DOCS
```

### Phase 5: DOCS
```
Parallelism: NO (sequential)
Agent: docs

Updates:
├─ _index.md files
├─ .brain/context/current.md
└─ Docstrings

Gate: AUTO-PROCEED to COMPLETION
```

---

## Parameters System

### YAML Metadata
```yaml
---
description: What the command does
arguments:
  - name: param_name
    description: What it does
    required: true|false
---
```

### Template Variables
Commands use `$ARGUMENTS.{param}` in templates:

```markdown
# /implement-feature presentation
# becomes:
Task(explore, "Find patterns in src/casare_rpa/$ARGUMENTS.scope/")
# becomes:
Task(explore, "Find patterns in src/casare_rpa/presentation/")
```

### Parameter Reference

| Command | Params | Type | Default | Example |
|---------|--------|------|---------|---------|
| implement-feature | scope | enum | none | presentation |
|  | mode | enum | implement | refactor, optimize, extend |
| implement-node | node_name | string | required | ClickElement |
|  | category | enum | optional | browser, integration |
|  | mode | enum | implement | extend, refactor, clone |
| fix-feature | type | enum | auto-detect | crash, output, ui, perf |
|  | description | string | required | "Node execution crashes" |

---

## Agent Coordination

### Parallel Execution Rule
"Launch up to **5 agents in parallel** when tasks are independent"

```python
# CORRECT - All parallel
Task(explore, "Find X")
Task(explore, "Find Y")
Task(researcher, "Research Z")
# All launch simultaneously

# WRONG - Sequential wastes time
Task(explore, "Find X") → wait
Task(explore, "Find Y") → wait
Task(researcher, "Research Z")
```

### When Agents Can Parallelize
1. Different scopes (explore domain + explore infrastructure)
2. Independent components (builder + ui, builder + integrations)
3. Performance analysis + refactoring (quality(perf) + refactor)

### Sequential Blocking Points
1. **PLAN gate**: User must approve planning document
2. **VALIDATE loop**: quality → reviewer → (fix if issues)
3. **DOCS phase**: Single docs agent

---

## Key Design Patterns

### Mode Router
Commands route to different agents based on mode parameter:

```
/implement-feature [mode]
├─ implement (default) → New feature workflow
├─ refactor → Code cleanup workflow
├─ optimize → Performance improvement workflow
└─ extend → Add to existing workflow

/implement-node [mode]
├─ implement (default) → Create new node
├─ extend → Add ports to existing
├─ refactor → Improve existing
└─ clone → Create variant

/fix-feature [type]
├─ crash → Exception/stack trace diagnosis
├─ output → Wrong data debugging
├─ ui → Display issue diagnosis
├─ perf → Performance profiling
├─ flaky → Test intermittency analysis
└─ (auto-detect if not specified)
```

### Planning Document Pattern
All PLAN phases create `.brain/plans/{name}.md` with standard structure:
```markdown
# Feature: Name
## Scope / Category
## Files to Create/Modify
## Agent Assignments
## Parallel Opportunities
## Risks & Mitigation
## Test Plan
```

### Agent Chain Pattern
```
Research agents → Architect → Execution agents → Validation loop → Docs
(parallel)      (sequential)  (parallel)        (sequential)    (sequential)
  ↑                             ↑                    ↑
  ├─ explore                    ├─ builder          ├─ quality
  ├─ researcher                 ├─ ui               └─ reviewer
  └─ (auto-proceed)             ├─ integrations         ↓
                                ├─ refactor        Loop if ISSUES
                                └─ (USER GATE      ↓
                                   to approve)    DOCS
```

---

## Code Quality Standards

All agents apply these **non-negotiable rules** during EXECUTE:

```python
# CORRECT ✓
color = THEME['bg_primary']
client = UnifiedHttpClient()
@Slot(str)
def on_signal(self, data): pass
bus.publish(NodeCompleted(node_id="x"))
node.add_exec_input()
try:
    result = risky()
except Exception as e:
    logger.error(f"Failed: {e}")

# WRONG ✗
color = "#1a1a2e"
response = httpx.get(url)
def on_signal(self): pass  # Missing @Slot
bus.publish({"type": "done"})
node.add_input_port("exec", EXEC_INPUT)
try:
    result = risky()
except:
    pass
```

---

## Real-World Example

### User Invocation
```bash
/implement-feature presentation
"Add workflow template browser panel"
```

### What Happens
```
1. RESEARCH (parallel)
   ├─ explore: Find existing panels, patterns
   ├─ explore: Find test patterns in tests/presentation/
   └─ researcher: Research UI patterns

2. PLAN (architect creates .brain/plans/workflow-template-browser.md)
   [USER GATE: User reviews and approves plan]

3. EXECUTE (parallel)
   ├─ ui: Create main TemplatePanel widget
   ├─ ui: Create dialog component
   └─ (refactor handles cleanup if mode=optimize)

4. VALIDATE (loop)
   ├─ quality: Create test suite
   ├─ reviewer: Checks code + patterns
   └─ (if ISSUES: fix → re-validate)

5. DOCS
   └─ docs: Update presentation/canvas/_index.md, context

OUTPUT:
✓ Files created: main_panel.py, dialog.py, test_*.py
✓ Tests passing: 25/25
✓ Review: APPROVED
```

---

## Strengths of This System

1. **Parallel Efficiency**: Up to 5 agents work simultaneously on independent tasks
2. **Quality Gates**: Mandatory user approval on plan, automated validation on code
3. **Flexibility**: Modes allow same command for different workflows (implement/refactor/optimize)
4. **Standards Enforcement**: Rules layer ensures consistent code quality
5. **Documentation**: Both technical (.claude/) and human-readable (agent-rules/)
6. **Scalability**: 10 specialized agents handle diverse tasks
7. **Traceability**: Planning documents in .brain/plans/ guide future changes
8. **Error Recovery**: Validation loop auto-fixes issues without user intervention

---

## Key Files to Remember

### Commands
- `.claude/commands/implement-feature.md` - Feature template
- `.claude/commands/implement-node.md` - Node template
- `.claude/commands/fix-feature.md` - Bug fix template
- `agent-rules/commands/*.md` - Detailed human guides

### Agents
- `.claude/agents/*.md` - 10 agent specifications

### Standards
- `.claude/rules/01-core.md` - Core rules
- `.claude/rules/02-architecture.md` - DDD patterns
- `.claude/rules/ui/theme-rules.md` - Theme usage
- `.claude/rules/ui/signal-slot-rules.md` - Qt patterns

### Output
- `.brain/plans/{name}.md` - Planning documents
- `.brain/decisions/*.md` - Decision trees
- `.brain/context/current.md` - Session state

---

## Recommendations

### For Understanding the System
1. Read `COMMAND_QUICK_REFERENCE.md` (2-min overview)
2. Read `COMMAND_ARCHITECTURE.md` (detailed system design)
3. Explore `.claude/commands/` for actual YAML format
4. Review `agent-rules/commands/` for workflow examples

### For Using the Commands
1. Check `CLAUDE.md` for quick invocation examples
2. Reference `agent-rules/commands/{command}.md` for detailed flow
3. Review `.brain/decisions/` for your specific task type
4. Follow `.claude/rules/` for code standards

### For Extending the System
1. Define new agents in `.claude/agents/{new-agent}.md`
2. Create command templates in `.claude/commands/{new-command}.md`
3. Add detailed guide in `agent-rules/commands/{new-command}.md`
4. Document standards in `.claude/rules/{topic}.md`

---

## Conclusion

CasareRPA's command system is a **well-architected multi-agent orchestration platform** that:

- Uses **5-phase pattern** for all operations (RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS)
- Coordinates **up to 5 agents in parallel** for efficiency
- Enforces **user approval gates** at planning stage
- Implements **automatic validation loops** for code quality
- Maintains **comprehensive documentation** at multiple levels
- Applies **consistent coding standards** across all code

This structure enables **rapid feature development** with **high quality assurance** through parallel agent coordination and automated validation.
