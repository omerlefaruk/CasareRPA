# .claude/commands Index

Slash commands for common development workflows.

## Available Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| [implement-feature.md](implement-feature.md) | Feature implementation workflow | `/implement-feature <description>` |
| [implement-node.md](implement-node.md) | Node implementation workflow | `/implement-node <node-name>` |
| [fix-feature.md](fix-feature.md) | Bug fix workflow | `/fix-feature <bug-description>` |
| [plan-workflow.md](plan-workflow.md) | Workflow planning | `/plan-workflow <goal>` |

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

## Cross-References

| Topic | See Also |
|-------|----------|
| Full command details | `agent-rules/commands/` |
| Decision trees | `.brain/decisions/` |
| Agent definitions | `.claude/agents/` |

---

*Parent: [../_index.md](../_index.md)*
*Full reference: [../../agent-rules/commands/](../../agent-rules/commands/)*
*Last updated: 2025-12-14*
