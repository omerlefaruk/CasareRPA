# Pull Request Guidelines

This document outlines the process for creating and reviewing pull requests in CasareRPA.

## Branch Naming

Use descriptive branch names with appropriate prefixes:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/node-versioning` |
| `fix/` | Bug fix | `fix/selector-timeout` |
| `refactor/` | Code restructure | `refactor/execution-engine` |
| `docs/` | Documentation | `docs/api-reference` |
| `test/` | Test improvements | `test/node-coverage` |
| `chore/` | Maintenance tasks | `chore/update-dependencies` |

```bash
# Create feature branch
git checkout -b feat/my-feature main

# Create bugfix branch
git checkout -b fix/issue-123 main
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code change, no new feature or fix |
| `test` | Adding or updating tests |
| `chore` | Maintenance (deps, CI, etc.) |

### Examples

```bash
# Simple commit
git commit -m "feat: add login node for web automation"

# With scope
git commit -m "fix(browser): resolve timeout on element click"

# With body
git commit -m "feat(nodes): add PDF extraction node

- Supports text extraction from all pages
- Handles encrypted PDFs with password
- Returns structured data with page numbers"

# Breaking change
git commit -m "refactor!: rename ExecutionContext to RunContext

BREAKING CHANGE: All node execute() signatures now use RunContext.
Migration: Replace ExecutionContext with RunContext in all imports."
```

### Rules

- Subject line: 50 characters max, imperative mood ("add", not "added")
- Body: Wrap at 72 characters, explain WHY not WHAT
- Footer: Reference issues with `Fixes #123` or `Closes #123`

## Creating a Pull Request

### 1. Prepare Your Branch

```bash
# Ensure branch is up to date
git checkout main
git pull origin main
git checkout feat/my-feature
git rebase main

# Run tests
pytest tests/ -v

# Run linter
ruff check src/ tests/ --fix
ruff format src/ tests/

# Commit any fixes
git add .
git commit -m "style: fix linting issues"
```

### 2. Push and Create PR

```bash
git push -u origin feat/my-feature
```

Then create PR via GitHub UI or CLI:

```bash
gh pr create --title "feat: add PDF extraction node" --body-file PR_TEMPLATE.md
```

### 3. PR Description Template

Use this template for all PRs:

```markdown
## Summary

Brief description of what this PR does (1-3 sentences).

## Changes

- List of specific changes
- Include file paths for significant changes
- Note any new dependencies

## Test Plan

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] Manual testing completed
- [ ] All tests passing locally

## Screenshots (if UI changes)

Before | After
--- | ---
[image] | [image]

## Checklist

- [ ] Code follows project coding standards
- [ ] Self-reviewed my code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] No breaking changes (or documented)
- [ ] Added tests for new functionality

## Related Issues

Fixes #123
Related to #456
```

## Code Review Checklist

Reviewers should verify:

### Code Quality

- [ ] Follows [Coding Standards](coding-standards.md)
- [ ] Type hints on all public APIs
- [ ] Docstrings on public functions
- [ ] No hardcoded values (uses constants/Theme)
- [ ] Errors handled and logged with context

### Architecture

- [ ] Respects DDD layer boundaries
- [ ] No circular imports
- [ ] Uses dependency injection
- [ ] Typed events for communication

### Testing

- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases
- [ ] Mocking strategy is correct
- [ ] Coverage targets met

### Security

- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] External calls use UnifiedHttpClient
- [ ] No SQL injection vectors

### Performance

- [ ] Async where appropriate
- [ ] No blocking calls in async code
- [ ] Resource cleanup (context managers)
- [ ] No unnecessary loops/allocations

## CI/CD Pipeline

Every PR triggers automated checks:

| Check | Tool | Requirement |
|-------|------|-------------|
| Lint | Ruff | No errors |
| Format | Ruff | No changes needed |
| Tests | pytest | All passing |
| Coverage | pytest-cov | >= 75% |
| Security | pip-audit | No high/critical vulns |

### Viewing CI Status

- Check status icons on PR
- Click "Details" to see logs
- Fix any failures before requesting review

### Common CI Failures

| Failure | Fix |
|---------|-----|
| Ruff lint errors | `ruff check src/ --fix` |
| Format issues | `ruff format src/` |
| Test failures | Run `pytest tests/ -x --pdb` locally |
| Coverage below threshold | Add tests for uncovered code |

## Review Process

### 1. Self-Review

Before requesting review:

```bash
# Diff against main
git diff main...HEAD

# Check for common issues
ruff check src/ tests/
pytest tests/ -v --cov=casare_rpa
```

### 2. Request Review

- Assign 1-2 reviewers familiar with the area
- Add appropriate labels (feature, bugfix, etc.)
- Link related issues

### 3. Address Feedback

- Respond to all comments
- Make requested changes in new commits (don't force push until approved)
- Re-request review after addressing feedback

### 4. Approval and Merge

Requirements for merge:
- At least 1 approval from reviewer
- All CI checks passing
- No unresolved comments
- Branch up to date with main

## Merging

### Merge Strategy

Use **Squash and Merge** for most PRs:

```bash
# Via GitHub UI
Select "Squash and merge"

# Via CLI
gh pr merge --squash
```

This creates a single commit on main with a clean history.

### When to Use Regular Merge

Use regular merge for:
- Release branches
- Large features with meaningful commit history

### Post-Merge

```bash
# Delete local branch
git checkout main
git pull origin main
git branch -d feat/my-feature

# Delete remote branch (usually automatic)
git push origin --delete feat/my-feature
```

## Handling Merge Conflicts

```bash
# Update your branch
git checkout feat/my-feature
git fetch origin
git rebase origin/main

# Resolve conflicts in each file
# Edit files to resolve conflicts
git add <resolved-files>
git rebase --continue

# Force push (only your branch!)
git push --force-with-lease origin feat/my-feature
```

> **Warning:** Never force push to `main` or shared branches.

## Worktree Protocol (Parallel Development)

For working on multiple features simultaneously:

```bash
# Create isolated worktree
git worktree add -b feat/new-feature ../new-feature main

# Work in worktree
cd ../new-feature
# Make changes...
git add . && git commit -m "feat: description"

# Merge back
git checkout main
git merge feat/new-feature
git worktree remove ../new-feature
```

## Quick Reference

### Common Commands

```bash
# Create branch
git checkout -b feat/my-feature main

# Update branch
git fetch origin && git rebase origin/main

# Push branch
git push -u origin feat/my-feature

# Create PR
gh pr create --title "feat: description" --body "Summary..."

# View PR status
gh pr status

# Merge PR
gh pr merge --squash
```

### Checklist Before Submitting

- [ ] Branch name follows convention
- [ ] Commits follow conventional format
- [ ] Tests pass locally
- [ ] Linter passes
- [ ] PR description filled out
- [ ] Related issues linked

## Related Documentation

- [Coding Standards](coding-standards.md) - Style guidelines
- [Testing Guide](testing.md) - Test requirements
- [Release Process](release-process.md) - How releases work

---

**Questions?** Check existing PRs for examples or ask in the issue thread.
