# Skills Reference Table

**Parent:** `.claude/skills/_index.md` | **Last Updated:** 2025-12-25

## Complete Skills Matrix

| Skill | Category | Lines | Use When | Output |
|-------|----------|-------|----------|--------|
| **node-template-generator** | Development | ~100 | Creating new nodes | Node scaffolding with properties, ports |
| **test-generator** | Development | ~430 | Writing unit tests | Test file with fixtures + assertions |
| **import-fixer** | Development | ~50 | Cleaning imports | Fixed import blocks |
| **code-reviewer** | Quality | ~120 | After implementation | APPROVED/ISSUES with file:line |
| **workflow-validator** | Quality | ~400 | Checking workflow files | ValidationReport with errors |
| **chain-tester** | Quality | ~295 | Integration testing | WorkflowBuilder test patterns |
| **brain-updater** | Documentation | ~150 | Session complete | .brain/ file updates |
| **changelog-updater** | Documentation | ~80 | Release pending | CHANGELOG.md entry |
| **commit-message-generator** | Operations | ~60 | Git commit | Conventional commit message |
| **dependency-updater** | Operations | ~90 | Package update | requirements.txt + pyproject.toml |

**Archived:**
- ~~agent-invoker~~ - Use `/chain` command instead

---

## Quick Reference by Task Type

| Task | Use Skill | Command |
|------|-----------|---------|
| Add new node | node-template-generator | Generate node template |
| Write tests | test-generator | Generate tests |
| Clean imports | import-fixer | Fix imports |
| Review code | code-reviewer | Review code |
| Validate workflow | workflow-validator | Validate workflow |
| Test chains | chain-tester | Test chain |
| Update .brain | brain-updater | Update brain |
| Prepare release | changelog-updater | Update changelog |
| Commit changes | commit-message-generator | Generate commit |
| Update deps | dependency-updater | Update deps |

---

## Skill vs Agent Decision

| Situation | Use | Example |
|-----------|-----|---------|
| Generate scaffolding | **Skill** | node-template-generator |
| Implement feature | **Agent** | builder |
| Design system | **Agent** | architect |
| Test implementation | **Agent** | quality |
| Review code | **Agent** | reviewer (uses code-reviewer format) |
| Find patterns | **Agent** | explore |
| Research topic | **Agent** | researcher |

**Rule:** Skills generate templates/checklists. Agents perform work.
