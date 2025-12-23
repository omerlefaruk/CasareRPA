<<<<<<< HEAD
# .claude/skills Index
=======
# Skills Index
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

Reusable skill templates for automation tasks.

## Available Skills

| Skill | Purpose | Trigger |
|-------|---------|---------|
| [node-template-generator.md](node-template-generator.md) | Generate node scaffolding | "Generate node template" |
| [workflow-validator.md](workflow-validator.md) | Validate workflow files | "Validate workflow" |
| [commit-message-generator.md](commit-message-generator.md) | Generate commit messages | "Generate commit" |
| [dependency-updater.md](dependency-updater.md) | Update dependencies | "Update deps" |
| [test-generator.md](test-generator.md) | Generate test files | "Generate tests" |
| [changelog-updater.md](changelog-updater.md) | Update changelog | "Update changelog" |
| [import-fixer.md](import-fixer.md) | Fix import statements | "Fix imports" |
| [code-reviewer.md](code-reviewer.md) | Automated code review | "Review code" |
| [brain-updater.md](brain-updater.md) | Update .brain/ files | "Update brain" |
| [chain-tester.md](chain-tester.md) | Test agent chains | "Test chain" |
| [agent-invoker.md](agent-invoker.md) | Invoke agents | "Invoke agent" |

## Skill Categories

### Development
- `node-template-generator.md` - Node scaffolding
- `test-generator.md` - Test file generation
- `import-fixer.md` - Import cleanup

### Quality
- `code-reviewer.md` - Code review
- `workflow-validator.md` - Workflow validation
- `chain-tester.md` - Agent chain testing

### Documentation
- `brain-updater.md` - Knowledge base updates
- `changelog-updater.md` - Release notes

### Operations
- `commit-message-generator.md` - Git commits
- `dependency-updater.md` - Dependency management
- `agent-invoker.md` - Agent orchestration

## Usage

Skills are invoked via the Skill tool:
```python
Skill(skill="node-template-generator")
Skill(skill="test-generator")
```

## Cross-References

| Topic | See Also |
|-------|----------|
<<<<<<< HEAD
| Agent definitions | `.claude/agents/` |
| Commands | `.claude/commands/` |
=======
| Agent definitions | `../agents/` |
| Commands | `../commands/` |
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
| Node templates | `.brain/docs/node-templates.md` |

---

*Parent: [../_index.md](../_index.md)*
*Last updated: 2025-12-14*
