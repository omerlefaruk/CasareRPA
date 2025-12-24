# Skills Index

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
| [performance.md](performance.md) | Performance optimization | "Profile performance" |
| [error-doctor.md](error-doctor.md) | Error diagnosis | "Diagnose error" |
| [refactor.md](refactor.md) | Safe code refactoring | "Refactor code" |
| [ui-specialist.md](ui-specialist.md) | PySide6 UI development | "Create UI widget" |
| [integrations.md](integrations.md) | External API integrations | "Add integration" |
| [security-auditor.md](security-auditor.md) | Security auditing | "Audit security" |
| [ci-cd.md](ci-cd.md) | CI/CD pipelines | "Create CI pipeline" |
| [explorer.md](explorer.md) | Codebase exploration | "Explore codebase" |

## Skill Categories

### Development
- `node-template-generator.md` - Node scaffolding
- `test-generator.md` - Test file generation
- `import-fixer.md` - Import cleanup
- `refactor.md` - Code refactoring

### Quality & Performance
- `code-reviewer.md` - Code review
- `workflow-validator.md` - Workflow validation
- `chain-tester.md` - Agent chain testing
- `performance.md` - Performance profiling

### UI & Experience
- `ui-specialist.md` - PySide6 widgets
- `error-doctor.md` - Error handling

### Integration
- `integrations.md` - External APIs
- `security-auditor.md` - Security auditing

### DevOps
- `ci-cd.md` - CI/CD pipelines
- `dependency-updater.md` - Dependency management

### Documentation
- `brain-updater.md` - Knowledge base updates
- `changelog-updater.md` - Release notes

### Utilities
- `commit-message-generator.md` - Git commits
- `agent-invoker.md` - Agent orchestration
- `explorer.md` - Codebase exploration

## MCP-First Standard (NEW)

All new skills follow MCP-first workflow:

1. **codebase** - Semantic search (FIRST, not grep!)
2. **sequential-thinking** - Complex analysis
3. **filesystem** - view_file related files
4. **git** - Check history/changes
5. **exa** - Web research for best practices
6. **ref** - Library documentation lookup

## Usage

Skills are invoked via the Skill tool:
```python
Skill(skill="node-template-generator")
Skill(skill="performance")
```

## Cross-References

| Topic | See Also |
|-------|----------|
| Agent definitions | `../agents/` |
| Commands | `../commands/` |
| Node templates | `.brain/docs/node-templates.md` |
| OpenCode agents | `../../.opencode/agent/` |
| MCP config | `../../.opencode/mcp_config.json` |

---

*Parent: [../_index.md](../_index.md)*
*Last updated: 2025-12-25*
