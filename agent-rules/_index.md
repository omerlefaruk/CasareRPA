# Agent Rules Index

Reference-only agent rules for CasareRPA. Primary source of truth lives in `.agent/` (mirrored to `.claude/`).

## Directory Structure

| Directory | Purpose | Count |
|-----------|---------|-------|
| `rules/` | Core behavior rules | 18 |
| `agents/` | Specialized agent definitions | 11 |
| `skills/` | Reusable skill templates | 18 |
| `commands/` | Workflow commands | 10 |

## Rules (rules/)

| File | Purpose |
|------|---------|
| `00-role.md` | Role & Philosophy |
| `01-core.md` | Core workflow & standards |
| `01-workflow-default.md` | Default workflow configuration |
| `01-workflow.md` | 5-Phase Workflow |
| `02-architecture.md` | DDD 2025 Architecture |
| `02-coding-standards.md` | Coding Standards |
| `03-architecture.md` | Clean Architecture |
| `03-nodes.md` | Node development |
| `04-agents.md` | Agent Registry |
| `05-triggers.md` | Workflow Triggers |
| `06-enforcement.md` | Quality Enforcement |
| `07-tools.md` | Tool Usage |
| `08-token-optimization.md` | Token Efficiency |
| `09-brain-protocol.md` | Brain Protocol |
| `10-node-workflow.md` | Node Development |
| `11-node-templates.md` | Node Templates |
| `12-ddd-events.md` | Typed events reference |

## Agents (agents/)

| Agent | Use Case |
|-------|----------|
| `architect.md` | System design |
| `builder.md` | Implementation |
| `docs.md` | Documentation |
| `explore.md` | Codebase navigation |
| `integrations.md` | External services |
| `quality.md` | Testing/QA |
| `refactor.md` | Code improvement |
| `researcher.md` | Investigation |
| `reviewer.md` | Code review |
| `ui.md` | PySide6 UI |

## Skills (skills/)

| Skill | Purpose |
|-------|---------|
| `agent-invoker.md` | Invoke agent workflows |
| `api-integration.md` | API integration guidance |
| `brain-updater.md` | Update .brain/ files |
| `chain-tester.md` | Agent chain testing |
| `changelog-updater.md` | Changelog updates |
| `code-reviewer.md` | Automated code review |
| `commit-message-generator.md` | Commit message helper |
| `dependency-updater.md` | Dependency updates |
| `error-diagnosis.md` | Error diagnosis playbook |
| `import-fixer.md` | Fix imports |
| `node-creator.md` | Node creation workflow |
| `node-template-generator.md` | Scaffold nodes |
| `performance-optimizer.md` | Performance tuning |
| `semantic-search.md` | Semantic search guidance |
| `test-generator.md` | Generate test files |
| `ui-widget.md` | UI widget templates |
| `workflow-validator.md` | Workflow validation |

## Commands (commands/)

| Command | Workflow |
|---------|----------|
| `fix-feature.md` | Bug fix workflow |
| `implement-feature.md` | Feature implementation |
| `implement-node.md` | Node implementation |
| `plan-workflow.md` | Workflow planning |
| `search-codebase.md` | Codebase search workflow |
| `new-pattern-checklist.md` | Document new patterns/rules |
| `qa-checklist.md` | QA + self-review checklist |
| `review-plan.md` | Plan review and approval |
| `phase-report.md` | Phase/progress report helper |
