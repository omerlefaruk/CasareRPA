<<<<<<< HEAD
# .claude/commands Index
=======
# Commands Index
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

Slash commands for common development workflows.

## Available Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| [implement-feature.md](implement-feature.md) | Feature implementation workflow | `/implement-feature <description>` |
| [implement-node.md](implement-node.md) | Node implementation workflow | `/implement-node <node-name>` |
| [fix-feature.md](fix-feature.md) | Bug fix workflow | `/fix-feature <bug-description>` |
| [plan-workflow.md](plan-workflow.md) | Workflow planning | `/plan-workflow <goal>` |
<<<<<<< HEAD
=======
| [new-pattern-checklist.md](new-pattern-checklist.md) | Document new patterns/rules | `/new-pattern-checklist` |
| [qa-checklist.md](qa-checklist.md) | QA + self-review checklist | `/qa-checklist` |
| [review-plan.md](review-plan.md) | Plan review and approval | `/review-plan` |
| [phase-report.md](phase-report.md) | Phase/progress report helper | `/phase-report` |
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

## Command Workflows

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

<<<<<<< HEAD
=======
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

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
## Cross-References

| Topic | See Also |
|-------|----------|
<<<<<<< HEAD
| Full command details | `agent-rules/commands/` |
| Decision trees | `.brain/decisions/` |
| Agent definitions | `.claude/agents/` |
=======
| Reference command details | `agent-rules/commands/` |
| Decision trees | `.brain/decisions/` |
| Agent definitions | `../agents/` |
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

---

*Parent: [../_index.md](../_index.md)*
<<<<<<< HEAD
*Full reference: [../../agent-rules/commands/](../../agent-rules/commands/)*
=======
*Reference: [../../agent-rules/commands/](../../agent-rules/commands/)*
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
*Last updated: 2025-12-14*
