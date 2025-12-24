# Skills Index (.opencode)

This folder provides a compatibility layer for `.opencode` agent framework.

**All skills are sourced from:** `.claude/skills/`

## Available Skills

| Skill | Source | Description |
|-------|--------|-------------|
| [ci-cd](.claude/skills/ci-cd.md) | `.claude/skills/ci-cd.md` | CI/CD pipelines, GitHub Actions, quality gates |
| [error-doctor](.claude/skills/error-doctor.md) | `.claude/skills/error-doctor.md` | Systematic error diagnosis |
| [explorer](.claude/skills/explorer.md) | `.claude/skills/explorer.md` | Codebase exploration with semantic search |
| [integrations](.claude/skills/integrations.md) | `.claude/skills/integrations.md` | External API integrations, OAuth, databases |
| [performance](.claude/skills/performance.md) | `.claude/skills/performance.md` | Performance optimization, caching, async |
| [refactor](.claude/skills/refactor.md) | `.claude/skills/refactor.md` | Code refactoring with DDD patterns |
| [security-auditor](.claude/skills/security-auditor.md) | `.claude/skills/security-auditor.md` | Security auditing, OWASP compliance |
| [ui-specialist](.claude/skills/ui-specialist.md) | `.claude/skills/ui-specialist.md` | PySide6 UI, dark theme, signals/slots |

## MCP-First Standard

All skills follow the MCP-first workflow:

1. **codebase** → Semantic search (FIRST, not grep)
2. **sequential-thinking** → Complex analysis
3. **filesystem** → view_file related files
4. **git** → Check history/changes
5. **exa** → Web research for best practices
6. **ref** → Library documentation lookup

## Usage in Agents

```markdown
## Skills Reference

| Skill | Purpose | Trigger |
|-------|---------|---------|
| [skill-name](.claude/skills/skill-name.md) | Description | "trigger phrase" |
```
