# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# CasareRPA Commands - Quick Reference

## Three Main Commands

| Command | Use For | Required Args |
|---------|---------|---------------|
| `/implement-feature` | New features, refactor, optimize | None (optional: scope, mode) |
| `/implement-node` | Create automation nodes | node_name (optional: category, mode) |
| `/fix-feature` | Fix bugs, crashes, performance | description (optional: type) |

---

## Command Parameters

### /implement-feature
```
Scope:  domain | application | infrastructure | presentation | nodes
Mode:   implement (default) | refactor | optimize | extend
Example: /implement-feature presentation
         "Add workflow template browser"
```

### /implement-node
```
node_name (required): e.g., "ClickElement", "SendSlackMessage"
category: browser | desktop | data | integration | system | flow | ai
mode:     implement (default) | extend | refactor | clone
Example: /implement-node integration
         category: integration
         "Send Slack notification"
```

### /fix-feature
```
type: crash | output | ui | perf | flaky | (leave empty for auto-detect)
description (required): Description of the bug
Example: /fix-feature perf
         "Canvas freezes when loading large workflow"
```

---

## 5-Phase Execution Pattern

### Phase 1: RESEARCH
**Agents**: explore (1-3) + researcher (optional)
**Parallelism**: YES
**Gate**: Auto-proceed

```
Task(explore, "Find patterns in {scope}/")
Task(explore, "Find test patterns")
Task(researcher, "Research best practices")  # Optional
```

### Phase 2: PLAN
**Agent**: architect
**Parallelism**: NO
**Gate**: USER APPROVAL REQUIRED ("Plan ready. Approve?")

```
Output: .brain/plans/{name}.md
├─ Scope
├─ Files to create/modify
├─ Agent assignments
└─ Risks & mitigation
```

### Phase 3: EXECUTE
**Agents**: Depends on mode (2-5 agents)
**Parallelism**: YES
**Gate**: Auto-proceed (no user approval)

**For /implement-feature:**
```
implement: builder + ui + integrations
refactor:  refactor only
optimize:  quality(perf) + refactor
extend:    builder + refactor
```

**For /implement-node:**
```
implement: builder + ui + quality
extend:    builder + quality
refactor:  refactor + quality
clone:     builder + ui + quality
```

**For /fix-feature:**
```
fix: builder + refactor
```

### Phase 4: VALIDATE
**Agents**: quality → reviewer (loop)
**Parallelism**: NO (sequential loop)
**Gate**: Tests pass + Review approved

```
quality (mode: test)  → run pytest
reviewer              → APPROVED or ISSUES

Loop: If ISSUES → fix → re-validate
```

### Phase 5: DOCS
**Agent**: docs
**Parallelism**: NO
**Gate**: Auto-proceed

```
Update: _index.md files
        .brain/context/current.md
        docstrings
```

---

## Available Agents

| Agent | Use For | Model |
|-------|---------|-------|
| **explore** | Find patterns, code search | haiku |
| **researcher** | External research, APIs, docs | opus |
| **architect** | System design, planning | opus |
| **builder** | Write code, DDD logic | opus |
| **refactor** | Code cleanup, restructure | opus |
| **ui** | PySide6/Qt widgets, panels | opus |
| **integrations** | API clients, external services | opus |
| **quality** | Tests, performance profiling | opus |
| **reviewer** | Code review gate | opus |
| **docs** | Documentation updates | opus |

---

## Execution Summary by Command

### /implement-feature Flow
```
explore(×2) + researcher
    ↓
architect [USER GATE]
    ↓
builder + ui + integrations (parallel)
    ↓
quality + reviewer (loop)
    ↓
docs
```

### /implement-node Flow
```
explore(×2) + researcher(optional)
    ↓
architect [USER GATE]
    ↓
builder + ui + quality (parallel)
    ↓
reviewer (loop)
    ↓
registration
    ↓
docs
```

### /fix-feature Flow
```
explore(×3-5) + researcher(optional)
    ↓
architect [USER GATE]
    ↓
builder + refactor (parallel)
    ↓
quality + reviewer (loop)
    ↓
docs (optional)
```

---

## Parallel Execution Rules

**CRITICAL**: "Launch up to 5 agents in parallel when tasks are independent"

### When Agents Can Parallel
1. Same phase, different scopes (explore + explore)
2. Independent components (builder + ui in EXECUTE)
3. Performance profiling + refactoring (quality(perf) + refactor)

### When Agents Must Sequence
1. After PLAN (must wait for user approval)
2. During VALIDATE (quality → reviewer → loop)
3. In DOCS (single docs agent)

---

## Task Syntax

All agents receive tasks like:
```
Task(subagent_type="explore",
     prompt="Find patterns in src/casare_rpa/presentation/")

Task(subagent_type="builder",
     prompt="Create entity in domain/entities/my_entity.py...")

Task(subagent_type="quality",
     prompt="mode=test\nRun pytest tests/nodes/ -v")
```

---

## Code Rules (All Agents Follow)

| Rule | Correct | Wrong |
|------|---------|-------|
| Colors | `THEME['bg_primary']` | `"#1a1a2e"` |
| HTTP | `UnifiedHttpClient` | `httpx.get()` |
| Slots | `@Slot(str)` | Missing decorator |
| Connections | `functools.partial(fn, x)` | `lambda: fn(x)` |
| Events | `NodeCompleted(id="x")` | `{"type": "done"}` |
| Exec Ports | `add_exec_input()` | `add_input_port("exec")` |
| Errors | `try/except` + loguru | Silent `pass` |

---

## Planning Documents

After PLAN phase, agents create:

```
.brain/plans/
├── {feature-name}.md          # For /implement-feature
├── node-{node-name}.md        # For /implement-node
└── fix-{issue}.md             # For /fix-feature
```

**Structure**:
```markdown
# [Feature|Node|Fix]: {Name}

## Scope / Category
description

## Files to Create/Modify
- path/to/file.py - Purpose

## Agent Assignments
- builder: domain logic
- ui: panels/widgets
- integrations: API clients

## Parallel Opportunities
- Phase 1: builder + ui (independent)

## Risks
- Risk description - Mitigation
```

---

## Key Files

### Command Definitions
- `.claude/commands/implement-feature.md` - Template with YAML metadata
- `.claude/commands/implement-node.md` - Template with YAML metadata
- `.claude/commands/fix-feature.md` - Template with YAML metadata
- `agent-rules/commands/*.md` - Detailed human-readable guides

### Agent Specifications
- `.claude/agents/{agent-name}.md` - Individual agent prompts/behavior

### Project Standards
- `.claude/rules/01-core.md` - Workflow and standards
- `.claude/rules/02-architecture.md` - DDD patterns
- `.claude/rules/03-nodes.md` - Node development
- `.claude/rules/ui/signal-slot-rules.md` - Signal/slot patterns
- `.claude/rules/ui/theme-rules.md` - Theme usage rules

---

## Decision Trees (Reference)

For detailed step-by-step guidance:
- `.brain/decisions/add-feature.md` - Feature implementation layers
- `.brain/decisions/add-node.md` - Node creation workflow
- `.brain/decisions/fix-bug.md` - Debugging strategy

---

## Mode Reference

### Feature Modes
| Mode | Agents | When to Use |
|------|--------|------------|
| implement | builder + ui + integrations | New feature from scratch |
| refactor | refactor | Cleanup existing code |
| optimize | quality(perf) + refactor | Performance improvement |
| extend | builder + refactor | Add to existing feature |

### Node Modes
| Mode | Agents | When to Use |
|------|--------|------------|
| implement | builder + ui + quality | New node from scratch |
| extend | builder + quality | Add ports/properties |
| refactor | refactor + quality | Improve node code |
| clone | builder + ui + quality | Create variation |

---

## Example Invocations

### New Feature (Full Stack)
```bash
/implement-feature
"Add OAuth login with social providers"
# Scope: cross-cutting (all layers)
# Mode: implement (default)
```

### Scoped Feature
```bash
/implement-feature infrastructure
"Add Redis caching layer"
# Scope: infrastructure (APIs, persistence)
```

### New Node
```bash
/implement-node browser
"Click with retry and screenshot"
# Mode: implement (default)
```

### Bug Fix
```bash
/fix-feature perf
"Canvas freezes on 500-node workflow load"
# Type: perf (auto-detects from prompt)
```

---

## Gates & Approvals

| Phase | Type | Who Approves | Action |
|-------|------|--------------|--------|
| PLAN | User | You | "Plan ready. Approve?" → YES/NO |
| VALIDATE | Automated | Reviewer agent | If ISSUES found, loops back |
| EXECUTE | Auto | None | Proceeds if PLAN approved |

---

## Troubleshooting Commands

### If plan is wrong
Reject and agent re-plans with feedback

### If code has issues
Reviewer provides ISSUES list
Agent fixes → re-validates automatically

### If tests fail
Quality agent re-runs tests
Loop continues until all pass

### If agent gets stuck
- Check `.brain/context/current.md` for state
- Provide more specific prompt details
- Reference specific patterns in `.brain/systemPatterns.md`

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `COMMAND_STRUCTURE_ANALYSIS.md` | Full command architecture |
| `agent-rules/commands/*.md` | Detailed command flows + examples |
| `.brain/systemPatterns.md` | Existing implementation patterns |
| `.brain/projectRules.md` | Full coding standards |
| `CLAUDE.md` | Quick commands + search strategy |
