---
name: commit-message-generator
description: Generate well-formatted, conventional commit messages based on staged changes.
---

# Commit Message Generator

Generate conventional commit messages following project standards.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, whitespace
- **refactor**: Code change (not fix/feature)
- **perf**: Performance improvement
- **test**: Adding/correcting tests
- **build**: Build system/dependencies
- **ci**: CI configuration
- **chore**: Other changes

## Scopes

**Domain**: `domain/entities`, `domain/services`, `domain/repositories`
**Application**: `use-cases`
**Infrastructure**: `resources`, `persistence`
**Presentation**: `canvas`, `controllers`, `components`, `visual-nodes`
**Nodes**: `nodes/browser`, `nodes/desktop`, `nodes/data`, etc.
**Other**: `tests`, `ci`, `build`

## Subject Line

- Imperative mood: "add" not "added"
- Lowercase first letter
- No period at end
- Max 72 characters

## Example

```
feat(nodes/browser): add screenshot capture node

- Implement ScreenshotNode with full-page capture
- Add PNG/JPEG format support
- Include automatic filename generation

Supports both full-page and element-specific captures.

Tests: tests/nodes/browser/test_screenshot_node.py (12 tests)
```

## Claude Code Attribution

For commits generated with Claude Code:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```
