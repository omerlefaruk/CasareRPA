# Subagent Expansion Plan

## Current Status ✅

### Implemented Subagents (16)
| Subagent | Model | Phase | Status |
|:---------|:------|:------|:-------|
| `@node-creator` | Pro | 1 | ✅ Done |
| `@error-doctor` | Flash | 1 | ✅ Done |
| `@ui-specialist` | Flash | 1 | ✅ Done |
| `@code-reviewer` | Pro | 1 | ✅ Done |
| `@test-generator` | Flash | 1 | ✅ Done |
| `@architect` | Pro | 1 | ✅ Done |
| `@integrations` | Flash | 1 | ✅ Done |
| `@explorer` | Flash | 2 | ✅ Done |
| `@refactor` | Pro | 2 | ✅ Done |
| `@docs-writer` | Flash | 2 | ✅ Done |
| `@performance` | Flash | 2 | ✅ Done |
| `@workflow-expert` | Pro | 3 | ✅ Done |
| `@security-auditor` | Pro | 3 | ✅ Done |
| `@database` | Flash | 3 | ✅ Done |
| `@ci-cd` | Flash | 4 | ✅ Done |
| `@playwright` | Flash | 4 | ✅ Done |

---

## Phase 2: Essential Additions ✅ COMPLETE

### 1. `@explorer` - Codebase Navigator ✅
**Purpose:** Quickly understand and navigate the CasareRPA codebase
**Model:** Flash (fast navigation)
**Tools:** `read`, `grep`
**Use Cases:**
- "Where is the workflow execution implemented?"
- "Find all nodes that use OAuth"
- "Show me how BaseNode is extended"

### 2. `@docs-writer` - Documentation Specialist ✅
**Purpose:** Create and maintain documentation
**Model:** Flash
**Tools:** `read`, `write`, `edit`
**Use Cases:**
- "Document this module with docstrings"
- "Create a README for the nodes folder"
- "Update API docs for auth endpoints"

### 3. `@refactor` - Code Improvement Specialist ✅
**Purpose:** Safe refactoring without changing behavior
**Model:** Pro (complex reasoning)
**Tools:** `read`, `write`, `edit`, `grep`, `bash`
**Use Cases:**
- "Refactor this class to use composition"
- "Extract common logic into a base class"
- "Clean up imports in this module"

### 4. `@performance` - Performance Optimizer ✅
**Purpose:** Identify and fix performance bottlenecks
**Model:** Flash
**Tools:** `read`, `grep`, `bash`
**Use Cases:**
- "Find blocking calls in async functions"
- "Optimize this database query"
- "Profile this workflow execution"

---

## Phase 3: Domain-Specific Subagents ✅ COMPLETE

### 5. `@workflow-expert` - Workflow Design Specialist ✅
**Purpose:** Design and debug RPA workflows
**Model:** Pro
**Tools:** `read`, `write`, `edit`, `grep`
**Use Cases:**
- "Design a workflow for email processing"
- "Debug why this workflow hangs at node X"
- "Optimize this workflow for parallel execution"

### 6. `@security-auditor` - Security Specialist ✅
**Purpose:** Identify and fix security vulnerabilities
**Model:** Pro (critical analysis)
**Tools:** `read`, `grep`
**Use Cases:**
- "Audit auth.py for vulnerabilities"
- "Check for hardcoded secrets"
- "Review JWT implementation"

### 7. `@database` - Database & Supabase Specialist ✅
**Purpose:** Database schema design and queries
**Model:** Flash
**Tools:** `read`, `write`, `edit`, `grep`
**Use Cases:**
- "Design schema for workflow history"
- "Optimize this Supabase query"
- "Create migration for new robot fields"

---

## Phase 4: Automation & DevOps ✅ COMPLETE

### 8. `@ci-cd` - CI/CD Pipeline Specialist ✅
**Purpose:** GitHub Actions, testing pipelines
**Model:** Flash
**Tools:** `read`, `write`, `edit`
**Use Cases:**
- "Set up automated testing workflow"
- "Add code coverage to CI"
- "Create release pipeline"

### 9. `@playwright` - Browser Automation Expert ✅
**Purpose:** Playwright test and node development
**Model:** Flash
**Tools:** `read`, `write`, `edit`, `grep`, `bash`
**Use Cases:**
- "Create a browser node for form filling"
- "Debug this Playwright locator"
- "Write E2E tests for the canvas UI"

---

## Implementation Priority

| Priority | Subagent | Reason |
|:---------|:---------|:-------|
| 🔴 High | `@explorer` | Essential for understanding large codebases |
| 🔴 High | `@refactor` | Ongoing code improvement |
| 🟠 Medium | `@docs-writer` | Keeps documentation up-to-date |
| 🟠 Medium | `@workflow-expert` | Core domain of CasareRPA |
| 🟠 Medium | `@security-auditor` | Critical for production safety |
| 🟢 Low | `@performance` | Optimization when needed |
| 🟢 Low | `@database` | Supabase-specific work |
| 🟢 Low | `@ci-cd` | DevOps improvements |
| 🟢 Low | `@playwright` | Browser automation specialists |

---

## Cost Optimization Strategy

### Model Assignment
- **Gemini 2.5 Pro** → Complex reasoning, architecture, security
- **Gemini 2.5 Flash** → Fast lookups, simple edits, documentation

### Tool Restrictions
- **Read-only subagents** (explorer, code-reviewer, security-auditor) → Safer, faster
- **Write-enabled subagents** (node-creator, refactor) → Can modify code

---

## Next Steps

1. ☑ Implement Phase 1 subagents (7 core) - DONE
2. ☑ Implement Phase 2 subagents (4 essential) - DONE
3. ☑ Implement Phase 3 subagents (3 domain) - DONE
4. ☑ Implement Phase 4 subagents (2 DevOps) - DONE
5. ☐ Test each subagent with sample tasks
6. ☐ Document usage examples in README

---

## 🎉 ALL PHASES COMPLETE!

**Total Subagents:** 16
**Pro Models:** 6 (complex reasoning)
**Flash Models:** 10 (fast execution)
