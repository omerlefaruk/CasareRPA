# Agents Index

Specialized subagents for CasareRPA workflow. All agents include **worktree guard** to prevent working on main/master.

## Core Agents (Workflow Phases)

| Agent | Purpose | Phase | Skills |
|-------|---------|-------|--------|
| **explore** | Codebase search, pattern discovery | RESEARCH | - |
| **architect** | System design, architecture planning | PLAN | node-template-generator, workflow-validator |
| **builder** | Code writing (KISS & DDD) | EXECUTE | node-template-generator, import-fixer, error-doctor |
| **refactor** | Safe code refactoring | EXECUTE | import-fixer, error-doctor |
| **integrations** | External API integrations | EXECUTE | dependency-updater, error-doctor |
| **quality** | Testing, performance | VALIDATE | test-generator, performance, workflow-validator |
| **security-auditor** | Security audits | VALIDATE | - |
| **reviewer** | Code review gate (MANDATORY) | VALIDATE | - |
| **docs** | Documentation generation | DOCS | changelog-updater, brain-updater, commit-message-generator |

## Utility Agents

| Agent | Purpose | When to Use | Skills |
|-------|---------|-------------|--------|
| **general** | Research, multi-step tasks | Uncertain queries | error-doctor, chain-tester, ci-cd |
| **researcher** | Competitive analysis, library comparison | External research | - |
| **ui** | PySide6 UI design | Canvas UI work | ui-specialist |

## Worktree Guard

All agents run this check before starting work:
```bash
python scripts/check_not_main_branch.py
```

If on main/master, agents refuse to proceed and instruct:
```bash
python scripts/create_worktree.py "feature-name"
```

## Workflow Sequence

```
explore → architect → builder/refactor/integrations → quality → reviewer → docs
```

## Agent Format

```yaml
---
name: agent-name
description: Brief description
---
```

## Skills (See ../skills/)

Skills are invoked by agents via the Skill tool:

| Skill | Assigned Agents |
|-------|-----------------|
| node-template-generator | builder, architect |
| import-fixer | builder, refactor |
| error-doctor | builder, refactor, integrations, general |
| test-generator | quality |
| performance | quality |
| workflow-validator | architect, quality |
| changelog-updater | docs |
| brain-updater | docs |
| commit-message-generator | docs |
| dependency-updater | integrations |
| ui-specialist | ui |
| chain-tester | general |
| ci-cd | general |
| agent-invoker | reference only |
