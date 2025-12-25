# Agent & Worktree Protocols

**Part of:** `.brain/projectRules.md` | **See also:** `coding-standards.md`

## Agent Protocol (Multi-Agent Coordination)

### Brain Updates
After completing major tasks, update `.brain/` files:

| File | When | What |
|------|------|------|
| **current.md** | After PLAN/BUILD phase | Current focus, blockers, decisions |
| **systemPatterns.md** | When discovering new pattern | Document reusable patterns |
| **projectRules.md** | When rules change | Update this file (read-only outside main) |

### Planning Protocol

1. **Create Plan File:** `.claude/plans/{feature}.md`
2. **Launch Explore Agents** (1-3 parallel): Research, document findings
3. **User Approval:** Wait for sign-off before BUILD
4. **Execute in Parallel:** Up to 10 agents for implementation
5. **QA Phase:** Test + integration testing
6. **Documentation:** Generate user guides + API docs

### State Machine
```
┌─────────┐     approval      ┌───────┐     QA      ┌──────┐
│  PLAN   ├──────────────────>│ BUILD ├───────────>│  QA  │
└─────────┘                   └───────┘            └──────┘
                                                        │
                                                    approval
                                                        │
                                                        v
                                                    ┌────────┐
                                                    │  DOCS  │
                                                    └────────┘
```

**Transitions:**
- PLAN → BUILD: Requires user approval of design
- BUILD → QA: All tasks completed
- QA → DOCS: Tests passing
- DOCS → END: Documentation complete

## Worktree Protocol (Multi-Instance Work)

Use Git worktrees for parallel feature development:

### Create Isolated Worktree
```bash
git worktree add -b feat/{name} ../{name} main

# Example
git worktree add -b feat/node-versioning ../node-versioning main
```

### Work in Worktree
```bash
cd ../{name}
python run.py
pytest tests/
git add . && git commit -m "feat: description"
```

### Merge Back to Main
```bash
# In main repo
git checkout main
git merge feat/{name}
git push origin main

# Cleanup worktree
git worktree remove ../{name}
```

### Rules
- **One worktree per agent** (no interference)
- **Base all on `main`** (always up-to-date)
- **Commit naming:** `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **No force pushes** (respect other agents)
- **Clean up after merge** (remove worktree)

---

**See:** `.claude/plans/` for active plans
