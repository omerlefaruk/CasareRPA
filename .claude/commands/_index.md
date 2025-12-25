# Commands Index

Slash commands for common development workflows.

## Available Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| [chain.md](chain.md) | Agent chaining with loop-based error recovery | `/chain <task_type> "<description>" [options]` |
| [implement-feature.md](implement-feature.md) | Feature implementation workflow | `/implement-feature <description>` |
| [implement-node.md](implement-node.md) | Node implementation workflow | `/implement-node <node-name>` |
| [fix-feature.md](fix-feature.md) | Bug fix workflow | `/fix-feature <bug-description>` |
| [plan-workflow.md](plan-workflow.md) | Workflow planning | `/plan-workflow <goal>` |
| [new-pattern-checklist.md](new-pattern-checklist.md) | Document new patterns/rules | `/new-pattern-checklist` |
| [qa-checklist.md](qa-checklist.md) | QA + self-review checklist | `/qa-checklist` |
| [review-plan.md](review-plan.md) | Plan review and approval | `/review-plan` |
| [phase-report.md](phase-report.md) | Phase/progress report helper | `/phase-report` |

## Command Workflows

### /chain (Agent Chaining)
```
Task Types: implement, fix, refactor, research, extend, clone, test, docs, security, ui, integration
Options: --parallel, --priority, --max-iterations, --timeout, --dry-run, --skip-review

PHASE 1: EXPLORE (parallel 2-3 agents)
  → Find existing patterns, tests, rules

PHASE 2: ARCHITECT (for implement/extend)
  → Create plan in .brain/plans/
  → GATE: User approval

PHASE 3: BUILD (parallel 2-5 agents)
  → builder / refactor / integrations / ui

PHASE 4: QUALITY
  → Run tests, lint, type check

PHASE 5: REVIEWER (gate)
  → APPROVED or ISSUES
  → LOOP: If ISSUES → BUILD → QUALITY → REVIEWER (max 3)

PHASE 6: DOCS
  → Update _index.md, .brain/context/current.md
```

### /implement-feature
```
1. RESEARCH: explore agent finds related code
2. PLAN: architect creates plan in .brain/plans/
3. EXECUTE: builder implements feature
4. VALIDATE: quality → reviewer loop
5. DOCS: Update documentation
```

### /implement-node
```
1. CHECK: Verify node doesn't exist
2. PLAN: Design node with properties
3. CREATE: Generate node + visual node
4. REGISTER: Add to _NODE_REGISTRY
5. TEST: Create and run tests
6. DOCS: Update _index.md files
```

### /fix-feature
```
1. DIAGNOSE: explore finds root cause
2. PLAN: architect creates fix plan
3. FIX: builder applies minimal fix
4. VALIDATE: quality → reviewer loop
5. DOCS: Update .brain/errors.md if needed
```

### /plan-workflow
```
1. ANALYZE: Understand goal
2. DESIGN: Create workflow structure
3. IDENTIFY: List required nodes
4. DOCUMENT: Create plan document
```

### /new-pattern-checklist
```
1. VALIDATE: Confirm pattern is reusable
2. GUIDE: Update AGENTS.md and sync CLAUDE.md + GEMINI.md
3. RULES: Update rules and .brain docs
4. INDEX: Update _index.md files if needed
5. EVIDENCE: Add tests/examples
```

### /qa-checklist
```
1. REVIEW: Self code review for correctness and style
2. QA: Run tests or document why not
3. DOCS: Update rules, AGENTS.md, and docs as needed
```

### /review-plan
```
1. VERIFY: Plan scope, risks, and success criteria
2. ALIGN: Re-read rules/design docs
3. APPROVE: Ask user to approve before EXECUTE
```

### /phase-report
```
1. REPORT: Print phase/progress block
2. LOG: Append to .brain/context/current.md
```

## Cross-References

| Topic | See Also |
|-------|----------|
| Reference command details | `agent-rules/commands/` |
| Decision trees | `.brain/decisions/` |
| Agent definitions | `../agents/` |

---

*Parent: [../_index.md](../_index.md)*
*Reference: [../../agent-rules/commands/](../../agent-rules/commands/)*
*Last updated: 2025-12-14*
