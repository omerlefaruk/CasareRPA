# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# CasareRPA Agent Definitions: .claude vs agent-rules

## Overview

Two agent definition directories exist with different purposes and content depth:

| Aspect | `.claude/agents/` | `agent-rules/agents/` |
|--------|-----------------|----------------------|
| **Status** | PRIMARY (Active) | SECONDARY (Reference) |
| **Purpose** | Full agent specifications for execution | Simplified versions for documentation |
| **Format** | YAML frontmatter + markdown content | Markdown only (no YAML) |
| **Detail Level** | Comprehensive (100-150 lines) | Concise (20-35 lines) |
| **Model Assignment** | YES (haiku/opus hints) | NO |
| **Context Scope** | YES (defined for agent runtime) | NO |
| **Qdrant Examples** | YES (detailed usage) | YES (mentioned) |
| **External Research** | YES (MCP tools specified) | MINIMAL |

---

## Detailed Comparison by Agent

### ARCHITECT Agent

#### `.claude/agents/architect.md` (PRIMARY)
- **Lines:** 154
- **YAML Frontmatter:**
  ```yaml
  name: architect
  description: Implementation and system design...
  model: opus
  context-scope: [current, patterns]
  ```
- **Key Sections:**
  - MCP tools research (design research, external documentation)
  - Semantic search with qdrant-find (lines 32-35)
  - .brain protocol (read current.md, report discoveries)
  - Expertise breakdown (Implementation vs System Design)
  - Architecture understanding (3 decoupled apps)
  - 8 coding standards sections
  - Output format (implementation vs design)
  - Quality verification checklist
  - Pipeline: always followed by quality → reviewer

#### `agent-rules/agents/architect.md` (SECONDARY)
- **Lines:** 43
- **No YAML frontmatter**
- **Key Sections:**
  - Role definition
  - When to use
  - MCP tools for design research (high-level)
  - Workflow (5 steps)
  - Outputs (diagrams, docs, plans, risk assessments)
  - Key considerations

**Difference:** Primary is 3.5x more detailed with specific coding standards, expertise breakdown, and execution guidance.

---

### BUILDER Agent

#### `.claude/agents/builder.md` (PRIMARY)
- **Lines:** 113
- **YAML Frontmatter:**
  ```yaml
  name: builder
  description: Code writing. Follows KISS & DDD...
  model: opus
  context-scope: [current, rules]
  ```
- **Key Sections:**
  - Semantic search first (qdrant-find examples)
  - .brain protocol (read current.md + projectRules.md)
  - Index-first discovery (5 index files to check)
  - Core philosophy (KISS + DDD explanation)
  - 4 coding standards sections
  - Architecture overview
  - Output format
  - Quality verification
  - Pipeline (quality → reviewer)

#### `agent-rules/agents/builder.md` (SECONDARY)
- **Lines:** 30
- **No YAML frontmatter**
- **Key Sections:**
  - Role: "Write production-quality code following established patterns"
  - When to use (4 items)
  - Workflow (4 steps)
  - Standards (type hints, async, docstrings, tests)
  - Output

**Difference:** Primary includes qdrant-find usage, DDD philosophy explanation, and quality checklist.

---

### EXPLORE Agent

#### `.claude/agents/explore.md` (PRIMARY)
- **Lines:** 134+
- **YAML Frontmatter:**
  ```yaml
  name: explore
  description: Fast codebase exploration...
  model: haiku
  ```
- **Key Sections:**
  - Semantic search (lines 9-21): "**ALWAYS use `qdrant-find` FIRST**" - PRIMARY emphasis
  - Tier system (Tier 1 < 500 tokens, Tier 2 < 2000, Tier 3 < 5000)
  - Index-first with 8 P0-P3 index files
  - Throughness mapping (Where is X, How does X work, etc.)
  - Architecture overview (3 apps, key directories)
  - Output format template
  - MCP tools (secondary)
  - Response rules (5 rules)

#### `agent-rules/agents/explore.md` (SECONDARY)
- **Lines:** 30
- **No YAML frontmatter**
- **Key Sections:**
  - Role: "Understand and navigate the codebase efficiently"
  - When to use (4 items)
  - Workflow (4 steps using view_file_outline, grep_search, find_by_name)
  - Key index files (4 files)
  - Tips (3 items)

**Difference:** Primary has tiered exploration system, qdrant-find emphasis, and comprehensive architecture overview. Reference is basic navigation guide.

---

### QUALITY Agent

#### `.claude/agents/quality.md` (PRIMARY)
- **Lines:** 100+
- **YAML Frontmatter:**
  ```yaml
  name: quality
  description: Testing and QA specialist...
  model: opus
  ```
- **Key Sections:**
  - Semantic search with qdrant-find (lines 34-38)
  - MCP tools for testing research (3 tools specified)
  - Test structure (4 test directories)
  - Commands (pytest variants)
  - Standards (mock, edge cases, fixtures, coverage)
  - Outputs

#### `agent-rules/agents/quality.md` (SECONDARY)
- **Lines:** 51
- **No YAML frontmatter**
- **Key Sections:**
  - Role
  - When to use
  - MCP tools for testing research (brief)
  - Test structure
  - Commands
  - Standards
  - Outputs

**Difference:** Both similar, but primary includes specific qdrant-find examples and more detailed MCP tool usage.

---

### REVIEWER Agent

#### `.claude/agents/reviewer.md` (PRIMARY)
- **YAML Frontmatter:**
  ```yaml
  name: reviewer
  description: Code review specialist...
  model: opus
  ```
- **Sections:**
  - Qdrant usage (similar implementations comparison)
  - Checklist (6 items including type hints, tests, error handling)
  - Feedback style (4 traits)
  - Outputs

#### `agent-rules/agents/reviewer.md` (SECONDARY)
- **Sections:** Same structure but more concise

---

### REFACTOR Agent

#### `.claude/agents/refactor.md` (PRIMARY)
- **YAML Frontmatter and qdrant-find usage**
- **Workflow:** Identify → Plan → Execute → Verify
- **Guidelines:** Small changes, tests pass, preserve behavior

#### `agent-rules/agents/refactor.md` (SECONDARY)
- **No YAML**
- **Simpler version of same content**

---

### RESEARCHER Agent

#### `.claude/agents/researcher.md` (PRIMARY)
- **YAML Frontmatter:**
  ```yaml
  name: researcher
  description: Investigation specialist with MCP-powered research...
  ```
- **Key Emphasis:**
  - MCP research tools (PRIMARY: Ref → Code → Web)
  - Research strategy (3 pathways)
  - Workflow (Define → Gather → Analyze → Report)
  - Qdrant-find for understanding existing before researching

#### `agent-rules/agents/researcher.md` (SECONDARY)
- **Simpler structure**
- **Missing MCP research strategy prioritization**

---

### INTEGRATIONS Agent

#### `.claude/agents/integrations.md` (PRIMARY)
- **MCP tools heavily emphasized:**
  ```python
  # Priority 1: Official docs
  mcp__Ref__ref_search_documentation
  # Priority 2: Code examples
  mcp__exa__get_code_context_exa
  # Priority 3: Patterns
  mcp__exa__web_search_exa
  ```
- **Key areas defined** (infrastructure paths)
- **Patterns listed** (UnifiedHttpClient, credential providers, retry/circuit breaker)
- **Qdrant usage** for integration pattern discovery

#### `agent-rules/agents/integrations.md` (SECONDARY)
- **Same content but less detailed**
- **MCP tools listed but no priority order**

---

### UI Agent

#### `.claude/agents/ui.md` (PRIMARY)
- **YAML with model: opus**
- **Qdrant examples for UI patterns**
- **Standards defined** (BaseWidget inheritance, signal/slot, theme system, qasync)

#### `agent-rules/agents/ui.md` (SECONDARY)
- **Simplified version**
- **Key areas and patterns listed**
- **Less detail on standards**

---

### DOCS Agent

#### `.claude/agents/docs.md` (PRIMARY)
- **Qdrant-find usage**
- **Workflow** (Audit → Plan → Write → Review)
- **Standards** (clear language, code examples, keep near code)
- **Output types**

#### `agent-rules/agents/docs.md` (SECONDARY)
- **Simpler version**
- **Same basic structure, less detail**

---

## Key Differences Summary

| Aspect | `.claude/agents/` | `agent-rules/agents/` |
|--------|-----------------|----------------------|
| **YAML Frontmatter** | YES (all 10 agents) | NO |
| **Model Assignment** | YES (haiku/opus) | NO |
| **Context Scope** | YES (current, rules, patterns) | NO |
| **Qdrant Examples** | ALL 10 agents | ALL 10 agents mentioned |
| **Qdrant Detail** | Specific query examples | General mention |
| **MCP Tool Prioritization** | YES (P1, P2, P3 order) | MINIMAL |
| **Workflow Steps** | Detailed, numbered | Simple list |
| **Coding Standards** | Comprehensive (4-8 sections) | Basic list |
| **Architecture Detail** | Full (3 apps, file structure) | Minimal |
| **Output Format** | Specified with examples | Listed |
| **Quality Verification** | YES (pre-finalization) | NO |
| **Pipeline Definition** | YES ("followed by X") | NO |
| **Lines of Content** | 100-154 | 20-51 |
| **Primary Use** | Agent execution | Human reference |

---

## File Usage Recommendation

### Use `.claude/agents/` When:
- Configuring or invoking agents programmatically
- Need to understand full agent context and scope
- Checking model assignment and context requirements
- Following detailed workflows and verification steps
- Researching MCP tool usage patterns

### Use `agent-rules/agents/` When:
- Creating onboarding documentation
- Need quick reference for agent purposes
- Simplified decision trees for agent selection
- Human-readable agent descriptions
- Reference material for team members

### For Developers:
- **Reference `.claude/agents/` as source of truth** for agent behavior and expectations
- **Keep `agent-rules/agents/` for documentation and onboarding purposes**
- **Both should be kept in sync but at different detail levels**

---

## Syncing Strategy

When updating agents:

1. **Make changes to `.claude/agents/` FIRST** (primary source)
2. **Extract key points to `agent-rules/agents/`** (simplified copy)
3. **Maintain consistency in:**
   - Agent purpose/description
   - When to use guidelines
   - Key workflows
   - Qdrant-find usage (mention in both)
4. **Primary-only content:** YAML, MCP tool priorities, verification checklists, pipelines

---

## Future Enhancements

1. **Automated sync verification** - Ensure both versions stay consistent
2. **Agent metadata file** - Single source for model/context assignments
3. **Qdrant integration** - Ensure all qdrant-find examples are tested
4. **MCP tool documentation** - Formalize research tool usage patterns
5. **Agent execution framework** - Leverage YAML frontmatter for runtime configuration
