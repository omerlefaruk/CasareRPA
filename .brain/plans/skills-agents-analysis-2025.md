# Skills & Agents Analysis + Recommendations

**Date**: 2025-12-26
**Purpose**: Analyze official Anthropic standards, identify gaps, recommend additions

---

## Part 1: Official Anthropic Skills Structure

### Folder Format (Verified from anthropics/skills)

```
skills/
├── my-skill/
│   ├── SKILL.md          (REQUIRED - ALL CAPS filename)
│   ├── LICENSE.txt       (optional, for licensing)
│   ├── scripts/          (optional - executable code/black-box helpers)
│   ├── references/       (optional - detailed docs loaded as needed)
│   ├── examples/         (optional - usage examples)
│   ├── templates/        (optional - code/file templates)
│   └── forms.md          (optional - specific patterns, e.g., pdf/forms.md)
```

### Key Principles

1. **Progressive Disclosure**: SKILL.md = overview + quick start. Heavy details go in `references/`
2. **Black-Box Scripts**: `scripts/` contain helpers called directly, never read into context
3. **YAML Frontmatter**:
   ```yaml
   ---
   name: skill-name
   description: What it does + when to use it
   license: Optional (e.g., Proprietary, Apache-2.0)
   ---
   ```

### Official Skills Catalog (anthropics/skills)

| Skill | Purpose | Structure |
|-------|---------|-----------|
| **pdf** | PDF manipulation (text, tables, forms, create) | SKILL.md + forms.md + reference.md + scripts/ |
| **docx** | Word documents (create, edit, tracked changes) | SKILL.md + docx-js.md + ooxml.md + scripts/ |
| **pptx** | PowerPoint creation/editing | SKILL.md + html2pptx.md + ooxml/ + scripts/ |
| **xlsx** | Excel operations | SKILL.md + recalc.py |
| **mcp-builder** | MCP server development | SKILL.md + references/ (best practices, python, node, evaluation) |
| **webapp-testing** | Playwright testing for local webapps | SKILL.md + examples/ + scripts/ |
| **skill-creator** | Meta-skill for creating skills | SKILL.md + references/ + scripts/ |
| **algorithmic-art** | Generative art creation | SKILL.md + templates/ |
| **brand-guidelines** | Brand compliance | SKILL.md only (simple) |
| **canvas-design** | Canvas graphics | SKILL.md + canvas-fonts/ |
| **internal-comms** | Internal documentation | SKILL.md + examples/ |
| **theme-factory** | Theme generation | SKILL.md + themes/ + theme-showcase.pdf |

---

## Part 2: Current CasareRPA Skills Audit

### Current Skills (12 single-file .md)

| Skill | Description | Lines | Status |
|-------|-------------|-------|--------|
| `test-generator.md` | Generate pytest test suites | ~430 | **Good candidate for folder** |
| `code-reviewer.md` | Structured review output format | ~120 | Keep single-file |
| `commit-message-generator.md` | Generate conventional commits | ~80 | Keep single-file |
| `changelog-updater.md` | Update CHANGELOG.md | ~60 | Keep single-file |
| `workflow-validator.md` | Validate workflow schemas | ~150 | Consider folder |
| `node-template-generator.md` | Generate new nodes | ~200 | **Good candidate for folder** |
| `chain-tester.md` | Test agent chains | ~100 | Keep single-file |
| `dependency-updater.md` | Update dependencies | ~80 | Keep single-file |
| `import-fixer.md` | Fix unused imports | ~60 | Keep single-file |
| `brain-updater.md` | Update .brain/ context | ~100 | Keep single-file |
| `agent-invoker.md` | Invoke agents with context | ~80 | Keep single-file |

### Migration Candidates (Folder Structure)

**Priority 1 - High Value, Large Files:**

1. **test-generator** → `test-generator/SKILL.md` + `references/`
   - `references/node-tests.md` - Node testing patterns
   - `references/controller-tests.md` - Controller patterns
   - `references/domain-tests.md` - Domain entity patterns
   - `examples/` - Sample test files

2. **node-template-generator** → `node-template-generator/SKILL.md` + `templates/` + `references/`
   - `templates/browser_node.py` - Browser node template
   - `templates/desktop_node.py` - Desktop node template
   - `templates/data_node.py` - Data node template
   - `references/node-checklist.md` - Full checklist

3. **workflow-validator** → `workflow-validator/SKILL.md` + `schemas/`
   - `schemas/workflow-v1.json` - JSON schema
   - `schemas/workflow-v2.json` - Latest schema
   - `references/migration-guide.md` - Version migration

---

## Part 3: Skills We Should Add

### From Official Anthropic (Adapt for CasareRPA)

| Official Skill | CasareRPA Adaptation | Purpose |
|----------------|---------------------|---------|
| **mcp-builder** | `mcp-server/` | Create MCP servers for RPA integrations |
| **webapp-testing** | `playwright-testing/` | Test RPA workflows with Playwright |
| **skill-creator** | `skill-creator/` | Create custom CasareRPA skills |

### New Skills for CasareRPA

| Skill | Purpose | Structure |
|-------|---------|-----------|
| **rpa-patterns** | Common RPA patterns (retry, recovery, polling) | SKILL.md + examples/ |
| **node-debugging** | Debug node execution issues | SKILL.md + references/troubleshooting.md |
| **workflow-optimizer** | Optimize workflow performance | SKILL.md + references/bottlenecks.md |
| **selector-strategies** | CSS/XPath selector best practices | SKILL.md + examples/ |
| **error-recovery** | RPA error handling patterns | SKILL.md + examples/ |
| **migration-guide** | Import from UiPath/PowerAutomate | SKILL.md + references/mappings.md |

---

## Part 4: Current CasareRPA Agents Audit

### Current Agents (11)

| Agent | Description | Model | Structured Sections | "Use PROACTIVELY" |
|-------|-------------|-------|---------------------|------------------|
| **architect** | Implementation and system design | opus | Partial | ❌ No |
| **builder** | Code writing (KISS & DDD) | opus | Partial | ❌ No |
| **docs** | Documentation generation | - | Need to verify | ❌ No |
| **explore** | Fast codebase exploration | opus | Partial | ❌ No |
| **integrations** | External system integrations | opus | Partial | ❌ No |
| **quality** | Testing and performance | opus | Partial | ❌ No |
| **refactor** | Code cleanup and modernization | opus | Partial | ❌ No |
| **researcher** | Technical research and competitive analysis | opus | Partial | ❌ No |
| **reviewer** | Code review gate | - | Need to verify | ❌ No |
| **ui** | Qt/PySide6 UI development | - | Need to verify | ❌ No |

### Missing Structured Sections

**Real-world agent structure** (from 0xfurai's 100+ agents):

```yaml
---
name: react-expert
description: React development expert... Use PROACTIVELY for React refactoring...
model: claude-sonnet-4-20250514
---

## Focus Areas
- List of 5-10 key topics

## Approach
- List of 5-10 principles

## Quality Checklist
- List of 5-10 verification steps

## Output
- List of deliverables
```

---

## Part 5: Agents We Should Add

### High Priority Gaps

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **debugger** | Debug production issues, analyze logs | When investigating failures |
| **security** | Security audit, vulnerability scan | Before deployment |
| **performance** | Profiling, optimization analysis | When slow execution |
| **database** | Database operations, migrations | For data layer work |
| **devops** | CI/CD, deployment, infrastructure | For ops tasks |

### Agent Specializations (Domain-Specific)

| Agent | Domain | Use PROACTIVELY for... |
|-------|--------|----------------------|
| **browser-automation** | Playwright nodes | Browser node development, selector issues |
| **desktop-automation** | UIAutomation nodes | Windows desktop automation |
| **api-integration** | HTTP/API nodes | REST/GraphQL integrations |
| **data-processing** | Data nodes | ETL, transformation nodes |
| **workflow-design** | Workflow structure | Complex workflow layout |

---

## Part 6: Skills for Agents Assignment

### Current Agent → Skills Mapping

| Agent | Current Skills | Should Add |
|-------|----------------|------------|
| **architect** | - | mcp-server, rpa-patterns |
| **builder** | - | node-template-generator |
| **quality** | test-generator | playwright-testing, workflow-validator |
| **reviewer** | code-reviewer | security-audit (new) |
| **integrations** | - | mcp-server, api-patterns (new) |
| **refactor** | - | rpa-patterns |
| **researcher** | - | migration-guide |
| **explore** | - | (none - semantic search is native) |
| **ui** | - | qt-patterns (new) |
| **docs** | changelog-updater, brain-updater | - |

### New Skills for Specific Agents

| Agent | New Skill | Purpose |
|-------|-----------|---------|
| **quality** | `performance-testing/` | Load testing, stress testing patterns |
| **integrations** | `oauth-flows/` | OAuth 2.0 patterns for integrations |
| **ui** | `qt-patterns/` | Qt signal/slot, threading, widgets |
| **debugger** | `log-analysis/` | Parse and analyze RPA logs |
| **security** | `security-audit/` | Security checklist for RPA |

---

## Part 7: Implementation Plan

### Phase 1: Skills Migration (P0)

**Migrate to folder structure:**

1. **test-generator** (Priority 1)
   ```
   .claude/skills/test-generator/
   ├── SKILL.md          (overview + quick start)
   ├── references/
   │   ├── node-tests.md
   │   ├── controller-tests.md
   │   └── domain-tests.md
   └── examples/
       └── sample_test.py
   ```

2. **node-template-generator** (Priority 2)
   ```
   .claude/skills/node-template-generator/
   ├── SKILL.md
   ├── templates/
   │   ├── browser.py
   │   ├── desktop.py
   │   └── data.py
   └── references/
       └── node-checklist.md
   ```

3. **workflow-validator** (Priority 3)
   ```
   .claude/skills/workflow-validator/
   ├── SKILL.md
   ├── schemas/
   │   ├── workflow-v1.json
   │   └── workflow-v2.json
   └── references/
       └── migration.md
   ```

### Phase 2: New Skills (P1)

**Create new domain-specific skills:**

1. `rpa-patterns/` - Retry, recovery, polling patterns
2. `playwright-testing/` - Adapt from official webapp-testing
3. `mcp-server/` - Adapt from official mcp-builder
4. `selector-strategies/` - CSS/XPath best practices
5. `error-recovery/` - RPA error handling

### Phase 3: Agent Structure (P1)

**Add structured sections to all agents:**

```yaml
---
name: architect
description: Implementation and system design for nodes, executors, data contracts, cross-component features. Use PROACTIVELY for architectural decisions, impact analysis, and implementation planning.
model: opus
---

## Focus Areas
- DDD 2025 architecture patterns
- Node development and registration
- Data contracts and JSON schemas
- Cross-component coordination
- Impact analysis and roadmaps

## Approach
- Read relevant _index.md before grep/glob
- Create implementation plans before coding
- Follow domain purity rules
- Use typed events for communication
- Consider token optimization

## Quality Checklist
- Plan reviewed before implementation
- All external calls have error handling
- Type hints complete and accurate
- Tests written before code
- Documentation updated

## Output
- Implementation plan
- Code following DDD patterns
- Test suite
- Updated documentation
```

### Phase 4: New Agents (P2)

**Add missing specialist agents:**

1. **debugger** - Debug production issues
2. **security** - Security audits
3. **performance** - Profiling and optimization
4. **database** - Database operations

---

## Part 8: Token Efficiency Analysis

### Current Single-File Skills

```
test-generator.md:              ~430 lines = ~6,000 tokens (every time)
node-template-generator.md:     ~200 lines = ~3,000 tokens (every time)
workflow-validator.md:          ~150 lines = ~2,000 tokens (every time)
────────────────────────────────────────────────────────
Total:                          ~11,000 tokens per relevant session
```

### After Progressive Disclosure

```
test-generator/SKILL.md:        ~100 lines = ~1,500 tokens
node-template-generator/SKILL.md: ~80 lines = ~1,200 tokens
workflow-validator/SKILL.md:     ~60 lines = ~900 tokens
references/* (loaded only when needed): ~6,000 tokens
────────────────────────────────────────────────────────
Base load:                       ~3,600 tokens (67% reduction)
```

**Savings: ~67% reduction in base skill context load**

---

## Part 9: File Structure Comparison

### Before

```
.claude/
├── skills/
│   ├── test-generator.md
│   ├── code-reviewer.md
│   ├── node-template-generator.md
│   └── ... (9 more single files)
└── agents/
    ├── architect.md
    ├── builder.md
    └── ... (9 more single files)
```

### After

```
.claude/
├── skills/
│   ├── test-generator/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── node-tests.md
│   │   │   ├── controller-tests.md
│   │   │   └── domain-tests.md
│   │   └── examples/
│   ├── node-template-generator/
│   │   ├── SKILL.md
│   │   ├── templates/
│   │   └── references/
│   ├── workflow-validator/
│   │   ├── SKILL.md
│   │   ├── schemas/
│   │   └── references/
│   ├── rpa-patterns/           (NEW)
│   ├── playwright-testing/      (NEW - adapted)
│   ├── mcp-server/              (NEW - adapted)
│   ├── selector-strategies/     (NEW)
│   ├── error-recovery/          (NEW)
│   └── *.md                     (keep single files for simple skills)
└── agents/
    ├── architect.md             (updated with structured sections)
    ├── builder.md               (updated)
    ├── debugger.md              (NEW)
    ├── security.md              (NEW)
    ├── performance.md           (NEW)
    └── database.md              (NEW)
```

---

## Part 10: Quick Reference Tables

### Skills: Single vs Folder

| Criteria | Single File | Folder Structure |
|----------|-------------|------------------|
| **Size** | <100 lines | >100 lines |
| **Complexity** | Simple (one purpose) | Complex (multiple scenarios) |
| **Examples** | Embedded in SKILL.md | Separate `examples/` folder |
| **References** | All in one file | Progressive `references/` |
| **Scripts** | None | `scripts/` for black-box helpers |

### Agent Description Pattern

| Component | Format | Example |
|-----------|--------|---------|
| **name** | lowercase-hyphens | `browser-automation` |
| **description** | What it does + "Use PROACTIVELY for..." | "Browser automation expert. Use PROACTIVELY for Playwright node development..." |
| **model** | opus, sonnet, haiku | `opus` for architecture |
| **Focus Areas** | 5-10 bullet points | Key topics |
| **Approach** | 5-10 principles | How to work |
| **Quality Checklist** | 5-10 checks | Verification steps |
| **Output** | Deliverables list | What's produced |

---

## Next Steps

1. **Review this plan** - Approve/reject phases
2. **Start Phase 1** - Migrate test-generator to folder structure
3. **Test migration** - Verify skill still works
4. **Continue migration** - node-template-generator, workflow-validator
5. **Add new skills** - rpa-patterns, playwright-testing, etc.
6. **Update agents** - Add structured sections, "Use PROACTIVELY"
7. **Add new agents** - debugger, security, performance, database

---

## Sources

- [anthropics/skills - Official Repository](https://github.com/anthropics/skills)
- [Claude Code - Skills Documentation](https://code.claude.com/docs/en/skills)
- [0xfurai/claude-code-subagents - 100+ Agents](https://github.com/0xfurai/claude-code-subagents)
