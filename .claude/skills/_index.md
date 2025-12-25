# Skills Index

Utility skills for CasareRPA agent framework. Workflow-phase agents are now in `../agents/`.

## Agent → Skill Mappings

| Agent | Assigned Skills |
|-------|----------------|
| **builder** | `node-template-generator`, `import-fixer`, `error-doctor` |
| **explore** | (none - read-only exploration) |
| **architect** | `node-template-generator`, `workflow-validator` |
| **quality** | `test-generator`, `performance`, `workflow-validator` |
| **reviewer** | (none - read-only review) |
| **refactor** | `import-fixer`, `error-doctor` |
| **integrations** | `dependency-updater`, `error-doctor` |
| **docs** | `changelog-updater`, `brain-updater`, `commit-message-generator` |
| **ui** | `ui-specialist` |
| **general** | `error-doctor`, `chain-tester`, `ci-cd` |
| **researcher** | (none - external research) |
| **security-auditor** | (none - read-only audit) |

## Promoted to Agents

The following have been promoted to agents (see `../agents/_index.md`):
- ~~explorer~~ → **explore** agent
- ~~refactor~~ → **refactor** agent
- ~~integrations~~ → **integrations** agent
- ~~security-auditor** → **security-auditor** agent

## Available Skills

| Skill | Description | Assigned To |
|-------|-------------|-------------|
| `brain-updater` | Update .brain/ context files after tasks | docs |
| `chain-tester` | Test agent chaining workflows | general |
| `changelog-updater` | Update CHANGELOG.md entries | docs |
| `ci-cd` | CI/CD pipelines, GitHub Actions | general |
| `commit-message-generator` | Generate conventional commit messages | docs |
| `dependency-updater` | Update project dependencies | integrations |
| `error-doctor` | Systematic error diagnosis | builder, refactor, integrations, general |
| `import-fixer` | Fix Python import statements | builder, refactor |
| `node-template-generator` | Generate new node templates | builder, architect |
| `performance` | Performance optimization, caching | quality |
| `test-generator` | Generate pytest test suites | quality |
| `ui-specialist` | PySide6 UI, dark theme, signals/slots | ui |
| `workflow-validator` | Validate workflow JSON files | architect, quality |

## Skill Format

Each skill follows this structure:

```
.claude/skills/
├── _index.md
├── agent-invoker/
│   └── agent-invoker.md
├── brain-updater/
│   └── brain-updater.md
└── ...
```

Each skill file includes:
- YAML frontmatter with `name`, `description`, `license`, `compatibility`
- Detailed usage instructions
- Code examples where applicable
