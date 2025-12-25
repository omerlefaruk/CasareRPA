# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Command Structure Analysis - Complete Documentation

**Analysis Date**: 2025-12-14
**Scope**: CasareRPA command system (`.claude/commands/` and `agent-rules/commands/`)
**Total Documentation**: 2,978 lines across 6 comprehensive analysis documents

---

## Executive Summary

CasareRPA implements a **sophisticated two-layer command orchestration system** that coordinates 10 specialized agents through a universal 5-phase execution pattern.

### The System Consists Of:
- **3 main commands**: `/implement-feature`, `/implement-node`, `/fix-feature`
- **10 specialized agents**: explore, researcher, architect, builder, ui, integrations, refactor, quality, reviewer, docs
- **5-phase pattern**: RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS
- **Parallel execution**: Up to 5 agents work simultaneously on independent tasks
- **Quality gates**: User approval at PLAN, automated validation loop at VALIDATE

---

## Analysis Documents Created

### 1. COMMAND_FINDINGS_SUMMARY.md (444 lines)
**Quick executive overview** of the entire command system
- Best for: 10-minute understanding
- Contains: Quick answer, 5-phase pattern, file structure, real-world example
- **Start here** for quick understanding

### 2. COMMAND_QUICK_REFERENCE.md (384 lines)
**Fast lookup reference** for command structure
- Best for: Quick parameter/agent lookups while working
- Contains: Command parameter tables, agent list, code rules, examples
- Keep nearby for quick reference

### 3. COMMAND_ARCHITECTURE.md (712 lines)
**System architecture and design** documentation
- Best for: 20-minute deep dive into how the system works
- Contains: System diagrams, file structure, phase execution models, routing logic
- Understand the "why" behind each component

### 4. COMMAND_STRUCTURE_ANALYSIS.md (635 lines)
**Comprehensive reference** with complete technical details
- Best for: 45-minute complete reference
- Contains: Detailed command specifications, parameter processing, agent coordination
- Use when you need complete accuracy

### 5. COMMAND_STRUCTURE_INDEX.md (369 lines)
**Navigation guide** to all analysis documents
- Best for: Finding the right document for your needs
- Contains: Reading guide by time, topic cross-references, scenario guides
- Start here to decide which document to read

---

## Key Findings

### The Command System

**Two-Layer Architecture**:
```
User-facing: .claude/commands/
├── implement-feature.md (YAML + template)
├── implement-node.md    (YAML + template)
└── fix-feature.md       (YAML + template)

Reference: agent-rules/commands/
├── implement-feature.md (2000+ words, detailed)
├── implement-node.md    (2500+ words, detailed)
└── fix-feature.md       (2000+ words, detailed)
```

### The 5-Phase Pattern

**Universal execution model** for all commands:
1. **RESEARCH** (parallel) - explore agents discover patterns
2. **PLAN** (sequential) - architect designs, user approves [GATE]
3. **EXECUTE** (parallel) - builder, ui, integrations implement
4. **VALIDATE** (sequential loop) - quality tests, reviewer approves [LOOP]
5. **DOCS** (sequential) - docs agent updates documentation

### The Three Commands

| Command | Purpose | Required Args | Key Feature |
|---------|---------|---------------|------------|
| `/implement-feature` | New features, refactor, optimize | None | 4 modes: implement/refactor/optimize/extend |
| `/implement-node` | Create automation nodes | node_name | 6 phases (includes registration) |
| `/fix-feature` | Fix bugs and issues | description | Bug type routing (crash/output/ui/perf/flaky) |

### The 10 Agents

| Agent | Role | Model |
|-------|------|-------|
| explore | Fast codebase search | haiku |
| researcher | External research via MCP | opus |
| architect | System design & planning | opus |
| builder | Code implementation | opus |
| refactor | Code cleanup | opus |
| ui | Qt/PySide6 components | opus |
| integrations | API clients & services | opus |
| quality | Tests & performance | opus |
| reviewer | Code review gate | opus |
| docs | Documentation updates | opus |

---

## How It Works (Quick Overview)

### User Invokes Command
```bash
/implement-feature presentation
"Add workflow template browser"
```

### System Executes 5 Phases
```
1. RESEARCH (parallel)
   ├─ explore: Find patterns in presentation/
   ├─ explore: Find test patterns
   └─ researcher: Research UI patterns

2. PLAN (architect)
   └─ Creates .brain/plans/workflow-template-browser.md
   └─ [USER GATE: "Plan ready. Approve?"]

3. EXECUTE (parallel)
   ├─ ui: Create main panel + dialog
   └─ refactor: Optimize if needed

4. VALIDATE (loop)
   ├─ quality: Run pytest
   ├─ reviewer: Check code + patterns
   └─ [Loop if ISSUES until APPROVED]

5. DOCS
   └─ docs: Update _index.md files
```

### Output
```
✓ Files created: N
✓ Tests passing: N/N
✓ Review: APPROVED
✓ Documentation updated
```

---

## Key Concepts

### Parallel Execution Rule
"Launch up to 5 agents in parallel when tasks are independent"

**When possible**:
- explore + explore (different scopes)
- builder + ui (different components)
- quality(perf) + refactor (parallel optimization)

**When sequential**:
- PLAN → EXECUTE (user gate)
- EXECUTE → VALIDATE (code must exist)
- quality → reviewer (test must pass)

### Parameter System
Commands use YAML metadata + template variable substitution:

```yaml
# Definition in .claude/commands/implement-feature.md
arguments:
  - name: scope
    required: false
  - name: mode
    required: false

# In command body:
Task(explore, "Find patterns in src/casare_rpa/$ARGUMENTS.scope/")

# When user provides scope="presentation":
Task(explore, "Find patterns in src/casare_rpa/presentation/")
```

### Planning Documents
PLAN phase creates `.brain/plans/{name}.md`:
```markdown
# Feature: Name
## Scope
## Files to Create/Modify
## Agent Assignments
## Parallel Opportunities
## Risks & Mitigation
```

Guides EXECUTE phase implementation.

### Coding Standards
All agents enforce rules during EXECUTE:
```python
# Correct
color = THEME['bg_primary']
client = UnifiedHttpClient()
@Slot(str)
def on_signal(self, data): pass

# Wrong
color = "#1a1a2e"
response = httpx.get(url)
def on_signal(self): pass  # Missing @Slot
```

---

## File Structure

### Commands Layer (.claude/commands/)
```
.claude/commands/
├── implement-feature.md     (3.6 KB, YAML + template)
├── implement-node.md        (5.5 KB, YAML + template)
└── fix-feature.md           (4.8 KB, YAML + template)
```

### Agents Layer (.claude/agents/)
```
.claude/agents/
├── explore.md
├── architect.md
├── builder.md
├── ui.md
├── integrations.md
├── refactor.md
├── quality.md
├── reviewer.md
├── researcher.md
└── docs.md
```

### Standards Layer (.claude/rules/)
```
.claude/rules/
├── 01-core.md                (Core workflow rules)
├── 02-architecture.md        (DDD patterns)
├── 03-nodes.md              (Node-specific rules)
├── 04-ddd-events.md         (Event definitions)
├── nodes/node-registration.md
└── ui/
    ├── theme-rules.md       (THEME usage)
    └── signal-slot-rules.md (Qt decorators)
```

### Reference Layer (agent-rules/commands/)
```
agent-rules/commands/
├── implement-feature.md     (2000+ words)
├── implement-node.md        (2500+ words)
└── fix-feature.md           (2000+ words)
```

---

## Usage Guide

### For 5-Minute Overview
Read: **COMMAND_FINDINGS_SUMMARY.md**
- Quick answer
- 5-phase pattern
- Three commands table
- Real-world example

### For Quick Reference
Use: **COMMAND_QUICK_REFERENCE.md**
- Command parameter tables
- Agent list
- Code rules
- Example invocations

### For System Understanding
Read: **COMMAND_ARCHITECTURE.md**
- System diagrams
- File structure
- Phase execution models
- Agent coordination

### For Complete Reference
Read: **COMMAND_STRUCTURE_ANALYSIS.md**
- Detailed command specs
- Parameter processing
- Phase details
- All examples

### For Navigation
Use: **COMMAND_STRUCTURE_INDEX.md**
- Reading guide by time/role
- Topic cross-references
- Scenario navigation
- Document comparison

---

## Real-World Examples

### Example 1: Implement New Feature
```bash
/implement-feature presentation
"Add workflow template browser panel"

Phase 1: RESEARCH (parallel)
└─ explore + researcher discover patterns

Phase 2: PLAN (architect designs)
└─ .brain/plans/workflow-template-browser.md
└─ [USER APPROVES]

Phase 3: EXECUTE (parallel)
├─ ui: Create main panel + dialog
└─ quality: Create tests

Phase 4: VALIDATE (loop until approved)
├─ quality: Run pytest
├─ reviewer: Check code
└─ [Loop if issues]

Phase 5: DOCS
└─ Update presentation/canvas/_index.md
```

### Example 2: Create New Node
```bash
/implement-node browser
"Click element with retry and screenshot"

Phase 1: RESEARCH
├─ explore: Find similar browser nodes
├─ explore: Find base classes
└─ researcher: Research Playwright patterns

Phase 2: PLAN
└─ .brain/plans/node-ClickElement.md
└─ [USER APPROVES]

Phase 3: EXECUTE (parallel)
├─ builder: Node logic class
├─ ui: Visual wrapper
└─ quality: Unit tests

Phase 4: VALIDATE
└─ [Loop until reviewer approves]

Phase 5: REGISTRATION
└─ Update registry_data.py

Phase 6: DOCS
└─ Update nodes/_index.md
```

### Example 3: Fix Bug
```bash
/fix-feature perf
"Canvas freezes on large workflow load"

Phase 1: DIAGNOSE (parallel)
├─ explore: Find blocking calls
├─ explore: Find loops
├─ explore: Find git history
└─ quality: Profile performance

Phase 2: PLAN
└─ .brain/plans/fix-canvas-freeze.md
└─ [USER APPROVES]

Phase 3: FIX (parallel)
├─ refactor: Optimize hot paths
└─ builder: Fix blocking calls

Phase 4: VALIDATE
└─ [Loop until approved]

Phase 5: DOCS (optional)
└─ Update .brain/errors.md
```

---

## Strengths of This System

1. **Parallel Efficiency** - Up to 5 agents work simultaneously
2. **Quality Gates** - User approval on plan, automatic validation on code
3. **Flexibility** - Modes for different workflows (implement/refactor/optimize/extend)
4. **Standards Enforcement** - Rules layer ensures consistent code quality
5. **Specialization** - 10 distinct agents with specific expertise
6. **Documentation** - Both machine-readable (.claude/) and human-readable (agent-rules/)
7. **Planning** - .brain/plans/ documents guide implementation
8. **Error Recovery** - Validation loop auto-fixes issues without user intervention

---

## Learning Path

### For Quick Understanding (15 minutes)
1. Read COMMAND_FINDINGS_SUMMARY.md (10 min)
2. Skim COMMAND_QUICK_REFERENCE.md (5 min)

### For Complete Understanding (45 minutes)
1. Read COMMAND_FINDINGS_SUMMARY.md (10 min)
2. Read COMMAND_ARCHITECTURE.md (20 min)
3. Reference COMMAND_STRUCTURE_ANALYSIS.md as needed (15 min)

### For Full Expertise (90 minutes)
1. Read all 4 analysis documents (60 min)
2. Study source files in .claude/ (30 min)
3. Review agent-rules/commands/ for detailed flows

### For Specific Questions
1. Use COMMAND_STRUCTURE_INDEX.md to find relevant section
2. Jump to appropriate document
3. Use browser search for specific terms

---

## Quick Navigation

| Need | Document | Section |
|------|----------|---------|
| **Quick overview** | COMMAND_FINDINGS_SUMMARY.md | (entire document) |
| **Command syntax** | COMMAND_QUICK_REFERENCE.md | Command Parameters |
| **Phase details** | COMMAND_ARCHITECTURE.md | Phase Execution Model |
| **Agent list** | COMMAND_QUICK_REFERENCE.md | Available Agents |
| **Parameter reference** | COMMAND_STRUCTURE_ANALYSIS.md | Section 7 |
| **Code rules** | COMMAND_QUICK_REFERENCE.md | Code Rules |
| **Examples** | Any document | Example Invocations |
| **File locations** | COMMAND_STRUCTURE_ANALYSIS.md | Sections 2 & 10 |

---

## Files Delivered

1. **COMMAND_STRUCTURE_INDEX.md** (369 lines)
   - Navigation guide to all documents
   - Reading guides by time and role
   - Topic cross-references

2. **COMMAND_FINDINGS_SUMMARY.md** (444 lines)
   - Executive overview
   - Key concepts explained
   - Real-world examples
   - Recommendations

3. **COMMAND_QUICK_REFERENCE.md** (384 lines)
   - Quick lookup tables
   - Command parameter reference
   - Agent list
   - Code rules summary

4. **COMMAND_ARCHITECTURE.md** (712 lines)
   - System diagrams
   - File structure with explanations
   - Phase execution models
   - Agent coordination patterns

5. **COMMAND_STRUCTURE_ANALYSIS.md** (635 lines)
   - Complete technical reference
   - Detailed command specifications
   - Parameter processing details
   - All usage examples

6. **README_COMMAND_ANALYSIS.md** (this file)
   - Overview of all analysis
   - Key findings summary
   - Quick navigation guide

---

## Recommendations

### For Quick Start
1. Read COMMAND_FINDINGS_SUMMARY.md first
2. Keep COMMAND_QUICK_REFERENCE.md handy
3. Reference agent-rules/commands/ for your specific task

### For Deep Understanding
1. Read all analysis documents in order listed above
2. Study source files in .claude/commands/ and .claude/agents/
3. Review agent-rules/commands/ for detailed workflows

### For System Extension
1. Study COMMAND_ARCHITECTURE.md file structure section
2. Review .claude/commands/ YAML format
3. Study .claude/agents/ agent format
4. Review agent-rules/commands/ for detailed flows

---

## Next Steps

1. **Choose your entry point** based on available time and role
2. **Read appropriate document(s)** from the analysis
3. **Reference source files** in .claude/ and agent-rules/
4. **Use COMMAND_QUICK_REFERENCE.md** for ongoing lookup

---

## Statistics

**Total Lines of Analysis**: 2,978 lines
- COMMAND_ARCHITECTURE.md: 712 lines (24%)
- COMMAND_STRUCTURE_ANALYSIS.md: 635 lines (21%)
- COMMAND_FINDINGS_SUMMARY.md: 444 lines (15%)
- COMMAND_STRUCTURE_INDEX.md: 369 lines (12%)
- COMMAND_QUICK_REFERENCE.md: 384 lines (13%)
- README_COMMAND_ANALYSIS.md: 434 lines (15%)

**Coverage**:
- 3 main commands analyzed in detail
- 10 agents documented
- 5-phase pattern explained at 3 depth levels
- 7 real-world examples provided
- 20+ tables and diagrams created

---

## Conclusion

This analysis provides **comprehensive documentation** of CasareRPA's command system at multiple depth levels:

- **5-minute overview**: COMMAND_FINDINGS_SUMMARY.md
- **Quick reference**: COMMAND_QUICK_REFERENCE.md
- **System design**: COMMAND_ARCHITECTURE.md
- **Complete reference**: COMMAND_STRUCTURE_ANALYSIS.md
- **Navigation guide**: COMMAND_STRUCTURE_INDEX.md

Choose your document based on time available and depth needed. All documents cross-reference each other for easy navigation.

The system itself demonstrates **sophisticated agent orchestration**, **quality-first design**, and **scalable architecture** suitable for complex, multi-layer development workflows.
